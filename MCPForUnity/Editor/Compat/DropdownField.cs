#if !UNITY_2021_1_OR_NEWER
using System;
using System.Collections.Generic;
using System.Linq;
using UnityEditor.UIElements;
using UnityEngine.UIElements;

namespace MCPForUnity.Editor
{
    /// <summary>
    /// Unity 2020.3 stand-in for UnityEngine.UIElements.DropdownField (added in 2021.1).
    /// It is a PopupField&lt;string&gt; registered under the same UXML name, so <c>ui:DropdownField</c>
    /// in UXML and <c>DropdownField</c> in code under the MCPForUnity.Editor namespace keep working.
    /// </summary>
    public class DropdownField : PopupField<string>
    {
        public new class UxmlFactory : UxmlFactory<DropdownField, UxmlTraits>
        {
            // Factories are looked up by uxmlQualifiedName, which defaults to typeof(T).FullName
            // rather than uxmlNamespace + uxmlName, so all three are overridden.
            public override string uxmlName => "DropdownField";
            public override string uxmlNamespace => "UnityEngine.UIElements";
            public override string uxmlQualifiedName => "UnityEngine.UIElements.DropdownField";
        }

        public new class UxmlTraits : BaseField<string>.UxmlTraits
        {
            private readonly UxmlStringAttributeDescription m_Choices = new UxmlStringAttributeDescription { name = "choices" };
            private readonly UxmlIntAttributeDescription m_Index = new UxmlIntAttributeDescription { name = "index", defaultValue = -1 };

            public override void Init(VisualElement ve, IUxmlAttributes bag, CreationContext cc)
            {
                base.Init(ve, bag, cc);
                var field = (DropdownField)ve;

                string choices = m_Choices.GetValueFromBag(bag, cc);
                if (!string.IsNullOrEmpty(choices))
                {
                    field.choices = choices.Split(',').Select(c => c.Trim()).ToList();
                }

                int index = m_Index.GetValueFromBag(bag, cc);
                if (index >= 0 && field.choices != null && index < field.choices.Count)
                {
                    field.index = index;
                }
            }
        }

        public DropdownField() : this(null) { }

        public DropdownField(string label) : base(label) { }

        public DropdownField(List<string> choices, int defaultIndex,
            Func<string, string> formatSelectedValueCallback = null,
            Func<string, string> formatListItemCallback = null)
            : base(choices, defaultIndex, formatSelectedValueCallback, formatListItemCallback) { }

        public DropdownField(string label, List<string> choices, int defaultIndex,
            Func<string, string> formatSelectedValueCallback = null,
            Func<string, string> formatListItemCallback = null)
            : base(label, choices, defaultIndex, formatSelectedValueCallback, formatListItemCallback) { }
    }
}
#endif
