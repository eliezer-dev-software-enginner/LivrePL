# parser.py
# Etapa 2 + correção de STATIC (etapa 3) + Etapa 4 do interpretador AdvPL:
# parser recursivo descendente -> AST
#
# A correção da etapa 3 desambigua "STATIC FUNCTION Foo()" (nova função) de
# "STATIC nVez := 0" (variável estática) via is_function_start/parse_function_body.
# A etapa 4 adiciona DO CASE, BEGIN SEQUENCE, code blocks e CLASS/METHOD.

from lexer import Lexer, TokenType


class ParseError(Exception):
    pass


# ---------- Nós da AST ----------

class Program:
    def __init__(self, functions, classes=None, methods=None):
        self.functions = functions
        self.classes = classes or []
        self.methods = methods or []

class FunctionDecl:
    def __init__(self, name, params, body):
        self.name = name
        self.params = params
        self.body = body

class VarDecl:
    def __init__(self, kind, name, expr):
        self.kind = kind   # LOCAL, PRIVATE, PUBLIC, STATIC
        self.name = name
        self.expr = expr

class Assign:
    def __init__(self, target, op, expr):
        self.target = target  # Identifier, Index ou MemberAccess
        self.op = op          # ':=', '+=', '-='
        self.expr = expr

class If:
    def __init__(self, branches, else_body):
        self.branches = branches      # lista de (cond, body)
        self.else_body = else_body

class ForLoop:
    def __init__(self, var, start, end, step, body):
        self.var = var
        self.start = start
        self.end = end
        self.step = step
        self.body = body

class WhileLoop:
    def __init__(self, cond, body):
        self.cond = cond
        self.body = body

class Return:
    def __init__(self, expr):
        self.expr = expr

class PrintStmt:
    def __init__(self, exprs, newline):
        self.exprs = exprs
        self.newline = newline  # True para '?', False para '??'

class LoopStmt:
    pass

class ExitStmt:
    pass

class ExprStmt:
    def __init__(self, expr):
        self.expr = expr

# --- nós da etapa 4 ---

class CaseStmt:
    def __init__(self, branches, otherwise_body):
        self.branches = branches            # lista de (cond, body)
        self.otherwise_body = otherwise_body

class SequenceStmt:
    def __init__(self, body, recover_var, recover_body):
        self.body = body
        self.recover_var = recover_var  # nome em RECOVER USING x, ou None
        self.recover_body = recover_body

class BlockLiteral:
    def __init__(self, params, body):
        self.params = params  # lista de nomes
        self.body = body      # única expressão (escopo v1)

class MemberAccess:
    def __init__(self, target, name):
        self.target = target
        self.name = name

class MethodCall:
    def __init__(self, target, name, args):
        self.target = target
        self.name = name
        self.args = args

class ClassDecl:
    def __init__(self, name, parent, data_fields, method_sigs):
        self.name = name
        self.parent = parent              # nome da classe pai, ou None
        self.data_fields = data_fields
        self.method_sigs = method_sigs    # lista de (nome, is_constructor)

class MethodDecl:
    def __init__(self, class_name, method_name, params, body):
        self.class_name = class_name
        self.method_name = method_name
        self.params = params
        self.body = body

# --- nós das etapas 1-3 ---

class BinOp:
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right

class UnaryOp:
    def __init__(self, op, expr):
        self.op = op
        self.expr = expr

class Literal:
    def __init__(self, value):
        self.value = value

class Identifier:
    def __init__(self, name):
        self.name = name

class ArrayLiteral:
    def __init__(self, elements):
        self.elements = elements

class Index:
    def __init__(self, target, index_expr):
        self.target = target
        self.index_expr = index_expr

class Call:
    def __init__(self, name, args):
        self.name = name
        self.args = args


# ---------- Parser ----------

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    # --- utilidades ---
    def peek(self, offset=0):
        return self.tokens[self.pos + offset]

    def current(self):
        return self.peek()

    def at(self, *types):
        return self.current().type in types

    def advance(self):
        tok = self.tokens[self.pos]
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
        return tok

    def expect(self, type_, msg=None):
        if self.current().type != type_:
            raise ParseError(
                msg or f"Esperado {type_}, encontrado {self.current().type} "
                       f"({self.current().value!r}) na linha {self.current().line}"
            )
        return self.advance()

    def skip_newlines(self):
        while self.at(TokenType.NEWLINE):
            self.advance()

    def skip_terminator(self):
        # fim de comando: uma ou mais quebras de linha (ou EOF)
        if self.at(TokenType.EOF):
            return
        if not self.at(TokenType.NEWLINE):
            raise ParseError(
                f"Esperado fim de linha, encontrado {self.current().type} "
                f"na linha {self.current().line}"
            )
        self.skip_newlines()

    # --- ponto de entrada ---
    def parse_program(self):
        functions, classes, methods = [], [], []
        self.skip_newlines()
        while not self.at(TokenType.EOF):
            if self.at(TokenType.CLASS):
                classes.append(self.parse_class())
            elif self.at(TokenType.METHOD):
                methods.append(self.parse_method_impl())
            else:
                functions.append(self.parse_function())
            self.skip_newlines()
        return Program(functions, classes, methods)

    def is_function_start(self):
        # Um novo bloco de topo começa em: FUNCTION, STATIC FUNCTION,
        # USER FUNCTION, CLASS, ou METHOD
        if self.at(TokenType.FUNCTION):
            return True
        if self.at(TokenType.STATIC, TokenType.USER) and self.peek(1).type == TokenType.FUNCTION:
            return True
        if self.at(TokenType.CLASS, TokenType.METHOD):
            return True
        return False

    def parse_function(self):
        if self.at(TokenType.STATIC, TokenType.USER):
            self.advance()
        self.expect(TokenType.FUNCTION)
        name = self.expect(TokenType.IDENTIFIER).value
        self.expect(TokenType.LPAREN)
        params = []
        if not self.at(TokenType.RPAREN):
            params.append(self.expect(TokenType.IDENTIFIER).value)
            while self.at(TokenType.COMMA):
                self.advance()
                params.append(self.expect(TokenType.IDENTIFIER).value)
        self.expect(TokenType.RPAREN)
        self.skip_terminator()

        body = self.parse_function_body()
        return FunctionDecl(name, params, body)

    def parse_function_body(self):
        stmts = []
        self.skip_newlines()
        while not (self.is_function_start() or self.at(TokenType.EOF)):
            stmts.append(self.parse_statement())
            self.skip_terminator()
        return stmts

    def parse_statement_list(self, stop_types):
        stmts = []
        self.skip_newlines()
        while not self.at(*stop_types):
            stmts.append(self.parse_statement())
            self.skip_terminator()
        return stmts

    # --- statements ---
    def parse_statement(self):
        t = self.current().type

        if t in (TokenType.LOCAL, TokenType.PRIVATE, TokenType.PUBLIC, TokenType.STATIC):
            return self.parse_vardecl()
        if t == TokenType.IF:
            return self.parse_if()
        if t == TokenType.FOR:
            return self.parse_for()
        if t == TokenType.WHILE:
            return self.parse_while()
        if t == TokenType.DO:
            if self.peek(1).type == TokenType.CASE:
                return self.parse_docase()
            return self.parse_while()
        if t == TokenType.BEGIN:
            return self.parse_sequence()
        if t == TokenType.RETURN:
            return self.parse_return()
        if t == TokenType.LOOP:
            self.advance()
            return LoopStmt()
        if t == TokenType.EXIT:
            self.advance()
            return ExitStmt()
        if t == TokenType.IDENTIFIER and self.current().value in ("?", "??"):
            return self.parse_print()

        return self.parse_assign_or_call()

    def parse_vardecl(self):
        kind = self.advance().type.name  # LOCAL/PRIVATE/PUBLIC/STATIC
        decls = []
        name = self.expect(TokenType.IDENTIFIER).value
        expr = None
        if self.at(TokenType.ASSIGN):
            self.advance()
            expr = self.parse_expr()
        decls.append(VarDecl(kind, name, expr))
        while self.at(TokenType.COMMA):
            self.advance()
            name = self.expect(TokenType.IDENTIFIER).value
            expr = None
            if self.at(TokenType.ASSIGN):
                self.advance()
                expr = self.parse_expr()
            decls.append(VarDecl(kind, name, expr))
        # Se houver mais de uma declaração na mesma linha, devolvemos
        # uma lista "achatada" -- o interpretador trata VarDecl individualmente.
        if len(decls) == 1:
            return decls[0]
        return decls  # o interpretador precisa saber lidar com listas

    def parse_if(self):
        self.expect(TokenType.IF)
        cond = self.parse_expr()
        self.skip_terminator()
        branches = []
        body = self.parse_statement_list(
            stop_types=(TokenType.ELSEIF, TokenType.ELSE, TokenType.ENDIF)
        )
        branches.append((cond, body))
        while self.at(TokenType.ELSEIF):
            self.advance()
            cond = self.parse_expr()
            self.skip_terminator()
            body = self.parse_statement_list(
                stop_types=(TokenType.ELSEIF, TokenType.ELSE, TokenType.ENDIF)
            )
            branches.append((cond, body))
        else_body = None
        if self.at(TokenType.ELSE):
            self.advance()
            self.skip_terminator()
            else_body = self.parse_statement_list(stop_types=(TokenType.ENDIF,))
        self.expect(TokenType.ENDIF)
        return If(branches, else_body)

    def parse_for(self):
        self.expect(TokenType.FOR)
        var = self.expect(TokenType.IDENTIFIER).value
        self.expect(TokenType.ASSIGN)
        start = self.parse_expr()
        self.expect(TokenType.TO)
        end = self.parse_expr()
        step = None
        if self.at(TokenType.STEP):
            self.advance()
            step = self.parse_expr()
        self.skip_terminator()
        body = self.parse_statement_list(stop_types=(TokenType.NEXT,))
        self.expect(TokenType.NEXT)
        if self.at(TokenType.IDENTIFIER):
            self.advance()  # 'NEXT x' -- nome da variável é opcional/documentacional
        return ForLoop(var, start, end, step, body)

    def parse_while(self):
        if self.at(TokenType.DO):
            self.advance()
        self.expect(TokenType.WHILE)
        cond = self.parse_expr()
        self.skip_terminator()
        body = self.parse_statement_list(stop_types=(TokenType.ENDDO,))
        self.expect(TokenType.ENDDO)
        return WhileLoop(cond, body)

    def parse_docase(self):
        self.expect(TokenType.DO)
        self.expect(TokenType.CASE)
        self.skip_terminator()
        branches = []
        while self.at(TokenType.CASE):
            self.advance()
            cond = self.parse_expr()
            self.skip_terminator()
            body = self.parse_statement_list(
                stop_types=(TokenType.CASE, TokenType.OTHERWISE, TokenType.ENDCASE)
            )
            branches.append((cond, body))
        otherwise_body = None
        if self.at(TokenType.OTHERWISE):
            self.advance()
            self.skip_terminator()
            otherwise_body = self.parse_statement_list(stop_types=(TokenType.ENDCASE,))
        self.expect(TokenType.ENDCASE)
        return CaseStmt(branches, otherwise_body)

    def parse_sequence(self):
        self.expect(TokenType.BEGIN)
        self.expect(TokenType.SEQUENCE)
        self.skip_terminator()
        body = self.parse_statement_list(stop_types=(TokenType.RECOVER, TokenType.END))
        recover_var, recover_body = None, []
        if self.at(TokenType.RECOVER):
            self.advance()
            if self.at(TokenType.USING):
                self.advance()
                recover_var = self.expect(TokenType.IDENTIFIER).value
            self.skip_terminator()
            recover_body = self.parse_statement_list(stop_types=(TokenType.END,))
        self.expect(TokenType.END)
        self.expect(TokenType.SEQUENCE)
        return SequenceStmt(body, recover_var, recover_body)

    def parse_return(self):
        self.expect(TokenType.RETURN)
        expr = None
        if not self.at(TokenType.NEWLINE, TokenType.EOF):
            expr = self.parse_expr()
        return Return(expr)

    def parse_print(self):
        newline = self.current().value == "?"
        self.advance()
        exprs = []
        if not self.at(TokenType.NEWLINE, TokenType.EOF):
            exprs.append(self.parse_expr())
            while self.at(TokenType.COMMA):
                self.advance()
                exprs.append(self.parse_expr())
        return PrintStmt(exprs, newline)

    def parse_assign_or_call(self):
        expr = self.parse_postfix()
        if self.at(TokenType.ASSIGN, TokenType.PLUS_ASSIGN, TokenType.MINUS_ASSIGN):
            op = self.advance().value
            value = self.parse_expr()
            return Assign(expr, op, value)
        return ExprStmt(expr)

    # --- declaração de classe e implementação de método (etapa 4) ---

    def parse_class(self):
        self.expect(TokenType.CLASS)
        name = self.expect(TokenType.IDENTIFIER).value
        parent = None
        if self.at(TokenType.FROM):
            self.advance()
            parent = self.expect(TokenType.IDENTIFIER).value
        self.skip_terminator()

        data_fields, method_sigs = [], []
        while not self.at(TokenType.ENDCLASS):
            if self.at(TokenType.DATA):
                self.advance()
                data_fields.append(self.expect(TokenType.IDENTIFIER).value)
                self.skip_terminator()
            elif self.at(TokenType.METHOD):
                self.advance()
                mname = self.expect(TokenType.IDENTIFIER).value
                self.expect(TokenType.LPAREN)
                while not self.at(TokenType.RPAREN):
                    self.advance()
                self.expect(TokenType.RPAREN)
                is_ctor = False
                if self.at(TokenType.CONSTRUCTOR):
                    self.advance()
                    is_ctor = True
                method_sigs.append((mname, is_ctor))
                self.skip_terminator()
            else:
                raise ParseError(
                    f"Esperado DATA ou METHOD dentro de CLASS, encontrado "
                    f"{self.current().type} na linha {self.current().line}"
                )
        self.expect(TokenType.ENDCLASS)
        return ClassDecl(name, parent, data_fields, method_sigs)

    def parse_method_impl(self):
        self.expect(TokenType.METHOD)
        method_name = self.expect(TokenType.IDENTIFIER).value
        self.expect(TokenType.LPAREN)
        params = []
        if not self.at(TokenType.RPAREN):
            params.append(self.expect(TokenType.IDENTIFIER).value)
            while self.at(TokenType.COMMA):
                self.advance()
                params.append(self.expect(TokenType.IDENTIFIER).value)
        self.expect(TokenType.RPAREN)
        if self.at(TokenType.CONSTRUCTOR):
            self.advance()
        self.expect(TokenType.CLASS)
        class_name = self.expect(TokenType.IDENTIFIER).value
        self.skip_terminator()
        body = self.parse_function_body()
        return MethodDecl(class_name, method_name, params, body)

    # --- expressões (precedência) ---
    def parse_expr(self):
        return self.parse_or()

    def parse_or(self):
        left = self.parse_and()
        while self.at(TokenType.OR):
            self.advance()
            right = self.parse_and()
            left = BinOp(left, "OR", right)
        return left

    def parse_and(self):
        left = self.parse_not()
        while self.at(TokenType.AND):
            self.advance()
            right = self.parse_not()
            left = BinOp(left, "AND", right)
        return left

    def parse_not(self):
        if self.at(TokenType.NOT):
            self.advance()
            expr = self.parse_not()
            return UnaryOp("NOT", expr)
        return self.parse_comparison()

    def parse_comparison(self):
        left = self.parse_additive()
        while self.at(TokenType.EQ, TokenType.NEQ, TokenType.LT,
                      TokenType.GT, TokenType.LTE, TokenType.GTE):
            op = self.advance().value
            right = self.parse_additive()
            left = BinOp(left, op, right)
        return left

    def parse_additive(self):
        left = self.parse_term()
        while self.at(TokenType.PLUS, TokenType.MINUS):
            op = self.advance().value
            right = self.parse_term()
            left = BinOp(left, op, right)
        return left

    def parse_term(self):
        left = self.parse_power()
        while self.at(TokenType.STAR, TokenType.SLASH):
            op = self.advance().value
            right = self.parse_power()
            left = BinOp(left, op, right)
        return left

    def parse_power(self):
        left = self.parse_unary()
        if self.at(TokenType.POWER):
            self.advance()
            right = self.parse_power()  # associatividade à direita
            return BinOp(left, "**", right)
        return left

    def parse_unary(self):
        if self.at(TokenType.MINUS, TokenType.PLUS):
            op = self.advance().value
            expr = self.parse_unary()
            return UnaryOp(op, expr)
        return self.parse_postfix()

    def parse_postfix(self):
        expr = self.parse_primary()
        while True:
            if self.at(TokenType.LPAREN):
                self.advance()
                args = []
                if not self.at(TokenType.RPAREN):
                    args.append(self.parse_expr())
                    while self.at(TokenType.COMMA):
                        self.advance()
                        args.append(self.parse_expr())
                self.expect(TokenType.RPAREN)
                if isinstance(expr, Identifier):
                    expr = Call(expr.name, args)
                elif isinstance(expr, MemberAccess):
                    expr = MethodCall(expr.target, expr.name, args)
                else:
                    raise ParseError("Chamada inválida")
            elif self.at(TokenType.LBRACKET):
                self.advance()
                idx = self.parse_expr()
                self.expect(TokenType.RBRACKET)
                expr = Index(expr, idx)
            elif self.at(TokenType.COLON):
                self.advance()
                name = self.expect(TokenType.IDENTIFIER).value
                expr = MemberAccess(expr, name)
            else:
                break
        return expr

    def parse_primary(self):
        tok = self.current()

        if tok.type == TokenType.NUMBER:
            self.advance()
            return Literal(tok.value)
        if tok.type == TokenType.STRING:
            self.advance()
            return Literal(tok.value)
        if tok.type == TokenType.LOGICAL:
            self.advance()
            return Literal(tok.value)
        if tok.type == TokenType.NIL:
            self.advance()
            return Literal(None)
        if tok.type == TokenType.IDENTIFIER:
            self.advance()
            return Identifier(tok.value)
        if tok.type == TokenType.DCOLON:
            self.advance()
            name = self.expect(TokenType.IDENTIFIER).value
            return MemberAccess(Identifier("SELF"), name)
        if tok.type == TokenType.LPAREN:
            self.advance()
            expr = self.parse_expr()
            self.expect(TokenType.RPAREN)
            return expr
        if tok.type == TokenType.LBRACE:
            self.advance()
            if self.at(TokenType.PIPE):
                return self.parse_block_literal()
            elements = []
            if not self.at(TokenType.RBRACE):
                elements.append(self.parse_expr())
                while self.at(TokenType.COMMA):
                    self.advance()
                    elements.append(self.parse_expr())
            self.expect(TokenType.RBRACE)
            return ArrayLiteral(elements)

        raise ParseError(
            f"Token inesperado {tok.type} ({tok.value!r}) na linha {tok.line}"
        )

    def parse_block_literal(self):
        self.expect(TokenType.PIPE)
        params = []
        if not self.at(TokenType.PIPE):
            params.append(self.expect(TokenType.IDENTIFIER).value)
            while self.at(TokenType.COMMA):
                self.advance()
                params.append(self.expect(TokenType.IDENTIFIER).value)
        self.expect(TokenType.PIPE)
        body = self.parse_expr()  # escopo v1: bloco de expressão única
        self.expect(TokenType.RBRACE)
        return BlockLiteral(params, body)


def parse_source(source):
    tokens = Lexer(source).tokenize()
    return Parser(tokens).parse_program()


# ---------- impressão da AST para depuração ----------

def dump(node, indent=0):
    pad = "  " * indent
    if isinstance(node, list):
        for n in node:
            dump(n, indent)
        return
    if isinstance(node, Program):
        print(f"{pad}Program")
        if node.functions:
            print(f"{pad}  funcoes:")
            for f in node.functions:
                dump(f, indent + 1)
        if node.classes:
            print(f"{pad}  classes:")
            for c in node.classes:
                dump(c, indent + 1)
        if node.methods:
            print(f"{pad}  methods:")
            for m in node.methods:
                dump(m, indent + 1)
    elif isinstance(node, FunctionDecl):
        print(f"{pad}FunctionDecl {node.name}({', '.join(node.params)})")
        for s in node.body:
            dump(s, indent + 1)
    elif isinstance(node, ClassDecl):
        print(f"{pad}ClassDecl {node.name} parent={node.parent}")
        print(f"{pad}  data: {node.data_fields}")
        print(f"{pad}  methods: {node.method_sigs}")
    elif isinstance(node, MethodDecl):
        print(f"{pad}MethodDecl {node.class_name}.{node.method_name}"
              f"({', '.join(node.params)})")
        for s in node.body:
            dump(s, indent + 1)
    elif isinstance(node, VarDecl):
        print(f"{pad}VarDecl {node.kind} {node.name} := ...")
        if node.expr:
            dump(node.expr, indent + 1)
    elif isinstance(node, If):
        print(f"{pad}If")
        for cond, body in node.branches:
            print(f"{pad}  branch cond=")
            dump(cond, indent + 2)
            dump(body, indent + 2)
        if node.else_body is not None:
            print(f"{pad}  else:")
            dump(node.else_body, indent + 2)
    elif isinstance(node, CaseStmt):
        print(f"{pad}CaseStmt")
        for cond, body in node.branches:
            print(f"{pad}  case cond=")
            dump(cond, indent + 2)
            dump(body, indent + 2)
        if node.otherwise_body is not None:
            print(f"{pad}  otherwise:")
            dump(node.otherwise_body, indent + 2)
    elif isinstance(node, SequenceStmt):
        print(f"{pad}SequenceStmt recover_var={node.recover_var}")
        dump(node.body, indent + 1)
        dump(node.recover_body, indent + 1)
    elif isinstance(node, ForLoop):
        print(f"{pad}ForLoop {node.var}")
        dump(node.body, indent + 1)
    elif isinstance(node, WhileLoop):
        print(f"{pad}WhileLoop")
        dump(node.body, indent + 1)
    elif isinstance(node, Return):
        print(f"{pad}Return")
        if node.expr:
            dump(node.expr, indent + 1)
    elif isinstance(node, PrintStmt):
        print(f"{pad}PrintStmt (newline={node.newline})")
        for e in node.exprs:
            dump(e, indent + 1)
    elif isinstance(node, Assign):
        print(f"{pad}Assign {node.op}")
        dump(node.target, indent + 1)
        dump(node.expr, indent + 1)
    elif isinstance(node, ExprStmt):
        print(f"{pad}ExprStmt")
        dump(node.expr, indent + 1)
    elif isinstance(node, BinOp):
        print(f"{pad}BinOp {node.op}")
        dump(node.left, indent + 1)
        dump(node.right, indent + 1)
    elif isinstance(node, UnaryOp):
        print(f"{pad}UnaryOp {node.op}")
        dump(node.expr, indent + 1)
    elif isinstance(node, Literal):
        print(f"{pad}Literal {node.value!r}")
    elif isinstance(node, Identifier):
        print(f"{pad}Identifier {node.name}")
    elif isinstance(node, ArrayLiteral):
        print(f"{pad}ArrayLiteral")
        for e in node.elements:
            dump(e, indent + 1)
    elif isinstance(node, BlockLiteral):
        print(f"{pad}BlockLiteral params={node.params}")
        dump(node.body, indent + 1)
    elif isinstance(node, MemberAccess):
        print(f"{pad}MemberAccess .{node.name}")
        dump(node.target, indent + 1)
    elif isinstance(node, MethodCall):
        print(f"{pad}MethodCall .{node.name}")
        dump(node.target, indent + 1)
        for a in node.args:
            dump(a, indent + 1)
    elif isinstance(node, Index):
        print(f"{pad}Index")
        dump(node.target, indent + 1)
        dump(node.index_expr, indent + 1)
    elif isinstance(node, Call):
        print(f"{pad}Call {node.name}")
        for a in node.args:
            dump(a, indent + 1)
    else:
        print(f"{pad}{node}")


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

Return NIL
'''
    program = parse_source(exemplo)
    dump(program)
