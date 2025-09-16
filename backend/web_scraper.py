"""
Web Scraper for OpenAI Codegen Adapter

This module analyzes websites to discover API endpoints and create
client integrations that can route to any AI provider.
"""

import json
import uuid
import asyncio
import aiohttp
import re
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Set
from pathlib import Path
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class WebScraper:
    """Analyzes websites to discover API endpoints and resources"""
    
    def __init__(self, storage_path: str = "data/websites.json"):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.websites = {}
        self.analysis_progress = {}
        self._load_websites()
    
    def _load_websites(self):
        """Load websites from storage"""
        try:
            if self.storage_path.exists():
                with open(self.storage_path, 'r') as f:
                    self.websites = json.load(f)
                logger.info(f"Loaded {len(self.websites)} websites from storage")
            else:
                self.websites = {}
        except Exception as e:
            logger.error(f"Failed to load websites: {e}")
            self.websites = {}
    
    def _save_websites(self):
        """Save websites to storage"""
        try:
            with open(self.storage_path, 'w') as f:
                json.dump(self.websites, f, indent=2, default=str)
            logger.info(f"Saved {len(self.websites)} websites to storage")
        except Exception as e:
            logger.error(f"Failed to save websites: {e}")
    
    async def get_websites(self) -> List[Dict[str, Any]]:
        """Get all analyzed websites"""
        return list(self.websites.values())
    
    async def start_analysis(self, url: str) -> str:
        """Start website analysis and return analysis ID"""
        analysis_id = str(uuid.uuid4())
        self.analysis_progress[analysis_id] = {
            "url": url,
            "percentage": 0,
            "completed": False,
            "started_at": datetime.now().isoformat(),
        }
        logger.info(f"Started analysis for {url} with ID {analysis_id}")
        return analysis_id
    
    async def get_analysis_progress(self, analysis_id: str) -> Dict[str, Any]:
        """Get analysis progress"""
        if analysis_id not in self.analysis_progress:
            raise ValueError(f"Analysis {analysis_id} not found")
        return self.analysis_progress[analysis_id]
    
    async def get_analysis_results(self, analysis_id: str) -> Dict[str, Any]:
        """Get analysis results"""
        if analysis_id not in self.analysis_progress:
            raise ValueError(f"Analysis {analysis_id} not found")
        
        progress = self.analysis_progress[analysis_id]
        if not progress["completed"]:
            raise ValueError(f"Analysis {analysis_id} not completed yet")
        
        return progress.get("results", {})
    
    async def analyze_website(self, url: str, analysis_id: str):
        """Analyze a website for API endpoints and resources"""
        try:
            logger.info(f"Starting website analysis for {url}")
            
            # Update progress
            self.analysis_progress[analysis_id]["percentage"] = 10
            
            # Fetch the main page
            html_content = await self._fetch_page(url)
            if not html_content:
                raise Exception("Failed to fetch website content")
            
            self.analysis_progress[analysis_id]["percentage"] = 30
            
            # Parse HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract basic information
            title = soup.find('title')
            title_text = title.get_text().strip() if title else urlparse(url).netloc
            
            self.analysis_progress[analysis_id]["percentage"] = 50
            
            # Discover API endpoints
            endpoints = await self._discover_endpoints(url, soup, html_content)
            
            self.analysis_progress[analysis_id]["percentage"] = 70
            
            # Extract links and resources
            links = self._extract_links(url, soup)
            
            self.analysis_progress[analysis_id]["percentage"] = 90
            
            # Compile results
            results = {
                "url": url,
                "title": title_text,
                "endpoints": endpoints,
                "links": links,
                "analysis_date": datetime.now().isoformat(),
                "total_endpoints": len(endpoints),
                "total_links": len(links),
            }
            
            # Mark as completed
            self.analysis_progress[analysis_id]["percentage"] = 100
            self.analysis_progress[analysis_id]["completed"] = True
            self.analysis_progress[analysis_id]["results"] = results
            
            logger.info(f"Completed analysis for {url}: {len(endpoints)} endpoints, {len(links)} links")
            
        except Exception as e:
            logger.error(f"Website analysis failed for {url}: {e}")
            self.analysis_progress[analysis_id]["error"] = str(e)
            self.analysis_progress[analysis_id]["completed"] = True
    
    async def _fetch_page(self, url: str) -> Optional[str]:
        """Fetch a web page"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        return await response.text()
                    else:
                        logger.warning(f"Failed to fetch {url}: HTTP {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
    
    async def _discover_endpoints(self, base_url: str, soup: BeautifulSoup, html_content: str) -> List[Dict[str, Any]]:
        """Discover API endpoints from website content"""
        endpoints = []
        
        # 1. Look for API documentation patterns
        endpoints.extend(self._find_api_docs_endpoints(base_url, soup))
        
        # 2. Analyze JavaScript for API calls
        endpoints.extend(self._find_js_endpoints(base_url, soup, html_content))
        
        # 3. Look for common API patterns in links
        endpoints.extend(self._find_link_endpoints(base_url, soup))
        
        # 4. Check for OpenAPI/Swagger specs
        endpoints.extend(await self._find_openapi_endpoints(base_url))
        
        # Remove duplicates and sort by confidence
        unique_endpoints = self._deduplicate_endpoints(endpoints)
        return sorted(unique_endpoints, key=lambda x: x.get('confidence', 0), reverse=True)
    
    def _find_api_docs_endpoints(self, base_url: str, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Find endpoints from API documentation"""
        endpoints = []
        
        # Look for code blocks with HTTP methods
        code_blocks = soup.find_all(['code', 'pre'])
        for block in code_blocks:
            text = block.get_text()
            
            # Match HTTP method patterns
            http_patterns = [
                r'(GET|POST|PUT|DELETE|PATCH)\s+([/\w\-\{\}]+)',
                r'(curl|fetch|axios).*?([/\w\-\{\}]+)',
                r'https?://[^\s]+/api[^\s]*',
            ]
            
            for pattern in http_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple) and len(match) >= 2:
                        method = match[0].upper()
                        path = match[1]
                        
                        if method in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                            endpoints.append({
                                'method': method,
                                'path': path,
                                'url': urljoin(base_url, path),
                                'confidence': 0.8,
                                'source': 'api_docs',
                                'description': f'Found in API documentation'
                            })
        
        return endpoints
    
    def _find_js_endpoints(self, base_url: str, soup: BeautifulSoup, html_content: str) -> List[Dict[str, Any]]:
        """Find endpoints from JavaScript code"""
        endpoints = []
        
        # Extract JavaScript content
        js_content = ""
        for script in soup.find_all('script'):
            if script.string:
                js_content += script.string + "\n"
        
        # Also check inline HTML for JS
        js_content += html_content
        
        # Look for API call patterns
        api_patterns = [
            r'fetch\s*\(\s*[\'"`]([^\'"`]+)[\'"`]',
            r'axios\.\w+\s*\(\s*[\'"`]([^\'"`]+)[\'"`]',
            r'\.get\s*\(\s*[\'"`]([^\'"`]+)[\'"`]',
            r'\.post\s*\(\s*[\'"`]([^\'"`]+)[\'"`]',
            r'XMLHttpRequest.*?open\s*\(\s*[\'"`](\w+)[\'"`]\s*,\s*[\'"`]([^\'"`]+)[\'"`]',
            r'/api/[^\s\'"]+',
            r'/v\d+/[^\s\'"]+',
        ]
        
        for pattern in api_patterns:
            matches = re.findall(pattern, js_content, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    if len(match) == 2:  # XMLHttpRequest pattern
                        method, path = match
                        method = method.upper()
                    else:
                        method = 'GET'
                        path = match[0]
                else:
                    method = 'GET'
                    path = match
                
                if path.startswith('/') or path.startswith('http'):
                    full_url = urljoin(base_url, path) if path.startswith('/') else path
                    endpoints.append({
                        'method': method,
                        'path': path,
                        'url': full_url,
                        'confidence': 0.7,
                        'source': 'javascript',
                        'description': f'Found in JavaScript code'
                    })
        
        return endpoints
    
    def _find_link_endpoints(self, base_url: str, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Find potential endpoints from links"""
        endpoints = []
        
        # Look for links that might be API endpoints
        links = soup.find_all('a', href=True)
        for link in links:
            href = link['href']
            text = link.get_text().strip()
            
            # Check if link looks like an API endpoint
            if any(pattern in href.lower() for pattern in ['/api/', '/v1/', '/v2/', '/graphql', '/rest']):
                endpoints.append({
                    'method': 'GET',
                    'path': href,
                    'url': urljoin(base_url, href),
                    'confidence': 0.5,
                    'source': 'links',
                    'description': f'API-like link: {text}'
                })
        
        return endpoints
    
    async def _find_openapi_endpoints(self, base_url: str) -> List[Dict[str, Any]]:
        """Check for OpenAPI/Swagger specifications"""
        endpoints = []
        
        # Common OpenAPI spec locations
        spec_paths = [
            '/swagger.json',
            '/openapi.json',
            '/api-docs',
            '/docs/swagger.json',
            '/v1/swagger.json',
            '/api/swagger.json',
        ]
        
        for path in spec_paths:
            try:
                spec_url = urljoin(base_url, path)
                async with aiohttp.ClientSession() as session:
                    async with session.get(spec_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                        if response.status == 200:
                            spec_data = await response.json()
                            
                            # Parse OpenAPI spec
                            if 'paths' in spec_data:
                                for path, methods in spec_data['paths'].items():
                                    for method, details in methods.items():
                                        if method.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                                            endpoints.append({
                                                'method': method.upper(),
                                                'path': path,
                                                'url': urljoin(base_url, path),
                                                'confidence': 0.9,
                                                'source': 'openapi',
                                                'description': details.get('summary', 'OpenAPI endpoint')
                                            })
                            break  # Found a spec, no need to check others
            except Exception as e:
                logger.debug(f"Failed to fetch OpenAPI spec from {spec_url}: {e}")
                continue
        
        return endpoints
    
    def _extract_links(self, base_url: str, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract all links and resources from the page"""
        links = []
        
        # Extract regular links
        for link in soup.find_all('a', href=True):
            href = link['href']
            text = link.get_text().strip()
            
            links.append({
                'type': 'link',
                'url': urljoin(base_url, href),
                'text': text,
                'internal': urlparse(href).netloc == '' or urlparse(href).netloc == urlparse(base_url).netloc
            })
        
        # Extract script sources
        for script in soup.find_all('script', src=True):
            links.append({
                'type': 'script',
                'url': urljoin(base_url, script['src']),
                'text': 'JavaScript file',
                'internal': urlparse(script['src']).netloc == '' or urlparse(script['src']).netloc == urlparse(base_url).netloc
            })
        
        # Extract CSS links
        for css in soup.find_all('link', rel='stylesheet', href=True):
            links.append({
                'type': 'stylesheet',
                'url': urljoin(base_url, css['href']),
                'text': 'CSS file',
                'internal': urlparse(css['href']).netloc == '' or urlparse(css['href']).netloc == urlparse(base_url).netloc
            })
        
        return links
    
    def _deduplicate_endpoints(self, endpoints: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate endpoints"""
        seen = set()
        unique_endpoints = []
        
        for endpoint in endpoints:
            key = (endpoint['method'], endpoint['path'])
            if key not in seen:
                seen.add(key)
                unique_endpoints.append(endpoint)
        
        return unique_endpoints
    
    async def save_website(self, website_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save analyzed website"""
        try:
            website_id = str(uuid.uuid4())
            website = {
                "id": website_id,
                "url": website_data.get("url", ""),
                "name": website_data.get("name", ""),
                "analysis": website_data.get("analysis", {}),
                "endpoints": website_data.get("analysis", {}).get("endpoints", []),
                "links": website_data.get("analysis", {}).get("links", []),
                "created_at": datetime.now().isoformat(),
                "analysis_date": website_data.get("analysis", {}).get("analysis_date"),
            }
            
            self.websites[website_id] = website
            self._save_websites()
            
            logger.info(f"Saved website: {website['url']} ({website_id})")
            return website
        except Exception as e:
            logger.error(f"Failed to save website: {e}")
            raise


# Export main class
__all__ = ['WebScraper']

