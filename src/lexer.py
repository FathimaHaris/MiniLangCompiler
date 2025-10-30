import re
from typing import NamedTuple, List

# Define the structure of a token
class Token(NamedTuple):
    type: str
    value: str
    line: int
    column: int

# Reserved keywords in MiniLang
KEYWORDS = {
    "fn", "return", "if", "else", "while", "int", "float", "print"
}

# Token specification using regex
TOKEN_SPEC = [
    ("NUMBER",   r"\d+(\.\d+)?"),      # Integer or float
    ("IDENT",    r"[A-Za-z_][A-Za-z0-9_]*"),  # Identifiers
    ("OP",       r"[+\-*/=<>!]+"),     # Operators
    ("LPAREN",   r"\("),
    ("RPAREN",   r"\)"),
    ("LBRACE",   r"\{"),
    ("RBRACE",   r"\}"),
    ("COLON",    r":"),
    ("COMMA",    r","),
    ("SEMICOLON",r";"),
    ("NEWLINE",  r"\n"),
    ("SKIP",     r"[ \t]+"),           # Skip spaces and tabs
    ("MISMATCH", r"."),                # Any other character
]

# Combine into one big regex
token_re = re.compile("|".join(f"(?P<{name}>{pattern})" for name, pattern in TOKEN_SPEC))

def lex(code: str) -> List[Token]:
    """Tokenize MiniLang source code."""
    tokens = []
    line_num = 1
    line_start = 0

    for mo in token_re.finditer(code):
        kind = mo.lastgroup
        value = mo.group()
        column = mo.start() - line_start

        if kind == "NUMBER":
            tokens.append(Token(kind, value, line_num, column))
        elif kind == "IDENT":
            if value in KEYWORDS:
                tokens.append(Token(value.upper(), value, line_num, column))
            else:
                tokens.append(Token("IDENT", value, line_num, column))
        elif kind == "NEWLINE":
            line_num += 1
            line_start = mo.end()
        elif kind == "SKIP":
            continue
        elif kind == "MISMATCH":
            raise RuntimeError(f"Unexpected character {value!r} at line {line_num}")
        else:
            tokens.append(Token(kind, value, line_num, column))
    return tokens

if __name__ == "__main__":
    # Example program to test
    code = """
fn factorial(n:int): int {
        result = 1;
        while (n > 1) {
            result = result * n;
            n = n - 1;
        }
        return result;
}
    """
    toks = lex(code)
    for t in toks:
        print(t)
