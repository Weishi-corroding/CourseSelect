# 智能选课系统 - 模块化版本

## 项目结构

```
Course/
├── main.py              # 主程序入口和主窗口
├── config.py            # 配置和常量（色彩主题、样式表、文件路径）
├── core.py              # 核心功能（登录、选课、文件操作）
├── threads.py           # 后台线程处理（非阻塞选课）
├── ui_components.py     # 自定义 UI 组件（菜单栏等）
├── dialogs.py           # 对话框和输入框（应用样式表）
├── __init__.py          # 包初始化文件
├── sccourse.py          # 旧版本（已备份为 sccourse.py.bak）
├── accounts.json        # 选课人账户列表
├── courses.json         # 课程列表（按用户）
├── cookies.json         # Cookie 存储
└── README.md            # 本文档
```

## 模块说明

### 1. **config.py** - 配置管理
- **颜色主题**: Nord Dark Theme 配色方案
- **样式表**: 全局 PyQt5 样式表（包括对话框、输入框等）
- **常量**: 文件路径、URL 等

**作用**: 统一管理所有配置，便于修改主题和常量

```python
from config import NORD_THEME, APP_STYLESHEET, FILES
```

### 2. **core.py** - 核心功能
- `get_cookies(name, password)` - Selenium 登录获取 Cookie
- `sccourse(cookies, courseid)` - curl 提交选课请求
- 文件操作: `load_accounts()`, `save_accounts()`, `load_courses()` 等

**作用**: 隔离业务逻辑，便于单独测试

```python
from core import get_cookies, sccourse, load_accounts, save_courses
```

### 3. **threads.py** - 后台线程
- `CourseSelectionThread` - 非阻塞式选课循环

**作用**: 独立处理耗时操作，防止 UI 冻结

```python
from threads import CourseSelectionThread
```

### 4. **ui_components.py** - UI 组件
- `CustomMenuBar` - 自定义菜单栏（logo + 菜单 + 窗口控制）

**作用**: 可复用的 UI 部件，便于修改样式

```python
from ui_components import CustomMenuBar
```

### 5. **dialogs.py** - 对话框（已应用样式表）
- `StyledInputDialog` - 样式化输入对话框
- `StyledMessageBox` - 样式化消息框
- `get_text_input()` - 单行输入
- `get_multiline_input()` - 多行输入（自定义对话框）

**作用**: 所有弹出窗口都应用 Nord 主题样式表

```python
from dialogs import StyledMessageBox, get_text_input, get_multiline_input
```

### 6. **main.py** - 主程序
- `MainWindow` - 主应用窗口
- `main()` - 应用入口

**作用**: 组织所有模块，实现完整的应用逻辑

## 运行程序

```bash
cd d:\Course
python main.py
```

## 测试各模块

### 测试核心功能 (core.py)
```bash
python -c "
from core import load_accounts, load_courses, load_cookies_dict
print('Accounts:', load_accounts())
print('Courses:', load_courses())
print('Cookies:', load_cookies_dict())
"
```

### 测试对话框样式
```bash
python -c "
from PyQt5.QtWidgets import QApplication
from dialogs import StyledMessageBox, get_text_input
app = QApplication([])
text, ok = get_text_input(None, 'Test', 'Enter text:')
print(f'Input: {text}')
"
```

### 测试线程
```bash
python -c "
from threads import CourseSelectionThread
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QCoreApplication

app = QApplication([])
thread = CourseSelectionThread('test_cookie', ['123'], 'user', 'pass')
thread.update_status.connect(print)
thread.start()
QCoreApplication.processEvents()
"
```

## 改进的功能

### 1. 对话框样式修复
- ✅ 新建选课人、新建课程等弹出窗口现在应用完整的 Nord 主题样式表
- ✅ 自定义多行输入对话框，支持 Consolas 字体
- ✅ 所有消息框（信息、警告、错误）统一风格

### 2. 代码模块化
- ✅ 分离关注点：配置、业务逻辑、UI、对话框、线程
- ✅ 便于单独测试各个模块
- ✅ 便于修改和扩展（改一个颜色只需改 config.py）
- ✅ 减少单文件代码行数（从 650+ 行分散到多个专业模块）

## 维护建议

1. **新增功能**: 在对应模块中添加，e.g., 新增登录方式 → 修改 `core.py`
2. **修改样式**: 统一修改 `config.py` 中的样式表
3. **新增 UI 组件**: 在 `ui_components.py` 中创建，并在 `dialogs.py` 或 `main.py` 中使用
4. **测试**: 每个模块都可以独立导入和测试

## 文件依赖关系

```
main.py
├── config.py (配置、样式表)
├── ui_components.py (菜单栏组件)
│   └── config.py
├── dialogs.py (样式化对话框)
│   └── config.py
├── threads.py (后台线程)
│   └── core.py
└── core.py (业务逻辑)
```

所有模块都可以独立导入，无循环依赖。

## 原文件备份

原始的 `sccourse.py` 已备份为 `sccourse.py.bak`。若需恢复，执行：
```bash
cp sccourse.py.bak sccourse.py
```
