# src/codegen.py
from llvmlite import ir, binding
from parser import Parser, lex
from semantic_analyzer import SemanticAnalyzer

# === Code Generator ===

class CodeGenerator:
    def __init__(self):
        self.module = ir.Module(name="MiniLangModule")
        self.builder = None
        self.func = None
        self.symbols = {}

    def generate(self, ast):
        for func in ast.functions:
            self.codegen_function(func)
        return self.module

    def codegen_function(self, func):
        func_type = ir.FunctionType(ir.IntType(32), [])
        llvm_func = ir.Function(self.module, func_type, name=func.name)
        block = llvm_func.append_basic_block(name="entry")
        self.builder = ir.IRBuilder(block)
        self.func = llvm_func
        self.symbols = {}

        for stmt in func.body:
           self.codegen_stmt(stmt)

        # Only emit default return if block isn't terminated already
        if not self.builder.block.is_terminated:
             self.builder.ret(ir.Constant(ir.IntType(32), 0))

        return llvm_func

    def codegen_stmt(self, stmt):
        from parser import VarAssign, ReturnStmt, PrintStmt
        if isinstance(stmt, VarAssign):
            val = self.codegen_expr(stmt.value)
            ptr = self.builder.alloca(ir.IntType(32), name=stmt.name)
            self.builder.store(val, ptr)
            self.symbols[stmt.name] = ptr

        elif isinstance(stmt, ReturnStmt):
            val = self.codegen_expr(stmt.value)
            self.builder.ret(val)

        elif isinstance(stmt, PrintStmt):
            val = self.codegen_expr(stmt.value)

            # Declare printf if not already
            printf = self.module.globals.get("printf")
            if printf is None:
                voidptr_ty = ir.IntType(8).as_pointer()
                printf_ty = ir.FunctionType(ir.IntType(32), [voidptr_ty], var_arg=True)
                printf = ir.Function(self.module, printf_ty, name="printf")

            # Create format string "%d\n"
            fmt = "%d\n\0"
            c_fmt = ir.Constant(ir.ArrayType(ir.IntType(8), len(fmt)),
                                bytearray(fmt.encode("utf8")))
            global_fmt = ir.GlobalVariable(self.module, c_fmt.type, name="fstr")
            global_fmt.linkage = 'internal'
            global_fmt.global_constant = True
            global_fmt.initializer = c_fmt

            fmt_ptr = self.builder.bitcast(global_fmt, ir.IntType(8).as_pointer())

            # Call printf(fmt, value)
            self.builder.call(printf, [fmt_ptr, val])



    def codegen_expr(self, expr):
        from parser import Number, Var, BinaryOp
        if isinstance(expr, Number):
            return ir.Constant(ir.IntType(32), int(expr.value))
        elif isinstance(expr, Var):
            ptr = self.symbols.get(expr.name)
            if not ptr:
                raise NameError(f"Undefined variable {expr.name}")
            return self.builder.load(ptr, expr.name)
        elif isinstance(expr, BinaryOp):
            left = self.codegen_expr(expr.left)
            right = self.codegen_expr(expr.right)
            if expr.op == '+':
                return self.builder.add(left, right)
            elif expr.op == '-':
                return self.builder.sub(left, right)
            elif expr.op == '*':
                return self.builder.mul(left, right)
            elif expr.op == '/':
                return self.builder.sdiv(left, right)
        else:
            raise NotImplementedError(f"Unsupported expression: {expr}")


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

    # Run semantic check
    SemanticAnalyzer(ast).analyze()

    # Generate LLVM IR
    cg = CodeGenerator()
    module = cg.generate(ast)
    print("\n=== LLVM IR ===")
    print(module)
