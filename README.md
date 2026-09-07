# CourseSelect

东华大学选课辅助桌面工具，提供账号管理、课程查询、课程计划、选课监控、捡漏监控和升级课程等功能。

最新 Windows 版本可在 [GitHub Releases](https://github.com/Weishi-corroding/CourseSelect/releases) 下载。

## 功能

- 管理多个选课人及其登录 Cookie。
- 拉取学期课程与课表数据，自动按服务器总记录分页获取。
- 按课程代码、名称、教师、校区、上课时间和剩余名额查询课程。
- 余量统一按“课程容量 − 已录取人数”计算。
- 将课程班级（`cttId`）加入待选或待删除计划；列表支持 Ctrl 多选和 Delete 删除。
- 对待选课程并发选课，支持验证码输入和 PushPlus 通知。
- 监控待选课程的目标班级，在出现空位时尝试选课。
- 升级课程支持设置多个备选班级，任一班级出现空位即可尝试升级。

## Windows 直接使用

从 [Releases](https://github.com/Weishi-corroding/CourseSelect/releases) 下载 `CourseSelect-*-windows-x64.exe`，双击启动即可。

首次使用前，依次完成：

1. 在当前账号下添加选课人。
2. 更新该选课人的 Cookie。
3. 在“课程查询”中获取课程数据。
4. 查询课程并加入待选计划，再按需启动选课或捡漏监控。

## 从源码运行

需要 Python 3.10 或更高版本。

```bash
git clone https://github.com/Weishi-corroding/CourseSelect.git
cd CourseSelect
python -m pip install -r requirements.txt
python main.py
```

课程数据也可以单独抓取：

```bash
python course_fetcher.py
```

## 课程查询

课程查询页会读取 `courses_full.json`。可直接在界面内点击获取课程，或运行 `course_fetcher.py` 生成数据文件。

支持松江与延安路校区筛选。地点识别覆盖松江、大学生体育中心、刘翔体育场、学院楼、图文信息大楼、化工楼、复材大楼、综合实验楼、工程训练中心，以及延安路、1—4 教、逸夫楼、中南楼、中北楼、旭日楼、管理楼和 IECB 等地点。

勾选“跳过礼貌等待”后，课程抓取会连续请求课程详情；默认模式会在请求之间保留短暂等待。

## 本地数据文件

以下文件运行时自动创建，已被 Git 忽略，不会提交到仓库：

| 文件 | 作用 |
| --- | --- |
| `accounts.json` | 选课人账号信息 |
| `cookies.json` | Cookie 缓存 |
| `courses.json` | 各选课人的待选课程班级 |
| `delete_courses.json` | 各选课人的待删除课程班级 |
| `courses_full.json` | 课程查询和监控使用的课程与课表数据 |
| `settings.json` | 本地界面与运行设置 |

## 核心文件

| 文件 | 作用 |
| --- | --- |
| `main.py` | 应用入口与异常日志初始化 |
| `main_window.py` | 主窗口、账号、课程计划和选课任务界面 |
| `course_query_window.py` | 课程查询界面、筛选与数据获取流程 |
| `course_fetcher.py` | 课程和课表数据抓取脚本 |
| `course_service.py` | 登录、选课、退课和本地数据服务 |
| `course_table_model.py` | 高性能课程表格模型 |
| `ui_components.py` | 可中断线程、日志视图与共享界面组件 |

## 开发验证

```bash
python -m unittest discover -s tests -q
```

## 许可证

本项目未附带许可证文件。使用者应自行遵守学校选课系统的规则与要求。
