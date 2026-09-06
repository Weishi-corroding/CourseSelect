# -*- coding: utf-8 -*-
"""核心功能模块 - 登录、选课逻辑 - 纯 HTTP + RSA 版"""

import sys
import os
import re
import time
import json
import base64
import textwrap
import subprocess
import traceback
import urllib.request
import urllib.parse

import requests
import threading
from requests.adapters import HTTPAdapter

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

_thread_local = threading.local()

def cleanup_thread_session():
    """显式关闭当前线程的 session，释放连接池资源"""
    if hasattr(_thread_local, 'session'):
        try:
            _thread_local.session.close()
        except Exception:
            pass
        try:
            del _thread_local.session
        except Exception:
            pass

def _get_session():
    """返回线程本地的 requests.Session（连接池 + 静态请求头）"""
    try:
        return _thread_local.session
    except AttributeError:
        session = requests.Session()
        session.headers.update({
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
            "Connection": "keep-alive",
            "Origin": "https://jwgl.dhu.edu.cn",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0",
            "X-Requested-With": "XMLHttpRequest",
            "sec-ch-ua": '"Microsoft Edge";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
        })
        adapter = HTTPAdapter(pool_connections=10, pool_maxsize=20)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        _thread_local.session = session
        return session

def _requests_post(url, data, cookies, headers_extra=None, timeout=15):
    """requests.post 的统一封装（连接池版），返回响应文本"""
    session = _get_session()
    # 每次请求特有的头部：Cookie（每个worker固定）、Referer（由调用方通过 headers_extra 传入）
    headers = {"Cookie": cookies}
    if headers_extra:
        headers.update(headers_extra)
    try:
        resp = session.post(url, data=data, headers=headers, timeout=timeout)
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
    post_data = urllib.parse.urlencode({"courseCode": course_code})
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
        "&bSortable_8=false&bSortable_9=false&"
        + urllib.parse.urlencode({"courseCode": course_code})
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

_CAS_BASE = "https://cas.dhu.edu.cn/esc-sso"
_JWGL_LOGIN = "https://jwgl.dhu.edu.cn/dhu/casLogin"
_LOGIN_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0"
)


def _build_pem(pub_key_b64):
    """把 CAS 返回的单行 base64 公钥包成 PEM。漏一个换行 load_pem_public_key 就会抛 ValueError。"""
    body = "\n".join(textwrap.wrap(pub_key_b64, 64))
    return f"-----BEGIN PUBLIC KEY-----\n{body}\n-----END PUBLIC KEY-----\n"


def _rsa_encrypt_password(pub_key_b64, password):
    """对齐 DLSF: node-forge 的 RSAES-PKCS1-V1_5 == cryptography 的 PKCS1v15。"""
    # Only login needs RSA; opening the workspace should not initialize it.
    from cryptography.hazmat.primitives.asymmetric import padding as _rsa_padding
    from cryptography.hazmat.primitives.serialization import load_pem_public_key
    pub = load_pem_public_key(_build_pem(pub_key_b64).encode("utf-8"))
    encrypted = pub.encrypt(password.encode("utf-8"), _rsa_padding.PKCS1v15())
    return base64.b64encode(encrypted).decode("ascii")


def _extract_jwgl_cookies(response):
    """
    从 ticket 跳转响应里抠 JSESSIONID 和 newjwgl。
    优先用 response.cookies（urllib3 已分桶），缺了再降级到 raw Set-Cookie 头正则。
    """
    js = response.cookies.get("JSESSIONID")
    nj = response.cookies.get("newjwgl")
    if js and nj:
        return js, nj

    raw_headers = []
    try:
        # urllib3.HTTPHeaderDict.getlist 不会把多个 Set-Cookie 合并
        raw_headers = response.raw.headers.getlist("Set-Cookie")
    except Exception:
        merged = response.headers.get("Set-Cookie") or ""
        if merged:
            raw_headers = [merged]

    for line in raw_headers:
        if js is None:
            m = re.search(r"JSESSIONID=([^;]+)", line)
            if m:
                js = m.group(1)
        if nj is None:
            m = re.search(r"newjwgl=([^;]+)", line)
            if m:
                nj = m.group(1)
    return js, nj


def get_cookies(name, password, report_callback=None, browser_type=None):
    """
    通过 CAS HTTP API + RSA 加密获取教务系统 Session（替代 Selenium 浏览器登录）。

    流程对齐 DLSF (app.js loginGetToken)：
      1) GET  /esc-sso/authn/policy           → 拿 RSA 公钥 + publicKeyId
      2) PKCS1v15 加密密码
      3) POST /esc-sso/authn/login            → 拿 CAS 域 Cookie
      4) GET  /esc-sso/login?service=jwgl/... → 期望 302，从 Location 拿 ticket URL
      5) GET  ticket URL                      → 从 Set-Cookie 抠 JSESSIONID + newjwgl

    参数:
        name         CAS 用户名（学号）
        password     明文密码
        report_callback(msg)  可选，UI 日志回调
        browser_type 已废弃，仅为兼容旧调用保留

    返回:
        [{"name":"JSESSIONID","value":"..."}, {"name":"newjwgl","value":"..."}]

    失败时抛 RuntimeError，外层 update_cookie_dialog 已有 try/except 兜底。
    """
    def _report(msg):
        _log_to_file(msg)
        try:
            if report_callback:
                report_callback(msg)
        except Exception:
            pass

    _report(f"--- 开始 CAS 登录: {name} ---")

    sess = requests.Session()
    sess.headers.update({
        "User-Agent": _LOGIN_UA,
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    })

    try:
        # ── Step 1: 取 RSA 公钥 ──
        ts = int(time.time() * 1000)
        _report("CAS Step 1/5: 获取登录策略 (RSA 公钥)")
        r = sess.get(f"{_CAS_BASE}/authn/policy",
                     params={"_": ts, "app": "gateway"}, timeout=15)
        try:
            policy = r.json()
            pub_key_b64 = policy["data"]["param"]["publicKey"]
            pub_key_id = policy["data"]["param"]["publicKeyId"]
        except Exception:
            raise RuntimeError(f"获取登录策略失败 (HTTP {r.status_code}): {r.text[:200]}")

        # ── Step 2: RSA 加密密码 ──
        _report("CAS Step 2/5: RSA 加密密码")
        encrypted = _rsa_encrypt_password(pub_key_b64, password)

        # ── Step 3: 提交登录，拿 CAS 域 Cookie 写进 session ──
        _report("CAS Step 3/5: 提交登录请求")
        ts = int(time.time() * 1000)
        login_resp = sess.post(
            f"{_CAS_BASE}/authn/login",
            params={"_": ts},
            json={
                "authType": "webLocalAuth",
                "dataField": {
                    "username": name,
                    "password": encrypted,
                    "publicKeyId": pub_key_id,
                },
                "extendField": {"app": "gateway"},
            },
            timeout=15,
        )
        try:
            result = login_resp.json()
        except Exception:
            raise RuntimeError(f"登录响应非 JSON: {login_resp.text[:200]}")

        if result.get("code") == "IAM031006":
            raise RuntimeError("用户名或密码错误")
        if not result.get("success", True) and result.get("code"):
            # CAS 还会用各种 code 表示其它失败（被锁定/需要二次认证等）
            msg = result.get("message") or result.get("msg") or result.get("code")
            raise RuntimeError(f"CAS 登录失败: {msg}")

        # ── Step 4: 触发 service 跳转，拿 ticket ──
        _report("CAS Step 4/5: 申请教务系统 Ticket")
        r1 = sess.get(f"{_CAS_BASE}/login",
                      params={"service": _JWGL_LOGIN},
                      allow_redirects=False, timeout=15)
        ticket_url = r1.headers.get("Location")
        if not ticket_url:
            # 如果 CAS 没下发 ticket，多半是触发了二次认证（企业微信/手机短信验证码）
            raise RuntimeError(
                "未获取到 Ticket。该账号可能需要企业微信/短信验证码，"
                "请先到教务系统手动登录一次后再试。"
            )

        # ── Step 5: 跟着 ticket URL 走，从 Set-Cookie 抠 JSESSIONID + newjwgl ──
        _report("CAS Step 5/5: 兑换 JSESSIONID")
        r2 = sess.get(ticket_url, allow_redirects=False, timeout=15)
        js, nj = _extract_jwgl_cookies(r2)

        if not js or not nj:
            raise RuntimeError(
                f"未能解析教务系统 Cookie (HTTP {r2.status_code})。"
                f"JSESSIONID={'有' if js else '无'}, newjwgl={'有' if nj else '无'}"
            )

        _report(f"✅ 登录成功: JSESSIONID={js[:8]}..., newjwgl={nj}")
        return [
            {"name": "JSESSIONID", "value": js},
            {"name": "newjwgl", "value": nj},
        ]

    except requests.exceptions.Timeout:
        raise RuntimeError("CAS 登录超时，请检查网络")
    except RuntimeError:
        raise
    except Exception as e:
        _report(f"❌ 登录异常:\n{traceback.format_exc()}")
        raise RuntimeError(f"CAS 登录异常: {e}")
    finally:
        try:
            sess.close()
        except Exception:
            pass
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
    post_data = urllib.parse.urlencode({
        "courseCode": courseCode,
        "classNo": classNo,
        "cancelType": "2",
    })
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
    data = {"cttId": courseid, "needMaterial": "false"}
    if cap_code:
        data["capCode"] = cap_code
    post_data = urllib.parse.urlencode(data)
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
