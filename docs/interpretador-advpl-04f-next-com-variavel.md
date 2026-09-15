# Interpretador AdvPL — Correção: `NEXT x` (nome da variável após NEXT)

Bug reportado testando um `FOR` aninhado.

## Erro original

```advpl
for x:=1 to 10
    for y:=1 to 10
        ? cValToChar(x) + " + " + cValToChar(y) + " = " + cValToChar(x + y)
    next y
    ? "--------" + CRLF
next x
```

```
[ERRO] Esperado fim de linha, encontrado TokenType.IDENTIFIER na linha 8
```

No AdvPL real, `NEXT` aceita opcionalmente o nome da variável de controle do laço logo em seguida (`NEXT x`) — é puramente documentacional/legibilidade, principalmente útil em `FOR` aninhados pra deixar claro qual laço está fechando ali. O parser só sabia lidar com `NEXT` sozinho.

## Correção

`parse_for`, em `parser.py`, passa a consumir opcionalmente um `IDENTIFIER` logo depois do `NEXT`:

```python
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
```

Importante: o nome depois do `NEXT` é só consumido e descartado — não há validação de que bate com a variável do próprio `FOR` (o AdvPL real também não faz essa validação em tempo de execução; é convenção, não uma trava semântica).

## Teste real (FOR aninhado, 3x3)

```advpl
User Function ex()
    Local x := 1
    Local y := 0

    for x:=1 to 3
        for y:=1 to 3
            ? cValToChar(x) + " + " + cValToChar(y) + " = " + cValToChar(x + y)
        next y
        ? "--------" + CRLF
    next x

Return(Nil)
```

Saída real:
```
1 + 1 = 2
1 + 2 = 3
1 + 3 = 4
--------

2 + 1 = 3
2 + 2 = 4
2 + 3 = 5
--------

3 + 1 = 4
3 + 2 = 5
3 + 3 = 6
--------

```

Confirma `FOR` aninhado funcionando corretamente com `NEXT y` e `NEXT x` fechando cada nível, e o `CRLF` (da correção anterior) imprimindo a linha em branco extra entre os blocos.

Revalidei todos os testes anteriores (lexer, parser, interpretador etapas 2–4, `UserException`/`Throw`, `USER FUNCTION`, `cValToChar`, `CRLF`/`??`) e nada foi afetado por essa correção.
