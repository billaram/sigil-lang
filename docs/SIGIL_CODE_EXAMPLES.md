# Sigil Code — Example Prompts & Expected Output

A practical guide showing what you can ask `sigil code` to generate, the Sigil source it produces, and the expected runtime output.

Use these as reference when working with the interactive agent (`sigil code`) or when writing Sigil programs by hand.

---

## 1. Hello World — Constants, Rules, Main Block

**Prompt:**
> Create a simple hello world program that defines a greeting, checks a value against a threshold, and prints the greeting.

**Sigil Code:**

```sigil
-- hello.sigil
-- The simplest Sigil program

define GREETING as "Hello, Sigil!"
define THRESHOLD as 100

rule high_value:
  when x exceeds THRESHOLD
  then trigger alert with severity :warning
  explain "Value exceeded threshold"

main:
  given x as 150
  print(GREETING)
  print("Done!")
```

**Run:**
```bash
sigil run hello.sigil
```

**Output:**
```
Hello, Sigil!
Done!
```

---

## 2. Calculator — Compute Functions with Types

**Prompt:**
> Build a calculator with add, multiply, and square functions. Show the results in main.

**Sigil Code:**

```sigil
-- calculator.sigil
-- Compute functions with type annotations

compute add from a: Number, b: Number returns Number:
  return a + b

compute multiply from a: Number, b: Number returns Number:
  return a * b

compute square from x: Number returns Number:
  return x * x

main:
  given result as add(3, 4)
  print(result)

  given product as multiply(5, 6)
  print(product)

  given sq as square(7)
  print(sq)
```

**Run:**
```bash
sigil run calculator.sigil
```

**Output:**
```
7
30
49
```

---

## 3. Pattern Matching — Match Expressions with Symbols

**Prompt:**
> Create a severity classifier that maps symbol levels to text labels and numeric priority scores using match expressions.

**Sigil Code:**

```sigil
-- pattern_matching.sigil
-- Match expressions with symbol patterns and wildcard

type Severity is one of:
  critical
  high
  medium
  low

compute severity_label from level: Symbol returns Text:
  return match level:
    :critical -> "CRITICAL - Immediate action required"
    :high -> "HIGH - Action required within 1 hour"
    :medium -> "MEDIUM - Action required within 24 hours"
    :low -> "LOW - No immediate action"
    _ -> "UNKNOWN - Unrecognized severity"

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
```

**Run:**
```bash
sigil run pattern_matching.sigil
```

**Output:**
```
HIGH - Action required within 1 hour
75
```

---

## 4. Pipeline Operations — Filter, Sort, Map

**Prompt:**
> Given a list of test scores, filter scores above 80, sort descending and take the top 3, and double all scores.

**Sigil Code:**

```sigil
-- pipeline.sigil
-- Pipeline operator: filter, sort, take, map

define scores as [85, 92, 78, 95, 88, 73, 91]

main:
  -- Find scores above 80
  given high_scores as scores |> filter where it exceeds 80
  print(high_scores)

  -- Sort descending and take top 3
  given top_3 as high_scores |> sort by it descending |> take first 3
  print(top_3)

  -- Double all scores
  given doubled as scores |> map to it * 2
  print(doubled)
```

**Run:**
```bash
sigil run pipeline.sigil
```

**Output:**
```
[85, 92, 95, 88, 91]
[95, 92, 91]
[170, 184, 156, 190, 176, 146, 182]
```

---

## 5. Priority Rules — Conflict Resolution

**Prompt:**
> Create a temperature monitoring system with three priority levels: critical (emergency shutdown), warning (alert), and normal (log). Higher priority rules should fire first.

**Sigil Code:**

```sigil
-- priority_rules.sigil
-- Higher priority rules fire first when multiple match

define CRITICAL_TEMP as 200
define WARNING_TEMP as 100

rule critical_alert with priority 10:
  when temperature exceeds CRITICAL_TEMP
  then trigger shutdown with severity :critical
  explain "Temperature critically high — emergency shutdown"

rule warning_alert with priority 5:
  when temperature exceeds WARNING_TEMP
  then trigger alert with severity :warning
  explain "Temperature above warning threshold"

rule normal_status with priority 1:
  when temperature is below WARNING_TEMP
  then trigger log with status :normal
  explain "Temperature within normal range"

main:
  given temperature as 250
  print(temperature)
```

**Run:**
```bash
sigil run priority_rules.sigil
```

**Output:**
```
250
```

**Run with trace** to see which rules fired:
```bash
sigil run priority_rules.sigil --trace
```

---

## 6. Backward Chaining — Goal-Driven Queries

**Prompt:**
> Create a logic program that determines if a bird can fly. Birds with wings can fly, but penguins cannot fly despite having wings. Use backward chaining with query.

**Sigil Code:**

```sigil
-- backward_chaining.sigil
-- Goal-driven evaluation using query

rule has_wings:
  when species is :bird
  then wings is true

rule is_penguin:
  when species is :penguin
  then wings is true

rule can_fly_bird:
  when wings is true
  and species is :bird
  then can_fly is true
  explain "Birds with wings can fly"

rule cannot_fly_penguin:
  when species is :penguin
  then can_fly is false
  explain "Penguins cannot fly despite having wings"

main:
  given species as :bird
  query can_fly
  print(can_fly)
```

**Run:**
```bash
sigil run backward_chaining.sigil
```

**Output:**
```
true
```

**Run with trace** to see the proof tree:
```bash
sigil run backward_chaining.sigil --trace
```

**Trace Output:**
```
── Backward Chaining ──

[query can_fly] PROVED via can_fly_bird
  bindings: can_fly = true
  [query wings] PROVED via has_wings
    bindings: wings = true

── Output ──
true
```

---

## 7. Standard Library — Math Functions

**Prompt:**
> Show how to use the math standard library: square root, absolute value, rounding, and constants like PI.

**Sigil Code:**

```sigil
-- math_demo.sigil
-- Using sigil.math standard library

import sigil.math

main:
  given root as sqrt(144)
  given absolute as abs(-42)
  given rounded as round(3.14159, 2)

  print(root)
  print(absolute)
  print(rounded)
  print(PI)
```

**Run:**
```bash
sigil run math_demo.sigil
```

**Output:**
```
12.0
42
3.14
3.141592653589793
```

---

## 8. Temperature Monitoring — Records, Multiple Rules, Priorities

**Prompt:**
> Build a complete temperature monitoring system with sensor reading records, thresholds for safe/warning/critical levels, and prioritized rules that trigger different alert severities.

**Sigil Code:**

```sigil
-- temperature.sigil
-- Temperature monitoring with records and prioritized rules

type SensorReading is record:
  sensor_id: Text
  temperature: Number
  status: Symbol

define SAFE_THRESHOLD as 100
define WARNING_THRESHOLD as 80
define CRITICAL_THRESHOLD as 150

rule emergency_shutdown with priority 100:
  when reading temperature exceeds CRITICAL_THRESHOLD
  then shutdown_system

rule temperature_alert with priority 10:
  when reading temperature exceeds SAFE_THRESHOLD
  and reading status is :active
  then trigger alert with severity :high

rule temperature_warning with priority 5:
  when reading temperature is between WARNING_THRESHOLD and SAFE_THRESHOLD
  and reading status is :active
  then trigger alert with severity :medium

rule normal_operation with priority 1:
  when reading temperature is below WARNING_THRESHOLD
  then log status :normal
```

**Run with JSON input:**
```bash
sigil run temperature.sigil --input '{"reading": {"sensor_id": "S1", "temperature": 120, "status": ":active"}}'
```

---

## 9. Neural Declaration — Sentiment Classifier with Fallback

**Prompt:**
> Create a neural sentiment classifier that falls back to :neutral when confidence is low, then route results through symbolic rules.

**Sigil Code:**

```sigil
-- sentiment.sigil
-- Neural-symbolic: classify then route through rules

neural classify_sentiment from text: Text:
  model "hf:distilbert-base-uncased-finetuned-sst-2-english"
  returns Symbol
  confidence_threshold 0.85
  fallback to :neutral

rule positive_action with priority 5:
  given sentiment from input
  when sentiment is :positive
  then action is :promote
  explain "Positive sentiment — promote content"

rule negative_action with priority 5:
  given sentiment from input
  when sentiment is :negative
  then action is :review
  explain "Negative sentiment — flag for review"

rule neutral_action with priority 1:
  given sentiment from input
  when sentiment is :neutral
  then action is :skip
  explain "Neutral or unknown — no action needed"
```

> **Note:** Neural declarations require the model backend (e.g., HuggingFace transformers) to be installed. Without it, the fallback value (`:neutral`) is used.

---

## 10. Loan Eligibility — Full Decision System

**Prompt:**
> Build a complete loan eligibility system with applicant records, regulatory thresholds, multiple eligibility checks, interest rate computation, and a final approve/deny decision with audit traces.

**Sigil Code:**

```sigil
-- loan_eligibility.sigil
-- Full decision system: types, rules, compute, traces

import sigil.math

type Applicant is record:
  name: Text
  age: Number
  income: Number
  credit_score: Number
  debt_to_income: Number
  employment_years: Number
  loan_amount: Number

type Decision is one of:
  approved with rate: Number
  denied with reasons: list of Text
  review with notes: Text

define MIN_AGE as 21
define MAX_AGE as 65
define MIN_CREDIT_SCORE as 680
define MAX_DTI as 43
define MIN_INCOME as 30000

rule age_check:
  when applicant age is between MIN_AGE and MAX_AGE
  then age_eligible is true
  explain "Applicant age within eligible range"

rule income_check:
  when applicant income is at least MIN_INCOME
  then income_eligible is true
  explain "Income meets minimum threshold"

rule credit_check:
  when applicant credit_score is at least MIN_CREDIT_SCORE
  then credit_eligible is true
  explain "Credit score meets minimum"

rule dti_check:
  when applicant debt_to_income is at most MAX_DTI
  then dti_eligible is true
  explain "DTI within federal limit"

rule full_eligibility with priority 10:
  when age_eligible is true
  and income_eligible is true
  and credit_eligible is true
  and dti_eligible is true
  then loan_approved is true
  explain "All eligibility criteria satisfied"

compute calculate_rate from score: Number returns Number:
  given base_rate as 5.5
  given adjustment as (score - 680) * 0.01
  given rate as base_rate - adjustment
  return math.max(rate, 2.5)
```

---

## Using `sigil code` — Interactive Agent Workflows

### Starting a Session

```bash
# Start in the current directory
sigil code

# Start in a specific project directory
sigil code --working-dir ./my-project

# Use a different model
sigil code --model claude-sonnet-4-20250514
```

```
Sigil Code v0.1.0 — AI assistant for the Sigil language
Type 'exit' to quit, ':help' for commands.

sigil-code> _
```

### Local Commands (handled without LLM)

| Command    | Description                        |
|------------|------------------------------------|
| `:help`    | Show available commands             |
| `:files`   | List .sigil files in working dir   |
| `:reset`   | Clear conversation history         |
| `:history` | Show conversation turn count       |
| `:pwd`     | Show working directory             |
| `exit`     | Quit the session                   |

---

### Workflow 1: Create a New Project from Template

**Prompt:**
```
sigil-code> Scaffold a rules project called fraud-detection
```

**What happens:**
1. Agent calls the `scaffold` tool with template `rules` and name `fraud-detection`
2. Creates `fraud-detection/` directory with `types.sigil` and `rules.sigil`
3. Agent explains the project structure

**Expected response:**
```
I've scaffolded a new "rules" project in fraud-detection/. Here's what was created:

  fraud-detection/
    types.sigil   — Type definitions (Priority enum)
    rules.sigil   — Decision rules with priorities

You can run it with:
  sigil run fraud-detection/rules.sigil --input '{"severity": 95, "status": ":active"}'
```

Available templates: `basic`, `rules`, `neural`, `full`

```
sigil-code> Scaffold a full project called insurance-claims
```

Creates: `main.sigil`, `types.sigil`, `rules.sigil`, `compute.sigil`, `input.json`

---

### Workflow 2: Generate a New Sigil File from Description

**Prompt:**
```
sigil-code> Create a fraud detection rule system that checks transaction amount,
            frequency, and location risk. Flag transactions over 10000 as high risk,
            and anything from a flagged country as requiring review.
```

**What happens:**
1. Agent generates Sigil code from your description
2. Agent calls `validate` tool to check it compiles
3. If errors → agent reads them, fixes the code, validates again (automatic)
4. Once valid → agent calls `write_file` to save it
5. Agent explains what was created

**Expected response:**
```
I've created fraud_rules.sigil with 3 rules:

  - high_amount (priority 10): flags transactions over 10000
  - flagged_country (priority 8): flags transactions from risky locations
  - low_risk (priority 1): marks remaining transactions as safe

The code has been validated — no parse or type errors.

To run it:
  sigil run fraud_rules.sigil --input '{"amount": 15000, "country": ":flagged", "frequency": 5}'
```

---

### Workflow 3: Fix Errors in an Existing File

If you have a broken `.sigil` file, ask the agent to read and fix it:

**Prompt:**
```
sigil-code> Read rules.sigil and fix any errors
```

**What happens:**
1. Agent calls `read_file` to see the current contents
2. Agent calls `validate` to find errors
3. Agent fixes the issues (wrong operators, bad indentation, invalid units, etc.)
4. Agent calls `validate` again to confirm the fix
5. Agent calls `write_file` to save the corrected version

**Common errors the agent auto-corrects:**

| Error | Agent Fix |
|-------|-----------|
| `when x > 100` in a rule | → `when x exceeds 100` |
| `x ** 2` | → `pow(x, 2)` (adds `import sigil.math`) |
| 4-space indent | → 2-space indent |
| `30 days` (invalid unit) | → `30` (removes unit) |
| `type Status is enum:` | → `type Status is one of:` |
| `:variant` in enum body | → `variant` (no colon) |
| `return` in main block | → `given result as ...` + `print(result)` |

---

### Workflow 4: Update an Existing File

**Prompt:**
```
sigil-code> Add a medium_risk rule to fraud_rules.sigil that triggers when
            amount is between 5000 and 10000 with priority 5
```

**What happens:**
1. Agent calls `read_file` to get current contents
2. Agent adds the new rule to the existing code
3. Agent calls `validate` to check everything still works
4. Agent calls `write_file` to save the updated version
5. Agent shows what changed

---

### Workflow 5: Run and Test Code

**Prompt:**
```
sigil-code> Run fraud_rules.sigil with amount 15000 and country :flagged
```

**What happens:**
1. Agent calls `execute` with the code and input data
2. Shows output and explains what rules fired

**Prompt:**
```
sigil-code> Run it again with amount 500 and country :safe
```

The agent remembers context from the conversation and re-runs with new inputs.

---

### Workflow 6: Iterative Development

A typical multi-turn session:

```
sigil-code> Create a credit scoring system with risk levels

  [Agent generates, validates, writes credit_score.sigil]

sigil-code> Add a compute function that calculates a weighted score
            from credit_history, income, and debt_ratio

  [Agent reads the file, adds compute function, validates, writes]

sigil-code> The threshold for high risk should be 300 not 500, update it

  [Agent reads, updates the constant, validates, writes]

sigil-code> Run it with credit_history 720, income 85000, debt_ratio 0.3

  [Agent executes, shows output]

sigil-code> Add a neural classifier that predicts default probability
            using the openai backend with 0.9 confidence threshold

  [Agent adds neural declaration, validates, writes]

sigil-code> :files
  credit_score.sigil (480 bytes)

sigil-code> exit
```

---

### Workflow 7: Explain Existing Code

**Prompt:**
```
sigil-code> Read temperature.sigil and explain what it does
```

The agent reads the file and provides a natural language explanation of the types, rules, priorities, and how they interact.

---

### Workflow 8: Format Code

**Prompt:**
```
sigil-code> Format rules.sigil to fix the indentation
```

**What happens:**
1. Agent calls `read_file` to get the source
2. Agent calls `format_code` which round-trips through the AST formatter
3. Agent calls `write_file` with the formatted output

---

## Quick Reference — Common Patterns

| Pattern | Syntax |
|---------|--------|
| Constant | `define NAME as value` |
| Constant with unit | `define TEMP as 100 degrees` |
| Rule | `rule name with priority N:` |
| Condition (greater) | `when x exceeds 100` |
| Condition (less) | `when x is below 50` |
| Condition (range) | `when x is between 10 and 90` |
| Condition (equality) | `when status is :active` |
| Simple action | `then trigger alert with severity :high` |
| Set action | `then risk_level is :high` |
| Block action | `then:` (indented statements) |
| Compute function | `compute name from x: Number returns Number:` |
| Match expression | `match x: when :a then 1, when :b then 2` |
| Pipeline | `data \|> filter where it exceeds 80` |
| Symbol | `:active`, `:high`, `:unknown` |
| Import | `import sigil.math` / `from sigil.math import sqrt` |
| Neural | `neural name from x: Text:` |
| Main block | `main:` (given + print, no return) |
| Query | `query goal_name` |
| Enum type | `type Name is one of:` + indented variants |
| Record type | `type Name is record:` + indented fields |

---

## CLI Commands

```bash
# Interactive AI agent (create, fix, run Sigil programs via conversation)
sigil code
sigil code --working-dir ./my-project
sigil code --model claude-sonnet-4-20250514

# Execute a program
sigil run file.sigil
sigil run file.sigil --input '{"temperature": 150}'
sigil run file.sigil --trace

# Other tools
sigil check file.sigil          # Type-check
sigil fmt file.sigil             # Format
sigil lint file.sigil            # Lint
sigil lex file.sigil             # Dump tokens
sigil parse-ast file.sigil       # Dump AST
sigil repl                       # Interactive REPL
sigil parse "description"        # One-shot NL-to-Sigil generation
```
