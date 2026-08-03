---
name: actualizar
description: Subir este BOS a una versión más nueva de la plataforma. Consulta al registro cuál es la última publicada, mueve LAS DOS ANCLAS de versión que tiene el repo (la imagen del backend y el core de cada aplicación) y se niega a seguir si solo puede mover una. Úsala cuando se pida "actualizar el sistema", "subir de versión", "pasar a la última", "hay una versión nueva" o "actualizar la plataforma".
---

# Actualizar este BOS

Este repo **fija** la versión de la plataforma sobre la que corre. Actualizar no es tocar un número:
es mover **dos anclas a la vez** y comprobar que el resultado arranca.

> **La regla que gobierna todo lo demás: las dos anclas se mueven juntas o no se mueve ninguna.**
> Mover una sola no rompe el build — y eso es justo lo peligroso: despliega, arranca, y el sistema
> corre con dos mitades de versiones distintas. Se descubre horas después y por síntomas que no
> apuntan a la causa.

---

## Paso 1 · Preguntar al registro cuál es la última versión

**Nunca de un README, de una nota ni de una lista mantenida a mano**: esas envejecen y nadie se
entera. La verdad está en el registro donde se publican las imágenes.

Primero, saca del propio repo la imagen que ya usa (no la escribas de memoria):

```bash
IMAGEN=$(grep -oE 'ghcr\.io/[^:[:space:]]+' Dockerfile | head -1)
echo "$IMAGEN"          # p. ej. ghcr.io/<organización>/<imagen-base>
REPO_IMG=${IMAGEN#ghcr.io/}
```

Pide un token de lectura para ESA imagen y lista sus etiquetas:

```bash
TOKEN=$(curl -s "https://ghcr.io/token?scope=repository:${REPO_IMG}:pull&service=ghcr.io" \
        | python3 -c 'import sys,json; print(json.load(sys.stdin)["token"])')

curl -s -H "Authorization: Bearer $TOKEN" "https://ghcr.io/v2/${REPO_IMG}/tags/list" \
  | python3 -c '
import sys, json
tags = [t for t in json.load(sys.stdin)["tags"] if t[:1].isdigit()]
tags.sort(key=lambda s: [int(p) for p in s.split(".")])
print("\n".join(tags[-8:]))'
```

- Si la imagen es **privada**, ese token anónimo devuelve 401: exporta primero el token de lectura
  del proyecto y pásalo (`-u USUARIO:$TOKEN_LECTURA` al pedir el token, o el flujo que use tu
  plataforma). **No pegues el token en ningún fichero de este repo.**
- Elige una versión **concreta y publicada**. Nada de `latest`: la gracia de este repo es que la
  versión esté fijada y sea reproducible.

---

## Paso 2 · Las DOS anclas

Localízalas **antes de editar nada** y enséñalas juntas:

```bash
echo "── ANCLA 1: imagen del backend ──"
# Solo las líneas de CÓDIGO: el Dockerfile explica esta variable en varios comentarios, y editar
# un comentario creyendo que es el ancla deja el repo igual y a ti convencido de lo contrario.
grep -nE '^[[:space:]]*(ARG|FROM)[[:space:]].*MOLDE_VERSION' Dockerfile

echo "── ANCLA 2: core de cada aplicación ──"
grep -rn 'horus-bos-core' fronts/*/package.json 2>/dev/null || echo "(sin fronts/ en este repo)"
```

**ANCLA 1 — la imagen del backend.** No lleva número dentro del `Dockerfile`: se pasa al construir
(`--build-arg MOLDE_VERSION=X.Y.Z`), así que el número vive **donde se dispara el build** — la
variable del servicio en tu plataforma de despliegue, o el comando si construyes a mano. Ahí es donde
hay que cambiarlo.

**ANCLA 2 — el core de cada aplicación.** Un rango `^X.Y.Z` en el `package.json` de **cada** carpeta
de `fronts/`, más el lockfile.

> ### Por qué mover solo la imagen no basta, con números
> El rango `^0.20.3` admite `0.20.4`, `0.20.9`… **pero no `0.21.0`**: cuando el primer número es `0`,
> el acento circunflejo fija también el segundo. O sea:
>
> | Vas de → a | ¿La aplicación se mueve sola? |
> |---|---|
> | `0.20.3` → `0.20.4` | Sí. El rango ya lo admitía. |
> | `0.20.3` → `0.21.0` | **No.** El backend sube y las aplicaciones se quedan atrás, en silencio. |
>
> Ese segundo caso es el que muerde: no falla nada, y el sistema queda partido en dos versiones.

### La guarda: dos o ninguna

Antes de tocar un solo fichero, responde estas tres. Si alguna falla, **para y avísalo**; no dejes el
repo a medio mover:

1. **¿Aparece el ancla 1?** Si `grep MOLDE_VERSION Dockerfile` no devuelve nada, este repo no tiene
   la forma que esta skill supone: no sigas a ciegas.
2. **¿Puedes cambiar el ancla 1 de verdad?** No basta con verla: hace falta poder editar la variable
   donde se dispara el build. Si no tienes ese acceso, **no toques el ancla 2**: dejarías las
   aplicaciones pidiendo un core que el backend no acompaña.
3. **¿Cuántas aplicaciones hay en `fronts/`?** Se mueven **todas**. Mover unas sí y otras no es la
   misma avería, más difícil de ver.

> **Un repo SIN carpeta `fronts/` no es un caso de «solo una ancla».** Es un repo al que todavía no
> le han generado las aplicaciones: entonces la única ancla que existe es la 1, y moverla es
> correcto y completo. Dilo explícitamente al informar, para que nadie lo confunda con un cambio a
> medias.

### Hacer el cambio

```bash
# Ancla 2, en todas las aplicaciones a la vez (sustituye X.Y.Z por la versión elegida)
sed -i 's|"@horusscale/horus-bos-core": *"\^[0-9.]*"|"@horusscale/horus-bos-core": "^X.Y.Z"|' \
  fronts/*/package.json

grep -rn 'horus-bos-core' fronts/*/package.json     # comprobar que TODAS quedaron iguales

npm install                                          # actualiza el lockfile
```

- `npm install` necesita credencial para el paquete del core (el registro la exige incluso para
  paquetes públicos). Usa la variable de entorno que ya emplea tu build; **no crees un fichero de
  credenciales dentro del repo**.
- El **lockfile entra en el commit**. Si no, cada build resuelve por su cuenta y dejan de ser
  reproducibles.
- Y cambia el ancla 1 donde toque: la variable del servicio de tu plataforma.

---

## Paso 3 · Empujar y esperar los verdes

```bash
git add -A && git commit -m "Actualizar plataforma a X.Y.Z (imagen y aplicaciones)"
git push
```

Espera a que **todos** los servicios terminen su despliegue y queden en verde: el backend y **cada**
aplicación. Un verde parcial no es un verde — si una aplicación falla y las demás no, es señal
típica de que una de las anclas se quedó atrás.

Si un build falla, lee el mensaje entero antes de tocar nada: estos errores vienen con instrucciones.

---

## Paso 4 · La comprobación en pantalla — esta parte es del humano

**Esta skill no puede hacer este paso y no lo simula.** Que los despliegues estén verdes solo dice
que el sistema arrancó, no que sirva. Entrega este checklist a quien pueda mirar la pantalla:

- [ ] **Entrar con un usuario de cada rol.** No basta con uno: cada rol abre un conjunto distinto de
      pantallas, y lo que se rompe suele romperse en uno solo.
- [ ] **Recorrer el flujo entero** de principio a fin con un caso real: darlo de alta, moverlo por
      todas sus fases hasta cerrarlo.
- [ ] **Leer las palabras.** Los rótulos tienen que ser los del cliente —los que usa su equipo al
      hablar—, no términos genéricos ni de otro proyecto.
- [ ] **Mirar la marca**: logotipo, nombre y colores correctos, y ninguna referencia a la
      organización que construyó el sistema.
- [ ] **Comprobar que los datos siguen ahí** y se ven donde se veían.

Mientras ese checklist no esté hecho, la actualización está **desplegada, no verificada**. Dilo con
esas palabras al informar: no son sinónimos, y confundirlos es cómo se dan por buenas las
actualizaciones que no lo estaban.

---

## Si algo no cuadra, para

Esta skill prefiere detenerse a dejar el repo a medias. Casos en los que **no se sigue**:

- Solo se puede mover una de las dos anclas (paso 2).
- La versión elegida no aparece en el listado del registro — no existe o no está publicada.
- El repo no tiene la forma que esta skill supone (falta el `Dockerfile`, o no aparece el ancla 1).

En todos ellos: informa de **qué se encontró, qué falta y qué se habría cambiado**, y deja el repo
tal y como estaba.
