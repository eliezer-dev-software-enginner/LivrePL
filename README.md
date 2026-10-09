# Interpretador AdvPL (Sem Licenca)

Interpretador/executor de codigo AdvPL (linguagem do Protheus/TOTVS) feito em Python, sem necessidade de AppServer, licenca ou banco de dados.

## Instalar e usar em qualquer diretorio

O projeto agora e instalavel e cria o comando `livrepl`. A instalacao abaixo usa o checkout local; nao exige publicar no PyPI.

### 1. Preparar os requisitos

Voce precisa de **Python 3.8 ou mais recente**. No Windows, marque a opcao de adicionar Python ao PATH durante a instalacao. Confira no terminal:

```bash
python --version
```

Em Linux, o comando pode ser `python3 --version`; nesse caso, use `python3` onde este guia disser `python`. Para a opcao com Git abaixo, voce tambem precisa ter Git instalado. A opcao ZIP nao exige Git.

### 2. Obter o projeto

Escolha **uma** das duas opcoes.

**Opcao A — Clonar com Git**

Abra o terminal na pasta em que deseja guardar o projeto e execute:

```bash
git clone https://github.com/eliezer-dev-software-enginner/LivrePL.git
cd LivrePL
```

**Opcao B — Baixar e extrair o ZIP**

1. Abra o [repositorio LivrePL no GitHub](https://github.com/eliezer-dev-software-enginner/LivrePL).
2. Clique no botao **Code** e escolha **Download ZIP**.
3. Extraia o ZIP inteiro para uma pasta do computador. Nao execute a instalacao dentro do arquivo compactado.
4. Abra um terminal na pasta extraida que contem **pyproject.toml**, **main.py** e **README.md**. Na branch main, ela normalmente se chama `LivrePL-main`.

Exemplo no Windows PowerShell, ajustando o caminho para onde voce extraiu:

```powershell
Set-Location "$HOME\Downloads\LivrePL-main"
```

Exemplo em Linux/macOS:

```bash
cd ~/Downloads/LivrePL-main
```

Se voce extraiu o ZIP para uma pasta que contem outra `LivrePL-main`, entre nessa pasta interna. O proximo comando de instalacao deve ser executado ao lado do `pyproject.toml`.

### 3. Instalar com pipx

Se pipx ja esta instalado, pule a preparacao abaixo.

Em Ubuntu/Debian, instale pelo gerenciador do sistema:

```bash
sudo apt update
sudo apt install pipx
pipx ensurepath
```

No Windows PowerShell, com Python disponivel:

```powershell
python -m pip install --user pipx
python -m pipx ensurepath
```

Abra um novo terminal depois de configurar o PATH e volte para a pasta obtida no passo 2. Se `pipx` ainda nao for reconhecido no Windows, use `python -m pipx` no lugar de `pipx`.

Com Python e pipx disponiveis, execute **na pasta que contem o pyproject.toml**:

```bash
pipx install .
pipx ensurepath
```

O ponto em `pipx install .` significa a pasta atual com o codigo do LivrePL, nao a pasta dos seus fontes AdvPL. A instalacao cria o comando `livrepl` em um ambiente isolado.

### 4. Executar seus fontes

Abra um novo terminal para carregar o PATH. Confira `livrepl --help`. Depois, entre em qualquer pasta com codigo AdvPL:

```bash
cd /caminho/dos/fontes
livrepl arquivo.prw MinhaFuncao
livrepl arquivo.prw MinhaFuncao --arg 5
livrepl --ast arquivo.prw
livrepl --help
```

No PowerShell:

```powershell
Set-Location C:\meus-fontes
livrepl .\arquivo.prw MinhaFuncao --arg 5
```

Caminhos relativos do fonte e operacoes de arquivo AdvPL usam o diretorio atual do terminal. O comando nao muda para a pasta de instalacao. A entrada padrao continua MAIN; para User Function informe seu nome.

### Primeiro programa

Depois de instalar, crie um arquivo `teste.prw` em uma pasta de sua escolha e salve:

```advpl
User Function Teste()
    ? "Ola, LivrePL!"
Return NIL
```

Abra o terminal nessa pasta e execute:

```bash
livrepl teste.prw Teste
```

Saida esperada:

```text
Ola, LivrePL!
```

Voce nao precisa copiar o interpretador para essa pasta nem executar o comando dentro do repositorio LivrePL.

### Atualizar ou desinstalar

Se instalou a partir de um clone, execute `git pull` na pasta LivrePL para obter as atualizacoes. Se usou ZIP, baixe e extraia uma nova copia. Em seguida, execute `pipx install --force .` na pasta do codigo atualizado. O comando sozinho reinstala o codigo local; ele nao baixa atualizacoes do GitHub.

Para desenvolver e refletir alteracoes do checkout: `pipx install --editable .`. Para remover: `pipx uninstall livrepl`.

### Alternativa ao pipx: ambiente virtual

Na pasta do repositorio, crie e instale em um ambiente virtual:

```bash
python -m venv .venv
.venv/bin/python -m pip install .
source .venv/bin/activate
```

No Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install .
.\.venv\Scripts\Activate.ps1
```

Se o PowerShell bloquear Activate.ps1, voce pode executar o comando instalado pelo caminho completo, sem ativar o ambiente: `C:\caminho\LivrePL\.venv\Scripts\livrepl.exe C:\fontes\arquivo.prw MinhaFuncao`.

Com o ambiente ativado, `livrepl` funciona de qualquer pasta. Tambem e possivel usar `python -m livrepl` com o Python desse ambiente. A execucao antiga `python main.py` continua funcionando no checkout.

## Uso e exemplos

### Executar exemplos sem instalar

```bash
python main.py exemplos/ola.prw
python main.py exemplos/todas-etapas.prw
python main.py exemplos/utilitarios.prw
```

O nome da funcao de entrada pode diferir do nome do arquivo. Por exemplo, se `ex13b.prw` declara `User Function ex13()`, execute `python main.py ex13b.prw ex13`.

### Dependencias locais com usePrw

O LivrePL carrega os fontes declarados em comentarios `//usePrw`, assim como o TestLab:

```advpl
//usePrw('auxiliar.prw')
Function Main()
    ? U_Dobro(5)
Return NIL
```

Em `auxiliar.prw`:

```advpl
User Function Dobro(nValor)
Return nValor * 2
```

Execute `livrepl principal.prw`: a saida e `10`. O mesmo carregamento funciona com `python main.py principal.prw` e `python -m livrepl principal.prw`.

- Uma declaracao por linha; aspas simples ou duplas. O caminho e relativo ao arquivo que declara a dependencia.
- Subpastas sao permitidas; dependencias devem permanecer dentro da pasta do fonte principal, como no TestLab.
- Dependencias recursivas, repetidas ou circulares sao carregadas uma unica vez por caminho resolvido.
- Arquivos ausentes, extensoes diferentes de `.prw` e caminhos fora da pasta principal geram erro com identificacao do fonte.
- Funcoes publicas e classes dos fontes carregados ficam disponiveis; User Function aceita o simbolo `U_...`. Static Function fica acessivel apenas ao proprio fonte, inclusive em code blocks e metodos definidos nele.
- Funcoes estaticas de arquivos diferentes podem ter o mesmo nome; seu estado STATIC permanece separado. Colisoes publicas sao rejeitadas segundo o perfil modern/legacy10.
- `--ast` mostra as declaracoes de todos os fontes carregados. UTF-8 (com ou sem BOM) e CP1252 sao aceitos.

`//usePrw` e uma convencao local, nao uma funcao AdvPL nem um substituto para `#include`. O preprocessamento de includes continua com os limites documentados. Para usar a mudanca numa instalacao normal, reinstale com `pipx install --force .` na pasta do LivrePL.

### Executar um modulo especifico (com entry point diferente)

```bash
python main.py arquivo.prw NOMEFUNC
```

Para passar argumentos à função de entrada, informe um array JSON em `--args-json`. Por exemplo, no PowerShell, a partir de `caminho-protheus`:

```powershell
python ..\livrePL\main.py .\Fontes\exercicios-sintaxe\nivel1\ex5.prw ex5 --args-json '["5"]'
```

Algumas configurações do Windows PowerShell removem as aspas internas antes de entregar o JSON ao Python. Para passar texto sem depender desse tratamento de aspas, prefira `--arg` (repita a opção para vários parâmetros):

```powershell
python ..\livrePL\main.py .\Fontes\exercicios-sintaxe\nivel1\ex5.prw ex5 --arg 5
```

O resultado é `eh impar`. Use `--arg 4` para testar o caminho par. `--args-json` continua disponível quando o tipo do argumento importa; `--arg` e `--args-json` não podem ser combinados. Sem argumentos, a chamada mantém o comportamento anterior: cada parâmetro ausente recebe `NIL`. `Val()` exige texto e informa um erro AdvPL quando recebe outro tipo.

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

## Aspectos tecnicos do interpretador

### Arquitetura do interpretador

Um interpretador tree-walking que executa scripts `.prw` de AdvPL diretamente no terminal. Coberto por 4 etapas:

1. **Lexer** - tokenizacao de codigo-fonte AdvPL
2. **Parser** - analise recursiva descendente gerando AST
3. **Interpretador** - execucao percorrendo a AST (com pilha de chamadas, escopo dinamico de PRIVATE, STATIC persistente)
4. **Etapa 4** - DO CASE, BEGIN SEQUENCE/RECOVER, code blocks `{|x| expr}`, classes (CLASS/METHOD, heranca simples via FROM), `UserException()`/`Throw()` para excecoes lancadas pelo proprio codigo AdvPL

### Funcionalidades da linguagem

- **Tipos**: Character, Numeric, Logical, Date, Array, NIL, Block (code block), Object. Datas possuem tipo proprio, data vazia, comparacoes e calculos por dias.
- **Controle de fluxo**: IF/ELSEIF/ELSE, FOR..TO..STEP/NEXT, DO WHILE/ENDDO, WHILE/ENDDO, DO CASE/OTHERWISE, BEGIN SEQUENCE/RECOVER (recupera tanto `UserException`/`Throw` quanto erros internos do interpretador)
- **Escopo**: LOCAL, PRIVATE (dinamico pela pilha), PUBLIC, STATIC (persistente entre chamadas)
- **Parametros por referencia**: `@variavel` em chamadas de funcoes e metodos do proprio `.prw` permite que o parametro altere a variavel de quem chamou. Sem `@`, escalares sao passados por valor. Entre as nativas, `FreeObj(@objeto)` aceita referencia para limpar a variavel.
- **Argumentos omitidos**: chamadas como `Funcao(1,,3)` e `oModel:AddFields('ID', /*cOwner*/, oStruct)` preservam a posicao vazia como `NIL`; comentarios entre virgulas nao viram argumentos.
- **OOP**: CLASS/DATA/METHOD, heranca simples (FROM), SELF, ::attr, obj:Metodo()
- **Code blocks**: `{|x,y| x+y}` com closure de leitura + Eval()
- **Excecoes**: `UserException(cMsg)` cria um objeto `ERROR` com `:Description` e lanca; `Throw(valor)` lanca qualquer valor/objeto (inclusive classes de excecao do proprio usuario)
- **69 funcoes nativas**: texto, arrays, datas, conversoes, erros, saida de terminal e arquivos locais. Lista completa e limites em [biblioteca-padrao.md](docs/biblioteca-padrao.md).
- **Datas e relogio**: `Date()` retorna a data do sistema com `ValType() == "D"`; `Time()` retorna `HH:MM:SS`. `CToD`/`DToC` usam `DD/MM/AAAA` por padrao; `SToD`/`DToS` usam `AAAAMMDD`.
- **Busca em texto**: operador `$`, alem de `At` e `RAt`.
- **Saida**: `?` (com quebra de linha) e `??` (nao quebra linha, concatena na mesma linha)
- **Modulo**: `%` calcula o resto da divisao, com a mesma precedencia de `*` e `/`.
- **Constante global `CRLF`**: `Chr(13)+Chr(10)` pre-definida como PUBLIC, disponivel em qualquer script (padrao do PROTHEUS.CH)
- **Preprocessador basico**: `#define`, `#include` (no-op)
- **Continuacao de linha**: `;` aceita comentario `//` antes da quebra de linha.

### Estrutura do codigo

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

### Ver a AST gerada

```bash
python main.py --ast exemplos/todas-etapas.prw
```

### Diagnosticos de execucao

Erros no `.prw` agora lancam excecoes: o Python exibe o traceback no terminal e o processo termina com codigo diferente de zero, sem o prefixo `[ERRO]`. A mensagem da excecao inclui a linha da expressao e os tipos AdvPL envolvidos. Isso cobre concatenacao entre texto e numero, operadores aritmeticos e comparacoes com tipos incompativeis, divisao/modulo por zero, variavel ou funcao inexistente, indice invalido de array e argumentos incorretos em `Len`, `AllTrim`, `Upper`, `Lower` e `AAdd`. Por exemplo, `"Total: " + 7` produz `AdvPLRuntimeError: [linha 3] ... Use cValToChar() ...`. Erros de uso das opcoes da CLI ainda aparecem como mensagens `[ERRO]`. Diretivas removidas pelo preprocessador podem alterar a numeracao das linhas. Esses diagnosticos nao validam a logica do algoritmo: um laco que conta itens errados pode executar sem erro.

### Perfis de nomes

O perfil `modern` e o padrao do LivrePL: nomes completos, sem truncamento. Para simular a regra historica dos dez caracteres significativos, passe `--name-profile legacy10`:

```powershell
python main.py arquivo.prw MinhaFuncao --name-profile legacy10
```

Nesse perfil, funcoes, classes, metodos e variaveis sao resolvidos pelos dez primeiros caracteres; uma `User Function` tambem tem o simbolo externo `U_` seguido dos oito primeiros caracteres do nome. Declaracoes diferentes que colidam geram erro explicito antes da execucao, em vez de sobrescrever uma definicao. A opcao e uma simulacao de compatibilidade, nao uma garantia de comportamento para toda versao do AppServer.

### Rodar o modulo interpreter diretamente

```bash
python interpreter.py    # roda exemplo com PRIVATE dinamico
python lexer.py          # imprime tokens do exemplo basico
python parser.py         # imprime AST do exemplo basico
```

### Documentacao tecnica

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

### Como foi construido

O projeto foi idealizado e conduzido por **Eliezer Dev** ([GitHub](https://github.com/eliezer-dev-software-enginner)), que definiu o escopo, validou cada etapa e decidiu as proximas construcoes da linguagem a implementar.

- **Claude Code (modelo Claude Sonnet 5, esforco Medium)** foi usado para o levantamento de requisitos e para desenhar a arquitetura do interpretador (lexer -> parser/AST -> tree-walking interpreter) em conversa iterativa, etapa por etapa. Tambem gerou toda a documentacao tecnica em Markdown presente em `docs/` - incluindo o escopo inicial (v1), o design de cada etapa (lexer, parser, interpretador, OOP/excecoes) e os trechos de codigo Python correspondentes, sempre testando cada peca antes de documentar a saida real.
- **OpenCode** foi usado para traduzir os trechos de codigo Python presentes nos documentos Markdown de `docs/` nas implementacoes de fato do projeto (`lexer.py`, `parser.py`, `interpreter.py`, etc.), integrando tudo em uma base de codigo coesa e executavel.
