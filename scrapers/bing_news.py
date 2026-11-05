import urllib.parse
import xml.etree.ElementTree as ET
import httpx
from bs4 import BeautifulSoup
from scrapers.fact_checker import is_relevant_to_query

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/rss+xml,application/xml,text/xml;q=0.9,*/*;q=0.8"
}

async def scrape_bing_news(query: str, limit: int = 20):
    """
    Scrape news from Bing News RSS.
    """
    encoded_query = urllib.parse.quote(query)
    url = f"https://www.bing.com/news/search?q={encoded_query}&format=rss"
    
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
                source_elem = item.find("Source") or item.find("source")
                
                title = title_elem.text.strip() if title_elem is not None and title_elem.text else ""
                link = link_elem.text.strip() if link_elem is not None and link_elem.text else ""
                pub_date = pub_elem.text.strip() if pub_elem is not None and pub_elem.text else ""
                
                # In Bing News RSS, redirect URL is often inside link or apiclick url
                if "url=" in link:
                    try:
                        parsed = urllib.parse.urlparse(link)
                        qs = urllib.parse.parse_qs(parsed.query)
                        if "url" in qs:
                            link = qs["url"][0]
                    except Exception:
                        pass
                        
                source_name = "Bing News"
                if source_elem is not None and source_elem.text:
                    source_name = source_elem.text.strip()
                    
                snippet = ""
                if desc_elem is not None and desc_elem.text:
                    soup = BeautifulSoup(desc_elem.text, "html.parser")
                    snippet = soup.get_text(separator=" ").strip()
                if not snippet:
                    snippet = f"Berita terindeks via Bing News dari penerbit {source_name}."
                    
                if not is_relevant_to_query(query, title, snippet):
                    continue
                    
                items.append({
                    "id": f"bing_{len(items)+1}",
                    "title": title,
                    "url": link,
                    "snippet": snippet[:280] + ("..." if len(snippet) > 280 else ""),
                    "source": source_name,
                    "platform": "Bing News",
                    "platform_icon": "bing",
                    "published_at": pub_date,
                    "category": "Media Berita"
                })
                
                if len(items) >= limit:
                    break
    except Exception as e:
        print(f"[Error Bing News Scraper]: {e}")
        
    return items
