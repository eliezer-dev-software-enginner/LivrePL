# Interpretador AdvPL — Etapa 2: Parser (AST)

Segunda peça do interpretador: consumir a lista de tokens gerada pelo lexer (etapa 1) e montar uma **AST** (Abstract Syntax Tree) — a representação estruturada do programa que o interpretador (etapa 3) vai percorrer para executar.

Depende do arquivo `lexer.py` da etapa anterior (`from lexer import Lexer, TokenType`).

---

## O que o parser cobre nesta etapa

**Estrutura:**
- Programa = lista de `FUNCTION` (com `STATIC FUNCTION` também aceito)
- Corpo de função = lista de comandos, delimitado por quebra de linha

**Comandos (statements):**
- `LOCAL` / `PRIVATE` / `PUBLIC` / `STATIC` (com múltiplas declarações separadas por vírgula na mesma linha)
- `IF / ELSEIF / ELSE / ENDIF`
- `FOR ... TO ... STEP ... NEXT`
- `DO WHILE / ENDDO`
- `RETURN` (com ou sem expressão)
- `? expr, expr, ...` e `?? ...` (saída, com ou sem nova linha)
- `LOOP` e `EXIT`
- Atribuição (`:=`, `+=`, `-=`) e chamada de função como comando solto

**Expressões, em ordem de precedência (da mais baixa pra mais alta):**
```
OR
AND
NOT
== <> < > <= >=
+ -
* /
**              (associatividade à direita)
unário + -
pós-fixo: chamada de função ( ) e indexação [ ]
primário: número, string, .T./.F., NIL, identificador, ( expr ), { array }
```

---

## Código

```python
# parser.py
# Etapa 2 do interpretador AdvPL: parser recursivo descendente -> AST

from lexer import Lexer, TokenType


class ParseError(Exception):
    pass


# ---------- Nós da AST ----------

class Program:
    def __init__(self, functions):
        self.functions = functions

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
        self.target = target  # Identifier ou Index
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
        functions = []
        self.skip_newlines()
        while not self.at(TokenType.EOF):
            functions.append(self.parse_function())
            self.skip_newlines()
        return Program(functions)

    def parse_function(self):
        if self.at(TokenType.STATIC):
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

        body = self.parse_statement_list(
            stop_types=(TokenType.FUNCTION, TokenType.STATIC, TokenType.EOF)
        )
        return FunctionDecl(name, params, body)

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
        if t == TokenType.DO:
            return self.parse_while()
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
        return ForLoop(var, start, end, step, body)

    def parse_while(self):
        self.expect(TokenType.DO)
        self.expect(TokenType.WHILE)
        cond = self.parse_expr()
        self.skip_terminator()
        body = self.parse_statement_list(stop_types=(TokenType.ENDDO,))
        self.expect(TokenType.ENDDO)
        return WhileLoop(cond, body)

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
                else:
                    raise ParseError("Chamada inválida")
            elif self.at(TokenType.LBRACKET):
                self.advance()
                idx = self.parse_expr()
                self.expect(TokenType.RBRACKET)
                expr = Index(expr, idx)
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
        if tok.type == TokenType.LPAREN:
            self.advance()
            expr = self.parse_expr()
            self.expect(TokenType.RPAREN)
            return expr
        if tok.type == TokenType.LBRACE:
            self.advance()
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
        for f in node.functions:
            dump(f, indent + 1)
    elif isinstance(node, FunctionDecl):
        print(f"{pad}FunctionDecl {node.name}({', '.join(node.params)})")
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
```

---

## Teste rápido (saída real verificada)

Rodando o bloco `__main__` acima — que agora inclui um `IF/ELSE` além do `FOR` da etapa anterior — a AST gerada é:

```
Program
  FunctionDecl Main()
    VarDecl LOCAL nTotal := ...
      Literal 0
    VarDecl LOCAL aItens := ...
      ArrayLiteral
        Literal 10
        Literal 20
        Literal 30
    VarDecl LOCAL i := ...
    ForLoop i
      Assign +=
        Identifier nTotal
        Index
          Identifier aItens
          Identifier i
    If
      branch cond=
        BinOp >
          Identifier nTotal
          Literal 50
        PrintStmt (newline=True)
          Literal 'Total alto:'
          Call Str
            Identifier nTotal
      else:
        PrintStmt (newline=True)
          Literal 'Total baixo:'
          Call Str
            Identifier nTotal
    Return
      Literal None
```

A árvore confirma que o parser está montando corretamente: declarações de variável, array literal, laço `FOR`, atribuição composta (`+=`) sobre elemento indexado, `IF/ELSE` com condição via `BinOp`, chamada de função (`Str(nTotal)`) e `RETURN` com valor `NIL`.

---

## Decisões de projeto que valem registrar

- **`?`/`??` como comando dedicado, não chamada de função:** o lexer entrega `?` como `IDENTIFIER`, e o parser intercepta esse caso especificamente em `parse_statement` antes de cair no caminho genérico de atribuição/chamada. Isso reflete a realidade do AdvPL: `?` é sintaxe de comando, não uma função com parênteses.
- **`LOCAL/PRIVATE/PUBLIC/STATIC` com múltiplas variáveis na mesma linha** retornam uma lista de `VarDecl` em vez de um nó agregador — decisão deliberada para manter a AST simples; o interpretador (próxima etapa) trata `VarDecl` isoladamente, iterando a lista quando necessário.
- **Erros de parse** carregam número da linha e o token inesperado, aproveitando que o lexer já anota `line` em cada token — importante para depuração de scripts maiores.
- **`**` (potência) é associativa à direita** (`2 ** 3 ** 2` = `2 ** (3 ** 2)`), consistente com a maioria das linguagens que têm esse operador.

---

## Fora do escopo desta etapa

- `DO CASE / CASE / OTHERWISE / ENDCASE` — ainda não implementado (fica fácil de adicionar seguindo o mesmo padrão do `IF`)
- `BEGIN SEQUENCE / RECOVER / END SEQUENCE`
- Passagem de parâmetro por referência (`@variavel`)
- Code blocks (`{|x| ...}`)
- Declaração de classes (`CLASS/ENDCLASS`)

Esses ficam para quando o interpretador básico (etapa 3) já estiver rodando os exemplos do escopo v1.

---

## Próximo passo

Etapa 3: o **interpretador** propriamente dito — um tree-walking interpreter que percorre essa AST, mantém a tabela de símbolos (com atenção especial ao escopo dinâmico do `PRIVATE`), executa os laços/condicionais e resolve chamadas às funções nativas (`Len`, `Str`, `AllTrim` etc.).
