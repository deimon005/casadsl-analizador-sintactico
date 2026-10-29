# CasaDSL - Analizador sintáctico LL(1)

Proyecto de Teoría de la Computación (INFO1148). CasaDSL describe reglas de automatización de una casa y verifica su estructura mediante un parser predictivo escrito a mano en Python.

**Integrantes:** José Jiménez, Franco Oyarzo y Demian Quezada.

**Repositorio:** https://github.com/deimon005/casadsl-analizador-sintactico

```text
WHEN temperatura > 28 AND humedad < 40 THEN encender ventilador;
WHEN NOT (movimiento == TRUE OR puerta == TRUE) THEN activar alarma;
```

El programa analiza las instrucciones y produce un AST; no ejecuta acciones sobre dispositivos. Las reglas deben terminar con `;` y cada acción se escribe como dos identificadores: verbo y objetivo.

## Ejecución

Requiere **Python 3.10 o superior**. El analizador y sus pruebas utilizan solamente la biblioteca estándar; no hay dependencias que instalar para ejecutarlos. En Windows también se puede usar `py` en lugar de `python`. Ejecutar los comandos desde la carpeta que contiene este README.

```console
python -m casadsl examples/demo.casa --ast
python -m casadsl examples/demo.casa --json
python -m casadsl examples/demo.casa --tokens
python -m casadsl --text "WHEN temperatura > 28 THEN encender ventilador;" --ast
python -m casadsl --grammar
```

Sin archivo ni `--text`, la entrada se lee de la entrada estándar. Un archivo se interpreta como UTF-8 (se admite BOM). La salida normal informa que la entrada es válida. Los errores señalan línea, columna, elemento esperado y token encontrado. Los códigos de salida son `0` para éxito, `1` para error del lenguaje y `2` para problemas de uso o de archivos.

```console
python -m casadsl examples/error.casa
```

Este último comando debe rechazar la entrada: falta `THEN`.

## Lenguaje y extensión

- Palabras reservadas: `WHEN`, `THEN`, `AND`, `OR`, `NOT`, `TRUE`, `FALSE`. No distinguen mayúsculas y minúsculas.
- Identificadores: letras ASCII o `_`, seguidos de letras ASCII, dígitos o `_`. Se conserva su escritura.
- Valores: enteros no negativos y booleanos. No se admiten decimales, cadenas ni números negativos.
- Comparadores: `>`, `<`, `>=`, `<=`, `==`, `!=`.
- Condiciones: comparaciones unidas por `AND` y `OR`.
- Extensión obligatoria: negación `NOT` y agrupación con paréntesis, integradas en gramática, tabla, AST y pruebas.
- Precedencia: comparación, `NOT`, `AND`, `OR`. `AND` y `OR` se agrupan por la izquierda.
- Un programa tiene al menos una regla. No hay comentarios ni asignaciones.

Ejemplo: `a == TRUE OR b == TRUE AND c == TRUE` se interpreta como `a == TRUE OR (b == TRUE AND c == TRUE)`.

El análisis es sintáctico. No comprueba si existe un sensor o un dispositivo ni si un operador es adecuado para el tipo de valor. Por ejemplo, `temperatura > TRUE` es sintácticamente válida en esta gramática, aunque una fase semántica podría rechazarla.

Por recursos, la implementación admite hasta 1000 dígitos por número y hasta 100 llamadas activas de `Factor` (99 operadores `NOT` o 99 agrupaciones sobre una comparación). Las entradas que exceden esas cotas reciben un diagnóstico controlado; son límites de implementación, no restricciones de la gramática abstracta. Las listas de reglas y de operadores se recorren con bucles.

## Pruebas reproducibles

```console
python -m unittest discover -s tests -v
python scripts/run_cases.py
```

El corpus de `data/casos.json` incluye casos válidos, sintácticamente inválidos, casos límite y errores léxicos adicionales. El segundo comando genera `output/resultados_pruebas.json`, `.csv` y `.md`, con entrada, resultado esperado, resultado obtenido, observación y detalle del error. Devuelve un código distinto de cero si alguna expectativa falla.

## Archivos

| Ruta | Contenido |
| --- | --- |
| `casadsl/lexer.py` | Tokens y analizador léxico adaptado del notebook entregado |
| `casadsl/parser.py` | Parser predictivo por descenso recursivo |
| `casadsl/grammar.py` | Gramática, cálculo iterativo de FIRST/FOLLOW y tabla LL(1) |
| `casadsl/ast_tools.py` | AST legible y exportación DOT |
| `examples/` | Programa de demostración y ejemplo incorrecto |
| `tests/` | Pruebas del lenguaje, AST, lexer y análisis formal |
| `data/casos.json` | Corpus documentado de entradas |
| `docs/informe.md` | Fuente legible del informe |
| `docs/gramatica.txt` | Producciones numeradas |
| `docs/first_follow.json` | Conjuntos calculados |
| `docs/tabla_ll1.csv` | Tabla predictiva completa; celdas vacías indican error |
| `docs/guia_defensa.md` | Explicaciones y preguntas para preparar la defensa |
| `output/pdf/informe_casadsl.pdf` | Informe de entrega |
| `output/` | Resultados y evidencias de ejecución |

El análisis formal se deriva de las producciones, pero no genera el parser: las funciones sintácticas se implementan y explican explícitamente. No se utiliza un generador automático de parsers.

## Regenerar el informe

Los resultados y el informe se entregan ya generados. Para reconstruir el PDF y las evidencias se requieren Python, `reportlab` y `Pillow`; estas dependencias son únicamente de documentación.

```console
python scripts/run_cases.py
python scripts/build_evidence.py
python scripts/build_report.py
```

Las capturas del navegador incluidas en los anexos se obtienen a partir de la página de evidencias con salidas reales. Si se modifica el código, hay que repetir las ejecuciones y las capturas antes de entregar. El informe puede generarse sin capturas, pero dejará explícito que falta esa evidencia.

## Preparación de la entrega

La portada y el anexo incluyen los integrantes y el repositorio registrado en `data/entrega.json`. Si cambia alguno de esos datos, actualizar el archivo y regenerar el informe. La copia local funciona independientemente de la publicación.

Se utilizó IA generativa como apoyo para preparar el desarrollo y la documentación. El grupo debe revisar, comprender y poder explicar cada parte, como exige el enunciado. La guía de defensa y el código comentado ayudan a esa revisión.

