//! WASM bindings for the Sigil runtime.
//!
//! Provides a `SigilRuntime` struct exported via wasm-bindgen that
//! runs the full pipeline: source → lex → parse → compile → VM execute.

use wasm_bindgen::prelude::*;

use crate::compiler;
use crate::lexer;
use crate::parser;
use crate::vm::{Engine, VMValue};

use std::collections::HashMap;
use std::collections::HashSet;

/// Runtime for executing Sigil programs from WASM.
#[wasm_bindgen]
pub struct SigilRuntime {
    programs: Vec<crate::vm::Chunk>,
}

#[wasm_bindgen]
impl SigilRuntime {
    /// Create a new SigilRuntime.
    #[wasm_bindgen(constructor)]
    pub fn new() -> Self {
        SigilRuntime {
            programs: Vec::new(),
        }
    }

    /// Full pipeline: source code + input JSON → result JSON.
    ///
    /// Returns a JSON object with `output_lines`, `result`, `bindings`, and `trace`.
    /// On error, returns a JSON object with an `error` field.
    pub fn run(&self, source: &str, input_json: &str) -> String {
        match self.run_inner(source, input_json) {
            Ok(json) => json,
            Err(e) => format!("{{\"error\":{}}}", serde_json::to_string(&e).unwrap_or_else(|_| format!("\"{}\"", e))),
        }
    }

    /// Compile source code and store it. Returns a program handle (index).
    pub fn compile(&mut self, source: &str) -> Result<usize, JsError> {
        let tokens = lexer::tokenize(source).map_err(|e| JsError::new(&e))?;
        let program = parser::parse(tokens).map_err(|e| JsError::new(&e))?;
        let chunk = compiler::compile(&program);
        let id = self.programs.len();
        self.programs.push(chunk);
        Ok(id)
    }

    /// Execute a previously compiled program with new input.
    pub fn execute(&self, program_id: usize, input_json: &str) -> String {
        if program_id >= self.programs.len() {
            return format!("{{\"error\":\"Invalid program ID: {}\"}}", program_id);
        }
        let chunk = &self.programs[program_id];
        match self.execute_chunk(chunk, input_json) {
            Ok(json) => json,
            Err(e) => format!("{{\"error\":{}}}", serde_json::to_string(&e).unwrap_or_else(|_| format!("\"{}\"", e))),
        }
    }
}

impl SigilRuntime {
    fn run_inner(&self, source: &str, input_json: &str) -> Result<String, String> {
        let tokens = lexer::tokenize(source)?;
        let program = parser::parse(tokens)?;
        let chunk = compiler::compile(&program);
        self.execute_chunk(&chunk, input_json)
    }

    fn execute_chunk(&self, chunk: &crate::vm::Chunk, input_json: &str) -> Result<String, String> {
        let input: HashMap<String, serde_json::Value> =
            serde_json::from_str(input_json).map_err(|e| format!("Invalid input JSON: {}", e))?;

        let mut engine = Engine::new(chunk.clone());

        // Load input bindings
        let mut inputs = HashMap::new();
        for (key, val) in &input {
            inputs.insert(key.clone(), json_to_vmvalue(val));
        }
        engine.load_inputs(inputs);

        let vm_result = engine.run().map_err(|e| format!("VM error: {}", e))?;

        // Build trace: which rules fired + explain strings
        let mut trace_entries = Vec::new();
        let mut fired_rules: HashSet<String> = HashSet::new();

        // Detect fired rules by checking if their action side-effects occurred
        // We reconstruct from the rule definitions + bindings
        for rule in &chunk.rules {
            // Try evaluating the condition to see if this rule would fire
            let mut test_engine = Engine::new(chunk.clone());
            // Copy all bindings from the executed engine
            let bindings = engine.call_stack.all_bindings();
            let mut test_inputs = HashMap::new();
            for (k, v) in &bindings {
                test_inputs.insert(k.clone(), v.clone());
            }
            // Also copy original inputs
            for (key, val) in &input {
                test_inputs.insert(key.clone(), json_to_vmvalue(val));
            }
            test_engine.load_inputs(test_inputs);

            // Check condition
            if let Ok(true) = test_engine.execute_from(rule.cond_offset) {
                let explain = rule.explain_idx
                    .and_then(|idx| chunk.strings.get(idx as usize))
                    .cloned()
                    .unwrap_or_default();

                if !fired_rules.contains(&rule.name) {
                    trace_entries.push(serde_json::json!({
                        "rule": rule.name,
                        "priority": rule.priority,
                        "fired": true,
                        "explain": explain,
                    }));
                    fired_rules.insert(rule.name.clone());
                }
            } else {
                let explain = rule.explain_idx
                    .and_then(|idx| chunk.strings.get(idx as usize))
                    .cloned()
                    .unwrap_or_default();

                trace_entries.push(serde_json::json!({
                    "rule": rule.name,
                    "priority": rule.priority,
                    "fired": false,
                    "explain": explain,
                }));
            }
        }

        // Sort trace by priority descending
        trace_entries.sort_by(|a, b| {
            let pa = a["priority"].as_i64().unwrap_or(0);
            let pb = b["priority"].as_i64().unwrap_or(0);
            pb.cmp(&pa)
        });

        // Collect results
        let mut result = serde_json::Map::new();
        result.insert("output_lines".into(), serde_json::to_value(&engine.output_lines).unwrap());
        result.insert("result".into(), vmvalue_to_json(&vm_result));

        let bindings = engine.call_stack.all_bindings();
        let mut bindings_json = serde_json::Map::new();
        for (k, v) in &bindings {
            bindings_json.insert(k.clone(), vmvalue_to_json(v));
        }
        result.insert("bindings".into(), serde_json::Value::Object(bindings_json));
        result.insert("trace".into(), serde_json::Value::Array(trace_entries));

        serde_json::to_string(&result).map_err(|e| format!("JSON serialization error: {}", e))
    }
}

fn json_to_vmvalue(val: &serde_json::Value) -> VMValue {
    match val {
        serde_json::Value::Null => VMValue::None,
        serde_json::Value::Bool(b) => VMValue::Bool(*b),
        serde_json::Value::Number(n) => {
            if let Some(i) = n.as_i64() {
                VMValue::Int(i)
            } else if let Some(f) = n.as_f64() {
                VMValue::Float(f)
            } else {
                VMValue::None
            }
        }
        serde_json::Value::String(s) => VMValue::Text(s.clone()),
        serde_json::Value::Array(arr) => {
            VMValue::List(arr.iter().map(json_to_vmvalue).collect())
        }
        serde_json::Value::Object(obj) => {
            let fields: HashMap<String, VMValue> = obj
                .iter()
                .map(|(k, v)| (k.clone(), json_to_vmvalue(v)))
                .collect();
            VMValue::Record { type_name: None, fields }
        }
    }
}

fn vmvalue_to_json(val: &VMValue) -> serde_json::Value {
    match val {
        VMValue::Int(n) => serde_json::Value::Number((*n).into()),
        VMValue::Float(f) => serde_json::Number::from_f64(*f)
            .map(serde_json::Value::Number)
            .unwrap_or(serde_json::Value::Null),
        VMValue::Bool(b) => serde_json::Value::Bool(*b),
        VMValue::Text(s) => serde_json::Value::String(s.clone()),
        VMValue::Symbol(s) => serde_json::Value::String(format!(":{}", s)),
        VMValue::None => serde_json::Value::Null,
        VMValue::Unbound => serde_json::Value::Null,
        VMValue::List(items) => {
            serde_json::Value::Array(items.iter().map(vmvalue_to_json).collect())
        }
        VMValue::Record { type_name: _, fields } => {
            let obj: serde_json::Map<String, serde_json::Value> = fields
                .iter()
                .map(|(k, v)| (k.clone(), vmvalue_to_json(v)))
                .collect();
            serde_json::Value::Object(obj)
        }
        VMValue::Variant { variant_name, .. } => serde_json::Value::String(variant_name.clone()),
        VMValue::Closure { .. } => serde_json::Value::String("<closure>".into()),
    }
}
