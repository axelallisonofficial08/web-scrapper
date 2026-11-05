import re
from typing import List, Dict, Any

REPUTABLE_OUTLETS = [
    # Indonesian Mainstream
    "kompas", "detik", "tempo", "cnn", "antara", "reuters", "bbc", "cnbc",
    "bisnis.com", "media indonesia", "kumparan", "tirto", "liputan6", "merdeka",
    "jawa pos", "tribun", "suara.com", "viva.co.id", "inews", "the jakarta post",
    "republika", "sindonews", "rri.co.id", "kabar24", "kotak game", "duniaku",
    # Global Tech, Gaming & Mainstream
    "ign", "kotaku", "gamespot", "the verge", "techcrunch", "bloomberg",
    "forbes", "polygon", "engadget", "eurogamer", "nintendo life", "pc gamer",
    "associated press", "ap news", "the guardian", "new york times", "washington post",
    "al jazeera", "afp"
]

SENSATIONAL_KEYWORDS = [
    "geger", "bikin geger", "heboh", "mengejutkan", "tak disangka", "bongkar rahasia",
    "jangan kaget", "viral!", "viral parah", "ternyata oh ternyata", "terkuak", "terbongkar",
    "bikin merinding", "wajib share", "sebelum dihapus", "astaga"
]

def analyze_item_credibility(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluate credibility and verification attributes of an individual item.
    """
    platform = item.get("platform", "")
    source = item.get("source", "").lower()
    title = item.get("title", "")
    upper_title = title.upper()
    
    tier = "Community / Social"
    badge_color = "slate"
    credibility_score = 50
    notes = []
    
    # Check if Fact-Check
    if "Cek Fakta" in platform or item.get("category") == "Cek Fakta / Verifikasi":
        tier = "Lembaga Cek Fakta"
        badge_color = "emerald"
        credibility_score = 95
        verdict = item.get("verdict", "Pemeriksaan Fakta")
        notes.append(f"Hasil Verifikasi: {verdict}")
    elif any(rep in source for rep in REPUTABLE_OUTLETS) or any(rep in item.get("url", "").lower() for rep in REPUTABLE_OUTLETS):
        tier = "Media Arus Utama (Terverifikasi)"
        badge_color = "blue"
        credibility_score = 88
        notes.append("Penerbit media pers resmi terdaftar & terindeks.")
    elif "Reddit" in platform or "X (" in platform or "Twitter" in platform or "TikTok" in platform or "Instagram" in platform:
        tier = "Opini / Media Sosial"
        badge_color = "amber"
        credibility_score = 45
        notes.append("Klaim pengguna internet / media sosial, memerlukan konfirmasi media.")
    else:
        tier = "Situs Web Terbuka"
        badge_color = "zinc"
        credibility_score = 65
        notes.append("Sumber publik umum.")

    # Check for sensationalism / clickbait
    sensational_found = [w for w in SENSATIONAL_KEYWORDS if w in title.lower()]
    is_sensational = len(sensational_found) > 0
    if is_sensational:
        credibility_score -= 15
        notes.append(f"Indikator bombastis/clickbait terdeteksi: '{', '.join(sensational_found)}'")
        
    if title.isupper() and len(title) > 20:
        credibility_score -= 10
        notes.append("Judul menggunakan huruf kapital penuh (sensasionalistis).")

    # Clamping
    credibility_score = max(10, min(99, credibility_score))

    item["credibility_score"] = credibility_score
    item["tier"] = tier
    item["badge_color"] = badge_color
    item["is_sensational"] = is_sensational
    item["verification_notes"] = notes
    return item

def generate_verification_report(items: List[Dict[str, Any]], query: str) -> Dict[str, Any]:
    """
    Synthesize all gathered news, social media, and fact check records into a unified verification status.
    """
    total = len(items)
    if total == 0:
        return {
            "verdict": "Belum Ditemukan Data",
            "verdict_type": "secondary",
            "score": 0,
            "reputable_sources_count": 0,
            "fact_checks_count": 0,
            "social_count": 0,
            "summary": f"Tidak ditemukan pemberitaan publik atau cuitan terkait '{query}'. Pastikan kata kunci spesifik.",
            "recommendation": "Coba gunakan nama orang, instansi, atau topik yang lebih spesifik."
        }
        
    fact_checks = [i for i in items if i.get("category") == "Cek Fakta / Verifikasi"]
    hoax_flags = [i for i in fact_checks if i.get("verdict_type") == "danger"]
    
    reputable_items = [i for i in items if "Media Arus Utama" in i.get("tier", "")]
    social_items = [i for i in items if "Media Sosial" in i.get("category", "")]
    
    unique_reputable_sources = list(set([i.get("source", "") for i in reputable_items]))
    reputable_count = len(unique_reputable_sources)
    fact_count = len(fact_checks)
    social_count = len(social_items)
    
    # Calculate overall confidence
    if len(hoax_flags) > 0:
        verdict = "PERINGATAN HOAKS / DISINFORMASI"
        verdict_type = "danger"
        score = 25
        summary = (
            f"Ditemukan {len(hoax_flags)} arsip bantahan/klarifikasi dari lembaga cek fakta independen "
            f"yang mengategorikan klaim seputar '{query}' sebagai hoaks, disinformasi, atau penipuan."
        )
        recommendation = "Buka tautan cek fakta di bawah untuk membaca klarifikasi dan bukti autentik sebelum mempercayai atau membagikan."
    elif reputable_count >= 3:
        verdict = "TERKONFIRMASI BANYAK MEDIA RESMI"
        verdict_type = "success"
        score = 90
        summary = (
            f"Informasi ini diberitakan secara luas oleh setidaknya {reputable_count} media berita arus utama terkemuka "
            f"({', '.join(unique_reputable_sources[:4])}{' dll' if reputable_count > 4 else ''}). "
            f"Konsistensi pemberitaan antar redaksi mengindikasikan peristiwa atau pernyataan ini faktual."
        )
        recommendation = "Klik salah satu tautan media resmi di bawah untuk membaca konfirmasi dan kutipan narasumber secara mendalam."
    elif reputable_count in (1, 2):
        verdict = "TERPANTANG DI BEBERAPA MEDIA"
        verdict_type = "info"
        score = 75
        summary = (
            f"Topik ini terpantau diberitakan oleh {reputable_count} media berita ({', '.join(unique_reputable_sources)}). "
            f"Belum menjadi konsensus masif, namun ada liputan jurnalistik."
        )
        recommendation = "Periksa detail tanggal rilis berita dan kredibilitas redaksi sebelum mengambil kesimpulan."
    elif social_count > 0:
        verdict = "KLAIM MEDIA SOSIAL (BELUM TERKONFIRMASI)"
        verdict_type = "warning"
        score = 45
        summary = (
            f"Isu ini banyak dibahas di media sosial (Reddit, X/Twitter, dll.) dengan {social_count} cuitan/unggahan ditemukan, "
            f"namun BELUM terkonfirmasi di media berita arus utama terpercaya."
        )
        recommendation = "Sikap waspada disarankan. Periksa apakah akun pengunggah memiliki bukti konkret atau hanya berupa rumor/opini."
    else:
        verdict = "INFORMASI TERBATAS"
        verdict_type = "secondary"
        score = 55
        summary = f"Terdeteksi {total} rekaman indeks web umum terkait '{query}'."
        recommendation = "Lakukan cross-check dengan mengunjungi situs sumber asli melalui tombol redirect."

    return {
        "verdict": verdict,
        "verdict_type": verdict_type,
        "score": score,
        "reputable_sources_count": reputable_count,
        "fact_checks_count": fact_count,
        "social_count": social_count,
        "summary": summary,
        "recommendation": recommendation,
        "unique_sources": unique_reputable_sources
    }
