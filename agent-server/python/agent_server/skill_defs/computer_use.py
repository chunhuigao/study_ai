SKILL = {
    "id": "computer_use",
    "name": "Computer Use",
    "description": "受限桌面自动化能力，可打开浏览器/网页、读取浏览器状态、获取屏幕上下文、移动鼠标、点击、输入文本和执行快捷键。",
    "enabled": True,
    "builtin": True,
    "tools": [
        "computer_info",
        "computer_open",
        "computer_open_browser",
        "computer_browser_state",
        "computer_move_mouse",
        "computer_click",
        "computer_type_text",
        "computer_hotkey",
        "computer_wait",
    ],
    "instructions": (
        "只有当用户明确要求操作电脑、浏览器或桌面应用时才使用。"
        "打开浏览器或网页时优先用 computer_open_browser；"
        "确认当前页面时用 computer_browser_state；"
        "只有高层浏览器工具无法完成时，才使用坐标点击、鼠标移动和文本输入；"
        "执行点击和输入前，先用 computer_info 或 computer_browser_state 确认当前状态；"
        "用户要求登录时，只能打开登录页并等待用户手动输入账号、密码或验证码，不要索要、生成或提交密码；"
        "不要执行删除文件、提交表单、购买、转账或其他高风险操作。"
    ),
}
