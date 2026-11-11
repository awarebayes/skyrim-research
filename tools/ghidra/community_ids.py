"""Collect Address Library id -> community name associations from a CommonLibSSE checkout.

Works on CommonLibSSE-NG and on the powerof3 fork, which share the RELOCATION_ID(se, ae) and
VariantID(se, ae, vr) conventions. Output rows: (ae_id, se_id, kind, name, how, source), where
kind is vtable, rtti, nirtti, func, data, offset or unknown, and how is 'table' when the name is
the declared identifier or 'enclosing' when it is the nearest preceding definition (a heuristic
that callers must label as such). source is 'path:line' inside the checkout.
"""
import os
import re

VAR = re.compile(r"VariantID\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(0x[0-9a-fA-F]+|\d+)\s*\)")
REL = re.compile(r"(?:RELOCATION_ID|REL::RelocationID)\(\s*(\d+)\s*,\s*(\d+)\s*\)")
ARR = re.compile(r"\b((?:VTABLE|RTTI|NiRTTI)_\w+)\s*[\{\(]")
CONST = re.compile(r"constexpr\s+auto\s+(\w+)\s*=\s*RELOCATION_ID")
NS = re.compile(r"^\s*namespace\s+([\w:]+)")
CLS = re.compile(r"^\s*(?:class|struct)\s+(?:\w+\s+)?(\w+)\s*(?:final\s*)?(?::[^;{]*)?\s*$")
DEF = re.compile(r"([~\w]+(?:::[~\w]+)*)\s*\([^;]*$")
SKIP = {"if", "for", "while", "switch", "return", "sizeof", "decltype", "static_assert",
        "REL", "func", "singleton", "assert", "using"}
TABLE_FILES = ("Offsets_VTABLE.h", "Offsets_RTTI.h", "Offsets_NiRTTI.h")


def _scan_tables(path, rel, out):
    with open(path, encoding="utf-8", errors="replace") as fh:
        for n, line in enumerate(fh, 1):
            m = ARR.search(line)
            if not m:
                continue
            name = m.group(1)
            kind = "vtable" if name.startswith("VTABLE_") else ("nirtti" if name.startswith("NiRTTI_") else "rtti")
            hits = list(VAR.finditer(line))
            if not hits:
                # RTTI tables declare `VariantID NAME(se, ae, vr)`, so the numbers follow the name.
                hits = list(re.finditer(re.escape(name) + r"\(\s*(\d+)\s*,\s*(\d+)\s*,", line))
            for k, v in enumerate(hits):
                label = name + ("[%d]" % k if kind == "vtable" else "")
                out.append((int(v.group(2)), int(v.group(1)), kind, label, "table", "%s:%d" % (rel, n)))


def _scan_code(path, rel, out):
    ns, ns_depths = [], []
    depth = 0
    last_cls = last_def = pending_ns = None
    with open(path, encoding="utf-8", errors="replace") as fh:
        lines = list(fh)
    for n, line in enumerate(lines, 1):
        s = line.split("//", 1)[0]
        mn = NS.match(s)
        if mn:
            pending_ns = mn.group(1)
        mc = CLS.match(s)
        if mc:
            last_cls = mc.group(1)
        md = DEF.search(s)
        if md and "RELOCATION_ID" not in s and not s.strip().startswith(("using", "return", "#")):
            if md.group(1).split("::")[-1] not in SKIP:
                last_def = md.group(1)
        for m in REL.finditer(s):
            se, ae = int(m.group(1)), int(m.group(2))
            mconst = CONST.search(s)
            if mconst:
                out.append((ae, se, "offset", "::".join(ns + [mconst.group(1)]), "table", "%s:%d" % (rel, n)))
                continue
            compact = s.replace(" ", "")
            kind = "func" if ("func_t" in s or "decltype(&" in s) else ("data" if "*>" in compact else "unknown")
            base = last_def or "?"
            if "::" not in base and last_cls and rel.endswith(".h"):
                base = last_cls + "::" + base
            out.append((ae, se, kind, base, "enclosing", "%s:%d" % (rel, n)))
        opens, closes = s.count("{"), s.count("}")
        if pending_ns and opens:
            parts = pending_ns.split("::")
            ns.extend(parts)
            ns_depths.append((depth, len(parts)))
            pending_ns = None
        depth += opens - closes
        while ns_depths and depth <= ns_depths[-1][0]:
            _, cnt = ns_depths.pop()
            del ns[-cnt:]


def scan(root):
    out = []
    for sub in ("include", "src"):
        for d, _, files in sorted(os.walk(os.path.join(root, sub))):
            for f in sorted(files):
                if not f.endswith((".h", ".cpp", ".hpp")) or f == "PCH.h":
                    continue
                p = os.path.join(d, f)
                rel = os.path.relpath(p, root)
                (_scan_tables if f in TABLE_FILES else _scan_code)(p, rel, out)
    return out
