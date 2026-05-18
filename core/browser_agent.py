"""
LOVE Browser Agent — Wave 11 Deep Web Navigation
Allows LOVE to autonomously browse the web, read HTML, convert it to markdown, and extract information.
"""

import requests
import json
import urllib.parse
try:
    from bs4 import BeautifulSoup
    from markdownify import markdownify as md
except ImportError:
    pass

class WebBrowser:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
        self.session = requests.Session()
        
    def navigate(self, url: str) -> str:
        """Navigates to a URL and returns the parsed text/markdown content."""
        if not url.startswith("http"):
            url = "https://" + url
            
        print(f"[BrowserAgent] 🌐 Navigating to: {url}")
        try:
            response = self.session.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            # Parse HTML and convert to markdown
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove junk elements
            for element in soup(["script", "style", "nav", "footer", "iframe", "noscript"]):
                element.decompose()
                
            # Convert to markdown for LLM consumption
            markdown_text = md(str(soup), heading_style="ATX").strip()
            
            # Truncate if too massive (e.g. over 20,000 chars)
            if len(markdown_text) > 30000:
                markdown_text = markdown_text[:30000] + "\n\n...[CONTENT TRUNCATED FOR LENGTH]..."
                
            return markdown_text
        except requests.exceptions.RequestException as e:
            return f"Error navigating to {url}: {str(e)}"
        except Exception as e:
            return f"Error parsing {url}: {str(e)}"

    def search_web(self, query: str) -> str:
        """Searches duckduckgo and returns top links."""
        print(f"[BrowserAgent] 🔍 Searching for: {query}")
        try:
            url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
            response = self.session.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            
            for a in soup.find_all('a', class_='result__snippet'):
                title_elem = a.parent.parent.find('h2', class_='result__title')
                if not title_elem: continue
                title = title_elem.text.strip()
                snippet = a.text.strip()
                href = title_elem.find('a')['href']
                if href.startswith('//duckduckgo.com/l/?uddg='):
                    href = urllib.parse.unquote(href.split('uddg=')[1].split('&')[0])
                
                results.append({
                    "title": title,
                    "snippet": snippet,
                    "url": href
                })
                
                if len(results) >= 5: # Top 5 results
                    break
                    
            return json.dumps(results, indent=2)
        except Exception as e:
            return f"Error executing search: {str(e)}"

_browser = None

def get_browser() -> WebBrowser:
    global _browser
    if _browser is None:
        _browser = WebBrowser()
    return _browser

def register_browser_tools(registry):
    """Register browser tools into the LOVE Tool Registry."""
    browser = get_browser()
    
    registry.register_tool(
        name="browser_navigate",
        func=browser.navigate,
        description="Navigate to a URL and read the textual content of the webpage as markdown.",
        parameters={
            "url": "The full URL to navigate to (e.g., 'https://en.wikipedia.org/wiki/AGI')."
        }
    )
    
    registry.register_tool(
        name="browser_search",
        func=browser.search_web,
        description="Search the web and get the top 5 links and snippets.",
        parameters={
            "query": "The search term."
        }
    )
