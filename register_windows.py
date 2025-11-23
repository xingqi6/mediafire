"""
MediaFire 自动注册脚本 - Windows 本地版
特点:
1. 带界面浏览器,可以观察整个过程
2. 检测到验证码时自动暂停,等待手动处理
3. 完成验证码后自动继续
4. 详细的控制台输出
"""

import os
import random
import string
import time
import logging
from typing import Optional, Tuple

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

# 彩色日志(Windows 支持)
try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    HAS_COLOR = True
except ImportError:
    HAS_COLOR = False
    print("提示: 安装 colorama 可获得彩色输出 (pip install colorama)")

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


def print_color(message: str, color: str = "white"):
    """彩色打印"""
    if not HAS_COLOR:
        print(message)
        return
    
    colors = {
        "red": Fore.RED,
        "green": Fore.GREEN,
        "yellow": Fore.YELLOW,
        "blue": Fore.BLUE,
        "cyan": Fore.CYAN,
        "magenta": Fore.MAGENTA,
    }
    
    print(colors.get(color, "") + message + Style.RESET_ALL)


def print_banner():
    """打印启动横幅"""
    banner = """
╔══════════════════════════════════════════════════════════╗
║      MediaFire 自动注册工具 - Windows 本地版            ║
║                                                          ║
║  特性: 可视化浏览器 + 手动验证码处理                    ║
╚══════════════════════════════════════════════════════════╝
    """
    print_color(banner, "cyan")


def generate_random_name() -> Tuple[str, str]:
    """生成随机姓名"""
    first_name = ''.join(random.choices(string.ascii_letters, k=6)).capitalize()
    last_name = ''.join(random.choices(string.ascii_letters, k=7)).capitalize()
    return first_name, last_name


def create_driver() -> webdriver.Chrome:
    """创建 Chrome 驱动(带界面)"""
    print_color("\n[1/6] 正在启动 Chrome 浏览器...", "cyan")
    
    chrome_options = Options()
    
    # 不使用无头模式,显示浏览器窗口
    # chrome_options.add_argument("--headless")  # 注释掉
    
    # 窗口大小
    chrome_options.add_argument("--start-maximized")
    
    # 反检测配置
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    
    # 禁用烦人的提示
    chrome_options.add_experimental_option("prefs", {
        "profile.default_content_setting_values.notifications": 2,
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False
    })
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # 移除 webdriver 标识
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """
        })
        
        driver.set_page_load_timeout(60)
        driver.implicitly_wait(5)
        
        print_color("✓ Chrome 浏览器启动成功", "green")
        return driver
    except Exception as e:
        print_color(f"✗ 浏览器启动失败: {e}", "red")
        raise


def wait_element(driver: webdriver.Chrome, by: By, value: str, timeout: int = 10):
    """等待元素出现"""
    try:
        return WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )
    except TimeoutException:
        return None


def find_element_safe(driver: webdriver.Chrome, element_type: str):
    """安全查找元素"""
    strategies = {
        "first_name": [
            (By.NAME, "reg_first_name"),
            (By.ID, "reg_first_name"),
        ],
        "last_name": [
            (By.NAME, "reg_last_name"),
            (By.ID, "reg_last_name"),
        ],
        "email": [
            (By.NAME, "reg_email"),
            (By.ID, "reg_email"),
        ],
        "password": [
            (By.NAME, "reg_pass"),
            (By.ID, "reg_pass"),
        ],
        "checkbox": [
            (By.NAME, "agreement"),
            (By.ID, "agreement"),
        ],
        "submit": [
            (By.NAME, "signup_continue"),
            (By.ID, "signup_continue"),
        ]
    }
    
    if element_type not in strategies:
        return None
    
    for by, value in strategies[element_type]:
        elem = wait_element(driver, by, value, timeout=8)
        if elem:
            return elem
    
    return None


def click_sign_up_basic(driver: webdriver.Chrome) -> bool:
    """点击 BASIC 套餐的 SIGN UP 按钮"""
    print_color("\n[2/6] 正在选择 BASIC 套餐...", "cyan")
    
    strategies = [
        (By.XPATH, "(//button[contains(text(), 'SIGN UP')])[last()]"),
        (By.XPATH, "//button[contains(text(), 'SIGN UP')]"),
    ]
    
    for by, value in strategies:
        try:
            button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((by, value))
            )
            # 滚动到按钮位置
            driver.execute_script("arguments[0].scrollIntoView(true);", button)
            time.sleep(1)
            button.click()
            print_color("✓ 已点击 SIGN UP 按钮", "green")
            time.sleep(3)
            return True
        except:
            continue
    
    return False


def wait_for_captcha(driver: webdriver.Chrome) -> bool:
    """检测并等待用户完成验证码"""
    # 检查是否有验证码
    has_captcha = False
    captcha_keywords = ["recaptcha", "captcha", "g-recaptcha"]
    
    for keyword in captcha_keywords:
        if keyword in driver.page_source.lower():
            has_captcha = True
            break
    
    if not has_captcha:
        return True
    
    print_color("\n" + "="*60, "yellow")
    print_color("⚠️  检测到验证码(CAPTCHA)!", "yellow")
    print_color("="*60, "yellow")
    print_color("\n请在浏览器窗口中完成验证码:", "yellow")
    print_color("1. 点击「我不是机器人」复选框", "yellow")
    print_color("2. 如果出现图片验证,请完成选择", "yellow")
    print_color("3. 等待验证通过后,脚本会自动继续", "yellow")
    print_color("\n正在等待...(最多 3 分钟)\n", "yellow")
    
    # 等待验证码消失
    start_time = time.time()
    max_wait = 180  # 3分钟
    
    while time.time() - start_time < max_wait:
        time.sleep(2)
        
        # 检查验证码是否还在
        still_has_captcha = False
        for keyword in captcha_keywords:
            if keyword in driver.page_source.lower():
                still_has_captcha = True
                break
        
        if not still_has_captcha:
            print_color("\n✓ 验证码已完成!", "green")
            time.sleep(2)
            return True
        
        # 显示倒计时
        elapsed = int(time.time() - start_time)
        remaining = max_wait - elapsed
        print(f"\r等待中... 剩余时间: {remaining}秒  ", end="", flush=True)
    
    print_color("\n\n✗ 验证码等待超时", "red")
    return False


def register_one_account(email: str, password: str, ref_link: str) -> bool:
    """注册单个账号"""
    driver: Optional[webdriver.Chrome] = None
    
    try:
        print_color("\n" + "="*60, "cyan")
        print_color(f"开始注册账号: {email}", "cyan")
        print_color("="*60, "cyan")
        
        driver = create_driver()
        
        # 访问邀请链接
        print_color(f"\n访问邀请链接: {ref_link}", "blue")
        driver.get(ref_link)
        time.sleep(4)
        
        # 点击 SIGN UP
        current_url = driver.current_url
        if "upgrade" in current_url.lower():
            if not click_sign_up_basic(driver):
                print_color("⚠️  无法点击 SIGN UP,尝试直接访问注册页面", "yellow")
                reg_url = ref_link
                if "?" in ref_link:
                    base = ref_link.split("?")[0]
                    params = ref_link.split("?")[1]
                    reg_url = f"{base.rstrip('/')}/upgrade/registration.php?pid=free&{params}"
                else:
                    reg_url = f"{ref_link.rstrip('/')}/upgrade/registration.php?pid=free"
                
                driver.get(reg_url)
                time.sleep(3)
        
        # 填写表单
        print_color("\n[3/6] 正在填写注册表单...", "cyan")
        
        first_name, last_name = generate_random_name()
        
        elements = {
            "first_name": find_element_safe(driver, "first_name"),
            "last_name": find_element_safe(driver, "last_name"),
            "email": find_element_safe(driver, "email"),
            "password": find_element_safe(driver, "password"),
            "checkbox": find_element_safe(driver, "checkbox"),
            "submit": find_element_safe(driver, "submit"),
        }
        
        # 检查元素
        for name, elem in elements.items():
            if not elem and name != "checkbox":
                print_color(f"✗ 无法找到 {name} 输入框", "red")
                return False
        
        # 填写表单
        print_color(f"  姓名: {first_name} {last_name}", "blue")
        elements["first_name"].clear()
        elements["first_name"].send_keys(first_name)
        time.sleep(0.5)
        
        elements["last_name"].clear()
        elements["last_name"].send_keys(last_name)
        time.sleep(0.5)
        
        print_color(f"  邮箱: {email}", "blue")
        elements["email"].clear()
        elements["email"].send_keys(email)
        time.sleep(0.5)
        
        print_color(f"  密码: {'*' * len(password)}", "blue")
        elements["password"].clear()
        elements["password"].send_keys(password)
        time.sleep(0.5)
        
        # 勾选条款
        if elements["checkbox"]:
            if not elements["checkbox"].is_selected():
                elements["checkbox"].click()
                print_color("  ✓ 已勾选服务条款", "blue")
                time.sleep(0.5)
        
        print_color("✓ 表单填写完成", "green")
        
        # 检查验证码
        print_color("\n[4/6] 检查验证码...", "cyan")
        if not wait_for_captcha(driver):
            print_color("✗ 验证码处理失败", "red")
            return False
        
        # 提交表单
        print_color("\n[5/6] 提交注册表单...", "cyan")
        try:
            elements["submit"].click()
            print_color("✓ 已点击提交按钮", "green")
        except:
            driver.execute_script("arguments[0].click();", elements["submit"])
            print_color("✓ 已使用 JS 点击提交按钮", "green")
        
        time.sleep(5)
        
        # 检查结果
        print_color("\n[6/6] 等待注册结果...", "cyan")
        final_url = driver.current_url
        
        # 如果还在注册页面,说明失败
        if "registration.php" in final_url:
            print_color("✗ 仍在注册页面,注册可能失败", "red")
            
            # 查找错误信息
            try:
                error_selectors = [
                    "//div[contains(@class, 'error')]",
                    "//span[contains(@class, 'error')]",
                    "//*[contains(text(), 'already')]",
                    "//*[contains(text(), 'invalid')]",
                ]
                
                for selector in error_selectors:
                    elements_found = driver.find_elements(By.XPATH, selector)
                    for elem in elements_found:
                        if elem.is_displayed() and elem.text.strip():
                            print_color(f"错误信息: {elem.text}", "red")
            except:
                pass
            
            input("\n按 Enter 键关闭浏览器...")
            return False
        
        # 等待跳转
        try:
            WebDriverWait(driver, 30).until(
                EC.any_of(
                    EC.url_contains("myfiles"),
                    EC.url_contains("dashboard"),
                    EC.url_contains("welcome"),
                )
            )
            
            print_color("\n" + "="*60, "green")
            print_color("✓✓✓ 注册成功! ✓✓✓", "green")
            print_color("="*60, "green")
            print_color(f"\n账号: {email}", "green")
            print_color(f"密码: {password}", "green")
            
            # 检查是否需要邮箱验证
            if "verify" in driver.page_source.lower():
                print_color("\n⚠️  需要邮箱验证,请检查邮箱并点击验证链接", "yellow")
            
            input("\n按 Enter 键继续下一个账号(或关闭浏览器)...")
            return True
            
        except TimeoutException:
            # 可能需要邮箱验证
            if "verify" in driver.page_source.lower() or "confirmation" in driver.page_source.lower():
                print_color("\n" + "="*60, "yellow")
                print_color("⚠️  注册成功,但需要邮箱验证", "yellow")
                print_color("="*60, "yellow")
                print_color(f"\n账号: {email}", "yellow")
                print_color(f"请检查邮箱并点击验证链接", "yellow")
                
                input("\n按 Enter 键继续...")
                return True
            
            print_color("\n✗ 注册失败: 未检测到成功标识", "red")
            input("\n按 Enter 键关闭浏览器...")
            return False
    
    except Exception as e:
        print_color(f"\n✗ 发生异常: {e}", "red")
        import traceback
        traceback.print_exc()
        input("\n按 Enter 键关闭浏览器...")
        return False
    
    finally:
        if driver:
            driver.quit()
            print_color("\n浏览器已关闭", "blue")


def main():
    """主函数"""
    print_banner()
    
    print_color("\n请输入配置信息:", "cyan")
    print_color("-" * 60, "cyan")
    
    # 交互式输入
    ref_link = input("\n1. MediaFire 邀请链接: ").strip()
    if not ref_link:
        print_color("✗ 邀请链接不能为空", "red")
        input("按 Enter 键退出...")
        return
    
    password = input("2. 统一密码: ").strip()
    if not password:
        print_color("✗ 密码不能为空", "red")
        input("按 Enter 键退出...")
        return
    
    email_input = input("3. 邮箱列表(逗号分隔): ").strip()
    if not email_input:
        print_color("✗ 邮箱不能为空", "red")
        input("按 Enter 键退出...")
        return
    
    emails = [e.strip() for e in email_input.split(",") if e.strip()]
    
    print_color(f"\n配置确认:", "cyan")
    print_color(f"  邀请链接: {ref_link}", "blue")
    print_color(f"  密码: {'*' * len(password)}", "blue")
    print_color(f"  邮箱数量: {len(emails)}", "blue")
    print_color(f"  邮箱列表:", "blue")
    for i, email in enumerate(emails, 1):
        print_color(f"    [{i}] {email}", "blue")
    
    confirm = input("\n确认开始注册? (y/n): ").lower()
    if confirm != 'y':
        print_color("已取消", "yellow")
        return
    
    # 开始批量注册
    success_count = 0
    failed_list = []
    
    for idx, email in enumerate(emails, 1):
        print_color(f"\n\n{'='*60}", "magenta")
        print_color(f"进度: [{idx}/{len(emails)}]", "magenta")
        print_color(f"{'='*60}", "magenta")
        
        if register_one_account(email, password, ref_link):
            success_count += 1
        else:
            failed_list.append(email)
        
        # 如果不是最后一个,等待一下
        if idx < len(emails):
            wait_time = random.randint(10, 20)
            print_color(f"\n等待 {wait_time} 秒后继续下一个账号...", "yellow")
            time.sleep(wait_time)
    
    # 显示最终结果
    print_color("\n\n" + "="*60, "cyan")
    print_color("批量注册任务完成", "cyan")
    print_color("="*60, "cyan")
    print_color(f"\n总计: {len(emails)} 个账号", "blue")
    print_color(f"成功: {success_count} 个", "green")
    print_color(f"失败: {len(failed_list)} 个", "red")
    
    if failed_list:
        print_color("\n失败的邮箱:", "red")
        for email in failed_list:
            print_color(f"  - {email}", "red")
    
    input("\n\n按 Enter 键退出...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_color("\n\n程序被用户中断", "yellow")
    except Exception as e:
        print_color(f"\n\n程序出错: {e}", "red")
        import traceback
        traceback.print_exc()
        input("\n按 Enter 键退出...")
