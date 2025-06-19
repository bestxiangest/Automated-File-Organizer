# 个人文件自动化整理归档工具

一个功能强大的文件自动整理工具，支持图形界面和命令行两种使用方式，能够根据文件类型自动分类整理文件，提高文件管理效率。

## ✨ 主要功能

### 🖥️ 图形界面功能
- **智能文件整理**: 根据文件扩展名自动分类整理文件
- **实时文件监控**: 监控指定目录，自动整理新增文件
- **桌面快速整理**: 一键整理桌面文件
- **配置规则管理**: 可视化添加、编辑、删除文件分类规则
- **定时提醒功能**: 设置定时提醒进行文件整理
- **系统托盘支持**: 最小化到系统托盘，后台运行
- **日志查看**: 实时查看整理日志和操作记录
- **预览模式**: 预览整理结果，确认后再执行

### 💻 命令行功能
- **批量文件整理**: `organize` - 整理指定目录的所有文件
- **实时监控**: `monitor` - 监控目录变化，自动整理新文件
- **预览整理结果**: `preview` - 预览整理操作，不实际移动文件
- **文件统计**: `stats` - 显示目录文件类型统计信息
- **配置管理**: `config` - 管理分类规则和配置

### 🔧 核心特性
- **智能分类**: 支持10+种文件类型分类（图片、文档、音频、视频等）
- **自定义规则**: 支持添加自定义文件类型和分类规则
- **安全操作**: 支持预览模式，避免误操作
- **日志记录**: 完整的操作日志，支持日志轮转
- **配置持久化**: JSON格式配置文件，支持导入导出
- **跨平台支持**: 支持Windows、macOS、Linux

## 📦 安装说明

### 环境要求
- Python 3.8+
- 支持的操作系统：Windows、macOS、Linux

### 依赖安装

```bash
# 克隆项目
git clone <repository-url>
cd "Automated File Organizer"

# 安装依赖
pip install -r requirements.txt
```

### 主要依赖包
- `watchdog>=3.0.0` - 文件系统监控
- `tkinter` - GUI界面（通常随Python安装）
- `psutil>=5.9.0` - 系统信息管理
- `pystray>=0.19.0` - 系统托盘功能
- `Pillow>=9.0.0` - 图像处理
- `send2trash>=1.8.0` - 安全删除文件

## 🚀 使用方法

### 图形界面模式

```bash
# 启动图形界面
python main.py
```

#### 主要操作
1. **选择源目录**: 点击"浏览"按钮选择要整理的文件夹
2. **选择目标目录**: 选择整理后文件的存放位置
3. **开始整理**: 点击"开始整理"按钮执行文件整理
4. **实时监控**: 点击"开始监控"启用自动整理功能
5. **桌面整理**: 点击"快速整理桌面"一键整理桌面文件
6. **配置管理**: 在"配置规则"标签页中管理文件分类规则

### 命令行模式

```bash
# 整理文件夹
python cli.py organize /path/to/source /path/to/target

# 预览整理结果（不实际移动文件）
python cli.py organize /path/to/source /path/to/target --dry-run

# 监控文件夹
python cli.py monitor /path/to/watch /path/to/target

# 递归监控子目录
python cli.py monitor /path/to/watch /path/to/target --recursive

# 预览整理结果
python cli.py preview /path/to/source /path/to/target

# 显示文件统计
python cli.py stats /path/to/directory

# 配置管理
python cli.py config --list                    # 列出当前配置
python cli.py config --reset                   # 重置为默认配置
python cli.py config --export config.json      # 导出配置
python cli.py config --import config.json      # 导入配置
```

## 📁 文件分类规则

### 默认分类
- **图片**: jpg, jpeg, png, gif, bmp, tiff, svg, webp, ico
- **文档**: doc, docx, pdf, txt, rtf, odt, pages
- **表格**: xls, xlsx, csv, ods, numbers
- **演示文稿**: ppt, pptx, odp, key
- **音频**: mp3, wav, flac, aac, ogg, wma, m4a
- **视频**: mp4, avi, mkv, mov, wmv, flv, webm, m4v
- **压缩包**: zip, rar, 7z, tar, gz, bz2, xz
- **可执行程序**: exe, msi, dmg, pkg, deb, rpm, app
- **代码**: py, js, html, css, java, cpp, c, php, rb, go, rs
- **字体**: ttf, otf, woff, woff2, eot

### 自定义规则
可以通过图形界面或配置文件添加自定义分类规则：

```json
{
  "file_types": {
    "自定义分类": [".ext1", ".ext2"]
  }
}
```

## ⚙️ 配置说明

### 配置文件位置
- 配置文件：`config/settings.json`
- 日志文件：`logs/file_organizer.log`

### 主要配置项
- `file_types`: 文件类型分类规则
- `default_category`: 未匹配文件的默认分类
- `organize_by_date`: 是否按日期组织文件
- `date_format`: 日期格式
- `create_subcategories`: 是否创建子分类
- `excluded_extensions`: 排除的文件扩展名

## 🔨 打包部署

### 打包成可执行文件

```bash
# 使用内置打包脚本
python build.py

# 或手动使用PyInstaller
pyinstaller --onefile --windowed --icon=icon.svg main.py
```

### 清理构建文件

```bash
python build.py --clean
```

## 📝 日志系统

### 日志功能
- 自动记录所有文件操作
- 支持日志轮转（默认10MB，保留5个备份）
- 可配置日志级别和输出格式
- 支持控制台和文件双重输出

### 日志查看
- 图形界面：点击"查看日志"按钮
- 命令行：直接查看 `logs/file_organizer.log` 文件

## 🛡️ 安全特性

- **预览模式**: 支持预览整理结果，确认后再执行
- **安全删除**: 使用 `send2trash` 库，文件移动到回收站而非永久删除
- **异常处理**: 完善的异常处理机制，避免程序崩溃
- **权限检查**: 自动检查文件和目录权限

## 🔧 开发说明

### 项目结构
```
Automated File Organizer/
├── main.py              # 图形界面主程序
├── cli.py               # 命令行接口
├── file_organizer.py    # 核心文件整理逻辑
├── config_manager.py    # 配置管理
├── logger_setup.py      # 日志设置
├── build.py             # 打包脚本
├── requirements.txt     # 依赖列表
├── icon.svg            # 应用图标
├── config/             # 配置目录
│   └── settings.json   # 配置文件
└── logs/               # 日志目录
    └── file_organizer.log
```

### 核心模块
- `FileOrganizer`: 文件整理核心类
- `ConfigManager`: 配置管理类
- `FileOrganizerLogger`: 日志记录类
- `FileOrganizerGUI`: 图形界面类
- `FileOrganizerCLI`: 命令行接口类

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🐛 问题反馈

如果您遇到任何问题或有功能建议，请在 [Issues](../../issues) 页面提交。

## 📊 更新日志

### v1.0.0
- 初始版本发布
- 支持图形界面和命令行两种模式
- 实现基本的文件分类整理功能
- 添加实时监控功能
- 支持自定义分类规则
- 完善的日志系统

---

**享受更高效的文件管理体验！** 🎉