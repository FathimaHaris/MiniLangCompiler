from dataclasses import dataclass
from typing import List, Optional
from lexer import Token, lex

# ============================================================
#  CUSTOM COMPILER ERROR HANDLER (COLORED, NO TRACEBACK)
# ============================================================

class MiniLangSyntaxError(Exception):
    """Custom syntax error for MiniLang compiler (no traceback)."""
    RED = "\033[91m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

    def __init__(self, message, line=None, column=None, line_text=None):
        self.message = message
        self.line = line
        self.column = column
        self.line_text = line_text

    def __str__(self):
        # Header
        error = f"{self.RED}{self.BOLD}Syntax Error:{self.RESET} {self.message}"
        if self.line is not None:
            error += f" {self.CYAN}(line {self.line}, column {self.column}){self.RESET}"
        if self.line_text:
            error += f"\n  {self.line_text.rstrip()}\n  {self.YELLOW}{' ' * self.column}^{self.RESET}"
        return error


# ============================================================
#  AST NODE DEFINITIONS
# ============================================================

@dataclass
class Program:
    functions: List["Function"]

@dataclass
class Function:
    name: str
    params: List["Param"]
    return_type: str
    body: List["Stmt"]

@dataclass
class Param:
    name: str
    type: str

# ---- Statements ----
class Stmt: pass

@dataclass
class VarAssign(Stmt):
    name: str
    value: "Expr"

@dataclass
class ReturnStmt(Stmt):
    value: "Expr"

@dataclass
class PrintStmt(Stmt):
    value: "Expr"

# ---- Expressions ----
class Expr: pass

@dataclass
class BinaryOp(Expr):
    op: str
    left: "Expr"
    right: "Expr"

@dataclass
class Number(Expr):
    value: str

@dataclass
class Var(Expr):
    name: str


# ============================================================
#  PARSER IMPLEMENTATION
# ============================================================

class Parser:
    def __init__(self, tokens: List[Token], source: str = ""):
        self.tokens = tokens
        self.source_lines = source.splitlines()
        self.pos = 0

    def get_line(self, line_num: int) -> str:
        if 1 <= line_num <= len(self.source_lines):
            return self.source_lines[line_num - 1]
        return ""

    def current(self) -> Optional[Token]:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def advance(self):
        self.pos += 1

    def expect(self, type_: str):
        tok = self.current()
        if not tok or tok.type != type_:
            got = f"'{tok.value}'" if tok else "EOF"
            line_text = self.get_line(tok.line if tok else 1)
            raise MiniLangSyntaxError(
                f"Expected {type_} but got {got}",
                line=tok.line if tok else None,
                column=tok.column if tok else 0,
                line_text=line_text
            )
        self.advance()
        return tok

    # ---- Grammar rules ----

    def parse(self) -> Program:
        funcs = []
        while self.current():
            funcs.append(self.function())
        return Program(funcs)

    def function(self) -> Function:
        self.expect("FN")

        name_token = self.expect("IDENT")
        name = name_token.value

        self.expect("LPAREN")

        if self.current() is None:
            raise MiniLangSyntaxError("Unexpected end of input while parsing parameters")

        if self.current().type != "RPAREN":
            params = self.params()
        else:
            params = []

        self.expect("RPAREN")
        self.expect("COLON")

        tok = self.current()
        if tok is None:
            raise MiniLangSyntaxError("Unexpected end of input after ':' (expected return type)")

        if tok.type in ( "INT", "TYPE"):
            ret_type = tok.value
            self.advance()
        else:
            line_text = self.get_line(tok.line)
            raise MiniLangSyntaxError(
                f"Expected type name but got '{tok.value}'",
                line=tok.line,
                column=tok.column,
                line_text=line_text
            )

        body = self.block()
        return Function(name, params, ret_type, body)

    def params(self) -> List[Param]:
        params = []
        while True:
            name = self.expect("IDENT").value
            self.expect("COLON")
            type_ = self.expect("IDENT").value
            params.append(Param(name, type_))
            if self.current().type == "COMMA":
                self.advance()
                continue
            else:
                break
        return params

    def block(self) -> List["Stmt"]:
        stmts = []
        self.expect("LBRACE")
        while self.current() and self.current().type != "RBRACE":
            stmts.append(self.statement())
        self.expect("RBRACE")
        return stmts

    def statement(self) -> "Stmt":
        tok = self.current()

        if tok.type == "RETURN":
            self.advance()
            value = self.expression()
            self.expect("SEMICOLON")
            return ReturnStmt(value)

        elif tok.type == "PRINT":
            self.advance()
            self.expect("LPAREN")
            value = self.expression()
            self.expect("RPAREN")
            self.expect("SEMICOLON")
            return PrintStmt(value)

        elif tok.type == "IDENT":
            name = tok.value
            self.advance()
            self.expect("OP")
            value = self.expression()
            self.expect("SEMICOLON")
            return VarAssign(name, value)

        else:
            line_text = self.get_line(tok.line)
            raise MiniLangSyntaxError(
                f"Unexpected token '{tok.value}'",
                line=tok.line,
                column=tok.column,
                line_text=line_text
            )

    # ---- Expressions ----
    def expression(self) -> "Expr":
        left = self.term()
        while self.current() and self.current().value in {"+", "-"}:
            op = self.current().value
            self.advance()
            right = self.term()
            left = BinaryOp(op, left, right)
        return left

    def term(self) -> "Expr":
        left = self.factor()
        while self.current() and self.current().value in {"*", "/"}:
            op = self.current().value
            self.advance()
            right = self.factor()
            left = BinaryOp(op, left, right)
        return left

    def factor(self) -> "Expr":
        tok = self.current()

        if tok.type == "NUMBER":
            self.advance()
            return Number(tok.value)
        elif tok.type == "IDENT":
            self.advance()
            return Var(tok.value)
        elif tok.type == "LPAREN":
            self.advance()
            expr = self.expression()
            self.expect("RPAREN")
            return expr
        else:
            line_text = self.get_line(tok.line)
            raise MiniLangSyntaxError(
                f"Unexpected token in expression: '{tok.value}'",
                line=tok.line,
                column=tok.column,
                line_text=line_text
            )


# ============================================================
#  PRETTY PRINT AST
# ============================================================

def pretty_print(node, indent=0):
    prefix = "  " * indent
    if isinstance(node, list):
        for item in node:
            pretty_print(item, indent)
    elif hasattr(node, "__dataclass_fields__"):
        print(f"{prefix}{node.__class__.__name__}:")
        for field, value in node.__dict__.items():
            print(f"{prefix}  {field}:")
            pretty_print(value, indent + 2)
    else:
        print(f"{prefix}{node}")


# ============================================================
#  MAIN TESTING ENTRY POINT
# ============================================================

if __name__ == "__main__":
    code = """
fn main():int
{
        x = 5;
        y = x + 10;
        print(y);
        return 0;
}
    """

    try:
        tokens = lex(code)
        parser = Parser(tokens, code)
        ast = parser.parse()
        pretty_print(ast)

    except MiniLangSyntaxError as e:
        print(e)

    except SyntaxError as e:
        print(f"\033[91mSyntax Error:\033[0m {e}")

    except Exception as e:
        print(f"\033[91mInternal Compiler Error:\033[0m {e}")
