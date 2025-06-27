"""
Advanced web tools for internet access, browser automation, and web scraping.
"""

import requests
import json
import time
import os
import subprocess
from typing import Dict, List, Any, Optional, Union
from urllib.parse import urljoin, urlparse, quote
from pathlib import Path
import tempfile
import base64

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, WebDriverException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

try:
    import PIL
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class WebBrowser:
    """Advanced browser automation and web interaction."""
    
    def __init__(self, headless: bool = True, timeout: int = 10):
        self.headless = headless
        self.timeout = timeout
        self.driver = None
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
    
    def start_browser(self) -> str:
        """Initialize and start the browser."""
        if not SELENIUM_AVAILABLE:
            return "Selenium not available. Install with: pip install selenium"
        
        try:
            options = Options()
            if self.headless:
                options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")
            
            self.driver = webdriver.Chrome(options=options)
            self.driver.set_page_load_timeout(self.timeout)
            return "Browser started successfully"
        except Exception as e:
            return f"Failed to start browser: {str(e)}"
    
    def navigate_to(self, url: str) -> str:
        """Navigate to a specific URL."""
        if not self.driver:
            result = self.start_browser()
            if "Failed" in result:
                return result
        
        try:
            self.driver.get(url)
            return f"Successfully navigated to {url}"
        except Exception as e:
            return f"Failed to navigate to {url}: {str(e)}"
    
    def get_page_content(self, url: Optional[str] = None) -> str:
        """Get the current page content or navigate to URL and get content."""
        if url:
            nav_result = self.navigate_to(url)
            if "Failed" in nav_result:
                return nav_result
        
        if not self.driver:
            return "Browser not started"
        
        try:
            return self.driver.page_source
        except Exception as e:
            return f"Failed to get page content: {str(e)}"
    
    def find_element(self, selector: str, by_type: str = "css") -> str:
        """Find an element on the page."""
        if not self.driver:
            return "Browser not started"
        
        try:
            if by_type.lower() == "css":
                element = self.driver.find_element(By.CSS_SELECTOR, selector)
            elif by_type.lower() == "xpath":
                element = self.driver.find_element(By.XPATH, selector)
            elif by_type.lower() == "id":
                element = self.driver.find_element(By.ID, selector)
            elif by_type.lower() == "class":
                element = self.driver.find_element(By.CLASS_NAME, selector)
            else:
                return f"Unsupported selector type: {by_type}"
            
            return f"Element found: {element.text[:200]}..."
        except Exception as e:
            return f"Element not found: {str(e)}"
    
    def click_element(self, selector: str, by_type: str = "css") -> str:
        """Click an element on the page."""
        if not self.driver:
            return "Browser not started"
        
        try:
            if by_type.lower() == "css":
                element = WebDriverWait(self.driver, self.timeout).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
            elif by_type.lower() == "xpath":
                element = WebDriverWait(self.driver, self.timeout).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
            elif by_type.lower() == "id":
                element = WebDriverWait(self.driver, self.timeout).until(
                    EC.element_to_be_clickable((By.ID, selector))
                )
            else:
                return f"Unsupported selector type: {by_type}"
            
            element.click()
            return f"Successfully clicked element: {selector}"
        except TimeoutException:
            return f"Timeout waiting for element to be clickable: {selector}"
        except Exception as e:
            return f"Failed to click element: {str(e)}"
    
    def type_text(self, selector: str, text: str, by_type: str = "css") -> str:
        """Type text into an input element."""
        if not self.driver:
            return "Browser not started"
        
        try:
            if by_type.lower() == "css":
                element = WebDriverWait(self.driver, self.timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
            elif by_type.lower() == "xpath":
                element = WebDriverWait(self.driver, self.timeout).until(
                    EC.presence_of_element_located((By.XPATH, selector))
                )
            elif by_type.lower() == "id":
                element = WebDriverWait(self.driver, self.timeout).until(
                    EC.presence_of_element_located((By.ID, selector))
                )
            else:
                return f"Unsupported selector type: {by_type}"
            
            element.clear()
            element.send_keys(text)
            return f"Successfully typed text into: {selector}"
        except TimeoutException:
            return f"Timeout waiting for element: {selector}"
        except Exception as e:
            return f"Failed to type text: {str(e)}"
    
    def take_screenshot(self, filename: Optional[str] = None) -> str:
        """Take a screenshot of the current page."""
        if not self.driver:
            return "Browser not started"
        
        try:
            if not filename:
                filename = f"screenshot_{int(time.time())}.png"
            
            self.driver.save_screenshot(filename)
            return f"Screenshot saved as: {filename}"
        except Exception as e:
            return f"Failed to take screenshot: {str(e)}"
    
    def execute_javascript(self, script: str) -> str:
        """Execute JavaScript on the current page."""
        if not self.driver:
            return "Browser not started"
        
        try:
            result = self.driver.execute_script(script)
            return f"JavaScript executed. Result: {str(result)[:500]}..."
        except Exception as e:
            return f"Failed to execute JavaScript: {str(e)}"
    
    def close_browser(self) -> str:
        """Close the browser."""
        if self.driver:
            try:
                self.driver.quit()
                self.driver = None
                return "Browser closed successfully"
            except Exception as e:
                return f"Error closing browser: {str(e)}"
        return "Browser was not running"


class WebScraper:
    """Advanced web scraping and data extraction."""
    
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
    
    def fetch_url(self, url: str, method: str = "GET", data: Optional[Dict] = None, headers: Optional[Dict] = None) -> Dict[str, Any]:
        """Fetch content from a URL with advanced options."""
        try:
            if headers:
                self.session.headers.update(headers)
            
            if method.upper() == "GET":
                response = self.session.get(url, timeout=self.timeout)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data, timeout=self.timeout)
            elif method.upper() == "PUT":
                response = self.session.put(url, json=data, timeout=self.timeout)
            else:
                return {"error": f"Unsupported HTTP method: {method}"}
            
            response.raise_for_status()
            
            # Try to parse as JSON first
            try:
                content = response.json()
                content_type = "json"
            except:
                content = response.text
                content_type = "text"
            
            return {
                "status_code": response.status_code,
                "content": content,
                "content_type": content_type,
                "headers": dict(response.headers),
                "url": response.url
            }
        except requests.exceptions.RequestException as e:
            return {"error": f"Request failed: {str(e)}"}
    
    def parse_html(self, html: str, selectors: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Parse HTML content and extract data using CSS selectors."""
        if not BS4_AVAILABLE:
            return {"error": "BeautifulSoup not available. Install with: pip install beautifulsoup4"}
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            result = {
                "title": soup.title.string if soup.title else None,
                "text": soup.get_text()[:1000],  # First 1000 chars
                "links": [{"text": a.get_text(), "href": a.get("href")} 
                         for a in soup.find_all("a", href=True)[:10]],  # First 10 links
                "images": [{"alt": img.get("alt", ""), "src": img.get("src")} 
                          for img in soup.find_all("img")[:5]]  # First 5 images
            }
            
            # Extract custom selectors if provided
            if selectors:
                result["custom"] = {}
                for name, selector in selectors.items():
                    elements = soup.select(selector)
                    result["custom"][name] = [elem.get_text().strip() for elem in elements[:5]]
            
            return result
        except Exception as e:
            return {"error": f"Failed to parse HTML: {str(e)}"}
    
    def search_web(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """Search the web using DuckDuckGo (no API key required)."""
        try:
            # Use DuckDuckGo Instant Answer API
            url = "https://api.duckduckgo.com/"
            params = {
                "q": query,
                "format": "json",
                "no_html": "1",
                "skip_disambig": "1"
            }
            
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            
            results = []
            
            # Add instant answer if available
            if data.get("Answer"):
                results.append({
                    "title": "Instant Answer",
                    "snippet": data["Answer"],
                    "url": data.get("AnswerURL", ""),
                    "type": "instant_answer"
                })
            
            # Add related topics
            for topic in data.get("RelatedTopics", [])[:num_results-len(results)]:
                if isinstance(topic, dict) and "Text" in topic:
                    results.append({
                        "title": topic.get("Text", "")[:100] + "...",
                        "snippet": topic.get("Text", ""),
                        "url": topic.get("FirstURL", ""),
                        "type": "related_topic"
                    })
            
            return results[:num_results]
        except Exception as e:
            return [{"error": f"Search failed: {str(e)}"}]


class APIManager:
    """Manage and interact with various APIs."""
    
    def __init__(self):
        self.session = requests.Session()
        self.api_keys = {}
    
    def set_api_key(self, service: str, key: str) -> str:
        """Set API key for a service."""
        self.api_keys[service] = key
        return f"API key set for {service}"
    
    def get_weather(self, location: str) -> Dict[str, Any]:
        """Get weather information using a free weather API."""
        try:
            # Using wttr.in - no API key required
            url = f"https://wttr.in/{quote(location)}?format=j1"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": f"Failed to get weather: {str(e)}"}
    
    def get_news(self, query: str = "technology", language: str = "en") -> List[Dict[str, Any]]:
        """Get news using a free news API."""
        try:
            # Using free news API (no key required for basic usage)
            url = "https://newsapi.org/v2/everything"
            params = {
                "q": query,
                "language": language,
                "sortBy": "publishedAt",
                "pageSize": 5
            }
            
            if "newsapi" in self.api_keys:
                params["apiKey"] = self.api_keys["newsapi"]
            
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 401:
                # Try alternative free news source
                return self._get_news_alternative(query)
            
            response.raise_for_status()
            data = response.json()
            return data.get("articles", [])
        except Exception as e:
            return [{"error": f"Failed to get news: {str(e)}"}]
    
    def _get_news_alternative(self, query: str) -> List[Dict[str, Any]]:
        """Alternative news source that doesn't require API key."""
        try:
            # Use RSS feeds or web scraping as fallback
            scraper = WebScraper()
            # This is a simplified example - you'd implement RSS parsing here
            return [{"title": f"Alternative news search for: {query}", "description": "API key required for full news access"}]
        except:
            return [{"error": "No news sources available without API key"}]
    
    def make_api_call(self, url: str, method: str = "GET", data: Optional[Dict] = None, headers: Optional[Dict] = None) -> Dict[str, Any]:
        """Make a generic API call."""
        try:
            if headers:
                self.session.headers.update(headers)
            
            if method.upper() == "GET":
                response = self.session.get(url, timeout=10)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data, timeout=10)
            elif method.upper() == "PUT":
                response = self.session.put(url, json=data, timeout=10)
            elif method.upper() == "DELETE":
                response = self.session.delete(url, timeout=10)
            else:
                return {"error": f"Unsupported HTTP method: {method}"}
            
            response.raise_for_status()
            
            try:
                return response.json()
            except:
                return {"text": response.text, "status_code": response.status_code}
        except requests.exceptions.RequestException as e:
            return {"error": f"API call failed: {str(e)}"}


# Global instances
web_browser = WebBrowser()
web_scraper = WebScraper()
api_manager = APIManager()


# Tool functions for the agent
def browse_web(url: str, action: str = "get", **kwargs) -> str:
    """
    Browse the web with various actions.
    
    Actions:
    - get: Get page content
    - click: Click an element (requires selector)
    - type: Type text (requires selector and text)
    - screenshot: Take a screenshot
    - javascript: Execute JavaScript (requires script)
    """
    try:
        if action == "get":
            return web_browser.get_page_content(url)
        elif action == "click":
            if not kwargs.get("selector"):
                return "Click action requires 'selector' parameter"
            web_browser.navigate_to(url)
            return web_browser.click_element(kwargs["selector"], kwargs.get("by_type", "css"))
        elif action == "type":
            if not kwargs.get("selector") or not kwargs.get("text"):
                return "Type action requires 'selector' and 'text' parameters"
            web_browser.navigate_to(url)
            return web_browser.type_text(kwargs["selector"], kwargs["text"], kwargs.get("by_type", "css"))
        elif action == "screenshot":
            web_browser.navigate_to(url)
            return web_browser.take_screenshot(kwargs.get("filename") or f"screenshot_{int(time.time())}.png")
        elif action == "javascript":
            if not kwargs.get("script"):
                return "JavaScript action requires 'script' parameter"
            web_browser.navigate_to(url)
            return web_browser.execute_javascript(kwargs["script"])
        else:
            return f"Unsupported action: {action}"
    except Exception as e:
        return f"Web browsing failed: {str(e)}"


def search_internet(query: str, num_results: int = 5) -> str:
    """Search the internet for information."""
    try:
        results = web_scraper.search_web(query, num_results)
        return json.dumps(results, indent=2)
    except Exception as e:
        return f"Internet search failed: {str(e)}"


def fetch_web_content(url: str, method: str = "GET", data: Optional[Dict] = None) -> str:
    """Fetch content from a web URL."""
    try:
        result = web_scraper.fetch_url(url, method, data)
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return f"Web fetch failed: {str(e)}"


def parse_webpage(url: str, selectors: Optional[Dict[str, str]] = None) -> str:
    """Parse a webpage and extract structured data."""
    try:
        # First fetch the content
        result = web_scraper.fetch_url(url)
        if "error" in result:
            return json.dumps(result)
        
        # Then parse it
        parsed = web_scraper.parse_html(result["content"], selectors)
        return json.dumps(parsed, indent=2)
    except Exception as e:
        return f"Webpage parsing failed: {str(e)}"


def get_weather_info(location: str) -> str:
    """Get weather information for a location."""
    try:
        weather = api_manager.get_weather(location)
        return json.dumps(weather, indent=2)
    except Exception as e:
        return f"Weather fetch failed: {str(e)}"


def get_news_headlines(query: str = "technology", language: str = "en") -> str:
    """Get latest news headlines."""
    try:
        news = api_manager.get_news(query, language)
        return json.dumps(news, indent=2)
    except Exception as e:
        return f"News fetch failed: {str(e)}"


def call_api(url: str, method: str = "GET", data: Optional[Dict] = None, headers: Optional[Dict] = None) -> str:
    """Make a generic API call."""
    try:
        result = api_manager.make_api_call(url, method, data, headers)
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return f"API call failed: {str(e)}"


def install_web_dependencies() -> str:
    """Install required dependencies for web functionality."""
    try:
        dependencies = [
            "selenium>=4.0.0",
            "beautifulsoup4>=4.9.0",
            "Pillow>=8.0.0",
            "webdriver-manager>=3.8.0"
        ]
        
        for dep in dependencies:
            subprocess.run(["pip", "install", dep], check=True, capture_output=True)
        
        return "Web dependencies installed successfully"
    except subprocess.CalledProcessError as e:
        return f"Failed to install dependencies: {str(e)}"
    except Exception as e:
        return f"Installation error: {str(e)}"
