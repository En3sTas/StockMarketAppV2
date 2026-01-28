// Global Değişkenler
const API_BASE_URL = "http://localhost:5158/api/hisseler";

// Portföy Verileri (Sabit)
// Portföy Verileri (LocalStorage'dan Başlat)
let MY_PORTFOLIO = JSON.parse(localStorage.getItem('myPortfolio')) || [
    { sembol: "TUPRS", adet: 22, maliyet: 183.20 },
    { sembol: "TOASO", adet: 20, maliyet: 245.90 },
    { sembol: "YKBNK", adet: 137, maliyet: 37.12 },
    { sembol: "ASELS", adet: 31, maliyet: 210.70 },
    { sembol: "BRSAN", adet: 13, maliyet: 528.50 }
];

// LocalStorage Kaydetme Fonksiyonu
function savePortfolio() {
    localStorage.setItem('myPortfolio', JSON.stringify(MY_PORTFOLIO));
    renderPortfolio();
}

// Yeni Hisse Ekleme
function addToPortfolio(symbol, count, cost) {
    if (!symbol || count <= 0 || cost < 0) {
        alert("Lütfen geçerli değerler giriniz!");
        return;
    }

    // Varsa güncelle, yoksa ekle
    const existing = MY_PORTFOLIO.find(p => p.sembol === symbol);
    if (existing) {
        // Ağırlıklı ortalama maliyet hesabı
        const totalCost = (existing.adet * existing.maliyet) + (count * cost);
        const totalCount = existing.adet + count;
        existing.maliyet = totalCost / totalCount;
        existing.adet = totalCount;
    } else {
        MY_PORTFOLIO.push({ sembol: symbol, adet: count, maliyet: cost });
    }

    savePortfolio();
    closeAddModal();
}

// Hiss Silme
function removeFromPortfolio(symbol) {
    if (confirm(`${symbol} hissesini portföyden silmek istediğinize emin misiniz?`)) {
        MY_PORTFOLIO = MY_PORTFOLIO.filter(p => p.sembol !== symbol);
        savePortfolio();
    }
}

// Modal İşlemleri
function openAddModal() { document.getElementById('addStockModal').classList.remove('hidden'); }
function closeAddModal() { document.getElementById('addStockModal').classList.add('hidden'); }

function submitAddStock() {
    const sym = document.getElementById('addSymbol').value.toUpperCase();
    const qty = parseFloat(document.getElementById('addQuantity').value);
    const cost = parseFloat(document.getElementById('addCost').value);
    addToPortfolio(sym, qty, cost);

    // Temizle
    document.getElementById('addSymbol').value = '';
    document.getElementById('addQuantity').value = '';
    document.getElementById('addCost').value = '';
}

let globalData = [];
let currentTab = 'trend';

// Tab Değiştirme Fonksiyonu
function switchTab(tabName) {
    currentTab = tabName;
    const marketView = document.getElementById('market-view');
    const portfolioView = document.getElementById('portfolio-view');

    // Tab Buttons
    const tabTrend = document.getElementById('tab-trend');
    const tabScout = document.getElementById('tab-scout');
    const tabPortfolio = document.getElementById('tab-portfolio');

    // Reset Classes
    const activeClass = "tab-active px-6 py-2 rounded-md text-sm font-bold transition flex items-center gap-2";
    const passiveClass = "tab-passive px-6 py-2 rounded-md text-sm font-bold transition flex items-center gap-2 opacity-70 hover:opacity-100";

    tabTrend.className = passiveClass + " hover:text-emerald-400";
    tabScout.className = passiveClass + " hover:text-orange-400";
    tabPortfolio.className = passiveClass;

    if (tabName === 'portfolio') {
        marketView.classList.add('hidden');
        portfolioView.classList.remove('hidden');
        tabPortfolio.className = activeClass;
        // Portföy sekmesi için tüm verileri çekelim
        verileriGetir();
    } else {
        marketView.classList.remove('hidden');
        portfolioView.classList.add('hidden');

        if (tabName === 'trend') {
            tabTrend.className = activeClass + " text-emerald-400";
        } else if (tabName === 'scout') {
            tabScout.className = activeClass + " text-orange-400";
        }
        verileriGetir(); // Reload data for the active tab
    }
}

// Veri Çekme Fonksiyonu
async function verileriGetir() {
    const statusDiv = document.getElementById('connectionStatus');
    const messageArea = document.getElementById('messageArea');
    const params = new URLSearchParams();

    // Filtre değerlerini URL parametrelerine ekle
    // Portföy modunda filtreleri KULLANMA (tüm verileri al)
    if (currentTab !== 'portfolio') {
        addParam(params, 'minFk', 'minFk'); addParam(params, 'maxFk', 'maxFk');
        addParam(params, 'minPdDd', 'minPdDd'); addParam(params, 'maxPdDd', 'maxPdDd');
        addParam(params, 'minRsi', 'minRsi'); addParam(params, 'maxRsi', 'maxRsi');
        addParam(params, 'minMacdHist', 'minMacdHist'); addParam(params, 'maxMacdHist', 'maxMacdHist');
        addParam(params, 'minAdx', 'minAdx'); addParam(params, 'maxAdx', 'maxAdx');
        addParam(params, 'minHacimOrani', 'minHacim'); addParam(params, 'maxHacimOrani', 'maxHacim');
        addParam(params, 'minDmp', 'minDmp'); addParam(params, 'minDmn', 'minDmn');
        addParam(params, 'signal', 'filterSignal');
    }

    try {
        // ... (loading logic)

        let url = API_BASE_URL;
        if (currentTab === 'trend') {
            url = "http://localhost:5158/api/market/trend";
        } else if (currentTab === 'scout') {
            url = "http://localhost:5158/api/market/scout";
        }
        // 'portfolio' için API_BASE_URL (Tüm Hisseler) kalır

        const response = await fetch(`${url}?${params.toString()}`);
        if (!response.ok) throw new Error("API Hatası");

        globalData = await response.json();

        statusDiv.innerHTML = '<span class="w-2 h-2 rounded-full bg-emerald-500"></span> Online';
        statusDiv.className = "flex items-center gap-2 text-xs font-mono text-emerald-400 bg-emerald-900/20 px-3 py-1.5 rounded-full border border-emerald-900";
        messageArea.classList.add('hidden');

        // Eğer Portföy sekmesiysek dev tabloyu render etmeye gerek yok
        if (currentTab !== 'portfolio') {
            let filteredData = frontendFiltrele(globalData);
            applySort(filteredData);
            renderMarketTable(filteredData);
        }

        // Portföyü her zaman güncelle (çünkü arka planda fetch yaptıkça fiyatlar değişiyor)
        renderPortfolio();

    } catch (error) {
        // ... (error handling)
    }
}

// SIRALAMA MANTIĞI
let currentSort = { column: 'score', direction: 'desc' };

function sortTable(column) {
    // Aynı kolona tıkladıysa yön değiştir
    if (currentSort.column === column) {
        currentSort.direction = currentSort.direction === 'asc' ? 'desc' : 'asc';
    } else {
        // Yeni kolon seçildiyse varsayılan yönler
        currentSort.column = column;
        // Metinler için A-Z (asc), Sayılar için Z-A (desc) varsayılan olsun
        currentSort.direction = (column === 'sembol' || column === 'signal') ? 'asc' : 'desc';
    }

    // Header ikonlarını güncelle (Opsiyonel görsel güncelleme için)
    updateSortIcons();

    // Veriyi yeniden filtrele, sırala ve çiz
    let filteredData = frontendFiltrele(globalData);
    applySort(filteredData);
    renderMarketTable(filteredData);
}

function applySort(data) {
    data.sort((a, b) => {
        let valA = a[currentSort.column];
        let valB = b[currentSort.column];

        // Null/Undefined kontrolü (En sona atalım)
        if (valA === null || valA === undefined) valA = -999999;
        if (valB === null || valB === undefined) valB = -999999;

        // String karşılaştırma için
        if (typeof valA === 'string') valA = valA.toLowerCase();
        if (typeof valB === 'string') valB = valB.toLowerCase();

        if (valA < valB) return currentSort.direction === 'asc' ? -1 : 1;
        if (valA > valB) return currentSort.direction === 'asc' ? 1 : -1;
        return 0;
    });
}

function updateSortIcons() {
    // Tüm headerlardaki ikonları resetle (Bu fonksiyon için HTML tarafında id veya class düzeni gerekir, şimdilik basit tutalım)
    // İleride headerlara ok işareti eklenebilir.
    console.log(`Sıralama: ${currentSort.column} (${currentSort.direction})`);
}

// Frontend Filtreleme
function frontendFiltrele(data) {
    const maxAdx = parseFloat(val('maxAdx')) || 9999;
    const minHacim = parseFloat(val('minHacim')) || 0;
    const maxHacim = parseFloat(val('maxHacim')) || 9999;
    const maxFk = parseFloat(val('maxFk')) || 9999;
    const maxPdDd = parseFloat(val('maxPdDd')) || 9999;
    const minScoreEl = document.getElementById('minScoreSlider');
    const minScore = minScoreEl ? (parseFloat(minScoreEl.value) || 0) : 0;

    return data.filter(h =>
        h.adx <= maxAdx &&
        h.hacimOrani >= minHacim && h.hacimOrani <= maxHacim &&
        h.fk <= maxFk &&
        h.pdDd <= maxPdDd &&
        (h.score || 0) >= minScore
    );
}



// Yardımcı Fonksiyon: Değişimi Hesapla ve Badge Döndür
function getDiffBadge(current, prev) {
    if (prev === undefined || prev === null || prev === 0) return '';

    const diff = current - prev;
    if (Math.abs(diff) < 0.01) return ''; // Çok küçük farkları gösterme

    const color = diff > 0 ? 'text-emerald-400' : 'text-red-400';
    const icon = diff > 0 ? '▲' : '▼';

    return `<div class="${color} text-[10px] font-mono mt-1">${icon} ${Math.abs(diff).toFixed(2)}</div>`;
}

// Piyasa Tablosunu Çiz
function renderMarketTable(data) {
    const tbody = document.getElementById('hisseTablosu');
    tbody.innerHTML = '';

    if (data.length === 0) {
        tbody.innerHTML = '<tr><td colspan="16" class="p-12 text-center text-gray-500">Aradığınız kriterlere uygun hisse bulunamadı.</td></tr>';
        return;
    }

    data.forEach(h => {
        try {
            const rsiClass = h.rsi < 30 ? 'text-emerald-400 font-bold animate-pulse' : (h.rsi > 70 ? 'text-red-400 font-bold' : 'text-gray-400');
            const macdClass = h.macdHist > 0 ? 'text-emerald-400' : 'text-red-400';
            const adxClass = h.adx > 25 ? 'text-white font-bold' : 'text-gray-600';

            let volText = 'text-gray-500';
            let volIcon = 'fa-battery-quarter text-gray-700';
            if (h.hacimOrani > 2.0) { volText = 'text-orange-400 font-bold'; volIcon = 'fa-fire-flame-curved animate-pulse text-orange-500'; }
            else if (h.hacimOrani > 1.2) { volText = 'text-emerald-300'; volIcon = 'fa-arrow-trend-up text-emerald-500'; }

            // Signal Badge Logic
            let signalBadge = '';
            switch (h.signal) {
                case 'STRONG_BUY': signalBadge = '<span class="bg-gradient-to-r from-emerald-600 to-green-500 text-white px-3 py-1 rounded-full text-[10px] font-bold shadow-lg shadow-emerald-900/40 animate-pulse"><i class="fa-solid fa-rocket mr-1"></i> GÜÇLÜ AL</span>'; break;
                case 'BUY': signalBadge = '<span class="bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 px-2 py-1 rounded text-[10px] font-bold">✅ AL</span>'; break;
                case 'WATCH': signalBadge = '<span class="bg-yellow-500/10 text-yellow-400 border border-yellow-500/30 px-2 py-1 rounded text-[10px] font-bold">👀 İZLE</span>'; break;
                default: signalBadge = '<span class="text-gray-600 text-[10px]">NO TRADE</span>';
            }

            // Score Color Logic
            let scoreColor = 'text-gray-500';
            if (h.score >= 75) scoreColor = 'text-emerald-400 font-bold';
            else if (h.score >= 50) scoreColor = 'text-yellow-400';
            else if (h.score >= 30) scoreColor = 'text-orange-400';
            else scoreColor = 'text-red-400';

            const tarih = new Date(h.sonGuncelleme).toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' });

            const row = `
            <tr class="hover:bg-gray-800/40 transition border-b border-gray-800/30 group">
                <td class="p-4 font-bold text-white sticky left-0 bg-[#0b0f19] group-hover:bg-gray-800/40 z-10 border-r border-gray-800/50">${h.sembol}</td>
                
                <td class="p-4 text-blue-300 font-mono text-base tracking-tight">
                    ${h.fiyat.toFixed(2)} ₺
                    ${getDiffBadge(h.fiyat, h.fiyatOnceki)}
                </td>
                
                <td class="p-4 font-mono ${h.fiyat > h.sma50 ? 'text-emerald-300/90' : 'text-gray-600'}">${h.sma50.toFixed(2)}</td>
                <td class="p-4 font-mono ${h.fiyat > h.sma200 ? 'text-yellow-300/90' : 'text-gray-600'}">${h.sma200.toFixed(2)}</td>
                
                <td class="p-4 font-mono ${rsiClass}">
                    ${h.rsi.toFixed(2)}
                    ${getDiffBadge(h.rsi, h.rsiOnceki)}
                </td>
                
                <td class="p-4 text-center bg-blue-900/5">
                    <div class="flex flex-col items-center">
                        <span class="${adxClass} text-sm flex flex-col items-center">
                            ${h.adx.toFixed(2)}
                            ${getDiffBadge(h.adx, h.adxOnceki)}
                        </span>
                        <div class="text-[10px] mt-1 flex gap-2 font-mono bg-gray-900/80 px-2 py-0.5 rounded border border-gray-700/50">
                            <span class="text-emerald-500" title="+DI">+${h.dmp.toFixed(1)}</span>
                            <span class="text-gray-600">|</span>
                            <span class="text-red-500" title="-DI">-${h.dmn.toFixed(1)}</span>
                        </div>
                    </div>
                </td>

                <td class="p-4 text-center">
                        <div class="flex items-center justify-center gap-2 bg-gray-900/30 py-1.5 px-3 rounded-lg border border-gray-800/50">
                        <i class="fa-solid ${volIcon}"></i>
                        <span class="${volText} font-mono">${h.hacimOrani.toFixed(2)}x</span>
                    </div>
                </td>

                <td class="p-4 font-mono ${macdClass}">${h.macdHist.toFixed(2)}</td>
                <td class="p-4 text-gray-500 text-[10px] font-mono">
                    <div class="flex flex-col gap-1">
                        <span class="bg-gray-800/50 px-1 rounded w-max">L: ${h.macdLine.toFixed(2)}</span>
                        <span class="bg-gray-800/50 px-1 rounded w-max">S: ${h.macdSignal.toFixed(2)}</span>
                    </div>
                </td>

                <td class="p-4 text-gray-400 font-mono">${h.fk.toFixed(2)}</td>
                <td class="p-4 text-gray-400 font-mono">${h.pdDd.toFixed(2)}</td>

                <!-- NEW: Trading Signal Cells -->
                <td class="p-4 text-center">${signalBadge}</td>
                <td class="p-4 text-center">
                    <div class="flex flex-col items-center">
                        <span class="${scoreColor} text-lg font-mono">${h.score || 0}</span>
                        <div class="w-16 h-1 bg-gray-700 rounded-full mt-1 overflow-hidden">
                            <div class="h-full ${h.score >= 75 ? 'bg-emerald-500' : (h.score >= 50 ? 'bg-yellow-500' : 'bg-red-500')}" style="width: ${h.score || 0}%"></div>
                        </div>
                    </div>
                </td>
                <td class="p-4 text-right font-mono text-red-300 text-xs">${(h.stopPrice || 0).toFixed(2)} ₺</td>
                <td class="p-4 text-right font-mono text-emerald-300 text-xs">${(h.targetPrice || 0).toFixed(2)} ₺</td>

                <td class="p-4 text-xs text-gray-600 font-mono">${tarih}</td>
            </tr>`;
            tbody.innerHTML += row;
        } catch (err) {
            console.error("Rendering Error for stock:", h, err);
        }
    });
}

// Portföy Tablosunu Çiz
function renderPortfolio() {
    const tbody = document.getElementById('portfolioTablosu');
    tbody.innerHTML = '';
    let totalVal = 0, totalCost = 0;

    MY_PORTFOLIO.forEach(item => {
        const liveData = globalData.find(d => d.sembol === item.sembol || d.sembol.includes(item.sembol));
        let currentPrice = liveData ? liveData.fiyat : 0;
        let totalValue = currentPrice * item.adet;
        let costValue = item.maliyet * item.adet;
        let pnl = totalValue - costValue;
        let pnlPercent = costValue > 0 ? (pnl / costValue) * 100 : 0;

        if (currentPrice > 0) {
            totalVal += totalValue;
            totalCost += costValue;
        }

        const pnlClass = pnl >= 0 ? 'text-emerald-400' : 'text-red-400';
        const bgClass = pnl >= 0 ? 'bg-emerald-500/10' : 'bg-red-500/10';

        let signalBadge = '<span class="text-gray-600">-</span>';
        if (liveData) {
            if (liveData.rsi < 30 && liveData.adx > 20) signalBadge = '<span class="bg-emerald-500 text-black px-2 py-1 rounded text-xs font-bold animate-pulse">AL FIRSATI</span>';
            else if (liveData.rsi > 70) signalBadge = '<span class="bg-red-500 text-white px-2 py-1 rounded text-xs font-bold">SAT (Şişti)</span>';
            else if (liveData.hacimOrani > 2.0) signalBadge = '<span class="bg-orange-500 text-white px-2 py-1 rounded text-xs font-bold">HACİM PATLAMASI</span>';
        }

        const row = `
            <tr class="hover:bg-gray-800/40 border-b border-gray-800/30 ${bgClass} group">
                <td class="p-4 font-bold text-white">${item.sembol}</td>
                <td class="p-4 text-right font-mono text-gray-300">${item.adet}</td>
                <td class="p-4 text-right font-mono text-gray-400">${item.maliyet.toFixed(2)} ₺</td>
                <td class="p-4 text-right font-mono text-blue-300 font-bold">${currentPrice > 0 ? currentPrice.toFixed(2) + ' ₺' : '...'}</td>
                <td class="p-4 text-right font-mono text-white font-bold">${totalValue.toFixed(2)} ₺</td>
                <td class="p-4 text-right font-mono ${pnlClass}">${pnl > 0 ? '+' : ''}${pnl.toFixed(2)} ₺</td>
                <td class="p-4 text-right font-mono ${pnlClass} font-bold">%${pnlPercent.toFixed(2)}</td>
                <td class="p-4 text-center">${signalBadge}</td>
                <td class="p-4 text-center">
                    <button onclick="removeFromPortfolio('${item.sembol}')" class="text-gray-600 hover:text-red-500 transition opacity-0 group-hover:opacity-100">
                        <i class="fa-solid fa-trash-can"></i>
                    </button>
                </td>
            </tr>`;
        tbody.innerHTML += row;
    });

    const totalPnL = totalVal - totalCost;
    const totalPnLPercent = totalCost > 0 ? (totalPnL / totalCost) * 100 : 0;

    // Güvenli erişim kontrolü
    const totalBalanceEl = document.getElementById('totalBalance');
    if (totalBalanceEl) totalBalanceEl.innerText = `₺${totalVal.toLocaleString('tr-TR', { minimumFractionDigits: 2 })}`;

    const stockCountEl = document.getElementById('stockCount');
    if (stockCountEl) stockCountEl.innerText = MY_PORTFOLIO.length;

    const pnlEl = document.getElementById('totalPnL');
    const pnlPerEl = document.getElementById('totalPnLPercent');
    const pnlIcon = document.getElementById('pnlIcon');

    if (pnlEl && pnlPerEl && pnlIcon) {
        pnlEl.innerText = `${totalPnL > 0 ? '+' : ''}₺${totalPnL.toLocaleString('tr-TR', { minimumFractionDigits: 2 })}`;
        pnlPerEl.innerText = `%${totalPnLPercent.toFixed(2)}`;

        if (totalPnL >= 0) {
            pnlEl.className = "text-3xl font-bold text-emerald-400 font-mono";
            pnlPerEl.className = "text-sm font-bold font-mono text-emerald-500 bg-emerald-500/10 px-2 py-1 rounded";
            pnlIcon.className = "bg-emerald-500/20 p-3 rounded-full text-emerald-400";
        } else {
            pnlEl.className = "text-3xl font-bold text-red-400 font-mono";
            pnlPerEl.className = "text-sm font-bold font-mono text-red-500 bg-red-500/10 px-2 py-1 rounded";
            pnlIcon.className = "bg-red-500/20 p-3 rounded-full text-red-400";
        }
    }
}

// Yardımcı Fonksiyonlar
function addParam(params, name, id) { const el = document.getElementById(id); if (el && el.value) params.append(name, el.value); }
function val(id) { return document.getElementById(id) ? document.getElementById(id).value : null; }
function temizle() { document.querySelectorAll('input').forEach(i => i.value = ''); verileriGetir(); }

// BAŞLANGIÇ & OTOMATİK YENİLEME MANTIĞI
// -------------------------------------

// 1. Sayfa ilk açıldığında veriyi çek
window.onload = verileriGetir;

// 2. Her 30 saniyede bir kontrol et ve güncelle
setInterval(() => {
    const toggle = document.getElementById('autoRefreshToggle');

    // DİKKAT: Sadece toggle elementi varsa ve CHECKED (seçili) ise çalışır.
    if (toggle && toggle.checked) {
        console.log("🔄 Canlı veri güncelleniyor...");
        verileriGetir();

        // Yenileme butonunu döndür (Görsel efekt)
        const refreshBtn = document.querySelector('.fa-rotate');
        if (refreshBtn) {
            refreshBtn.classList.add('fa-spin');
            setTimeout(() => refreshBtn.classList.remove('fa-spin'), 1000);
        }
    } else {
        console.log("⏸️ Canlı veri duraklatıldı.");
    }
}, 30000); // 30000 ms = 30 Saniye

// Slider Değer Göstergesi
document.addEventListener('DOMContentLoaded', () => {
    const slider = document.getElementById('minScoreSlider');
    const valueDisplay = document.getElementById('minScoreValue');
    if (slider && valueDisplay) {
        slider.addEventListener('input', (e) => {
            valueDisplay.innerText = e.target.value;
        });
    }
});