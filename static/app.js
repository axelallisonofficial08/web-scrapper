// NewsPulse & FactVerify Frontend Logic

let allItems = [];
let selectedPlatform = 'all';
let selectedPublisher = 'all';
let searchKeywordFilter = '';
let currentSort = 'credibility';
let lastQuery = '';

document.addEventListener('DOMContentLoaded', () => {
    lucide.createIcons();
    initEventListeners();
});

function initEventListeners() {
    const searchInput = document.getElementById('search-input');
    const searchBtn = document.getElementById('btn-search');
    const filterInput = document.getElementById('filter-keyword');
    const sortSelect = document.getElementById('sort-select');
    const publisherSelect = document.getElementById('publisher-select');
    const resetFilterBtn = document.getElementById('btn-reset-filters');
    const exportCsvBtn = document.getElementById('btn-export-csv');
    const exportJsonBtn = document.getElementById('btn-export-json');

    searchBtn.addEventListener('click', performSearch);
    searchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') performSearch();
    });

    // Preset buttons
    document.querySelectorAll('.preset-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            searchInput.value = btn.innerText;
            performSearch();
        });
    });

    // Search inside results
    filterInput.addEventListener('input', (e) => {
        searchKeywordFilter = e.target.value.toLowerCase().trim();
        renderCards();
    });

    // Specific Publisher select
    publisherSelect.addEventListener('change', (e) => {
        selectedPublisher = e.target.value;
        renderCards();
    });

    // Sort select
    sortSelect.addEventListener('change', (e) => {
        currentSort = e.target.value;
        renderCards();
    });

    // Reset filters
    if (resetFilterBtn) {
        resetFilterBtn.addEventListener('click', resetAllFilters);
    }

    // Export buttons
    exportCsvBtn.addEventListener('click', () => {
        window.location.href = '/api/export?format=csv';
    });
    exportJsonBtn.addEventListener('click', () => {
        window.location.href = '/api/export?format=json';
    });
}

async function performSearch() {
    const input = document.getElementById('search-input');
    const query = input.value.trim();
    if (!query) return;

    lastQuery = query;
    const searchBtn = document.getElementById('btn-search');
    const loadingState = document.getElementById('loading-state');
    const resultsContainer = document.getElementById('results-container');
    const verificationBanner = document.getElementById('verification-banner');
    const initialState = document.getElementById('initial-state');
    const exportCsvBtn = document.getElementById('btn-export-csv');
    const exportJsonBtn = document.getElementById('btn-export-json');

    // UI state
    searchBtn.disabled = true;
    initialState.classList.add('hidden');
    resultsContainer.classList.add('hidden');
    verificationBanner.classList.add('hidden');
    loadingState.classList.remove('hidden');

    // Reset previous filters
    selectedPlatform = 'all';
    selectedPublisher = 'all';
    searchKeywordFilter = '';
    const filterInput = document.getElementById('filter-keyword');
    if (filterInput) filterInput.value = '';

    const limitSelect = document.getElementById('limit-per-source');
    const limitPerSource = limitSelect ? parseInt(limitSelect.value, 10) : 30;

    const payload = {
        query: query,
        lang: "id",
        include_google: document.getElementById('src-google').checked,
        include_bing: document.getElementById('src-bing').checked,
        include_reddit: document.getElementById('src-reddit').checked,
        include_twitter: document.getElementById('src-twitter').checked,
        include_factcheck: document.getElementById('src-factcheck').checked,
        limit_per_source: limitPerSource
    };

    try {
        const resp = await fetch('/api/search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!resp.ok) {
            const err = await resp.json();
            throw new Error(err.detail || 'Gagal mengambil data berita.');
        }

        const data = await resp.json();
        allItems = data.items || [];

        // Render verification banner
        renderVerificationBanner(data.verification_report, data.elapsed_seconds, data.total_results);

        // Render dynamic Platform filter pills ("Didapat Dari Mana")
        renderPlatformFilterPills(data.platform_counts);

        // Populate unique publisher dropdown
        populatePublisherDropdown();

        // Render Cards
        renderCards();

        // Show results
        loadingState.classList.add('hidden');
        verificationBanner.classList.remove('hidden');
        resultsContainer.classList.remove('hidden');
        exportCsvBtn.classList.remove('hidden');
        exportJsonBtn.classList.remove('hidden');

    } catch (error) {
        loadingState.classList.add('hidden');
        alert('Terjadi kesalahan saat scraping: ' + error.message);
        initialState.classList.remove('hidden');
    } finally {
        searchBtn.disabled = false;
        lucide.createIcons();
    }
}

function renderVerificationBanner(report, elapsedSeconds, totalResults) {
    const card = document.getElementById('verdict-card');
    const badge = document.getElementById('verdict-badge');
    const title = document.getElementById('verdict-title');
    const summary = document.getElementById('verdict-summary');
    const recText = document.getElementById('verdict-recommendation-text');
    const recBox = document.getElementById('verdict-recommendation');
    const iconContainer = document.getElementById('verdict-icon-container');

    document.getElementById('stat-elapsed').innerText = `Selesai dalam ${elapsedSeconds} detik`;
    document.getElementById('stat-total').innerText = totalResults;
    document.getElementById('stat-reputable').innerText = report.reputable_sources_count;
    document.getElementById('stat-fact').innerText = report.fact_checks_count;
    document.getElementById('stat-social').innerText = report.social_count;

    title.innerText = report.verdict;
    summary.innerText = report.summary;
    recText.innerText = report.recommendation;

    // Reset styles
    card.className = 'rounded-2xl border p-6 transition-all duration-300 relative overflow-hidden ';
    badge.className = 'text-xs font-bold px-3 py-1 rounded-full uppercase tracking-wider ';
    recBox.className = 'text-xs font-medium px-3.5 py-2.5 rounded-xl border flex items-start space-x-2 ';

    if (report.verdict_type === 'danger') {
        // Red Hoax alert
        card.className += 'bg-rose-950/30 border-rose-800/80 text-rose-200';
        badge.className += 'bg-rose-500/20 text-rose-300 border border-rose-500/40';
        badge.innerText = '⚠️ Peringatan Hoaks / Disinformasi';
        recBox.className += 'bg-rose-900/40 border-rose-700/60 text-rose-200';
        iconContainer.className = 'bg-rose-500/20 text-rose-400 p-2 rounded-lg';
        iconContainer.innerHTML = '<i data-lucide="alert-triangle" class="w-5 h-5"></i>';
    } else if (report.verdict_type === 'success') {
        // Green Confirmed Mainstream Media
        card.className += 'bg-emerald-950/30 border-emerald-800/80 text-emerald-200';
        badge.className += 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40';
        badge.innerText = '✓ Terkonfirmasi Media Kredibel';
        recBox.className += 'bg-emerald-900/40 border-emerald-700/60 text-emerald-200';
        iconContainer.className = 'bg-emerald-500/20 text-emerald-400 p-2 rounded-lg';
        iconContainer.innerHTML = '<i data-lucide="shield-check" class="w-5 h-5"></i>';
    } else if (report.verdict_type === 'warning') {
        // Amber Social chatter / unverified
        card.className += 'bg-amber-950/30 border-amber-800/80 text-amber-200';
        badge.className += 'bg-amber-500/20 text-amber-300 border border-amber-500/40';
        badge.innerText = '⚡ Klaim Media Sosial / Belum Valid';
        recBox.className += 'bg-amber-900/40 border-amber-700/60 text-amber-200';
        iconContainer.className = 'bg-amber-500/20 text-amber-400 p-2 rounded-lg';
        iconContainer.innerHTML = '<i data-lucide="message-circle" class="w-5 h-5"></i>';
    } else {
        // Blue / Neutral info
        card.className += 'bg-sky-950/30 border-sky-800/80 text-sky-200';
        badge.className += 'bg-sky-500/20 text-sky-300 border border-sky-500/40';
        badge.innerText = 'ℹ️ Liputan Berita Terbatas';
        recBox.className += 'bg-sky-900/40 border-sky-700/60 text-sky-200';
        iconContainer.className = 'bg-sky-500/20 text-sky-400 p-2 rounded-lg';
        iconContainer.innerHTML = '<i data-lucide="info" class="w-5 h-5"></i>';
    }
}

function renderPlatformFilterPills(platformCounts) {
    const container = document.getElementById('platform-filter-container');
    if (!container) return;
    container.innerHTML = '';

    const totalCount = allItems.length;

    // Platform definitions with icons and colors
    const platformsInfo = {
        'all': { label: 'Semua Platform', icon: 'layers', color: 'sky' },
        'Google News': { label: 'Google News', icon: 'chrome', color: 'blue' },
        'Bing News': { label: 'Bing News', icon: 'compass', color: 'teal' },
        'X (Twitter)': { label: 'X (Twitter)', icon: 'twitter', color: 'indigo' },
        'Instagram': { label: 'Instagram', icon: 'instagram', color: 'pink' },
        'TikTok': { label: 'TikTok', icon: 'video', color: 'cyan' },
        'Reddit': { label: 'Reddit', icon: 'message-square', color: 'orange' },
        'Cek Fakta': { label: 'Cek Fakta', icon: 'shield-alert', color: 'rose' }
    };

    // Always include 'all'
    const pillsToRender = [{ key: 'all', count: totalCount }];

    // Add platforms that actually have items
    for (const [plat, count] of Object.entries(platformCounts || {})) {
        if (count > 0) {
            pillsToRender.push({ key: plat, count: count });
        }
    }

    pillsToRender.forEach(p => {
        const info = platformsInfo[p.key] || { label: p.key, icon: 'globe', color: 'slate' };
        const isActive = selectedPlatform === p.key;

        const btn = document.createElement('button');
        btn.className = `platform-pill text-xs font-semibold px-3 py-1.5 rounded-xl border flex items-center space-x-1.5 transition cursor-pointer ${
            isActive
                ? 'bg-sky-500 border-sky-400 text-white shadow-md shadow-sky-500/20 ring-1 ring-sky-300/30'
                : 'bg-slate-950/80 border-slate-800 text-slate-300 hover:border-slate-700 hover:text-white hover:bg-slate-900'
        }`;
        btn.setAttribute('data-platform', p.key);

        btn.innerHTML = `
            <i data-lucide="${info.icon}" class="w-3.5 h-3.5"></i>
            <span>${info.label}</span>
            <span class="text-[10px] px-1.5 py-0.2 rounded-full font-bold ${
                isActive ? 'bg-sky-700/60 text-sky-100' : 'bg-slate-800 text-slate-400'
            }">${p.count}</span>
        `;

        btn.addEventListener('click', () => {
            selectedPlatform = p.key;
            renderPlatformFilterPills(platformCounts);
            renderCards();
        });

        container.appendChild(btn);
    });

    lucide.createIcons();
}

function populatePublisherDropdown() {
    const select = document.getElementById('publisher-select');
    if (!select) return;

    // Count items per publisher/source
    const pubCounts = {};
    allItems.forEach(i => {
        const src = i.source || 'Tidak Diketahui';
        pubCounts[src] = (pubCounts[src] || 0) + 1;
    });

    // Sort publishers alphabetically
    const sortedPublishers = Object.keys(pubCounts).sort((a, b) => a.localeCompare(b));

    select.innerHTML = `<option value="all">Semua Media & Akun (${allItems.length})</option>`;
    sortedPublishers.forEach(pub => {
        const opt = document.createElement('option');
        opt.value = pub;
        opt.innerText = `${pub} (${pubCounts[pub]})`;
        if (selectedPublisher === pub) {
            opt.selected = true;
        }
        select.appendChild(opt);
    });
}

function renderCards() {
    const grid = document.getElementById('cards-grid');
    const emptyState = document.getElementById('empty-filter-state');
    const activeBanner = document.getElementById('active-filter-banner');
    const activeText = document.getElementById('active-filter-text');

    grid.innerHTML = '';

    // 1. Filter by Platform (Didapat Dari Mana)
    let filtered = allItems;
    if (selectedPlatform !== 'all') {
        filtered = filtered.filter(i => {
            if (selectedPlatform === 'Cek Fakta') {
                return i.platform === 'Cek Fakta' || i.category === 'Cek Fakta / Verifikasi';
            }
            return i.platform === selectedPlatform;
        });
    }

    // 2. Filter by Specific Publisher
    if (selectedPublisher !== 'all') {
        filtered = filtered.filter(i => i.source === selectedPublisher);
    }

    // 3. Filter by Keyword
    if (searchKeywordFilter) {
        filtered = filtered.filter(i => 
            (i.title && i.title.toLowerCase().includes(searchKeywordFilter)) ||
            (i.snippet && i.snippet.toLowerCase().includes(searchKeywordFilter)) ||
            (i.source && i.source.toLowerCase().includes(searchKeywordFilter)) ||
            (i.platform && i.platform.toLowerCase().includes(searchKeywordFilter))
        );
    }

    // Active filter banner status
    const hasFilter = (selectedPlatform !== 'all' || selectedPublisher !== 'all' || searchKeywordFilter !== '');
    if (activeBanner) {
        if (hasFilter) {
            const filterLabels = [];
            if (selectedPlatform !== 'all') filterLabels.push(`Platform: ${selectedPlatform}`);
            if (selectedPublisher !== 'all') filterLabels.push(`Sumber: ${selectedPublisher}`);
            if (searchKeywordFilter) filterLabels.push(`Kata Kunci: "${searchKeywordFilter}"`);
            
            activeText.innerText = `${filterLabels.join(' • ')} (${filtered.length} ditemukan)`;
            activeBanner.classList.remove('hidden');
            activeBanner.classList.add('flex');
        } else {
            activeBanner.classList.add('hidden');
            activeBanner.classList.remove('flex');
        }
    }

    if (filtered.length === 0) {
        emptyState.classList.remove('hidden');
        return;
    } else {
        emptyState.classList.add('hidden');
    }

    // 4. Sort
    let sorted = [...filtered];
    if (currentSort === 'credibility') {
        sorted.sort((a, b) => (b.credibility_score || 0) - (a.credibility_score || 0));
    } else if (currentSort === 'latest') {
        // preserve original order / timestamps
    } else if (currentSort === 'platform') {
        sorted.sort((a, b) => a.platform.localeCompare(b.platform));
    }

    // 5. Render DOM cards
    sorted.forEach(item => {
        const card = createCardElement(item);
        grid.appendChild(card);
    });

    lucide.createIcons();
}

function createCardElement(item) {
    const el = document.createElement('div');
    el.className = 'news-card bg-slate-900 border border-slate-800 rounded-2xl p-5 flex flex-col justify-between space-y-4 hover:border-slate-700 transition relative overflow-hidden';

    // Platform Badge & Color
    let platformBg = 'bg-slate-800 text-slate-300 border-slate-700';
    let iconName = 'globe';

    if (item.platform === 'Google News') {
        platformBg = 'bg-blue-500/10 text-blue-400 border-blue-500/30';
        iconName = 'chrome';
    } else if (item.platform === 'Bing News') {
        platformBg = 'bg-teal-500/10 text-teal-400 border-teal-500/30';
        iconName = 'compass';
    } else if (item.platform === 'Reddit') {
        platformBg = 'bg-orange-500/10 text-orange-400 border-orange-500/30';
        iconName = 'message-square';
    } else if (item.platform.includes('X') || item.platform.includes('Twitter')) {
        platformBg = 'bg-indigo-500/10 text-indigo-300 border-indigo-500/30';
        iconName = 'twitter';
    } else if (item.platform === 'Instagram') {
        platformBg = 'bg-pink-500/10 text-pink-400 border-pink-500/30';
        iconName = 'instagram';
    } else if (item.platform === 'TikTok') {
        platformBg = 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30';
        iconName = 'video';
    } else if (item.category === 'Cek Fakta / Verifikasi' || item.platform === 'Cek Fakta') {
        platformBg = 'bg-rose-500/10 text-rose-400 border-rose-500/30';
        iconName = 'shield-alert';
    }

    // Credibility badge
    let credColor = 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';
    if (item.credibility_score < 50) {
        credColor = 'bg-rose-500/10 text-rose-400 border-rose-500/20';
    } else if (item.credibility_score < 75) {
        credColor = 'bg-amber-500/10 text-amber-400 border-amber-500/20';
    }

    // Clickbait warning pill
    let clickbaitHtml = '';
    if (item.is_sensational) {
        clickbaitHtml = `<span class="inline-flex items-center text-[10px] font-bold text-amber-400 bg-amber-500/10 border border-amber-500/30 px-2 py-0.5 rounded">⚠️ Sensasional</span>`;
    }

    // Fact check verdict pill
    let factVerdictHtml = '';
    if (item.verdict) {
        const isDanger = item.verdict_type === 'danger';
        factVerdictHtml = `
            <div class="p-2 rounded-lg ${isDanger ? 'bg-rose-500/15 border border-rose-500/30 text-rose-300' : 'bg-emerald-500/15 border border-emerald-500/30 text-emerald-300'} text-xs font-semibold flex items-center space-x-1.5">
                <i data-lucide="${isDanger ? 'alert-triangle' : 'check-circle-2'}" class="w-4 h-4 shrink-0"></i>
                <span>Verifikasi: ${escapeHtml(item.verdict)}</span>
            </div>
        `;
    }

    el.innerHTML = `
        <div class="space-y-3">
            <!-- Header Badges with Interactive Filter On Click -->
            <div class="flex items-center justify-between text-xs gap-2">
                <button 
                    onclick="filterByPlatform('${escapeHtml(item.platform)}')"
                    title="Klik untuk menyaring hanya dari platform ini"
                    class="inline-flex items-center space-x-1 px-2.5 py-1 rounded-lg border font-medium ${platformBg} hover:opacity-80 transition cursor-pointer"
                >
                    <i data-lucide="${iconName}" class="w-3.5 h-3.5 mr-1"></i>
                    <span>${escapeHtml(item.platform)}</span>
                </button>

                <div class="flex items-center space-x-1.5">
                    ${clickbaitHtml}
                    <span class="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold border ${credColor}">
                        ${item.credibility_score}% Validitas
                    </span>
                </div>
            </div>

            ${factVerdictHtml}

            <!-- Title -->
            <h3 class="font-bold text-sm sm:text-base text-white hover:text-sky-400 transition leading-snug line-clamp-2">
                <a href="${escapeHtml(item.url)}" target="_blank" rel="noopener noreferrer">
                    ${escapeHtml(item.title)}
                </a>
            </h3>

            <!-- Snippet -->
            <p class="text-xs text-slate-400 leading-relaxed line-clamp-3">
                ${escapeHtml(item.snippet)}
            </p>
        </div>

        <!-- Footer / Metadata & Action Buttons -->
        <div class="pt-3 border-t border-slate-800/80 space-y-3">
            <div class="flex items-center justify-between text-[11px] text-slate-400">
                <button 
                    onclick="filterByPublisher('${escapeHtml(item.source)}')"
                    title="Klik untuk menyaring hanya dari penerbit ini"
                    class="font-medium text-slate-300 hover:text-sky-400 hover:underline transition truncate max-w-[170px] text-left cursor-pointer"
                >
                    ${escapeHtml(item.source)}
                </button>
                <span class="text-slate-500 shrink-0">
                    ${formatDate(item.published_at)}
                </span>
            </div>

            <!-- Redirect & Action Buttons -->
            <div class="grid grid-cols-5 gap-2">
                <a 
                    href="${escapeHtml(item.url)}" 
                    target="_blank" 
                    rel="noopener noreferrer"
                    class="col-span-4 bg-sky-500/10 hover:bg-sky-500 hover:text-white text-sky-400 border border-sky-500/30 font-medium py-2 px-3 rounded-xl text-xs flex items-center justify-center space-x-1.5 transition group cursor-pointer"
                >
                    <span>Buka Sumber Asli</span>
                    <i data-lucide="external-link" class="w-3.5 h-3.5 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition"></i>
                </a>

                <button 
                    onclick="copyToClipboard('${escapeHtml(item.url)}')"
                    title="Salin Tautan"
                    class="col-span-1 bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700 rounded-xl flex items-center justify-center transition cursor-pointer"
                >
                    <i data-lucide="copy" class="w-3.5 h-3.5"></i>
                </button>
            </div>
        </div>
    `;

    return el;
}

function filterByPlatform(platformName) {
    selectedPlatform = platformName;
    const container = document.getElementById('platform-filter-container');
    if (container) {
        // Re-render pills with active state
        document.querySelectorAll('.platform-pill').forEach(btn => {
            const p = btn.getAttribute('data-platform');
            if (p === platformName) {
                btn.className = btn.className.replace(/bg-slate-950\/80.*$/, 'bg-sky-500 border-sky-400 text-white shadow-md shadow-sky-500/20 ring-1 ring-sky-300/30');
            } else {
                btn.className = btn.className.replace(/bg-sky-500.*$/, 'bg-slate-950/80 border-slate-800 text-slate-300 hover:border-slate-700 hover:text-white hover:bg-slate-900');
            }
        });
    }
    renderCards();
}

function filterByPublisher(publisherName) {
    selectedPublisher = publisherName;
    const select = document.getElementById('publisher-select');
    if (select) {
        select.value = publisherName;
    }
    renderCards();
}

function resetAllFilters() {
    selectedPlatform = 'all';
    selectedPublisher = 'all';
    searchKeywordFilter = '';

    const filterInput = document.getElementById('filter-keyword');
    const publisherSelect = document.getElementById('publisher-select');
    if (filterInput) filterInput.value = '';
    if (publisherSelect) publisherSelect.value = 'all';

    // Update pills
    document.querySelectorAll('.platform-pill').forEach(btn => {
        const p = btn.getAttribute('data-platform');
        if (p === 'all') {
            btn.className = btn.className.replace(/bg-slate-950\/80.*$/, 'bg-sky-500 border-sky-400 text-white shadow-md shadow-sky-500/20 ring-1 ring-sky-300/30');
        } else {
            btn.className = btn.className.replace(/bg-sky-500.*$/, 'bg-slate-950/80 border-slate-800 text-slate-300 hover:border-slate-700 hover:text-white hover:bg-slate-900');
        }
    });

    renderCards();
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showToast("Tautan berita berhasil disalin ke clipboard!");
    }).catch(() => {
        showToast("Gagal menyalin tautan.");
    });
}

function showToast(message) {
    const toast = document.getElementById('toast');
    const toastText = document.getElementById('toast-text');
    toastText.innerText = message;

    toast.classList.remove('translate-y-20', 'opacity-0');
    toast.classList.add('translate-y-0', 'opacity-100');

    setTimeout(() => {
        toast.classList.remove('translate-y-0', 'opacity-100');
        toast.classList.add('translate-y-20', 'opacity-0');
    }, 2800);
}

function formatDate(dateStr) {
    if (!dateStr || dateStr === 'Terdeteksi Terkini' || dateStr === 'Liputan Khusus') {
        return dateStr || 'Baru Saja';
    }
    try {
        const d = new Date(dateStr);
        if (isNaN(d.getTime())) return dateStr;
        return d.toLocaleDateString('id-ID', {
            day: 'numeric',
            month: 'short',
            year: 'numeric'
        });
    } catch {
        return dateStr;
    }
}

function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}
