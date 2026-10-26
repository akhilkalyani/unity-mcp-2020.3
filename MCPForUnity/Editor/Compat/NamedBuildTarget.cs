#if !UNITY_2021_2_OR_NEWER
using UnityEditor;

namespace MCPForUnity.Editor
{
    /// <summary>
    /// Unity 2020.3 stand-in for UnityEditor.Build.NamedBuildTarget (added in 2021.2), backed by
    /// BuildTargetGroup. The implicit conversion lets it flow into the BuildTargetGroup overloads of
    /// PlayerSettings that 2020.3 provides.
    /// </summary>
    public readonly struct NamedBuildTarget
    {
        public BuildTargetGroup TargetGroup { get; }

        public string TargetName => TargetGroup.ToString();

        private NamedBuildTarget(BuildTargetGroup targetGroup)
        {
            TargetGroup = targetGroup;
        }

        public static NamedBuildTarget FromBuildTargetGroup(BuildTargetGroup targetGroup) => new NamedBuildTarget(targetGroup);

        public BuildTargetGroup ToBuildTargetGroup() => TargetGroup;

        public static implicit operator BuildTargetGroup(NamedBuildTarget target) => target.TargetGroup;

        public override string ToString() => TargetName;
    }
}
#endif
