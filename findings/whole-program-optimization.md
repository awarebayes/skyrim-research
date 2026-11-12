# Finding: whole-program optimization does not explain the prologue-only near-misses

Status: OBSERVED (LTCG and flag-sweep results measured; the cause of the near-misses stays open)
Author / human operator: awarebayes
AI assistance / model: Claude Code Engineer worker (claude-opus-5-5); task p9-ltcg-experiment
Target build id / image SHA-256: `sse-steam-1-7-104` /
`846efccf0c1374d71f892907f46549560f2fcb0a75cb87a3eed438baa0f1402f`
Function RVA / size (if applicable): 0xce3250/112, 0xce32d0/126, 0x237a20/435, 0x1523e50/163,
0x15237e0/384, 0x1523d20/286 (names as in CommonLibSSE-NG b93280e)
Source exposure: mixed (binary-analysis of the pinned image, community-headers)
Sources and immutable revisions / licenses: compiler 19.16.27054 per `tools/verifier/pinned.sha256`;
recipe `reconstruction/recipes/msvc-19.16.27054-o2.json`; `tools/verifier/align.py` at this commit
Name provenance: COMMUNITY
Confidence: high that `/GL` + `/LTCG` and the swept flags leave these functions' code unchanged
for these sources; low for the next hypotheses

## Question and method

Can `/GL` with link-time code generation (the header records `LTCG` and 68 LTCG objects), or
another flag, produce the prologue/stack differences no source spelling removed (cookbook rules
12, 13)? Units: BSReadWriteLock and InventoryChanges/RemoveFavorite (best private triage drafts),
BSLightingShaderMaterialBase (current draft); NiObject::ProcessClone is untested (its draft was
not kept). On the standing verifier: 25 compile variants per unit, and `/GL` objects linked
`/LTCG` into a DLL with a map file, undefined externals bound with `/ALTERNATENAME` to distinct
stand-ins in a non-`/GL` object. Link modes: functions kept by `/INCLUDE`; plus a `/GL` caller
object; exported instead; for the lock, eight `/GL` callers and no `/INCLUDE` (functions internal
to the link). Functions were taken from the DLL by the new `tools/verifier/image_listing.py` and
scored with `align.py` (no unwind input on this path). Control: the units linked without LTCG
score exactly as their objects do (all 17 passing functions at 0).

## Observations

- LTCG: in every link mode, every function of the three units is byte-identical (outside
  relocated fields) to the non-LTCG link. Distances stay: LockForRead 1, LockForWrite 2 (same
  callee-saved swap; LockForRead was inlined away in the internal mode), 0x1523e50 7.5,
  0x15237e0 3.5, 0x1523d20 2, RemoveFavorite 53.1; passing functions stay at 0.
- Flags without LTCG: `/O1`, `/Ox`, `/Ob0`, `/Ob1`, `/Oy-`, `/Os`, `/favor:INTEL64|AMD64|ATOM`,
  `/Zc:inline`, `/guard:cf`, `/Qspectre`, `/hotpatch`, `/GS`, `/fp:fast`, `/Gw`, `/d2SSAOptimizer-`,
  `/EHa`, `/EHs`, `/Zi`, `/std:c++17`, `/volatile:iso`, `/MT`. None lowers a failing function's
  distance or changes its difference classes or register map. `/O1`, `/Os`, `/Ob0`, `/Ob1`,
  `/favor:ATOM|AMD64`, `/guard:cf`, `/d2SSAOptimizer-`, `/std:c++17` and `/EHa` break functions
  that pass now; the others equal the recipe.
- RemoveFavorite: a guard with an out-of-line destructor in the list helper (no throwing call in
  scope) gives no -2 store and no handler; under LTCG with the destructor visible the guard
  vanishes. A guard around the loop's external calls gives the -2 store and a C++ handler (unwind
  flag 2) in every mode, also under LTCG with the destructor and the four callees visible as
  non-inlined, non-throwing `/GL` bodies. "-2 store without a handler" never appeared.
- Image counts (local, 89,973 ordinary functions): 21,156 save callee-saved registers in leading
  home-slot stores; 768 skip the first home slot and never use it afterwards (both
  BSLightingShaderMaterialBase functions among them), over 23 of 24 1-MB ranges, at most 2.8% of
  any range, in 271 runs; the densest hold 57 functions in 8 KB and 46 in 24 KB. -2 store without
  a handler: 151 functions, 132 in 0xd06c60..0xea2540 (about 1.6 MB, 4 runs), 10 in
  0x22d220..0x240fe0 (around RemoveFavorite); 24,217 functions have a -2 store and a handler.

## Interpretation and alternatives

LockForRead, LockForWrite, 0x1523e50, 0x15237e0, 0x1523d20: LTCG refuted as the cause for these
sources; the swept flags refuted. RemoveFavorite: LTCG not confirmed (undetermined). ProcessClone:
undetermined. A link-mode verifier would unlock none of these functions. The -2-without-handler
pattern clusters by address, so it belongs to a few objects or a source idiom used there. Next
hypotheses, untested: EH state removed after frame layout (a `noexcept` or `throw()` helper whose
throwing path folds away), or frame layout kept from dead code (a parameter or `this` whose
address is taken and then optimised out), tried first on one dense run.

## Reproduction and sanitized evidence

Private scripts, logs and tables: `<worktree>/.local/p9/`; handoff
`.local/handoffs/p9-ltcg-experiment.md`. Machine: `sr-verifier-msvc141`, five short runs.

## Negative results and limitations

DLL-path distances exclude unwind fields; code identity still covers saved-register order. Only
one or two `/GL` objects took part, so effects needing the other LTCG objects (cross-module
inlining into these functions) are not reproduced; the lock functions call only imports. The
census is an approximate byte-pattern count (rsp-relative accesses only). The compiler revision
field is absent from the Rich header and was not varied. PGO was not run (no profile signature).

## Reviewer and outcome

Not reviewed. No function is matched by this finding.
