# External contributions: intake into the acceptance pipeline

How a pull request opened with `tools/contrib.py submit` becomes an accepted function. Nothing here
changes the acceptance rule in `docs/verification.md`; an external pull request enters it at the
same point as a Drafter's worktree branch.

## Flow

1. **CI** (`.github/workflows/contrib-intake.yml`, GitHub-hosted, no secrets, no game data) runs the
   contributor-scope checks from the base branch's tools against the pull request's files read as
   data: only `reconstruction/<area>/<Class>.{h,cpp}`, at most 64 KiB per file, the source lint
   (`tools/lint_reconstruction.py`), and no newly added `SIBLING(...)` or `Sibling source:` material.
   `check.yml` runs the usual infrastructure checks.
2. **Pick-up.** The orchestrator treats an open contributor pull request like a finished draft and
   gives it to an Engineer. The Engineer reads the diff (source text, never executed) before
   anything is compiled, re-runs the intake on a local branch
   (`git fetch upstream pull/<n>/head:contrib/pr-<n>`, then
   `python3 tools/contrib.py intake --base main --head contrib/pr-<n>`), and writes the internal
   task directory for the unit as for any draft (`tools/ghidra/export_pack.py` or by hand).
3. **Confirmation.** `tools/verifier/confirm` compiles and compares the unit on two project hosts,
   exactly as for internal drafts. The contributor's local summary is never evidence; it only says
   what to expect.
4. **Review.** A fresh Reviewer (who did not triage the pull request) reviews the unit against the
   blocking grounds. Contributor and AI assistance stated in the header and pull request are read
   like any other provenance statement.
5. **Integration.** The Engineer merges the contributor's commit without squashing, so its author
   stays in history, runs `tools/accept_function.py` as usual, and adds a trailer to the
   acceptance commit for each contributor:
   `Co-authored-by: <name> <email as in the contributor's commit>`. The unit header's `Drafted by`
   line already names them.
6. **Reject.** A `reject` is posted back on the pull request as its blocking reasons only (no bytes,
   listings or private paths; the same filter as naming findings). The contributor revises and the
   pull request re-enters at step 1. An `escalate` follows `docs/verification.md`.

The project's own planner should skip RVAs named by an open claim issue or pull request
(`claim: <build> 0x<rva> ...`); `python3 tools/contrib.py next --json` lists only unclaimed ones.

## Threat note: compiling contributed source

The verifier rule says machines "never run untrusted PR code". Compiling a pull request's C++ does
not execute it, but the compiler itself reads attacker-chosen input:

- **Compiler as attack surface.** `cl.exe` 19.16 under Wine parses arbitrary C++. A crafted file
  could crash it or, in principle, exploit a parser bug to run code on the verifier host, which
  holds the game image. Mitigations in place: verifier hosts hold no credentials, the source is
  read by an Engineer before the first compile, and only `reconstruction/` files are taken from the
  pull request (the tools that compile and compare come from the project's own branch). Remaining:
  no sandbox beyond the machine itself; resource exhaustion (template or macro blow-up) is bounded
  only by a timeout in `tools/contrib.py` (180 s), not in `tools/verifier/unit_build.py`.
- **`#include` abuse.** Reading a host file through an include (a drive letter, `Z:` under Wine, an
  absolute or parent path) would pull it into compiler diagnostics. Enforced: the include closure
  (`tools/source_digest.py`) refuses unresolvable, absolute, symlinked and `..` repository paths;
  the lint now also refuses any include name that is not a plain relative path (no drive letter,
  backslash, leading `/` or `..`), before any compile; the verifier clears `INCLUDE`/`CL`/`_CL_`
  and refuses a build whose `/showIncludes` list leaves the repository and toolchain.
- **`#pragma`, `#import`, `_Pragma`.** Already refused by the lint and the closure scan: pragmas
  other than `once`/`pack`/`warning` (so no `comment(lib)`, `include_alias` or `message`),
  `#import`, `#include_next`, `_Pragma`/`__pragma`, `__has_include`, header units, raw strings and
  trigraphs.
- **Path escapes in the pull request itself.** Only files matching
  `reconstruction/<area>/<Class>.{h,cpp}` pass intake; symlinks and non-UTF-8 files are refused by
  `tools/check.py`.

Open points for the maintainer are listed in the contributor-flow handoff (sandboxing the compile,
a timeout in the verifier's compile, and who may trigger a confirm run for a pull request).
