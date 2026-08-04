---
name: implementar
description: Poner en marcha este BOS por primera vez — proyecto y base de datos en la plataforma de despliegue, secretos, credencial del registro, el servicio del backend y uno por aplicación, primera publicación y checklist de entrega. Detecta si las aplicaciones todavía no existen en el repo y lo dice en vez de fingir el paso. Úsala cuando se pida "implementar", "montar el sistema", "primera puesta en marcha", "desplegar por primera vez" o "poner esto en producción".
instrucciones_para: "0.20.3"
---

<!-- `instrucciones_para` es el SELLO: la versión de la plataforma que estas instrucciones describen.
     Lo compara la skill `actualizar` tras sincronizar, para avisar si se han separado. -->

# Poner en marcha este BOS por primera vez

**Antes de empezar, esto ya tiene que estar hecho:** la definición del cliente escrita en
`config/<cliente>.bos.json` y el repo creado a partir de la plantilla. Si aún no, ese es el paso
previo — no sigas.

Al final de esta guía hay un sistema **desplegado**. Verificado lo hace una persona mirando la
pantalla, y ese paso está aquí abajo con su nombre.

---

## Paso 0 · Mira qué hay en el repo antes de prometer nada

```bash
ls -d fronts/app/ 2>/dev/null || echo "SIN fronts/app"
```

**Si no hay `fronts/app`, léelo entero antes de continuar.** No es un error tuyo ni un fallo del
repo: esta plantilla no trae la aplicación. Hoy se genera **por cliente** y no es autoservicio.

> **Una sola cáscara sirve TODAS las apps del cliente — no busques una carpeta por app.** Antes
> había un directorio de front por aplicación; hoy hay UNA cáscara (`fronts/app`) que arranca
> distinta según la variable de entorno con la que se ejecute (ver paso 5). Contar carpetas ya no
> dice cuántas aplicaciones tiene el cliente — eso lo dice `config/<cliente>.bos.json`.

Consecuencia práctica, dicha de frente:

- **El backend sí se puede montar entero** con lo que hay. Ese trabajo no está bloqueado.
- **La aplicación no**, y no hay forma de improvisarla: sin ese árbol, el `Dockerfile.front` no
  tiene qué construir.

Así que el resultado honesto de esta guía, en un repo recién nacido, es **un backend en marcha y una
solicitud bien formada** para lo que falta. Escríbela y entrégala:

```
QUÉ HACE FALTA
  Las aplicaciones (fronts) para este cliente.

PARA QUÉ CLIENTE Y CON QUÉ DEFINICIÓN
  Identificador del cliente y ruta de su fichero de definición en este repo.

QUÉ APLICACIONES
  Una por cada flujo que la definición declara, más las transversales que el cliente vaya a usar.
  Sácalas de la definición y enuméralas por su identificador; no las inventes.

DÓNDE VA A CORRER
  El proyecto de despliegue ya creado (enlázalo) y a qué dirección responde el backend.

PARA CUÁNDO
  Qué queda bloqueado sin ellas y con qué fecha.
```

> **No lo llames «pendiente menor».** Sin aplicaciones el cliente no tiene por dónde entrar: el
> backend sirve datos, no pantallas. Un backend solo es media entrega, y decirlo claro ahora es más
> barato que descubrirlo el día de la demostración.

---

## Paso 1 · Proyecto y base de datos

En la plataforma de despliegue del **cliente** (no en la de nadie más): crea un proyecto y, dentro,
una base de datos **PostgreSQL**.

> **Postgres no es una preferencia, es un requisito.** El sistema toma un bloqueo propio de Postgres
> para ordenar lo que ocurre. Con otro motor **no falla al desplegar**: falla más tarde, en caliente,
> la primera vez que alguien hace algo — y ahí ya nadie lo relaciona con esta decisión.

> **El plan de pago importa, y su síntoma es traicionero:** en los planes gratuitos hay un tope de
> servicios, y los que no caben **no avisan** — simplemente no arrancan, sin un error que apunte a la
> causa. Este sistema son varios servicios (uno de backend, uno por aplicación, más la base de
> datos). Confírmalo antes de empezar a crear.

---

## Paso 2 · Los secretos, generados aquí y ahora

El sistema exige tres cosas para arrancar sano, y **si faltan, el contenedor muere con un mensaje que
las nombra** — no arranca a medias:

| Variable | Qué es |
|---|---|
| `KEY` | Clave de firma. **Fija y única por instancia.** |
| `SECRET` | Clave de firma. **Fija y única por instancia.** |
| `DATABASE_URL` | Conexión a la base de datos. *(La plataforma suele ofrecerla ya resuelta al enlazar la base; si no, existe la alternativa de declararla por partes.)* |

Genera las dos claves **ahora**, con lo que tengas a mano:

```bash
echo "KEY=$(openssl rand -hex 32)"
echo "SECRET=$(openssl rand -hex 32)"
# sin openssl:
python3 -c "import secrets; print('KEY=' + secrets.token_hex(32)); print('SECRET=' + secrets.token_hex(32))"
```

> **Fijas para siempre, y de esta instancia.** Si cambian, todas las sesiones abiertas mueren. Si se
> reutilizan entre clientes, dos sistemas distintos firman con la misma llave. Genera un par nuevo por
> instancia y guárdalo **en el gestor de secretos de la plataforma**, nunca en este repo.

Y para que el sistema pueda configurarse solo al desplegar, hacen falta también las credenciales de
la cuenta administradora inicial:

| Variable | Qué es |
|---|---|
| `ADMIN_EMAIL` | Correo de la cuenta administradora inicial. |
| `ADMIN_PASSWORD` | Su contraseña. **Genera una fuerte; no la reutilices.** |

---

## Paso 3 · La credencial del registro

Las piezas versionadas del sistema se descargan de un registro privado por defecto. Hace falta **un
token de lectura de paquetes** del cliente, guardado como variable del proyecto.

**El nombre de la variable no es libre.** Tiene que ser exactamente el que las recetas de construcción
declaran, o la plataforma no lo pasará al construir y el fallo será un error de descarga que no
menciona ninguna credencial:

```bash
# El nombre exacto, sacado de la propia receta en vez de escrito de memoria:
grep -n '^ARG.*TOKEN' Dockerfile.front
```

- Se escribe **en el gestor de secretos de la plataforma**, nunca en un fichero del repo. Lo que se
  commitea aquí queda en el historial para siempre.
- Muchas plataformas **dejan escribir un secreto pero no leerlo de vuelta**. Es lo deseable: se opera
  sin ver la credencial.
- La pieza del backend puede ser pública o no según el momento; **la de las aplicaciones exige token
  siempre**, incluso cuando es pública. Así que la credencial hace falta igual: no te fíes de que una
  descarga suelta funcione sin ella.

---

## Paso 4 · El servicio del backend

- **Origen:** este repo. **Receta:** el `Dockerfile` de la raíz.
- **Variables de construcción:** `MOLDE_VERSION` con la versión a fijar. **No tiene valor por
  defecto**: sin ella el build falla en seco, y es deliberado.
- **Variables de ejecución:** las del paso 2 (`KEY`, `SECRET`, conexión a la base, `ADMIN_EMAIL`,
  `ADMIN_PASSWORD`).
- **Enlaza la base de datos** al servicio para que la conexión se resuelva sola.

> **Lo que configura el sistema se ejecuta una vez por despliegue, no una vez por copia.** Si la
> plataforma tiene un hueco para «comando de publicación» (el que corre entre construir y arrancar),
> ahí va. Si no lo tiene, existe una variable de respaldo que lo dispara al arrancar; búscala en la
> documentación de la versión que estés fijando antes de inventar un apaño.

---

## Paso 5 · UNA imagen, un servicio por aplicación

Solo si el paso 0 encontró `fronts/app`. La forma cambió: **se construye UNA imagen** (no una por
aplicación) y **se arrancan N servicios desde esa misma imagen**, cada uno con distinta variable de
entorno diciéndole qué aplicación servir.

**Qué aplicaciones existen** — no se cuentan carpetas (siempre hay una sola): se leen del config.
El lanzador siempre está; súmale cada flujo/transversal que el cliente vaya a usar:

```bash
python3 -c "
import json
c = json.load(open('config/<cliente>.bos.json'))
apps = ['lanzador'] + [a['id'] for a in c.get('apps', []) if a.get('kind') in ('pipeline','transversal')]
print('\n'.join(apps))
"
```

**La imagen (una sola vez):**

- **Receta:** `Dockerfile.front`.
- **Variable de construcción:** `BOS_CONFIG` = ruta del fichero de definición · más la credencial
  del paso 3. `FRONT_ID` **ya no existe** — no lo declares.
- Etiqueta la imagen del cliente y no la reconstruyas por aplicación: las N que vienen abajo
  arrancan todas de esta misma imagen.

**Los servicios (uno por aplicación, todos desde la imagen de arriba):**

- **Variable de ejecución que identifica la app**: `NUXT_PUBLIC_BOS_APP` = el identificador exacto
  (uno de los que listó el paso anterior). **Obligatoria — sin ella el contenedor no arranca**, y es
  deliberado: un valor por defecto serviría otra aplicación en silencio, y un arranque que falla se
  ve mientras que una pantalla equivocada no.
- **Variable de ejecución que apunta al backend**: la dirección pública del backend, para que la
  aplicación sepa a quién preguntar. El nombre exacto, sacado de la receta:

```bash
grep -n 'ENV .*URL' Dockerfile.front
```

> **La imagen lleva la definición horneada dentro; la aplicación activa se elige AL ARRANCAR.** El
> config se hornea en el build (por eso cada cambio de definición exige reconstruir la imagen, y por
> eso la imagen de un cliente no sirve para otro) — pero QUÉ aplicación sirve cada contenedor se
> decide con `NUXT_PUBLIC_BOS_APP` en el arranque, no en el build.

### Dos vías, y cuál es la fiable

- **Si tienes credencial de la plataforma con permiso para crear servicios**, hazlo por su API o su
  herramienta de línea de comandos: es más rápido y deja rastro. Comprueba primero que la credencial
  funciona con una lectura (listar los proyectos) antes de crear nada.
- **Si no la tienes**, hazlo por la interfaz, servicio por servicio, con esta misma lista delante.
  **Esta vía siempre funciona**, así que si la automática se atasca no pelees con ella: cambia.

En cualquiera de las dos, al terminar **enumera lo creado y compáralo con lo que debía existir**:
un servicio de backend, uno por aplicación listada arriba (todos desde la MISMA imagen), una base de
datos. Un servicio de menos no avisa: simplemente falta una pantalla que nadie abrió todavía.

---

## Paso 6 · Primera publicación

Empuja y espera a que **todos** los servicios terminen en verde:

```bash
git add -A && git commit -m "Primera puesta en marcha" && git push
```

- **Un verde parcial no es un verde.** Anota cuántos servicios debían quedar en verde y cuéntalos.
- La primera construcción tarda más que las siguientes: descarga todo por primera vez.
- Si un build falla, **lee el mensaje entero antes de tocar nada**: estos errores vienen con
  instrucciones y suelen nombrar la variable que falta.

---

## Paso 7 · La comprobación en pantalla — esta parte es del humano

**Esta skill no puede hacer este paso y no lo simula.** Verde significa que arrancó, no que sirva.

- [ ] **Entrar con un usuario de cada rol**, no solo con uno.
- [ ] **Recorrer el flujo entero** con un caso real: darlo de alta, moverlo por sus fases, cerrarlo.
- [ ] **Leer las palabras**: los rótulos tienen que ser los del cliente, los que usa su equipo.
- [ ] **Mirar la marca**: logotipo, nombre y colores correctos, y ninguna referencia a quien lo
      construyó.
- [ ] **Probar desde el móvil**, no solo desde el escritorio.

Mientras ese checklist no esté hecho, el sistema está **desplegado, no verificado**. Dilo con esas
palabras: no son sinónimos, y confundirlos es cómo se entrega algo que nadie miró.

---

## Paso 8 · Entregar

Lo que queda no es técnico y **es del cliente**:

- **Las altas de personas se hacen desde la propia aplicación de administración**, no editando la
  definición. Enséñaselo a quien vaya a hacerlo: es suyo a partir de ahora.
- **Cambia la contraseña de la cuenta administradora inicial** y entrégala por un canal seguro.
- Deja dicho **qué versión quedó fijada** y cómo se sube (hay una skill `actualizar` en este mismo
  repo).
- Y **qué pedir cuando quieran algo nuevo**: hay una skill `cambios` que tría el pedido y dice si se
  resuelve aquí o hay que solicitarlo.

---

## Si algo no cuadra, para

- **Faltan las aplicaciones** (paso 0): monta el backend y entrega la solicitud. No lo disimules.
- **El build muere sin nombrar una credencial**: casi siempre es el nombre de la variable del token,
  que tiene que coincidir **exactamente** con el declarado en la receta (paso 3).
- **El contenedor arranca y muere**: lee el mensaje — nombra la variable de arranque que falta.
- **Un servicio no aparece**: comprueba el tope de servicios del plan (paso 1). No da error.

En todos los casos: informa de **qué se creó, qué falta y qué se intentó**, y no dejes servicios a
medias sin decirlo.
