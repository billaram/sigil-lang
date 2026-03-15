//! Token type definitions for the Sigil lexer.

use std::collections::HashMap;
use std::collections::HashSet;
use std::sync::LazyLock;

/// All token types in the Sigil language.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum TokenType {
    // --- Keywords ---
    Rule, When, Then, And, Or, Not, If, Else,
    Given, Define, As, Is, Exceeds, Below, Between,
    Any, All, None_, In,
    Import, Export, From, Module, Type, Neural, Explain, With,
    True, False, Using, Compute, Return, Trace, Match,
    For, Each, Evaluate, Main,
    Has, Have, Private, Mutable, Try, On, Error,
    Fallback, To, Returns, Record, One, Of, Priority,
    At, Least, Most, Becomes, Empty,
    Contains, Starts, Ends, Matches, Pattern, Equals,
    Python, Rust, List, Option_, Filter, Where, Sort, By,
    Take, First, Last, Map, Ascending, Descending,
    Assigned, Count, Query, Within,

    // --- Literals ---
    Number, String, Symbol,

    // --- Identifiers ---
    Identifier,

    // --- Unit suffix ---
    Unit,

    // --- Operators ---
    Plus, Minus, Star, Slash,
    Gt, Lt, Gte, Lte, Eq, Neq,
    Pipe, Arrow, Dot, DoubleColon,

    // --- Delimiters ---
    LParen, RParen, LBracket, RBracket, LBrace, RBrace,
    Colon, Comma,

    // --- Structure ---
    Indent, Dedent, Newline, Eof,

    // --- Special ---
    DocComment,
}

/// A single token from Sigil source code.
#[derive(Debug, Clone)]
pub struct Token {
    pub token_type: TokenType,
    pub value: String,
    pub line: usize,
    pub column: usize,
}

impl Token {
    pub fn new(token_type: TokenType, value: impl Into<String>, line: usize, column: usize) -> Self {
        Token { token_type, value: value.into(), line, column }
    }
}

/// Map keyword strings to their TokenType.
pub static KEYWORDS: LazyLock<HashMap<&'static str, TokenType>> = LazyLock::new(|| {
    let mut m = HashMap::new();
    m.insert("rule", TokenType::Rule);
    m.insert("when", TokenType::When);
    m.insert("then", TokenType::Then);
    m.insert("and", TokenType::And);
    m.insert("or", TokenType::Or);
    m.insert("not", TokenType::Not);
    m.insert("if", TokenType::If);
    m.insert("else", TokenType::Else);
    m.insert("given", TokenType::Given);
    m.insert("define", TokenType::Define);
    m.insert("as", TokenType::As);
    m.insert("is", TokenType::Is);
    m.insert("exceeds", TokenType::Exceeds);
    m.insert("below", TokenType::Below);
    m.insert("between", TokenType::Between);
    m.insert("any", TokenType::Any);
    m.insert("all", TokenType::All);
    m.insert("none", TokenType::None_);
    m.insert("in", TokenType::In);
    m.insert("import", TokenType::Import);
    m.insert("export", TokenType::Export);
    m.insert("from", TokenType::From);
    m.insert("module", TokenType::Module);
    m.insert("type", TokenType::Type);
    m.insert("neural", TokenType::Neural);
    m.insert("explain", TokenType::Explain);
    m.insert("with", TokenType::With);
    m.insert("true", TokenType::True);
    m.insert("false", TokenType::False);
    m.insert("using", TokenType::Using);
    m.insert("compute", TokenType::Compute);
    m.insert("return", TokenType::Return);
    m.insert("trace", TokenType::Trace);
    m.insert("match", TokenType::Match);
    m.insert("for", TokenType::For);
    m.insert("each", TokenType::Each);
    m.insert("evaluate", TokenType::Evaluate);
    m.insert("main", TokenType::Main);
    m.insert("has", TokenType::Has);
    m.insert("have", TokenType::Have);
    m.insert("private", TokenType::Private);
    m.insert("mutable", TokenType::Mutable);
    m.insert("try", TokenType::Try);
    m.insert("on", TokenType::On);
    m.insert("error", TokenType::Error);
    m.insert("fallback", TokenType::Fallback);
    m.insert("to", TokenType::To);
    m.insert("returns", TokenType::Returns);
    m.insert("record", TokenType::Record);
    m.insert("one", TokenType::One);
    m.insert("of", TokenType::Of);
    m.insert("priority", TokenType::Priority);
    m.insert("at", TokenType::At);
    m.insert("least", TokenType::Least);
    m.insert("most", TokenType::Most);
    m.insert("becomes", TokenType::Becomes);
    m.insert("empty", TokenType::Empty);
    m.insert("contains", TokenType::Contains);
    m.insert("starts", TokenType::Starts);
    m.insert("ends", TokenType::Ends);
    m.insert("matches", TokenType::Matches);
    m.insert("pattern", TokenType::Pattern);
    m.insert("equals", TokenType::Equals);
    m.insert("python", TokenType::Python);
    m.insert("rust", TokenType::Rust);
    m.insert("list", TokenType::List);
    m.insert("Option", TokenType::Option_);
    m.insert("filter", TokenType::Filter);
    m.insert("where", TokenType::Where);
    m.insert("sort", TokenType::Sort);
    m.insert("by", TokenType::By);
    m.insert("take", TokenType::Take);
    m.insert("first", TokenType::First);
    m.insert("last", TokenType::Last);
    m.insert("map", TokenType::Map);
    m.insert("ascending", TokenType::Ascending);
    m.insert("descending", TokenType::Descending);
    m.insert("assigned", TokenType::Assigned);
    m.insert("count", TokenType::Count);
    m.insert("query", TokenType::Query);
    m.insert("within", TokenType::Within);
    m
});

/// Known unit suffixes.
pub static UNIT_SUFFIXES: LazyLock<HashSet<&'static str>> = LazyLock::new(|| {
    let mut s = HashSet::new();
    s.insert("degrees");
    s.insert("percent");
    s.insert("seconds");
    s.insert("milliseconds");
    s.insert("dollars");
    s.insert("confidence");
    s.insert("years");
    s
});
