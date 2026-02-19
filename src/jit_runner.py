# src/jit_runner.py
from llvmlite import binding
import ctypes
from codegen import CodeGenerator
from parser import Parser
from lexer import lex

# ------------------------
# Sample program
# ------------------------
code = """
fn main(): int {
    x = 5;
    y = x + 10;
    if (y > 10) {
        print("Greater");
    } else {
        print("Smaller");
    }
    while (x < 8) {
        print(x);
        x = x + 1;
    }
    return y;
}
"""

# ------------------------
# Parse & generate LLVM IR
# ------------------------
tokens = lex(code)
parser = Parser(tokens)
ast = parser.parse()

cg = CodeGenerator()
module = cg.generate(ast)

llvm_ir = str(module)
print("\n=== Generated LLVM IR ===\n")
print(llvm_ir)

# ------------------------
# Initialize LLVM
# ------------------------

binding.initialize_native_target()
binding.initialize_native_asmprinter()

# ------------------------
# Create execution engine
# ------------------------
target = binding.Target.from_default_triple()
target_machine = target.create_target_machine()
backing_mod = binding.parse_assembly("")
engine = binding.create_mcjit_compiler(backing_mod, target_machine)

# ------------------------
# Compile LLVM IR
# ------------------------
mod = binding.parse_assembly(llvm_ir)
mod.verify()
engine.add_module(mod)
engine.finalize_object()
engine.run_static_constructors()

# ------------------------
# Get pointer to 'main' and call it
# ------------------------
func_ptr = engine.get_function_address("main")
cfunc = ctypes.CFUNCTYPE(ctypes.c_int)(func_ptr)

# ------------------------
# Run program
# ------------------------
print("\n=== JIT Execution ===")
result = cfunc()
print(f"\nProgram returned: {result}")
