import urllib.parse
import xml.etree.ElementTree as ET
import httpx
from bs4 import BeautifulSoup
from scrapers.fact_checker import is_relevant_to_query

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/rss+xml,application/xml,text/xml;q=0.9,*/*;q=0.8"
}

async def scrape_reddit_posts(query: str, limit: int = 15):
    """
    Scrape social discussions and public threads from Reddit.
    Uses Google News indexing for site:reddit.com to bypass Reddit 429 rate limits,
    with direct link extraction.
    """
    encoded_query = urllib.parse.quote(f"site:reddit.com {query}")
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
                
                # Clean title: strip "- Reddit" suffix
                clean_title = raw_title
                if clean_title.endswith("- Reddit"):
                    clean_title = clean_title[:-8].strip()
                    
                snippet = ""
                if desc_elem is not None and desc_elem.text:
                    soup = BeautifulSoup(desc_elem.text, "html.parser")
                    snippet = soup.get_text(separator=" ").strip()
                if not snippet:
                    snippet = f"Diskusi komunitas sosial Reddit seputar topik: {clean_title}."
                    
                # Strict relevance
                if not is_relevant_to_query(query, clean_title, snippet):
                    continue
                    
                items.append({
                    "id": f"reddit_{len(items)+1}",
                    "title": clean_title,
                    "url": link,
                    "snippet": snippet[:280] + ("..." if len(snippet) > 280 else ""),
                    "source": "Reddit Community",
                    "platform": "Reddit",
                    "platform_icon": "reddit",
                    "published_at": pub_date or "Diskusi Publik",
                    "category": "Media Sosial"
                })
                
                if len(items) >= limit:
                    break
    except Exception as e:
        print(f"[Error Reddit Scraper]: {e}")
        
    return items
