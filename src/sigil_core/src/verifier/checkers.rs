//! Verification checkers: completeness, dead rules, conflicts, termination.
//!
//! Each checker takes encoded BDDs and returns structured results.

use biodivine_lib_bdd::Bdd;
use std::collections::{HashMap, HashSet};

use super::encoder::VerifierContext;
use super::report::{CompletenessResult, ConflictResult, DeadRuleResult, TerminationResult};
use super::witness::decode_witness;
use super::RuleInfo;

/// Check whether the union of all rules covers the entire valid input space.
pub fn check_completeness(ctx: &VerifierContext, rule_bdds: &[Bdd]) -> CompletenessResult {
    // Coverage = union of all rule BDDs
    let mut coverage = ctx.vars.mk_false();
    for bdd in rule_bdds {
        coverage = coverage.or(bdd);
    }

    // Uncovered = valid inputs not matched by any rule
    let uncovered = ctx.ordering_bdd.and_not(&coverage);

    if uncovered.is_false() {
        CompletenessResult {
            is_complete: true,
            coverage_percent: 100.0,
            witness: None,
        }
    } else {
        // Estimate coverage percentage via BDD node ratio
        let coverage_percent = estimate_coverage(&ctx.ordering_bdd, &coverage);
        let witness = uncovered
            .sat_valuations()
            .next()
            .map(|v| decode_witness(ctx, &v));
        CompletenessResult {
            is_complete: false,
            coverage_percent,
            witness,
        }
    }
}

/// Check which rules have unsatisfiable conditions (dead rules).
pub fn check_dead_rules(rules: &[RuleInfo], rule_bdds: &[Bdd]) -> Vec<DeadRuleResult> {
    rules
        .iter()
        .zip(rule_bdds)
        .map(|(rule, bdd)| DeadRuleResult {
            rule_name: rule.name.clone(),
            is_dead: bdd.is_false(),
        })
        .collect()
}

/// Check for conflicting rule pairs.
///
/// Two rules conflict if:
/// 1. They can both fire on the same input (overlapping conditions)
/// 2. They write to the same target with different values
/// 3. They have the same priority (no resolution)
pub fn check_conflicts(
    ctx: &VerifierContext,
    rules: &[RuleInfo],
    rule_bdds: &[Bdd],
) -> Vec<ConflictResult> {
    let mut conflicts = Vec::new();
    let n = rules.len();

    for i in 0..n {
        for j in (i + 1)..n {
            // Same action → no conflict
            if rules[i].action == rules[j].action {
                continue;
            }
            // Different targets → no conflict (rules set different variables)
            if rules[i].action.target != rules[j].action.target {
                continue;
            }
            // Different priority → resolved by priority
            if rules[i].priority != rules[j].priority {
                continue;
            }
            // Check overlap
            let overlap = rule_bdds[i].and(&rule_bdds[j]);
            if !overlap.is_false() {
                let witness = overlap
                    .sat_valuations()
                    .next()
                    .map(|v| decode_witness(ctx, &v));
                conflicts.push(ConflictResult {
                    rule_a: rules[i].name.clone(),
                    rule_b: rules[j].name.clone(),
                    witness,
                });
            }
        }
    }
    conflicts
}

/// Check termination by analyzing read/write variable dependencies.
///
/// Builds a dependency graph: if rule A writes variable X, and rule B reads X
/// and writes Y, there's an edge A→B. Cycles in this graph indicate
/// potential non-termination (forward chaining may loop).
pub fn check_termination(rules: &[RuleInfo]) -> TerminationResult {
    // Build write→read dependency graph on variables
    // Node: variable name
    // Edge: X → Y if some rule reads X and writes Y
    let mut edges: HashMap<String, HashSet<String>> = HashMap::new();

    for rule in rules {
        for read_var in &rule.read_vars {
            for write_var in &rule.write_vars {
                if read_var != write_var {
                    edges
                        .entry(read_var.clone())
                        .or_default()
                        .insert(write_var.clone());
                }
            }
        }
        // Self-loops: rule reads and writes the same variable
        for read_var in &rule.read_vars {
            if rule.write_vars.contains(read_var) {
                edges
                    .entry(read_var.clone())
                    .or_default()
                    .insert(read_var.clone());
            }
        }
    }

    let cycles = find_cycles(&edges);
    TerminationResult {
        terminates: cycles.is_empty(),
        cycles,
    }
}

/// Find all cycles in a directed graph using DFS.
fn find_cycles(edges: &HashMap<String, HashSet<String>>) -> Vec<Vec<String>> {
    let mut cycles = Vec::new();
    let mut visited: HashSet<String> = HashSet::new();
    let mut on_stack: HashSet<String> = HashSet::new();
    let mut path: Vec<String> = Vec::new();

    let all_nodes: HashSet<&String> = edges
        .keys()
        .chain(edges.values().flat_map(|s| s.iter()))
        .collect();

    for node in all_nodes {
        if !visited.contains(node) {
            dfs_find_cycles(
                node,
                edges,
                &mut visited,
                &mut on_stack,
                &mut path,
                &mut cycles,
            );
        }
    }
    cycles
}

fn dfs_find_cycles(
    node: &str,
    edges: &HashMap<String, HashSet<String>>,
    visited: &mut HashSet<String>,
    on_stack: &mut HashSet<String>,
    path: &mut Vec<String>,
    cycles: &mut Vec<Vec<String>>,
) {
    visited.insert(node.to_string());
    on_stack.insert(node.to_string());
    path.push(node.to_string());

    if let Some(neighbors) = edges.get(node) {
        for neighbor in neighbors {
            if !visited.contains(neighbor) {
                dfs_find_cycles(neighbor, edges, visited, on_stack, path, cycles);
            } else if on_stack.contains(neighbor) {
                // Found a cycle — extract it from path
                if let Some(start_idx) = path.iter().position(|n| n == neighbor) {
                    let cycle: Vec<String> = path[start_idx..].to_vec();
                    cycles.push(cycle);
                }
            }
        }
    }

    on_stack.remove(node);
    path.pop();
}

/// Estimate coverage percentage using BDD satisfying-assignment counting.
fn estimate_coverage(universe: &Bdd, coverage: &Bdd) -> f64 {
    let universe_count = universe.cardinality();
    if universe_count == 0.0 {
        return 100.0;
    }
    let covered_count = coverage.and(universe).cardinality();
    (covered_count / universe_count * 100.0).min(100.0)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::verifier::{ActionInfo, ConditionInfo, RuleInfo};
    use crate::verifier::encoder::VerifierContext;

    fn make_action(val: &str) -> ActionInfo {
        ActionInfo {
            kind: "set".to_string(),
            target: Some("result".to_string()),
            value: Some(val.to_string()),
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

    fn make_rule(name: &str, conditions: Vec<ConditionInfo>, action: ActionInfo) -> RuleInfo {
        RuleInfo {
            name: name.to_string(),
            priority: 0,
            conditions,
            action,
            read_vars: vec![],
            write_vars: vec![],
        }
    }

    #[test]
    fn test_completeness_complete_rules() {
        // x > 50 OR x <= 50 covers everything
        let rules = vec![
            make_rule(
                "high",
                vec![make_comparison("x", "exceeds", 50.0)],
                make_action("high"),
            ),
            make_rule(
                "low",
                vec![make_comparison("x", "is at most", 50.0)],
                make_action("low"),
            ),
        ];
        let ctx = VerifierContext::from_rules(&rules);
        let rule_bdds: Vec<_> = rules.iter().map(|r| ctx.encode_rule(r)).collect();
        let result = check_completeness(&ctx, &rule_bdds);
        assert!(result.is_complete, "x > 50 OR x <= 50 should be complete");
    }

    #[test]
    fn test_completeness_incomplete_rules() {
        // Only x > 50 — leaves x <= 50 uncovered
        let rules = vec![make_rule(
            "high",
            vec![make_comparison("x", "exceeds", 50.0)],
            make_action("high"),
        )];
        let ctx = VerifierContext::from_rules(&rules);
        let rule_bdds: Vec<_> = rules.iter().map(|r| ctx.encode_rule(r)).collect();
        let result = check_completeness(&ctx, &rule_bdds);
        assert!(!result.is_complete, "only x > 50 should be incomplete");
        assert!(result.witness.is_some(), "should provide witness");
    }

    #[test]
    fn test_dead_rule() {
        // x > 100 AND x < 50 is unsatisfiable
        let rules = vec![make_rule(
            "dead",
            vec![
                make_comparison("x", "exceeds", 100.0),
                make_comparison("x", "is below", 50.0),
            ],
            make_action("never"),
        )];
        let ctx = VerifierContext::from_rules(&rules);
        let rule_bdds: Vec<_> = rules.iter().map(|r| ctx.encode_rule(r)).collect();
        let result = check_dead_rules(&rules, &rule_bdds);
        assert_eq!(result.len(), 1);
        assert!(result[0].is_dead, "x > 100 AND x < 50 should be dead");
    }

    #[test]
    fn test_conflict_detection() {
        // Two rules: both fire when x > 50, different actions, same priority
        let rules = vec![
            make_rule(
                "r1",
                vec![make_comparison("x", "exceeds", 50.0)],
                make_action("action_a"),
            ),
            make_rule(
                "r2",
                vec![make_comparison("x", "exceeds", 50.0)],
                make_action("action_b"),
            ),
        ];
        let ctx = VerifierContext::from_rules(&rules);
        let rule_bdds: Vec<_> = rules.iter().map(|r| ctx.encode_rule(r)).collect();
        let result = check_conflicts(&ctx, &rules, &rule_bdds);
        assert_eq!(result.len(), 1, "should detect one conflict");
        assert_eq!(result[0].rule_a, "r1");
        assert_eq!(result[0].rule_b, "r2");
    }

    #[test]
    fn test_no_conflict_different_priority() {
        // Different priority → resolved
        let rules = vec![
            RuleInfo {
                name: "r1".to_string(),
                priority: 10,
                conditions: vec![make_comparison("x", "exceeds", 50.0)],
                action: make_action("action_a"),
                read_vars: vec![],
                write_vars: vec![],
            },
            RuleInfo {
                name: "r2".to_string(),
                priority: 5,
                conditions: vec![make_comparison("x", "exceeds", 50.0)],
                action: make_action("action_b"),
                read_vars: vec![],
                write_vars: vec![],
            },
        ];
        let ctx = VerifierContext::from_rules(&rules);
        let rule_bdds: Vec<_> = rules.iter().map(|r| ctx.encode_rule(r)).collect();
        let result = check_conflicts(&ctx, &rules, &rule_bdds);
        assert!(result.is_empty(), "different priority should resolve conflict");
    }

    #[test]
    fn test_termination_no_cycles() {
        let rules = vec![RuleInfo {
            name: "r1".to_string(),
            priority: 0,
            conditions: vec![],
            action: make_action("done"),
            read_vars: vec!["x".into()],
            write_vars: vec!["y".into()],
        }];
        let result = check_termination(&rules);
        assert!(result.terminates, "no cycles should mean termination");
    }

    #[test]
    fn test_termination_with_cycle() {
        // r1 reads x, writes y; r2 reads y, writes x → cycle
        let rules = vec![
            RuleInfo {
                name: "r1".to_string(),
                priority: 0,
                conditions: vec![],
                action: make_action("a"),
                read_vars: vec!["x".into()],
                write_vars: vec!["y".into()],
            },
            RuleInfo {
                name: "r2".to_string(),
                priority: 0,
                conditions: vec![],
                action: make_action("b"),
                read_vars: vec!["y".into()],
                write_vars: vec!["x".into()],
            },
        ];
        let result = check_termination(&rules);
        assert!(!result.terminates, "cycle should mean non-termination");
        assert!(!result.cycles.is_empty(), "should report cycle");
    }

    #[test]
    fn test_termination_self_loop() {
        // Rule reads and writes same variable
        let rules = vec![RuleInfo {
            name: "r1".to_string(),
            priority: 0,
            conditions: vec![],
            action: make_action("a"),
            read_vars: vec!["x".into()],
            write_vars: vec!["x".into()],
        }];
        let result = check_termination(&rules);
        assert!(!result.terminates, "self-loop should mean non-termination");
    }
}
