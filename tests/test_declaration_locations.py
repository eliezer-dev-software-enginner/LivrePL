import unittest

from parser import VarDecl, parse_source


class DeclarationLocationTests(unittest.TestCase):
    def test_declarations_keep_keyword_line(self):
        source = "Function Main()\n\nLocal nA := 1, nB := 2\nReturn nA\n"
        declarations = parse_source(source).functions[0].body[0]
        self.assertEqual([3, 3], [node.line for node in declarations])
        self.assertTrue(all(isinstance(node, VarDecl) for node in declarations))


if __name__ == "__main__":
    unittest.main()
