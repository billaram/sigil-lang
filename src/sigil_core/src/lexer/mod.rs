//! Sigil lexer — tokenizes source code into a stream of tokens.

pub mod tokens;
pub mod scanner;

pub use tokens::{Token, TokenType};
pub use scanner::tokenize;

#[cfg(test)]
mod tests;
