# Interpretador AdvPL — Correções: `CRLF` e `??`

Dois bugs reportados/encontrados ao testar o exercício 7 (tabuada) da lista de exercícios.

## 1. `CRLF` não declarado

### Erro original

```
[ERRO] Variável 'CRLF' não declarada
```

`CRLF` é uma constante padrão do Protheus (normalmente vinda de `PROTHEUS.CH`, valendo `Chr(13) + Chr(10)`) usada pra forçar quebra de linha dentro de uma string, sem depender do `?` do comando de saída. O interpretador não tinha nenhuma constante pré-definida.

### Correção

`CRLF` agora é injetada direto no escopo `PUBLIC` (`globals`) na criação do `Interpreter`, disponível em qualquer script sem precisar de `#include`/declaração:

```python
def __init__(self, program: Program):
    self.functions = {f.name.upper(): f for f in program.functions}
    self.globals = {}     # PUBLIC
    self.globals["CRLF"] = "\r\n"  # constante padrão do PROTHEUS.CH
    self.statics = {}
    # ...
```

Como ela vive em `self.globals`, funciona exatamente como qualquer variável `PUBLIC` normal — pode até ser lida/sobrescrita como qualquer outra (não há um conceito de "constante imutável" nesta etapa do interpretador; documentando essa limitação aqui).

---

## 2. `??` nunca funcionou de verdade

Bug **pré-existente desde a etapa 1** (lexer), encontrado ao testar o cenário acima — não é consequência da correção do `CRLF`, é independente.

### O problema

O lexer tratava cada `?` isoladamente, sempre emitindo um token `IDENTIFIER` com valor `"?"` — nunca reconhecia dois `?` consecutivos como um único comando `??` (impressão sem quebra de linha, usada pra concatenar saída na mesma linha).

```python
# lexer.py, ANTES
if ch == "?":
    self.add_token(TokenType.IDENTIFIER, "?")
    return
```

Rodando `Lexer("?? texto").tokenize()`, o resultado era:
```
Token(TokenType.IDENTIFIER, '?', line=1)
Token(TokenType.IDENTIFIER, '?', line=1)
Token(TokenType.IDENTIFIER, 'texto', line=1)
```

Ou seja: dois comandos `?` (cada um imprimindo, com quebra de linha) em vez de um único `??` sem quebra. Isso nunca dava erro visível de sintaxe (`parse_print` tratava cada `?` como um `PrintStmt` isolado válido), então o bug ficou mascarado até um script realmente depender do comportamento de "não quebrar linha" do `??`.

### Correção

```python
# lexer.py, DEPOIS
if ch == "?":
    if self.match("?"):
        self.add_token(TokenType.IDENTIFIER, "??")
    else:
        self.add_token(TokenType.IDENTIFIER, "?")
    return
```

Agora `Lexer("?? texto").tokenize()` produz corretamente um único token `IDENTIFIER` com valor `"??"`, que o parser já sabia interpretar certo (`parse_print` já checava `self.current().value in ("?", "??")` desde a etapa 2 — só nunca recebia o valor `"??"` de fato porque o lexer não gerava).

---

## Teste real (os dois juntos)

```advpl
User Function ex()
    Local i := 1
    Local cResultado := ""

    For i := 1 To 3
        cResultado += "1 + " + cValToChar(i) + " = " + cValToChar(1 + i) + CRLF
    Next

    ?? cResultado
Return(Nil)
```

Saída real:
```
1 + 1 = 2
1 + 2 = 3
1 + 3 = 4
```

(cada linha do `cResultado` construída manualmente com `CRLF` no fim, e impressa tudo de uma vez com `??` — sem o `??` duplicar quebra de linha extra no final, sem o `CRLF` faltando entre as linhas).

Revalidei todos os testes anteriores (lexer, parser, interpretador etapas 2–4, `UserException`/`Throw`, `USER FUNCTION`, `cValToChar`) e nada foi afetado por essas duas correções.

## Nota sobre outras constantes do PROTHEUS.CH

`CRLF` foi adicionada pontualmente porque foi a que você bateu primeiro. Existem outras constantes comuns do `PROTHEUS.CH` que provavelmente vão aparecer em exercícios futuros (ex: `TAB` = `Chr(9)`) — se/quando aparecerem, o padrão é o mesmo: adicionar em `self.globals` na inicialização do `Interpreter`.
