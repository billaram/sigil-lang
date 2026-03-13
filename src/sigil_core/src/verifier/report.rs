//! Verification report types.
//!
//! All result structs are serializable to JSON for the Python bridge.

use serde::Serialize;

/// Full verification report for a rule set.
#[derive(Debug, Serialize)]
pub struct VerificationReport {
    pub completeness: CompletenessResult,
    pub dead_rules: Vec<DeadRuleResult>,
    pub conflicts: Vec<ConflictResult>,
    pub termination: TerminationResult,
    pub rule_count: usize,
    pub variable_count: usize,
    pub bdd_variable_count: usize,
}

impl VerificationReport {
    /// Create an empty report for an empty rule set.
    pub fn empty() -> Self {
        Self {
            completeness: CompletenessResult {
                is_complete: true,
                coverage_percent: 100.0,
                witness: None,
            },
            dead_rules: vec![],
            conflicts: vec![],
            termination: TerminationResult {
                terminates: true,
                cycles: vec![],
            },
            rule_count: 0,
            variable_count: 0,
            bdd_variable_count: 0,
        }
    }
}

/// Result of completeness checking.
#[derive(Debug, Serialize)]
pub struct CompletenessResult {
    /// Whether all valid inputs are covered by at least one rule.
    pub is_complete: bool,
    /// Approximate coverage percentage.
    pub coverage_percent: f64,
    /// If incomplete, a human-readable counterexample.
    pub witness: Option<String>,
}

/// Result of dead rule checking for a single rule.
#[derive(Debug, Serialize)]
pub struct DeadRuleResult {
    pub rule_name: String,
    pub is_dead: bool,
}

/// Result of conflict checking for a pair of rules.
#[derive(Debug, Serialize)]
pub struct ConflictResult {
    pub rule_a: String,
    pub rule_b: String,
    /// Human-readable description of an input that triggers both rules.
    pub witness: Option<String>,
}

/// Result of termination analysis.
#[derive(Debug, Serialize)]
pub struct TerminationResult {
    /// Whether the rule set is guaranteed to terminate.
    pub terminates: bool,
    /// Any detected dependency cycles (each is a list of variable names).
    pub cycles: Vec<Vec<String>>,
}
