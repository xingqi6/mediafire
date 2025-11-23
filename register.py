import os
import random
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager  # 使用 webdriver-manager 来自动下载 chromedriver

# 获取环境变量
mediafire_ref_link = os.getenv("MEDIAFIRE_REF_LINK")
mediafire_password = os.getenv("MEDIAFIRE_PASSWORD")
email_list = os.getenv("EMAIL_LIST").split(",")  # 获取邮箱列表

# 随机生成名字
def generate_random_name():
    first_names = ['John', 'Jane', 'Alex', 'Emily', 'Chris']
    last_names = ['Smith', 'Johnson', 'Brown', 'Davis', 'Miller']
    return random.choice(first_names) + " " + random.choice(last_names)

# 设置 Chrome 选项
options = Options()
options.headless = True  # 无头模式

# 如果有下载 chromedriver，使用本地路径
chromedriver_path = "/path/to/your/chromedriver"  # 修改为你上传的 chromedriver 路径
driver_service = Service(chromedriver_path)
driver = webdriver.Chrome(service=driver_service, options=options)

# 注册账号函数
def register_account(email):
    driver.get(mediafire_ref_link)
    
    # 随机填写名字
    name = generate_random_name()
    driver.find_element(By.NAME, "name").send_keys(name)

    # 填写邮箱
    driver.find_element(By.NAME, "email").send_keys(email)

    # 填写密码
    driver.find_element(By.NAME, "password").send_keys(mediafire_password)

    # 提交表单
    driver.find_element(By.NAME, "submit").click()
    time.sleep(5)  # 等待页面加载

# 循环处理邮箱列表
for email in email_list:
    register_account(email)

# 完成后关闭浏览器
driver.quit()
