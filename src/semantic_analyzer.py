# src/semantic_analyzer.py
from parser import Parser, lex, Program, Function, VarAssign, ReturnStmt, PrintStmt, Number, Var, BinaryOp

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
            raise SemanticError(f"Type mismatch in assignment to '{name}'.")

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
        self.current_function = func
        local_scope = SymbolTable()

        # For now, parameters not used — can add later
        print(f"Analyzing function: {func.name}")

        for stmt in func.body:
            self.visit_stmt(stmt, local_scope, func.return_type)

    def visit_stmt(self, stmt, scope: SymbolTable, expected_return: str):
        if isinstance(stmt, VarAssign):
            val_type = self.visit_expr(stmt.value, scope)
            if stmt.name not in scope.symbols:
                scope.declare(stmt.name, val_type)
            else:
                scope.assign(stmt.name, val_type)

        elif isinstance(stmt, ReturnStmt):
            val_type = self.visit_expr(stmt.value, scope)
            if val_type != expected_return:
                raise SemanticError(f"Return type mismatch: expected {expected_return}, got {val_type}")

        elif isinstance(stmt, PrintStmt):
            self.visit_expr(stmt.value, scope)

        else:
            raise SemanticError(f"Unknown statement: {stmt}")

    def visit_expr(self, expr, scope: SymbolTable) -> str:
        if isinstance(expr, Number):
            return "int"
        elif isinstance(expr, Var):
            return scope.lookup(expr.name)
        elif isinstance(expr, BinaryOp):
            left_type = self.visit_expr(expr.left, scope)
            right_type = self.visit_expr(expr.right, scope)
            if left_type != right_type:
                raise SemanticError(f"Type mismatch in binary op: {left_type} vs {right_type}")
            return left_type
        else:
            raise SemanticError(f"Unknown expression: {expr}")


if __name__ == "__main__":
    code = """
fn main(): int {
        
        y = x + 10;
        print(y);
        return 0;
}
    """

    tokens = lex(code)
    parser = Parser(tokens)
    ast = parser.parse()

    # analyzer = SemanticAnalyzer(ast)
    # analyzer.analyze()




    try:
        SemanticAnalyzer(ast).analyze()
    except SemanticError as e:
        print(f"Semantic Error: {e}")
        exit(1)
    
    print("✅ Semantic analysis passed!")