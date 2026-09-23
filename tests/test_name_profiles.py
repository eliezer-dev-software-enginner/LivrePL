import contextlib
import io
import unittest
from pathlib import Path

from interpreter import run_source
from main import main
from naming import NameCollisionError


class NameProfileTests(unittest.TestCase):
    def test_cli_reports_legacy_collision_without_traceback(self):
        source = Path(__file__).parent / "fixtures" / "name_collision.prw"
        error = io.StringIO()
        with contextlib.redirect_stderr(error):
            code = main([str(source), "AtualizaCadastroCliente", "--name-profile", "legacy10"])
        self.assertEqual(1, code)
        self.assertIn("colidem", error.getvalue())
        self.assertNotIn("Traceback", error.getvalue())

    def test_modern_keeps_distinct_long_function_names(self):
        source = (
            "Function AtualizaCadastroCliente()\nReturn 1\n"
            "Function AtualizaCadastroFornecedor()\nReturn 2\n"
            "Function Main()\nReturn AtualizaCadastroCliente() + AtualizaCadastroFornecedor()\n"
        )
        self.assertEqual(3, run_source(source))

    def test_legacy_rejects_function_collision_at_ten_characters(self):
        source = (
            "Function AtualizaCadastroCliente()\nReturn 1\n"
            "Function AtualizaCadastroFornecedor()\nReturn 2\n"
        )
        with self.assertRaisesRegex(NameCollisionError, "AtualizaCadastroCliente.*AtualizaCadastroFornecedor"):
            run_source(source, name_profile="legacy10")

    def test_legacy_resolves_call_by_significant_prefix(self):
        source = (
            "Function AtualizaCadastroCliente()\nReturn 4\n"
            "Function Main()\nReturn AtualizaCadastroOutraCoisa()\n"
        )
        self.assertEqual(4, run_source(source, name_profile="legacy10"))

    def test_legacy_user_function_uses_eight_character_external_symbol(self):
        source = (
            "User Function ProcessaDados()\nReturn 1\n"
            "User Function ProcessaFila()\nReturn 2\n"
        )
        with self.assertRaisesRegex(NameCollisionError, "ProcessaDados.*ProcessaFila"):
            run_source(source, name_profile="legacy10")

    def test_legacy_resolves_user_function_external_symbol(self):
        source = (
            "User Function ProcessaDadosFaturamento()\nReturn 6\n"
            "Function Main()\nReturn U_ProcessaOutraCoisa()\n"
        )
        self.assertEqual(6, run_source(source, name_profile="legacy10"))

    def test_legacy_variable_names_share_first_ten_characters(self):
        source = (
            "Function Main()\n"
            "Local nTotalGeralAnual := 3\n"
            "nTotalGeralMensal := 7\n"
            "Return nTotalGeralAnual\n"
        )
        self.assertEqual(3, run_source(source))
        self.assertEqual(7, run_source(source, name_profile="legacy10"))

    def test_legacy_rejects_distinct_local_declarations_with_same_prefix(self):
        source = (
            "Function Main()\n"
            "Local nTotalGeralAnual := 3\n"
            "Local nTotalGeralMensal := 7\n"
            "Return Nil\n"
        )
        with self.assertRaisesRegex(NameCollisionError, "nTotalGeralAnual.*nTotalGeralMensal"):
            run_source(source, name_profile="legacy10")

    def test_legacy_rejects_class_name_collision(self):
        source = (
            "Class AtualizaCadastroCliente\nEndClass\n"
            "Class AtualizaCadastroFornecedor\nEndClass\n"
        )
        with self.assertRaisesRegex(NameCollisionError, "AtualizaCadastroCliente.*AtualizaCadastroFornecedor"):
            run_source(source, name_profile="legacy10")

    def test_legacy_rejects_method_collision(self):
        source = (
            "Class MinhaClasse\n"
            "Method AtualizaCadastroCliente()\n"
            "Method AtualizaCadastroFornecedor()\n"
            "EndClass\n"
            "Method AtualizaCadastroCliente() Class MinhaClasse\nReturn 1\n"
            "Method AtualizaCadastroFornecedor() Class MinhaClasse\nReturn 2\n"
        )
        with self.assertRaisesRegex(NameCollisionError, "AtualizaCadastroCliente.*AtualizaCadastroFornecedor"):
            run_source(source, name_profile="legacy10")


if __name__ == "__main__":
    unittest.main()
