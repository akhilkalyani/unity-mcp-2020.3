using System;
using System.Linq;
using System.Reflection;
using System.Threading;
using UnityEditor.PackageManager;

namespace MCPForUnity.Editor
{
    internal static class PackageInfoCompat
    {
        public static UnityEditor.PackageManager.PackageInfo[] GetAllRegisteredPackages()
        {
#if UNITY_2021_3_OR_NEWER
            return UnityEditor.PackageManager.PackageInfo.GetAllRegisteredPackages();
#else
            // Unity 2020.3 only has this as the internal PackageInfo.GetAll().
            var getAll = typeof(UnityEditor.PackageManager.PackageInfo).GetMethod(
                "GetAll", BindingFlags.Static | BindingFlags.Public | BindingFlags.NonPublic, null, Type.EmptyTypes, null);
            if (getAll?.Invoke(null, null) is UnityEditor.PackageManager.PackageInfo[] all)
            {
                return all;
            }

            var request = Client.List(true, true);
            var deadline = DateTime.UtcNow.AddSeconds(10);
            while (!request.IsCompleted && DateTime.UtcNow < deadline)
            {
                Thread.Sleep(10);
            }
            return request.IsCompleted && request.Status == StatusCode.Success
                ? request.Result.ToArray()
                : Array.Empty<UnityEditor.PackageManager.PackageInfo>();
#endif
        }
    }
}
