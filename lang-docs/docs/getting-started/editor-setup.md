# Editor Setup

Sigil is a young language — full editor support is planned for future phases. Here are some tips to make working with `.sigil` files more comfortable today.

## VS Code

### Syntax highlighting

No dedicated VS Code extension exists yet. For basic highlighting, associate `.sigil` files with Python mode (the indentation style is similar):

1. Open Settings (`Cmd+,` / `Ctrl+,`)
2. Search for "files.associations"
3. Add: `"*.sigil": "python"`

This gives you comment highlighting and basic indentation support.

!!! tip "Coming soon"
    A dedicated VS Code extension with full syntax highlighting, diagnostics, and snippets is planned for Phase 4.

### Recommended settings

Add to your workspace `.vscode/settings.json`:

```json
{
  "files.associations": {
    "*.sigil": "python"
  },
  "[python]": {
    "editor.tabSize": 2
  }
}
```

## Neovim

### Basic filetype detection

Add to your Neovim config:

```lua
vim.filetype.add({
  extension = {
    sigil = "sigil",
  },
})
```

### Syntax highlighting

For basic highlighting, use the Python treesitter parser as a fallback:

```lua
vim.treesitter.language.register("python", "sigil")
```

### Running Sigil from Neovim

Map a key to run the current file:

```lua
vim.api.nvim_create_autocmd("FileType", {
  pattern = "sigil",
  callback = function()
    vim.keymap.set("n", "<leader>r", function()
      vim.cmd("!sigil run %")
    end, { buffer = true, desc = "Run Sigil file" })
  end,
})
```

## Other editors

For any editor, the key settings are:

- **File extension**: `.sigil`
- **Comment style**: `--` (single line), `{- ... -}` (multi-line)
- **Indentation**: 2 spaces (significant whitespace)
- **Encoding**: UTF-8

!!! info "LSP support"
    A Language Server Protocol (LSP) implementation is planned for Phase 4, which will bring diagnostics, completion, and hover info to any LSP-compatible editor.
