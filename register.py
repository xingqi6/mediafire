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
        logger.debug(f"等待元素超时: {by}={value}")
        return None


def wait_and_click(
    driver: webdriver.Chrome,
    by: By,
    value: str,
    timeout: int = 20
) -> bool:
    """等待元素可点击并点击"""
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((by, value))
        )
        element.click()
        return True
    except TimeoutException:
        logger.debug(f"等待可点击元素超时: {by}={value}")
        return False


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
            element = wait_element(driver, by, value, timeout=10)
            if element:
                logger.debug(f"成功定位元素: {by}={value}")
                return element
        except Exception as e:
            logger.debug(f"定位策略失败 {by}={value}: {e}")
            continue
    return None


def click_sign_up_button(driver: webdriver.Chrome) -> bool:
    """
    点击 BASIC 套餐的 SIGN UP 按钮
    :return: 点击成功返回 True
    """
    logger.info("正在查找 BASIC 套餐的 SIGN UP 按钮")
    
    # 多种定位策略
    strategies = [
        # 通过按钮文本定位
        (By.XPATH, "//button[contains(text(), 'SIGN UP')]"),
        # 通过包含 "Ad-supported" 的区域内的按钮
        (By.XPATH, "//div[contains(text(), 'Ad-supported')]//ancestor::div[contains(@class, 'plan') or contains(@class, 'card')]//button"),
        # 通过 BASIC 相关文本定位
        (By.XPATH, "//h3[contains(text(), 'BASIC')]//following::button[1]"),
        # 直接查找所有 SIGN UP 按钮(取最后一个,通常是 BASIC)
        (By.XPATH, "(//button[contains(text(), 'SIGN UP')])[last()]"),
    ]
    
    for by, value in strategies:
        try:
            if wait_and_click(driver, by, value, timeout=10):
                logger.info("✓ 成功点击 SIGN UP 按钮")
                time.sleep(2)  # 等待页面跳转
                return True
        except Exception as e:
            logger.debug(f"点击策略失败 {by}={value}: {e}")
            continue
    
    logger.error("✗ 无法找到 SIGN UP 按钮")
    return False


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
        
        # ========== 第一步: 访问邀请链接并选择套餐 ==========
        logger.info(f"正在访问邀请链接: {ref_link}")
        driver.get(ref_link)
        time.sleep(3)  # 等待页面完全加载
        
        # 检查是否在套餐选择页面
        if "upgrade" in driver.current_url or "Choose the plan" in driver.page_source:
            logger.info("检测到套餐选择页面,准备点击 BASIC 套餐")
            
            # 点击 BASIC 套餐的 SIGN UP 按钮
            if not click_sign_up_button(driver):
                logger.error("无法点击 SIGN UP 按钮,尝试继续...")
        
        # ========== 第二步: 填写注册表单 ==========
        time.sleep(3)  # 等待注册表单加载
        logger.info(f"当前页面 URL: {driver.current_url}")
        
        # 检查是否到达注册表单页面
        if "registration" not in driver.current_url:
            logger.warning("未能跳转到注册页面,尝试直接访问注册链接")
            # 构造注册链接
            if "?" in ref_link:
                registration_url = ref_link.replace("/upgrade/", "/upgrade/registration.php/") + "&pid=free"
            else:
                registration_url = ref_link.replace("/upgrade/", "/upgrade/registration.php/") + "?pid=free"
            
            logger.info(f"尝试访问: {registration_url}")
            driver.get(registration_url)
            time.sleep(3)
        
        # 定位表单元素 - First Name
        first_name_input = safe_find_element(driver, [
            (By.NAME, "first_name"),
            (By.ID, "first_name"),
            (By.XPATH, "//input[@placeholder='First Name']"),
            (By.CSS_SELECTOR, "input[type='text']")
        ])
        
        if not first_name_input:
            logger.error("无法定位 First Name 输入框")
            return False
        
        # 定位表单元素 - Last Name
        last_name_input = safe_find_element(driver, [
            (By.NAME, "last_name"),
            (By.ID, "last_name"),
            (By.XPATH, "//input[@placeholder='Last Name']"),
        ])
        
        if not last_name_input:
            logger.error("无法定位 Last Name 输入框")
            return False
        
        # 定位表单元素 - Email
        email_input = safe_find_element(driver, [
            (By.NAME, "email"),
            (By.ID, "email"),
            (By.CSS_SELECTOR, "input[type='email']"),
            (By.XPATH, "//input[@placeholder='Email']")
        ])
        
        if not email_input:
            logger.error("无法定位邮箱输入框")
            return False
        
        # 定位表单元素 - Password
        password_input = safe_find_element(driver, [
            (By.NAME, "password"),
            (By.ID, "password"),
            (By.CSS_SELECTOR, "input[type='password']"),
            (By.XPATH, "//input[@placeholder='Password']")
        ])
        
        if not password_input:
            logger.error("无法定位密码输入框")
            return False
        
        # 生成随机姓名
        full_name = generate_random_name()
        first_name, last_name = full_name.split()
        
        logger.info(f"填写注册信息: 姓名={full_name}, 邮箱={email}")
        
        # 填写表单
        first_name_input.clear()
        first_name_input.send_keys(first_name)
        time.sleep(0.5)
        
        last_name_input.clear()
        last_name_input.send_keys(last_name)
        time.sleep(0.5)
        
        email_input.clear()
        email_input.send_keys(email)
        time.sleep(0.5)
        
        password_input.clear()
        password_input.send_keys(password)
        time.sleep(0.5)
        
        # 勾选同意条款复选框
        try:
            checkbox = safe_find_element(driver, [
                (By.XPATH, "//input[@type='checkbox']"),
                (By.CSS_SELECTOR, "input[type='checkbox']")
            ])
            if checkbox and not checkbox.is_selected():
                checkbox.click()
                logger.info("已勾选服务条款")
                time.sleep(0.5)
        except Exception as e:
            logger.warning(f"勾选条款复选框失败: {e}")
        
        # 点击提交按钮
        submit_btn = safe_find_element(driver, [
            (By.XPATH, "//button[contains(text(), 'CREATE ACCOUNT')]"),
            (By.XPATH, "//button[contains(text(), 'CONTINUE')]"),
            (By.CSS_SELECTOR, "button[type='submit']"),
            (By.XPATH, "//input[@type='submit']")
        ])
        
        if not submit_btn:
            logger.error("无法定位提交按钮")
            return False
        
        logger.info("点击注册按钮")
        submit_btn.click()
        
        # ========== 第三步: 等待注册结果 ==========
        logger.info("等待注册结果...")
        try:
            WebDriverWait(driver, 45).until(
                EC.any_of(
                    EC.url_contains("myfiles"),
                    EC.url_contains("dashboard"),
                    EC.url_contains("welcome"),
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
                return True
            
            # 检查是否有错误提示
            error_elements = driver.find_elements(By.XPATH, "//*[contains(@class, 'error') or contains(text(), 'Error')]")
            if error_elements:
                error_msg = error_elements[0].text
                logger.error(f"注册失败: {email} - 错误信息: {error_msg}")
            else:
                logger.error(f"注册超时: {email} - 未检测到成功标识")
                logger.info(f"最终页面 URL: {driver.current_url}")
            
            return False
    
    except Exception as e:
        logger.error(f"✗ 注册失败: {email} - 异常: {str(e)}")
        
        # 失败时保存截图
        try:
            if driver:
                screenshot_name = f"error_{email.replace('@', '_at_')}_{int(time.time())}.png"
                driver.save_screenshot(screenshot_name)
                logger.info(f"错误截图已保存: {screenshot_name}")
        except Exception as screenshot_err:
            logger.warning(f"保存错误截图失败: {str(screenshot_err)}")
        
        return False
    
    finally:
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
