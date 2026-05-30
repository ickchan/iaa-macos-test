import QtQuick
import QtQuick.Window

// Custom title bar for frameless window (Windows only).
//
// Button hit-test layout (right → left, each 46 px wide):
//   close    → HTCLIENT     — QML handles click + hover
//   maximize → HTMAXBUTTON  — OS handles click (snap-layout popup on hover);
//              hover state fed back via maxHoverBridge.hoveredChanged signal
//   minimize → HTCLIENT     — QML handles click + hover
//
// Icons use Segoe Fluent Icons (Win 11) / Segoe MDL2 Assets (Win 10) so the
// glyphs are identical to the native caption buttons.
Item {
    id: root
    height: 32

    signal minimizeRequested()
    signal closeRequested()

    readonly property string _iconFont: "Segoe Fluent Icons"

    // Tracks OS-reported hover for the maximize button (Windows only).
    // On Windows, HTMAXBUTTON steals mouse events from Qt; maxHoverBridge
    // relays WM_NCMOUSEMOVE/WM_NCMOUSELEAVE so we can show a hover highlight.
    property bool _maxHoveredByOS: false

    Connections {
        target: (Qt.platform.os === "windows" && typeof maxHoverBridge !== "undefined")
            ? maxHoverBridge : null
        function onHoveredChanged(hovered) { root._maxHoveredByOS = hovered }
    }

    // ── Minimize ──────────────────────────────────────────────────────────────
    Rectangle {
        id: minBtn
        width: 46; height: parent.height
        anchors.right: maxBtn.left
        color: _minHover.containsMouse
            ? Qt.rgba(palette.windowText.r, palette.windowText.g, palette.windowText.b, 0.08)
            : "transparent"

        Text {
            anchors.centerIn: parent
            font.family: root._iconFont
            font.pixelSize: 10
            text: "\uE921"       // ChromeMinimize
            color: palette.windowText
        }
        MouseArea {
            id: _minHover
            anchors.fill: parent
            hoverEnabled: true
            onClicked: root.minimizeRequested()
        }
    }

    // ── Maximize / Restore ────────────────────────────────────────────────────
    Rectangle {
        id: maxBtn
        width: 46; height: parent.height
        anchors.right: closeBtn.left

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
            // ChromeRestore (E923) when maximised, ChromeMaximize (E922) otherwise
            text: window.visibility === Window.Maximized ? "\uE923" : "\uE922"
            color: palette.windowText
        }
        MouseArea {
            id: _maxHover
            anchors.fill: parent
            // On Windows the OS intercepts mouse events over HTMAXBUTTON;
            // enable the MouseArea only on other platforms.
            hoverEnabled: Qt.platform.os !== "windows"
            enabled:      Qt.platform.os !== "windows"
            onClicked: {
                if (window.visibility === Window.Maximized) window.showNormal()
                else window.showMaximized()
            }
        }
    }

    // ── Close ─────────────────────────────────────────────────────────────────
    Rectangle {
        id: closeBtn
        width: 46; height: parent.height
        anchors.right: parent.right
        color: _closeHover.containsMouse ? "#c42b1c" : "transparent"

        Text {
            anchors.centerIn: parent
            font.family: root._iconFont
            font.pixelSize: 10
            text: "\uE8BB"       // ChromeClose
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
