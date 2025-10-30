import sys
from llvmlite import binding
import ctypes
from lexer import lex
from parser import Parser
from semantic_analyzer import SemanticAnalyzer
from codegen import CodeGenerator

def run_code(source_code: str, emit_llvm=False):
    from llvmlite import binding
    import ctypes
    from lexer import lex
    from parser import Parser
    from semantic_analyzer import SemanticAnalyzer
    from codegen import CodeGenerator

    # === Compilation Pipeline ===
    tokens = lex(source_code)
    parser = Parser(tokens)
    ast = parser.parse()

    # Semantic Analysis
    SemanticAnalyzer(ast).analyze()

    # Codegen
    cg = CodeGenerator()
    module = cg.generate(ast)
    llvm_ir = str(module)

    if emit_llvm:
        with open("out.ll", "w") as f:
            f.write(llvm_ir)
        print("✅ LLVM IR written to out.ll")
        return

    # === Initialize LLVM for JIT ===
    binding.initialize_native_target()
    binding.initialize_native_asmprinter()

    # === JIT Execution ===
    llvm_mod = binding.parse_assembly(llvm_ir)
    llvm_mod.verify()

    target = binding.Target.from_default_triple()
    target_machine = target.create_target_machine()
    engine = binding.create_mcjit_compiler(binding.parse_assembly(""), target_machine)
    engine.add_module(llvm_mod)
    engine.finalize_object()

    func_ptr = engine.get_function_address("main")
    cfunc = ctypes.CFUNCTYPE(ctypes.c_int)(func_ptr)
    result = cfunc()

    print(f"\n=== Program exited with code {result} ===")\
    
    

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python src/main.py <source.mini> [--emit-llvm]")
        sys.exit(1)

    filename = sys.argv[1]
    emit_llvm = "--emit-llvm" in sys.argv

    with open(filename, "r") as f:
        code = f.read()

    run_code(code, emit_llvm)
