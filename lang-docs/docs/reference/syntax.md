# Syntax Reference

Complete reference for Sigil's syntax. For a gentler introduction, see the [Language Tour](../tour/index.md).

---

## Program structure

A Sigil program consists of top-level declarations in any order:

```sigil
module temperature_monitoring    -- optional module declaration

import sigil.math                -- imports

type SensorReading is record:    -- type definitions
  sensor_id: Text
  temperature: Number

define MAX_TEMP as 100           -- constants

rule temp_check:                 -- rules
  when temperature exceeds MAX_TEMP
  then alert

compute average from xs: list of Number returns Number:  -- functions
  return math.mean(xs)

main:                            -- entry point
  given data from input
  evaluate temp_check
```

---

## Lexical elements

### Comments

| Syntax | Description |
|--------|-------------|
| `-- text` | Single-line comment |
| `{- text -}` | Multi-line comment |
| `--- text` | Doc comment (attached to next declaration) |

### Identifiers

Identifiers start with a letter or underscore and contain letters, digits, and underscores. UTF-8 is supported.

```
valid_name
_private
sensor_id_2
```

### Keywords

Sigil has approximately 30 keywords, all common English words:

| Category | Keywords |
|----------|----------|
| Declarations | `rule`, `compute`, `define`, `type`, `neural`, `module`, `main` |
| Conditions | `when`, `then`, `and`, `or`, `not`, `if`, `else` |
| Comparisons | `is`, `exceeds`, `below`, `between`, `equals` |
| Quantifiers | `any`, `all`, `none`, `in`, `at`, `least`, `most` |
| Bindings | `given`, `as`, `from`, `with`, `becomes`, `return` |
| Types | `record`, `one`, `of`, `list` |
| Modifiers | `priority`, `explain`, `trace` |
| Imports | `import`, `export`, `private` |
| Control | `for`, `each`, `evaluate`, `match` |
| Literals | `true`, `false`, `none` |
| Neural | `neural`, `model`, `confidence_threshold`, `fallback`, `candidates` |

---

## Literals

### Numbers

```sigil
42                  -- integer
3.14                -- float
1_000_000           -- underscore separator
100 degrees         -- number with unit
50 percent          -- number with unit
```

### Text

```sigil
"hello world"                     -- simple string
"temperature is {temp} degrees"   -- string interpolation
```

Interpolation uses `{expression}` inside double-quoted strings.

### Booleans

```sigil
true
false
```

### Symbols

```sigil
:active
:critical
:approved
```

Symbols are interned atoms. They start with `:` and are compared by identity.

### None

```sigil
none
```

### Lists

```sigil
[1, 2, 3]
["a", "b", "c"]
[:active, :inactive]
```

### Records

```sigil
{name: "Alice", age: 30, role: :engineer}
```

---

## Declarations

### `define` — Constants

```sigil
define MAX_TEMP as 100
define GREETING as "hello"
define REGIONS as ["us-east", "us-west"]
```

### `type` — Type definitions

**Record types:**

```sigil
type Person is record:
  name: Text
  age: Number
  email: Text
```

**Enum types (sum types):**

```sigil
type Severity is one of:
  low
  medium
  high
  critical
```

**Enum with associated data:**

```sigil
type Decision is one of:
  approved with rate: Number
  denied with reasons: list of Text
  review with notes: Text
```

**Type aliases:**

```sigil
type Age is Number
type Name is Text
```

**Constrained types:**

```sigil
type Percentage is Number between 0 and 100
type PositiveInt is Number above 0
```

**Unit types:**

```sigil
type Temperature is Number with unit degrees
type Duration is Number with unit seconds
```

### `rule` — Rule declarations

Basic form:

```
rule NAME:
  when CONDITION
  then ACTION
```

Full form:

```
rule NAME with priority NUMBER:
  when CONDITION
  and CONDITION
  then ACTION
  explain "TEXT"
  trace:
    category SYMBOL
    retention NUMBER years
```

**Block actions** use a `then:` block with multiple statements:

```sigil
rule complex_action with priority 10:
  when condition is true
  then:
    given x as compute_something()
    return result with value: x
  explain "Computed result"
```

### `compute` — Function declarations

```sigil
compute NAME from PARAM: TYPE, PARAM: TYPE returns TYPE:
  BODY
```

Example:

```sigil
compute risk_score from applicant: Person returns Number:
  given base as 100
  given factor as applicant.age / 10
  return base - factor
```

### `neural` — Neural declarations

```sigil
neural NAME from PARAM: TYPE:
  model "MODEL_NAME"
  returns TYPE
  confidence_threshold NUMBER
  fallback to VALUE
```

Optional clauses: `candidates [...]`, `using python MODULE`.

### `main` — Entry point

```sigil
main:
  given data from input
  evaluate all rules with data
```

---

## Condition operators

### Comparison

| Sigil | Meaning | Symbolic |
|-------|---------|----------|
| `x exceeds y` | x > y | `x > y` |
| `x is below y` | x < y | `x < y` |
| `x is at least y` | x >= y | `x >= y` |
| `x is at most y` | x <= y | `x <= y` |
| `x equals y` | x == y | `x = y` |
| `x is y` | x == y | `x = y` |
| `x is not y` | x != y | `x != y` |
| `x is between a and b` | a <= x <= b | — |

### Logical

| Sigil | Meaning |
|-------|---------|
| `COND and COND` | Both conditions must hold |
| `COND or COND` | At least one condition must hold |
| `not COND` | Condition must not hold |

### Collection

| Sigil | Meaning |
|-------|---------|
| `x in collection` | x is a member of collection |
| `x not in collection` | x is not a member |
| `collection contains x` | collection contains x (reversed) |

### Quantifiers

| Sigil | Meaning |
|-------|---------|
| `any X in XS has COND` | At least one element satisfies condition |
| `all XS have COND` | Every element satisfies condition |

---

## Statements

### `given` — Binding

```sigil
given x as 42                     -- bind to expression
given data from input             -- bind from external input
given result from some_function() -- bind from function call
```

### `becomes` — Mutation

```sigil
counter becomes counter + 1
```

### `return` — Return value

```sigil
return value
return approved with rate: 5.5
```

### `for each` — Iteration

```sigil
for each item in collection:
  process(item)
```

### `if / else` — Conditional

```sigil
if condition:
  do_something()
else if other_condition:
  do_other()
else:
  do_default()
```

### `match` — Pattern matching

```sigil
match value:
  pattern1 -> result1
  pattern2 -> result2
```

### `evaluate` — Rule evaluation

```sigil
evaluate rule_name
evaluate rule_name with data
evaluate all rules
evaluate all rules with data
```

---

## Field access

Sigil uses space-based field access:

```sigil
reading temperature       -- equivalent to reading.temperature
applicant credit_score    -- equivalent to applicant.credit_score
```

Dot notation also works: `reading.temperature`.

---

## Module system

```sigil
module lending.eligibility          -- declare module

import sigil.math                   -- import Sigil module
import python pandas as pd         -- import Python package
import rust sigil_core::solver     -- import Rust crate

from sigil.math import mean        -- selective import

export some_rule                    -- explicit export
private rule internal:              -- private declaration
  when x then y
```

---

## Grammar properties

- **PEG-based**: Unambiguous, deterministic, linear-time parsing
- **Indentation-sensitive**: Significant whitespace (spaces only, no tabs)
- **Newline-separated**: Statements are separated by newlines
- **UTF-8**: Full Unicode support for identifiers
- **~30 keywords**: All common English words
