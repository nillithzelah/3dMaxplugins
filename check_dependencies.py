#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查并安装3ds Max插件所需的Python依赖
"""

import sys
import subprocess
import importlib

def check_module(module_name):
    """检查模块是否已安装"""
    try:
        importlib.import_module(module_name)
        return True
    except ImportError:
        return False

def install_module(module_name):
    """安装模块"""
    try:
        print(f"正在安装 {module_name}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", module_name])
        return True
    except subprocess.CalledProcessError as e:
        print(f"安装 {module_name} 失败: {e}")
        return False

def main():
    print("检查3ds Max插件依赖...")
    print("=" * 50)
    
    # 必需的模块列表
    required_modules = [
        "requests",
        "PySide6"
    ]
    
    missing_modules = []
    
    # 检查每个模块
    for module in required_modules:
        if check_module(module):
            print(f"✅ {module} 已安装")
        else:
            print(f"❌ {module} 未安装")
            missing_modules.append(module)
    
    print("=" * 50)
    
    if missing_modules:
        print(f"发现 {len(missing_modules)} 个缺失的模块:")
        for module in missing_modules:
            print(f"  - {module}")
        
        print("\n是否要自动安装这些模块? (y/n): ", end="")
        choice = input().lower().strip()
        
        if choice in ['y', 'yes', '是']:
            print("\n开始安装...")
            success_count = 0
            
            for module in missing_modules:
                if install_module(module):
                    success_count += 1
                    print(f"✅ {module} 安装成功")
                else:
                    print(f"❌ {module} 安装失败")
            
            print(f"\n安装完成: {success_count}/{len(missing_modules)} 个模块安装成功")
            
            if success_count == len(missing_modules):
                print("🎉 所有依赖已安装完成！现在可以运行3ds Max插件了")
            else:
                print("⚠️  部分模块安装失败，请手动安装")
        else:
            print("跳过自动安装")
    else:
        print("🎉 所有依赖都已安装！")
    
    print("\n按回车键退出...")
    input()

if __name__ == "__main__":
    main() 