; ModuleID = "MiniLangModule"
target triple = "unknown-unknown-unknown"
target datalayout = ""

define i32 @"main"()
{
entry:
  %"x" = alloca i32
  store i32 5, i32* %"x"
  %"x.1" = load i32, i32* %"x"
  %".3" = icmp sgt i32 %"x.1", 3
  %".4" = zext i1 %".3" to i32
  %".5" = icmp ne i32 %".4", 0
  br i1 %".5", label %"then_0", label %"else_0"
then_0:
  %".7" = bitcast [8 x i8]* @"str_1" to i8*
  %".8" = bitcast [4 x i8]* @"fstr_2" to i8*
  %".9" = call i32 (i8*, ...) @"printf"(i8* %".8", i8* %".7")
  br label %"ifcont_0"
else_0:
  %".11" = bitcast [8 x i8]* @"str_3" to i8*
  %".12" = bitcast [4 x i8]* @"fstr_4" to i8*
@"str_1" = internal constant [8 x i8] c"Greater\00"
declare i32 @"printf"(i8* %".1", ...)

@"fstr_2" = internal constant [4 x i8] c"%s\0a\00"
@"str_3" = internal constant [8 x i8] c"Smaller\00"
@"fstr_4" = internal constant [4 x i8] c"%s\0a\00"