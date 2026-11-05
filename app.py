import asyncio
import csv
import io
import time
from typing import List, Optional
from fastapi import FastAPI, Query, Request, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from scrapers.google_news import scrape_google_news
from scrapers.bing_news import scrape_bing_news
from scrapers.reddit import scrape_reddit_posts
from scrapers.social_mentions import scrape_twitter_x_mentions, scrape_other_social_mentions
from scrapers.fact_checker import scrape_turnbackhoax, scrape_additional_factchecks
from scrapers.analyzer import analyze_item_credibility, generate_verification_report

app = FastAPI(
    title="NewsPulse & FactVerify Dashboard",
    description="Multi-platform news & social scraper with automated verification & redirect",
    version="1.0.0"
)

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Cache in-memory last search results for export
LAST_SEARCH_CACHE = {
    "query": "",
    "timestamp": 0,
    "items": [],
    "report": {}
}

class SearchRequest(BaseModel):
    query: str
    lang: str = "id"
    include_google: bool = True
    include_bing: bool = True
    include_reddit: bool = True
    include_twitter: bool = True
    include_factcheck: bool = True
    limit_per_source: int = 15

@app.get("/", response_class=FileResponse)
async def home():
    return FileResponse("templates/index.html")

@app.post("/api/search")
async def search_news(payload: SearchRequest):
    query = payload.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query pencarian tidak boleh kosong.")
        
    start_time = time.time()
    tasks = []
    
    # 1. Google News
    if payload.include_google:
        tasks.append(scrape_google_news(query, lang=payload.lang, limit=payload.limit_per_source))
        
    # 2. Bing News
    if payload.include_bing:
        tasks.append(scrape_bing_news(query, limit=payload.limit_per_source))
        
    # 3. Reddit Discussions
    if payload.include_reddit:
        tasks.append(scrape_reddit_posts(query, limit=payload.limit_per_source))
        
    # 4. X / Twitter and Social Mentions
    if payload.include_twitter:
        tasks.append(scrape_twitter_x_mentions(query, limit=payload.limit_per_source))
        tasks.append(scrape_other_social_mentions(query, limit=min(25, payload.limit_per_source)))
        
    # 5. TurnBackHoax & Cek Fakta
    if payload.include_factcheck:
        tasks.append(scrape_turnbackhoax(query, limit=payload.limit_per_source))
        tasks.append(scrape_additional_factchecks(query, limit=min(15, payload.limit_per_source)))
        
    # Run all asynchronously
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    all_items = []
    seen_urls = set()
    seen_titles = set()
    
    for res in results:
        if isinstance(res, list):
            for item in res:
                url = item.get("url", "").strip()
                title = item.get("title", "").strip().lower()
                
                # Simple deduplication
                if url and url in seen_urls:
                    continue
                if title and title in seen_titles:
                    continue
                    
                seen_urls.add(url)
                seen_titles.add(title)
                all_items.append(item)
        elif isinstance(res, Exception):
            print(f"[Scraper Task Exception]: {res}")
            
    # Credibility & Fact Analysis
    analyzed_items = [analyze_item_credibility(i) for i in all_items]
    
    # Sort items: Fact-checks first, then high credibility, then others
    analyzed_items.sort(
        key=lambda x: (
            1 if x.get("category") == "Cek Fakta / Verifikasi" else 2,
            -x.get("credibility_score", 50)
        )
    )
    
    # Generate verification report
    verification_report = generate_verification_report(analyzed_items, query)
    elapsed_seconds = round(time.time() - start_time, 2)
    
    # Update cache for export
    LAST_SEARCH_CACHE["query"] = query
    LAST_SEARCH_CACHE["timestamp"] = time.time()
    LAST_SEARCH_CACHE["items"] = analyzed_items
    LAST_SEARCH_CACHE["report"] = verification_report
    
    # Calculate statistics by platform
    platform_counts = {}
    for it in analyzed_items:
        plat = it.get("platform", "Lainnya")
        platform_counts[plat] = platform_counts.get(plat, 0) + 1
        
    return {
        "status": "success",
        "query": query,
        "elapsed_seconds": elapsed_seconds,
        "total_results": len(analyzed_items),
        "platform_counts": platform_counts,
        "verification_report": verification_report,
        "items": analyzed_items
    }

@app.get("/api/export")
async def export_results(format: str = Query("csv", pattern="^(csv|json)$")):
    """Export current cached search results to CSV or JSON."""
    items = LAST_SEARCH_CACHE.get("items", [])
    query = LAST_SEARCH_CACHE.get("query", "news_search")
    
    if not items:
        raise HTTPException(status_code=400, detail="Belum ada data pencarian untuk di-export.")
        
    if format == "json":
        return JSONResponse(
            content={
                "query": query,
                "exported_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "total": len(items),
                "report": LAST_SEARCH_CACHE.get("report", {}),
                "results": items
            },
            headers={"Content-Disposition": f'attachment; filename="news_scrape_{query}.json"'}
        )
        
    # Export CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "ID", "Platform", "Kategori", "Sumber / Penulis", "Judul", "URL / Link Asli",
        "Tanggal Terbit", "Skor Kredibilitas", "Kategori Sumber", "Catatan Verifikasi"
    ])
    
    for item in items:
        writer.writerow([
            item.get("id", ""),
            item.get("platform", ""),
            item.get("category", ""),
            item.get("source", ""),
            item.get("title", ""),
            item.get("url", ""),
            item.get("published_at", ""),
            item.get("credibility_score", ""),
            item.get("tier", ""),
            "; ".join(item.get("verification_notes", []))
        ])
        
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="news_scrape_{query}.csv"'}
    )

if __name__ == "__main__":
    import os
    import uvicorn
    port = int(os.environ.get("PORT", 7000))
    uvicorn.run("app:app", host="127.0.0.1", port=port, reload=True)
