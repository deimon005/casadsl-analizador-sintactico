"""Integración de la consola y límites de recursos documentados."""
import contextlib
import io
import json
import unittest
from unittest.mock import patch

from casadsl.__main__ import main
from casadsl.lexer import MAX_NUMBER_DIGITS, LexerError, tokenize
from casadsl.parser import MAX_NESTING, ParseError, parse


class CliTests(unittest.TestCase):
    def invoke(self, args, stdin=""):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err), \
                patch("sys.stdin", io.StringIO(stdin)):
            code = main(args)
        return code, out.getvalue(), err.getvalue()

    def test_json_output_is_machine_readable(self):
        code, out, err = self.invoke(["--text", "WHEN x > 1 THEN a b;", "--json"])
        self.assertEqual(code, 0)
        self.assertEqual(err, "")
        self.assertEqual(json.loads(out)["type"], "Program")

    def test_invalid_input_is_reported_on_stderr(self):
        code, out, err = self.invoke(["--text", "WHEN x > THEN a b;"])
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        self.assertIn("Error sintáctico", err)
        self.assertNotIn("Traceback", err)

    def test_stdin_is_supported(self):
        code, out, err = self.invoke([], stdin="WHEN x > 1 THEN a b;")
        self.assertEqual(code, 0)
        self.assertIn("1 regla(s)", out)
        self.assertEqual(err, "")

    def test_io_error_has_distinct_exit_code(self):
        with patch("casadsl.__main__.Path.read_text", side_effect=OSError("archivo inexistente")):
            code, out, err = self.invoke(["no_existe.casa"])
        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        self.assertIn("archivo inexistente", err)

    def test_grammar_json_is_complete(self):
        code, out, err = self.invoke(["--grammar-json"])
        self.assertEqual(code, 0)
        report = json.loads(out)
        self.assertEqual(report["conflicts"], [])
        self.assertEqual(len(report["table"]), 25)
        self.assertEqual(err, "")


class ResourceLimitTests(unittest.TestCase):
    def test_literal_at_digit_limit_is_accepted(self):
        source = "WHEN x == " + "9" * MAX_NUMBER_DIGITS + " THEN a b;"
        ast = parse(source)
        value = ast["rules"][0]["condition"]["value"]["value"]
        self.assertEqual(len(str(value)), MAX_NUMBER_DIGITS)

    def test_literal_over_digit_limit_has_useful_lexical_error(self):
        source = "WHEN x == " + "9" * (MAX_NUMBER_DIGITS + 1) + " THEN a b;"
        with self.assertRaises(LexerError) as caught:
            tokenize(source)
        self.assertIn(str(MAX_NUMBER_DIGITS), str(caught.exception))

    def test_deep_nesting_at_supported_limit(self):
        depth = MAX_NESTING - 1
        source = "WHEN " + "(" * depth + "x > 1" + ")" * depth + " THEN a b;"
        self.assertEqual(parse(source)["type"], "Program")

    def test_excessive_nesting_returns_parse_error(self):
        source = "WHEN " + "NOT " * MAX_NESTING + "x > 1 THEN a b;"
        with self.assertRaises(ParseError) as caught:
            parse(source)
        self.assertIn(str(MAX_NESTING), str(caught.exception))


if __name__ == "__main__":
    unittest.main()
