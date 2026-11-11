# References and attribution

Reviewed 2026-11-11. These references informed project organization and research direction;
no upstream source, text passages, logos, screenshots or site assets were copied into this repo.
Reported upstream achievements have not been independently reproduced here.

- [momusdigital/fnv_decomp](https://github.com/momusdigital/fnv_decomp), reviewed at
  `91e1b6e8d8bb0f9a33e8cf88e77268757449e0a6`: reconstruction and comparison workflow.
  Its LICENSE grants no license; do not copy its implementation or tools.
- [momusdigital/fnv_decomp_exe](https://github.com/momusdigital/fnv_decomp_exe), reviewed at
  `d11951cb936c38252cefbc99eb69d777bf5decd2`: separate local executable-building project.
  Its LICENSE grants no license. Linked as a reference only; Skyrim building is not implemented.
- [FNV report](https://www.fnvdecomp.com/) and [method](https://www.fnvdecomp.com/how):
  public progress, verification and scope communication. Reference only; no reuse permission assumed.
- [Fallout 3 report](https://f3decomp.com/) and [method](https://f3decomp.com/how):
  active-project reporting and work organization. Reference only; no reuse permission assumed.
- [ByteBard97/skyrim-re-toolkit](https://github.com/ByteBard97/skyrim-re-toolkit), reviewed at
  `b5039b37de51c78a04d0319fbdb4c436a339853a`: type archives and runtime research tooling.
  README reports MIT for toolkit/community headers and Apache-2.0 for the parser extension;
  verify actual license files and dependency revisions before importing. Not vendored here.
- [CommonLibSSE-NG](https://github.com/CharmedBaryon/CommonLibSSE-NG): reverse-engineered
  community declarations; MIT at review time. Not vendored or pinned as a dependency here.
- [Mudcrab](https://github.com/Mudcrab-Team/mudcrab): independent Rust engine implementation;
  contextual link only. No source or research material has been transferred between repos.

Original code in this bootstrap uses the Python standard library. GitHub Actions referenced in
workflows execute as hosted dependencies, pinned by commit. No third-party runtime code is bundled.
Future imports need a separate attribution entry with exact revision, license, paths and changes.
