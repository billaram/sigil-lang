# Cookbook

Guided walkthroughs of Sigil's example programs. Each page explains the code line by line, shows how to run it, and highlights the key concepts demonstrated.

---

## Examples

| Example | Concepts | Difficulty |
|---------|----------|------------|
| [Hello World](hello-world.md) | Constants, rules, `explain` | Beginner |
| [Temperature Monitor](temperature-monitor.md) | Records, priorities, multiple rules | Beginner |
| [Loan Eligibility](loan-eligibility.md) | Types, compute, forward chaining, traces | Intermediate |
| [Medical Triage](medical-triage.md) | Neural bridge, quantifiers, compliance traces | Advanced |
| [Compliance Checker](compliance-checker.md) | Neural parsing, policy rules, audit traces | Advanced |

---

## How to run examples

All examples live in the `examples/` directory of the Sigil repository:

```bash
# Clone the repo
git clone https://github.com/billaram/sigil-lang.git
cd sigil-lang

# Install
pip install -e ".[dev]"

# Run an example
sigil run examples/basics/hello.sigil

# Run with trace output
sigil run examples/basics/temperature.sigil \
  --input '{"reading": {"sensor_id": "S1", "temperature": 120, "status": ":active"}}' \
  --trace
```
