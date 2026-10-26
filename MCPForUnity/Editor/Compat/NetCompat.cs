using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Security.Cryptography;
using System.Text;

namespace MCPForUnity.Editor
{
    /// <summary>
    /// Stand-ins for .NET Standard 2.1 / .NET Core APIs that are missing from the .NET 4.x profile of
    /// Unity 2020.3. The extension methods are picked up by everything under the MCPForUnity.Editor
    /// namespace; on newer editors the built-in instance methods take precedence.
    /// </summary>
    internal static class NetCompat
    {
        public static int Clamp(int value, int min, int max) => value < min ? min : value > max ? max : value;

        public static long Clamp(long value, long min, long max) => value < min ? min : value > max ? max : value;

        public static float Clamp(float value, float min, float max) => value < min ? min : value > max ? max : value;

        public static double Clamp(double value, double min, double max) => value < min ? min : value > max ? max : value;

        public static bool Contains(this string s, string value, StringComparison comparisonType)
            => s.IndexOf(value, comparisonType) >= 0;

        public static bool Contains(this string s, char value) => s.IndexOf(value) >= 0;

        public static int IndexOf(this string s, char value, StringComparison comparisonType)
            => s.IndexOf(value.ToString(), comparisonType);

        public static string Replace(this string s, string oldValue, string newValue, StringComparison comparisonType)
        {
            if (string.IsNullOrEmpty(oldValue))
                throw new ArgumentException("String cannot be of zero length.", nameof(oldValue));

            var sb = new StringBuilder(s.Length);
            int pos = 0;
            int idx;
            while ((idx = s.IndexOf(oldValue, pos, comparisonType)) >= 0)
            {
                sb.Append(s, pos, idx - pos).Append(newValue);
                pos = idx + oldValue.Length;
            }
            return sb.Append(s, pos, s.Length - pos).ToString();
        }

        public static bool Remove<TKey, TValue>(this Dictionary<TKey, TValue> dict, TKey key, out TValue value)
        {
            if (dict.TryGetValue(key, out value))
            {
                dict.Remove(key);
                return true;
            }
            return false;
        }

        public static bool TryParseEnum(Type enumType, string value, bool ignoreCase, out object result)
        {
            result = null;
            if (string.IsNullOrWhiteSpace(value))
                return false;
            try
            {
                result = Enum.Parse(enumType, value, ignoreCase);
                return true;
            }
            catch (ArgumentException)
            {
                return false;
            }
            catch (OverflowException)
            {
                return false;
            }
        }

        public static string GetRelativePath(string relativeTo, string path)
        {
            string from = Path.GetFullPath(relativeTo);
            string to = Path.GetFullPath(path);
            var comparison = Path.DirectorySeparatorChar == '\\' ? StringComparison.OrdinalIgnoreCase : StringComparison.Ordinal;

            char[] separators = { Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar };
            string[] fromParts = from.TrimEnd(separators).Split(separators);
            string[] toParts = to.TrimEnd(separators).Split(separators);

            int common = 0;
            while (common < fromParts.Length && common < toParts.Length
                   && string.Equals(fromParts[common], toParts[common], comparison))
            {
                common++;
            }
            if (common == 0)
                return to;

            var parts = new List<string>();
            for (int i = common; i < fromParts.Length; i++)
                parts.Add("..");
            for (int i = common; i < toParts.Length; i++)
                parts.Add(toParts[i]);
            return parts.Count == 0 ? "." : string.Join(Path.DirectorySeparatorChar.ToString(), parts);
        }

        /// <summary>Appends one argument to <see cref="ProcessStartInfo.Arguments"/>, quoted per the
        /// Windows/Mono command-line rules (replacement for ProcessStartInfo.ArgumentList).</summary>
        public static void AddArgument(this ProcessStartInfo psi, string argument)
        {
            string quoted = QuoteArgument(argument ?? string.Empty);
            psi.Arguments = string.IsNullOrEmpty(psi.Arguments) ? quoted : psi.Arguments + " " + quoted;
        }

        private static string QuoteArgument(string arg)
        {
            if (arg.Length > 0 && arg.IndexOfAny(new[] { ' ', '\t', '\n', '\v', '"' }) < 0)
                return arg;

            var sb = new StringBuilder("\"");
            int backslashes = 0;
            foreach (char c in arg)
            {
                if (c == '\\')
                {
                    backslashes++;
                    continue;
                }
                if (c == '"')
                {
                    sb.Append('\\', backslashes * 2 + 1).Append('"');
                }
                else
                {
                    sb.Append('\\', backslashes).Append(c);
                }
                backslashes = 0;
            }
            sb.Append('\\', backslashes * 2).Append('"');
            return sb.ToString();
        }

        /// <summary>PBKDF2-HMAC-SHA256, equivalent to
        /// <c>new Rfc2898DeriveBytes(password, salt, iterations, HashAlgorithmName.SHA256).GetBytes(length)</c>
        /// (that constructor is not available in Unity 2020.3).</summary>
        public static byte[] Pbkdf2Sha256(string password, byte[] salt, int iterations, int length)
        {
            byte[] result = new byte[length];
            using (var hmac = new HMACSHA256(new UTF8Encoding(false).GetBytes(password)))
            {
                int hashLength = hmac.HashSize / 8;
                byte[] block = new byte[salt.Length + 4];
                Buffer.BlockCopy(salt, 0, block, 0, salt.Length);
                int offset = 0;
                for (uint blockIndex = 1; offset < length; blockIndex++)
                {
                    block[salt.Length] = (byte)(blockIndex >> 24);
                    block[salt.Length + 1] = (byte)(blockIndex >> 16);
                    block[salt.Length + 2] = (byte)(blockIndex >> 8);
                    block[salt.Length + 3] = (byte)blockIndex;

                    byte[] u = hmac.ComputeHash(block);
                    byte[] t = (byte[])u.Clone();
                    for (int i = 1; i < iterations; i++)
                    {
                        u = hmac.ComputeHash(u);
                        for (int j = 0; j < hashLength; j++)
                            t[j] ^= u[j];
                    }

                    int count = Math.Min(hashLength, length - offset);
                    Buffer.BlockCopy(t, 0, result, offset, count);
                    offset += count;
                }
            }
            return result;
        }
    }
}
