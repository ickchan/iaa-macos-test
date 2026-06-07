pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls

Column {
    id: root

    required property var field
    required property var formController

    spacing: 4

    CheckBox {
        text: root.field.label || ""
        enabled: !!root.field.enabled
        checked: !!root.field.value
        onToggled: root.formController.setValue(root.field.id, checked)
    }

}
