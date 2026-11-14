# A Windows PC as a verifier host

What a Windows machine needs to compile units natively for the matching gate, and what was
measured on the first one. The runner side (`tools/verifier/runners.py`, `host_agent.py`,
`unit_build.py --loader native`) drives it over SSH; this page is the host's half of that contract.
Host names, addresses, accounts and key paths belong in local configuration under `.local/`, never
here.

## Measured result

On a Windows 11 Pro x64 PC (AMD Ryzen 7 7800X3D, 8 cores, 32 GB), compiling natively with the
pinned toolset (cl 19.16.27054; the four binaries in `tools/verifier/pinned.sha256` byte-identical
to the pins) and the pinned recipes, every accepted unit with a two-host match record at the time (83 units,
247 functions, both `msvc-19.16.27054-o2` and `o2-fpfast`) gave, for every function, a comparator
`pass` and the same code-section SHA-256 as both committed hosts, with the same source digest and
the same repository files opened. The comparator ran twice: on the Mac with the objects copied
back, and on the PC itself against a verified copy of the pinned image. The units covered trivial
accessors, deleting destructors with unwind data, BSLightingShaderMaterialBase, and 36 units that
include a header shared with other units (`TESForm.h`, `NiObject.h`). The result was the same with
the toolset unpacked natively on the PC and with a copy of a Wine host's install.

The native install is not file-identical to a Wine host's. The compiler binaries are, but msvc-wine's
`install.sh`, which only Wine hosts run, rewrites the toolset and SDK headers with its `fixinclude`
script (carriage returns removed, include names lowercased): of the 762 files compared, 638 headers
differed, 629 of them by exactly those two changes. None of the other 9 is among the 77 toolset and
SDK headers the accepted units open, and the code bytes above did not change. A native host keeps
Microsoft's headers unmodified.

The same held for objects compiled from a CRLF checkout (code bytes do not depend on line ends),
but the source digest did not: Git for Windows' defaults with `text=auto` check `.cpp`/`.h` out
with CRLF, which changes `tools/source_digest.py`'s digest. `.gitattributes` now pins `*.cpp` and
`*.h` to LF, measured to give a CRLF-free checkout under those defaults.

Timings on that PC: one unit compiles in about 0.04 to 0.15 s; all 83 units in 3.5 s serially and
0.7 s with 8 parallel compiles; 332 compiles ran without an error at 1, 4, 8, 16 and 32 parallel
compiles (14.1, 4.1, 2.6, 2.0 and 1.8 s). One round trip from a Mac on the same network for a
small unit (prepare, upload by sftp, compile, fetch the object by sftp, compare on the Mac) took
2.2 s on an idle link, of which the compile was under 0.2 s; while a Steam download saturated the
PC's Wi-Fi it took 29 s, or 13 s with SSH connection sharing (`ControlMaster`). The network, not
the compiler, limits such a host.

Unpacking the toolset and SDK natively took 43 s once the 747.9 MB of payloads (41 packages, the
same selection as on the Mac) were in vsdownload.py's cache.

The contributor path ran on the same PC from a clone with Git for Windows' defaults: `.\sr.cmd
doctor`, `setup --exe <image> --no-install --no-sources --no-sibling` with `SR_MSVC` pointing at
the native toolset (its self-test passed), and `compare` on a practice task (pass). LLVM, the
community sources and the Steam lookup of the image were not exercised there.

## What must be installed

- OpenSSH Server with key-only login for the account the runner uses. The default shell is
  Windows PowerShell 5.1; with execution policy `Restricted`, send commands inline or with
  `-EncodedCommand`, never as `.ps1` files.
- Python 3.11 or newer (standard library only). Call it by full path, for example
  `%LOCALAPPDATA%\Programs\Python\Python312\python.exe`: `python` on PATH may be the Microsoft Store
  alias, which does not run Python.
- The pinned toolset and SDK, unpacked natively by msvc-wine's `vsdownload.py` at the commit and
  with the manifest and options of `tools/verifier/setup_boat_machine.sh` (`--major 15 --host-arch
  x64 --architecture x64 --with-default no --with-msvc yes --with-sdk yes --sdk-version 10.0.19041
  --accept-license --dest <toolchain>`). On Windows it unpacks the SDK with `msiexec /a` (an
  administrative extract: no installation, no registry entries), which works from an SSH session.
  Running it accepts Microsoft's licence for whoever runs it. msvc-wine's `install.sh` is not used.
  On a slow link, fill vsdownload.py's `--cache` directory first (for example with
  `--only-download --cache <dir>` on a faster machine, then a copy): it checks every cached payload
  against the pinned manifest's SHA-256 before using it and downloads only what is missing.
- For comparing on the host as well: the pinned image, checked against `builds/target.json`.

Nothing else is needed: no Visual Studio installer, no `vcvars`, no PATH change.

## Layout

```
<toolchain>\VC\Tools\MSVC\14.16.27023\bin\Hostx64\x64\cl.exe   (c1xx.dll, c2.dll, link.exe beside it)
<toolchain>\VC\Tools\MSVC\14.16.27023\include, atlmfc\include
<toolchain>\Windows Kits\10\Include\10.0.19041.0\shared, ucrt, um, winrt
<work>\<run>\                                                    one fresh copy per run
```

Exactly one toolset directory and one SDK include version must exist under `<toolchain>`.

## Compile

From the root of the unit's repository copy, with `INCLUDE`, `LIB`, `LIBPATH`, `CL`, `_CL_` and
`EXTERNAL_INCLUDE` removed from the environment and `INCLUDE` then set to exactly these directories,
in this order (the order msvc-wine's `msvcenv.sh` uses):

```
<msvc>\atlmfc\include;<msvc>\include;<sdk>\shared;<sdk>\ucrt;<sdk>\um;<sdk>\winrt;<sdk>\km
```

where `<msvc>` is `<toolchain>\VC\Tools\MSVC\14.16.27023` and `<sdk>` is
`<toolchain>\Windows Kits\10\Include\10.0.19041.0` (`km` does not exist in this SDK; listing it
keeps the list identical to the Wine hosts'). Then:

```
<msvc>\bin\Hostx64\x64\cl.exe <recipe flags> /showIncludes /Fo<absolute object path> <compiled .cpp>
```

`/showIncludes` prints absolute Windows paths; repository files appear under the copy's root.

## Files in and out

Unit sources, the recipe and anything else the run needs go to the host as files (scp or sftp,
whose Windows paths are written `/C:/...`), never on a command line; the object and the sanitized
report come back the same way. Standard input also carries binary data intact to a Python process
started over SSH, which saves the separate sftp session where that matters. Copies made this way
keep their LF line ends; a Git clone on the host relies on `.gitattributes`.

### Concurrent confirmations and transport failures

Use green-main runner tooling. Each SSH host's private `runners.json` may set `max_sessions`
(default 4), independently of `max_parallel` compile jobs and batch size. All SSH commands and
SCP transfers, including probes and cleanup, take a cross-process session slot. Locks live in
`runner-sessions/` beside the selected shared runner configuration; `SR_VERIFIER_STATE` overrides
that state directory. Independent worker clones must select the same configuration with
`SR_RUNNERS_CONFIG` or the same state with `SR_VERIFIER_STATE`, and use the same per-host limit.
A dead client releases its slots automatically. No Windows service configuration change is needed.

Connection failures (SSH/SCP exit 255, SCP connection-reset/closed errors, or OS connection errors)
get at most three total attempts, with 1- and 2-second backoff. Each failure is logged as a
`transport_error` in private `transport-errors.jsonl` and the caller's log. Exhaustion remains an
infrastructure error, never comparison evidence. Other SSH exits, including a comparator mismatch,
are returned once. Retries reuse the exact run identity: if the connection failed after the agent
created its run directory, the agent refuses duplicate execution rather than comparing again.
Such an incomplete confirmation needs explicit recovery after its worker finishes; transport
retries never turn a mismatch into a pass.

## Things that stall from SSH

Background Intelligent Transfer Service downloads, `winget`, the Microsoft Store and the Visual
Studio installer wait for an interactive logon and must not be used from SSH. `curl.exe` and
Python's `urllib` work. A process that must outlive the SSH session (a long download, for
example) is started through `Win32_Process.Create` (CIM), which places it outside the session's
job object; anything long runs in the background with a log and is polled. Directory listings
show a stale size for a file that is still being written; open it to read its real length.
