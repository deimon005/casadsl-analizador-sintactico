"""Pruebas de reconocimiento, estructura, posiciones y análisis formal."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from casadsl.lexer import LexerError, tokenize
from casadsl.parser import ParseError, Parser, parse
from casadsl.grammar import END, EPSILON, GRAMMAR, START, first_sets, follow_sets, ll1_table

ROOT = Path(__file__).resolve().parents[1]
CASES = json.loads((ROOT / "data" / "casos.json").read_text(encoding="utf-8"))


def condition(source: str) -> dict:
    return parse(f"WHEN {source} THEN activar alarma;")["rules"][0]["condition"]


class CorpusTests(unittest.TestCase):
    """Cada caso del corpus es un test independiente, visible en unittest."""


def make_corpus_test(case):
    def test(self):
        if case["expected"] == "valid":
            ast = parse(case["source"])
            self.assertEqual(ast["type"], "Program")
            self.assertGreaterEqual(len(ast["rules"]), 1)
        else:
            expected_error = LexerError if case["expected"] == "lexical_error" else ParseError
            with self.assertRaises(expected_error):
                parse(case["source"])
    test.__doc__ = case["observation"]
    return test


for case in CASES:
    setattr(CorpusTests, f"test_{case['id']}", make_corpus_test(case))


class LexerTests(unittest.TestCase):
    def test_longest_relational_operators(self):
        tokens = tokenize("x>=1 x<=2 x==3 x!=4 x>5 x<6")
        self.assertEqual([t.lexeme for t in tokens if t.type == "OP_REL"],
                         [">=", "<=", "==", "!=", ">", "<"])

    def test_reservadas_no_confunden_prefijos(self):
        tokens = tokenize("when Whenx THEN then_target")
        self.assertEqual([t.type for t in tokens], ["WHEN", "ID", "THEN", "ID", END])
        self.assertEqual(tokens[1].lexeme, "Whenx")

    def test_crlf_positions(self):
        tokens = tokenize("WHEN\r\n  x > 0")
        token = tokens[1]
        self.assertEqual((token.lexeme, token.line, token.column, token.offset), ("x", 2, 3, 8))

    def test_tab_is_one_source_column(self):
        token = tokenize("\tx")[0]
        self.assertEqual((token.line, token.column, token.offset), (1, 2, 1))

    def test_reject_unknown_character_at_exact_line(self):
        with self.assertRaises(LexerError) as caught:
            tokenize("WHEN\n x $ 1")
        message = str(caught.exception)
        self.assertIn("$", message)
        self.assertRegex(message.lower(), r"l[ií]nea\s*[:=]?\s*2")
        self.assertRegex(message.lower(), r"columna\s*[:=]?\s*4")

    def test_eof_is_explicit(self):
        tokens = tokenize("x\n")
        self.assertEqual(tokens[-1].type, END)
        self.assertEqual((tokens[-1].line, tokens[-1].column, tokens[-1].offset), (2, 1, 2))


class AstTests(unittest.TestCase):
    def test_single_rule_structure(self):
        self.assertEqual(parse("WHEN temp > 28 THEN encender ventilador;"), {
            "type": "Program", "rules": [{"type": "Rule", "condition": {
                "type": "Compare", "sensor": "temp", "operator": ">",
                "value": {"type": "Number", "value": 28}}, "action": {
                "type": "Action", "verb": "encender", "target": "ventilador"}}]})

    def test_and_has_priority_over_or(self):
        tree = condition("a > 1 OR b > 2 AND c > 3")
        self.assertEqual(tree["operator"], "OR")
        self.assertEqual(tree["left"]["sensor"], "a")
        self.assertEqual(tree["right"]["operator"], "AND")

    def test_parentheses_override_priority(self):
        tree = condition("(a > 1 OR b > 2) AND c > 3")
        self.assertEqual(tree["operator"], "AND")
        self.assertEqual(tree["left"]["operator"], "OR")
        self.assertEqual(tree["right"]["sensor"], "c")

    def test_not_has_priority_over_and(self):
        tree = condition("NOT a > 1 AND b > 2")
        self.assertEqual(tree["operator"], "AND")
        self.assertEqual(tree["left"]["type"], "Not")
        self.assertEqual(tree["left"]["operand"]["sensor"], "a")

    def test_not_can_wrap_compound_expression(self):
        tree = condition("NOT (a > 1 OR b > 2)")
        self.assertEqual(tree["type"], "Not")
        self.assertEqual(tree["operand"]["operator"], "OR")

    def test_left_associativity_or(self):
        tree = condition("a > 1 OR b > 2 OR c > 3")
        self.assertEqual(tree["operator"], "OR")
        self.assertEqual(tree["left"]["operator"], "OR")
        self.assertEqual(tree["right"]["sensor"], "c")

    def test_left_associativity_and(self):
        tree = condition("a > 1 AND b > 2 AND c > 3")
        self.assertEqual(tree["operator"], "AND")
        self.assertEqual(tree["left"]["operator"], "AND")
        self.assertEqual(tree["right"]["sensor"], "c")

    def test_boolean_ast_values_are_bool(self):
        for spelling, value in [("TRUE", True), ("false", False)]:
            with self.subTest(spelling=spelling):
                leaf = condition(f"x == {spelling}")["value"]
                self.assertEqual(leaf, {"type": "Boolean", "value": value})
                self.assertIs(type(leaf["value"]), bool)

    def test_identifiers_preserve_case(self):
        ast = parse("when SensorA > 1 then Encender LuzA;")
        rule = ast["rules"][0]
        self.assertEqual(rule["condition"]["sensor"], "SensorA")
        self.assertEqual(rule["action"]["verb"], "Encender")
        self.assertEqual(rule["action"]["target"], "LuzA")

    def test_token_api_accepts_lexed_program(self):
        source = "WHEN x > 1 THEN a b;"
        self.assertEqual(Parser(tokenize(source)).parse(), parse(source))


class ErrorTests(unittest.TestCase):
    def test_missing_then_reports_expected_keyword(self):
        with self.assertRaises(ParseError) as caught:
            parse("WHEN x > 1 activar alarma;")
        self.assertIn("THEN", str(caught.exception))

    def test_missing_target_reports_source_location(self):
        with self.assertRaises(ParseError) as caught:
            parse("\nWHEN temperatura > 25 THEN\n encender ;")
        message = str(caught.exception).lower()
        self.assertRegex(message, r"l[ií]nea\s*[:=]?\s*3")
        self.assertRegex(message, r"columna\s*[:=]?\s*11")

    def test_eof_in_error_is_human_readable(self):
        with self.assertRaises(ParseError) as caught:
            parse("WHEN x > 1 THEN a b")
        message = str(caught.exception)
        self.assertTrue("EOF" in message or "fin" in message.lower())
        self.assertTrue(";" in message or "PUNTO_COMA" in message)


class GrammarTests(unittest.TestCase):
    def test_first_all_nonterminals(self):
        self.assertEqual(first_sets(), {
            "Programa": {"WHEN"}, "RestoPrograma": {"WHEN", EPSILON},
            "Regla": {"WHEN"}, "Expr": {"NOT", "PARENT_IZQ", "ID"},
            "RestoOr": {"OR", EPSILON}, "Termino": {"NOT", "PARENT_IZQ", "ID"},
            "RestoAnd": {"AND", EPSILON}, "Factor": {"NOT", "PARENT_IZQ", "ID"},
            "Comparacion": {"ID"}, "Valor": {"NUM", "TRUE", "FALSE"}, "Accion": {"ID"}})

    def test_follow_all_nonterminals(self):
        self.assertEqual(follow_sets(), {
            "Programa": {END}, "RestoPrograma": {END}, "Regla": {"WHEN", END},
            "Expr": {"THEN", "PARENT_DER"}, "RestoOr": {"THEN", "PARENT_DER"},
            "Termino": {"OR", "THEN", "PARENT_DER"},
            "RestoAnd": {"OR", "THEN", "PARENT_DER"},
            "Factor": {"AND", "OR", "THEN", "PARENT_DER"},
            "Comparacion": {"AND", "OR", "THEN", "PARENT_DER"},
            "Valor": {"AND", "OR", "THEN", "PARENT_DER"},
            "Accion": {"PUNTO_COMA"}})

    def test_table_has_expected_epsilon_and_factor_entries(self):
        table = ll1_table()
        self.assertEqual(len(table), 25)
        self.assertEqual(table[("RestoPrograma", END)], ())
        self.assertEqual(table[("RestoOr", "PARENT_DER")], ())
        self.assertEqual(table[("RestoAnd", "OR")], ())
        self.assertEqual(table[("Factor", "NOT")], ("NOT", "Factor"))
        self.assertEqual(table[("Factor", "ID")], ("Comparacion",))

    def test_table_parser_agrees_with_recursive_parser_on_corpus(self):
        """Un reconocedor por pila contrasta el parser manual con la tabla formal."""
        table = ll1_table()
        for case in CASES:
            if case["expected"] == "lexical_error":
                continue
            with self.subTest(case=case["id"]):
                tokens = tokenize(case["source"])
                stack = [END, START]
                index = 0
                accepted = True
                while stack:
                    top = stack.pop()
                    lookahead = tokens[index].type
                    if top in GRAMMAR:
                        production = table.get((top, lookahead))
                        if production is None:
                            accepted = False
                            break
                        stack.extend(reversed(production))
                    elif top == lookahead:
                        index += 1
                    else:
                        accepted = False
                        break
                self.assertEqual(accepted and index == len(tokens), case["expected"] == "valid")


if __name__ == "__main__":
    unittest.main()
