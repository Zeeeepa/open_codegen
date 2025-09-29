#!/usr/bin/env python3
"""
Auto-populate API repositories with actual code files
This script automatically clones/updates all API repositories to ensure code files are present
"""

import os
import subprocess
import sys
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Repository configurations with actual code
API_REPOSITORIES = [
    {
        "name": "k2think2api3",
        "url": "https://github.com/Zeeeepa/k2think2api3.git",
        "path": "apis/k2think2api3",
        "main_files": ["k2think_proxy.py", "get_tokens.py"]
    },
    {
        "name": "k2think2api2", 
        "url": "https://github.com/Zeeeepa/k2think2api2.git",
        "path": "apis/k2think2api2",
        "main_files": ["main.py"]
    },
    {
        "name": "k2Think2Api",
        "url": "https://github.com/Zeeeepa/k2Think2Api.git", 
        "path": "apis/k2Think2Api",
        "main_files": ["main.py"]
    },
    {
        "name": "grok2api",
        "url": "https://github.com/Zeeeepa/grok2api.git",
        "path": "apis/grok2api", 
        "main_files": ["app.py", "wsgi.py"]
    },
    {
        "name": "OpenAI-Compatible-API-Proxy-for-Z",
        "url": "https://github.com/Zeeeepa/OpenAI-Compatible-API-Proxy-for-Z.git",
        "path": "apis/OpenAI-Compatible-API-Proxy-for-Z",
        "main_files": ["main.go"]
    },
    {
        "name": "Z.ai2api",
        "url": "https://github.com/Zeeeepa/Z.ai2api.git",
        "path": "apis/Z.ai2api",
        "main_files": ["app.py"]
    },
    {
        "name": "z.ai2api_python",
        "url": "https://github.com/Zeeeepa/z.ai2api_python.git",
        "path": "apis/z.ai2api_python", 
        "main_files": ["main.py"]
    },
    {
        "name": "ZtoApi",
        "url": "https://github.com/Zeeeepa/ZtoApi.git",
        "path": "apis/ZtoApi",
        "main_files": ["main.go"]
    },
    {
        "name": "zai-python-sdk",
        "url": "https://github.com/Zeeeepa/zai-python-sdk.git",
        "path": "apis/zai-python-sdk",
        "main_files": ["client.py", "custom_models.py", "__init__.py"]
    },
    {
        "name": "ZtoApits", 
        "url": "https://github.com/Zeeeepa/ZtoApits.git",
        "path": "apis/ZtoApits",
        "main_files": ["package.json", "index.js"]
    },
    # Documentation repositories (still included for completeness)
    {
        "name": "qwen-api",
        "url": "https://github.com/Zeeeepa/qwen-api.git", 
        "path": "apis/qwen-api",
        "main_files": ["README.md", "qwen.json"]
    },
    {
        "name": "qwenchat2api",
        "url": "https://github.com/Zeeeepa/qwenchat2api.git",
        "path": "apis/qwenchat2api", 
        "main_files": ["README.md"]
    }
]

def run_command(cmd, cwd=None, check=True):
    """Run a command and return the result"""
    try:
        logger.info(f"Running: {cmd}")
        result = subprocess.run(
            cmd, 
            shell=True, 
            cwd=cwd, 
            capture_output=True, 
            text=True,
            check=check
        )
        if result.stdout:
            logger.debug(f"STDOUT: {result.stdout}")
        if result.stderr:
            logger.debug(f"STDERR: {result.stderr}")
        return result
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {cmd}")
        logger.error(f"Error: {e.stderr}")
        if check:
            raise
        return e

def ensure_directory(path):
    """Ensure directory exists"""
    Path(path).mkdir(parents=True, exist_ok=True)

def clone_or_update_repo(repo_config):
    """Clone or update a single repository"""
    repo_path = Path(repo_config["path"])
    repo_name = repo_config["name"]
    repo_url = repo_config["url"]
    
    logger.info(f"Processing {repo_name}...")
    
    if repo_path.exists():
        # Repository exists, update it
        logger.info(f"Updating existing repository: {repo_name}")
        
        # Check if it's a git repository
        if (repo_path / ".git").exists():
            # Pull latest changes
            run_command("git fetch origin", cwd=repo_path)
            run_command("git reset --hard origin/main", cwd=repo_path, check=False)
            run_command("git pull origin main", cwd=repo_path, check=False)
        else:
            # Not a git repo, remove and clone fresh
            logger.warning(f"Directory exists but is not a git repo, removing: {repo_path}")
            import shutil
            shutil.rmtree(repo_path)
            ensure_directory(repo_path.parent)
            run_command(f"git clone {repo_url} {repo_path.name}", cwd=repo_path.parent)
    else:
        # Repository doesn't exist, clone it
        logger.info(f"Cloning new repository: {repo_name}")
        ensure_directory(repo_path.parent)
        run_command(f"git clone {repo_url} {repo_path.name}", cwd=repo_path.parent)
    
    # Verify main files exist
    missing_files = []
    for main_file in repo_config["main_files"]:
        file_path = repo_path / main_file
        if not file_path.exists():
            missing_files.append(main_file)
    
    if missing_files:
        logger.warning(f"Repository {repo_name} is missing expected files: {missing_files}")
    else:
        logger.info(f"✅ Repository {repo_name} has all expected files: {repo_config['main_files']}")
    
    return len(missing_files) == 0

def populate_all_apis():
    """Populate all API repositories with actual code"""
    logger.info("🚀 Starting API repository population...")
    
    # Ensure apis directory exists
    ensure_directory("apis")
    
    success_count = 0
    total_count = len(API_REPOSITORIES)
    
    for repo_config in API_REPOSITORIES:
        try:
            if clone_or_update_repo(repo_config):
                success_count += 1
        except Exception as e:
            logger.error(f"Failed to process {repo_config['name']}: {e}")
    
    logger.info(f"✅ Successfully populated {success_count}/{total_count} repositories")
    
    if success_count < total_count:
        logger.warning(f"⚠️  {total_count - success_count} repositories had issues")
        return False
    
    logger.info("🎉 All API repositories populated successfully!")
    return True

def main():
    """Main function"""
    try:
        success = populate_all_apis()
        if success:
            logger.info("🎯 All repositories are ready for use!")
            sys.exit(0)
        else:
            logger.error("❌ Some repositories failed to populate properly")
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("⏹️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"💥 Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
