# Sigil for Python Developers

A side-by-side guide for Python programmers learning Sigil.

---

## Variables and constants

=== "Python"

    ```python
    MAX_TEMP = 100
    greeting = "hello"
    ```

=== "Sigil"

    ```sigil
    define MAX_TEMP as 100
    define greeting as "hello"
    ```

In Sigil, all top-level bindings are immutable. There is no reassignment at the top level.

---

## Conditionals

=== "Python"

    ```python
    if temperature > 100:
        alert("too hot")
    elif temperature > 80:
        warn("getting warm")
    else:
        log("normal")
    ```

=== "Sigil"

    ```sigil
    rule hot_check:
      when temperature exceeds 100
      then alert "too hot"

    rule warm_check:
      when temperature is between 80 and 100
      then warn "getting warm"

    rule normal_check:
      when temperature is below 80
      then log "normal"
    ```

!!! info "Rules vs if/else"
    In Python, you write sequential conditionals. In Sigil, you write *rules* — declarative conditions that are evaluated by a forward-chaining engine. Rules with higher priority fire first. This is not just syntax sugar — it's a different execution model.

---

## Functions

=== "Python"

    ```python
    def bmi(weight: float, height: float) -> float:
        return weight / (height * height)
    ```

=== "Sigil"

    ```sigil
    compute bmi from weight: Number, height: Number returns Number:
      return weight / (height * height)
    ```

---

## Local variables

=== "Python"

    ```python
    def risk_score(applicant):
        base = 100
        age_factor = applicant.age / 10
        return base - age_factor
    ```

=== "Sigil"

    ```sigil
    compute risk_score from applicant: Person returns Number:
      given base as 100
      given age_factor as applicant.age / 10
      return base - age_factor
    ```

`given X as Y` is Sigil's equivalent of variable assignment. Variables bound with `given` are immutable by default.

---

## Mutation

=== "Python"

    ```python
    total = 0
    for item in items:
        total += item
    ```

=== "Sigil"

    ```sigil
    given total as 0
    for each item in items:
      total becomes total + item
    ```

Mutation is explicit in Sigil — the `becomes` keyword makes reassignment visible.

---

## Data classes / records

=== "Python"

    ```python
    @dataclass
    class Person:
        name: str
        age: int
        email: str
    ```

=== "Sigil"

    ```sigil
    type Person is record:
      name: Text
      age: Number
      email: Text
    ```

---

## Enums

=== "Python"

    ```python
    class Severity(Enum):
        LOW = "low"
        MEDIUM = "medium"
        HIGH = "high"
        CRITICAL = "critical"
    ```

=== "Sigil"

    ```sigil
    type Severity is one of:
      low
      medium
      high
      critical
    ```

---

## Pattern matching

=== "Python"

    ```python
    match severity:
        case "low":
            return "No action needed"
        case "medium":
            return "Monitor situation"
        case "high":
            return "Immediate attention"
        case "critical":
            return "Emergency response"
    ```

=== "Sigil"

    ```sigil
    match severity:
      low      -> "No action needed"
      medium   -> "Monitor situation"
      high     -> "Immediate attention"
      critical -> "Emergency response"
    ```

---

## Loops

=== "Python"

    ```python
    for reading in readings:
        if reading.temperature > 100:
            alert(reading)
    ```

=== "Sigil"

    ```sigil
    for each reading in readings:
      evaluate temperature_alert with reading
    ```

---

## Collections

=== "Python"

    ```python
    regions = ["us-east", "us-west", "eu-central"]
    if region in regions:
        enable_feature()
    ```

=== "Sigil"

    ```sigil
    define regions as ["us-east", "us-west", "eu-central"]

    rule region_check:
      when region in regions
      then enable_feature
    ```

---

## Key differences

| Concept | Python | Sigil |
|---------|--------|-------|
| Execution model | Sequential | Forward-chaining rules |
| Mutability | Mutable by default | Immutable by default |
| Null handling | `None` + runtime errors | `none` + `_UNBOUND` for missing fields |
| Type system | Optional (mypy) | Gradual (optional, required at boundaries) |
| Output | Return values | Decisions + traces |
| Non-determinism | Anywhere | Only via `neural` keyword |
| Comments | `#` | `--` |
| Strings | `"..."` or `'...'` | `"..."` only |
| Atoms/enums | `Enum` class | `:symbol` literals |
| Entry point | `if __name__ == "__main__"` | `main:` block |

---

## Things Sigil does that Python doesn't

### Execution traces

Every rule evaluation produces an auditable trace — not console.log debugging, but structured execution records. In regulated industries, the trace is the output.

### Forward chaining

Rules don't execute top-to-bottom. The engine evaluates all rules iteratively until no new rules can fire (fixed point). Priority controls firing order.

### The neural boundary

The `neural` keyword declares an explicit boundary between ML models and deterministic logic. There's nothing like this in Python — you just call functions and hope.

```sigil
neural classify from text: Text:
  model "classifier-v2"
  returns Symbol
  confidence_threshold 0.85
  fallback to :unknown
```

### Explain clauses

Every rule carries its own documentation as executable metadata:

```sigil
rule credit_check:
  when score is below 680
  then deny
  explain "Credit score {score} below minimum threshold of 680"
```
