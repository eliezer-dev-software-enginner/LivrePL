# Escopo do Interpretador AdvPL (Linguagem Pura) — v1

Objetivo: executar scripts `.prw` básicos localmente, sem AppServer, sem SX3, sem MVC, sem banco de dados. Só a linguagem.

---

## 1. Arquitetura geral

```
Código-fonte (.prw)
      │
      ▼
[1] Pré-processador   → expande #command, #xtranslate, #define, #include
      │
      ▼
[2] Lexer/Tokenizer   → transforma texto em tokens
      │
      ▼
[3] Parser            → gera AST (Abstract Syntax Tree)
      │
      ▼
[4] Interpretador     → percorre a AST e executa (tree-walking interpreter)
```

Cada etapa é um módulo independente. Recomendo Python para o protótipo (rapidez de desenvolvimento) — dá pra migrar pra outra linguagem depois se precisar de performance.

---

## 2. Pré-processador

O pré-processador é a etapa mais "estranha" pra quem vem de linguagens modernas, porque muita coisa que parece sintaxe da linguagem é na verdade macro.

**Escopo v1:**
- `#define CONST valor` — substituição simples de constantes
- `#include "protheus.ch"` — ignorar ou resolver como no-op (não vamos simular os `.ch` completos, só os `#define` que você realmente usar)
- `#command ADD OPTION ... ACTION ...` — tratar como caso especial hardcoded (não precisa de motor genérico de `#command` na v1)
- `#xtranslate` — fora do escopo v1, salvo se você usar em algo específico

**Fora do escopo v1:** motor genérico de `#command`/`#xtranslate` com regras arbitrárias definidas pelo usuário.

---

## 3. Tipos de dados

| Tipo AdvPL | Equivalente interno | Observação |
|---|---|---|
| Character | string | `"texto"` ou `'texto'` |
| Numeric | float/int | AdvPL não distingue muito na sintaxe |
| Logical | bool | `.T.` / `.F.` |
| Date | objeto Date | `CTOD("01/01/2026")` |
| Array | list | `{1, 2, 3}` |
| NIL | None | `NIL` |
| Block (codeblock) | função anônima | `{|x| x + 1}` |
| Object | instância de classe | ver seção Classes |

---

## 4. Comandos de controle de fluxo

- `IF / ELSEIF / ELSE / ENDIF`
- `DO WHILE / ENDDO` (com `LOOP` e `EXIT`)
- `FOR ... TO ... STEP ... NEXT`
- `DO CASE / CASE / OTHERWISE / ENDCASE`
- `BEGIN SEQUENCE / RECOVER / END SEQUENCE` (equivalente a try/catch simplificado)

---

## 5. Declaração de variáveis e escopo

- `LOCAL`
- `PRIVATE` — com propagação para funções chamadas na mesma pilha (esse é o ponto mais delicado; escopo dinâmico, não léxico)
- `PUBLIC`
- `STATIC`
- Atribuição: `:=`

**Observação importante:** `PRIVATE` em AdvPL/Clipper usa escopo dinâmico — uma variável `PRIVATE` declarada numa função é visível nas funções chamadas por ela (pilha), não apenas na função onde foi criada. Isso é diferente de tudo que existe em Python/JS/etc. e precisa de uma pilha de escopos dedicada no interpretador, não um simples dicionário por função.

---

## 6. Funções e sintaxe de comando

- `FUNCTION nome(param1, param2) ... RETURN valor`
- `STATIC FUNCTION`
- Passagem de parâmetros por valor (padrão) e por referência (`@variavel`)
- Sintaxe de comando (sem parênteses) vs. sintaxe de função (com parênteses) — ex: `? "oi"` é açúcar sintático pra uma chamada de função de saída

---

## 7. Funções nativas mínimas (biblioteca padrão da v1)

**String:**
`AllTrim`, `Alltrim`, `Len`, `SubStr`, `StrTran`, `Upper`, `Lower`, `Space`, `PadR`, `PadL`, `Val`, `Str`

**Numérica:**
`Round`, `Int`, `Abs`, `Max`, `Min`

**Array:**
`AAdd`, `ASize`, `ALen`, `AScan`, `ASort`, `ArrayToList` (se necessário)

**Data:**
`CTOD`, `DTOC`, `Date`, `Day`, `Month`, `Year`

**Saída/console:**
`ConOut`, `?` / `??` (print simples no terminal, sem depender de `ConsoleLog=1` do appserver.ini)

**Tipo/validação:**
`ValType`, `Empty`, `IsNil`

---

## 8. Classes (OOP básico)

Escopo v1 reduzido, sem herança múltipla nem os recursos avançados do framework:

- `CLASS nome / ENDCLASS`
- `DATA atributo`
- `METHOD nome() CONSTRUCTOR`
- `METHOD nome() CLASS nome` (implementação fora da declaração)
- Herança simples: `CLASS Filha FROM Pai`

**Fora do escopo v1:** interfaces, classes friend, `WITH OBJECT`, persistência de objetos.

---

## 9. Fora do escopo (explícito)

Para não gerar expectativa errada — isto **não** entra na v1:
- Qualquer coisa de banco de dados (`DBUseArea`, SX3, alias de tabela)
- MVC (`FWMBrowse`, `ModelDef`, `ViewDef`)
- REST (`WSRESTFUL`), RPC, Pontos de Entrada
- `SmartClient`, `MsgAlert`, interface gráfica
- Multi-thread / `StartJob`

---

## 10. Roteiro de implementação sugerido

1. Lexer (tokenizar strings, números, operadores, palavras reservadas)
2. Parser de expressões (precedência de operadores: `+ - * / ** := == <> AND OR NOT`)
3. Parser de comandos de fluxo (`IF`, `DO WHILE`, `FOR`)
4. Interpretador rodando só expressões + `IF`/`FOR`/`DO WHILE` + `?`
5. Adicionar `FUNCTION`/`RETURN` com pilha de chamadas
6. Implementar escopo `PRIVATE`/`PUBLIC`/`STATIC` corretamente
7. Adicionar arrays e funções nativas de string/array
8. Adicionar `CLASS`/`METHOD` por último (é o que mais depende do resto já funcionar)

---

## 11. Critério de "pronto" para v1

Você consegue rodar um `.prw` simples do tipo:

```advpl
Function Main()
    Local nTotal := 0
    Local aItens := {10, 20, 30}
    Local i

    For i := 1 To Len(aItens)
        nTotal += aItens[i]
    Next

    ? "Total: " + Str(nTotal)

Return NIL
```

...direto no terminal, sem AppServer, sem licença, sem servidor de compilação.
