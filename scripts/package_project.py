"""Prepara ZIP y manifiesto de entrega, sin cachés, Git ni temporales."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output"


def deliverables():
    """Selección explícita: no incluye archivos personales ni .git."""
    folders = ["casadsl", "data", "docs", "examples", "scripts", "tests", ".github"]
    files = [ROOT / name for name in ["README.md", ".gitignore", "requirements-docs.txt"]]
    for folder in folders:
        files.extend(p for p in (ROOT / folder).rglob("*")
                     if p.is_file() and "__pycache__" not in p.parts)
    files.extend(p for p in OUTPUT.rglob("*")
                 if p.is_file() and p.suffix != ".zip" and p.name != "manifest.json")
    return sorted(files, key=lambda p: p.relative_to(ROOT).as_posix())


def main():
    OUTPUT.mkdir(exist_ok=True)
    files = deliverables()
    manifest = {"files": [{"path": p.relative_to(ROOT).as_posix(),
                            "bytes": p.stat().st_size,
                            "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
                           for p in files]}
    manifest_path = OUTPUT / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    files.append(manifest_path)
    target = OUTPUT / "casadsl_proyecto.zip"
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        for p in files:
            archive.write(p, "casadsl_proyecto/" + p.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(target) as archive:
        if archive.testzip() is not None:
            raise RuntimeError("ZIP con una entrada dañada")
    print(f"Paquete: {target.name}; {len(files)} archivos; {target.stat().st_size} bytes.")


if __name__ == "__main__":
    main()
