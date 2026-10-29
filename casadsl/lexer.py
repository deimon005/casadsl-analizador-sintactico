"""Lexer basado en la especificación del notebook de referencia.

Extiende la base con posiciones y EOF. Los identificadores son ASCII; las
reservadas ignoran mayúsculas. Los números son enteros no negativos.
"""

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class Token:
    """Token y posición de inicio (línea/columna desde 1, offset desde 0)."""

    type: str
    lexeme: str
    line: int
    column: int
    offset: int


class LexerError(ValueError):
    """Entrada con símbolos no pertenecientes al vocabulario léxico."""


RESERVED = frozenset({"WHEN", "THEN", "AND", "OR", "NOT", "TRUE", "FALSE"})
MAX_NUMBER_DIGITS = 1000
TOKEN_SPEC = [
    ("NUM", r"[0-9]+"),
    ("OP_REL", r">=|<=|==|!=|>|<"),
    ("PUNTO_COMA", r";"),
    ("PARENT_IZQ", r"\("),
    ("PARENT_DER", r"\)"),
    ("ID", r"[A-Za-z_][A-Za-z0-9_]*"),
    ("ESPACIO", r"[ \t\r\n]+"),
    ("ERROR", r"[\s\S]"),
]
TOKEN_PATTERN = re.compile("|".join(f"(?P<{name}>{pattern})" for name, pattern in TOKEN_SPEC))


def tokenize(source: str) -> list[Token]:
    """Convierte texto en tokens con EOF; falla en el primer error léxico.

    Las tabulaciones cuentan como una columna. CRLF cuenta como un salto.
    Se limita cada literal a 1000 dígitos por recursos, no por la gramática.
    """
    tokens = []
    line, column = 1, 1
    for match in TOKEN_PATTERN.finditer(source):
        kind = match.lastgroup
        lexeme = match.group()
        if kind == "ERROR":
            raise LexerError(
                f"Error léxico en línea {line}, columna {column}: símbolo no reconocido {lexeme!r}."
            )
        if kind == "ID" and lexeme.upper() in RESERVED:
            kind = lexeme.upper()
        if kind == "NUM" and len(lexeme) > MAX_NUMBER_DIGITS:
            raise LexerError(
                f"Error léxico en línea {line}, columna {column}: "
                f"el número supera el límite de {MAX_NUMBER_DIGITS} dígitos."
            )
        if kind != "ESPACIO":
            tokens.append(Token(kind, lexeme, line, column, match.start()))
        # Normaliza saltos solo para calcular posiciones; el lexema se conserva.
        normalized = lexeme.replace("\r\n", "\n").replace("\r", "\n")
        if "\n" in normalized:
            line += normalized.count("\n")
            column = len(normalized.rsplit("\n", 1)[1]) + 1
        else:
            column += len(normalized)
    tokens.append(Token("EOF", "", line, column, len(source)))
    return tokens
