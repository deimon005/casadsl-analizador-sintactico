"""Genera informe PDF, fuente Markdown y anexos formales desde el proyecto.

Dependencias solo de documentación: reportlab, Pillow.
No cambia expectativas de prueba. Si faltan resultados o hay fallos, aborta.
"""
from __future__ import annotations

from collections import defaultdict
import csv
from html import escape
import json
from pathlib import Path
import re
import sys
import textwrap

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from casadsl.grammar import GRAMMAR, TERMINALS, END, EPSILON, START, analysis_report, first_of_sequence, first_sets, follow_sets, ll1_table
from casadsl.parser import parse
from casadsl.ast_tools import format_ast
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Preformatted, PageBreak, Image, KeepTogether

DOCS = ROOT / "docs"
OUT = ROOT / "output"
EVID = OUT / "evidencias"
WIDTH = A4[0] - 88
NAVY = colors.HexColor("#18334F")
TEAL = colors.HexColor("#007C83")
GRAY = colors.HexColor("#52647A")
PALE = colors.HexColor("#EDF3F7")


def fonts():
    candidates = [Path("C:/Windows/Fonts"), Path("/usr/share/fonts/truetype/dejavu")]
    for folder in candidates:
        if (folder / "arial.ttf").exists():
            names = ["arial.ttf", "arialbd.ttf", "ariali.ttf", "consola.ttf"]
        elif (folder / "DejaVuSans.ttf").exists():
            names = ["DejaVuSans.ttf", "DejaVuSans-Bold.ttf", "DejaVuSans-Oblique.ttf", "DejaVuSansMono.ttf"]
        else:
            continue
        for family, name in zip(["Body", "BodyBold", "BodyItalic", "Mono"], names):
            pdfmetrics.registerFont(TTFont(family, str(folder / name)))
        pdfmetrics.registerFontFamily("Body", normal="Body", bold="BodyBold", italic="BodyItalic", boldItalic="BodyBold")
        return
    raise RuntimeError("No se encontraron Arial/Consolas ni DejaVu. Ajustar fonts() a las fuentes instaladas.")


def main():
    fonts()
    DOCS.mkdir(exist_ok=True)
    (OUT / "pdf").mkdir(parents=True, exist_ok=True)
    report = json.loads((OUT / "resultados_pruebas.json").read_text(encoding="utf-8"))
    runs = json.loads((EVID / "ejecuciones.json").read_text(encoding="utf-8"))
    meta = json.loads((ROOT / "data" / "entrega.json").read_text(encoding="utf-8"))
    if report["summary"]["failed"] or runs["tests"]["returncode"]:
        raise RuntimeError("Hay pruebas fallidas: corregir antes de generar el informe.")
    test_log = runs["tests"]["stdout"] + runs["tests"]["stderr"]
    match = re.search(r"Ran (\d+) tests?", test_log)
    test_count = int(match.group(1)) if match else None
    analysis = analysis_report()
    first = first_sets()
    follow = follow_sets(first)
    matrix = ll1_table()
    numbered = []
    for head, alternatives in GRAMMAR.items():
        for rhs in alternatives:
            numbered.append((len(numbered) + 1, head, rhs))
    labels = {(head, rhs): f"P{num:02}" for num, head, rhs in numbered}
    grammar_text = "\n".join(f"P{n:02}  {head} -> {' '.join(rhs) or EPSILON}" for n, head, rhs in numbered)
    (DOCS / "gramatica.txt").write_text(grammar_text + "\n", encoding="utf-8")
    (DOCS / "first_follow.json").write_text(json.dumps({"first": analysis["first"], "follow": analysis["follow"]}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (DOCS / "analisis_completo.json").write_text(json.dumps(analysis, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    terminals = sorted(TERMINALS) + [END]
    with (DOCS / "tabla_ll1.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["No terminal", *terminals])
        for head in GRAMMAR:
            writer.writerow([head, *[labels[(head, matrix[head, token])] if (head, token) in matrix else "" for token in terminals]])

    styles = {
        "p": ParagraphStyle("p", fontName="Body", fontSize=10, leading=14.4, spaceAfter=9, textColor=NAVY),
        "h1": ParagraphStyle("h1", fontName="BodyBold", fontSize=19, leading=24, spaceAfter=17, textColor=NAVY),
        "h2": ParagraphStyle("h2", fontName="BodyBold", fontSize=12, leading=16, spaceBefore=10, spaceAfter=7, textColor=TEAL),
        "small": ParagraphStyle("small", fontName="Body", fontSize=8.2, leading=11, spaceAfter=7, textColor=GRAY),
        "cell": ParagraphStyle("cell", fontName="Body", fontSize=8, leading=10.8, textColor=NAVY),
        "head": ParagraphStyle("head", fontName="BodyBold", fontSize=8.3, leading=11, textColor=colors.white),
        "code": ParagraphStyle("code", fontName="Mono", fontSize=8, leading=10.4, textColor=NAVY, backColor=PALE, borderPadding=9, spaceBefore=5, spaceAfter=12),
    }
    story = []
    md = []

    def p(text, small=False):
        story.append(Paragraph(escape(text), styles["small" if small else "p"]))
        md.extend([text, ""])

    def h(text, level=1):
        story.append(Paragraph(escape(text), styles["h1" if level == 1 else "h2"]))
        md.extend(["#" * (level + 1) + " " + text, ""])

    def code(text, size=8):
        style = ParagraphStyle("codecopy", parent=styles["code"], fontSize=size, leading=size * 1.3)
        max_chars = int(WIDTH / (size * .61)) - 3
        lines = []
        for line in text.splitlines():
            lines.extend(textwrap.wrap(line, width=max_chars, replace_whitespace=False, drop_whitespace=False) or [""])
        story.append(Preformatted("\n".join(lines), style))
        md.extend(["```text", text, "```", ""])

    def table(headers, rows, widths=None):
        data = [[Paragraph(escape(str(x)), styles["head"]) for x in headers]]
        data.extend([[Paragraph(escape(str(x)).replace("\n", "<br/>"), styles["cell"]) for x in row] for row in rows])
        t = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), NAVY),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PALE]),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LINEBELOW", (0, 0), (-1, 0), .8, TEAL),
            ("LINEBELOW", (0, -1), (-1, -1), .5, colors.HexColor("#C8D6E2")),
        ]))
        story.extend([t, Spacer(1, 10)])
        md.extend(["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"])
        md.extend("| " + " | ".join(str(x).replace("\n", "<br>").replace("|", "\\|") for x in row) + " |" for row in rows)
        md.append("")

    def newpage():
        story.append(PageBreak())

    story.append(Spacer(1, 32))
    p("TEORÍA DE LA COMPUTACIÓN / INFO1148", small=True)
    story.append(Spacer(1, 22))
    title_style = ParagraphStyle("title", fontName="BodyBold", fontSize=43, leading=50, textColor=NAVY)
    story.append(Paragraph("CasaDSL", title_style))
    md.extend(["# CasaDSL", ""])
    h("Diseño e implementación de un analizador sintáctico", 2)
    p("Lenguaje de reglas para automatización de una casa")
    story.append(Spacer(1, 24))
    p("Informe de proyecto grupal. Python, gramática libre de contexto, FIRST/FOLLOW, tabla LL(1), descenso recursivo y AST.")
    table(["Dato", "Información"], [
        ["Integrantes", ", ".join(meta["integrantes"]) or "Pendiente: completar los nombres del grupo antes de entregar."],
        ["Asignatura", meta["asignatura"]],
        ["Preparación", meta["fecha_preparacion"] + " (no corresponde a una fecha límite del curso)"],
        ["Repositorio", meta["repositorio"] or "Pendiente: incorporar la URL real de GitHub en el anexo."],
        ["Validación", f"{report['summary']['passed']}/{report['summary']['total']} casos documentados; {test_count} pruebas automatizadas aprobadas."],
    ], [105, WIDTH - 105])
    h("Resumen", 2)
    p("CasaDSL permite describir condiciones sobre sensores y asociarlas con acciones. El sistema convierte el texto en tokens, verifica la gramática y construye un AST. La gramática final tiene 11 no terminales, 18 producciones y una tabla predictiva con 25 celdas ocupadas sin conflictos. La extensión agrega negación y agrupación. Las ejecuciones se conservan como evidencia reproducible.")
    p("El proyecto analiza la forma de las reglas. No ejecuta dispositivos ni incorpora validación semántica de sensores, tipos o acciones.", small=True)

    newpage()
    h("1. Introducción y especificación")
    p("El dominio elegido es la automatización doméstica. Una regla indica cuándo realizar una acción: por ejemplo, encender un ventilador si una temperatura supera un umbral. El propósito del lenguaje es ofrecer instrucciones pequeñas, legibles y verificables mediante reglas formales.")
    code("WHEN temperatura > 28 AND humedad < 40 THEN encender ventilador;")
    h("1.1 Alfabeto y categorías léxicas", 2)
    p("El alfabeto relevante incluye letras ASCII A-Z y a-z, dígitos 0-9, guion bajo, los caracteres > < = ! ; ( ) y espacios, tabulaciones y saltos de línea LF/CR/CRLF. La pertenencia al alfabeto no garantiza un token válido: '=' solo no es un comparador admitido. Las reservadas ignoran mayúsculas y los identificadores conservan su escritura.")
    table(["Categoría", "Definición / ejemplos"], [
        ["Reservadas (7)", "WHEN, THEN, AND, OR, NOT, TRUE, FALSE"],
        ["ID", "[A-Za-z_][A-Za-z0-9_]*; temperatura, _sensor1, ventilador"],
        ["NUM", "[0-9]+; enteros no negativos; 0, 28, 000"],
        ["OP_REL", ">=, <=, ==, !=, >, < (los compuestos se reconocen primero)"],
        ["Separadores", "PUNTO_COMA = ;, PARENT_IZQ = (, PARENT_DER = )"],
        ["Espacio", "[ \\t\\r\\n]+; se descarta conservando la posición"],
        ["EOF", "Marcador agregado por el lexer; no se escribe en el programa"],
    ], [120, WIDTH - 120])
    h("1.2 Estructura y decisiones", 2)
    p("Cada programa tiene una o más reglas. Cada regla comienza con WHEN, contiene una condición, la palabra THEN, dos identificadores de acción (verbo y objetivo) y termina con ';'. Las condiciones admiten seis comparadores, AND, OR, NOT y paréntesis. Una palabra reservada no puede utilizarse como identificador.")
    p("Cada comparación tiene la forma ID OP_REL Valor. No se aceptan condiciones booleanas sueltas, comparaciones encadenadas, asignaciones, decimales, números negativos, cadenas ni comentarios. La semántica de los nombres es externa: 'temperatura > TRUE' es sintácticamente válida en esta gramática, aunque no sería una regla útil sin un análisis de tipos.")

    newpage()
    h("2. Ejemplos de especificación")
    p("Los siguientes ejemplos cumplen el mínimo inicial de cinco entradas válidas y cinco inválidas. La sección de pruebas amplía este conjunto y registra los resultados de ejecución.")
    rows = []
    selected = [x for x in report["results"] if x["id"] in {"V01", "V05", "V07", "V10", "V11", "I01", "I02", "I03", "I05", "I12"}]
    for case in selected:
        rows.append([case["id"], case["source"], "Válida" if case["expected"] == "valid" else "Inválida", case["observation"]])
    table(["ID", "Entrada", "Clase", "Justificación"], rows, [30, 238, 50, WIDTH - 318])
    p("AND y OR constituyen la construcción compuesta base. NOT y los paréntesis forman la extensión elegida y se integran al análisis formal y al parser.", small=True)

    newpage()
    h("3. Gramática libre de contexto")
    p("Se define G = (N, T, P, S). El símbolo inicial S es Programa. Los no terminales N son los nombres de la izquierda de las producciones. Los terminales T son categorías de tokens; cada OP_REL representa uno de los seis lexemas relacionales. EOF es un marcador de fin para el algoritmo predictivo, y ε denota la cadena vacía, no un token de entrada.")
    p("N = {" + ", ".join(GRAMMAR) + "}.")
    p("T = {" + ", ".join(sorted(TERMINALS)) + "}.")
    code(grammar_text, 8.5)
    p("La gramática consta de 18 producciones. Las únicas producciones anulables son P03, P07 y P10. Programa no deriva ε, de modo que una entrada vacía no es válida.")
    h("3.1 Interpretación", 2)
    p("Expr combina términos mediante OR; Termino combina factores mediante AND; Factor reconoce NOT, agrupación o comparación. Accion consume exactamente dos identificadores. Las colas permiten repetir reglas y operadores sin recursión izquierda.")

    newpage()
    h("4. Análisis de la gramática")
    h("4.1 Recursión izquierda", 2)
    p("La gramática final no presenta recursión izquierda directa ni indirecta. Antes de recorrer un ciclo recursivo se consume un terminal: WHEN para repetir reglas, OR o AND para sus colas, NOT para negación y '(' para agrupación. Las cadenas de no terminales iniciales terminan en uno de esos terminales o en ID; no regresan al mismo no terminal sin consumir entrada.")
    p("Una formulación alternativa Expr -> Expr OR Termino | Termino sí tendría recursión izquierda. Se reemplaza por Expr -> Termino RestoOr y RestoOr -> OR Termino RestoOr | ε. La versión final usa esta estructura.")
    h("4.2 Factorización por la izquierda", 2)
    code("Versión con prefijo común:\nPrograma -> Regla Programa | Regla\n\nVersión factorizada:\nPrograma -> Regla RestoPrograma\nRestoPrograma -> Regla RestoPrograma | ε")
    p("La primera versión comienza con Regla en ambas alternativas, por lo que no permite elegir directamente con un token. La versión final extrae ese prefijo común. Las alternativas de Factor comienzan con NOT, PARENT_IZQ e ID; las de Valor con NUM, TRUE y FALSE. No requieren factorización adicional.")
    h("4.3 Ambigüedad, precedencia y AST", 2)
    p("La separación en Expr, Termino y Factor fija la precedencia: comparaciones, NOT, AND, OR. Los paréntesis permiten cambiar la agrupación. Así, 'a == TRUE OR b == TRUE AND c == TRUE' agrupa el AND dentro del lado derecho del OR. La ausencia de conflictos LL(1) confirma una elección única de producción en cada paso.")
    p("Las colas de la gramática recurren por la derecha; el AST se construye mediante acumulación por la izquierda para AND y OR. Esta es una regla explícita de construcción del AST. Los no terminales auxiliares y los paréntesis no aparecen como nodos, pero su efecto se conserva.")

    newpage()
    h("5. Conjuntos FIRST y FOLLOW")
    p("FIRST(A) contiene los terminales que pueden iniciar una derivación de A; incluye ε si A es anulable. FOLLOW(A) contiene los terminales que pueden seguir a A en una forma sentencial; EOF se agrega al símbolo inicial.")
    rows = [[nt, "{ " + ", ".join(sorted(first[nt])) + " }", "{ " + ", ".join(sorted(follow[nt])) + " }"] for nt in GRAMMAR]
    table(["No terminal", "FIRST", "FOLLOW"], rows, [100, 180, WIDTH - 280])
    h("5.1 Método de cálculo", 2)
    p("FIRST se calcula por punto fijo: se agregan los inicios de cada producción y se avanza al siguiente símbolo cuando el anterior es anulable. FOLLOW se inicia con EOF en Programa; para A -> α B β se agrega FIRST(β) sin ε a FOLLOW(B), y si β es anulable se agrega FOLLOW(A). Se repite hasta que ningún conjunto cambie.")
    h("5.2 Justificaciones representativas", 2)
    p("FIRST(Factor) = {NOT, PARENT_IZQ, ID}: son los inicios de sus tres alternativas. FOLLOW(Expr) = {THEN, PARENT_DER}: Expr aparece entre WHEN y THEN, o dentro de paréntesis. FIRST(RestoOr) = {OR, ε}; cuando no llega OR, la alternativa vacía corresponde únicamente a THEN o PARENT_DER.")
    p("FOLLOW(Factor) y FOLLOW(Comparacion) incluyen AND, OR, THEN y PARENT_DER. FOLLOW(Valor) hereda esos símbolos por estar al final de Comparacion. FOLLOW(Accion) solo contiene PUNTO_COMA por la forma de Regla. Los once conjuntos se verifican mediante valores esperados independientes en las pruebas.")

    newpage()
    h("6. Tabla predictiva LL(1)")
    p("Para A -> α se ubica la producción en M[A,t] para cada t de FIRST(α) sin ε. Si α es anulable, también se usa cada símbolo de FOLLOW(A). La siguiente tabla presenta todas las entradas ocupadas agrupando anticipaciones que seleccionan la misma producción. Las demás celdas indican error; la matriz completa se incluye en docs/tabla_ll1.csv.")
    rows = []
    for num, head, rhs in numbered:
        tokens = sorted(token for (nt, token), production in matrix.items() if nt == head and production == rhs)
        rows.append([head, ", ".join(tokens), f"P{num:02}: {' '.join(rhs) or EPSILON}"])
    table(["No terminal", "Anticipación", "Producción"], rows, [94, 146, WIDTH - 240])
    p(f"Resultado: {len(matrix)} celdas ocupadas; 0 conflictos. Cada celda contiene como máximo una producción: la gramática final es LL(1).")
    p("En las alternativas anulables: {WHEN} y FOLLOW(RestoPrograma)={EOF} son disjuntos; {OR} y FOLLOW(RestoOr)={THEN,PARENT_DER} son disjuntos; {AND} y FOLLOW(RestoAnd)={OR,THEN,PARENT_DER} son disjuntos. Estas separaciones permiten decidir cuándo consumir y cuándo terminar una cola.")

    newpage()
    h("7. Diseño e implementación del parser")
    p("La implementación utiliza únicamente la biblioteca estándar. El flujo es: texto -> tokenize -> lista de Token con EOF -> Parser.parse -> AST. El lexer adapta la base del notebook proporcionado: conserva su vocabulario, añade posiciones y EOF y admite saltos CRLF. Usa dígitos ASCII explícitos para que el alfabeto quede definido.")
    table(["Archivo / función", "Responsabilidad y relación formal"], [
        ["lexer.py / tokenize", "Reconocer tokens y conservar línea, columna y desplazamiento. Detectar el primer símbolo no reconocido."],
        ["parser.py / parse", "Consumir Programa y RestoPrograma. Exigir al menos una regla y EOF."],
        ["rule / action", "Reconocer Regla y Accion; exigir WHEN, THEN, dos ID y ';'."],
        ["expression / term", "Reconocer Expr/RestoOr y Termino/RestoAnd con bucles; construir OR/AND."],
        ["factor / comparison / value", "Resolver Factor con una anticipación; reconocer Comparacion y Valor."],
        ["grammar.py", "Calcular FIRST/FOLLOW y la tabla a partir de las producciones; no genera el parser."],
        ["ast_tools.py", "Recorrer el AST y representarlo como texto, JSON o DOT."],
        ["__main__.py", "Leer archivo/entrada estándar, mostrar resultados y devolver códigos de salida."],
    ], [146, WIDTH - 146])
    p("expect comprueba el token actual y avanza. Los restos se implementan con bucles y solo aceptan terminar ante un token de su FOLLOW. El parser exige EOF; así evita aceptar un prefijo correcto seguido de tokens sobrantes. Cada alternativa de Factor y Valor se decide con un token, coherentemente con la tabla LL(1).")
    h("7.1 Recursos y alcance", 2)
    p("El reconocimiento es lineal en la cantidad de tokens para entradas dentro de los límites del entorno. La lista de tokens y el AST requieren memoria lineal. La impresión con sangría de un árbol muy profundo puede ocupar más espacio que su número de nodos.")
    p("El lexer limita cada número a 1000 dígitos y el parser a 100 llamadas activas de Factor (99 agrupaciones anidadas sobre una comparación son aceptadas). Estos son límites de implementación para producir diagnósticos controlados; la gramática abstracta no impone esas cotas. Las pruebas distinguen los límites de recursos del corpus de equivalencia con LL(1). Las tabulaciones cuentan como una columna y CRLF como un salto de línea.")

    newpage()
    h("8. AST y manejo de errores")
    p("El AST representa el programa mediante Program, Rule, Action, Compare, Number, Boolean, Binary y Not. Los separadores y no terminales auxiliares se omiten. Este árbol se obtiene ejecutando el parser con una entrada válida que combina las dos extensiones:")
    ast_source = "WHEN NOT (temperatura > 28 OR humedad < 40) THEN activar alarma;"
    code(ast_source + "\n\n" + format_ast(parse(ast_source)), 8.5)
    p("NOT tiene como hijo la expresión OR completa por efecto de los paréntesis. Action conserva el verbo activar y el objetivo alarma. Se incluyen el AST en texto, JSON y DOT en output/evidencias/.")
    h("8.1 Diagnósticos reales", 2)
    examples = [next(x for x in report["results"] if x["id"] == case_id) for case_id in ["I03", "I06", "I12", "X02"]]
    for case in examples:
        p(case["id"] + ": " + case["detail"], small=True)
    p("El programa se detiene en el primer error. Informa línea y columna y distingue un símbolo desconocido (error léxico) de una combinación de tokens incorrecta (error sintáctico). No implementa recuperación para continuar con errores posteriores.")

    newpage()
    h("9. Casos de prueba y resultados")
    p(f"El corpus contiene {report['summary']['total']} casos y produjo {report['summary']['passed']} coincidencias con el resultado esperado. Las categorías son disjuntas: los errores léxicos adicionales no sustituyen las entradas sintácticamente inválidas. Los casos límite pueden ser válidos o inválidos según la regla que ejercitan.")
    table(["Categoría", "Cantidad", "Objetivo"], [
        ["Válidos", "12", "Comparadores, booleanos, múltiples reglas, AND/OR y extensión."],
        ["Inválidos sintácticos", "12", "Reservadas/separadores ausentes, operandos faltantes, estructura incorrecta y tokens sobrantes."],
        ["Casos límite", "8", "Vacío, espacios, cero, mayúsculas, CRLF, anidación, ceros iniciales y ';' extra."],
        ["Errores léxicos adicionales", "4", "Negativos, decimales, identificadores no ASCII y comentarios no admitidos."],
    ], [146, 50, WIDTH - 196])
    p(f"La batería unittest ejecutó {test_count} pruebas con resultado OK. Además del corpus, comprueba estructura del AST, precedencia y asociatividad, posiciones, mensajes, CLI, límites, FIRST/FOLLOW y tabla. Un reconocedor independiente por pila LL(1) compara sus decisiones de aceptación con las del parser de descenso recursivo en el corpus.")
    code("python -m unittest discover -s tests -v\npython scripts/run_cases.py")
    p("En las tablas siguientes, Válida significa aceptación; Sintaxis significa rechazo sintáctico y Léxico rechazo léxico. En todos los casos listados, esperado y obtenido coinciden. La observación documenta el propósito del caso. El JSON/CSV conserva también el diagnóstico completo y las entradas con espacios exactos.")
    translations = {"valid": "Válida", "syntax_error": "Sintaxis", "lexical_error": "Léxico"}
    for category, title in [("valido", "9.1 Entradas válidas"), ("invalido", "9.2 Entradas sintácticamente inválidas"), ("limite", "9.3 Casos límite"), ("lexico", "9.4 Errores léxicos adicionales")]:
        newpage()
        h(title)
        rows = []
        for row in report["results"]:
            if row["category"] != category:
                continue
            source = row["source"]
            if not source:
                source = "(entrada vacía)"
            elif not source.strip():
                source = repr(source)
            else:
                source = source.replace("\r", "\\r").replace("\t", "\\t").replace("\n", "\\n")
            rows.append([row["id"], source, translations[row["expected"]] + " / " + translations[row["actual"]], row["observation"]])
        table(["ID", "Entrada", "Esperado / obtenido", "Observación"], rows, [30, 211, 74, WIDTH - 315])

    newpage()
    h("10. Extensión creativa y conclusiones")
    h("10.1 Negación y agrupación", 2)
    p("La extensión permite negar comparaciones o condiciones compuestas y modificar la precedencia con paréntesis. La base ya contiene AND y OR, por lo que la ampliación tiene un efecto observable: NOT (a == TRUE OR b == TRUE) niega el conjunto, mientras NOT a == TRUE OR b == TRUE solo niega la primera comparación.")
    table(["Parte", "Integración de la extensión"], [
        ["Gramática", "P11: Factor -> NOT Factor; P12: Factor -> PARENT_IZQ Expr PARENT_DER."],
        ["FIRST/FOLLOW", "NOT y PARENT_IZQ pertenecen a FIRST(Factor/Termino/Expr); PARENT_DER aparece en FOLLOW de expresiones y componentes."],
        ["Tabla LL(1)", "Las anticipaciones NOT y PARENT_IZQ seleccionan alternativas distintas; PARENT_DER permite cerrar las colas anulables."],
        ["Parser y AST", "factor implementa recursión controlada, crea Not y reconoce grupos. El árbol conserva el efecto de la agrupación."],
        ["Pruebas", "V09-V11 y L06 ejercitan negación/grupos. I08 e I12 rechazan agrupaciones vacías o sin cierre; pruebas unitarias verifican precedencia."],
    ], [100, WIDTH - 100])
    h("10.2 Conclusiones", 2)
    p("Se obtuvo un lenguaje coherente con los requisitos mínimos y un parser predictivo propio. La factorización y la separación por niveles de precedencia producen una gramática LL(1). El cálculo formal, las funciones del parser y el AST representan las mismas decisiones del lenguaje. Las pruebas documentadas y el reconocedor alternativo no detectaron discrepancias en el conjunto evaluado.")
    p("La validez sintáctica no garantiza que una regla sea útil o segura para un dispositivo. Una ampliación futura podría añadir análisis de tipos, un catálogo de sensores y acciones, o ejecución simulada; cada cambio de sintaxis exigiría actualizar gramática, análisis formal y pruebas. La batería aporta evidencia de corrección para los casos revisados, no una demostración exhaustiva de todo comportamiento del software.")
    p("Se utilizó IA generativa como apoyo de desarrollo y documentación. El grupo debe revisar y comprender las producciones, cálculos y código, y ser capaz de defenderlos. La guía docs/guia_defensa.md ofrece un recorrido de explicación.")

    for filename, title, caption in [
        ("captura_valido.png", "Anexo A. Ejecución válida y AST", "Captura de la vista de evidencias con stdout real del programa de tres reglas. Se verifica aceptación y se representa la estructura sintáctica."),
        ("captura_error.png", "Anexo B. Detección de errores", "Captura de una ejecución inválida. La vista muestra el comando, el diagnóstico real y el código de salida distinto de cero."),
        ("captura_pruebas.png", "Anexo C. Demostración de pruebas", "Captura de los resúmenes reales de unittest y del corpus. El registro completo está en output/evidencias/pruebas_unittest.txt."),
    ]:
        newpage()
        h(title)
        path = EVID / filename
        p(caption)
        if path.exists():
            image = Image(str(path))
            scale = min(WIDTH / image.imageWidth, 570 / image.imageHeight)
            image.drawWidth = image.imageWidth * scale
            image.drawHeight = image.imageHeight * scale
            image.hAlign = "CENTER"
            story.extend([image, Spacer(1, 12)])
            md.extend([f"![{title}](../output/evidencias/{filename})", ""])
        else:
            p("Pendiente: capturar la vista HTML correspondiente antes de la entrega. Las salidas textuales ya se conservan; no se presenta una captura inexistente.")

    newpage()
    h("Anexo D. Entrega y reproducibilidad")
    repo = meta["repositorio"]
    if repo:
        p("Repositorio GitHub del código fuente: " + repo)
        story.append(Paragraph('<link href="' + escape(repo, quote=True) + '">' + escape(repo) + '</link>', styles["p"]))
    else:
        p("Repositorio GitHub: pendiente de incorporar la URL real del repositorio del grupo. La entrega local contiene el código completo y el README, pero este dato debe completarse antes de presentar el informe.")
    p("Integrantes: " + (", ".join(meta["integrantes"]) or "pendientes de completar en data/entrega.json y regenerar el informe."))
    code("python -m casadsl examples/demo.casa --ast\npython -m casadsl examples/error.casa\npython -m casadsl --grammar\npython -m unittest discover -s tests -v\npython scripts/run_cases.py")
    p("Requisito de ejecución: Python 3.10 o superior, sin bibliotecas externas para parser y pruebas. El informe se regenera con reportlab y Pillow; las capturas se vuelven a obtener de las vistas de evidencias después de cualquier cambio. El README explica formato, ejemplos, archivos y dependencias.")
    h("Archivos auxiliares", 2)
    p("docs/gramatica.txt contiene las producciones numeradas; docs/first_follow.json contiene los conjuntos; docs/tabla_ll1.csv contiene la matriz completa; docs/analisis_completo.json conserva el análisis; data/casos.json contiene entradas y expectativas; output/resultados_pruebas.* conserva los resultados; output/evidencias/ incluye registros, AST, vistas y capturas.")
    h("Fuentes del proyecto", 2)
    p("1. Material de la asignatura: Proyecto Analisis_Sintactico.pdf, 6 páginas, facilitado por el usuario. Define requisitos, restricciones y entregables.", small=True)
    p("2. Material de la asignatura: Rubrica_Proyecto.pdf, 2 páginas, facilitado por el usuario. Define criterios y ponderaciones de evaluación.", small=True)
    p("3. Notebook anlizador_lexico1.ipynb, facilitado por el usuario. Base del análisis léxico; se adaptó con posiciones, EOF, saltos de línea y límites de recursos.", small=True)
    p("Los documentos de la asignatura orientan el alcance académico. Las salidas, conjuntos y tabla de este informe se derivan de los archivos locales del proyecto y de las ejecuciones conservadas, sin atribuir al material fuente resultados que no contiene.", small=True)

    def page_decoration(canvas, doc):
        canvas.saveState()
        w, height = A4
        canvas.setFillColor(TEAL)
        canvas.rect(0, height - 8, w, 8, fill=1, stroke=0)
        canvas.setStrokeColor(colors.HexColor("#CFDBE4"))
        canvas.line(44, 42, w - 44, 42)
        canvas.setFont("Body", 8)
        canvas.setFillColor(GRAY)
        canvas.drawString(44, 28, "CasaDSL | Teoría de la Computación")
        canvas.drawRightString(w - 44, 28, str(doc.page))
        canvas.restoreState()

    target = OUT / "pdf" / "informe_casadsl.pdf"
    doc = SimpleDocTemplate(str(target), pagesize=A4, rightMargin=44, leftMargin=44,
                            topMargin=45, bottomMargin=56, title="CasaDSL - Analizador sintáctico LL(1)",
                            author="Proyecto de Teoría de la Computación", subject="Gramática, parser, FIRST/FOLLOW, tabla LL(1), AST y pruebas")
    doc.build(story, onFirstPage=page_decoration, onLaterPages=page_decoration)
    (DOCS / "informe.md").write_text("\n".join(md), encoding="utf-8")
    print("Informe generado:", target)


if __name__ == "__main__":
    main()
