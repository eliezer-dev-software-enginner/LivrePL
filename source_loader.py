import re
from pathlib import Path

if __package__:
    from .preprocessor import preprocess
    from .parser import Program, parse_source
    from .naming import NamePolicy
else:
    from preprocessor import preprocess
    from parser import Program, parse_source
    from naming import NamePolicy


_USE_PRW = re.compile(r"^\s*//\s*usePrw\s*\(\s*(['\"])([^'\"]+)\1\s*\)\s*$", re.IGNORECASE)


class SourceLoadError(ValueError):
    pass


def _references(source):
    index = 0
    line_start = 0
    while index < len(source):
        if source[index] == "\n":
            line_start = index + 1
            index += 1
        elif source.startswith("/*", index):
            end = source.find("*/", index + 2)
            end = len(source) if end < 0 else end + 2
            last_line = source.rfind("\n", index, end)
            if last_line >= 0:
                line_start = last_line + 1
            index = end
        elif source.startswith("//", index):
            end = source.find("\n", index)
            end = len(source) if end < 0 else end
            match = _USE_PRW.fullmatch(source[line_start:end])
            if match:
                yield match.group(2)
            index = end
        elif source[index] in ("'", '"'):
            quote = source[index]
            index += 1
            while index < len(source):
                if source[index] == quote:
                    if index + 1 < len(source) and source[index + 1] == quote:
                        index += 2
                        continue
                    index += 1
                    break
                index += 1
        else:
            index += 1


def discover_source_units(path):
    root = Path(path).resolve()
    visited = set()
    units = []
    pending = [root]
    while pending:
        current = pending.pop()
        if current in visited:
            continue
        visited.add(current)
        try:
            raw = current.read_bytes()
            try:
                source = raw.decode("utf-8-sig")
            except UnicodeDecodeError:
                source = raw.decode("cp1252")
        except (OSError, UnicodeError) as error:
            raise SourceLoadError(f"Nao foi possivel ler fonte '{current}': {error}") from error
        units.append((current, source))
        dependencies = []
        for reference in _references(source):
            relative = Path(reference.replace("\\", "/"))
            dependency = (current.parent / relative).resolve()
            if relative.is_absolute() or re.match(r"^[A-Za-z]:", reference):
                raise SourceLoadError(f"usePrw em '{current}': caminho deve ser relativo: '{reference}'")
            if dependency.suffix.lower() != ".prw":
                raise SourceLoadError(f"usePrw em '{current}': dependencia deve ser .prw: '{reference}'")
            try:
                dependency.relative_to(root.parent)
            except ValueError:
                raise SourceLoadError(f"usePrw em '{current}': dependencia fora da pasta do fonte principal: '{reference}'")
            if not dependency.is_file():
                raise SourceLoadError(f"usePrw em '{current}': fonte nao encontrado: '{reference}'")
            dependencies.append(dependency)
        pending.extend(reversed(dependencies))
    return units


def compile_sources(source_units, name_profile="modern"):
    combined = Program([])
    combined.static_functions = {}
    policy = NamePolicy(name_profile)
    for source_name, source in source_units:
        source_name = str(source_name)
        try:
            program = parse_source(preprocess(source))
            policy.validate_program(program)
        except Exception as error:
            error.args = (f"Erro no fonte '{source_name}': {error}",)
            raise
        for declaration in (*program.functions, *program.methods):
            declaration.source_path = source_name
        combined.static_functions[source_name] = [f for f in program.functions if f.kind == "STATIC"]
        combined.functions.extend(f for f in program.functions if f.kind != "STATIC")
        combined.classes.extend(program.classes)
        combined.methods.extend(program.methods)
        if not hasattr(combined, "entry_source"):
            combined.entry_source = source_name
    policy.validate_program(combined)
    return combined
