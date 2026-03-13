//! BDD encoder: translates Sigil conditions to BDD formulas.
//!
//! Uses threshold discretization to convert numeric comparisons into boolean
//! predicates, then builds BDDs using biodivine-lib-bdd.

use biodivine_lib_bdd::{Bdd, BddVariable, BddVariableSet, BddVariableSetBuilder};
use std::collections::{BTreeSet, HashMap};

use super::discretize::{discretize, DiscretizationResult};
use super::{ConditionInfo, RuleInfo};

/// Mapping info for decoding BDD witnesses back to human-readable values.
#[derive(Debug, Clone)]
pub struct ThresholdMapping {
    pub bdd_var: BddVariable,
    pub threshold: i64,
}

/// Context for encoding a rule set into BDDs.
#[derive(Debug)]
pub struct VerifierContext {
    pub vars: BddVariableSet,
    /// Variable name → sorted list of (bdd_var, threshold_value) for x_le_N predicates.
    pub numeric_mappings: HashMap<String, Vec<ThresholdMapping>>,
    /// Variable name → map of symbol_value → bdd_var for x_eq_symbol predicates.
    pub symbol_mappings: HashMap<String, HashMap<String, BddVariable>>,
    /// Variable name → bdd_var for boolean predicates.
    pub boolean_mappings: HashMap<String, BddVariable>,
    /// Variable name → bdd_var for is_assigned predicates.
    pub assigned_mappings: HashMap<String, BddVariable>,
    /// Variable name → bdd_var for is_empty predicates.
    pub empty_mappings: HashMap<String, BddVariable>,
    /// Monotonicity + mutual-exclusion constraints.
    pub ordering_bdd: Bdd,
    /// All input variable names.
    pub input_variables: Vec<String>,
    /// Total BDD variables created.
    bdd_var_count: usize,
}

impl VerifierContext {
    /// Build a verifier context by scanning all rule conditions.
    pub fn from_rules(rules: &[RuleInfo]) -> Self {
        let disc = discretize(rules);
        Self::from_discretization(&disc)
    }

    /// Build context from a pre-computed discretization result.
    pub fn from_discretization(disc: &DiscretizationResult) -> Self {
        let mut builder = BddVariableSetBuilder::new();
        let mut numeric_mappings: HashMap<String, Vec<ThresholdMapping>> = HashMap::new();
        let mut symbol_mappings: HashMap<String, HashMap<String, BddVariable>> = HashMap::new();
        let mut boolean_mappings: HashMap<String, BddVariable> = HashMap::new();
        let mut assigned_mappings: HashMap<String, BddVariable> = HashMap::new();
        let mut empty_mappings: HashMap<String, BddVariable> = HashMap::new();
        let mut input_variables: Vec<String> = Vec::new();
        let mut bdd_var_count = 0;

        // Collect all variable names for stable ordering
        let mut all_vars: BTreeSet<String> = BTreeSet::new();
        for k in disc.numeric_thresholds.keys() {
            all_vars.insert(k.clone());
        }
        for k in disc.symbol_enums.keys() {
            all_vars.insert(k.clone());
        }
        for k in &disc.boolean_vars {
            all_vars.insert(k.clone());
        }
        for k in &disc.assigned_vars {
            all_vars.insert(k.clone());
        }
        for k in &disc.empty_vars {
            all_vars.insert(k.clone());
        }

        for var_name in &all_vars {
            input_variables.push(var_name.clone());

            // Numeric thresholds: create x_le_N boolean variables
            if let Some(thresholds) = disc.numeric_thresholds.get(var_name) {
                let mut mappings = Vec::new();
                for &threshold in thresholds {
                    let bdd_name = format!("{}_le_{}", var_name, threshold);
                    let bdd_var = builder.make_variable(&bdd_name);
                    mappings.push(ThresholdMapping {
                        bdd_var,
                        threshold,
                    });
                    bdd_var_count += 1;
                }
                numeric_mappings.insert(var_name.clone(), mappings);
            }

            // Symbol enums: create x_eq_symbol boolean variables
            if let Some(symbols) = disc.symbol_enums.get(var_name) {
                let mut sym_map = HashMap::new();
                for sym in symbols {
                    let bdd_name = format!("{}_eq_{}", var_name, sym);
                    let bdd_var = builder.make_variable(&bdd_name);
                    sym_map.insert(sym.clone(), bdd_var);
                    bdd_var_count += 1;
                }
                symbol_mappings.insert(var_name.clone(), sym_map);
            }

            // Boolean variables
            if disc.boolean_vars.contains(var_name) {
                let bdd_name = format!("{}_true", var_name);
                let bdd_var = builder.make_variable(&bdd_name);
                boolean_mappings.insert(var_name.clone(), bdd_var);
                bdd_var_count += 1;
            }

            // Assigned variables
            if disc.assigned_vars.contains(var_name) {
                let bdd_name = format!("{}_assigned", var_name);
                let bdd_var = builder.make_variable(&bdd_name);
                assigned_mappings.insert(var_name.clone(), bdd_var);
                bdd_var_count += 1;
            }

            // Empty variables
            if disc.empty_vars.contains(var_name) {
                let bdd_name = format!("{}_empty", var_name);
                let bdd_var = builder.make_variable(&bdd_name);
                empty_mappings.insert(var_name.clone(), bdd_var);
                bdd_var_count += 1;
            }
        }

        let vars = builder.build();

        // Build ordering constraints
        let ordering_bdd = build_ordering_constraints(
            &vars,
            &numeric_mappings,
            &symbol_mappings,
        );

        VerifierContext {
            vars,
            numeric_mappings,
            symbol_mappings,
            boolean_mappings,
            assigned_mappings,
            empty_mappings,
            ordering_bdd,
            input_variables,
            bdd_var_count,
        }
    }

    /// Number of input variables.
    pub fn variable_count(&self) -> usize {
        self.input_variables.len()
    }

    /// Number of BDD boolean variables.
    pub fn bdd_variable_count(&self) -> usize {
        self.bdd_var_count
    }

    /// Encode a single condition as a BDD.
    pub fn encode_condition(&self, cond: &ConditionInfo) -> Bdd {
        match cond.kind.as_str() {
            "comparison" => self.encode_comparison(cond),
            "boolean" => self.encode_boolean(cond),
            "membership" => self.encode_membership(cond),
            "is_assigned" => self.encode_assigned(cond),
            "is_empty" => self.encode_empty(cond),
            "not" => {
                if let Some(ref inner) = cond.left {
                    self.encode_condition(inner).not()
                } else {
                    self.vars.mk_true()
                }
            }
            "compound" => self.encode_compound(cond),
            // String conditions, quantified, contains, has_count — skip (always true)
            _ => self.vars.mk_true(),
        }
    }

    /// Encode a full rule: conjunction of all conditions intersected with ordering.
    pub fn encode_rule(&self, rule: &RuleInfo) -> Bdd {
        let mut bdd = self.ordering_bdd.clone();
        for cond in &rule.conditions {
            let cond_bdd = self.encode_condition(cond);
            bdd = bdd.and(&cond_bdd);
        }
        bdd
    }

    fn encode_comparison(&self, cond: &ConditionInfo) -> Bdd {
        let var = match &cond.variable {
            Some(v) => v,
            None => return self.vars.mk_true(),
        };
        let op = match &cond.operator {
            Some(o) => o.as_str(),
            None => return self.vars.mk_true(),
        };

        match op {
            "exceeds" => {
                // x exceeds N → NOT(x_le_N)
                if let Some(val) = cond.value {
                    self.encode_not_le(var, val as i64)
                } else {
                    self.vars.mk_true()
                }
            }
            "is below" => {
                // x is below N → x_le_(N-1)
                if let Some(val) = cond.value {
                    self.encode_le(var, val as i64 - 1)
                } else {
                    self.vars.mk_true()
                }
            }
            "is at least" => {
                // x is at least N → NOT(x_le_(N-1))
                if let Some(val) = cond.value {
                    self.encode_not_le(var, val as i64 - 1)
                } else {
                    self.vars.mk_true()
                }
            }
            "is at most" => {
                // x is at most N → x_le_N
                if let Some(val) = cond.value {
                    self.encode_le(var, val as i64)
                } else {
                    self.vars.mk_true()
                }
            }
            "is between" => {
                // x is between L and H → NOT(x_le_(L-1)) AND x_le_H
                if let (Some(low), Some(high)) = (cond.value, cond.value2) {
                    let not_below = self.encode_not_le(var, low as i64 - 1);
                    let at_most = self.encode_le(var, high as i64);
                    not_below.and(&at_most)
                } else {
                    self.vars.mk_true()
                }
            }
            "is" | "equals" => {
                if let Some(ref sym) = cond.symbol {
                    // Symbol equality: x is :active → x_eq_active
                    self.encode_symbol_eq(var, sym)
                } else if let Some(val) = cond.value {
                    // Numeric equality: x is N → NOT(x_le_(N-1)) AND x_le_N
                    let ival = val as i64;
                    let not_below = self.encode_not_le(var, ival - 1);
                    let at_most = self.encode_le(var, ival);
                    not_below.and(&at_most)
                } else {
                    self.vars.mk_true()
                }
            }
            "is not" => {
                if let Some(ref sym) = cond.symbol {
                    // Symbol inequality: x is not :active → NOT(x_eq_active)
                    self.encode_symbol_eq(var, sym).not()
                } else {
                    self.vars.mk_true()
                }
            }
            _ => self.vars.mk_true(),
        }
    }

    fn encode_boolean(&self, cond: &ConditionInfo) -> Bdd {
        let var = match &cond.variable {
            Some(v) => v,
            None => return self.vars.mk_true(),
        };
        if let Some(bdd_var) = self.boolean_mappings.get(var) {
            let val = cond.bool_value.unwrap_or(true);
            self.vars.mk_literal(*bdd_var, val)
        } else {
            self.vars.mk_true()
        }
    }

    fn encode_membership(&self, cond: &ConditionInfo) -> Bdd {
        let var = match &cond.variable {
            Some(v) => v,
            None => return self.vars.mk_true(),
        };
        let negated = cond.negated.unwrap_or(false);
        if let Some(ref elems) = cond.elements {
            // x in [1, 2, 3] → x_eq_1 OR x_eq_2 OR x_eq_3
            // Encode each element as an exact-value BDD (NOT(x_le_(e-1)) AND x_le_e)
            let mut result = self.vars.mk_false();
            for &e in elems {
                let ival = e as i64;
                let exact = self.encode_not_le(var, ival - 1).and(&self.encode_le(var, ival));
                result = result.or(&exact);
            }
            if negated {
                result.not()
            } else {
                result
            }
        } else {
            self.vars.mk_true()
        }
    }

    fn encode_assigned(&self, cond: &ConditionInfo) -> Bdd {
        let var = match &cond.variable {
            Some(v) => v,
            None => return self.vars.mk_true(),
        };
        let negated = cond.negated.unwrap_or(false);
        if let Some(bdd_var) = self.assigned_mappings.get(var) {
            self.vars.mk_literal(*bdd_var, !negated)
        } else {
            self.vars.mk_true()
        }
    }

    fn encode_empty(&self, cond: &ConditionInfo) -> Bdd {
        let var = match &cond.variable {
            Some(v) => v,
            None => return self.vars.mk_true(),
        };
        let negated = cond.negated.unwrap_or(false);
        if let Some(bdd_var) = self.empty_mappings.get(var) {
            self.vars.mk_literal(*bdd_var, !negated)
        } else {
            self.vars.mk_true()
        }
    }

    fn encode_compound(&self, cond: &ConditionInfo) -> Bdd {
        let op = cond.operator.as_deref().unwrap_or("and");
        let left = cond
            .left
            .as_ref()
            .map(|c| self.encode_condition(c))
            .unwrap_or_else(|| self.vars.mk_true());
        let right = cond
            .right
            .as_ref()
            .map(|c| self.encode_condition(c))
            .unwrap_or_else(|| self.vars.mk_true());
        match op {
            "or" => left.or(&right),
            _ => left.and(&right),
        }
    }

    /// Encode x_le_threshold. Finds the BDD variable for the threshold.
    fn encode_le(&self, var: &str, threshold: i64) -> Bdd {
        if let Some(mappings) = self.numeric_mappings.get(var) {
            // Find exact threshold match
            for m in mappings {
                if m.threshold == threshold {
                    return self.vars.mk_var(m.bdd_var);
                }
            }
            // Threshold not found — find nearest. If threshold is above all thresholds,
            // the condition is always true. If below all, always false.
            if let Some(first) = mappings.first() {
                if threshold < first.threshold {
                    return self.vars.mk_false();
                }
            }
            if let Some(last) = mappings.last() {
                if threshold >= last.threshold {
                    return self.vars.mk_var(last.bdd_var);
                }
            }
            // Find the highest threshold <= the requested one
            for m in mappings.iter().rev() {
                if m.threshold <= threshold {
                    return self.vars.mk_var(m.bdd_var);
                }
            }
            self.vars.mk_true()
        } else {
            // Variable not in numeric thresholds — unconstrained
            self.vars.mk_true()
        }
    }

    /// Encode NOT(x_le_threshold).
    fn encode_not_le(&self, var: &str, threshold: i64) -> Bdd {
        self.encode_le(var, threshold).not()
    }

    /// Encode symbol equality.
    fn encode_symbol_eq(&self, var: &str, symbol: &str) -> Bdd {
        if let Some(sym_map) = self.symbol_mappings.get(var) {
            if let Some(bdd_var) = sym_map.get(symbol) {
                return self.vars.mk_var(*bdd_var);
            }
        }
        self.vars.mk_true()
    }
}

/// Build monotonicity constraints for numeric thresholds and mutual exclusion
/// for symbol enums.
fn build_ordering_constraints(
    vars: &BddVariableSet,
    numeric_mappings: &HashMap<String, Vec<ThresholdMapping>>,
    symbol_mappings: &HashMap<String, HashMap<String, BddVariable>>,
) -> Bdd {
    let mut ordering = vars.mk_true();

    // Monotonicity: for each variable, x_le_a implies x_le_b when a < b
    for mappings in numeric_mappings.values() {
        for i in 0..mappings.len().saturating_sub(1) {
            let a = mappings[i].bdd_var;
            let b = mappings[i + 1].bdd_var;
            // a_le_X → b_le_Y  ≡  NOT(a_le_X) OR b_le_Y
            let implication = vars.mk_var(a).imp(&vars.mk_var(b));
            ordering = ordering.and(&implication);
        }
    }

    // Mutual exclusion: for symbol enums, at most one can be true
    for sym_map in symbol_mappings.values() {
        let sym_vars: Vec<BddVariable> = sym_map.values().copied().collect();
        // Pairwise exclusion: NOT(x_eq_a AND x_eq_b) for all pairs
        for i in 0..sym_vars.len() {
            for j in (i + 1)..sym_vars.len() {
                let not_both = vars
                    .mk_var(sym_vars[i])
                    .and(&vars.mk_var(sym_vars[j]))
                    .not();
                ordering = ordering.and(&not_both);
            }
        }
    }

    ordering
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::verifier::{ActionInfo, ConditionInfo, RuleInfo};

    fn make_action() -> ActionInfo {
        ActionInfo {
            kind: "set".to_string(),
            target: Some("result".to_string()),
            value: Some("true".to_string()),
        }
    }

    fn make_comparison(var: &str, op: &str, val: f64) -> ConditionInfo {
        ConditionInfo {
            kind: "comparison".to_string(),
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

    fn make_between(var: &str, low: f64, high: f64) -> ConditionInfo {
        ConditionInfo {
            kind: "comparison".to_string(),
            variable: Some(var.to_string()),
            operator: Some("is between".to_string()),
            value: Some(low),
            value2: Some(high),
            symbol: None,
            bool_value: None,
            elements: None,
            negated: None,
            left: None,
            right: None,
        }
    }

    fn make_symbol_eq(var: &str, sym: &str) -> ConditionInfo {
        ConditionInfo {
            kind: "comparison".to_string(),
            variable: Some(var.to_string()),
            operator: Some("is".to_string()),
            value: None,
            value2: None,
            symbol: Some(sym.to_string()),
            bool_value: None,
            elements: None,
            negated: None,
            left: None,
            right: None,
        }
    }

    fn make_bool_cond(var: &str, val: bool) -> ConditionInfo {
        ConditionInfo {
            kind: "boolean".to_string(),
            variable: Some(var.to_string()),
            operator: None,
            value: None,
            value2: None,
            symbol: None,
            bool_value: Some(val),
            elements: None,
            negated: None,
            left: None,
            right: None,
        }
    }

    fn make_rule(name: &str, conditions: Vec<ConditionInfo>) -> RuleInfo {
        RuleInfo {
            name: name.to_string(),
            priority: 0,
            conditions,
            action: make_action(),
            read_vars: vec![],
            write_vars: vec![],
        }
    }

    #[test]
    fn test_exceeds_encoding() {
        let rules = vec![make_rule("r1", vec![make_comparison("x", "exceeds", 100.0)])];
        let ctx = VerifierContext::from_rules(&rules);
        let bdd = ctx.encode_rule(&rules[0]);
        // Should be satisfiable (x > 100 is possible)
        assert!(!bdd.is_false(), "x exceeds 100 should be satisfiable");
    }

    #[test]
    fn test_dead_rule_detection() {
        // x > 100 AND x < 50 → unsatisfiable
        let rules = vec![make_rule(
            "dead",
            vec![
                make_comparison("x", "exceeds", 100.0),
                make_comparison("x", "is below", 50.0),
            ],
        )];
        let ctx = VerifierContext::from_rules(&rules);
        let bdd = ctx.encode_rule(&rules[0]);
        assert!(bdd.is_false(), "x > 100 AND x < 50 should be unsatisfiable");
    }

    #[test]
    fn test_between_encoding() {
        let rules = vec![make_rule("r1", vec![make_between("x", 10.0, 90.0)])];
        let ctx = VerifierContext::from_rules(&rules);
        let bdd = ctx.encode_rule(&rules[0]);
        assert!(!bdd.is_false(), "x between 10 and 90 should be satisfiable");
    }

    #[test]
    fn test_symbol_equality() {
        let rules = vec![
            make_rule("r1", vec![make_symbol_eq("status", "active")]),
            make_rule("r2", vec![make_symbol_eq("status", "inactive")]),
        ];
        let ctx = VerifierContext::from_rules(&rules);
        let bdd1 = ctx.encode_rule(&rules[0]);
        let bdd2 = ctx.encode_rule(&rules[1]);
        // Both should be individually satisfiable
        assert!(!bdd1.is_false());
        assert!(!bdd2.is_false());
        // They should be mutually exclusive (symbol mutual exclusion)
        let overlap = bdd1.and(&bdd2);
        assert!(overlap.is_false(), "status=active AND status=inactive should be impossible");
    }

    #[test]
    fn test_boolean_encoding() {
        let rules = vec![
            make_rule("r1", vec![make_bool_cond("flag", true)]),
            make_rule("r2", vec![make_bool_cond("flag", false)]),
        ];
        let ctx = VerifierContext::from_rules(&rules);
        let bdd1 = ctx.encode_rule(&rules[0]);
        let bdd2 = ctx.encode_rule(&rules[1]);
        // Both satisfiable
        assert!(!bdd1.is_false());
        assert!(!bdd2.is_false());
        // Mutually exclusive
        assert!(bdd1.and(&bdd2).is_false());
    }

    #[test]
    fn test_compound_and() {
        let rules = vec![make_rule(
            "r1",
            vec![ConditionInfo {
                kind: "compound".to_string(),
                variable: None,
                operator: Some("and".to_string()),
                value: None,
                value2: None,
                symbol: None,
                bool_value: None,
                elements: None,
                negated: None,
                left: Some(Box::new(make_comparison("x", "exceeds", 10.0))),
                right: Some(Box::new(make_comparison("x", "is below", 50.0))),
            }],
        )];
        let ctx = VerifierContext::from_rules(&rules);
        let bdd = ctx.encode_rule(&rules[0]);
        assert!(!bdd.is_false(), "x > 10 AND x < 50 should be satisfiable");
    }

    #[test]
    fn test_compound_or() {
        let rules = vec![make_rule(
            "r1",
            vec![ConditionInfo {
                kind: "compound".to_string(),
                variable: None,
                operator: Some("or".to_string()),
                value: None,
                value2: None,
                symbol: None,
                bool_value: None,
                elements: None,
                negated: None,
                left: Some(Box::new(make_comparison("x", "exceeds", 100.0))),
                right: Some(Box::new(make_comparison("x", "is below", 50.0))),
            }],
        )];
        let ctx = VerifierContext::from_rules(&rules);
        let bdd = ctx.encode_rule(&rules[0]);
        assert!(!bdd.is_false(), "x > 100 OR x < 50 should be satisfiable");
    }

    #[test]
    fn test_ordering_monotonicity() {
        // Create rules that force multiple thresholds on same variable
        let rules = vec![
            make_rule("r1", vec![make_comparison("x", "exceeds", 10.0)]),
            make_rule("r2", vec![make_comparison("x", "exceeds", 50.0)]),
        ];
        let ctx = VerifierContext::from_rules(&rules);
        // x > 50 should imply x > 10
        let bdd_gt_50 = ctx.encode_rule(&rules[1]);
        let bdd_gt_10 = ctx.encode_rule(&rules[0]);
        // Everything satisfying x > 50 should also satisfy x > 10
        let gt50_and_not_gt10 = bdd_gt_50.and_not(&bdd_gt_10);
        assert!(
            gt50_and_not_gt10.is_false(),
            "x > 50 AND NOT(x > 10) should be impossible with ordering"
        );
    }

    #[test]
    fn test_not_condition() {
        let rules = vec![make_rule(
            "r1",
            vec![ConditionInfo {
                kind: "not".to_string(),
                variable: None,
                operator: None,
                value: None,
                value2: None,
                symbol: None,
                bool_value: None,
                elements: None,
                negated: None,
                left: Some(Box::new(make_comparison("x", "exceeds", 100.0))),
                right: None,
            }],
        )];
        let ctx = VerifierContext::from_rules(&rules);
        let bdd = ctx.encode_rule(&rules[0]);
        assert!(!bdd.is_false(), "NOT(x > 100) should be satisfiable");
    }
}
