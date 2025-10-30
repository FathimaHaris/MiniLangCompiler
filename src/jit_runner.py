# src/jit_runner.py
from llvmlite import binding
import ctypes
from codegen import CodeGenerator
from parser import Parser
from lexer import lex

# Step 1: Sample program
code = """
fn main(): int {
    x = 5;
    y = x + 10;
    print(y);
    return 42;
}
"""

# Step 2: Parse and generate LLVM IR
tokens = lex(code)
parser = Parser(tokens)
ast = parser.parse()

cg = CodeGenerator()
module = cg.generate(ast)

llvm_ir = str(module)
print("\n=== Generated LLVM IR ===\n")
print(llvm_ir)

# # Step 3: Initialize LLVM
# binding.initialize()
binding.initialize_native_target()
binding.initialize_native_asmprinter()

# Step 4: Create an execution engine
target = binding.Target.from_default_triple()
target_machine = target.create_target_machine()
backing_mod = binding.parse_assembly("")
engine = binding.create_mcjit_compiler(backing_mod, target_machine)

# Step 5: Compile the LLVM IR
mod = binding.parse_assembly(llvm_ir)
mod.verify()
engine.add_module(mod)
engine.finalize_object()

# Step 6: Get pointer to 'main' and call it
func_ptr = engine.get_function_address("main")

# Convert pointer to a Python-callable function
cfunc = ctypes.CFUNCTYPE(ctypes.c_int)(func_ptr)

print("\n=== JIT Execution Result ===")
result = cfunc()
print(f"\nProgram returned: {result}")
