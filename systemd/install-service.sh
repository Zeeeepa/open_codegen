#!/bin/bash
"""
Install OpenAI Interceptor as a systemd service on Ubuntu.
"""

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SERVICE_NAME="openai-interceptor"
SERVICE_FILE="openai-interceptor.service"
INSTALL_DIR="/opt/openai-interceptor"
SYSTEMD_DIR="/etc/systemd/system"

echo -e "${BLUE}🚀 Installing OpenAI Interceptor as systemd service...${NC}"

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}❌ This script must be run as root (use sudo)${NC}"
   exit 1
fi

# Check if systemd is available
if ! command -v systemctl &> /dev/null; then
    echo -e "${RED}❌ systemctl not found. This system doesn't use systemd.${NC}"
    exit 1
fi

# Create installation directory
echo -e "${YELLOW}📁 Creating installation directory...${NC}"
mkdir -p "$INSTALL_DIR"

# Copy application files
echo -e "${YELLOW}📋 Copying application files...${NC}"
cp -r openai_codegen_adapter "$INSTALL_DIR/"
cp -r interceptor "$INSTALL_DIR/"
cp requirements.txt "$INSTALL_DIR/"
cp server.py "$INSTALL_DIR/"

# Install Python dependencies
echo -e "${YELLOW}📦 Installing Python dependencies...${NC}"
cd "$INSTALL_DIR"
pip3 install -r requirements.txt

# Copy systemd service file
echo -e "${YELLOW}⚙️ Installing systemd service...${NC}"
cp "systemd/$SERVICE_FILE" "$SYSTEMD_DIR/"

# Set proper permissions
chmod 644 "$SYSTEMD_DIR/$SERVICE_FILE"
chmod +x "$INSTALL_DIR/server.py"

# Reload systemd
echo -e "${YELLOW}🔄 Reloading systemd daemon...${NC}"
systemctl daemon-reload

# Enable service
echo -e "${YELLOW}✅ Enabling service...${NC}"
systemctl enable "$SERVICE_NAME"

echo -e "${GREEN}✅ OpenAI Interceptor service installed successfully!${NC}"
echo ""
echo -e "${BLUE}📋 Service Management Commands:${NC}"
echo -e "  Start service:    ${YELLOW}sudo systemctl start $SERVICE_NAME${NC}"
echo -e "  Stop service:     ${YELLOW}sudo systemctl stop $SERVICE_NAME${NC}"
echo -e "  Restart service:  ${YELLOW}sudo systemctl restart $SERVICE_NAME${NC}"
echo -e "  Check status:     ${YELLOW}sudo systemctl status $SERVICE_NAME${NC}"
echo -e "  View logs:        ${YELLOW}sudo journalctl -u $SERVICE_NAME -f${NC}"
echo ""
echo -e "${BLUE}📍 Installation Directory: ${YELLOW}$INSTALL_DIR${NC}"
echo -e "${BLUE}📍 Service File: ${YELLOW}$SYSTEMD_DIR/$SERVICE_FILE${NC}"
echo ""
echo -e "${YELLOW}⚠️ Note: You still need to:${NC}"
echo -e "  1. Set up DNS interception: ${YELLOW}sudo python3 -m interceptor.ubuntu_dns enable${NC}"
echo -e "  2. Set up SSL certificates: ${YELLOW}sudo python3 -m interceptor.ubuntu_ssl setup${NC}"
echo -e "  3. Start the service: ${YELLOW}sudo systemctl start $SERVICE_NAME${NC}"
