#!/usr/bin/env python3
"""
调试辅助脚本 - 分析保存的 HTML 文件
用法: python debug_page.py page_form_xxx.html
"""

import sys
import re
from pathlib import Path


def analyze_html(html_file):
    """分析 HTML 文件,提取关键信息"""
    if not Path(html_file).exists():
        print(f"❌ 文件不存在: {html_file}")
        return
    
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("=" * 80)
    print(f"分析文件: {html_file}")
    print("=" * 80)
    
    # 检查是否有错误信息
    print("\n【1】检查错误信息:")
    error_patterns = [
        r'<div[^>]*class="[^"]*error[^"]*"[^>]*>(.*?)</div>',
        r'<span[^>]*class="[^"]*error[^"]*"[^>]*>(.*?)</span>',
        r'<p[^>]*class="[^"]*error[^"]*"[^>]*>(.*?)</p>',
    ]
    
    errors_found = []
    for pattern in error_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
        for match in matches:
            clean_text = re.sub(r'<[^>]+>', '', match).strip()
            if clean_text and len(clean_text) > 3:
                errors_found.append(clean_text)
    
    if errors_found:
        print("⚠️  发现错误信息:")
        for err in errors_found:
            print(f"   - {err}")
    else:
        print("✅ 未发现明显错误信息")
    
    # 检查是否有验证码
    print("\n【2】检查验证码:")
    captcha_keywords = ['recaptcha', 'captcha', 'g-recaptcha', 'hcaptcha']
    captcha_found = any(kw in content.lower() for kw in captcha_keywords)
    
    if captcha_found:
        print("⚠️  检测到验证码元素!")
        for kw in captcha_keywords:
            if kw in content.lower():
                print(f"   - 发现关键词: {kw}")
    else:
        print("✅ 未检测到验证码")
    
    # 提取表单信息
    print("\n【3】表单信息:")
    
    # 查找所有 input 标签
    input_pattern = r'<input[^>]*>'
    inputs = re.findall(input_pattern, content, re.IGNORECASE)
    
    print(f"共发现 {len(inputs)} 个输入框:")
    
    for i, inp in enumerate(inputs, 1):
        # 提取属性
        type_match = re.search(r'type="([^"]*)"', inp, re.IGNORECASE)
        name_match = re.search(r'name="([^"]*)"', inp, re.IGNORECASE)
        id_match = re.search(r'id="([^"]*)"', inp, re.IGNORECASE)
        placeholder_match = re.search(r'placeholder="([^"]*)"', inp, re.IGNORECASE)
        
        input_type = type_match.group(1) if type_match else "text"
        input_name = name_match.group(1) if name_match else "(无)"
        input_id = id_match.group(1) if id_match else "(无)"
        input_placeholder = placeholder_match.group(1) if placeholder_match else "(无)"
        
        # 只显示重要的输入框
        if input_type not in ['hidden'] or i <= 20:
            print(f"  [{i}] type={input_type}, name={input_name}, id={input_id}, placeholder={input_placeholder}")
    
    # 查找提交按钮
    print("\n【4】提交按钮:")
    button_patterns = [
        r'<button[^>]*type="submit"[^>]*>(.*?)</button>',
        r'<input[^>]*type="submit"[^>]*>',
        r'<button[^>]*>(.*?)</button>',
    ]
    
    buttons_found = []
    for pattern in button_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
        for match in matches:
            if isinstance(match, tuple):
                match = match[0] if match else ""
            clean_text = re.sub(r'<[^>]+>', '', str(match)).strip()
            if clean_text:
                buttons_found.append(clean_text)
    
    if buttons_found:
        print("发现按钮:")
        for btn in set(buttons_found):
            print(f"   - {btn}")
    else:
        print("⚠️  未找到明显的提交按钮")
    
    # 检查页面标题
    print("\n【5】页面标题:")
    title_match = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE)
    if title_match:
        print(f"   {title_match.group(1)}")
    
    # 检查是否在正确页面
    print("\n【6】页面判断:")
    if "registration" in content.lower():
        print("✅ 这是注册页面")
    elif "myfiles" in content.lower() or "dashboard" in content.lower():
        print("✅ 这是用户主页(注册成功)")
    elif "upgrade" in content.lower() and "plan" in content.lower():
        print("⚠️  这是套餐选择页面")
    else:
        print("⚠️  未知页面类型")
    
    # 检查成功标识
    success_keywords = ['welcome', 'success', 'congratulations', 'account created']
    success_found = any(kw in content.lower() for kw in success_keywords)
    
    if success_found:
        print("✅ 发现成功标识关键词")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python debug_page.py <html文件>")
        print("示例: python debug_page.py page_form_1763900126.html")
        sys.exit(1)
    
    analyze_html(sys.argv[1])
