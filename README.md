# MediaFire 自动注册脚本

本项目使用 **Python + Selenium + GitHub Actions** 自动化批量注册 MediaFire 账号。支持通过邀请链接注册，邮箱列表通过环境变量传入，密码统一配置。

---

## 功能

- 自动通过 MediaFire 邀请链接注册账号
- 邮箱列表支持批量注册
- 注册信息自动填写：
  - 名字随机生成
  - 邮箱从列表中读取
  - 密码统一配置
- 支持 GitHub Actions 自动执行
- 无头浏览器执行（无需显示 GUI）

---

## 项目结构

/mediafire-register
├── .github
│ └── workflows
│ └── register.yml # GitHub Actions 工作流
├── register.py # 自动注册脚本
├── requirements.txt # Python 依赖
├── README.md # 项目说明

---

## 环境变量配置

在 GitHub 仓库的 **Settings → Secrets → Actions** 中添加以下环境变量：

| 环境变量名              | 说明                          | 示例值 |
|------------------------|-------------------------------|--------|
| `MEDIAFIRE_REF_LINK`    | MediaFire 邀请链接             | `https://www.mediafire.com/?nnfhfnh` |
| `MEDIAFIRE_PASSWORD`    | 注册账号密码（统一）            | `your_password_here` |
| `EMAIL_LIST`            | 用逗号分隔的邮箱列表            | `email1@example.com,email2@example.com` |

---

## 安装依赖

在本地或 GitHub Actions 中执行：

```bash
pip install --upgrade pip
pip install -r requirements.txt
requirements.txt 示例：
selenium==4.5.0
webdriver-manager==3.5.0

GitHub Actions 配置

工作流文件：.github/workflows/register.yml
name: Register MediaFire Accounts

on:
  workflow_dispatch:   # 手动触发
  schedule:
    - cron: "0 0 * * *"   # 可选，每天自动触发

jobs:
  register_accounts:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v2

      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'

      - name: Install Google Chrome
        run: |
          sudo apt-get update
          sudo apt-get install -y wget curl unzip
          wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
          sudo dpkg -i google-chrome-stable_current_amd64.deb
          sudo apt-get -f install

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run registration script
        run: |
          python register.py
        env:
          MEDIAFIRE_REF_LINK: ${{ secrets.MEDIAFIRE_REF_LINK }}
          MEDIAFIRE_PASSWORD: ${{ secrets.MEDIAFIRE_PASSWORD }}
          EMAIL_LIST: ${{ secrets.EMAIL_LIST }}
···
使用方法

将项目上传到 GitHub 仓库

配置 GitHub Secrets（环境变量）

手动触发工作流或等待定时任务触发

脚本会自动循环邮箱列表进行注册

注意事项

chromedriver 版本兼容问题

建议在 GitHub Actions 中安装最新稳定版 Chrome

使用 webdriver-manager 自动下载对应版本的 chromedriver

邮箱验证

MediaFire 可能要求邮箱验证，此脚本未包含邮箱验证码处理，需要手动或自行实现
