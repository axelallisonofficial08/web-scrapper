import urllib.parse
import xml.etree.ElementTree as ET
import httpx
from bs4 import BeautifulSoup
from scrapers.fact_checker import is_relevant_to_query

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/rss+xml,application/xml,text/xml;q=0.9,*/*;q=0.8"
}

def clean_ddg_url(url: str) -> str:
    """Extract actual destination URL from redirect link."""
    if "duckduckgo.com/l/?" in url:
        try:
            parsed = urllib.parse.urlparse(url)
            qs = urllib.parse.parse_qs(parsed.query)
            if "uddg" in qs:
                return qs["uddg"][0]
        except Exception:
            pass
    return url

async def scrape_twitter_x_mentions(query: str, limit: int = 15):
    """
    Search for Twitter/X posts & mentions using high-reliability RSS indexing.
    """
    encoded_query = urllib.parse.quote(f"site:x.com OR site:twitter.com {query}")
    url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
    items = []
    
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True, headers=HEADERS) as client:
            resp = await client.get(url)
            if resp.status_code != 200:
                return items
                
            root = ET.fromstring(resp.content)
            channel = root.find("channel")
            if channel is None:
                return items
                
            for item in channel.findall("item"):
                title_elem = item.find("title")
                link_elem = item.find("link")
                pub_elem = item.find("pubDate")
                desc_elem = item.find("description")
                
                raw_title = title_elem.text.strip() if title_elem is not None and title_elem.text else ""
                link = link_elem.text.strip() if link_elem is not None and link_elem.text else ""
                pub_date = pub_elem.text.strip() if pub_elem is not None and pub_elem.text else ""
                
                # Clean title
                clean_title = raw_title
                if clean_title.endswith("- X"):
                    clean_title = clean_title[:-3].strip()
                elif clean_title.endswith("- Twitter"):
                    clean_title = clean_title[:-9].strip()
                    
                snippet = ""
                if desc_elem is not None and desc_elem.text:
                    soup = BeautifulSoup(desc_elem.text, "html.parser")
                    snippet = soup.get_text(separator=" ").strip()
                if not snippet:
                    snippet = f"Postingan / opini publik di X (Twitter): {clean_title}"
                    
                if not is_relevant_to_query(query, clean_title, snippet):
                    continue
                    
                items.append({
                    "id": f"x_{len(items)+1}",
                    "title": clean_title,
                    "url": link,
                    "snippet": snippet[:280] + ("..." if len(snippet) > 280 else ""),
                    "source": "X (Twitter) Feed",
                    "platform": "X (Twitter)",
                    "platform_icon": "twitter",
                    "published_at": pub_date or "Terdeteksi Terkini",
                    "category": "Media Sosial"
                })
                
                if len(items) >= limit:
                    break
    except Exception as e:
        print(f"[Error X/Twitter Scraper]: {e}")
        
    return items

async def scrape_other_social_mentions(query: str, limit: int = 10):
    """
    Search for TikTok / Instagram / Threads public mentions via RSS indexing.
    """
    encoded_query = urllib.parse.quote(f"site:instagram.com OR site:tiktok.com {query}")
    url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
    items = []
    
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True, headers=HEADERS) as client:
            resp = await client.get(url)
            if resp.status_code != 200:
                return items
                
            root = ET.fromstring(resp.content)
            channel = root.find("channel")
            if channel is None:
                return items
                
            for item in channel.findall("item"):
                title_elem = item.find("title")
                link_elem = item.find("link")
                pub_elem = item.find("pubDate")
                desc_elem = item.find("description")
                
                title = title_elem.text.strip() if title_elem is not None and title_elem.text else ""
                link = link_elem.text.strip() if link_elem is not None and link_elem.text else ""
                pub_date = pub_elem.text.strip() if pub_elem is not None and pub_elem.text else ""
                
                snippet = ""
                if desc_elem is not None and desc_elem.text:
                    soup = BeautifulSoup(desc_elem.text, "html.parser")
                    snippet = soup.get_text(separator=" ").strip()
                    
                if not is_relevant_to_query(query, title, snippet):
                    continue
                    
                platform_name = "TikTok" if "tiktok" in title.lower() or "tiktok" in link.lower() else "Instagram"
                platform_icon = "tiktok" if platform_name == "TikTok" else "instagram"
                
                items.append({
                    "id": f"soc_{len(items)+1}",
                    "title": title,
                    "url": link,
                    "snippet": snippet[:280] + ("..." if len(snippet) > 280 else ""),
                    "source": f"{platform_name} Post",
                    "platform": platform_name,
                    "platform_icon": platform_icon,
                    "published_at": pub_date or "Terdeteksi Terkini",
                    "category": "Media Sosial"
                })
                
                if len(items) >= limit:
                    break
    except Exception as e:
        print(f"[Error Other Social Scraper]: {e}")
        
    return items
