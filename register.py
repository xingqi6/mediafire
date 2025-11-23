import os
import random
import string
import time
from typing import Optional

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


def log(msg: str) -> None:
    """简单日志输出，包含时间戳和模块标识"""
    print(f"[MEDIAFIRE-REGISTER] {time.strftime('%Y-%m-%d %H:%M:%S')} - {msg}", flush=True)


def generate_random_name() -> str:
    """生成随机全名（6位名 + 7位姓）"""
    first_name = ''.join(random.choices(string.ascii_letters, k=6))
    last_name = ''.join(random.choices(string.ascii_letters, k=7))
    return f"{first_name} {last_name}"


def create_driver() -> webdriver.Chrome:
    """创建适配 GitHub Actions/Linux 的无头 Chrome 驱动"""
    chrome_options = Options()
    # 无头模式配置
    chrome_options.add_argument("--headless=new")
    # Linux 环境兼容配置
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # 禁用 GPU（无头模式无需）
    chrome_options.add_argument("--disable-gpu")
    # 设置窗口大小（模拟正常浏览）
    chrome_options.add_argument("--window-size=1280,720")
    # 规避反爬检测
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)

    # 自动安装对应版本 ChromeDriver
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options,
    )
    # 设置页面加载超时时间
    driver.set_page_load_timeout(30)
    return driver


def wait_element(driver: webdriver.Chrome, by: By, value: str, timeout: int = 20) -> webdriver.remote.webelement.WebElement:
    """封装显式等待，等待元素加载完成并返回"""
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((by, value)),
        message=f"超时未找到元素：{by}={value}"
    )


def register_one_account(email: str, password: str, ref_link: str) -> bool:
    """
    注册单个 MediaFire 账号
    :param email: 注册邮箱
    :param password: 账号密码
    :param ref_link: 邀请链接
    :return: 注册成功返回 True，失败返回 False
    """
    driver: Optional[webdriver.Chrome] = None
    try:
        log(f"开始注册账号：{email}")
        driver = create_driver()

        # 打开邀请注册链接
        driver.get(ref_link)

        # 定位并填写表单（需根据实际页面调整元素定位方式）
        email_input = wait_element(driver, By.NAME, "email", timeout=30)
        name_input = wait_element(driver, By.NAME, "full_name", timeout=30)
        password_input = wait_element(driver, By.NAME, "password", timeout=30)

        # 生成并填写随机全名
        full_name = generate_random_name()
        email_input.clear()
        email_input.send_keys(email)
        name_input.clear()
        name_input.send_keys(full_name)
        password_input.clear()
        password_input.send_keys(password)

        # 定位并点击提交按钮（CSS 选择器需根据实际页面调整）
        submit_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit_btn.click()

        # 等待注册成功（两种成功标识：跳转到文件页面 或 出现欢迎提示）
        WebDriverWait(driver, 40).until(
            EC.any_of(
                EC.url_contains("myfiles"),  # 成功跳转文件页面
                EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'Welcome')]"))  # 出现欢迎文本
            ),
            message=f"注册超时：{email}"
        )

        log(f"注册成功：{email}")
        return True

    except Exception as e:
        log(f"注册失败：{email}，错误信息：{str(e)}")
        # 失败时保存截图用于调试
        try:
            if driver:
                screenshot_name = f"error_screenshot_{int(time.time())}.png"
                driver.save_screenshot(screenshot_name)
                log(f"错误截图已保存：{screenshot_name}")
        except Exception as screenshot_err:
            log(f"保存错误截图失败：{str(screenshot_err)}")
        return False

    finally:
        # 确保驱动正常退出
        if driver:
            driver.quit()


def main() -> None:
    """主函数：从环境变量读取配置，批量注册账号"""
    # 从环境变量获取配置（适合 CI/CD 环境使用）
    ref_link = os.getenv("MEDIAFIRE_REF_LINK", "").strip()
    password = os.getenv("MEDIAFIRE_PASSWORD", "").strip()
    email_list_raw = os.getenv("EMAIL_LIST", "").strip()

    # 验证配置完整性
    if not ref_link:
        raise RuntimeError("环境变量 MEDIAFIRE_REF_LINK 未设置（必填）")
    if not password:
        raise RuntimeError("环境变量 MEDIAFIRE_PASSWORD 未设置（必填）")
    if not email_list_raw:
        raise RuntimeError("环境变量 EMAIL_LIST 未设置（必填）")

    # 解析邮箱列表（格式：邮箱1,邮箱2,邮箱3）
    emails = [email.strip() for email in email_list_raw.split(",") if email.strip()]
    if not emails:
        raise RuntimeError("EMAIL_LIST 中未包含有效邮箱")

    log(f"批量注册任务开始，共需注册 {len(emails)} 个账号")
    success_count = 0

    # 逐个注册账号（添加间隔避免请求过快）
    for email in emails:
        if register_one_account(email, password, ref_link):
            success_count += 1
        time.sleep(5)  # 注册间隔：5秒

    # 输出任务结果
    log(f"批量注册任务完成：成功 {success_count}/{len(emails)} 个账号")


if __name__ == "__main__":
    main()
    finally:
        if driver:
            driver.quit()


def main():
    ref_link = os.getenv("MEDIAFIRE_REF_LINK", "").strip()
    password = os.getenv("MEDIAFIRE_PASSWORD", "").strip()
    email_list_raw = os.getenv("EMAIL_LIST", "").strip()

    if not ref_link:
        raise RuntimeError("环境变量 MEDIAFIRE_REF_LINK 未设置")
    if not password:
        raise RuntimeError("环境变量 MEDIAFIRE_PASSWORD 未设置")
    if not email_list_raw:
        raise RuntimeError("环境变量 EMAIL_LIST 未设置")

    emails = [e.strip() for e in email_list_raw.split(",") if e.strip()]
    if not emails:
        raise RuntimeError("EMAIL_LIST 中没有有效邮箱")

    log(f"即将注册 {len(emails)} 个账号")
    success = 0

    for email in emails:
        ok = register_one_account(email, password, ref_link)
        if ok:
            success += 1
        time.sleep(5)

    log(f"全部完成：成功 {success}/{len(emails)}")


if __name__ == "__main__":
    main()        return False

    finally:
        if driver:
            driver.quit()


def main():
    ref_link = os.getenv("MEDIAFIRE_REF_LINK", "").strip()
    password = os.getenv("MEDIAFIRE_PASSWORD", "").strip()
    email_list_raw = os.getenv("EMAIL_LIST", "").strip()

    if not ref_link:
        raise RuntimeError("环境变量 MEDIAFIRE_REF_LINK 未设置")
    if not password:
        raise RuntimeError("环境变量 MEDIAFIRE_PASSWORD 未设置")
    if not email_list_raw:
        raise RuntimeError("环境变量 EMAIL_LIST 未设置")

    emails = [e.strip() for e in email_list_raw.split(",") if e.strip()]
    if not emails:
        raise RuntimeError("EMAIL_LIST 中没有有效邮箱")

    log(f"即将注册 {len(emails)} 个账号")
    success = 0

    for email in emails:
        ok = register_one_account(email, password, ref_link)
        if ok:
            success += 1
        # 轻微延时，防止触发风控
        time.sleep(5)

    log(f"全部完成：成功 {success}/{len(emails)}")


if __name__ == "__main__":
    main()    finally:
        if driver:
            driver.quit()


def main():
    ref_link = os.getenv("MEDIAFIRE_REF_LINK", "").strip()
    password = os.getenv("MEDIAFIRE_PASSWORD", "").strip()
    email_list_raw = os.getenv("EMAIL_LIST", "").strip()

    if not ref_link:
        raise RuntimeError("环境变量 MEDIAFIRE_REF_LINK 未设置")
    if not password:
        raise RuntimeError("环境变量 MEDIAFIRE_PASSWORD 未设置")
    if not email_list_raw:
        raise RuntimeError("环境变量 EMAIL_LIST 未设置")

    emails = [e.strip() for e in email_list_raw.split(",") if e.strip()]
    if not emails:
        raise RuntimeError("EMAIL_LIST 中没有有效邮箱")

    log(f"即将注册 {len(emails)} 个账号")
    success = 0

    for email in emails:
        ok = register_one_account(email, password, ref_link)
        if ok:
            success += 1
        time.sleep(5)

    log(f"全部完成：成功 {success}/{len(emails)}")


if __name__ == "__main__":
    main()    if not ref_link:
        raise RuntimeError("环境变量 MEDIAFIRE_REF_LINK 未设置")
    if not password:
        raise RuntimeError("环境变量 MEDIAFIRE_PASSWORD 未设置")
    if not email_list_raw:
        raise RuntimeError("环境变量 EMAIL_LIST 未设置")

    emails = [e.strip() for e in email_list_raw.split(",") if e.strip()]
    if not emails:
        raise RuntimeError("EMAIL_LIST 中没有有效邮箱")

    log(f"即将注册 {len(emails)} 个账号")
    success = 0
    for email in emails:
        if register_one_account(email, password, ref_link):
            success += 1
        time.sleep(5)

    log(f"全部完成：成功 {success}/{len(emails)}")


if __name__ == "__main__":
    main()    except Exception as e:
        log(f"注册失败：{email}，错误：{e}")
        # 截图调试（在 GitHub Actions 的 artifacts 里可以看）
        try:
            if driver:
                ts = int(time.time())
                driver.save_screenshot(f"error_{email}_{ts}.png")
        except Exception:
            pass
        return False

    finally:
        if driver:
            driver.quit()


def main():
    ref_link = os.getenv("MEDIAFIRE_REF_LINK", "").strip()
    password = os.getenv("MEDIAFIRE_PASSWORD", "").strip()
    email_list_raw = os.getenv("EMAIL_LIST", "").strip()

    if not ref_link:
        raise RuntimeError("环境变量 MEDIAFIRE_REF_LINK 未设置")
    if not password:
        raise RuntimeError("环境变量 MEDIAFIRE_PASSWORD 未设置")
    if not email_list_raw:
        raise RuntimeError("环境变量 EMAIL_LIST 未设置")

    emails = [e.strip() for e in email_list_raw.split(",") if e.strip()]
    if not emails:
        raise RuntimeError("EMAIL_LIST 中没有有效邮箱")

    log(f"即将注册 {len(emails)} 个账号")
    success = 0

    for email in emails:
        ok = register_one_account(email, password, ref_link)
        if ok:
            success += 1
        # 可选：每个账号之间稍微停顿，避免触发风控
        time.sleep(5)

    log(f"全部完成：成功 {success}/{len(emails)}")


if __name__ == "__main__":
    main()
