# Maintaining the project report

The public report is generated from `data/progress.json` at each push to `main` and manual
workflow dispatch. It needs no accounts, trackers, backend, third-party fonts or external APIs.
It links to GitHub issues for discussion. Edit the JSON and submit a reviewed commit to change
the displayed state; GitHub issue edits alone do not change it.

```sh
python3 tools/check.py
python3 tools/build_site.py
```

Open `dist/index.html`. `dist/progress.json` is the same validated public metadata. `dist/` is
ignored; GitHub Actions generates and deploys it. Only that generated directory is uploaded.
The commit shown on the site identifies the version used to generate the report. CI uses Python
3.12; local tools support Python 3.11+. No Python package installation is required.

Bootstrap intentionally has no scope denominator, trend chart, cost estimates or leaderboard.
These require real accepted records. A GitHub Projects board is optional issue organization;
the versioned JSON remains authoritative for the public report. The maintainer's current CLI
token lacked Projects scopes at bootstrap, so board creation may require separate authorization.
The repository's Issues queue remains usable without those scopes.
