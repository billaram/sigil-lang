//! Threshold extraction from Sigil rule conditions.
//!
//! Scans all rule conditions and extracts numeric comparison points, symbol
//! enum values, and boolean variable names. These become the BDD variables
//! for threshold discretization.

use std::collections::{BTreeSet, HashMap, HashSet};

use super::ConditionInfo;
use super::RuleInfo;

/// All thresholds and variables extracted from a rule set.
#[derive(Debug, Clone)]
pub struct DiscretizationResult {
    /// Variable name → sorted set of numeric threshold values.
    pub numeric_thresholds: HashMap<String, BTreeSet<i64>>,
    /// Variable name → set of symbol values it's compared against.
    pub symbol_enums: HashMap<String, BTreeSet<String>>,
    /// Variables used in boolean checks (is true / is false).
    pub boolean_vars: HashSet<String>,
    /// Variables checked for assignment (is assigned / is not assigned).
    pub assigned_vars: HashSet<String>,
    /// Variables checked for emptiness.
    pub empty_vars: HashSet<String>,
}

impl DiscretizationResult {
    pub fn new() -> Self {
        Self {
            numeric_thresholds: HashMap::new(),
            symbol_enums: HashMap::new(),
            boolean_vars: HashSet::new(),
            assigned_vars: HashSet::new(),
            empty_vars: HashSet::new(),
        }
    }
}

/// Extract all thresholds from a rule set.
pub fn discretize(rules: &[RuleInfo]) -> DiscretizationResult {
    let mut result = DiscretizationResult::new();
    for rule in rules {
        for cond in &rule.conditions {
            extract_from_condition(cond, &mut result);
        }
    }
    result
}

fn extract_from_condition(cond: &ConditionInfo, result: &mut DiscretizationResult) {
    match cond.kind.as_str() {
        "comparison" => {
            if let (Some(ref var), Some(ref op)) = (&cond.variable, &cond.operator) {
                match op.as_str() {
                    "exceeds" | "is below" | "is at least" | "is at most" => {
                        if let Some(val) = cond.value {
                            let thresholds =
                                result.numeric_thresholds.entry(var.clone()).or_default();
                            // Add the threshold and neighbors for boundary precision
                            let ival = val as i64;
                            thresholds.insert(ival);
                            // For strict comparisons, we need the adjacent value
                            match op.as_str() {
                                "exceeds" => {
                                    thresholds.insert(ival);
                                }
                                "is below" => {
                                    thresholds.insert(ival - 1);
                                }
                                "is at least" => {
                                    thresholds.insert(ival - 1);
                                }
                                "is at most" => {
                                    thresholds.insert(ival);
                                }
                                _ => {}
                            }
                        }
                    }
                    "is between" => {
                        if let (Some(low), Some(high)) = (cond.value, cond.value2) {
                            let thresholds =
                                result.numeric_thresholds.entry(var.clone()).or_default();
                            let low_i = low as i64;
                            let high_i = high as i64;
                            thresholds.insert(low_i - 1);
                            thresholds.insert(high_i);
                        }
                    }
                    "is" | "equals" => {
                        if let Some(ref sym) = cond.symbol {
                            result
                                .symbol_enums
                                .entry(var.clone())
                                .or_default()
                                .insert(sym.clone());
                        } else if let Some(val) = cond.value {
                            // Numeric equality — add threshold
                            let thresholds =
                                result.numeric_thresholds.entry(var.clone()).or_default();
                            let ival = val as i64;
                            thresholds.insert(ival);
                            thresholds.insert(ival - 1);
                        }
                    }
                    "is not" => {
                        if let Some(ref sym) = cond.symbol {
                            result
                                .symbol_enums
                                .entry(var.clone())
                                .or_default()
                                .insert(sym.clone());
                        }
                    }
                    _ => {}
                }
            }
        }
        "boolean" => {
            if let Some(ref var) = cond.variable {
                result.boolean_vars.insert(var.clone());
            }
        }
        "membership" => {
            if let (Some(ref var), Some(ref elems)) = (&cond.variable, &cond.elements) {
                let thresholds = result.numeric_thresholds.entry(var.clone()).or_default();
                for &e in elems {
                    let ival = e as i64;
                    thresholds.insert(ival);
                    thresholds.insert(ival - 1);
                }
            }
        }
        "is_assigned" => {
            if let Some(ref var) = cond.variable {
                result.assigned_vars.insert(var.clone());
            }
        }
        "is_empty" => {
            if let Some(ref var) = cond.variable {
                result.empty_vars.insert(var.clone());
            }
        }
        "not" => {
            if let Some(ref inner) = cond.left {
                extract_from_condition(inner, result);
            }
        }
        "compound" => {
            if let Some(ref left) = cond.left {
                extract_from_condition(left, result);
            }
            if let Some(ref right) = cond.right {
                extract_from_condition(right, result);
            }
        }
        _ => {}
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::verifier::{ActionInfo, ConditionInfo, RuleInfo};

    fn make_cond(kind: &str, var: &str, op: &str, val: f64) -> ConditionInfo {
        ConditionInfo {
            kind: kind.to_string(),
            variable: Some(var.to_string()),
            operator: Some(op.to_string()),
            value: Some(val),
            value2: None,
            symbol: None,
            bool_value: None,
            elements: None,
            negated: None,
            left: None,
            right: None,
        }
    }

    fn make_action() -> ActionInfo {
        ActionInfo {
            kind: "set".to_string(),
            target: Some("result".to_string()),
            value: Some("true".to_string()),
        }
    }

    #[test]
    fn test_extract_exceeds() {
        let rules = vec![RuleInfo {
            name: "r1".to_string(),
            priority: 0,
            conditions: vec![make_cond("comparison", "age", "exceeds", 25.0)],
            action: make_action(),
            read_vars: vec!["age".into()],
            write_vars: vec![],
        }];
        let result = discretize(&rules);
        assert!(result.numeric_thresholds.contains_key("age"));
        assert!(result.numeric_thresholds["age"].contains(&25));
    }

    #[test]
    fn test_extract_between() {
        let rules = vec![RuleInfo {
            name: "r1".to_string(),
            priority: 0,
            conditions: vec![ConditionInfo {
                kind: "comparison".to_string(),
                variable: Some("temp".to_string()),
                operator: Some("is between".to_string()),
                value: Some(10.0),
                value2: Some(90.0),
                symbol: None,
                bool_value: None,
                elements: None,
                negated: None,
                left: None,
                right: None,
            }],
            action: make_action(),
            read_vars: vec!["temp".into()],
            write_vars: vec![],
        }];
        let result = discretize(&rules);
        let thresholds = &result.numeric_thresholds["temp"];
        assert!(thresholds.contains(&9));  // low - 1
        assert!(thresholds.contains(&90)); // high
    }

    #[test]
    fn test_extract_symbol() {
        let rules = vec![RuleInfo {
            name: "r1".to_string(),
            priority: 0,
            conditions: vec![ConditionInfo {
                kind: "comparison".to_string(),
                variable: Some("status".to_string()),
                operator: Some("is".to_string()),
                value: None,
                value2: None,
                symbol: Some("active".to_string()),
                bool_value: None,
                elements: None,
                negated: None,
                left: None,
                right: None,
            }],
            action: make_action(),
            read_vars: vec!["status".into()],
            write_vars: vec![],
        }];
        let result = discretize(&rules);
        assert!(result.symbol_enums["status"].contains("active"));
    }

    #[test]
    fn test_extract_boolean() {
        let rules = vec![RuleInfo {
            name: "r1".to_string(),
            priority: 0,
            conditions: vec![ConditionInfo {
                kind: "boolean".to_string(),
                variable: Some("flag".to_string()),
                operator: None,
                value: None,
                value2: None,
                symbol: None,
                bool_value: Some(true),
                elements: None,
                negated: None,
                left: None,
                right: None,
            }],
            action: make_action(),
            read_vars: vec!["flag".into()],
            write_vars: vec![],
        }];
        let result = discretize(&rules);
        assert!(result.boolean_vars.contains("flag"));
    }

    #[test]
    fn test_extract_compound() {
        let rules = vec![RuleInfo {
            name: "r1".to_string(),
            priority: 0,
            conditions: vec![ConditionInfo {
                kind: "compound".to_string(),
                variable: None,
                operator: Some("and".to_string()),
                value: None,
                value2: None,
                symbol: None,
                bool_value: None,
                elements: None,
                negated: None,
                left: Some(Box::new(make_cond("comparison", "x", "exceeds", 100.0))),
                right: Some(Box::new(make_cond("comparison", "y", "is below", 50.0))),
            }],
            action: make_action(),
            read_vars: vec!["x".into(), "y".into()],
            write_vars: vec![],
        }];
        let result = discretize(&rules);
        assert!(result.numeric_thresholds.contains_key("x"));
        assert!(result.numeric_thresholds.contains_key("y"));
    }

    #[test]
    fn test_extract_membership() {
        let rules = vec![RuleInfo {
            name: "r1".to_string(),
            priority: 0,
            conditions: vec![ConditionInfo {
                kind: "membership".to_string(),
                variable: Some("x".to_string()),
                operator: None,
                value: None,
                value2: None,
                symbol: None,
                bool_value: None,
                elements: Some(vec![1.0, 2.0, 3.0]),
                negated: Some(false),
                left: None,
                right: None,
            }],
            action: make_action(),
            read_vars: vec!["x".into()],
            write_vars: vec![],
        }];
        let result = discretize(&rules);
        let thresholds = &result.numeric_thresholds["x"];
        assert!(thresholds.contains(&1));
        assert!(thresholds.contains(&2));
        assert!(thresholds.contains(&3));
    }
}
