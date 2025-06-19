#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目打包脚本
用于将Python项目打包成可执行文件
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


class ProjectBuilder:
    """项目构建器"""
    
    def __init__(self):
        self.project_dir = Path(__file__).parent
        self.dist_dir = self.project_dir / "dist"
        self.build_dir = self.project_dir / "build"
        
    def clean(self):
        """清理构建目录"""
        print("清理构建目录...")
        
        dirs_to_clean = [self.dist_dir, self.build_dir]
        for dir_path in dirs_to_clean:
            if dir_path.exists():
                shutil.rmtree(dir_path)
                print(f"已删除: {dir_path}")
        
        # 清理spec文件
        for spec_file in self.project_dir.glob("*.spec"):
            spec_file.unlink()
            print(f"已删除: {spec_file}")
    
    def check_dependencies(self):
        """检查依赖"""
        print("检查依赖...")
        
        required_packages = ['PyInstaller']
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package)
                print(f"✓ {package}")
            except ImportError:
                missing_packages.append(package)
                print(f"✗ {package} (缺失)")
        
        if missing_packages:
            print(f"\n缺少依赖包: {', '.join(missing_packages)}")
            print("请运行: pip install pyinstaller")
            return False
        
        return True
    
    def build_gui(self):
        """构建GUI版本"""
        print("\n构建GUI版本...")
        
        cmd = [
            'python', '-m', 'PyInstaller',
            '--onefile',
            '--windowed',
            '--name', '文件整理工具',
            '--add-data', 'config;config',
            '--hidden-import', 'tkinter',
            '--hidden-import', 'watchdog',
            'main.py'
        ]
        
        # 如果图标文件存在，添加图标参数
        if (self.project_dir / 'icon.ico').exists():
            cmd.insert(-1, '--icon')
            cmd.insert(-1, 'icon.ico')
        
        try:
            result = subprocess.run(cmd, cwd=self.project_dir, check=True)
            print("GUI版本构建成功!")
            return True
        except subprocess.CalledProcessError as e:
            print(f"GUI版本构建失败: {e}")
            return False
    

    
    def create_portable_package(self):
        """创建便携版包"""
        print("\n创建便携版包...")
        
        portable_dir = self.dist_dir / "portable"
        portable_dir.mkdir(parents=True, exist_ok=True)
        
        # 复制可执行文件
        exe_files = list(self.dist_dir.glob("*.exe"))
        for exe_file in exe_files:
            if exe_file.parent != portable_dir:
                shutil.copy2(exe_file, portable_dir)
                print(f"已复制: {exe_file.name}")
        
        # 复制配置文件
        config_src = self.project_dir / "config"
        config_dst = portable_dir / "config"
        if config_src.exists():
            shutil.copytree(config_src, config_dst, dirs_exist_ok=True)
            print("已复制配置文件")
        
        # 创建日志目录
        logs_dir = portable_dir / "logs"
        logs_dir.mkdir(exist_ok=True)
        print("已创建日志目录")
        
        # 复制README
        readme_src = self.project_dir / "README.md"
        if readme_src.exists():
            shutil.copy2(readme_src, portable_dir)
            print("已复制README文件")
        
        # 创建启动脚本
        self._create_launch_scripts(portable_dir)
        
        print(f"便携版包已创建: {portable_dir}")
    
    def _create_launch_scripts(self, portable_dir):
        """创建启动脚本"""
        # Windows批处理文件
        bat_content = '''@echo off
chcp 65001 > nul
echo 文件整理工具
echo ================
echo 双击"文件整理工具.exe"启动程序
echo.
echo 使用说明:
echo - 配置文件: config/settings.json
echo - 日志文件: logs/file_organizer.log
echo.
start "" "文件整理工具.exe"
'''
        
        bat_file = portable_dir / "启动.bat"
        with open(bat_file, 'w', encoding='gbk') as f:
            f.write(bat_content)
        
        # Linux/Mac shell脚本
        sh_content = '''#!/bin/bash
echo "文件整理工具"
echo "================="
echo "启动图形界面程序"
echo
echo "使用说明:"
echo "- 配置文件: config/settings.json"
echo "- 日志文件: logs/file_organizer.log"
echo
./文件整理工具
'''


        
        sh_file = portable_dir / "launch.sh"
        with open(sh_file, 'w', encoding='utf-8') as f:
            f.write(sh_content)
        
        # 设置执行权限（在Unix系统上）
        if os.name != 'nt':
            os.chmod(sh_file, 0o755)
    
    def create_installer_script(self):
        """创建安装脚本"""
        print("\n创建安装脚本...")
        
        # Windows安装脚本
        install_bat = '''@echo off
chcp 65001 > nul
echo 文件整理工具 - 安装脚本
echo ========================
echo.

set "INSTALL_DIR=%USERPROFILE%\\文件整理工具"
echo 安装目录: %INSTALL_DIR%
echo.

if exist "%INSTALL_DIR%" (
    echo 检测到已安装版本，是否覆盖安装？
    set /p confirm=输入 Y 确认，其他键取消: 
    if /i not "%confirm%"=="Y" (
        echo 安装已取消
        pause
        exit /b
    )
    rmdir /s /q "%INSTALL_DIR%"
)

echo 正在安装...
mkdir "%INSTALL_DIR%"
xcopy /e /i /h /y "." "%INSTALL_DIR%"

echo.
echo 是否创建桌面快捷方式？
set /p shortcut=输入 Y 创建，其他键跳过: 
if /i "%shortcut%"=="Y" (
    echo 正在创建桌面快捷方式...
    powershell "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\\Desktop\\文件整理工具.lnk'); $Shortcut.TargetPath = '%INSTALL_DIR%\\文件整理工具.exe'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.Save()"
)

echo.
echo 安装完成！
echo 程序位置: %INSTALL_DIR%
echo 可以通过开始菜单或桌面快捷方式启动
echo.
pause
'''
        
        install_file = self.dist_dir / "install.bat"
        with open(install_file, 'w', encoding='gbk') as f:
            f.write(install_bat)
        
        print(f"安装脚本已创建: {install_file}")
    
    def build_all(self):
        """构建GUI版本"""
        print("开始构建项目...")
        print("=" * 50)
        
        # 检查依赖
        if not self.check_dependencies():
            return False
        
        # 清理
        self.clean()
        
        # 构建GUI版本
        gui_success = self.build_gui()
        
        if gui_success:
            # 创建便携版包
            self.create_portable_package()
            
            # 创建安装脚本
            self.create_installer_script()
            
            print("\n" + "=" * 50)
            print("构建完成!")
            print(f"输出目录: {self.dist_dir}")
            print("✓ GUI版本构建成功")
            
            print("\n可用文件:")
            for file in self.dist_dir.rglob("*"):
                if file.is_file():
                    print(f"  {file.relative_to(self.dist_dir)}")
            
            return True
        else:
            print("\n构建失败!")
            return False


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="项目构建工具")
    parser.add_argument('--clean', action='store_true', help='仅清理构建目录')
    parser.add_argument('--check', action='store_true', help='仅检查依赖')
    
    args = parser.parse_args()
    
    builder = ProjectBuilder()
    
    if args.clean:
        builder.clean()
    elif args.check:
        builder.check_dependencies()
    else:
        builder.build_all()


if __name__ == "__main__":
    main()