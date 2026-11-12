# Finding: held small queue units after generator repairs

Status: OBSERVED properties of the pinned image; selection only. Nothing reconstructed or compared.
Author / human operator: awarebayes
AI assistance / model: GPT Sol integrating Engineer, task p46-queue-refill-2; local analysis authorized by the maintainer
Date (UTC): 2026-11-13
Target build id / image SHA-256: `sse-steam-1-7-104` / `846efccf0c1374d71f892907f46549560f2fcb0a75cb87a3eed438baa0f1402f`
Function RVA / size (if applicable): private stage manifest `.local/scratch/p46/a-manifest.json`
Source exposure: mixed (binary-analysis of the pinned image through the private function table; community-headers; community name databases; the FNV sibling index)
Sources and immutable revisions / licenses: CharmedBaryon/CommonLibSSE-NG `b93280e832f263dbef44e44cbe2936622a02f91a` (MIT); powerof3/CommonLibSSE `654e55f7979c1733033d5dbef176e43827bac944` (GPL-3.0; files carrying its declarations state GPL-3.0); Address Library 1.7.104.0; meh321's name list `skyrimae.rename`, used with the author's permission as reported by the maintainer (`docs/authorizations.md`); momusdigital/fnv_decomp `91e1b6e8` (no licence; used by maintainer decision)
Name provenance: COMMUNITY (unverified), class names EXE_RTTI
Confidence: high for counts and the filters; medium for class attribution; low to medium for names

## Method and observations

Revisit the 19 units (54 functions) held by the second small queue selection. Repair the
skeleton generator without changing the comparator, validator or lint. Reapply the selection's
exclusions against current matched inventory, local queue passes and the generator lane.
Three functions in two units are now excluded by those clusters: this enrollment contains
17 units and 51 functions, all at most 64 bytes. Inventory status is mapped only.
Every unit has a plain sheet without FNV snippets. Skeletons and packs stay private.

Root interface stand-ins now have a virtual destructor to provide the observed primary vftable
storage. This is a size/layout scaffold, not evidence about that destructor's implementation.
Missing event template and opaque enum declarations follow the pinned community declarations.
Missing or unresolved shared headers use local base stand-ins. Repeated ambiguous bare dtor
names get distinct guessed method placeholders and private binding hints; no subobject layout
or destructor signature is inferred from the repeated name.

## Limits and confidence

Compile smoke uses private copies with only the deliberate non-compiling body marker replaced
by a throw statement. The generated bodies remain unfilled and must fail until drafted.
Compilation is not matching evidence. No source body, raw listing or decompiler output is
published here, and nothing is accepted or marked matched. Counts and exclusions are high
confidence; the original selection's class and name uncertainties remain.
