# Verification

Date: 2026-08-05

## Result

**PASS** as a standalone portfolio repository.

## Clean-copy test

The repository was copied to a fresh temporary directory without `build/` or `.git/`.

These commands passed from that copy:

```bash
python3 run_demo.py
python3 -m unittest discover -s tests -v
```

Result:

- verifier: `ACCEPT`
- errors: 0
- tests: 11 of 11 passed
- top claim: dialectically accepted with direct evidence
- selected capability objection: dialectically rejected
- generated outputs: byte-identical across two runs

## Tests with teeth

The suite rejects:

- a changed source hash
- a changed manifest root
- a self-consistent extract changed from Codex 15 of 25 to 0 of 25
- a missing selected objection
- a candidate record promoted into positive support
- a changed confidence label
- a broad claim matching the frozen tripwire
- a dependency cycle

## Exposure scan

The packaged repository contains no absolute Aletheia paths, credentials, passwords, API keys, or hidden-task identity. It includes sanitized evidence extracts and original artifact hashes.

## Scope

This verifies the portable code and included extracts. It does not expose or independently reproduce the private full reports from their hashes.
