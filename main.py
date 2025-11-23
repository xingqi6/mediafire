# main.py
import requests
import os
import random
import string
import time

# --- 环境变量读取 ---
MAIL_LOGIN_URL = os.getenv('MAIL_LOGIN_URL')
MAIL_USERNAME = os.getenv('MAIL_USERNAME')
MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
MEDIAFIRE_REGISTER_URL = os.getenv('MEDIAFIRE_REGISTER_URL')
ACCOUNT_PASSWORD = os.getenv('ACCOUNT_PASSWORD')
REGISTRATION_COUNT = int(os.getenv('REGISTRATION_COUNT', 1)) # 默认只执行一次

# --- 核心函数 ---

def generate_random_string(length=8):
    """生成随机用户名或密码片段"""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def login_and_create_email(session):
    """
    登录临时邮箱后台并创建新邮箱。
    
    返回: 创建成功的邮箱地址 (e.g., 'new_user@928090.xyz') 或 None
    """
    print(f"尝试登录邮箱后台: {MAIL_LOGIN_URL}")
    
    # 步骤 1: 登录请求 (可能需要先GET获取Cookie/CSRF Token)
    # TODO: 根据实际网站结构填充登录数据
    login_payload = {
        "username": MAIL_USERNAME,
        "password": MAIL_PASSWORD,
        # "csrf_token": "..." # 如果网站有CSRF保护
    }
    
    try:
        # TODO: 替换为实际的登录路径
        login_response = session.post(f"{MAIL_LOGIN_URL}/login_path", data=login_payload)
        login_response.raise_for_status()
        
        # 检查是否登录成功 (例如：检查跳转或响应内容中的关键字)
        if "登录成功标识" not in login_response.text:
             print("登录失败，请检查账号密码和登录路径。")
             return None

        # 步骤 2: 创建新邮箱
        new_username = generate_random_string(10)
        # TODO: 替换为实际的创建邮箱请求路径和数据
        create_payload = {
            "action": "create",
            "new_email_prefix": new_username,
            # 其他必要的字段...
        }
        
        create_response = session.post(f"{MAIL_LOGIN_URL}/create_email_path", data=create_payload)
        create_response.raise_for_status()
        
        # TODO: 提取创建成功的完整邮箱地址
        new_email = f"{new_username}@928090.xyz" # 假设是这个格式
        print(f"✅ 成功创建新邮箱: {new_email}")
        return new_email
        
    except requests.exceptions.RequestException as e:
        print(f"邮箱操作出错: {e}")
        return None

def register_mediafire(session, email):
    """
    使用创建的邮箱注册 MediaFire。
    """
    print(f"尝试使用邮箱 {email} 注册 MediaFire...")
    
    # 随机生成前两个字段 (名字)
    first_name = generate_random_string(6).capitalize()
    last_name = generate_random_string(8).capitalize()
    
    # 步骤 1: 访问注册页面 (MediaFire 可能会在 GET 请求中设置必要的 Cookie)
    session.get(MEDIAFIRE_REGISTER_URL) 
    
    # 步骤 2: 提交注册表单
    # TODO: 必须准确分析 MediaFire 注册表单的字段名称！
    register_payload = {
        "first_name": first_name,         # 随机名字
        "last_name": last_name,           # 随机名字
        "email": email,                   # 临时邮箱
        "password": ACCOUNT_PASSWORD,     # 环境变量自定义密码
        "tos_accepted": "1",              # 接受条款
        # "csrf_token": "..." # 如果网站有CSRF保护，需要从GET请求中提取
    }
    
    try:
        # TODO: 替换为实际的 MediaFire 注册 POST 提交路径
        register_response = session.post("https://www.mediafire.com/register/submit", data=register_payload)
        register_response.raise_for_status()

        # TODO: 检查注册是否成功 (例如：检查响应内容或跳转)
        if "注册成功标识" in register_response.text or register_response.status_code in [200, 302]:
             print(f"🎉 成功注册 MediaFire 账户: {email} / {ACCOUNT_PASSWORD}")
             return True
        else:
             print(f"❌ MediaFire 注册失败。响应内容截选: {register_response.text[:200]}")
             return False

    except requests.exceptions.RequestException as e:
        print(f"MediaFire 注册出错: {e}")
        return False


# --- 主执行逻辑 ---
def run_registration_flow():
    """执行整个重复流程"""
    print(f"--- 开始执行 MediaFire 批量注册流程，共计 {REGISTRATION_COUNT} 次 ---")
    
    success_count = 0
    
    for i in range(1, REGISTRATION_COUNT + 1):
        print(f"\n======== 第 {i} 次注册开始 ========")
        
        # 使用 Session 保持会话和 Cookie
        s = requests.Session()
        s.headers.update({
            'User-Agent': generate_random_string(10), # 随机User-Agent以防屏蔽
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6',
        })
        
        # 1. 创建邮箱
        new_email = login_and_create_email(s)
        
        if not new_email:
            print(f"第 {i} 次失败：未能成功创建邮箱。跳过注册。")
            continue
            
        # 2. 注册 MediaFire
        if register_mediafire(s, new_email):
            success_count += 1
            
        print(f"======== 第 {i} 次注册结束 ========")
        
        # 3. 间隔时间，避免过于频繁的请求
        time.sleep(random.randint(5, 15)) 
        
    print(f"\n--- 流程结束。总计执行 {REGISTRATION_COUNT} 次，成功 {success_count} 次 ---")


if __name__ == "__main__":
    # 基本检查
    if not all([MAIL_USERNAME, MAIL_PASSWORD, ACCOUNT_PASSWORD]):
        print("错误：必要的敏感环境变量 (MAIL_USERNAME, MAIL_PASSWORD, ACCOUNT_PASSWORD) 未设置！请检查 GitHub Secrets。")
    elif not all([MAIL_LOGIN_URL, MEDIAFIRE_REGISTER_URL]):
        print("警告：URL 环境变量未设置，将使用默认 URL。")
    else:
        run_registration_flow()
