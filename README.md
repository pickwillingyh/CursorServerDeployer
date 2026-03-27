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
- ✅ Automatic version checking (non-intrusive)

## Installation

### Using uvx (Recommended)

No installation required! Use `uvx` to run directly:

```bash
uvx cursor-server-deployer
```

#### Local setup of `uvx`

If you don't have `uv`/`uvx` yet, install it first (see the official docs at [`https://docs.astral.sh/uv`](https://docs.astral.sh/uv)):

```bash
# Linux / macOS
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 | iex"
```

After installation, make sure `uvx` is on your `PATH`:

```bash
uvx --version
```

Then you can run this tool from any directory without creating a virtualenv manually:

```bash
uvx cursor-server-deployer --help
```

### Using pipx

Install to your current environment:

```bash
pipx install cursor-server-deployer
```

### Using pip

```bash
pip install cursor-server-deployer
```

### Using uvx (Local Development)

If you want to test the local version without installing it:

```bash
# Clone the repository
git clone https://github.com/yourusername/cursor-server-deployer.git
cd cursor-server-deployer

# Run directly with uvx from local source
uvx --from . cursor-server-deployer --help

# Or use --with-editable for development (changes reflect immediately)
uvx --with-editable . --from . cursor-server-deployer --help

# Run deployment
uvx --with-editable . --from . cursor-server-deployer --host mycloud.com --user root

# Run in interactive mode
uvx --with-editable . --from . cursor-server-deployer

# Add a server
uvx --with-editable . --from . cursor-server-deployer add-server --host example.com --user admin

# List servers
uvx --with-editable . --from . cursor-server-deployer list-servers
```

### Using uv (Development)

To run from source code:

```bash
# Clone the repository
git clone https://github.com/yourusername/cursor-server-deployer.git
cd cursor-server-deployer

# Sync dependencies
uv sync

# Run the tool
uv run python -m cursor_server_deployer --help

# Run deployment
uv run python -m cursor_server_deployer --host mycloud.com --user root

# Run in interactive mode
uv run python -m cursor_server_deployer

# Add a server
uv run python -m cursor_server_deployer add-server --host example.com --user admin

# List servers
uv run python -m cursor_server_deployer list-servers
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

## Version Checking

The tool automatically checks for updates in a non-intrusive way:
- Update checks happen silently in the background
- You'll only be notified when a new version is available
- The tool never interrupts your workflow with update prompts
- You can check for updates manually using: `uvx cursor-server-deployer --check-update`

## Requirements

- Python 3.10+
- Cursor installed locally
- SSH access to remote servers

## Development

### Building and Publishing

Use `poe` (Python Task Executor) for common development tasks:

```bash
# Install poe
pip install poethepoet

# Run available tasks
poe

# Common tasks:
poe build          # Build the package
poe publish        # Publish to PyPI
poe publish-test   # Publish to TestPyPI
poe version        # Bump version
poe clean         # Clean build artifacts
poe test          # Run tests
```

## Acknowledgments

This project was inspired by and includes information from the following sources:

- [How to download Cursor Remote SSH Server manually](https://forum.cursor.com/t/how-to-download-cursor-remote-ssh-server-manually/30455) - The Cursor Forum community for sharing insights about Cursor remote server setup

Special thanks to the Cursor community members who contributed their knowledge and experiences, making this tool possible.

## License

MIT
