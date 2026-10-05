import unittest

from interpreter import AdvPLRuntimeError, run_source


def evaluate(expression):
    return run_source('Function Main()\nReturn ' + expression + '\n')


class AdditionalUtilityTests(unittest.TestCase):
    def test_sortable_date_format_and_parts(self):
        self.assertEqual('20240229', evaluate("DToS(SToD('20240229'))"))
        self.assertEqual('29/02/2024', evaluate("DToC(SToD('20240229'))"))
        self.assertEqual([29, 2, 2024], evaluate("{Day(SToD('20240229')), Month(SToD('20240229')), Year(SToD('20240229'))}"))
        self.assertEqual(' ' * 8, evaluate("DToS(SToD(''))"))
        self.assertEqual([0, 0, 0], evaluate("{Day(CToD('')), Month(CToD('')), Year(CToD(''))}"))
        self.assertTrue(evaluate("Empty(SToD('20230229'))"))
        self.assertTrue(evaluate("Empty(SToD('2024011'))"))

    def test_string_utilities(self):
        cases = {
            "Right('abcd', 2)": 'cd', "Right('abcd', 0)": '',
            "Replicate('ab', 3)": 'ababab', "Replicate('ab', 0)": '',
            "RAt('ab', 'abcab')": 4, "RAt('x', 'abc')": 0,
            "LTrim('  a  ')": 'a  ', "RTrim('  a  ')": '  a',
            "Trim('  a  ')": '  a', "Asc('A')": 65, "Asc('')": 0,
            "PadC('a', 4, '-')": '-a--', "PadC('abcde', 3)": 'abc',
        }
        for expression, expected in cases.items():
            with self.subTest(expression=expression):
                self.assertEqual(expected, evaluate(expression))

    def test_strzero_precision_sign_and_overflow(self):
        self.assertEqual('00042', evaluate('StrZero(42, 5)'))
        self.assertEqual('012.50', evaluate('StrZero(12.5, 6, 2)'))
        self.assertEqual('-0042', evaluate('StrZero(-42, 5)'))
        self.assertEqual('***', evaluate('StrZero(1234, 3)'))

    def test_chr_asc_roundtrip_cp1252_codes(self):
        self.assertEqual([65, 128, 231], evaluate('{Asc(Chr(65)), Asc(Chr(128)), Asc(Chr(231))}'))

    def test_multidimensional_array_has_independent_rows(self):
        self.assertEqual([[9, None], [None, None]], run_source('''Function Main()
Local a := Array(2, 2)
a[1][1] := 9
Return a
'''))

    def test_fill_copy_ranges_and_nested_array_references(self):
        self.assertEqual([0, 9, 9, 0], evaluate('AFill({0, 0, 0, 0}, 9, 2, 2)'))
        self.assertEqual([0, 2, 3], evaluate('ACopy({1, 2, 3}, {0, 0, 0}, 2, 2, 2)'))
        self.assertEqual([7, 7], run_source('''Function Main()
Local a := {{1}}
Local b := ACopy(a, {Nil})
b[1][1] := 7
Return {a[1][1], b[1][1]}
'''))
        self.assertEqual([8, 8], run_source('''Function Main()
Local a := AFill(Array(2), {1})
a[1][1] := 8
Return {a[1][1], a[2][1]}
'''))

    def test_insert_delete_keep_array_length(self):
        self.assertEqual([1, None, 2], evaluate('AIns({1, 2, 3}, 2)'))
        self.assertEqual([1, 3, None], evaluate('ADel({1, 2, 3}, 2)'))
        self.assertEqual(3, evaluate('ATail({1, 2, 3})'))
        self.assertIsNone(evaluate('ATail({})'))

    def test_aeval_passes_values_and_original_indices(self):
        self.assertEqual([[2, 2], [3, 3]], run_source('''Function Main()
Local a := {}
AEval({1, 2, 3, 4}, {|x, i| AAdd(a, {x, i})}, 2, 2)
Return a
'''))

    def test_seconds_is_consistent_with_runtime_clock(self):
        from interpreter import Interpreter
        from parser import parse_source
        runtime = Interpreter(parse_source('Function Main()\nReturn Seconds()\n'))
        runtime.builtins['TIME'] = lambda args: '12:34:56'
        self.assertEqual(45296, runtime.run())
        self.assertEqual(0, runtime.call_function('FError', []))

    def test_contains_operator_is_native(self):
        self.assertTrue(evaluate("'bc' $ 'abcd'"))
        self.assertFalse(evaluate("'BC' $ 'abcd'"))
        with self.assertRaises(AdvPLRuntimeError):
            evaluate("1 $ '123'")

    def test_invalid_types_and_ranges_raise_advpl_errors(self):
        for expression in ('Array(-1)', 'Array(.T.)', 'Right(1, 2)',
                           'AFill({}, 1, 0)', 'ACopy({}, {}, 1, 2, 0)',
                           'AEval({}, 1)', 'SToD(1)', 'DToS(1)', 'PadC(1, 3, \'\')'):
            with self.subTest(expression=expression):
                with self.assertRaises(AdvPLRuntimeError):
                    evaluate(expression)
