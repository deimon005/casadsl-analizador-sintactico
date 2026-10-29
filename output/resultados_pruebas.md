# Resultados de pruebas de CasaDSL

Resultado: **36/36** casos correctos; **0** discrepancias.

Las categorías son disjuntas. Los casos de error léxico son adicionales y no sustituyen las 12 entradas sintácticamente inválidas.

| ID | Categoría | Esperado | Obtenido | Coincide |
| --- | --- | --- | --- | --- |
| V01 | valido | valid | valid | Sí |
| V02 | valido | valid | valid | Sí |
| V03 | valido | valid | valid | Sí |
| V04 | valido | valid | valid | Sí |
| V05 | valido | valid | valid | Sí |
| V06 | valido | valid | valid | Sí |
| V07 | valido | valid | valid | Sí |
| V08 | valido | valid | valid | Sí |
| V09 | valido | valid | valid | Sí |
| V10 | valido | valid | valid | Sí |
| V11 | valido | valid | valid | Sí |
| V12 | valido | valid | valid | Sí |
| I01 | invalido | syntax_error | syntax_error | Sí |
| I02 | invalido | syntax_error | syntax_error | Sí |
| I03 | invalido | syntax_error | syntax_error | Sí |
| I04 | invalido | syntax_error | syntax_error | Sí |
| I05 | invalido | syntax_error | syntax_error | Sí |
| I06 | invalido | syntax_error | syntax_error | Sí |
| I07 | invalido | syntax_error | syntax_error | Sí |
| I08 | invalido | syntax_error | syntax_error | Sí |
| I09 | invalido | syntax_error | syntax_error | Sí |
| I10 | invalido | syntax_error | syntax_error | Sí |
| I11 | invalido | syntax_error | syntax_error | Sí |
| I12 | invalido | syntax_error | syntax_error | Sí |
| L01 | limite | syntax_error | syntax_error | Sí |
| L02 | limite | syntax_error | syntax_error | Sí |
| L03 | limite | valid | valid | Sí |
| L04 | limite | valid | valid | Sí |
| L05 | limite | valid | valid | Sí |
| L06 | limite | valid | valid | Sí |
| L07 | limite | valid | valid | Sí |
| L08 | limite | syntax_error | syntax_error | Sí |
| X01 | lexico | lexical_error | lexical_error | Sí |
| X02 | lexico | lexical_error | lexical_error | Sí |
| X03 | lexico | lexical_error | lexical_error | Sí |
| X04 | lexico | lexical_error | lexical_error | Sí |

## V01: Comparación mayor que y acción con verbo y destino.

```text
WHEN temperatura > 28 THEN encender ventilador;
```

Esperado: `valid`. Obtenido: `valid`.

Programa aceptado: 1 regla(s).

## V02: Comparación menor que.

```text
WHEN humedad < 40 THEN activar riego;
```

Esperado: `valid`. Obtenido: `valid`.

Programa aceptado: 1 regla(s).

## V03: Operador compuesto mayor o igual.

```text
WHEN luz >= 80 THEN cerrar persiana;
```

Esperado: `valid`. Obtenido: `valid`.

Programa aceptado: 1 regla(s).

## V04: Operador compuesto menor o igual.

```text
WHEN bateria <= 15 THEN activar ahorro;
```

Esperado: `valid`. Obtenido: `valid`.

Programa aceptado: 1 regla(s).

## V05: Igualdad con valor booleano verdadero.

```text
WHEN movimiento == TRUE THEN activar alarma;
```

Esperado: `valid`. Obtenido: `valid`.

Programa aceptado: 1 regla(s).

## V06: Desigualdad con valor booleano falso.

```text
WHEN puerta != FALSE THEN encender luz;
```

Esperado: `valid`. Obtenido: `valid`.

Programa aceptado: 1 regla(s).

## V07: Construcción compuesta con AND.

```text
WHEN temperatura > 28 AND humedad < 40 THEN encender ventilador;
```

Esperado: `valid`. Obtenido: `valid`.

Programa aceptado: 1 regla(s).

## V08: Construcción compuesta con OR.

```text
WHEN humo == TRUE OR temperatura > 60 THEN activar alarma;
```

Esperado: `valid`. Obtenido: `valid`.

Programa aceptado: 1 regla(s).

## V09: Extensión NOT aplicada a una comparación.

```text
WHEN NOT movimiento == TRUE THEN apagar luz;
```

Esperado: `valid`. Obtenido: `valid`.

Programa aceptado: 1 regla(s).

## V10: Paréntesis cambian la agrupación frente a la precedencia normal.

```text
WHEN (temperatura > 28 OR humedad < 40) AND puerta == FALSE THEN activar clima;
```

Esperado: `valid`. Obtenido: `valid`.

Programa aceptado: 1 regla(s).

## V11: Integración de NOT con agrupación y operador binario.

```text
WHEN NOT (humo == FALSE AND puerta == TRUE) THEN activar alarma;
```

Esperado: `valid`. Obtenido: `valid`.

Programa aceptado: 1 regla(s).

## V12: Programa compuesto por dos reglas.

```text
WHEN temperatura > 28 THEN encender ventilador;
WHEN movimiento == TRUE THEN activar alarma;
```

Esperado: `valid`. Obtenido: `valid`.

Programa aceptado: 2 regla(s).

## I01: Falta WHEN al comienzo de la regla.

```text
temperatura > 28 THEN encender ventilador;
```

Esperado: `syntax_error`. Obtenido: `syntax_error`.

Error sintáctico en línea 1, columna 1: se esperaba WHEN para iniciar una regla (el programa no puede estar vacío); se encontró 'temperatura' (ID).

## I02: Falta la palabra reservada THEN.

```text
WHEN temperatura > 28 encender ventilador;
```

Esperado: `syntax_error`. Obtenido: `syntax_error`.

Error sintáctico en línea 1, columna 23: se esperaba AND, OR, THEN o ')' después de la comparación; se encontró 'encender' (ID).

## I03: Falta un valor después del operador relacional.

```text
WHEN temperatura > THEN encender ventilador;
```

Esperado: `syntax_error`. Obtenido: `syntax_error`.

Error sintáctico en línea 1, columna 20: se esperaba un valor NUM, TRUE o FALSE después del operador relacional; se encontró 'THEN' (THEN).

## I04: Falta el operador relacional.

```text
WHEN temperatura 28 THEN encender ventilador;
```

Esperado: `syntax_error`. Obtenido: `syntax_error`.

Error sintáctico en línea 1, columna 18: se esperaba un operador relacional: >, <, >=, <=, == o !=; se encontró '28' (NUM).

## I05: Falta el punto y coma final.

```text
WHEN temperatura > 28 THEN encender ventilador
```

Esperado: `syntax_error`. Obtenido: `syntax_error`.

Error sintáctico en línea 1, columna 47: se esperaba ';' al final de la regla; se encontró fin de entrada.

## I06: La acción carece de destino.

```text
WHEN temperatura > 28 THEN encender;
```

Esperado: `syntax_error`. Obtenido: `syntax_error`.

Error sintáctico en línea 1, columna 36: se esperaba un identificador de dispositivo después de la acción; se encontró ';' (PUNTO_COMA).

## I07: El verbo de la acción debe ser un identificador.

```text
WHEN temperatura > 28 THEN 12 ventilador;
```

Esperado: `syntax_error`. Obtenido: `syntax_error`.

Error sintáctico en línea 1, columna 28: se esperaba un identificador de acción después de THEN; se encontró '12' (NUM).

## I08: No se permite una condición vacía entre paréntesis.

```text
WHEN () THEN encender ventilador;
```

Esperado: `syntax_error`. Obtenido: `syntax_error`.

Error sintáctico en línea 1, columna 7: se esperaba un identificador de sensor, NOT o '(' para iniciar una condición; se encontró ')' (PARENT_DER).

## I09: AND necesita un factor a su derecha.

```text
WHEN temperatura > 28 AND THEN encender ventilador;
```

Esperado: `syntax_error`. Obtenido: `syntax_error`.

Error sintáctico en línea 1, columna 27: se esperaba un identificador de sensor, NOT o '(' para iniciar una condición; se encontró 'THEN' (THEN).

## I10: No se permiten comparaciones encadenadas.

```text
WHEN temperatura > 28 < 40 THEN encender ventilador;
```

Esperado: `syntax_error`. Obtenido: `syntax_error`.

Error sintáctico en línea 1, columna 23: se esperaba AND, OR, THEN o ')' después de la comparación; se encontró '<' (OP_REL).

## I11: Se rechazan tokens sobrantes después de un programa válido.

```text
WHEN temperatura > 28 THEN encender ventilador; basura
```

Esperado: `syntax_error`. Obtenido: `syntax_error`.

Error sintáctico en línea 1, columna 49: se esperaba WHEN para otra regla o fin de entrada; se encontró 'basura' (ID).

## I12: Falta el paréntesis de cierre.

```text
WHEN (temperatura > 28 THEN encender ventilador;
```

Esperado: `syntax_error`. Obtenido: `syntax_error`.

Error sintáctico en línea 1, columna 24: se esperaba ')' para cerrar la agrupación; se encontró 'THEN' (THEN).

## L01: Entrada de longitud cero: se exige al menos una regla.

```text
(entrada vacía)
```

Esperado: `syntax_error`. Obtenido: `syntax_error`.

Error sintáctico en línea 1, columna 1: se esperaba WHEN para iniciar una regla (el programa no puede estar vacío); se encontró fin de entrada.

## L02: Una entrada formada solo por espacios tampoco es un programa.

```text
 	
  
```

Esperado: `syntax_error`. Obtenido: `syntax_error`.

Error sintáctico en línea 2, columna 3: se esperaba WHEN para iniciar una regla (el programa no puede estar vacío); se encontró fin de entrada.

## L03: Identificadores de un carácter y el menor entero no negativo.

```text
WHEN x > 0 THEN a b;
```

Esperado: `valid`. Obtenido: `valid`.

Programa aceptado: 1 regla(s).

## L04: Reservadas sin distinción de mayúsculas; identificadores con guion bajo y dígitos.

```text
wHeN _sensor1 == fAlSe tHeN Apagar Luz_2;
```

Esperado: `valid`. Obtenido: `valid`.

Programa aceptado: 1 regla(s).

## L05: Separadores mixtos, saltos CRLF y operadores sin espacios.

```text
	WHEN
 x>=10
 THEN	activar dispositivo;

```

Esperado: `valid`. Obtenido: `valid`.

Programa aceptado: 1 regla(s).

## L06: Negación repetida y tres niveles de agrupación.

```text
WHEN NOT NOT (((x == 0))) THEN a b;
```

Esperado: `valid`. Obtenido: `valid`.

Programa aceptado: 1 regla(s).

## L07: Los ceros iniciales son permitidos por la especificación léxica.

```text
WHEN x == 000 THEN a b;
```

Esperado: `valid`. Obtenido: `valid`.

Programa aceptado: 1 regla(s).

## L08: No hay sentencias vacías: un punto y coma adicional es inválido.

```text
WHEN x > 0 THEN a b;;
```

Esperado: `syntax_error`. Obtenido: `syntax_error`.

Error sintáctico en línea 1, columna 21: se esperaba WHEN para otra regla o fin de entrada; se encontró ';' (PUNTO_COMA).

## X01: Los enteros negativos no pertenecen al lenguaje; el signo menos es desconocido.

```text
WHEN temperatura > -1 THEN encender ventilador;
```

Esperado: `lexical_error`. Obtenido: `lexical_error`.

Error léxico en línea 1, columna 20: símbolo no reconocido '-'.

## X02: Los números decimales no pertenecen al lenguaje; el punto es desconocido.

```text
WHEN temperatura > 28.5 THEN encender ventilador;
```

Esperado: `lexical_error`. Obtenido: `lexical_error`.

Error léxico en línea 1, columna 22: símbolo no reconocido '.'.

## X03: Los identificadores admiten solamente letras ASCII, dígitos y guion bajo.

```text
WHEN señal == TRUE THEN activar alarma;
```

Esperado: `lexical_error`. Obtenido: `lexical_error`.

Error léxico en línea 1, columna 8: símbolo no reconocido 'ñ'.

## X04: Los comentarios no forman parte de las extensiones elegidas.

```text
WHEN x > 1 THEN a b; # comentario
```

Esperado: `lexical_error`. Obtenido: `lexical_error`.

Error léxico en línea 1, columna 22: símbolo no reconocido '#'.
