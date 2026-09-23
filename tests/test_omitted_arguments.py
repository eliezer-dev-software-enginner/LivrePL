import unittest

from interpreter import run_source
from parser import ParseError, parse_source


class OmittedArgumentsTests(unittest.TestCase):
    def test_middle_argument_omitted_with_block_comment(self):
        source = (
            "Function Main()\nReturn Receber('ZA1MASTER', /*cOwner*/, 7)\n"
            "Function Receber(cId, cOwner, nValor)\n"
            "Return {cId, cOwner, nValor}\n"
        )
        self.assertEqual(["ZA1MASTER", None, 7], run_source(source))

    def test_multiple_leading_and_trailing_omissions(self):
        source = (
            "Function Main()\nReturn Receber(, 2,,)\n"
            "Function Receber(a, b, c, d)\nReturn {a, b, c, d}\n"
        )
        self.assertEqual([None, 2, None, None], run_source(source))

    def test_empty_parentheses_still_mean_no_arguments(self):
        source = "Function Main()\nReturn Receber()\nFunction Receber(x)\nReturn x\n"
        self.assertIsNone(run_source(source))

    def test_omission_in_method_call_is_parsed(self):
        program = parse_source(
            "Function Main()\nLocal o := Criar()\nReturn o:AddFields('ZA1MASTER',, 7)\n"
        )
        call = program.functions[0].body[1].expr
        self.assertEqual(3, len(call.args))
        self.assertIsNone(call.args[1].value)

    def test_unrelated_invalid_argument_still_fails(self):
        with self.assertRaises(ParseError):
            parse_source("Function Main()\nReturn Receber(1 +, 2)\n")


if __name__ == "__main__":
    unittest.main()
