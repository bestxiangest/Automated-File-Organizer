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

# 标准库导入
import os  # 操作系统接口，用于文件和目录操作
import sys  # 系统特定的参数和函数
import json  # JSON数据处理
import shutil  # 高级文件操作工具
import logging  # 日志记录功能
import argparse  # 命令行参数解析
from datetime import datetime  # 日期时间处理
from pathlib import Path  # 面向对象的文件系统路径
from typing import Dict, List, Optional  # 类型提示

# GUI相关库导入
import tkinter as tk  # Python标准GUI库
from tkinter import ttk, filedialog, messagebox  # tkinter的增强组件和对话框
import threading  # 多线程支持

# 系统托盘和图像处理库
import pystray  # 系统托盘图标支持
from PIL import Image, ImageDraw  # 图像处理库

# Windows系统API
import win32gui  # Windows GUI API
import win32process  # Windows进程API
import psutil  # 系统和进程工具

# 自定义模块导入
from file_organizer import FileOrganizer  # 文件整理核心功能
from config_manager import ConfigManager  # 配置管理
from logger_setup import setup_logger  # 日志设置


class FileOrganizerGUI:
    """文件整理工具图形界面类
    
    提供完整的图形用户界面，包括：
    - 文件夹选择和整理功能
    - 系统托盘支持
    - 定时提醒功能
    - 实时监控功能
    - 配置管理界面
    """
    
    def __init__(self):
        """初始化文件整理工具GUI
        
        创建主窗口，初始化所有组件和变量
        """
        # 创建主窗口
        self.root = tk.Tk()  # 创建tkinter主窗口对象
        self.root.title("🗂️ 智能文件整理工具")  # 设置窗口标题
        self.root.geometry("750x600")  # 设置窗口初始大小
        self.root.minsize(650, 500)  # 设置最小窗口大小
        
        # 设置现代化主题样式
        self.setup_modern_theme()
        
        # 初始化核心组件
        self.config_manager = ConfigManager()  # 配置管理器，处理用户设置
        self.logger = setup_logger()  # 日志记录器，记录操作日志
        self.organizer = FileOrganizer(self.config_manager, self.logger)  # 文件整理器核心
        
        # 定时提醒功能相关变量
        self.reminder_timer = None  # 定时器对象，用于定时提醒
        self.reminder_enabled = False  # 提醒功能开关状态
        
        # GUI界面变量
        self.folder_var = tk.StringVar()  # 存储用户选择的文件夹路径
        self.status_var = tk.StringVar(value="🟢 就绪")  # 显示当前操作状态
        
        # 系统托盘功能相关变量
        self.tray_icon = None  # 托盘图标对象
        self.is_hidden = False  # 窗口是否隐藏到托盘
        
        # 文件监控功能相关变量
        self.monitoring = False  # 监控功能开关状态
        self.observer = None  # 文件系统观察者对象
        
        # 初始化用户界面
        self.setup_ui()  # 创建和布局所有GUI组件
        
        # 设置窗口关闭事件处理
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)  # 绑定窗口关闭事件
        
    def setup_modern_theme(self):
        """设置现代化主题样式"""
        # 设置窗口背景色为浅色
        self.root.configure(bg='#f8f9fa')
        
        # 创建自定义样式
        style = ttk.Style()
        
        # 配置现代化的颜色主题
        style.theme_use('clam')  # 使用clam主题作为基础
        
        # 自定义按钮样式
        style.configure('Modern.TButton',
                       background='#007bff',
                       foreground='white',
                       borderwidth=0,
                       focuscolor='none',
                       padding=(12, 8))
        style.map('Modern.TButton',
                 background=[('active', '#0056b3'),
                           ('pressed', '#004085')])
        
        # 自定义主要按钮样式
        style.configure('Primary.TButton',
                       background='#28a745',
                       foreground='white',
                       borderwidth=0,
                       focuscolor='none',
                       padding=(15, 10))
        style.map('Primary.TButton',
                 background=[('active', '#218838'),
                           ('pressed', '#1e7e34')])
        
        # 自定义次要按钮样式
        style.configure('Secondary.TButton',
                       background='#6c757d',
                       foreground='white',
                       borderwidth=0,
                       focuscolor='none',
                       padding=(10, 6))
        style.map('Secondary.TButton',
                 background=[('active', '#5a6268'),
                           ('pressed', '#545b62')])
        
        # 自定义输入框样式
        style.configure('Modern.TEntry',
                       fieldbackground='white',
                       borderwidth=1,
                       relief='solid',
                       padding=(8, 6))
        
        # 自定义标签框样式
        style.configure('Modern.TLabelframe',
                       background='#f8f9fa',
                       borderwidth=1,
                       relief='solid')
        style.configure('Modern.TLabelframe.Label',
                       background='#f8f9fa',
                       foreground='#495057',
                       font=('Segoe UI', 10, 'bold'))
        
        # 自定义标签样式
        style.configure('Title.TLabel',
                       background='#f8f9fa',
                       foreground='#212529',
                       font=('Segoe UI', 18, 'bold'))
        
        style.configure('Subtitle.TLabel',
                       background='#f8f9fa',
                       foreground='#6c757d',
                       font=('Segoe UI', 10))
        
        style.configure('Status.TLabel',
                       background='#f8f9fa',
                       foreground='#28a745',
                       font=('Segoe UI', 9))
        
    def setup_ui(self):
        """设置现代化用户界面
        
        创建并布局所有GUI组件，采用现代化设计：
        - 卡片式布局
        - 现代化按钮样式
        - 紧凑的间距
        - 美观的颜色搭配
        """
        # 创建主容器，使用现代化背景色
        main_container = tk.Frame(self.root, bg='#f8f9fa')
        main_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # 标题区域
        title_frame = tk.Frame(main_container, bg='#f8f9fa')
        title_frame.pack(fill=tk.X, pady=(0, 20))
        
        # 主标题
        title_label = ttk.Label(title_frame, text="🗂️ 智能文件整理工具", style='Title.TLabel')
        title_label.pack()
        
        # 副标题
        subtitle_label = ttk.Label(title_frame, text="让文件管理变得简单高效", style='Subtitle.TLabel')
        subtitle_label.pack(pady=(5, 0))
        
        # 文件夹选择卡片
        folder_card = tk.Frame(main_container, bg='white', relief='solid', bd=1)
        folder_card.pack(fill=tk.X, pady=(0, 15))
        
        folder_inner = tk.Frame(folder_card, bg='white')
        folder_inner.pack(fill=tk.X, padx=20, pady=15)
        
        # 文件夹选择标题
        folder_title = ttk.Label(folder_inner, text="📁 选择要整理的文件夹", 
                                font=('Segoe UI', 11, 'bold'), background='white', foreground='#495057')
        folder_title.pack(anchor=tk.W, pady=(0, 10))
        
        # 文件夹路径输入区域
        path_frame = tk.Frame(folder_inner, bg='white')
        path_frame.pack(fill=tk.X)
        
        # 文件夹路径输入框
        self.folder_entry = ttk.Entry(path_frame, textvariable=self.folder_var, 
                                     style='Modern.TEntry', font=('Segoe UI', 10))
        self.folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        # 浏览按钮
        browse_btn = ttk.Button(path_frame, text="📂 浏览", 
                               command=self.browse_folder, style='Modern.TButton')
        browse_btn.pack(side=tk.RIGHT)
        
        # 主要操作区域
        action_card = tk.Frame(main_container, bg='white', relief='solid', bd=1)
        action_card.pack(fill=tk.X, pady=(0, 15))
        
        action_inner = tk.Frame(action_card, bg='white')
        action_inner.pack(fill=tk.X, padx=20, pady=15)
        
        # 操作区域标题
        action_title = ttk.Label(action_inner, text="⚡ 快速操作", 
                                font=('Segoe UI', 11, 'bold'), background='white', foreground='#495057')
        action_title.pack(anchor=tk.W, pady=(0, 15))
        
        # 主要按钮区域
        main_buttons_frame = tk.Frame(action_inner, bg='white')
        main_buttons_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 一键整理按钮（主要按钮）
        organize_btn = ttk.Button(main_buttons_frame, text="🚀 一键整理", 
                                 command=self.organize_files, style='Primary.TButton')
        organize_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 快速整理桌面按钮
        desktop_btn = ttk.Button(main_buttons_frame, text="🖥️ 整理桌面", 
                                command=self.quick_organize_desktop, style='Modern.TButton')
        desktop_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 次要按钮区域
        secondary_buttons_frame = tk.Frame(action_inner, bg='white')
        secondary_buttons_frame.pack(fill=tk.X)
        
        # 配置规则按钮
        config_btn = ttk.Button(secondary_buttons_frame, text="⚙️ 配置规则", 
                               command=self.open_config, style='Secondary.TButton')
        config_btn.pack(side=tk.LEFT, padx=(0, 8))
        
        # 查看日志按钮
        log_btn = ttk.Button(secondary_buttons_frame, text="📋 查看日志", 
                            command=self.view_logs, style='Secondary.TButton')
        log_btn.pack(side=tk.LEFT, padx=(0, 8))
        
        # 定时提醒按钮
        self.reminder_button = ttk.Button(secondary_buttons_frame, text="⏰ 开启提醒", 
                                         command=self.toggle_reminder, style='Secondary.TButton')
        self.reminder_button.pack(side=tk.LEFT, padx=(0, 8))
        
        # 隐藏到托盘按钮
        tray_btn = ttk.Button(secondary_buttons_frame, text="📌 托盘", 
                             command=self.hide_to_tray, style='Secondary.TButton')
        tray_btn.pack(side=tk.RIGHT)
        
        # 状态显示区域
        status_frame = tk.Frame(main_container, bg='#f8f9fa')
        status_frame.pack(fill=tk.X, pady=(0, 15))
        
        status_label = ttk.Label(status_frame, textvariable=self.status_var, style='Status.TLabel')
        status_label.pack()
        
        # 日志显示卡片
        log_card = tk.Frame(main_container, bg='white', relief='solid', bd=1)
        log_card.pack(fill=tk.BOTH, expand=True)
        
        log_inner = tk.Frame(log_card, bg='white')
        log_inner.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)
        
        # 日志区域标题
        log_title = ttk.Label(log_inner, text="📝 操作日志", 
                             font=('Segoe UI', 11, 'bold'), background='white', foreground='#495057')
        log_title.pack(anchor=tk.W, pady=(0, 10))
        
        # 日志文本区域
        log_text_frame = tk.Frame(log_inner, bg='white')
        log_text_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建日志文本框，使用现代化样式
        self.log_text = tk.Text(log_text_frame, 
                               height=12, 
                               font=('Consolas', 9),
                               bg='#f8f9fa',
                               fg='#495057',
                               relief='flat',
                               wrap=tk.WORD,
                               padx=10,
                               pady=8)
        
        # 创建滚动条
        scrollbar = ttk.Scrollbar(log_text_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        # 布局日志文本框和滚动条
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 配置网格权重，使界面可以自适应窗口大小变化
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
    def browse_folder(self):
        """浏览文件夹
        
        打开文件夹选择对话框，让用户选择要整理的文件夹
        如果用户选择了文件夹，则更新界面上的文件夹路径显示
        """
        # 打开文件夹选择对话框
        folder = filedialog.askdirectory(title="选择要整理的文件夹")
        # 如果用户选择了文件夹（没有取消）
        if folder:
            # 将选择的文件夹路径设置到界面变量中
            self.folder_var.set(folder)
            
    def organize_files(self):
        """整理文件
        
        主要的文件整理入口方法，执行以下步骤：
        1. 验证用户是否选择了文件夹
        2. 检查文件夹是否存在
        3. 在后台线程中启动文件整理操作
        """
        # 获取用户选择的文件夹路径
        folder = self.folder_var.get()
        
        # 检查是否选择了文件夹
        if not folder:
            messagebox.showerror("错误", "请选择要整理的文件夹")
            return
            
        # 检查文件夹是否存在
        if not os.path.exists(folder):
            messagebox.showerror("错误", "文件夹不存在")
            return
            
        # 在文件夹内创建分类子文件夹
        target = os.path.join(folder, "分类文件")
        os.makedirs(target, exist_ok=True)
            
        # 在后台线程中执行整理操作，避免阻塞UI界面
        # daemon=True确保主程序退出时线程也会退出
        threading.Thread(target=self._organize_files_thread, 
                        args=(folder, target), daemon=True).start()
        
    def _organize_files_thread(self, source, target):
        """在后台线程中执行文件整理
        
        Args:
            source (str): 源文件夹路径
            target (str): 目标分类文件夹路径
            
        该方法在独立线程中运行，避免阻塞主UI线程
        执行实际的文件整理操作并更新界面状态和日志
        """
        try:
            # 更新状态显示为正在整理
            self.status_var.set("正在整理文件...")
            # 记录开始整理的日志
            self.log_message(f"开始整理文件夹: {source}")
            
            # 调用文件整理器执行实际的整理操作
            result = self.organizer.organize_folder(source, target)
            
            # 记录整理结果日志
            self.log_message(f"整理完成! 处理了 {result['total']} 个文件")
            self.log_message(f"成功: {result['success']}, 失败: {result['failed']}")
            
            # 整理完成后更新状态
            self.status_var.set("整理完成")
            
        except Exception as e:
            # 如果整理过程中发生异常，更新状态并记录错误
            self.logger.error(f"整理文件时出错: {e}")
            self.log_message(f"错误: {e}")
            self.status_var.set("整理失败")
            
    def quick_organize_desktop(self):
        """快速整理桌面
        
        自动获取当前用户的桌面路径，并启动文件整理操作
        这是一个便捷功能，用户无需手动选择桌面文件夹
        """
        # 获取当前用户的桌面路径
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        # 检查桌面路径是否存在
        if os.path.exists(desktop_path):
            # 将桌面路径设置到文件夹选择框中
            self.folder_var.set(desktop_path)
            # 启动文件整理操作
            self.organize_files()
        else:
            # 如果找不到桌面文件夹，显示错误消息
            messagebox.showerror("错误", "无法找到桌面文件夹")
            
    def toggle_reminder(self):
        """切换定时提醒状态
        
        根据当前提醒状态，开启或关闭定时提醒功能
        这是一个开关方法，用于在开启和关闭状态之间切换
        """
        # 如果当前未开启提醒，则开启
        if not self.reminder_enabled:
            self.start_reminder()
        else:
            # 如果当前已开启提醒，则关闭
            self.stop_reminder()
            
    def start_reminder(self):
        """开始定时提醒
        
        启动定时提醒功能，每2小时提醒用户整理文件
        更新按钮文本和状态显示，并安排第一次提醒
        """
        # 设置提醒状态为已启用
        self.reminder_enabled = True
        # 更新按钮文本为关闭提醒
        self.reminder_button.config(text="关闭定时提醒")
        # 更新状态显示
        self.status_var.set("定时提醒已开启")
        # 记录日志
        self.log_message("定时提醒已开启 - 每2小时提醒一次")
        
        # 安排第一次提醒（2小时后）
        self.schedule_next_reminder()
        
    def stop_reminder(self):
        """停止定时提醒
        
        关闭定时提醒功能，取消已安排的提醒任务
        更新按钮文本和状态显示
        """
        # 如果有正在等待的提醒任务，取消它
        if self.reminder_timer:
            self.root.after_cancel(self.reminder_timer)
            self.reminder_timer = None
            
        # 设置提醒状态为已禁用
        self.reminder_enabled = False
        # 更新按钮文本为开启提醒
        self.reminder_button.config(text="开启定时提醒")
        # 更新状态显示
        self.status_var.set("定时提醒已关闭")
        # 记录日志
        self.log_message("定时提醒已关闭")
        
    def schedule_next_reminder(self):
        """安排下一次提醒
        
        使用tkinter的after方法安排2小时后的提醒
        只有在提醒功能启用时才会安排下一次提醒
        """
        # 检查提醒功能是否仍然启用
        if self.reminder_enabled:
            # 安排2小时后的提醒（2小时 = 7200000毫秒）
            self.reminder_timer = self.root.after(7200000, self.show_reminder)
            
    def show_reminder(self):
        """显示整理提醒
        
        显示文件整理提醒通知，包含建议检查的文件夹
        显示提醒后自动安排下一次提醒
        """
        # 确认提醒功能仍然启用
        if self.reminder_enabled:
            # 显示提醒通知
            self.show_notification(
                "文件整理提醒", 
                "是时候整理一下文件了！\n\n建议检查：\n• 桌面文件\n• 下载文件夹\n• 临时文件"
            )
            # 记录提醒日志
            self.log_message("显示定时整理提醒")
            # 安排下一次提醒
            self.schedule_next_reminder()
        
    def open_config(self):
        """打开配置窗口
        
        创建并显示配置窗口，允许用户修改文件分类规则
        传入主窗口和配置管理器实例
        """
        # 创建配置窗口实例
        ConfigWindow(self.root, self.config_manager)
        
    def view_logs(self):
        """查看日志文件
        
        打开日志文件供用户查看详细的操作记录
        如果日志文件不存在，会创建日志目录并提示用户
        """
        # 构建日志文件路径
        log_file = os.path.join(os.getcwd(), "logs", "file_organizer.log")
        try:
            # 检查日志文件是否存在
            if os.path.exists(log_file):
                # 使用系统默认程序打开日志文件
                os.startfile(log_file)

                # 如果日志文件不存在，创建日志目录并提示用户
                log_dir = os.path.dirname(log_file)
                os.makedirs(log_dir, exist_ok=True)
                messagebox.showinfo("信息", f"日志文件不存在：{log_file}\n\n日志目录已创建，请先进行一些操作后再查看日志。")
        except Exception as e:
            # 如果打开日志文件失败，显示错误消息
            messagebox.showerror("错误", f"无法打开日志文件：{str(e)}")
            # 记录错误到日志系统
            self.logger.error(f"打开日志文件失败: {e}")
            
    def log_message(self, message):
        """在界面上显示日志消息
        
        Args:
            message (str): 要显示的日志消息
            
        在GUI界面的日志文本框中显示带时间戳的消息
        确保在主线程中更新UI组件
        """
        # 生成当前时间戳
        timestamp = datetime.now().strftime("%H:%M:%S")
        # 格式化日志条目，包含时间戳和消息
        log_entry = f"[{timestamp}] {message}\n"
        
        # 使用tkinter的after方法确保在主线程中更新UI
        # after(0, ...)会在下一个空闲时刻执行，保证线程安全
        self.root.after(0, self._update_log_text, log_entry)
        
    def stop_monitoring(self):
        """停止文件监控
        
        安全地停止watchdog文件监控器
        清理监控相关的资源和状态
        """
        try:
            # 检查是否存在监控器实例且不为空
            if hasattr(self, 'observer') and self.observer:
                # 停止监控器
                self.observer.stop()
                # 等待监控器线程结束
                self.observer.join()
                # 清空监控器引用
                self.observer = None
            # 设置监控状态为False
            self.monitoring = False
            # 记录停止监控的日志
            self.logger.info("文件监控已停止")
        except Exception as e:
            # 如果停止监控时发生异常，记录错误
            self.logger.error(f"停止监控时出错: {e}")
            
    def start_monitoring(self, folder_path):
        """开始文件监控
        
        Args:
            folder_path (str): 要监控的文件夹路径
            
        使用watchdog库监控指定文件夹的文件变化
        当有新文件创建时会在日志中显示
        """
        try:
            # 如果已经在监控，先停止当前监控
            if self.monitoring:
                self.stop_monitoring()
                
            # 导入watchdog相关模块
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler
            
            # 定义文件事件处理器类
            class FileHandler(FileSystemEventHandler):
                """文件系统事件处理器
                
                处理文件创建、修改、删除等事件
                """
                def __init__(self, gui):
                    """初始化处理器
                    
                    Args:
                        gui: GUI实例的引用，用于更新界面
                    """
                    self.gui = gui
                    
                def on_created(self, event):
                    """文件创建事件处理
                    
                    Args:
                        event: 文件系统事件对象
                    """
                    # 只处理文件创建事件，忽略文件夹创建
                    if not event.is_directory:
                        # 在GUI日志中显示新文件信息
                        self.gui.log_message(f"检测到新文件: {os.path.basename(event.src_path)}")
                        
            # 创建文件监控器实例
            self.observer = Observer()
            # 创建事件处理器实例
            handler = FileHandler(self)
            # 为指定路径安排监控，recursive=False表示不递归监控子文件夹
            self.observer.schedule(handler, folder_path, recursive=False)
            # 启动监控器
            self.observer.start()
            # 设置监控状态为True
            self.monitoring = True
            # 记录开始监控的日志
            self.logger.info(f"开始监控文件夹: {folder_path}")
            
        except Exception as e:
            # 如果启动监控时发生异常，记录错误并设置状态为False
            self.logger.error(f"启动监控时出错: {e}")
            self.monitoring = False
        
    def _update_log_text(self, message):
        """更新日志文本框
        
        Args:
            message (str): 要添加到日志文本框的消息
            
        在GUI的日志文本框中插入新消息并自动滚动到底部
        此方法必须在主线程中调用
        """
        # 在文本框末尾插入新消息
        self.log_text.insert(tk.END, message)
        # 自动滚动到文本框底部，显示最新消息
        self.log_text.see(tk.END)
        
    def create_tray_icon(self):
        """创建托盘图标
        
        使用PIL库创建一个简单的图标图像
        绘制文件夹样式的图标，包含"整理"文字
        如果创建失败，使用简单的蓝色方块作为备用图标
        """
        # 尝试创建自定义图标
        try:
            # 创建64x64像素的RGBA图像，背景为蓝色
            image = Image.new('RGBA', (64, 64), color=(74, 144, 226, 255))
            # 创建绘图对象
            draw = ImageDraw.Draw(image)
            
            # 绘制文件夹图标的各个部分
            # 绘制文件夹主体（矩形）
            draw.rectangle([10, 25, 54, 50], fill=(255, 255, 255, 255), outline=(46, 92, 138, 255), width=2)
            # 绘制文件夹标签（小矩形）
            draw.rectangle([10, 20, 30, 25], fill=(255, 255, 255, 255), outline=(46, 92, 138, 255), width=1)
            
            # 尝试添加文字
            try:
                # 尝试加载默认字体
                font = ImageDraw.ImageFont.load_default()
                # 在图标上绘制"整理"文字
                draw.text((18, 30), "整理", fill=(46, 92, 138, 255), font=font)
            except:
                # 如果字体加载失败，使用简单的"F"字符
                draw.text((18, 30), "F", fill=(46, 92, 138, 255))
                
            # 记录成功创建图标的日志
            self.logger.info("成功创建托盘图标")
            
        except Exception as e:
            # 如果创建图标失败，记录错误并使用备用图标
            self.logger.error(f"创建图标失败: {e}")
            # 创建最简单的备用图标（蓝色方块）
            image = Image.new('RGB', (32, 32), color='blue')
        
        # 创建托盘菜单，定义托盘图标的右键菜单项
        menu = pystray.Menu(
            # "快速整理" 子菜单
            pystray.MenuItem("快速整理", pystray.Menu(
                pystray.MenuItem("整理桌面", self.tray_organize_desktop),
                pystray.MenuItem("整理下载文件夹", self.tray_organize_downloads),
                pystray.MenuItem("整理文档文件夹", self.tray_organize_documents)
            )),
            # "文件统计" 子菜单
            pystray.MenuItem("文件统计", pystray.Menu(
                pystray.MenuItem("桌面文件统计", self.tray_stats_desktop),
                pystray.MenuItem("下载文件夹统计", self.tray_stats_downloads),
                pystray.MenuItem("系统垃圾文件扫描", self.tray_scan_junk)
            )),
            # "实用工具" 子菜单
            pystray.MenuItem("实用工具", pystray.Menu(
                pystray.MenuItem("清理回收站", self.tray_empty_recycle),
                pystray.MenuItem("清理临时文件", self.tray_clean_temp),
                pystray.MenuItem("查找重复文件", self.tray_find_duplicates)
            )),
            # 分隔线
            pystray.Menu.SEPARATOR,
            # "显示主窗口" 菜单项
            pystray.MenuItem("显示主窗口", self.show_window),
            # "退出" 菜单项
            pystray.MenuItem("退出", self.quit_app)
        )
        
        # 创建托盘图标实例
        self.tray_icon = pystray.Icon("文件整理工具", image, menu=menu)
        
    def hide_to_tray(self):
        """隐藏到系统托盘
        
        隐藏主窗口，并在系统托盘显示图标
        确保先停止现有托盘图标，然后重新创建以避免冲突
        """
        # 先停止现有的托盘图标（如果存在）
        if self.tray_icon:
            try:
                self.tray_icon.stop()
            except:
                pass  # 忽略停止时可能出现的错误
            self.tray_icon = None
            
        # 重新创建托盘图标
        self.create_tray_icon()
            
        # 隐藏主窗口
        self.root.withdraw()
        # 更新隐藏状态
        self.is_hidden = True
        
        # 在新线程中运行托盘图标，避免阻塞主UI线程
        threading.Thread(target=self.tray_icon.run, daemon=True).start()
        
    def show_window(self, icon=None, item=None):
        """显示主窗口
        
        从系统托盘恢复并显示主窗口
        将窗口置于顶层，确保用户可以看到
        同时停止托盘图标以避免重复创建
        """
        # 显示主窗口
        self.root.deiconify()
        # 将窗口置于顶层
        self.root.lift()
        # 更新隐藏状态
        self.is_hidden = False
        
        # 停止当前的托盘图标，避免重复创建导致的问题
        if self.tray_icon:
            try:
                self.tray_icon.stop()
            except:
                pass  # 忽略停止时可能出现的错误
            self.tray_icon = None
        
    def on_closing(self):
        """窗口关闭事件处理
        
        当用户点击窗口关闭按钮时调用此方法
        负责安全地清理所有后台任务和资源，然后关闭窗口
        """
        try:
            # 检查并停止文件监控
            if hasattr(self, 'monitoring') and self.monitoring:
                self.stop_monitoring()
            # 检查并停止定时提醒
            if hasattr(self, 'reminder_enabled') and self.reminder_enabled:
                self.stop_reminder()
            # 检查并停止托盘图标
            if hasattr(self, 'tray_icon') and self.tray_icon:
                self.tray_icon.stop()
        except Exception as e:
            # 记录关闭过程中发生的任何错误
            self.logger.error(f"关闭程序时出错: {e}")
        finally:
            # 确保窗口最终被销毁
            self.root.destroy()
        
    def quit_app(self, icon=None, item=None):
        """退出应用程序
        
        从托盘菜单或程序内部调用，完全退出应用程序
        清理所有资源并强制结束进程，确保完全退出
        """
        # 记录退出日志
        self.logger.info("正在退出应用程序...")
        # 停止定时提醒
        if self.reminder_enabled:
            self.stop_reminder()
        # 停止托盘图标
        if self.tray_icon:
            self.tray_icon.stop()
        # 退出tkinter主循环
        self.root.quit()
        # 销毁主窗口
        self.root.destroy()
        # 强制结束进程，确保所有线程都已终止
        import os
        os._exit(0)
        
    def get_active_folder(self):
        """获取当前活动窗口的文件夹路径 (Windows特定)
        
        尝试通过多种方法获取当前Windows资源管理器活动窗口的文件夹路径
        方法1：使用COM接口 (Shell.Application)
        方法2：使用窗口标题和进程信息
        
        Returns:
            str or None: 如果成功获取到文件夹路径，则返回路径字符串，否则返回None
        """
        try:
            # --- 方法1: 通过COM接口 (Shell.Application) --- #
            try:
                # 导入win32com模块
                import win32com.client
                # 创建Shell.Application COM对象
                shell = win32com.client.Dispatch("Shell.Application")
                # 获取所有打开的窗口
                windows = shell.Windows()
                
                # 获取当前前台窗口的句柄
                active_hwnd = win32gui.GetForegroundWindow()
                self.logger.info(f"当前活动窗口句柄: {active_hwnd}")
                
                # 遍历所有窗口，查找与活动窗口句柄匹配的资源管理器窗口
                for window in windows:
                    try:
                        # 检查窗口句柄是否匹配
                        if hasattr(window, 'HWND') and window.HWND == active_hwnd:
                            # 获取窗口的URL格式位置
                            location = window.LocationURL
                            if location:
                                self.logger.info(f"找到活动窗口位置: {location}")
                                # 将 'file:///' 格式的URL转换为本地路径
                                if location.startswith('file:///'):
                                    import urllib.parse
                                    # 解码URL并移除 'file:///' 前缀
                                    path = urllib.parse.unquote(location[8:])
                                    # 将路径分隔符转换为Windows格式
                                    path = path.replace('/', '\\')
                                    # 验证路径是否存在且为文件夹
                                    if os.path.exists(path) and os.path.isdir(path):
                                        self.logger.info(f"通过Shell Application检测到活动文件夹: {path}")
                                        return path
                    except Exception as e:
                        # 忽略检查单个窗口时可能出现的错误
                        self.logger.debug(f"检查窗口时出错: {e}")
                        continue
            except Exception as e:
                # 如果COM方法整体失败，记录错误并继续尝试下一种方法
                self.logger.debug(f"Shell Application方法失败: {e}")
            
            # --- 方法2: 通过窗口标题和进程信息 --- #
            try:
                # 获取当前前台窗口句柄
                hwnd = win32gui.GetForegroundWindow()
                # 获取窗口所属进程ID
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                # 获取进程对象
                process = psutil.Process(pid)
                # 获取进程名称
                process_name = process.name().lower()
                
                self.logger.info(f"当前活动进程: {process_name}")
                
                # 检查进程是否为资源管理器
                if 'explorer.exe' in process_name:
                    # 获取窗口标题
                    window_title = win32gui.GetWindowText(hwnd)
                    self.logger.info(f"资源管理器窗口标题: '{window_title}'")
                    
                    # 尝试从窗口标题中解析路径
                    if window_title and window_title.strip():
                        # 检查路径是否存在
                        # Windows 10/11的资源管理器标题通常是 '文件夹名' 或 '文件夹名 - 文件资源管理器'
                        if ' - ' in window_title:
                            folder_name = window_title.split(' - ')[0].strip()
                        else:
                            folder_name = window_title.strip()
                        
                        self.logger.info(f"解析出的文件夹名: '{folder_name}'")
                        
                        # 尝试一些常见的路径组合来验证解析出的文件夹名
                        user_home = os.path.expanduser("~")
                        possible_paths = [
                            folder_name,  # 假设是完整路径
                            os.path.join(user_home, folder_name),  # 用户主目录下的文件夹
                            os.path.join(user_home, "Desktop", folder_name),  # 桌面上的文件夹
                            os.path.join(user_home, "Documents", folder_name),  # 文档里的文件夹
                            os.path.join(user_home, "Downloads", folder_name),  # 下载目录的文件夹
                            os.path.join("C:\\", folder_name),  # C盘根目录下的文件夹
                            os.path.join("D:\\", folder_name),  # D盘根目录下的文件夹
                        ]
                        
                        # 遍历可能的路径，找到存在的那个
                        for path in possible_paths:
                            if os.path.exists(path) and os.path.isdir(path):
                                self.logger.info(f"通过标题解析找到路径: {path}")
                                return path
                    
                    # 如果标题解析失败，尝试获取资源管理器进程的当前工作目录作为备选
                    try:
                        cwd = process.cwd()
                        if os.path.exists(cwd) and os.path.isdir(cwd):
                            self.logger.info(f"使用进程工作目录: {cwd}")
                            return cwd
                    except Exception as e:
                        self.logger.debug(f"获取进程工作目录失败: {e}")
            except Exception as e:
                self.logger.debug(f"窗口标题方法失败: {e}")
            
            # 如果所有方法都失败了，则返回None
            self.logger.warning("所有检测方法都失败，无法获取活动文件夹")
            return None
            
        except Exception as e:
            # 捕获任何未预料的异常
            self.logger.error(f"获取活动文件夹时发生严重错误: {e}")
            return None
            
    # --- 托盘菜单功能 --- #
    
    def tray_organize_desktop(self, icon=None, item=None):
        """托盘菜单项：整理桌面
        
        调用一个通用方法来整理桌面文件夹，并显示通知
        """
        self._organize_folder_with_notification(
            os.path.join(os.path.expanduser("~"), "Desktop"),
            "桌面"
        )
        
    def tray_organize_downloads(self, icon=None, item=None):
        """托盘菜单项：整理下载文件夹
        
        调用一个通用方法来整理下载文件夹，并显示通知
        """
        self._organize_folder_with_notification(
            os.path.join(os.path.expanduser("~"), "Downloads"),
            "下载文件夹"
        )
        
    def tray_organize_documents(self, icon=None, item=None):
        """托盘菜单项：整理文档文件夹
        
        调用一个通用方法来整理文档文件夹，并显示通知
        """
        self._organize_folder_with_notification(
            os.path.join(os.path.expanduser("~"), "Documents"),
            "文档文件夹"
        )
        
    def _organize_folder_with_notification(self, folder_path, folder_name):
        """通用整理逻辑：整理指定文件夹并发送桌面通知

        Args:
            folder_path (str): 要整理的文件夹的完整路径
            folder_name (str): 文件夹的友好名称，用于通知
        """
        try:
            # 检查文件夹是否存在
            if not os.path.exists(folder_path):
                self.show_notification("错误", f"{folder_name}不存在")
                return
                
            # 确定目标文件夹路径
            target = os.path.join(folder_path, "分类文件")
            os.makedirs(target, exist_ok=True)
            
            # 调用核心整理逻辑
            moved_files = self.organizer.organize_folder(folder_path, target)
            
            # 根据整理结果显示不同的通知
            if moved_files:
                message = f"成功整理{folder_name} {len(moved_files)} 个文件"
                self.show_notification("整理完成", message)
            else:
                self.show_notification("整理完成", f"{folder_name}没有需要整理的文件")
                
        except Exception as e:
            # 记录并通知整理过程中发生的错误
            self.logger.error(f"整理{folder_name}时出错: {e}")
            self.show_notification("错误", f"整理{folder_name}失败: {e}")
            
    # --- 托盘文件统计功能 --- #
    
    def tray_stats_desktop(self, icon=None, item=None):
        """托盘菜单项：统计桌面文件
        
        调用通用统计方法来分析桌面文件夹
        """
        self._show_folder_stats(
            os.path.join(os.path.expanduser("~"), "Desktop"),
            "桌面"
        )
        
    def tray_stats_downloads(self, icon=None, item=None):
        """托盘菜单项：统计下载文件夹
        
        调用通用统计方法来分析下载文件夹
        """
        self._show_folder_stats(
            os.path.join(os.path.expanduser("~"), "Downloads"),
            "下载文件夹"
        )
        
    def _show_folder_stats(self, folder_path, folder_name):
        """通用统计逻辑：分析文件夹内容并以通知形式显示统计信息

        Args:
            folder_path (str): 要统计的文件夹的完整路径
            folder_name (str): 文件夹的友好名称，用于通知
        """
        try:
            # 检查文件夹是否存在
            if not os.path.exists(folder_path):
                self.show_notification("错误", f"{folder_name}不存在")
                return
                
            # 初始化统计变量
            file_count = 0
            folder_count = 0
            total_size = 0
            file_types = {}
            
            # 遍历文件夹内容
            for item in os.listdir(folder_path):
                item_path = os.path.join(folder_path, item)
                if os.path.isfile(item_path):
                    file_count += 1
                    size = os.path.getsize(item_path)
                    total_size += size
                    
                    # 按扩展名统计文件类型
                    ext = os.path.splitext(item)[1].lower()
                    if ext:
                        file_types[ext] = file_types.get(ext, 0) + 1
                elif os.path.isdir(item_path):
                    folder_count += 1
                    
            # 将总大小转换为MB
            size_mb = total_size / (1024 * 1024)
            
            # 找出最常见的三种文件类型
            top_types = sorted(file_types.items(), key=lambda x: x[1], reverse=True)[:3]
            types_str = ", ".join([f"{ext}({count})" for ext, count in top_types])
            
            # 构建通知消息
            message = f"{folder_name}统计:\n\n文件: {file_count} 个\n文件夹: {folder_count} 个\n总大小: {size_mb:.1f} MB\n\n主要类型: {types_str}"
            self.show_notification(f"{folder_name}统计", message)
            
        except Exception as e:
            # 记录并通知统计过程中发生的错误
            self.logger.error(f"统计{folder_name}时出错: {e}")
            self.show_notification("错误", f"统计{folder_name}失败: {e}")
            
    # --- 托盘实用工具 --- #
    
    def tray_scan_junk(self, icon=None, item=None):
        """托盘菜单项：扫描垃圾文件
        
        在用户常用目录中扫描并报告潜在的垃圾文件
        """
        try:
            # 定义常见的垃圾文件模式
            junk_patterns = [
                "*.tmp", "*.temp", "*.log", "*.bak", "*.old",
                "Thumbs.db", "desktop.ini", ".DS_Store"  # 包含macOS的垃圾文件
            ]
            
            # 初始化找到的垃圾文件列表
            junk_files = []
            # 定义要扫描的常用路径
            scan_paths = [
                os.path.join(os.path.expanduser("~"), "Desktop"),
                os.path.join(os.path.expanduser("~"), "Downloads"),
                os.path.join(os.path.expanduser("~"), "Documents")
            ]
            
            # 遍历路径和模式进行扫描
            for scan_path in scan_paths:
                if os.path.exists(scan_path):
                    for pattern in junk_patterns:
                        import glob
                        matches = glob.glob(os.path.join(scan_path, pattern))
                        junk_files.extend(matches)
                        
            # 根据扫描结果构建通知消息
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
            
    def tray_empty_recycle(self, icon=None, item=None):
        """托盘菜单项：清空回收站 (Windows特定)
        
        使用winshell库来清空回收站
        """
        try:
            # 导入winshell库（仅在需要时）
            import winshell
            # 调用清空回收站功能，不显示确认对话框、进度和声音
            winshell.recycle_bin().empty(confirm=False, show_progress=False, sound=False)
            self.show_notification("清理完成", "回收站已清空")
        except ImportError:
            # 如果winshell未安装，则提示用户
            self.show_notification("错误", "需要安装winshell模块 (pip install winshell)")
        except Exception as e:
            self.logger.error(f"清理回收站时出错: {e}")
            self.show_notification("错误", f"清理回收站失败: {e}")
            
    def tray_clean_temp(self, icon=None, item=None):
        """托盘菜单项：清理系统临时文件
        
        删除当前用户的临时文件夹中的所有文件
        """
        try:
            # 获取系统临时文件夹路径
            import tempfile
            temp_dir = tempfile.gettempdir()
            
            # 初始化清理计数器
            cleaned_count = 0
            cleaned_size = 0
            
            # 遍历临时文件夹中的所有项目
            for item in os.listdir(temp_dir):
                item_path = os.path.join(temp_dir, item)
                try:
                    # 只处理文件
                    if os.path.isfile(item_path):
                        size = os.path.getsize(item_path)
                        os.remove(item_path)
                        cleaned_count += 1
                        cleaned_size += size
                except Exception:
                    # 忽略无法删除的文件（可能正在被使用）
                    continue
                    
            # 构建并显示清理结果通知
            size_mb = cleaned_size / (1024 * 1024)
            message = f"清理完成\n\n删除文件: {cleaned_count} 个\n释放空间: {size_mb:.1f} MB"
            self.show_notification("临时文件清理", message)
            
        except Exception as e:
            self.logger.error(f"清理临时文件时出错: {e}")
            self.show_notification("错误", f"清理临时文件失败: {e}")
            
    def tray_find_duplicates(self, icon=None, item=None):
        """托盘菜单项：查找重复文件
        
        通过计算文件内容的MD5哈希值来查找常用目录中的重复文件
        """
        try:
            import hashlib
            
            # 定义要扫描的路径
            scan_paths = [
                os.path.join(os.path.expanduser("~"), "Desktop"),
                os.path.join(os.path.expanduser("~"), "Downloads"),
                os.path.join(os.path.expanduser("~"), "Documents")
            ]
            
            # 初始化哈希字典和重复文件列表
            file_hashes = {}
            duplicates = []
            
            # 遍历路径进行扫描
            for scan_path in scan_paths:
                if not os.path.exists(scan_path):
                    continue
                    
                for item in os.listdir(scan_path):
                    item_path = os.path.join(scan_path, item)
                    if os.path.isfile(item_path):
                        try:
                            # 读取文件内容并计算MD5哈希
                            with open(item_path, 'rb') as f:
                                file_hash = hashlib.md5(f.read()).hexdigest()
                                
                            # 检查哈希是否已存在
                            if file_hash in file_hashes:
                                duplicates.append((item_path, file_hashes[file_hash]))
                            else:
                                file_hashes[file_hash] = item_path
                        except Exception:
                            # 忽略无法读取的文件
                            continue
                            
            # 构建并显示扫描结果通知
            if duplicates:
                message = f"发现 {len(duplicates)} 组重复文件\n\n建议手动检查和删除"
            else:
                message = "未发现重复文件"
                
            self.show_notification("重复文件扫描", message)
            
        except Exception as e:
            self.logger.error(f"查找重复文件时出错: {e}")
            self.show_notification("错误", f"查找重复文件失败: {e}")
            
    def show_notification(self, title, message):
        """显示一个tkinter的消息提示框

        为了防止阻塞GUI主线程，此方法使用 root.after(0, ...) 
        将消息框的显示安排到下一个GUI事件循环中执行。

        Args:
            title (str): 消息框的标题
            message (str): 消息框显示的内容
        """
        try:
            # 定义一个内部函数来显示对话框
            def show_dialog():
                try:
                    messagebox.showinfo(title, message)
                    self.logger.info(f"已显示通知对话框: {title} - {message}")
                except Exception as e:
                    self.logger.error(f"显示对话框时出错: {e}")
            
            # 使用after方法在主线程中安全地调用GUI更新
            self.root.after(0, show_dialog)
            
        except Exception as e:
            self.logger.error(f"安排通知时出错: {e}")
    
    def run(self):
        """启动并运行GUI主循环
        
        这是一个阻塞操作，会一直运行直到窗口被关闭。
        在主循环结束后，会执行一些清理工作。
        """
        try:
            # 启动tkinter事件循环
            self.root.mainloop()
        finally:
            # 确保在程序退出时停止所有后台服务
            if self.reminder_enabled:
                self.stop_reminder()
            if self.tray_icon:
                self.tray_icon.stop()

# --- 配置窗口类 --- #

class ConfigWindow:
    """配置窗口类
    
    负责创建和管理用于修改分类规则的配置窗口。
    """
    
    def __init__(self, parent, config_manager):
        """初始化配置窗口

        Args:
            parent (tk.Widget): 父窗口
            config_manager (ConfigManager): 配置管理器实例
        """
        self.config_manager = config_manager
        
        # 创建顶层窗口
        self.window = tk.Toplevel(parent)
        self.window.title("配置规则")
        self.window.geometry("600x400")
        # 设置为瞬态窗口，并获取焦点
        self.window.transient(parent)
        self.window.grab_set()
        
        # 初始化UI并加载配置
        self.setup_ui()
        self.load_config()
        
    def setup_ui(self):
        """创建并布局配置窗口的UI组件"""
        # 主框架
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 规则显示区域
        rules_frame = ttk.LabelFrame(main_frame, text="文件类型分类规则", padding="5")
        rules_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 使用Treeview显示规则
        columns = ('category', 'extensions')
        self.tree = ttk.Treeview(rules_frame, columns=columns, show='headings', height=10)
        
        # 设置列标题
        self.tree.heading('category', text='分类名称')
        self.tree.heading('extensions', text='文件扩展名 (逗号分隔)')
        
        # 设置列宽
        self.tree.column('category', width=200)
        self.tree.column('extensions', width=300)
        
        # 添加垂直滚动条
        scrollbar = ttk.Scrollbar(rules_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # 布局Treeview和滚动条
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 底部按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        # 添加、编辑、删除、保存、取消按钮
        ttk.Button(button_frame, text="添加规则", command=self.add_rule).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="编辑规则", command=self.edit_rule).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="删除规则", command=self.delete_rule).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="保存", command=self.save_config).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="取消", command=self.window.destroy).pack(side=tk.RIGHT, padx=5)
        
    def load_config(self):
        """从配置管理器加载规则并显示在Treeview中"""
        # 获取当前配置
        # 获取当前的配置字典
        config = self.config_manager.get_config()
        # 更新配置中的'file_types'部分

        # 调用ConfigManager保存更新后的配置
        rules = config.get('file_types', {})
        
        # 将规则逐条插入到Treeview
        for category, extensions in rules.items():
            ext_str = ', '.join(extensions)  # 将扩展名列表转换为字符串
            self.tree.insert('', tk.END, values=(category, ext_str))
            
    def add_rule(self):
        """处理“添加规则”按钮点击事件，打开编辑对话框"""
        # 调用编辑对话框，但不传递任何现有值
        self.edit_rule_dialog()
        
    def edit_rule(self):
        """处理“编辑规则”按钮点击事件，打开编辑对话框并填充现有值"""
        # 获取当前选中的规则
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请选择要编辑的规则")
            return
            
        # 获取选中项的数据并打开编辑对话框
        item = selection[0]
        values = self.tree.item(item, 'values')
        self.edit_rule_dialog(item, values[0], values[1])
        
    def delete_rule(self):
        """处理“删除规则”按钮点击事件，删除选中的规则"""
        # 获取当前选中的规则
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请选择要删除的规则")
            return
            
        if messagebox.askyesno("确认", "确定要删除选中的规则吗？"):
            self.tree.delete(selection[0])
            
    def edit_rule_dialog(self, item=None, category="", extensions=""):
        """
        创建并显示用于添加或编辑规则的对话框。

        Args:
            item: Treeview中的项，如果是编辑模式则提供，默认为None（添加模式）。
            category (str): 要编辑的分类名称，默认为空字符串。
            extensions (str): 要编辑的扩展名列表（逗号分隔），默认为空字符串。
        """
        """编辑规则对话框"""
        # 创建一个顶级窗口作为对话框
        dialog = tk.Toplevel(self.window)
        # 设置对话框标题
        dialog.title("编辑规则")
        # 设置对话框大小
        dialog.geometry("400x200")
        # 将对话框设置为父窗口的瞬态窗口，使其显示在父窗口之上
        dialog.transient(self.window)
        # 捕获所有事件，实现模态对话框效果
        dialog.grab_set()
        
        # 创建“分类名称”标签和输入框
        # ttk.Label用于显示文本标签
        # tk.StringVar用于绑定输入框的值，并预设当前分类名称
        ttk.Label(dialog, text="分类名称:").pack(pady=5)
        # 创建一个字符串变量，并用传入的category值初始化

        # 创建一个输入框，并将其与字符串变量绑定
        category_var = tk.StringVar(value=category)
        ttk.Entry(dialog, textvariable=category_var, width=40).pack(pady=5)
        
        # 创建“文件扩展名”标签和输入框
        # 提示用户扩展名应以逗号分隔
        ttk.Label(dialog, text="文件扩展名 (用逗号分隔):").pack(pady=5)
        # 创建一个字符串变量，并用传入的extensions值初始化

        # 创建一个输入框，并将其与字符串变量绑定
        extensions_var = tk.StringVar(value=extensions)
        ttk.Entry(dialog, textvariable=extensions_var, width=40).pack(pady=5)
        
        # 创建一个框架来容纳“保存”和“取消”按钮
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=20)
        
        def save_rule():
            """定义在对话框中点击“保存”按钮时执行的内部函数"""
            # 获取并清理分类名称和扩展名输入
            cat = category_var.get().strip()

            ext = extensions_var.get().strip()
            
            # 检查输入是否为空
            if not cat or not ext:
                messagebox.showerror("错误", "请填写完整信息")
                return
                return
                
            # 如果item存在，则表示是编辑模式，更新现有规则
            if item:
                self.tree.item(item, values=(cat, ext))
            # 否则是添加模式，插入新规则
            else:
                self.tree.insert('', tk.END, values=(cat, ext))
                
            # 保存后销毁对话框
            dialog.destroy()
            
        # 创建“保存”按钮，并绑定save_rule函数
        ttk.Button(button_frame, text="保存", command=save_rule).pack(side=tk.LEFT, padx=5)
        # 创建“取消”按钮，点击时直接销毁对话框
        ttk.Button(button_frame, text="取消", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        
    def save_config(self):
        """将Treeview中的所有规则保存到配置文件中"""
        """保存配置"""
        # 创建一个空字典来存储规则
        rules = {}
        # 遍历Treeview中的所有顶级项
        for item in self.tree.get_children():
            # 获取每个项的值（分类名称和扩展名）
            values = self.tree.item(item, 'values')
            # 提取分类名称
            category = values[0]
            # 提取扩展名字符串，并将其分割成列表

            extensions = [ext.strip() for ext in values[1].split(',')]
            # 将分类和对应的扩展名列表存入字典
            rules[category] = extensions
            
        config = self.config_manager.get_config()
        config['file_types'] = rules
        self.config_manager.save_config(config)
        
        # 显示保存成功的消息提示
        messagebox.showinfo("成功", "配置已保存")
        # 关闭配置窗口
        self.window.destroy()


def main():
    """应用程序的主入口函数"""
    """主函数"""
    # 确保日志和配置目录存在，如果不存在则创建
    # exist_ok=True表示如果目录已存在，不会引发错误
    os.makedirs("logs", exist_ok=True)

    os.makedirs("config", exist_ok=True)
    
    # 创建FileOrganizerGUI类的实例

    # 运行应用程序的主事件循环
    app = FileOrganizerGUI()
    app.run()


# 当该脚本作为主程序直接运行时，执行以下代码
if __name__ == "__main__":
    # 调用主函数，启动应用程序
    main()