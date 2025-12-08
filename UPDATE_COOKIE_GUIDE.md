# 更新 Cookie 功能说明

## 功能变更

### 之前的方式
- **方法**: 从文件导入 Cookie
- **操作**: 菜单 → 导入 → Cookie 文件

### 现在的方式
- **方法**: 自动登录获取 Cookie
- **操作**: 菜单 → 新建 → 更新 Cookie
- **优势**: 
  - ✅ 自动化程度高，无需手动导出 Cookie
  - ✅ Cookie 始终最新
  - ✅ 登录失败会有详细错误提示

## 工作流程

### 使用步骤

1. **选择用户**
   - 从下拉菜单中选择需要更新 Cookie 的用户

2. **点击更新 Cookie**
   - 菜单 → 新建 → 更新 Cookie
   - 或者：点击 🎓 logo → 新建 → 更新 Cookie

3. **自动登录**
   - 程序使用该用户的学号和密码自动登录
   - 使用 Selenium + Edge WebDriver 进行登录
   - 登录过程在后台进行（headless 模式）

4. **获取并保存 Cookie**
   - 登录成功后，自动提取 Cookie
   - 保存到本地 `cookies.json` 文件
   - 状态栏显示成功消息

## 错误处理

### 可能的错误

1. **未选择用户**
   - 提示: "请先选择一个抢课人！"
   - 解决: 先从下拉菜单选择用户

2. **账户信息缺失**
   - 提示: "未找到用户...的账户信息！"
   - 原因: 账户数据被删除或损坏
   - 解决: 重新新建该用户账户

3. **登录失败**
   - 提示: "无法获取 Cookie: ..."（含具体错误信息）
   - 可能原因:
     - 学号或密码错误
     - 学选课系统维护中
     - 网络连接问题
     - WebDriver 路径配置问题
   - 解决: 检查学号和密码，确保网络正常

## 代码实现

### 核心逻辑
```python
def update_cookie_for_user(self):
    # 1. 获取选中用户的账户信息
    # 2. 调用 core.get_cookies(username, password)
    # 3. 转换 Cookie 格式为字符串
    # 4. 保存到 cookies.json
    # 5. 显示成功提示
```

### 关键函数
- **`core.get_cookies(name, password)`** - 使用 Selenium 登录并获取 Cookie
- **`load_cookies_dict()`** - 读取本地 cookies.json
- **`save_cookies_dict(cookies_dict)`** - 保存 cookies.json

## 状态显示

### 成功时
```
正在为 用户名 获取 Cookie...
✓ 已成功获取 用户名 的 Cookie
```

### 失败时
```
正在为 用户名 获取 Cookie...
✗ 获取 Cookie 失败: 具体错误信息
```

## 注意事项

- ⚠️ 确保 Edge WebDriver (msedgedriver.exe) 在系统 PATH 中或配置正确
- ⚠️ 学选课系统可能有登录频率限制，频繁更新 Cookie 可能被限制
- ⚠️ 如果学号或密码错误，会导致登录失败
- ℹ️ Cookie 有有效期，定期更新可确保选课功能正常

## 文件改动

- `main.py`
  - 修改 `update_cookie_for_user()` 方法
  - 从文件导入改为自动登录获取
  - 添加详细的状态提示和错误处理
