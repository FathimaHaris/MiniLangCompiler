from dataclasses import dataclass
from typing import List, Optional
from lexer import Token, lex
from typing import NamedTuple

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
    type_: Optional[str] 
    value: "Expr"

class VarDecl(NamedTuple):
    name: str
    type_: str



@dataclass
class ReturnStmt(Stmt):
    value: Optional["Expr"] = None

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


@dataclass
class StringLiteral(Expr):
    value: str

@dataclass
class IfStmt(Stmt):
    condition: "Expr"
    then_branch: List["Stmt"]
    else_branch: Optional[List["Stmt"]] = None

@dataclass
class WhileStmt(Stmt):
    condition: "Expr"
    body: List["Stmt"]


# ============================================================
#  PARSER IMPLEMENTATION
# ============================================================

class Parser:
    def __init__(self, tokens: List[Token], source: str = ""):
        self.tokens = tokens
        self.source_lines = source.splitlines()
        self.pos = 0
        self.symbols = {}  # Keep track of declared variables

    def get_line(self, line_num: int) -> str:
        if 1 <= line_num <= len(self.source_lines):
            return self.source_lines[line_num - 1]
        return ""

    def current(self) -> Optional[Token]:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def advance(self):
        self.pos += 1

    def peek(self, offset=1):
        """Look ahead by `offset` tokens without advancing."""
        if self.pos + offset < len(self.tokens):
            return self.tokens[self.pos + offset]
        return None


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

        # ---- Optional return type ----
        if self.current() and self.current().type == "COLON":
            self.advance()
            tok = self.current()

            if tok is None:
                raise MiniLangSyntaxError("Unexpected end of input after ':' (expected return type)")

            # Accept any valid type name
            if tok.type in ("INT", "FLOAT", "BOOL", "STRING", "VOID"):
                ret_type = tok.value
                self.advance()
            elif tok.type == "IDENT":
                # Allow user-defined types later (e.g., struct names)
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
        else:
            # No type declared — default to void
            ret_type = "void"

        # ---- Function body ----
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
    

    def return_stmt(self):
        self.expect("RETURN")
        # allow both `return;` and `return <expr>;`
        if self.current() and self.current().type != "SEMICOLON":
            value = self.expression()
        else:
            value = None
        self.expect("SEMICOLON")
        return ReturnStmt(value)




    def print_stmt(self):
        self.expect("PRINT")
        self.expect("LPAREN")
        value = self.expression()
        self.expect("RPAREN")
        self.expect("SEMICOLON")
        return PrintStmt(value)
    

    def statement(self):
        tok = self.current()

        if tok is None:
            return None

        if tok.type == "RETURN":
            return self.return_stmt()
        
        elif tok.type == "PRINT":
            return self.print_stmt()
        
        elif tok.type == "IF":
            return self.if_stmt()
        
        elif tok.type == "WHILE":
            return self.while_stmt()
        
        elif tok.type == "IDENT":
            # Could be variable assignment or function call
            next_tok = self.peek()
            if next_tok and next_tok.type in ("COLON", "OP", "LPAREN"):
                return self.var_assign_or_call()
            else:
                raise MiniLangSyntaxError(f"Unexpected token {tok.value}")
        else:
            line_text = self.get_line(tok.line)
            raise MiniLangSyntaxError(
                f"Unexpected statement start: '{tok.value}'",
                line=tok.line,
                column=tok.column,
                line_text=line_text
            )



    def if_stmt(self):

        self.expect("IF")
        self.expect("LPAREN")
        condition = self.expression()
        self.expect("RPAREN")

        then_branch = self.block()
        else_branch = None

        if self.current() and self.current().type == "ELSE":
            self.advance()
            else_branch = self.block()

        return IfStmt(condition, then_branch, else_branch)
    
    def while_stmt(self):

        self.expect("WHILE")
        self.expect("LPAREN")
        condition = self.expression()
        self.expect("RPAREN")
        body = self.block()
        return WhileStmt(condition, body)




    def var_assign_or_call(self):
        name_token = self.expect("IDENT")
        name = name_token.value

        var_type = None
        # Case 1: optional declaration
        if self.current() and self.current().type == "COLON":
            self.advance()
            type_tok = self.current()
            if type_tok.type in ("INT", "FLOAT", "BOOL", "STRING"):
                var_type = type_tok.value
                self.advance()
                self.symbols[name] = var_type  # register declared variable
            else:
                raise MiniLangSyntaxError(f"Invalid type: {type_tok.value}")

            # Pure declaration: z:int;
            if self.current() and self.current().type == "SEMICOLON":
                self.advance()
                return VarDecl(name, var_type)

        # Case 2: assignment (must be declared)
        if self.current() and self.current().type == "OP" and self.current().value == "=":
            # check if variable exists
            if var_type is None and name not in self.symbols:
                raise MiniLangSyntaxError(
                    f"Variable '{name}' is not declared before assignment",
                    line=name_token.line,
                    column=name_token.column,
                    line_text=self.get_line(name_token.line)
                )

            self.advance()
            value = self.expression()
            self.expect("SEMICOLON")

            # If this is an assignment after declaration, use recorded type
            if var_type is None:
                var_type = self.symbols[name]

            return VarAssign(name, var_type, value)

        # Case 3: function call
        elif self.current() and self.current().type == "LPAREN":
            args = self.arguments()
            self.expect("SEMICOLON")
            return FunctionCall(name, args)

        # Case 4: declaration only
        elif var_type is not None:
            self.expect("SEMICOLON")
            return VarDecl(name, var_type)

        else:
            raise MiniLangSyntaxError(f"Unexpected token after identifier '{name}'")


    
    
    # ---- Expressions ----

    def expression(self) -> "Expr":
        return self.comparison()
    
    def comparison(self) -> "Expr":
        left = self.term_expr()
        while self.current() and self.current().value in {"<", ">", "<=", ">=", "==", "!="}:
            op = self.current().value
            self.advance()
            right = self.term_expr()
            left = BinaryOp(op, left, right)
        return left
    

    def term_expr(self) -> "Expr":
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
        
        elif tok.type == "STRING":
            self.advance()
            return StringLiteral(tok.value)

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
fn main(): int {
    x: int = 5;
    y: int = 10;
    z: int;
    z = x + y;
    print(z);  
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
