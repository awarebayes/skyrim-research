## Reconstructed function(s)

| RVA | name (community, unverified) | local result | reason | candidate/target bytes | code section (first 16) |
|---|---|---|---|---|---|
{{functions_table}}

A local pass is **not** acceptance. The project re-runs the comparison on two of its own verifier
hosts, a fresh Reviewer checks the source against the blocking grounds in `docs/verification.md`,
and only then is the function recorded as `matched`. A reject comes back here with reasons.

## Sanitized local comparator summary

Produced by `tools/contrib.py compare` at tool revision `{{tool_revision}}`. Hashes, counts and
reason codes only; no bytes, listings or decompiler output.

```json
{{report_json}}
```

## Provenance and assistance

- Drafted by: {{drafted_by}} (a person, and the AI model if one wrote code)
- Source exposure (as stated in the unit header): see the header's `Source exposure:` line.
- Label check (`tools/check_labels.py`, advisory):
{{label_findings}}
- Origin check (`tools/check_origin.py`, bodies close to a same-named community body):
{{origin_findings}}

## Checklist

- [ ] I read LEGAL.md, PROVENANCE.md and the licensing scope, and can contribute this material.
- [ ] Only reconstruction source is in this pull request: no game files, bytes, listings,
  disassembly, decompiler output, dumps, proprietary symbols or secrets, here or in comments.
- [ ] Every name carries its origin label (`docs/drafter-card.md`); a body adapted from a community
  source is declared in the unit header with its licence.
- [ ] No material from the FNV decompilation (its use by external contributors awaits a maintainer decision).
- [ ] AI assistance and source exposure are stated above and in the unit header.
- [ ] `python3 tools/check.py` and `python3 tools/contrib.py submit --dry-run` ran clean.
