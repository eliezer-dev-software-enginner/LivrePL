import contextlib
import io
import unittest
from pathlib import Path

from interpreter import AdvPLRuntimeError, run_source
from main import main


ROOT = Path(__file__).resolve().parents[1]


class ModuloTests(unittest.TestCase):
    def test_modulo_has_multiplication_precedence(self):
        self.assertEqual(
            [1, 3, 1],
            run_source(
                "Function Main()\n"
                "Return { 7 % 3, 1 + 7 % 3 * 2, 8 / 2 % 3 }\n"
            ),
        )

    def test_modulo_by_zero_reports_runtime_error(self):
        with self.assertRaisesRegex(AdvPLRuntimeError, "modulo por zero"):
            run_source("Function Main()\nReturn 5 % 0\n")

    def test_modulo_rejects_non_numeric_operands(self):
        with self.assertRaisesRegex(AdvPLRuntimeError, "operandos numericos"):
            run_source('Function Main()\nReturn "5" % 2\n')


class CliArgumentsTests(unittest.TestCase):
    def test_passes_json_array_to_entry(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = main([
                str(ROOT / "tests" / "fixtures" / "modulo.prw"),
                "Ex5",
                "--args-json",
                '["5"]',
            ])
        self.assertEqual(0, code)
        self.assertEqual("eh impar\n", output.getvalue())

    def test_rejects_non_array_json(self):
        error = io.StringIO()
        with contextlib.redirect_stderr(error):
            code = main([
                str(ROOT / "tests" / "fixtures" / "modulo.prw"),
                "Ex5",
                "--args-json",
                '"5"',
            ])
        self.assertEqual(2, code)
        self.assertIn("array JSON", error.getvalue())

    def test_text_argument_avoids_native_json_quoting(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = main([
                str(ROOT / "tests" / "fixtures" / "modulo.prw"),
                "Ex5",
                "--arg",
                "5",
            ])
        self.assertEqual(0, code)
        self.assertEqual("eh impar\n", output.getvalue())

    def test_numeric_argument_to_val_raises_exception(self):
        with self.assertRaisesRegex(AdvPLRuntimeError, "Val: esperado argumento caractere"):
            main([
                str(ROOT / "tests" / "fixtures" / "modulo.prw"),
                "Ex5",
                "--args-json",
                "[5]",
            ])

    def test_rejects_mixing_text_and_json_arguments(self):
        error = io.StringIO()
        with contextlib.redirect_stderr(error):
            code = main([
                str(ROOT / "tests" / "fixtures" / "modulo.prw"),
                "Ex5",
                "--arg",
                "5",
                "--args-json",
                '["5"]',
            ])
        self.assertEqual(2, code)
        self.assertIn("nao podem ser usados juntos", error.getvalue())

    def test_no_args_keeps_existing_entry_behavior(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = main([str(ROOT / "exemplos" / "ola.prw")])
        self.assertEqual(0, code)
        self.assertIn("Inicio da execucao", output.getvalue())


if __name__ == "__main__":
    unittest.main()
