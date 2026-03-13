"""Project templates for the Sigil Code agent scaffold tool."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TemplateFile:
    """A file within a project template."""

    path: str
    content: str


@dataclass(frozen=True)
class ProjectTemplate:
    """A project scaffold template."""

    name: str
    description: str
    files: tuple[TemplateFile, ...]


BASIC_TEMPLATE = ProjectTemplate(
    name="basic",
    description="Simple Sigil program with a constant, rule, and main block",
    files=(
        TemplateFile(
            path="main.sigil",
            content="""\
-- Basic Sigil program
define THRESHOLD as 100

rule check_value with priority 5:
  when value exceeds THRESHOLD
  then trigger alert with severity :high
  explain "Value exceeded threshold"

main:
  given value as 150
  print("Checking value: {value}")
""",
        ),
    ),
)

RULES_TEMPLATE = ProjectTemplate(
    name="rules",
    description="Multi-rule decision system with type definitions",
    files=(
        TemplateFile(
            path="types.sigil",
            content="""\
-- Type definitions
type Priority is one of:
  low
  medium
  high
  critical
""",
        ),
        TemplateFile(
            path="rules.sigil",
            content="""\
-- Decision rules
rule critical_alert with priority 10:
  given severity from input
  given status from input
  when severity exceeds 90
  and status is :active
  then priority is :critical
  explain "Severity above 90 with active status"

rule high_alert with priority 5:
  given severity from input
  when severity exceeds 70
  then priority is :high
  explain "Severity above 70"

rule low_alert with priority 1:
  given severity from input
  when severity is below 30
  then priority is :low
  explain "Low severity event"
""",
        ),
    ),
)

NEURAL_TEMPLATE = ProjectTemplate(
    name="neural",
    description="Neural classifier with symbolic rule processing",
    files=(
        TemplateFile(
            path="classifier.sigil",
            content="""\
-- Neural text classifier
neural classify from text: Text:
  model "hf:distilbert-base-uncased-finetuned-sst-2-english"
  returns Symbol
  confidence_threshold 0.8
  fallback to :unknown
""",
        ),
        TemplateFile(
            path="rules.sigil",
            content="""\
-- Post-classification rules
define DEFAULT_ACTION as :escalate

rule positive_response with priority 5:
  given sentiment from input
  when sentiment is :positive
  then action is :approve
  explain "Positive sentiment detected"

rule negative_response with priority 5:
  given sentiment from input
  when sentiment is :negative
  then action is :review
  explain "Negative sentiment requires review"

rule unknown_response with priority 1:
  given sentiment from input
  when sentiment is :unknown
  then action is :escalate
  explain "Could not classify — escalate to human"
""",
        ),
    ),
)

FULL_TEMPLATE = ProjectTemplate(
    name="full",
    description="Complete project with types, rules, compute, and main",
    files=(
        TemplateFile(
            path="types.sigil",
            content="""\
-- Type definitions
type Request is record:
  amount: Number
  category: Symbol
  approved: Bool

type Decision is one of:
  approve
  deny
  review
""",
        ),
        TemplateFile(
            path="rules.sigil",
            content="""\
-- Business rules
rule auto_approve with priority 10:
  given amount from input
  given category from input
  when amount is below 1000
  and category is :standard
  then decision is :approve
  explain "Standard requests under 1000 auto-approved"

rule deny_large with priority 5:
  given amount from input
  when amount exceeds 50000
  then decision is :deny
  explain "Amounts over 50000 require board approval"

rule review_others with priority 1:
  given amount from input
  when amount exceeds 1000
  then decision is :review
  explain "Manual review required for amounts over 1000"
""",
        ),
        TemplateFile(
            path="compute.sigil",
            content="""\
-- Compute functions
compute calculate_tax from amount: Number, rate: Number returns Number:
  return amount * rate

compute apply_discount from price: Number, discount: Number returns Number:
  if discount > 1:
    return price
  else:
    return price * (1 - discount)
""",
        ),
        TemplateFile(
            path="main.sigil",
            content="""\
-- Main entry point
main:
  given amount as 5000
  given category as :standard
  print("Processing request for {amount}")
""",
        ),
        TemplateFile(
            path="input.json",
            content="""\
{
  "amount": 5000,
  "category": ":standard"
}
""",
        ),
    ),
)

TEMPLATES: dict[str, ProjectTemplate] = {
    "basic": BASIC_TEMPLATE,
    "rules": RULES_TEMPLATE,
    "neural": NEURAL_TEMPLATE,
    "full": FULL_TEMPLATE,
}


def get_template(name: str) -> ProjectTemplate | None:
    """Get a project template by name."""
    return TEMPLATES.get(name)


def list_templates() -> list[str]:
    """List available template names."""
    return list(TEMPLATES.keys())
