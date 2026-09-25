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

## 2026-09-23 — Diagnosticos de runtime

- Expressoes da AST passam a guardar a linha do token; `AdvPLRuntimeError` inclui `[linha N]` quando a origem e conhecida.
- Operacoes aritmeticas, concatenacao, comparacoes, indices de array e alguns builtins frequentes validam tipos e limites antes da operacao Python.
- `+` entre caractere e numerico sugere `cValToChar()`; erros exibem tipos AdvPL, nao tipos Python.
- Foram adicionados testes de regressao para erros comuns e caminhos validos. A logica do algoritmo continua responsabilidade do programa AdvPL; a numeracao pode ser deslocada por preprocessamento que remove linhas.

### Excecoes visiveis na CLI

- `main.py` nao captura mais erros de lexer, parser, nomes ou runtime do `.prw`; o Python mostra traceback e retorna codigo nao zero.
- Mensagens de uso incorreto das opcoes da CLI continuam com `[ERRO]` e codigo 2.
- Os testes foram atualizados para verificar a excecao propagada e a saida real do processo.

## 2026-09-23 — Parametros por referencia

- O lexer reconhece `@` e o parser representa `@nome` como argumento por referencia.
- O interpretador liga parametros a variaveis `LOCAL`, `PRIVATE`, `PUBLIC` ou `STATIC` do chamador; leitura, atribuicao e repasse de referencia preservam o mesmo valor de origem.
- Fora de argumentos de chamada, `@` gera erro explicito. Funcoes nativas do LivrePL ainda nao implementam parametros por referencia.
- Uma fixture propria reproduz o exercicio `ex13b.prw` sem depender do repositorio `caminho-protheus` nos testes do LivrePL.

## 2026-09-23 — Argumentos omitidos em chamadas

- O parser aceita lacunas em listas de argumentos de funcoes e metodos, inclusive quando ha comentario de bloco entre virgulas. Cada lacuna vira `Literal(None)` e mantem sua posicao.
- Testes cobrem lacunas iniciais, intermediarias e finais, chamadas sem argumentos e preservacao de erro sintatico real.
- Em `ZA1MVC.prw`, isso elimina o falso erro de sintaxe em `AddFields`; a verificacao seguinte encontra `oStruZA1` nao declarado, divergente do `oStruct` existente no proprio fonte.

## 2026-09-25 — Localizacao de declaracoes na AST

- `VarDecl` guarda a linha da palavra-chave (`LOCAL`, `STATIC`, `PRIVATE` ou `PUBLIC`), inclusive quando uma linha declara varias variaveis.
- O parser do LivrePL continua aceitando declaracoes em qualquer posicao: a ordem estrita pedida pelo usuario e politica do AdvPL TestLab, nao regra universal da linguagem conforme a documentacao TOTVS.
- Um teste proprio confirma a coordenada, sem depender do repositorio TestLab.
