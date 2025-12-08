# -*- coding: utf-8 -*-
"""核心功能模块 - 登录、选课逻辑"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.edge.options import Options
import subprocess
import json
from config import LOGIN_URL, COURSE_SUBMIT_URL, FILES


def get_cookies(name, password, report_callback=None, headless=True):
    """通过 Selenium 登录并获取 Cookies

    report_callback: 可选回调函数，用于在 GUI 中显示进度，例如 `self.status_box.append`。
    headless: 是否以无头模式启动浏览器（默认 True）。
    """
    def _report(msg):
        try:
            if report_callback:
                report_callback(msg)
        except Exception:
            # 报告失败时不要阻塞流程
            pass

    edge_options = Options()
    if headless:
        edge_options.add_argument("--headless")
    edge_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Edge(options=edge_options)

    try:
        _report(f"正在打开登录页面: {LOGIN_URL}")
        driver.get(LOGIN_URL)
        username_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "input"))
        )
        username_box.send_keys(name)
        _report(f"用户名输入成功: {name}")

        password_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//input[@type="password"]'))
        )
        password_box.send_keys(password)
        _report("密码输入成功")

        login_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//button[@title="登录"]'))
        )
        login_button.click()
        _report("点击登录按钮，等待登录完成...")

        # 等待登录完成
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, "//li[text()='个人信息查看']"))
        )
        _report("登录成功")

        cookies = driver.get_cookies()
        _report(f"共获取到 {len(cookies)} 个 cookie")
        return cookies
    finally:
        try:
            driver.quit()
        except Exception:
            pass


def sccourse(cookies, courseid):
    """通过 curl 提交课程选择请求"""
    curl_cmd = [
        "curl",
        COURSE_SUBMIT_URL,
        "-H", "Accept: application/json, text/javascript, */*; q=0.01",
        "-H", "Accept-Language: zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "-H", "Connection: keep-alive",
        "-H", "Content-Type: application/x-www-form-urlencoded;charset=UTF-8",
        "-b", cookies,
        "-H", "Origin: https://jwgl.dhu.edu.cn",
        "-H", "Referer: https://jwgl.dhu.edu.cn/dhu/selectcourse/toSCC",
        "-H", "Sec-Fetch-Dest: empty",
        "-H", "Sec-Fetch-Mode: cors",
        "-H", "Sec-Fetch-Site: same-origin",
        "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36 Edg/140.0.0.0",
        "-H", "X-Requested-With: XMLHttpRequest",
        "-H", r'sec-ch-ua: "Chromium";v="140", "Not=A?Brand";v="24", "Microsoft Edge";v="140"',
        "-H", "sec-ch-ua-mobile: ?0",
        "-H", 'sec-ch-ua-platform: "Windows"',
        "--data-raw", f"cttId={courseid}&needMaterial=false"
    ]
    try:
        # 设置一个合理的超时，避免在无法访问校园网时长时间阻塞
        creationflags = 0
        # 在 Windows 上避免弹出命令行窗口
        if hasattr(subprocess, 'CREATE_NO_WINDOW'):
            creationflags = subprocess.CREATE_NO_WINDOW

        result = subprocess.run(
            curl_cmd,
            capture_output=True,
            text=True,
            check=True,
            encoding="utf-8",
            timeout=8,
            creationflags=creationflags,
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        # 返回 stderr/ stdout 供上层记录，但不抛出异常
        err = e.stderr or e.stdout or str(e)
        return f"CALL_ERROR: {err}"
    except subprocess.TimeoutExpired as e:
        return f"TIMEOUT: {e}"
    except Exception as e:
        return f"EXCEPTION: {e}"


def load_accounts():
    """加载账户列表"""
    try:
        with open(FILES["accounts"], "r", encoding="utf-8") as f:
            return json.load(f).get("accounts", [])
    except FileNotFoundError:
        return []


def save_accounts(accounts):
    """保存账户列表"""
    with open(FILES["accounts"], "w", encoding="utf-8") as f:
        json.dump({"accounts": accounts}, f, ensure_ascii=False, indent=4)


def load_courses():
    """加载课程列表"""
    try:
        with open(FILES["courses"], "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def save_courses(courses):
    """保存课程列表"""
    with open(FILES["courses"], "w", encoding="utf-8") as f:
        json.dump(courses, f, ensure_ascii=False, indent=4)


def load_cookies_dict():
    """加载 Cookies 字典"""
    try:
        with open(FILES["cookies"], "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def save_cookies_dict(cookies_dict):
    """保存 Cookies 字典"""
    with open(FILES["cookies"], "w", encoding="utf-8") as f:
        json.dump(cookies_dict, f, ensure_ascii=False, indent=4)
