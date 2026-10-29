"""Ejecuta el corpus y guarda evidencia reproducible en JSON, CSV y Markdown.

Uso desde la raíz del proyecto: python scripts/run_cases.py
No requiere dependencias externas ni modifica los casos esperados.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from casadsl.lexer import LexerError
from casadsl.parser import ParseError, parse


def evaluate(source: str) -> tuple[str, str]:
    """Devuelve la clasificación obtenida y el diagnóstico real del parser."""
    try:
        ast = parse(source)
    except LexerError as exc:
        return "lexical_error", str(exc)
    except ParseError as exc:
        return "syntax_error", str(exc)
    return "valid", f"Programa aceptado: {len(ast['rules'])} regla(s)."


def run_cases(cases: list[dict]) -> dict:
    results = []
    for case in cases:
        actual, detail = evaluate(case["source"])
        results.append({**case, "actual": actual,
                        "passed": actual == case["expected"], "detail": detail})
    passed = sum(case["passed"] for case in results)
    return {"summary": {"total": len(results), "passed": passed,
                        "failed": len(results) - passed,
                        "categories": dict(Counter(x["category"] for x in results)),
                        "expected": dict(Counter(x["expected"] for x in results))},
            "results": results}


def markdown_report(report: dict) -> str:
    summary = report["summary"]
    lines = ["# Resultados de pruebas de CasaDSL", "",
             f"Resultado: **{summary['passed']}/{summary['total']}** casos correctos; "
             f"**{summary['failed']}** discrepancias.", "",
             "Las categorías son disjuntas. Los casos de error léxico son adicionales "
             "y no sustituyen las 12 entradas sintácticamente inválidas.", "",
             "| ID | Categoría | Esperado | Obtenido | Coincide |", 
             "| --- | --- | --- | --- | --- |"]
    for row in report["results"]:
        lines.append(f"| {row['id']} | {row['category']} | {row['expected']} | "
                     f"{row['actual']} | {'Sí' if row['passed'] else 'No'} |")
    for row in report["results"]:
        lines.extend(["", f"## {row['id']}: {row['observation']}", "", "```text",
                      row["source"] or "(entrada vacía)", "```", "",
                      f"Esperado: `{row['expected']}`. Obtenido: `{row['actual']}`.", "",
                      row["detail"]])
    return "\n".join(lines) + "\n"


def save_report(report: dict, output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    (output / "resultados_pruebas.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    fields = ["id", "category", "source", "expected", "actual", "passed", "observation", "detail"]
    with (output / "resultados_pruebas.csv").open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(report["results"])
    (output / "resultados_pruebas.md").write_text(markdown_report(report), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=ROOT / "data" / "casos.json")
    parser.add_argument("--output", type=Path, default=ROOT / "output")
    args = parser.parse_args()
    cases = json.loads(args.cases.read_text(encoding="utf-8"))
    report = run_cases(cases)
    save_report(report, args.output)
    summary = report["summary"]
    print(f"Casos: {summary['total']} | Correctos: {summary['passed']} | "
          f"Discrepancias: {summary['failed']}")
    print(f"Evidencia: {args.output.name}/resultados_pruebas.json (.csv y .md)")
    return 0 if summary["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
