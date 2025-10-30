#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path
from main import run_code

VERSION = "0.1.0"

def main():
    parser = argparse.ArgumentParser(
        prog="minilang",
        description="MiniLang Compiler and JIT Runner"
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # === minilang run <file> ===
    run_parser = subparsers.add_parser("run", help="Run a MiniLang source file")
    run_parser.add_argument("file", type=Path, help="Path to MiniLang source file")

    # === minilang compile <file> ===
    compile_parser = subparsers.add_parser("compile", help="Compile to LLVM IR")
    compile_parser.add_argument("file", type=Path, help="Path to MiniLang source file")
    compile_parser.add_argument("--emit-llvm", action="store_true", help="Emit LLVM IR to out.ll")

    # === minilang version ===
    subparsers.add_parser("version", help="Show compiler version")

    parser.add_argument("--version", action="version", version=f"MiniLang {VERSION}")


    args = parser.parse_args()


    # === Command handling ===
    if args.command == "version":
        print(f"MiniLang Compiler v{VERSION}")
        sys.exit(0)

    elif args.command in ("run", "compile"):
        if not args.file.exists():
            print(f"Error: file '{args.file}' not found.")
            sys.exit(1)

        with open(args.file, "r") as f:
            code = f.read()

        if args.command == "run":
            run_code(code)
        elif args.command == "compile":
            run_code(code, emit_llvm=args.emit_llvm)

if __name__ == "__main__":
    main()
