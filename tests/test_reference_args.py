import contextlib
import io
import unittest
from pathlib import Path

from interpreter import AdvPLRuntimeError, run_source
from main import run_file
from parser import ParseError, parse_source


class ReferenceArgumentTests(unittest.TestCase):
    def test_reference_updates_caller_local(self):
        source = (
            "Function Main()\n"
            "Local n := 1\n"
            "Incrementar(@n)\n"
            "Return n\n"
            "Function Incrementar(nValor)\n"
            "nValor += 1\n"
            "Return NIL\n"
        )
        self.assertEqual(2, run_source(source))

    def test_without_at_scalar_is_passed_by_value(self):
        source = (
            "Function Main()\n"
            "Local n := 1\n"
            "Incrementar(n)\n"
            "Return n\n"
            "Function Incrementar(nValor)\n"
            "nValor += 1\n"
            "Return NIL\n"
        )
        self.assertEqual(1, run_source(source))

    def test_reference_can_be_forwarded(self):
        source = (
            "Function Main()\nLocal n := 1\nPrimeira(@n)\nReturn n\n"
            "Function Primeira(nValor)\nSegunda(@nValor)\nReturn NIL\n"
            "Function Segunda(nValor)\nnValor += 2\nReturn NIL\n"
        )
        self.assertEqual(3, run_source(source))

    def test_reference_to_undeclared_variable_has_source_line(self):
        with self.assertRaisesRegex(AdvPLRuntimeError, r"\[linha 2\].*NaoExiste"):
            run_source("Function Main()\nAlterar(@NaoExiste)\nReturn NIL\n")

    def test_at_requires_variable_name(self):
        with self.assertRaisesRegex(ParseError, "'@' exige nome de variável"):
            parse_source("Function Main()\nReturn Alterar(@5)\n")

    def test_at_outside_call_is_rejected(self):
        with self.assertRaisesRegex(AdvPLRuntimeError, "só pode ser usado em argumento"):
            run_source("Function Main()\nLocal n := 1\nReturn @n\n")

    def test_ex13b_equivalent_fixture(self):
        source_path = Path(__file__).parent / "fixtures" / "reference_args.prw"
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            run_file(str(source_path), entry="ex13")
        self.assertIn("Total positivos: 3", output.getvalue())
        self.assertIn("Total negativos: 3", output.getvalue())

    def test_reference_updates_public(self):
        source = (
            "Function Main()\nPublic n := 1\nIncrementar(@n)\nReturn n\n"
            "Function Incrementar(nValor)\nnValor += 1\nReturn NIL\n"
        )
        self.assertEqual(2, run_source(source))

    def test_reference_updates_private(self):
        source = (
            "Function Main()\nPrivate n := 1\nIncrementar(@n)\nReturn n\n"
            "Function Incrementar(nValor)\nnValor += 1\nReturn NIL\n"
        )
        self.assertEqual(2, run_source(source))

    def test_reference_updates_static(self):
        source = (
            "Function Main()\nStatic n := 1\nIncrementar(@n)\nReturn n\n"
            "Function Incrementar(nValor)\nnValor += 1\nReturn NIL\n"
        )
        self.assertEqual(2, run_source(source))

    def test_builtin_reference_is_rejected_explicitly(self):
        with self.assertRaisesRegex(AdvPLRuntimeError, "não suportada pela função nativa"):
            run_source("Function Main()\nLocal n := 1\nReturn Len(@n)\n")


if __name__ == "__main__":
    unittest.main()
