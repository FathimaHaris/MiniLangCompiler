# src/parser.py

from dataclasses import dataclass
from typing import List, Optional
from lexer import Token, lex

# ========== AST NODE DEFINITIONS ==========

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
    left: Expr
    right: Expr

@dataclass
class Number(Expr):
    value: str

@dataclass
class Var(Expr):
    name: str



# ========== PARSER IMPLEMENTATION ==========

class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def current(self) -> Token:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def advance(self):
        self.pos += 1

    def expect(self, type_: str):
        tok = self.current()
        if not tok or tok.type != type_:
            raise SyntaxError(f"Expected {type_} but got {tok}")
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
        name = self.expect("IDENT").value
        self.expect("LPAREN")
        params = self.params() if self.current().type != "RPAREN" else []
        self.expect("RPAREN")
        self.expect("COLON")
        tok = self.current()
        if tok.type in ("IDENT", "INT"):
          ret_type = tok.value
          self.advance()
        else:
           raise SyntaxError(f"Expected type name but got {tok}")

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

    def block(self) -> List[Stmt]:
        stmts = []
        self.expect("LBRACE")
        while self.current().type != "RBRACE":
            stmts.append(self.statement())
        self.expect("RBRACE")
        return stmts

    def statement(self) -> Stmt:
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
            # assignment
            name = tok.value
            self.advance()
            self.expect("OP")  # should be "="
            value = self.expression()
            self.expect("SEMICOLON")
            return VarAssign(name, value)

        else:
            raise SyntaxError(f"Unexpected token {tok}")

    # ---- Expressions ----
    def expression(self) -> Expr:
        left = self.term()
        while self.current() and self.current().value in {"+", "-"}:
            op = self.current().value
            self.advance()
            right = self.term()
            left = BinaryOp(op, left, right)
        return left

    def term(self) -> Expr:
        left = self.factor()
        while self.current() and self.current().value in {"*", "/"}:
            op = self.current().value
            self.advance()
            right = self.factor()
            left = BinaryOp(op, left, right)
        return left

    def factor(self) -> Expr:
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
            raise SyntaxError(f"Unexpected token in expression: {tok}")



def pretty_print(node, indent=0):
    prefix = "  " * indent
    if isinstance(node, list):
        for item in node:
            pretty_print(item, indent)
    elif hasattr(node, "__dataclass_fields__"):  # If it's a dataclass (AST node)
        print(f"{prefix}{node.__class__.__name__}:")
        for field, value in node.__dict__.items():
            print(f"{prefix}  {field}:")
            pretty_print(value, indent + 2)
    else:
        print(f"{prefix}{node}")






if __name__ == "__main__":
    code = """
fn main(): int {
        x = 5;
        y = x + 10;
        print(y);
        return 0;
}
    """

    tokens = lex(code)
    parser = Parser(tokens)
    ast = parser.parse()
    pretty_print(ast)

