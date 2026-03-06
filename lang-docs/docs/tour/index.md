# Language Tour

This is a progressive walkthrough of Sigil's features — from comments to neural declarations. Each section builds on the last.

---

## Comments

```sigil
-- This is a single-line comment

{- This is a
   multi-line comment -}

--- This is a doc comment (attached to the next declaration)
--- It supports **markdown** formatting
rule documented_rule:
  when x is true then y
```

---

## Constants

Use `define` to create named constants. Constants are immutable.

```sigil
define PI as 3.14159
define MAX_RETRIES as 3
define DEFAULT_TIMEOUT as 30 seconds
define SUPPORTED_REGIONS as ["us-east", "us-west", "eu-central"]
```

---

## Literals

Sigil has a rich set of literal types:

=== "Numbers"

    ```sigil
    42                  -- integer
    3.14                -- float
    100 degrees         -- number with unit
    50 percent          -- number with unit
    1_000_000           -- underscore separator
    ```

=== "Text"

    ```sigil
    "hello world"                     -- simple string
    "temperature is {temp} degrees"   -- interpolated string
    ```

=== "Symbols"

    ```sigil
    :active
    :critical
    :approved
    :pending
    ```

    Symbols are interned atoms — lightweight identifiers for states, categories, and labels. They start with `:` and are compared by identity, not by string value.

=== "Collections"

    ```sigil
    -- Lists
    [1, 2, 3, 4, 5]
    ["alpha", "beta", "gamma"]

    -- Records
    {name: "Alice", age: 30, role: :engineer}
    ```

=== "Booleans"

    ```sigil
    true
    false
    none    -- absence of value
    ```

---

## Rules

Rules are the core construct in Sigil. A rule declares *when* a condition holds and *what* to do about it.

### Basic rules

```sigil
rule simple_check:
  when temperature exceeds 100
  then alert
```

### Multiple conditions

Use `and` and `or` to combine conditions:

```sigil
rule compound_check:
  when temperature exceeds 100
  and humidity exceeds 80
  and wind_speed is below 5
  then alert with severity :high

rule either_condition:
  when temperature exceeds 100
  or pressure exceeds 1013
  then monitor_closely
```

### Negation

```sigil
rule exclusion:
  when temperature exceeds 100
  and not maintenance_mode is true
  then alert
```

### Priority

Rules with higher priority fire first during forward chaining:

```sigil
rule emergency_shutdown with priority 100:
  when temperature exceeds 200
  then shutdown_system

rule temperature_warning with priority 5:
  when temperature exceeds 80
  then warn
```

### The `explain` clause

Every rule can include an explanation — a human-readable reason that becomes part of the execution trace:

```sigil
rule temperature_alert:
  when temperature exceeds 100
  then alert
  explain "Temperature exceeded safe threshold"
```

In regulated domains (finance, healthcare, compliance), the explanation is not optional — it's the audit record.

---

## Conditions

Sigil supports natural-language-style comparisons:

### Comparison operators

```sigil
x exceeds y            -- x > y
x is below y           -- x < y
x is at least y        -- x >= y
x is at most y         -- x <= y
x equals y             -- x == y
x is y                 -- x == y (for symbols, booleans)
x is not y             -- x != y
x is between a and b   -- a <= x <= b
```

Sigil also supports symbolic operators (`>`, `<`, `>=`, `<=`, `=`, `!=`).

### Collection operators

```sigil
x in collection           -- membership
x not in collection       -- non-membership
collection contains x     -- membership (reversed)
```

### Quantifiers

```sigil
-- Check if any element matches
when any sensor in sensors has temperature exceeding 100
  then alert

-- Check if all elements match
when all sensors have status :active
  then system_healthy
```

---

## Types

### Record types

```sigil
type Person is record:
  name: Text
  age: Number
  email: Text
```

### Enum types (sum types)

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

### Type aliases

```sigil
type Age is Number
type Name is Text
```

### Constrained types

```sigil
type Percentage is Number between 0 and 100
type PositiveInt is Number above 0
```

### Unit types

```sigil
type Temperature is Number with unit degrees
type Duration is Number with unit seconds
```

!!! info "Gradual typing"
    Types are optional for rapid prototyping but encouraged for production rules. Type annotations are required at module boundaries and in neural declarations.

---

## Compute functions

`compute` blocks define pure functions:

```sigil
compute bmi from weight: Number, height: Number returns Number:
  return weight / (height * height)
```

### Local bindings with `given`

```sigil
compute risk_score from applicant: Person returns Number:
  given base as 100
  given age_factor as applicant.age / 10
  return base - age_factor
```

### Pattern matching

```sigil
compute describe_severity from level: Severity returns Text:
  match level:
    low      -> "No action needed"
    medium   -> "Monitor situation"
    high     -> "Immediate attention required"
    critical -> "Emergency response activated"
```

---

## Control flow

### If / else

```sigil
compute categorize from value: Number returns Symbol:
  if value exceeds 100:
    return :high
  else if value exceeds 50:
    return :medium
  else:
    return :low
```

### For each

```sigil
compute total from items: list of Number returns Number:
  given sum as 0
  for each item in items:
    sum becomes sum + item
  return sum
```

!!! tip "Mutation is explicit"
    The `becomes` keyword is how you reassign a variable. Sigil is immutable by default — `becomes` makes mutation visible and deliberate.

---

## The main block

The `main` block is the entry point for a Sigil program:

```sigil
main:
  given readings from input
  for each reading in readings:
    evaluate temperature_alert with reading
```

Use `given X from input` to bind variables from external input data (passed via `--input` on the CLI).

---

## Traces

Every rule evaluation produces a trace. Traces are not a debugging feature — they are fundamental output.

```sigil
rule audited_decision:
  when amount exceeds 10000
  then flag_for_review
  trace:
    category :financial
    retention 7 years
  explain "Transaction exceeds reporting threshold"
```

Run with `--trace` to see full execution traces:

```
TRACE [temperature_alert]:
  EVAL sensor.temperature > 100 → true  [sensor.temperature = 142]
  EVAL sensor.status = :active  → true
  MATCH rule temperature_alert  → fires
  ACTION trigger alert {severity: :critical}
  EXPLAIN "Temperature exceeded safe threshold on active sensor"
```

!!! warning "Traces in regulated domains"
    In finance, healthcare, and compliance, the trace is often more important than the decision itself. It's the audit record that proves *why* a decision was made.

---

## Neural declarations

The `neural` keyword is the only way to introduce non-determinism in Sigil. It declares a boundary where an LLM or ML model provides input to the symbolic system.

```sigil
neural classify_intent from user_input: Text:
  model "intent-classifier-v2"
  returns Symbol
  confidence_threshold 0.85
  candidates [:inquiry, :complaint, :purchase, :cancellation]
  fallback to :unknown
```

Key properties:

- **Return type is required** — no inference across the neural boundary
- **Confidence threshold is required** — results below the threshold use the fallback
- **Fallback is required** — every neural call has a deterministic fallback

```sigil
neural extract_symptoms from clinical_text: Text:
  model "medical-ner-v3"
  returns list of Text
  confidence_threshold 0.75
  fallback to empty list
```

!!! info "Neural is a declaration, not an implementation"
    In Phase 1, neural declarations are stubs — the symbolic engine treats them as type-annotated boundaries. The actual neural bridge (connecting to real ML models) is Phase 3.

---

## Module system

```sigil
-- Declare a module
module lending.eligibility

-- Import other Sigil modules
import sigil.math

-- Import Python packages
import python pandas as pd

-- Selective import
from sigil.math import mean, median
```

---

## Putting it all together

Here's a complete Sigil program that uses most features:

```sigil
module examples.temperature

type SensorReading is record:
  sensor_id: Text
  temperature: Number
  status: Symbol

define SAFE_THRESHOLD as 100
define WARNING_THRESHOLD as 80

rule temperature_alert with priority 10:
  when reading temperature exceeds SAFE_THRESHOLD
  and reading status is :active
  then trigger alert with severity :high
  explain "Sensor {reading.sensor_id} exceeded safe threshold"

rule temperature_warning with priority 5:
  when reading temperature is between WARNING_THRESHOLD and SAFE_THRESHOLD
  and reading status is :active
  then trigger alert with severity :medium
  explain "Temperature approaching safe threshold"

rule normal_operation with priority 1:
  when reading temperature is below WARNING_THRESHOLD
  then log status :normal
  explain "Temperature within normal range"
```

---

## Next steps

- **[Syntax Reference](../reference/syntax.md)** — Complete syntax reference
- **[Type System](../reference/types.md)** — Deep dive into types
- **[Cookbook](../cookbook/index.md)** — Guided walkthroughs of real examples
