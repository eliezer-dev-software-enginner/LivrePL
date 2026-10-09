import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PackageCliTests(unittest.TestCase):
    def test_package_cli_runs_relative_source_without_shadowed_imports(self):
        with tempfile.TemporaryDirectory() as folder:
            cwd = Path(folder)
            (cwd / "teste.prw").write_text(
                'User Function Teste(cNome)\n? "Ola " + cNome\nReturn NIL\n',
                encoding="utf-8",
            )
            for name in ("parser", "lexer", "interpreter", "advpl_date", "standard_library"):
                (cwd / (name + ".py")).write_text('raise RuntimeError("shadow import")\n')
            code = (
                "import importlib.util, sys; "
                "from pathlib import Path; "
                "root=Path(sys.argv[1]); "
                "spec=importlib.util.spec_from_file_location('livrepl', root/'__init__.py', submodule_search_locations=[str(root)]); "
                "module=importlib.util.module_from_spec(spec); "
                "sys.modules['livrepl']=module; spec.loader.exec_module(module); "
                "from livrepl.main import main; "
                "raise SystemExit(main(['teste.prw','Teste','--arg','Dev']))"
            )
            result = subprocess.run([sys.executable, "-c", code, str(ROOT)], cwd=cwd,
                                    capture_output=True, text=True)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual("Ola Dev\n", result.stdout)
