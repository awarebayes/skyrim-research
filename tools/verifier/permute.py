#!/usr/bin/env python3
"""Source permuter for one near-miss function: seeded rewrites, batch compiles, no model in the loop.

    tools/verifier/permute.py run <task-dir> --rva 0x... [--function Class::Name] [--also Class::Helper]
        [--source-root DIR] [--budget 600] [--batch 16] [--patience 8] [--seed 1] [--out DIR]
        [--transport scp|inline] [--no-resume] [--dry-run]
    tools/verifier/permute.py mutate <file.cpp> --function Class::Name [--steps 3] [--seed 1]

`run` reads the unit of a task directory (task.json as for `attempt`), finds the definition of the
target function in the compiled file, and searches for a variant of that one body whose object
code is closer to the target:

1. Mutations are deterministic, seeded rewrites at token and statement level (no C++ parser):
   the mechanisable rules of docs/matching-cookbook.md and docs/ideas-next.md P3 (R1 to R7), listed
   in MUTATIONS. Each one keeps ordinary C++; a few (temporaries, widths, signedness) can change
   meaning, which is harmless for the search because only a byte-identical object counts, and the
   Reviewer still reads the winner against the target.
2. Every candidate must pass tools/lint_reconstruction.py before it is compiled.
3. Candidates go to the standing verifier in batches: the candidate bodies (compressed) are
   uploaded as one file (or, with `--transport inline`, carried in the command line), and ONE
   `boat exec` per batch returns one sanitized line per candidate (distance from
   align.py, its components, instruction counts, a hash of the function's object code, seconds).
   The machine compiles them in parallel (`--jobs`, default 4 = its vCPUs), each worker in its
   own hard-linked copy of the unit, with the recipe's flags and the environment unit_build uses.
4. Search: greedy hill-climb over batches with sideways moves, random restarts from the best,
   and a seen-set keyed by the function's object-code hash. Stops at distance 0, at the Boat time
   budget, or after --patience batches without a new best.
5. At distance 0 the winning unit is compiled and compared once more by unit_build.py (the real
   comparator, all of the task's functions). Only that report says pass; run `attempt` on the
   winning source before anything is reviewed.

Outputs (private, under the task's .local tree unless --out): `best.cpp` (the unit with the best
body), `history.jsonl` (one row per scored candidate: id, parent, mutations, score), `result.json`
(start and best distance, candidates, Boat seconds, comparator result) and the comparator's
files under `final/`. Nothing game-derived is printed. Wall time of the run is queued to the cost
ledger as stage `draft`, as `attempt` does. `mutate` prints a mutated copy of a local file; it
is for tests and for perturbing a matched unit in a recovery self-test.
"""
import argparse
import base64
import copy
import hashlib
import json
import os
from pathlib import Path
import random
import re
import shlex
import shutil
import sys
import time
import zlib

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
REMOTE_TOOLS = ('tools/verifier/permute.py', 'tools/verifier/align.py', 'tools/verifier/disasm.py')

# --------------------------------------------------------------------------------------------
# Tokens: every token keeps the whitespace and comments before it, so emit(parse(x)) == x.

TOKEN = re.compile(r'''
   (?P<str>(?:u8|[uUL])?"(?:\\.|[^"\\\n])*"|'(?:\\.|[^'\\\n])*')
  |(?P<num>\.?[0-9](?:[A-Za-z0-9_.]|[eEpP][+-])*)
  |(?P<id>[A-Za-z_][A-Za-z0-9_]*)
  |(?P<pp>\#[^\n]*)
  |(?P<op>::|->|\+\+|--|<<=|>>=|<<|>>|<=|>=|==|!=|&&|\|\||[-+*/%&|^]=|\.\.\.|[{}()\[\];,<>=+\-*/%&|^!~?:.])
''', re.X)
TRIVIA = re.compile(r'(?:\s+|//[^\n]*|/\*.*?\*/)*', re.S)


class Tok:
    __slots__ = ('kind', 'text', 'pre')

    def __init__(self, kind, text, pre=' '):
        self.kind, self.text, self.pre = kind, text, pre

    def __repr__(self):
        return f'Tok({self.text!r})'


def lex(text):
    toks, i = [], 0
    while True:
        m = TRIVIA.match(text, i)
        pre, i = m.group(0), m.end()
        if i >= len(text):
            return toks, pre
        m = TOKEN.match(text, i)
        if not m:
            raise ValueError(f'cannot tokenise at offset {i}')
        toks.append(Tok(m.lastgroup, m.group(0), pre))
        i = m.end()


def emit_toks(toks):
    return ''.join(t.pre + t.text for t in toks)


def new(text, pre=' '):
    kind = 'id' if re.fullmatch(r'[A-Za-z_]\w*', text) else 'num' if text[:1].isdigit() else 'op'
    return Tok(kind, text, pre)


def toks_of(text, pre=' '):
    out, _ = lex(text)
    if out:
        out[0].pre = pre
    return out


# --------------------------------------------------------------------------------------------
# Statements. A body is a Block; nodes hold token lists, so emitting them reproduces the source.

class Node:
    kind = 'node'

    def toks(self):
        raise NotImplementedError


class Simple(Node):
    """Declaration, expression, return, break, continue: tokens up to and including `;`."""
    kind = 'simple'

    def __init__(self, toks):
        self.t = toks

    def toks(self):
        return list(self.t)


class Label(Node):
    kind = 'label'

    def __init__(self, toks):
        self.t = toks

    def toks(self):
        return list(self.t)


class Block(Node):
    kind = 'block'

    def __init__(self, lb, stmts, rb):
        self.lb, self.stmts, self.rb = lb, stmts, rb

    def toks(self):
        out = [self.lb]
        for s in self.stmts:
            out += s.toks()
        return out + [self.rb]


class If(Node):
    kind = 'if'

    def __init__(self, head, cond, rp, then, else_kw=None, els=None):
        self.head, self.cond, self.rp, self.then, self.else_kw, self.els = head, cond, rp, then, else_kw, els

    def toks(self):
        out = list(self.head) + list(self.cond) + [self.rp] + self.then.toks()
        if self.els is not None:
            out += [self.else_kw] + self.els.toks()
        return out


class Loop(Node):
    """for, while and switch: keyword, `(`, header tokens, `)`, body."""

    def __init__(self, kw, lp, inner, rp, body):
        self.kind = kw.text
        self.kw, self.lp, self.inner, self.rp, self.body = kw, lp, inner, rp, body

    def toks(self):
        return [self.kw, self.lp] + list(self.inner) + [self.rp] + self.body.toks()


class Opaque(Node):
    """do-while and try/catch: token runs and nested statements in order."""
    kind = 'opaque'

    def __init__(self, parts):
        self.parts = parts

    def toks(self):
        out = []
        for p in self.parts:
            out += p.toks() if isinstance(p, Node) else list(p)
        return out


def _balanced(toks, i):
    """Index just past the group opened at toks[i] (one of ( [ {)."""
    pairs = {'(': ')', '[': ']', '{': '}'}
    stack = []
    while i < len(toks):
        t = toks[i].text
        if t in pairs:
            stack.append(pairs[t])
        elif t in (')', ']', '}'):
            if not stack or stack.pop() != t:
                raise ValueError('unbalanced brackets')
            if not stack:
                return i + 1
        i += 1
    raise ValueError('unbalanced brackets')


def parse_block(toks, i):
    if toks[i].text != '{':
        raise ValueError('block expected')
    lb, i, stmts = toks[i], i + 1, []
    while i < len(toks) and toks[i].text != '}':
        st, i = parse_stmt(toks, i)
        stmts.append(st)
    if i >= len(toks):
        raise ValueError('unterminated block')
    return Block(lb, stmts, toks[i]), i + 1


def _paren(toks, i):
    if toks[i].text != '(':
        raise ValueError('( expected')
    end = _balanced(toks, i)
    return toks[i], toks[i + 1:end - 1], toks[end - 1], end


def parse_stmt(toks, i):
    t = toks[i].text
    if t == '{':
        return parse_block(toks, i)
    if t == 'if':
        head = [toks[i]]
        i += 1
        if toks[i].text == 'constexpr':
            head.append(toks[i])
            i += 1
        lp, cond, rp, i = _paren(toks, i)
        then, i = parse_stmt(toks, i)
        if i < len(toks) and toks[i].text == 'else':
            kw = toks[i]
            els, i = parse_stmt(toks, i + 1)
            return If(head + [lp], cond, rp, then, kw, els), i
        return If(head + [lp], cond, rp, then), i
    if t in ('for', 'while', 'switch'):
        kw = toks[i]
        lp, inner, rp, i = _paren(toks, i + 1)
        body, i = parse_stmt(toks, i)
        return Loop(kw, lp, inner, rp, body), i
    if t == 'do':
        body, j = parse_stmt(toks, i + 1)
        end = j
        while toks[end].text != ';':
            end = _balanced(toks, end) if toks[end].text in '([{' else end + 1
        return Opaque([[toks[i]], body, toks[j:end + 1]]), end + 1
    if t == 'try':
        block, j = parse_block(toks, i + 1)
        parts = [[toks[i]], block]
        while j < len(toks) and toks[j].text == 'catch':
            end = _balanced(toks, j + 1)
            handler, k = parse_block(toks, end)
            parts += [toks[j:end], handler]
            j = k
        return Opaque(parts), j
    if t in ('case', 'default') or (toks[i].kind == 'id' and i + 1 < len(toks) and toks[i + 1].text == ':'
                                    and t not in KEYWORDS):
        j = i
        while toks[j].text != ':':
            j += 1
        return Label(toks[i:j + 1]), j + 1
    j = i
    while j < len(toks) and toks[j].text != ';':
        if toks[j].text in ('(', '[', '{'):
            j = _balanced(toks, j)
        elif toks[j].text == '}':
            raise ValueError('statement without ;')
        else:
            j += 1
    if j >= len(toks):
        raise ValueError('statement without ;')
    return Simple(toks[i:j + 1]), j + 1


def parse_body(text):
    """(Block, trailing trivia) of a `{ ... }` body text."""
    toks, tail = lex(text)
    block, i = parse_block(toks, 0)
    if i != len(toks):
        raise ValueError('text after the body')
    return block, tail


def emit(block, tail=''):
    return emit_toks(block.toks()) + tail


# --------------------------------------------------------------------------------------------
# Locating the function definition in the compiled file.

def find_body(text, qualified):
    """(start, end) of the `{ ... }` body of the definition of `qualified` (e.g. "TESFile::Seek")."""
    parts = qualified.split('::')
    toks, _ = lex(text)
    offsets, pos = [], 0
    for t in toks:
        pos += len(t.pre)
        offsets.append(pos)
        pos += len(t.text)
    names = [t.text for t in toks]
    want = []
    for p in parts:
        want += [p, '::']
    want = want[:-1]
    hits = []
    for i in range(len(toks) - len(want)):
        if names[i:i + len(want)] != want or (i and names[i - 1] == '::'):
            continue
        j = i + len(want)
        if j >= len(toks) or names[j] != '(':
            continue
        j = _balanced(toks, j)
        # qualifiers between ) and { : const, noexcept, override, -> type; a `;` means a declaration
        while j < len(toks) and names[j] not in ('{', ';', ':'):
            j = _balanced(toks, j) if names[j] in ('(', '[') else j + 1
        if j < len(toks) and names[j] == '{':
            end = _balanced(toks, j)
            hits.append((offsets[j], offsets[end - 1] + 1))
    if len(hits) != 1:
        raise ValueError(f'{qualified}: {len(hits)} definitions found in the compiled file (need exactly 1)')
    return hits[0]


# --------------------------------------------------------------------------------------------
# Tree helpers.

KEYWORDS = {'return', 'if', 'else', 'for', 'while', 'do', 'switch', 'case', 'default', 'break', 'continue',
            'goto', 'new', 'delete', 'sizeof', 'static_cast', 'reinterpret_cast', 'const_cast',
            'dynamic_cast', 'throw', 'try', 'catch', 'typedef', 'using', 'operator', 'alignof', 'decltype',
            'noexcept', 'static_assert', 'this', 'nullptr', 'true', 'false'}
TYPE_WORDS = {'unsigned', 'signed', 'short', 'long', 'int', 'char', 'bool', 'float', 'double', 'void',
              'auto', 'const', 'volatile', 'static', 'wchar_t', '__int64', 'std', 'struct', 'class'}
ASSIGN_OPS = {'=', '+=', '-=', '*=', '/=', '%=', '&=', '|=', '^=', '<<=', '>>='}


def walk_blocks(node):
    """Every Block in the tree, outermost first."""
    if isinstance(node, Block):
        yield node
        for s in node.stmts:
            yield from walk_blocks(s)
    elif isinstance(node, If):
        yield from walk_blocks(node.then)
        if node.els is not None:
            yield from walk_blocks(node.els)
    elif isinstance(node, Loop):
        yield from walk_blocks(node.body)
    elif isinstance(node, Opaque):
        for p in node.parts:
            if isinstance(p, Node):
                yield from walk_blocks(p)


def walk_nodes(node):
    yield node
    if isinstance(node, Block):
        for s in node.stmts:
            yield from walk_nodes(s)
    elif isinstance(node, If):
        yield from walk_nodes(node.then)
        if node.els is not None:
            yield from walk_nodes(node.els)
    elif isinstance(node, Loop):
        yield from walk_nodes(node.body)
    elif isinstance(node, Opaque):
        for p in node.parts:
            if isinstance(p, Node):
                yield from walk_nodes(p)


def expr_lists(root):
    """Mutable token lists that hold expressions: simple statements, conditions, loop headers."""
    out = []
    for n in walk_nodes(root):
        if isinstance(n, Simple):
            out.append(n.t)
        elif isinstance(n, If):
            out.append(n.cond)
        elif isinstance(n, Loop):
            out.append(n.inner)
    return out


def uses(toks, name):
    """Positions where identifier `name` is used as a variable (not as a member or qualified name)."""
    return [i for i, t in enumerate(toks) if t.text == name and t.kind == 'id'
            and not (i and toks[i - 1].text in ('.', '->', '::'))
            and not (i + 1 < len(toks) and toks[i + 1].text == '::')]


def node_mentions(node, name):
    return bool(uses(node.toks(), name))


def has_call(toks):
    return any(t.text == '(' and i and (toks[i - 1].kind == 'id' or toks[i - 1].text in (')', ']', '>'))
               and toks[i - 1].text not in KEYWORDS - {'this'}
               for i, t in enumerate(toks))


def written(toks, name):
    """True when `name` is assigned, incremented or has its address taken in `toks`."""
    for i in uses(toks, name):
        nxt = toks[i + 1].text if i + 1 < len(toks) else ''
        prv = toks[i - 1].text if i else ''
        if nxt in ASSIGN_OPS or nxt in ('++', '--') or prv in ('++', '--'):
            return True
        if prv == '&' and (i < 2 or toks[i - 2].kind != 'id' and toks[i - 2].text not in (')', ']')):
            return True
    return False


def decl_info(st):
    """(type tokens, name, index of `=` or None) when a simple statement declares one local."""
    if not isinstance(st, Simple):
        return None
    t = st.t
    if not t or t[0].kind != 'id' or t[0].text in KEYWORDS:
        return None
    i, words = 0, 0
    while i < len(t) and t[i].text in ('const', 'volatile', 'static', 'struct', 'class'):
        i += 1
    while i < len(t) and t[i].kind == 'id' and t[i].text in TYPE_WORDS - {'std', 'const', 'volatile'}:
        i += 1
        words += 1
    if not words:
        if i >= len(t) or t[i].kind != 'id':
            return None
        i += 1
        while i + 1 < len(t) and t[i].text == '::' and t[i + 1].kind == 'id':
            i += 2
        if i < len(t) and t[i].text == '<':
            depth = 0
            while i < len(t):
                depth += {'<': 1, '>': -1, '>>': -2}.get(t[i].text, 0)
                i += 1
                if depth <= 0:
                    break
    while i < len(t) and t[i].text in ('*', '&', 'const', 'volatile'):
        i += 1
    if i >= len(t) or t[i].kind != 'id' or t[i].text in KEYWORDS:
        return None
    name = i
    nxt = t[name + 1].text if name + 1 < len(t) else ''
    if nxt == ';':
        return t[:name], t[name].text, None
    if nxt == '=' and _top_level_comma(t[name + 2:-1]) is None:
        return t[:name], t[name].text, name + 1
    return None


def _top_level_comma(toks):
    depth = 0
    for i, t in enumerate(toks):
        if t.text in '([{':
            depth += 1
        elif t.text in ')]}':
            depth -= 1
        elif t.text == ',' and depth == 0:
            return i
    return None


def ends_in_return(node):
    if isinstance(node, Simple):
        return bool(node.t) and node.t[0].text in ('return', 'break', 'continue', 'throw', 'goto')
    if isinstance(node, Block):
        return bool(node.stmts) and ends_in_return(node.stmts[-1])
    if isinstance(node, If):
        return node.els is not None and ends_in_return(node.then) and ends_in_return(node.els)
    return False


def as_block(node, indent=None):
    if isinstance(node, Block):
        return node
    return Block(new('{'), [node], new('}', ' '))


def declared_names(stmts):
    return {d[1] for d in (decl_info(s) for s in stmts) if d}


# --------------------------------------------------------------------------------------------
# Atoms: operands simple enough to move without a parser: names, members, empty calls, literals.

def atom_end(toks, i):
    if i >= len(toks):
        return None
    t = toks[i]
    if t.kind in ('num', 'str'):
        return i + 1
    if t.kind != 'id' or (t.text in KEYWORDS and t.text not in ('this', 'nullptr', 'true', 'false')):
        return None
    j = i + 1
    while j < len(toks):
        if toks[j].text in ('.', '->', '::') and j + 1 < len(toks) and toks[j + 1].kind == 'id':
            j += 2
        elif toks[j].text == '(' and j + 1 < len(toks) and toks[j + 1].text == ')':
            j += 2
        elif toks[j].text == '[':
            k = atom_end(toks, j + 1)
            if k is None or k >= len(toks) or toks[k].text != ']':
                break
            j = k + 1
        else:
            break
    return j


def atom_spans(toks):
    """{end: start} of the longest atom ending at each position."""
    by_end = {}
    for i in range(len(toks)):
        if i and toks[i - 1].text in ('.', '->', '::'):
            continue
        e = atom_end(toks, i)
        if e is not None and (e not in by_end or by_end[e] > i):
            by_end[e] = i
    return by_end


# No statement start: `T * name;` and `T & name = x;` are declarations, not products.
LEFT_OK = {'(', ',', '=', 'return', '&&', '||', '?', ':', '['} | ASSIGN_OPS
RIGHT_OK = {')', ',', ';', '&&', '||', '?', ':', ']', '}'}
FLIP = {'<': '>', '>': '<', '<=': '>=', '>=': '<=', '==': '==', '!=': '!='}
NEGATE = {'<': '>=', '>=': '<', '>': '<=', '<=': '>', '==': '!=', '!=': '=='}
COMMUTE = {'+', '*', '&', '|', '^', '==', '!='}


def expr_sites(root, ops, pure=False):
    """[(token list, site)] over the body; a simple statement's list starts a statement."""
    out = []
    for n in walk_nodes(root):
        if isinstance(n, Simple):
            out += [(n.t, s) for s in binary_sites(n.t, ops, pure, start=';')]
        elif isinstance(n, If):
            out += [(n.cond, s) for s in binary_sites(n.cond, ops, pure)]
        elif isinstance(n, Loop):
            out += [(n.inner, s) for s in binary_sites(n.inner, ops, pure)]
    return out


def binary_sites(toks, ops, pure=False, start='('):
    """(left start, op index, right end) for `atom op atom` with low-precedence neighbours."""
    by_end = atom_spans(toks)
    out = []
    for k, t in enumerate(toks):
        if t.text not in ops or k not in by_end:
            continue
        s = by_end[k]
        e = atom_end(toks, k + 1)
        if e is None:
            continue
        left = toks[s - 1].text if s else start
        right = toks[e].text if e < len(toks) else ')'
        if left not in LEFT_OK or right not in RIGHT_OK:
            continue
        if pure and (has_call(toks[s:k]) or has_call(toks[k + 1:e])):
            continue
        out.append((s, k, e))
    return out


def swap_operands(toks, s, k, e, op_text):
    left, right = toks[s:k], toks[k + 1:e]
    pre_l, pre_op, pre_r = left[0].pre, toks[k].pre, right[0].pre
    left, right = [copy.copy(x) for x in left], [copy.copy(x) for x in right]
    right[0].pre, left[0].pre = pre_l, pre_r
    toks[s:e] = right + [Tok('op', op_text, pre_op)] + left


def top_level(toks, op):
    """Index of the first `op` outside brackets, or None."""
    depth = 0
    for i, t in enumerate(toks):
        if t.text in '([{':
            depth += 1
        elif t.text in ')]}':
            depth -= 1
        elif t.text == op and depth == 0:
            return i
    return None


def top_level_all(toks, op):
    depth, out = 0, []
    for i, t in enumerate(toks):
        if t.text in '([{':
            depth += 1
        elif t.text in ')]}':
            depth -= 1
        elif t.text == op and depth == 0:
            out.append(i)
    return out


def negate(cond):
    """Token list of the negated condition."""
    if not cond:
        return toks_of('false')
    if cond[0].text == '!' and len(cond) > 1:
        rest = cond[1:]
        if atom_end(rest, 0) == len(rest):
            out = [copy.copy(x) for x in rest]
            out[0].pre = cond[0].pre
            return out
        if rest[0].text == '(' and _balanced(rest, 0) == len(rest):
            out = [copy.copy(x) for x in rest[1:-1]]
            out[0].pre = cond[0].pre
            return out
    if top_level(cond, '&&') is None and top_level(cond, '||') is None and top_level(cond, '?') is None:
        hits = [i for i, t in enumerate(cond) if t.text in NEGATE and top_level(cond, t.text) == i]
        if len(hits) == 1 and not any(t.text in ('<', '>') for t in cond if t is not cond[hits[0]]):
            out = [copy.copy(x) for x in cond]
            out[hits[0]] = Tok('op', NEGATE[cond[hits[0]].text], cond[hits[0]].pre)
            return out
    if atom_end(cond, 0) == len(cond):
        return [Tok('op', '!', cond[0].pre)] + _with_pre(cond, '')
    return [Tok('op', '!', cond[0].pre), Tok('op', '(', '')] + _with_pre(cond, '') + [Tok('op', ')', '')]


def _with_pre(toks, pre):
    out = [copy.copy(x) for x in toks]
    if out:
        out[0].pre = pre
    return out


# --------------------------------------------------------------------------------------------
# Mutations. Each takes (body Block, rng) and returns True when it changed the tree. Tags name the
# cookbook rule or P3 rule (docs/ideas-next.md) it mechanises.

def m_decl_swap(root, rng):
    """R1: swap two adjacent local declarations whose initialisers do not depend on each other."""
    sites = []
    for b in walk_blocks(root):
        for i in range(len(b.stmts) - 1):
            a, c = decl_info(b.stmts[i]), decl_info(b.stmts[i + 1])
            if not a or not c:
                continue
            ta, tc = b.stmts[i].t, b.stmts[i + 1].t
            if uses(tc, a[1]) or uses(ta, c[1]):
                continue
            if a[2] is not None and c[2] is not None and has_call(ta) and has_call(tc):
                continue
            sites.append((b, i))
    if not sites:
        return False
    b, i = rng.choice(sites)
    x, y = b.stmts[i], b.stmts[i + 1]
    x.t[0].pre, y.t[0].pre = y.t[0].pre, x.t[0].pre
    b.stmts[i], b.stmts[i + 1] = y, x
    return True


def m_decl_move(root, rng):
    """R1: move an uninitialised or call-free declaration to its block's start or to its first use."""
    sites = []
    for b in walk_blocks(root):
        for i, st in enumerate(b.stmts):
            d = decl_info(st)
            if not d or (d[2] is not None and has_call(st.t)):
                continue
            init_names = {t.text for t in st.t[d[2] + 1:]} if d[2] is not None else set()
            first = next((j for j in range(i + 1, len(b.stmts)) if node_mentions(b.stmts[j], d[1])), None)
            if first is not None and first > i + 1:
                between = b.stmts[i + 1:first]
                if not any(node_mentions(s, n) for s in between for n in init_names):
                    sites.append((b, i, first - 1))
            top = 0
            while top < i and isinstance(b.stmts[top], Label):
                top += 1
            if i > top:
                before = b.stmts[top:i]
                if not any(node_mentions(s, n) for s in before for n in init_names | {d[1]}) \
                        and not any(isinstance(s, Label) for s in before):
                    sites.append((b, i, top))
    if not sites:
        return False
    b, i, j = rng.choice(sites)
    st = b.stmts.pop(i)
    b.stmts.insert(j, st)
    return True


def m_decl_split(root, rng):
    """R2: `T x = e;` becomes `T x; x = e;`, or the reverse."""
    sites = []
    for b in walk_blocks(root):
        for i, st in enumerate(b.stmts):
            d = decl_info(st)
            if not d:
                continue
            words = {t.text for t in d[0]}
            if d[2] is not None and not words & {'const', 'auto', 'static'} and '&' not in words \
                    and not (st.t[d[2] + 1].text == '{'):
                sites.append(('split', b, i, d))
            if d[2] is None and i + 1 < len(b.stmts) and isinstance(b.stmts[i + 1], Simple):
                nt = b.stmts[i + 1].t
                if len(nt) > 2 and nt[0].text == d[1] and nt[1].text == '=' and not uses(nt[2:], d[1]):
                    sites.append(('join', b, i, d))
    if not sites:
        return False
    how, b, i, d = rng.choice(sites)
    st = b.stmts[i]
    if how == 'split':
        decl = Simple(st.t[:d[2]] + [Tok('op', ';', '')])
        assign = Simple([Tok('id', d[1], st.t[0].pre)] + st.t[d[2]:])
        b.stmts[i:i + 1] = [decl, assign]
    else:
        nt = b.stmts[i + 1].t
        b.stmts[i:i + 2] = [Simple(st.t[:-1] + [Tok('op', '=', ' ')] + nt[2:])]
    return True


def m_temp_inline(root, rng):
    """R3: inline a temporary into its single use in the next statement (or a pure one everywhere)."""
    sites = []
    body_toks = root.toks()
    for b in walk_blocks(root):
        for i, st in enumerate(b.stmts):
            d = decl_info(st)
            if not d or d[2] is None or i + 1 >= len(b.stmts):
                continue
            init = st.t[d[2] + 1:-1]
            if not init or top_level(init, ',') is not None:
                continue
            rest = [t for s in b.stmts[i + 1:] for t in s.toks()]
            if written(rest, d[1]) or len(uses(body_toks, d[1])) != 1 + len(uses(rest, d[1])):
                continue
            n_next = len(uses(b.stmts[i + 1].toks(), d[1]))
            if n_next == 1 and len(uses(rest, d[1])) == 1:
                sites.append((b, i, d, init))
            elif not has_call(init) and uses(rest, d[1]) and atom_end(init, 0) == len(init):
                sites.append((b, i, d, init))  # a re-read of a member at every use (cookbook 1)
    if not sites:
        return False
    b, i, d, init = rng.choice(sites)
    words = [t.text for t in d[0]]
    plain = atom_end(init, 0) == len(init)
    if 'auto' in words or (words and words[-1] in ('*', '&')) or 'bool' in words:
        repl = init if plain else [Tok('op', '(', '')] + _with_pre(init, '') + [Tok('op', ')', '')]
    else:
        tname = ' '.join(t.text for t in d[0] if t.text not in ('const', 'volatile', 'static'))
        repl = toks_of(f'static_cast<{tname}>(', '') + _with_pre(init, '') + [Tok('op', ')', '')]
    del b.stmts[i]
    for st in b.stmts[i:]:
        for n in walk_nodes(st):
            for lst in ([n.t] if isinstance(n, Simple) else [n.cond] if isinstance(n, If)
                        else [n.inner] if isinstance(n, Loop) else []):
                for pos in reversed(uses(lst, d[1])):
                    r = _with_pre(repl, lst[pos].pre)
                    lst[pos:pos + 1] = r
    return True


def m_temp_introduce(root, rng):
    """R3: name a member read (or empty call) that a block's statements repeat, from its first use on."""
    sites = []
    for b in walk_blocks(root):
        counts = {}
        for idx, st in enumerate(b.stmts):
            if not isinstance(st, (Simple, If, Loop)):
                continue
            lst = st.t if isinstance(st, Simple) else st.cond if isinstance(st, If) else st.inner
            by_end = atom_spans(lst)
            for e, s in by_end.items():
                text = tuple(t.text for t in lst[s:e])
                if len(text) >= 3 and ('->' in text or '.' in text):
                    counts.setdefault(text, []).append(idx)
        for text, idxs in counts.items():
            if len(idxs) < 2:
                continue
            first = idxs[0]
            region = [t for s in b.stmts[first:] for t in s.toks()]
            joined = [t.text for t in region]
            n = len(text)
            writes = any(joined[j:j + n] == list(text) and j + n < len(joined) and joined[j + n] in ASSIGN_OPS | {'++', '--'}
                         for j in range(len(joined) - n))
            if writes or isinstance(b.stmts[first], Loop) and b.stmts[first].kind != 'switch':
                continue
            sites.append((b, first, text))
    if not sites:
        return False
    b, first, text = rng.choice(sites)
    taken = {t.text for t in root.toks() if t.kind == 'id'}
    k = 0
    while f'v{k}' in taken:
        k += 1
    name = f'v{k}'
    pre = b.stmts[first].toks()[0].pre
    # An atom never holds two adjacent names, so its tokens can be joined without spaces.
    decl = Simple(toks_of(f'auto {name} =', pre) + toks_of(''.join(text), ' ') + [Tok('op', ';', '')])
    n = len(text)
    for st in b.stmts[first:]:
        for node in walk_nodes(st):
            for lst in ([node.t] if isinstance(node, Simple) else [node.cond] if isinstance(node, If)
                        else [node.inner] if isinstance(node, Loop) else []):
                j = 0
                while j <= len(lst) - n:
                    if tuple(t.text for t in lst[j:j + n]) == text and not (j and lst[j - 1].text in ('.', '->', '::')) \
                            and not (j + n < len(lst) and lst[j + n].text == '('):
                        lst[j:j + n] = [Tok('id', name, lst[j].pre)]
                    j += 1
    b.stmts.insert(first, decl)
    return True


def m_if_invert(root, rng):
    """R5: `if (c) A else B` becomes `if (!c) B else A`."""
    sites = [n for n in walk_nodes(root) if isinstance(n, If) and n.els is not None and not isinstance(n.els, If)]
    if not sites:
        return False
    n = rng.choice(sites)
    n.cond[:] = negate(n.cond)
    n.then, n.els = as_block(n.els), as_block(n.then)
    return True


def m_early_return(root, rng):
    """R5: early return versus nested: `if (c) {..return;} rest` <-> `if (c) {..return;} else {rest}`."""
    sites = []
    for b in walk_blocks(root):
        for i, st in enumerate(b.stmts):
            if not isinstance(st, If):
                continue
            if st.els is None and ends_in_return(st.then) and i + 1 < len(b.stmts) \
                    and not any(isinstance(s, Label) for s in b.stmts[i + 1:]):
                sites.append(('nest', b, i))
            if st.els is not None and isinstance(st.els, Block) and ends_in_return(st.then):
                outer = declared_names(b.stmts[:i] + b.stmts[i + 1:])
                if not declared_names(st.els.stmts) & outer:
                    sites.append(('flat', b, i))
    if not sites:
        return False
    how, b, i = rng.choice(sites)
    st = b.stmts[i]
    if how == 'nest':
        rest = b.stmts[i + 1:]
        del b.stmts[i + 1:]
        st.then = as_block(st.then)
        st.else_kw, st.els = new('else'), Block(new('{'), rest, new('}', b.rb.pre))
    else:
        inner = st.els.stmts
        st.else_kw, st.els = None, None
        b.stmts[i + 1:i + 1] = inner
    return True


def m_and_split(root, rng):
    """R5: `if (a && b) S` <-> `if (a) { if (b) S }` (no else on either)."""
    sites = []
    for n in walk_nodes(root):
        if not isinstance(n, If) or n.els is not None:
            continue
        k = top_level(n.cond, '&&')
        if k is not None and top_level(n.cond, '||') is None and top_level(n.cond, '?') is None:
            sites.append(('split', n, k))
        inner = n.then.stmts[0] if isinstance(n.then, Block) and len(n.then.stmts) == 1 else n.then
        if isinstance(inner, If) and inner.els is not None:
            continue
        if isinstance(inner, If):
            sites.append(('join', n, inner))
    if not sites:
        return False
    how, n, x = rng.choice(sites)
    if how == 'split':
        a, c = n.cond[:x], n.cond[x + 1:]
        c = _with_pre(c, '')
        n.cond[:] = a
        n.then = Block(new('{'), [If([new('if'), Tok('op', '(', ' ')], c, Tok('op', ')', ''), n.then)], new('}'))
    else:
        def wrap(c):
            if top_level(c, '||') is not None or top_level(c, '?') is not None or top_level(c, '=') is not None:
                return [Tok('op', '(', c[0].pre)] + _with_pre(c, '') + [Tok('op', ')', '')]
            return [copy.copy(t) for t in c]
        n.cond[:] = wrap(n.cond) + [Tok('op', '&&', ' ')] + _with_pre(wrap(x.cond), ' ')
        n.then = x.then
    return True


def m_loop_form(root, rng):
    """R6: `for (i; c; s) B` <-> `{ i; while (c) { B s; } }`; `while (c)` <-> `for (; c;)`."""
    sites = []
    for b in walk_blocks(root):
        for i, st in enumerate(b.stmts):
            if not isinstance(st, Loop) or st.kind not in ('for', 'while'):
                continue
            if st.kind == 'while':
                sites.append(('while-for', b, i))
                continue
            if len(top_level_all(st.inner, ';')) != 2 or any(t.text == 'continue' for t in st.body.toks()):
                continue
            sites.append(('for-while', b, i))
    if not sites:
        return False
    how, b, i = rng.choice(sites)
    st = b.stmts[i]
    if how == 'while-for':
        st.kw = Tok('id', 'for', st.kw.pre)
        st.kind = 'for'
        st.inner[:] = [Tok('op', ';', '')] + _with_pre(st.inner, ' ') + [Tok('op', ';', '')]
        return True
    semis = top_level_all(st.inner, ';')
    init, cond, step = st.inner[:semis[0]], st.inner[semis[0] + 1:semis[1]], st.inner[semis[1] + 1:]
    body = as_block(st.body)
    if step:
        body.stmts.append(Simple(_with_pre(step, ' ') + [Tok('op', ';', '')]))
    loop = Loop(Tok('id', 'while', ' ' if init else st.kw.pre), Tok('op', '(', ' '),
                _with_pre(cond, '') if cond else toks_of('true', ''), Tok('op', ')', ''), body)
    if init:
        b.stmts[i] = Block(Tok('op', '{', st.kw.pre), [Simple(_with_pre(init, ' ') + [Tok('op', ';', '')]), loop],
                           new('}'))
    else:
        b.stmts[i] = loop
    return True


INT_TYPES = ['std::int8_t', 'std::uint8_t', 'std::int16_t', 'std::uint16_t', 'std::int32_t', 'std::uint32_t',
             'std::int64_t', 'std::uint64_t']
SIGN_FLIP = {'int': 'unsigned int', 'unsigned int': 'int', 'unsigned': 'int', 'char': 'unsigned char',
             'unsigned char': 'char', 'short': 'unsigned short', 'unsigned short': 'short',
             'long': 'unsigned long', 'unsigned long': 'long', 'bool': 'std::uint8_t'}


def m_int_type(root, rng):
    """R4: signedness or width of a local's integral type; width of a switch operand (cookbook 6)."""
    sites = []
    for n in walk_nodes(root):
        d = decl_info(n) if isinstance(n, Simple) else None
        if d:
            tt = [t.text for t in d[0] if t.text not in ('const', 'volatile', 'static')]
            text = ''.join(tt) if '::' in tt else ' '.join(tt)
            if text in INT_TYPES or text in SIGN_FLIP:
                sites.append(('decl', n, d, text))
        if isinstance(n, Loop) and n.kind == 'switch':
            sites.append(('switch', n, None, None))
    if not sites:
        return False
    how, n, d, text = rng.choice(sites)
    if how == 'switch':
        inner = n.inner
        if inner and inner[0].text == 'static_cast':
            close = top_level(inner, '>')
            lp = close + 1 if close is not None else None
            if lp is not None and lp < len(inner) and inner[lp].text == '(' and _balanced(inner, lp) == len(inner):
                n.inner[:] = _with_pre(inner[lp + 1:-1], '')
                return True
            return False
        t = rng.choice(['std::uint32_t', 'std::int32_t', 'std::uint8_t'])
        n.inner[:] = toks_of(f'static_cast<{t}>(', '') + _with_pre(inner, '') + [Tok('op', ')', '')]
        return True
    if text in INT_TYPES and rng.random() < 0.5:
        k = INT_TYPES.index(text)
        repl = INT_TYPES[k ^ 1]
    elif text in INT_TYPES:
        repl = rng.choice([t for t in INT_TYPES if t != text])
    else:
        repl = SIGN_FLIP[text]
    start = next(i for i, t in enumerate(n.t) if t.text not in ('const', 'volatile', 'static'))
    end = len(d[0])
    while end > start and n.t[end - 1].text in ('const', 'volatile'):
        end -= 1
    n.t[start:end] = toks_of(repl, n.t[start].pre)
    return True


def m_compare(root, rng):
    """R7: `a < b` -> `b > a`, `a == b` -> `b == a` (compare direction and operand order)."""
    sites = expr_sites(root, set(FLIP))
    if not sites:
        return False
    lst, (s, k, e) = rng.choice(sites)
    swap_operands(lst, s, k, e, FLIP[lst[k].text])
    return True


def m_commute(root, rng):
    """R7: operand order of a commutative arithmetic or bitwise operator; of `&&`/`||` when pure."""
    sites = expr_sites(root, COMMUTE - {'==', '!='}) + expr_sites(root, {'&&', '||'}, pure=True)
    if not sites:
        return False
    lst, (s, k, e) = rng.choice(sites)
    swap_operands(lst, s, k, e, lst[k].text)
    return True


def m_test_form(root, rng):
    """R5/R7: `!x` <-> `x == 0`, `x` <-> `x != 0` as a whole condition; `nullptr` <-> `0` in tests."""
    sites = []
    for n in walk_nodes(root):
        if isinstance(n, If) or isinstance(n, Loop) and n.kind == 'while':
            c = n.cond if isinstance(n, If) else n.inner
            if c and c[0].text == '!' and atom_end(c, 1) == len(c):
                sites.append(('not-eq', c))
            elif c and atom_end(c, 0) == len(c):
                sites.append(('ne', c))
            elif len(c) >= 3 and c[-2].text in ('==', '!=') and c[-1].text in ('0', 'nullptr') \
                    and atom_end(c, 0) == len(c) - 2:
                sites.append(('drop', c))
    for lst in expr_lists(root):
        for i, t in enumerate(lst):
            if t.text in ('nullptr', '0') and i and lst[i - 1].text in ('==', '!='):
                sites.append(('null', lst, i))
    if not sites:
        return False
    site = rng.choice(sites)
    how, c = site[0], site[1]
    if how == 'not-eq':
        c[:] = _with_pre(c[1:], c[0].pre) + [Tok('op', '==', ' '), Tok('num', '0', ' ')]
    elif how == 'ne':
        c[:] = c + [Tok('op', '!=', ' '), Tok('num', '0', ' ')]
    elif how == 'drop':
        body = c[:-2]
        c[:] = ([Tok('op', '!', c[0].pre)] + _with_pre(body, '')) if c[-2].text == '==' else body
    else:
        i = site[2]
        c[i] = Tok('num' if c[i].text == 'nullptr' else 'id', '0' if c[i].text == 'nullptr' else 'nullptr', c[i].pre)
    return True


def m_increment(root, rng):
    """Increment forms as a statement or loop step: `++i`, `i++`, `i += 1`, `i = i + 1`."""
    sites = []
    for n in walk_nodes(root):
        if isinstance(n, Simple) and len(n.t) in (3, 4, 6):
            sites.append(n.t)
        if isinstance(n, Loop) and n.kind == 'for':
            semi = [j for j, t in enumerate(n.inner) if t.text == ';']
            if len(semi) == 2:
                sites.append(('step', n, semi[1]))
    cands = []
    for s in sites:
        if isinstance(s, tuple):
            _, n, j = s
            step = n.inner[j + 1:]
            name = _incr_name(step)
            if name:
                cands.append((n.inner, j + 1, len(n.inner), name, False))
        else:
            name = _incr_name(s[:-1])
            if name:
                cands.append((s, 0, len(s) - 1, name, True))
    if not cands:
        return False
    lst, a, b, (name, op), stmt = rng.choice(cands)
    forms = [f'++{name}', f'{name}++', f'{name} {op}= 1', f'{name} = {name} {op} 1']
    if op == '-':
        forms[0], forms[1] = f'--{name}', f'{name}--'
    current = ''.join(t.text for t in lst[a:b])
    choices = [f for f in forms if f.replace(' ', '') != current]
    lst[a:b] = toks_of(rng.choice(choices), lst[a].pre)
    return True


def _incr_name(toks):
    txt = [t.text for t in toks]
    if len(txt) == 2 and txt[0] in ('++', '--') and toks[1].kind == 'id':
        return txt[1], txt[0][0]
    if len(txt) == 2 and txt[1] in ('++', '--') and toks[0].kind == 'id':
        return txt[0], txt[1][0]
    if len(txt) == 3 and txt[1] in ('+=', '-=') and txt[2] == '1' and toks[0].kind == 'id':
        return txt[0], txt[1][0]
    if len(txt) == 5 and txt[1] == '=' and txt[2] == txt[0] and txt[3] in ('+', '-') and txt[4] == '1' \
            and toks[0].kind == 'id':
        return txt[0], txt[3]
    return None


def m_out_init(root, rng):
    """Cookbook 9: a local whose address is passed out keeps or drops its zero initialiser."""
    sites = []
    body = root.toks()
    for b in walk_blocks(root):
        for i, st in enumerate(b.stmts):
            d = decl_info(st)
            if not d:
                continue
            taken = any(body[j - 1].text == '&' and (j < 2 or body[j - 2].text in ('(', ',', '='))
                        for j in uses(body, d[1]))
            if not taken:
                continue
            init = [t.text for t in st.t[d[2] + 1:-1]] if d[2] is not None else None
            if init in (['nullptr'], ['0'], ['{', '}']):
                sites.append(('drop', st, d))
            elif init is None:
                sites.append(('add', st, d))
    if not sites:
        return False
    how, st, d = rng.choice(sites)
    if how == 'drop':
        st.t[d[2]:-1] = []
    else:
        pointer = any(t.text == '*' for t in d[0])
        st.t[-1:-1] = [Tok('op', '=', ' '), new('nullptr' if pointer else '0')]
    return True


MUTATIONS = {
    'out-init': (m_out_init, 'cookbook 9', 1),
    'decl-swap': (m_decl_swap, 'R1', 3),
    'decl-move': (m_decl_move, 'R1', 2),
    'decl-split': (m_decl_split, 'R2, cookbook 9', 2),
    'temp-inline': (m_temp_inline, 'R3, cookbook 1', 3),
    'temp-introduce': (m_temp_introduce, 'R3, cookbook 1', 2),
    'if-invert': (m_if_invert, 'R5, cookbook 2', 3),
    'early-return': (m_early_return, 'R5, cookbook 2', 3),
    'and-split': (m_and_split, 'R5', 2),
    'loop-form': (m_loop_form, 'R6', 2),
    'int-type': (m_int_type, 'R4, cookbook 6', 2),
    'compare': (m_compare, 'R7', 3),
    'commute': (m_commute, 'R7', 2),
    'test-form': (m_test_form, 'R5/R7', 2),
    'increment': (m_increment, 'increment forms', 1),
}


def mutate(root, rng, steps=1, names=None):
    """Apply `steps` random applicable mutations in place; returns the names applied."""
    pool = [n for n in (names or MUTATIONS)]
    weights = [MUTATIONS[n][2] for n in pool]
    applied = []
    tries = 0
    while len(applied) < steps and tries < steps * 12:
        tries += 1
        name = rng.choices(pool, weights)[0]
        if MUTATIONS[name][0](root, rng):
            applied.append(name)
    return applied


# --------------------------------------------------------------------------------------------
# Unit text, lint gate and seen sets.

class Unit:
    """The compiled file split around the mutated bodies: the target's first, then `also` helpers.

    Candidates differ only in those bodies. A Block or a str stands for the target body alone;
    a list holds one entry per body.
    """

    def __init__(self, text, qualified, also=()):
        self.text = text
        self.spans, self.blocks, self.tails = [], [], []
        for name in (qualified, *also):
            start, end = find_body(text, name)
            if any(start < e and s < end for s, e in self.spans):
                raise ValueError(f'{name}: body overlaps another mutated body')
            block, tail = parse_body(text[start:end])
            if emit(block, tail) != text[start:end]:
                raise ValueError(f'{name}: body does not round-trip through the tokenizer')
            self.spans.append((start, end))
            self.blocks.append(block)
            self.tails.append(tail)
        self.start, self.end = self.spans[0]
        self.block, self.tail = self.blocks[0], self.tails[0]

    def forest(self):
        return list(self.blocks)

    def body_of(self, tree):
        if isinstance(tree, Block):
            return emit(tree, self.tail)
        return [emit(b, t) for b, t in zip(tree, self.tails)]

    def with_body(self, body):
        bodies = [body] if isinstance(body, str) else body
        return splice(self.text, self.spans[:len(bodies)], bodies)


def splice(text, spans, bodies):
    """`text` with each span replaced by its body (spans do not overlap)."""
    for (s, e), body in sorted(zip(spans, bodies), key=lambda x: -x[0][0]):
        text = text[:s] + body + text[e:]
    return text


def mutate_forest(forest, rng, steps):
    """Like mutate, over several bodies; a helper's mutation is named `<rule>@<body index>`."""
    applied, tries = [], 0
    while len(applied) < steps and tries < steps * 12:
        tries += 1
        i = rng.randrange(len(forest))
        done = mutate(forest[i], rng, 1)
        applied += [f'{n}@{i}' if i else n for n in done]
    return applied


def lint_gate(lint_root, compiled, build_id):
    """A function text -> [problems] running tools/lint_reconstruction.py on the candidate file."""
    sys.path.insert(0, str(REPO / 'tools'))
    import lint_reconstruction

    def check(text):
        path = Path(lint_root) / compiled
        path.write_text(text)
        return lint_reconstruction.lint_file(lint_root, compiled, build_id)
    return check


def make_lint_root(dest, source_root, closure):
    """A private tree the lint can read: the unit's files plus links to builds/, findings/, reports/."""
    dest = Path(dest)
    shutil.rmtree(dest, ignore_errors=True)
    dest.mkdir(parents=True)
    for name in ('builds', 'findings', 'reports'):
        (dest / name).symlink_to(REPO / name)
    (dest / 'reconstruction').mkdir()
    (dest / 'reconstruction' / 'recipes').symlink_to(REPO / 'reconstruction' / 'recipes')
    for name in closure:
        if name.startswith('reconstruction/recipes/'):
            continue
        p = dest / name
        p.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(Path(source_root) / name, p)
    return dest


def score_key(row):
    """Order of candidates: distance first, then exact edits, then instruction-count difference."""
    if row.get('st') != 'ok':
        return (float('inf'),)
    return (row['d'], row.get('ex', 0), abs(row.get('n', 0) - row.get('nt', 0)))


# --------------------------------------------------------------------------------------------
# Search, independent of how candidates are scored (so tests can use a local scorer).

class Search:
    def __init__(self, unit, scorer, lint, rng, batch=16, patience=8, restart_after=3, budget=600.0,
                 log=print, clock=time.monotonic, max_steps=3):
        self.unit, self.scorer, self.lint, self.rng = unit, scorer, lint, rng
        self.batch, self.patience, self.restart_after, self.budget = batch, patience, restart_after, budget
        self.log, self.clock, self.max_steps = log, clock, max_steps
        self.seen_src, self.seen_obj, self.history = set(), {}, []
        self.lint_rejected = 0
        self.next_id = 0

    def _candidates(self, parents):
        out, guard = [], 0
        while len(out) < self.batch and guard < self.batch * 20:
            guard += 1
            parent = self.rng.choice(parents)
            tree = copy.deepcopy(parent['tree'])
            steps = 1 + min(self.max_steps - 1, int(self.rng.expovariate(1.2)))
            applied = mutate_forest(tree, self.rng, steps)
            if not applied:
                continue
            body = self.unit.body_of(tree)
            digest = hashlib.sha256(json.dumps(body).encode()).hexdigest()
            if digest in self.seen_src:
                continue
            self.seen_src.add(digest)
            problems = self.lint(self.unit.with_body(body))
            if problems:
                self.lint_rejected += 1
                continue
            self.next_id += 1
            out.append({'id': f'v{self.next_id:05d}', 'parent': parent['id'], 'muts': parent['muts'] + applied,
                        'tree': tree, 'body': body})
        return out

    def run(self):
        started = self.clock()
        base_tree = self.unit.forest()
        base_body = self.unit.body_of(base_tree)
        problems = self.lint(self.unit.with_body(base_body))
        if problems:
            return {'status': 'base-lint-failed', 'problems': problems}
        self.seen_src.add(hashlib.sha256(json.dumps(base_body).encode()).hexdigest())
        base = {'id': 'v00000', 'parent': None, 'muts': [], 'tree': base_tree, 'body': base_body}
        rows = self.scorer([base])
        base.update(rows[0])
        self._record(base)
        if base.get('st') != 'ok':
            return {'status': 'base-not-scored', 'base': _public(base)}
        start = best = current = base
        self.seen_obj[base.get('h')] = score_key(base)
        stale_best = stale_current = rounds = 0
        stop = 'patience'
        while True:
            if score_key(best)[0] == 0:
                stop = 'distance-0'
                break
            if self.clock() - started >= self.budget:
                stop = 'budget'
                break
            if stale_best >= self.patience:
                stop = 'patience'
                break
            if stale_current >= self.restart_after:
                # Random restart: a few random steps away from the best, so the climb leaves a plateau.
                tree = copy.deepcopy(best['tree'])
                applied = mutate_forest(tree, self.rng, self.rng.randint(2, 5))
                # Unscored on purpose: the first new object of the next batch becomes the current point.
                current = {'id': best['id'] + '+r', 'muts': best['muts'] + applied, 'tree': tree, 'st': 'restart'}
                stale_current = 0
            cands = self._candidates([current] * 3 + [best])
            if not cands:
                stale_best += 1
                stale_current += 1
                rounds += 1
                continue
            rows = self.scorer(cands)
            rounds += 1
            new_best = new_current = None
            for c, r in zip(cands, rows):
                c.update(r)
                fresh = c.get('h') not in self.seen_obj
                c['new_object'] = fresh
                self._record(c)
                if c.get('st') != 'ok' or not fresh:
                    continue
                self.seen_obj[c['h']] = score_key(c)
                if new_current is None or score_key(c) < score_key(new_current):
                    new_current = c
            if new_current is not None and score_key(new_current) < score_key(best):
                new_best = new_current
            if new_best is not None:
                best = current = new_best
                stale_best = stale_current = 0
            elif new_current is not None and score_key(new_current) < score_key(current):
                current = new_current
                stale_best += 1
                stale_current = 0
            elif new_current is not None and score_key(new_current) == score_key(current) and self.rng.random() < 0.3:
                current = new_current  # sideways move on a plateau: same score, different object code
                stale_best += 1
                stale_current += 1
            else:
                stale_best += 1
                stale_current += 1
            self.log(f'round {rounds}: {len(cands)} candidates, best {_fmt(best)}, current {_fmt(current)}')
        return {'status': stop, 'start': start, 'best': best, 'rounds': rounds,
                'candidates': len(self.history), 'lint_rejected': self.lint_rejected,
                'unique_objects': len(self.seen_obj), 'seconds': round(self.clock() - started, 1)}

    def _record(self, c):
        self.history.append(_public(c))


def _public(c):
    return {k: v for k, v in c.items() if k not in ('tree', 'body')}


def _fmt(c):
    return f'd={c.get("d")}' if c.get('st') == 'ok' else str(c.get('st'))


# --------------------------------------------------------------------------------------------
# Remote side: runs on the verifier host inside the task's run directory.

def encode_payload(obj):
    return base64.b64encode(zlib.compress(json.dumps(obj).encode(), 9)).decode()


def decode_payload(text):
    return json.loads(zlib.decompress(base64.b64decode(text)))


def function_hash(listing):
    """Hash of the function's object code: instruction bytes and relocation symbols, in order."""
    import align
    h = hashlib.sha256()
    for addr, data, _text, relocs in align.parse_listing(listing):
        h.update(f'{addr:x}:{"".join(data)}:{";".join(f"{r[1]}={r[2]}" for r in relocs)}\n'.encode())
    return h.hexdigest()[:16]


def remote_batch(payload, run_dir):
    """Compile and score every candidate; print one sanitized JSON line each."""
    import concurrent.futures
    import subprocess
    sys.path.insert(0, str(HERE))
    import align
    import disasm
    from unit_build import clean_env
    run = Path(run_dir).resolve()  # cl runs in each worker's copy, so /Fo needs an absolute path
    repo = run / 'repo'
    p = payload
    objdump = disasm.find_objdump(p.get('objdump') or '/usr/bin/llvm-objdump')
    image = p['image']
    target_file = run / 'perm' / f'target-0x{p["rva"]:x}.txt'
    target_file.parent.mkdir(parents=True, exist_ok=True)
    if not target_file.is_file():
        listing, base = align.objdump_target(objdump, image, p['rva'], p['size'])
        target_file.write_text(json.dumps({'listing': listing, 'base': base}))
    tgt = json.loads(target_file.read_text())
    symbols = align.load_symbols(repo / p['symbols'])
    recipe = json.loads((repo / p['recipe']).read_text())
    base_text = (repo / p['compiled']).read_text()
    spans = [tuple(x) for x in p['spans']]
    env = clean_env(os.environ)
    msvc = Path(p['msvc'])
    t_rows = align._as_rows(tgt['listing'])
    n_target = len(align.build(t_rows, size=p['size'], base=tgt['base']))

    def worker_dir(k):
        w = run / 'perm' / f'w{k}'
        stamp = w / '.stamp'
        want = hashlib.sha256(base_text.encode()).hexdigest()
        if not stamp.is_file() or stamp.read_text() != want:
            shutil.rmtree(w, ignore_errors=True)
            w.mkdir(parents=True)
            subprocess.run(['cp', '-al', str(repo), str(w / 'repo')], check=True)
            stamp.write_text(want)
        return w

    workers = [worker_dir(k) for k in range(p['jobs'])]
    free = list(range(p['jobs']))
    import threading
    lock = threading.Lock()

    def one(item):
        cid, body = item
        with lock:
            k = free.pop()
        t0 = time.monotonic()
        try:
            w = workers[k]
            src = w / 'repo' / p['compiled']
            tmp = src.with_name(src.name + '.tmp')
            tmp.write_text(splice(base_text, spans, body))
            os.replace(tmp, src)  # replaces the hard link, so the shared copy stays unchanged
            obj = w / f'{cid}.obj'
            proc = subprocess.run([str(msvc / 'bin/x64/cl')] + recipe['flags'] + [f'/Fo{obj}', p['compiled']],
                                  cwd=w / 'repo', env=env, capture_output=True, text=True, errors='replace',
                                  timeout=300)
            if proc.returncode != 0 or not obj.is_file():
                (w / 'last-compile.log').write_text(proc.stdout + proc.stderr)
                # Error codes only: compiler messages quote source text, and exec output is kept.
                codes = sorted(set(re.findall(r'\b(?:error|fatal error) ([A-Z]+\d+)', proc.stdout + proc.stderr)))
                return {'id': cid, 'st': 'compile-failed', 'codes': codes[:5], 'rc': proc.returncode,
                        't': round(time.monotonic() - t0, 2)}
            cand = align.objdump_candidate(objdump, obj, p['symbol'])
            obj.unlink()
            if not align.parse_listing(cand):
                return {'id': cid, 'st': 'no-symbol', 't': round(time.monotonic() - t0, 2)}
            _text, data = align.summarise(tgt['listing'], cand, symbols=symbols, image_base=tgt['base'],
                                          target_size=p['size'])
            comps = data['components']
            return {'id': cid, 'st': 'ok', 'd': data['distance'], 'p': comps['prologue'], 'b': comps['body'],
                    'r': comps['refs'], 'es': data['edits']['shape'], 'ex': data['edits']['exact'],
                    'n': data['candidate_instructions'], 'nt': n_target, 'h': function_hash(cand),
                    't': round(time.monotonic() - t0, 2)}
        except Exception as exc:  # noqa: BLE001 - one broken candidate must not lose the batch
            return {'id': cid, 'st': 'error', 'why': type(exc).__name__, 't': round(time.monotonic() - t0, 2)}
        finally:
            with lock:
                free.append(k)

    t0 = time.monotonic()
    with concurrent.futures.ThreadPoolExecutor(p['jobs']) as pool:
        for row in pool.map(one, p['cands']):
            print(json.dumps(row), flush=True)
    print(json.dumps({'batch': len(p['cands']), 'wall': round(time.monotonic() - t0, 2)}), flush=True)
    return 0


# --------------------------------------------------------------------------------------------
# Local driver.

def remote_scorer(machine, run_dir, payload_base, timings, log, transport='scp', stage=None):
    """Score a batch remotely. `scp` uploads the candidate bodies as a file first (two Boat calls);
    `inline` puts them, compressed, in the exec command line (one call), which Boat may retain."""
    import boatctl
    counter = [0]

    def score(cands):
        payload = dict(payload_base, cands=[[c['id'], c['body']] for c in cands])
        blob = encode_payload(payload)
        counter[0] += 1
        t0 = time.monotonic()
        if transport == 'inline':
            arg = f'--payload {blob}'
        else:
            name = f'batch-{counter[0]:04d}.b64'
            local = Path(stage) / name
            local.write_text(blob)
            try:
                boatctl.upload(machine, local, f'{run_dir}/{name}')
            finally:
                local.unlink(missing_ok=True)
            arg = f'--payload-file {name}'
        cmd = f'cd {shlex.quote(run_dir)} && python3 -I repo/tools/verifier/permute.py remote --run . {arg}'
        code, out = 2, ''
        for wait in (0, 5, 15):
            time.sleep(wait)
            try:
                code, out, _err = boatctl.execute(machine, cmd, 600)
                break
            except boatctl.BoatError as exc:
                # Transient gateway errors (HTTP 5xx) seen on the trial; the batch is safe to repeat
                # because it writes only inside the run directory.
                log(f'boat exec failed ({str(exc)[:60]}); retrying')
        wall = time.monotonic() - t0
        timings['exec_seconds'] = timings.get('exec_seconds', 0) + wall
        timings['execs'] = timings.get('execs', 0) + 1
        rows = {}
        for line in out.splitlines():
            try:
                row = json.loads(line)
            except ValueError:
                continue
            if 'id' in row:
                rows[row['id']] = row
            elif 'batch' in row:
                timings['remote_wall'] = timings.get('remote_wall', 0) + row['wall']
        if code != 0 or not rows:
            log(f'remote batch exit {code}, {len(rows)} rows')
        return [rows.get(c['id'], {'id': c['id'], 'st': 'lost'}) for c in cands]
    return score


def run(args):
    sys.path.insert(0, str(HERE))
    import boatctl
    import pipeline
    started = time.monotonic()
    task = pipeline.load_task(args.task_dir)
    rva = int(args.rva, 0)
    fn = next((f for f in task['functions'] if f['rva'] == rva), None)
    if fn is None:
        raise SystemExit(f'0x{rva:x} is not a function of the task')
    raw = json.loads((task['dir'] / 'task.json').read_text())
    entry = next(f for f in raw['functions'] if int(str(f['rva']), 0) == rva)
    qualified = args.function or entry.get('community_name')
    if not qualified:
        raise SystemExit('give --function Class::Name')
    source_root = Path(args.source_root).resolve() if args.source_root else REPO
    out = Path(args.out).resolve() if args.out else task['dir'] / 'permute' / f'0x{rva:x}'
    pipeline.private_root(out)
    out.mkdir(parents=True, exist_ok=True)
    compiled = task['compiled']
    unit = Unit((source_root / compiled).read_text(), qualified, args.also or ())
    from source_digest import include_closure
    closure = include_closure(source_root, compiled)
    files = {name: REPO / name for name in pipeline.TOOL_FILES + REMOTE_TOOLS}
    files.update({name: source_root / name for name in closure})
    files[task['recipe']] = REPO / task['recipe']
    files[task['symbols_repo'] or pipeline.PRIVATE_SYMBOLS] = task['symbols_local']
    lint = lint_gate(make_lint_root(out / 'lintroot', source_root, closure), compiled, task['build_id'])
    if args.dry_run:
        return dry_run(unit, lint, random.Random(args.seed), args.batch)
    config = pipeline.load_config(task['dir'])
    machine, state = boatctl.lookup()
    if machine is None or (args.no_resume and state not in boatctl.RUNNING):
        raise SystemExit(f'{boatctl.STANDING} is not running (state {state}); --no-resume forbids starting it')
    if args.no_resume:
        left = boatctl.seconds_left(boatctl.info(machine))
        if left is not None and left < args.budget + 120:
            raise SystemExit(f'only {left} s left before the machine auto-stops; budget is {args.budget} s')
        how = 'warm (not resumed or extended)'
    else:
        machine, how = pipeline.ensure_standing()
    remote_root = args.remote_root or f'{boatctl.REMOTE_HOME}/tasks/permute'
    run_dir = f'{remote_root}/{task["task_id"]}-0x{rva:x}'
    log = print
    log(f'permute {task["task_id"]} 0x{rva:x} {qualified}: machine {how}; remote {run_dir}')
    # The first compile is a real unit_build run of the unchanged unit: it syncs the copy the
    # workers link to and checks toolchain and image hashes on this boot.
    # Every run starts from a fresh remote copy: the run directory is removed at the end, so a
    # stored sync state would make Host skip the upload of files that are no longer there.
    (out / '.sync.json').unlink(missing_ok=True)
    host = pipeline.Host(machine, 'permute', run_dir, task, state_path=out / '.sync.json',
                         local_image=config.get('image'))
    stage = out / '.stage'
    stage.mkdir(exist_ok=True)
    t0 = time.monotonic()
    code, text = host.run(files, stage)
    timings = {'baseline_seconds': round(time.monotonic() - t0, 1)}
    if code not in (0, 1):
        log(f'baseline unit_build exit {code}: ' + ' | '.join(text.splitlines()[-3:]))
        return 2
    payload_base = {'rva': rva, 'size': fn['size'], 'symbol': fn['symbol'], 'compiled': compiled,
                    'recipe': task['recipe'], 'symbols': task['symbols_repo'] or pipeline.PRIVATE_SYMBOLS,
                    'spans': [list(s) for s in unit.spans], 'jobs': args.jobs,
                    'image': pipeline.remote_image(task['build_id']), 'msvc': f'{boatctl.REMOTE_HOME}/msvc'}
    scorer = remote_scorer(machine, run_dir, payload_base, timings, log, args.transport, stage)
    search = Search(unit, scorer, lint, random.Random(args.seed), batch=args.batch, patience=args.patience,
                    restart_after=args.restart_after, budget=args.budget, log=log, max_steps=args.max_steps)
    try:
        result = search.run()
    except BaseException:
        # Leave no game-derived listings or objects on the machine and keep the cost record.
        if not args.keep_remote:
            boatctl.execute(machine, f'rm -rf {shlex.quote(run_dir)}', 60)
        pipeline.record_cost(task, 'draft', time.monotonic() - started, time.monotonic() - started)
        raise
    with open(out / 'history.jsonl', 'w') as f:
        for row in search.history:
            f.write(json.dumps(row) + '\n')
    summary = {'task': task['task_id'], 'rva': f'0x{rva:x}', 'function': qualified, 'status': result['status'],
               'seed': args.seed, 'batch': args.batch, 'jobs': args.jobs}
    final = None
    if 'best' in result:
        best = result['best']
        (out / 'best.cpp').write_text(unit.with_body(best['body']))
        summary.update({'start_distance': result['start'].get('d'), 'best_distance': best.get('d'),
                        'best_id': best['id'], 'best_mutations': best['muts'], 'rounds': result['rounds'],
                        'candidates': result['candidates'], 'lint_rejected': result['lint_rejected'],
                        'unique_objects': result['unique_objects'],
                        'compile_failed': sum(1 for r in search.history if r.get('st') != 'ok')})
        if best.get('d') == 0 and best['id'] != 'v00000':
            final = verify_final(host, files, compiled, out, unit.with_body(best['body']), rva, stage)
            summary['comparator'] = final
    else:
        summary.update({k: v for k, v in result.items() if k != 'status'})
    if not args.keep_remote:
        boatctl.execute(machine, f'rm -rf {shlex.quote(run_dir)}', 60)
    wall = time.monotonic() - started
    timings['wall_seconds'] = round(wall, 1)
    n = summary.get('candidates') or 0
    summary['timings'] = {k: round(v, 1) if isinstance(v, float) else v for k, v in timings.items()}
    summary['candidates_per_boat_minute'] = round(n / (wall / 60), 1) if wall else None
    (out / 'result.json').write_text(json.dumps(summary, indent=1) + '\n')
    pipeline.record_cost(task, 'draft', wall, wall)
    log(f'result: {summary["status"]}; start d={summary.get("start_distance")} best d={summary.get("best_distance")} '
        f'({summary.get("best_mutations")}); {n} candidates in {wall:.0f} s '
        f'({summary["candidates_per_boat_minute"]}/Boat min); comparator {final}')
    log(f'private: {out}/ (best.cpp, history.jsonl, result.json)')
    return 0 if final == 'pass' else 1


def dry_run(unit, lint, rng, batch):
    """Local check before any Boat time: the base lints and the mutations find sites in this body."""
    problems = lint(unit.with_body(unit.body_of(unit.forest())))
    print(f'base lint: {"PASS" if not problems else "FAIL"}' + ''.join(f'\n  {p}' for p in problems))
    sites = {}
    for name, (fn, _tag, _w) in MUTATIONS.items():
        hits = sum(fn(copy.deepcopy(b), random.Random(i)) for i in range(5) for b in unit.blocks)
        sites[name] = hits
    print('mutations with a site: ' + ', '.join(n for n, h in sites.items() if h) or 'none')
    search = Search(unit, lambda cands: [], lint, rng, batch=batch, log=lambda m: None)
    cands = search._candidates([{'id': 'v00000', 'muts': [], 'tree': unit.forest()}])
    print(f'one batch: {len(cands)} candidates, {search.lint_rejected} refused by lint')
    return 0 if not problems else 1


def verify_final(host, files, compiled, out, text, rva, stage):
    """Compile the winning unit with unit_build.py and return the comparator's result for the target."""
    path = out / 'final-src' / compiled
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    files = dict(files, **{compiled: path})
    code, _ = host.run(files, stage)
    dest = host.fetch(out / 'final')
    try:
        rep = json.loads((dest / f'0x{rva:x}' / 'report.json').read_text())
    except (OSError, ValueError):
        rep = {}
    # Other functions of the unit may be near-misses of their own; the verdict here is the target's.
    return 'pass' if code in (0, 1) and rep.get('result') == 'pass' else \
        f'{rep.get("result", "error")} {rep.get("reason")} (unit_build exit {code})'


def mutate_cmd(args):
    text = Path(args.file).read_text()
    unit = Unit(text, args.function)
    rng = random.Random(args.seed)
    tree = copy.deepcopy(unit.block)
    applied = mutate(tree, rng, args.steps)
    sys.stdout.write(unit.with_body(unit.body_of(tree)))
    print(f'mutations: {", ".join(applied)}', file=sys.stderr)
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest='cmd', required=True)
    r = sub.add_parser('run', help='search for one function of a task')
    r.add_argument('task_dir')
    r.add_argument('--rva', required=True)
    r.add_argument('--function', help='qualified name of the definition to mutate (default: community name)')
    r.add_argument('--also', action='append', metavar='Class::Helper',
                   help='also mutate this definition in the same file (repeatable), e.g. an inline helper')
    r.add_argument('--source-root', help='checkout-shaped tree holding reconstruction/ (default: this checkout)')
    r.add_argument('--out', help='private output directory (default: <task-dir>/permute/0x<rva>)')
    r.add_argument('--budget', type=float, default=600.0, help='seconds of Boat time (default 600 = 10 min)')
    r.add_argument('--batch', type=int, default=16)
    r.add_argument('--jobs', type=int, default=4)
    r.add_argument('--patience', type=int, default=8, help='batches without a new best before stopping')
    r.add_argument('--restart-after', type=int, default=3, help='batches without progress before a restart')
    r.add_argument('--max-steps', type=int, default=3, help='most mutations stacked in one candidate')
    r.add_argument('--seed', type=int, default=1)
    r.add_argument('--remote-root', help='parent directory on the machine (default ~/tasks/permute)')
    r.add_argument('--keep-remote', action='store_true')
    r.add_argument('--no-resume', action='store_true', help='refuse unless the standing machine is already running')
    r.add_argument('--dry-run', action='store_true', help='lint the base and one batch locally; no Boat time')
    m = sub.add_parser('mutate', help='print a mutated copy of a file (tests, recovery self-tests)')
    m.add_argument('file')
    m.add_argument('--function', required=True)
    m.add_argument('--steps', type=int, default=3)
    m.add_argument('--seed', type=int, default=1)
    rm = sub.add_parser('remote', help=argparse.SUPPRESS)
    rm.add_argument('--run', required=True)
    rm.add_argument('--payload')
    rm.add_argument('--payload-file')
    r.add_argument('--transport', choices=('scp', 'inline'), default='scp',
                   help='scp: bodies uploaded as a file (default); inline: in the exec command line')
    a = p.parse_args(argv)
    if a.cmd == 'remote':
        if a.payload_file:
            path = Path(a.run) / a.payload_file
            blob = path.read_text()
            path.unlink()
        else:
            blob = a.payload
        return remote_batch(decode_payload(blob), a.run)
    if a.cmd == 'mutate':
        return mutate_cmd(a)
    return run(a)


if __name__ == '__main__':
    raise SystemExit(main())
