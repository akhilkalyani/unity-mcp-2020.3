"""Compile MCPForUnity with Unity 2020.3's own Roslyn (C# 8) against the references and defines Unity
uses for editor assemblies, without opening the editor.

References and defines are read from a Unity 2020.3 project's generated Assembly-CSharp-Editor.csproj
(open the project once in Unity with the Rider or Visual Studio package installed to generate it).
The project must contain com.unity.test-framework and a Newtonsoft.Json package.

usage:
  python -I compile_check.py --project <unity-project> [--unity <Editor dir>] [--package MCPForUnity]
                             [--out <dir>] [--define X] [--undefine Y]
"""
import argparse
import glob
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))

ap = argparse.ArgumentParser()
ap.add_argument("--project", required=True, help="Unity 2020.3 project with a generated Assembly-CSharp-Editor.csproj")
ap.add_argument("--unity", default=r"C:\Program Files\Unity\Hub\Editor\2020.3.40f1\Editor", help="Unity 2020.3 Editor folder")
ap.add_argument("--package", default=os.path.join(HERE, "..", "..", "MCPForUnity"))
ap.add_argument("--out", default=os.path.join(tempfile.gettempdir(), "mcpforunity-2020.3-check"))
ap.add_argument("--define", action="append", default=[])
ap.add_argument("--undefine", action="append", default=[])
args = ap.parse_args()

csc = os.path.join(args.unity, "Data", "Tools", "Roslyn", "csc.exe")
csproj = os.path.join(args.project, "Assembly-CSharp-Editor.csproj")
text = open(csproj, encoding="utf-8").read()
defines = re.search(r"<DefineConstants>([^<]*)", text).group(1).split(";")
defines = [d for d in defines if d and d not in args.undefine] + args.define

refs = []
for hp in re.findall(r"<HintPath>([^<]*)", text):
    p = hp if os.path.isabs(hp) else os.path.join(args.project, hp)
    if (p.lower().startswith(args.unity.lower()) and "PlaybackEngines" not in p) or "Newtonsoft.Json" in p:
        refs.append(p)
for name in ("UnityEditor.TestRunner.dll", "UnityEngine.TestRunner.dll"):
    refs.append(os.path.join(args.project, "Library", "ScriptAssemblies", name))

os.makedirs(args.out, exist_ok=True)


def compile_asm(name, src_dir, extra_refs):
    files = glob.glob(os.path.join(src_dir, "**", "*.cs"), recursive=True)
    out = os.path.join(args.out, name + ".dll")
    rsp = os.path.join(args.out, name + ".rsp")
    with open(rsp, "w", encoding="utf-8") as f:
        f.write("-target:library\n-nologo\n-langversion:8.0\n-nostdlib+\n-noconfig\n-deterministic\n")
        f.write("-nowarn:0169,0649,0414,0618,0612,1701,1702,0219,0162,0168,0067,8632\n")
        f.write(f'-out:"{out}"\n')
        f.write("-define:" + ";".join(defines) + "\n")
        for r in refs + extra_refs:
            f.write(f'-r:"{r}"\n')
        for s in files:
            f.write(f'"{s}"\n')
    proc = subprocess.run([csc, "@" + rsp], capture_output=True, text=True, encoding="utf-8", errors="replace")
    errors = [l for l in proc.stdout.splitlines() if ": error " in l]
    print(f"== {name}: {len(files)} files, exit {proc.returncode}, {len(errors)} errors")
    pkg = os.path.abspath(args.package)
    for l in errors:
        print(l.replace(pkg + os.sep, ""))
    return proc.returncode == 0, out


ok_rt, runtime = compile_asm("MCPForUnity.Runtime", os.path.join(args.package, "Runtime"), [])
ok_ed, _ = compile_asm("MCPForUnity.Editor", os.path.join(args.package, "Editor"), [runtime] if ok_rt else [])
sys.exit(0 if ok_rt and ok_ed else 1)
