# MiniLang Language Specification

MiniLang is a small, statically typed, C-like language designed to learn compiler design and LLVM code generation.

## Keywords
`fn`, `return`, `if`, `else`, `while`, `int`, `float`, `print`

## Types
- int (32-bit)
- float (64-bit)

## Syntax Example
```plaintext
fn factorial(n:int): int {
    result = 1;
    while (n > 1) {
        result = result * n;
        n = n - 1;
    }
    return result;
}

fn main(): int {
    x = 5;
    y = factorial(x);
    print(y);
    return 0;
}
```

## Grammer

program       → (function)* EOF ;
function      → "fn" IDENT "(" parameters? ")" ":" type block ;
parameters    → parameter ("," parameter)* ;
parameter     → IDENT ":" type ;
type          → "int" | "float" ;
block         → "{" statement* "}" ;
statement     → expr_stmt | return_stmt | if_stmt | while_stmt | block ;
expr_stmt     → expression ";" ;
return_stmt   → "return" expression ";" ;
if_stmt       → "if" "(" expression ")" block ("else" block)? ;
while_stmt    → "while" "(" expression ")" block ;
expression    → assignment ;
assignment    → IDENT "=" assignment | equality ;
equality      → comparison (("==" | "!=") comparison)* ;
comparison    → term ((">" | "<" | ">=" | "<=") term)* ;
term          → factor (("+" | "-") factor)* ;
factor        → unary (("*" | "/") unary)* ;
unary         → ("+" | "-") unary | primary ;
primary       → NUMBER | IDENT | IDENT "(" arguments? ")" | "(" expression ")" ;
arguments     → expression ("," expression)* ;
