#!/usr/bin/env python3
"""
Setup Git hooks for automatic API repository population
"""

import os
import shutil
import stat
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_git_hooks():
    """Setup Git hooks for automatic API population"""
    logger.info("🔧 Setting up Git hooks for automatic API population...")
    
    # Paths
    hooks_source_dir = Path(".githooks")
    git_hooks_dir = Path(".git/hooks")
    
    if not git_hooks_dir.exists():
        logger.error("❌ .git/hooks directory not found. Are you in a Git repository?")
        return False
    
    if not hooks_source_dir.exists():
        logger.error("❌ .githooks directory not found")
        return False
    
    # Copy hooks
    hooks_installed = 0
    for hook_file in hooks_source_dir.glob("*"):
        if hook_file.is_file():
            dest_file = git_hooks_dir / hook_file.name
            
            # Copy the hook
            shutil.copy2(hook_file, dest_file)
            
            # Make it executable
            dest_file.chmod(dest_file.stat().st_mode | stat.S_IEXEC)
            
            logger.info(f"✅ Installed hook: {hook_file.name}")
            hooks_installed += 1
    
    if hooks_installed > 0:
        logger.info(f"🎉 Successfully installed {hooks_installed} Git hooks!")
        logger.info("📋 Hooks will automatically populate API repositories on:")
        logger.info("   - git pull (post-merge)")
        logger.info("   - git checkout (post-checkout)")
        return True
    else:
        logger.warning("⚠️  No hooks found to install")
        return False

def main():
    """Main function"""
    try:
        success = setup_git_hooks()
        if success:
            logger.info("🎯 Git hooks setup complete!")
            return 0
        else:
            logger.error("❌ Failed to setup Git hooks")
            return 1
    except Exception as e:
        logger.error(f"💥 Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
