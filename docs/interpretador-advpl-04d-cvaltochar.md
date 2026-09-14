# Interpretador AdvPL — Correção: `cValToChar`

Bug reportado ao testar o exercício 2 da lista de exercícios: `cValToChar` (função nativa real do AdvPL, usada para converter qualquer valor em string) não existia na biblioteca nativa do interpretador.

## Erro original

```advpl
User Function ex2()
Local x := 3
Local y := 4

? cValToChar(x) + " + " + cValToChar(y) + " = " + (x + y)
RETURN(Nil)
```

```
[ERRO] Função 'cValToChar' não encontrada
```

## Correção

Novo builtin `CVALTOCHAR`, adicionado em `_build_builtins` de `interpreter.py`:

```python
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

# registrado como:
"CVALTOCHAR": b_cvaltochar,
```

Diferente do `Str()` (que já existia), `cValToChar` aceita qualquer tipo escalar (número, lógico, string) — não só número — e não faz nenhuma formatação/padding, só a conversão direta para texto. `NIL` vira string vazia (`""`), igual ao comportamento real do AdvPL. Arrays continuam não suportados (gera erro, já que `cValToChar` de array não tem um significado direto no AdvPL real também).

## Teste real

```advpl
User Function ex2()
Local x := 3
Local y := 4

? cValToChar(x) + " + " + cValToChar(y) + " = " + cValToChar(x + y)
? cValToChar(x) + " - " + cValToChar(y) + " = " + cValToChar(x - y)
? cValToChar(x) + " * " + cValToChar(y) + " = " + cValToChar(x * y)
? cValToChar(x) + " / " + cValToChar(y) + " = " + cValToChar(x / y)

RETURN(Nil)
```

Saída real:
```
3 + 4 = 7
3 - 4 = -1
3 * 4 = 12
3 / 4 = 0.75
```

## Achado adicional (não é bug — é comportamento correto)

O script **original** do exercício (antes do ajuste acima) concatenava o resultado da conta *sem* `cValToChar`:

```advpl
? cValToChar(x) + " + " + cValToChar(y) + " = " + (x + y)
```

Isso gera erro **mesmo depois da correção do `cValToChar`**:
```
[erro] Operação '+' inválida entre <class 'str'> e <class 'int'>
```

Esse erro é esperado e fiel ao AdvPL real: o operador `+` exige os dois operandos do mesmo tipo — não existe conversão implícita de número pra string na concatenação (diferente de linguagens como JavaScript/Python). Documentando aqui pra não ser confundido com um bug do interpretador no futuro: qualquer script que misturar `string + número` diretamente com `+` deve mesmo falhar, e é isso que valida que `apply_binop` está se comportando como o AdvPL de verdade.

Revalidei todos os testes anteriores (lexer, parser, interpretador etapas 2–4, `UserException`/`Throw`, `USER FUNCTION`) e nada foi afetado por essa adição.

## Funções nativas — lista atualizada

Com `cValToChar`, a biblioteca nativa passa de 23 para **24 funções**:
`Len`, `SubStr`, `AllTrim`, `Upper`, `Lower`, `Str`, `Val`, `Space`, `PadR`, `PadL`, `AAdd`, `ASize`, `ALen`, `ValType`, `Empty`, `Round`, `Int`, `Abs`, `Max`, `Min`, `Eval`, `UserException`, `Throw`, `CValToChar`.
