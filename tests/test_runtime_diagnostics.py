import subprocess
import sys
import unittest
from pathlib import Path

from interpreter import AdvPLRuntimeError, run_source
from main import main


class RuntimeDiagnosticsTests(unittest.TestCase):
    def assert_runtime_error(self, expression, *parts):
        source = f"Function Main()\nLocal n := 1\nReturn {expression}\n"
        with self.assertRaises(AdvPLRuntimeError) as captured:
            run_source(source)
        message = str(captured.exception)
        self.assertIn("[linha 3]", message)
        self.assertNotIn("<class", message)
        for part in parts:
            self.assertIn(part, message)

    def test_text_plus_number_explains_conversion(self):
        self.assert_runtime_error('"Total: " + 7', "concatenar", "caractere", "numérico", "cValToChar")

    def test_number_plus_text_explains_conversion(self):
        self.assert_runtime_error('7 + " itens"', "concatenar", "numérico", "caractere")

    def test_division_by_zero(self):
        self.assert_runtime_error("10 / 0", "Divisão por zero", "'/'")

    def test_invalid_arithmetic_types(self):
        self.assert_runtime_error('"a" - 1', "'-'", "caractere", "numérico")

    def test_invalid_comparison_types(self):
        self.assert_runtime_error('"a" < 1', "'<'", "caractere", "numérico")

    def test_unknown_variable(self):
        self.assert_runtime_error("NaoExiste", "Variável 'NaoExiste' não declarada")

    def test_unknown_function(self):
        self.assert_runtime_error("NaoExiste()", "Função 'NaoExiste' não encontrada")

    def test_array_index_zero(self):
        self.assert_runtime_error("{10, 20}[0]", "Índice 0", "1..2")

    def test_array_index_out_of_bounds(self):
        self.assert_runtime_error("{10, 20}[3]", "Índice 3", "1..2")

    def test_array_index_non_integer(self):
        self.assert_runtime_error('{10, 20}["1"]', "Índice de array", "caractere")

    def test_len_with_number(self):
        self.assert_runtime_error("Len(5)", "Len", "caractere ou array", "numérico")

    def test_alltrim_with_number(self):
        self.assert_runtime_error("AllTrim(5)", "AllTrim", "caractere", "numérico")

    def test_aadd_with_non_array(self):
        self.assert_runtime_error('AAdd("texto", 1)', "AAdd", "array", "caractere")

    def test_unary_minus_with_text(self):
        self.assert_runtime_error('-"texto"', "unário '-'", "numérico", "caractere")

    def test_invalid_array_assignment(self):
        with self.assertRaises(AdvPLRuntimeError) as captured:
            run_source("Function Main()\nLocal a := {1}\na[0] := 2\nReturn a\n")
        self.assertIn("[linha 3]", str(captured.exception))
        self.assertIn("Índice 0", str(captured.exception))

    def test_invalid_compound_assignment(self):
        with self.assertRaises(AdvPLRuntimeError) as captured:
            run_source('Function Main()\nLocal c := "x"\nc += 1\nReturn c\n')
        self.assertIn("[linha 3]", str(captured.exception))
        self.assertIn("concatenar", str(captured.exception))

    def test_valid_operations_still_work(self):
        self.assertEqual([3, "Total: 7", 20], run_source(
            'Function Main()\nReturn {1 + 2, "Total: " + cValToChar(7), {10, 20}[2]}\n'
        ))

    def test_cli_raises_original_ex13_error(self):
        source_path = Path(__file__).parent / "fixtures" / "runtime_error.prw"
        with self.assertRaisesRegex(AdvPLRuntimeError, r"\[linha 3\].*cValToChar"):
            main([str(source_path), "ex13"])

    def test_script_displays_python_traceback_and_nonzero_exit(self):
        root = Path(__file__).resolve().parents[1]
        source_path = root / "tests" / "fixtures" / "runtime_error.prw"
        result = subprocess.run(
            [sys.executable, str(root / "main.py"), str(source_path), "ex13"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        self.assertNotEqual(0, result.returncode)
        self.assertIn("Traceback (most recent call last)", result.stderr)
        self.assertIn("AdvPLRuntimeError: [linha 3]", result.stderr)
        self.assertNotIn("[ERRO]", result.stderr)


if __name__ == "__main__":
    unittest.main()
