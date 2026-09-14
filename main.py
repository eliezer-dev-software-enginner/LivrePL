# main.py
# Executa um script AdvPL (.prw) sem AppServer, sem licença, sem banco.
#
# Uso:
#   python main.py arquivo.prw [FuncaoDeEntrada]
#
# Exemplo:
#   python main.py exemplos/todas-etapas.prw
#   python main.py exemplos/ola.prw "ROTINA"

import sys

from preprocessor import preprocess
from interpreter import run_source, Interpreter, AdvPLRuntimeError
from parser import parse_source, dump, ParseError
from lexer import LexError


def run_file(path: str, entry: str = "MAIN", args=None, dump_ast: bool = False):
    with open(path, encoding="utf-8", errors="replace") as f:
        source = f.read()

    source = preprocess(source)

    if dump_ast:
        program = parse_source(source)
        dump(program)
        return None

    return run_source(source, entry=entry, args=args)


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]

    dump_ast = False
    rest = []
    for a in argv:
        if a == "--ast":
            dump_ast = True
        else:
            rest.append(a)
    argv = rest

    if len(argv) < 1:
        print("Uso: python main.py arquivo.prw [FuncaoDeEntrada] [--ast]")
        print("Ex.: python main.py exemplos/todas-etapas.prw")
        return 2

    path = argv[0]
    entry = argv[1] if len(argv) > 1 else "MAIN"

    try:
        run_file(path, entry=entry, dump_ast=dump_ast)
    except (ParseError, LexError, AdvPLRuntimeError) as e:
        print(f"[ERRO] {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())