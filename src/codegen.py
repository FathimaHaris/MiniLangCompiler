# src/codegen.py
from llvmlite import ir, binding
from parser import Parser, lex
from semantic_analyzer import SemanticAnalyzer


class CodeGenerator:
    def __init__(self):
        self.module = ir.Module(name="MiniLangModule")
        self.builder = None
        self.func = None
        self.symbols = {}
        self._str_constants = {}     # cache for string constants
        self._unique_counter = 0     # global unique counter

    # ------------------------------------------------------------
    # Main entry: generate code for all functions in AST
    # ------------------------------------------------------------
    def generate(self, ast):
        for func in ast.functions:
            self.codegen_function(func)
        return self.module

    # ------------------------------------------------------------
    # Function codegen
    # ------------------------------------------------------------
    def codegen_function(self, func):
        func_type = ir.FunctionType(ir.IntType(32), [])
        llvm_func = ir.Function(self.module, func_type, name=func.name)
        block = llvm_func.append_basic_block(name="entry")
        self.builder = ir.IRBuilder(block)
        self.func = llvm_func
        self.symbols = {}

        for stmt in func.body:
            self.codegen_stmt(stmt)

        # Default return 0 if not terminated
        if not self.builder.block.is_terminated:
            self.builder.ret(ir.Constant(ir.IntType(32), 0))

        return llvm_func

    # ------------------------------------------------------------
    # Statement codegen
    # ------------------------------------------------------------
    def codegen_stmt(self, stmt):
        from parser import VarAssign, ReturnStmt, PrintStmt, IfStmt, WhileStmt

        # Variable assignment
        if isinstance(stmt, VarAssign):
         
            if stmt.value is not None:
                val = self.codegen_expr(stmt.value)
            else:
                val = ir.Constant(ir.IntType(32), 0)  # default initialize to 0

            # allocate if not exists
            if stmt.name not in self.symbols:
                ptr = self.builder.alloca(ir.IntType(32), name=stmt.name)
                self.symbols[stmt.name] = ptr
            else:
                ptr = self.symbols[stmt.name]

            self.builder.store(val, ptr)


        # Return statement
        elif isinstance(stmt, ReturnStmt):
            val = self.codegen_expr(stmt.value)
            self.builder.ret(val)

        # Print statement
        elif isinstance(stmt, PrintStmt):
            val = self.codegen_expr(stmt.value)
            self.call_printf(val)

        # If statement
        elif isinstance(stmt, IfStmt):
            cond_val = self.codegen_expr(stmt.condition)
            cond_bool = self.builder.icmp_signed('!=', cond_val, ir.Constant(ir.IntType(32), 0))

            then_block = self.builder.append_basic_block(name=f"then_{self._unique_counter}")
            else_block = self.builder.append_basic_block(name=f"else_{self._unique_counter}")
            merge_block = self.builder.append_basic_block(name=f"ifcont_{self._unique_counter}")
            self._unique_counter += 1

            self.builder.cbranch(cond_bool, then_block, else_block)

            # THEN branch
            self.builder.position_at_start(then_block)
            for s in stmt.then_branch:
                self.codegen_stmt(s)
            if not self.builder.block.is_terminated:
                self.builder.branch(merge_block)

            # ELSE branch
            self.builder.position_at_start(else_block)
            if stmt.else_branch:
                for s in stmt.else_branch:
                    self.codegen_stmt(s)
            if not self.builder.block.is_terminated:
                self.builder.branch(merge_block)

            # Merge block
            self.builder.position_at_start(merge_block)

        # While statement
        elif isinstance(stmt, WhileStmt):
            # Create blocks
            loop_cond_bb = self.builder.append_basic_block(f"loop_cond_{id(stmt)}")
            loop_body_bb = self.builder.append_basic_block(f"loop_body_{id(stmt)}")
            after_loop_bb = self.builder.append_basic_block(f"after_loop_{id(stmt)}")

            # Jump to condition first
            self.builder.branch(loop_cond_bb)

            # Condition block
            self.builder.position_at_start(loop_cond_bb)
            cond_val = self.codegen_expr(stmt.condition)
            zero = ir.Constant(ir.IntType(32), 0)
            cond_bool = self.builder.icmp_signed("!=", cond_val, zero)
            self.builder.cbranch(cond_bool, loop_body_bb, after_loop_bb)

            # Body block
            self.builder.position_at_start(loop_body_bb)
            for s in stmt.body:  # iterate each statement
                self.codegen_stmt(s)
            if not self.builder.block.is_terminated:
                self.builder.branch(loop_cond_bb)

            # After loop
            self.builder.position_at_start(after_loop_bb)

    # ------------------------------------------------------------
    # Expression codegen
    # ------------------------------------------------------------
    def codegen_expr(self, expr):
        from parser import Number, Var, BinaryOp, StringLiteral

        # Integer constant
        if isinstance(expr, Number):
            return ir.Constant(ir.IntType(32), int(expr.value))

        # Variable reference
        elif isinstance(expr, Var):
            ptr = self.symbols.get(expr.name)
            if not ptr:
                raise NameError(f"Undefined variable {expr.name}")
            return self.builder.load(ptr, expr.name)

        # String literal
        elif isinstance(expr, StringLiteral):
            s = expr.value
            if s in self._str_constants:
                global_str = self._str_constants[s]
            else:
                name = f"str_{self._unique_counter}"
                self._unique_counter += 1

                bytes_val = bytearray((s + "\0").encode("utf8"))
                str_const = ir.Constant(ir.ArrayType(ir.IntType(8), len(bytes_val)), bytes_val)
                global_str = ir.GlobalVariable(self.module, str_const.type, name=name)
                global_str.linkage = 'internal'
                global_str.global_constant = True
                global_str.initializer = str_const

                self._str_constants[s] = global_str

            return self.builder.bitcast(global_str, ir.IntType(8).as_pointer())

        # Binary operations
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
            elif expr.op in ['>', '<', '==', '!=', '>=', '<=']:
                cmp_map = {
                    '>': '>',
                    '<': '<',
                    '==': '==',
                    '!=': '!=',
                    '>=': '>=',
                    '<=': '<='
                }
                cmp = self.builder.icmp_signed(cmp_map[expr.op], left, right)
                return self.builder.zext(cmp, ir.IntType(32))

            else:
                raise NotImplementedError(f"Unsupported operator {expr.op}")
        else:
            raise NotImplementedError(f"Unsupported expression: {expr}")

    # ------------------------------------------------------------
    # printf helper
    # ------------------------------------------------------------
    def call_printf(self, val):
        # declare printf if not yet
        printf = self.module.globals.get("printf")
        if printf is None:
            voidptr_ty = ir.IntType(8).as_pointer()
            printf_ty = ir.FunctionType(ir.IntType(32), [voidptr_ty], var_arg=True)
            printf = ir.Function(self.module, printf_ty, name="printf")

        # determine format
        val_ty = val.type
        is_string = getattr(val_ty, "pointee", None) == ir.IntType(8)

        fmt = "%s\n\0" if is_string else "%d\n\0"
        c_fmt = ir.Constant(ir.ArrayType(ir.IntType(8), len(fmt)), bytearray(fmt.encode("utf8")))

        name = f"fstr_{self._unique_counter}"
        self._unique_counter += 1
        global_fmt = ir.GlobalVariable(self.module, c_fmt.type, name=name)
        global_fmt.linkage = 'internal'
        global_fmt.global_constant = True
        global_fmt.initializer = c_fmt

        fmt_ptr = self.builder.bitcast(global_fmt, ir.IntType(8).as_pointer())
        self.builder.call(printf, [fmt_ptr, val])


# ------------------------------------------------------------
# Standalone test
# ------------------------------------------------------------
if __name__ == "__main__":
    code = """
fn main(): int {
   x: int = 0;
    while (x < 5) {
        print(x);
        x = x + 1;
    }
    return 0;
}
    """

    tokens = lex(code)
    parser = Parser(tokens)
    ast = parser.parse()
    SemanticAnalyzer(ast).analyze()

    cg = CodeGenerator()
    module = cg.generate(ast)
    print("\n=== LLVM IR ===")
    print(module)
