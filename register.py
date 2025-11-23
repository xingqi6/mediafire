import os
import random
import string
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


def log(msg: str) -> None:
    """简单日志输出"""
    print(f"[MEDIAFIRE-REGISTER] {msg}", flush=True)


def generate_random_name() -> str:
    """生成随机名称"""
    first = ''.join(random.choices(string.ascii_letters, k=6))
    last = ''.join(random.choices(string.ascii_letters, k=7))
    return f"{first} {last}"


def create_driver() -> webdriver.Chrome:
    """创建适配 GitHub Actions / Linux 的无头 Chrome"""
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1280,720")

    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options,
    )
    driver.set_page_load_timeout(30)
    return driver


def wait(driver: webdriver.Chrome, by, value: str, timeout: int = 20):
    """封装显式等待"""
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((by, value))
    )


def register_one_account(email: str, password: str, ref_link: str) -> bool:
    """注册单个 MediaFire 账号，成功返回 True"""
    driver = None
    try:
        log(f"开始注册邮箱：{email}")
        driver = create_driver()

        # 打开邀请链接
        driver.get(ref_link)

        # 下面几行元素定位需要你根据实际注册页面的 name/id 做微调
        email_input = wait(driver, By.NAME, "email", timeout=30)
        name_input = wait(driver, By.NAME, "full_name", timeout=30)
        password_input = wait(driver, By.NAME, "password", timeout=30)

        full_name = generate_random_name()

        email_input.clear()
        email_input.send_keys(email)

        name_input.clear()
        name_input.send_keys(full_name)

        password_input.clear()
        password_input.send_keys(password)

        # 提交按钮：如有不同，请改 CSS 选择器
        submit_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit_btn.click()

        # 等待注册成功后的页面/提示
        WebDriverWait(driver, 40).until(
            EC.any_of(
                EC.url_contains("myfiles"),
                EC.presence_of_element_located(
                    (By.XPATH, "//*[contains(text(),'Welcome')]")
                ),
            )
        )

        log(f"注册成功：{email}")
        return True

    except Exception as e:
        log(f"注册失败：{email}，错误：{e}")
        try:
            if driver:
                ts = int(time.time())
                driver.save_screenshot(f"error_{ts}.png")
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
