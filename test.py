# -*- coding: utf-8 -*-
"""
PushPlus 微信推送功能独立测试脚本
逻辑与主程序 core.py 完全一致
"""

import json
import urllib.request
import sys

def send_push_notification(token, title, content):
    """
    发送 PushPlus 微信通知 (核心逻辑)
    """
    if not token:
        print("❌ 错误：Token 不能为空")
        return
    
    url = "http://www.pushplus.plus/send"
    
    # 构造请求数据
    data = {
        "token": token,
        "title": title,
        "content": content,
        "template": "html" # 使用 HTML 模板以支持换行和加粗
    }
    
    print(f"🔄 正在发送请求到 PushPlus...")
    
    try:
        # 1. 数据编码
        json_data = json.dumps(data).encode('utf-8')
        
        # 2. 构造请求对象
        req = urllib.request.Request(
            url, 
            data=json_data, 
            headers={'Content-Type': 'application/json'}
        )
        
        # 3. 发起请求并获取响应
        with urllib.request.urlopen(req) as response:
            result = response.read().decode('utf-8')
            print(f"✅ 服务器响应: {result}")
            
            # 简单的结果分析
            res_json = json.loads(result)
            if res_json.get("code") == 200:
                print("\n🎉 测试成功！请检查你的微信（PushPlus公众号）。")
            else:
                print(f"\n⚠️ 发送可能失败，错误信息: {res_json.get('msg')}")
                
    except Exception as e:
        print(f"\n❌ 网络请求异常: {e}")

def main():
    print("=" * 40)
    print("      PushPlus 微信推送测试工具")
    print("=" * 40)
    print("说明：")
    print("1. 请确保你已关注 'PushPlus推送加' 公众号")
    print("2. 请前往 http://www.pushplus.plus/ 获取你的 Token")
    print("-" * 40)
    
    # 获取用户输入
    token = input("请输入你的 PushPlus Token: ").strip()
    
    if not token:
        print("❌ 未输入 Token，程序退出。")
        return

    # 构造测试内容
    title = "抢课系统测试消息"
    content = (
        "你好！<br>"
        "这是来自 <b>智能抢课系统</b> 的测试消息。<br>"
        "如果你看到了这条消息，说明你的 Token 配置正确，"
        "可以放心地填入主程序的设置中了！<br>"
        "<br>"
        "<i>End of Test</i>"
    )

    # 执行发送
    send_push_notification(token, title, content)
    
    input("\n按回车键退出...")

if __name__ == "__main__":
    main()