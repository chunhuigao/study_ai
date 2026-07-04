SKILL = {
    "id": "computer_use",
    "name": "Computer Use",
    "description": "受限桌面自动化能力，可获取屏幕上下文、打开 URL/应用、移动鼠标、点击、输入文本和执行快捷键。",
    "enabled": False,
    "builtin": True,
    "tools": [
        "computer_info",
        "computer_open",
        "computer_move_mouse",
        "computer_click",
        "computer_type_text",
        "computer_hotkey",
        "computer_wait",
    ],
    "instructions": (
        "只有当用户明确要求操作电脑、浏览器或桌面应用时才使用。"
        "执行点击和输入前，先用 computer_info 确认当前前台应用；"
        "不要执行删除文件、提交表单、购买、转账或其他高风险操作。"
    ),
}
