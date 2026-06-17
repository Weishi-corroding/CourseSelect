# -*- coding: utf-8 -*-
"""
捡漏模式诊断脚本 — 无 GUI，逐步骤测试并保存原始响应
用于排查 "JSON 解析失败" 的根本原因（cookie 过期？被限流？返回了 HTML？）
"""
import sys, os, json, time, traceback, io

# Windows 控制台 GBK 编码兼容：替换无法打印的字符
enc = getattr(sys.stdout, 'encoding', '').upper()
if enc in ('GBK', 'GB2312', 'CP936', ''):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 确保能导入 core.py
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core import (
    load_cookies_dict, load_courses,
    access_judge, query_course_info, sccourse,
)

# ── 配置 ──────────────────────────────────────────────────────────
USERNAME = "朱思闻"
DEBUG_DIR = "debug_output"
COURSES_FULL = "courses_full.json"

# ── 辅助 ──────────────────────────────────────────────────────────
def ensure_debug_dir():
    os.makedirs(DEBUG_DIR, exist_ok=True)

def save_response(name, text):
    """将原始响应保存到文件"""
    ts = time.strftime("%H%M%S")
    fname = f"{ts}_{name}.txt"
    path = os.path.join(DEBUG_DIR, fname)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return path

def summarize(text, label="响应"):
    """打印响应的摘要信息"""
    length = len(text)
    if not text:
        print(f"  ⚠️  {label}: 空响应（长度=0）")
        return
    print(f"  📊 {label}: {length} 字符")
    # 显示前 300 字符
    preview = text[:300]
    print(f"  🔍 开头: {repr(preview)}")
    # 判断是否是 JSON
    try:
        parsed = json.loads(text)
        print(f"  ✅ JSON 解析成功 → {type(parsed).__name__}")
        if isinstance(parsed, dict):
            print(f"     keys: {list(parsed.keys())[:10]}")
            if "success" in parsed:
                print(f"     success: {parsed['success']}")
            if "msg" in parsed:
                print(f"     msg: {parsed['msg']}")
            if "aaData" in parsed:
                print(f"     aaData 条数: {len(parsed.get('aaData', []))}")
        return True
    except json.JSONDecodeError as e:
        print(f"  ❌ JSON 解析失败: {e}")
        # 检查是否是 HTML
        if text.strip().startswith("<!") or text.strip().startswith("<"):
            print(f"  💡 原因: 服务器返回了 HTML（可能是登录页/错误页）")
            # 提取 title 帮助判断
            import re
            m = re.search(r"<title>(.*?)</title>", text, re.IGNORECASE)
            if m:
                print(f"     HTML 标题: {m.group(1)}")
        elif "TIMEOUT" in text:
            print(f"  💡 原因: 请求超时")
        elif "CURL ERROR" in text or "EXCEPTION" in text:
            print(f"  💡 原因: 底层请求异常")
        return False

def find_course_code(ctt_id):
    """从 courses_full.json 查找 cttId → kcbh"""
    try:
        with open(COURSES_FULL, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"  ⚠️  无法加载 {COURSES_FULL}: {e}")
        return None, None
    for course in data.get("courses", []):
        tt = course.get("timetable")
        if not tt:
            continue
        for cls in tt.get("classes", []):
            if cls.get("cttId") == ctt_id:
                return course.get("kcbh"), course.get("kcmc")
    return None, None

# ── 主流程 ──────────────────────────────────────────────────────────
def main():
    ensure_debug_dir()
    print("=" * 60)
    print(f"  捡漏模式诊断 — 用户: {USERNAME}")
    print(f"  时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  原始响应目录: {os.path.abspath(DEBUG_DIR)}/")
    print("=" * 60)

    # ── 步骤 0: 加载配置 ──
    print("\n📦 [步骤0] 加载配置...")
    cookies_dict = load_cookies_dict()
    cookie = cookies_dict.get(USERNAME, "")
    if not cookie:
        print(f"  ❌ 未找到 {USERNAME} 的 Cookie！")
        sys.exit(1)
    print(f"  ✅ Cookie 已加载 ({len(cookie)} 字符)")
    print(f"     前50字符: {cookie[:50]}...")

    courses = load_courses().get(USERNAME, [])
    if not courses:
        print(f"  ❌ {USERNAME} 没有待选课程")
        sys.exit(1)
    print(f"  ✅ 待选课程: {courses}")

    # ── 步骤 1: 查找课程代码 ──
    print("\n🔍 [步骤1] cttId → kcbh 映射查找...")
    for ctt_id in courses:
        kcbh, kcmc = find_course_code(ctt_id)
        if kcbh:
            print(f"  ✅ cttId={ctt_id} → kcbh={kcbh} ({kcmc})")
        else:
            print(f"  ⚠️  cttId={ctt_id} 未在 {COURSES_FULL} 中找到")

    # 用第一个课程进行后续测试
    TARGET_CTT = courses[0]
    COURSE_CODE, COURSE_NAME = find_course_code(TARGET_CTT)
    if not COURSE_CODE:
        print(f"  ❌ 无法获取课程代码，使用默认值测试")
        COURSE_CODE = TARGET_CTT

    # ── 步骤 2: accessJudge ──
    print(f"\n🔑 [步骤2] accessJudge (courseCode={COURSE_CODE})...")
    for attempt in range(3):
        print(f"  --- 第 {attempt+1} 次尝试 ---")
        resp = access_judge(cookie, COURSE_CODE)
        path = save_response(f"accessJudge_{attempt+1}", resp)
        print(f"    已保存: {path}")
        ok = summarize(resp, "accessJudge")
        if ok:
            break
        if attempt < 2:
            time.sleep(2)
    print()

    # ── 步骤 3: initACC (query_course_info) ──
    print(f"📋 [步骤3] initACC (courseCode={COURSE_CODE})...")
    for attempt in range(3):
        print(f"  --- 第 {attempt+1} 次尝试 ---")
        resp = query_course_info(cookie, COURSE_CODE)
        path = save_response(f"initACC_{attempt+1}", resp)
        print(f"    已保存: {path}")
        ok = summarize(resp, "initACC")
        if ok:
            # 如果是 JSON，打印 enrollCnt / maxCnt
            try:
                data = json.loads(resp)
                if data.get("success"):
                    for cls in data.get("aaData", []):
                        if str(cls.get("cttId")) == TARGET_CTT:
                            print(f"     🎯 目标班级: {cls.get('classNo')} "
                                  f"已选={cls.get('enrollCnt')}/{cls.get('maxCnt')} "
                                  f"教师={cls.get('techName','?')}")
            except:
                pass
            break
        if attempt < 2:
            print("  ⏳ 等待 3 秒后重试...")
            time.sleep(3)
    print()

    # ── 步骤 4: scSubmit (直接抢课) ──
    print(f"🎯 [步骤4] scSubmit (cttId={TARGET_CTT})...")
    for attempt in range(3):
        print(f"  --- 第 {attempt+1} 次尝试 ---")
        resp = sccourse(cookie, TARGET_CTT)
        path = save_response(f"scSubmit_{attempt+1}", resp)
        print(f"    已保存: {path}")
        ok = summarize(resp, "scSubmit")
        if ok:
            try:
                data = json.loads(resp)
                if data.get("success"):
                    print(f"  🎉 抢课成功！")
                elif data.get("msg") == "F":
                    print(f"  💡 风控拦截 (msg=F)")
                else:
                    print(f"  📝 服务器消息: {data.get('msg', '?')}")
            except:
                pass
            break
        if attempt < 2:
            print("  ⏳ 等待 3 秒后重试...")
            time.sleep(3)
    print()

    # ── 步骤 5: 连续测试（模拟捡漏压力） ──
    print("🔄 [步骤5] 连续 5 次 initACC 模拟捡漏压力...")
    for i in range(5):
        print(f"  --- 第 {i+1}/5 ---")
        resp = query_course_info(cookie, COURSE_CODE)
        ok = summarize(resp, f"initACC 压力#{i+1}")
        if not ok:
            print(f"  ⚠️  第 {i+1} 次已出现解析失败！")
        time.sleep(0.5)
    print()

    # ── 汇总 ──
    print("=" * 60)
    print("  诊断结论建议")
    print("=" * 60)
    print("请检查 debug_output/ 下的原始响应文件：")
    print("  - 如果返回了 HTML（含 <!DOCTYPE>）→ Cookie 可能已过期")
    print("  - 如果返回空字符串 → 可能被限流或网络问题")
    print("  - 如果返回 JSON 但 msg=F → 风控拦截")
    print("  - 如果返回 JSON 正常 → 可能是偶发问题，检查重试逻辑")
    print()
    print("提示：用 !python test_pickup_debug.py 运行")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠️  用户中断")
    except Exception as e:
        print(f"\n❌ 脚本异常: {e}")
        traceback.print_exc()
