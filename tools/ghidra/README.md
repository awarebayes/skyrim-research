# Context packs and Drafter tasks from Ghidra

`export_pack.py` turns a list of `(build id, RVA)` into private per-function context packs and the
task directories that `tools/verifier/attempt` consumes, so preparing a function for a Drafter is
one command instead of an Engineer's hand analysis. `ExportPack.java` is the headless Ghidra
script it runs; `community_ids.py` reads Address Library ids and names from a CommonLibSSE checkout.
All three are original code and contain no game data. **Everything they write is game-derived and
stays under `.local/`** (G1 and G2 in `docs/authorizations.md`); never copy a pack into a tracked
file, issue, PR, log or upload.

## Setup

A private config, by default `.local/config/export_pack.json`, holds every machine-specific path:

| key | meaning |
|---|---|
| `analyze_headless`, `java_home`, `maxmem` | Ghidra 12.2 `support/analyzeHeadless`, a JDK it accepts, heap size |
| `project_dir`, `project_name`, `program` | an analysed project of the pinned image, opened `-readOnly` |
| `image` | the pinned executable; its SHA-256 must equal `builds/target.json` or the tool stops |
| `addrlib` | Address Library database for the pinned version (format 5, as shipped for 1.7.x) |
| `ng_root`, `ng_revision` | CommonLibSSE-NG checkout (MIT) and its commit |
| `po3_root`, `po3_revision` | optional powerof3/CommonLibSSE checkout (GPL-3.0): local naming fallback only |

Names, headers and excerpts come from NG first. Anything found only in the powerof3 fork is written
to a file whose name ends in `.GPL-local-only.*`; do not publish or paste from those files.

## Commands (repository root)

```sh
python3 tools/ghidra/export_pack.py packs <list file> [--recipe msvc-19.16.27054-o2] [--max-attempts 12]
python3 tools/ghidra/export_pack.py survey --sample 2000 --seed 1     # suitability only, random functions
python3 tools/ghidra/export_pack.py survey --named                    # every NG-named function
python3 tools/ghidra/export_pack.py bind --task .local/tasks/<id> [--object <candidate.obj>]
```

List file: one function per line, `<build id> <rva> <task id> [<unit .cpp>]`, `#` comments.
Lines with the same task id form one task and must name the same unit (or none: the tool then
reuses `reconstruction/*/<Class>.cpp` if it exists, else proposes `reconstruction/<area>/<Class>.cpp` by the
prefix rule of `reconstruction/README.md` and stops when no rule covers the class).
Only the pinned build is accepted; addresses never transfer between builds.

Timing on the maintainer's Mac (Ghidra 12.2, project already analysed): about 8 to 9 s of fixed
Ghidra start-up per run, then roughly 0.003 s per function for the listing and decompilation of a
random sample. A run of 8 functions took 8.6 s (1.1 s per function); 2,000 functions took 15.7 s
(0.01 s per function). Batch many functions per run.

## Pack: `.local/packs/<build id>/<rva>/`

- `README.md`: summary for the Drafter (size, community name and its source, owning class,
  unwind form, verdict, references table, unnamed targets).
- `pack.json`: the same, machine-readable (`pack_schema` 1).
- `listing.txt`, `decompiled.c`: Ghidra instruction listing with reference targets, decompiler output.
- `class-excerpt.h`: the owning class body from the community header, trimmed when over 4 KB to
  its declaration head, access specifiers, virtuals, the method itself and the members whose
  offset comments match an observed displacement; `source-excerpt.cpp`: the community line that
  ties the name to the Address Library id; `reference-decls.h`: declarations of the referenced
  members (or the community wrapper around a free function's id).
- `vtables.txt`: for the owning class and each RTTI base (read from the image's complete object
  locator), the slot table from the community `VTABLE_<Class>` id: slot, byte offset, target RVA,
  Address Library name and the virtual the community header declares for that slot.
- `signature-types.h`: trimmed community declarations of the types named in the function's
  declaration (MIT sources only).
- README sections "Observed memory operands" (non-stack displacements, base register, width,
  instruction offset) and "Calling and return convention" (`this` in RCX, parameter registers,
  the MSVC x64 rule for returning a class by value through a hidden pointer).
- `python3 tools/ghidra/export_pack.py refresh <pack dir>...` rebuilds these aids for existing
  packs without running Ghidra.

### Comparator v1 verdict

`unsupported` when any of these hold (each is a contract v1 refusal, `docs/comparator-contract.md`):
`exception-handler`, `chained-unwind`, `unwind-version`, `multiple-pdata`, `pdata-not-at-entry`,
`split-body` (analysis body not contiguous), `addr64` (a DIR64 base relocation patches the range),
`jump-table` (an indirect jump with two or more recovered targets), `thunk`, `import-thunk`,
`unresolvable-reference` (a reference into the middle of another function, or outside the image),
`not-a-function`. `caution` when the function is supported but needs care: no `.pdata` (a leaf whose
size comes from the analysis; flagged again when code rather than int3 padding follows it), an
indirect jump without recovered targets, a referenced function or datum without an Address Library
id, a string literal, code addresses outside any analysed function. Otherwise `supported`.

References are classified as `addrlib-id`, `constant` (`__real@`/`__xmm@` names derived from the
literal's contents), `import` (`__imp_<name>`, the IAT slot), `image-base` (`__ImageBase`),
`string-literal`, `function-no-id`, `data-no-id`, `code-no-function`, `mid-function`.
Branches inside the function and segment-relative operands (TLS through `gs:`) carry no
relocation and are not listed.

## Task: `.local/tasks/<task id>/`

`task.json` is the format `tools/verifier/pipeline.py` reads (`load_task`); extra keys are ignored
by it and kept for people:

```json
{"task_id": "second-batch-a",
 "build_id": "sse-steam-1-7-104",
 "compiled": "reconstruction/<area>/<Class>.cpp",
 "recipe": "reconstruction/recipes/msvc-19.16.27054-o2.json",
 "symbols": "symbols.json",
 "functions": [{"rva": "0x...", "size": 53, "symbol": "unbound:Class::Method",
                "function_id": "sse-steam-1-7-104-0x...", "community_name": "Class::Method",
                "name_origin": "COMMUNITY", "verdict": "supported", "pack": ".local/packs/..."}],
 "max_attempts": 12,
 "export": {"generator": "tools/ghidra/export_pack.py", "task_schema": 1,
            "target_image_sha256": "...", "unit_already_records": []}}
```

- One task is one translation unit and one recipe; several functions of one unit share a task.
- `symbol` is the placeholder `unbound:<community name>` until binding fills it. The comparator
  identifies the candidate only by that exact decorated name (external, at offset 0 of its own `/Gy`
  COMDAT), and the name depends on the Drafter's declarations, so it cannot be derived before the
  first compile. `tools/verifier/attempt` binds after each compile and compares again in the same
  run; a run that compared nothing because of binding is not counted against `max_attempts`.
- If the unit already backs a match record, `unit_already_records` lists it and the accepted
  function is added to `functions` with `"role": "regression"`, so every attempt re-checks it. An
  edit to the unit changes its digest and leaves that record stale until it is re-verified.
- `symbols.json` is the comparator symbol map (schema 1). The exporter pre-fills only names it can
  derive (constants, imports, `__ImageBase`); re-running the exporter keeps entries already bound.

Binding (`tools/verifier/bind.py`, run by `attempt`; `export_pack.py bind` runs it by hand) reads
the compiled object. A task function is bound by a hint, by keeping a symbol the object still
defines, by the one defined function whose qualified name (template arguments, types and
parameters dropped, demangled with `llvm-undname` when available) equals the community name, or
by the one whose member name does; so Drafters' class names may differ from the community ones.
A symbol that disappears and is replaced is reported as "decorated name changed" with both names.
A reference is bound by a hint, by position (the target's own relocated field at the same offset,
decoded from the local image, accepted only if it is one of the pack's listed targets), or by a
unique community or member name. What remains is listed with the file to edit:
`<task dir>/bind-hints.json`, a JSON object of decorated or qualified name -> RVA (format in the
module docstring). `symbols.json` and `task.json` are written by the tools, not by hand. A wrong
binding cannot produce a pass, because the comparator checks every relocation against the image.

## Limits

- Suitability is a prediction from the image and the analysis; only the comparator decides.
- Community names are joined through the Address Library by id. For wrappers the name is the
  nearest enclosing definition (`how: enclosing`), a heuristic that is sometimes wrong.
- The exporter applies only the prefix rule for areas; an owning-system area is passed in the list file.
