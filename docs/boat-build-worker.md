# Boat as a build worker candidate

Status: RESEARCHED, NOT REPRODUCED. Checked against official documentation 2026-11-11.
No account, machine, compiler installation or proprietary input upload was performed.
Research assistance: Codex subagent; human maintainer remains responsible for acceptance.

## Fit

Boat provides x86-64 Ubuntu 24.04 sandboxes, remote SSH/SCP, CLI/API access and GitHub CI
integration. It has no GPU and no Windows runner. This makes it a candidate for static
analysis and compilation from an Apple Silicon Mac, not an established Skyrim/SKSE runtime
host. Boat documents Wine for Windows console builds. Exact legacy MSVC under Wine needs an
experiment; producing an EXE with MinGW or Clang would not establish original-compiler matching.

Sources: [machines](https://docs.boat.dev/machines), [CI](https://docs.boat.dev/ci).

## Alternative: nested Windows

Boat exposes `/dev/kvm` and CPU virtualization extensions. A separately licensed nested x64
Windows guest is technically plausible, but the documented examples do not establish a
supported Windows/MSVC configuration. vCPUs are shared. Do not promise game launch, SKSE,
debugger behavior or representative performance measurements before testing.

Source: [virtualization](https://docs.boat.dev/machines/virtualization).

## Cost and retention

At review time the minimum plan was $20/month credited toward compute, with credits expiring
at the end of the billing period. Running compute is billed per second. Small (2 vCPU, 4 GB,
51 GB disk) was $0.018/hour; default (4 vCPU, 8 GB, 51 GB disk) $0.036/hour; large (8 vCPU,
16 GB, 111 GB disk) $0.072/hour. Occasional use still incurs the minimum plan charge.
The seven-day trial requires a card and includes 25 compute hours. Prices can change.

Stopped machines do not incur compute charges, but their disk is retained for at least
14 days rather than guaranteed indefinitely. Saved snapshots have no scheduled expiration;
ten were included in the $20 plan and extra snapshots cost $0.056/day each. Default auto-stop
is one hour: long imports/builds need an explicit deadline. Treat memory/processes as disposable,
keep original infrastructure in Git, and keep authorized private backups independently.

Sources: [pricing](https://docs.boat.dev/pricing), [limits](https://docs.boat.dev/limits).

## Private data and public CI

Boat's terms authorize service operation including processing and snapshots, while placing
responsibility for necessary rights on the customer. Its privacy policy states foundation
models are not trained on sandbox contents; access for operations, support, abuse and legal
purposes is still possible. Those terms do not establish rights to upload Skyrim binaries,
proprietary symbols, SDKs or Microsoft compiler packages. Review relevant licenses and obtain
explicit maintainer authorization for those inputs separately. Start with synthetic/original code.
Never put credentials in the repository or expose proprietary inputs to untrusted PR jobs.

Sources: [terms](https://boat.dev/terms), [privacy](https://boat.dev/privacy).

## First experiment and acceptance criteria

1. With explicit provisioning scope and a cost limit, create an x86-64 Linux sandbox.
2. Compile original synthetic C++ using an authorized exact MSVC toolchain under Wine.
3. Record compiler hash, SDK provenance, flags and host details; reproduce identical output.
4. Exercise the future relocation-aware comparator only on synthetic inputs initially.
5. Stop/delete resources as intended and verify retained data/snapshots and billing state.

If Wine fails, evaluate a licensed nested Windows guest as a separate experiment. Do not
substitute a different compiler and report it as a successful matching-worker validation.
