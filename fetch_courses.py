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
import argparse
import re
import atexit
import threading
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# 复用 core 模块的路径 / 文件常量
FILES = {
    "accounts": "accounts.json",
    "courses": "courses.json",
    "cookies": "cookies.json",
}
LOG_FILE = "CoureseSelectDebug.log"


class SessionExpired(Exception):
    """Cookie 已失效，服务器返回或跳转到了统一登录页面。"""


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


_thread_local = threading.local()


def _get_session():
    """Return one pooled HTTP session per fetching thread."""
    session = getattr(_thread_local, "session", None)
    if session is not None:
        return session

    retry = Retry(
        total=2,
        connect=2,
        read=1,
        status=2,
        backoff_factor=0.5,
        status_forcelist=(502, 503, 504),
        allowed_methods=frozenset({"POST"}),
    )
    session = requests.Session()
    adapter = HTTPAdapter(pool_connections=4, pool_maxsize=8, max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    _thread_local.session = session
    return session


def cleanup_fetch_session():
    """Close the current thread's connection pool."""
    session = getattr(_thread_local, "session", None)
    if session is not None:
        session.close()
        del _thread_local.session


atexit.register(cleanup_fetch_session)


def _common_headers(cookies):
    """构造与浏览器和 core.py 一致的请求头。"""
    return {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
        "Origin": "https://jwgl.dhu.edu.cn",
        "Referer": "https://jwgl.dhu.edu.cn/dhu/PublicQuery/toPage",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/149.0.0.0 Safari/537.36 Edg/149.0.0.0"),
        "X-Requested-With": "XMLHttpRequest",
        "sec-ch-ua": '"Microsoft Edge";v="149", "Chromium";v="149", "Not)A;Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "Cookie": cookies,
    }


def _post_json(url, post_data, cookies, timeout=35):
    """POST a read-only query and return its JSON object, with actionable errors."""
    try:
        response = _get_session().post(
            url,
            data=post_data,
            headers=_common_headers(cookies),
            timeout=timeout,
        )
        response.raise_for_status()
    except requests.exceptions.Timeout:
        log("⚠️ 教务系统请求超时")
        return None
    except requests.exceptions.SSLError as exc:
        log(f"⚠️ HTTPS 握手失败: {exc}")
        return None
    except requests.exceptions.RequestException as exc:
        log(f"⚠️ 网络请求失败: {exc}")
        return None

    response_text = response.text.strip()
    if "cas.dhu.edu.cn" in response.url or response_text.startswith("/dhu/casLogin"):
        log("⚠️ Cookie 已失效，服务器跳转到了登录页面，请先更新 Cookie")
        raise SessionExpired("Cookie 已失效，服务器跳转到了登录页面")
    if not response.content:
        log("⚠️ 教务系统返回了空响应，Cookie 可能已失效")
        return None
    try:
        return response.json()
    except requests.exceptions.JSONDecodeError:
        content_type = response.headers.get("Content-Type", "未知")
        log(f"⚠️ 响应不是 JSON (Content-Type: {content_type})，Cookie 可能已失效")
        return None


# ── API 1: 获取学期开课总列表 ─────────────────────────────────────
def fetch_course_list(cookies, term_id=88, display_length=1876):
    """
    调用 getSelectCourseTermList，按服务器总记录数分页获取全部课程。

    display_length 是单页大小，不再是课程总数上限。
    返回 aaData 列表 (list[dict])。
    """
    url = "https://jwgl.dhu.edu.cn/dhu/PublicQuery/getSelectCourseTermList"
    try:
        page_size = int(display_length)
    except (TypeError, ValueError):
        page_size = 1876
    if page_size <= 0:
        page_size = 1876

    log(f"📡 正在获取学期开课列表 (termId={term_id})...")
    records = []
    offset = 0
    total = None
    page = 1

    while total is None or offset < total:
        post_data = (
            f"sEcho={page}&iColumns=6&sColumns="
            f"&iDisplayStart={offset}"
            f"&iDisplayLength={page_size}"
            "&mDataProp_0=kcmc&mDataProp_1=kcbh&mDataProp_2=xf"
            "&mDataProp_3=jxdg_url&mDataProp_4=jxrl_url&mDataProp_5=orgname"
            "&iSortCol_0=0&sSortDir_0=asc&iSortingCols=1"
            "&bSortable_0=false&bSortable_1=false&bSortable_2=false"
            "&bSortable_3=false&bSortable_4=false&bSortable_5=false"
            f"&termId={term_id}&course="
        )
        data = _post_json(url, post_data, cookies, timeout=35)
        if data is None:
            log(f"❌ 第 {page} 页获取失败，已中止以避免保存不完整数据")
            return []
        if not data.get("success"):
            log(f"⚠️ 第 {page} 页接口返回失败: {data.get('msg', '未知错误')}")
            return []

        page_records = data.get("aaData") or []
        if total is None:
            raw_total = data.get("iTotalDisplayRecords", data.get("iTotalRecords"))
            try:
                total = max(0, int(raw_total))
            except (TypeError, ValueError):
                total = len(page_records)

        if not page_records:
            log(f"❌ 第 {page} 页返回空数据，服务器报告仍有 {max(0, total - offset)} 条未获取")
            return []

        records.extend(page_records)
        offset += len(page_records)
        log(f"  已获取 {min(offset, total)}/{total} 门课程")
        page += 1

    if len(records) > total:
        records = records[:total]
    log(f"✅ 成功获取全部 {len(records)} 门课程 (服务器总记录: {total})")
    return records


# ── API 2: 获取单门课的开课详细信息 ───────────────────────────────
def fetch_course_timetable(cookies, kcbh, term_id=88):
    """
    调用 getCourseTimeTableInfo 获取某门课程的具体开课信息。
    返回解析后的 dict。
    """
    url = "https://jwgl.dhu.edu.cn/dhu/PublicQuery/getCourseTimeTableInfo"
    post_data = f"kcbh={kcbh}&termId={term_id}"

    data = _post_json(url, post_data, cookies, timeout=35)
    if data is None:
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
    每行: kcbh | kcmc | orgname | cttId | classNo | maxCnt | enrollCnt | applyCnt | 选课范围 | 教师 | (colspan=3 时间地点)
    """
    soup = BeautifulSoup(html, "html.parser")
    classes = []

    for tr in soup.find_all("tr"):
        # 跳过表头
        if tr.find("th"):
            continue

        # 只取当前行的单元格，避免把内层排课表格的 td 混入主表列。
        tds = tr.find_all("td", recursive=False)
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
            "selection_scope": txt(tds[8]),
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
