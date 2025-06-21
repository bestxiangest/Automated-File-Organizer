#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志设置模块
提供统一的日志记录功能
"""

import os
import logging
import logging.handlers
from datetime import datetime
from typing import Optional


def setup_logger(name: str = "FileOrganizer", 
                 log_file: str = "logs/file_organizer.log",
                 level: str = "INFO",
                 max_size: int = 10485760,  # 10MB
                 backup_count: int = 5,
                 console_output: bool = True) -> logging.Logger:
    """
    设置日志记录器
    
    Args:
        name: 日志记录器名称
        log_file: 日志文件路径
        level: 日志级别
        max_size: 日志文件最大大小（字节）
        backup_count: 备份文件数量
        console_output: 是否输出到控制台
        
    Returns:
        配置好的日志记录器
    """
    # 创建日志记录器
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # 如果已经有处理器，先清除
    if logger.handlers:
        logger.handlers.clear()
    
    # 创建日志目录 - 使用绝对路径
    if not os.path.isabs(log_file):
        log_file = os.path.join(os.getcwd(), log_file)
    
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    
    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 文件处理器（带轮转）
    try:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, 
            maxBytes=max_size, 
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(getattr(logging, level.upper(), logging.INFO))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"创建文件日志处理器失败: {e}")
    
    # 控制台处理器
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    return logger


class FileOrganizerLogger:
    """
    文件整理器专用日志记录器
    提供更丰富的日志记录功能
    """
    
    def __init__(self, config_manager=None):
        self.config_manager = config_manager
        self.logger = self._setup_logger()
        
    def _setup_logger(self) -> logging.Logger:
        """根据配置设置日志记录器"""
        if self.config_manager:
            config = self.config_manager.get_config()
            logging_config = config.get('logging', {})
            
            return setup_logger(
                name="FileOrganizer",
                log_file=logging_config.get('file', 'logs/file_organizer.log'),
                level=logging_config.get('level', 'INFO'),
                max_size=logging_config.get('max_size', 10485760),
                backup_count=logging_config.get('backup_count', 5)
            )
        else:
            return setup_logger()
    
    def log_file_operation(self, operation: str, source: str, target: str = None, 
                          success: bool = True, error: str = None):
        """
        记录文件操作日志
        
        Args:
            operation: 操作类型（move, copy, delete等）
            source: 源文件路径
            target: 目标文件路径
            success: 操作是否成功
            error: 错误信息
        """
        if success:
            if target:
                self.logger.info(f"文件{operation}成功: {source} -> {target}")
            else:
                self.logger.info(f"文件{operation}成功: {source}")
        else:
            if target:
                self.logger.error(f"文件{operation}失败: {source} -> {target}, 错误: {error}")
            else:
                self.logger.error(f"文件{operation}失败: {source}, 错误: {error}")
    
    def log_organization_start(self, source_dir: str, target_dir: str):
        """记录整理开始"""
        self.logger.info(f"开始整理文件夹: {source_dir} -> {target_dir}")
    
    def log_organization_end(self, stats: dict):
        """记录整理结束"""
        self.logger.info(
            f"文件整理完成 - 总计: {stats.get('total', 0)}, "
            f"成功: {stats.get('success', 0)}, "
            f"失败: {stats.get('failed', 0)}, "
            f"跳过: {stats.get('skipped', 0)}"
        )
    
    def log_monitoring_start(self, directory: str):
        """记录监控开始"""
        self.logger.info(f"开始监控目录: {directory}")
    
    def log_monitoring_stop(self):
        """记录监控停止"""
        self.logger.info("文件监控已停止")
    
    def log_config_change(self, change_description: str):
        """记录配置变更"""
        self.logger.info(f"配置变更: {change_description}")
    
    def log_error(self, error_msg: str, exception: Exception = None):
        """记录错误"""
        if exception:
            self.logger.error(f"{error_msg}: {str(exception)}", exc_info=True)
        else:
            self.logger.error(error_msg)
    
    def log_warning(self, warning_msg: str):
        """记录警告"""
        self.logger.warning(warning_msg)
    
    def log_info(self, info_msg: str):
        """记录信息"""
        self.logger.info(info_msg)
    
    def log_debug(self, debug_msg: str):
        """记录调试信息"""
        self.logger.debug(debug_msg)
    
    def error(self, error_msg: str, exc_info: bool = False):
        """记录错误（兼容性方法）"""
        self.logger.error(error_msg, exc_info=exc_info)
    
    def info(self, info_msg: str):
        """记录信息（兼容性方法）"""
        self.logger.info(info_msg)
    
    def warning(self, warning_msg: str):
        """记录警告（兼容性方法）"""
        self.logger.warning(warning_msg)
    
    def debug(self, debug_msg: str):
        """记录调试信息（兼容性方法）"""
        self.logger.debug(debug_msg)
    
    def get_recent_logs(self, lines: int = 100) -> list:
        """
        获取最近的日志记录
        
        Args:
            lines: 要获取的行数
            
        Returns:
            日志行列表
        """
        log_file = "logs/file_organizer.log"
        if self.config_manager:
            config = self.config_manager.get_config()
            log_file = config.get('logging', {}).get('file', log_file)
        
        try:
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    all_lines = f.readlines()
                    return all_lines[-lines:] if len(all_lines) > lines else all_lines
        except Exception as e:
            self.logger.error(f"读取日志文件失败: {e}")
        
        return []
    
    def clear_old_logs(self, days: int = 30):
        """
        清理旧的日志文件
        
        Args:
            days: 保留天数
        """
        log_dir = "logs"
        if self.config_manager:
            config = self.config_manager.get_config()
            log_file = config.get('logging', {}).get('file', 'logs/file_organizer.log')
            log_dir = os.path.dirname(log_file)
        
        try:
            if os.path.exists(log_dir):
                current_time = datetime.now()
                
                for filename in os.listdir(log_dir):
                    if filename.endswith('.log') or filename.endswith('.log.1'):
                        file_path = os.path.join(log_dir, filename)
                        file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                        
                        if (current_time - file_time).days > days:
                            os.remove(file_path)
                            self.logger.info(f"删除旧日志文件: {filename}")
        except Exception as e:
            self.logger.error(f"清理旧日志文件失败: {e}")
    
    def export_logs(self, output_file: str, start_date: str = None, end_date: str = None) -> bool:
        """
        导出日志到文件
        
        Args:
            output_file: 输出文件路径
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            
        Returns:
            是否成功导出
        """
        try:
            logs = self.get_recent_logs(10000)  # 获取更多日志
            
            filtered_logs = []
            for log_line in logs:
                # 简单的日期过滤（可以改进）
                if start_date or end_date:
                    # 这里可以添加更复杂的日期过滤逻辑
                    pass
                filtered_logs.append(log_line)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.writelines(filtered_logs)
            
            self.logger.info(f"日志导出成功: {output_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"导出日志失败: {e}")
            return False
    
    def get_log_statistics(self) -> dict:
        """
        获取日志统计信息
        
        Returns:
            包含统计信息的字典
        """
        stats = {
            'total_lines': 0,
            'error_count': 0,
            'warning_count': 0,
            'info_count': 0,
            'file_operations': 0
        }
        
        try:
            logs = self.get_recent_logs(10000)
            
            for log_line in logs:
                stats['total_lines'] += 1
                
                if 'ERROR' in log_line:
                    stats['error_count'] += 1
                elif 'WARNING' in log_line:
                    stats['warning_count'] += 1
                elif 'INFO' in log_line:
                    stats['info_count'] += 1
                
                if '文件' in log_line and ('成功' in log_line or '失败' in log_line):
                    stats['file_operations'] += 1
                    
        except Exception as e:
            self.logger.error(f"获取日志统计失败: {e}")
        
        return stats


# 创建全局日志记录器实例
_global_logger = None


def get_logger() -> logging.Logger:
    """获取全局日志记录器"""
    global _global_logger
    if _global_logger is None:
        _global_logger = setup_logger()
    return _global_logger


def log_exception(func):
    """
    装饰器：自动记录函数异常
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger = get_logger()
            logger.error(f"函数 {func.__name__} 执行失败: {str(e)}", exc_info=True)
            raise
    return wrapper