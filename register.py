import os
import random
import string
import time
import logging
from typing import Optional, List, Tuple

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def generate_random_name() -> str:
    """生成随机全名(6位名 + 7位姓)"""
    first_name = ''.join(random.choices(string.ascii_letters, k=6)).capitalize()
    last_name = ''.join(random.choices(string.ascii_letters, k=7)).capitalize()
    return first_name, last_name


def create_driver() -> webdriver.Chrome:
    """创建适配 GitHub Actions/Linux 的无头 Chrome 驱动"""
    chrome_options = Options()
    
    # 无头模式配置
    chrome_options.add_argument("--headless=new")
    
    # Linux 环境兼容配置
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # 禁用 GPU(无头模式无需)
    chrome_options.add_argument("--disable-gpu")
    
    # 设置窗口大小(模拟正常浏览)
    chrome_options.add_argument("--window-size=1920,1080")
    
    # 规避反爬检测
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    
    # 禁用浏览器通知
    chrome_options.add_argument("--disable-notifications")
    
    # 设置语言
    chrome_options.add_argument("--lang=en-US")
    
    # 设置 User-Agent
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    try:
        # 自动安装对应版本 ChromeDriver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # 设置页面加载超时时间
        driver.set_page_load_timeout(60)
        driver.implicitly_wait(5)
        
        logger.info("Chrome 驱动初始化成功")
        return driver
    except Exception as e:
        logger.error(f"Chrome 驱动初始化失败: {e}")
        raise


def save_page_source(driver: webdriver.Chrome, filename: str = "page_debug.html"):
    """保存当前页面源码用于调试"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        logger.info(f"页面源码已保存到: {filename}")
    except Exception as e:
        logger.warning(f"保存页面源码失败: {e}")


def debug_find_inputs(driver: webdriver.Chrome):
    """调试函数:列出页面上所有输入框"""
    try:
        all_inputs = driver.find_elements(By.TAG_NAME, "input")
        logger.info(f"=== 页面调试信息 ===")
        logger.info(f"发现 {len(all_inputs)} 个输入框:")
        
        for i, inp in enumerate(all_inputs):
            input_type = inp.get_attribute("type") or "text"
            input_name = inp.get_attribute("name") or "(无name)"
            input_id = inp.get_attribute("id") or "(无id)"
            input_placeholder = inp.get_attribute("placeholder") or "(无placeholder)"
            
            logger.info(f"  [{i+1}] type={input_type}, name={input_name}, id={input_id}, placeholder={input_placeholder}")
        
        logger.info("===================")
    except Exception as e:
        logger.warning(f"调试信息获取失败: {e}")


def wait_element(
    driver: webdriver.Chrome, 
    by: By, 
    value: str, 
    timeout: int = 15
) -> Optional[webdriver.remote.webelement.WebElement]:
    """封装显式等待,等待元素加载完成并返回"""
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )
        return element
    except TimeoutException:
        return None


def find_element_flexible(driver: webdriver.Chrome, element_type: str) -> Optional[webdriver.remote.webelement.WebElement]:
    """
    灵活查找元素,支持多种策略
    :param element_type: 元素类型 (first_name, last_name, email, password, checkbox, submit)
    """
    strategies = {
        "first_name": [
            (By.NAME, "first_name"),
            (By.ID, "first_name"),
            (By.CSS_SELECTOR, "input[placeholder*='First']"),
            (By.CSS_SELECTOR, "input[placeholder*='first']"),
            (By.XPATH, "//label[contains(text(), 'First')]/following::input[1]"),
            (By.XPATH, "//label[contains(text(), 'first')]/following::input[1]"),
            (By.XPATH, "(//input[@type='text'])[1]"),  # 第一个文本输入框
        ],
        "last_name": [
            (By.NAME, "last_name"),
            (By.ID, "last_name"),
            (By.CSS_SELECTOR, "input[placeholder*='Last']"),
            (By.CSS_SELECTOR, "input[placeholder*='last']"),
            (By.XPATH, "//label[contains(text(), 'Last')]/following::input[1]"),
            (By.XPATH, "//label[contains(text(), 'last')]/following::input[1]"),
            (By.XPATH, "(//input[@type='text'])[2]"),  # 第二个文本输入框
        ],
        "email": [
            (By.NAME, "email"),
            (By.ID, "email"),
            (By.CSS_SELECTOR, "input[type='email']"),
            (By.CSS_SELECTOR, "input[placeholder*='Email']"),
            (By.CSS_SELECTOR, "input[placeholder*='email']"),
            (By.XPATH, "//label[contains(text(), 'Email')]/following::input[1]"),
        ],
        "password": [
            (By.NAME, "password"),
            (By.ID, "password"),
            (By.CSS_SELECTOR, "input[type='password']"),
            (By.CSS_SELECTOR, "input[placeholder*='Password']"),
            (By.CSS_SELECTOR, "input[placeholder*='password']"),
            (By.XPATH, "//label[contains(text(), 'Password')]/following::input[1]"),
        ],
        "checkbox": [
            (By.CSS_SELECTOR, "input[type='checkbox']"),
            (By.XPATH, "//input[@type='checkbox']"),
        ],
        "submit": [
            (By.XPATH, "//button[contains(text(), 'CREATE ACCOUNT')]"),
            (By.XPATH, "//button[contains(text(), 'Create Account')]"),
            (By.XPATH, "//button[contains(text(), 'CONTINUE')]"),
            (By.XPATH, "//button[contains(text(), 'Continue')]"),
            (By.XPATH, "//button[contains(text(), 'Sign Up')]"),
            (By.XPATH, "//button[contains(text(), 'SIGN UP')]"),
            (By.CSS_SELECTOR, "button[type='submit']"),
            (By.XPATH, "//input[@type='submit']"),
            (By.XPATH, "//button[contains(@class, 'submit')]"),
        ]
    }
    
    if element_type not in strategies:
        logger.error(f"未知的元素类型: {element_type}")
        return None
    
    for by, value in strategies[element_type]:
        try:
            element = wait_element(driver, by, value, timeout=8)
            if element and element.is_displayed():
                logger.info(f"✓ 成功定位 {element_type}: {by}={value}")
                return element
        except Exception as e:
            continue
    
    logger.error(f"✗ 无法定位 {element_type}")
    return None


def click_sign_up_button(driver: webdriver.Chrome) -> bool:
    """点击 BASIC 套餐的 SIGN UP 按钮"""
    logger.info("正在查找并点击 SIGN UP 按钮")
    
    strategies = [
        # 方案1: 直接查找所有 SIGN UP 按钮(取最后一个)
        (By.XPATH, "(//button[contains(text(), 'SIGN UP')])[last()]"),
        # 方案2: 查找 BASIC 区域的按钮
        (By.XPATH, "//div[contains(text(), 'BASIC')]//following::button[contains(text(), 'SIGN UP')][1]"),
        # 方案3: 查找包含 "Ad-supported" 的区域
        (By.XPATH, "//div[contains(text(), 'Ad-supported')]//following::button[1]"),
        # 方案4: 查找所有 SIGN UP 并取第三个(PRO/ULTRA/BASIC)
        (By.XPATH, "(//button[contains(text(), 'SIGN UP')])[3]"),
    ]
    
    for by, value in strategies:
        try:
            button = wait_element(driver, by, value, timeout=10)
            if button:
                button.click()
                logger.info("✓ 成功点击 SIGN UP 按钮")
                time.sleep(3)  # 等待页面跳转
                return True
        except Exception as e:
            logger.debug(f"点击策略失败: {e}")
            continue
    
    return False


def register_one_account(email: str, password: str, ref_link: str) -> bool:
    """注册单个 MediaFire 账号"""
    driver: Optional[webdriver.Chrome] = None
    
    try:
        logger.info(f"开始注册账号: {email}")
        driver = create_driver()
        
        # ========== 步骤1: 访问邀请链接 ==========
        logger.info(f"正在访问邀请链接: {ref_link}")
        driver.get(ref_link)
        time.sleep(4)
        
        logger.info(f"当前 URL: {driver.current_url}")
        
        # ========== 步骤2: 检测并点击 SIGN UP ==========
        # 检查是否在套餐选择页面
        if "upgrade" in driver.current_url.lower():
            logger.info("检测到套餐选择页面")
            
            # 保存页面源码用于调试
            save_page_source(driver, f"page_upgrade_{int(time.time())}.html")
            
            # 尝试点击 SIGN UP
            if click_sign_up_button(driver):
                time.sleep(3)
                logger.info(f"点击后 URL: {driver.current_url}")
            else:
                logger.warning("无法点击 SIGN UP,尝试构造注册链接")
                # 直接构造注册 URL
                if "?" in ref_link:
                    base_url = ref_link.split("?")[0]
                    params = ref_link.split("?")[1]
                    registration_url = f"{base_url.replace('/upgrade/', '/upgrade/registration.php')}?pid=free&{params}"
                else:
                    registration_url = f"{ref_link}?pid=free"
                
                logger.info(f"尝试直接访问: {registration_url}")
                driver.get(registration_url)
                time.sleep(3)
        
        # ========== 步骤3: 填写注册表单 ==========
        logger.info(f"准备填写表单,当前 URL: {driver.current_url}")
        
        # 保存页面源码和截图用于调试
        save_page_source(driver, f"page_form_{int(time.time())}.html")
        driver.save_screenshot(f"screenshot_form_{int(time.time())}.png")
        
        # 输出调试信息
        debug_find_inputs(driver)
        
        # 等待页面完全加载
        time.sleep(2)
        
        # 定位表单元素
        first_name_input = find_element_flexible(driver, "first_name")
        if not first_name_input:
            logger.error("无法定位 First Name 输入框")
            return False
        
        last_name_input = find_element_flexible(driver, "last_name")
        if not last_name_input:
            logger.error("无法定位 Last Name 输入框")
            return False
        
        email_input = find_element_flexible(driver, "email")
        if not email_input:
            logger.error("无法定位邮箱输入框")
            return False
        
        password_input = find_element_flexible(driver, "password")
        if not password_input:
            logger.error("无法定位密码输入框")
            return False
        
        # 生成随机姓名
        first_name, last_name = generate_random_name()
        logger.info(f"填写信息: {first_name} {last_name} / {email}")
        
        # 填写表单
        try:
            first_name_input.clear()
            first_name_input.send_keys(first_name)
            time.sleep(0.8)
            
            last_name_input.clear()
            last_name_input.send_keys(last_name)
            time.sleep(0.8)
            
            email_input.clear()
            email_input.send_keys(email)
            time.sleep(0.8)
            
            password_input.clear()
            password_input.send_keys(password)
            time.sleep(0.8)
            
            logger.info("✓ 表单填写完成")
        except Exception as e:
            logger.error(f"填写表单时出错: {e}")
            return False
        
        # 勾选同意条款
        checkbox = find_element_flexible(driver, "checkbox")
        if checkbox:
            try:
                if not checkbox.is_selected():
                    checkbox.click()
                    logger.info("✓ 已勾选服务条款")
                    time.sleep(0.5)
            except Exception as e:
                logger.warning(f"勾选条款失败: {e}")
        
        # 点击提交按钮
        submit_btn = find_element_flexible(driver, "submit")
        if not submit_btn:
            logger.error("无法定位提交按钮")
            return False
        
        logger.info("点击提交按钮")
        submit_btn.click()
        
        # ========== 步骤4: 等待注册结果 ==========
        logger.info("等待注册结果...")
        try:
            WebDriverWait(driver, 40).until(
                EC.any_of(
                    EC.url_contains("myfiles"),
                    EC.url_contains("dashboard"),
                    EC.url_contains("welcome"),
                    EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'Welcome')]")),
                    EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'Success')]")),
                )
            )
            
            final_url = driver.current_url
            logger.info(f"注册成功! 最终 URL: {final_url}")
            logger.info(f"✓ 账号 {email} 注册完成")
            return True
            
        except TimeoutException:
            final_url = driver.current_url
            logger.info(f"超时,最终 URL: {final_url}")
            
            # 检查是否需要邮箱验证
            page_text = driver.page_source.lower()
            if any(keyword in page_text for keyword in ["verify", "verification", "confirmation", "check your email"]):
                logger.warning(f"⚠ 账号 {email} 已注册,需要邮箱验证")
                return True
            
            # 检查错误信息
            try:
                error_elements = driver.find_elements(By.XPATH, "//*[contains(@class, 'error')]")
                if error_elements:
                    error_msg = error_elements[0].text
                    logger.error(f"注册错误: {error_msg}")
            except:
                pass
            
            logger.error(f"注册失败: {email}")
            driver.save_screenshot(f"error_timeout_{int(time.time())}.png")
            return False
    
    except Exception as e:
        logger.error(f"✗ 注册异常: {email} - {str(e)}", exc_info=True)
        
        if driver:
            try:
                driver.save_screenshot(f"error_exception_{int(time.time())}.png")
                save_page_source(driver, f"error_exception_{int(time.time())}.html")
            except:
                pass
        
        return False
    
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass


def validate_email(email: str) -> bool:
    """邮箱格式验证"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def main() -> None:
    """主函数"""
    logger.info("=" * 60)
    logger.info("MediaFire 自动注册脚本启动")
    logger.info("=" * 60)
    
    ref_link = os.getenv("MEDIAFIRE_REF_LINK", "").strip()
    password = os.getenv("MEDIAFIRE_PASSWORD", "").strip()
    email_list_raw = os.getenv("EMAIL_LIST", "").strip()
    
    if not ref_link or not password or not email_list_raw:
        logger.error("必需的环境变量未设置")
        raise RuntimeError("请设置 MEDIAFIRE_REF_LINK, MEDIAFIRE_PASSWORD, EMAIL_LIST")
    
    emails = [email.strip() for email in email_list_raw.split(",") if email.strip()]
    valid_emails = [e for e in emails if validate_email(e)]
    
    if not valid_emails:
        logger.error("没有有效邮箱")
        raise RuntimeError("EMAIL_LIST 中没有有效邮箱")
    
    logger.info(f"配置信息:")
    logger.info(f"  邀请链接: {ref_link}")
    logger.info(f"  密码长度: {len(password)} 字符")
    logger.info(f"  有效邮箱: {len(valid_emails)} 个")
    logger.info("-" * 60)
    
    success_count = 0
    failed_emails = []
    
    for index, email in enumerate(valid_emails, 1):
        logger.info(f"进度: [{index}/{len(valid_emails)}]")
        
        if register_one_account(email, password, ref_link):
            success_count += 1
        else:
            failed_emails.append(email)
        
        if index < len(valid_emails):
            wait_time = random.randint(8, 15)
            logger.info(f"等待 {wait_time} 秒...")
            time.sleep(wait_time)
    
    logger.info("=" * 60)
    logger.info(f"任务完成: 成功 {success_count}/{len(valid_emails)}")
    if failed_emails:
        logger.info(f"失败邮箱: {', '.join(failed_emails)}")
    logger.info("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n程序被用户中断")
    except Exception as e:
        logger.error(f"程序出错: {e}", exc_info=True)
        raise
