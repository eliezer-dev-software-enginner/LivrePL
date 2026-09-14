# Interpretador AdvPL — Etapa 4: DO CASE, BEGIN SEQUENCE, Code Blocks e CLASS/METHOD

Quarta etapa: fechando os itens que ficaram de fora do escopo v1 (documento de escopo original) — `DO CASE`, tratamento básico de erro (`BEGIN SEQUENCE`), code blocks (`{|x| ...}`) e OOP básico (`CLASS`/`METHOD`, com herança simples via `FROM`).

Esta etapa **estende** `lexer.py`, `parser.py` e `interpreter.py` das etapas 1–3. Abaixo estão apenas as adições/alterações — os arquivos completos das etapas anteriores continuam válidos e servem de base.

---

## 1. Lexer — novos tokens

Novos tipos de token: `BEGIN`, `SEQUENCE`, `RECOVER`, `END`, `USING`, `CLASS`, `ENDCLASS`, `DATA`, `METHOD`, `CONSTRUCTOR`, `FROM`, `COLON` (`:`), `DCOLON` (`::`), `PIPE` (`|`).

```python
# --- novos valores no enum TokenType ---
BEGIN = auto()
SEQUENCE = auto()
RECOVER = auto()
END = auto()
USING = auto()
CLASS = auto()
ENDCLASS = auto()
DATA = auto()
METHOD = auto()
CONSTRUCTOR = auto()
FROM = auto()
# ...
COLON = auto()     # :
DCOLON = auto()    # ::
PIPE = auto()      # |
```

```python
# --- novas entradas em KEYWORDS ---
"BEGIN": TokenType.BEGIN,
"SEQUENCE": TokenType.SEQUENCE,
"RECOVER": TokenType.RECOVER,
"END": TokenType.END,
"USING": TokenType.USING,
"CLASS": TokenType.CLASS,
"ENDCLASS": TokenType.ENDCLASS,
"DATA": TokenType.DATA,
"METHOD": TokenType.METHOD,
"CONSTRUCTOR": TokenType.CONSTRUCTOR,
"FROM": TokenType.FROM,
```

```python
# --- scan_token: ':' agora também reconhece '::', e '|' é token novo ---
if ch == ":":
    if self.match("="):
        self.add_token(TokenType.ASSIGN, ":=")
    elif self.match(":"):
        self.add_token(TokenType.DCOLON, "::")
    else:
        self.add_token(TokenType.COLON, ":")
    return

if ch == "|":
    self.add_token(TokenType.PIPE, "|")
    return
```

**Teste real (tokens novos):**
```
oPessoa:cNome := "Joao"       -> IDENTIFIER, COLON, IDENTIFIER, ASSIGN, STRING
::nIdade                      -> DCOLON, IDENTIFIER
BEGIN SEQUENCE / RECOVER USING oErro / END SEQUENCE  -> tokens correspondentes
{|x,y| x+y}                   -> LBRACE, PIPE, IDENTIFIER, COMMA, IDENTIFIER, PIPE, ...
CLASS Pessoa / ENDCLASS        -> CLASS, IDENTIFIER, ENDCLASS
```
Confirmado rodando o lexer contra esse trecho — saída real, sem erros.

---

## 2. Parser — novos nós de AST

```python
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
```

`Program` agora carrega também `classes` e `methods`, além de `functions`:

```python
class Program:
    def __init__(self, functions, classes=None, methods=None):
        self.functions = functions
        self.classes = classes or []
        self.methods = methods or []
```

### Ponto de entrada — reconhecendo `CLASS` e `METHOD` no nível do programa

```python
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
    # Um novo bloco de topo começa em: FUNCTION, STATIC FUNCTION, CLASS, ou METHOD
    if self.at(TokenType.FUNCTION):
        return True
    if self.at(TokenType.STATIC) and self.peek(1).type == TokenType.FUNCTION:
        return True
    if self.at(TokenType.CLASS, TokenType.METHOD):
        return True
    return False
```

### `CLASS ... ENDCLASS` e implementação de `METHOD ... CLASS Nome`

Segue o padrão real do AdvPL: a `CLASS` só declara `DATA` e assinaturas de `METHOD`; a implementação de cada método é um bloco de topo separado, à parte, como uma `FUNCTION`:

```python
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
```

### `DO CASE / CASE / OTHERWISE / ENDCASE`

`parse_statement` agora diferencia `DO WHILE` de `DO CASE` olhando o token seguinte a `DO`:

```python
if t == TokenType.DO:
    if self.peek(1).type == TokenType.CASE:
        return self.parse_docase()
    return self.parse_while()

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
```

### `BEGIN SEQUENCE / RECOVER USING x / END SEQUENCE`

```python
if t == TokenType.BEGIN:
    return self.parse_sequence()

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
```

### Member access (`obj:attr`, `obj:Metodo()`) e `::attr` dentro de método

`parse_postfix` ganha um terceiro caso (além de chamada e indexação):

```python
elif self.at(TokenType.COLON):
    self.advance()
    name = self.expect(TokenType.IDENTIFIER).value
    expr = MemberAccess(expr, name)
```

E, quando um `MemberAccess` é seguido de `(`, vira `MethodCall` em vez de `Call`:

```python
if isinstance(expr, Identifier):
    expr = Call(expr.name, args)
elif isinstance(expr, MemberAccess):
    expr = MethodCall(expr.target, expr.name, args)
```

`::atributo` em `parse_primary` é açúcar sintático para `Self:atributo`:

```python
if tok.type == TokenType.DCOLON:
    self.advance()
    name = self.expect(TokenType.IDENTIFIER).value
    return MemberAccess(Identifier("SELF"), name)
```

### Code blocks: `{|x, y| expr}`

Dentro de `parse_primary`, ao ver `{`, se o próximo token for `|`, é bloco de código em vez de array literal:

```python
if tok.type == TokenType.LBRACE:
    self.advance()
    if self.at(TokenType.PIPE):
        return self.parse_block_literal()
    # ... (caminho de array literal, sem alteração)

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
```

**Teste real do parser** (`Do Case`, `Begin Sequence`, `{|x,y| x+y}`, `Class`/`Method`) — rodado contra um exemplo combinando tudo:
```
Funcoes: ['Main']
Classes: [('Pessoa', None, ['cNome', 'nIdade'], [('New', True), ('Cumprimentar', False)])]
Methods: [('Pessoa', 'New', ['cNome', 'nIdade']), ('Pessoa', 'Cumprimentar', [])]
```
Confirma que a `CLASS` foi parseada com seus `DATA`/assinaturas de `METHOD`, e as implementações (`METHOD ... CLASS Pessoa`) viraram entradas separadas em `program.methods`.

---

## 3. Interpretador — execução das novas construções

### Runtime de objetos

```python
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
```

`Frame` ganha um campo `self_obj`, usado apenas quando o frame corresponde à execução de um `METHOD`:

```python
class Frame:
    def __init__(self, func_name, self_obj=None):
        self.func_name = func_name
        self.locals = {}
        self.privates = {}
        self.self_obj = self_obj
```

### Registro de classes e resolução de herança

```python
self.classes = {c.name.upper(): c for c in program.classes}
self.methods = {}
for m in program.methods:
    self.methods[(m.class_name.upper(), m.method_name.upper())] = m

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
```

A instanciação acontece via `call_function`: se o nome chamado não é `FUNCTION` nem nativa, mas é o nome de uma `CLASS` (ex.: `Pessoa()`), retorna um `AdvPLObject` novo:

```python
if upper in self.classes:
    return self.instantiate(upper)
```

Isso reproduz o padrão real do AdvPL: `Pessoa()` cria a instância "crua", e `:New(...)` (chamado em seguida via `MethodCall`) é quem inicializa os atributos.

### `SELF` — leitura especial na tabela de símbolos

```python
def lookup(self, name):
    upper = name.upper()
    frame = self.call_stack[-1]

    if upper == "SELF":
        if frame.self_obj is not None:
            return frame.self_obj
        raise AdvPLRuntimeError("SELF usado fora de um METHOD")
    # ... resto da resolução (LOCAL -> STATIC -> PRIVATE -> PUBLIC) sem mudança
```

### `MemberAccess` (leitura/escrita de atributo) e `MethodCall`

```python
# leitura
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

# chamada de método
if isinstance(node, MethodCall):
    obj = self.eval(node.target)
    args = [self.eval(a) for a in node.args]
    return self.call_method(obj, node.name, args)
```

```python
# escrita (obj:attr := valor), dentro de assign_target
elif isinstance(target, MemberAccess):
    obj = self.eval(target.target)
    if not isinstance(obj, AdvPLObject):
        raise AdvPLRuntimeError("Tentativa de atribuir atributo em valor que não é objeto")
    obj.attrs[target.name.upper()] = value
```

### `DO CASE` e `BEGIN SEQUENCE`

```python
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
    except (AdvPLRuntimeError, ZeroDivisionError, TypeError,
             ValueError, IndexError) as e:
        if stmt.recover_var:
            self.assign_existing(stmt.recover_var, str(e))
        self.exec_block(stmt.recover_body)
```

A captura é deliberadamente restrita a essas exceções — os sinais internos de controle (`ReturnSignal`, `LoopSignal`, `ExitSignal`) **não** herdam dessas classes, então `RETURN`/`LOOP`/`EXIT` dentro de um `BEGIN SEQUENCE` continuam se propagando normalmente, sem serem engolidos pelo `RECOVER`.

### Code blocks: criação e `Eval()`

```python
if isinstance(node, BlockLiteral):
    return AdvPLBlock(node.params, node.body, self.call_stack[-1])

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
```

`Eval(bloco, arg1, arg2, ...)` foi adicionado à biblioteca nativa:

```python
def b_eval(args):
    block, rest = args[0], args[1:]
    return self.invoke_block(block, rest)
# ...
"EVAL": b_eval,
```

Como o bloco é empurrado na mesma `call_stack`, a busca de `PRIVATE` continua funcionando normalmente por escopo dinâmico dentro do bloco (herda a pilha de chamadas real); só o `LOCAL` precisa da cópia explícita porque `LOCAL` nunca é herdado entre frames.

---

## Teste real — tudo combinado

```advpl
Function Main()
    Local n := 2

    Do Case
    Case n == 1
        ? "um"
    Case n == 2
        ? "dois"
    Otherwise
        ? "outro"
    EndCase

    Begin Sequence
        Local aVazio := {}
        ? aVazio[1]
    Recover Using cErro
        ? "Erro capturado:", cErro
    End Sequence

    Local bSoma := {|x, y| x + y}
    ? "Eval bloco:", Eval(bSoma, 2, 3)

    Local oPessoa := Pessoa():New("Maria", 30)
    oPessoa:Cumprimentar()
    ? "Idade:", oPessoa:nIdade

    Local oAluno := Aluno():New("Joao", 20, "Turma A")
    oAluno:Cumprimentar()          // herdado de Pessoa
    ? "Turma:", oAluno:cTurma

Return NIL

Class Pessoa
    Data cNome
    Data nIdade

    Method New(cNome, nIdade) Constructor
    Method Cumprimentar()
EndClass

Method New(cNome, nIdade) Class Pessoa
    ::cNome := cNome
    ::nIdade := nIdade
Return Self

Method Cumprimentar() Class Pessoa
    ? "Ola, meu nome e " + ::cNome
Return NIL

Class Aluno From Pessoa
    Data cTurma

    Method New(cNome, nIdade, cTurma) Constructor
EndClass

Method New(cNome, nIdade, cTurma) Class Aluno
    ::cNome := cNome
    ::nIdade := nIdade
    ::cTurma := cTurma
Return Self
```

**Saída real (verificada rodando o script):**
```
dois
Erro capturado: list index out of range
Eval bloco: 5
Ola, meu nome e Maria
Idade: 30
Ola, meu nome e Joao
Turma: Turma A
```

Confirma, nessa ordem: `DO CASE` selecionando o ramo certo; `BEGIN SEQUENCE` capturando o erro de índice fora do array vazio e desviando pro `RECOVER`; o code block somando `2 + 3` via `Eval()`; a classe `Pessoa` funcionando com construtor e método; e — o ponto mais importante — `Aluno` (que **não** redefine `Cumprimentar`) usando a versão **herdada** de `Pessoa` através da cadeia `FROM`.

Depois desse teste, rodei de novo os testes das etapas 2 e 3 (dump da AST original, `PRIVATE` dinâmico, isolamento de `LOCAL`, persistência de `STATIC`) para confirmar que nada quebrou com as mudanças — todos passaram sem alteração de comportamento.

---

## Simplificações desta etapa

- **Code blocks são de expressão única** (`{|x| expr}`), não múltiplos comandos separados por `;` como o AdvPL real permite em alguns contextos.
- **Closure de code block é só leitura**: o bloco enxerga uma cópia das `LOCAL` do frame onde foi criado no momento da criação; se o bloco reatribuir uma dessas variáveis, isso não volta para o frame original. `PRIVATE` funciona normalmente (por estar na pilha de chamadas real), então essa limitação afeta só `LOCAL` capturada.
- **`BEGIN SEQUENCE`/`RECOVER`** captura os erros do próprio interpretador — não existe ainda um comando `BREAK` explícito do AdvPL para forçar o desvio para o `RECOVER` a partir de qualquer ponto.
- **Herança é single-inheritance simples** (`FROM` aponta para uma única classe pai); não há interfaces, `WITH OBJECT`, nem sobrescrita com chamada explícita ao método do pai (`::Super:Metodo()`).
- Assinatura de `METHOD` dentro do `CLASS ... ENDCLASS` é só registrada para saber quais existem e qual é `CONSTRUCTOR` — os parâmetros declarados ali são ignorados (quem manda são os parâmetros da implementação separada, `METHOD ... CLASS Nome`), igual ao comportamento real do framework.

---

## Estado atual do escopo v1 (revisitando o documento original)

Com as etapas 1–4, praticamente todo o escopo definido em `escopo-interpretador-advpl-v1.md` está coberto:

✅ Tipos, controle de fluxo (`IF`, `DO WHILE`, `FOR`, agora também `DO CASE`)
✅ Escopo de variáveis (`LOCAL`/`PRIVATE`/`PUBLIC`/`STATIC`, incluindo a propagação dinâmica do `PRIVATE`)
✅ Funções e sintaxe de comando
✅ Biblioteca nativa mínima (20 funções, incluindo `Eval`)
✅ Classes básicas (`CLASS`/`ENDCLASS`, `DATA`, `METHOD`, herança simples via `FROM`)
🟡 `BEGIN SEQUENCE/RECOVER` — presente, mas sem `BREAK` explícito
🟡 Code blocks — presentes, mas limitados a expressão única e closure só de leitura

O que continua fora do escopo (por design, conforme o documento original): banco de dados, MVC, REST, RPC, SmartClient, multi-thread.
