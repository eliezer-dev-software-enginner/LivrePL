# Interpretador AdvPL — Etapa 3: Interpretador (Tree-Walking Executor)

Terceira e última peça do núcleo: percorrer a AST (etapa 2) e executar de verdade — variáveis, laços, condicionais, chamadas de função e uma biblioteca nativa mínima. É aqui que um `Main()` completo passa a rodar de ponta a ponta, no terminal, sem AppServer.

Depende de `lexer.py` (etapa 1) e `parser.py` (etapa 2).

---

## Correção aplicada ao parser (etapa 2) nesta sessão

Ao testar `STATIC nVez := 0` dentro do corpo de uma função, o parser quebrava. Causa: a etapa 2 tratava `STATIC` sempre como sinal de fim do corpo da função (pensando que seria o início de uma nova `STATIC FUNCTION`), mesmo quando era apenas uma declaração de variável estática local ao corpo.

**Correção:** o fim do corpo de uma função agora só é reconhecido quando o token é `FUNCTION`, ou quando é `STATIC` **seguido de** `FUNCTION` (lookahead de 1 token). Isso desambiguiza `STATIC FUNCTION Foo()` (nova função) de `STATIC nVez := 0` (variável estática comum).

```python
def is_function_start(self):
    if self.at(TokenType.FUNCTION):
        return True
    if self.at(TokenType.STATIC) and self.peek(1).type == TokenType.FUNCTION:
        return True
    return False

def parse_function_body(self):
    stmts = []
    self.skip_newlines()
    while not (self.is_function_start() or self.at(TokenType.EOF)):
        stmts.append(self.parse_statement())
        self.skip_terminator()
    return stmts
```

Isso substitui a chamada anterior a `parse_statement_list(stop_types=(FUNCTION, STATIC, EOF))` dentro de `parse_function`. Os arquivos de saída desta e da etapa anterior já refletem essa correção.

---

## Arquitetura do interpretador

- **Tree-walking**: percorre a AST recursivamente, sem gerar bytecode.
- **Pilha de chamadas (`call_stack`)**: uma lista de `Frame`, um por chamada de função ativa.
- **`Frame`**: guarda `locals` (dict, só visível no próprio frame) e `privates` (dict, visível no próprio frame **e** propagada para frames filhos).
- **`globals`**: dict único para `PUBLIC`.
- **`statics`**: dict indexado por nome de função, cada um guardando as variáveis `STATIC` daquela função — o inicializador só roda na primeira chamada.

### Regra de resolução de variável (leitura), nesta ordem:
1. `LOCAL` do frame atual
2. `STATIC` da função atual
3. `PRIVATE` — percorre o frame atual e sobe a pilha de chamadas até a base (escopo dinâmico)
4. `PUBLIC` (globais)
5. Se não achar em lugar nenhum → erro

### Regra de escrita (`:=` sobre variável já existente):
Mesma ordem de busca acima, mas grava no local onde a variável foi encontrada. Se não existir em nenhum escopo, o interpretador cria a variável implicitamente como `PRIVATE` no frame atual — replicando o comportamento padrão do Clipper/AdvPL quando não há declaração explícita.

---

## Código

```python
# interpreter.py
# Etapa 3 do interpretador AdvPL: tree-walking executor

from parser import (
    parse_source, Program, FunctionDecl, VarDecl, Assign, If, ForLoop,
    WhileLoop, Return, PrintStmt, LoopStmt, ExitStmt, ExprStmt, BinOp,
    UnaryOp, Literal, Identifier, ArrayLiteral, Index, Call
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


# ---------- Frame de execução (pilha de chamadas) ----------

class Frame:
    def __init__(self, func_name):
        self.func_name = func_name
        self.locals = {}    # LOCAL: só visível neste frame
        self.privates = {}  # PRIVATE: visível neste frame e nos frames filhos


# ---------- Interpretador ----------

class Interpreter:
    def __init__(self, program: Program):
        self.functions = {f.name.upper(): f for f in program.functions}
        self.globals = {}     # PUBLIC
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

        raise AdvPLRuntimeError(f"Função '{name}' não encontrada")

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

        return {
            "LEN": b_len,
            "SUBSTR": b_substr,
            "ALLTRIM": b_alltrim,
            "UPPER": b_upper,
            "LOWER": b_lower,
            "STR": b_str,
            "VAL": b_val,
            "SPACE": b_space,
            "PADR": b_padr,
            "PADL": b_padl,
            "AADD": b_aadd,
            "ASIZE": b_asize,
            "ALEN": b_alen,
            "VALTYPE": b_valtype,
            "EMPTY": b_empty,
            "ROUND": b_round,
            "INT": b_int,
            "ABS": b_abs,
            "MAX": b_max,
            "MIN": b_min,
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
    // cMsg não foi declarada aqui, mas é PRIVATE herdada de Main()
    ? "Dentro de MostraPrivate, cMsg =", cMsg
Return NIL
'''
    run_source(exemplo)
```

---

## Teste 1 — saída real (FOR, IF/ELSE, PRIVATE dinâmico, nativas)

Rodando o bloco `__main__` acima:

```
Total alto: 60
Chamando MostraPrivate...
Dentro de MostraPrivate, cMsg = definida em Main
AllTrim teste: espacos
ValType nTotal: N
```

Confirma: soma do array via `FOR` (60 = 10+20+30, então `IF > 50` cai no ramo certo), e o ponto mais importante — **`cMsg` foi declarada como `PRIVATE` em `Main()` e lida dentro de `MostraPrivate()` sem ter sido declarada lá**. Isso é exatamente o escopo dinâmico do Clipper/AdvPL funcionando.

## Teste 2 — saída real (isolamento de `LOCAL`)

```advpl
Function Main()
    Local nX := 100
    TestaLocal()
Return NIL

Function TestaLocal()
    ? nX     // nX é LOCAL de Main -- não deveria propagar
Return NIL
```

Saída real:
```
[erro esperado capturado] Variável 'nX' não declarada
```

Confirma o oposto do `PRIVATE`: uma variável `LOCAL` **não** vaza para funções chamadas — o erro é o comportamento correto.

## Teste 3 — saída real (`STATIC` persistindo entre chamadas)

```advpl
Function Main()
    Local i := 0
    Do While i < 3
        ? "contador STATIC:", Contador()
        i += 1
    EndDo
Return NIL

Function Contador()
    Static nVez := 0
    nVez += 1
Return nVez
```

Saída real:
```
contador STATIC: 1
contador STATIC: 2
contador STATIC: 3
```

Confirma que o inicializador `Static nVez := 0` só roda na primeira chamada, e o valor persiste (soma) nas chamadas seguintes — diferente de `LOCAL`, que reiniciaria a cada chamada.

---

## O que já funciona de ponta a ponta

- `FUNCTION`/`STATIC FUNCTION`, parâmetros, `RETURN`
- `LOCAL`, `PRIVATE` (com herança dinâmica pela pilha), `PUBLIC`, `STATIC` (com persistência e inicialização única)
- `IF/ELSEIF/ELSE/ENDIF`, `FOR/TO/STEP/NEXT`, `DO WHILE/ENDDO`, `LOOP`, `EXIT`
- Arrays (`{}`, indexação 1-based, leitura e escrita)
- `?`/`??`
- Atribuição composta (`+=`, `-=`)
- 19 funções nativas: `Len`, `SubStr`, `AllTrim`, `Upper`, `Lower`, `Str`, `Val`, `Space`, `PadR`, `PadL`, `AAdd`, `ASize`, `ALen`, `ValType`, `Empty`, `Round`, `Int`, `Abs`, `Max`, `Min`

## Simplificações/limitações conhecidas desta etapa

- `?`/`??` usam `print()` do Python — separador sempre por espaço simples entre os argumentos; o AdvPL real tem regras de espaçamento um pouco mais específicas.
- Erros de tipo (`+` entre tipos incompatíveis) e índice de array fora do range aparecem como `AdvPLRuntimeError`/exceção Python crua, sem tratamento tipo `BEGIN SEQUENCE`.
- `DO CASE`, code blocks (`{|x| ...}`), `@variavel` por referência e `CLASS/ENDCLASS` continuam fora do escopo — ficam para uma etapa 4.

---

## Próximo passo sugerido (etapa 4)

Com a linguagem "pura" já rodando de ponta a ponta, os candidatos naturais para a próxima etapa são: `DO CASE/ENDCASE`, code blocks, `BEGIN SEQUENCE/RECOVER/END SEQUENCE`, e então `CLASS/ENDCLASS` (OOP básico) — nessa ordem de complexidade crescente, conforme o plano do escopo original.
