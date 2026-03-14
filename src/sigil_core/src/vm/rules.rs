//! Forward chaining rule engine for the VM.

use std::collections::HashSet;

use super::chunk::RuleInfo;
use super::engine::Engine;

/// Maximum forward chaining iterations.
const MAX_ITERATIONS: usize = 100;

/// Run forward chaining: iterate rules until fixed point.
pub fn run_forward_chaining(engine: &mut Engine) -> Result<(), String> {
    let mut rules: Vec<RuleInfo> = engine.chunk.rules.clone();
    // Sort by priority descending
    rules.sort_by(|a, b| b.priority.cmp(&a.priority));

    let mut fired_rules: HashSet<String> = HashSet::new();

    for _iteration in 0..MAX_ITERATIONS {
        let mut any_fired = false;

        for rule in &rules {
            if fired_rules.contains(&rule.name) {
                continue;
            }

            // Evaluate conditions by running bytecode from cond_offset
            let cond_result = engine.execute_from(rule.cond_offset)?;

            if cond_result {
                // Execute action block
                engine.execute_from_void(rule.action_offset)?;

                // Explain strings are recorded in trace, NOT output_lines
                // (matching tree-walker behavior)

                fired_rules.insert(rule.name.clone());
                any_fired = true;
            }
        }

        if !any_fired {
            break; // Fixed point reached
        }
    }

    Ok(())
}
