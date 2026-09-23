# DECISIONS.md — Registro de modificacoes

Este arquivo registra todas as modificacoes realizadas no projeto. Este arquivo não é corrigido/alterado, apenas recebe entradas para ficar como histórico.

## 2026-09-23

### Perfis de nomes da linguagem
- Arquivos: `naming.py`, `parser.py`, `interpreter.py`, `main.py`, `README.md`, `docs/CONTEXT.md`, `tests/test_name_profiles.py`.
- O perfil `modern` permanece como padrao e nao trunca nomes, preservando os casos existentes.
- O perfil opt-in `legacy10` resolve funcoes, classes, metodos e variaveis pelos dez primeiros caracteres; `User Function` tem simbolo externo `U_` mais oito caracteres.
- Colisoes entre declaracoes de funcoes, classes, metodos ou variaveis no mesmo escopo produzem `NameCollisionError` antes da execucao. Nomes completos sao mantidos nas mensagens.
- A CLI escolhe o perfil com `--name-profile`, sem alterar a sintaxe dos fontes.

### Operador de modulo e argumentos da CLI
- Arquivos: `lexer.py`, `parser.py`, `interpreter.py`, `main.py`, `README.md`, `docs/CONTEXT.md`, `tests/test_modulo_cli.py`.
- `%` agora e reconhecido e executado como resto da divisao, com a mesma precedencia de `*` e `/`. Operandos nao numericos e modulo por zero geram erro claro.
- `--args-json` recebe um array JSON e o passa a funcao de entrada; a execucao sem argumentos permanece igual.
- Testes unitarios, exercicio real `ex5.prw` e regressao basica dos exemplos aprovados.

### Argumento textual robusto no Windows PowerShell
- Arquivos: `main.py`, `interpreter.py`, `README.md`, `docs/CONTEXT.md`, `tests/test_modulo_cli.py`.
- Em algumas invocacoes nativas do Windows PowerShell, `--args-json '["5"]'` chega ao Python como `[5]`; o fonte `ex5.prw` chama `Val(cNum)` e esperava texto.
- `--arg 5` passa explicitamente a string `"5"` e pode ser repetido para varios parametros. Nao pode ser combinado com `--args-json`.
- `Val()` agora produz erro AdvPL claro para argumento nao textual, evitando `AttributeError` Python.

## 2026-09-22

### Suporte ao TestLab: `WHILE` direto e `IIf`
- Arquivos: `parser.py`, `interpreter.py`, `README.md`
- `WHILE ... ENDDO` passa a ser aceito alem de `DO WHILE ... ENDDO`.
- `IIf(condicao, valorVerdadeiro, valorFalso)` passa a ser funcao nativa, com tres argumentos.
- Uso: interpretacao headless de fontes reais AdvPL pelo projeto irmao `advpl-testlab`.

### 04f — `NEXT x` (nome da variável após NEXT)
- Arquivo: `parser.py`, `README.md`
- `parse_for` passou a consumir opcionalmente um `IDENTIFIER` logo após `NEXT` (apenas documentacional/legibilidade, descartado sem validação)
- Teste real: FOR aninhado 3x3 com `NEXT y`/`NEXT x` e `CRLF` (doc 04f) imprimiu exatamente a saída esperada
- Regressao OK: `exemplos/ola.prw`, `exemplos/todas-etapas.prw`, `python interpreter.py`
- README.md atualizado: referencia ao doc 04f
- Ref.: `docs/interpretador-advpl-04f-next-com-variavel.md`

## 2026-09-15

### 04e — `CRLF` e `??`
- Arquivo: `interpreter.py`, `README.md`
- Constante `CRLF` (`Chr(13)+Chr(10)`) injetada em `self.globals` na criacao do `Interpreter`, disponivel em qualquer script como PUBLIC normal (sem necessidade de `#include`)
- `??` (impressao sem quebra de linha) ja era reconhecido pelo lexer/parser; confirmado com teste real descrito no doc 04e
- Teste real: script temporario do doc 04e (User Function `ex`, laco FOR gravando em `cResultado` com `CRLF` e `?? cResultado`) imprime linha a linha `1 + i = n`
- Regressao OK: `exemplos/ola.prw`, `exemplos/todas-etapas.prw`, `python interpreter.py`
- README.md atualizado: bullets de saida (`?`/`??`) e constante `CRLF`; referencia ao doc 04e
- Ref.: `docs/interpretador-advpl-04e-crlf-dois-interrogacao.md`

## 2026-09-14

### 04b — `UserException` / `Throw` no BEGIN SEQUENCE
- Arquivo: `interpreter.py`
- Nova exceção `ThrownException` (carrega o valor lancado, não só mensagem)
- Builtins novos: `USEREXCEPTION` (cria objeto `ERROR` com `:Description` e lanca) e `THROW` (lanca qualquer valor)
- `RECOVER USING x` agora distingue: `Throw`/`UserException` -> `x` recebe o valor exato; erro interno do interpretador -> `x` recebe objeto `ERROR` com `:Description`
- Exceção propaga corretamente atraves de chamadas de funcao (pilha Python)
- Ref.: `docs/interpretador-advpl-04b-userexception-throw.md`

### 04c — `USER FUNCTION`
- Arquivos: `lexer.py`, `parser.py`
- `USER` virou palavra reservada (`TokenType.USER` + `KEYWORDS`)
- `parse_function` e `is_function_start` aceitam `STATIC` ou `USER` como prefixo opcional de `FUNCTION`
- `USER FUNCTION` tratada igual a `FUNCTION` comum (sem distincao de visibilidade)
- Ref.: `docs/interpretador-advpl-04c-user-function.md`

### 04d — `cValToChar`
- Arquivo: `interpreter.py`
- Novo builtin `CVALTOCHAR`: converte qualquer valor escalar em string (numero, logico, texto); `NIL` vira `""`; array gera erro
- Biblioteca nativa passa de 23 para 24 funcoes
- Ref.: `docs/interpretador-advpl-04d-cvaltochar.md`

### Outras alteracoes
- Criado `.gitignore` (Python: `__pycache__/`, bytecode, venv, artefatos de IDE/teste)
- Criado `docs/CONTEXT.md` (contexto do projeto e rotina de trabalho)
- README.md atualizado: funcionalidades 04b/04d, contagem de nativas (21 -> 24), seção "Testar um User Function", referencia aos docs 04b/04c/04d
- Correção do README: fragmento UTF-16 (`# LivrePL`) colado no fim do arquivo foi removido (quebrava a renderizacao no GitHub)
- Subido para `origin/main` no repositório `LivrePL`
