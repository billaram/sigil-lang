# Sigil: Type System Design

## Philosophy

Sigil uses a **gradual type system** — types are optional for rapid prototyping but encouraged for production rules. The type system serves two primary goals:

1. **Catch rule errors early**: Unit mismatches, incomplete conditions, type violations
2. **Document the neural/symbolic boundary**: Neural returns must declare types; symbolic rules inherit them

## Base Types

```
Number      Unified numeric type (int or float, determined by context)
Text        UTF-8 string
Boolean     true / false
Symbol      Interned atom (:active, :critical, :approved)
None        Absence of value
```

## Composite Types

```sigil
-- Lists (homogeneous)
list of Number          -- [1, 2, 3]
list of Text            -- ["a", "b", "c"]
list of Symbol          -- [:active, :inactive]

-- Records (structural typing)
record:
  name: Text
  age: Number
  status: Symbol

-- Named record types
type Person is record:
  name: Text
  age: Number

-- Option (explicit nullability)
Option[Number]          -- Number or none
Option[Text]            -- Text or none

-- Sum types (tagged unions)
type Result is one of:
  success with value: Number
  failure with reason: Text
  pending
```

## Unit Types

Sigil has first-class dimensional analysis:

```sigil
type Temperature is Number with unit degrees
type Duration is Number with unit seconds
type Money is Number with unit dollars
type Ratio is Number with unit percent

-- Usage
define boiling_point as 100 degrees
define timeout as 30 seconds
define price as 49.99 dollars
define threshold as 85 percent
```

### Unit Checking

```sigil
-- OK: same units
when temperature exceeds 100 degrees   -- Number(degrees) > Number(degrees)

-- ERROR: unit mismatch (caught at type-check time)
when temperature exceeds 30 seconds
--                       ^^^^^^^^^^
-- Error: Cannot compare Temperature (degrees) with Duration (seconds)

-- OK: explicit conversion
when convert(temperature, :fahrenheit) exceeds 212 degrees
```

### Built-in Unit Conversions

```
Temperature: celsius <-> fahrenheit <-> kelvin
Duration:    seconds <-> milliseconds <-> minutes <-> hours
Money:       (via exchange rate config, not built-in conversion)
Ratio:       percent <-> fraction (50 percent = 0.5)
```

## Domain Types

Types specific to neuro-symbolic programming:

```sigil
-- Confidence: result of neural operations (0.0 to 1.0)
type Confidence is Number between 0.0 and 1.0

-- Trace: execution record
type Trace is record:
  rule_name: Text
  timestamp: Number
  steps: list of TraceStep
  decision: Symbol
  duration_ms: Number

type TraceStep is record:
  expression: Text
  result: Boolean
  bindings: record  -- variable values at this step

-- Rule: first-class rule value
type Rule is record:
  name: Text
  priority: Number
  conditions: list of Expression
  actions: list of Action
```

## Type Inference

Sigil infers types from context when not explicitly annotated:

```sigil
-- Inferred: temperature is Number (from comparison with Number literal)
rule check:
  when temperature exceeds 100
  then alert

-- Inferred: items is list of Number (from math.mean usage)
compute average from items:
  return math.mean(items)

-- Explicit: required at module boundaries and neural declarations
compute risk_score from applicant: Applicant returns Number:
  ...

neural classify from text: Text:
  returns Symbol
  ...
```

### Inference Rules

1. **Literals**: Direct type from syntax (`42` → Number, `"hello"` → Text, `:active` → Symbol)
2. **Operators**: Inferred from operands (`x > 100` → x must be Number)
3. **Function calls**: Return type from declaration or standard library
4. **Record access**: Field type from record type definition
5. **Neural returns**: Must be explicitly declared (no inference across neural boundary)

## Structural Typing

Records use structural subtyping — a record with more fields is a subtype of one with fewer:

```sigil
type HasName is record:
  name: Text

type Person is record:
  name: Text
  age: Number

-- Person is a subtype of HasName (has all required fields)
compute greet from entity: HasName returns Text:
  return "Hello, {entity.name}"

-- Both work:
greet({name: "Alice"})                  -- HasName
greet({name: "Bob", age: 30})           -- Person (subtype of HasName)
```

## Constraint Types

Types with runtime constraints, checked at boundaries:

```sigil
type Percentage is Number between 0 and 100
type PositiveNumber is Number above 0
type NonEmpty[T] is list of T with count above 0
type Email is Text matching "[^@]+@[^@]+\\.[^@]+"

-- Constraint checked at assignment/function boundary
define score as 105          -- Error: 105 is not a valid Percentage (max 100)
define ratio as -5           -- Error: -5 is not a valid PositiveNumber
```

## Type at the Neural/Symbolic Boundary

The most important type-checking happens at the boundary between neural and symbolic:

```sigil
-- Neural declaration MUST specify return type
neural classify from text: Text:
  model "intent-v2"
  returns Symbol                    -- explicit return type
  confidence_threshold 0.85
  fallback to :unknown

-- When neural result enters symbolic rules, types are checked
rule handle_intent:
  given intent from classify(user_text)   -- intent: Symbol (from neural decl)
  when intent is :purchase                -- Symbol = Symbol: OK
  and intent exceeds 100                  -- ERROR: Symbol has no 'exceeds' operator
  then process_purchase
```

### Neural Type Guarantees

| Property | Guarantee |
|----------|-----------|
| Return type | Declared and enforced |
| Confidence | Always attached (0.0-1.0) |
| Fallback | Type-compatible with return type |
| Null safety | Fallback prevents null returns |

## Type Compatibility Table

| Operation | Left Type | Right Type | Result |
|-----------|-----------|------------|--------|
| `exceeds`, `is below`, `is between` | Number | Number | Boolean |
| `is`, `equals` | Any T | Same T | Boolean |
| `in`, `contains` | T, List[T] | -- | Boolean |
| `and`, `or` | Boolean | Boolean | Boolean |
| `not` | Boolean | -- | Boolean |
| `+`, `-`, `*`, `/` | Number | Number | Number |
| `starts with`, `ends with`, `contains` | Text | Text | Boolean |
| `matches pattern` | Text | Text (regex) | Boolean |

## Error Messages

Type errors are designed to be helpful and domain-aware:

```
Error at line 12, column 8:
  when temperature exceeds "hot"
                           ^^^^^
  Type mismatch in comparison:
    Left side:  temperature (Number, inferred from context)
    Right side: "hot" (Text)
    Operator:   exceeds (requires Number on both sides)

  Suggestions:
    - Use a numeric threshold: when temperature exceeds 100
    - Compare text values with 'is': when temperature_label is "hot"
    - Define a named constant: define HOT_THRESHOLD as 100
```

```
Error at line 5, column 3:
  neural classify from text: Text:
    returns Number
    fallback to "unknown"
                ^^^^^^^^^
  Type mismatch in fallback:
    Neural returns: Number
    Fallback value: "unknown" (Text)

  The fallback must match the return type.
  Suggestion: fallback to 0 (or another Number value)
```
