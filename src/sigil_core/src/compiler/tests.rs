//! Compiler tests — verify AST to bytecode compilation.

use crate::compiler::compile;
use crate::lexer::tokenize;
use crate::parser::parser::parse;
use crate::vm::{Engine, Opcode, VMValue};

use std::collections::HashMap;

fn compile_source(source: &str) -> crate::vm::Chunk {
    let tokens = tokenize(source).unwrap();
    let program = parse(tokens).unwrap();
    compile(&program)
}

fn run(source: &str, inputs: HashMap<String, VMValue>) -> (VMValue, Vec<String>, HashMap<String, VMValue>) {
    let chunk = compile_source(source);
    let mut engine = Engine::new(chunk);
    engine.load_inputs(inputs);
    let result = engine.run().unwrap();
    let output = engine.output_lines.clone();
    let bindings = engine.call_stack.all_bindings();
    (result, output, bindings)
}

// --- Constants ---

#[test]
fn test_compile_const() {
    let chunk = compile_source("define X as 42");
    assert!(chunk.init_offset.is_some());
    assert!(chunk.code.iter().any(|op| matches!(op, Opcode::PushInt(42))));
}

#[test]
fn test_compile_string_const() {
    let chunk = compile_source("define MSG as \"hello\"");
    assert!(chunk.strings.contains(&"hello".to_string()));
}

// --- Compute ---

#[test]
fn test_compile_compute() {
    let source = "compute add from a: Number, b: Number returns Number:\n  return a + b\n";
    let chunk = compile_source(source);
    assert!(chunk.functions.contains_key("add"));
    let func = &chunk.functions["add"];
    assert_eq!(func.param_count, 2);
    assert_eq!(func.param_names, vec!["a", "b"]);
}

// --- Rules ---

#[test]
fn test_compile_rule() {
    let source = "rule check:\n  when x exceeds 10\n  then alert is true\n";
    let chunk = compile_source(source);
    assert_eq!(chunk.rules.len(), 1);
    assert_eq!(chunk.rules[0].name, "check");
}

#[test]
fn test_compile_rule_with_priority() {
    let source = "rule urgent with priority 5:\n  when x is true\n  then y is 1\n";
    let chunk = compile_source(source);
    assert_eq!(chunk.rules[0].priority, 5);
}

#[test]
fn test_compile_rule_with_explain() {
    let source = "rule r:\n  when x exceeds 10\n  then y is 1\n  explain \"threshold exceeded\"\n";
    let chunk = compile_source(source);
    assert!(chunk.rules[0].explain_idx.is_some());
}

// --- Main ---

#[test]
fn test_compile_main() {
    let source = "main:\n  given x as 42\n";
    let chunk = compile_source(source);
    assert!(chunk.main_offset.is_some());
}

// --- End-to-end execution ---

#[test]
fn test_e2e_const_main_print() {
    let source = "define X as 42\nmain:\n  print(X)\n";
    let (_, output, _) = run(source, HashMap::new());
    assert_eq!(output, vec!["42"]);
}

#[test]
fn test_e2e_compute_call() {
    let source = "compute double from n: Number returns Number:\n  return n * 2\nmain:\n  given result as double(21)\n  print(result)\n";
    let (_, output, _) = run(source, HashMap::new());
    assert_eq!(output, vec!["42"]);
}

#[test]
fn test_e2e_simple_arithmetic() {
    let source = "main:\n  given x as 10 + 20\n  print(x)\n";
    let (_, output, _) = run(source, HashMap::new());
    assert_eq!(output, vec!["30"]);
}

#[test]
fn test_e2e_input_binding() {
    let source = "main:\n  given temp from input\n  print(temp)\n";
    let mut inputs = HashMap::new();
    inputs.insert("temp".to_string(), VMValue::Int(98));
    let (_, output, _) = run(source, inputs);
    assert_eq!(output, vec!["98"]);
}

#[test]
fn test_e2e_if_statement() {
    let source = "main:\n  given x as 10\n  if x exceeds 5:\n    print(\"big\")\n  else:\n    print(\"small\")\n";
    let (_, output, _) = run(source, HashMap::new());
    assert_eq!(output, vec!["big"]);
}

#[test]
fn test_e2e_for_loop() {
    let source = "main:\n  given items as [1, 2, 3]\n  for each item in items:\n    print(item)\n";
    let (_, output, _) = run(source, HashMap::new());
    assert_eq!(output, vec!["1", "2", "3"]);
}

#[test]
fn test_e2e_rule_fires() {
    let source = "rule check:\n  when temp exceeds 100\n  then alert is true\n";
    let mut inputs = HashMap::new();
    inputs.insert("temp".to_string(), VMValue::Int(150));
    let (_, _output, bindings) = run(source, inputs);
    match bindings.get("alert") {
        Some(VMValue::Bool(true)) => {}
        _ => panic!("Expected alert to be true, got: {:?}", bindings.get("alert")),
    }
}

#[test]
fn test_e2e_list_operations() {
    let source = "main:\n  given items as [10, 20, 30]\n  given total as len(items)\n  print(total)\n";
    let (_, output, _) = run(source, HashMap::new());
    assert_eq!(output, vec!["3"]);
}

// --- Opcode verification ---

#[test]
fn test_opcodes_for_arithmetic() {
    let chunk = compile_source("define X as 1 + 2");
    assert!(chunk.code.iter().any(|op| matches!(op, Opcode::Add)));
}

#[test]
fn test_opcodes_for_comparison() {
    let chunk = compile_source("rule r:\n  when x exceeds 10\n  then y is 1\n");
    assert!(chunk.code.iter().any(|op| matches!(op, Opcode::CmpExceeds)));
}
