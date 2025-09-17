#!/usr/bin/env python3
"""
司机配送成本分析系统启动脚本
使用方法：
1. 安装依赖：pip install -r requirements.txt
2. 运行应用：python run_app.py
"""

import subprocess
import sys
import os
import webbrowser
import time
from pathlib import Path

def check_dependencies():
    """检查依赖包是否安装"""
    required_packages = [
        'streamlit', 'streamlit-folium', 'folium',
        'plotly', 'pandas', 'numpy'
    ]

    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print("❌ 缺少以下依赖包:")
        for pkg in missing_packages:
            print(f"   - {pkg}")
        print("\n请运行以下命令安装依赖:")
        print("pip install -r requirements.txt")
        return False

    return True

def check_data_files():
    """检查数据文件是否存在"""
    required_files = [
        'data/2025-08-20_打卡_已匹配.csv',
        'data/2025-08-20_司机成本分析.csv',
        'data/2025-08-20_分公司汇总.csv',
        'delivery_cost_calculator.py'
    ]

    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)

    if missing_files:
        print("❌ 缺少以下数据文件:")
        for file in missing_files:
            print(f"   - {file}")
        print("\n请确保已运行数据预处理脚本生成必要文件")
        return False

    return True

def start_streamlit():
    """启动Streamlit应用"""
    print("🚀 启动司机配送成本分析系统...")
    print("📊 正在准备数据...")

    # 检查依赖
    if not check_dependencies():
        return False

    # 检查数据文件
    if not check_data_files():
        return False

    print("✅ 所有检查通过，启动Web应用...")

    # 启动Streamlit
    try:
        cmd = [sys.executable, "-m", "streamlit", "run", "streamlit_app.py",
               "--server.port", "8501"]

        print("🌐 Web应用将在浏览器中打开...")
        print("📍 本地访问地址: http://localhost:8501")
        print("⏹️  按 Ctrl+C 停止应用")

        # 等待一下再打开浏览器
        def open_browser():
            time.sleep(3)
            webbrowser.open('http://localhost:8501')

        import threading
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()

        # 运行Streamlit
        subprocess.run(cmd)

    except KeyboardInterrupt:
        print("\n👋 应用已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        return False

    return True

def main():
    """主函数"""
    print("=" * 60)
    print("🚚 司机配送成本分析系统")
    print("=" * 60)

    if not start_streamlit():
        print("\n💡 如果遇到问题，请检查:")
        print("1. 是否已安装所有依赖包")
        print("2. 是否已运行数据预处理脚本")
        print("3. Python版本是否为3.8+")
        sys.exit(1)

if __name__ == "__main__":
    main()