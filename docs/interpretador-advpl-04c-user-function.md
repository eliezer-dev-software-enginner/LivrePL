# Interpretador AdvPL — Correção: `USER FUNCTION`

Bug reportado ao testar o exercício 1 da lista de exercícios: o parser não reconhecia `User Function nome()`, sintaxe real e comum do Protheus para marcar uma função como "pública"/exportada (equivalente, na prática, a uma `FUNCTION` comum para efeitos deste interpretador).

## Erro original

```advpl
User Function ola()
    Local cNome := "Dev"
    ? cNome
Return(Nil)
```

```
[ERRO] Esperado TokenType.FUNCTION, encontrado TokenType.IDENTIFIER ('User') na linha 13
```

O lexer tratava `User` como um `IDENTIFIER` qualquer (não era palavra reservada), então o parser não sabia lidar com esse prefixo antes de `Function` — só reconhecia `FUNCTION` puro ou `STATIC FUNCTION`.

## Correção

**Lexer** — `USER` vira palavra reservada:

```python
# TokenType
USER = auto()

# KEYWORDS
"USER": TokenType.USER,
```

**Parser** — `parse_function` e `is_function_start` passam a aceitar `STATIC` **ou** `USER` como prefixo opcional de `FUNCTION`:

```python
def parse_function(self):
    if self.at(TokenType.STATIC, TokenType.USER):
        self.advance()
    self.expect(TokenType.FUNCTION)
    # ... resto sem alteração

def is_function_start(self):
    if self.at(TokenType.FUNCTION):
        return True
    if self.at(TokenType.STATIC, TokenType.USER) and self.peek(1).type == TokenType.FUNCTION:
        return True
    if self.at(TokenType.CLASS, TokenType.METHOD):
        return True
    return False
```

`USER FUNCTION` é tratada exatamente como uma `FUNCTION` comum internamente — o interpretador não faz nenhuma distinção de visibilidade (não existe conceito de função "privada ao módulo" nesta etapa).

## Teste real

```advpl
User Function ola()
    Local cNome := "Dev"
    ? cNome
Return(Nil)
```

Executando com entry point `ola`:
```
Dev
```

Também confirmado: `Return(Nil)` (com parênteses) funciona sem problema — o parser já tratava `(` como abertura de expressão entre parênteses dentro de `RETURN`, então `Return(Nil)` e `Return Nil` são equivalentes.

Revalidei todos os testes anteriores (lexer, parser, interpretador etapas 2–4, `UserException`/`Throw`) e nada foi afetado por essa mudança.

## Atenção

Como `USER` agora é palavra reservada (assim como no AdvPL real), ela não pode mais ser usada como nome de variável ou função dentro de scripts — se algum script antigo usar `User` como identificador, isso agora vai gerar erro de parse.

## Pendência em aberto (não resolvida aqui)

O script do exercício 1 não define uma função `Main()` — só `ola()`. Se o ponto de entrada padrão do `main.py` (fora do escopo desta sessão — foi implementado via OpenCode, não documentado aqui) sempre tenta chamar `Main()` quando nenhum nome é passado por linha de comando, isso vai gerar:

```
[ERRO] Função de entrada 'MAIN' não encontrada
```

Solução imediata: passar o nome da função explicitamente (`python main.py arquivo.prw ola`). Uma melhoria futura seria o `main.py` cair automaticamente na função `User Function` quando não houver `Main()` definida — mas isso depende de revisar o código do `main.py`, que não foi compartilhado nesta sessão.
