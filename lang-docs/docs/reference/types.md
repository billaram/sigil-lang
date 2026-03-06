# Type System

Sigil uses a **gradual type system** — types are optional for rapid prototyping but encouraged for production rules. Type annotations are required at module boundaries and in neural declarations.

---

## Base types

| Type | Description | Examples |
|------|-------------|---------|
| `Number` | Integer or float | `42`, `3.14`, `100 degrees` |
| `Text` | UTF-8 string | `"hello"`, `"temp is {t}"` |
| `Boolean` | True or false | `true`, `false` |
| `Symbol` | Interned atom | `:active`, `:critical` |
| `None` | Absence of value | `none` |

---

## Composite types

### Lists

Homogeneous ordered collections:

```sigil
list of Number          -- [1, 2, 3]
list of Text            -- ["a", "b", "c"]
list of Symbol          -- [:active, :inactive]
```

### Records

Structural typed collections of named fields:

```sigil
type Person is record:
  name: Text
  age: Number
  status: Symbol
```

Records use **structural subtyping** — a record with more fields is a subtype of one with fewer:

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
greet({name: "Alice"})              -- HasName
greet({name: "Bob", age: 30})       -- Person (subtype)
```

### Sum types (enums)

```sigil
type Severity is one of:
  low
  medium
  high
  critical

type Decision is one of:
  approved with rate: Number
  denied with reasons: list of Text
  review with notes: Text
```

### Option type

Explicit nullability:

```sigil
Option[Number]          -- Number or none
Option[Text]            -- Text or none
```

---

## Unit types

Sigil has first-class dimensional analysis:

```sigil
type Temperature is Number with unit degrees
type Duration is Number with unit seconds
type Money is Number with unit dollars
type Ratio is Number with unit percent
```

Usage:

```sigil
define boiling_point as 100 degrees
define timeout as 30 seconds
define price as 49.99 dollars
define threshold as 85 percent
```

### Unit checking

```sigil
-- OK: same units
when temperature exceeds 100 degrees

-- ERROR: unit mismatch (caught at type-check time)
when temperature exceeds 30 seconds
-- Error: Cannot compare Temperature (degrees) with Duration (seconds)
```

### Built-in conversions

| Category | Conversions |
|----------|------------|
| Temperature | celsius, fahrenheit, kelvin |
| Duration | seconds, milliseconds, minutes, hours |
| Ratio | percent (50 percent = 0.5 fraction) |

---

## Constrained types

Types with runtime constraints, checked at boundaries:

```sigil
type Percentage is Number between 0 and 100
type PositiveNumber is Number above 0
type NonEmpty[T] is list of T with count above 0
type Email is Text matching "[^@]+@[^@]+\\.[^@]+"
```

Violations are caught at assignment or function boundaries:

```
Error: 105 is not a valid Percentage (max 100)
```

---

## Domain types

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
```

---

## Type inference

Sigil infers types from context when not explicitly annotated:

| Source | Inference |
|--------|-----------|
| Literals | `42` -> Number, `"hello"` -> Text, `:active` -> Symbol |
| Operators | `x > 100` -> x must be Number |
| Function calls | Return type from declaration |
| Record access | Field type from record definition |

```sigil
-- Inferred: temperature is Number (from comparison with literal)
rule check:
  when temperature exceeds 100
  then alert

-- Explicit: required at module boundaries
compute risk_score from applicant: Applicant returns Number:
  ...
```

!!! warning "Neural boundary"
    Type inference does not cross the neural boundary. Neural declarations must explicitly declare their return type and fallback type.

---

## Type compatibility

| Operation | Left | Right | Result |
|-----------|------|-------|--------|
| `exceeds`, `is below`, `is between` | Number | Number | Boolean |
| `is`, `equals` | Any T | Same T | Boolean |
| `in`, `contains` | T, List[T] | — | Boolean |
| `and`, `or` | Boolean | Boolean | Boolean |
| `not` | Boolean | — | Boolean |
| `+`, `-`, `*`, `/` | Number | Number | Number |
| `starts with`, `ends with`, `contains` | Text | Text | Boolean |
| `matches pattern` | Text | Text (regex) | Boolean |

---

## Type at the neural/symbolic boundary

The most important type-checking happens where neural meets symbolic:

```sigil
-- Neural declaration MUST specify return type
neural classify from text: Text:
  model "intent-v2"
  returns Symbol
  confidence_threshold 0.85
  fallback to :unknown

-- When neural result enters symbolic rules, types are checked
rule handle_intent:
  given intent from classify(user_text)
  when intent is :purchase          -- Symbol = Symbol: OK
  then process_purchase
```

### Neural type guarantees

| Property | Guarantee |
|----------|-----------|
| Return type | Declared and enforced |
| Confidence | Always attached (0.0-1.0) |
| Fallback | Type-compatible with return type |
| Null safety | Fallback prevents null returns |

---

## Error messages

Type errors include source location, context, and suggestions:

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
```
