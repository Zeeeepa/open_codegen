#!/bin/bash
"""
Ubuntu Uninstallation Script for OpenAI API Interceptor
Complete removal of transparent OpenAI API interception from Ubuntu.
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

echo -e "${PURPLE}🗑️ OpenAI API Interceptor - Ubuntu Uninstallation${NC}"
echo -e "${PURPLE}==================================================${NC}"
echo ""

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}❌ This script must be run as root${NC}"
   echo -e "${YELLOW}   Please run: sudo $0${NC}"
   exit 1
fi

echo -e "${GREEN}✅ Running as root${NC}"
echo ""

# Stop and disable service
echo -e "${BLUE}🛑 Stopping and disabling service...${NC}"
if systemctl is-active --quiet "$SERVICE_NAME"; then
    systemctl stop "$SERVICE_NAME"
    echo -e "${GREEN}✅ Service stopped${NC}"
else
    echo -e "${YELLOW}ℹ️ Service was not running${NC}"
fi

if systemctl is-enabled --quiet "$SERVICE_NAME" 2>/dev/null; then
    systemctl disable "$SERVICE_NAME"
    echo -e "${GREEN}✅ Service disabled${NC}"
else
    echo -e "${YELLOW}ℹ️ Service was not enabled${NC}"
fi

# Remove systemd service file
echo -e "${BLUE}🗑️ Removing systemd service file...${NC}"
if [ -f "/etc/systemd/system/$SERVICE_NAME.service" ]; then
    rm "/etc/systemd/system/$SERVICE_NAME.service"
    systemctl daemon-reload
    echo -e "${GREEN}✅ Service file removed${NC}"
else
    echo -e "${YELLOW}ℹ️ Service file not found${NC}"
fi

# Disable DNS interception
echo -e "${BLUE}🌐 Disabling DNS interception...${NC}"
if [ -d "$INSTALL_DIR" ]; then
    cd "$INSTALL_DIR"
    python3 -m interceptor.ubuntu_dns disable 2>/dev/null || echo -e "${YELLOW}⚠️ DNS disable had issues${NC}"
    echo -e "${GREEN}✅ DNS interception disabled${NC}"
else
    echo -e "${YELLOW}ℹ️ Installation directory not found${NC}"
fi

# Remove SSL certificates
echo -e "${BLUE}🔐 Removing SSL certificates...${NC}"
if [ -d "$INSTALL_DIR" ]; then
    cd "$INSTALL_DIR"
    python3 -m interceptor.ubuntu_ssl remove 2>/dev/null || echo -e "${YELLOW}⚠️ SSL removal had issues${NC}"
    echo -e "${GREEN}✅ SSL certificates removed${NC}"
else
    echo -e "${YELLOW}ℹ️ Installation directory not found${NC}"
fi

# Remove installation directory
echo -e "${BLUE}📁 Removing installation directory...${NC}"
if [ -d "$INSTALL_DIR" ]; then
    rm -rf "$INSTALL_DIR"
    echo -e "${GREEN}✅ Installation directory removed${NC}"
else
    echo -e "${YELLOW}ℹ️ Installation directory not found${NC}"
fi

# Clean up any remaining files
echo -e "${BLUE}🧹 Cleaning up remaining files...${NC}"

# Remove any backup files
if [ -f "/etc/hosts.openai-interceptor.backup" ]; then
    rm "/etc/hosts.openai-interceptor.backup"
    echo -e "${GREEN}✅ Removed hosts backup file${NC}"
fi

# Remove certificate directory if it exists
if [ -d "/usr/local/share/ca-certificates/openai-interceptor" ]; then
    rm -rf "/usr/local/share/ca-certificates/openai-interceptor"
    update-ca-certificates 2>/dev/null || true
    echo -e "${GREEN}✅ Removed certificate directory${NC}"
fi

echo ""
echo -e "${PURPLE}🎉 Uninstallation Complete!${NC}"
echo -e "${PURPLE}===========================${NC}"
echo ""
echo -e "${GREEN}✅ OpenAI API Interceptor has been completely removed${NC}"
echo ""
echo -e "${BLUE}🔍 Verification:${NC}"

# Test DNS resolution
echo -e "${BLUE}🧪 Testing DNS resolution...${NC}"
if python3 -c "import socket; ip=socket.gethostbyname('api.openai.com'); print('DNS Test:', ip); exit(0 if ip != '127.0.0.1' else 1)" 2>/dev/null; then
    echo -e "${GREEN}✅ DNS interception successfully removed${NC}"
else
    echo -e "${YELLOW}⚠️ DNS may still be intercepted - check /etc/hosts manually${NC}"
fi

# Check service status
if systemctl list-unit-files | grep -q "$SERVICE_NAME"; then
    echo -e "${YELLOW}⚠️ Service file may still exist${NC}"
else
    echo -e "${GREEN}✅ Service completely removed${NC}"
fi

# Check installation directory
if [ -d "$INSTALL_DIR" ]; then
    echo -e "${YELLOW}⚠️ Installation directory still exists${NC}"
else
    echo -e "${GREEN}✅ Installation directory removed${NC}"
fi

echo ""
echo -e "${GREEN}🎯 OpenAI API calls will now go to the real OpenAI servers${NC}"
echo -e "${GREEN}   Normal OpenAI API functionality has been restored.${NC}"
echo ""
echo -e "${BLUE}ℹ️ If you experience any issues, you may need to:${NC}"
echo -e "  - Restart your applications${NC}"
echo -e "  - Clear DNS cache: ${YELLOW}sudo resolvectl flush-caches${NC} (or ${YELLOW}sudo systemd-resolve --flush-caches${NC} on older systems)"
echo -e "  - Check /etc/hosts for any remaining entries${NC}"
echo ""
