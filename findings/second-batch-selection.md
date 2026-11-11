# Finding: second batch of five functions selected by a scripted exporter

Status: OBSERVED properties of the pinned image; selection only. Nothing reconstructed or compared.
Author / human operator: awarebayes
AI assistance / model: Claude Code Engineer worker (claude-opus-5-5), task p4-candidates-and-packs; local only
Date (UTC): 2026-11-11
Target build id / image SHA-256: `sse-steam-1-7-104` / `846efccf0c1374d71f892907f46549560f2fcb0a75cb87a3eed438baa0f1402f`
Function RVA / size (if applicable): see the table
Source exposure: mixed (binary-analysis of the pinned image in local Ghidra 12.2; community-headers; a community address database)
Sources and immutable revisions / licenses: CharmedBaryon/CommonLibSSE-NG `b93280e832f263dbef44e44cbe2936622a02f91a` (MIT) for every published name;
Address Library 1.7.104.0 `versionlib-1-7-104-0.bin` SHA-256 `8aab3dd251d135b849bd983f86a4a205c920fa3e81f8e30c0e63ccfef9423842`
(publishing id/offset pairs approved, `docs/authorizations.md`); powerof3/CommonLibSSE `654e55f7979c1733033d5dbef176e43827bac944`
(GPL-3.0) consulted locally as a fallback only; nothing from it is published here.
Name provenance: COMMUNITY (unverified; each is the nearest enclosing NG definition of the id, a heuristic)
Confidence: high for sizes, unwind forms and reference counts; low to medium for names

## Question and method

Which five functions give a Drafter trial the most varied friction while staying inside comparator
contract v1? `tools/ghidra/export_pack.py survey --named` classified all 579 function starts that NG
names through the Address Library (224 supported, 60 supported with caution, 295 unsupported), and
`packs` wrote private context packs and task directories for the picks. The verdict uses the
image's `.pdata`, `UNWIND_INFO`, DIR64 base relocations and import table, plus Ghidra's references.

## Observations

| slot | RVA (AE id) | size | name (NG) | unwind | references leaving the function |
|---|---|---|---|---|---|
| a | `0xef8900` (70826) | 53 | `NiTimeController::ProcessClone` | v1, no handler, 3 codes | 1 direct call (id 70190, NG `NiObject::ProcessClone`), 1 virtual call, no data |
| b | `0x240f50` (16212) | 54 | `BSPointerHandleManagerInterface::GetHandle` | v1, no handler, 2 codes | 1 call (id 12326, NG `Offset::CreateRefHandle`), 1 `.data` read (id 400312, no community name) |
| c | `0x73ae00` (40299) | 172 | `ArmorRatingVisitorBase::Visit` | v1, no handler, 4 codes | 3 direct calls (ids 17797 unnamed, 16017, 23526), 2 virtual calls |
| d | `0xce3970` (68245) | 76 | `BSTimer::SetGlobalTimeMultiplier` | none (leaf, no `.pdata`) | 4 accesses to 2 `.data` globals (ids 388442, 388443, NG `BSTimer` statics); SSE divide, multiply, compare |
| e | `0x2e7fc0` (19691) | 156 | `Actor::HasOutfitItems` | v1, no handler, 4 codes | 2 direct calls (id 16040, id 11702 unnamed), 11 conditional branches |

All five: one or zero `.pdata` entries exactly at the range, no DIR64 relocation in range, no jump
table, no import, every reference target has an Address Library id. Backups:
`0x7499e0` (40488, 47 B, `PlayerCharacter::AddSkillExperience`, 1 call to an unnamed id),
`0xf55d90` (72439, 112 B, `NiControllerSequence::SetPhase`, FP leaf without `.pdata`, no references),
`0x2e8690` (19703, 201 B, `TESObjectREFR::GetWeightInContainer`, 4 calls and 1 global read, saves XMM6).

Suitability of a random sample (2,000 Ghidra functions in the main `.text`, seed 1): 462 supported
(median 64 B), 901 supported but leaf without `.pdata` (median 12 B; size from analysis), 56 other
cautions, 581 unsupported (median 110 B; about two thirds of the sampled bytes). Unsupported reasons
(a function may have several): exception handler 457, chained unwind 109 (all also multiple `.pdata`),
thunk 16, non-contiguous body 13, jump table 5, import thunk 2, `.pdata` not at entry 1.

## Interpretation and alternatives

Why each was chosen, and the risk seen: (a) simplest call case with both names in NG; the class
is virtual-heavy, so the Drafter must declare enough of `NiObject` to get a direct base call and
the right decorated name. (b) call plus global read, noted earlier as a backup; NG declares
`GetHandle` inside a class template, so the original may be one instantiation or several folded
together, and the global has no community name (any name given is a GUESS). (c) shares the
RTTI-evidenced anonymous-namespace translation unit with the accepted `0x73ad90`; adding it
edits that unit, which makes the existing match record stale until it is re-verified. One callee is
an NG variadic template wrapper. (d) FP leaf without unwind data, so the size is the analysed body
(followed by int3 padding); its float equality test has no unordered branch, which may point to
`/fp:fast` rather than the pinned recipe's `/fp:precise` (inference). (e) larger, loop with an
inlined list walk; the second callee is unnamed. LTCG or inlining across units is possible for all
five and not observable per function.

## Reproduction and sanitized evidence

`python3 tools/ghidra/export_pack.py survey --named`, `survey --sample 2000 --seed 1` and
`packs <list>` with a private config (`tools/ghidra/README.md`). Packs, listings and decompiler output
stay under `.local/`. Timing: 8 functions with decompilation in 8.6 s; 2,000 in 15.7 s.

## Negative results and limitations

Verdicts predict the comparator; only a comparator run decides. Names come from a heuristic join
and are unverified. Leaf sizes without `.pdata` come from Ghidra. One host, one run.

## Reviewer and outcome

Not reviewed. Inventory entries added as `mapped` only.
