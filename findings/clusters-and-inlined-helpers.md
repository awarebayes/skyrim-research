# Finding: code clusters for stamping, and a census of inlined helpers

Status: OBSERVED (counts on the pinned image); HYPOTHESIS (that stamped sources compile to their targets: nothing was compiled or compared)
Author / human operator: awarebayes
AI assistance / model: Claude Code Engineer worker (claude-opus-5-5), task p7-clusters-and-helpers; local only
Date (UTC): 2026-11-12
Target build id / image SHA-256: `sse-steam-1-7-104` / `846efccf0c1374d71f892907f46549560f2fcb0a75cb87a3eed438baa0f1402f` (re-hashed)
Function RVA / size (if applicable): exemplars named below; cluster tables private
Source exposure: binary-analysis (the image's code, `.pdata`, RTTI, POGO and relocation data; Ghidra export for entry points); community-headers for names
Sources and immutable revisions / licenses: CharmedBaryon/CommonLibSSE-NG `b93280e8` (MIT) and powerof3/CommonLibSSE `654e55f7` (GPL-3.0, names only) through Address Library 1.7.104.0
Name provenance: EXE_RTTI (class names), COMMUNITY (method names, unverified), GUESS (destructor identities)
Confidence: high for counts; medium for the stamping design until the Boat tests below run

## Question and method

How much code repeats with only its references changed, which repeats can be stamped from one
solved exemplar, and which code runs recur inside functions (inlined helpers)? Tools, original
stdlib Python with tests on synthetic fixtures only: `tools/analysis/x64.py` (length decoder;
boundaries and targets agreed with llvm-objdump on 3,000 sampled functions, apart from Ghidra sizes
that end inside an instruction), `imagemodel.py` (compared range and reference fields with the
comparator's definitions: `REL32`/`REL32_k`, `ADDR32NB` through an image-base register, switch
tables, `DIR64`; ranges grown as the exporter grows them), `clusters.py`, `stamp.py`,
`inline_census.py`. Population: the 90,144 `.text$mn` entries that are not funclets or thunks
(20.5 MB). Whole run: clusters 12 s, census 30 s. Outputs stay under `.local/analysis/`.

## Observations

Levels: *exact* (same bytes), *masked* (L1: reference fields blanked; same field layout, unwind
codes and chained entries, so members differ only in which symbols they name), *shape* (L2: also
displacements and immediates). The exact level reproduces the guidelines' 9,596 copies in 1,086
groups exactly; L1 gives 34,515 repeats (guidelines: 34,433) and 232 clusters of 20 or more.

| members | L1 clusters | functions | bytes |
|---|---|---|---|
| 2 | 2,988 | 5,976 | 918,126 |
| 3-4 | 1,107 | 3,706 | 464,281 |
| 5-9 | 565 | 3,605 | 420,942 |
| 10-19 | 258 | 3,345 | 356,965 |
| 20-99 | 183 | 7,880 | 814,274 |
| 100+ | 49 | 15,153 | 646,407 |

- L1 repeats: 34,515 functions, 2.91 MB; L2 repeats: 41,249, 3.61 MB. 1,639 L1 clusters (10,075
  functions) have a C++ handler. Cases: class methods 1,066 clusters (14,969 functions), template
  instantiations 511 (3,473), duplicated helpers with identical targets 1,589 (9,573), unowned 1,984 (11,650).
- Identity: 17,930 cluster members have an RTTI owner class, 30,614 have some class identity
  (owner, community name, or the vftable they store); only 101 have an Address Library name.
- Shapes, read from the code and the vftable slot (no member needs a community name for these):
  deleting destructor (destroy, then free if bit 0 of the flags) 100 clusters, 4,753 functions;
  empty function 1,733; adjustor thunk 1,464; constant return 1,171; returns a member of `this`
  547; reference-count release 197. The largest cluster is 2,062 deleting destructors of 8-byte
  interfaces (slot 0 in 1,999 cases); the out-of-line form that only restores the vftable pointer
  is one cluster of 1,060.
- Existing exemplars (46 accepted or passing functions): 39 are alone at L1. The out-of-line
  ItemFilter destructor of the InventoryChanges unit (`0x22b710`, passing) leads the 1,060 cluster
  and, through the same source, the 2,062 cluster; `NiTimeController::ProcessClone` (`0xef8900`,
  accepted) shares a cluster with `NiAVObject::ProcessClone`; five more have one unnamed partner.
- Parameter table of the destructor family: 2,192 functions get a complete row (398 root classes,
  561 functions; 1,631 derived classes whose own vftable store was removed); 782 also have an area
  by the prefix rule; the generator writes 308 of them today (55 units). 68 vftables are each stored
  by several out-of-line destructors (809 functions), which cannot be told apart and are not stamped.

Census (one representative per L1 cluster, 55,629 functions; windows of 6, and of 4 when they
hold a call or data target; branch sense kept, distance dropped):

| hosts | windows | maximal bodies | with an out-of-line twin | also repeated in one host |
|---|---|---|---|---|
| 2+ | 349,111 | 28,726 | 3,259 | 1,041 |
| 5+ | 49,938 | 1,852 | 262 | 322 |
| 20+ | 6,494 | 172 | 35 | 88 |
| 100+ | 616 | 8 | 4 | 7 |

- Of 8,426 representatives over 512 B, 1,878 contain a body of 20 or more hosts; those bodies hold
  1.3% of their instructions. No twin of a 20+ body has an Address Library name.
- Within-function repeats (3 instructions, branch sense ignored, anchored on a reference or a
  member displacement): 49,681 groups in 17,709 functions, a candidate list rather than a census.
- Ground truth from the third batch, all found: the "is open" check of TESFile Seek and Duplicate
  is one 16-instruction body with exactly those two hosts; `IsCompressed()` appears twice in
  SeekNextSubrecord (+0x15, +0x62); the root walk appears twice in Duplicate (+0x60, +0x71).

## Interpretation and alternatives

Stamping covers small code: the destructor family alone is 2,192 functions (87 KB) from one
solved pattern. Three source forms: (a) template members: one template in a shared header and
one explicit instantiation per member; (b) the same method on other classes: one unit per class,
from the exemplar plus a parameter row (class from RTTI, callees from the reference columns, member
names from community headers); (c) copies of one helper with the same targets: one candidate
compared against every copy, which needs contract support for internal-linkage symbols (as the
static initializers do). Derived classes store their base's vftable, so a stored vftable names
the class only for root classes; the owner comes from vftable slot 0 instead. The inline census
sees fewer shared bodies than the 8-instruction window count suggested: most frequent windows are
argument and idiom runs that do not extend to one maximal body.

## Reproduction and sanitized evidence

`python3 tools/analysis/clusters.py build`, `... rank --exemplars <tsv>`,
`python3 tools/analysis/stamp.py params|emit ...`, `python3 tools/analysis/inline_census.py build|show|export`,
with a private config naming the image, the Ghidra export and the community checkouts. Trial
units and task directories: `<worktree>/.local/stamp-trial/`.

## Negative results and limitations

No compiler ran: every stamped unit is a candidate until `attempt` passes. Jump-table functions
cluster only by identical tables; 8,973 entries are flagged split bodies and keep their own
cluster; Ghidra sizes were corrected for 517 entries. Body ids change whenever the tokenizer changes.
Middleware clusters (std, Havok, Scaleform, Bethesda.net) are ranked out but still counted above.

## Reviewer and outcome

Not reviewed.
