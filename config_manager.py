#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理模块
负责处理程序配置和用户自定义规则
"""

import os
import json
from typing import Dict, Any
from pathlib import Path


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file: str = "config/settings.json"):
        self.config_file = config_file
        self.config_dir = os.path.dirname(config_file)
        self._ensure_config_dir()
        self._config = self._load_default_config()
        self.load_config()
    
    def _ensure_config_dir(self):
        """确保配置目录存在"""
        if self.config_dir and not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir, exist_ok=True)
    
    def _load_default_config(self) -> Dict[str, Any]:
        """加载默认配置"""
        return {
            # 文件类型分类规则
            "file_types": {
                "图片": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".svg", ".webp", ".ico"],
                "文档": [".doc", ".docx", ".pdf", ".txt", ".rtf", ".odt", ".pages"],
                "表格": [".xls", ".xlsx", ".csv", ".ods", ".numbers"],
                "演示文稿": [".ppt", ".pptx", ".odp", ".key"],
                "音频": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma", ".m4a"],
                "视频": [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm", ".m4v"],
                "压缩包": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz"],
                "程序": [".exe", ".msi", ".dmg", ".pkg", ".deb", ".rpm", ".app"],
                "代码": [".py", ".js", ".html", ".css", ".java", ".cpp", ".c", ".php", ".rb", ".go", ".rs"],
                "字体": [".ttf", ".otf", ".woff", ".woff2", ".eot"]
            },
            
            # 默认分类（未匹配的文件）
            "default_category": "其他文件",
            
            # 是否按日期组织文件
            "organize_by_date": False,
            
            # 日期格式
            "date_format": "%Y-%m",
            
            # 是否创建子目录按文件类型进一步分类
            "create_subcategories": False,
            
            # 文件大小限制（字节），0表示无限制
            "max_file_size": 0,
            
            # 最小文件大小（字节），小于此大小的文件将被跳过
            "min_file_size": 0,
            
            # 排除的文件扩展名
            "excluded_extensions": [".tmp", ".temp", ".log", ".cache"],
            
            # 排除的文件名模式
            "excluded_patterns": ["Thumbs.db", ".DS_Store", "desktop.ini"],
            
            # 是否处理隐藏文件
            "process_hidden_files": False,
            
            # 重复文件处理策略: "skip", "rename", "replace"
            "duplicate_strategy": "rename",
            
            # 监控设置
            "monitor_settings": {
                "enabled": True,
                "delay": 1,  # 文件创建后等待时间（秒）
                "recursive": False  # 是否递归监控子目录
            },
            
            # 日志设置
            "logging": {
                "level": "INFO",
                "file": "logs/file_organizer.log",
                "max_size": 10485760,  # 10MB
                "backup_count": 5
            },
            
            # 界面设置
            "ui_settings": {
                "theme": "default",
                "language": "zh_CN",
                "window_size": "800x600",
                "remember_paths": True
            },
            
            # 最近使用的路径
            "recent_paths": {
                "source_dirs": [],
                "target_dirs": []
            },
            
            # 高级设置
            "advanced": {
                "use_file_hash": True,  # 是否使用文件哈希检查重复
                "hash_algorithm": "md5",  # 哈希算法
                "chunk_size": 4096,  # 读取文件的块大小
                "max_hash_file_size": 1048576,  # 最大哈希文件大小（1MB）
                "preserve_timestamps": True,  # 是否保留文件时间戳
                "create_shortcuts": False  # 是否创建快捷方式而不是移动文件
            }
        }
    
    def load_config(self) -> Dict[str, Any]:
        """从文件加载配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                    # 合并配置，文件配置覆盖默认配置
                    self._merge_config(self._config, file_config)
        except Exception as e:
            print(f"加载配置文件失败: {e}，使用默认配置")
        
        return self._config
    
    def save_config(self, config: Dict[str, Any] = None) -> bool:
        """保存配置到文件"""
        try:
            if config is not None:
                self._config = config
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存配置文件失败: {e}")
            return False
    
    def get_config(self) -> Dict[str, Any]:
        """获取当前配置"""
        return self._config.copy()
    
    def get_setting(self, key: str, default=None):
        """获取特定配置项"""
        keys = key.split('.')
        value = self._config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set_setting(self, key: str, value):
        """设置特定配置项"""
        keys = key.split('.')
        config = self._config
        
        # 导航到最后一级
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # 设置值
        config[keys[-1]] = value
    
    def _merge_config(self, base: Dict, override: Dict):
        """递归合并配置字典"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value
    
    def add_file_type_rule(self, category: str, extensions: list):
        """添加文件类型规则"""
        if "file_types" not in self._config:
            self._config["file_types"] = {}
        
        # 确保扩展名以点开头
        normalized_extensions = []
        for ext in extensions:
            if not ext.startswith('.'):
                ext = '.' + ext
            normalized_extensions.append(ext.lower())
        
        self._config["file_types"][category] = normalized_extensions
    
    def remove_file_type_rule(self, category: str):
        """删除文件类型规则"""
        if "file_types" in self._config and category in self._config["file_types"]:
            del self._config["file_types"][category]
    
    def get_file_categories(self) -> list:
        """获取所有文件分类"""
        return list(self._config.get("file_types", {}).keys())
    
    def get_extensions_for_category(self, category: str) -> list:
        """获取指定分类的文件扩展名"""
        return self._config.get("file_types", {}).get(category, [])
    
    def add_recent_path(self, path_type: str, path: str):
        """添加最近使用的路径"""
        if "recent_paths" not in self._config:
            self._config["recent_paths"] = {"source_dirs": [], "target_dirs": []}
        
        if path_type not in self._config["recent_paths"]:
            self._config["recent_paths"][path_type] = []
        
        paths = self._config["recent_paths"][path_type]
        
        # 如果路径已存在，先移除
        if path in paths:
            paths.remove(path)
        
        # 添加到开头
        paths.insert(0, path)
        
        # 限制最大数量
        max_recent = 10
        if len(paths) > max_recent:
            paths[:] = paths[:max_recent]
    
    def get_recent_paths(self, path_type: str) -> list:
        """获取最近使用的路径"""
        return self._config.get("recent_paths", {}).get(path_type, [])
    
    def validate_config(self) -> list:
        """验证配置的有效性"""
        errors = []
        
        # 检查必需的配置项
        required_keys = ["file_types", "default_category"]
        for key in required_keys:
            if key not in self._config:
                errors.append(f"缺少必需的配置项: {key}")
        
        # 检查文件类型配置
        if "file_types" in self._config:
            file_types = self._config["file_types"]
            if not isinstance(file_types, dict):
                errors.append("file_types 必须是字典类型")
            else:
                for category, extensions in file_types.items():
                    if not isinstance(extensions, list):
                        errors.append(f"分类 '{category}' 的扩展名必须是列表类型")
                    else:
                        for ext in extensions:
                            if not isinstance(ext, str):
                                errors.append(f"分类 '{category}' 中的扩展名必须是字符串")
        
        # 检查日志配置
        if "logging" in self._config:
            logging_config = self._config["logging"]
            valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
            if "level" in logging_config and logging_config["level"] not in valid_levels:
                errors.append(f"无效的日志级别: {logging_config['level']}")
        
        return errors
    
    def reset_to_default(self):
        """重置为默认配置"""
        self._config = self._load_default_config()
    
    def export_config(self, file_path: str) -> bool:
        """导出配置到指定文件"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"导出配置失败: {e}")
            return False
    
    def import_config(self, file_path: str) -> bool:
        """从指定文件导入配置"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                imported_config = json.load(f)
            
            # 验证导入的配置
            temp_config = self._config.copy()
            self._config = imported_config
            errors = self.validate_config()
            
            if errors:
                self._config = temp_config
                print(f"导入的配置无效: {'; '.join(errors)}")
                return False
            
            return True
        except Exception as e:
            print(f"导入配置失败: {e}")
            return False
    
    def get_config_summary(self) -> Dict[str, Any]:
        """获取配置摘要信息"""
        file_types = self._config.get("file_types", {})
        total_categories = len(file_types)
        total_extensions = sum(len(exts) for exts in file_types.values())
        
        return {
            "total_categories": total_categories,
            "total_extensions": total_extensions,
            "organize_by_date": self._config.get("organize_by_date", False),
            "default_category": self._config.get("default_category", "其他文件"),
            "duplicate_strategy": self._config.get("duplicate_strategy", "rename"),
            "monitor_enabled": self._config.get("monitor_settings", {}).get("enabled", True)
        }