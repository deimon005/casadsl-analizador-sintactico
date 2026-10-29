"""Interfaz de consola: python -m casadsl [archivo | --text TEXTO]."""

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys

from .ast_tools import ast_to_json, format_ast, write_dot
from .grammar import GRAMMAR, analysis_report
from .lexer import LexerError, tokenize
from .parser import ParseError, Parser


def main(argv=None) -> int:
    """Valida entradas y devuelve 0=éxito, 1=entrada inválida, 2=uso/archivo."""
    # Salida reproducible en Windows y al redirigir FIRST/FOLLOW con epsilon.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Analizador sintáctico predictivo CasaDSL")
    ap.add_argument("file", nargs="?", help="archivo UTF-8; sin archivo lee stdin")
    ap.add_argument("--text", help="analiza directamente una cadena")
    ap.add_argument("--tokens", action="store_true", help="muestra los tokens con posición")
    output = ap.add_mutually_exclusive_group()
    output.add_argument("--ast", action="store_true", help="muestra el AST como árbol de texto")
    output.add_argument("--json", action="store_true", help="muestra solamente el AST JSON salvo --tokens")
    ap.add_argument("--dot", metavar="ARCHIVO", help="guarda el AST en formato Graphviz DOT")
    ap.add_argument("--grammar", action="store_true", help="muestra gramática, FIRST, FOLLOW y tabla LL(1)")
    ap.add_argument("--grammar-json", action="store_true", help="muestra análisis de gramática como JSON")
    args = ap.parse_args(argv)
    if args.file and args.text is not None:
        ap.error("use un archivo o --text, no ambos")
    if args.grammar or args.grammar_json:
        report = analysis_report()
        if args.grammar_json:
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 0
        for nt, productions in GRAMMAR.items():
            print(nt + " -> " + " | ".join(" ".join(p) if p else "ε" for p in productions))
        print("\nFIRST / FOLLOW")
        for nt in GRAMMAR:
            print(f"{nt}: FIRST={report['first'][nt]}; FOLLOW={report['follow'][nt]}")
        print("\nTabla LL(1) (las celdas omitidas son error)")
        for cell in report["table"]:
            rhs = " ".join(cell["production"]) or "ε"
            print(f"M[{cell['nonterminal']}, {cell['lookahead']}] = {rhs}")
        print(f"\nConflictos: {len(report['conflicts'])}. La gramática es LL(1).")
        return 0
    try:
        if args.text is not None:
            source = args.text
        elif args.file:
            source = Path(args.file).read_text(encoding="utf-8-sig")
        else:
            source = sys.stdin.read()
        tokens = tokenize(source)
        if args.tokens:
            for token in tokens:
                print(json.dumps(asdict(token), ensure_ascii=False))
        ast = Parser(tokens).parse()
        if args.dot:
            write_dot(ast, args.dot)
        if args.json:
            print(ast_to_json(ast))
        else:
            print(f"Entrada válida: {len(ast['rules'])} regla(s).")
            if args.ast:
                print(format_ast(ast))
        return 0
    except (LexerError, ParseError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except (OSError, UnicodeError) as exc:
        print(f"No se pudo leer/escribir el archivo: {exc}", file=sys.stderr)
        return 2
    except RecursionError:
        print("La entrada excede la profundidad de representación del AST.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
