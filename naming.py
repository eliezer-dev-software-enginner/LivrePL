from parser import VarDecl


class NameCollisionError(ValueError):
    pass


def _declarations(node):
    if isinstance(node, (list, tuple)):
        for item in node:
            yield from _declarations(item)
    elif hasattr(node, "__dict__"):
        if isinstance(node, VarDecl):
            yield node.name
        for value in vars(node).values():
            yield from _declarations(value)


class NamePolicy:
    def __init__(self, profile="modern"):
        if profile not in ("modern", "legacy10"):
            raise ValueError(f"Perfil de nomes desconhecido: '{profile}'")
        self.profile = profile

    def key(self, name):
        upper = name.upper()
        return upper[:10] if self.profile == "legacy10" else upper

    def user_symbol(self, name):
        upper = name.upper()
        return "U_" + (upper[:8] if self.profile == "legacy10" else upper)

    def validate_program(self, program):
        symbols = {}
        for function in program.functions:
            keys = [self.key(function.name)]
            if function.kind == "USER":
                keys.append(self.user_symbol(function.name))
            for key in keys:
                previous = symbols.get(key)
                if previous is not None and previous is not function:
                    raise NameCollisionError(
                        f"Funcoes '{previous.name}' e '{function.name}' "
                        f"colidem no simbolo '{key}' ({self.profile})"
                    )
                symbols[key] = function

        classes = {}
        for class_decl in program.classes:
            key = self.key(class_decl.name)
            previous = classes.get(key)
            if previous is not None:
                raise NameCollisionError(
                    f"Classes '{previous.name}' e '{class_decl.name}' "
                    f"colidem no simbolo '{key}' ({self.profile})"
                )
            classes[key] = class_decl

        methods = {}
        for method in program.methods:
            key = (self.key(method.class_name), self.key(method.method_name))
            previous = methods.get(key)
            if previous is not None:
                raise NameCollisionError(
                    f"Metodos '{previous.method_name}' e '{method.method_name}' "
                    f"colidem na classe '{method.class_name}' ({self.profile})"
                )
            methods[key] = method

        for callable_decl in (*program.functions, *program.methods):
            names = {}
            for name in (*callable_decl.params, *_declarations(callable_decl.body)):
                key = self.key(name)
                previous = names.get(key)
                if previous is not None and previous.upper() != name.upper():
                    raise NameCollisionError(
                        f"Variaveis '{previous}' e '{name}' colidem "
                        f"na funcao '{getattr(callable_decl, 'name', getattr(callable_decl, 'method_name', ''))}' "
                        f"({self.profile})"
                    )
                names[key] = name
