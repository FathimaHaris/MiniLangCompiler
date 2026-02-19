# src/jit_runner_optimized.py
from llvmlite import binding as llvm
import ctypes
from codegen import CodeGenerator
from parser import Parser
from lexer import lex

code = """
fn main(): int {
    x :int= 5;
    y:int = x + 10;
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
print("\n=== Original LLVM IR ===\n")
print(llvm_ir)

# ------------------------
# Initialize LLVM (modern llvmlite)
# ------------------------
llvm.initialize_native_target()
llvm.initialize_native_asmprinter()

# ------------------------
# Parse IR into binding module
# ------------------------
mod = llvm.parse_assembly(llvm_ir)
mod.verify()

# ------------------------
# Create TargetMachine (needed by PassBuilder)
# ------------------------
target = llvm.Target.from_default_triple()
target_machine = target.create_target_machine()

# ------------------------
# NEW Pass Manager API (replaces create_pass_manager_builder)
# ------------------------
# Rough equivalent of -O2:
pto = llvm.create_pipeline_tuning_options(speed_level=2, size_level=0)

# Optional knobs (you can enable/disable as you like)
pto.loop_vectorization = True
pto.slp_vectorization = True
pto.loop_unrolling = True

pass_builder = llvm.create_pass_builder(target_machine, pto)

# Get a populated module pass manager and run it
mpm = pass_builder.getModulePassManager()
mpm.run(mod, pass_builder)

optimized_ir = str(mod)
print("\n=== Optimized LLVM IR ===\n")
print(optimized_ir)

# ------------------------
# Create JIT execution engine
# ------------------------
backing_mod = llvm.parse_assembly("")
engine = llvm.create_mcjit_compiler(backing_mod, target_machine)

engine.add_module(mod)
engine.finalize_object()

engine.run_static_constructors()

# ------------------------
# Run main()
# ------------------------
func_ptr = engine.get_function_address("main")
cfunc = ctypes.CFUNCTYPE(ctypes.c_int)(func_ptr)

print("\n=== JIT Execution ===")
result = cfunc()
print(f"\nProgram returned: {result}")
