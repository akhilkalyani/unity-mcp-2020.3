"""C# comment/string masker shared by the downlevel tools."""


def mask(s):
    """Same-length copy of s with comments and string/char literal contents replaced by '_'
    (newlines kept), so code-only regexes and bracket matching ignore them."""
    out = list(s)
    n = len(s)
    i = 0

    def blank(a, b):
        for k in range(a, b):
            if out[k] not in "\r\n":
                out[k] = "_"

    def scan_string(i):
        """i at the opening quote/prefix; return index after the literal."""
        j = i
        interp = verbatim = False
        while s[j] in "$@":
            interp |= s[j] == "$"
            verbatim |= s[j] == "@"
            j += 1
        j += 1  # opening quote
        while j < n:
            c = s[j]
            if verbatim and c == '"':
                if j + 1 < n and s[j + 1] == '"':
                    j += 2
                    continue
                return j + 1
            if not verbatim and c == "\\":
                j += 2
                continue
            if not verbatim and c == '"':
                return j + 1
            if interp and c == "{":
                if j + 1 < n and s[j + 1] == "{":
                    j += 2
                    continue
                depth = 1
                j += 1
                while j < n and depth:
                    if s[j] == '"' or (s[j] in "$@" and j + 1 < n and s[j + 1] in '"$@'):
                        j = scan_string(j)
                        continue
                    if s[j] == "{":
                        depth += 1
                    elif s[j] == "}":
                        depth -= 1
                    j += 1
                continue
            j += 1
        return j

    while i < n:
        c = s[i]
        if c == "/" and i + 1 < n and s[i + 1] == "/":
            j = s.find("\n", i)
            j = n if j < 0 else j
            blank(i, j)
            i = j
        elif c == "/" and i + 1 < n and s[i + 1] == "*":
            j = s.find("*/", i + 2)
            j = n if j < 0 else j + 2
            blank(i, j)
            i = j
        elif c == '"' or (c in "$@" and i + 1 < n and s[i + 1] in '"$@' and (s[i + 1] == '"' or (i + 2 < n and s[i + 2] == '"'))):
            j = scan_string(i)
            blank(i, j)
            i = j
        elif c == "'":
            j = i + 1
            while j < n and s[j] != "'":
                j += 2 if s[j] == "\\" else 1
            blank(i, j + 1)
            i = j + 1
        else:
            i += 1
    return "".join(out)
