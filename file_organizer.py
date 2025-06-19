#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件整理核心模块
负责文件的分类和整理逻辑
"""

import os
import shutil
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class FileOrganizer:
    """文件整理器"""
    
    def __init__(self, config_manager, logger):
        self.config_manager = config_manager
        self.logger = logger
        
    def organize_folder(self, source_dir: str, target_dir: str) -> Dict[str, int]:
        """
        整理文件夹中的所有文件
        
        Args:
            source_dir: 源文件夹路径
            target_dir: 目标文件夹路径
            
        Returns:
            包含处理结果统计的字典
        """
        result = {'total': 0, 'success': 0, 'failed': 0, 'skipped': 0}
        
        try:
            # 确保目标目录存在
            os.makedirs(target_dir, exist_ok=True)
            
            # 只遍历源目录中的直接文件，不递归进入子目录
            try:
                items = os.listdir(source_dir)
            except PermissionError:
                self.logger.error(f"无权限访问目录: {source_dir}")
                return result
            
            for item in items:
                item_path = os.path.join(source_dir, item)
                
                # 只处理文件，跳过目录
                if os.path.isfile(item_path):
                    result['total'] += 1
                    
                    try:
                        # 跳过隐藏文件和系统文件
                        if item.startswith('.') or item.startswith('~'):
                            result['skipped'] += 1
                            continue
                            
                        # 整理单个文件
                        organized_path = self.organize_file(item_path, target_dir)
                        if organized_path:
                            result['success'] += 1
                            self.logger.info(f"文件已整理: {item} -> {organized_path}")
                        else:
                            result['skipped'] += 1
                            
                    except Exception as e:
                        result['failed'] += 1
                        self.logger.error(f"整理文件失败 {item}: {e}")
                else:
                    # 记录跳过的目录
                    self.logger.info(f"跳过目录: {item}")
                        
        except Exception as e:
            self.logger.error(f"整理文件夹失败: {e}")
            raise
            
        return result
    
    def organize_file(self, file_path: str, target_dir: str) -> Optional[str]:
        """
        整理单个文件
        
        Args:
            file_path: 文件路径
            target_dir: 目标目录
            
        Returns:
            整理后的文件路径，如果跳过则返回None
        """
        try:
            if not os.path.exists(file_path) or not os.path.isfile(file_path):
                return None
                
            # 获取文件信息
            file_info = self._get_file_info(file_path)
            
            # 确定目标分类目录
            category_dir = self._determine_category_dir(file_info, target_dir)
            
            # 创建目标目录
            os.makedirs(category_dir, exist_ok=True)
            
            # 生成目标文件路径
            target_file_path = self._generate_target_path(file_info, category_dir)
            
            # 移动文件
            shutil.move(file_path, target_file_path)
            
            return os.path.relpath(target_file_path, target_dir)
            
        except Exception as e:
            self.logger.error(f"整理文件失败 {file_path}: {e}")
            raise
    
    def _get_file_info(self, file_path: str) -> Dict:
        """
        获取文件信息
        
        Args:
            file_path: 文件路径
            
        Returns:
            包含文件信息的字典
        """
        file_stat = os.stat(file_path)
        file_name = os.path.basename(file_path)
        name, extension = os.path.splitext(file_name)
        
        return {
            'path': file_path,
            'name': file_name,
            'base_name': name,
            'extension': extension.lower(),
            'size': file_stat.st_size,
            'created_time': datetime.fromtimestamp(file_stat.st_ctime),
            'modified_time': datetime.fromtimestamp(file_stat.st_mtime),
            'accessed_time': datetime.fromtimestamp(file_stat.st_atime)
        }
    
    def _determine_category_dir(self, file_info: Dict, target_dir: str) -> str:
        """
        确定文件的分类目录
        
        Args:
            file_info: 文件信息
            target_dir: 目标根目录
            
        Returns:
            分类目录路径
        """
        config = self.config_manager.get_config()
        
        # 根据文件扩展名确定分类
        category = self._get_file_category(file_info['extension'], config)
        
        # 根据配置决定是否按日期分组
        if config.get('organize_by_date', False):
            date_folder = file_info['created_time'].strftime('%Y-%m')
            return os.path.join(target_dir, category, date_folder)
        else:
            return os.path.join(target_dir, category)
    
    def _get_file_category(self, extension: str, config: Dict) -> str:
        """
        根据文件扩展名获取分类
        
        Args:
            extension: 文件扩展名
            config: 配置信息
            
        Returns:
            文件分类名称
        """
        file_types = config.get('file_types', {})
        
        # 移除扩展名前的点
        ext = extension.lstrip('.')
        
        # 查找匹配的分类
        for category, extensions in file_types.items():
            if ext in [e.lstrip('.') for e in extensions]:
                return category
        
        # 如果没有找到匹配的分类，返回默认分类
        return config.get('default_category', '其他文件')
    
    def _generate_target_path(self, file_info: Dict, category_dir: str) -> str:
        """
        生成目标文件路径，处理重名文件
        
        Args:
            file_info: 文件信息
            category_dir: 分类目录
            
        Returns:
            目标文件路径
        """
        base_name = file_info['base_name']
        extension = file_info['extension']
        
        target_path = os.path.join(category_dir, file_info['name'])
        
        # 如果文件已存在，处理重名
        if os.path.exists(target_path):
            # 检查是否为同一文件（通过文件大小和修改时间）
            if self._is_same_file(file_info['path'], target_path):
                # 如果是同一文件，跳过
                raise FileExistsError(f"文件已存在且内容相同: {file_info['name']}")
            
            # 生成新的文件名
            counter = 1
            while True:
                new_name = f"{base_name}_{counter}{extension}"
                new_path = os.path.join(category_dir, new_name)
                
                if not os.path.exists(new_path):
                    target_path = new_path
                    break
                    
                counter += 1
                
                # 防止无限循环
                if counter > 1000:
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    new_name = f"{base_name}_{timestamp}{extension}"
                    target_path = os.path.join(category_dir, new_name)
                    break
        
        return target_path
    
    def _is_same_file(self, file1: str, file2: str) -> bool:
        """
        检查两个文件是否相同
        
        Args:
            file1: 第一个文件路径
            file2: 第二个文件路径
            
        Returns:
            如果文件相同返回True，否则返回False
        """
        try:
            stat1 = os.stat(file1)
            stat2 = os.stat(file2)
            
            # 比较文件大小
            if stat1.st_size != stat2.st_size:
                return False
            
            # 比较文件内容的哈希值（仅对小文件）
            if stat1.st_size < 1024 * 1024:  # 1MB以下的文件
                return self._get_file_hash(file1) == self._get_file_hash(file2)
            
            # 对于大文件，只比较大小和修改时间
            return abs(stat1.st_mtime - stat2.st_mtime) < 1
            
        except Exception:
            return False
    
    def _get_file_hash(self, file_path: str) -> str:
        """
        计算文件的MD5哈希值
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件的MD5哈希值
        """
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
        except Exception:
            return ""
        return hash_md5.hexdigest()
    
    def get_file_statistics(self, directory: str) -> Dict:
        """
        获取目录中文件的统计信息
        
        Args:
            directory: 目录路径
            
        Returns:
            包含统计信息的字典
        """
        stats = {
            'total_files': 0,
            'total_size': 0,
            'file_types': {},
            'categories': {}
        }
        
        config = self.config_manager.get_config()
        
        try:
            # 只统计指定目录中的直接文件，不递归进入子目录
            items = os.listdir(directory)
            for item in items:
                item_path = os.path.join(directory, item)
                
                # 只处理文件，跳过目录
                if os.path.isfile(item_path):
                    if item.startswith('.') or item.startswith('~'):
                        continue
                        
                    file_stat = os.stat(item_path)
                    
                    stats['total_files'] += 1
                    stats['total_size'] += file_stat.st_size
                    
                    # 统计文件类型
                    _, extension = os.path.splitext(item)
                    extension = extension.lower()
                    
                    if extension in stats['file_types']:
                        stats['file_types'][extension] += 1
                    else:
                        stats['file_types'][extension] = 1
                    
                    # 统计分类
                    category = self._get_file_category(extension, config)
                    if category in stats['categories']:
                        stats['categories'][category] += 1
                    else:
                        stats['categories'][category] = 1
                        
        except Exception as e:
            self.logger.error(f"获取文件统计信息失败: {e}")
            
        return stats
    
    def preview_organization(self, source_dir: str, target_dir: str) -> List[Dict]:
        """
        预览文件整理结果，不实际移动文件
        
        Args:
            source_dir: 源目录
            target_dir: 目标目录
            
        Returns:
            预览结果列表
        """
        preview_results = []
        
        try:
            # 只预览指定目录中的直接文件，不递归进入子目录
            items = os.listdir(source_dir)
            for item in items:
                item_path = os.path.join(source_dir, item)
                
                # 只处理文件，跳过目录
                if os.path.isfile(item_path):
                    if item.startswith('.') or item.startswith('~'):
                        continue
                        
                    file_info = self._get_file_info(item_path)
                    
                    # 确定目标分类目录
                    category_dir = self._determine_category_dir(file_info, target_dir)
                    relative_category = os.path.relpath(category_dir, target_dir)
                    
                    preview_results.append({
                        'source_path': item_path,
                        'file_name': file_info['name'],
                        'category': relative_category,
                        'size': file_info['size'],
                        'extension': file_info['extension']
                    })
                    
        except Exception as e:
            self.logger.error(f"预览整理结果失败: {e}")
            
        return preview_results