---
name: cambios
description: Triar un pedido del cliente y decidir qué clase de cambio es — definición (se hace aquí y ahora), pieza nueva o modificación de algo que ya trae (se solicitan, no se improvisan). Traza la frontera con ejemplos y produce la solicitud bien formada cuando no es autoservicio. Úsala cuando llegue "¿podemos hacer que…?", "el cliente quiere…", "necesitamos añadir…", "¿esto se puede cambiar?" o cualquier pedido que no sepas si toca la definición o el producto.
instrucciones_para: "0.20.3"
---

<!-- `instrucciones_para` es el SELLO: la versión de la plataforma que estas instrucciones describen.
     Lo compara la skill `actualizar` tras sincronizar, para avisar si se han separado. -->

# Qué clase de cambio te están pidiendo

Todo pedido del cliente cae en **uno de tres tipos**, y la diferencia no es de tamaño sino de **dónde
vive la respuesta**. Confundirlos cuesta caro en las dos direcciones: tratar como imposible algo que
era una línea de la definición, o prometer para el viernes algo que exige construir una pieza.

| | Qué es | Quién lo hace |
|---|---|---|
| **1 · Definición** | Se puede decir con los **datos** de la definición de este cliente | **Tú, ahora**, en este repo |
| **2 · Pieza nueva** | El sistema no hace eso **en absoluto** | Se **solicita**: no es autoservicio |
| **3 · Modificar lo que ya trae** | Existe, pero de otra manera, y **más allá de sus opciones** | Se **solicita**, y queda registrado |

---

## La línea roja, y por qué no depende de tu disciplina

**El producto no se modifica por dentro.** Y aquí no hace falta acordarse: **este repo no contiene ese
código**. Mira lo que hay —la definición, las recetas de imagen y estas instrucciones— y comprobarás
que el motor no está. Viaja versionado, desde fuera.

Así que si un camino parece exigir tocar el producto, eso **no es un obstáculo a rodear: es el
diagnóstico**. Significa tipo 2 o tipo 3. Nunca un parche local.

> Un parche local, si de algún modo se colara, dejaría a este cliente fuera del producto: cada
> actualización tendría que resolver un conflicto que nadie recuerda haber creado, y las mejoras que
> llegan a todos dejarían de llegarle a él. Sale carísimo, y siempre más tarde.

---

## Paso 1 · Triar

Léelo con **las palabras del cliente**, no traducidas todavía. Y aplica esta regla antes que ninguna
otra:

> ### Regla de la duda: ante la duda, **inténtalo como tipo 1**
> No lo pienses mucho: escribe el cambio en la definición y deja que **el validador conteste**. Al
> construir, el sistema comprueba lo que declaraste y, si no cuadra, **falla con un mensaje que dice
> qué pasa y qué hacer** — no con un error oscuro.
>
> El intento es barato y la respuesta es objetiva: un build que falla **no despliega nada** y no deja
> rastro en el sistema del cliente. Discutir media hora si algo «se podrá» cuesta más que probarlo.

### Es TIPO 1 si el pedido se puede decir con datos de la definición

Cosas que son datos, no código: los **nombres** de todo (el objeto, sus fases, los rótulos que ve el
usuario) · las **fases** del flujo y qué las mueve · **quién ve qué** (zonas, roles, qué módulos
aparece cada uno) · el **equipo** · la **marca** (logotipo, colores, tipografía) · los **campos** de
la ficha · y cualquier **opción ya declarada** de una pieza que el sistema ya trae.

### Es TIPO 2 si el sistema no hace eso en absoluto

Nada de lo que hay se le parece: haría falta una colección de datos nueva, una pantalla nueva o un
flujo que ninguna pieza existente cubre.

### Es TIPO 3 si existe, pero de otra manera

La pantalla o el flujo ya están, y el cliente los quiere **distintos**, más allá de las opciones que
esa pieza expone. La prueba está en el paso 1: **lo intentaste como tipo 1 y el validador dijo que
ese dial no existe**.

---

## Paso 2 · Actuar según el tipo

### Tipo 1 — se hace aquí

1. Edita la definición (`config/<cliente>.bos.json`). Las notas `_*` del propio fichero explican cada
   bloque y avisan de las trampas.
2. Construye. **El build es el validador**: si algo no cuadra, se para y te dice qué.
3. **Guardar y publicar son el mismo acto**: al empujar el cambio, el sistema se reconstruye y
   despliega. No hay un botón aparte de «publicar» — tenlo presente antes de empujar a media tarde.
4. Haz el **checklist en pantalla** (más abajo). Sin él, el cambio está desplegado, no verificado.

### Tipos 2 y 3 — se solicitan, y la solicitud es el trabajo

Hoy **no son autoservicio**. Lo que sí puedes hacer —y es lo que decide si el pedido avanza rápido o
da tres vueltas— es formular la **solicitud bien formada**. Copia esto y respóndelo con las palabras
del cliente, no con las tuyas:

```
QUÉ PIDE, en sus palabras
  (la frase del cliente, literal; no la traduzcas todavía)

QUÉ TIENE QUE PASAR
  El comportamiento, contado como un caso concreto de principio a fin.

QUIÉN LO USA
  Qué rol, en qué momento de su trabajo, y cada cuánto.

CON QUÉ DATOS
  Qué información hace falta, y si ya existe en el sistema o habría que empezar a capturarla.

QUÉ HACEN HOY EN SU LUGAR
  El apaño actual (una hoja de cálculo, un mensaje, hacerlo a mano). Esto vale más de lo que parece:
  enseña el flujo real y qué duele de verdad.

TIPO Y POR QUÉ
  2 o 3, y qué te llevó ahí — sobre todo, qué intentaste como tipo 1 y qué contestó el validador.

URGENCIA REAL
  Qué se rompe si no está, y para cuándo. «Cuanto antes» no es una fecha.
```

**Y para el tipo 3, dilo al cliente sin adornos:** su caso **queda registrado**. Cuando esa
diferencia se convierta en una opción del producto, deja de ser una petición y pasa a ser **tipo 1**
— una línea en su definición, y disponible también para todos los demás. Por eso interesa que la
solicitud diga el *para qué*, no una solución ya cocinada: dos clientes que piden lo mismo con
palabras distintas se convierten en **una** opción bien puesta, y la que se construye es la del
problema, no la del primero que llamó.

**Mientras tanto**, y esto también es tu trabajo: si hay una forma de resolverlo con lo que hay —aunque
sea menos elegante— ofrécela, y **di claramente que es un mientras-tanto**. Un apaño presentado como
solución definitiva es una deuda que nadie apuntó.

---

## Paso 3 · Los ejemplos, que es donde se aprende la frontera

### Tipo 1 · definición

- **«Que las oportunidades se llamen obras.»** El objeto y sus rótulos son datos. Se cambia el
  nombre en singular y plural y los rótulos que ve el usuario.
- **«Falta una fase entre presupuesto enviado y ganado: presupuesto revisado.»** Las fases y lo que
  mueve de una a otra son definición. Se añade la fase y la transición que la alimenta.
- **«El comercial no debería ver el panel de dirección.»** Quién ve qué es definición: se ajusta qué
  zonas abren ese módulo.
- **«Añade metros cuadrados a la ficha.»** Un campo más del objeto es definición.

### Tipo 2 · pieza nueva

- **«Queremos emitir las facturas desde aquí.»** No hay nada parecido: datos nuevos, pantalla nueva,
  numeración, un flujo propio. Solicitud.
- **«Que avise por mensajería instantánea cuando entra un caso urgente.»** Un canal de salida que el
  sistema no tiene. Solicitud.
- **«Un portal donde el cliente final entre a ver su expediente.»** Otro público, otra aplicación,
  otras reglas de acceso. Solicitud.

### Tipo 3 · existe, pero de otra manera

- **«La pantalla de reparto, pero agrupando por zona geográfica en vez de por estado.»** La pantalla
  existe; agrupar por otra cosa no es una de sus opciones. Solicitud, y queda registrado.
- **«El aviso, pero a las ocho de la mañana en vez de al entrar el caso.»** El aviso existe; cuándo
  se dispara no es ajustable. Solicitud.

### Los casos de borde — los que de verdad enseñan

> **Parece tipo 2 y es tipo 1.**
> *«Necesitamos una pantalla para ver todo lo que se cerró el mes pasado.»*
> Suena a pantalla nueva. Pero **lo cerrado ya se enseña**: la vista general lo contempla, no hace
> falta construir nada para eso. Lo del *mes pasado* es otra pregunta —si acotar por fecha es una de
> las opciones de esa vista—, y esa se contesta como todas: **inténtalo y que responda el validador**.
> Lo importante es que el pedido se ha partido en dos, y la mitad grande ya estaba resuelta.
> **La señal:** el cliente pide una PANTALLA porque es como él imagina la solución. Traduce siempre a
> **qué quiere ver**, no a la forma que le da. La forma suele existir ya.

> **Parece tipo 1 y es tipo 3.**
> *«Cambia el texto de ese botón.»*
> Un texto es lo más parecido a un dato que hay… salvo que **ese** texto concreto no esté expuesto
> como opción. Muchos rótulos lo están; no todos.
> **La señal:** lo intentaste como tipo 1 y el validador dijo que ese dial no existe. Ahí se acabó la
> discusión — y por eso la regla de la duda es «inténtalo», no «decide».

> **Parece tipo 1 y es tipo 3, el difícil.**
> *«Que este rol pueda editar solo lo de su propio equipo.»*
> Crear un rol es tipo 1 puro. Pero *hasta dónde alcanza* un rol viene en niveles ya definidos —lo
> suyo, todo en lectura, todo— y «solo lo de mi equipo» puede no ser uno de ellos.
> **La señal:** el pedido no es *quién*, es *cuánto*. Lo primero es definición; lo segundo puede no
> serlo.

> **Parece tipo 3 y es tipo 2.**
> *«Que al cerrar un caso se cree automáticamente el siguiente.»*
> Suena a variante de algo que ya pasa. Pero encadenar un flujo con otro no es un ajuste de una
> pieza: es una pieza. La diferencia práctica importa —el tipo 3 llega antes— así que no lo llames
> tipo 3 para dar mejor noticia.

---

## El checklist en pantalla — para los cambios de tipo 1

Que el despliegue esté verde solo dice que el sistema arrancó. Antes de decirle al cliente que está
hecho:

- [ ] **Entra con el rol al que le afecta** el cambio. Si toca a varios, con cada uno.
- [ ] **Recorre el caso concreto** que motivó el pedido, de principio a fin.
- [ ] **Lee las palabras en pantalla**: tienen que ser las del cliente.
- [ ] **Comprueba que no se movió nada más** — sobre todo lo que estaba al lado de lo que tocaste.

Mientras no esté hecho, el cambio está **desplegado, no verificado**. No son sinónimos.

---

## Si el validador te para

Es lo normal, y viene con instrucciones: **lee el mensaje entero antes de tocar nada**. Suele decir
qué falta y dónde. Dos que salen a menudo:

- Encendiste algo cuyas pantallas piden un nivel de acceso que la definición no declara → decláralo o
  apágalo.
- Le diste a un rol un acceso que ninguna pantalla de esa aplicación reconoce → quien lo tenga
  entraría a un sistema vacío.

Si el mensaje dice que **una opción no existe**, no busques la vuelta: acabas de confirmar que era
tipo 3. Escribe la solicitud y cítalo — es la mejor evidencia que puede llevar.
