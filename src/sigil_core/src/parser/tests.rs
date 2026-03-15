//! Parser tests — ported from tests/parser/test_parser.py

use crate::lexer::tokenize;
use super::parser::parse;
use super::ast::*;

fn parse_source(source: &str) -> Program {
    let tokens = tokenize(source).unwrap();
    parse(tokens).unwrap()
}

// --- Constants ---

#[test]
fn test_parse_const() {
    let prog = parse_source("define MAX as 100");
    assert_eq!(prog.declarations.len(), 1);
    match &prog.declarations[0] {
        Declaration::Const(c) => {
            assert_eq!(c.name, "MAX");
        }
        _ => panic!("Expected ConstDecl"),
    }
}

// --- Compute ---

#[test]
fn test_parse_compute_simple() {
    let source = "compute add from a: Number, b: Number returns Number:\n  return a + b\n";
    let prog = parse_source(source);
    assert_eq!(prog.declarations.len(), 1);
    match &prog.declarations[0] {
        Declaration::Compute(c) => {
            assert_eq!(c.name, "add");
            assert_eq!(c.params.len(), 2);
            assert_eq!(c.params[0].name, "a");
            assert_eq!(c.params[1].name, "b");
        }
        _ => panic!("Expected ComputeDecl"),
    }
}

// --- Rules ---

#[test]
fn test_parse_simple_rule() {
    let source = "rule check_temp:\n  when temperature exceeds 100\n  then alert is true\n";
    let prog = parse_source(source);
    assert_eq!(prog.declarations.len(), 1);
    match &prog.declarations[0] {
        Declaration::Rule(r) => {
            assert_eq!(r.name, "check_temp");
            assert!(!r.conditions.is_empty());
        }
        _ => panic!("Expected RuleDecl"),
    }
}

#[test]
fn test_parse_rule_with_priority() {
    let source = "rule urgent with priority 10:\n  when x is true\n  then y is 1\n";
    let prog = parse_source(source);
    match &prog.declarations[0] {
        Declaration::Rule(r) => {
            assert_eq!(r.priority, 10);
        }
        _ => panic!("Expected RuleDecl"),
    }
}

// --- Main ---

#[test]
fn test_parse_main() {
    let source = "main:\n  given x as 42\n  print(x)\n";
    let prog = parse_source(source);
    let main_count = prog.declarations.iter()
        .filter(|d| matches!(d, Declaration::Main(_)))
        .count();
    assert_eq!(main_count, 1);
}

// --- Expressions ---

#[test]
fn test_parse_binary_op() {
    let source = "define X as 1 + 2";
    let prog = parse_source(source);
    match &prog.declarations[0] {
        Declaration::Const(c) => {
            match &c.value {
                Expression::BinaryOp { operator, .. } => {
                    assert_eq!(operator, "+");
                }
                _ => panic!("Expected BinaryOp"),
            }
        }
        _ => panic!("Expected ConstDecl"),
    }
}

#[test]
fn test_parse_list_literal() {
    let source = "define ITEMS as [1, 2, 3]";
    let prog = parse_source(source);
    match &prog.declarations[0] {
        Declaration::Const(c) => {
            match &c.value {
                Expression::List(items) => {
                    assert_eq!(items.len(), 3);
                }
                _ => panic!("Expected List"),
            }
        }
        _ => panic!("Expected ConstDecl"),
    }
}

#[test]
fn test_parse_symbol_literal() {
    let source = "define STATUS as :active";
    let prog = parse_source(source);
    match &prog.declarations[0] {
        Declaration::Const(c) => {
            match &c.value {
                Expression::Symbol(name) => {
                    assert_eq!(name, "active");
                }
                _ => panic!("Expected Symbol"),
            }
        }
        _ => panic!("Expected ConstDecl"),
    }
}

// --- Types ---

#[test]
fn test_parse_record_type() {
    let source = "type Person is record:\n  name: Text\n  age: Number\n";
    let prog = parse_source(source);
    match &prog.declarations[0] {
        Declaration::Type(t) => {
            assert_eq!(t.name, "Person");
            match &t.body {
                TypeBody::Record(r) => {
                    assert_eq!(r.fields.len(), 2);
                    assert_eq!(r.fields[0].name, "name");
                    assert_eq!(r.fields[1].name, "age");
                }
                _ => panic!("Expected RecordBody"),
            }
        }
        _ => panic!("Expected TypeDecl"),
    }
}

#[test]
fn test_parse_enum_type() {
    let source = "type Status is one of:\n  active\n  inactive\n";
    let prog = parse_source(source);
    match &prog.declarations[0] {
        Declaration::Type(t) => {
            assert_eq!(t.name, "Status");
            match &t.body {
                TypeBody::Enum(e) => {
                    assert!(e.variants.len() >= 2);
                }
                _ => panic!("Expected EnumBody"),
            }
        }
        _ => panic!("Expected TypeDecl"),
    }
}

// --- Conditions ---

#[test]
fn test_parse_exceeds_condition() {
    let source = "rule r:\n  when x exceeds 10\n  then y is 1\n";
    let prog = parse_source(source);
    match &prog.declarations[0] {
        Declaration::Rule(r) => {
            assert!(!r.conditions.is_empty());
            match &r.conditions[0] {
                Condition::Comparison { operator, .. } => {
                    assert_eq!(operator, "exceeds");
                }
                _ => panic!("Expected Comparison condition"),
            }
        }
        _ => panic!("Expected RuleDecl"),
    }
}

#[test]
fn test_parse_between_condition() {
    let source = "rule r:\n  when x is between 10 and 20\n  then y is 1\n";
    let prog = parse_source(source);
    match &prog.declarations[0] {
        Declaration::Rule(r) => {
            match &r.conditions[0] {
                Condition::Comparison { operator, right2, .. } => {
                    assert_eq!(operator, "is between");
                    assert!(right2.is_some());
                }
                _ => panic!("Expected Comparison with between"),
            }
        }
        _ => panic!("Expected RuleDecl"),
    }
}

// --- Statements ---

#[test]
fn test_parse_for_loop() {
    let source = "compute process from items: Number:\n  for each item in items:\n    print(item)\n";
    let prog = parse_source(source);
    match &prog.declarations[0] {
        Declaration::Compute(c) => {
            assert!(!c.body.is_empty());
            match &c.body[0] {
                Statement::For { variable, .. } => {
                    assert_eq!(variable, "item");
                }
                _ => panic!("Expected ForStmt"),
            }
        }
        _ => panic!("Expected ComputeDecl"),
    }
}

#[test]
fn test_parse_if_else() {
    let source = "compute check from x: Number returns Number:\n  if x exceeds 10:\n    return true\n  else:\n    return false\n";
    let prog = parse_source(source);
    match &prog.declarations[0] {
        Declaration::Compute(c) => {
            match &c.body[0] {
                Statement::If { else_body, .. } => {
                    assert!(!else_body.is_empty());
                }
                _ => panic!("Expected IfStmt"),
            }
        }
        _ => panic!("Expected ComputeDecl"),
    }
}

// --- Multiple declarations ---

#[test]
fn test_parse_multiple_declarations() {
    let source = "define X as 10\ndefine Y as 20\n";
    let prog = parse_source(source);
    assert_eq!(prog.declarations.len(), 2);
}

// --- Error cases ---

#[test]
fn test_parse_error_no_colon() {
    let source = "rule bad_rule\n  when x exceeds 10\n";
    let result = parse(tokenize(source).unwrap());
    // Should produce an error
    assert!(result.is_err());
}
