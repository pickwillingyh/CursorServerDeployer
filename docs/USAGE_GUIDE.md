# Cursor Server Deployer 使用指南

## 功能概述

这是一个用于部署 Cursor 远程服务器的工具，支持：
- 自动下载 Cursor 服务器和 CLI 包
- 支持 SSH 密码和密钥认证
- 默认同时下载服务器包和 CLI 包
- 单个包下载失败不会中断整个流程

## 使用方法

### 1. 基本部署

```bash
# 部署到指定服务器
python -m cursor_server_deployer deploy --host your-server.com --user your-username

# 使用密码认证（会提示输入密码）
python -m cursor_server_deployer deploy --host your-server.com --user your-username --port 22

# 使用密钥认证
python -m cursor_server_deployer deploy --host your-server.com --user your-username --key-auth
```

### 2. 交互式模式

```bash
# 启动交互式菜单
python -m cursor_server_deployer

# 选择部署选项，会自动下载两个包（服务器包和 CLI 包）
```

### 3. 添加服务器

```bash
# 添加新服务器配置
python -m cursor_server_deployer add-server \
  --host your-server.com \
  --user your-username \
  --port 22 \
  --arch x64
```

### 4. 使用密码为 "dev" 的服务器

```bash
# 当系统提示输入密码时，输入 "dev"
python -m cursor_server_deployer deploy --host your-server.com --user your-username

# 在静默模式下（会自动使用最后一次配置的密码）
python -m cursor_server_deployer deploy --silent
```

## 下载说明

### URL 格式
- 服务器包：`https://downloads.cursor.com/production/{commit}/{os}/{arch}/cursor-reh-{os}-{arch}.tar.gz`
- CLI 包：`https://downloads.cursor.com/production/{commit}/{os}/{arch}/cli-{os}-{arch}.tar.gz`

### 文件命名
- 服务器包：`cursor-reh-{os}-{arch}.tar.gz`
- CLI 包：`cli-{os}-{arch}.tar.gz`

### User-Agent
使用官方格式：`Cursor/{version} (Windows; Remote-SSH)`

## 部署流程

1. **自动检测本地 Cursor 版本**
   - 从 `cursor --version` 获取版本信息和 commit hash

2. **下载包**
   - 同时下载服务器包和 CLI 包
   - 如果某个包下载失败，会继续下载另一个包
   - 下载的文件会缓存到 `~/.cursor-server-deployer/cache/`

3. **部署到服务器**
   - 创建目录结构：`/home/user/.cursor-server/cursor-{commit}/`
   - 上传并解压服务器包
   - 上传并解压 CLI 包到 `cli/` 目录
   - 设置正确的权限

## 错误处理

- **单个包下载失败**：会继续下载另一个包，不会中断整个流程
- **403 Forbidden 错误**：可能是 commit hash 不正确，确保使用正确的版本
- **连接错误**：检查服务器地址、用户名、端口和密码
- **权限错误**：确保用户对远程目录有写入权限

## 缓存管理

```bash
# 清理所有缓存
python -m cursor_server_deployer cache clear

# 清理超过 7 天的缓存文件
python -m cursor_server_deployer cache clear --older-than 7
```

## 注意事项

1. 确保本地已安装 Cursor
2. 确保有对远程服务器的 SSH 访问权限
3. 默认下载两个包，不需要额外选项
4. 下载失败时会重试，不会影响其他包的下载
5. 部署时会自动创建必要的目录结构

## 故障排除

### Unicode 编码错误
在中文 Windows 系统上，可能会出现 Unicode 字符显示问题。这不会影响功能，只是显示问题。

### 下载失败
- 检查网络连接
- 确认 commit hash 正确
- 尝试使用 `--force-download` 强制重新下载

### 部署失败
- 确认服务器信息正确
- 检查 SSH 连接
- 确认密码正确（对于您的服务器，密码是 "dev"）
- 检查远程目录权限