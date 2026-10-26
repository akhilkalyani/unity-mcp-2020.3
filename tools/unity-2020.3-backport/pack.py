"""Pack MCPForUnity into a Unity package tarball (npm-pack layout: everything under `package/`).

The .tgz can be copied to any machine and installed with Package Manager > + > "Add package from
tarball...", or referenced from Packages/manifest.json as "file:<relative path to .tgz>".

usage: python -I pack.py --revision N [--package MCPForUnity] [--out dist]

Bump --revision on every rebuild: projects that reference the .tgz by path only re-resolve it
when the path in their manifest changes.
"""
import argparse
import gzip
import io
import json
import os
import tarfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))

ap = argparse.ArgumentParser()
ap.add_argument("--package", default=os.path.join(ROOT, "MCPForUnity"))
ap.add_argument("--out", default=os.path.join(ROOT, "dist"))
ap.add_argument("--revision", type=int, required=True, help="backport build number, appended as -r<N>")
args = ap.parse_args()

pkg = os.path.abspath(args.package)
version = json.load(open(os.path.join(pkg, "package.json"), encoding="utf-8"))["version"]
name = json.load(open(os.path.join(pkg, "package.json"), encoding="utf-8"))["name"]

files = []
missing_meta = []
for root, dirs, names in os.walk(pkg):
    dirs.sort()
    for d in dirs:
        if not os.path.exists(os.path.join(root, d) + ".meta"):
            missing_meta.append(os.path.relpath(os.path.join(root, d), pkg))
    for n in sorted(names):
        path = os.path.join(root, n)
        rel = os.path.relpath(path, pkg).replace(os.sep, "/")
        if not n.endswith(".meta") and not os.path.exists(path + ".meta"):
            missing_meta.append(rel)
        files.append((path, rel))

# Immutable (tarball/git) packages ignore assets without .meta files, so refuse to pack those.
if missing_meta:
    raise SystemExit("missing .meta files:\n  " + "\n  ".join(missing_meta))

os.makedirs(args.out, exist_ok=True)
out_path = os.path.join(args.out, f"{name}-{version}-unity2020.3-r{args.revision}.tgz")
buf = io.BytesIO()
with tarfile.open(fileobj=buf, mode="w", format=tarfile.PAX_FORMAT) as tar:
    for path, rel in files:
        info = tarfile.TarInfo("package/" + rel)
        data = open(path, "rb").read()
        info.size = len(data)
        info.mode = 0o644
        info.mtime = 0
        tar.addfile(info, io.BytesIO(data))
with open(out_path, "wb") as f:
    with gzip.GzipFile(filename="", mode="wb", fileobj=f, mtime=0) as gz:
        gz.write(buf.getvalue())

print(f"{out_path} ({len(files)} files, {os.path.getsize(out_path) // 1024} KB)")
