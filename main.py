#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
个人文件自动化整理归档工具 (Automated File Organizer)
主程序文件

功能：
1. 一键整理文件夹内的文件
2. 监控指定文件夹，自动分类新文件
3. 支持自定义分类规则
4. 完整的日志记录和错误处理
"""

import os
import sys
import json
import shutil
import logging
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import pystray
from PIL import Image, ImageDraw
import win32gui
import win32process
import psutil

from file_organizer import FileOrganizer
from config_manager import ConfigManager
from logger_setup import setup_logger


class FileOrganizerGUI:
    """文件整理工具图形界面"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("文件整理工具")
        self.root.geometry("600x500")
        
        # 初始化组件
        self.config_manager = ConfigManager()
        self.logger = setup_logger()
        self.organizer = FileOrganizer(self.config_manager, self.logger)
        
        # 定时提醒相关
        self.reminder_timer = None
        self.reminder_enabled = False
        
        # 界面变量
        self.folder_var = tk.StringVar()  # 只保留一个文件夹选择
        self.status_var = tk.StringVar(value="就绪")
        
        # 托盘相关
        self.tray_icon = None
        self.is_hidden = False
        
        # 监控相关
        self.monitoring = False
        self.observer = None
        
        # 设置界面
        self.setup_ui()
        
        # 设置窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def setup_ui(self):
        """设置用户界面"""
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 标题
        title_label = ttk.Label(main_frame, text="个人文件自动化整理归档工具", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # 要整理的文件夹选择
        ttk.Label(main_frame, text="要整理的文件夹:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.folder_var, width=50).grid(row=1, column=1, padx=5)
        ttk.Button(main_frame, text="浏览", 
                  command=self.browse_folder).grid(row=1, column=2)
        
        # 操作按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=3, pady=20)
        
        ttk.Button(button_frame, text="一键整理", 
                  command=self.organize_files).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="快速整理桌面", 
                  command=self.quick_organize_desktop).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="配置规则", 
                  command=self.open_config).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="查看日志", 
                  command=self.view_logs).pack(side=tk.LEFT, padx=5)
        
        # 托盘和提醒按钮
        ttk.Button(button_frame, text="隐藏到托盘", command=self.hide_to_tray).pack(side=tk.RIGHT, padx=5)
        
        self.reminder_button = ttk.Button(button_frame, text="开启定时提醒", 
                                         command=self.toggle_reminder)
        self.reminder_button.pack(side=tk.RIGHT, padx=5)
        
        # 状态显示
        self.status_var = tk.StringVar(value="就绪")
        status_label = ttk.Label(main_frame, textvariable=self.status_var)
        status_label.grid(row=4, column=0, columnspan=3, pady=10)
        
        # 日志显示区域
        log_frame = ttk.LabelFrame(main_frame, text="操作日志", padding="5")
        log_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        
        self.log_text = tk.Text(log_frame, height=15, width=80)
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(5, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
    def browse_folder(self):
        """浏览要整理的文件夹"""
        folder = filedialog.askdirectory(title="选择要整理的文件夹")
        if folder:
            self.folder_var.set(folder)
            
    def organize_files(self):
        """整理文件"""
        folder = self.folder_var.get()
        
        if not folder:
            messagebox.showerror("错误", "请选择要整理的文件夹")
            return
            
        if not os.path.exists(folder):
            messagebox.showerror("错误", "文件夹不存在")
            return
            
        # 在文件夹内创建分类子文件夹
        target = os.path.join(folder, "分类文件")
        os.makedirs(target, exist_ok=True)
            
        # 在新线程中执行整理操作
        threading.Thread(target=self._organize_files_thread, 
                        args=(folder, target), daemon=True).start()
        
    def _organize_files_thread(self, source, target):
        """在后台线程中整理文件"""
        try:
            self.status_var.set("正在整理文件...")
            self.log_message(f"开始整理文件夹: {source}")
            
            result = self.organizer.organize_folder(source, target)
            
            self.log_message(f"整理完成! 处理了 {result['total']} 个文件")
            self.log_message(f"成功: {result['success']}, 失败: {result['failed']}")
            
            self.status_var.set("整理完成")
            
        except Exception as e:
            self.logger.error(f"整理文件时出错: {e}")
            self.log_message(f"错误: {e}")
            self.status_var.set("整理失败")
            
    def quick_organize_desktop(self):
        """快速整理桌面"""
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        if os.path.exists(desktop_path):
            self.folder_var.set(desktop_path)
            self.organize_files()
        else:
            messagebox.showerror("错误", "无法找到桌面文件夹")
            
    def toggle_reminder(self):
        """切换定时提醒"""
        if not self.reminder_enabled:
            self.start_reminder()
        else:
            self.stop_reminder()
            
    def start_reminder(self):
        """开始定时提醒"""
        self.reminder_enabled = True
        self.reminder_button.config(text="关闭定时提醒")
        self.status_var.set("定时提醒已开启")
        self.log_message("定时提醒已开启 - 每2小时提醒一次")
        
        # 设置2小时后的提醒
        self.schedule_next_reminder()
        
    def stop_reminder(self):
        """停止定时提醒"""
        if self.reminder_timer:
            self.root.after_cancel(self.reminder_timer)
            self.reminder_timer = None
            
        self.reminder_enabled = False
        self.reminder_button.config(text="开启定时提醒")
        self.status_var.set("定时提醒已关闭")
        self.log_message("定时提醒已关闭")
        
    def schedule_next_reminder(self):
        """安排下一次提醒"""
        if self.reminder_enabled:
            # 2小时 = 7200000毫秒
            self.reminder_timer = self.root.after(7200000, self.show_reminder)
            
    def show_reminder(self):
        """显示整理提醒"""
        if self.reminder_enabled:
            self.show_notification(
                "文件整理提醒", 
                "是时候整理一下文件了！\n\n建议检查：\n• 桌面文件\n• 下载文件夹\n• 临时文件"
            )
            self.log_message("显示定时整理提醒")
            # 安排下一次提醒
            self.schedule_next_reminder()
        
    def open_config(self):
        """打开配置窗口"""
        ConfigWindow(self.root, self.config_manager)
        
    def view_logs(self):
        """查看日志文件"""
        log_file = os.path.join(os.getcwd(), "logs", "file_organizer.log")
        try:
            if os.path.exists(log_file):
                os.startfile(log_file)
            else:
                # 如果日志文件不存在，创建日志目录并提示用户
                log_dir = os.path.dirname(log_file)
                os.makedirs(log_dir, exist_ok=True)
                messagebox.showinfo("信息", f"日志文件不存在：{log_file}\n\n日志目录已创建，请先进行一些操作后再查看日志。")
        except Exception as e:
            messagebox.showerror("错误", f"无法打开日志文件：{str(e)}")
            self.logger.error(f"打开日志文件失败: {e}")
            
    def log_message(self, message):
        """在界面上显示日志消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        # 在主线程中更新UI
        self.root.after(0, self._update_log_text, log_entry)
        
    def stop_monitoring(self):
        """停止文件监控"""
        try:
            if hasattr(self, 'observer') and self.observer:
                self.observer.stop()
                self.observer.join()
                self.observer = None
            self.monitoring = False
            self.logger.info("文件监控已停止")
        except Exception as e:
            self.logger.error(f"停止监控时出错: {e}")
            
    def start_monitoring(self, folder_path):
        """开始文件监控"""
        try:
            if self.monitoring:
                self.stop_monitoring()
                
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler
            
            class FileHandler(FileSystemEventHandler):
                def __init__(self, gui):
                    self.gui = gui
                    
                def on_created(self, event):
                    if not event.is_directory:
                        self.gui.log_message(f"检测到新文件: {os.path.basename(event.src_path)}")
                        
            self.observer = Observer()
            handler = FileHandler(self)
            self.observer.schedule(handler, folder_path, recursive=False)
            self.observer.start()
            self.monitoring = True
            self.logger.info(f"开始监控文件夹: {folder_path}")
            
        except Exception as e:
            self.logger.error(f"启动监控时出错: {e}")
            self.monitoring = False
        
    def _update_log_text(self, message):
        """更新日志文本框"""
        self.log_text.insert(tk.END, message)
        self.log_text.see(tk.END)
        
    def create_tray_icon(self):
        """创建托盘图标"""
        # 创建简单的PNG图标而不是使用SVG
        try:
            # 创建一个简单的图标
            image = Image.new('RGBA', (64, 64), color=(74, 144, 226, 255))
            draw = ImageDraw.Draw(image)
            
            # 绘制文件夹图标
            # 文件夹底部
            draw.rectangle([10, 25, 54, 50], fill=(255, 255, 255, 255), outline=(46, 92, 138, 255), width=2)
            # 文件夹标签
            draw.rectangle([10, 20, 30, 25], fill=(255, 255, 255, 255), outline=(46, 92, 138, 255), width=1)
            # 添加文字
            try:
                # 尝试使用默认字体
                font = ImageDraw.ImageFont.load_default()
                draw.text((18, 30), "整理", fill=(46, 92, 138, 255), font=font)
            except:
                # 如果字体加载失败，使用简单文字
                draw.text((18, 30), "F", fill=(46, 92, 138, 255))
                
            self.logger.info("成功创建托盘图标")
            
        except Exception as e:
            self.logger.error(f"创建图标失败: {e}")
            # 最简单的备用图标
            image = Image.new('RGB', (32, 32), color='blue')
        
        # 创建托盘菜单
        menu = pystray.Menu(
            pystray.MenuItem("快速整理", pystray.Menu(
                pystray.MenuItem("整理桌面", self.tray_organize_desktop),
                pystray.MenuItem("整理下载文件夹", self.tray_organize_downloads),
                pystray.MenuItem("整理文档文件夹", self.tray_organize_documents)
            )),
            pystray.MenuItem("文件统计", pystray.Menu(
                pystray.MenuItem("桌面文件统计", self.tray_stats_desktop),
                pystray.MenuItem("下载文件夹统计", self.tray_stats_downloads),
                pystray.MenuItem("系统垃圾文件扫描", self.tray_scan_junk)
            )),
            pystray.MenuItem("实用工具", pystray.Menu(
                pystray.MenuItem("清理回收站", self.tray_empty_recycle),
                pystray.MenuItem("清理临时文件", self.tray_clean_temp),
                pystray.MenuItem("查找重复文件", self.tray_find_duplicates)
            )),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("显示主窗口", self.show_window),
            pystray.MenuItem("退出", self.quit_app)
        )
        
        # 创建托盘图标
        self.tray_icon = pystray.Icon("文件整理工具", image, menu=menu)
        
    def hide_to_tray(self):
        """隐藏到系统托盘"""
        if not self.tray_icon:
            self.create_tray_icon()
            
        self.root.withdraw()  # 隐藏主窗口
        self.is_hidden = True
        
        # 在新线程中运行托盘图标
        threading.Thread(target=self.tray_icon.run, daemon=True).start()
        
    def show_window(self, icon=None, item=None):
        """显示主窗口"""
        self.root.deiconify()  # 显示主窗口
        self.root.lift()  # 置顶
        self.is_hidden = False
        
    def on_closing(self):
        """窗口关闭事件"""
        try:
            if hasattr(self, 'monitoring') and self.monitoring:
                self.stop_monitoring()
            if hasattr(self, 'reminder_enabled') and self.reminder_enabled:
                self.stop_reminder()
            if hasattr(self, 'tray_icon') and self.tray_icon:
                self.tray_icon.stop()
        except Exception as e:
            self.logger.error(f"关闭程序时出错: {e}")
        finally:
            self.root.destroy()
        
    def quit_app(self, icon=None, item=None):
        """退出应用"""
        self.logger.info("正在退出应用程序...")
        if self.reminder_enabled:
            self.stop_reminder()
        if self.tray_icon:
            self.tray_icon.stop()
        self.root.quit()
        self.root.destroy()
        # 强制结束进程
        import os
        import sys
        os._exit(0)
        
    def get_active_folder(self):
        """获取当前活动窗口的文件夹路径"""
        try:
            # 方法1: 通过Shell Application获取资源管理器窗口
            try:
                import win32com.client
                shell = win32com.client.Dispatch("Shell.Application")
                windows = shell.Windows()
                
                # 获取当前活动窗口句柄
                active_hwnd = win32gui.GetForegroundWindow()
                self.logger.info(f"当前活动窗口句柄: {active_hwnd}")
                
                # 遍历所有资源管理器窗口
                for window in windows:
                    try:
                        # 检查是否是当前活动窗口
                        if hasattr(window, 'HWND') and window.HWND == active_hwnd:
                            # 获取当前路径
                            location = window.LocationURL
                            if location:
                                self.logger.info(f"找到活动窗口位置: {location}")
                                # 将file:///格式转换为本地路径
                                if location.startswith('file:///'):
                                    import urllib.parse
                                    path = urllib.parse.unquote(location[8:])  # 移除file:///
                                    path = path.replace('/', '\\')
                                    if os.path.exists(path) and os.path.isdir(path):
                                        self.logger.info(f"通过Shell Application检测到活动文件夹: {path}")
                                        return path
                    except Exception as e:
                        self.logger.debug(f"检查窗口时出错: {e}")
                        continue
            except Exception as e:
                self.logger.debug(f"Shell Application方法失败: {e}")
            
            # 方法2: 通过窗口标题和进程信息
            try:
                hwnd = win32gui.GetForegroundWindow()
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                process = psutil.Process(pid)
                process_name = process.name().lower()
                
                self.logger.info(f"当前活动进程: {process_name}")
                
                if 'explorer.exe' in process_name:
                    # 获取窗口标题
                    window_title = win32gui.GetWindowText(hwnd)
                    self.logger.info(f"资源管理器窗口标题: '{window_title}'")
                    
                    # 尝试解析窗口标题中的路径信息
                    if window_title and window_title.strip():
                        # Windows 10/11的资源管理器标题格式
                        if ' - ' in window_title:
                            folder_name = window_title.split(' - ')[0].strip()
                        else:
                            folder_name = window_title.strip()
                        
                        self.logger.info(f"解析出的文件夹名: '{folder_name}'")
                        
                        # 尝试一些常见的路径组合
                        user_home = os.path.expanduser("~")
                        possible_paths = [
                            folder_name,  # 直接路径
                            os.path.join(user_home, folder_name),  # 用户目录下
                            os.path.join(user_home, "Desktop", folder_name),  # 桌面下
                            os.path.join(user_home, "Documents", folder_name),  # 文档下
                            os.path.join(user_home, "Downloads", folder_name),  # 下载下
                            os.path.join("C:\\", folder_name),  # C盘根目录
                            os.path.join("D:\\", folder_name),  # D盘根目录
                        ]
                        
                        for path in possible_paths:
                            if os.path.exists(path) and os.path.isdir(path):
                                self.logger.info(f"通过标题解析找到路径: {path}")
                                return path
                    
                    # 如果标题解析失败，尝试获取进程工作目录
                    try:
                        cwd = process.cwd()
                        if os.path.exists(cwd) and os.path.isdir(cwd):
                            self.logger.info(f"使用进程工作目录: {cwd}")
                            return cwd
                    except Exception as e:
                        self.logger.debug(f"获取进程工作目录失败: {e}")
            except Exception as e:
                self.logger.debug(f"窗口标题方法失败: {e}")
            
            self.logger.warning("所有检测方法都失败，无法获取活动文件夹")
            return None
            
        except Exception as e:
            self.logger.error(f"获取活动文件夹时发生严重错误: {e}")
            return None
            
    # 托盘快速整理功能
    def tray_organize_desktop(self, icon=None, item=None):
        """托盘：整理桌面"""
        self._organize_folder_with_notification(
            os.path.join(os.path.expanduser("~"), "Desktop"),
            "桌面"
        )
        
    def tray_organize_downloads(self, icon=None, item=None):
        """托盘：整理下载文件夹"""
        self._organize_folder_with_notification(
            os.path.join(os.path.expanduser("~"), "Downloads"),
            "下载文件夹"
        )
        
    def tray_organize_documents(self, icon=None, item=None):
        """托盘：整理文档文件夹"""
        self._organize_folder_with_notification(
            os.path.join(os.path.expanduser("~"), "Documents"),
            "文档文件夹"
        )
        
    def _organize_folder_with_notification(self, folder_path, folder_name):
        """整理文件夹并显示通知"""
        try:
            if not os.path.exists(folder_path):
                self.show_notification("错误", f"{folder_name}不存在")
                return
                
            target = os.path.join(folder_path, "分类文件")
            os.makedirs(target, exist_ok=True)
            
            moved_files = self.organizer.organize_folder(folder_path, target)
            
            if moved_files:
                message = f"成功整理{folder_name} {len(moved_files)} 个文件"
                self.show_notification("整理完成", message)
            else:
                self.show_notification("整理完成", f"{folder_name}没有需要整理的文件")
                
        except Exception as e:
            self.logger.error(f"整理{folder_name}时出错: {e}")
            self.show_notification("错误", f"整理{folder_name}失败: {e}")
            
    # 托盘文件统计功能
    def tray_stats_desktop(self, icon=None, item=None):
        """托盘：桌面文件统计"""
        self._show_folder_stats(
            os.path.join(os.path.expanduser("~"), "Desktop"),
            "桌面"
        )
        
    def tray_stats_downloads(self, icon=None, item=None):
        """托盘：下载文件夹统计"""
        self._show_folder_stats(
            os.path.join(os.path.expanduser("~"), "Downloads"),
            "下载文件夹"
        )
        
    def _show_folder_stats(self, folder_path, folder_name):
        """显示文件夹统计信息"""
        try:
            if not os.path.exists(folder_path):
                self.show_notification("错误", f"{folder_name}不存在")
                return
                
            file_count = 0
            folder_count = 0
            total_size = 0
            file_types = {}
            
            for item in os.listdir(folder_path):
                item_path = os.path.join(folder_path, item)
                if os.path.isfile(item_path):
                    file_count += 1
                    size = os.path.getsize(item_path)
                    total_size += size
                    
                    # 统计文件类型
                    ext = os.path.splitext(item)[1].lower()
                    if ext:
                        file_types[ext] = file_types.get(ext, 0) + 1
                elif os.path.isdir(item_path):
                    folder_count += 1
                    
            # 格式化大小
            size_mb = total_size / (1024 * 1024)
            
            # 获取最常见的文件类型
            top_types = sorted(file_types.items(), key=lambda x: x[1], reverse=True)[:3]
            types_str = ", ".join([f"{ext}({count})" for ext, count in top_types])
            
            message = f"{folder_name}统计:\n\n文件: {file_count} 个\n文件夹: {folder_count} 个\n总大小: {size_mb:.1f} MB\n\n主要类型: {types_str}"
            self.show_notification(f"{folder_name}统计", message)
            
        except Exception as e:
            self.logger.error(f"统计{folder_name}时出错: {e}")
            self.show_notification("错误", f"统计{folder_name}失败: {e}")
            
    def tray_scan_junk(self, icon=None, item=None):
        """托盘：扫描垃圾文件"""
        try:
            junk_patterns = [
                "*.tmp", "*.temp", "*.log", "*.bak", "*.old",
                "Thumbs.db", "desktop.ini", ".DS_Store"
            ]
            
            junk_files = []
            scan_paths = [
                os.path.join(os.path.expanduser("~"), "Desktop"),
                os.path.join(os.path.expanduser("~"), "Downloads"),
                os.path.join(os.path.expanduser("~"), "Documents")
            ]
            
            for scan_path in scan_paths:
                if os.path.exists(scan_path):
                    for pattern in junk_patterns:
                        import glob
                        matches = glob.glob(os.path.join(scan_path, pattern))
                        junk_files.extend(matches)
                        
            if junk_files:
                total_size = sum(os.path.getsize(f) for f in junk_files if os.path.exists(f))
                size_mb = total_size / (1024 * 1024)
                message = f"发现 {len(junk_files)} 个垃圾文件\n总大小: {size_mb:.1f} MB\n\n建议手动清理"
            else:
                message = "未发现明显的垃圾文件"
                
            self.show_notification("垃圾文件扫描", message)
            
        except Exception as e:
            self.logger.error(f"扫描垃圾文件时出错: {e}")
            self.show_notification("错误", f"扫描失败: {e}")
            
    # 托盘实用工具功能
    def tray_empty_recycle(self, icon=None, item=None):
        """托盘：清理回收站"""
        try:
            import winshell
            winshell.recycle_bin().empty(confirm=False, show_progress=False, sound=False)
            self.show_notification("清理完成", "回收站已清空")
        except ImportError:
            self.show_notification("错误", "需要安装winshell模块")
        except Exception as e:
            self.logger.error(f"清理回收站时出错: {e}")
            self.show_notification("错误", f"清理回收站失败: {e}")
            
    def tray_clean_temp(self, icon=None, item=None):
        """托盘：清理临时文件"""
        try:
            import tempfile
            temp_dir = tempfile.gettempdir()
            
            cleaned_count = 0
            cleaned_size = 0
            
            for item in os.listdir(temp_dir):
                item_path = os.path.join(temp_dir, item)
                try:
                    if os.path.isfile(item_path):
                        size = os.path.getsize(item_path)
                        os.remove(item_path)
                        cleaned_count += 1
                        cleaned_size += size
                except:
                    continue  # 跳过无法删除的文件
                    
            size_mb = cleaned_size / (1024 * 1024)
            message = f"清理完成\n\n删除文件: {cleaned_count} 个\n释放空间: {size_mb:.1f} MB"
            self.show_notification("临时文件清理", message)
            
        except Exception as e:
            self.logger.error(f"清理临时文件时出错: {e}")
            self.show_notification("错误", f"清理临时文件失败: {e}")
            
    def tray_find_duplicates(self, icon=None, item=None):
        """托盘：查找重复文件"""
        try:
            import hashlib
            
            scan_paths = [
                os.path.join(os.path.expanduser("~"), "Desktop"),
                os.path.join(os.path.expanduser("~"), "Downloads"),
                os.path.join(os.path.expanduser("~"), "Documents")
            ]
            
            file_hashes = {}
            duplicates = []
            
            for scan_path in scan_paths:
                if not os.path.exists(scan_path):
                    continue
                    
                for item in os.listdir(scan_path):
                    item_path = os.path.join(scan_path, item)
                    if os.path.isfile(item_path):
                        try:
                            # 计算文件哈希
                            with open(item_path, 'rb') as f:
                                file_hash = hashlib.md5(f.read()).hexdigest()
                                
                            if file_hash in file_hashes:
                                duplicates.append((item_path, file_hashes[file_hash]))
                            else:
                                file_hashes[file_hash] = item_path
                        except:
                            continue
                            
            if duplicates:
                message = f"发现 {len(duplicates)} 组重复文件\n\n建议手动检查和删除"
            else:
                message = "未发现重复文件"
                
            self.show_notification("重复文件扫描", message)
            
        except Exception as e:
            self.logger.error(f"查找重复文件时出错: {e}")
            self.show_notification("错误", f"查找重复文件失败: {e}")
            

        
    def show_notification(self, title, message):
        """显示通知对话框"""
        try:
            # 使用tkinter的messagebox显示信息对话框
            # 在新线程中显示，避免阻塞主界面
            def show_dialog():
                try:
                    messagebox.showinfo(title, message)
                    self.logger.info(f"已显示通知对话框: {title} - {message}")
                except Exception as e:
                    self.logger.error(f"显示对话框时出错: {e}")
            
            # 在主线程中执行GUI操作
            self.root.after(0, show_dialog)
            
        except Exception as e:
            self.logger.error(f"显示通知时出错: {e}")
    
    def run(self):
        """运行GUI"""
        try:
            self.root.mainloop()
        finally:
            if self.reminder_enabled:
                self.stop_reminder()
            if self.tray_icon:
                self.tray_icon.stop()





class ConfigWindow:
    """配置窗口"""
    
    def __init__(self, parent, config_manager):
        self.config_manager = config_manager
        
        self.window = tk.Toplevel(parent)
        self.window.title("配置规则")
        self.window.geometry("600x400")
        self.window.transient(parent)
        self.window.grab_set()
        
        self.setup_ui()
        self.load_config()
        
    def setup_ui(self):
        """设置配置窗口UI"""
        # 主框架
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 文件类型规则
        rules_frame = ttk.LabelFrame(main_frame, text="文件类型分类规则", padding="5")
        rules_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 创建树形视图
        columns = ('category', 'extensions')
        self.tree = ttk.Treeview(rules_frame, columns=columns, show='headings', height=10)
        
        self.tree.heading('category', text='分类名称')
        self.tree.heading('extensions', text='文件扩展名')
        
        self.tree.column('category', width=200)
        self.tree.column('extensions', width=300)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(rules_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(button_frame, text="添加规则", command=self.add_rule).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="编辑规则", command=self.edit_rule).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="删除规则", command=self.delete_rule).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="保存", command=self.save_config).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="取消", command=self.window.destroy).pack(side=tk.RIGHT, padx=5)
        
    def load_config(self):
        """加载配置"""
        config = self.config_manager.get_config()
        rules = config.get('file_types', {})
        
        for category, extensions in rules.items():
            ext_str = ', '.join(extensions)
            self.tree.insert('', tk.END, values=(category, ext_str))
            
    def add_rule(self):
        """添加规则"""
        self.edit_rule_dialog()
        
    def edit_rule(self):
        """编辑规则"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请选择要编辑的规则")
            return
            
        item = selection[0]
        values = self.tree.item(item, 'values')
        self.edit_rule_dialog(item, values[0], values[1])
        
    def delete_rule(self):
        """删除规则"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请选择要删除的规则")
            return
            
        if messagebox.askyesno("确认", "确定要删除选中的规则吗？"):
            self.tree.delete(selection[0])
            
    def edit_rule_dialog(self, item=None, category="", extensions=""):
        """编辑规则对话框"""
        dialog = tk.Toplevel(self.window)
        dialog.title("编辑规则")
        dialog.geometry("400x200")
        dialog.transient(self.window)
        dialog.grab_set()
        
        # 分类名称
        ttk.Label(dialog, text="分类名称:").pack(pady=5)
        category_var = tk.StringVar(value=category)
        ttk.Entry(dialog, textvariable=category_var, width=40).pack(pady=5)
        
        # 文件扩展名
        ttk.Label(dialog, text="文件扩展名 (用逗号分隔):").pack(pady=5)
        extensions_var = tk.StringVar(value=extensions)
        ttk.Entry(dialog, textvariable=extensions_var, width=40).pack(pady=5)
        
        # 按钮
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=20)
        
        def save_rule():
            cat = category_var.get().strip()
            ext = extensions_var.get().strip()
            
            if not cat or not ext:
                messagebox.showerror("错误", "请填写完整信息")
                return
                
            if item:
                self.tree.item(item, values=(cat, ext))
            else:
                self.tree.insert('', tk.END, values=(cat, ext))
                
            dialog.destroy()
            
        ttk.Button(button_frame, text="保存", command=save_rule).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="取消", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        
    def save_config(self):
        """保存配置"""
        rules = {}
        for item in self.tree.get_children():
            values = self.tree.item(item, 'values')
            category = values[0]
            extensions = [ext.strip() for ext in values[1].split(',')]
            rules[category] = extensions
            
        config = self.config_manager.get_config()
        config['file_types'] = rules
        self.config_manager.save_config(config)
        
        messagebox.showinfo("成功", "配置已保存")
        self.window.destroy()


def main():
    """主函数"""
    # 创建必要的目录
    os.makedirs("logs", exist_ok=True)
    os.makedirs("config", exist_ok=True)
    
    # 启动GUI
    app = FileOrganizerGUI()
    app.run()


if __name__ == "__main__":
    main()