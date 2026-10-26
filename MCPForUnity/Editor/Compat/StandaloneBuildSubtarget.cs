#if !UNITY_2021_2_OR_NEWER
namespace MCPForUnity.Editor
{
    /// <summary>
    /// Unity 2020.3 stand-in for UnityEditor.StandaloneBuildSubtarget (added in 2021.2).
    /// Before 2021.2 a dedicated server build is a headless standalone build, so Server maps to
    /// EditorUserBuildSettings.enableHeadlessMode / BuildOptions.EnableHeadlessMode.
    /// </summary>
    public enum StandaloneBuildSubtarget
    {
        Player = 2,
        Server = 1,
    }
}
#endif
