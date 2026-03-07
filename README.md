# Cursor Server Deployer

A powerful tool for deploying Cursor remote servers to Linux machines.

## Features

- ✅ Auto-detect local Cursor version
- ✅ Download Cursor server from official releases
- ✅ Multi-server management
- ✅ SSH key authentication support
- ✅ Interactive menu interface
- ✅ Silent mode for repeat deployments
- ✅ Extensible download strategies
- ✅ Rich console output with progress

## Installation

No installation required! Use `uvx` to run directly:

```bash
uvx cursor-server-deployer
```

## Usage

### Basic Deployment

```bash
# Deploy to a remote server
uvx cursor-server-deployer --host mycloud.com --user root

# Specify port and architecture
uvx cursor-server-deployer --host mycloud.com --port 22 --user root --arch x64

# Silent mode (uses last configuration)
uvx cursor-server-deployer --silent

# Verbose logging
uvx cursor-server-deployer --verbose
```

### Interactive Mode

```bash
# Launch interactive menu
uvx cursor-server-deployer

# You'll see options like:
# - Deploy to remote servers
# - Add new server
# - Manage server list
# - Setup SSH key authentication
# - View deployment history
```

### Server Management

```bash
# Add a new server
uvx cursor-server-deployer add-server \
  --host example.com \
  --user admin \
  --port 2222 \
  --arch arm64

# List all servers
uvx cursor-server-deployer list-servers

# Remove a server
uvx cursor-server-deployer remove-server --server-id server1
```

### SSH Key Authentication

```bash
# Setup SSH key for a server (upgrade from password)
uvx cursor-server-deployer setup-key --server-id server1

# After setup, you can use standard SSH tools:
ssh cursor-mycloud.com-22  # Uses the alias in ~/.ssh/config
```

### Multi-Server Deployment

```bash
# Deploy to multiple servers
uvx cursor-server-deployer deploy --servers server1,server2,server3

# Select servers interactively
uvx cursor-server-deployer deploy --interactive
```

## Configuration

Configuration is stored in `~/.cursor-server-deployer/`:

```
~/.cursor-server-deployer/
├── config.json              # Server configurations
├── history.json             # Deployment history
├── logs/                    # Log files
└── cache/                   # Downloaded server files
```

## SSH Key Management

SSH keys are stored in the standard `~/.ssh/` directory:

```
~/.ssh/
├── id_ed25519_cursor_<host>_<port>     # Private key
├── id_ed25519_cursor_<host>_<port>.pub # Public key
└── config                              # SSH config (auto-updated)
```

## Security Features

- No password caching (enter each time)
- SSH keys stored in standard `~/.ssh/` location
- Per-server independent keys
- Automatic SSH config updates
- ED25519 keys (modern and secure)
- Proper file permissions (600/644/700)

## Requirements

- Python 3.10+
- Cursor installed locally
- SSH access to remote servers

## License

MIT