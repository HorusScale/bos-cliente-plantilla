#!/usr/bin/env python3
"""Espera a que Railway TERMINE de desplegar un commit en los servicios indicados (0.55, C8).

POR QUÉ EXISTE. Verificar contra un despliegue que todavía no ha terminado —o que es del commit
anterior— ya mordió dos veces en ADO. El panel no ayuda: un servicio muestra «SUCCESS» con el
despliegue VIEJO mientras el nuevo sigue construyendo, se queda en `NEEDS_APPROVAL` días enteros
(el arreglo de recuperación de contraseñas de ADO estuvo parado desde el 11-sep sin que nadie lo
viera), o no llega nunca porque al servicio le falta el trigger (5 de 6 servicios de ADO, ticket
422ea83bffbd). `docs/distribucion/despliegue.md` traía el checklist a mano; esto lo ejecuta.

QUÉ HACE, por cada servicio, hasta que todos llegan a un estado terminal o se agota el tiempo:
  · busca el despliegue MÁS RECIENTE de ESE commit (`meta.commitHash`, admite un SHA corto);
  · espera a que termine: SUCCESS (o SLEEPING, que es un SUCCESS dormido) es verde; FAILED,
    CRASHED, REMOVED y SKIPPED son rojo;
  · NEEDS_APPROVAL no avanza solo: lo AVISA y deja de esperarlo (con `--esperar-aprobacion`, sigue
    esperando a que alguien lo apruebe);
  · si hay un despliegue MÁS NUEVO de otro commit, el tuyo no es el que corre: rojo, y lo nombra;
  · si en `--gracia` segundos no aparece ningún despliegue de ese commit, rojo: o el trigger no
    está, o los `watchPatterns` lo saltaron. Lo dice con el commit del último que sí hay.

SOLO LECTURA. Solo consultas GraphQL (`query`); `_graphql()` se niega a mandar una `mutation` antes
de abrir la conexión. No aprueba, no relanza, no toca variables: eso lo decide una persona.

LA CREDENCIAL. Un token de PROYECTO de Railway en el entorno (`RAILWAY_TOKEN`, o el nombre que digas
con `--token-env`), que va en la cabecera `Project-Access-Token` — NO como `Authorization: Bearer`,
que con un token de proyecto responde «Not Authorized» (medido en ADO el 4-sep: una sesión entera
perdida). El token nunca se imprime: todo lo que sale por pantalla pasa por `_tapar()`.

EL USER-AGENT. `curl/8.4.0`: el de urllib lo rechaza Cloudflare delante de la API con un 403 «error
code: 1010», que se lee igual que un fallo de credencial y no lo es (medido en ADO).

QUÉ ESTÁ MEDIDO Y QUÉ NO. La consulta de despliegues (`deployments(input: {serviceId,
environmentId})`, con `status`, `createdAt` y `meta`) es la que se usó en ADO contra la API real. Las
dos de descubrimiento (`projectToken` para proyecto y entorno; `project.services` para resolver
nombres) siguen la documentación pública de Railway y aquí solo se han ejercido contra un servidor
falso: si fallaran, `--proyecto`, `--entorno` e ids de servicio las evitan.

SALIDA: 0 todos en SUCCESS con el commit esperado · 1 alguno terminó mal, no llegó o no es el commit
· 2 uso, credencial o API · 3 nada falló pero alguno espera aprobación · 4 tiempo agotado.

Uso:
    RAILWAY_TOKEN=… python3 scripts/deploy/esperar_railway.py \\
        --commit "$(git rev-parse origin/main)" --servicio backend --servicio front-ventas
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ENDPOINT = "https://backboard.railway.com/graphql/v2"
USER_AGENT = "curl/8.4.0"

VERDE = {"SUCCESS", "SLEEPING"}
ROJO = {"FAILED", "CRASHED", "REMOVED", "SKIPPED"}
APROBACION = "NEEDS_APPROVAL"
NO_SUSTITUYEN = {"SKIPPED", "REMOVED", "FAILED", APROBACION}
# El resto (INITIALIZING, QUEUED, WAITING, BUILDING, DEPLOYING, REMOVING…) es «en curso». No se
# enumera a propósito: un estado nuevo de Railway debe ESPERARSE, no darse por bueno ni por malo.

RC_OK, RC_FALLO, RC_USO, RC_APROBACION, RC_TIEMPO = 0, 1, 2, 3, 4

Q_TOKEN = "query { projectToken { projectId environmentId } }"
Q_SERVICIOS = ("query($id: String!) { project(id: $id) { services { edges { node { id name } } } } }")
Q_DESPLIEGUES = ("query($input: DeploymentListInput!, $first: Int) { deployments(first: $first, "
                 "input: $input) { edges { node { id status createdAt meta } } } }")


class ErrorRailway(Exception):
    """La API no contestó lo que hacía falta. Siempre sale con rc=2."""


def _tapar(texto, token):
    """Nada que salga por pantalla lleva el token, ni aunque la API lo devuelva en un error."""
    s = str(texto)
    return s.replace(token, "«token»") if token else s


def endpoint_permitido(url):
    """El token solo viaja a Railway o a un servidor LOCAL de pruebas. Un endpoint configurable sin
    esta guarda sería la forma más corta de mandar la credencial a cualquier sitio."""
    if url == ENDPOINT:
        return True
    p = urllib.parse.urlsplit(url)
    return p.scheme in ("http", "https") and p.hostname in ("127.0.0.1", "localhost", "::1")


class Cliente:
    def __init__(self, token, endpoint=ENDPOINT, timeout=30):
        if not endpoint_permitido(endpoint):
            raise ErrorRailway(f"endpoint no permitido: {endpoint} (solo {ENDPOINT} o uno local de pruebas)")
        self.token, self.endpoint, self.timeout = token, endpoint, timeout

    def _graphql(self, documento, variables=None):
        # SOLO LECTURA, comprobado ANTES de abrir la conexión: este script no muta nada en Railway.
        if not documento.lstrip().startswith("query") or re.search(r"\bmutation\b", documento):
            raise ValueError("esperar_railway.py es de solo lectura: se negó a mandar algo que no es una `query`")
        cuerpo = json.dumps({"query": documento, "variables": variables or {}}).encode()
        req = urllib.request.Request(self.endpoint, data=cuerpo, method="POST", headers={
            "Content-Type": "application/json",
            "Project-Access-Token": self.token,
            "User-Agent": USER_AGENT,
        })
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                datos = json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            cuerpo_err = e.read().decode(errors="replace")[:300]
            if e.code in (401, 403):
                pista = (" Cloudflare rechazó el cliente («error code: 1010»), no la credencial."
                         if "1010" in cuerpo_err else
                         " ¿Es un token de PROYECTO de ese proyecto y entorno? Va en Project-Access-Token.")
                raise ErrorRailway(f"Railway respondió {e.code}.{pista}")
            raise ErrorRailway(f"Railway respondió {e.code}: {cuerpo_err}")
        except (urllib.error.URLError, OSError, ValueError) as e:
            raise ErrorRailway(f"no pude hablar con Railway ({e})")
        if datos.get("errors"):
            msgs = "; ".join(str(x.get("message", x)) for x in datos["errors"])
            if "Not Authorized" in msgs:
                msgs += " — ¿el token es de PROYECTO y de este proyecto/entorno?"
            raise ErrorRailway(f"la API devolvió errores: {msgs}")
        return datos.get("data") or {}

    def ambito(self):
        d = self._graphql(Q_TOKEN).get("projectToken") or {}
        if not d.get("projectId") or not d.get("environmentId"):
            raise ErrorRailway("el token no dice a qué proyecto y entorno pertenece: pasa --proyecto y --entorno")
        return d["projectId"], d["environmentId"]

    def servicios(self, proyecto):
        d = self._graphql(Q_SERVICIOS, {"id": proyecto}).get("project") or {}
        return {e["node"]["name"]: e["node"]["id"] for e in (d.get("services") or {}).get("edges", [])}

    def despliegues(self, servicio_id, entorno, cuantos=10):
        d = self._graphql(Q_DESPLIEGUES, {"first": cuantos,
                                          "input": {"serviceId": servicio_id, "environmentId": entorno}})
        return [e["node"] for e in (d.get("deployments") or {}).get("edges", [])]


# ── LA EVALUACIÓN (pura: recibe la lista de despliegues, no habla con nadie) ────────────────────────

def _commit(dep):
    meta = dep.get("meta")
    if isinstance(meta, str):
        try:
            meta = json.loads(meta)
        except ValueError:
            meta = None
    return ((meta or {}).get("commitHash") or "").lower()


def mismo_commit(a, b):
    """SHA completo o corto (≥7), a cualquiera de los dos lados."""
    a, b = (a or "").lower(), (b or "").lower()
    return len(a) >= 7 and len(b) >= 7 and (a.startswith(b) or b.startswith(a))


def evaluar(despliegues, commit):
    """→ dict con `estado` ∈ {OK, ROJO, APROBACION, EN_CURSO, SIN_DESPLIEGUE, SUPERADO} y el detalle."""
    deps = sorted(despliegues, key=lambda d: d.get("createdAt") or "", reverse=True)
    ultimo = deps[0] if deps else None
    propio = next((d for d in deps if mismo_commit(_commit(d), commit)), None)
    base = {"ultimo_commit": _commit(ultimo)[:7] if ultimo else "", "ultimo_estado": (ultimo or {}).get("status", "")}
    if not propio:
        return {"estado": "SIN_DESPLIEGUE", **base}
    det = {**base, "despliegue": propio.get("id", ""), "status": propio.get("status", ""),
           "creado": propio.get("createdAt", "")}
    # ¿HAY UNO MÁS NUEVO DE OTRO COMMIT QUE LO SUSTITUYE? No cuenta cualquiera: uno SKIPPED (los
    # watchPatterns lo saltaron), REMOVED (cancelado), FAILED (Railway deja corriendo el anterior) o
    # retenido en NEEDS_APPROVAL no ha sustituido al tuyo — el tuyo sigue siendo lo que corre.
    for d in deps[:deps.index(propio)]:
        if not mismo_commit(_commit(d), commit) and d.get("status") not in NO_SUSTITUYEN:
            return {"estado": "SUPERADO", **det, "nuevo_commit": _commit(d)[:7], "nuevo_estado": d.get("status", "")}
    st = propio.get("status", "")
    if st in VERDE:
        return {"estado": "OK", **det}
    if st in ROJO:
        return {"estado": "ROJO", **det}
    if st == APROBACION:
        return {"estado": "APROBACION", **det}
    return {"estado": "EN_CURSO", **det}


def explicar(ev, commit):
    c = commit[:7]
    e = ev["estado"]
    if e == "OK":
        return f"{ev['status']} · {c}"
    if e == "ROJO" and ev.get("status") == "SKIPPED":
        return (f"SKIPPED · Railway NO desplegó {c} en este servicio (sus watchPatterns no lo cubren): "
                "sigue corriendo el anterior")
    if e == "ROJO":
        return f"{ev['status']} · el despliegue de {c} terminó mal: mira su log de build/arranque en Railway"
    if e == "APROBACION":
        return (f"NEEDS_APPROVAL · {c} está RETENIDO en un approval gate y no avanzará solo: apruébalo en "
                "Railway o desactiva el gate (docs/distribucion/despliegue.md)")
    if e == "SUPERADO":
        return (f"{ev['status']} · hay un despliegue MÁS NUEVO de otro commit ({ev['nuevo_commit'] or '?'}, "
                f"{ev['nuevo_estado']}) que lo sustituye: {c} no es lo que corre. Espera ese commit")
    if e in ("SIN_DESPLIEGUE", "NO_LLEGO"):
        previo = (f"el último es {ev['ultimo_commit'] or '(sin commit)'} {ev['ultimo_estado']}"
                  if ev.get("ultimo_estado") else "este servicio no tiene ningún despliegue")
        if e == "NO_LLEGO":
            return (f"NO LLEGÓ · ningún despliegue de {c} ({previo}). ¿Le falta el trigger al servicio, o "
                    "sus watchPatterns lo saltaron? (checklist en docs/distribucion/despliegue.md)")
        return f"aún no hay despliegue de {c} ({previo})"
    if e == "TIEMPO":
        return f"{ev.get('status') or 'sin despliegue'} · se agotó el tiempo esperando a {c}"
    return f"{ev.get('status', '')} · en curso"


# ── EL BUCLE ────────────────────────────────────────────────────────────────────────────────────────

def esperar(cliente, servicios, entorno, commit, intervalo=10, tiempo_max=1200, gracia=300,
            esperar_aprobacion=False, reloj=time.monotonic, dormir=time.sleep, out=print):
    """servicios: {nombre: id}. → {nombre: evaluación final}."""
    inicio = reloj()
    pendientes = dict(servicios)
    final, visto = {}, {}
    fallos_red = 0
    while True:
        for nombre, sid in list(pendientes.items()):
            try:
                ev = evaluar(cliente.despliegues(sid, entorno), commit)
                fallos_red = 0
            except ErrorRailway:
                # UN CORTE DE RED NO ES UN VEREDICTO: durante una espera de veinte minutos, un fallo
                # suelto se reintenta. Tres seguidos ya no son un corte: se para y se dice.
                fallos_red += 1
                if fallos_red >= 3:
                    raise
                continue
            clave = (ev["estado"], ev.get("status"), ev.get("despliegue"))
            if visto.get(nombre) != clave:
                visto[nombre] = clave
                out(f"  {nombre:<20} {explicar(ev, commit)}")
            transcurrido = reloj() - inicio
            if ev["estado"] in ("OK", "ROJO", "SUPERADO") or (ev["estado"] == "APROBACION" and not esperar_aprobacion):
                final[nombre] = ev
                del pendientes[nombre]
            elif ev["estado"] == "SIN_DESPLIEGUE" and transcurrido >= gracia:
                final[nombre] = {**ev, "estado": "NO_LLEGO"}
                del pendientes[nombre]
        if not pendientes:
            return final
        if reloj() - inicio >= tiempo_max:
            for nombre in pendientes:
                final[nombre] = {"estado": "TIEMPO", "status": (visto.get(nombre) or (None, ""))[1]}
            return final
        dormir(intervalo)


def codigo_de_salida(final):
    estados = {ev["estado"] for ev in final.values()}
    if estados & {"ROJO", "SUPERADO", "NO_LLEGO"}:
        return RC_FALLO
    if "TIEMPO" in estados:
        return RC_TIEMPO
    if "APROBACION" in estados:
        return RC_APROBACION
    return RC_OK


def main(argv=None, env=None, reloj=time.monotonic, dormir=time.sleep, out=print):
    env = os.environ if env is None else env
    p = argparse.ArgumentParser(description="Espera a que Railway termine de desplegar un commit (solo lectura).")
    p.add_argument("--commit", required=True, help="SHA esperado (completo o corto, ≥7)")
    p.add_argument("--servicio", action="append", required=True, help="nombre o id del servicio (repetible)")
    p.add_argument("--proyecto", help="id del proyecto (por defecto: el del token)")
    p.add_argument("--entorno", help="id del entorno (por defecto: el del token)")
    p.add_argument("--intervalo", type=float, default=10, help="segundos entre consultas (10)")
    p.add_argument("--tiempo-max", type=float, default=1200, help="segundos máximos esperando (1200)")
    p.add_argument("--gracia", type=float, default=300,
                   help="segundos que se espera a que APAREZCA un despliegue del commit (300)")
    p.add_argument("--esperar-aprobacion", action="store_true",
                   help="seguir esperando un NEEDS_APPROVAL en vez de avisar y parar")
    p.add_argument("--token-env", default="RAILWAY_TOKEN", help="variable de entorno con el token de proyecto")
    p.add_argument("--json", action="store_true", help="el resultado final en JSON por stdout")
    a = p.parse_args(argv)

    token = env.get(a.token_env, "")
    di = lambda s: out(_tapar(s, token))  # noqa: E731 — TODO lo que se imprime pasa por aquí
    if not token:
        di(f"✗ falta el token de PROYECTO de Railway en la variable {a.token_env} (Project → Settings → "
           "Tokens). Se lee del entorno y no se imprime nunca.")
        return RC_USO
    if not re.fullmatch(r"[0-9a-fA-F]{7,40}", a.commit):
        di(f"✗ --commit {a.commit!r} no parece un SHA (7 a 40 caracteres hexadecimales)")
        return RC_USO
    try:
        cli = Cliente(token, env.get("RAILWAY_GRAPHQL_URL") or ENDPOINT)
        proyecto, entorno = a.proyecto, a.entorno
        if not (proyecto and entorno):
            p_tok, e_tok = cli.ambito()
            proyecto, entorno = proyecto or p_tok, entorno or e_tok
        por_nombre = cli.servicios(proyecto)
        ids = set(por_nombre.values())
        servicios = {}
        for s in a.servicio:
            if s in por_nombre:
                servicios[s] = por_nombre[s]
            elif s in ids:
                servicios[next(n for n, i in por_nombre.items() if i == s)] = s
            else:
                di(f"✗ el servicio {s!r} no está en el proyecto. Hay: {', '.join(sorted(por_nombre)) or '(ninguno)'}")
                return RC_USO
        di(f"→ esperando a Railway · commit {a.commit[:7]} · {len(servicios)} servicio(s) · entorno "
           f"{entorno[:8]}… · cada {a.intervalo:g} s, máx. {a.tiempo_max:g} s")
        final = esperar(cli, servicios, entorno, a.commit, a.intervalo, a.tiempo_max, a.gracia,
                        a.esperar_aprobacion, reloj, dormir, di)
    except ErrorRailway as e:
        di(f"✗ {e}")
        return RC_USO

    rc = codigo_de_salida(final)
    marca = {"OK": "✓", "APROBACION": "⚠", "TIEMPO": "…"}
    di("══ resultado ══")
    for nombre in servicios:
        ev = final[nombre]
        di(f"  {marca.get(ev['estado'], '✗')} {nombre:<20} {explicar(ev, a.commit)}")
    if a.json:
        di(json.dumps({"commit": a.commit, "rc": rc, "servicios": final}, ensure_ascii=False))
    return rc


if __name__ == "__main__":
    sys.exit(main())
