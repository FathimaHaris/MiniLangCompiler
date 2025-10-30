; ModuleID = "MiniLangModule"
target triple = "unknown-unknown-unknown"
target datalayout = ""

define i32 @"main"()
{
entry:
  %"x" = alloca i32
  store i32 5, i32* %"x"
  %"x.1" = load i32, i32* %"x"
  %".3" = add i32 %"x.1", 10
  %"y" = alloca i32
  store i32 %".3", i32* %"y"
  %"y.1" = load i32, i32* %"y"
  %".5" = bitcast [4 x i8]* @"fstr" to i8*
  %".6" = call i32 (i8*, ...) @"printf"(i8* %".5", i32 %"y.1")
  ret i32 42
}

declare i32 @"printf"(i8* %".1", ...)

@"fstr" = internal constant [4 x i8] c"%d\0a\00"