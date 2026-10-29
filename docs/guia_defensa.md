# Guía para comprender y defender CasaDSL

## Qué hace el proyecto

El lexer reconoce piezas individuales: WHEN, identificadores, números, comparadores y separadores. El parser comprueba cómo se combinan esas piezas y construye un AST. Por ejemplo, un lexer puede reconocer todos los tokens de `WHEN temperatura > THEN encender ventilador;`, pero el parser lo rechaza porque después de `>` falta un valor.

## Por qué un lenguaje de automatización

Una regla relaciona una condición sobre sensores con una acción sobre un dispositivo. El dominio es suficientemente concreto para escribir ejemplos comprensibles y suficientemente pequeño para explicar una gramática completa. Los identificadores permiten vocabulario propio de la casa: `temperatura`, `humedad`, `ventilador`, `alarma`.

## FIRST y FOLLOW

FIRST(A) contiene los terminales con los que puede comenzar una cadena derivada de A; también contiene epsilon si A puede producir la cadena vacía. FOLLOW(A) contiene los tokens que pueden aparecer inmediatamente después de A. EOF se incluye en FOLLOW del símbolo inicial porque marca el final de un programa completo.

Ejemplo: FIRST(Factor) = {NOT, PARENT_IZQ, ID}. Tras un Factor pueden venir AND, OR, THEN o PARENT_DER, por lo que FOLLOW(Factor) contiene esos cuatro terminales. FIRST(RestoOr) = {OR, epsilon}; su alternativa vacía solo corresponde cuando el siguiente token es THEN o PARENT_DER.

## Por qué la gramática es LL(1)

Cada celda de la tabla predictiva contiene como máximo una producción. Las alternativas de Factor comienzan por NOT, PARENT_IZQ e ID; las de Valor por NUM, TRUE y FALSE. En los restos anulables, FIRST de la alternativa no vacía no se cruza con FOLLOW del no terminal. El análisis mecánico de las producciones verifica que no haya conflictos.

## Recursión y factorización

`Programa -> Regla Programa | Regla` tiene un prefijo común. Se factoriza como `Programa -> Regla RestoPrograma` y `RestoPrograma -> Regla RestoPrograma | epsilon`. La producción original no tiene recursión izquierda, pero sí necesita factorización para una tabla LL(1) directa.

Una regla como `Expr -> Expr OR Termino | Termino` sí tendría recursión izquierda. CasaDSL utiliza `Expr -> Termino RestoOr` y `RestoOr -> OR Termino RestoOr | epsilon`. La gramática final no contiene recursión izquierda directa ni indirecta: todo ciclo recursivo consume un terminal antes de volver al mismo no terminal.

## Precedencia y asociatividad

Las comparaciones son las unidades de la condición. NOT actúa sobre el siguiente Factor; AND combina factores; OR combina términos. Por eso `a == TRUE OR b == TRUE AND c == TRUE` produce un OR cuyo hijo derecho es AND. Los paréntesis vuelven a llamar a Expr y permiten cambiar esa agrupación.

Las colas de OR y AND son recursivas por la derecha en la gramática. El parser construye el AST acumulando por la izquierda. Esa elección se explica como una regla de construcción del AST y evita confundir la forma del árbol de derivación con la asociatividad del AST.

## Cómo explicar el código

1. Mostrar el lexer y explicar por qué reconoce `>=` antes que `>`.
2. Mostrar el método que consume WHEN, una expresión, THEN, una acción y `;`.
3. Relacionar Expr, Termino y Factor con OR, AND y NOT/paréntesis.
4. Mostrar que el parser exige EOF después de todas las reglas: no acepta un prefijo válido seguido de basura.
5. Ejecutar un caso válido, un caso con falta de THEN y otro con paréntesis sin cerrar.
6. Enseñar cómo cambia el AST cuando se añaden paréntesis.
7. Ejecutar la batería de pruebas y explicar una prueba límite.

## Preguntas posibles

**¿Se podría usar solo una expresión regular?** El reconocimiento de tokens sí usa expresiones regulares. Las agrupaciones arbitrariamente anidadas requieren controlar una estructura recursiva; el parser implementa esa estructura.

**¿Un AST es lo mismo que el árbol sintáctico completo?** No. El AST conserva comparaciones, operadores, reglas y acciones, y omite separadores y no terminales auxiliares. El enunciado admite cualquiera de las dos representaciones.

**¿Qué ocurre con una entrada vacía?** Se rechaza: Programa requiere al menos una Regla.

**¿Qué ocurre con dos reglas seguidas?** Se aceptan si cada regla termina en `;`; RestoPrograma reconoce las siguientes.

**¿Qué errores no comprueba?** No comprueba existencia de dispositivos, tipos ni efectos de acciones. Esas tareas pertenecerían al análisis semántico o a un intérprete.

**¿Por qué NOT y paréntesis cuentan como extensión?** Porque tienen producciones propias, afectan a FIRST/FOLLOW y a la tabla, producen nodos/agrupaciones en el AST y tienen pruebas de aceptación y rechazo. Su reconocimiento en el lexer, por sí solo, no bastaría.

**¿Dónde se usó IA?** Como apoyo de desarrollo y documentación. El grupo debe responder con honestidad y defender la solución revisada; ninguna prueba automática reemplaza esa comprensión.

## Antes de entregar

Completar los integrantes y el repositorio real, revisar el PDF, ejecutar los comandos del README y practicar la explicación. La fecha de preparación del documento no representa una fecha límite del curso.
