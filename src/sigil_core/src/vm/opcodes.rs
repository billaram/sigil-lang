//! Bytecode opcodes for the Sigil VM.

use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub enum Opcode {
    // --- Stack ---
    PushInt(i64),
    PushFloat(f64),
    PushBool(bool),
    PushNone,
    PushUnbound,
    PushString(u32),  // index into string pool
    PushSymbol(u32),  // index into string pool
    PushList(u16),    // pop N items -> list
    PushRecord(u16),  // pop N key-value pairs -> record
    PushVariant(u32, u16), // type_name idx, pop N field pairs
    Pop,
    Dup,

    // --- Arithmetic ---
    Add,
    Sub,
    Mul,
    Div,
    Neg,
    Mod,

    // --- Comparison ---
    Eq,
    Neq,
    Gt,
    Lt,
    Gte,
    Lte,

    // --- Logic ---
    Not,
    And,
    Or,

    // --- Variables ---
    Load(u32),       // string pool index -> push variable value
    Store(u32),      // pop value -> bind to variable name
    LoadField(u32),  // pop record -> push field value (or Unbound)
    StoreField(u32), // pop value, pop record -> set field
    Mutate(u32),     // `becomes` — in-place mutation

    // --- Control Flow ---
    Jump(u32),          // unconditional jump
    JumpIfFalse(u32),   // pop, jump if false/unbound
    JumpIfTrue(u32),    // pop, jump if true
    JumpIfUnbound(u32), // pop, jump if _UNBOUND

    // --- Functions ---
    Call(u32, u8),        // function name idx, arg count
    Return,
    CallBuiltin(u16, u8), // builtin ID, arg count
    MakeClosure(u32, u8), // function name idx, capture count

    // --- Sigil Conditions ---
    CmpExceeds,  // a > b
    CmpBelow,    // a < b
    CmpAtLeast,  // a >= b
    CmpAtMost,   // a <= b
    CmpBetween,  // low <= a <= high
    CmpIs,       // a == b (value or symbol)
    CmpIsNot,    // a != b
    IsAssigned,  // !(is_unbound)
    IsEmpty,     // is_empty(list/none/unbound)
    Contains,    // collection contains element
    InList,      // element in list
    HasCount,    // len(collection) == count
    StringOp(u8), // 0=starts_with, 1=ends_with, 2=contains, 3=matches

    // --- Rule Engine ---
    BeginRule(u32),  // rule index -> start trace
    EndRule,
    FireRule(u32),   // mark rule as fired
    CheckFired(u32), // push true if already fired
    SetExplain(u32), // set explain string (string pool idx)

    // --- Output ---
    Print,

    // --- Special ---
    Halt,

    // --- Index Access ---
    IndexAccess, // pop index, pop object -> push value
}
