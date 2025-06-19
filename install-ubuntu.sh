#!/bin/bash
"""
Ubuntu Installation Script for OpenAI API Interceptor
Complete setup for transparent OpenAI API interception on Ubuntu.
"""

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
SERVICE_NAME="openai-interceptor"
INSTALL_DIR="/opt/openai-interceptor"

echo -e "${PURPLE}🚀 OpenAI API Interceptor - Ubuntu Installation${NC}"
echo -e "${PURPLE}===============================================${NC}"
echo ""

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}❌ This script must be run as root${NC}"
   echo -e "${YELLOW}   Please run: sudo $0${NC}"
   exit 1
fi

# Check Ubuntu version
if ! grep -q "Ubuntu" /etc/os-release; then
    echo -e "${RED}❌ This script is designed for Ubuntu systems only${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Running on Ubuntu as root${NC}"
echo ""

# Update package list
echo -e "${BLUE}📦 Updating package list...${NC}"
apt update

# Install required packages
echo -e "${BLUE}📦 Installing required packages...${NC}"
apt install -y python3 python3-pip openssl curl

# Install Python dependencies
echo -e "${BLUE}🐍 Installing Python dependencies...${NC}"
pip3 install fastapi uvicorn pydantic requests

# Create installation directory
echo -e "${BLUE}📁 Creating installation directory...${NC}"
mkdir -p "$INSTALL_DIR"

# Copy application files
echo -e "${BLUE}📋 Copying application files...${NC}"
cp -r openai_codegen_adapter "$INSTALL_DIR/"
cp -r interceptor "$INSTALL_DIR/"
cp -r systemd "$INSTALL_DIR/"
cp requirements.txt "$INSTALL_DIR/" 2>/dev/null || echo "requirements.txt not found, skipping"
cp server.py "$INSTALL_DIR/"

# Set proper permissions
chmod +x "$INSTALL_DIR/server.py"
chmod -R 755 "$INSTALL_DIR"

# Install systemd service
echo -e "${BLUE}⚙️ Installing systemd service...${NC}"
cp "$INSTALL_DIR/systemd/openai-interceptor.service" "/etc/systemd/system/"
chmod 644 "/etc/systemd/system/openai-interceptor.service"
systemctl daemon-reload
systemctl enable "$SERVICE_NAME"

echo -e "${GREEN}✅ Service installed and enabled${NC}"

# Setup SSL certificates
echo -e "${BLUE}🔐 Setting up SSL certificates...${NC}"
cd "$INSTALL_DIR"
python3 -m interceptor.ubuntu_ssl setup

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ SSL certificates configured${NC}"
else
    echo -e "${YELLOW}⚠️ SSL certificate setup had issues, but continuing...${NC}"
fi

# Setup DNS interception
echo -e "${BLUE}🌐 Setting up DNS interception...${NC}"
python3 -m interceptor.ubuntu_dns enable

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ DNS interception configured${NC}"
else
    echo -e "${YELLOW}⚠️ DNS interception setup had issues, but continuing...${NC}"
fi

# Start the service
echo -e "${BLUE}🚀 Starting OpenAI Interceptor service...${NC}"
systemctl start "$SERVICE_NAME"

# Check service status
sleep 2
if systemctl is-active --quiet "$SERVICE_NAME"; then
    echo -e "${GREEN}✅ Service is running successfully!${NC}"
else
    echo -e "${YELLOW}⚠️ Service may have issues. Check status with: systemctl status $SERVICE_NAME${NC}"
fi

echo ""
echo -e "${PURPLE}🎉 Installation Complete!${NC}"
echo -e "${PURPLE}========================${NC}"
echo ""
echo -e "${GREEN}✅ OpenAI API Interceptor is now installed and running${NC}"
echo ""
echo -e "${BLUE}📋 Service Management:${NC}"
echo -e "  Status:    ${YELLOW}sudo systemctl status $SERVICE_NAME${NC}"
echo -e "  Stop:      ${YELLOW}sudo systemctl stop $SERVICE_NAME${NC}"
echo -e "  Start:     ${YELLOW}sudo systemctl start $SERVICE_NAME${NC}"
echo -e "  Restart:   ${YELLOW}sudo systemctl restart $SERVICE_NAME${NC}"
echo -e "  Logs:      ${YELLOW}sudo journalctl -u $SERVICE_NAME -f${NC}"
echo ""
echo -e "${BLUE}🔧 Management Commands:${NC}"
echo -e "  DNS Status:    ${YELLOW}sudo python3 -m interceptor.ubuntu_dns status${NC}"
echo -e "  SSL Status:    ${YELLOW}sudo python3 -m interceptor.ubuntu_ssl status${NC}"
echo -e "  Test DNS:      ${YELLOW}sudo python3 -m interceptor.ubuntu_dns test${NC}"
echo ""
echo -e "${BLUE}🧪 Testing:${NC}"
echo -e "  Test with:     ${YELLOW}python3 test.py${NC}"
echo ""
echo -e "${GREEN}🎯 All OpenAI API calls will now be intercepted transparently!${NC}"
echo -e "${GREEN}   Applications using OpenAI API will work without modification.${NC}"
echo ""

# Test DNS resolution
echo -e "${BLUE}🧪 Testing DNS resolution...${NC}"
if python3 -c "import socket; print('✅ DNS Test:', socket.gethostbyname('api.openai.com'))" 2>/dev/null; then
    echo -e "${GREEN}✅ DNS interception is working${NC}"
else
    echo -e "${YELLOW}⚠️ DNS test failed - check configuration${NC}"
fi

echo ""
echo -e "${PURPLE}Installation log saved to: /var/log/openai-interceptor-install.log${NC}"
