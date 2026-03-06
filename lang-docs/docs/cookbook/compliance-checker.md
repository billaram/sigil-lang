# Compliance Checker

AML/KYC compliance checking for financial transactions. Neural parsing extracts transaction data; symbolic rules enforce regulatory policy.

**Source:** `examples/neuro_symbolic/compliance_checker.sigil`

---

## What we're building

A compliance system that checks financial transactions against Anti-Money Laundering (AML) and Know Your Customer (KYC) regulations. Neural models parse transaction narratives; symbolic rules evaluate sanctions, PEP status, jurisdiction risk, and reporting thresholds.

---

## Full source

```sigil
module examples.compliance

-- Types
type Transaction is record: -- (1)!
  id: Text
  amount: Number
  currency: Symbol
  sender_account_age_days: Number
  recipient_jurisdiction: Symbol
  transaction_type: Symbol
  sender_pep_status: Boolean
  sender_sanctions_match: Boolean

type RiskLevel is one of: -- (2)!
  block with reason: Text
  escalate with reason: Text
  flag with reason: Text
  clear

-- Neural: parse transaction narrative into structured form
neural parse_transaction from narrative: Text: -- (3)!
  model "fin-ner-v2"
  returns Transaction
  confidence_threshold 0.85
  fallback to manual_review

-- High-risk jurisdictions (FATF grey/black list)
define HIGH_RISK_JURISDICTIONS as [ -- (4)!
  :iran, :north_korea, :myanmar,
  :syria, :yemen, :south_sudan
]

-- Thresholds
define CTR_THRESHOLD as 10000
define SUSPICIOUS_THRESHOLD as 5000
define NEW_ACCOUNT_DAYS as 30

-- Sanctions and PEP checks (highest priority)
rule sanctions_block with priority 100: -- (5)!
  when transaction sender_sanctions_match is true
  then risk is block with reason: "OFAC sanctions match"
  explain "Transaction blocked: sender matches OFAC sanctions list"
  trace:
    category :aml
    regulation "OFAC SDN"
    retention 7 years

rule pep_escalation with priority 95:
  when transaction sender_pep_status is true
  and transaction amount exceeds SUSPICIOUS_THRESHOLD
  then risk is escalate with reason: "PEP with significant transaction"
  explain "Politically Exposed Person flagged for enhanced due diligence"

-- Jurisdiction risk
rule high_risk_jurisdiction with priority 90: -- (6)!
  when transaction recipient_jurisdiction in HIGH_RISK_JURISDICTIONS
  then risk is escalate with reason: "High-risk jurisdiction: {transaction.recipient_jurisdiction}"
  explain "Recipient in FATF high-risk jurisdiction"

-- CTR filing requirement
rule ctr_filing with priority 80: -- (7)!
  when transaction amount exceeds CTR_THRESHOLD
  and transaction currency is :usd
  then risk is flag with reason: "CTR filing required (>{CTR_THRESHOLD} USD)"
  explain "Transaction exceeds CTR threshold per BSA requirements"
  trace:
    regulation "BSA/FinCEN CTR"

-- New account + large transaction
rule new_account_risk with priority 75:
  when transaction sender_account_age_days is below NEW_ACCOUNT_DAYS
  and transaction amount exceeds SUSPICIOUS_THRESHOLD
  then risk is escalate with reason: "New account ({transaction.sender_account_age_days} days) with large transaction"
  explain "Account age below {NEW_ACCOUNT_DAYS} days with transaction above {SUSPICIOUS_THRESHOLD}"

-- Clear if no rules fired
rule transaction_clear with priority 1: -- (8)!
  when risk is not assigned
  then risk is clear
  explain "Transaction passed all compliance checks"

-- Entry point
main:
  given narrative from input
  given transaction as parse_transaction(narrative)
  evaluate all rules with transaction
  trace:
    category :compliance
    retention 7 years
    compliance [:bsa, :aml, :fatf, :ofac]
```

1. **Transaction record** — captures all fields needed for compliance checks: amount, currency, sender details, and jurisdiction.
2. **Risk levels** — four possible outcomes: `block` (immediate halt), `escalate` (human review), `flag` (report filing), or `clear` (passed).
3. **Neural parsing** — the NER model converts free-text transaction narratives into structured `Transaction` records. Confidence threshold of 0.85 ensures high accuracy; fallback is manual review.
4. **FATF jurisdictions** — FATF grey/black list countries defined as constants. Uses Symbol lists for efficient membership checking.
5. **Sanctions block (priority 100)** — highest priority rule. OFAC sanctions matches cause immediate blocking. Trace includes 7-year retention for regulatory compliance.
6. **Jurisdiction risk** — checks recipient against FATF high-risk jurisdictions using `in` membership operator.
7. **CTR filing** — Currency Transaction Reports required for USD transactions exceeding $10,000 per BSA requirements.
8. **Default clear** — lowest priority rule fires only if no risk rules fired (`risk is not assigned`).

---

## Rule priority cascade

The rules form a priority cascade that mirrors regulatory severity:

| Priority | Rule | Action |
|----------|------|--------|
| 100 | Sanctions match | **Block** |
| 95 | PEP + large transaction | Escalate |
| 90 | High-risk jurisdiction | Escalate |
| 80 | CTR threshold | Flag |
| 75 | New account + large | Escalate |
| 1 | No risks found | Clear |

Higher-priority rules fire first. Once a risk level is assigned, lower-priority rules that would assign a *different* risk level are effectively overridden.

---

## Key concepts

- **Neural parsing** — unstructured text to structured records via ML model
- **Sum types with data** — `RiskLevel` variants carry reason strings
- **Membership testing** — `jurisdiction in HIGH_RISK_JURISDICTIONS`
- **Priority cascade** — regulatory severity maps directly to rule priority
- **Compliance traces** — `regulation`, `retention`, and `compliance` metadata for audit
- **Default rules** — low-priority catch-all for the "clear" case
- **Space-based field access** — `transaction sender_sanctions_match` reads naturally
