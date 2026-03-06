# Loan Eligibility

A full loan eligibility determination system following federal lending guidelines. Demonstrates forward chaining, compute blocks, and compliance traces.

**Source:** `examples/rules/loan_eligibility.sigil`

---

## What we're building

A rule-based system that evaluates a loan application against five eligibility criteria, computes an interest rate, and produces an auditable decision with compliance traces.

---

## Full source

```sigil
module examples.loan_eligibility

import sigil.math

-- Type definitions
type Applicant is record: -- (1)!
  name: Text
  age: Number
  income: Number
  credit_score: Number
  debt_to_income: Number
  employment_years: Number
  loan_amount: Number

type Decision is one of: -- (2)!
  approved with rate: Number
  denied with reasons: list of Text
  review with notes: Text

-- Regulatory constants
define MIN_AGE as 21 -- (3)!
define MAX_AGE as 65
define MIN_CREDIT_SCORE as 680
define MAX_DTI as 43
define MIN_INCOME as 30000
define MIN_EMPLOYMENT_YEARS as 2

-- Eligibility rules
rule age_check: -- (4)!
  when applicant age is between MIN_AGE and MAX_AGE
  then age_eligible is true
  explain "Applicant age {applicant.age} is within eligible range ({MIN_AGE}-{MAX_AGE})"

rule income_check:
  when applicant income is at least MIN_INCOME
  then income_eligible is true
  explain "Applicant income {applicant.income} meets minimum threshold of {MIN_INCOME}"

rule credit_check:
  when applicant credit_score is at least MIN_CREDIT_SCORE
  then credit_eligible is true
  explain "Credit score {applicant.credit_score} meets minimum of {MIN_CREDIT_SCORE}"

rule dti_check:
  when applicant debt_to_income is at most MAX_DTI
  then dti_eligible is true
  explain "DTI {applicant.debt_to_income}% within federal limit of {MAX_DTI}%"

rule employment_check:
  when applicant employment_years is at least MIN_EMPLOYMENT_YEARS
  then employment_eligible is true
  explain "Employment history of {applicant.employment_years} years meets requirement"

-- Composite eligibility
rule full_eligibility with priority 10: -- (5)!
  when age_eligible is true
  and income_eligible is true
  and credit_eligible is true
  and dti_eligible is true
  and employment_eligible is true
  then loan_approved is true
  explain "All eligibility criteria satisfied"

-- Interest rate computation
compute calculate_rate from applicant: Applicant returns Number: -- (6)!
  given base_rate as 5.5
  given credit_adjustment as (applicant.credit_score - 680) * 0.01
  given dti_adjustment as (MAX_DTI - applicant.debt_to_income) * 0.05
  given rate as base_rate - credit_adjustment - dti_adjustment
  return math.max(rate, 2.5)

-- Final decision rules
rule approve_decision with priority 20: -- (7)!
  when loan_approved is true
  then:
    given rate as calculate_rate(applicant)
    return approved with rate: rate
  explain "Loan approved at {rate}% interest"
  trace:
    category :lending
    compliance [:cfpb, :ecoa, :fcra]

rule deny_decision with priority 15:
  when loan_approved is not true
  then:
    return denied with reasons: collect_denial_reasons()
  explain "Application denied — see trace for specific failures"
  trace:
    category :lending
    compliance [:cfpb, :ecoa, :fcra]

-- Helper function
compute collect_denial_reasons returns list of Text: -- (8)!
  given reasons as []
  if age_eligible is not true:
    reasons becomes reasons + ["Age outside eligible range"]
  if income_eligible is not true:
    reasons becomes reasons + ["Income below minimum threshold"]
  if credit_eligible is not true:
    reasons becomes reasons + ["Credit score below minimum"]
  if dti_eligible is not true:
    reasons becomes reasons + ["Debt-to-income ratio exceeds limit"]
  if employment_eligible is not true:
    reasons becomes reasons + ["Insufficient employment history"]
  return reasons
```

1. **Record type** — `Applicant` defines all fields needed for the eligibility check.
2. **Sum type** — `Decision` has three variants: `approved`, `denied`, or `review`, each with different associated data.
3. **Regulatory constants** — federal lending thresholds defined as named constants for auditability.
4. **Individual eligibility rules** — each criterion is a separate rule that sets a boolean flag. This is forward chaining in action.
5. **Composite rule** — fires only after all five individual rules have set their flags to `true`. Priority 10 ensures it runs after the basic checks.
6. **Compute block** — pure function that calculates the interest rate based on the applicant's profile. Uses `given` for local bindings.
7. **Block action** — `then:` starts a multi-statement action block. The rule calls `calculate_rate()` and returns a structured decision.
8. **Denial reasons** — collects all failed criteria. Uses `becomes` for mutation (appending to the list).

---

## How forward chaining works here

This example demonstrates Sigil's forward-chaining execution model:

1. **Iteration 1**: The five individual rules (`age_check`, `income_check`, etc.) evaluate their conditions against the input applicant data. If a condition is met, the rule fires and sets a flag (e.g., `age_eligible is true`).

2. **Iteration 2**: `full_eligibility` can now evaluate because the flags exist. If all five are `true`, it sets `loan_approved is true`.

3. **Iteration 3**: Either `approve_decision` or `deny_decision` fires based on `loan_approved`.

4. **Fixed point**: No more rules can fire. Execution stops.

---

## Running it

```bash
sigil run examples/rules/loan_eligibility.sigil \
  --input '{"applicant": {"name": "Alice", "age": 35, "income": 75000, "credit_score": 740, "debt_to_income": 30, "employment_years": 5, "loan_amount": 250000}}'
```

Try an applicant who fails some criteria:

```bash
sigil run examples/rules/loan_eligibility.sigil \
  --input '{"applicant": {"name": "Bob", "age": 19, "income": 20000, "credit_score": 600, "debt_to_income": 50, "employment_years": 1, "loan_amount": 100000}}'
```

---

## Key concepts

- **Forward chaining** — rules fire iteratively until a fixed point; intermediate flags build up to composite decisions
- **Sum types** — `Decision` has distinct variants with different associated data
- **Compute blocks** — pure functions for calculations, called from rule actions
- **Block actions** — `then:` enables multi-statement rule actions
- **Compliance traces** — `trace:` metadata tags decisions for regulatory audit
- **`becomes`** — explicit mutation for list accumulation
