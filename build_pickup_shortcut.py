import plistlib
import uuid

IGNORE_REGEX = r"已取件|已签收|已领取|已取出|验证码|登录码|动态码|退回|已退|派送中"
STATION_REGEX = r"(?<=【)[^】]{1,20}(?=】)"
CODE_REGEX = (
    r"(?<![0-9A-Za-z\-])"
    r"(?:[A-Za-z]-\d{1,3}-\d{1,5}|\d{1,3}-\d{1,3}-\d{1,5}|\d{1,2}-\d{3,5})"
    r"(?![0-9A-Za-z\-])"
    r"|(?:(?<=取件码)|(?<=取件码：)|(?<=取件码:)|(?<=取件码 )|(?<=取件码: )"
    r"|(?<=提货码)|(?<=提货码：)|(?<=提货码 )|(?<=取货码)|(?<=取货码：)"
    r"|(?<=凭码)|(?<=凭))"
    r"[0-9A-Za-z]{4,8}(?![0-9A-Za-z\-])"
)

def u():
    return str(uuid.uuid4()).upper()

def action_out_ref(output_uuid: str, output_name: str):
    return {
        "Value": {"OutputName": output_name, "OutputUUID": output_uuid, "Type": "ActionOutput"},
        "WFSerializationType": "WFTextTokenAttachment",
    }

def shortcut_input_ref():
    return {
        "Value": {"Type": "ExtensionInput"},
        "WFSerializationType": "WFTextTokenAttachment",
    }

def token_string(parts):
    text = ""
    attachments = {}
    for p in parts:
        if isinstance(p, str):
            text += p
        else:
            pos = len(text)
            text += "\ufffc"
            attachments[f"{{{pos}, 1}}"] = p
    return {
        "Value": {"attachmentsByRange": attachments, "string": text},
        "WFSerializationType": "WFTextTokenString",
    }

def build_shortcut(out_path: str):
    id_ignore = u()
    grp_ignore = u()
    id_station_match = u()
    grp_station = u()
    id_station_first = u()
    id_station_default = u()
    id_code_match = u()
    grp_empty = u()
    grp_repeat = u()
    id_combine = u()

    actions = [
        {"WFWorkflowActionIdentifier": "is.workflow.actions.setvariable", "WFWorkflowActionParameters": {"WFInput": shortcut_input_ref(), "WFVariableName": "rawText"}},
        {"WFWorkflowActionIdentifier": "is.workflow.actions.text.match", "WFWorkflowActionParameters": {"UUID": id_ignore, "WFMatchTextCaseSensitive": False, "WFMatchTextPattern": IGNORE_REGEX, "text": token_string([{"Type": "Variable", "VariableName": "rawText"}])}},
        {"WFWorkflowActionIdentifier": "is.workflow.actions.conditional", "WFWorkflowActionParameters": {"GroupingIdentifier": grp_ignore, "WFCondition": 100, "WFControlFlowMode": 0, "WFInput": {"Type": "Variable", "VariableName": action_out_ref(id_ignore, "Matches")}}},
        {"WFWorkflowActionIdentifier": "is.workflow.actions.exit", "WFWorkflowActionParameters": {}},
        {"WFWorkflowActionIdentifier": "is.workflow.actions.conditional", "WFWorkflowActionParameters": {"GroupingIdentifier": grp_ignore, "WFControlFlowMode": 2}},
        {"WFWorkflowActionIdentifier": "is.workflow.actions.text.match", "WFWorkflowActionParameters": {"UUID": id_station_match, "WFMatchTextCaseSensitive": False, "WFMatchTextPattern": STATION_REGEX, "text": token_string([{"Type": "Variable", "VariableName": "rawText"}])}},
        {"WFWorkflowActionIdentifier": "is.workflow.actions.conditional", "WFWorkflowActionParameters": {"GroupingIdentifier": grp_station, "WFCondition": 100, "WFControlFlowMode": 0, "WFInput": {"Type": "Variable", "VariableName": action_out_ref(id_station_match, "Matches")}}},
        {"WFWorkflowActionIdentifier": "is.workflow.actions.getitemfromlist", "WFWorkflowActionParameters": {"UUID": id_station_first, "WFInput": action_out_ref(id_station_match, "Matches"), "WFItemSpecifier": "First Item"}},
        {"WFWorkflowActionIdentifier": "is.workflow.actions.setvariable", "WFWorkflowActionParameters": {"WFInput": action_out_ref(id_station_first, "Item from List"), "WFVariableName": "station"}},
        {"WFWorkflowActionIdentifier": "is.workflow.actions.conditional", "WFWorkflowActionParameters": {"GroupingIdentifier": grp_station, "WFControlFlowMode": 1}},
        {"WFWorkflowActionIdentifier": "is.workflow.actions.gettext", "WFWorkflowActionParameters": {"UUID": id_station_default, "WFTextActionText": "快递"}},
        {"WFWorkflowActionIdentifier": "is.workflow.actions.setvariable", "WFWorkflowActionParameters": {"WFInput": action_out_ref(id_station_default, "Text"), "WFVariableName": "station"}},
        {"WFWorkflowActionIdentifier": "is.workflow.actions.conditional", "WFWorkflowActionParameters": {"GroupingIdentifier": grp_station, "WFControlFlowMode": 2}},
        {"WFWorkflowActionIdentifier": "is.workflow.actions.text.match", "WFWorkflowActionParameters": {"UUID": id_code_match, "WFMatchTextCaseSensitive": False, "WFMatchTextPattern": CODE_REGEX, "text": token_string([{"Type": "Variable", "VariableName": "rawText"}])}},
        {"WFWorkflowActionIdentifier": "is.workflow.actions.conditional", "WFWorkflowActionParameters": {"GroupingIdentifier": grp_empty, "WFCondition": 101, "WFControlFlowMode": 0, "WFInput": {"Type": "Variable", "VariableName": action_out_ref(id_code_match, "Matches")}}},
        {"WFWorkflowActionIdentifier": "is.workflow.actions.exit", "WFWorkflowActionParameters": {}},
        {"WFWorkflowActionIdentifier": "is.workflow.actions.conditional", "WFWorkflowActionParameters": {"GroupingIdentifier": grp_empty, "WFControlFlowMode": 2}},
        {"WFWorkflowActionIdentifier": "is.workflow.actions.repeat.each", "WFWorkflowActionParameters": {"GroupingIdentifier": grp_repeat, "WFControlFlowMode": 0, "WFInput": action_out_ref(id_code_match, "Matches")}},
        {"WFWorkflowActionIdentifier": "is.workflow.actions.addnewreminder", "WFWorkflowActionParameters": {"WFCalendarItemCalendar": "待取快递", "WFCalendarItemNotes": token_string([{"Type": "Variable", "VariableName": "rawText"}]), "WFCalendarItemTitle": token_string([{"Type": "Variable", "VariableName": "Repeat Item"}, " · ", {"Type": "Variable", "VariableName": "station"}])}},
        {"WFWorkflowActionIdentifier": "is.workflow.actions.repeat.each", "WFWorkflowActionParameters": {"GroupingIdentifier": grp_repeat, "WFControlFlowMode": 2}},
        {"WFWorkflowActionIdentifier": "is.workflow.actions.text.combine", "WFWorkflowActionParameters": {"UUID": id_combine, "WFTextCustomSeparator": " / ", "WFTextSeparator": "Custom", "text": action_out_ref(id_code_match, "Matches")}},
        {"WFWorkflowActionIdentifier": "is.workflow.actions.notification", "WFWorkflowActionParameters": {"WFNotificationActionBody": token_string([{"OutputName": "Combined Text", "OutputUUID": id_combine, "Type": "ActionOutput"}, " · ", {"Type": "Variable", "VariableName": "station"}]), "WFNotificationActionTitle": "📦 新取件码已上桌面"}},
    ]

    shortcut = {
        "WFWorkflowActions": actions,
        "WFWorkflowClientVersion": "2605.0.5",
        "WFWorkflowHasOutputFallback": False,
        "WFWorkflowHasShortcutInputVariables": True,
        "WFWorkflowIcon": {"WFWorkflowIconGlyphNumber": 59761, "WFWorkflowIconStartColor": 4274264319},
        "WFWorkflowImportQuestions": [{"ActionIndex": 18, "Category": "Parameter", "DefaultValue": "待取快递", "ParameterKey": "WFCalendarItemCalendar", "Text": "请选择用来显示取件码的「提醒事项」列表（建议选『待取快递』）"}],
        "WFWorkflowInputContentItemClasses": ["WFStringContentItem"],
        "WFWorkflowMinimumClientVersion": 900,
        "WFWorkflowMinimumClientVersionString": "900",
        "WFWorkflowNoInputBehavior": {"Name": "WFWorkflowNoInputBehaviorGetClipboard", "Parameters": {}},
        "WFWorkflowOutputContentItemClasses": [],
        "WFWorkflowTypes": ["NCWidget", "Watch", "ActionExtension"],
    }
    with open(out_path, "wb") as f:
        plistlib.dump(shortcut, f, fmt=plistlib.FMT_BINARY)
    print("Wrote:", out_path)

if __name__ == "__main__":
    build_shortcut("pickup_unsigned.shortcut")
