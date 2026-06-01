import QtQuick
import QtQuick.Controls
import QtQuick.Window

// Windows 窗口控件（最小化 / 最大化 / 关闭）。
// hit-test 布局（从右到左，各 46px）：
//   close    → HTCLIENT（QML 处理点击 + hover）
//   maximize → HTMAXBUTTON（OS 处理贴靠布局弹窗；hover 由 maxHoverBridge 中转）
//   minimize → HTCLIENT（QML 处理点击 + hover）
Row {
    id: root

    signal minimizeRequested()
    signal closeRequested()

    // maxHoverBridge 从 QML 上下文全局属性获取，无需作为属性传入
    required property var window

    visible: Qt.platform.os === "windows"
    spacing: 0

    readonly property string _iconFont: "Segoe Fluent Icons"
    property bool _maxHoveredByOS: false

    Connections {
        target: (Qt.platform.os === "windows" && typeof maxHoverBridge !== "undefined")
            ? maxHoverBridge : null
        function onHoveredChanged(hovered) { root._maxHoveredByOS = hovered }
    }

    // ── Minimize（E921 = ChromeMinimize）─────────────────────────────
    Rectangle {
        width: 46; height: root.height
        color: _minHover.containsMouse
            ? Qt.rgba(palette.windowText.r, palette.windowText.g, palette.windowText.b, 0.08)
            : "transparent"
        Text {
            anchors.centerIn: parent
            font.family: root._iconFont
            font.pixelSize: 10
            text: ""
            color: palette.windowText
        }
        MouseArea {
            id: _minHover
            anchors.fill: parent
            hoverEnabled: true
            onClicked: root.minimizeRequested()
        }
    }

    // ── Maximize / Restore（E922 / E923）──────────────────────────────
    Rectangle {
        width: 46; height: root.height
        readonly property bool _hovered: Qt.platform.os === "windows"
            ? root._maxHoveredByOS
            : _maxHover.containsMouse
        color: _hovered
            ? Qt.rgba(palette.windowText.r, palette.windowText.g, palette.windowText.b, 0.08)
            : "transparent"
        Text {
            anchors.centerIn: parent
            font.family: root._iconFont
            font.pixelSize: 10
            text: root.window.visibility === Window.Maximized ? "" : ""
            color: palette.windowText
        }
        MouseArea {
            id: _maxHover
            anchors.fill: parent
            hoverEnabled: Qt.platform.os !== "windows"
            enabled:      Qt.platform.os !== "windows"
            onClicked: {
                if (root.window.visibility === Window.Maximized) root.window.showNormal()
                else root.window.showMaximized()
            }
        }
    }

    // ── Close（E8BB = ChromeClose）────────────────────────────────────
    Rectangle {
        width: 46; height: root.height
        color: _closeHover.containsMouse ? "#c42b1c" : "transparent"
        Text {
            anchors.centerIn: parent
            font.family: root._iconFont
            font.pixelSize: 10
            text: ""
            color: _closeHover.containsMouse ? "white" : palette.windowText
        }
        MouseArea {
            id: _closeHover
            anchors.fill: parent
            hoverEnabled: true
            onClicked: root.closeRequested()
        }
    }
}
