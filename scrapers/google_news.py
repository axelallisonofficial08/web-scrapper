import urllib.parse
import xml.etree.ElementTree as ET
import httpx
from bs4 import BeautifulSoup
from scrapers.fact_checker import is_relevant_to_query

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/rss+xml,application/xml,text/xml;q=0.9,*/*;q=0.8"
}

async def fetch_gnews_feed(client: httpx.AsyncClient, query: str, hl: str, gl: str, ceid: str, limit: int):
    encoded_query = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={encoded_query}&hl={hl}&gl={gl}&ceid={ceid}"
    items = []
    try:
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
            source_elem = item.find("source")
            
            raw_title = title_elem.text if title_elem is not None and title_elem.text else ""
            link = link_elem.text if link_elem is not None and link_elem.text else ""
            pub_date = pub_elem.text if pub_elem is not None and pub_elem.text else ""
            
            source_name = "Google News"
            if source_elem is not None and source_elem.text:
                source_name = source_elem.text.strip()
            elif " - " in raw_title:
                parts = raw_title.rsplit(" - ", 1)
                raw_title = parts[0].strip()
                source_name = parts[1].strip()
                
            snippet = ""
            if desc_elem is not None and desc_elem.text:
                soup = BeautifulSoup(desc_elem.text, "html.parser")
                snippet = soup.get_text(separator=" ").strip()
                if snippet.startswith(raw_title):
                    snippet = snippet[len(raw_title):].strip()
            if not snippet:
                snippet = f"Berita dipublikasikan oleh {source_name}. Klik untuk membaca liputan lengkap di situs sumber."
                
            if not is_relevant_to_query(query, raw_title, snippet):
                continue
                
            items.append({
                "id": f"gnews_{len(items)+1}",
                "title": raw_title,
                "url": link,
                "snippet": snippet[:280] + ("..." if len(snippet) > 280 else ""),
                "source": source_name,
                "platform": "Google News",
                "platform_icon": "google",
                "published_at": pub_date,
                "category": "Media Berita"
            })
            
            if len(items) >= limit:
                break
    except Exception as e:
        print(f"[Error Google News Fetch]: {e}")
    return items

async def scrape_google_news(query: str, lang: str = "id", region: str = "ID", limit: int = 25):
    """
    Scrape news from Google News RSS. Fetches both Indonesian and Global news to maximize coverage.
    """
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True, headers=HEADERS) as client:
        # First fetch Indonesian news
        items = await fetch_gnews_feed(client, query, "id", "ID", "ID:id", limit)
        
        # If results are few or for broader coverage, also fetch international feed
        if len(items) < limit:
            global_items = await fetch_gnews_feed(client, query, "en-US", "US", "US:en", limit - len(items))
            seen_urls = set(i["url"] for i in items)
            for g in global_items:
                if g["url"] not in seen_urls:
                    items.append(g)
                    
        return items[:limit]
