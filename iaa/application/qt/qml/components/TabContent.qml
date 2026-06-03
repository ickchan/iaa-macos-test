import QtQuick
import QtQuick.Layouts
import "../pages"
import "../dialogs"

Item {
    id: root

    property var runCtrl: null
    property var progBridge: null
    property var logBridge: null
    property var formController: null
    property var navigation: null
    property bool prefsMode: false

    AutoLiveDialog {
        id: autoLiveDialog
        runCtrl: root.runCtrl
    }

    readonly property int sideNavIndex: sideNav.currentIndex

    RowLayout {
        anchors.fill: parent
        spacing: 0

        SideNavigationBar {
            id: sideNav
            Layout.fillHeight: true
            visible: !root.prefsMode
            model: ["控制", "配置", "日志", "关于"]

            onCurrentChanging: function(index, previousIndex) {
                if (root.navigation) {
                    root.navigation.requestGuardedAction("切换页面", function() {
                        sideNav.confirmSwitch(index)
                    })
                } else {
                    sideNav.confirmSwitch(index)
                }
            }
        }

        StackLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            visible: !root.prefsMode
            currentIndex: sideNav.currentIndex

            ControlPage {
                autoLiveDialog: autoLiveDialog
                runCtrl: root.runCtrl
                progBridge: root.progBridge
            }

            SettingsPage {
                formController: root.formController
                runCtrl: root.runCtrl
            }

            LogPage {
                logBridge: root.logBridge
            }

            AboutPage {}
        }
    }
}
