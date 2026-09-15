# Interpretador AdvPL (Sem Licenca)

Interpretador/executor de codigo AdvPL (linguagem do Protheus/TOTVS) feito em Python, sem necessidade de AppServer, licenca ou banco de dados.

## O que e

Um interpretador tree-walking que executa scripts `.prw` de AdvPL diretamente no terminal. Coberto por 4 etapas:

1. **Lexer** - tokenizacao de codigo-fonte AdvPL
2. **Parser** - analise recursiva descendente gerando AST
3. **Interpretador** - execucao percorrendo a AST (com pilha de chamadas, escopo dinamico de PRIVATE, STATIC persistente)
4. **Etapa 4** - DO CASE, BEGIN SEQUENCE/RECOVER, code blocks `{|x| expr}`, classes (CLASS/METHOD, heranca simples via FROM), `UserException()`/`Throw()` para excecoes lancadas pelo proprio codigo AdvPL

## Funcionalidades

- **Tipos**: Character, Numeric, Logical, Array, NIL, Block (code block)
- **Controle de fluxo**: IF/ELSEIF/ELSE, FOR..TO..STEP/NEXT, DO WHILE/ENDDO, DO CASE/OTHERWISE, BEGIN SEQUENCE/RECOVER (recupera tanto `UserException`/`Throw` quanto erros internos do interpretador)
- **Escopo**: LOCAL, PRIVATE (dinamico pela pilha), PUBLIC, STATIC (persistente entre chamadas)
- **OOP**: CLASS/DATA/METHOD, heranca simples (FROM), SELF, ::attr, obj:Metodo()
- **Code blocks**: `{|x,y| x+y}` com closure de leitura + Eval()
- **Excecoes**: `UserException(cMsg)` cria um objeto `ERROR` com `:Description` e lanca; `Throw(valor)` lanca qualquer valor/objeto (inclusive classes de excecao do proprio usuario)
- **24 funcoes nativas**: Len, Str, CValToChar, AllTrim, Upper, Lower, SubStr, Val, Space, PadR, PadL, AAdd, ASize, ALen, ValType, Empty, Round, Int, Abs, Max, Min, Eval, UserException, Throw
- **Saida**: `?` (com quebra de linha) e `??` (nao quebra linha, concatena na mesma linha)
- **Constante global `CRLF`**: `Chr(13)+Chr(10)` pre-definida como PUBLIC, disponivel em qualquer script (padrao do PROTHEUS.CH)
- **Preprocessador basico**: `#define`, `#include` (no-op)

## Como testar

### Requisitos

- Python 3.6+

### Executar um script .prw

```bash
python main.py exemplos/ola.prw
python main.py exemplos/todas-etapas.prw
```

### Ver a AST gerada

```bash
python main.py --ast exemplos/todas-etapas.prw
```

### Executar um modulo especifico (com entry point diferente)

```bash
python main.py arquivo.prw NOMEFUNC
```

### Testar um User Function

Scripts AdvPL costumam declarar o ponto de entrada como `User Function`, nao como `Function Main()`. O interpretador aceita as duas formas — para executar um `User Function`, passe o nome da funcao como entry point:

```bash
# ola.prw:
User Function ola()
    Local cNome := "Dev"
    ? cNome
Return(Nil)

python main.py ola.prw ola
```

Saida:
```
Dev
```

Se o script so tiver `User Function` (sem `Function Main()`), executar sem passar o nome gera o erro `Funcao de entrada 'MAIN' nao encontrada` — basta passar o nome da funcao.

### Rodar o modulo interpreter diretamente

```bash
python interpreter.py    # roda exemplo com PRIVATE dinamico
python lexer.py          # imprime tokens do exemplo basico
python parser.py         # imprime AST do exemplo basico
```

### Testar criando um .prw com codigo AdvPL

```bash
# crie um arquivo teste.prw:
cat > teste.prw << 'EOF'
Function Main()
    ? "Hello World!"
    ? 2 + 2
Return NIL
EOF

python main.py teste.prw
```

Saida:
```
Hello World!
4
```

## Estrutura

```
.
├── main.py            # CLI: python main.py arquivo.prw
├── preprocessor.py    # #define / #include (roda antes do lexer)
├── lexer.py           # Etapa 1: tokenizador
├── parser.py          # Etapa 2: parser recursivo -> AST
├── interpreter.py     # Etapa 3+4: tree-walking executor
├── exemplos/
│   ├── ola.prw        # FOR, IF, PRIVATE, nativas basicas
│   └── todas-etapas.prw  # DO CASE, code blocks, CLASS/METHOD
└── docs/              # Documentacao detalhada por etapa
```

## Exemplo completo

```advpl
Function Main()
    Local aNotas := {7, 8, 9, 10}
    Local nMedia := 0
    Local i

    For i := 1 To Len(aNotas)
        nMedia += aNotas[i]
    Next
    nMedia := Round(nMedia / Len(aNotas), 1)

    Do Case
    Case nMedia >= 9
        ? "Aprovado com excelencia:", Str(nMedia)
    Case nMedia >= 6
        ? "Aprovado:", Str(nMedia)
    Otherwise
        ? "Reprovado:", Str(nMedia)
    EndCase

    Local bDobro := {|x| x * 2}
    ? "Dobro de 5:", Eval(bDobro, 5)

    Local oAluno := Aluno():New("Maria", 21)
    oAluno:Apresentar()

Return NIL

Class Aluno
    Data cNome
    Data nIdade

    Method New(cNome, nIdade) Constructor
    Method Apresentar()
EndClass

Method New(cNome, nIdade) Class Aluno
    ::cNome := cNome
    ::nIdade := nIdade
Return Self

Method Apresentar() Class Aluno
    ? "Sou " + ::cNome + ", tenho " + Str(::nIdade) + " anos"
Return NIL
```

## Limitacoes (escopo v1)

Fora do escopo (por design): banco de dados (DBUseArea, SX3, alias), MVC (FWMBrowse), REST (WSRESTFUL), SmartClient, multi-thread, code blocks multi-comando, heranca multipla.

## Referencia

Documentacao detalhada de cada etapa esta em `docs/`:

- `escopo-interpretador-advpl-v1.md` - escopo geral
- `interpretador-advpl-01-lexer.md` - etapa 1
- `interpretador-advpl-02-parser.md` - etapa 2
- `interpretador-advpl-03-interpretador.md` - etapa 3
- `interpretador-advpl-04-docase-sequence-blocos-classes.md` - etapa 4
- `interpretador-advpl-04b-userexception-throw.md` - adendo: `UserException`/`Throw` no BEGIN SEQUENCE
- `interpretador-advpl-04c-user-function.md` - correcao: `USER FUNCTION`
- `interpretador-advpl-04d-cvaltochar.md` - correcao: `CValToChar`
- `interpretador-advpl-04e-crlf-dois-interrogacao.md` - correcao: `CRLF` e `??`
- `interpretador-advpl-04f-next-com-variavel.md` - correcao: `NEXT x` (variavel opcional apos NEXT)
- `CONTEXT.md` - contexto do projeto e rotina de trabalho
- `DECISIONS.md` - registro de modificacoes

## FAQ

**Pra quem e recomendado?**
Para estudantes e analistas de sistemas que querem testar trechos de codigo AdvPL rapidamente, sem depender de um ambiente Protheus completo - nem sempre acessivel fora do trabalho. Ideal para estudar a sintaxe da linguagem, treinar logica de programacao em AdvPL, ou rodar scripts isolados (algoritmos, manipulacao de string/array, OOP basico). Nao substitui o Protheus para nada que dependa de banco de dados, dicionario de dados (SX3) ou MVC.

**Infringe os termos de uso do Protheus?**
Nao. Este projeto nao usa, nao distribui e nao faz engenharia reversa de nenhum binario da TOTVS (AppServer, compilador, etc.) - e um interpretador escrito do zero em Python que reconhece a *sintaxe* da linguagem AdvPL, sem nenhum codigo proprietario da TOTVS envolvido. Ele nao tem qualquer pretensao comercial, e nao recria o framework Protheus (SX3, MVC, REST, licenciamento) - so a linguagem "pura". Ainda assim, isto nao e uma opiniao juridica; se voce pretende usar isso em contexto corporativo, vale validar com sua empresa.

**O que e AST?**
AST (*Abstract Syntax Tree*, ou Arvore Sintatica Abstrata) e a representacao estruturada do codigo depois que ele passa pela analise gramatical - cada lacos, condicional, operacao e chamada de funcao vira um "no" em uma arvore, em vez de continuar sendo texto solto. E essa arvore que o interpretador percorre para executar o programa (por isso o termo *tree-walking interpreter*). Rode `python main.py --ast arquivo.prw` para ver a AST de um script seu.

**Meu codigo .prw real do trabalho roda aqui?**
So se ele for "AdvPL puro" - sem `DBUseArea`, sem classes do framework (`FWMBrowse`, `ModelDef`), sem `WSRESTFUL`, sem Pontos de Entrada. Um `.prw` que ja depende do dicionario de dados (SX3) ou de banco nao vai rodar, porque esse ecossistema nao foi (e nao esta previsto para ser) recriado aqui - ver secao "Limitacoes".

**Por que Python e nao outra linguagem?**
Velocidade de desenvolvimento do prototipo - parser e interpretador tree-walking em Python sao rapidos de escrever e depurar, e nao ha restricao de performance critica pro objetivo do projeto (rodar scripts pequenos localmente, nao processar carga de producao).

**O projeto vai crescer pra suportar banco de dados/MVC no futuro?**
Nao esta no roadmap. Isso praticamente significaria reimplementar o Protheus inteiro (SX3, DBAccess, MVC, REST), o que foge do objetivo original do projeto - rodar a linguagem "pura" localmente, sem dependencia de infraestrutura.

**Posso contribuir?**
Sim. Abra uma issue ou PR - principalmente ideias de exemplos `.prw`, funcoes nativas faltando, ou correcoes de comportamento que divirjam do AdvPL real.

## Como foi construido

O projeto foi idealizado e conduzido por **Eliezer Dev** ([GitHub](https://github.com/eliezer-dev-software-enginner)), que definiu o escopo, validou cada etapa e decidiu as proximas construcoes da linguagem a implementar.

- **Claude Code (modelo Claude Sonnet 5, esforco Medium)** foi usado para o levantamento de requisitos e para desenhar a arquitetura do interpretador (lexer -> parser/AST -> tree-walking interpreter) em conversa iterativa, etapa por etapa. Tambem gerou toda a documentacao tecnica em Markdown presente em `docs/` - incluindo o escopo inicial (v1), o design de cada etapa (lexer, parser, interpretador, OOP/excecoes) e os trechos de codigo Python correspondentes, sempre testando cada peca antes de documentar a saida real.
- **OpenCode** foi usado para traduzir os trechos de codigo Python presentes nos documentos Markdown de `docs/` nas implementacoes de fato do projeto (`lexer.py`, `parser.py`, `interpreter.py`, etc.), integrando tudo em uma base de codigo coesa e executavel.