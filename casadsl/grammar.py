"""Gramática y cálculo por punto fijo de FIRST, FOLLOW y tabla LL(1).

Este módulo analiza la gramática; no genera el parser ni ejecuta su código.
Una tupla vacía representa una producción epsilon.
"""

EPSILON = "ε"
END = "EOF"
START = "Programa"
GRAMMAR: dict[str, list[tuple[str, ...]]] = {
    "Programa": [("Regla", "RestoPrograma")],
    "RestoPrograma": [("Regla", "RestoPrograma"), ()],
    "Regla": [("WHEN", "Expr", "THEN", "Accion", "PUNTO_COMA")],
    "Expr": [("Termino", "RestoOr")],
    "RestoOr": [("OR", "Termino", "RestoOr"), ()],
    "Termino": [("Factor", "RestoAnd")],
    "RestoAnd": [("AND", "Factor", "RestoAnd"), ()],
    "Factor": [("NOT", "Factor"), ("PARENT_IZQ", "Expr", "PARENT_DER"), ("Comparacion",)],
    "Comparacion": [("ID", "OP_REL", "Valor")],
    "Valor": [("NUM",), ("TRUE",), ("FALSE",)],
    "Accion": [("ID", "ID")],
}
NONTERMINALS = frozenset(GRAMMAR)
TERMINALS = frozenset(
    symbol
    for productions in GRAMMAR.values()
    for production in productions
    for symbol in production
    if symbol not in NONTERMINALS
)


def first_of_sequence(sequence, first: dict[str, set[str]]) -> set[str]:
    """FIRST de una secuencia; propaga epsilon mientras cada símbolo sea anulable."""
    result = set()
    for symbol in sequence:
        symbol_first = first[symbol] if symbol in GRAMMAR else {symbol}
        result.update(symbol_first - {EPSILON})
        if EPSILON not in symbol_first:
            break
    else:
        result.add(EPSILON)
    return result


def first_sets() -> dict[str, set[str]]:
    """Calcula FIRST de todos los no terminales hasta alcanzar un punto fijo."""
    first = {nt: set() for nt in GRAMMAR}
    changed = True
    while changed:
        changed = False
        for nt, productions in GRAMMAR.items():
            for production in productions:
                before = len(first[nt])
                first[nt].update(first_of_sequence(production, first))
                changed |= len(first[nt]) != before
    return first


def follow_sets(first=None) -> dict[str, set[str]]:
    """Calcula FOLLOW; EOF pertenece inicialmente a FOLLOW(Programa)."""
    if first is None:
        first = first_sets()
    follow = {nt: set() for nt in GRAMMAR}
    follow[START].add(END)
    changed = True
    while changed:
        changed = False
        for head, productions in GRAMMAR.items():
            for production in productions:
                for i, symbol in enumerate(production):
                    if symbol not in GRAMMAR:
                        continue
                    suffix_first = first_of_sequence(production[i + 1 :], first)
                    before = len(follow[symbol])
                    follow[symbol].update(suffix_first - {EPSILON})
                    if EPSILON in suffix_first:
                        follow[symbol].update(follow[head])
                    changed |= len(follow[symbol]) != before
    return follow


def ll1_table() -> dict[tuple[str, str], tuple[str, ...]]:
    """Construye tabla dispersa; una colisión entre alternativas es un error."""
    first = first_sets()
    follow = follow_sets(first)
    table = {}
    for nt, productions in GRAMMAR.items():
        for production in productions:
            selected = first_of_sequence(production, first)
            lookaheads = selected - {EPSILON}
            if EPSILON in selected:
                lookaheads |= follow[nt]
            for token in sorted(lookaheads):
                key = (nt, token)
                if key in table and table[key] != production:
                    raise ValueError(f"Conflicto LL(1) en {nt}, {token}: {table[key]} / {production}")
                table[key] = production
    return table


def analysis_report() -> dict:
    """Análisis serializable para documentación reproducible y CLI."""
    first = first_sets()
    follow = follow_sets(first)
    table = ll1_table()
    return {
        "start": START,
        "epsilon": EPSILON,
        "end": END,
        "nonterminals": list(GRAMMAR),
        "terminals": sorted(TERMINALS),
        "grammar": {nt: [list(p) for p in ps] for nt, ps in GRAMMAR.items()},
        "first": {nt: sorted(values) for nt, values in first.items()},
        "follow": {nt: sorted(values) for nt, values in follow.items()},
        "table": [
            {"nonterminal": nt, "lookahead": token, "production": list(production)}
            for (nt, token), production in table.items()
        ],
        "conflicts": [],
    }
