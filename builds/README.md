# Target manifests

`target.json` is public metadata, initially unselected. Use `tools/fingerprint.py` to prepare a
private candidate. Review the actual release identity and hash before pinning. An executable
hash is identity metadata, not permission to distribute that executable. Never copy game files
here. Additional build manifests need distinct IDs; do not merge address spaces across versions.
