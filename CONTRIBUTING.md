# Contributing

This is a personal portfolio project. External contributions are not accepted at this time.

If you are evaluating the repository, please read the [Reviewer Checklist](README.md#reviewer-checklist) in the README.

## Running the Tests

```bash
# Install Python environment (uv required)
uv sync --extra dev

# Run the full test suite (74 tests, no external dependencies)
uv run pytest

# Run the optional web cockpit build
cd web && npm install && npm run build
```

## Safe Development Conventions

1. **No real credentials.** The classifier and source manifest contain no API keys or external access tokens.
2. **No real AI-system profiles.** Use the 14 synthetic example profiles in `examples/`. Do not add real company AI system descriptions.
3. **Draft only.** All artifact outputs carry `review_status: draft_only_human_review_required`. Do not remove this status field.
4. **Source manifest currency.** The bundled source manifest reflects a point-in-time snapshot. Verify dates against primary EUR-Lex and Official Journal sources before any live use.
5. **Test before commit.** Run `uv run pytest` before staging any change.

## Coding Agents

See `AGENTS.md` for guidelines on how future coding agents should work on this repository.
