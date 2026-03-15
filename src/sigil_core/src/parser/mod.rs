//! Sigil parser — converts token stream into AST.

pub mod ast;
pub mod parser;

pub use ast::*;
pub use parser::parse;

#[cfg(test)]
mod tests;
