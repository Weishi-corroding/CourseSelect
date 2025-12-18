# -*- coding: utf-8 -*-
"""核心功能模块 - 登录、选课逻辑"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.edge.options import Options
import subprocess
import json
import os
import time
from config import LOGIN_URL, COURSE_SUBMIT_URL, FILES


def get_cookies(name, password, report_callback=None, debug_mode=False):
    """通过 Selenium 登录并获取 Cookies

    report_callback: 可选回调函数，用于在 GUI 中显示进度，例如 `self.status_box.append`。
    debug_mode: 调试模式，显示更详细的日志（默认 False）。
    """
    def _report(msg):
        try:
            if report_callback:
                report_callback(msg)
        except Exception:
            # 报告失败时不要阻塞流程
            pass

    edge_options = Options()
    
    # 始终显示浏览器窗口（不使用无头模式）
    edge_options.add_argument("--disable-dev-shm-usage")
    edge_options.add_argument("--no-sandbox")
    edge_options.add_argument("--disable-gpu")
    edge_options.add_argument("--disable-extensions")
    edge_options.add_argument("--disable-plugins")
    edge_options.add_argument("--start-maximized")
    
    # 使用本目录中的 msedgedriver
    driver_path = os.path.join(os.path.dirname(__file__), "msedgedriver.exe")
    driver = None

    try:
        _report(f"正在初始化浏览器驱动...")
        
        service = webdriver.EdgeService(driver_path, verbose=debug_mode)
        driver = webdriver.Edge(service=service, options=edge_options)
        
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

        # 等待登录完成 - 改为等待 URL 变化（更可靠）
        # 登录成功后应该从 casLogin 页面跳转到其他页面
        import time
        wait_time = 0
        max_wait = 30
        login_url = driver.current_url
        
        while wait_time < max_wait:
            try:
                current_url = driver.current_url
                if "casLogin" not in current_url:
                    _report(f"URL 已变更，登录成功: {current_url}")
                    time.sleep(2)  # 给页面加载时间
                    break
                time.sleep(0.5)
                wait_time += 0.5
            except Exception as e:
                _report(f"检查 URL 时出错: {e}")
                time.sleep(0.5)
                wait_time += 0.5
        
        if wait_time >= max_wait:
            _report("⚠️  等待登录超时，但继续尝试获取 cookies...")
        
        _report("登录成功")

        try:
            _report("正在获取 cookies...")
            cookies = driver.get_cookies()
            _report(f"共获取到 {len(cookies)} 个 cookie")
            
            if debug_mode:
                for c in cookies:
                    _report(f"  Cookie: {c['name']} = {c['value'][:50]}...")
            
            _report(f"Cookie 获取完成，准备返回...")
            return cookies
            
        except Exception as cookie_error:
            _report(f"❌ 在获取 cookies 时出错: {cookie_error}")
            import traceback
            _report(f"错误堆栈: {traceback.format_exc()}")
            raise
            
    except Exception as e:
        error_msg = str(e)
        _report(f"浏览器驱动异常: {error_msg}")
        if "Symbols not available" in error_msg:
            _report("⚠️  驱动符号错误。请检查：")
            _report("  1. msedgedriver 版本是否与 Edge 匹配")
            _report("  2. Edge 浏览器是否需要更新")
        import traceback
        _report(f"完整错误信息: {traceback.format_exc()}")
        raise
    finally:
        try:
            if driver:
                _report("正在关闭浏览器...")
                driver.quit()
                _report("浏览器已关闭")
        except Exception as quit_error:
            _report(f"关闭浏览器时出错: {quit_error}")

# 假设基础 URL 如下，请根据实际情况调整或使用全局变量
COURSE_CANCEL_URL = "https://jwgl.dhu.edu.cn/dhu/selectcourse/cancelSC"

def cancelSC(cookies, courseCode, classNo):
    """通过 curl 提交退选课程请求"""
    # 构造请求体数据，cancelType 固定为 1
    post_data = f"courseCode={courseCode}&classNo={classNo}&cancelType=1"
    
    curl_cmd = [
        "curl",
        COURSE_CANCEL_URL,
        "-H", "Accept: application/json, text/javascript, */*; q=0.01",
        "-H", "Accept-Language: zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "-H", "Connection: keep-alive",
        "-H", "Content-Type: application/x-www-form-urlencoded;charset=UTF-8",
        "-b", cookies,
        "-H", "Origin: https://jwgl.dhu.edu.cn",
        # 退选的 Referer 通常和选课一致，或者指向选课主页
        "-H", "Referer: https://jwgl.dhu.edu.cn/dhu/selectcourse/toSCC",
        "-H", "Sec-Fetch-Dest: empty",
        "-H", "Sec-Fetch-Mode: cors",
        "-H", "Sec-Fetch-Site: same-origin",
        "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36 Edg/140.0.0.0",
        "-H", "X-Requested-With: XMLHttpRequest",
        "-H", r'sec-ch-ua: "Chromium";v="140", "Not=A?Brand";v="24", "Microsoft Edge";v="140"',
        "-H", "sec-ch-ua-mobile: ?0",
        "-H", 'sec-ch-ua-platform: "Windows"',
        "--data-raw", post_data
    ]

    try:
        creationflags = 0
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
        err = e.stderr or e.stdout or str(e)
        return f"CALL_ERROR: {err}"
    except subprocess.TimeoutExpired as e:
        return f"TIMEOUT: {e}"
    except Exception as e:
        return f"EXCEPTION: {e}"

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


def load_delete_courses():
    """加载待删除课程列表"""
    try:
        with open(FILES["delete_courses"], "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def save_delete_courses(delete_courses):
    """保存待删除课程列表"""
    with open(FILES["delete_courses"], "w", encoding="utf-8") as f:
        json.dump(delete_courses, f, ensure_ascii=False, indent=4)
