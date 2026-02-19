import re
from typing import NamedTuple, List

class Token(NamedTuple):
    type: str
    value: str
    line: int
    column: int

KEYWORDS = {
    "fn", "return", "if", "else", "while",
    "int", "float", "bool", "string", "print", "true", "false"
}

TOKEN_SPEC = [
    ("NUMBER",   r"\d+(\.\d+)?"),
    ("STRING",   r'"([^"\\]|\\.)*"'),
    ("IDENT",    r"[A-Za-z_][A-Za-z0-9_]*"),
    ("OP",       r"[+\-*/=<>!]+"),
    ("LPAREN",   r"\("),
    ("RPAREN",   r"\)"),
    ("LBRACE",   r"\{"),
    ("RBRACE",   r"\}"),
    ("COLON",    r":"),
    ("COMMA",    r","),
    ("SEMICOLON",r";"),
    ("NEWLINE",  r"\n"),
    ("SKIP",     r"[ \t]+"),
    ("MISMATCH", r"."),
]

token_re = re.compile("|".join(f"(?P<{name}>{pattern})" for name, pattern in TOKEN_SPEC))

def lex(code: str) -> List[Token]:
    tokens = []
    line_num = 1
    line_start = 0

    for mo in token_re.finditer(code):
        kind = mo.lastgroup
        value = mo.group()
        column = mo.start() - line_start

        if kind == "NUMBER":
            tokens.append(Token(kind, value, line_num, column))
        elif kind == "STRING":
            value = value[1:-1]  # remove quotes
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
    code = '''
fn main(): int {
    x: int = 42;
    y: string = "hello world";
    flag: bool = true;
    print(y);
    return 0;
}
    '''
    for t in lex(code):
        print(t)
