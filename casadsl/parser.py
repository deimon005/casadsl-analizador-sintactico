"""Parser predictivo escrito a mano, con un token de anticipación.

Cada método corresponde a un no terminal. Los restos de listas se recorren
con bucles; la recursión queda en NOT y agrupaciones. El AST omite separadores
y paréntesis, pero conserva la precedencia y asociación de las condiciones.
"""

from .grammar import END, follow_sets
from .lexer import Token, tokenize


class ParseError(ValueError):
    """Error sintáctico con posición y expectativa concreta."""


MAX_NESTING = 100
_FOLLOW = follow_sets()


class Parser:
    """Consume una lista de Token terminada en EOF y construye un AST."""

    def __init__(self, tokens: list[Token]):
        if not tokens or tokens[-1].type != END:
            raise ValueError("La secuencia de tokens debe terminar en EOF.")
        if any(token.type == END for token in tokens[:-1]):
            raise ValueError("EOF solo puede aparecer al final de la secuencia.")
        self.tokens = tokens
        self.index = 0
        self.depth = 0

    @property
    def current(self) -> Token:
        return self.tokens[self.index]

    def fail(self, expected: str):
        token = self.current
        found = "fin de entrada" if token.type == END else f"{token.lexeme!r} ({token.type})"
        raise ParseError(
            f"Error sintáctico en línea {token.line}, columna {token.column}: "
            f"se esperaba {expected}; se encontró {found}."
        )

    def expect(self, kind: str, description: str | None = None) -> Token:
        if self.current.type != kind:
            self.fail(description or kind)
        token = self.current
        if kind != END:
            self.index += 1
        return token

    def parse(self) -> dict:
        """Programa -> Regla RestoPrograma; exige al menos una regla y EOF."""
        if self.current.type != "WHEN":
            self.fail("WHEN para iniciar una regla (el programa no puede estar vacío)")
        rules = [self.rule()]
        while self.current.type == "WHEN":
            rules.append(self.rule())
        # RestoPrograma -> epsilon solo sobre FOLLOW(RestoPrograma).
        if self.current.type not in _FOLLOW["RestoPrograma"]:
            self.fail("WHEN para otra regla o fin de entrada")
        self.expect(END)
        return {"type": "Program", "rules": rules}

    def rule(self) -> dict:
        """Regla -> WHEN Expr THEN Accion PUNTO_COMA."""
        self.expect("WHEN")
        condition = self.expression()
        self.expect("THEN", "la palabra reservada THEN")
        action = self.action()
        self.expect("PUNTO_COMA", "';' al final de la regla")
        return {"type": "Rule", "condition": condition, "action": action}

    def expression(self) -> dict:
        """Expr -> Termino RestoOr; acumula OR asociando a la izquierda."""
        node = self.term()
        while self.current.type == "OR":
            self.expect("OR")
            right = self.term()
            node = {"type": "Binary", "operator": "OR", "left": node, "right": right}
        if self.current.type not in _FOLLOW["RestoOr"]:
            self.fail("OR, THEN o ')' después de la condición")
        return node

    def term(self) -> dict:
        """Termino -> Factor RestoAnd; AND tiene mayor precedencia que OR."""
        node = self.factor()
        while self.current.type == "AND":
            self.expect("AND")
            right = self.factor()
            node = {"type": "Binary", "operator": "AND", "left": node, "right": right}
        if self.current.type not in _FOLLOW["RestoAnd"]:
            self.fail("AND, OR, THEN o ')' después de la comparación")
        return node

    def factor(self) -> dict:
        """Factor -> NOT Factor | '(' Expr ')' | Comparacion."""
        if self.depth >= MAX_NESTING:
            self.fail(f"una condición con menos de {MAX_NESTING} niveles de NOT/paréntesis")
        self.depth += 1
        try:
            if self.current.type == "NOT":
                self.expect("NOT")
                return {"type": "Not", "operand": self.factor()}
            if self.current.type == "PARENT_IZQ":
                self.expect("PARENT_IZQ")
                node = self.expression()
                self.expect("PARENT_DER", "')' para cerrar la agrupación")
                return node
            if self.current.type == "ID":
                return self.comparison()
            self.fail("un identificador de sensor, NOT o '(' para iniciar una condición")
        finally:
            self.depth -= 1

    def comparison(self) -> dict:
        """Comparacion -> ID OP_REL Valor."""
        sensor = self.expect("ID", "un identificador de sensor").lexeme
        operator = self.expect("OP_REL", "un operador relacional: >, <, >=, <=, == o !=").lexeme
        value = self.value()
        return {"type": "Compare", "sensor": sensor, "operator": operator, "value": value}

    def value(self) -> dict:
        """Valor -> NUM | TRUE | FALSE."""
        token = self.current
        if token.type == "NUM":
            self.expect("NUM")
            return {"type": "Number", "value": int(token.lexeme)}
        if token.type in {"TRUE", "FALSE"}:
            self.expect(token.type)
            return {"type": "Boolean", "value": token.type == "TRUE"}
        self.fail("un valor NUM, TRUE o FALSE después del operador relacional")

    def action(self) -> dict:
        """Accion -> ID ID (verbo y dispositivo)."""
        verb = self.expect("ID", "un identificador de acción después de THEN").lexeme
        target = self.expect("ID", "un identificador de dispositivo después de la acción").lexeme
        return {"type": "Action", "verb": verb, "target": target}


def parse(source: str) -> dict:
    """Entrada pública: texto -> lexer -> parser -> AST, sin ejecutar acciones."""
    return Parser(tokenize(source)).parse()
