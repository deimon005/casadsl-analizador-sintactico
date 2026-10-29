# Relación entre gramática y código

El parser está escrito a mano en `casadsl/parser.py`. La tabla calculada por
`casadsl/grammar.py` sirve para analizar y verificar la gramática; no genera
el parser. El lexer entrega tokens, cada uno con línea, columna y offset.

| Producción | Método | Resultado |
| --- | --- | --- |
| Programa → Regla RestoPrograma | `Parser.parse` | `Program` con una o más reglas |
| RestoPrograma → Regla RestoPrograma / ε | Bucle en `Parser.parse` | Lista de reglas; ε solo ante EOF |
| Regla → WHEN Expr THEN Accion PUNTO_COMA | `Parser.rule` | `Rule(condition, action)` |
| Expr → Termino RestoOr | `Parser.expression` | Condición con OR |
| RestoOr → OR Termino RestoOr / ε | Bucle en `Parser.expression` | Nodos `Binary` con OR |
| Termino → Factor RestoAnd | `Parser.term` | Condición con AND |
| RestoAnd → AND Factor RestoAnd / ε | Bucle en `Parser.term` | Nodos `Binary` con AND |
| Factor → NOT Factor / PARENT_IZQ Expr PARENT_DER / Comparacion | `Parser.factor` | Negación, grupo o comparación |
| Comparacion → ID OP_REL Valor | `Parser.comparison` | `Compare(sensor, operator, value)` |
| Valor → NUM / TRUE / FALSE | `Parser.value` | `Number` o `Boolean` |
| Accion → ID ID | `Parser.action` | `Action(verb, target)` |

## Decisiones para explicar en la defensa

- Cada método selecciona su alternativa mediante el token actual. Los restos
  solo terminan si el token pertenece a su FOLLOW; un token ajeno produce error.
- Los bucles equivalen a la recursión derecha de las listas en la gramática.
  Durante la construcción del AST, AND y OR se acumulan a la izquierda.
- Las comparaciones son unidades básicas. NOT se aplica a un factor; AND agrupa
  factores y OR agrupa términos. Por ello la precedencia lógica es
  `NOT > AND > OR`. Los paréntesis cambian la agrupación y no generan un nodo
  adicional en el AST.
- `expect` consume exactamente un terminal o entrega un error con posición,
  símbolo esperado y símbolo encontrado. EOF garantiza que no quede texto extra.
- El programa exige una regla como mínimo. No admite bloques vacíos, valores
  aislados como condiciones, decimales, números negativos ni comentarios.
- Solo las palabras reservadas ignoran mayúsculas. Los identificadores conservan
  su escritura; su patrón es ASCII y pueden contener letras, dígitos y `_`, sin
  comenzar por un dígito.
- La validez es sintáctica: no se comprueba la existencia de sensores ni acciones,
  ni compatibilidad de tipos; tampoco se controlan dispositivos reales.
- Por recursos se aceptan literales de hasta 1000 dígitos y como máximo 99 niveles
  simultáneos de NOT/paréntesis. Estos límites pertenecen a la implementación,
  no a la GLC. Las cadenas largas de AND/OR y las listas de reglas usan bucles.
- El AST en texto y DOT se recorre de forma iterativa. JSON usa un respaldo
  iterativo cuando su estructura excede la profundidad del serializador estándar.

## Lectura de FIRST/FOLLOW y tabla

`first_sets()` y `follow_sets()` repiten la propagación hasta que ningún conjunto
cambia. `first_of_sequence` propaga ε solo si todos los símbolos previos son
anulables. Para cada producción A → α, la tabla coloca esa producción en
FIRST(α) sin ε y, si α es anulable, también en FOLLOW(A). Las celdas omitidas
son errores. Una colisión de producciones diferentes genera `ValueError`.

La gramática tiene 11 no terminales, 18 alternativas de producción (3 de ellas
vacías) y 25 celdas predictivas ocupadas, sin conflictos.
