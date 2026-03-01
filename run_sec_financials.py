#!/usr/bin/env python3
"""
简化版SEC财务数据提取器启动脚本
使用内置模块，减少外部依赖
"""

import sys
import os
import io

# 设置UTF-8编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def check_dependencies():
    """检查依赖包"""
    missing_deps = []
    
    # 检查requests
    try:
        import requests
        print("[OK] requests 已安装")
    except ImportError:
        missing_deps.append("requests")
        print("[X] requests 未安装")
    
    # 检查pandas
    try:
        import pandas
        print("[OK] pandas 已安装")
    except ImportError:
        missing_deps.append("pandas")
        print("[X] pandas 未安装")
    
    # 检查dateutil
    try:
        import dateutil
        print("[OK] python-dateutil 已安装")
    except ImportError:
        missing_deps.append("python-dateutil")
        print("[X] python-dateutil 未安装")
    
    return missing_deps

def install_dependencies():
    """指导安装依赖"""
    print("\n" + "="*60)
    print("依赖安装指南")
    print("="*60)
    
    print("\n方法1: 使用MSYS2包管理器 (推荐)")
    print("--------------------------------")
    print("1. 打开MSYS2 UCRT64终端")
    print("2. 运行以下命令:")
    print("   pacman -S mingw-w64-ucrt-x86_64-python-requests")
    print("   pacman -S mingw-w64-ucrt-x86_64-python-pandas")
    print("   pacman -S mingw-w64-ucrt-x86_64-python-dateutil")
    
    print("\n方法2: 使用pip (如果可用)")
    print("------------------------")
    print("1. 检查pip是否可用:")
    print("   python -m pip --version")
    print("2. 如果可用，运行:")
    print("   python -m pip install requests pandas python-dateutil")
    
    print("\n方法3: 使用系统Python")
    print("-------------------")
    print("1. 检查系统Python安装:")
    print("   where python")
    print("2. 使用系统Python的pip:")
    print("   C:\\Python39\\python.exe -m pip install requests pandas python-dateutil")
    
    print("\n安装后，重新运行此脚本验证。")

def run_without_deps():
    """使用简化版本运行（无外部依赖）"""
    print("\n" + "="*60)
    print("使用简化版本运行")
    print("="*60)
    
    # 这里可以调用简化版本的代码
    # 暂时先显示帮助信息
    print("\n简化版本功能:")
    print("1. 股票代码到CIK映射")
    print("2. 基本SEC API访问")
    print("3. CSV数据导出")
    print("\n完整功能需要安装依赖包。")

def main():
    """主函数"""
    print("SEC Financial Data Extractor - 启动器")
    print("="*60)
    
    # 检查依赖
    missing_deps = check_dependencies()
    
    if not missing_deps:
        print("\n[OK] 所有依赖已安装，启动完整版本...")
        print("-" * 40)
        
        # 导入并运行主程序
        try:
            from sec_financials.main import main as sec_main
            sec_main()
        except ImportError as e:
            print(f"导入错误: {e}")
            print("请确保从项目根目录运行:")
            print("  python run_sec_financials.py")
            return 1
    else:
        print(f"\n[X] 缺少 {len(missing_deps)} 个依赖包: {', '.join(missing_deps)}")
        
        # 询问用户
        print("\n请选择:")
        print("1. 显示安装指南")
        print("2. 使用简化版本运行（功能有限）")
        print("3. 退出")
        
        try:
            choice = input("\n请输入选择 (1-3): ").strip()
            
            if choice == "1":
                install_dependencies()
            elif choice == "2":
                run_without_deps()
            elif choice == "3":
                print("退出程序")
                return 0
            else:
                print("无效选择")
                return 1
                
        except KeyboardInterrupt:
            print("\n用户中断")
            return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())