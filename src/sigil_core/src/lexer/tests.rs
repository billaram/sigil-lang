//! Lexer tests — ported from tests/lexer/test_lexer.py

use super::scanner::tokenize;
use super::tokens::TokenType;

fn types(source: &str) -> Vec<TokenType> {
    tokenize(source).unwrap().iter().map(|t| t.token_type).collect()
}

// --- Keywords ---

#[test]
fn test_keywords() {
    let tokens = tokenize("rule when then and or not").unwrap();
    let tt: Vec<_> = tokens.iter().map(|t| t.token_type).collect();
    assert_eq!(tt[0], TokenType::Rule);
    assert_eq!(tt[1], TokenType::When);
    assert_eq!(tt[2], TokenType::Then);
    assert_eq!(tt[3], TokenType::And);
    assert_eq!(tt[4], TokenType::Or);
    assert_eq!(tt[5], TokenType::Not);
}

#[test]
fn test_more_keywords() {
    let tokens = tokenize("if else given define as is").unwrap();
    let tt: Vec<_> = tokens.iter().map(|t| t.token_type).collect();
    assert_eq!(tt[0], TokenType::If);
    assert_eq!(tt[1], TokenType::Else);
    assert_eq!(tt[2], TokenType::Given);
    assert_eq!(tt[3], TokenType::Define);
    assert_eq!(tt[4], TokenType::As);
    assert_eq!(tt[5], TokenType::Is);
}

#[test]
fn test_compute_keywords() {
    let tt = types("compute return match for each evaluate main");
    assert_eq!(tt[0], TokenType::Compute);
    assert_eq!(tt[1], TokenType::Return);
    assert_eq!(tt[2], TokenType::Match);
    assert_eq!(tt[3], TokenType::For);
    assert_eq!(tt[4], TokenType::Each);
    assert_eq!(tt[5], TokenType::Evaluate);
    assert_eq!(tt[6], TokenType::Main);
}

// --- Numbers ---

#[test]
fn test_integer() {
    let tokens = tokenize("42").unwrap();
    assert_eq!(tokens[0].token_type, TokenType::Number);
    assert_eq!(tokens[0].value, "42");
}

#[test]
fn test_float() {
    let tokens = tokenize("3.14").unwrap();
    assert_eq!(tokens[0].token_type, TokenType::Number);
    assert_eq!(tokens[0].value, "3.14");
}

#[test]
fn test_number_with_unit() {
    let tokens = tokenize("100 degrees").unwrap();
    assert_eq!(tokens[0].token_type, TokenType::Number);
    assert_eq!(tokens[0].value, "100");
    assert_eq!(tokens[1].token_type, TokenType::Unit);
    assert_eq!(tokens[1].value, "degrees");
}

#[test]
fn test_number_with_percent_unit() {
    let tokens = tokenize("85 percent").unwrap();
    assert_eq!(tokens[0].token_type, TokenType::Number);
    assert_eq!(tokens[1].token_type, TokenType::Unit);
    assert_eq!(tokens[1].value, "percent");
}

// --- Strings ---

#[test]
fn test_simple_string() {
    let tokens = tokenize("\"hello world\"").unwrap();
    assert_eq!(tokens[0].token_type, TokenType::String);
    assert_eq!(tokens[0].value, "hello world");
}

#[test]
fn test_string_escapes() {
    let tokens = tokenize("\"line1\\nline2\"").unwrap();
    assert_eq!(tokens[0].value, "line1\nline2");
}

#[test]
fn test_triple_quoted_string() {
    let tokens = tokenize("\"\"\"multi\nline\"\"\"").unwrap();
    assert_eq!(tokens[0].token_type, TokenType::String);
    assert_eq!(tokens[0].value, "multi\nline");
}

// --- Symbols ---

#[test]
fn test_symbol() {
    let tokens = tokenize(":active").unwrap();
    assert_eq!(tokens[0].token_type, TokenType::Symbol);
    assert_eq!(tokens[0].value, "active");
}

#[test]
fn test_symbol_with_underscore() {
    let tokens = tokenize(":high_risk").unwrap();
    assert_eq!(tokens[0].token_type, TokenType::Symbol);
    assert_eq!(tokens[0].value, "high_risk");
}

// --- Operators ---

#[test]
fn test_arithmetic_operators() {
    let tt = types("+ - * /");
    assert_eq!(tt[0], TokenType::Plus);
    assert_eq!(tt[1], TokenType::Minus);
    assert_eq!(tt[2], TokenType::Star);
    assert_eq!(tt[3], TokenType::Slash);
}

#[test]
fn test_comparison_operators() {
    let tt = types("> < >= <= = !=");
    assert_eq!(tt[0], TokenType::Gt);
    assert_eq!(tt[1], TokenType::Lt);
    assert_eq!(tt[2], TokenType::Gte);
    assert_eq!(tt[3], TokenType::Lte);
    assert_eq!(tt[4], TokenType::Eq);
    assert_eq!(tt[5], TokenType::Neq);
}

#[test]
fn test_pipe_operator() {
    let tt = types("|>");
    assert_eq!(tt[0], TokenType::Pipe);
}

#[test]
fn test_arrow_operator() {
    let tt = types("->");
    assert_eq!(tt[0], TokenType::Arrow);
}

#[test]
fn test_double_colon() {
    let tt = types("::");
    assert_eq!(tt[0], TokenType::DoubleColon);
}

// --- Delimiters ---

#[test]
fn test_delimiters() {
    let tt = types("( ) [ ] { } : ,");
    assert_eq!(tt[0], TokenType::LParen);
    assert_eq!(tt[1], TokenType::RParen);
    assert_eq!(tt[2], TokenType::LBracket);
    assert_eq!(tt[3], TokenType::RBracket);
    assert_eq!(tt[4], TokenType::LBrace);
    assert_eq!(tt[5], TokenType::RBrace);
    assert_eq!(tt[6], TokenType::Colon);
    assert_eq!(tt[7], TokenType::Comma);
}

// --- Identifiers ---

#[test]
fn test_identifier() {
    let tokens = tokenize("my_var").unwrap();
    assert_eq!(tokens[0].token_type, TokenType::Identifier);
    assert_eq!(tokens[0].value, "my_var");
}

// --- Indentation ---

#[test]
fn test_indent_dedent() {
    let source = "rule x:\n  when a\n  then b\n";
    let tokens = tokenize(source).unwrap();
    let tt: Vec<_> = tokens.iter().map(|t| t.token_type).collect();
    assert!(tt.contains(&TokenType::Indent));
    assert!(tt.contains(&TokenType::Dedent));
}

#[test]
fn test_nested_indent() {
    let source = "if x:\n  if y:\n    z\n";
    let tokens = tokenize(source).unwrap();
    let indent_count = tokens.iter().filter(|t| t.token_type == TokenType::Indent).count();
    let dedent_count = tokens.iter().filter(|t| t.token_type == TokenType::Dedent).count();
    assert_eq!(indent_count, 2);
    assert_eq!(dedent_count, 2);
}

// --- Comments ---

#[test]
fn test_single_line_comment() {
    let tokens = tokenize("x -- this is a comment\ny").unwrap();
    let vals: Vec<_> = tokens.iter()
        .filter(|t| t.token_type == TokenType::Identifier)
        .map(|t| t.value.as_str())
        .collect();
    assert_eq!(vals, vec!["x", "y"]);
}

#[test]
fn test_doc_comment() {
    let tokens = tokenize("--- This is doc\nx").unwrap();
    let doc = tokens.iter().find(|t| t.token_type == TokenType::DocComment);
    assert!(doc.is_some());
    assert_eq!(doc.unwrap().value, "This is doc");
}

#[test]
fn test_multiline_comment() {
    let tokens = tokenize("x {- comment -} y").unwrap();
    let ids: Vec<_> = tokens.iter()
        .filter(|t| t.token_type == TokenType::Identifier)
        .map(|t| t.value.as_str())
        .collect();
    assert_eq!(ids, vec!["x", "y"]);
}

#[test]
fn test_nested_multiline_comment() {
    let tokens = tokenize("x {- outer {- inner -} outer -} y").unwrap();
    let ids: Vec<_> = tokens.iter()
        .filter(|t| t.token_type == TokenType::Identifier)
        .map(|t| t.value.as_str())
        .collect();
    assert_eq!(ids, vec!["x", "y"]);
}

// --- Booleans ---

#[test]
fn test_true_false() {
    let tt = types("true false");
    assert_eq!(tt[0], TokenType::True);
    assert_eq!(tt[1], TokenType::False);
}

// --- EOF ---

#[test]
fn test_eof() {
    let tokens = tokenize("").unwrap();
    assert_eq!(tokens.last().unwrap().token_type, TokenType::Eof);
}

// --- Error cases ---

#[test]
fn test_tab_error() {
    let result = tokenize("\tx");
    assert!(result.is_err());
    assert!(result.unwrap_err().contains("Tabs are not allowed"));
}

#[test]
fn test_unterminated_string() {
    let result = tokenize("\"hello");
    assert!(result.is_err());
}

#[test]
fn test_unterminated_multiline_comment() {
    let result = tokenize("{- unclosed");
    assert!(result.is_err());
}

// --- Line/column tracking ---

#[test]
fn test_line_column() {
    let tokens = tokenize("x\ny").unwrap();
    let x = &tokens[0];
    assert_eq!(x.line, 1);
    assert_eq!(x.column, 1);
    let y = tokens.iter().find(|t| t.value == "y").unwrap();
    assert_eq!(y.line, 2);
}

// --- Full program ---

#[test]
fn test_simple_rule() {
    let source = "rule check_temp:\n  when temperature exceeds 100\n  then trigger alert\n";
    let tokens = tokenize(source).unwrap();
    let tt: Vec<_> = tokens.iter().map(|t| t.token_type).collect();
    assert!(tt.contains(&TokenType::Rule));
    assert!(tt.contains(&TokenType::When));
    assert!(tt.contains(&TokenType::Exceeds));
    assert!(tt.contains(&TokenType::Then));
}

#[test]
fn test_define_const() {
    let source = "define MAX as 100";
    let tokens = tokenize(source).unwrap();
    assert_eq!(tokens[0].token_type, TokenType::Define);
    assert_eq!(tokens[1].token_type, TokenType::Identifier);
    assert_eq!(tokens[2].token_type, TokenType::As);
    assert_eq!(tokens[3].token_type, TokenType::Number);
}
