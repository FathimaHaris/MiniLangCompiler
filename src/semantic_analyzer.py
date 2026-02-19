from parser import (
    Parser, lex,
    Program, Function, VarAssign, ReturnStmt, PrintStmt,
    Number,VarDecl, Var, BinaryOp, StringLiteral, IfStmt, WhileStmt
)

class SemanticError(Exception):
    pass


class SymbolTable:
    """Keeps track of variable declarations and types."""
    def __init__(self):
        self.symbols = {}

    def declare(self, name: str, type_: str):
        if name in self.symbols:
            raise SemanticError(f"Variable '{name}' already declared.")
        self.symbols[name] = type_

    def assign(self, name: str, type_: str):
        if name not in self.symbols:
            raise SemanticError(f"Variable '{name}' not declared.")
        if self.symbols[name] != type_:
            raise SemanticError(f"Type mismatch in assignment to '{name}'. "
                                f"Expected '{self.symbols[name]}', got '{type_}'")

    def lookup(self, name: str):
        if name not in self.symbols:
            raise SemanticError(f"Variable '{name}' not declared.")
        return self.symbols[name]


class SemanticAnalyzer:
    def __init__(self, ast: Program):
        self.ast = ast
        self.global_scope = SymbolTable()
        self.current_function = None

    def analyze(self):
        for func in self.ast.functions:
            self.visit_function(func)

    def visit_function(self, func: Function):
        print(f"Analyzing function: {func.name}")
        self.current_function = func
        local_scope = SymbolTable()

        # Declare parameters
        for param in func.params:
            local_scope.declare(param.name, param.type)

        for stmt in func.body:
            self.visit_stmt(stmt, local_scope, func.return_type)

    def visit_stmt(self, stmt, scope: SymbolTable, expected_return: str):
        from parser import VarAssign, ReturnStmt, PrintStmt, IfStmt, WhileStmt

        if isinstance(stmt, VarAssign):
            val_type = self.visit_expr(stmt.value, scope)

            if stmt.type_:
                if stmt.name not in scope.symbols:
                    # First declaration with optional initialization
                    scope.declare(stmt.name, stmt.type_)
                else:
                    # Already declared → just an assignment
                    scope.assign(stmt.name, val_type)
            else:
                # No type specified → must already exist
                if stmt.name not in scope.symbols:
                    raise SemanticError(f"Variable '{stmt.name}' not declared")
                scope.assign(stmt.name, val_type)

        elif isinstance(stmt, VarDecl):
            scope.declare(stmt.name, stmt.type_)


        elif isinstance(stmt, ReturnStmt):
            if stmt.value:
                val_type = self.visit_expr(stmt.value, scope)
                if expected_return != "void" and val_type != expected_return:
                    raise SemanticError(f"Return type mismatch: expected '{expected_return}', got '{val_type}'")
            else:
                if expected_return != "void":
                    raise SemanticError(f"Return statement missing value (expected {expected_return})")

        elif isinstance(stmt, PrintStmt):
            self.visit_expr(stmt.value, scope)

        elif isinstance(stmt, IfStmt):
            cond_type = self.visit_expr(stmt.condition, scope)
            if cond_type != "bool" and cond_type != "int":
                raise SemanticError("Condition in if-statement must be bool or int")

            for s in stmt.then_branch:
                self.visit_stmt(s, scope, expected_return)

            if stmt.else_branch:
                for s in stmt.else_branch:
                    self.visit_stmt(s, scope, expected_return)

        elif isinstance(stmt, WhileStmt):
            cond_type = self.visit_expr(stmt.condition, scope)
            if cond_type != "bool" and cond_type != "int":
                raise SemanticError("Condition in while-statement must be bool or int")

            for s in stmt.body:
                self.visit_stmt(s, scope, expected_return)

        else:
            raise SemanticError(f"Unknown statement type: {stmt}")

    def visit_expr(self, expr, scope: SymbolTable) -> str:
        if isinstance(expr, Number):
            return "int"

        elif isinstance(expr, StringLiteral):
            return "string"

        elif isinstance(expr, Var):
            return scope.lookup(expr.name)

        elif isinstance(expr, BinaryOp):
            left_type = self.visit_expr(expr.left, scope)
            right_type = self.visit_expr(expr.right, scope)

            if expr.op in {"+", "-", "*", "/"}:
                if left_type != "int" or right_type != "int":
                    raise SemanticError(f"Arithmetic operation requires int operands, got {left_type} and {right_type}")
                return "int"

            elif expr.op in {"<", ">", "<=", ">=", "==", "!="}:
                if left_type != right_type:
                    raise SemanticError(f"Comparison operands must match, got {left_type} and {right_type}")
                return "bool"

            else:
                raise SemanticError(f"Unsupported operator: {expr.op}")

        else:
            raise SemanticError(f"Unknown expression type: {expr}")


if __name__ == "__main__":
    code = """
fn main(): int {
    x = 1;
    y: string = "hi";
    while (x < 5 ) {
        print(x);
        x = x + 1;
    }
    if (x > 3) {
        print("Greater");
    } else {
        print("Smaller");
    }
    return 0;
}
    """

    tokens = lex(code)
    parser = Parser(tokens, code)
    ast = parser.parse()

    try:
        SemanticAnalyzer(ast).analyze()
        print("✅ Semantic analysis passed!")
    except SemanticError as e:
        print(f"Semantic Error: {e}")
