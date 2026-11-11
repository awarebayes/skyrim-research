# Contributing

Read `AGENTS.md`, `LEGAL.md`, `PROVENANCE.md` and `docs/verification.md` first.
A human operator is accountable for AI-assisted work. State assistance and source exposure.
Do not submit material you lack rights to contribute. The licensing scope is in `LICENSE`;
there is no blanket relicensing of recovered implementations or third-party material.

1. Pick or open a focused issue. State who is working on it and how long the claim lasts.
2. Pin the target and dependencies before making build-specific claims. Keep inputs in `.local/`.
3. Record the method and outcome with the research template, including failures and unknowns.
4. Update the work item in `data/progress.json`. Changes to GitHub issues do not silently update
   the report: commit the reviewed status so it has a reproducible source revision.
5. Stage named files and inspect their contents. Run:

```sh
python3 tools/check.py --staged
python3 tools/check.py
python3 -m unittest discover -s tests -v
python3 tools/build_site.py
```

Include these results in the PR, along with exact revisions and limitations. Do not attach
private outputs. The automated guard is defense in depth, not a secret scanner or legal review.
Use the PR checklist. A passed infrastructure check does not establish a byte match.

## What is useful now

Pin the legally owned Skyrim target; identify compiler candidates; reproduce the community
archive import; define and implement a relocation-aware comparator with synthetic fixtures;
then recover one small function. Do not add dummy matches to make the website look active.

## Publication

Maintainer review is required before publishing reconstructed game functions or approving
behavior specifications for transfer. Keep executable-building tools separate if pursued later,
with a fresh review of scope and publication policy. No such builder exists here today.
