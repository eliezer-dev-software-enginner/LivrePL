# main.py
# Executa um script AdvPL (.prw) sem AppServer, sem licença, sem banco.
#
# Uso:
#   python main.py arquivo.prw [FuncaoDeEntrada]
#
# Exemplo:
#   python main.py exemplos/todas-etapas.prw
#   python main.py exemplos/ola.prw "ROTINA"

import json
import sys

from preprocessor import preprocess
from interpreter import run_source
from parser import parse_source, dump


def run_file(path: str, entry: str = "MAIN", args=None, dump_ast: bool = False,
             name_profile: str = "modern"):
    with open(path, encoding="utf-8", errors="replace") as f:
        source = f.read()

    source = preprocess(source)

    if dump_ast:
        program = parse_source(source)
        dump(program)
        return None

    return run_source(source, entry=entry, args=args, name_profile=name_profile)


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]

    dump_ast = False
    name_profile = "modern"
    args_json = None
    text_args = []
    rest = []
    index = 0
    while index < len(argv):
        a = argv[index]
        if a == "--ast":
            dump_ast = True
        elif a == "--args-json":
            index += 1
            if index >= len(argv):
                print("[ERRO] --args-json exige um array JSON", file=sys.stderr)
                return 2
            args_json = argv[index]
        elif a == "--arg":
            index += 1
            if index >= len(argv):
                print("[ERRO] --arg exige um valor de texto", file=sys.stderr)
                return 2
            text_args.append(argv[index])
        elif a == "--name-profile":
            index += 1
            if index >= len(argv) or argv[index] not in ("modern", "legacy10"):
                print("[ERRO] --name-profile aceita modern ou legacy10", file=sys.stderr)
                return 2
            name_profile = argv[index]
        else:
            rest.append(a)
        index += 1
    argv = rest

    if not 1 <= len(argv) <= 2:
        print("Uso: python main.py arquivo.prw [FuncaoDeEntrada] [--arg TEXTO ... | --args-json '[...]'] [--name-profile modern|legacy10] [--ast]")
        print("Ex.: python main.py exemplos/todas-etapas.prw")
        return 2

    path = argv[0]
    entry = argv[1] if len(argv) > 1 else "MAIN"

    if args_json is not None and text_args:
        print("[ERRO] --arg e --args-json nao podem ser usados juntos", file=sys.stderr)
        return 2

    entry_args = text_args or None
    if args_json is not None:
        try:
            entry_args = json.loads(args_json)
        except json.JSONDecodeError as exc:
            print(f"[ERRO] --args-json invalido: {exc.msg}", file=sys.stderr)
            return 2
        if not isinstance(entry_args, list):
            print("[ERRO] --args-json exige um array JSON", file=sys.stderr)
            return 2

    run_file(path, entry=entry, args=entry_args, dump_ast=dump_ast,
             name_profile=name_profile)

    return 0


if __name__ == "__main__":
    sys.exit(main())
