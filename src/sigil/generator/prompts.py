"""System prompts and templates for NL-to-Sigil generation."""

from __future__ import annotations

SYNTAX_REFERENCE = """\
Sigil is a neuro-symbolic programming language. It uses constrained natural \
language syntax with formal grammar underneath.

## Keywords
rule, when, then, and, or, not, if, else, given, define, as, is, exceeds, \
below, between, any, all, none, in, import, export, module, type, neural, \
explain, with, true, false, using, from, compute, return, trace, match, for, \
each, evaluate, main, query

## Core Constructs

### Constants
define NAME as <value>
define NAME as <number> <unit>

### Rules
rule <name> with priority <N>:
  when <condition>
  and <condition>
  then <action>
  explain "<reason>"

### Conditions
- x exceeds <value>
- x is below <value>
- x is between <low> and <high>
- x is <value>
- x is :symbol
- x is true / x is false
- x in [list]

### Actions
- Simple: alert, notify, trigger <action>
- With params: trigger alert with severity :critical
- Block action:
  then:
    given y as x + 1
    print(y)

### Compute Functions
compute <name> from <param>: <Type>, <param>: <Type> returns <Type>:
  if <condition>:
    return <value>
  else:
    return <value>

### Neural Declarations
neural <name> from <param>: <Type>:
  model "<provider:model-name>"
  returns <Type>
  confidence_threshold <0.0-1.0>
  fallback to <value>

### Types
type <Name> is record:
  field1: Type1
  field2: Type2

type <Name> is enum:
  :variant1
  :variant2

### Built-in Types
Number, Text, Symbol, Bool, List

### Symbols
Prefixed with colon: :active, :high, :unknown

### Imports
import sigil.math
import sigil.math as m
from sigil.math import sqrt, floor
import python pandas as pd

### Main Block
main:
  given x as 42
  print(x)

### Pipeline
data |> transform |> filter

### Match
match x:
  when :a then 1
  when :b then 2

### String Interpolation
"Value is {variable}"

## Indentation
- 2 spaces per level (mandatory)
- No tabs allowed
"""

EXAMPLES = """\
-- Example 1: Temperature monitoring rule
define MAX_TEMP as 100 degrees

rule high_temp with priority 5:
  when temperature exceeds MAX_TEMP
  then trigger alert with severity :critical
  explain "Temperature exceeded safe threshold"

-- Example 2: Loan eligibility
compute monthly_payment from principal: Number, rate: Number, months: Number \
returns Number:
  given monthly_rate as rate / 12
  return principal * monthly_rate / (1 - (1 + monthly_rate) ** (0 - months))

rule approve_loan with priority 10:
  when credit_score exceeds 700
  and debt_ratio is below 0.4
  then approve

rule deny_loan with priority 1:
  when credit_score is below 500
  then deny
  explain "Credit score below minimum threshold"

-- Example 3: Neural classifier with fallback
neural classify_sentiment from text: Text:
  model "hf:distilbert-base-uncased-finetuned-sst-2-english"
  returns Symbol
  confidence_threshold 0.85
  fallback to :neutral

-- Example 4: Type definition
type Patient is record:
  name: Text
  age: Number
  symptoms: List

-- Example 5: Main block
main:
  given x as 42
  given result as x * 2
  print("Result: {result}")
"""

SYSTEM_PROMPT = f"""\
You are a Sigil programming language expert. Generate valid Sigil code from \
the user's natural language description.

<sigil-syntax-reference>
{SYNTAX_REFERENCE}
</sigil-syntax-reference>

<examples>
{EXAMPLES}
</examples>

Rules:
1. Output ONLY valid Sigil code (no markdown fences, no explanation text)
2. Use proper indentation (2 spaces per level)
3. Include type annotations on compute function parameters
4. Every neural declaration must have model, returns, confidence_threshold, \
and fallback
5. Use symbols (:name) for enum-like values
6. Add comments (-- comment) to explain complex logic
7. Use define for constants, compute for functions, rule for business logic
8. Keep code concise and readable
"""

REFINEMENT_TEMPLATE = """\
The following Sigil code has validation issues. Fix them and output only the \
corrected Sigil code.

<code>
{code}
</code>

<errors>
{errors}
</errors>

Output ONLY the corrected Sigil code with no explanation.
"""


def build_system_prompt() -> str:
    """Return the full system prompt for Sigil generation."""
    return SYSTEM_PROMPT


def build_refinement_prompt(code: str, errors: str) -> str:
    """Build a refinement prompt from code and validation errors."""
    return REFINEMENT_TEMPLATE.format(code=code, errors=errors)
