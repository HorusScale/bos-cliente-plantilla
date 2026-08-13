# Plantilla de repo de cliente — BOS

Punto de partida del repo de **un cliente**. Se usa con el botón **«Use this template»** de GitHub:
crea un repo nuevo con estos ficheros y sin el historial de esta plantilla.

> **Cómo se llama el repo que crees: `<cliente>-bos`.** Sin sufijo de capa: aquí no vive solo el
> backend, sino la definición del sistema del cliente y las recetas de sus dos imágenes — y en la
> forma a la que vamos, será pura definición del negocio. Un nombre que promete menos de lo que hay
> envejece mal.

Lo que hay aquí es **la cáscara**: el config del cliente y las recetas para construir sus imágenes.
El producto —el motor, las capacidades, el core de las aplicaciones— **no vive aquí**: viaja en la
imagen base y en el paquete del core, ambos versionados. Por eso este repo es pequeño y se entiende
de una sentada.

## Qué es cada fichero

| Fichero | Qué es |
|---|---|
| `Dockerfile` | **Backend.** Cuelga de `ghcr.io/horusscale/molde-base:<versión>` y solo aporta el config. Al construir, ensambla dentro de la imagen las extensiones de las capacidades **activas** de ese config. |
| `Dockerfile.front` | **Las aplicaciones (fronts).** Capa Nuxt fina sobre `@horusscale/horus-bos-core`: UNA sola imagen sirve TODAS las apps del cliente — cada app se elige en el arranque del contenedor con `NUXT_PUBLIC_BOS_APP`, no en el build. ⚠ Necesita el árbol `fronts/app/` que **no viene aquí** — ver «Qué NO viene». |
| `config/cliente.bos.json` | **El flujo del cliente**: zonas, roles, equipo, capacidades y pipelines. Es *datos*, no código. Renómbralo al id de tu cliente. |
| `README.md` | Esto. |

## Los tres pasos

1. **Escribir el config.** Parte de `config/cliente.bos.json`, renómbralo (`config/<cliente>.bos.json`)
   y ajusta **las dos rutas** que lo nombran dentro del `Dockerfile` — tienen que coincidir.
   Las notas `_*` del propio fichero explican cada bloque y avisan de las trampas medidas.

2. **Construir el backend**, fijando la versión del Molde:

   ```bash
   docker build --build-arg MOLDE_VERSION=0.42.0 -t <cliente>-bos .
   ```

   > **`MOLDE_VERSION` no tiene valor por defecto, y es deliberado.** Un build sin `--build-arg`
   > no cae en una versión antigua: **falla en seco** (`ERROR: invalid reference format`). Un
   > default que apunta a un artefacto viejo es peor que no tener default.

3. **Desplegar** esa imagen junto a un Postgres. El **schema se aplica en el deploy**, no se hornea
   en la imagen. Los secretos los inyecta la plataforma por entorno: la imagen es *secret-free* y
   debe seguir siéndolo.

## Qué NO viene, y por qué se dice de frente

- **`fronts/`.** `Dockerfile.front` está aquí porque es la receta que se usa por cliente, pero el
  árbol `fronts/app/` que necesita **hoy lo genera Horus** para cada cliente; no se autoservicio
  todavía. Sin ese árbol, ese Dockerfile no tiene qué construir. Pídelo cuando llegues a ese paso.
- **Nada del producto**: ni `core/`, ni `capabilities/`, ni `extensions/`, ni `scripts/`. Todo eso
  vive en la imagen base (`molde-base`) y en el paquete `@horusscale/horus-bos-core`. Si algo de eso
  aparece en el repo de un cliente, es un error de frontera: el cliente deja de recibir un producto
  versionado y pasa a tener una copia que diverge.
- **Secretos.** Este repo no lleva ni una credencial, y no debe llevarla nunca: lo que se commitea
  aquí queda en el historial de git para siempre.

## Dos avisos que cuestan caro si se aprenden tarde

**El `password` del equipo.** En `team[]` va **en claro**, y si lo omites el build siembra uno por
defecto **sin avisar**: el usuario nace con una clave conocida. Cámbialo antes de construir. Lo sano
es aplicar el equipo desde una copia local y dejar `team` vacío en lo que se versiona.

**Las apps y su lanzador van juntos.** En cuanto declares `apps[]`, el build **exige** `launcher_url`
y se niega a construir sin ella. No es capricho: la marca del shell enlazaría a un botón muerto.

## Y si el build falla

Los guards del Molde fallan **ruidosamente y con instrucciones**: leen el mensaje entero antes de
tocar nada. Los que más se cruzan al empezar:

- `SUPERFICIE HUÉRFANA` — encendiste una capacidad cuyas pantallas piden una zona que tu config no
  declara. Añade la zona o apaga la capacidad.
- `ZONA MUDA` — le diste a un rol una zona que ninguna pantalla de esa app reconoce: quien la tenga
  entraría a un sistema vacío.
- `invalid reference format` — construiste sin `--build-arg MOLDE_VERSION` (ver paso 2).

---

*Procedimiento completo de implementación, versiones publicadas y guía del consultor: pídelos a
Horus Scale. Este repo es la puerta de entrada, no el manual entero.*
