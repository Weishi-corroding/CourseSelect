# -*- coding: utf-8 -*-
"""
开课数据爬取脚本
从教务系统获取所有开课课程列表及各课程的开课详细信息，汇总保存为 JSON。

API:
  GET SELECT COURSE TERM LIST  →  获取学期开课列表 (所有课程基本信息)
  GET COURSE TIME TABLE INFO   →  获取某门课的具体开课信息 (班级、容量、教师、时间地点)

用法:
  python fetch_courses.py                         # 使用 cookies.json 中第一个有效用户的 cookie
  python fetch_courses.py --user "张三"            # 指定用户
  python fetch_courses.py --term 88               # 指定学期 ID (默认 88)
  python fetch_courses.py --limit 10              # 仅抓取前 N 门课 (测试用)
  python fetch_courses.py --output courses_full.json
"""

import sys
import os
import json
import time
import subprocess
import argparse
import re
import threading

import requests
from requests.adapters import HTTPAdapter
from bs4 import BeautifulSoup

# 复用 core 模块的路径 / 文件常量
FILES = {
    "accounts": "accounts.json",
    "courses": "courses.json",
    "cookies": "cookies.json",
}
LOG_FILE = "CoureseSelectDebug.log"


class SessionExpired(Exception):
    """Cookie 已失效：服务器把请求重定向到了 CAS 登录页 (/dhu/caslogin)。"""
    pass


def _check_session_expired(resp):
    """若 curl 响应体疑似为 CAS 登录跳转，抛 SessionExpired。

    教务系统在 Cookie 失效时通常返回 302→/dhu/caslogin 或者直接返回一段
    内嵌 meta-refresh / JS 跳转到 /dhu/caslogin 的 HTML。curl 不跟 -L
    时这段内容会直接进 stdout。
    """
    if not resp:
        return
    low = resp.lower()
    if "caslogin" in low or "/dhu/caslogin" in resp:
        raise SessionExpired("cookie expired - response redirected to /dhu/caslogin")


# ── HTTP 连接池（requests.Session，replace curl subprocess on the hot path）─
# 与 core._get_session 同样采用 thread-local 模式：每个调用线程持有自己的
# Session，HTTPAdapter 给同主机维持 keep-alive。fetch_course_timetable 在
# 全量抓取时循环上千次，复用单个 TLS 连接能省掉每次的握手开销。

_STATIC_HEADERS = {
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
    "Connection": "keep-alive",
    "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
    "Origin": "https://jwgl.dhu.edu.cn",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36 Edg/149.0.0.0",
    "X-Requested-With": "XMLHttpRequest",
    "sec-ch-ua": '"Microsoft Edge";v="149", "Chromium";v="149", "Not)A;Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
}

_thread_local = threading.local()


def _get_session():
    """返回线程本地的 requests.Session（keep-alive 连接池 + 预置请求头）"""
    try:
        return _thread_local.session
    except AttributeError:
        s = requests.Session()
        s.headers.update(_STATIC_HEADERS)
        adapter = HTTPAdapter(pool_connections=4, pool_maxsize=8)
        s.mount("https://", adapter)
        s.mount("http://", adapter)
        _thread_local.session = s
        return s


def _http_post(url, body, cookies, *, timeout=35, referer=None):
    """POST 包装：通过线程本地 Session 发送，复用 keep-alive。

    Cookie 仅通过 header 注入（与原 curl `-H "Cookie: ..."` 行为一致），
    不传 cookies= 参数，避免 requests 把字符串误解析成 cookie jar。
    返回响应体字符串；超时/异常返回 ""（与 _run_curl 同语义）。
    """
    headers = {"Cookie": cookies}
    if referer:
        headers["Referer"] = referer
    try:
        resp = _get_session().post(url, data=body, headers=headers, timeout=timeout)
        return resp.text or ""
    except requests.Timeout:
        log("⚠️ HTTP 超时")
        return ""
    except Exception as e:
        log(f"⚠️ HTTP 异常: {e}")
        return ""



# ── 日志 ──────────────────────────────────────────────────────────
def log(msg):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    line = f"[{timestamp}] [FETCH] {msg}"
    # Windows 终端 GBK 兼容：尝试替换无法编码的字符
    try:
        print(line)
    except UnicodeEncodeError:
        safe = line.encode("ascii", errors="replace").decode("ascii")
        print(safe)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except:
        pass


# ── 文件 I/O（复用 core.py 风格）─────────────────────────────────
def load_accounts():
    try:
        with open(FILES["accounts"], "r", encoding="utf-8") as f:
            return json.load(f).get("accounts", [])
    except:
        return []


def load_cookies_dict():
    try:
        with open(FILES["cookies"], "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


def save_json(data, filepath):
    os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    log(f"✅ 数据已保存到: {filepath} ({len(data)} 条课程记录)")


# ── curl 辅助 ─────────────────────────────────────────────────────
def _run_curl(cmd, timeout=30):
    """执行 curl 命令并返回 stdout 字符串"""
    try:
        creationflags = 0
        if hasattr(subprocess, "CREATE_NO_WINDOW"):
            creationflags = subprocess.CREATE_NO_WINDOW
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=timeout,
            creationflags=creationflags,
            stdin=subprocess.DEVNULL,
        )
        if result.returncode != 0:
            log(f"⚠️ curl 返回码 {result.returncode}: {result.stderr[:200]}")
            return ""
        return result.stdout
    except subprocess.TimeoutExpired:
        log("⚠️ curl 超时")
        return ""
    except Exception as e:
        log(f"⚠️ curl 异常: {e}")
        return ""


def _common_headers(cookies):
    """构造与 core.py 一致的请求头列表"""
    return [
        "-H", "Accept: application/json, text/javascript, */*; q=0.01",
        "-H", "Accept-Language: zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "-H", "Connection: keep-alive",
        "-H", "Content-Type: application/x-www-form-urlencoded;charset=UTF-8",
        "-H", "Origin: https://jwgl.dhu.edu.cn",
        "-H", "Referer: https://jwgl.dhu.edu.cn/dhu/PublicQuery/toPage",
        "-H", "Sec-Fetch-Dest: empty",
        "-H", "Sec-Fetch-Mode: cors",
        "-H", "Sec-Fetch-Site: same-origin",
        "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36 Edg/149.0.0.0",
        "-H", "X-Requested-With: XMLHttpRequest",
        "-H", 'sec-ch-ua: "Microsoft Edge";v="149", "Chromium";v="149", "Not)A;Brand";v="24"',
        "-H", "sec-ch-ua-mobile: ?0",
        "-H", 'sec-ch-ua-platform: "Windows"',
        "-H", f"Cookie: {cookies}",
    ]


# ── API 1: 获取学期开课总列表 ─────────────────────────────────────
def _build_course_list_body(term_id, display_length):
    """构造 getSelectCourseTermList 的 DataTables POST body"""
    return (
        "sEcho=1&iColumns=6&sColumns="
        "&iDisplayStart=0"
        f"&iDisplayLength={display_length}"
        "&mDataProp_0=kcmc&mDataProp_1=kcbh&mDataProp_2=xf"
        "&mDataProp_3=jxdg_url&mDataProp_4=jxrl_url&mDataProp_5=orgname"
        "&iSortCol_0=0&sSortDir_0=asc&iSortingCols=1"
        "&bSortable_0=false&bSortable_1=false&bSortable_2=false"
        "&bSortable_3=false&bSortable_4=false&bSortable_5=false"
        f"&termId={term_id}&course="
    )


def fetch_course_list(cookies, term_id=88, display_length=None):
    """
    调用 getSelectCourseTermList 获取学期全部课程基本信息。
    返回 aaData 列表 (list[dict])。

    display_length:
        None (默认) → 先做一次 iDisplayLength=1 的探测调用拿到
                      iTotalRecords/iTotalDisplayRecords，再用真实总数
                      二次拉取，保证不会因为硬编码上限漏课。
        显式整数    → 直接按该值拉取（旧行为，CLI 测试可用 --limit 简化）。
    """
    url = "https://jwgl.dhu.edu.cn/dhu/PublicQuery/getSelectCourseTermList"

    log(f"📡 正在获取学期开课列表 (termId={term_id})...")

    # 自动发现总课程数
    if display_length is None:
        probe = _http_post(
            url, _build_course_list_body(term_id, 1), cookies, timeout=20,
            referer="https://jwgl.dhu.edu.cn/dhu/PublicQuery/toPage",
        )
        if not probe:
            log("❌ 探测调用未获取到响应")
            return []
        _check_session_expired(probe)
        try:
            probe_data = json.loads(probe)
        except json.JSONDecodeError:
            log(f"❌ 探测调用 JSON 解析失败，前 200 字符: {probe[:200]}")
            return []
        if not probe_data.get("success"):
            log(f"⚠️ 探测调用失败: {probe_data.get('msg', '未知错误')}")
            return []
        # DataTables 协议返回 iTotalRecords / iTotalDisplayRecords，本系统两者一致
        total = (
            probe_data.get("iTotalDisplayRecords")
            or probe_data.get("iTotalRecords")
            or 0
        )
        try:
            total = int(total)
        except (TypeError, ValueError):
            total = 0
        if total <= 0:
            log(f"⚠️ 探测调用未返回有效 iTotalRecords (got {total!r})，回退到 2000")
            total = 2000
        else:
            log(f"🔢 服务器报告本学期共 {total} 门课，按此数量拉取")
        display_length = total

    resp = _http_post(
        url, _build_course_list_body(term_id, display_length), cookies, timeout=35,
        referer="https://jwgl.dhu.edu.cn/dhu/PublicQuery/toPage",
    )

    if not resp:
        log("❌ 未获取到响应")
        return []

    # Cookie 失效检测：抛 SessionExpired 让调用方触发重登录
    _check_session_expired(resp)

    try:
        data = json.loads(resp)
    except json.JSONDecodeError:
        log(f"❌ JSON 解析失败，响应前 200 字符: {resp[:200]}")
        return []

    if not data.get("success"):
        log(f"⚠️ 接口返回失败: {data.get('msg', '未知错误')}")
        return []

    records = data.get("aaData", [])
    log(f"✅ 成功获取 {len(records)} 门课程 (服务器总记录: {data.get('iTotalDisplayRecords', '?')})")
    return records


# ── API 2: 获取单门课的开课详细信息 ───────────────────────────────
def fetch_course_timetable(cookies, kcbh, term_id=88):
    """
    调用 getCourseTimeTableInfo 获取某门课程的具体开课信息。
    返回解析后的 dict。
    """
    url = "https://jwgl.dhu.edu.cn/dhu/PublicQuery/getCourseTimeTableInfo"
    post_data = f"kcbh={kcbh}&termId={term_id}"

    resp = _http_post(
        url, post_data, cookies, timeout=35,
        referer="https://jwgl.dhu.edu.cn/dhu/PublicQuery/toPage",
    )
    if not resp:
        return None

    # Cookie 失效检测：抛 SessionExpired 让调用方触发重登录
    _check_session_expired(resp)

    try:
        data = json.loads(resp)
    except json.JSONDecodeError:
        log(f"⚠️  [{kcbh}] JSON 解析失败")
        return None

    if not data.get("success"):
        log(f"⚠️  [{kcbh}] 接口返回失败")
        return None

    # 解析 content 中的 HTML 表格 → 结构化数据
    html_content = data.get("content", "")
    classes = _parse_timetable_html(html_content)
    return {
        "course_code": kcbh,
        "raw_html": html_content,
        "classes": classes,
        "class_count": len(classes),
    }


def _parse_timetable_html(html):
    """
    用 BeautifulSoup 解析开课班级 HTML 表格。
    每行: kcbh | kcmc | orgname | cttId | classNo | maxCnt | enrollCnt | applyCnt | 建议优选专业 (校区) | 教师 | (colspan=3 时间地点)
    """
    soup = BeautifulSoup(html, "html.parser")
    classes = []

    for tr in soup.find_all("tr"):
        # 跳过表头
        if tr.find("th"):
            continue

        tds = tr.find_all("td")
        if len(tds) < 10:
            continue

        def txt(td):
            return td.get_text(strip=True)

        # 教师信息
        teacher_td = tds[9]
        teacher = teacher_td.get_text(strip=True)
        teacher_id = ""
        a_tag = teacher_td.find("a")
        if a_tag and a_tag.get("onclick"):
            m = re.search(r'intoTeacherInfo\("(\d+)"\)', a_tag["onclick"])
            if m:
                teacher_id = m.group(1)

        # 时间地点列 (最后一个 td，内含嵌套表格)
        schedule_html = ""
        schedule_entries = []
        if len(tds) > 10:
            inner_table = tds[10].find("table")
            if inner_table:
                schedule_html = str(inner_table)
                schedule_entries = _parse_schedule_bs(inner_table)

        cls_info = {
            "cttId": txt(tds[3]),
            "classNo": txt(tds[4]),
            "maxCnt": _int_or(txt(tds[5])),
            "enrollCnt": _int_or(txt(tds[6])),
            "applyCnt": _int_or(txt(tds[7])),
            # td[8] 是"建议优选专业"列，对公共课等课程实际就是校区文本
            # （如 "延安路校区" / "松江校区"），是最权威的校区来源
            "suggested_major": txt(tds[8]),
            "teacher_name": teacher,
            "teacher_id": teacher_id,
            "schedule_raw": schedule_html,
            "schedule": schedule_entries,
        }
        classes.append(cls_info)

    return classes


def _parse_schedule_bs(table_tag):
    """用 BeautifulSoup 解析时间地点嵌套表格"""
    entries = []
    for tr in table_tag.find_all("tr"):
        cells = tr.find_all("td")
        if len(cells) >= 3:
            entries.append({
                "weeks": cells[0].get_text(strip=True),
                "time_slot": cells[1].get_text(strip=True),
                "classroom": cells[2].get_text(strip=True),
            })
        elif len(cells) == 2:
            entries.append({
                "weeks": cells[0].get_text(strip=True),
                "time_slot": cells[1].get_text(strip=True),
                "classroom": "",
            })
    return entries


def _int_or(s, default=0):
    try:
        return int(s)
    except ValueError:
        return default


# ── 主流程 ─────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="抓取教务系统开课数据")
    parser.add_argument("--user", default="", help="指定用户名（从 cookies.json 中选取）")
    parser.add_argument("--term", type=int, default=88, help="学期 ID (默认 88)")
    parser.add_argument("--limit", type=int, default=0, help="限制抓取前 N 门课 (0=不限制)")
    parser.add_argument("--output", default="courses_full.json", help="输出 JSON 文件路径")
    parser.add_argument("--list-only", action="store_true", help="仅获取课程列表，不获取详细开课信息")
    args = parser.parse_args()

    # 1. 获取 cookie
    cookies_dict = load_cookies_dict()
    if not cookies_dict:
        log("❌ cookies.json 为空或不存在，请先运行主程序获取 Cookie")
        sys.exit(1)

    # 如果指定了用户，使用该用户的 cookie
    if args.user:
        if args.user not in cookies_dict:
            log(f"❌ cookies.json 中未找到用户: {args.user}，可用: {list(cookies_dict.keys())}")
            sys.exit(1)
        cookie_str = cookies_dict[args.user]
        current_user = args.user
        log(f"👤 使用用户: {args.user}")
    else:
        # 自动选择第一个有效的
        current_user = list(cookies_dict.keys())[0]
        cookie_str = cookies_dict[current_user]
        log(f"👤 自动选择用户: {current_user}")

    # 2. 获取课程列表
    courses = fetch_course_list(cookie_str, term_id=args.term)
    if not courses:
        log("❌ 未获取到课程数据，退出")
        sys.exit(1)

    # 标准化课程字段
    normalized_courses = []
    for c in courses:
        normalized_courses.append({
            "id": c.get("id", ""),
            "kcbh": c.get("kcbh", ""),
            "kcmc": c.get("kcmc", ""),
            "xf": c.get("xf", ""),
            "orgname": c.get("orgname", ""),
            "jxdg_url": c.get("jxdg_url", ""),
            "jxrl_url": c.get("jxrl_url", ""),
        })

    if args.list_only:
        output = {
            "meta": {
                "term_id": args.term,
                "user": current_user,
                "fetch_time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "total_courses": len(normalized_courses),
            },
            "courses": normalized_courses,
        }
        save_json(output, args.output)
        log("✅ 列表获取完成 (未获取详细开课信息)")
        return

    # 3. 逐门获取开课详细信息
    limit = args.limit if args.limit > 0 else len(normalized_courses)
    log(f"🚀 开始逐门获取开课详细信息 (共 {len(normalized_courses)} 门，本次取 {limit} 门)...")

    results = []
    for i, course in enumerate(normalized_courses[:limit]):
        kcbh = course["kcbh"]
        kcmc = course["kcmc"]
        log(f"  [{i+1}/{limit}] {kcbh} {kcmc}")

        timetable = fetch_course_timetable(cookie_str, kcbh, term_id=args.term)

        result = {
            **course,  # id, kcbh, kcmc, xf, orgname
            "timetable": timetable,
        }
        results.append(result)

        # 礼貌性延迟，避免触发风控
        if i < limit - 1:
            time.sleep(0.3)

    # 4. 汇总输出
    output = {
        "meta": {
            "term_id": args.term,
            "user": current_user,
            "fetch_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_courses": len(normalized_courses),
            "fetched_detail_count": len(results),
        },
        "courses": results,
    }

    save_json(output, args.output)
    log(f"\n{'='*50}")
    log(f"📊 汇总:")
    log(f"   总课程数: {output['meta']['total_courses']}")
    log(f"   已获取详情: {output['meta']['fetched_detail_count']} 门")
    total_classes = sum(len(c.get("timetable", {}).get("classes", [])) for c in results if c.get("timetable"))
    log(f"   总开课班级数: {total_classes}")
    log(f"   输出文件: {args.output}")
    log(f"{'='*50}")


if __name__ == "__main__":
    main()
