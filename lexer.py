# lexer.py
# Etapa 1 + Etapa 4 do interpretador AdvPL: tokenizador
#
# Etapa 4 adiciona os tokens: BEGIN, SEQUENCE, RECOVER, END, USING,
# CLASS, ENDCLASS, DATA, METHOD, CONSTRUCTOR, FROM, COLON (:), DCOLON (::)
# e PIPE (|), além do reconhecimento de "??".

from enum import Enum, auto


class TokenType(Enum):
    # Literais
    NUMBER = auto()
    STRING = auto()
    LOGICAL = auto()
    NIL = auto()
    IDENTIFIER = auto()

    # Palavras reservadas (etapas 1-3)
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

    # Palavras reservadas (etapa 4)
    BEGIN = auto()
    SEQUENCE = auto()
    RECOVER = auto()
    END = auto()
    USING = auto()
    CLASS = auto()
    ENDCLASS = auto()
    DATA = auto()
    METHOD = auto()
    CONSTRUCTOR = auto()
    FROM = auto()
    USER = auto()

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
    PERCENT = auto()      # %
    POWER = auto()        # **
    PLUS_ASSIGN = auto()  # +=
    MINUS_ASSIGN = auto() # -=
    AT = auto()

    # Delimitadores
    LPAREN = auto()
    RPAREN = auto()
    LBRACE = auto()
    RBRACE = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    COMMA = auto()
    COLON = auto()       # :   (etapa 4)
    DCOLON = auto()      # ::  (etapa 4)
    PIPE = auto()        # |   (etapa 4)

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
    # etapa 4
    "BEGIN": TokenType.BEGIN,
    "SEQUENCE": TokenType.SEQUENCE,
    "RECOVER": TokenType.RECOVER,
    "END": TokenType.END,
    "USING": TokenType.USING,
    "CLASS": TokenType.CLASS,
    "ENDCLASS": TokenType.ENDCLASS,
    "DATA": TokenType.DATA,
    "METHOD": TokenType.METHOD,
    "CONSTRUCTOR": TokenType.CONSTRUCTOR,
    "FROM": TokenType.FROM,
    "USER": TokenType.USER,
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
            if self.match(":"):
                self.add_token(TokenType.DCOLON, "::")
                return
            self.add_token(TokenType.COLON, ":")
            return

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

        if ch == "%":
            self.add_token(TokenType.PERCENT, "%")
            return

        if ch == "@":
            self.add_token(TokenType.AT, "@")
            return

        if ch == "|":
            self.add_token(TokenType.PIPE, "|")
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
            if self.match("?"):
                self.add_token(TokenType.IDENTIFIER, "??")
            else:
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
