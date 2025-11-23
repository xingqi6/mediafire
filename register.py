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
    return f"{first_name} {last_name}"


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
    
    try:
        # 自动安装对应版本 ChromeDriver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # 设置页面加载超时时间
        driver.set_page_load_timeout(60)
        driver.implicitly_wait(10)
        
        logger.info("Chrome 驱动初始化成功")
        return driver
    except Exception as e:
        logger.error(f"Chrome 驱动初始化失败: {e}")
        raise


def wait_element(
    driver: webdriver.Chrome, 
    by: By, 
    value: str, 
    timeout: int = 20
) -> Optional[webdriver.remote.webelement.WebElement]:
    """
    封装显式等待,等待元素加载完成并返回
    :return: 找到元素返回元素对象,超时返回 None
    """
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )
        return element
    except TimeoutException:
        logger.warning(f"等待元素超时: {by}={value}")
        return None


def safe_find_element(
    driver: webdriver.Chrome, 
    strategies: List[Tuple[By, str]]
) -> Optional[webdriver.remote.webelement.WebElement]:
    """
    使用多种策略定位元素,提高稳定性
    :param strategies: 定位策略列表 [(By.ID, 'xxx'), (By.NAME, 'yyy')]
    :return: 找到的元素或 None
    """
    for by, value in strategies:
        try:
            element = wait_element(driver, by, value, timeout=15)
            if element:
                logger.debug(f"成功定位元素: {by}={value}")
                return element
        except Exception as e:
            logger.debug(f"定位策略失败 {by}={value}: {e}")
            continue
    return None


def register_one_account(email: str, password: str, ref_link: str) -> bool:
    """
    注册单个 MediaFire 账号
    :param email: 注册邮箱
    :param password: 账号密码
    :param ref_link: 邀请链接
    :return: 注册成功返回 True,失败返回 False
    """
    driver: Optional[webdriver.Chrome] = None
    
    try:
        logger.info(f"开始注册账号: {email}")
        driver = create_driver()
        
        # 打开邀请注册链接
        logger.info(f"正在访问注册页面: {ref_link}")
        driver.get(ref_link)
        time.sleep(3)  # 等待页面完全加载
        
        # 多策略定位邮箱输入框
        email_input = safe_find_element(driver, [
            (By.NAME, "email"),
            (By.ID, "email"),
            (By.CSS_SELECTOR, "input[type='email']"),
            (By.XPATH, "//input[@placeholder='Email' or @placeholder='email']")
        ])
        
        if not email_input:
            logger.error("无法定位邮箱输入框")
            return False
        
        # 多策略定位姓名输入框
        name_input = safe_find_element(driver, [
            (By.NAME, "full_name"),
            (By.NAME, "name"),
            (By.ID, "full_name"),
            (By.XPATH, "//input[@placeholder='Full Name' or @placeholder='Name']")
        ])
        
        if not name_input:
            logger.error("无法定位姓名输入框")
            return False
        
        # 多策略定位密码输入框
        password_input = safe_find_element(driver, [
            (By.NAME, "password"),
            (By.ID, "password"),
            (By.CSS_SELECTOR, "input[type='password']"),
            (By.XPATH, "//input[@placeholder='Password' or @placeholder='password']")
        ])
        
        if not password_input:
            logger.error("无法定位密码输入框")
            return False
        
        # 生成并填写随机全名
        full_name = generate_random_name()
        logger.info(f"填写注册信息: 姓名={full_name}, 邮箱={email}")
        
        email_input.clear()
        email_input.send_keys(email)
        time.sleep(0.5)
        
        name_input.clear()
        name_input.send_keys(full_name)
        time.sleep(0.5)
        
        password_input.clear()
        password_input.send_keys(password)
        time.sleep(0.5)
        
        # 多策略定位提交按钮
        submit_btn = safe_find_element(driver, [
            (By.CSS_SELECTOR, "button[type='submit']"),
            (By.XPATH, "//button[contains(text(), 'Sign Up') or contains(text(), 'Register')]"),
            (By.XPATH, "//input[@type='submit']")
        ])
        
        if not submit_btn:
            logger.error("无法定位提交按钮")
            return False
        
        logger.info("点击注册按钮")
        submit_btn.click()
        
        # 等待注册结果(多种成功标识)
        logger.info("等待注册结果...")
        try:
            WebDriverWait(driver, 45).until(
                EC.any_of(
                    EC.url_contains("myfiles"),  # 跳转到文件页面
                    EC.url_contains("dashboard"),  # 跳转到仪表板
                    EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'Welcome') or contains(text(),'welcome')]")),
                    EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'Success') or contains(text(),'success')]"))
                )
            )
            logger.info(f"✓ 注册成功: {email}")
            return True
            
        except TimeoutException:
            # 检查是否需要邮箱验证
            if driver.find_elements(By.XPATH, "//*[contains(text(),'verify') or contains(text(),'Verify') or contains(text(),'confirmation')]"):
                logger.warning(f"⚠ 账号 {email} 需要邮箱验证,请手动完成验证")
                return True  # 虽需验证但注册请求已提交
            
            # 检查是否有错误提示
            error_elements = driver.find_elements(By.XPATH, "//*[contains(@class, 'error') or contains(text(), 'Error')]")
            if error_elements:
                error_msg = error_elements[0].text
                logger.error(f"注册失败: {email} - 错误信息: {error_msg}")
            else:
                logger.error(f"注册超时: {email} - 未检测到成功标识")
            
            return False
    
    except Exception as e:
        logger.error(f"✗ 注册失败: {email} - 异常: {str(e)}")
        
        # 失败时保存截图用于调试
        try:
            if driver:
                screenshot_name = f"error_{email.replace('@', '_at_')}_{int(time.time())}.png"
                driver.save_screenshot(screenshot_name)
                logger.info(f"错误截图已保存: {screenshot_name}")
        except Exception as screenshot_err:
            logger.warning(f"保存错误截图失败: {str(screenshot_err)}")
        
        return False
    
    finally:
        # 确保驱动正常退出
        if driver:
            try:
                driver.quit()
                logger.debug("浏览器驱动已关闭")
            except Exception as e:
                logger.warning(f"关闭浏览器驱动时出错: {e}")


def validate_email(email: str) -> bool:
    """简单的邮箱格式验证"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def main() -> None:
    """主函数: 从环境变量读取配置,批量注册账号"""
    logger.info("=" * 60)
    logger.info("MediaFire 自动注册脚本启动")
    logger.info("=" * 60)
    
    # 从环境变量获取配置
    ref_link = os.getenv("MEDIAFIRE_REF_LINK", "").strip()
    password = os.getenv("MEDIAFIRE_PASSWORD", "").strip()
    email_list_raw = os.getenv("EMAIL_LIST", "").strip()
    
    # 验证配置完整性
    if not ref_link:
        logger.error("环境变量 MEDIAFIRE_REF_LINK 未设置(必填)")
        raise RuntimeError("环境变量 MEDIAFIRE_REF_LINK 未设置")
    
    if not password:
        logger.error("环境变量 MEDIAFIRE_PASSWORD 未设置(必填)")
        raise RuntimeError("环境变量 MEDIAFIRE_PASSWORD 未设置")
    
    if not email_list_raw:
        logger.error("环境变量 EMAIL_LIST 未设置(必填)")
        raise RuntimeError("环境变量 EMAIL_LIST 未设置")
    
    # 解析邮箱列表
    emails = [email.strip() for email in email_list_raw.split(",") if email.strip()]
    
    # 验证邮箱格式
    valid_emails = []
    for email in emails:
        if validate_email(email):
            valid_emails.append(email)
        else:
            logger.warning(f"邮箱格式无效,已跳过: {email}")
    
    if not valid_emails:
        logger.error("EMAIL_LIST 中没有有效邮箱")
        raise RuntimeError("EMAIL_LIST 中没有有效邮箱")
    
    logger.info(f"配置信息:")
    logger.info(f"  邀请链接: {ref_link}")
    logger.info(f"  密码长度: {len(password)} 字符")
    logger.info(f"  有效邮箱: {len(valid_emails)} 个")
    logger.info("-" * 60)
    
    # 批量注册
    success_count = 0
    failed_emails = []
    
    for index, email in enumerate(valid_emails, 1):
        logger.info(f"进度: [{index}/{len(valid_emails)}]")
        
        if register_one_account(email, password, ref_link):
            success_count += 1
        else:
            failed_emails.append(email)
        
        # 注册间隔(避免触发风控)
        if index < len(valid_emails):
            wait_time = random.randint(5, 10)
            logger.info(f"等待 {wait_time} 秒后继续...")
            time.sleep(wait_time)
    
    # 输出任务结果
    logger.info("=" * 60)
    logger.info(f"批量注册任务完成")
    logger.info(f"  成功: {success_count}/{len(valid_emails)} 个账号")
    logger.info(f"  失败: {len(failed_emails)} 个账号")
    
    if failed_emails:
        logger.info(f"失败邮箱列表:")
        for email in failed_emails:
            logger.info(f"  - {email}")
    
    logger.info("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n程序被用户中断")
    except Exception as e:
        logger.error(f"程序执行出错: {e}", exc_info=True)
        raise
