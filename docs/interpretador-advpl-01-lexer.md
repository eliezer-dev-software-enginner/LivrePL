# Interpretador AdvPL — Etapa 1: Lexer (Tokenizer)

Primeira peça do interpretador: transformar código-fonte AdvPL em uma lista de tokens. Sem isso, nada do parser ou do executor funciona.

Linguagem de implementação: **Python 3** (padrão da biblioteca, sem dependências externas).

---

## O que o lexer precisa reconhecer (escopo desta etapa)

- Palavras reservadas: `FUNCTION`, `RETURN`, `LOCAL`, `PRIVATE`, `PUBLIC`, `STATIC`, `IF`, `ELSEIF`, `ELSE`, `ENDIF`, `DO`, `WHILE`, `ENDDO`, `FOR`, `TO`, `STEP`, `NEXT`, `CASE`, `OTHERWISE`, `ENDCASE`, `AND`, `OR`, `NOT`, `LOOP`, `EXIT`
- Identificadores (nomes de variáveis e funções)
- Números (inteiros e decimais)
- Strings (`"texto"` e `'texto'`)
- Literais lógicos: `.T.`, `.F.`
- `NIL`
- Operadores: `:=`, `==`, `<>`, `!=`, `<=`, `>=`, `<`, `>`, `=`, `+`, `-`, `*`, `/`, `**`, `+=`, `-=`
- Delimitadores: `(`, `)`, `{`, `}`, `[`, `]`, `,`
- Comentários: `//` (linha) e `/* */` (bloco)
- Quebra de linha (relevante em AdvPL, já que não usa `;` como terminador — cada linha é um comando, salvo continuação com `;`)

---

## Código

```python
# lexer.py
# Etapa 1 do interpretador AdvPL: tokenizador

from enum import Enum, auto


class TokenType(Enum):
    # Literais
    NUMBER = auto()
    STRING = auto()
    LOGICAL = auto()
    NIL = auto()
    IDENTIFIER = auto()

    # Palavras reservadas
    FUNCTION = auto()
    RETURN = auto()
    LOCAL = auto()
    PRIVATE = auto()
    PUBLIC = auto()
    STATIC = auto()
    IF = auto()
    ELSEIF = auto()
    ELSE = auto()
    ENDIF = auto()
    DO = auto()
    WHILE = auto()
    ENDDO = auto()
    FOR = auto()
    TO = auto()
    STEP = auto()
    NEXT = auto()
    CASE = auto()
    OTHERWISE = auto()
    ENDCASE = auto()
    AND = auto()
    OR = auto()
    NOT = auto()
    LOOP = auto()
    EXIT = auto()

    # Operadores
    ASSIGN = auto()       # :=
    EQ = auto()           # == ou =
    NEQ = auto()          # <> ou !=
    LTE = auto()          # <=
    GTE = auto()          # >=
    LT = auto()           # <
    GT = auto()           # >
    PLUS = auto()         # +
    MINUS = auto()        # -
    STAR = auto()         # *
    SLASH = auto()        # /
    POWER = auto()        # **
    PLUS_ASSIGN = auto()  # +=
    MINUS_ASSIGN = auto() # -=

    # Delimitadores
    LPAREN = auto()
    RPAREN = auto()
    LBRACE = auto()
    RBRACE = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    COMMA = auto()

    # Estrutura
    NEWLINE = auto()
    EOF = auto()


KEYWORDS = {
    "FUNCTION": TokenType.FUNCTION,
    "RETURN": TokenType.RETURN,
    "LOCAL": TokenType.LOCAL,
    "PRIVATE": TokenType.PRIVATE,
    "PUBLIC": TokenType.PUBLIC,
    "STATIC": TokenType.STATIC,
    "IF": TokenType.IF,
    "ELSEIF": TokenType.ELSEIF,
    "ELSE": TokenType.ELSE,
    "ENDIF": TokenType.ENDIF,
    "DO": TokenType.DO,
    "WHILE": TokenType.WHILE,
    "ENDDO": TokenType.ENDDO,
    "FOR": TokenType.FOR,
    "TO": TokenType.TO,
    "STEP": TokenType.STEP,
    "NEXT": TokenType.NEXT,
    "CASE": TokenType.CASE,
    "OTHERWISE": TokenType.OTHERWISE,
    "ENDCASE": TokenType.ENDCASE,
    "AND": TokenType.AND,
    "OR": TokenType.OR,
    "NOT": TokenType.NOT,
    "LOOP": TokenType.LOOP,
    "EXIT": TokenType.EXIT,
    "NIL": TokenType.NIL,
}


class Token:
    def __init__(self, type_, value, line):
        self.type = type_
        self.value = value
        self.line = line

    def __repr__(self):
        return f"Token({self.type}, {self.value!r}, line={self.line})"


class LexError(Exception):
    pass


class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.tokens = []

    def error(self, msg):
        raise LexError(f"[linha {self.line}] {msg}")

    def peek(self, offset=0):
        p = self.pos + offset
        if p < len(self.source):
            return self.source[p]
        return "\0"

    def advance(self):
        ch = self.source[self.pos]
        self.pos += 1
        if ch == "\n":
            self.line += 1
        return ch

    def match(self, expected):
        if self.peek() == expected:
            self.advance()
            return True
        return False

    def add_token(self, type_, value=None):
        self.tokens.append(Token(type_, value, self.line))

    def tokenize(self):
        while self.pos < len(self.source):
            self.scan_token()
        self.add_token(TokenType.EOF, None)
        return self.tokens

    def scan_token(self):
        ch = self.advance()

        # espaços e tabs ignorados; quebra de linha é significativa
        if ch in " \t\r":
            return
        if ch == "\n":
            self.add_token(TokenType.NEWLINE)
            return

        # continuação de linha com ';' -> ignora o newline seguinte
        if ch == ";":
            while self.peek() in " \t\r":
                self.advance()
            if self.peek() == "\n":
                self.advance()
            return

        # comentário de linha //
        if ch == "/" and self.peek() == "/":
            while self.peek() != "\n" and self.peek() != "\0":
                self.advance()
            return

        # comentário de bloco /* ... */
        if ch == "/" and self.peek() == "*":
            self.advance()
            while not (self.peek() == "*" and self.peek(1) == "/") and self.peek() != "\0":
                self.advance()
            if self.peek() == "\0":
                self.error("Comentário de bloco não fechado")
            self.advance()  # *
            self.advance()  # /
            return

        # strings
        if ch == '"' or ch == "'":
            self.scan_string(ch)
            return

        # números
        if ch.isdigit():
            self.scan_number(ch)
            return

        # .T. / .F. / .AND. / .OR. / .NOT.
        if ch == ".":
            self.scan_dot_literal()
            return

        # identificadores e palavras reservadas
        if ch.isalpha() or ch == "_":
            self.scan_identifier(ch)
            return

        # operadores e delimitadores
        if ch == ":":
            if self.match("="):
                self.add_token(TokenType.ASSIGN, ":=")
                return
            self.error(f"Caractere inesperado ':' (esperado ':=')")

        if ch == "=":
            if self.match("="):
                self.add_token(TokenType.EQ, "==")
            else:
                self.add_token(TokenType.EQ, "=")
            return

        if ch == "<":
            if self.match(">"):
                self.add_token(TokenType.NEQ, "<>")
            elif self.match("="):
                self.add_token(TokenType.LTE, "<=")
            else:
                self.add_token(TokenType.LT, "<")
            return

        if ch == ">":
            if self.match("="):
                self.add_token(TokenType.GTE, ">=")
            else:
                self.add_token(TokenType.GT, ">")
            return

        if ch == "!":
            if self.match("="):
                self.add_token(TokenType.NEQ, "!=")
                return
            self.error("Caractere inesperado '!'")

        if ch == "+":
            if self.match("="):
                self.add_token(TokenType.PLUS_ASSIGN, "+=")
            else:
                self.add_token(TokenType.PLUS, "+")
            return

        if ch == "-":
            if self.match("="):
                self.add_token(TokenType.MINUS_ASSIGN, "-=")
            else:
                self.add_token(TokenType.MINUS, "-")
            return

        if ch == "*":
            if self.match("*"):
                self.add_token(TokenType.POWER, "**")
            else:
                self.add_token(TokenType.STAR, "*")
            return

        if ch == "/":
            self.add_token(TokenType.SLASH, "/")
            return

        if ch == "(":
            self.add_token(TokenType.LPAREN, "(")
            return
        if ch == ")":
            self.add_token(TokenType.RPAREN, ")")
            return
        if ch == "{":
            self.add_token(TokenType.LBRACE, "{")
            return
        if ch == "}":
            self.add_token(TokenType.RBRACE, "}")
            return
        if ch == "[":
            self.add_token(TokenType.LBRACKET, "[")
            return
        if ch == "]":
            self.add_token(TokenType.RBRACKET, "]")
            return
        if ch == ",":
            self.add_token(TokenType.COMMA, ",")
            return
        if ch == "?":
            # '?' e '??' tratados como identificador especial de saída
            # (o parser decide o que fazer com isso)
            self.add_token(TokenType.IDENTIFIER, "?")
            return

        self.error(f"Caractere inesperado: {ch!r}")

    def scan_string(self, quote):
        start_line = self.line
        chars = []
        while self.peek() != quote:
            if self.peek() == "\0" or self.peek() == "\n":
                self.error("String não fechada")
            chars.append(self.advance())
        self.advance()  # consome a aspa de fechamento
        self.add_token(TokenType.STRING, "".join(chars))

    def scan_number(self, first_digit):
        chars = [first_digit]
        while self.peek().isdigit():
            chars.append(self.advance())
        if self.peek() == "." and self.peek(1).isdigit():
            chars.append(self.advance())  # '.'
            while self.peek().isdigit():
                chars.append(self.advance())
        text = "".join(chars)
        value = float(text) if "." in text else int(text)
        self.add_token(TokenType.NUMBER, value)

    def scan_dot_literal(self):
        # já consumiu o primeiro '.'
        # possíveis: .T. .F. .AND. .OR. .NOT.
        start = self.pos
        chars = []
        while self.peek().isalpha():
            chars.append(self.advance())
        word = "".join(chars).upper()
        if self.peek() == ".":
            self.advance()  # consome o ponto final
            if word == "T":
                self.add_token(TokenType.LOGICAL, True)
                return
            if word == "F":
                self.add_token(TokenType.LOGICAL, False)
                return
            if word == "AND":
                self.add_token(TokenType.AND, "AND")
                return
            if word == "OR":
                self.add_token(TokenType.OR, "OR")
                return
            if word == "NOT":
                self.add_token(TokenType.NOT, "NOT")
                return
        self.error(f"Literal com ponto inválido: '.{word}'")

    def scan_identifier(self, first_char):
        chars = [first_char]
        while self.peek().isalnum() or self.peek() == "_":
            chars.append(self.advance())
        word = "".join(chars)
        upper = word.upper()
        if upper in KEYWORDS:
            self.add_token(KEYWORDS[upper], upper)
        else:
            self.add_token(TokenType.IDENTIFIER, word)


if __name__ == "__main__":
    exemplo = '''
Function Main()
    Local nTotal := 0
    Local aItens := {10, 20, 30}
    Local i

    For i := 1 To Len(aItens)
        nTotal += aItens[i]
    Next

    ? "Total: " + Str(nTotal)

Return NIL
'''
    lexer = Lexer(exemplo)
    for tok in lexer.tokenize():
        if tok.type != TokenType.NEWLINE:
            print(tok)
```

---

## Teste rápido

Rodei o script contra o exemplo do `Main()` e a saída real (verificada) é:

```
Token(TokenType.FUNCTION, 'FUNCTION', line=2)
Token(TokenType.IDENTIFIER, 'Main', line=2)
Token(TokenType.LPAREN, '(', line=2)
Token(TokenType.RPAREN, ')', line=2)
Token(TokenType.LOCAL, 'LOCAL', line=3)
Token(TokenType.IDENTIFIER, 'nTotal', line=3)
Token(TokenType.ASSIGN, ':=', line=3)
Token(TokenType.NUMBER, 0, line=3)
Token(TokenType.LOCAL, 'LOCAL', line=4)
Token(TokenType.IDENTIFIER, 'aItens', line=4)
Token(TokenType.ASSIGN, ':=', line=4)
Token(TokenType.LBRACE, '{', line=4)
Token(TokenType.NUMBER, 10, line=4)
Token(TokenType.COMMA, ',', line=4)
Token(TokenType.NUMBER, 20, line=4)
Token(TokenType.COMMA, ',', line=4)
Token(TokenType.NUMBER, 30, line=4)
Token(TokenType.RBRACE, '}', line=4)
Token(TokenType.LOCAL, 'LOCAL', line=5)
Token(TokenType.IDENTIFIER, 'i', line=5)
Token(TokenType.FOR, 'FOR', line=7)
Token(TokenType.IDENTIFIER, 'i', line=7)
Token(TokenType.ASSIGN, ':=', line=7)
Token(TokenType.NUMBER, 1, line=7)
Token(TokenType.TO, 'TO', line=7)
Token(TokenType.IDENTIFIER, 'Len', line=7)
Token(TokenType.LPAREN, '(', line=7)
Token(TokenType.IDENTIFIER, 'aItens', line=7)
Token(TokenType.RPAREN, ')', line=7)
Token(TokenType.IDENTIFIER, 'nTotal', line=8)
Token(TokenType.PLUS_ASSIGN, '+=', line=8)
Token(TokenType.IDENTIFIER, 'aItens', line=8)
Token(TokenType.LBRACKET, '[', line=8)
Token(TokenType.IDENTIFIER, 'i', line=8)
Token(TokenType.RBRACKET, ']', line=8)
Token(TokenType.NEXT, 'NEXT', line=9)
Token(TokenType.IDENTIFIER, '?', line=11)
Token(TokenType.STRING, 'Total: ', line=11)
Token(TokenType.PLUS, '+', line=11)
Token(TokenType.IDENTIFIER, 'Str', line=11)
Token(TokenType.LPAREN, '(', line=11)
Token(TokenType.IDENTIFIER, 'nTotal', line=11)
Token(TokenType.RPAREN, ')', line=11)
Token(TokenType.RETURN, 'RETURN', line=13)
Token(TokenType.NIL, 'NIL', line=13)
Token(TokenType.EOF, None, line=14)
```

Isso confirma que o lexer já reconhece corretamente: palavras reservadas, identificadores, números, arrays literais (`{`, `}`, `,`), indexação (`[`, `]`), operadores compostos (`:=`, `+=`) e a saída `?`.

---

## Limitações conhecidas desta etapa (a resolver depois)

- `?` e `??` estão sendo tratados como identificador cru — o **parser** (próxima etapa) vai precisar de uma regra especial pra reconhecer isso como comando de saída, já que não é uma chamada de função convencional.
- Ainda não trata `#define`/`#include`/`#command` — isso fica pra um módulo de pré-processamento que roda **antes** do lexer (ou como uma primeira passada sobre o texto bruto).
- Case-insensitivity do AdvPL é tratado normalizando identificadores de palavra-chave para maiúsculo, mas nomes de variáveis (`IDENTIFIER`) mantêm a grafia original — isso será resolvido no interpretador (comparação de nomes case-insensitive na tabela de símbolos).

---

## Próximo passo

Etapa 2: o **parser**, que consome essa lista de tokens e monta a AST — começando pelas expressões (precedência de operadores) e pelos comandos de fluxo (`IF`, `FOR`, `DO WHILE`).
