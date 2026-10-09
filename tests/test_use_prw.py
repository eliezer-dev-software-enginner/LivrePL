import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from main import run_file
from interpreter import AdvPLRuntimeError
from naming import NameCollisionError
from source_loader import SourceLoadError, discover_source_units


class UsePrwTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def write(self, name, source, encoding="utf-8"):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source, encoding=encoding)
        return path

    def test_recursive_relative_sources_and_user_symbols(self):
        main = self.write("main.prw", "//usePrw('sub/aux.prw')\nFunction Main()\nReturn U_Aux(3)\n")
        self.write("sub/aux.prw", "//usePrw('nested/leaf.prw')\nUser Function Aux(n)\nReturn U_Leaf(n)\n")
        self.write("sub/nested/leaf.prw", "User Function Leaf(n)\nReturn n * 2\n")
        self.assertEqual(6, run_file(main))

    def test_circular_and_repeated_imports_load_once(self):
        main = self.write("main.prw", "//usePrw('aux.prw')\n//usePrw('aux.prw')\nFunction Main()\nReturn Aux()\n")
        self.write("aux.prw", "//usePrw('main.prw')\nFunction Aux()\nReturn 42\n")
        self.assertEqual(2, len(discover_source_units(main)))
        self.assertEqual(42, run_file(main))

    def test_static_functions_and_state_are_isolated_by_source(self):
        main = self.write("main.prw", "//usePrw('a.prw')\n//usePrw('b.prw')\nFunction Main()\nReturn { U_A(), U_A(), U_B(), U_B() }\n")
        for name, value in (("A", 10), ("B", 100)):
            self.write(name.lower()+".prw", f"User Function {name}()\nReturn LocalCount()\nStatic Function LocalCount()\nStatic n := {value}\nn += 1\nReturn n\n")
        self.assertEqual([11, 12, 101, 102], run_file(main))

    def test_cannot_call_static_function_from_other_source(self):
        main = self.write("main.prw", "//usePrw('aux.prw')\nFunction Main()\nReturn Secret()\n")
        self.write("aux.prw", "Static Function Secret()\nReturn 1\n")
        with self.assertRaisesRegex(AdvPLRuntimeError, "Secret.*não encontrada"):
            run_file(main)

    def test_codeblock_keeps_source_scope(self):
        main = self.write("main.prw", "//usePrw('aux.prw')\nFunction Main()\nReturn Eval(U_Factory())\n")
        self.write("aux.prw", "User Function Factory()\nReturn {|| Secret()}\nStatic Function Secret()\nReturn 7\n")
        self.assertEqual(7, run_file(main))

    def test_missing_non_prw_and_escape_paths_fail(self):
        for reference in ("missing.prw", "missing.txt", "../outside.prw"):
            with self.subTest(reference=reference):
                main = self.write("main.prw", f"//usePrw('{reference}')\nFunction Main()\nReturn NIL\n")
                with self.assertRaises(SourceLoadError):
                    run_file(main)

    def test_public_collisions_include_legacy_profile(self):
        main = self.write("main.prw", "//usePrw('aux.prw')\nFunction AtualizaCadastroCliente()\nReturn NIL\n")
        self.write("aux.prw", "Function AtualizaCadastroFornecedor()\nReturn NIL\n")
        with self.assertRaises(NameCollisionError):
            run_file(main, entry="AtualizaCadastroCliente", name_profile="legacy10")
        self.write("aux.prw", "Function AtualizaCadastroCliente()\nReturn NIL\n")
        with self.assertRaises(NameCollisionError):
            run_file(main, entry="AtualizaCadastroCliente")

    def test_directive_inside_block_comment_is_ignored(self):
        main = self.write("main.prw", "/*\n//usePrw('missing.prw')\n*/\nFunction Main()\nReturn 4\n")
        self.assertEqual(4, run_file(main))

    def test_cp1252_and_bom_sources_and_ast(self):
        main = self.write("main.prw", "//usePrw('aux.prw')\nFunction Main()\nReturn Aux()\n", "utf-8-sig")
        self.write("aux.prw", 'Function Aux()\nReturn "ação"\n', "cp1252")
        self.assertEqual("ação", run_file(main))
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            run_file(main, dump_ast=True)
        self.assertIn("FunctionDecl Aux", output.getvalue())
