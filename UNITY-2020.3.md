# MCP for Unity: Unity 2020.3 backport

This branch (`unity-2020.3`) is [CoplayDev/unity-mcp](https://github.com/CoplayDev/unity-mcp) **v10.3.0**
with the Unity package (`MCPForUnity/`) ported to **Unity 2020.3 LTS** (tested against 2020.3.40f1).
Upstream supports only 2021.3 and newer.

Only the C# editor package changed. The Python MCP server is the upstream release, unchanged:
`mcpforunityserver==10.3.0` from PyPI, which the package starts through `uvx` as before. Requirements
are the same as upstream otherwise: Python 3.10+ and [`uv`](https://docs.astral.sh/uv/).

## Install into a Unity 2020.3 project

Pick one of:

- **Git URL (easiest to share):** Package Manager → **+** → **Add package from git URL…**, or add this to
  `Packages/manifest.json` (Git must be installed on the machine):
  ```json
  "com.coplaydev.unity-mcp": "https://github.com/akhilkalyani/unity-mcp-2020.3.git?path=/MCPForUnity#unity-2020.3"
  ```
  Replace `#unity-2020.3` with a tag (for example `#v10.3.0-unity2020.3-r2`) to pin an exact build.
- **Tarball inside the project repo (no network access needed):** build it with
  `python -I tools/unity-2020.3-backport/pack.py --revision <N>`, which writes
  `dist/com.coplaydev.unity-mcp-10.3.0-unity2020.3-r<N>.tgz` (about 700 KB). Copy it into the project
  repo and reference it relative to the `Packages` folder, so it resolves on every clone:
  ```json
  "com.coplaydev.unity-mcp": "file:../../shared_packages/com.coplaydev.unity-mcp-10.3.0-unity2020.3-r2.tgz"
  ```
  Use a new revision number for every rebuild: Unity only re-reads a tarball when its path changes.
- **Tarball on one machine:** Package Manager → **+** → **Add package from tarball…** and pick the `.tgz`.
  Unity records its location in the manifest, so keep the file where it is.
- **Local folder** while working on the backport itself:
  ```json
  "com.coplaydev.unity-mcp": "file:D:/Projects/unity-mcp-2020.3/MCPForUnity"
  ```

Avoid absolute paths in a manifest that other people or machines use: they break on any machine
where the file is somewhere else.

### On each machine

The package travels with the project, but every machine also needs:

1. **uv** (it provides Python and runs the server). Windows: `winget install astral-sh.uv`; macOS/Linux:
   `curl -LsSf https://astral.sh/uv/install.sh | sh`.
2. **Your MCP client**, e.g. the `claude` CLI for Claude Code.
3. In Unity: **Window → MCP for Unity**, start the server, and press **Configure** for your client. Client
   registration is per machine (Claude Code uses `claude mcp add --scope local`), so repeat this step on
   each device.

**Newtonsoft.Json:** the package needs exactly one Newtonsoft.Json package in the project. Unlike
upstream, it does not pull in `com.unity.nuget.newtonsoft-json` itself, because many 2020.3 projects
already ship `jillejr.newtonsoft.json-for-unity`, and having both breaks compilation (duplicate
`Newtonsoft.Json.dll`). If the project has neither, add `"com.unity.nuget.newtonsoft-json": "3.0.2"`.

Then, in Unity: **Window → MCP for Unity**, start the server, and configure your client (for Claude Code
the window runs `claude mcp add` for you). After that, prompt your client as usual, for example
*"Create a cube at the origin and add a Rigidbody."*

## What differs on 2020.3

Everything compiles and loads on 2020.3. A few features rely on Unity APIs that 2020.3 does not have:

| Area | On Unity 2020.3 |
|---|---|
| `manage_ui`: `attach_ui_document`, `detach_ui_document`, `create_panel_settings`, `update_panel_settings`, `get_visual_tree`, `render_ui`, `modify_visual_element` | Return an error: runtime UI Toolkit (UIDocument/PanelSettings) is only built in from 2021.2. Creating, reading, updating, linking, listing and deleting UXML/USS files still works. |
| `manage_build`: `server` subtarget | Mapped to headless mode (`enableHeadlessMode` / `BuildOptions.EnableHeadlessMode`). |
| `manage_build`: `clean_build` option | Ignored (`BuildOptions.CleanBuildCache` does not exist). |
| Lighting settings: lightmap compression | On/off only (`compressLightmaps`); quality levels map to "on". |
| Skybox/material properties of type `Int` | Not reported separately (2020.3 has no `ShaderPropertyType.Int`). |
| Profiler counters: `fileio` category | Not available. |
| Prefab colour baking from a `MaterialPropertyBlock` | A colour is treated as set when it is not `(0,0,0,0)` (no `HasColor` API). |
| Editor window: optional package install/remove | Packages are added/removed one at a time (no `Client.AddAndRemove`). |
| Editor window: update notification | Disabled, because upstream releases require 2021.3+. |

The editor window's dropdowns use a small `PopupField`-based stand-in for `DropdownField`
(`Editor/Compat/DropdownField.cs`).

## How the port was done

- C# 9 syntax rewritten to C# 8 (Unity 2020.3's compiler): target-typed `new()`, `is not` patterns,
  `or`/`and` patterns, target-typed `?:`.
- .NET Standard 2.1 APIs missing from 2020.3's .NET 4.x profile replaced with equivalents in
  `Editor/Compat/NetCompat.cs` (string overloads, `Math.Clamp`, `Path.GetRelativePath`,
  `ProcessStartInfo.ArgumentList`, PBKDF2-SHA256, and so on). Ranges/indices became `Substring` calls.
- Unity 2021+ editor APIs are behind `#if UNITY_2021_2_OR_NEWER` / `UNITY_2021_3_OR_NEWER`, with 2020.3
  fallbacks or small stand-ins in `Editor/Compat/` (`NamedBuildTarget`, `StandaloneBuildSubtarget`,
  `PackageInfoCompat`). `PrefabStage` comes from `UnityEditor.Experimental.SceneManagement` on 2020.3.
- The editor asmdef references `UnityEditor.TestRunner` / `UnityEngine.TestRunner` explicitly.

The newer-Unity code paths are kept, so this branch should still build on 2021.3+, but only 2020.3 was
compile-checked.

## Checking a build without opening Unity

`tools/unity-2020.3-backport/compile_check.py` compiles both assemblies with Unity 2020.3's Roslyn
(C# 8), using the references and defines from a 2020.3 project's generated `Assembly-CSharp-Editor.csproj`:

```bash
python -I tools/unity-2020.3-backport/compile_check.py --project "<path to a 2020.3 project>" --define UNITY_VFX_GRAPH
```

`downlevel.py` in the same folder repeats the mechanical C# 9 → C# 8 rewrites. It is useful as a first
pass when porting a newer upstream release; the compile check then lists whatever is left.
