//! BDD witness decoding.
//!
//! Translates a BDD satisfying valuation back into human-readable
//! variable assignments (e.g., "x > 100, status = :active").

use biodivine_lib_bdd::BddValuation;
use std::collections::HashMap;

use super::encoder::{ThresholdMapping, VerifierContext};

/// Decode a BDD valuation into a human-readable witness string.
pub fn decode_witness(ctx: &VerifierContext, valuation: &BddValuation) -> String {
    let mut parts: Vec<String> = Vec::new();

    for var_name in &ctx.input_variables {
        // Decode numeric thresholds
        if let Some(mappings) = ctx.numeric_mappings.get(var_name) {
            if let Some(desc) = decode_numeric(var_name, mappings, valuation) {
                parts.push(desc);
                continue;
            }
        }

        // Decode symbol enums
        if let Some(sym_map) = ctx.symbol_mappings.get(var_name) {
            if let Some(desc) = decode_symbol(var_name, sym_map, valuation) {
                parts.push(desc);
                continue;
            }
        }

        // Decode booleans
        if let Some(bdd_var) = ctx.boolean_mappings.get(var_name) {
            let val = valuation.value(*bdd_var);
            parts.push(format!("{} is {}", var_name, val));
            continue;
        }

        // Decode assigned
        if let Some(bdd_var) = ctx.assigned_mappings.get(var_name) {
            let val = valuation.value(*bdd_var);
            if val {
                parts.push(format!("{} is assigned", var_name));
            } else {
                parts.push(format!("{} is not assigned", var_name));
            }
            continue;
        }

        // Decode empty
        if let Some(bdd_var) = ctx.empty_mappings.get(var_name) {
            let val = valuation.value(*bdd_var);
            if val {
                parts.push(format!("{} is empty", var_name));
            } else {
                parts.push(format!("{} is not empty", var_name));
            }
        }
    }

    if parts.is_empty() {
        "any input".to_string()
    } else {
        parts.join(", ")
    }
}

/// Decode a numeric variable's range from threshold predicates.
fn decode_numeric(
    var_name: &str,
    mappings: &[ThresholdMapping],
    valuation: &BddValuation,
) -> Option<String> {
    if mappings.is_empty() {
        return None;
    }

    // Find the transition point: the last threshold where x_le_T is false,
    // and the first threshold where x_le_T is true.
    let mut lower_bound: Option<i64> = None;
    let mut upper_bound: Option<i64> = None;

    for m in mappings {
        let is_le = valuation.value(m.bdd_var);
        if is_le {
            if upper_bound.is_none() {
                upper_bound = Some(m.threshold);
            }
        } else {
            lower_bound = Some(m.threshold);
        }
    }

    match (lower_bound, upper_bound) {
        (Some(lb), Some(ub)) => Some(format!("{} in ({}, {}]", var_name, lb, ub)),
        (Some(lb), None) => Some(format!("{} > {}", var_name, lb)),
        (None, Some(ub)) => Some(format!("{} <= {}", var_name, ub)),
        (None, None) => None,
    }
}

/// Decode a symbol variable's value.
fn decode_symbol(
    var_name: &str,
    sym_map: &HashMap<String, biodivine_lib_bdd::BddVariable>,
    valuation: &BddValuation,
) -> Option<String> {
    for (sym_name, bdd_var) in sym_map {
        if valuation.value(*bdd_var) {
            return Some(format!("{} is :{}", var_name, sym_name));
        }
    }
    // No symbol is true — variable has some other value
    let symbols: Vec<&String> = sym_map.keys().collect();
    if !symbols.is_empty() {
        Some(format!(
            "{} is not any of [{}]",
            var_name,
            symbols
                .iter()
                .map(|s| format!(":{}", s))
                .collect::<Vec<_>>()
                .join(", ")
        ))
    } else {
        None
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::verifier::{ActionInfo, ConditionInfo, RuleInfo};
    use crate::verifier::encoder::VerifierContext;

    fn make_action() -> ActionInfo {
        ActionInfo {
            kind: "set".to_string(),
            target: Some("result".to_string()),
            value: Some("true".to_string()),
        }
    }

    #[test]
    fn test_decode_numeric_witness() {
        let rules = vec![RuleInfo {
            name: "r1".to_string(),
            priority: 0,
            conditions: vec![ConditionInfo {
                kind: "comparison".to_string(),
                variable: Some("age".to_string()),
                operator: Some("exceeds".to_string()),
                value: Some(18.0),
                value2: None,
                symbol: None,
                bool_value: None,
                elements: None,
                negated: None,
                left: None,
                right: None,
            }],
            action: make_action(),
            read_vars: vec!["age".into()],
            write_vars: vec![],
        }];
        let ctx = VerifierContext::from_rules(&rules);
        let bdd = ctx.encode_rule(&rules[0]);
        // Get a satisfying assignment
        let valuation = bdd.sat_valuations().next();
        assert!(valuation.is_some(), "should have a witness");
        let witness = decode_witness(&ctx, &valuation.unwrap());
        assert!(witness.contains("age"), "witness should mention age");
    }

    #[test]
    fn test_decode_symbol_witness() {
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
        let ctx = VerifierContext::from_rules(&rules);
        let bdd = ctx.encode_rule(&rules[0]);
        let valuation = bdd.sat_valuations().next().unwrap();
        let witness = decode_witness(&ctx, &valuation);
        assert!(witness.contains("status"), "witness should mention status");
        assert!(witness.contains(":active"), "witness should mention :active");
    }
}
