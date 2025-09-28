from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.edge.options import Options
import json
from bs4 import BeautifulSoup
import subprocess
import time
import os
def get_cookies(name, password):
    edge_options = Options()
    edge_options.add_argument("--headless")   
    edge_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Edge(options=edge_options)
    driver.get("https://jwgl.dhu.edu.cn/dhu/casLogin")
    username_box = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "input")))
    username_box.send_keys(name)
    password_box = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//input[@type="password"]')))
    password_box.send_keys(password)
    login_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//button[@title="登录"]')))
    login_button.click()
    check_element = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, "//li[text()='个人信息查看']")))
    cookies = driver.get_cookies()
    
    print(cookies)
    driver.quit()
    return cookies
def sccourse(cookies, courseid):
    curl_cmd = [
        "curl",
        "https://jwgl.dhu.edu.cn/dhu/selectcourse/scSubmit",
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
    result = subprocess.run(curl_cmd, capture_output=True, text=True, check=True,encoding="utf-8")
    return result.stdout
if __name__ == "__main__":
    print(os.getcwd())
    with open("accounts.json", "r", encoding="utf-8") as f:
        accounts_data = json.load(f)["accounts"]

# 列出所有账号
    print("可用账号列表：")
    for i, acc in enumerate(accounts_data, start=1):
        print(f"{i}. {acc['name']} ({acc['username']})")

# 用户选择账号
    choice = int(input("请选择要登录的账号序号: ")) - 1
    selected_acc = accounts_data[choice]
    name = selected_acc["name"]
    username = selected_acc["username"]
    password = selected_acc["password"]

    print(f"\n你选择了账号: {name} ({username})")
    with open("courses.json", "r", encoding="utf-8") as f:
        courses_data = json.load(f)
    courses = courses_data.get(name, [])
    
    with open("cookies.json", "r", encoding="utf-8") as f:
        cookies_dict = json.load(f)
    cookies_str = cookies_dict.get(name, "")
    
    print(cookies_str)
    
    print(f"{name} 的课程编号: {courses}")
    choice = input("是否更新cookies？(y/n): ")
    if choice == 'y':
        print("正在登录...")
        cookies = get_cookies(username, password) 
        cookies_str = "; ".join(f"{c['name']}={c['value']}" for c in cookies)
        with open("cookies.json", "r", encoding="utf-8") as f:
            cookies_data = json.load(f)
        # 更新/新增 name 对应的 cookie
        cookies_data[name] = cookies_str
        # 写回文件
        with open("cookies.json", "w", encoding="utf-8") as f:
            json.dump(cookies_data, f, ensure_ascii=False, indent=4)
        print(f"已更新 {name} 的 cookie")

        print("登录成功！")
    b = True
    while b:
        for courseid in courses:
            print(f"正在选课,课程id {courseid} ...")
            result = sccourse(cookies_str, courseid)
            time.sleep(2)  # 等待3秒再尝试下一次选课
            if "true" in result and "Empty" not in result:
                print(f"{courseid}  选课成功！")
                b = False
            
            elif "F" in result:
                print("Cookie 可能已过期，需要重新登录。")
                print("正在登录...")
                cookies = get_cookies(username, password) 
                cookies_str = "; ".join(f"{c['name']}={c['value']}" for c in cookies)
                with open("cookies.json", "r", encoding="utf-8") as f:
                    cookies_data = json.load(f)
            # 更新/新增 name 对应的 cookie
                cookies_data[name] = cookies_str
             # 写回文件
                with open("cookies.json", "w", encoding="utf-8") as f:
                    json.dump(cookies_data, f, ensure_ascii=False, indent=4)
                print(f"已更新 {name} 的 cookie")

                print("登录成功！")
            else:
                print(f"{courseid}  选课失败，返回信息: {result}")
        