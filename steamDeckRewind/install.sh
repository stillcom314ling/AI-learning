#!/bin/bash
#
# Deck Rewind Installation Script
# Save-state functionality for Steam Deck games
#
# Usage: curl -sSL https://raw.githubusercontent.com/[USER]/deck-rewind/main/install.sh | bash
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Installation directories
INSTALL_DIR="$HOME/.local/share/deck-rewind"
CONFIG_DIR="$HOME/.config/deck-rewind"
BIN_DIR="$HOME/.local/bin"
SYSTEMD_DIR="$HOME/.config/systemd/user"

# Minimum Python version
MIN_PYTHON_VERSION="3.10"

print_banner() {
    echo -e "${BLUE}"
    echo "╔═══════════════════════════════════════════════════════════╗"
    echo "║                    DECK REWIND                            ║"
    echo "║         Save-State Functionality for Steam Deck           ║"
    echo "╚═══════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "\n${BLUE}==>${NC} $1"
}

# Check if running on Steam Deck
check_steam_deck() {
    log_step "Checking environment..."

    if [ -f "/etc/os-release" ]; then
        if grep -q "steamos" /etc/os-release 2>/dev/null; then
            log_info "Steam Deck (SteamOS) detected"
            return 0
        fi
    fi

    # Also check for Steam Deck hardware
    if [ -f "/sys/devices/virtual/dmi/id/product_name" ]; then
        if grep -qi "jupiter" /sys/devices/virtual/dmi/id/product_name 2>/dev/null; then
            log_info "Steam Deck hardware detected"
            return 0
        fi
    fi

    log_warn "Steam Deck not detected. Installation will continue, but some features may not work."
    read -p "Continue anyway? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
}

# Check Python version
check_python() {
    log_step "Checking Python installation..."

    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
        log_info "Found Python $PYTHON_VERSION"

        # Compare versions
        if python3 -c "import sys; exit(0 if sys.version_info >= (3, 10) else 1)"; then
            return 0
        else
            log_error "Python $MIN_PYTHON_VERSION or higher is required"
            return 1
        fi
    else
        log_error "Python 3 not found"
        return 1
    fi
}

# Install system dependencies
install_dependencies() {
    log_step "Installing system dependencies..."

    # Check if we can use pacman (SteamOS/Arch)
    if command -v pacman &> /dev/null; then
        # On Steam Deck, we need to disable read-only filesystem first
        if [ -f "/etc/os-release" ] && grep -q "steamos" /etc/os-release 2>/dev/null; then
            log_info "Enabling write access to root filesystem..."
            sudo steamos-readonly disable 2>/dev/null || true
        fi

        # Install packages
        log_info "Installing packages via pacman..."
        sudo pacman -Sy --noconfirm --needed \
            criu \
            python-pip \
            zstd \
            libnotify \
            2>/dev/null || log_warn "Some packages may have failed to install"

        # Re-enable read-only if on Steam Deck
        if [ -f "/etc/os-release" ] && grep -q "steamos" /etc/os-release 2>/dev/null; then
            sudo steamos-readonly enable 2>/dev/null || true
        fi

    elif command -v apt-get &> /dev/null; then
        log_info "Installing packages via apt..."
        sudo apt-get update
        sudo apt-get install -y \
            criu \
            python3-pip \
            zstd \
            libnotify-bin \
            2>/dev/null || log_warn "Some packages may have failed to install"

    else
        log_warn "Package manager not found. You may need to install dependencies manually:"
        log_warn "  - criu"
        log_warn "  - python3-pip"
        log_warn "  - zstd"
        log_warn "  - libnotify"
    fi
}

# Install Python packages
install_python_packages() {
    log_step "Installing Python packages..."

    # Create virtual environment or use user installation
    python3 -m pip install --user --upgrade pip

    # Install required packages
    python3 -m pip install --user \
        pyyaml>=6.0 \
        psutil>=5.9.0 \
        evdev>=1.6.0 \
        notify2 \
        zstandard \
        2>/dev/null || log_warn "Some Python packages may have failed to install"

    log_info "Python packages installed"
}

# Create directory structure
create_directories() {
    log_step "Creating directory structure..."

    mkdir -p "$INSTALL_DIR"
    mkdir -p "$INSTALL_DIR/snapshots"
    mkdir -p "$CONFIG_DIR"
    mkdir -p "$BIN_DIR"
    mkdir -p "$SYSTEMD_DIR"

    log_info "Directories created"
}

# Download and install Deck Rewind
install_deck_rewind() {
    log_step "Installing Deck Rewind..."

    # If running from repo, use local files
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

    if [ -d "$SCRIPT_DIR/deck_rewind" ]; then
        log_info "Installing from local source..."
        cp -r "$SCRIPT_DIR/deck_rewind" "$INSTALL_DIR/"

        if [ -f "$SCRIPT_DIR/setup.py" ]; then
            cd "$SCRIPT_DIR"
            python3 -m pip install --user -e . 2>/dev/null || {
                log_warn "pip install failed, using manual installation"
            }
        fi
    else
        # Download from GitHub
        log_info "Downloading from GitHub..."
        REPO_URL="https://github.com/[USER]/deck-rewind"
        TEMP_DIR=$(mktemp -d)

        if command -v git &> /dev/null; then
            git clone --depth 1 "$REPO_URL" "$TEMP_DIR/deck-rewind" 2>/dev/null || {
                log_error "Failed to clone repository"
                rm -rf "$TEMP_DIR"
                exit 1
            }
        else
            log_error "git not found. Please install git or run from local source."
            exit 1
        fi

        cp -r "$TEMP_DIR/deck-rewind/deck_rewind" "$INSTALL_DIR/"

        cd "$TEMP_DIR/deck-rewind"
        python3 -m pip install --user . 2>/dev/null || {
            log_warn "pip install failed, using manual installation"
        }

        rm -rf "$TEMP_DIR"
    fi

    log_info "Deck Rewind installed"
}

# Create CLI wrapper script
create_cli_wrapper() {
    log_step "Creating CLI wrapper..."

    cat > "$BIN_DIR/deck-rewind" << 'EOF'
#!/bin/bash
# Deck Rewind CLI wrapper

INSTALL_DIR="$HOME/.local/share/deck-rewind"

# Add to Python path if needed
export PYTHONPATH="$INSTALL_DIR:$PYTHONPATH"

# Run the main module
python3 -m deck_rewind.main "$@"
EOF

    chmod +x "$BIN_DIR/deck-rewind"

    # Add to PATH if not already there
    if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
        echo "" >> "$HOME/.bashrc"
        echo "# Deck Rewind" >> "$HOME/.bashrc"
        echo "export PATH=\"\$HOME/.local/bin:\$PATH\"" >> "$HOME/.bashrc"
        log_info "Added $BIN_DIR to PATH in .bashrc"
    fi

    log_info "CLI wrapper created"
}

# Install default configuration
install_config() {
    log_step "Installing configuration..."

    if [ ! -f "$CONFIG_DIR/config.yaml" ]; then
        cat > "$CONFIG_DIR/config.yaml" << 'EOF'
# Deck Rewind Configuration

snapshots:
  interval_seconds: 30
  max_rolling_snapshots: 10
  storage_path: "~/.local/share/deck-rewind/snapshots"
  compression: "zstd"
  compression_level: 3

snapshot_method:
  prefer_criu: true
  fallback_to_memory_dump: true
  save_thread_contexts: true

storage:
  max_total_size_gb: 10
  auto_cleanup: true

hotkeys:
  rewind_previous: "steam+l2"
  rewind_back: "steam+dpad_left"
  rewind_forward: "steam+dpad_right"
  list_snapshots: "steam+dpad_up"
  manual_snapshot: "steam+l1"

ui:
  show_notifications: true
  notification_duration_seconds: 3
  overlay_position: "top-right"

games:
  blacklist: []
  whitelist: []
EOF
        log_info "Default configuration installed"
    else
        log_info "Configuration already exists, skipping"
    fi
}

# Install systemd service
install_systemd_service() {
    log_step "Installing systemd service..."

    cat > "$SYSTEMD_DIR/deck-rewind.service" << EOF
[Unit]
Description=Deck Rewind - Game Save State Daemon
After=graphical-session.target

[Service]
Type=simple
ExecStart=$BIN_DIR/deck-rewind start --foreground
Restart=on-failure
RestartSec=5
Environment=DISPLAY=:0
Environment=XDG_RUNTIME_DIR=/run/user/%U

[Install]
WantedBy=default.target
EOF

    # Reload systemd and enable service
    systemctl --user daemon-reload
    systemctl --user enable deck-rewind.service 2>/dev/null || true

    log_info "Systemd service installed"
}

# Set up input device permissions
setup_permissions() {
    log_step "Setting up permissions..."

    # Add user to input group for controller access
    if groups | grep -q input; then
        log_info "User already in input group"
    else
        sudo usermod -aG input "$USER" 2>/dev/null || {
            log_warn "Could not add user to input group. Hotkeys may not work."
            log_warn "Run: sudo usermod -aG input $USER"
        }
    fi

    # Create udev rule for controller access
    UDEV_RULE="/etc/udev/rules.d/99-deck-rewind.rules"
    if [ ! -f "$UDEV_RULE" ]; then
        sudo tee "$UDEV_RULE" > /dev/null << 'EOF'
# Deck Rewind - Allow controller access
SUBSYSTEM=="input", ATTRS{name}=="*Steam*", MODE="0666"
SUBSYSTEM=="input", ATTRS{name}=="*Valve*", MODE="0666"
EOF
        sudo udevadm control --reload-rules 2>/dev/null || true
        log_info "udev rules installed"
    fi
}

# Create desktop shortcut (optional)
create_desktop_shortcut() {
    log_step "Creating desktop shortcut..."

    DESKTOP_FILE="$HOME/.local/share/applications/deck-rewind.desktop"

    cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Name=Deck Rewind
Comment=Game Save State Manager
Exec=$BIN_DIR/deck-rewind status
Icon=applications-games
Terminal=true
Type=Application
Categories=Game;Utility;
EOF

    log_info "Desktop shortcut created"
}

# Print post-installation instructions
print_instructions() {
    echo ""
    echo -e "${GREEN}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║           INSTALLATION COMPLETE!                          ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${BLUE}Quick Start:${NC}"
    echo "  1. Start the daemon:  deck-rewind start"
    echo "  2. Launch any game"
    echo "  3. Use Steam + L2 to rewind!"
    echo ""
    echo -e "${BLUE}Hotkeys:${NC}"
    echo "  Steam + L2       : Rewind to previous snapshot"
    echo "  Steam + D-pad ←  : Go back one snapshot"
    echo "  Steam + D-pad →  : Go forward one snapshot"
    echo "  Steam + D-pad ↑  : Show snapshot count"
    echo "  Steam + L1       : Create manual snapshot"
    echo ""
    echo -e "${BLUE}Commands:${NC}"
    echo "  deck-rewind start    - Start the daemon"
    echo "  deck-rewind stop     - Stop the daemon"
    echo "  deck-rewind status   - Check status"
    echo "  deck-rewind list     - List snapshots"
    echo "  deck-rewind logs     - View logs"
    echo "  deck-rewind config   - Configure settings"
    echo ""
    echo -e "${YELLOW}Note:${NC} You may need to log out and back in for"
    echo "       input permissions to take effect."
    echo ""
    echo -e "${BLUE}Configuration:${NC} $CONFIG_DIR/config.yaml"
    echo -e "${BLUE}Snapshots:${NC}     $INSTALL_DIR/snapshots/"
    echo ""
}

# Main installation function
main() {
    print_banner

    check_steam_deck
    check_python || exit 1
    install_dependencies
    install_python_packages
    create_directories
    install_deck_rewind
    create_cli_wrapper
    install_config
    install_systemd_service
    setup_permissions
    create_desktop_shortcut

    print_instructions

    # Ask to start service
    echo ""
    read -p "Start Deck Rewind daemon now? [Y/n] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
        systemctl --user start deck-rewind.service 2>/dev/null || {
            log_warn "Could not start service via systemd, starting manually..."
            "$BIN_DIR/deck-rewind" start &
        }
        log_info "Deck Rewind daemon started!"
    fi
}

# Run main
main "$@"
