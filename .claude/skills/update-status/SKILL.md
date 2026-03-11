---
description: Update ai_docs/STATUS.md after completing work
---

# Update Status

Update `ai_docs/STATUS.md` to reflect completed work.

## Steps

1. Read `ai_docs/STATUS.md` to understand current state

2. Ask the user what was completed (if not obvious from conversation context)

3. Update the file:
   - Move completed items from "Being Built" sections to "What Exists and Works"
   - Update test counts (run `pytest tests/ -v --tb=short 2>&1 | tail -5` to get current count)
   - Add any new known issues to "Known Issues / Open Questions"
   - Log any decisions made in "Decision Log"
   - Update the "Last updated" date at the top
   - Update "Current phase" and sprint info if applicable

4. Show the diff of changes made

## Important

- Keep the file structure consistent — don't reorganize sections
- Use checkboxes `[x]` for completed items, `[ ]` for incomplete
- Include specific counts (test numbers, file counts) where possible
