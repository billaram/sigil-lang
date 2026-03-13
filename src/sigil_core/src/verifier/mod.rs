//! BDD-based formal verification for Sigil rule sets.
//!
//! Encodes Sigil rule conditions as Binary Decision Diagrams using threshold
//! discretization, then checks completeness, conflicts, dead rules, and
//! termination via BDD operations.

pub mod discretize;
pub mod encoder;
pub mod checkers;
pub mod witness;
pub mod report;

use pyo3::prelude::*;
use pyo3::types::PyList;
use serde::Serialize;

use self::checkers::{check_completeness, check_conflicts, check_dead_rules, check_termination};
use self::encoder::VerifierContext;
use self::report::VerificationReport;

/// Serialized representation of a rule condition passed from Python.
#[derive(Debug, Clone, Serialize)]
pub struct ConditionInfo {
    pub kind: String,
    pub variable: Option<String>,
    pub operator: Option<String>,
    pub value: Option<f64>,
    pub value2: Option<f64>,
    pub symbol: Option<String>,
    pub bool_value: Option<bool>,
    pub elements: Option<Vec<f64>>,
    pub negated: Option<bool>,
    pub left: Option<Box<ConditionInfo>>,
    pub right: Option<Box<ConditionInfo>>,
}

/// Serialized representation of a rule action.
#[derive(Debug, Clone, Serialize, PartialEq)]
pub struct ActionInfo {
    pub kind: String,
    pub target: Option<String>,
    pub value: Option<String>,
}

/// Serialized representation of a Sigil rule.
#[derive(Debug, Clone, Serialize)]
pub struct RuleInfo {
    pub name: String,
    pub priority: i64,
    pub conditions: Vec<ConditionInfo>,
    pub action: ActionInfo,
    pub read_vars: Vec<String>,
    pub write_vars: Vec<String>,
}

/// Top-level verification: run all checks on a rule set.
pub fn verify_rules(rules: &[RuleInfo]) -> VerificationReport {
    if rules.is_empty() {
        return VerificationReport::empty();
    }

    let ctx = VerifierContext::from_rules(rules);
    let rule_bdds: Vec<_> = rules.iter().map(|r| ctx.encode_rule(r)).collect();

    let completeness = check_completeness(&ctx, &rule_bdds);
    let dead_rules = check_dead_rules(rules, &rule_bdds);
    let conflicts = check_conflicts(&ctx, rules, &rule_bdds);
    let termination = check_termination(rules);

    VerificationReport {
        completeness,
        dead_rules,
        conflicts,
        termination,
        rule_count: rules.len(),
        variable_count: ctx.variable_count(),
        bdd_variable_count: ctx.bdd_variable_count(),
    }
}

// --- Python FFI ---

fn extract_condition(obj: &Bound<'_, PyAny>) -> PyResult<ConditionInfo> {
    let kind: String = obj.get_item("kind")?.extract()?;
    Ok(ConditionInfo {
        kind: kind.clone(),
        variable: obj.get_item("variable").ok().and_then(|v| v.extract().ok()),
        operator: obj.get_item("operator").ok().and_then(|v| v.extract().ok()),
        value: obj.get_item("value").ok().and_then(|v| v.extract().ok()),
        value2: obj.get_item("value2").ok().and_then(|v| v.extract().ok()),
        symbol: obj.get_item("symbol").ok().and_then(|v| v.extract().ok()),
        bool_value: obj.get_item("bool_value").ok().and_then(|v| v.extract().ok()),
        elements: obj.get_item("elements").ok().and_then(|v| v.extract().ok()),
        negated: obj.get_item("negated").ok().and_then(|v| v.extract().ok()),
        left: obj
            .get_item("left")
            .ok()
            .and_then(|v| {
                if v.is_none() {
                    None
                } else {
                    extract_condition(&v).ok().map(Box::new)
                }
            }),
        right: obj
            .get_item("right")
            .ok()
            .and_then(|v| {
                if v.is_none() {
                    None
                } else {
                    extract_condition(&v).ok().map(Box::new)
                }
            }),
    })
}

fn extract_action(obj: &Bound<'_, PyAny>) -> PyResult<ActionInfo> {
    Ok(ActionInfo {
        kind: obj.get_item("kind")?.extract()?,
        target: obj.get_item("target").ok().and_then(|v| v.extract().ok()),
        value: obj.get_item("value").ok().and_then(|v| v.extract().ok()),
    })
}

fn extract_rules(rules_list: &Bound<'_, PyList>) -> PyResult<Vec<RuleInfo>> {
    let mut rules = Vec::new();
    for item in rules_list.iter() {
        let name: String = item.get_item("name")?.extract()?;
        let priority: i64 = item.get_item("priority")?.extract().unwrap_or(0);

        let conds_list = item.get_item("conditions")?;
        let mut conditions = Vec::new();
        for c in conds_list.downcast::<PyList>()?.iter() {
            conditions.push(extract_condition(&c)?);
        }

        let action = extract_action(&item.get_item("action")?)?;

        let read_vars: Vec<String> = item
            .get_item("read_vars")
            .ok()
            .and_then(|v| v.extract().ok())
            .unwrap_or_default();
        let write_vars: Vec<String> = item
            .get_item("write_vars")
            .ok()
            .and_then(|v| v.extract().ok())
            .unwrap_or_default();

        rules.push(RuleInfo {
            name,
            priority,
            conditions,
            action,
            read_vars,
            write_vars,
        });
    }
    Ok(rules)
}

/// Verify a set of rules passed from Python as a list of dicts.
/// Returns a JSON string with the verification report.
#[pyfunction]
pub fn verify_program(rules_list: &Bound<'_, PyList>) -> PyResult<String> {
    let rules = extract_rules(rules_list)?;
    let report = verify_rules(&rules);
    serde_json::to_string_pretty(&report)
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))
}
