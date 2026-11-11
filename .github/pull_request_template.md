## Change and evidence

Describe the result, exact target/source revisions, reproduction and limitations.

## Publication and provenance

- [ ] I read LEGAL.md, PROVENANCE.md and the licensing scope, and can contribute this material.
- [ ] No game bytes, raw exports, dumps, proprietary symbols, assets, secrets or unlicensed code.
- [ ] External sources, AI assistance and source exposure are declared.
- [ ] Any reconstructed source or implementation transfer has explicit maintainer review.
- [ ] Progress describes real results; infrastructure CI is not presented as a Skyrim match.

## Validation

- [ ] `python3 tools/check.py --staged` before commit
- [ ] `python3 tools/check.py`
- [ ] `python3 -m unittest discover -s tests -v`
- [ ] `python3 tools/build_site.py`
