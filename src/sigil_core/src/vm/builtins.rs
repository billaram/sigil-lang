//! Built-in function dispatch for the VM.

use super::stack::VMValue;

/// Built-in function IDs — match the compiler's BUILTIN_IDS.
pub const BUILTIN_PRINT: u16 = 0;
pub const BUILTIN_MAX: u16 = 1;
pub const BUILTIN_MIN: u16 = 2;
pub const BUILTIN_LEN: u16 = 3;
pub const BUILTIN_TYPE_OF: u16 = 4;
pub const BUILTIN_ABS: u16 = 5;
pub const BUILTIN_ROUND: u16 = 6;
pub const BUILTIN_SQRT: u16 = 7;
pub const BUILTIN_FLOOR: u16 = 8;
pub const BUILTIN_CEIL: u16 = 9;
pub const BUILTIN_APPEND: u16 = 10;
pub const BUILTIN_RANGE: u16 = 11;
pub const BUILTIN_SUM: u16 = 12;
pub const BUILTIN_TO_TEXT: u16 = 13;
pub const BUILTIN_TO_NUMBER: u16 = 14;

/// Execute a builtin function.
pub fn call_builtin(id: u16, args: Vec<VMValue>) -> Result<VMValue, String> {
    match id {
        BUILTIN_PRINT => Ok(VMValue::None), // Print is handled by the engine (output_lines)
        BUILTIN_MAX => builtin_max(args),
        BUILTIN_MIN => builtin_min(args),
        BUILTIN_LEN => builtin_len(args),
        BUILTIN_TYPE_OF => builtin_type_of(args),
        BUILTIN_ABS => builtin_abs(args),
        BUILTIN_ROUND => builtin_round(args),
        BUILTIN_SQRT => builtin_sqrt(args),
        BUILTIN_FLOOR => builtin_floor(args),
        BUILTIN_CEIL => builtin_ceil(args),
        BUILTIN_APPEND => builtin_append(args),
        BUILTIN_RANGE => builtin_range(args),
        BUILTIN_SUM => builtin_sum(args),
        BUILTIN_TO_TEXT => builtin_to_text(args),
        BUILTIN_TO_NUMBER => builtin_to_number(args),
        _ => Err(format!("Unknown builtin ID: {}", id)),
    }
}

fn builtin_max(args: Vec<VMValue>) -> Result<VMValue, String> {
    if args.len() == 1 {
        // max of a list
        if let VMValue::List(items) = &args[0] {
            return items
                .iter()
                .max_by(|a, b| cmp_numeric(a, b))
                .cloned()
                .ok_or_else(|| "max() of empty list".to_string());
        }
    }
    // max of two values
    if args.len() >= 2 {
        let a = &args[0];
        let b = &args[1];
        return Ok(if cmp_numeric(a, b) == std::cmp::Ordering::Greater {
            a.clone()
        } else {
            b.clone()
        });
    }
    Err("max() requires at least 1 argument".to_string())
}

fn builtin_min(args: Vec<VMValue>) -> Result<VMValue, String> {
    if args.len() == 1 {
        if let VMValue::List(items) = &args[0] {
            return items
                .iter()
                .min_by(|a, b| cmp_numeric(a, b))
                .cloned()
                .ok_or_else(|| "min() of empty list".to_string());
        }
    }
    if args.len() >= 2 {
        let a = &args[0];
        let b = &args[1];
        return Ok(if cmp_numeric(a, b) == std::cmp::Ordering::Less {
            a.clone()
        } else {
            b.clone()
        });
    }
    Err("min() requires at least 1 argument".to_string())
}

fn builtin_len(args: Vec<VMValue>) -> Result<VMValue, String> {
    if args.is_empty() {
        return Err("len() requires 1 argument".to_string());
    }
    match &args[0] {
        VMValue::List(items) => Ok(VMValue::Int(items.len() as i64)),
        VMValue::Text(s) => Ok(VMValue::Int(s.len() as i64)),
        VMValue::Record { fields, .. } => Ok(VMValue::Int(fields.len() as i64)),
        _ => Ok(VMValue::Int(0)),
    }
}

fn builtin_type_of(args: Vec<VMValue>) -> Result<VMValue, String> {
    if args.is_empty() {
        return Err("type_of() requires 1 argument".to_string());
    }
    let name = match &args[0] {
        VMValue::None | VMValue::Unbound => "None",
        VMValue::Bool(_) => "Bool",
        VMValue::Int(_) => "Number",
        VMValue::Float(_) => "Number",
        VMValue::Text(_) => "Text",
        VMValue::Symbol(_) => "Symbol",
        VMValue::Record { .. } => "Record",
        VMValue::Variant { .. } => "Variant",
        VMValue::List(_) => "List",
        VMValue::Closure { .. } => "Closure",
    };
    Ok(VMValue::Symbol(name.to_string()))
}

fn builtin_abs(args: Vec<VMValue>) -> Result<VMValue, String> {
    if args.is_empty() {
        return Err("abs() requires 1 argument".to_string());
    }
    match &args[0] {
        VMValue::Int(i) => Ok(VMValue::Int(i.abs())),
        VMValue::Float(f) => Ok(VMValue::Float(f.abs())),
        _ => Err("abs() requires a number".to_string()),
    }
}

fn builtin_round(args: Vec<VMValue>) -> Result<VMValue, String> {
    if args.is_empty() {
        return Err("round() requires 1 argument".to_string());
    }
    match &args[0] {
        VMValue::Float(f) => Ok(VMValue::Int(f.round() as i64)),
        VMValue::Int(i) => Ok(VMValue::Int(*i)),
        _ => Err("round() requires a number".to_string()),
    }
}

fn builtin_sqrt(args: Vec<VMValue>) -> Result<VMValue, String> {
    if args.is_empty() {
        return Err("sqrt() requires 1 argument".to_string());
    }
    match args[0].as_float() {
        Some(f) => Ok(VMValue::Float(f.sqrt())),
        _ => Err("sqrt() requires a number".to_string()),
    }
}

fn builtin_floor(args: Vec<VMValue>) -> Result<VMValue, String> {
    if args.is_empty() {
        return Err("floor() requires 1 argument".to_string());
    }
    match args[0].as_float() {
        Some(f) => Ok(VMValue::Int(f.floor() as i64)),
        _ => Err("floor() requires a number".to_string()),
    }
}

fn builtin_ceil(args: Vec<VMValue>) -> Result<VMValue, String> {
    if args.is_empty() {
        return Err("ceil() requires 1 argument".to_string());
    }
    match args[0].as_float() {
        Some(f) => Ok(VMValue::Int(f.ceil() as i64)),
        _ => Err("ceil() requires a number".to_string()),
    }
}

fn builtin_append(args: Vec<VMValue>) -> Result<VMValue, String> {
    if args.len() < 2 {
        return Err("append() requires 2 arguments".to_string());
    }
    match &args[0] {
        VMValue::List(items) => {
            let mut new_items = items.clone();
            new_items.push(args[1].clone());
            Ok(VMValue::List(new_items))
        }
        _ => Err("append() requires a list as first argument".to_string()),
    }
}

fn builtin_range(args: Vec<VMValue>) -> Result<VMValue, String> {
    let (start, end) = match args.len() {
        1 => (0i64, args[0].as_int().unwrap_or(0)),
        2.. => (
            args[0].as_int().unwrap_or(0),
            args[1].as_int().unwrap_or(0),
        ),
        _ => return Err("range() requires 1-2 arguments".to_string()),
    };
    let items: Vec<VMValue> = (start..end).map(VMValue::Int).collect();
    Ok(VMValue::List(items))
}

fn builtin_sum(args: Vec<VMValue>) -> Result<VMValue, String> {
    if args.is_empty() {
        return Err("sum() requires 1 argument".to_string());
    }
    match &args[0] {
        VMValue::List(items) => {
            let mut total = 0.0f64;
            let mut all_int = true;
            for item in items {
                match item {
                    VMValue::Int(i) => total += *i as f64,
                    VMValue::Float(f) => {
                        total += f;
                        all_int = false;
                    }
                    _ => return Err("sum() requires a list of numbers".to_string()),
                }
            }
            if all_int {
                Ok(VMValue::Int(total as i64))
            } else {
                Ok(VMValue::Float(total))
            }
        }
        _ => Err("sum() requires a list".to_string()),
    }
}

fn builtin_to_text(args: Vec<VMValue>) -> Result<VMValue, String> {
    if args.is_empty() {
        return Err("to_text() requires 1 argument".to_string());
    }
    Ok(VMValue::Text(format!("{}", args[0])))
}

fn builtin_to_number(args: Vec<VMValue>) -> Result<VMValue, String> {
    if args.is_empty() {
        return Err("to_number() requires 1 argument".to_string());
    }
    match &args[0] {
        VMValue::Int(i) => Ok(VMValue::Int(*i)),
        VMValue::Float(f) => Ok(VMValue::Float(*f)),
        VMValue::Text(s) => {
            if let Ok(i) = s.parse::<i64>() {
                Ok(VMValue::Int(i))
            } else if let Ok(f) = s.parse::<f64>() {
                Ok(VMValue::Float(f))
            } else {
                Err(format!("Cannot convert '{}' to number", s))
            }
        }
        VMValue::Bool(b) => Ok(VMValue::Int(if *b { 1 } else { 0 })),
        _ => Err("to_number() requires a convertible value".to_string()),
    }
}

fn cmp_numeric(a: &VMValue, b: &VMValue) -> std::cmp::Ordering {
    let fa = a.as_float().unwrap_or(0.0);
    let fb = b.as_float().unwrap_or(0.0);
    fa.partial_cmp(&fb).unwrap_or(std::cmp::Ordering::Equal)
}
