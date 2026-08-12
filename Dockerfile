# syntax=docker/dockerfile:1
# Backend del BOS de un cliente — cáscara de repo-fino.
#
# Cuelga de la imagen base versionada del Molde y solo aporta el config del cliente. `build.py`
# ensambla, DENTRO de esta imagen, las extensiones de las capacidades ACTIVAS de ese config (slimming
# por cliente). El repo de cliente = este Dockerfile + config/<cliente>.bos.json. Sin motor y sin las
# capacidades en el checkout: eso vive en la imagen base.
#
# Build:  docker build --build-arg MOLDE_VERSION=X.Y.Z -t <cliente>-bos .

# SIN DEFAULT, Y ES DELIBERADO. Aquí ponía `ARG MOLDE_VERSION=0.1.0`, y ese default era UNA TRAMPA
# CARGADA: la 0.1.0 es la imagen PODRIDA (sin gate de secretos → arranca SIN secretos, Directus se
# inventa un SECRET aleatorio y sirve un health 200 que MIENTE). Quien construyera sin pasar la
# versión se llevaba esa imagen EN SILENCIO y con un deploy verde.
#
# Sin default, un build sin `--build-arg MOLDE_VERSION` no cae en la podrida: FALLA. El tag queda
# vacío (`molde-base:`) y docker lo rechaza — MEDIDO, no supuesto:
#     ERROR: invalid reference format
# Un default que apunta a un artefacto podrido es peor que no tener default. Ruidoso > silencioso.
ARG MOLDE_VERSION
FROM ghcr.io/horusscale/molde-base:${MOLDE_VERSION}
USER root

# El config del cliente (único aporte de este repo). Renombra el fichero al id de tu cliente y ajusta
# las DOS rutas de abajo — tienen que coincidir.
COPY config/cliente.bos.json /molde/config/cliente.bos.json

# Ensambla SOLO las extensiones de las capacidades activas y las hornea en la imagen (la plataforma
# de despliegue no monta disco → viajan dentro). El schema NO se hornea: se aplica en el deploy.
RUN python3 /molde/scripts/build.py --config config/cliente.bos.json \
 && cp -r /molde/extensions/. /directus/extensions/ \
 && chown -R node:node /directus/extensions /molde
# ↑ /molde se re-chownea porque este RUN corre como root y deja out/ y extensions/ con dueño root: el
# apply en runtime corre como `node` y necesita reescribir /molde/out.

USER node
