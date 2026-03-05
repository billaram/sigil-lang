# Sigil: Language Syntax Specification

## Design Goals

1. **Reads like English**: A non-programmer should understand the intent
2. **Parses like a PEG**: Unambiguous, deterministic, linear-time
3. **Generates like code**: LLMs produce valid Sigil with high reliability
4. **Flat and regular**: Minimal nesting, consistent patterns

## Program Structure

A Sigil program consists of top-level declarations:

```sigil
-- Module declaration (optional, inferred from filename)
module temperature_monitoring

-- Imports
import python numpy as np
import sigil.math
import rust sigil_core::solver

-- Type definitions
type Temperature is Number with unit degrees
type SensorReading is record:
  sensor_id: Text
  temperature: Temperature
  status: Symbol
  timestamp: Number

-- Constants
define MAX_SAFE_TEMP as 100 degrees
define ALERT_COOLDOWN as 300 seconds

-- Rules (the core of Sigil)
rule temperature_alert:
  when reading temperature exceeds MAX_SAFE_TEMP
  and reading status is :active
  then trigger alert with severity :critical
  explain "Sensor {reading.sensor_id} exceeded {MAX_SAFE_TEMP}"

-- Functions (for computation)
compute average_temperature from readings:
  return math.mean(readings map temperature)

-- Entry point
main:
  given readings from load_sensor_data()
  for each reading in readings:
    evaluate temperature_alert with reading
```

## Lexical Structure

### Comments
```sigil
-- This is a single-line comment

{- This is a
   multi-line comment -}

--- This is a doc comment (attached to the next declaration)
--- It supports **markdown** formatting
rule documented_rule:
  when x is true then y
```

### Literals
```sigil
-- Numbers
42                  -- integer
3.14                -- float
100 degrees         -- number with unit
50 percent          -- number with unit
1_000_000           -- underscore separator

-- Text
"hello world"                    -- simple string
"temperature is {temp} degrees"  -- interpolated string
"""
  Multi-line text block
  preserves indentation
"""

-- Booleans
true
false

-- Symbols (atoms/keywords)
:active
:critical
:approved
:pending

-- Lists
[1, 2, 3, 4, 5]
["alpha", "beta", "gamma"]

-- Records
{name: "Alice", age: 30, role: :engineer}

-- None
none
```

### Units
```sigil
-- Sigil has first-class unit support
100 degrees
50 percent
3.5 seconds
1000 milliseconds
42 dollars
99.9 confidence    -- special: 0-100 scale maps to 0.0-1.0

-- Unit conversion is built-in
define temp_f as convert 100 degrees celsius to fahrenheit
```

## Declarations

### Type Declarations
```sigil
-- Simple type alias
type Age is Number
type Name is Text

-- Record type
type Person is record:
  name: Name
  age: Age
  email: Text

-- Enum type (sum type)
type Severity is one of:
  low
  medium
  high
  critical

-- Constrained type
type Percentage is Number between 0 and 100
type PositiveInt is Number above 0

-- Generic type
type Result[T] is one of:
  success with value: T
  failure with reason: Text

-- Unit type
type Temperature is Number with unit degrees
type Duration is Number with unit seconds
```

### Constant Definitions
```sigil
define PI as 3.14159
define MAX_RETRIES as 3
define DEFAULT_TIMEOUT as 30 seconds
define SUPPORTED_REGIONS as ["us-east", "us-west", "eu-central"]
```

### Rule Declarations

Rules are the primary construct in Sigil:

```sigil
-- Basic rule
rule simple_check:
  when temperature exceeds 100
  then alert

-- Rule with multiple conditions (AND)
rule compound_check:
  when temperature exceeds 100
  and humidity exceeds 80
  and wind_speed is below 5
  then alert with severity :high

-- Rule with OR conditions
rule either_condition:
  when temperature exceeds 100
  or pressure exceeds 1013
  then monitor_closely

-- Rule with NOT
rule exclusion:
  when temperature exceeds 100
  and not maintenance_mode is true
  then alert

-- Rule with BETWEEN
rule range_check:
  when temperature is between 80 and 100
  then warn

-- Rule with IN (membership)
rule membership_check:
  when region in SUPPORTED_REGIONS
  and tier in [:premium, :enterprise]
  then enable_feature

-- Rule with ANY/ALL/NONE (quantifiers)
rule quantifier_check:
  when any sensor in sensors has temperature exceeding 100
  then alert_any

rule all_check:
  when all sensors have status :active
  then system_healthy

-- Rule with priority
rule high_priority_alert with priority 10:
  when temperature exceeds 200
  then emergency_shutdown

-- Rule with metadata
rule documented_rule:
  version "2.1"
  author "safety_team"
  tags [:safety, :temperature, :critical]
  when temperature exceeds 100
  then alert
  explain "Temperature safety threshold exceeded per regulation CFR-49"
```

### Condition Operators

```sigil
-- Comparison (natural language style)
x exceeds y            -- x > y
x is below y           -- x < y
x is at least y        -- x >= y
x is at most y         -- x <= y
x equals y             -- x == y
x is y                 -- x == y (for symbols, booleans)
x is not y             -- x != y
x is between a and b   -- a <= x <= b

-- Also supports symbolic operators
x > y
x < y
x >= y
x <= y
x = y
x != y

-- Collection operators
x in collection           -- membership
x not in collection       -- non-membership
collection contains x     -- membership (reversed)
collection is empty       -- length == 0
collection has count n    -- length == n

-- String operators
text starts with "prefix"
text ends with "suffix"
text contains "substring"
text matches pattern "[A-Z]{3}-[0-9]{4}"
```

### Function Declarations (compute blocks)
```sigil
-- Pure computation
compute bmi from weight, height:
  return weight / (height * height)

-- With type annotations
compute risk_score from applicant: Person returns Number:
  given base as 100
  given age_factor as applicant.age / 10
  given income_factor as applicant.income / 50000
  return base - age_factor + income_factor

-- Pattern matching
compute describe_severity from level: Severity returns Text:
  match level:
    low      -> "No action needed"
    medium   -> "Monitor situation"
    high     -> "Immediate attention required"
    critical -> "Emergency response activated"
```

### Neural Declarations
```sigil
-- Neural classification
neural classify_intent from user_input: Text:
  model "intent-classifier-v2"
  returns Symbol
  confidence_threshold 0.85
  candidates [:inquiry, :complaint, :purchase, :cancellation]
  fallback to :unknown

-- Neural extraction
neural extract_entities from document: Text:
  model "ner-medical-v3"
  returns list of record:
    entity: Text
    type: Symbol
    span: record(start: Number, end: Number)
  confidence_threshold 0.7
  fallback to empty list

-- Neural with custom Python model
neural predict_churn from customer: CustomerProfile:
  using python churn_model.predict
  returns Confidence
  threshold 0.6
  fallback to 0.5
```

### Module System
```sigil
-- Declaring a module
module lending.eligibility

-- Importing
import sigil.math                         -- standard library
import python pandas as pd                -- Python package
import rust sigil_core::solver            -- Rust crate
import lending.credit_check               -- another Sigil module

-- Selective import
from sigil.math import mean, median, stddev
from lending.credit_check import credit_score_rule

-- Exporting (all top-level declarations are public by default)
private rule internal_helper:
  when x is true then y

-- Re-exporting
export lending.credit_check.credit_score_rule
```

## Control Flow

```sigil
-- Conditional (in compute blocks)
compute categorize from value: Number returns Symbol:
  if value exceeds 100:
    return :high
  else if value exceeds 50:
    return :medium
  else:
    return :low

-- For each (iteration)
compute total from items: list of Number returns Number:
  given sum as 0
  for each item in items:
    sum becomes sum + item
  return sum

-- Pipeline (functional composition)
compute process from data: list of Record:
  return data
    |> filter where status is :active
    |> sort by timestamp descending
    |> take first 10
    |> map to score

-- Let binding (given...as)
compute complex_calc from x: Number, y: Number:
  given a as x * x
  given b as y * y
  given hypotenuse as math.sqrt(a + b)
  return hypotenuse
```

## Trace Expressions

```sigil
-- Explicit trace annotation
rule audited_decision:
  when amount exceeds 10000
  then flag_for_review
  trace:
    category :financial
    retention 7 years
    format :detailed
  explain "Transaction exceeds reporting threshold per BSA/AML regulation"

-- Trace query (reading traces)
compute audit_report from traces: list of Trace:
  return traces
    |> filter where category is :financial
    |> filter where timestamp is between start_date and end_date
    |> format as table
```

## Complete Example: Loan Eligibility

```sigil
module lending.eligibility

--- Loan eligibility determination following federal lending guidelines.
--- All decisions produce full audit traces for CFPB compliance.

import sigil.math
import python sklearn.ensemble.GradientBoostingClassifier as GBC

-- Types
type Applicant is record:
  name: Text
  age: Number
  income: Number with unit dollars
  credit_score: Number
  debt_to_income: Percentage
  employment_years: Number
  loan_amount: Number with unit dollars

type Decision is one of:
  approved with rate: Percentage
  denied with reasons: list of Text
  review with notes: Text

-- Constants
define MIN_AGE as 21
define MAX_AGE as 65
define MIN_CREDIT_SCORE as 680
define MAX_DTI as 43 percent
define MIN_INCOME as 30000 dollars
define MIN_EMPLOYMENT as 2

-- Rules
rule age_eligibility:
  when applicant age is between MIN_AGE and MAX_AGE
  then age_ok is true
  explain "Applicant age {applicant.age} within eligible range"

rule income_eligibility:
  when applicant income is at least MIN_INCOME
  then income_ok is true
  explain "Income {applicant.income} meets minimum threshold"

rule credit_eligibility:
  when applicant credit_score is at least MIN_CREDIT_SCORE
  then credit_ok is true
  explain "Credit score {applicant.credit_score} meets requirement"

rule dti_eligibility:
  when applicant debt_to_income is at most MAX_DTI
  then dti_ok is true
  explain "DTI ratio {applicant.debt_to_income} within federal limit"

rule employment_eligibility:
  when applicant employment_years is at least MIN_EMPLOYMENT
  then employment_ok is true
  explain "Employment history of {applicant.employment_years} years sufficient"

rule full_eligibility with priority 10:
  when age_ok is true
  and income_ok is true
  and credit_ok is true
  and dti_ok is true
  and employment_ok is true
  then approve_loan

-- Rate computation
compute interest_rate from applicant: Applicant returns Percentage:
  given base_rate as 5.5 percent
  given credit_adj as (applicant.credit_score - 680) * 0.01
  given dti_adj as (MAX_DTI - applicant.debt_to_income) * 0.05
  return base_rate - credit_adj - dti_adj

-- Neural fallback for edge cases
neural assess_risk from applicant: Applicant:
  using python risk_model.predict
  returns Confidence
  threshold 0.7
  fallback to 0.5

-- Final decision
rule final_decision:
  when approve_loan is true
  then:
    given rate as interest_rate(applicant)
    return approved with rate: rate
  explain "Loan approved at {rate} interest rate"

rule denial_decision with priority 5:
  when approve_loan is not true
  then:
    given reasons as collect_failure_reasons()
    return denied with reasons: reasons
  explain "Application denied: {reasons}"

-- Entry point
main:
  given applicant from parse_application(input)
  evaluate all rules with applicant
  trace:
    category :lending
    retention 7 years
    compliance [:cfpb, :ecoa, :fcra]
```

## Grammar Summary

The full PEG grammar is specified in [GRAMMAR.peg](../spec/GRAMMAR.peg). Key properties:

- **~30 keywords**: All common English words
- **Indentation-based blocks**: No braces, no end keywords
- **Optional semicolons**: Newlines are statement separators
- **Context-sensitive keywords**: `when`, `then`, `and` are only keywords in rule context
- **UTF-8 identifiers**: Full Unicode support for domain terminology
- **No operator precedence ambiguity**: PEG ordered choice resolves all ambiguity
