pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import "../components"

ColumnLayout {
    id: root

    required property var field
    required property var formController

    spacing: 4

    function _normalizeOption(item, category) {
        if (item && typeof item === "object") {
            let label = item.label !== undefined && item.label !== null ? String(item.label) : ""
            let value = item.value !== undefined ? item.value : item
            let image = item.image !== undefined && item.image !== null ? item.image
                : (item.icon !== undefined && item.icon !== null ? item.icon
                    : (item.img !== undefined && item.img !== null ? item.img : ""))
            let group = item.category !== undefined && item.category !== null
                ? String(item.category)
                : (item.group !== undefined && item.group !== null ? String(item.group)
                    : (category || ""))
            return {
                label: label,
                value: value,
                image: image ? String(image) : "",
                category: group,
            }
        }
        let text = String(item)
        return { label: text, value: item, image: "", category: category || "" }
    }

    function _flattenOptions(options) {
        let flat = []
        if (!Array.isArray(options)) {
            return flat
        }
        if (options.length > 0 && options[0] && typeof options[0] === "object" && Array.isArray(options[0].options)) {
            for (let i = 0; i < options.length; ++i) {
                let group = options[i]
                let title = group.group || group.title || group.label || ""
                let items = Array.isArray(group.options) ? group.options : []
                for (let j = 0; j < items.length; ++j) {
                    flat.push(_normalizeOption(items[j], title))
                }
            }
            return flat
        }
        for (let i = 0; i < options.length; ++i) {
            flat.push(_normalizeOption(options[i], ""))
        }
        return flat
    }

    function _selectedValue() {
        let value = root.field.value
        if (Array.isArray(value) && value.length > 0) {
            return value[0]
        }
        return value
    }

    function _indexOfValue(items, value) {
        if (!items) {
            return -1
        }
        for (let i = 0; i < items.length; ++i) {
            if (items[i].value === value) {
                return i
            }
        }
        return -1
    }

    property var normalizedOptions: _flattenOptions(root.field.options || [])

    FormField {
        Layout.fillWidth: true
        labelText: root.field.label
        helpText: root.field.helpText || ""
        errorText: root.field.error || ""

        GridItemPicker {
            id: picker
            Layout.fillWidth: true
            enabled: !!root.field.enabled
            model: root.normalizedOptions
            textRole: "label"
            valueRole: "value"
            imageRole: "image"
            categoryRole: "category"
            columns: root.field.props && root.field.props.columns !== undefined && root.field.props.columns !== null
                ? root.field.props.columns
                : 0
            cellSize: root.field.props && root.field.props.cellSize !== undefined && root.field.props.cellSize !== null
                ? root.field.props.cellSize
                : 68
            iconSize: root.field.props && root.field.props.iconSize !== undefined && root.field.props.iconSize !== null
                ? root.field.props.iconSize
                : 44
            popupMaxHeight: root.field.props && root.field.props.popupMaxHeight !== undefined
                && root.field.props.popupMaxHeight !== null
                ? root.field.props.popupMaxHeight
                : 0
            showLabel: !(root.field.props && root.field.props.showLabel === false)
            popupPadding: root.field.props && root.field.props.popupPadding !== undefined
                && root.field.props.popupPadding !== null
                ? root.field.props.popupPadding
                : 8
            cellRadius: root.field.props && root.field.props.cellRadius !== undefined
                && root.field.props.cellRadius !== null
                ? root.field.props.cellRadius
                : 8
            currentIndex: root._indexOfValue(root.normalizedOptions, root._selectedValue())

            onActivated: function(index) {
                let options = root.normalizedOptions
                if (index < 0 || index >= options.length) {
                    return
                }
                let selected = options[index]
                root.formController.setValue(root.field.id, selected.value)
            }
        }
    }
}
