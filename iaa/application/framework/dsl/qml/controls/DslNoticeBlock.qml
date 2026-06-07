pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root

    required property var field
    required property var formController

    implicitWidth: layout.implicitWidth + 24
    implicitHeight: layout.implicitHeight + 24

    readonly property bool isDark: Application.styleHints.colorScheme === Qt.Dark
    
    property color bgColor: isDark ? Qt.rgba(0.2, 0.4, 0.8, 0.2) : Qt.rgba(0.9, 0.95, 1.0, 1.0)
    property color borderColor: isDark ? Qt.rgba(0.3, 0.5, 0.9, 0.5) : Qt.rgba(0.6, 0.8, 1.0, 1.0)
    property color titleColor: isDark ? "#FFFFFF" : "#111111"

    Component.onCompleted: {
        const style = root.field.props ? root.field.props.style : "note";
        if (style === "tip") {
            bgColor = isDark ? Qt.rgba(0.1, 0.36, 0.12, 0.3) : "#E8F5E9"
            borderColor = isDark ? Qt.rgba(0.18, 0.49, 0.19, 0.5) : "#C8E6C9"
        } else if (style === "warning") {
            bgColor = isDark ? Qt.rgba(0.9, 0.31, 0.0, 0.2) : "#FFF3E0"
            borderColor = isDark ? Qt.rgba(0.93, 0.42, 0.0, 0.5) : "#FFE0B2"
        } else if (style === "error") {
            bgColor = isDark ? Qt.rgba(0.71, 0.1, 0.1, 0.2) : "#FFEBEE"
            borderColor = isDark ? Qt.rgba(0.77, 0.15, 0.15, 0.5) : "#FFCDD2"
        } else {
            // note
            bgColor = isDark ? Qt.rgba(0.05, 0.27, 0.63, 0.3) : "#E3F2FD"
            borderColor = isDark ? Qt.rgba(0.08, 0.39, 0.75, 0.5) : "#BBDEFB"
        }
    }

    Rectangle {
        anchors.fill: parent
        color: root.bgColor
        border.color: root.borderColor
        border.width: 1
        radius: 4
    }

    ColumnLayout {
        id: layout
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.margins: 12
        anchors.top: parent.top
        spacing: 4

        Label {
            Layout.fillWidth: true
            text: root.field.props && root.field.props.title ? root.field.props.title : ""
            visible: text !== ""
            font.weight: Font.DemiBold
            font.pixelSize: 13
            color: root.titleColor
            wrapMode: Text.Wrap
        }

        Label {
            Layout.fillWidth: true
            text: root.field.props && root.field.props.content ? root.field.props.content : ""
            wrapMode: Text.Wrap
        }
    }
}
