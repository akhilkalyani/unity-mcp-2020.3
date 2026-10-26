"""Mechanical C# 9 -> C# 8 rewrites for Unity 2020.3:
  * target-typed `new(...)` in field/property/local declarations -> `new DeclaredType(...)`
  * `x is not null`  -> `x is object`
  * `x is not T [name]` -> `!(x is T [name])`
Anything it cannot rewrite safely is left alone and reported by the compiler.

usage: python -I downlevel.py <dir>...
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from masklib import mask  # noqa: E402

IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
STOP_KEYWORDS = {"return", "case", "when", "in", "else", "throw", "yield", "if", "while", "var"}
DECL_PRECEDERS = set(";{}(),\n")
MODIFIERS = {"public", "private", "protected", "internal", "static", "readonly", "const", "volatile", "new"}
NON_TYPES = {"return", "else", "in", "out", "ref", "case", "throw", "yield", "await", "var", "this", "base"}


def match_back(s, i, close, open_):
    """s[i] == close; return index of matching open."""
    depth = 0
    while i >= 0:
        c = s[i]
        if c == close:
            depth += 1
        elif c == open_:
            depth -= 1
            if depth == 0:
                return i
        i -= 1
    return -1


def skip_ws_back(s, i):
    while i >= 0 and s[i] in " \t\r\n":
        i -= 1
    return i


def ident_back(s, i, dots=False):
    """s[i] is last char of identifier; return start index."""
    j = i
    while j >= 0 and (s[j].isalnum() or s[j] == "_" or (dots and s[j] == ".")):
        j -= 1
    return j + 1


def declared_type(s, eq):
    """Given index of '=' in `Type name = new(`, return the Type text or None."""
    i = skip_ws_back(s, eq - 1)
    if i < 0:
        return None
    if s[i] == "}":  # property: `Type Name { get; set; } = new()`
        i = match_back(s, i, "}", "{")
        if i < 0:
            return None
        i = skip_ws_back(s, i - 1)
    if not (s[i].isalnum() or s[i] == "_"):
        return None
    name_start = ident_back(s, i)
    end = skip_ws_back(s, name_start - 1)
    if end < 0:
        return None
    i = end
    while True:
        c = s[i]
        if c == "?":
            i -= 1
            continue
        if c == "]":
            i = match_back(s, i, "]", "[")
            if i < 0:
                return None
            i -= 1
            continue
        if c == ")":
            i = match_back(s, i, ")", "(")
            if i < 0:
                return None
            start = i
            break
        if c == ">":
            i = match_back(s, i, ">", "<")
            if i < 0:
                return None
            i -= 1
        if not (s[i].isalnum() or s[i] == "_"):
            return None
        start = ident_back(s, i, dots=True)
        break
    type_text = s[start:end + 1]
    head = IDENT.match(type_text)
    if head and head.group(0) in NON_TYPES:
        return None
    before = skip_ws_back(s, start - 1)
    if before >= 0:
        if s[before] not in DECL_PRECEDERS and s[before] != "]":
            w = ident_back(s, before)
            if s[w:before + 1] not in MODIFIERS and not s[w:before + 1] == "using":
                return None
    return type_text


def rewrite_new(s):
    out = []
    pos = 0
    count = 0
    ms = mask(s)
    for m in re.finditer(r"(?<![=!<>])=\s*new\s*\(", ms):
        eq = m.start()
        if ms[eq + 1] in "=>":
            continue
        t = declared_type(ms, eq)
        if not t:
            continue
        paren = m.end() - 1
        out.append(s[pos:paren])
        out.append(" " + t if not s[paren - 1].isspace() else t)
        pos = paren
        count += 1
    out.append(s[pos:])
    return "".join(out), count


def operand_start(s, i):
    """i: index of last char of the operand before `is`. Return start index or -1."""
    j = i
    while j >= 0:
        c = s[j]
        if c in ")]":
            j = match_back(s, j, c, "(" if c == ")" else "[")
            if j < 0:
                return -1
            j -= 1
            continue
        if c.isalnum() or c in "_.":
            k = ident_back(s, j, dots=True)
            word = s[k:j + 1]
            if word in STOP_KEYWORDS:
                return j + 1
            j = k - 1
            continue
        if c == "?" and j + 1 < len(s) and s[j + 1] in ".[":
            j -= 1
            continue
        if c == "!" and j + 1 < len(s) and s[j + 1] != "=":
            j -= 1
            continue
        if c in " \t\r\n":
            k = skip_ws_back(s, j)
            if k < 0:
                return k + 1
            if s[k].isalnum() or s[k] == "_":
                w = s[ident_back(s, k):k + 1]
                if w in STOP_KEYWORDS:
                    return j + 1
                return -1  # two adjacent identifiers: not something we understand
            if s[k] in ".?":
                j = k
                continue
            return j + 1
        if c in "(,;{}=&|^:?[":
            return j + 1
        return -1  # arithmetic/relational/other: leave for manual fixing
    return 0


def pattern_end(s, i):
    """i: start of type pattern after `is not `. Return end index (exclusive) or -1."""
    m = re.compile(r"[A-Za-z_][\w.]*").match(s, i)
    if not m:
        return -1
    j = m.end()
    if j < len(s) and s[j] == "<":
        depth = 0
        while j < len(s):
            if s[j] == "<":
                depth += 1
            elif s[j] == ">":
                depth -= 1
                if depth == 0:
                    j += 1
                    break
            j += 1
    while j + 1 < len(s) and s[j:j + 2] == "[]":
        j += 2
    k = j
    while k < len(s) and s[k] in " \t":
        k += 1
    d = IDENT.match(s, k)
    if d and d.group(0) not in ("and", "or", "when", "is", "as"):
        j = d.end()
        k = j
        while k < len(s) and s[k] in " \t":
            k += 1
        d = IDENT.match(s, k)
    if d and d.group(0) in ("and", "or"):
        return -1
    return j


def rewrite_is_not(s):
    count = 0
    ms = mask(s)
    for m in reversed(list(re.finditer(r"\bis\s+not\s+null\b", ms))):
        s = s[:m.start()] + "is object" + s[m.end():]
        count += 1
    skip = set()
    while True:
        changed = False
        ms = mask(s)
        for m in re.finditer(r"\bis\s+not\s+", ms):
            if m.start() in skip:
                continue
            pe = pattern_end(ms, m.end())
            if pe < 0:
                skip.add(m.start())
                continue
            last = skip_ws_back(ms, m.start() - 1)
            st = operand_start(ms, last)
            if st < 0:
                skip.add(m.start())
                continue
            while s[st] in " \t\r\n":
                st += 1
            operand = s[st:last + 1]
            pattern = s[m.end():pe]
            s = s[:st] + "!(" + operand + " is " + pattern + ")" + s[pe:]
            count += 1
            changed = True
            break
        if not changed:
            break
    return s, count


def main():
    total_new = total_isnot = 0
    for root_dir in sys.argv[1:]:
        for dp, _, fns in os.walk(root_dir):
            for fn in fns:
                if not fn.endswith(".cs"):
                    continue
                p = os.path.join(dp, fn)
                raw = open(p, "rb").read()
                bom = raw.startswith(b"\xef\xbb\xbf")
                s = raw.decode("utf-8-sig")
                s2, a = rewrite_new(s)
                s2, b = rewrite_is_not(s2)
                if s2 != s:
                    data = s2.encode("utf-8")
                    open(p, "wb").write((b"\xef\xbb\xbf" if bom else b"") + data)
                    total_new += a
                    total_isnot += b
    print(f"new(): {total_new}, is not: {total_isnot}")


main()
