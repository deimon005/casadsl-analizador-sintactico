# Revisión independiente del analizador

Revisión del 29 de octubre de 2026. Se contrastaron la gramática, el lexer, el parser, el AST, el corpus de pruebas y la interfaz de consola. Esta revisión no evalúa la maquetación del informe PDF ni sus capturas.

## Resultado

No se encontraron discrepancias entre el reconocimiento de la gramática y el parser en las comprobaciones realizadas. La gramática tiene 11 no terminales, 18 producciones y 25 celdas ocupadas en la tabla LL(1). Los únicos no terminales anulables son RestoPrograma, RestoOr y RestoAnd. Un análisis independiente de esquinas izquierdas no encontró recursión izquierda directa ni indirecta.

Se generaron 120 programas y seis variantes por programa mediante inserción, borrado o sustitución de un token. En total se compararon 840 entradas (semilla 1148) con un reconocedor Earley de referencia, independiente de los cálculos FIRST/FOLLOW y de la tabla LL(1). Hubo 840 coincidencias: 160 aceptaciones y 680 rechazos. Los datos resumidos se guardan en `output/auditoria.json`. Esta comprobación de referencia se realizó únicamente para la auditoría; el producto utiliza el parser escrito a mano.

La suite automatizada comprueba adicionalmente precedencia, asociatividad, NOT y paréntesis, consumo hasta EOF, posiciones de tokens y errores, entrada estándar, JSON y límites de recursos. Para consultar el número actual de pruebas y repetirlas:

```console
python -m unittest discover -s tests -v
python scripts/run_cases.py
```

## Aspectos para la revisión del grupo

- El límite de 1000 dígitos por literal y la protección de profundidad son restricciones de recursos de la implementación; no son consecuencias de la gramática formal.
- Las comparaciones son sintácticas: no se valida existencia de sensores, tipos o acciones.
- La extensión incluye NOT y agrupaciones en el parser y sus pruebas; reconocer sus tokens en el lexer no bastaría para cumplirla.
- La coherencia de los resultados comprobados no demuestra corrección para todas las entradas posibles. El argumento formal de LL(1), la revisión de las funciones y las pruebas se complementan.
- Los integrantes confirmados y el repositorio creado se registran en `data/entrega.json` y en el informe. La publicación debe conservar el conjunto completo de archivos y resultados.
