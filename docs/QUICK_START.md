# Cursor Server Deployer - 快速开始指南

## 功能概述

这是一个用于部署 Cursor 远程服务器的工具，支持：
- 自动下载 Cursor 服务器和 CLI 包
- 支持 SSH 密码和密钥认证
- 默认同时下载两个包
- 单个包下载失败不会中断整个流程
- 缓存管理，避免重复下载

## 快速开始

### 1. 添加服务器
```bash
python -m cursor_server_deployer add-server \
  --host your-server.com \
  --user your-username \
  --port 22 \
  --arch x64
```

### 2. 部署到服务器
```bash
# 使用密码认证（会提示输入密码）
python -m cursor_server_deployer deploy --host your-server.com --user your-username

# 对于测试服务器，密码是 "dev"
```

### 3. 查看已配置的服务器
```bash
python -m cursor_server_deployer list-servers
```

## 命令参考

### 部署命令
```bash
python -m cursor_server_deployer deploy [OPTIONS]
```
- `--host` - 服务器地址
- `--user` - 用户名
- `--port` - SSH 端口（默认 22）
- `--key-auth` - 使用密钥认证
- `--silent` - 静默模式（使用缓存密码）
- `--force-download` - 强制重新下载

### 其他命令
```bash
# 添加服务器
python -m cursor_server_deployer add-server --host host --user user

# 列出服务器
python -m cursor_server_deployer list-servers

# 移除服务器
python -m cursor_server_deployer remove-server --host host --user user

# 管理缓存
python -m cursor_server_deployer cache clear
python -m cursor_server_deployer cache clear --older-than 7

# 查看历史
python -m cursor_server_deployer history

# 检查更新
python -m cursor_server_deployer check-update

# 查看帮助
python -m cursor_server_deployer --help
```

## 交互式模式
```bash
python -m cursor_server_deployer
```
启动交互式菜单，可以直观地管理服务器和部署。

## 功能验证

所有功能已验证通过：
- ✅ 版本检测：自动检测本地 Cursor 版本
- ✅ 下载功能：服务器包 (93MB) 和 CLI 包 (8.8MB) 都能正常下载
- ✅ 配置管理：支持添加、列出、删除服务器
- ✅ 认证支持：支持密码和密钥认证
- ✅ 缓存管理：避免重复下载，支持清理
- ✅ 错误处理：单个包失败不影响整体流程

## 故障排除

### 下载失败
- 检查网络连接
- 尝试使用 `--force-download` 强制重新下载
- 检查缓存权限

### 部署失败
- 确认服务器地址、用户名、密码正确
- 检查 SSH 连接
- 确认服务器有足够磁盘空间（约 100MB）
- 检查服务器端目录权限

### Unicode 错误
在中文 Windows 系统上可能会看到 Unicode 字符显示问题，这不影响功能。

## 目录结构

服务器上的部署结构：
```
/home/your-user/.cursor-server/
└── cursor-{commit}/
    ├── cursor-reh-linux-x64/  # 服务器包
    └── cli/                    # CLI 包
```

## 缓存位置

下载的文件缓存在：
```
~/.cursor-server-deployer/cache/
```

## 注意事项

1. 确保本地已安装 Cursor
2. 确保有对远程服务器的 SSH 访问权限
3. 默认端口为 22，如果不是需要指定 --port 参数
4. 对于测试服务器，密码是 "dev"

## 完整测试报告

查看详细的功能验证报告：`功能验证报告.md`