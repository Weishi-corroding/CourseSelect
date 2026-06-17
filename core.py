# -*- coding: utf-8 -*-
"""核心功能模块 - 登录、选课逻辑 - Chrome Portable / Edge 版"""

import sys
import os
import time
import json
import subprocess
import traceback
import urllib.request
import urllib.parse

import requests

# Selenium imports
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.chrome.options import Options as ChromeOptions
# 引入 Service 用于指定 chromedriver 路径
from selenium.webdriver.chrome.service import Service as ChromeService

if sys.stdin is None:
    try:
        sys.stdin = open(os.devnull, 'r')
    except Exception:
        pass

FILES = {
    "accounts": "accounts.json",
    "courses": "courses.json",
    "cookies": "cookies.json",
    "delete_courses": "delete_courses.json",
}
LOG_FILE = "CoureseSelectDebug.log"

LOGIN_URL = "https://jwgl.dhu.edu.cn/dhu/casLogin"
# ... (保留 core.py 前面的所有代码) ...

def _requests_post(url, data, cookies, headers_extra=None, timeout=15):
    """requests.post 的统一封装，返回响应文本"""
    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
        "Origin": "https://jwgl.dhu.edu.cn",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0",
        "X-Requested-With": "XMLHttpRequest",
        "sec-ch-ua": '"Microsoft Edge";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "Cookie": cookies,
    }
    if headers_extra:
        headers.update(headers_extra)
    try:
        resp = requests.post(url, data=data, headers=headers, timeout=timeout)
        return resp.text
    except requests.exceptions.Timeout:
        return "TIMEOUT"
    except Exception:
        return ""

def access_judge(cookies, course_code):
    """
    [模拟手工操作步骤1] 访问权限检查
    """
    url = "https://jwgl.dhu.edu.cn/dhu/selectcourse/accessJudge"
    post_data = f"courseCode={course_code}"
    extra = {"Referer": "https://jwgl.dhu.edu.cn/dhu/selectcourse/toSCC"}
    return _requests_post(url, post_data, cookies, headers_extra=extra, timeout=10)

def query_course_info(cookies, course_code):
    """
    [模拟手工操作步骤2] 获取班级列表 (initACC)
    参数完全复刻 DataTables 的请求格式
    """
    target_url = "https://jwgl.dhu.edu.cn/dhu/selectcourse/initACC"
    
    # 构造 DataTables 所需的巨大参数串 (直接复制你提供的 curl data)
    post_data = (
        "sEcho=1&iColumns=10&sColumns=&iDisplayStart=0&iDisplayLength=-1"
        "&mDataProp_0=cttId&mDataProp_1=classNo&mDataProp_2=maxCnt"
        "&mDataProp_3=applyCnt&mDataProp_4=enrollCnt&mDataProp_5=priorMajors"
        "&mDataProp_6=techName&mDataProp_7=cttId&mDataProp_8=cttId&mDataProp_9=cttId"
        "&iSortCol_0=0&sSortDir_0=asc&iSortingCols=1"
        "&bSortable_0=false&bSortable_1=false&bSortable_2=false&bSortable_3=false"
        "&bSortable_4=false&bSortable_5=false&bSortable_6=false&bSortable_7=false"
        "&bSortable_8=false&bSortable_9=false"
        f"&courseCode={course_code}"
    )

    curl_cmd = [
        "curl", target_url,
        "-H", "Accept: application/json, text/javascript, */*; q=0.01",
        "-H", "Accept-Language: zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "-H", "Connection: keep-alive",
        "-H", "Content-Type: application/x-www-form-urlencoded;charset=UTF-8",
        "-H", "Origin: https://jwgl.dhu.edu.cn",
        "-H", "Referer: https://jwgl.dhu.edu.cn/dhu/selectcourse/toSCC",
        "-H", "Sec-Fetch-Dest: empty",
        "-H", "Sec-Fetch-Mode: cors",
        "-H", "Sec-Fetch-Site: same-origin",
        "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0",
        "-H", "X-Requested-With: XMLHttpRequest",
        "-H", 'sec-ch-ua: "Microsoft Edge";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
        "-H", "sec-ch-ua-mobile: ?0",
        "-H", 'sec-ch-ua-platform: "Windows"',
        "-H", f"Cookie: {cookies}",
        "--data-raw", post_data,
        "--compressed", "-s", "--max-time", "10"
    ]
def query_course_info(cookies, course_code):
    """
    [模拟手工操作步骤2] 获取班级列表 (initACC)
    """
    url = "https://jwgl.dhu.edu.cn/dhu/selectcourse/initACC"
    post_data = (
        "sEcho=1&iColumns=10&sColumns=&iDisplayStart=0&iDisplayLength=-1"
        "&mDataProp_0=cttId&mDataProp_1=classNo&mDataProp_2=maxCnt"
        "&mDataProp_3=applyCnt&mDataProp_4=enrollCnt&mDataProp_5=priorMajors"
        "&mDataProp_6=techName&mDataProp_7=cttId&mDataProp_8=cttId&mDataProp_9=cttId"
        "&iSortCol_0=0&sSortDir_0=asc&iSortingCols=1"
        "&bSortable_0=false&bSortable_1=false&bSortable_2=false&bSortable_3=false"
        "&bSortable_4=false&bSortable_5=false&bSortable_6=false&bSortable_7=false"
        "&bSortable_8=false&bSortable_9=false"
        f"&courseCode={course_code}"
    )
    extra = {"Referer": "https://jwgl.dhu.edu.cn/dhu/selectcourse/toSCC"}
    return _requests_post(url, post_data, cookies, headers_extra=extra, timeout=10)

def _log_to_file(msg):
    try:
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
        
        log_path = os.path.join(base_path, LOG_FILE)
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] [CORE] {msg}\n")
    except:
        pass

def get_cookies(name, password, report_callback=None, browser_type="edge"):
    def _report(msg):
        _log_to_file(msg)
        try:
            if report_callback:
                report_callback(msg)
        except Exception:
            pass

    # 获取当前程序所在的基础目录
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))

    _report(f"--- 开始任务 ({browser_type}): {name} ---")
    
    driver = None
    try:
        if browser_type == "chrome":
            # ========================================================
            # Chrome Portable 路径配置
            # ========================================================
            chrome_folder = os.path.join(base_path, "chrome")
            chrome_bin_path = os.path.join(chrome_folder, "chrome", "chrome.exe")
            chromedriver_path = os.path.join(chrome_folder, "chrome", "chromedriver.exe")

            # 检查文件是否存在，方便调试
            if not os.path.exists(chrome_bin_path):
                _report(f"❌ 错误: 找不到 Chrome 主程序: {chrome_bin_path}")
                return []
            if not os.path.exists(chromedriver_path):
                _report(f"❌ 错误: 找不到 ChromeDriver: {chromedriver_path}")
                return []

            _report(f"使用本地 Chrome: {chrome_bin_path}")

            chrome_options = ChromeOptions()
            # 【重要】指定 Chrome 二进制文件位置
            chrome_options.binary_location = chrome_bin_path

            chrome_options.add_argument("--start-maximized")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            # 注意: excludeSwitches 会导致 Chrome 149+ 崩溃，已移除
            
            # 【重要】使用 Service 指定 chromedriver.exe 路径
            service = ChromeService(executable_path=chromedriver_path)
            
            # 隐藏 chromedriver 的黑色控制台窗口 (Windows专用)
            if hasattr(subprocess, 'CREATE_NO_WINDOW'):
                service.creation_flags = subprocess.CREATE_NO_WINDOW
            
            _report("正在启动 Chrome Portable WebDriver...")
            driver = webdriver.Chrome(service=service, options=chrome_options)
            _report("✅ Chrome Portable 启动成功！")
            
        else:
            # --- Edge 配置 (使用系统安装的 Edge) ---
            edge_options = EdgeOptions()
            edge_options.add_argument("--start-maximized")
            edge_options.add_argument("--disable-blink-features=AutomationControlled")
            # 注意: excludeSwitches 会导致 Edge 149+ 崩溃，已移除

            _report("正在启动 Edge WebDriver...")
            driver = webdriver.Edge(options=edge_options)
            _report("✅ Edge 启动成功！")
        
        _report(f"打开登录页: {LOGIN_URL}")
        # 跟随重定向到 CAS 统一认证页面 (cas.dhu.edu.cn)
        driver.get(LOGIN_URL)

        # 等待 CAS 页面 JS 渲染完成后再操作表单
        time.sleep(2)

        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text']"))).send_keys(name)
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='password']"))).send_keys(password)
        WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "登录")]'))).click()
        
        _report("登录提交，等待 JSESSIONID...")

        found_target_cookies = False
        wait_time = 0
        max_wait = 30
        target_cookies = []

        while wait_time < max_wait:
            current_cookies = driver.get_cookies()
            cookie_names = [c['name'] for c in current_cookies]
            
            if "JSESSIONID" in cookie_names or "newjwgl" in cookie_names:
                _report("✅ 成功捕获教务系统 Session！")
                target_cookies = current_cookies
                found_target_cookies = True
                break
            
            if "casLogin" in driver.current_url and wait_time > 5:
                try:
                    if driver.find_elements(By.CLASS_NAME, "el-form-item__error"):
                        _report(f"⚠️ 页面出现错误提示")
                except: pass

            time.sleep(1)
            wait_time += 1

        if not found_target_cookies:
            _report("❌ 获取 Cookie 超时。")
            return driver.get_cookies()

        return target_cookies

    except Exception as e:
        error_msg = traceback.format_exc()
        _report(f"❌ 核心异常:\n{error_msg}")
        if "SessionNotCreatedException" in str(e):
            _report(f"⚠️ 错误: 浏览器驱动版本不匹配 ({browser_type})！请检查 chrome/ 目录下的版本。")
        raise e
    finally:
        if driver:
            try: driver.quit()
            except: pass
        _report("--- 流程结束 ---")

def cancelSC(cookies, courseCode, classNo):
    target_url = "https://jwgl.dhu.edu.cn/dhu/selectcourse/cancelSC"
    post_data = f"courseCode={courseCode}&classNo={classNo}&cancelType=2"
    curl_cmd = [
        "curl", target_url,
        "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0",
        "-H", 'sec-ch-ua: "Microsoft Edge";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
        "-H", "sec-ch-ua-mobile: ?0",
        "-H", 'sec-ch-ua-platform: "Windows"',
        "-H", "Accept-Language: zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "-H", "Accept: application/json, text/javascript, */*; q=0.01",
        "-H", "Accept-Encoding: gzip, deflate, br, zstd",
        "-H", "Content-Type: application/x-www-form-urlencoded;charset=UTF-8",
        "-H", "X-Requested-With: XMLHttpRequest",
        "-H", "Origin: https://jwgl.dhu.edu.cn",
        "-H", "Referer: https://jwgl.dhu.edu.cn/dhu/selectcourse/toSSC",
        "-H", "Sec-Fetch-Dest: empty",
        "-H", "Sec-Fetch-Mode: cors",
        "-H", "Sec-Fetch-Site: same-origin",
        "-H", "Connection: keep-alive",
        "-H", f"Cookie: {cookies}",
        "--data-raw", post_data,
        "--compressed", "-s", "--max-time", "60"
    ]
    try:
        creationflags = 0
        if hasattr(subprocess, 'CREATE_NO_WINDOW'):
            creationflags = subprocess.CREATE_NO_WINDOW
        result = subprocess.run(curl_cmd, capture_output=True, text=True, encoding="utf-8", timeout=65, creationflags=creationflags, stdin=subprocess.DEVNULL)
        if result.returncode != 0: return f"CURL ERROR: {result.stderr}"
        return result.stdout
    except subprocess.TimeoutExpired: return "TIMEOUT"
    except Exception as e: return f"EXCEPTION: {e}"
def cancelSC(cookies, courseCode, classNo):
    url = "https://jwgl.dhu.edu.cn/dhu/selectcourse/cancelSC"
    post_data = f"courseCode={courseCode}&classNo={classNo}&cancelType=2"
    extra = {"Referer": "https://jwgl.dhu.edu.cn/dhu/selectcourse/toSSC"}
    result = _requests_post(url, post_data, cookies, headers_extra=extra, timeout=60)
    if result == "TIMEOUT":
        return "TIMEOUT"
    if not result:
        return "CURL ERROR: empty response"
    return result

def sccourse(cookies, courseid):
    target_url = "https://jwgl.dhu.edu.cn/dhu/selectcourse/scSubmit"
    post_data = f"cttId={courseid}&needMaterial=false"
    curl_cmd = [
        "curl", target_url,
        "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0",
        "-H", 'sec-ch-ua: "Microsoft Edge";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
        "-H", "sec-ch-ua-mobile: ?0",
        "-H", 'sec-ch-ua-platform: "Windows"',
        "-H", "Origin: https://jwgl.dhu.edu.cn",
        "-H", "Referer: https://jwgl.dhu.edu.cn/dhu/selectcourse/toSCC",
        "-H", "X-Requested-With: XMLHttpRequest",
        "-H", "Sec-Fetch-Dest: empty",
        "-H", "Sec-Fetch-Mode: cors",
        "-H", "Sec-Fetch-Site: same-origin",
        "-H", "Content-Type: application/x-www-form-urlencoded;charset=UTF-8",
        "-H", "Accept: application/json, text/javascript, */*; q=0.01",
        "-H", "Accept-Encoding: gzip, deflate, br, zstd",
        "-H", "Accept-Language: zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "-H", "Connection: keep-alive",
        "-H", f"Cookie: {cookies}",
        "--data-raw", post_data,
        "--compressed", "-s", "--max-time", "60"
    ]
    try:
        creationflags = 0
        if hasattr(subprocess, 'CREATE_NO_WINDOW'):
            creationflags = subprocess.CREATE_NO_WINDOW
        result = subprocess.run(curl_cmd, capture_output=True, text=True, encoding="utf-8", timeout=65, creationflags=creationflags, stdin=subprocess.DEVNULL)
        if result.returncode != 0: return f"CURL ERROR: {result.stderr}"
        return result.stdout
    except subprocess.TimeoutExpired: return "TIMEOUT"
    except Exception as e: return f"EXCEPTION: {e}"
def sccourse(cookies, courseid, cap_code=""):
    url = "https://jwgl.dhu.edu.cn/dhu/selectcourse/scSubmit"
    post_data = f"cttId={courseid}&needMaterial=false"
    if cap_code:
        post_data += f"&capCode={cap_code}"
    extra = {"Referer": "https://jwgl.dhu.edu.cn/dhu/selectcourse/toSCC"}
    result = _requests_post(url, post_data, cookies, headers_extra=extra, timeout=60)
    if result == "TIMEOUT":
        return "TIMEOUT"
    if not result:
        return "CURL ERROR: empty response"
    return result

def load_accounts():
    try:
        with open(FILES["accounts"], "r", encoding="utf-8") as f: return json.load(f).get("accounts", [])
    except: return []
def save_accounts(data):
    with open(FILES["accounts"], "w", encoding="utf-8") as f: json.dump({"accounts": data}, f, ensure_ascii=False, indent=4)
def load_courses():
    try:
        with open(FILES["courses"], "r", encoding="utf-8") as f: return json.load(f)
    except: return {}
def save_courses(data):
    with open(FILES["courses"], "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=4)
def load_cookies_dict():
    try:
        with open(FILES["cookies"], "r", encoding="utf-8") as f: return json.load(f)
    except: return {}
def save_cookies_dict(data):
    with open(FILES["cookies"], "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=4)
def load_delete_courses():
    try:
        with open(FILES["delete_courses"], "r", encoding="utf-8") as f: return json.load(f)
    except: return {}
def save_delete_courses(data):
    with open(FILES["delete_courses"], "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=4)

# === PushPlus 推送 ===
def send_push_notification(token, title, content):
    """发送 PushPlus 微信通知"""
    if not token: return
    url = "http://www.pushplus.plus/send"
    data = {"token": token, "title": title, "content": content, "template": "html"}
    try:
        json_data = json.dumps(data).encode('utf-8')
        req = urllib.request.Request(url, data=json_data, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req) as response:
            result = response.read().decode('utf-8')
            _log_to_file(f"PushPlus 响应: {result}")
    except Exception as e:
        _log_to_file(f"PushPlus 发送失败: {e}")