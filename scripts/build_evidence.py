"""Captura salidas reales y prepara vistas HTML para las capturas del informe.

Ejecutar desde cualquier carpeta: python scripts/build_evidence.py.
No fabrica pantallas de terminal: las vistas identifican su origen como
evidencia de procesos ejecutados y conservan stdout, stderr y exit code.
"""
from __future__ import annotations

import html
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "evidencias"


def run(args: list[str]) -> dict:
    result = subprocess.run(
        [sys.executable, *args], cwd=ROOT, capture_output=True,
        encoding="utf-8", errors="replace", env={**__import__('os').environ, "PYTHONIOENCODING": "utf-8"},
    )
    return {"command": "python " + " ".join(args), "returncode": result.returncode,
            "stdout": result.stdout, "stderr": result.stderr}


def page(title: str, subtitle: str, runs: list[dict]) -> str:
    cards = []
    for item in runs:
        content = item["stdout"] + item["stderr"]
        cards.append(f'<article><div class="command">{html.escape(item["command"])}</div>'
                     f'<pre>{html.escape(content.rstrip())}</pre>'
                     f'<div class="exit">Código de salida: {item["returncode"]}</div></article>')
    return '''<!doctype html><html lang="es"><meta charset="utf-8">
<title>CasaDSL | Evidencias de ejecución</title><style>
*{box-sizing:border-box}body{margin:0;background:#edf2f7;color:#172b45;font:16px Arial,sans-serif}
main{max-width:1180px;margin:auto;padding:32px}header{border-left:6px solid #007c83;padding-left:18px;margin-bottom:24px}
.tag{font-size:12px;letter-spacing:2px;color:#007c83;font-weight:bold}h1{font-size:30px;margin:8px 0}
p{line-height:1.5;margin:10px 0}article{background:#142439;color:#eaf1f8;border-radius:9px;margin:18px 0;overflow:hidden}
.command{padding:15px 19px;background:#203852;font:14px Consolas,monospace;color:#8ce4d4}
pre{font:14px/1.45 Consolas,monospace;white-space:pre-wrap;overflow-wrap:anywhere;margin:0;padding:20px}
.exit{padding:11px 20px;background:#1b3048;font-size:12px;color:#c4d5e5}
footer{font-size:12px;color:#52647a;line-height:1.5}</style><main><header>
<div class="tag">CASADSL / INFO1148</div>''' + f'<h1>{html.escape(title)}</h1><p>{html.escape(subtitle)}</p></header>' + ''.join(cards) + '''
<footer>Vista de evidencias: las salidas se capturaron ejecutando el código del proyecto.
Los registros íntegros se encuentran junto a estas vistas en ejecuciones.json y pruebas_unittest.txt.
No se simula la ejecución de dispositivos.</footer></main></html>'''


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    valid = run(["-m", "casadsl", "examples/demo.casa", "--ast"])
    error = run(["-m", "casadsl", "examples/error.casa"])
    tests = run(["-m", "unittest", "discover", "-s", "tests", "-v"])
    cases = run(["scripts/run_cases.py"])
    grammar = run(["-m", "casadsl", "--grammar"])
    all_runs = {"valid": valid, "error": error, "tests": tests, "cases": cases, "grammar": grammar}
    (OUT / "ejecuciones.json").write_text(json.dumps(all_runs, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT / "pruebas_unittest.txt").write_text(tests["stdout"] + tests["stderr"], encoding="utf-8")
    # La vista resumida muestra las últimas líneas reales del registro completo.
    summary = {**tests, "stderr": "\n".join(tests["stderr"].splitlines()[-5:]) + "\n"}
    views = {
        "demo_valido.html": page("Programa válido y AST", "Tres reglas aceptadas; se conserva la agrupación de NOT, AND y OR.", [valid]),
        "demo_error.html": page("Diagnóstico sintáctico", "El analizador rechaza una regla sin THEN e indica la posición del problema.", [error]),
        "demo_pruebas.html": page("Pruebas reproducibles", "Resumen real de unittest y del corpus documentado; el registro completo queda disponible.", [summary, cases]),
    }
    for filename, content in views.items():
        (OUT / filename).write_text(content, encoding="utf-8")
    # Captura de una ejecución independiente y pequeña para el AST del informe.
    source = "WHEN NOT (temperatura > 28 OR humedad < 40) THEN activar alarma;"
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from casadsl.parser import parse
    from casadsl.ast_tools import format_ast, write_dot
    ast = parse(source)
    (OUT / "ast_ejemplo.txt").write_text(source + "\n\n" + format_ast(ast) + "\n", encoding="utf-8")
    (OUT / "ast_ejemplo.json").write_text(json.dumps(ast, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_dot(ast, OUT / "ast_ejemplo.dot")
    expected = {"valid": 0, "error": 1, "tests": 0, "cases": 0, "grammar": 0}
    if any(all_runs[key]["returncode"] != value for key, value in expected.items()):
        print("Error: una ejecución no produjo el código esperado. Revisar ejecuciones.json.")
        return 1
    print("Evidencias verificadas:", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
