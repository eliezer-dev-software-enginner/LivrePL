# interpreter.py
# Etapa 3 + Etapa 4 do interpretador AdvPL: tree-walking executor
#
# A etapa 4 adiciona: objetos (CLASS/METHOD com herança FROM), code blocks
# ({|x,y| ...} com Eval()), DO CASE e BEGIN SEQUENCE/RECOVER.

from parser import (
    parse_source, Program, FunctionDecl, VarDecl, Assign, If, ForLoop,
    WhileLoop, Return, PrintStmt, LoopStmt, ExitStmt, ExprStmt, BinOp,
    UnaryOp, Literal, Identifier, ArrayLiteral, Index, Call,
    CaseStmt, SequenceStmt, BlockLiteral, MemberAccess, MethodCall,
)


class AdvPLRuntimeError(Exception):
    pass


class ReturnSignal(Exception):
    def __init__(self, value):
        self.value = value

class LoopSignal(Exception):
    pass

class ExitSignal(Exception):
    pass

class ThrownException(Exception):
    """Exceção lançada explicitamente pelo código AdvPL (UserException/Throw).
    Carrega o valor lançado (normalmente um objeto de erro com :Description,
    mas pode ser qualquer valor/objeto que o usuário decidir lançar)."""
    def __init__(self, value):
        self.value = value


# ---------- Frame de execução (pilha de chamadas) ----------

class Frame:
    def __init__(self, func_name, self_obj=None):
        self.func_name = func_name
        self.locals = {}    # LOCAL: só visível neste frame
        self.privates = {}  # PRIVATE: visível neste frame e nos frames filhos
        self.self_obj = self_obj  # objeto 'SELF', quando frame de um METHOD


# ---------- Runtime de objetos e code blocks (etapa 4) ----------

class AdvPLObject:
    def __init__(self, class_name):
        self.class_name = class_name
        self.attrs = {}


class AdvPLBlock:
    """Codeblock com closure de leitura sobre o frame onde foi criado
    (escopo v1: closure só de leitura, sem write-back para o frame original)."""
    def __init__(self, params, body_expr, captured_frame):
        self.params = params
        self.body_expr = body_expr
        self.captured_frame = captured_frame


# ---------- Interpretador ----------

class Interpreter:
    def __init__(self, program: Program):
        self.functions = {f.name.upper(): f for f in program.functions}
        self.classes = {c.name.upper(): c for c in program.classes}
        self.methods = {}
        for m in program.methods:
            self.methods[(m.class_name.upper(), m.method_name.upper())] = m
        self.globals = {}     # PUBLIC
        self.globals["CRLF"] = "\r\n"  # constante padrão do PROTHEUS.CH
        self.statics = {}     # nome_funcao -> {nome_var: valor}
        self.call_stack = []  # lista de Frame
        self.builtins = self._build_builtins()

    # --- ponto de entrada ---
    def run(self, entry="MAIN", args=None):
        if entry.upper() not in self.functions:
            raise AdvPLRuntimeError(f"Função de entrada '{entry}' não encontrada")
        return self.call_function(entry.upper(), args or [])

    # --- resolução/escrita de variáveis ---
    def declare(self, kind, name, value):
        upper = name.upper()
        frame = self.call_stack[-1]
        if kind == "LOCAL":
            frame.locals[upper] = value
        elif kind == "PRIVATE":
            frame.privates[upper] = value
        elif kind == "PUBLIC":
            self.globals[upper] = value
        elif kind == "STATIC":
            bucket = self.statics.setdefault(frame.func_name, {})
            # inicializador de STATIC só roda na primeira vez
            if upper not in bucket:
                bucket[upper] = value
        else:
            raise AdvPLRuntimeError(f"Tipo de declaração desconhecido: {kind}")

    def lookup(self, name):
        upper = name.upper()
        frame = self.call_stack[-1]

        if upper == "SELF":
            if frame.self_obj is not None:
                return frame.self_obj
            raise AdvPLRuntimeError("SELF usado fora de um METHOD")

        if upper in frame.locals:
            return frame.locals[upper]

        bucket = self.statics.get(frame.func_name)
        if bucket and upper in bucket:
            return bucket[upper]

        # PRIVATE: escopo dinâmico -- procura do frame atual até a base da pilha
        for f in reversed(self.call_stack):
            if upper in f.privates:
                return f.privates[upper]

        if upper in self.globals:
            return self.globals[upper]

        raise AdvPLRuntimeError(f"Variável '{name}' não declarada")

    def assign_existing(self, name, value):
        upper = name.upper()
        frame = self.call_stack[-1]

        if upper in frame.locals:
            frame.locals[upper] = value
            return

        bucket = self.statics.get(frame.func_name)
        if bucket and upper in bucket:
            bucket[upper] = value
            return

        for f in reversed(self.call_stack):
            if upper in f.privates:
                f.privates[upper] = value
                return

        if upper in self.globals:
            self.globals[upper] = value
            return

        # não declarada em lugar nenhum -> criada implicitamente como PRIVATE
        # (comportamento padrão do Clipper/AdvPL para atribuição sem declaração)
        frame.privates[upper] = value

    # --- chamada de função ---
    def call_function(self, name, args):
        upper = name.upper()

        if upper in self.functions:
            decl = self.functions[upper]
            frame = Frame(upper)
            for i, param in enumerate(decl.params):
                frame.locals[param.upper()] = args[i] if i < len(args) else None
            self.call_stack.append(frame)
            try:
                self.exec_block(decl.body)
                result = None
            except ReturnSignal as r:
                result = r.value
            finally:
                self.call_stack.pop()
            return result

        if upper in self.builtins:
            return self.builtins[upper](args)

        # se o nome chamado não é FUNCTION nem nativa, mas é o nome de uma
        # CLASS (ex.: Pessoa()), retorna uma instância "crua" da classe.
        # O padrão real do AdvPL: X() cria a instância, e :New(...) inicializa.
        if upper in self.classes:
            return self.instantiate(upper)

        raise AdvPLRuntimeError(f"Função '{name}' não encontrada")

    # --- classes e métodos (etapa 4) ---
    def class_chain(self, class_name_upper):
        """Do mais específico (folha) até o mais genérico (raiz), seguindo FROM."""
        chain = []
        cur = class_name_upper
        while cur and cur in self.classes:
            chain.append(cur)
            parent = self.classes[cur].parent
            cur = parent.upper() if parent else None
        return chain

    def instantiate(self, class_name_upper):
        decl = self.classes[class_name_upper]
        obj = AdvPLObject(decl.name)
        for cname in reversed(self.class_chain(class_name_upper)):  # raiz -> folha
            for field in self.classes[cname].data_fields:
                obj.attrs[field.upper()] = None
        return obj

    def call_method(self, obj, method_name, args):
        upper_method = method_name.upper()
        for cname in self.class_chain(obj.class_name.upper()):
            key = (cname, upper_method)
            if key in self.methods:
                decl = self.methods[key]
                frame = Frame(f"{cname}.{upper_method}", self_obj=obj)
                for i, param in enumerate(decl.params):
                    frame.locals[param.upper()] = args[i] if i < len(args) else None
                self.call_stack.append(frame)
                try:
                    self.exec_block(decl.body)
                    result = None
                except ReturnSignal as r:
                    result = r.value
                finally:
                    self.call_stack.pop()
                return result
        raise AdvPLRuntimeError(
            f"Método '{method_name}' não encontrado na classe '{obj.class_name}'"
        )

    # --- code blocks (etapa 4) ---
    def invoke_block(self, block, args):
        frame = Frame("(block)")
        frame.locals = dict(block.captured_frame.locals)  # closure de leitura
        for i, param in enumerate(block.params):
            frame.locals[param.upper()] = args[i] if i < len(args) else None
        self.call_stack.append(frame)
        try:
            return self.eval(block.body_expr)
        finally:
            self.call_stack.pop()

    # --- execução de comandos ---
    def exec_block(self, stmts):
        for stmt in stmts:
            self.exec_stmt(stmt)

    def exec_stmt(self, stmt):
        if isinstance(stmt, list):  # múltiplas VarDecl na mesma linha
            for s in stmt:
                self.exec_stmt(s)
            return

        if isinstance(stmt, VarDecl):
            value = self.eval(stmt.expr) if stmt.expr is not None else None
            self.declare(stmt.kind, stmt.name, value)

        elif isinstance(stmt, Assign):
            value = self.eval(stmt.expr)
            if stmt.op == "+=":
                value = self.apply_binop("+", self.eval(stmt.target), value)
            elif stmt.op == "-=":
                value = self.apply_binop("-", self.eval(stmt.target), value)
            self.assign_target(stmt.target, value)

        elif isinstance(stmt, If):
            for cond, body in stmt.branches:
                if truthy(self.eval(cond)):
                    self.exec_block(body)
                    return
            if stmt.else_body is not None:
                self.exec_block(stmt.else_body)

        elif isinstance(stmt, CaseStmt):
            for cond, body in stmt.branches:
                if truthy(self.eval(cond)):
                    self.exec_block(body)
                    return
            if stmt.otherwise_body is not None:
                self.exec_block(stmt.otherwise_body)

        elif isinstance(stmt, SequenceStmt):
            try:
                self.exec_block(stmt.body)
            except ThrownException as e:
                if stmt.recover_var:
                    self.assign_existing(stmt.recover_var, e.value)
                self.exec_block(stmt.recover_body)
            except (AdvPLRuntimeError, ZeroDivisionError, TypeError,
                     ValueError, IndexError) as e:
                if stmt.recover_var:
                    err_obj = AdvPLObject("ERROR")
                    err_obj.attrs["DESCRIPTION"] = str(e)
                    self.assign_existing(stmt.recover_var, err_obj)
                self.exec_block(stmt.recover_body)

        elif isinstance(stmt, ForLoop):
            start = self.eval(stmt.start)
            end = self.eval(stmt.end)
            step = self.eval(stmt.step) if stmt.step is not None else 1
            self.assign_or_declare_loopvar(stmt.var, start)
            while (step > 0 and self.lookup(stmt.var) <= end) or \
                  (step < 0 and self.lookup(stmt.var) >= end):
                try:
                    self.exec_block(stmt.body)
                except LoopSignal:
                    pass
                except ExitSignal:
                    break
                self.assign_existing(stmt.var, self.lookup(stmt.var) + step)

        elif isinstance(stmt, WhileLoop):
            while truthy(self.eval(stmt.cond)):
                try:
                    self.exec_block(stmt.body)
                except LoopSignal:
                    continue
                except ExitSignal:
                    break

        elif isinstance(stmt, Return):
            value = self.eval(stmt.expr) if stmt.expr is not None else None
            raise ReturnSignal(value)

        elif isinstance(stmt, PrintStmt):
            parts = [to_display(self.eval(e)) for e in stmt.exprs]
            text = " ".join(parts)
            if stmt.newline:
                print(text)
            else:
                print(text, end="")

        elif isinstance(stmt, LoopStmt):
            raise LoopSignal()

        elif isinstance(stmt, ExitStmt):
            raise ExitSignal()

        elif isinstance(stmt, ExprStmt):
            self.eval(stmt.expr)

        else:
            raise AdvPLRuntimeError(f"Comando não suportado: {type(stmt).__name__}")

    def assign_or_declare_loopvar(self, name, value):
        # a variável do FOR normalmente já foi declarada com LOCAL antes;
        # se não foi, cria como PRIVATE implicitamente (mesma regra de sempre)
        self.assign_existing(name, value)

    def assign_target(self, target, value):
        if isinstance(target, Identifier):
            self.assign_existing(target.name, value)
        elif isinstance(target, Index):
            container = self.eval(target.target)
            idx = self.eval(target.index_expr)
            if not isinstance(container, list):
                raise AdvPLRuntimeError("Tentativa de indexar valor que não é array")
            container[int(idx) - 1] = value  # arrays AdvPL são 1-based
        elif isinstance(target, MemberAccess):
            obj = self.eval(target.target)
            if not isinstance(obj, AdvPLObject):
                raise AdvPLRuntimeError("Tentativa de atribuir atributo em valor que não é objeto")
            obj.attrs[target.name.upper()] = value
        else:
            raise AdvPLRuntimeError("Alvo de atribuição inválido")

    # --- avaliação de expressões ---
    def eval(self, node):
        if isinstance(node, Literal):
            return node.value

        if isinstance(node, Identifier):
            return self.lookup(node.name)

        if isinstance(node, ArrayLiteral):
            return [self.eval(e) for e in node.elements]

        if isinstance(node, Index):
            container = self.eval(node.target)
            idx = self.eval(node.index_expr)
            if not isinstance(container, list):
                raise AdvPLRuntimeError("Tentativa de indexar valor que não é array")
            return container[int(idx) - 1]

        if isinstance(node, Call):
            args = [self.eval(a) for a in node.args]
            return self.call_function(node.name, args)

        if isinstance(node, UnaryOp):
            value = self.eval(node.expr)
            if node.op == "-":
                return -value
            if node.op == "+":
                return value
            if node.op == "NOT":
                return not truthy(value)
            raise AdvPLRuntimeError(f"Operador unário desconhecido: {node.op}")

        if isinstance(node, BinOp):
            if node.op == "AND":
                return truthy(self.eval(node.left)) and truthy(self.eval(node.right))
            if node.op == "OR":
                return truthy(self.eval(node.left)) or truthy(self.eval(node.right))
            left = self.eval(node.left)
            right = self.eval(node.right)
            return self.apply_binop(node.op, left, right)

        if isinstance(node, MemberAccess):
            obj = self.eval(node.target)
            if not isinstance(obj, AdvPLObject):
                raise AdvPLRuntimeError("Acesso de membro em valor que não é objeto")
            upper = node.name.upper()
            if upper not in obj.attrs:
                raise AdvPLRuntimeError(
                    f"Atributo '{node.name}' não existe em objetos da classe '{obj.class_name}'"
                )
            return obj.attrs[upper]

        if isinstance(node, MethodCall):
            obj = self.eval(node.target)
            args = [self.eval(a) for a in node.args]
            return self.call_method(obj, node.name, args)

        if isinstance(node, BlockLiteral):
            return AdvPLBlock(node.params, node.body, self.call_stack[-1])

        raise AdvPLRuntimeError(f"Nó de expressão não suportado: {type(node).__name__}")

    def apply_binop(self, op, left, right):
        if op == "+":
            if isinstance(left, str) and isinstance(right, str):
                return left + right
            if isinstance(left, (int, float)) and isinstance(right, (int, float)):
                return left + right
            raise AdvPLRuntimeError(f"Operação '+' inválida entre {type(left)} e {type(right)}")
        if op == "-":
            return left - right
        if op == "*":
            return left * right
        if op == "/":
            return left / right
        if op == "**":
            return left ** right
        if op == "==":
            return left == right
        if op == "<>":
            return left != right
        if op == "<":
            return left < right
        if op == ">":
            return left > right
        if op == "<=":
            return left <= right
        if op == ">=":
            return left >= right
        raise AdvPLRuntimeError(f"Operador binário desconhecido: {op}")

    # --- biblioteca padrão mínima ---
    def _build_builtins(self):
        def b_len(args):
            v = args[0]
            return len(v)

        def b_substr(args):
            s, start, *rest = args
            length = rest[0] if rest else len(s) - start + 1
            start = int(start)
            if start < 1:
                start = 1
            return s[start - 1: start - 1 + int(length)]

        def b_alltrim(args):
            return args[0].strip()

        def b_upper(args):
            return args[0].upper()

        def b_lower(args):
            return args[0].lower()

        def b_str(args):
            v = args[0]
            if isinstance(v, float) and v.is_integer():
                return str(int(v))
            return str(v)

        def b_cvaltochar(args):
            v = args[0]
            if v is None:
                return ""
            if isinstance(v, bool):
                return ".T." if v else ".F."
            if isinstance(v, float) and v.is_integer():
                return str(int(v))
            if isinstance(v, (int, float)):
                return str(v)
            if isinstance(v, str):
                return v
            raise AdvPLRuntimeError("cValToChar: tipo não suportado")

        def b_val(args):
            s = args[0].strip()
            try:
                if "." in s:
                    return float(s)
                return int(s)
            except ValueError:
                return 0

        def b_space(args):
            return " " * int(args[0])

        def b_padr(args):
            s, size = args[0], int(args[1])
            return s[:size].ljust(size)

        def b_padl(args):
            s, size = args[0], int(args[1])
            return s[:size].rjust(size)

        def b_aadd(args):
            arr, value = args[0], args[1]
            arr.append(value)
            return value

        def b_asize(args):
            arr, size = args[0], int(args[1])
            if size < len(arr):
                del arr[size:]
            else:
                arr.extend([None] * (size - len(arr)))
            return arr

        def b_alen(args):
            return len(args[0])

        def b_valtype(args):
            v = args[0]
            if v is None:
                return "U"
            if isinstance(v, bool):
                return "L"
            if isinstance(v, (int, float)):
                return "N"
            if isinstance(v, str):
                return "C"
            if isinstance(v, list):
                return "A"
            return "U"

        def b_empty(args):
            v = args[0]
            if v is None:
                return True
            if isinstance(v, (int, float)):
                return v == 0
            if isinstance(v, str):
                return v.strip() == ""
            if isinstance(v, list):
                return len(v) == 0
            if isinstance(v, bool):
                return v is False
            return False

        def b_iif(args):
            if len(args) != 3:
                raise AdvPLRuntimeError("IIf espera 3 argumentos")
            return args[1] if truthy(args[0]) else args[2]

        def b_round(args):
            v, decimals = args[0], int(args[1])
            return round(v, decimals)

        def b_int(args):
            return int(args[0])

        def b_abs(args):
            return abs(args[0])

        def b_max(args):
            return max(args[0], args[1])

        def b_min(args):
            return min(args[0], args[1])

        def b_eval(args):
            block, rest = args[0], args[1:]
            return self.invoke_block(block, rest)

        def b_userexception(args):
            msg = args[0] if args else ""
            err_obj = AdvPLObject("ERROR")
            err_obj.attrs["DESCRIPTION"] = msg
            raise ThrownException(err_obj)

        def b_throw(args):
            value = args[0] if args else None
            raise ThrownException(value)

        return {
            "LEN": b_len,
            "SUBSTR": b_substr,
            "ALLTRIM": b_alltrim,
            "UPPER": b_upper,
            "LOWER": b_lower,
            "STR": b_str,
            "CVALTOCHAR": b_cvaltochar,
            "VAL": b_val,
            "SPACE": b_space,
            "PADR": b_padr,
            "PADL": b_padl,
            "AADD": b_aadd,
            "ASIZE": b_asize,
            "ALEN": b_alen,
            "VALTYPE": b_valtype,
            "EMPTY": b_empty,
            "IIF": b_iif,
            "ROUND": b_round,
            "INT": b_int,
            "ABS": b_abs,
            "MAX": b_max,
            "MIN": b_min,
            "EVAL": b_eval,
            "USEREXCEPTION": b_userexception,
            "THROW": b_throw,
        }


# ---------- helpers ----------

def truthy(value):
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value != ""
    if isinstance(value, list):
        return len(value) > 0
    return True


def to_display(value):
    if value is None:
        return "NIL"
    if isinstance(value, bool):
        return ".T." if value else ".F."
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    if isinstance(value, list):
        return "{" + ", ".join(to_display(v) for v in value) + "}"
    if isinstance(value, AdvPLObject):
        return f"<Objeto {value.class_name}>"
    return str(value)


def run_source(source, entry="MAIN", args=None):
    program = parse_source(source)
    interpreter = Interpreter(program)
    return interpreter.run(entry, args)


if __name__ == "__main__":
    exemplo = '''
Function Main()
    Local nTotal := 0
    Local aItens := {10, 20, 30}
    Local i

    For i := 1 To Len(aItens)
        nTotal += aItens[i]
    Next

    If nTotal > 50
        ? "Total alto:", Str(nTotal)
    Else
        ? "Total baixo:", Str(nTotal)
    EndIf

    Private cMsg := "definida em Main"
    ? "Chamando MostraPrivate..."
    MostraPrivate()

    ? "AllTrim teste:", AllTrim("  espacos  ")
    ? "ValType nTotal:", ValType(nTotal)

Return NIL

Function MostraPrivate()
    ? "Dentro de MostraPrivate, cMsg =", cMsg
Return NIL
'''
    run_source(exemplo)
