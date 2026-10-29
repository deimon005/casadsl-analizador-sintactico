"""Representaciones del AST en texto y DOT, sin dependencias externas."""

from pathlib import Path
import json


def _label(node: dict) -> str:
    kind = node["type"]
    if kind == "Action":
        return f"Action: {node['verb']} {node['target']}"
    if kind == "Compare":
        return f"Compare: {node['sensor']} {node['operator']}"
    if kind == "Binary":
        return node["operator"]
    if kind == "Not":
        return "NOT"
    if kind == "Number":
        return f"Number: {node['value']}"
    if kind == "Boolean":
        return "Boolean: " + ("TRUE" if node["value"] else "FALSE")
    return kind


def _children(node: dict) -> list[dict]:
    kind = node["type"]
    if kind == "Program":
        return node["rules"]
    if kind == "Rule":
        return [node["condition"], node["action"]]
    if kind == "Binary":
        return [node["left"], node["right"]]
    if kind == "Not":
        return [node["operand"]]
    if kind == "Compare":
        return [node["value"]]
    return []


def format_ast(ast: dict) -> str:
    """Árbol ASCII; recorrido iterativo para admitir listas lógicas extensas."""
    lines = []
    stack = [(ast, "", "")]
    while stack:
        node, prefix, branch = stack.pop()
        lines.append(prefix + branch + _label(node))
        children = _children(node)
        child_prefix = prefix + ("   " if branch == "`- " else "|  " if branch else "")
        for i in reversed(range(len(children))):
            child_branch = "`- " if i == len(children) - 1 else "|- "
            stack.append((children[i], child_prefix, child_branch))
    return "\n".join(lines)


def ast_to_json(ast: dict) -> str:
    """JSON legible; ante gran profundidad usa serialización compacta iterativa.

    El parser permite cadenas largas de AND/OR sin recursión. json.dumps sí
    recorre el AST recursivamente: el respaldo evita rechazar esas entradas
    solo por la herramienta de presentación. No modifica el límite global
    de recursión del intérprete.
    """
    try:
        return json.dumps(ast, ensure_ascii=False, indent=2)
    except RecursionError:
        pass
    parts = []
    stack = [(False, ast)]
    while stack:
        raw, item = stack.pop()
        if raw:
            parts.append(item)
        elif isinstance(item, dict):
            entries = list(item.items())
            parts.append("{")
            stack.append((True, "}"))
            for i in reversed(range(len(entries))):
                key, value = entries[i]
                stack.append((False, value))
                stack.append((True, ":"))
                stack.append((True, json.dumps(key, ensure_ascii=False)))
                if i:
                    stack.append((True, ","))
        elif isinstance(item, list):
            parts.append("[")
            stack.append((True, "]"))
            for i in reversed(range(len(item))):
                stack.append((False, item[i]))
                if i:
                    stack.append((True, ","))
        else:
            parts.append(json.dumps(item, ensure_ascii=False))
    return "".join(parts)


def write_dot(ast: dict, path: str | Path) -> None:
    """Guarda un grafo DOT; visualizarlo con Graphviz es opcional."""
    lines = ["digraph AST {", "  rankdir=TB;", '  node [shape=box, fontname="Arial"];']
    stack = [(ast, None)]
    next_id = 0
    while stack:
        node, parent = stack.pop()
        current_id = f"n{next_id}"
        next_id += 1
        lines.append(f"  {current_id} [label={json.dumps(_label(node), ensure_ascii=False)}];")
        if parent is not None:
            lines.append(f"  {parent} -> {current_id};")
        for child in reversed(_children(node)):
            stack.append((child, current_id))
    lines.append("}")
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")
