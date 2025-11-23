import requests
import os
import random
import string
import time

# --- 环境变量读取 ---
# .rstrip('/') 是为了防止 URL 结尾有多个斜杠
MAIL_LOGIN_URL = os.getenv('MAIL_LOGIN_URL').rstrip('/')
MEDIAFIRE_REGISTER_URL = os.getenv('MEDIAFIRE_REGISTER_URL')

# 敏感信息
MAIL_USERNAME = os.getenv('MAIL_USERNAME')
MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
ACCOUNT_PASSWORD = os.getenv('ACCOUNT_PASSWORD')

# 控制次数
try:
    REGISTRATION_COUNT = int(os.getenv('REGISTRATION_COUNT', 1))
except ValueError:
    REGISTRATION_COUNT = 1

# --- 辅助函数 ---

def generate_random_string(length=8):
    """生成随机用户名或密码片段"""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

# --- 核心函数 ---

def login_and_create_email(session):
    """
    登录临时邮箱后台并创建新邮箱。
    """
    print(f"尝试处理邮箱端点: {MAIL_LOGIN_URL}/login")
    
    LOGIN_SUBMIT_URL = f"{MAIL_LOGIN_URL}/login" 
    
    try:
        # 步骤 0: 先 GET 访问登录页面，获取 Session Cookie 和 CSRF Token (如果需要)
        print("步骤 0: GET 访问登录页以初始化会话...")
        get_response = session.get(LOGIN_SUBMIT_URL)
        get_response.raise_for_status()
        
        # TODO: 如果网站有 CSRF 保护，在这里解析 get_response.text 提取 CSRF Token
        # csrf_token = extract_csrf(get_response.text) # 假设的提取函数
        
        # -------------------
        # 步骤 1: 登录请求 
        # -------------------
        
        # ⚠️ TODO 1: 替换为网站实际要求的登录字段名和值！
        login_payload = {
            "action": "login",               # <--- 假设通过 action 字段区分
            "user_field": MAIL_USERNAME,     # <--- 替换为实际的用户名字段名！
            "pass_field": MAIL_PASSWORD,     # <--- 替换为实际的密码字段名！
            # "csrf_token": csrf_token,      # 如果需要
        }
        
        print("步骤 1: 尝试 POST 登录...")
        login_response = session.post(LOGIN_SUBMIT_URL, data=login_payload)
        login_response.raise_for_status() 
        
        # 检查是否登录成功
        # ⚠️ TODO 2: 替换为实际的登录成功标识（例如：检查跳转后的 URL 或响应内容中的关键字）
        if login_response.status_code == 200 and "登录成功后的关键字" not in login_response.text:
             print("登录失败，请检查账号密码和登录逻辑。")
             return None

        print("✅ 登录成功。")

        # -------------------
        # 步骤 2: 创建新邮箱
        # -------------------
        new_username = generate_random_string(10)
        
        # ⚠️ TODO 3: 替换为网站实际要求的创建邮箱字段名和值！
        create_payload = {
            "action": "create",              # <--- 假设通过 action 字段区分
            "new_email_prefix_field": new_username, # <--- 替换为实际创建邮箱前缀的字段名！
            "domain_field": "928090.xyz",    # 如果需要指定域名
        }
        
        print(f"步骤 2: 尝试 POST 创建新邮箱 ({new_username}...)")
        create_response = session.post(LOGIN_SUBMIT_URL, data=create_payload)
        create_response.raise_for_status()
        
        # 检查是否创建成功
        # ⚠️ TODO 4: 替换为实际的创建成功标识
        if "创建成功后的关键字" in create_response.text:
            new_email = f"{new_username}@928090.xyz" 
            print(f"✅ 成功创建新邮箱: {new_email}")
            return new_email
        else:
            print(f"创建邮箱失败。响应内容截选: {create_response.text[:200]}")
            return None
        
    except requests.exceptions.RequestException as e:
        print(f"邮箱操作出错: {e}")
        return None

def register_mediafire(session, email):
    """
    使用创建的邮箱注册 MediaFire。
    """
    print(f"尝试使用邮箱 {email} 注册 MediaFire...")
    
    first_name = generate_random_string(6).capitalize()
    last_name = generate_random_string(8).capitalize()
    
    try:
        # 步骤 1: 访问注册页面 (获取必要的 Cookie)
        print("步骤 1: GET MediaFire 注册页...")
        session.get(MEDIAFIRE_REGISTER_URL) 
        
        # 步骤 2: 提交注册表单
        # ⚠️ TODO 5: 必须准确分析 MediaFire 注册表单的 POST 提交路径和字段名称！
        MEDIAFIRE_POST_URL = "https://www.mediafire.com/register/submit" # <--- 替换为实际提交路径！
        
        register_payload = {
            "first_name": first_name,         # 随机名字
            "last_name": last_name,           # 随机名字
            "email": email,                   # 临时邮箱
            "password": ACCOUNT_PASSWORD,     # 环境变量自定义密码
            "tos_accepted": "1",              # 接受条款
            # "csrf_token_mf": "..."          # 如果 MediaFire 需要 CSRF token
        }
        
        print("步骤 2: POST 提交 MediaFire 注册...")
        register_response = session.post(MEDIAFIRE_POST_URL, data=register_payload)
        register_response.raise_for_status()

        # ⚠️ TODO 6: 检查 MediaFire 注册是否成功 (检查响应内容或跳转)
        if "MediaFire注册成功标识" in register_response.text or register_response.status_code in [200, 302]:
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
    # 调试信息 (保留，用于日志追踪)
    print("-" * 50)
    print(f"DEBUG: REGISTRATION_COUNT is set to: {REGISTRATION_COUNT}")
    print(f"DEBUG: Login URL: {MAIL_LOGIN_URL}/login")
    print(f"DEBUG: Register URL: {MEDIAFIRE_REGISTER_URL}")
    print("-" * 50)
    
    if not all([MAIL_USERNAME, MAIL_PASSWORD, ACCOUNT_PASSWORD]):
        print("错误：必要的敏感环境变量 (MAIL_USERNAME, MAIL_PASSWORD, ACCOUNT_PASSWORD) 未设置！请检查 GitHub Secrets。")
        return
        
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
        
        # 3. 间隔时间
        time.sleep(random.randint(5, 15)) 
        
    print(f"\n--- 流程结束。总计执行 {REGISTRATION_COUNT} 次，成功 {success_count} 次 ---")


if __name__ == "__main__":
    run_registration_flow()
