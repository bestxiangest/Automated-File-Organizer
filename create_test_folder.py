#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建测试文件夹脚本
生成包含各种类型文件的测试文件夹
"""

import os
import random
import string

def create_test_folder():
    """创建测试文件夹和文件"""
    # 测试文件夹路径
    test_folder = "测试文件夹"
    
    # 如果文件夹已存在，先删除
    if os.path.exists(test_folder):
        import shutil
        shutil.rmtree(test_folder)
    
    # 创建主测试文件夹
    os.makedirs(test_folder, exist_ok=True)
    print(f"创建测试文件夹: {test_folder}")
    
    # 定义各种文件类型
    file_types = {
        '图片文件': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', '.ico'],
        '文档文件': ['.txt', '.doc', '.docx', '.pdf', '.xls', '.xlsx', '.ppt', '.pptx', '.rtf'],
        '音频文件': ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a'],
        '视频文件': ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v'],
        '压缩文件': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz'],
        '代码文件': ['.py', '.js', '.html', '.css', '.java', '.cpp', '.c', '.php', '.go', '.rs'],
        '其他文件': ['.exe', '.msi', '.dmg', '.deb', '.rpm', '.iso', '.bin']
    }
    
    # 文件名前缀
    file_prefixes = [
        '测试文件', '示例文档', '样本数据', '项目文件', '备份文件',
        '临时文件', '工作文档', '重要资料', '学习材料', '参考文件'
    ]
    
    # 在主文件夹中创建各种类型的文件
    file_count = 0
    for category, extensions in file_types.items():
        # 每种类型创建3-5个文件
        num_files = random.randint(3, 5)
        for i in range(num_files):
            prefix = random.choice(file_prefixes)
            ext = random.choice(extensions)
            filename = f"{prefix}_{i+1}{ext}"
            filepath = os.path.join(test_folder, filename)
            
            # 创建空文件
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"这是一个{category}的测试文件: {filename}\n")
                f.write(f"创建时间: {os.path.getctime}\n")
                f.write(f"文件类型: {category}\n")
            
            file_count += 1
            print(f"创建文件: {filename}")
    
    # 创建一些子文件夹（用于测试程序不会处理子文件夹）
    subfolders = [
        '重要项目文件夹',
        '工作文档',
        '个人资料',
        '软件安装包',
        '备份文件夹'
    ]
    
    for folder_name in subfolders:
        subfolder_path = os.path.join(test_folder, folder_name)
        os.makedirs(subfolder_path, exist_ok=True)
        print(f"创建子文件夹: {folder_name}")
        
        # 在子文件夹中也创建一些文件（测试程序不应该处理这些）
        for i in range(2, 4):
            ext = random.choice(['.txt', '.doc', '.jpg', '.mp3', '.zip'])
            filename = f"子文件夹文件_{i}{ext}"
            filepath = os.path.join(subfolder_path, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"这是子文件夹中的文件: {filename}\n")
                f.write(f"位置: {subfolder_path}\n")
                f.write("注意: 程序不应该处理这个文件！\n")
            
            print(f"  在子文件夹中创建: {filename}")
    
    # 创建一些特殊文件名的文件（测试边界情况）
    special_files = [
        '带空格的 文件名.txt',
        '中文文件名测试.docx',
        'file-with-dashes.pdf',
        'file_with_underscores.jpg',
        'UPPERCASE_FILE.MP3',
        'mixed.Case.File.png',
        '123数字开头.zip',
        '特殊字符@#$.txt'
    ]
    
    for filename in special_files:
        filepath = os.path.join(test_folder, filename)
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"特殊文件名测试: {filename}\n")
            file_count += 1
            print(f"创建特殊文件: {filename}")
        except Exception as e:
            print(f"无法创建文件 {filename}: {e}")
    
    print(f"\n测试文件夹创建完成！")
    print(f"总共创建了 {file_count} 个文件")
    print(f"创建了 {len(subfolders)} 个子文件夹")
    print(f"测试文件夹位置: {os.path.abspath(test_folder)}")
    print("\n现在你可以使用文件整理工具来测试各种功能了！")
    print("\n测试建议:")
    print("1. 选择这个测试文件夹进行一键整理")
    print("2. 测试监控功能，向文件夹中添加新文件")
    print("3. 测试托盘功能，右键整理活动文件夹")
    print("4. 验证程序只处理直接文件，不触碰子文件夹")

if __name__ == "__main__":
    create_test_folder()