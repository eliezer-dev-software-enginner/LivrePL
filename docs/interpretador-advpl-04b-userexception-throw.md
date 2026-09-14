# Interpretador AdvPL — Addendum: `UserException` / `Throw` no `BEGIN SEQUENCE`

Resposta à pergunta: **não**, a etapa 4 original só cobria erros internos do próprio interpretador (índice fora do array, divisão por zero, tipo incompatível). Não havia como o código AdvPL lançar sua própria exceção. Esta correção adiciona isso.

---

## O que muda

- Nova exceção interna `ThrownException`, que carrega o **valor lançado** (não só uma mensagem de texto).
- Novo builtin **`UserException(cMensagem)`**: cria um objeto de erro (com atributo `:Description`, igual ao AdvPL real) e lança.
- Novo builtin **`Throw(valor)`**: lança qualquer valor/objeto diretamente — inclusive uma instância de uma `CLASS` definida pelo próprio usuário, não só o objeto de erro padrão.
- `RECOVER USING x` agora diferencia as duas situações:
  - Se foi um `Throw`/`UserException` → `x` recebe exatamente o valor lançado.
  - Se foi um erro interno do interpretador (índice, tipo, etc.) → `x` recebe um objeto `ERROR` com `:Description`, para manter a mesma interface (`oErro:Description`) em ambos os casos.
- A exceção se propaga corretamente **através de chamadas de função** — se `UserException` é lançada dentro de uma função chamada de dentro do `BEGIN SEQUENCE`, o `RECOVER` externo ainda captura normalmente (igual ao comportamento real do AdvPL).

---

## Código — mudanças no `interpreter.py`

```python
class ThrownException(Exception):
    """Exceção lançada explicitamente pelo código AdvPL (UserException/Throw).
    Carrega o valor lançado (normalmente um objeto de erro com :Description,
    mas pode ser qualquer valor/objeto que o usuário decidir lançar)."""
    def __init__(self, value):
        self.value = value
```

```python
# exec_stmt, ramo de SequenceStmt
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
```

```python
# novos builtins, dentro de _build_builtins
def b_userexception(args):
    msg = args[0] if args else ""
    err_obj = AdvPLObject("ERROR")
    err_obj.attrs["DESCRIPTION"] = msg
    raise ThrownException(err_obj)

def b_throw(args):
    value = args[0] if args else None
    raise ThrownException(value)

# ... registrados como:
"USEREXCEPTION": b_userexception,
"THROW": b_throw,
```

`ThrownException` **não** herda de `AdvPLRuntimeError` — é capturada num `except` separado, antes do `except` genérico, para não se misturar com os erros internos.

---

## Teste real

```advpl
Function Main()
    Begin Sequence
        ValidaIdade(-5)
        ? "essa linha nao deveria rodar"
    Recover Using oErro
        ? "Erro capturado:", oErro:Description
    End Sequence

    Begin Sequence
        Throw(MinhaExcecao():New("Falha customizada", 42))
    Recover Using oErro2
        ? "Erro customizado:", oErro2:cMsg, "codigo:", oErro2:nCodigo
    End Sequence

    ? "Programa continua normalmente apos os dois recovers"
Return NIL

Function ValidaIdade(nIdade)
    If nIdade < 0
        UserException("Idade nao pode ser negativa: " + Str(nIdade))
    EndIf
    ? "Idade valida:", nIdade
Return NIL

Class MinhaExcecao
    Data cMsg
    Data nCodigo
    Method New(cMsg, nCodigo) Constructor
EndClass

Method New(cMsg, nCodigo) Class MinhaExcecao
    ::cMsg := cMsg
    ::nCodigo := nCodigo
Return Self
```

**Saída real (verificada):**
```
Erro capturado: Idade nao pode ser negativa: -5
Erro customizado: Falha customizada codigo: 42
Programa continua normalmente apos os dois recovers
```

Dois pontos confirmados aqui:
1. `UserException` lançada de **dentro de `ValidaIdade()`** (uma função chamada, não o corpo direto do `BEGIN SEQUENCE`) ainda é capturada pelo `RECOVER` de fora — a exceção Python atravessa naturalmente a pilha de chamadas do Python, sem precisar de nenhum código especial de propagação.
2. `Throw()` aceita **qualquer objeto**, inclusive uma classe de exceção totalmente definida pelo usuário (`MinhaExcecao`, com seus próprios atributos `cMsg`/`nCodigo`) — não fica preso ao objeto de erro padrão com `:Description`.

Depois desse teste, revalidei todos os testes das etapas anteriores (dump da AST, `PRIVATE` dinâmico, `LOCAL` isolado, `STATIC` persistente, o teste combinado da etapa 4) e todos continuam passando sem alteração de comportamento.

---

## Limitação que permanece

Ainda não existe um `BREAK` explícito (o comando do AdvPL real para forçar o desvio pro `RECOVER` a qualquer momento sem precisar de `UserException`/`Throw`) — mas na prática, `UserException`/`Throw` cobrem o caso de uso que você perguntou (lançar uma exceção própria do código), então isso deixa de ser um bloqueio para uso real.
