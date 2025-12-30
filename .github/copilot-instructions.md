# Copilot 指南 — CourseSelect 🧭

**目标（简短）**
- 帮助 AI 代理快速上手本仓库：理解整体架构、关键工作流、工程约定、外部依赖和常见陷阱。

## 1) 项目一览（关键点）
- GUI 桌面应用（PyQt5）用于自动化“教务选课”。
- 模块划分清晰：
  - `main.py` — 应用入口、UI 组合逻辑。
  - `config.py` — 颜色主题、样式表、常量与文件名（`FILES`）。
  - `core.py` — 业务逻辑（登录、通过 curl 提交选课/退选、文件 I/O）。
  - `threads.py` — 背景线程（`CourseSelectionThread`），避免阻塞 UI。
  - `dialogs.py` / `ui_components.py` — 弹窗与可复用 UI 组件。
- 本地持久化：JSON 文件放在仓库根目录（`accounts.json`, `courses.json`, `cookies.json`, `delete_courses.json`）。

## 2) 关键运行 / 打包 命令
- 本地运行（开发）：
  ```bash
  pip install -r requirements.txt
  python main.py
  ```
- 打包（Windows PowerShell 脚本）：
  ```powershell
  .\build_exe.ps1   # 会创建 .venv 并调用 pyinstaller
  ```
  注意：`build_exe.ps1` 会运行 `pyinstaller --onefile --windowed main.py`。

## 3) 外部依赖与运行时要求（重要）
- 浏览器自动化使用 Edge + Selenium：仓库包含 `msedgedriver.exe`（期望放在可执行目录）。如果 Edge 更新，请同步替换该驱动。
- 选课/退课请求使用 `curl`（通过 `subprocess.run` 调用）。在目标 Windows 环境需要可用的 `curl` 可执行文件，或将其替换为 `requests`。
- `requirements.txt`（PyQt5, selenium, beautifulsoup4, requests, pyinstaller, Pillow）

## 4) 项目特有约定与行为（必须掌握）
- JSON 格式示例：
  - `accounts.json` : {"accounts": [{"name": "张三", "username": "学号", "password": "密码"}, ...]}
  - `courses.json` : {"张三": ["courseId1", "courseId2"]}
  - `cookies.json` : {"张三": "name=value; name2=value2"}
  - `delete_courses.json` : {"张三": [{"courseCode":"COMP101","classNo":"1"}, ...]}
- `core.get_cookies(name, password, report_callback=None, debug_mode=False)`：
  - 使用 Edge（非 headless）执行登录并返回 cookies 列表（list of dicts）。
  - `report_callback` 用于把进度发送回 GUI（`status_box.append` 可直接传入）。
- `core.sccourse(cookies, courseid)` / `cancelSC(...)`：
  - 通过 `curl` 调用提交请求；返回字符串。
  - 返回值有错误前缀：`CALL_ERROR:`、`TIMEOUT:`、`EXCEPTION:`。
- `threads.CourseSelectionThread`：
  - 将 `sccourse` 的返回值解析：如果响应字符串包含 `"true"` 且不包含 `"Empty"` 则视为成功；若返回含 `"F"`，线程会尝试重新 `get_cookies()` 更新 cookie（这是项目内置的脆弱但现有的逻辑）。
  - 线程停止通过 `stop()`（设置 `is_running=False`），主线程应调用 `.wait()` 等待结束。
- 请求间隔：以秒为单位，默认 `request_interval = 2`（可以在设置对话框中修改）。

## 5) 常见故障 & 调试技巧 🔧
- 驱动不匹配：若 `get_cookies` 报驱动错误或 `Symbols not available`，需要替换 `msedgedriver.exe` 与系统 Edge 版本匹配。
- 无 `curl`：`sccourse`/`cancelSC` 会失败并返回 `CALL_ERROR`，可临时用 `requests` 替换实现以便排查。
- 在 GUI 中调试登录过程：给 `get_cookies(..., report_callback=self.status_box.append, debug_mode=True)` 以便获取更多日志。
- 无法选课但返回非异常：观察 `sccourse` 返回值字符串，线程逻辑基于关键字（`true`、`Empty`、`F`），修改解析需同步更新 `threads.py` 的判断。

## 6) 开发指南（在哪里改什么）
- 增加/修改样式：`config.py` → 修改 `APP_STYLESHEET` 或 `NORD_THEME`。
- 修改业务逻辑（登录/请求）：`core.py`。
- 修改多任务/并发策略：`threads.py`。
- UI 改动：`main.py`、`dialogs.py`、`ui_components.py`（保持事件/信号清晰，避免在主线程做长时间 I/O）。

## 7) 小样例（快速上手测试）
- 测试核心 I/O：
  ```bash
  python -c "from core import load_accounts, load_courses, load_cookies_dict; print(load_accounts(), load_courses(), load_cookies_dict())"
  ```
- 测试弹窗样式：
  ```bash
  python -c "from PyQt5.QtWidgets import QApplication; from dialogs import get_text_input; app=QApplication([]); print(get_text_input(None,'t','p'))"
  ```

## 8) 注意事项（对 AI 代理）⚠️
- 不要更改现有响应解析逻辑（`true`/`Empty`/`F`），除非同时更新 UI/threads 的处理与测试。
- 增加网络调用时优先复用 `core.py` 的接口风格（返回错误前缀或异常），以保持上层线程的错误处理兼容。
- 尽量保持 UI 线程无阻塞；新长任务请放入 `threads.py` 或引入异步模式并适配 PyQt 信号。

---

如果你希望我把某一节扩展为更详细的示例（例如：如何在 Windows 下替换 `msedgedriver` 并重建可执行文件，或把 `curl` 替换为 `requests`），告诉我想要扩展的部分，我会补充示例与测试步骤。 ✅