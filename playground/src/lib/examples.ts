import type { ExampleProgram } from '@/types/sigil'

export const EXAMPLES: ExampleProgram[] = [
  {
    id: 'hello',
    name: 'Hello Sigil',
    description: 'Constants, rules, and main block',
    source: `-- Hello Sigil!
-- The simplest Sigil program

define greeting as "Hello from Sigil!"
define answer as 42

rule hello_world:
  when true
  then print(greeting)
  explain "A simple greeting rule"

main:
  given x as answer * 2
  print("The answer doubled is:")
  print(x)
`,
    input: '{}',
  },
  {
    id: 'calculator',
    name: 'Calculator',
    description: 'Compute functions with type annotations',
    source: `-- Calculator: compute functions with types

compute add from a: Number, b: Number returns Number:
  return a + b

compute multiply from a: Number, b: Number returns Number:
  return a * b

compute factorial from n: Number returns Number:
  if n is 0
    return 1
  else
    return n * factorial(n - 1)

main:
  given sum as add(10, 25)
  given product as multiply(6, 7)
  given fact5 as factorial(5)
  print("10 + 25 =")
  print(sum)
  print("6 * 7 =")
  print(product)
  print("5! =")
  print(fact5)
`,
    input: '{}',
  },
  {
    id: 'temperature',
    name: 'Temperature Monitor',
    description: 'Rules with input data, priorities, and symbols',
    source: `-- Temperature Monitor
-- Rules with priorities and input data

define CRITICAL as 150
define WARNING as 100
define SAFE as 80

given temperature from input

rule critical_alert with priority 100:
  when temperature exceeds CRITICAL
  then print("CRITICAL: Temperature exceeds safe limits!")
  explain "Temperature critically high"

rule high_alert with priority 50:
  when temperature exceeds WARNING
  then print("WARNING: Temperature is high")
  explain "Temperature above warning threshold"

rule normal with priority 1:
  when temperature is below SAFE
  then print("OK: Temperature is normal")
  explain "Temperature in safe range"

main:
  print("Temperature reading:")
  print(temperature)
`,
    input: '{"temperature": 160}',
  },
  {
    id: 'pattern-matching',
    name: 'Pattern Matching',
    description: 'Match expressions with symbols and wildcards',
    source: `-- Pattern Matching
-- Match expressions with symbols

compute severity_label from level: Symbol returns Text:
  return match level:
    :critical -> "CRITICAL - Immediate action"
    :high -> "HIGH - Action within 1 hour"
    :medium -> "MEDIUM - Action within 24 hours"
    :low -> "LOW - No immediate action"
    _ -> "UNKNOWN"

compute priority_score from level: Symbol returns Number:
  return match level:
    :critical -> 100
    :high -> 75
    :medium -> 50
    :low -> 25
    _ -> 0

main:
  given level as :high
  given label as severity_label(level)
  given score as priority_score(level)
  print(label)
  print(score)
`,
    input: '{}',
  },
  {
    id: 'control-flow',
    name: 'Control Flow',
    description: 'If/else, for each, list operations',
    source: `-- Control Flow
-- If/else and for-each loops

compute classify from n: Number returns Text:
  if n exceeds 100
    return "large"
  else
    if n exceeds 10
      return "medium"
    else
      return "small"

main:
  given items as [5, 42, 150, 8, 99]
  for each item in items:
    given label as classify(item)
    print(item)
    print(label)
`,
    input: '{}',
  },
  {
    id: 'higher-order',
    name: 'Higher-Order Functions',
    description: 'Functions as values, pipelines',
    source: `-- Higher-Order Functions
-- Lambdas and pipelines

compute apply from func, value: Number returns Number:
  return func(value)

main:
  given double as (x) => x * 2
  given increment as (x) => x + 1

  given a as apply(double, 21)
  given b as apply(increment, a)
  print("double(21) =")
  print(a)
  print("increment(42) =")
  print(b)

  -- Pipeline
  given result as 10 |> double |> increment |> double
  print("10 |> double |> increment |> double =")
  print(result)
`,
    input: '{}',
  },
  {
    id: 'rule-engine',
    name: 'Rule Engine',
    description: 'Multi-rule forward chaining with input',
    source: `-- Loan Eligibility Engine
-- Multi-rule forward chaining

given credit_score from input
given income from input
given loan_amount from input

define MIN_CREDIT as 650
define MIN_INCOME_RATIO as 3

rule check_credit with priority 10:
  when credit_score exceeds MIN_CREDIT
  then print("Credit score: PASS")
  explain "Credit score meets minimum"

rule bad_credit with priority 10:
  when credit_score is below MIN_CREDIT
  then print("Credit score: FAIL")
  explain "Credit score below minimum"

rule check_income with priority 5:
  when income * MIN_INCOME_RATIO exceeds loan_amount
  then print("Income ratio: PASS")
  explain "Income sufficient for loan"

rule low_income with priority 5:
  when loan_amount exceeds income * MIN_INCOME_RATIO
  then print("Income ratio: FAIL")
  explain "Income insufficient for loan amount"

main:
  print("=== Loan Eligibility Report ===")
  print("Credit Score:")
  print(credit_score)
  print("Income:")
  print(income)
  print("Loan Amount:")
  print(loan_amount)
`,
    input: '{"credit_score": 720, "income": 75000, "loan_amount": 200000}',
  },
]
