import contextlib
import io
import uuid
import unittest
from datetime import date
from pathlib import Path

from advpl_date import AdvPLDate
from interpreter import AdvPLRuntimeError, Interpreter, run_source
from parser import parse_source


def evaluate(expression):
    return run_source("Function Main()\nReturn " + expression + "\n")


class StandardLibraryTests(unittest.TestCase):
    def test_clock_works_without_testlab(self):
        self.assertEqual(AdvPLDate.from_date(date.today()), evaluate("Date()"))
        self.assertRegex(evaluate("Time()"), r"^\d{2}:\d{2}:\d{2}$")
        self.assertEqual("D", evaluate("ValType(Date())"))

    def test_date_conversion_and_empty_date(self):
        self.assertEqual("29/02/2024", evaluate("DToC(CToD('29/02/2024'))"))
        self.assertTrue(evaluate("Empty(CToD('31/02/2024'))"))
        self.assertEqual("D", evaluate("ValType(CToD(''))"))
        self.assertEqual("", evaluate("DToC(CToD(''))"))
        self.assertEqual("05/10/2026", evaluate("CValToChar(CToD('05/10/2026'))"))

    def test_date_arithmetic_and_comparison(self):
        self.assertEqual("01/03/2024", evaluate("DToC(CToD('28/02/2024') + 2)"))
        self.assertEqual("28/02/2024", evaluate("DToC(CToD('01/03/2024') - 2)"))
        self.assertEqual(2, evaluate("CToD('01/03/2024') - CToD('28/02/2024')"))
        self.assertTrue(evaluate("CToD('01/03/2024') > CToD('28/02/2024')"))
        self.assertEqual("01/03/2024", evaluate("DToC(2 + CToD('28/02/2024'))"))
        with self.assertRaises(AdvPLRuntimeError):
            evaluate("Date() + '1'")
        with self.assertRaises(AdvPLRuntimeError):
            evaluate("Date() + 0.5")
        with self.assertRaises(AdvPLRuntimeError):
            evaluate("CToD('31/12/2999') + 1")
        self.assertTrue(evaluate("Empty(CToD('01/01/0099'))"))

    def test_text_utilities(self):
        self.assertEqual("abXXa", evaluate("StrTran('abbba', 'b', 'X', 2, 2)"))
        self.assertEqual("aa", evaluate("StrTran('abba', 'b')"))
        self.assertEqual("A", evaluate("Chr(65)"))
        self.assertEqual(3, evaluate("At('c', 'abcd')"))
        self.assertEqual(0, evaluate("At('x', 'abcd')"))
        self.assertEqual("ab", evaluate("Left('abcd', 2)"))
        self.assertEqual("texto", evaluate("EncodeUTF8('texto', 'cp1252')"))

    def test_aclone_recursively_copies_arrays(self):
        source = """Function Main()
Local a := {{1, 2}, 3}
Local b := AClone(a)
b[1][1] := 9
Return {a[1][1], b[1][1]}
"""
        self.assertEqual([1, 9], run_source(source))

    def test_aclone_preserves_cycles_without_recursion_error(self):
        result = run_source("Function Main()\nLocal a := {}\nAAdd(a, a)\nReturn AClone(a)\n")
        self.assertIs(result, result[0])

    def test_ascan_value_block_and_range(self):
        self.assertEqual(2, evaluate("AScan({1, 2, 3}, 2)"))
        self.assertEqual(3, evaluate("AScan({1, 2, 3}, {|x| x > 2})"))
        self.assertEqual(0, evaluate("AScan({1, 2, 3}, 3, 1, 2)"))

    def test_type_resolves_local_private_expression_and_unknown(self):
        self.assertEqual(["C", "N", "U", "D"], run_source("""Function Main()
Local c := 'abc'
Private n := 2
Return {Type('c'), Type('n + 1'), Type('ausente'), Type('Date()')}
"""))

    def test_errorblock_can_be_read_and_restored(self):
        self.assertEqual(["B", "U"], run_source("""Function Main()
Local bOld := ErrorBlock({|e| e})
Local cType := ValType(ErrorBlock())
ErrorBlock(bOld)
Return {cType, ValType(ErrorBlock())}
"""))

    def test_break_is_recovered(self):
        self.assertEqual("parou", run_source("""Function Main()
Local e
Begin Sequence
Break('parou')
Recover Using e
Return e
End Sequence
Return Nil
"""))

    def test_errorblock_receives_runtime_error_and_can_break_sequence(self):
        result = run_source("""Function Main()
Local e
ErrorBlock({|err| Break(err)})
Begin Sequence
Return 1 / 0
Recover Using e
Return e:Description
End Sequence
Return Nil
""")
        self.assertIn("zero", result)

    def test_type_probe_does_not_dispatch_errorblock(self):
        self.assertEqual("U", run_source("Function Main()\nErrorBlock({|err| Break(err)})\nReturn Type('ausente')\n"))

    def test_freeobj_clears_reference(self):
        self.assertEqual("U", run_source("""Function Main()
Local o := Objeto()
FreeObj(@o)
Return ValType(o)
Class Objeto
EndClass
"""))

    def test_transform_supported_masks(self):
        self.assertEqual("1,234.50", evaluate("Transform(1234.5, '9,999.99')"))
        self.assertEqual("1.234,50", evaluate("Transform(1234.5, '@E 9,999.99')"))
        self.assertEqual("ABC", evaluate("Transform('abc', '@!')"))

    def test_terminal_utilities(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            run_source("Function Main()\nConOut('log')\nAlert('aviso')\nReturn Nil\n")
        self.assertEqual("log\n[ALERTA] aviso\n", output.getvalue())

    def test_file_utilities_write_real_cp1252_bytes(self):
        path = Path(__file__).parent / ("saida-" + uuid.uuid4().hex + ".txt")
        self.addCleanup(path.unlink, missing_ok=True)
        runtime = Interpreter(parse_source("Function Main()\nReturn Nil\n"))
        handle = runtime.call_function("FCreate", [str(path)])
        try:
            self.assertGreaterEqual(handle, 0)
            self.assertEqual(3, runtime.call_function("FWrite", [handle, "açã"]))
        finally:
            if handle >= 0:
                self.assertTrue(runtime.call_function("FClose", [handle]))
        self.assertEqual("açã".encode("cp1252"), path.read_bytes())
        self.assertFalse(runtime.call_function("FClose", [handle]))
        self.assertNotEqual(0, runtime._file_error)

    def test_utilities_reject_invalid_arguments(self):
        for expression in ("Chr(.T.)", "Chr(256)", "DToC('2026-10-05')",
                           "CToD(1)", "Left(1, 2)", "AScan(1, 2)"):
            with self.subTest(expression=expression):
                with self.assertRaises(AdvPLRuntimeError):
                    evaluate(expression)
