import urllib.parse
import xml.etree.ElementTree as ET
import httpx
import re
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/rss+xml,application/xml,text/xml;q=0.9,*/*;q=0.8"
}

def is_relevant_to_query(query: str, title: str, snippet: str = "") -> bool:
    """
    Check if an item is strictly relevant to the search query.
    Prevents unrelated blog feed items from bleeding into different topics.
    """
    clean_q = re.sub(r'[^\w\s]', ' ', query.lower())
    words = [w for w in clean_q.split() if len(w) > 2]
    if not words:
        words = [w for w in clean_q.split() if w]
    if not words:
        return True
        
    combined = (title + " " + snippet).lower()
    return any(w in combined for w in words)

async def scrape_turnbackhoax(query: str, limit: int = 10):
    """
    Search TurnBackHoax.id (Mafindo) RSS feed with STRICT relevance filtering.
    """
    encoded_query = urllib.parse.quote(query)
    url = f"https://turnbackhoax.id/feed/?s={encoded_query}"
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

                # CRITICAL: Verify this post actually pertains to the user's query!
                # WordPress feeds fallback to latest posts if search query yields 0 matches.
                if not is_relevant_to_query(query, title, snippet):
                    continue
                    
                # Identify fact-check verdict
                verdict = "Klarifikasi / Cek Fakta"
                verdict_type = "warning"
                upper_title = title.upper()
                if "[SALAH]" in upper_title or "HOAX" in upper_title or "HOAKS" in upper_title:
                    verdict = "HOAKS / SALAH"
                    verdict_type = "danger"
                elif "[DISINFORMASI]" in upper_title:
                    verdict = "DISINFORMASI"
                    verdict_type = "danger"
                elif "[PENIPUAN]" in upper_title or "SCAM" in upper_title:
                    verdict = "PENIPUAN / SCAM"
                    verdict_type = "danger"
                elif "[MANIPULASI]" in upper_title or "[KONTEN DIMANIPULASI]" in upper_title:
                    verdict = "KONTEN DIMANIPULASI"
                    verdict_type = "danger"
                elif "[BENAR]" in upper_title:
                    verdict = "FAKTA BENAR"
                    verdict_type = "success"
                    
                items.append({
                    "id": f"fact_{len(items)+1}",
                    "title": title,
                    "url": link,
                    "snippet": snippet[:280] + ("..." if len(snippet) > 280 else ""),
                    "source": "TurnBackHoax (Mafindo)",
                    "platform": "Cek Fakta",
                    "platform_icon": "shield-alert",
                    "published_at": pub_date,
                    "category": "Cek Fakta / Verifikasi",
                    "verdict": verdict,
                    "verdict_type": verdict_type
                })
                
                if len(items) >= limit:
                    break
    except Exception as e:
        print(f"[Error TurnBackHoax Scraper]: {e}")
        
    return items

async def scrape_additional_factchecks(query: str, limit: int = 5):
    """
    Search indexed national fact check articles (Cek Fakta Kompas, Tempo, TurnBackHoax, RRI)
    using Google News Fact Check query.
    """
    encoded_query = urllib.parse.quote(f"{query} (cek fakta OR hoaks OR disinformasi OR klarifikasi OR site:turnbackhoax.id OR site:cekfakta.com)")
    url = f"https://news.google.com/rss/search?q={encoded_query}&hl=id&gl=ID&ceid=ID:id"
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
                source_elem = item.find("source")
                
                title = title_elem.text.strip() if title_elem is not None and title_elem.text else ""
                link = link_elem.text.strip() if link_elem is not None and link_elem.text else ""
                pub_date = pub_elem.text.strip() if pub_elem is not None and pub_elem.text else ""
                
                source_name = "Cek Fakta"
                if source_elem is not None and source_elem.text:
                    source_name = source_elem.text.strip()
                    
                snippet = ""
                if desc_elem is not None and desc_elem.text:
                    soup = BeautifulSoup(desc_elem.text, "html.parser")
                    snippet = soup.get_text(separator=" ").strip()
                    
                # STRICT RELEVANCE: must mention query keywords
                if not is_relevant_to_query(query, title, snippet):
                    continue
                    
                # MUST actually be a fact check article
                lower_text = (title + " " + snippet).lower()
                is_actual_factcheck = any(k in lower_text for k in [
                    "cek fakta", "hoaks", "hoax", "disinformasi", "klarifikasi",
                    "[salah]", "[penipuan]", "turnbackhoax", "cekfakta"
                ])
                if not is_actual_factcheck:
                    continue
                    
                verdict = "Pemeriksaan Fakta"
                verdict_type = "info"
                if any(w in lower_text for w in ["hoaks", "hoax", "salah", "penipuan", "disinformasi"]):
                    verdict = "HOAKS / DISINFORMASI"
                    verdict_type = "danger"
                elif "klarifikasi" in lower_text:
                    verdict = "KLARIFIKASI RESMI"
                    verdict_type = "info"
                elif "benar" in lower_text:
                    verdict = "FAKTA BENAR"
                    verdict_type = "success"
                    
                items.append({
                    "id": f"factext_{len(items)+1}",
                    "title": title,
                    "url": link,
                    "snippet": snippet[:280] + ("..." if len(snippet) > 280 else ""),
                    "source": f"{source_name} (Cek Fakta)",
                    "platform": "Cek Fakta",
                    "platform_icon": "shield-alert",
                    "published_at": pub_date or "Liputan Khusus",
                    "category": "Cek Fakta / Verifikasi",
                    "verdict": verdict,
                    "verdict_type": verdict_type
                })
                
                if len(items) >= limit:
                    break
    except Exception as e:
        print(f"[Error Extra Fact Check Scraper]: {e}")
        
    return items
