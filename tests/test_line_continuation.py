import unittest

from interpreter import run_source
from lexer import Lexer, TokenType


class LineContinuationTests(unittest.TestCase):
    def test_call_continues_after_trailing_comments(self):
        for newline in ("\n", "\r\n"):
            with self.subTest(newline=newline):
                source = newline.join([
                    "Function Main()",
                    "Return Receber( ; // argumentos",
                    "    'Solicitante', ; // titulo",
                    "    , ; // argumento omitido",
                    "    60 )",
                    "Function Receber(cTitulo, uVazio, nTamanho)",
                    "Return {cTitulo, uVazio, nTamanho}",
                    "",
                ])
                self.assertEqual(["Solicitante", None, 60], run_source(source))

    def test_regular_comment_preserves_statement_boundary(self):
        self.assertEqual(3, run_source(
            "Function Main()\n"
            "Local n := 1 // comentario\n"
            "n += 2\nReturn n\n"
        ))

    def test_comment_at_end_of_file_terminates(self):
        tokens = Lexer("1 ; // sem quebra final").tokenize()
        self.assertEqual([TokenType.NUMBER, TokenType.EOF],
                         [token.type for token in tokens])

    def test_continuation_preserves_line_numbers(self):
        tokens = Lexer("1 ; // comentario\n + 2\n").tokenize()
        self.assertEqual(2, tokens[1].line)
        self.assertEqual(TokenType.NEWLINE, tokens[-2].type)

    def test_comment_markers_in_strings_are_preserved(self):
        self.assertEqual("; // texto", run_source(
            "Function Main()\nReturn '; // texto'\n"
        ))


if __name__ == "__main__":
    unittest.main()
