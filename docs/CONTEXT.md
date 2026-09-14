# CONTEXT.md — Informações do projeto e rotina de trabalho

## Sobre este arquivo

Este arquivo guarda o contexto permanente do projeto para que, **em toda sessão nova**, o assistente consulte:

1. `README.md` — visão geral, funcionalidades e como testar
2. `CONTEXT.md` — este arquivo: arquitetura, rotina de trabalho e convenções
3. Os arquivos de código-fonte do projeto (`lexer.py`, `parser.py`, `interpreter.py`, `main.py`, `preprocessor.py`)

## O que é o projeto

Interpretador/executor de código AdvPL (linguagem do ERP Protheus/TOTVS) feito em Python, sem AppServer, licença ou banco de dados. Roda scripts `.prw` diretamente no terminal.

- Repositório remoto: `git@github.com:eliezer-dev-software-enginner/LivrePL.git` (branch `main`)
- Plataforma: Windows, shell PowerShell

## Arquitetura (fluxo de dados)

```
arquivo.prw
   -> preprocessor.py   (#define / #include — roda antes do lexer)
   -> lexer.py          (Etapa 1: tokenizador -> lista de Token)
   -> parser.py         (Etapa 2: parser recursivo descendente -> AST)
   -> interpreter.py    (Etapas 3+4: tree-walking executor)
```

- `main.py` — CLI: `python main.py arquivo.prw [FuncaoDeEntrada] [--ast]`. Entry point padrão é `MAIN`.
- `docs/` — documentação detalhada de cada etapa e dos adendos/correções.

## Funcionalidades implementadas

- Tipos: caracter, numérico, lógico, array, NIL, code block
- Controle de fluxo: IF/ELSEIF/ELSE, FOR..TO..STEP/NEXT, DO WHILE/ENDDO, DO CASE, BEGIN SEQUENCE/RECOVER
- Escopo: LOCAL, PRIVATE (dinâmico), PUBLIC, STATIC (persistente)
- OOP: CLASS/DATA/METHOD, herança simples (FROM), SELF, `::attr`, `obj:Metodo()`
- Code blocks `{|x| expr}` com closure de leitura + `Eval()`
- Exceções: `UserException(cMsg)` e `Throw(valor)` capturadas por `RECOVER USING x`
- Exceções internas do interpretador convertidas em objeto `ERROR` com `:Description`
- `User Function` como prefixo opcional de `FUNCTION`
- 24 funções nativas: Len, SubStr, AllTrim, Upper, Lower, Str, CValToChar, Val, Space, PadR, PadL, AAdd, ASize, ALen, ValType, Empty, Round, Int, Abs, Max, Min, Eval, UserException, Throw

## Convenções de código

- Sem comentários no código, salvo se o usuário pedir
- Nomes de builtins e palavras reservadas sempre em MAIÚSCULAS
- Variáveis AdvPL são case-insensitive (normalizadas via `.upper()`)
- Arrays AdvPL são 1-based
- Não usar emojis em arquivos
- Erros internos propagam como `AdvPLRuntimeError`

## Rotina do assistente em uma correção nova

Quando chega um novo arquivo `.md` em `docs/` descrevendo uma correção/etapa:

1. Ler o `.md` novo inteiro
2. Comparar com o código atual (ler `lexer.py`/`parser.py`/`interpreter.py` e/ou `main.py` conforme o alvo)
3. Aplicar exatamente o que o `.md` especifica (código, registro de builtin, etc.)
4. Rodar o teste real descrito no `.md` e confirmar a saída esperada
5. Rodar regressão básica: `python main.py exemplos/ola.prw`, `python main.py exemplos/todas-etapas.prw`, `python interpreter.py`
6. Atualizar o `README.md` se a correção muda funcionalidades/testes/listas (ex.: contagem de nativas)
7. Registrar a alteração em `DECISIONS.md`
8. Fazer commit (só quando o usuário pedir) e push

## Formatação de texto

O usuário escreve sem acentos. Manter o mesmo estilo nos arquivos (sem acentos) a menos que seja necessário.