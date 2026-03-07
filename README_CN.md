# Cursor Server Deployer

一个用于部署 Cursor 远程服务器到 Linux 机器的强大工具。

## 功能特性

- ✅ 自动检测本地 Cursor 版本
- ✅ 从官方发布版本下载 Cursor 服务器
- ✅ 多服务器管理
- ✅ SSH 密钥认证支持
- ✅ 交互式菜单界面
- ✅ 重复部署的静默模式
- ✅ 可扩展的下载策略
- ✅ 丰富的控制台输出和进度显示
- ✅ 自动版本检查（不干扰用户）

## 安装

### 使用 uvx（推荐）

无需安装！直接使用 `uvx` 运行：

```bash
uvx cursor-server-deployer
```

### 使用 pipx

安装到当前环境：

```bash
pipx install cursor-server-deployer
```

### 使用 pip

```bash
pip install cursor-server-deployer
```

### 使用 uv（开发环境）

```bash
# 克隆仓库
git clone https://github.com/yourusername/cursor-server-deployer.git
cd cursor-server-deployer

# 同步依赖
uv sync

# 运行工具
uv run python -m cursor_server_deployer --help
```

## 使用方法

### 基本部署

```bash
# 部署到远程服务器
uvx cursor-server-deployer --host mycloud.com --user root

# 指定端口和架构
uvx cursor-server-deployer --host mycloud.com --port 22 --user root --arch x64

# 静默模式（使用上次配置）
uvx cursor-server-deployer --silent

# 详细日志
uvx cursor-server-deployer --verbose
```

### 交互式模式

```bash
# 启动交互式菜单
uvx cursor-server-deployer

# 你将看到以下选项：
# - 部署到远程服务器
# - 添加新服务器
# - 管理服务器列表
# - 设置 SSH 密钥认证
# - 查看部署历史
```

### 服务器管理

```bash
# 添加新服务器
uvx cursor-server-deployer add-server \
  --host example.com \
  --user admin \
  --port 2222 \
  --arch arm64

# 列出所有服务器
uvx cursor-server-deployer list-servers

# 删除服务器
uvx cursor-server-deployer remove-server --server-id server1
```

### SSH 密钥认证

```bash
# 为服务器设置 SSH 密钥（从密码升级）
uvx cursor-server-deployer setup-key --server-id server1

# 设置完成后，你可以使用标准 SSH 工具：
ssh cursor-mycloud.com-22  # 使用 ~/.ssh/config 中的别名
```

### 多服务器部署

```bash
# 部署到多个服务器
uvx cursor-server-deployer deploy --servers server1,server2,server3

# 交互式选择服务器
uvx cursor-server-deployer deploy --interactive
```

## 配置

配置存储在 `~/.cursor-server-deployer/` 中：

```
~/.cursor-server-deployer/
├── config.json              # 服务器配置
├── history.json             # 部署历史
├── logs/                    # 日志文件
└── cache/                   # 下载的服务器文件
```

## SSH 密钥管理

SSH 密钥存储在标准的 `~/.ssh/` 目录中：

```
~/.ssh/
├── id_ed25519_cursor_<host>_<port>     # 私钥
├── id_ed25519_cursor_<host>_<port>.pub # 公钥
└── config                              # SSH 配置（自动更新）
```

## 安全特性

- 不缓存密码（每次都需要输入）
- SSH 密钥存储在标准的 `~/.ssh/` 位置
- 每个服务器独立的密钥
- 自动 SSH 配置更新
- ED25519 密钥（现代且安全）
- 正确的文件权限（600/644/700）

## 版本检查

该工具以不打扰用户的方式自动检查更新：
- 更新检查在后台静默进行
- 只有在有新版本可用时才会通知你
- 该工具绝不会用更新提示中断你的工作流程
- 你可以手动检查更新：`uvx cursor-server-deployer --check-update`

## 系统要求

- Python 3.10+
- 本地已安装 Cursor
- 对远程服务器的 SSH 访问权限

## 开发

### 构建和发布

使用 `poe`（Python 任务执行器）进行常见的开发任务：

```bash
# 安装 poe
pip install poethepoet

# 运行可用任务
poe

# 常用任务：
poe build          # 构建包
poe publish        # 发布到 PyPI
poe publish-test   # 发布到 TestPyPI
poe version        # 更新版本号
poe clean         # 清理构建产物
poe test          # 运行测试
```

## 致谢

本项目受到以下来源的启发并包含相关信息：

- [如何手动下载 Cursor Remote SSH Server](https://forum.cursor.com/t/how-to-download-cursor-remote-ssh-server-manually/30455) - Cursor 论坛社区分享了关于 Cursor 远程服务器设置的见解

特别感谢贡献知识和经验的 Cursor 社区成员，使这个工具成为可能。

## 许可证

MIT
