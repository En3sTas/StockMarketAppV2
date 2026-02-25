
// -- Global Variables --
const API_BASE_URL = "/api/hisseler";

// -- Portfolio Data (LocalStorage) --
let MY_PORTFOLIO = JSON.parse(localStorage.getItem('myPortfolio')) || [
    { sembol: "TUPRS", adet: 22, maliyet: 183.20, target: 220.0, initialStop: 170.0, trailingStop: 170.0, highestPrice: 183.20, strategy: "TREND" },
    { sembol: "TOASO", adet: 20, maliyet: 245.90, target: 300.0, initialStop: 230.0, trailingStop: 230.0, highestPrice: 245.90, strategy: "TREND" }
];

// -- LocalStorage Helpers --
function savePortfolio() {
    localStorage.setItem('myPortfolio', JSON.stringify(MY_PORTFOLIO));
    renderPortfolio();
}

// -- Add Stock to Portfolio --
function addToPortfolio(symbol, count, cost) {
    if (!symbol || count <= 0 || cost < 0) {
        alert("Lütfen geçerli değerler giriniz!");
        return;
    }

    const existing = MY_PORTFOLIO.find(p => p.sembol === symbol);
    const liveData = globalData.find(d => d.sembol === symbol);

    // Auto-Calculate Smart Levels
    const levels = calculateSmartLevels(cost, liveData);
    let autoStop = levels.initialStop;
    let autoTarget = levels.target;
    let strategy = levels.strategy;

    if (existing) {
        // Calculate Weighted Average Cost
        const totalCost = (existing.adet * existing.maliyet) + (count * cost);
        const totalCount = existing.adet + count;
        existing.maliyet = totalCost / totalCount;
        existing.adet = totalCount;

        // Update targets based on new average cost
        existing.initialStop = autoStop;
        existing.trailingStop = autoStop;
        existing.target = autoTarget;
        existing.highestPrice = existing.maliyet;
        existing.strategy = strategy;
    } else {
        MY_PORTFOLIO.push({
            sembol: symbol,
            adet: count,
            maliyet: cost,
            initialStop: parseFloat(autoStop.toFixed(2)),
            trailingStop: parseFloat(autoStop.toFixed(2)),
            target: parseFloat(autoTarget.toFixed(2)),
            highestPrice: cost,
            strategy: strategy
        });
    }

    savePortfolio();
    closeAddModal();
}

// -- Remove Stock from Portfolio --
function removeFromPortfolio(symbol) {
    if (confirm(`${symbol} hissesini portföyden silmek istediğinize emin misiniz?`)) {
        MY_PORTFOLIO = MY_PORTFOLIO.filter(p => p.sembol !== symbol);
        savePortfolio();
    }
}

// -- Modal Operations --
function openAddModal() { document.getElementById('addStockModal').classList.remove('hidden'); }
function closeAddModal() { document.getElementById('addStockModal').classList.add('hidden'); }

function submitAddStock() {
    const sym = document.getElementById('addSymbol').value.toUpperCase();
    const qty = parseFloat(document.getElementById('addQuantity').value);
    const cost = parseFloat(document.getElementById('addCost').value);
    addToPortfolio(sym, qty, cost);

    // Clear Inputs
    document.getElementById('addSymbol').value = '';
    document.getElementById('addQuantity').value = '';
    document.getElementById('addCost').value = '';
}


let globalData = [];
let currentTab = 'trend';

// -- Tab Switching Logic --
function switchTab(tabName) {
    currentTab = tabName;
    const marketView = document.getElementById('market-view');
    const portfolioView = document.getElementById('portfolio-view');
    const proView = document.getElementById('pro-view');

    // Tab Buttons
    const tabTrend = document.getElementById('tab-trend');
    const tabAll = document.getElementById('tab-all');
    const tabPro = document.getElementById('tab-pro');
    const tabPortfolio = document.getElementById('tab-portfolio');

    // Reset Classes
    const activeClass = "tab-active px-6 py-2 rounded-md text-sm font-bold transition flex items-center gap-2";
    const passiveClass = "tab-passive px-6 py-2 rounded-md text-sm font-bold transition flex items-center gap-2 opacity-70 hover:opacity-100";

    if (tabTrend) tabTrend.className = passiveClass + " hover:text-emerald-400";
    if (tabAll) tabAll.className = passiveClass + " hover:text-gray-400";
    if (tabPro) tabPro.className = passiveClass + " hover:text-purple-400";
    if (tabPortfolio) tabPortfolio.className = passiveClass;

    // Reset Views
    if (marketView) marketView.classList.add('hidden');
    if (portfolioView) portfolioView.classList.add('hidden');
    if (proView) proView.classList.add('hidden');

    if (tabName === 'portfolio') {
        if (portfolioView) portfolioView.classList.remove('hidden');
        if (tabPortfolio) tabPortfolio.className = activeClass;
        verileriGetir();
    } else if (tabName === 'pro') {
        if (proView) proView.classList.remove('hidden');
        if (tabPro) tabPro.className = activeClass + " text-amber-400";
        verileriGetir();
    } else {
        if (marketView) marketView.classList.remove('hidden');

        if (tabName === 'trend' && tabTrend) {
            tabTrend.className = activeClass + " text-emerald-400";
        } else if (tabName === 'all' && tabAll) {
            tabAll.className = activeClass + " text-gray-200";
        }
        verileriGetir();
    }
}

// -- Data Fetching Logic (API) --
async function verileriGetir() {
    const statusDiv = document.getElementById('connectionStatus');
    const messageArea = document.getElementById('messageArea');
    const params = new URLSearchParams();

    // Add filter props to params if not in portfolio mode
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
        let url = API_BASE_URL;
        if (currentTab === 'trend') {
            url = "http://localhost:5158/api/market/trend";
        } else if (currentTab === 'all' || currentTab === 'pro') {
            url = "http://localhost:5158/api/market/all";
        }

        const response = await fetch(`${url}?${params.toString()}`);
        if (!response.ok) throw new Error("API Hatası");

        globalData = await response.json();

        statusDiv.innerHTML = '<span class="w-2 h-2 rounded-full bg-emerald-500"></span> Online';
        statusDiv.className = "flex items-center gap-2 text-xs font-mono text-emerald-400 bg-emerald-900/20 px-3 py-1.5 rounded-full border border-emerald-900";
        messageArea.classList.add('hidden');

        // Render based on Tab
        if (currentTab === 'pro') {
            renderProTable(globalData);
        } else if (currentTab !== 'portfolio') {
            applySort(globalData);
            renderMarketTable(globalData);
        }

        // Always update portfolio in background
        renderPortfolio();

    } catch (error) {
        // Error handling masked for brevity
    }
}


// -- Sorting Logic --
let currentSort = { column: 'score', direction: 'desc' };

function sortTable(column) {
    if (currentSort.column === column) {
        currentSort.direction = currentSort.direction === 'asc' ? 'desc' : 'asc';
    } else {
        currentSort.column = column;
        currentSort.direction = (column === 'sembol' || column === 'signal') ? 'asc' : 'desc';
    }

    updateSortIcons();
    applySort(globalData);
    renderMarketTable(globalData);
}

function applySort(data) {
    data.sort((a, b) => {
        let valA = a[currentSort.column];
        let valB = b[currentSort.column];

        if (valA === null || valA === undefined) valA = -999999;
        if (valB === null || valB === undefined) valB = -999999;

        if (typeof valA === 'string') valA = valA.toLowerCase();
        if (typeof valB === 'string') valB = valB.toLowerCase();

        if (valA < valB) return currentSort.direction === 'asc' ? -1 : 1;
        if (valA > valB) return currentSort.direction === 'asc' ? 1 : -1;
        return 0;
    });
}

function updateSortIcons() {
    console.log(`Sorting: ${currentSort.column} (${currentSort.direction})`);
}

// -- Frontend Filtering --
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

// -- Helpers: Value Change Badge --
function getDiffBadge(current, prev) {
    if (prev === undefined || prev === null || prev === 0) return '';

    const diff = current - prev;
    if (Math.abs(diff) < 0.01) return '';

    const color = diff > 0 ? 'text-emerald-400' : 'text-red-400';
    const icon = diff > 0 ? '▲' : '▼';

    return `<div class="${color} text-[10px] font-mono mt-1">${icon} ${Math.abs(diff).toFixed(2)}</div>`;
}


// -- Render: Market Table --
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

            // Signal Badge
            let signalBadge = '';
            switch (h.signal) {
                case 'STRONG_BUY': signalBadge = '<span class="bg-gradient-to-r from-emerald-600 to-green-500 text-white px-3 py-1 rounded-full text-[10px] font-bold shadow-lg shadow-emerald-900/40 animate-pulse"><i class="fa-solid fa-rocket mr-1"></i> GÜÇLÜ AL</span>'; break;
                case 'BUY': signalBadge = '<span class="bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 px-2 py-1 rounded text-[10px] font-bold">✅ AL</span>'; break;
                case 'WATCH': signalBadge = '<span class="bg-yellow-500/10 text-yellow-400 border border-yellow-500/30 px-2 py-1 rounded text-[10px] font-bold">👀 İZLE</span>'; break;
                default: signalBadge = '<span class="text-gray-600 text-[10px]">NO TRADE</span>';
            }

            // Score Color
            let scoreColor = 'text-gray-500';
            if (h.score >= 75) scoreColor = 'text-emerald-400 font-bold';
            else if (h.score >= 50) scoreColor = 'text-yellow-400';
            else if (h.score >= 30) scoreColor = 'text-orange-400';
            else scoreColor = 'text-red-400';

            const tarih = new Date(h.sonGuncelleme).toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' });

            const row = `
            <tr id="row-${h.sembol}" class="hover:bg-gray-800/40 transition border-b border-gray-800/30 group">
                <td class="p-4 font-bold text-white sticky left-0 bg-[#0b0f19] group-hover:bg-gray-800/40 z-10 border-r border-gray-800/50">${h.sembol}</td>
                
                <td class="p-4 text-blue-300 font-mono text-base tracking-tight cell-fiyat">
                    ${h.fiyat.toFixed(2)} ₺
                    ${getDiffBadge(h.fiyat, h.fiyatOnceki)}
                </td>
                
                <td class="p-4 font-mono ${h.fiyat > h.sma50 ? 'text-emerald-300/90' : 'text-gray-600'}">${h.sma50.toFixed(2)}</td>
                <td class="p-4 font-mono ${h.fiyat > h.sma200 ? 'text-yellow-300/90' : 'text-gray-600'}">${h.sma200.toFixed(2)}</td>
                
                <td class="p-4 font-mono ${rsiClass} cell-rsi">
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

                <!-- Trading Signal Cells -->
                <td class="p-4 text-center cell-signal">${signalBadge}</td>
                <td class="p-4 text-center">
                    <div class="flex flex-col items-center">
                        <span class="${scoreColor} text-lg font-mono cell-score">${h.score || 0}</span>
                        <div class="w-16 h-1 bg-gray-700 rounded-full mt-1 overflow-hidden">
                            <div class="cell-score-bar h-full ${h.score >= 75 ? 'bg-emerald-500' : (h.score >= 50 ? 'bg-yellow-500' : 'bg-red-500')}" style="width: ${h.score || 0}%"></div>
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


// -- Render: Portfolio Table --
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

        // Backfill missing data (Target/Stop/Strategy) if liveData available
        if (liveData) {
            let needsUpdate = false;

            if (!item.target || !item.initialStop || !item.trailingStop || !item.strategy) {
                const levels = calculateSmartLevels(item.maliyet, liveData);
                item.target = levels.target;
                item.initialStop = levels.initialStop;
                item.trailingStop = item.trailingStop || levels.initialStop;
                item.strategy = levels.strategy;
                item.highestPrice = item.highestPrice || item.maliyet;
                needsUpdate = true;
            }

            // Update trailing stop
            if (currentPrice > 0) {
                updateTrailingStop(item, currentPrice, liveData);
                needsUpdate = true;
            }

            if (needsUpdate) {
                localStorage.setItem('myPortfolio', JSON.stringify(MY_PORTFOLIO));
            }
        }

        const pnlClass = pnl >= 0 ? 'text-emerald-400' : 'text-red-400';
        const bgClass = pnl >= 0 ? 'bg-emerald-500/10' : 'bg-red-500/10';

        let signalBadge = '<span class="text-gray-600">-</span>';

        if (liveData && item.target && item.trailingStop) {
            if (currentPrice >= item.target) {
                signalBadge = '<span class="bg-red-500 text-white px-2 py-1 rounded text-xs font-bold animate-pulse">🎯 HEDEF GELDİ (SAT)</span>';
            } else if (currentPrice <= item.trailingStop) {
                signalBadge = '<span class="bg-red-500 text-white px-2 py-1 rounded text-xs font-bold">🛑 STOP OLDU (SAT)</span>';
            } else {
                const stopDistance = ((currentPrice - item.trailingStop) / currentPrice * 100).toFixed(1);
                signalBadge = `<span class="text-emerald-500 text-xs font-bold">✅ TUT <span class="text-gray-500">(Stop: -${stopDistance}%)</span></span>`;
            }
        }
        else if (liveData) {
            if (liveData.rsi < 30) signalBadge = '<span class="bg-emerald-500 text-black px-2 py-1 rounded text-xs font-bold">DİP FIRSATI</span>';
            else signalBadge = '<span class="text-gray-500 text-xs">Bekle</span>';
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
                <td class="p-4 text-center text-xs font-mono text-gray-400">
                    <div>T: <span class="text-emerald-300">${item.target ? item.target.toFixed(2) : '-'}</span></div>
                    <div>S: <span class="text-red-300">${item.trailingStop ? item.trailingStop.toFixed(2) : '-'}</span></div>
                    ${item.highestPrice && item.highestPrice > item.maliyet ? `<div class="text-[9px] text-blue-400">Peak: ${item.highestPrice.toFixed(2)}</div>` : ''}
                </td>
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



// -- Helper: Calculate Smart Target/Stop --
function calculateSmartLevels(cost, liveData) {
    let stop = cost * 0.95; // Default 5%
    let target = cost * 1.15; // Default 15%
    let strategy = "TREND"; // Default strategy

    if (liveData && liveData.atr > 0) {
        const atr = liveData.atr;
        strategy = (liveData.strategy || "TREND").toUpperCase();

        // -- TREND Strategy --
        // Stop: 3.0 ATR
        stop = cost - (3.0 * atr);

        // Target: Dynamic Risk/Reward
        let multiplier = 4.0;

        if (liveData.adx > 30) multiplier += 2.0;
        else if (liveData.adx > 25) multiplier += 1.0;

        if (liveData.rsi > 75) multiplier -= 2.0;
        else if (liveData.rsi > 70) multiplier -= 1.0;

        if (multiplier < 2.0) multiplier = 2.0;

        target = cost + (multiplier * atr);
    }
    return {
        target: parseFloat(target.toFixed(2)),
        initialStop: parseFloat(stop.toFixed(2)),
        stop: parseFloat(stop.toFixed(2)),
        strategy: strategy
    };
}

// -- Trailing Stop Logic --
/**
 * Updates trailing stop based on current price.
 * Trailing stop only moves UP, never down.
 */
function updateTrailingStop(portfolioItem, currentPrice, liveData) {
    if (!liveData || !liveData.atr || liveData.atr <= 0) {
        return portfolioItem.trailingStop;
    }

    const strategy = portfolioItem.strategy || "TREND";
    const atr = liveData.atr;

    let atrMultiplier = 3.0; // TREND

    // Update highest price seen
    if (currentPrice > portfolioItem.highestPrice) {
        portfolioItem.highestPrice = currentPrice;
    }

    // Calculate new stop level
    const newStop = portfolioItem.highestPrice - (atrMultiplier * atr);

    // Trailing: Only move up
    const updatedStop = Math.max(portfolioItem.initialStop, newStop);

    portfolioItem.trailingStop = parseFloat(updatedStop.toFixed(2));

    return portfolioItem.trailingStop;
}

// -- SignalR (Real-Time Updates) --
const connection = new signalR.HubConnectionBuilder()
    .withUrl("/hubs/borsa")
    .withAutomaticReconnect()
    .build();

connection.start()
    .then(() => {
        console.log("🟢 SignalR Connected!");
        document.getElementById('connectionStatus').innerHTML = '<span class="w-2 h-2 rounded-full bg-emerald-500"></span> Canlı (WebSocket)';
        document.getElementById('connectionStatus').className = "flex items-center gap-2 text-xs font-mono text-emerald-400 bg-emerald-900/20 px-3 py-1.5 rounded-full border border-emerald-900";
    })
    .catch(err => console.error("SignalR Connection Error: ", err));

connection.on("ReceiveStockUpdate", (updatedStock) => {
    // 1. Update Global Data
    const index = globalData.findIndex(s => s.sembol === updatedStock.sembol);
    if (index !== -1) {
        globalData[index] = updatedStock;
    }

    // 2. Update Portfolio (Real-Time Trailing Stop)
    const portfolioItem = MY_PORTFOLIO.find(p => p.sembol === updatedStock.sembol);
    if (portfolioItem) {
        updateTrailingStop(portfolioItem, updatedStock.fiyat, updatedStock);

        if (currentTab === 'portfolio') {
            renderPortfolio();
        } else {
            savePortfolio();
        }
    }

    // 3. Update Market Table Row (Smart Patching)
    if (currentTab !== 'portfolio') {
        const row = document.getElementById(`row-${updatedStock.sembol}`);
        if (row) {
            // Flash Effect
            const isPositive = updatedStock.fiyat > updatedStock.fiyatOnceki;
            const flashClass = isPositive ? 'bg-emerald-900/40' : 'bg-red-900/40';

            row.classList.add(flashClass);
            setTimeout(() => row.classList.remove(flashClass), 500);

            // Update Cells
            updateCell(row, '.cell-fiyat', `${updatedStock.fiyat.toFixed(2)} ₺ ${getDiffBadge(updatedStock.fiyat, updatedStock.fiyatOnceki)}`);
            updateCell(row, '.cell-rsi', `${updatedStock.rsi.toFixed(2)} ${getDiffBadge(updatedStock.rsi, updatedStock.rsiOnceki)}`);
            updateCell(row, '.cell-score', updatedStock.score);

            // Update Score Bar
            const scoreBar = row.querySelector('.cell-score-bar');
            if (scoreBar) {
                scoreBar.style.width = `${updatedStock.score}%`;
                scoreBar.className = `h-full ${updatedStock.score >= 75 ? 'bg-emerald-500' : (updatedStock.score >= 50 ? 'bg-yellow-500' : 'bg-red-500')}`;
            }

            // Update Signal Badge
            const signalCell = row.querySelector('.cell-signal');
            if (signalCell) signalCell.innerHTML = getSignalBadge(updatedStock.signal);
        }
    }
});

function updateCell(row, selector, content) {
    const cell = row.querySelector(selector);
    if (cell) cell.innerHTML = content;
}

function getSignalBadge(signal) {
    switch (signal) {
        case 'STRONG_BUY': return '<span class="bg-gradient-to-r from-emerald-600 to-green-500 text-white px-3 py-1 rounded-full text-[10px] font-bold shadow-lg shadow-emerald-900/40 animate-pulse"><i class="fa-solid fa-rocket mr-1"></i> GÜÇLÜ AL</span>';
        case 'BUY': return '<span class="bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 px-2 py-1 rounded text-[10px] font-bold">✅ AL</span>';
        case 'WATCH': return '<span class="bg-yellow-500/10 text-yellow-400 border border-yellow-500/30 px-2 py-1 rounded text-[10px] font-bold">👀 İZLE</span>';
        default: return '<span class="text-gray-600 text-[10px]">NO TRADE</span>';
    }
}


// -- UI: Slider Value Display --
document.addEventListener('DOMContentLoaded', () => {
    const slider = document.getElementById('minScoreSlider');
    const valueDisplay = document.getElementById('minScoreValue');
    if (slider && valueDisplay) {
        slider.addEventListener('input', (e) => {
            valueDisplay.innerText = e.target.value;
        });
    }
});


// ─────────────────────────────────────────────────────────
// SMART PICKS — Unified Conviction Engine Renderer
// ─────────────────────────────────────────────────────────

const DANGER_TAGS_FE = ["Falling Knife", "High Sell Vol", "Bear Regime Risk"];
const POSITIVE_TAGS_FE = ["Strong Trend", "Whale Volume", "Smart Money In", "Above VWMA", "BB Squeeze", "Long-Term Bull"];
const WARNING_TAGS_FE = ["Overbought", "MFI Overbought", "Vol Divergence", "Tiring Trend", "RSI Reversal", "Weak Trend"];

function getTagHtml(tag) {
    const isDanger = DANGER_TAGS_FE.some(d => tag.includes(d));
    const isPositive = POSITIVE_TAGS_FE.some(p => tag.includes(p));
    const isWarning = WARNING_TAGS_FE.some(w => tag.includes(w));

    let cls = 'bg-gray-800 text-gray-400 border-gray-700';
    if (isDanger) cls = 'bg-red-500/15 text-red-400 border-red-500/40 font-bold';
    else if (isPositive) cls = 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
    else if (isWarning) cls = 'bg-yellow-500/10 text-yellow-400 border-yellow-500/30';

    return `<span class="inline-block px-2 py-0.5 rounded text-[10px] mr-1 mb-1 border ${cls}">${tag}</span>`;
}

function getConvictionLED(conviction) {
    const ledGreen = '<span class="w-2.5 h-2.5 rounded-full bg-emerald-400 shadow-[0_0_6px_rgba(52,211,153,0.8)]"></span>';
    const ledYellow = '<span class="w-2.5 h-2.5 rounded-full bg-yellow-400 shadow-[0_0_6px_rgba(250,204,21,0.8)]"></span>';
    const ledOff = '<span class="w-2.5 h-2.5 rounded-full bg-gray-700"></span>';

    const configs = {
        'DIAMOND': { leds: [ledGreen, ledGreen, ledGreen, ledGreen], badge: '💎 DIAMOND', cls: 'text-cyan-300 font-black' },
        'GOLD': { leds: [ledGreen, ledGreen, ledGreen, ledOff], badge: '🥇 GOLD', cls: 'text-amber-300 font-bold' },
        'SILVER': { leds: [ledGreen, ledGreen, ledOff, ledOff], badge: '🥈 SILVER', cls: 'text-gray-300 font-semibold' },
        'BRONZE': { leds: [ledYellow, ledOff, ledOff, ledOff], badge: '🥉 BRONZE', cls: 'text-orange-400 font-normal' }
    };
    const cfg = configs[conviction] || configs['BRONZE'];
    return `
        <div class="flex flex-col items-end gap-1">
            <span class="${cfg.cls} text-xs">${cfg.badge}</span>
            <div class="flex gap-1">${cfg.leds.join('')}</div>
        </div>`;
}

function getStrategyBadge(strategy) {
    switch (strategy) {
        case 'TREND': return '<span class="bg-blue-600/20 text-blue-300 px-2 py-0.5 rounded border border-blue-600/30 text-[10px]">📈 Trend</span>';
        case 'BREAKOUT': return '<span class="bg-purple-600/20 text-purple-300 px-2 py-0.5 rounded border border-purple-600/30 text-[10px]">🚀 Breakout</span>';
        case 'REVERSAL': return '<span class="bg-emerald-600/20 text-emerald-300 px-2 py-0.5 rounded border border-emerald-600/30 text-[10px]">🎣 Reversal</span>';
        default: return '<span class="text-gray-600 text-[10px]">⏳ Neutral</span>';
    }
}

function buildSmartCard(h, accentClass, borderClass) {
    const tags = h.tags || [];
    const unifiedScore = h.unifiedScore || 0;
    const conviction = h.conviction || 'BRONZE';
    const hasDanger = DANGER_TAGS_FE.some(d => tags.some(t => t.includes(d)));

    let scoreColor = 'text-gray-400';
    if (unifiedScore >= 75) scoreColor = 'text-emerald-400 font-bold';
    else if (unifiedScore >= 50) scoreColor = 'text-yellow-400';
    else scoreColor = 'text-red-400';

    const tagsHtml = tags.map(getTagHtml).join('');
    const scoreBar = `
        <div class="w-full h-1 bg-gray-800 rounded-full overflow-hidden mt-1">
            <div class="h-full ${unifiedScore >= 75 ? 'bg-emerald-500' : (unifiedScore >= 50 ? 'bg-yellow-500' : 'bg-red-500')}" style="width:${unifiedScore}%"></div>
        </div>`;

    const portfolio_warning = MY_PORTFOLIO.some(p => p.sembol === h.sembol) && hasDanger
        ? `<div class="mt-2 text-[10px] bg-red-500/10 text-red-400 border border-red-500/30 rounded px-2 py-1 font-bold">⚠️ Portföyünüzde var — dikkat!</div>`
        : '';

    return `
    <div class="glass rounded-xl p-5 border ${borderClass} hover:scale-[1.01] transition-transform relative">
        <div class="flex justify-between items-start mb-3">
            <div>
                <span class="text-white font-black text-xl tracking-wide">${h.sembol}</span>
                <div class="flex items-center gap-2 mt-1">
                    <span class="text-blue-300 font-mono text-sm">${(h.fiyat || 0).toFixed(2)} ₺</span>
                    ${getStrategyBadge(h.mainStrategy)}
                </div>
            </div>
            ${getConvictionLED(conviction)}
        </div>
        
        <div class="flex items-center justify-between mb-2">
            <div class="flex flex-col">
                <span class="text-[10px] text-gray-500 uppercase">Unified Score</span>
                <span class="${scoreColor} text-2xl font-mono leading-none">${unifiedScore}</span>
                ${scoreBar}
            </div>
            <div class="flex flex-col items-end gap-1">
                <div class="text-[10px] text-gray-500">
                    Stop: <span class="text-red-300 font-mono">${(h.stopPrice || 0).toFixed(2)} ₺</span>
                </div>
                <div class="text-[10px] text-gray-500">
                    Hedef: <span class="text-emerald-300 font-mono">${(h.targetPrice || 0).toFixed(2)} ₺</span>
                </div>
            </div>
        </div>

        <div class="flex flex-wrap mt-3">
            ${tagsHtml || '<span class="text-gray-700 text-[10px]">Tag yok</span>'}
        </div>
        ${portfolio_warning}

        <button onclick="openAddModal()"
            class="mt-3 w-full bg-blue-600/20 hover:bg-blue-600/40 text-blue-300 border border-blue-600/30 py-1.5 rounded text-xs font-semibold transition flex items-center justify-center gap-1">
            <i class="fa-solid fa-plus"></i> Portföye Ekle
        </button>
    </div>`;
}

function renderSmartPicks(data) {
    const topGrid = document.getElementById('topPicksGrid');
    const watchGrid = document.getElementById('watchlistGrid');
    const avoidGrid = document.getElementById('avoidGrid');
    const regimeLabel = document.getElementById('regimeLabel');
    const topCount = document.getElementById('topPicksCount');
    const watchCount = document.getElementById('watchlistCount');
    const avoidCount = document.getElementById('avoidCount');

    if (!topGrid) return;

    // ── Market Regime Banner ──
    const firstWithRegime = data.find(h => h.marketRegime);
    const regime = firstWithRegime ? firstWithRegime.marketRegime : 'SIDEWAYS';
    if (regimeLabel) {
        let rClass = 'text-gray-300', rIcon = '⚖️';
        if (regime === 'BULL') { rClass = 'text-emerald-400'; rIcon = '🐂'; }
        if (regime === 'BEAR') { rClass = 'text-red-400'; rIcon = '🐻'; }
        regimeLabel.innerHTML = `<span class="${rClass}">${rIcon} ${regime}</span>`;
    }

    // ── Section classification ──
    const DANGER = DANGER_TAGS_FE;
    const avoidList = [];
    const topList = [];
    const watchList = [];

    data.forEach(h => {
        const tags = h.tags || [];
        const unified = h.unifiedScore || 0;
        const conviction = h.conviction || 'BRONZE';
        const hasDanger = DANGER.some(d => tags.some(t => t.includes(d)));

        if (hasDanger) {
            avoidList.push(h);
        } else if (unified >= 65 && (conviction === 'DIAMOND' || conviction === 'GOLD')) {
            topList.push(h);
        } else if (unified >= 50 || conviction === 'SILVER') {
            watchList.push(h);
        }
        // below 50 + no danger → silently excluded (NO_TRADE)
    });

    // Sort by unifiedScore desc
    topList.sort((a, b) => (b.unifiedScore || 0) - (a.unifiedScore || 0));
    watchList.sort((a, b) => (b.unifiedScore || 0) - (a.unifiedScore || 0));
    avoidList.sort((a, b) => (b.unifiedScore || 0) - (a.unifiedScore || 0));

    if (topCount) topCount.innerText = topList.length;
    if (watchCount) watchCount.innerText = watchList.length;
    if (avoidCount) avoidCount.innerText = avoidList.length;

    // ── Render cards ──
    topGrid.innerHTML = topList.length
        ? topList.map(h => buildSmartCard(h, 'border-amber-500/30', 'border-amber-500/20')).join('')
        : '<p class="text-gray-600 text-sm col-span-3 py-8 text-center">Bugün kriterleri karşılayan hisse yok. Fırsatı bekleyin.</p>';

    watchGrid.innerHTML = watchList.length
        ? watchList.map(h => buildSmartCard(h, 'border-blue-500/30', 'border-blue-500/20')).join('')
        : '<p class="text-gray-600 text-sm col-span-3 py-8 text-center">İzlenecek hisse bulunmuyor.</p>';

    avoidGrid.innerHTML = avoidList.length
        ? avoidList.map(h => buildSmartCard(h, 'border-red-500/30', 'border-red-500/30')).join('')
        : '<p class="text-gray-600 text-sm col-span-3 py-8 text-center">✅ Tehlikeli hisse yok — piyasa temiz görünüyor.</p>';
}

// Keep backward-compat alias (SignalR path)
function renderProTable(data) { renderSmartPicks(data); }
