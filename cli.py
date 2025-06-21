#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
命令行接口模块
提供命令行方式使用文件整理工具
"""

import os
import sys
import argparse
import time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from file_organizer import FileOrganizer
from config_manager import ConfigManager
from logger_setup import setup_logger, FileOrganizerLogger


class CLIFileMonitorHandler(FileSystemEventHandler):
    """命令行模式的文件监控处理器"""
    
    def __init__(self, organizer, source_dir, target_dir, logger):
        self.organizer = organizer
        self.source_dir = source_dir
        self.target_dir = target_dir
        self.logger = logger
        
    def on_created(self, event):
        """文件创建事件"""
        if not event.is_directory:
            # 等待文件写入完成
            time.sleep(1)
            
            try:
                result = self.organizer.organize_file(event.src_path, self.target_dir)
                if result:
                    print(f"✓ 自动整理: {os.path.basename(event.src_path)} -> {result}")
                    self.logger.log_file_operation("自动整理", event.src_path, result)
            except Exception as e:
                print(f"✗ 自动整理失败: {os.path.basename(event.src_path)} - {e}")
                self.logger.log_error(f"自动整理失败: {os.path.basename(event.src_path)}", e)


class FileOrganizerCLI:
    """文件整理工具命令行接口"""
    
    def __init__(self):
        self.config_manager = ConfigManager()
        self.logger = FileOrganizerLogger(self.config_manager)
        self.organizer = FileOrganizer(self.config_manager, self.logger)
        
    def create_parser(self):
        """创建命令行参数解析器"""
        parser = argparse.ArgumentParser(
            description="个人文件自动化整理归档工具",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""示例用法:
  %(prog)s organize /path/to/folder
  %(prog)s monitor /path/to/folder
  %(prog)s preview /path/to/folder
  %(prog)s stats /path/to/directory
  %(prog)s config --list
            """
        )
        
        subparsers = parser.add_subparsers(dest='command', help='可用命令')
        
        # organize 命令
        organize_parser = subparsers.add_parser('organize', help='整理文件夹')
        organize_parser.add_argument('folder', help='要整理的文件夹路径')
        organize_parser.add_argument('--dry-run', action='store_true', help='预览模式，不实际移动文件')
        
        # monitor 命令
        monitor_parser = subparsers.add_parser('monitor', help='监控文件夹')
        monitor_parser.add_argument('folder', help='要监控的文件夹路径')
        monitor_parser.add_argument('--recursive', action='store_true', default=False, help='递归监控子目录')
        
        # preview 命令
        preview_parser = subparsers.add_parser('preview', help='预览整理结果')
        preview_parser.add_argument('folder', help='要预览整理的文件夹路径')
        preview_parser.add_argument('--limit', type=int, default=50, help='显示的最大文件数')
        
        # stats 命令
        stats_parser = subparsers.add_parser('stats', help='显示文件统计信息')
        stats_parser.add_argument('directory', help='要统计的目录路径')
        
        # config 命令
        config_parser = subparsers.add_parser('config', help='配置管理')
        config_group = config_parser.add_mutually_exclusive_group(required=True)
        config_group.add_argument('--list', action='store_true', help='列出当前配置')
        config_group.add_argument('--reset', action='store_true', help='重置为默认配置')
        config_group.add_argument('--export', metavar='FILE', help='导出配置到文件')
        config_group.add_argument('--import', metavar='FILE', dest='import_file', help='从文件导入配置')
        config_group.add_argument('--add-rule', nargs=2, metavar=('CATEGORY', 'EXTENSIONS'), 
                                help='添加文件类型规则 (扩展名用逗号分隔)')
        
        # logs 命令
        logs_parser = subparsers.add_parser('logs', help='日志管理')
        logs_group = logs_parser.add_mutually_exclusive_group(required=True)
        logs_group.add_argument('--show', type=int, metavar='LINES', default=50, help='显示最近的日志行数')
        logs_group.add_argument('--export', metavar='FILE', help='导出日志到文件')
        logs_group.add_argument('--clear', action='store_true', help='清理旧日志')
        logs_group.add_argument('--stats', action='store_true', help='显示日志统计')
        
        # 全局选项
        parser.add_argument('--verbose', '-v', action='store_true', help='详细输出')
        parser.add_argument('--quiet', '-q', action='store_true', help='静默模式')
        parser.add_argument('--config-file', metavar='FILE', help='指定配置文件路径')
        
        return parser
    
    def run(self, args=None):
        """运行命令行接口"""
        parser = self.create_parser()
        args = parser.parse_args(args)
        
        # 设置日志级别
        if args.verbose:
            self.logger.logger.setLevel('DEBUG')
        elif args.quiet:
            self.logger.logger.setLevel('ERROR')
        
        # 使用自定义配置文件
        if args.config_file:
            self.config_manager = ConfigManager(args.config_file)
            self.logger = FileOrganizerLogger(self.config_manager)
            self.organizer = FileOrganizer(self.config_manager, self.logger)
        
        # 执行命令
        try:
            if args.command == 'organize':
                self.cmd_organize(args)
            elif args.command == 'monitor':
                self.cmd_monitor(args)
            elif args.command == 'preview':
                self.cmd_preview(args)
            elif args.command == 'stats':
                self.cmd_stats(args)
            elif args.command == 'config':
                self.cmd_config(args)
            elif args.command == 'logs':
                self.cmd_logs(args)
            else:
                parser.print_help()
        except KeyboardInterrupt:
            print("\n操作已取消")
            sys.exit(0)
        except Exception as e:
            print(f"错误: {e}")
            if args.verbose:
                import traceback
                traceback.print_exc()
            sys.exit(1)
    
    def cmd_organize(self, args):
        """执行整理命令"""
        folder = os.path.abspath(args.folder)
        
        if not os.path.exists(folder):
            raise FileNotFoundError(f"目录不存在: {folder}")
        
        if args.dry_run:
            print("预览模式 - 不会实际移动文件")
            results = self.organizer.preview_organization(folder, folder)
            self._print_preview_results(results, args.get('limit', 50))
        else:
            print(f"开始整理文件夹: {folder}")
            
            # 显示进度
            import threading
            stop_progress = threading.Event()
            progress_thread = threading.Thread(
                target=self._show_progress, 
                args=(stop_progress,), 
                daemon=True
            )
            progress_thread.start()
            
            try:
                result = self.organizer.organize_folder(folder, folder)
                stop_progress.set()
                
                print(f"\n整理完成!")
                print(f"总计文件: {result['total']}")
                print(f"成功整理: {result['success']}")
                print(f"整理失败: {result['failed']}")
                print(f"跳过文件: {result['skipped']}")
                
            finally:
                stop_progress.set()
    
    def cmd_monitor(self, args):
        """执行监控命令"""
        folder = os.path.abspath(args.folder)
        
        if not os.path.exists(folder):
            raise FileNotFoundError(f"监控目录不存在: {folder}")
        
        print(f"开始监控目录: {folder}")
        print("新文件将在该目录内自动整理")
        print("按 Ctrl+C 停止监控")
        
        # 创建监控处理器
        event_handler = CLIFileMonitorHandler(self.organizer, folder, folder, self.logger)
        
        # 创建观察者
        observer = Observer()
        observer.schedule(event_handler, folder, recursive=args.recursive)
        observer.start()
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n停止监控...")
        finally:
            observer.stop()
            observer.join()
    
    def cmd_preview(self, args):
        """执行预览命令"""
        folder = os.path.abspath(args.folder)
        
        if not os.path.exists(folder):
            raise FileNotFoundError(f"目录不存在: {folder}")
        
        print(f"预览整理结果: {folder}")
        results = self.organizer.preview_organization(folder, folder)
        self._print_preview_results(results, args.limit)
    
    def cmd_stats(self, args):
        """执行统计命令"""
        directory = os.path.abspath(args.directory)
        
        if not os.path.exists(directory):
            raise FileNotFoundError(f"目录不存在: {directory}")
        
        print(f"分析目录: {directory}")
        stats = self.organizer.get_file_statistics(directory)
        
        print(f"\n文件统计信息:")
        print(f"总文件数: {stats['total_files']}")
        print(f"总大小: {self._format_size(stats['total_size'])}")
        
        print(f"\n按分类统计:")
        for category, count in sorted(stats['categories'].items()):
            print(f"  {category}: {count} 个文件")
        
        print(f"\n按扩展名统计 (前10):")
        sorted_types = sorted(stats['file_types'].items(), key=lambda x: x[1], reverse=True)
        for ext, count in sorted_types[:10]:
            ext_display = ext if ext else "(无扩展名)"
            print(f"  {ext_display}: {count} 个文件")
    
    def cmd_config(self, args):
        """执行配置命令"""
        if args.list:
            self._print_config()
        elif args.reset:
            self.config_manager.reset_to_default()
            self.config_manager.save_config()
            print("配置已重置为默认值")
        elif args.export:
            if self.config_manager.export_config(args.export):
                print(f"配置已导出到: {args.export}")
            else:
                print("导出配置失败")
        elif args.import_file:
            if self.config_manager.import_config(args.import_file):
                self.config_manager.save_config()
                print(f"配置已从 {args.import_file} 导入")
            else:
                print("导入配置失败")
        elif args.add_rule:
            category, extensions = args.add_rule
            ext_list = [ext.strip() for ext in extensions.split(',')]
            self.config_manager.add_file_type_rule(category, ext_list)
            self.config_manager.save_config()
            print(f"已添加规则: {category} -> {ext_list}")
    
    def cmd_logs(self, args):
        """执行日志命令"""
        if hasattr(args, 'show') and args.show:
            logs = self.logger.get_recent_logs(args.show)
            print(f"最近 {len(logs)} 行日志:")
            for log_line in logs:
                print(log_line.rstrip())
        elif args.export:
            if self.logger.export_logs(args.export):
                print(f"日志已导出到: {args.export}")
            else:
                print("导出日志失败")
        elif args.clear:
            self.logger.clear_old_logs()
            print("旧日志已清理")
        elif args.stats:
            stats = self.logger.get_log_statistics()
            print("日志统计信息:")
            print(f"  总行数: {stats['total_lines']}")
            print(f"  错误数: {stats['error_count']}")
            print(f"  警告数: {stats['warning_count']}")
            print(f"  信息数: {stats['info_count']}")
            print(f"  文件操作数: {stats['file_operations']}")
    
    def _print_config(self):
        """打印当前配置"""
        config = self.config_manager.get_config()
        summary = self.config_manager.get_config_summary()
        
        print("当前配置:")
        print(f"  文件分类数: {summary['total_categories']}")
        print(f"  支持扩展名数: {summary['total_extensions']}")
        print(f"  按日期组织: {summary['organize_by_date']}")
        print(f"  默认分类: {summary['default_category']}")
        print(f"  重复文件策略: {summary['duplicate_strategy']}")
        
        print("\n文件类型规则:")
        for category, extensions in config.get('file_types', {}).items():
            print(f"  {category}: {', '.join(extensions)}")
    
    def _print_preview_results(self, results, limit):
        """打印预览结果"""
        if not results:
            print("没有找到需要整理的文件")
            return
        
        print(f"\n找到 {len(results)} 个文件需要整理:")
        
        # 按分类分组
        by_category = {}
        for result in results[:limit]:
            category = result['category']
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(result)
        
        for category, files in by_category.items():
            print(f"\n{category} ({len(files)} 个文件):")
            for file_info in files[:10]:  # 每个分类最多显示10个文件
                size_str = self._format_size(file_info['size'])
                print(f"  {file_info['file_name']} ({size_str})")
            
            if len(files) > 10:
                print(f"  ... 还有 {len(files) - 10} 个文件")
        
        if len(results) > limit:
            print(f"\n... 还有 {len(results) - limit} 个文件未显示")
    
    def _format_size(self, size_bytes):
        """格式化文件大小"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        import math
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return f"{s} {size_names[i]}"
    
    def _show_progress(self, stop_event):
        """显示进度动画"""
        chars = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
        i = 0
        while not stop_event.is_set():
            print(f"\r{chars[i % len(chars)]} 正在整理文件...", end="", flush=True)
            time.sleep(0.1)
            i += 1


def main():
    """命令行入口函数"""
    # 创建必要的目录
    os.makedirs("logs", exist_ok=True)
    os.makedirs("config", exist_ok=True)
    
    cli = FileOrganizerCLI()
    cli.run()


if __name__ == "__main__":
    main()