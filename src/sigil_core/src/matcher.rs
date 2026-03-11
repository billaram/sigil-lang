//! Rete-lite pattern matcher for Sigil rules.
//!
//! A simplified Rete network that compiles rules into a discrimination network
//! for efficient matching against facts.

use pyo3::prelude::*;
use std::collections::HashMap;

use crate::values::SigilValue;

/// A single condition in a rule.
#[derive(Debug, Clone)]
pub struct Condition {
    pub field: String,
    pub operator: ConditionOp,
    pub value: SigilValue,
}

/// Condition operators.
#[derive(Debug, Clone)]
pub enum ConditionOp {
    Equals,
    NotEquals,
    GreaterThan,
    LessThan,
    GreaterOrEqual,
    LessOrEqual,
    Between(SigilValue, SigilValue),
    Contains,
}

/// A compiled rule in the Rete network.
#[derive(Debug, Clone)]
pub struct CompiledRule {
    pub name: String,
    pub priority: i64,
    pub conditions: Vec<Condition>,
}

/// A match result — a rule that matched against the facts.
#[derive(Debug, Clone)]
pub struct Match {
    pub rule_name: String,
    pub priority: i64,
    pub bindings: HashMap<String, SigilValue>,
}

/// A simplified Rete network for rule matching.
#[pyclass]
pub struct ReteNetwork {
    rules: Vec<CompiledRule>,
}

#[pymethods]
impl ReteNetwork {
    #[new]
    pub fn new() -> Self {
        ReteNetwork { rules: Vec::new() }
    }

    /// Add a compiled rule to the network.
    pub fn add_rule(
        &mut self,
        name: String,
        priority: i64,
        conditions: Vec<(String, String, PyObject)>,
        py: Python<'_>,
    ) -> PyResult<()> {
        let compiled_conditions: Vec<Condition> = conditions
            .into_iter()
            .map(|(field, op, val)| {
                let value = SigilValue::from_python(val.bind(py))?;
                let operator = match op.as_str() {
                    "==" | "is" => ConditionOp::Equals,
                    "!=" | "is_not" => ConditionOp::NotEquals,
                    ">" | "exceeds" => ConditionOp::GreaterThan,
                    "<" | "below" => ConditionOp::LessThan,
                    ">=" => ConditionOp::GreaterOrEqual,
                    "<=" => ConditionOp::LessOrEqual,
                    "contains" => ConditionOp::Contains,
                    _ => ConditionOp::Equals,
                };
                Ok(Condition {
                    field,
                    operator,
                    value,
                })
            })
            .collect::<PyResult<Vec<_>>>()?;

        self.rules.push(CompiledRule {
            name,
            priority,
            conditions: compiled_conditions,
        });
        Ok(())
    }

    /// Match facts against all rules and return matching rules sorted by priority.
    pub fn match_facts(&self, facts: HashMap<String, PyObject>, py: Python<'_>) -> PyResult<Vec<(String, i64)>> {
        let sigil_facts: HashMap<String, SigilValue> = facts
            .into_iter()
            .map(|(k, v)| {
                let sv = SigilValue::from_python(v.bind(py))?;
                Ok((k, sv))
            })
            .collect::<PyResult<HashMap<_, _>>>()?;

        let mut matches: Vec<(String, i64)> = Vec::new();

        for rule in &self.rules {
            if self.evaluate_conditions(&rule.conditions, &sigil_facts) {
                matches.push((rule.name.clone(), rule.priority));
            }
        }

        // Sort by priority (highest first)
        matches.sort_by(|a, b| b.1.cmp(&a.1));
        Ok(matches)
    }

    /// Return the number of compiled rules.
    pub fn rule_count(&self) -> usize {
        self.rules.len()
    }
}

impl ReteNetwork {
    fn evaluate_conditions(
        &self,
        conditions: &[Condition],
        facts: &HashMap<String, SigilValue>,
    ) -> bool {
        conditions.iter().all(|cond| self.evaluate_condition(cond, facts))
    }

    fn evaluate_condition(
        &self,
        cond: &Condition,
        facts: &HashMap<String, SigilValue>,
    ) -> bool {
        let fact_value = match facts.get(&cond.field) {
            Some(v) => v,
            None => return false,
        };

        match &cond.operator {
            ConditionOp::Equals => fact_value == &cond.value,
            ConditionOp::NotEquals => fact_value != &cond.value,
            ConditionOp::GreaterThan => compare_values(fact_value, &cond.value)
                .is_some_and(|ord| ord == std::cmp::Ordering::Greater),
            ConditionOp::LessThan => compare_values(fact_value, &cond.value)
                .is_some_and(|ord| ord == std::cmp::Ordering::Less),
            ConditionOp::GreaterOrEqual => compare_values(fact_value, &cond.value)
                .is_some_and(|ord| ord != std::cmp::Ordering::Less),
            ConditionOp::LessOrEqual => compare_values(fact_value, &cond.value)
                .is_some_and(|ord| ord != std::cmp::Ordering::Greater),
            ConditionOp::Between(low, high) => {
                compare_values(fact_value, low)
                    .is_some_and(|ord| ord != std::cmp::Ordering::Less)
                    && compare_values(fact_value, high)
                        .is_some_and(|ord| ord != std::cmp::Ordering::Greater)
            }
            ConditionOp::Contains => {
                if let (SigilValue::List(items), val) = (fact_value, &cond.value) {
                    items.contains(val)
                } else if let (SigilValue::Text(s), SigilValue::Text(sub)) =
                    (fact_value, &cond.value)
                {
                    s.contains(sub.as_str())
                } else {
                    false
                }
            }
        }
    }
}

/// Compare two SigilValues for ordering (numeric types only).
fn compare_values(a: &SigilValue, b: &SigilValue) -> Option<std::cmp::Ordering> {
    match (a, b) {
        (SigilValue::Int(a), SigilValue::Int(b)) => Some(a.cmp(b)),
        (SigilValue::Float(a), SigilValue::Float(b)) => a.partial_cmp(b),
        (SigilValue::Int(a), SigilValue::Float(b)) => (*a as f64).partial_cmp(b),
        (SigilValue::Float(a), SigilValue::Int(b)) => a.partial_cmp(&(*b as f64)),
        (SigilValue::Text(a), SigilValue::Text(b)) => Some(a.cmp(b)),
        _ => None,
    }
}
