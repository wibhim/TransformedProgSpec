method Max(a: int, b: int) returns (c: int)
  // What postcondition should go here, so that the function operates as expected?
  // Hint: there are many ways to write this.
    ensures c >= a && c >= b            // returned max is greater than or equal to both inputs
    ensures c == a || c == b            // returned max is equal to one of the inputs
{
  // fill in the code here
      if a >= b {
        c := a;
    }
    else {
        c := b;
    }
    return c;
}
method Testing()
{
  var result1 := Max(5, 10);
  assert result1 == 10;

  var result2 := Max(-3, -7);
  assert result2 == -3;

  var result3 := Max(42, 42);
  assert result3 == 42;

  var result4 := Max(0, -1);
  assert result4 == 0;
}


method Abs(x: int) returns (y: int)
  // Add a precondition here.
  ensures 0 <= y
  ensures 0 <= x ==> y == x
  ensures x < 0 ==> y == -x
{
  // Simplify the body to just one return statement
  if x < 0 {
    return -x;
  } else {
    return x;
  }
}

method Abs1(x: int) returns (y: int)
  // Add a precondition here so that the method verifies.
  // Don't change the postconditions.
  requires x == -1
  ensures 0 <= y
  ensures 0 <= x ==> y == x
  ensures x < 0 ==> y == -x
{
  y:= x + 2;
}
method Abs2(x: int) returns (y: int)
  // Add a precondition here so that the method verifies.
  // Don't change the postconditions.
  requires false
  ensures 0 <= y
  ensures 0 <= x ==> y == x
  ensures x < 0 ==> y == -x
{
  y:= x + 1;
}

method m(n: nat)
{
  var i: int := 0;
  while i < n
    invariant 0 <= i <= n
  {
    i := i + 1;
  }
  assert i == n;
}

function fib(n: nat): nat
{
  if n == 0 then 0
  else if n == 1 then 1
  else fib(n - 1) + fib(n - 2)
}
method ComputeFib(n: nat) returns (b: nat)
  ensures b == fib(n)
{
  if n == 0 { return 0; }
  var i := 1;
  var a := 0;
  b := 1;
  while i < n
    invariant 0 < i <= n
    invariant a == fib(i - 1)
    invariant b == fib(i)
  {
    a, b := b, a + b;
    i := i + 1;
  }
}

method mT()
{
  var i, n := 0, 20;
  while i < n
    invariant 0 <= i <= n
    decreases n - i
  {
    i := i + 1;
  }
}