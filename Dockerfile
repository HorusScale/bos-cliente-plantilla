# syntax=docker/dockerfile:1
# Cáscara de repo-fino de cliente (la produce el PRINCIPADO DE PROYECTO, no el Molde).
#
# Cuelga de la imagen base versionada del Molde y solo aporta el config del cliente. build.py ensambla
# las extensiones de las capacidades ACTIVAS de ese config dentro de esta imagen (slimming por cliente).
# El repo de cliente = este Dockerfile + config/cliente.bos.json (+ sus fronts, ver M6). Sin motor,
# sin las capacidades en el checkout: eso vive en la imagen base.
#
# Build:  docker build --build-arg MOLDE_VERSION=X.Y.Z -t cliente-bos .

# SIN DEFAULT, Y ES DELIBERADO. Aquí ponía `ARG MOLDE_VERSION=0.1.0`, y ese default era UNA TRAMPA
# CARGADA: la 0.1.0 es la imagen PODRIDA (pre-M5, sin gate de secretos → arranca SIN secretos, Directus
# se inventa un SECRET aleatorio y sirve un health 200 que MIENTE). Quien construyera sin pasar la
# versión se llevaba esa imagen EN SILENCIO y con un deploy verde.
#
# Sin default, un build sin `--build-arg MOLDE_VERSION` no cae en la podrida: FALLA. El tag queda vacío
# (`molde-base:`) y docker lo rechaza — MEDIDO, no supuesto:
#     ERROR: invalid reference format
# Un default que apunta a un artefacto podrido es peor que no tener default. Ruidoso > silencioso.
#
# En la práctica nadie lo pasa a mano: `make_client_repo.py` escribe aquí la versión REAL del Molde,
# derivada de package.json (la fuente de verdad) — la MISMA que ancla el core de los fronts. UNA ANCLA.
ARG MOLDE_VERSION
FROM ghcr.io/horusscale/molde-base:${MOLDE_VERSION}
USER root

# TODO config que llega A ESTE Dockerfile ya pasó por `make_client_repo.materializar()`, que pela
# `team[]` (nunca passwords en claro en un artefacto publicable) Y valida `agenda-publica` contra
# el ORIGINAL, antes de pelar (ticket 8ce3da2cc305). `build.py`, corriendo DENTRO de esta imagen,
# NO puede repetir esa validación: vería `team[]` vacío SIEMPRE y rechazaría cualquier
# agenda-publica activa, sana o no -- el dato que la contestaría ya no está. Esta bandera se lo
# dice: "esa pregunta ya se contestó, con el dato real, antes de que llegaras". Puesta AQUÍ (ENV,
# no CLI en el RUN de abajo) para que cubra CUALQUIER invocación de build.py dentro del
# contenedor -- este build, el apply-on-boot de entrypoint.sh, y el `docker exec` de
# adapters/local.py -- sin tener que repetir el flag en cada uno de los tres sitios.
ENV BOS_TEAM_PELADO=1

# El config del cliente (único aporte del repo de cliente). Ajusta el nombre al de tu cliente.
COPY config/cliente.bos.json /molde/config/cliente.bos.json

# Ensambla SOLO las extensiones de las capacidades activas y las hornea en la imagen (Railway no monta
# disco → viajan dentro). El schema NO se hornea: se aplica en deploy (M4).
RUN python3 /molde/scripts/build.py --config config/cliente.bos.json \
 && cp -r /molde/extensions/. /directus/extensions/ \
 && chown -R node:node /directus/extensions /molde
# ↑ /molde se re-chownea porque este RUN corre como root y deja out/ y extensions/ con dueño
# root: el apply en runtime (M4) corre como `node` y necesita reescribir /molde/out.

USER node
