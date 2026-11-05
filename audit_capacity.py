import asyncio
import urllib.parse
import xml.etree.ElementTree as ET
import httpx
from scrapers.fact_checker import is_relevant_to_query

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'application/rss+xml,application/xml,text/xml;q=0.9,*/*;q=0.8'
}

query = 'SEGA ARCADE'

async def audit():
    print(f"=== AUDIT KAPASITAS SCRAPING UNTUK QUERY: '{query}' ===\n")
    async with httpx.AsyncClient(timeout=15.0, headers=HEADERS, follow_redirects=True) as client:
        # 1. Google News ID
        url_g_id = f"https://news.google.com/rss/search?q={urllib.parse.quote(query)}&hl=id&gl=ID&ceid=ID:id"
        r_gid = await client.get(url_g_id)
        items_gid = ET.fromstring(r_gid.content).findall('.//item') if r_gid.status_code == 200 else []
        rel_gid = [i for i in items_gid if is_relevant_to_query(query, i.find('title').text or '', '')]
        print(f"1. Google News (ID / Indonesia):")
        print(f"   - Kapasitas Max Feed Google: {len(items_gid)} artikel")
        print(f"   - Relevan dengan '{query}': {len(rel_gid)} artikel")

        # 2. Google News Global / EN
        url_g_en = f"https://news.google.com/rss/search?q={urllib.parse.quote(query)}&hl=en-US&gl=US&ceid=US:en"
        r_gen = await client.get(url_g_en)
        items_gen = ET.fromstring(r_gen.content).findall('.//item') if r_gen.status_code == 200 else []
        rel_gen = [i for i in items_gen if is_relevant_to_query(query, i.find('title').text or '', '')]
        print(f"2. Google News (Global / International EN):")
        print(f"   - Kapasitas Max Feed Google: {len(items_gen)} artikel")
        print(f"   - Relevan dengan '{query}': {len(rel_gen)} artikel")

        # 3. Bing News
        url_b = f"https://www.bing.com/news/search?q={urllib.parse.quote(query)}&format=rss"
        r_b = await client.get(url_b)
        items_b = ET.fromstring(r_b.content).findall('.//item') if r_b.status_code == 200 else []
        rel_b = [i for i in items_b if is_relevant_to_query(query, i.find('title').text or '', '')]
        print(f"3. Bing News:")
        print(f"   - Kapasitas Max Feed Bing: {len(items_b)} artikel")
        print(f"   - Relevan dengan '{query}': {len(rel_b)} artikel")

        # 4. X (Twitter)
        q_x = f"site:x.com OR site:twitter.com {query}"
        url_x = f"https://news.google.com/rss/search?q={urllib.parse.quote(q_x)}&hl=en-US&gl=US&ceid=US:en"
        r_x = await client.get(url_x)
        items_x = ET.fromstring(r_x.content).findall('.//item') if r_x.status_code == 200 else []
        rel_x = [i for i in items_x if is_relevant_to_query(query, i.find('title').text or '', '')]
        print(f"4. X (Twitter):")
        print(f"   - Kapasitas Max Feed: {len(items_x)} cuitan / post")
        print(f"   - Relevan dengan '{query}': {len(rel_x)} cuitan / post")

        # 5. Reddit
        q_red = f"site:reddit.com {query}"
        url_red = f"https://news.google.com/rss/search?q={urllib.parse.quote(q_red)}&hl=en-US&gl=US&ceid=US:en"
        r_red = await client.get(url_red)
        items_red = ET.fromstring(r_red.content).findall('.//item') if r_red.status_code == 200 else []
        rel_red = [i for i in items_red if is_relevant_to_query(query, i.find('title').text or '', '')]
        print(f"5. Reddit:")
        print(f"   - Kapasitas Max Feed: {len(items_red)} thread / diskusi")
        print(f"   - Relevan dengan '{query}': {len(rel_red)} thread / diskusi")

        # 6. Instagram & TikTok
        q_soc = f"site:instagram.com OR site:tiktok.com {query}"
        url_soc = f"https://news.google.com/rss/search?q={urllib.parse.quote(q_soc)}&hl=en-US&gl=US&ceid=US:en"
        r_soc = await client.get(url_soc)
        items_soc = ET.fromstring(r_soc.content).findall('.//item') if r_soc.status_code == 200 else []
        rel_soc = [i for i in items_soc if is_relevant_to_query(query, i.find('title').text or '', '')]
        print(f"6. Instagram & TikTok:")
        print(f"   - Kapasitas Max Feed: {len(items_soc)} unggahan")
        print(f"   - Relevan dengan '{query}': {len(rel_soc)} unggahan")

        # 7. Cek Fakta (TurnBackHoax & Portal Cek Fakta)
        q_cf = f"{query} (cek fakta OR hoaks OR disinformasi OR site:turnbackhoax.id)"
        url_cf = f"https://news.google.com/rss/search?q={urllib.parse.quote(q_cf)}&hl=id&gl=ID&ceid=ID:id"
        r_cf = await client.get(url_cf)
        items_cf = ET.fromstring(r_cf.content).findall('.//item') if r_cf.status_code == 200 else []
        rel_cf = [i for i in items_cf if is_relevant_to_query(query, i.find('title').text or '', '')]
        # Filter for actual debunk
        debunks = [i for i in rel_cf if any(k in (i.find('title').text or '').lower() for k in ['cek fakta', 'hoaks', 'hoax', 'disinformasi', 'salah', 'penipuan'])]
        print(f"7. Cek Fakta (TurnBackHoax & CekFakta):")
        print(f"   - Arsip Hoaks ditemukan untuk '{query}': {len(debunks)} record")

if __name__ == '__main__':
    asyncio.run(audit())
