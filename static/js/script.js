// Global Değişkenler
const API_BASE_URL = "http://localhost:5158/api/hisseler";

const MY_PORTFOLIO = [
    { sembol: "BINHO", adet: 2420, maliyet: 10.68 }
];

let globalData = [];

// Tab Değiştirme Fonksiyonu
function switchTab(tabName) {
    const marketView = document.getElementById('market-view');
    const portfolioView = document.getElementById('portfolio-view');
    const tabMarket = document.getElementById('tab-market');
    const tabPortfolio = document.getElementById('tab-portfolio');

    if (tabName === 'market') {
        marketView.classList.remove('hidden');
        portfolioView.classList.add('hidden');
        tabMarket.className = "tab-active px-6 py-2 rounded-md text-sm font-bold transition flex items-center gap-2";
        tabPortfolio.className = "tab-passive px-6 py-2 rounded-md text-sm font-bold transition flex items-center gap-2";
    } else {
        marketView.classList.add('hidden');
        portfolioView.classList.remove('hidden');
        tabMarket.className = "tab-passive px-6 py-2 rounded-md text-sm font-bold transition flex items-center gap-2";
        tabPortfolio.className = "tab-active px-6 py-2 rounded-md text-sm font-bold transition flex items-center gap-2";
        renderPortfolio();
    }
}

// Veri Çekme Fonksiyonu
async function verileriGetir() {
    const statusDiv = document.getElementById('connectionStatus');
    const messageArea = document.getElementById('messageArea');
    const params = new URLSearchParams();
    
    addParam(params, 'minFk', 'minFk'); addParam(params, 'maxFk', 'maxFk');
    addParam(params, 'minPdDd', 'minPdDd'); addParam(params, 'maxPdDd', 'maxPdDd');
    addParam(params, 'minRsi', 'minRsi'); addParam(params, 'maxRsi', 'maxRsi');
    addParam(params, 'minMacdHist', 'minMacdHist'); addParam(params, 'maxMacdHist', 'maxMacdHist');
    addParam(params, 'minAdx', 'minAdx'); addParam(params, 'maxAdx', 'maxAdx');
    addParam(params, 'minHacimOrani', 'minHacim'); addParam(params, 'maxHacimOrani', 'maxHacim');
    addParam(params, 'minDmp', 'minDmp'); addParam(params, 'minDmn', 'minDmn');

    try {
        statusDiv.innerHTML = '<span class="w-2 h-2 rounded-full bg-yellow-500 animate-pulse"></span> ...';
        const response = await fetch(`${API_BASE_URL}?${params.toString()}`);
        if (!response.ok) throw new Error("API Hatası");
        
        globalData = await response.json();
        
        statusDiv.innerHTML = '<span class="w-2 h-2 rounded-full bg-emerald-500"></span> Online';
        statusDiv.className = "flex items-center gap-2 text-xs font-mono text-emerald-400 bg-emerald-900/20 px-3 py-1.5 rounded-full border border-emerald-900";
        messageArea.classList.add('hidden');
        
        let filteredData = frontendFiltrele(globalData);
        renderMarketTable(filteredData);
        renderPortfolio(); 

    } catch (error) {
        console.warn(error);
        statusDiv.innerHTML = '<span class="w-2 h-2 rounded-full bg-red-500"></span> Offline';
        statusDiv.className = "flex items-center gap-2 text-xs font-mono text-gray-500 bg-gray-900 px-3 py-1.5 rounded-full border border-gray-800";
        messageArea.classList.remove('hidden');
        
        const MOCK_DATA = [
            { sembol: "THYAO", fiyat: 273.50, sma50: 260.00, sma200: 240.50, rsi: 28.5, adx: 35.2, dmp: 12.0, dmn: 25.0, hacimOrani: 2.1, macdHist: 2.45, macdLine: 5.2, macdSignal: 2.75, fk: 3.2, pdDd: 0.8, sonGuncelleme: new Date().toISOString() },
            { sembol: "ASELS", fiyat: 62.10, sma50: 60.00, sma200: 65.00, rsi: 45.0, adx: 15.0, dmp: 18.0, dmn: 19.0, hacimOrani: 0.8, macdHist: -0.5, macdLine: 1.2, macdSignal: 1.7, fk: 12.5, pdDd: 3.4, sonGuncelleme: new Date().toISOString() }
        ];
        globalData = MOCK_DATA;
        renderMarketTable(MOCK_DATA);
    }
}

// Frontend Filtreleme
function frontendFiltrele(data) {
    const maxAdx = parseFloat(val('maxAdx')) || 9999;
    const minHacim = parseFloat(val('minHacim')) || 0;
    const maxHacim = parseFloat(val('maxHacim')) || 9999;
    const maxFk = parseFloat(val('maxFk')) || 9999;
    const maxPdDd = parseFloat(val('maxPdDd')) || 9999;

    return data.filter(h => 
        h.adx <= maxAdx && 
        h.hacimOrani >= minHacim && h.hacimOrani <= maxHacim &&
        h.fk <= maxFk &&
        h.pdDd <= maxPdDd
    );
}

// Piyasa Tablosunu Çiz
function renderMarketTable(data) {
    const tbody = document.getElementById('hisseTablosu');
    tbody.innerHTML = '';
    
    if (data.length === 0) {
        tbody.innerHTML = '<tr><td colspan="12" class="p-12 text-center text-gray-500">Aradığınız kriterlere uygun hisse bulunamadı.</td></tr>';
        return;
    }

    data.forEach(h => {
        const rsiClass = h.rsi < 30 ? 'text-emerald-400 font-bold animate-pulse' : (h.rsi > 70 ? 'text-red-400 font-bold' : 'text-gray-400');
        const macdClass = h.macdHist > 0 ? 'text-emerald-400' : 'text-red-400';
        const adxClass = h.adx > 25 ? 'text-white font-bold' : 'text-gray-600';
        
        let volText = 'text-gray-500';
        let volIcon = 'fa-battery-quarter text-gray-700';
        if (h.hacimOrani > 2.0) { volText = 'text-orange-400 font-bold'; volIcon = 'fa-fire-flame-curved animate-pulse text-orange-500'; }
        else if (h.hacimOrani > 1.2) { volText = 'text-emerald-300'; volIcon = 'fa-arrow-trend-up text-emerald-500'; }
        
        const tarih = new Date(h.sonGuncelleme).toLocaleTimeString('tr-TR', {hour: '2-digit', minute:'2-digit'});

        const row = `
            <tr class="hover:bg-gray-800/40 transition border-b border-gray-800/30 group">
                <td class="p-4 font-bold text-white sticky left-0 bg-[#0b0f19] group-hover:bg-gray-800/40 z-10 border-r border-gray-800/50">${h.sembol}</td>
                <td class="p-4 text-blue-300 font-mono text-base tracking-tight">${h.fiyat.toFixed(2)} ₺</td>
                <td class="p-4 font-mono ${h.fiyat > h.sma50 ? 'text-emerald-300/90' : 'text-gray-600'}">${h.sma50.toFixed(2)}</td>
                <td class="p-4 font-mono ${h.fiyat > h.sma200 ? 'text-yellow-300/90' : 'text-gray-600'}">${h.sma200.toFixed(2)}</td>
                <td class="p-4 font-mono ${rsiClass}">${h.rsi.toFixed(2)}</td>
                
                <td class="p-4 text-center bg-blue-900/5">
                    <div class="flex flex-col items-center">
                        <span class="${adxClass} text-sm">${h.adx.toFixed(2)}</span>
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
                <td class="p-4 text-xs text-gray-600 font-mono">${tarih}</td>
            </tr>`;
        tbody.innerHTML += row;
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
        
        if(currentPrice > 0) {
            totalVal += totalValue; 
            totalCost += costValue;
        }

        const pnlClass = pnl >= 0 ? 'text-emerald-400' : 'text-red-400';
        const bgClass = pnl >= 0 ? 'bg-emerald-500/10' : 'bg-red-500/10';
        
        let signalBadge = '<span class="text-gray-600">-</span>';
        if(liveData) {
            if(liveData.rsi < 30 && liveData.adx > 20) signalBadge = '<span class="bg-emerald-500 text-black px-2 py-1 rounded text-xs font-bold animate-pulse">AL FIRSATI</span>';
            else if(liveData.rsi > 70) signalBadge = '<span class="bg-red-500 text-white px-2 py-1 rounded text-xs font-bold">SAT (Şişti)</span>';
            else if(liveData.hacimOrani > 2.0) signalBadge = '<span class="bg-orange-500 text-white px-2 py-1 rounded text-xs font-bold">HACİM PATLAMASI</span>';
        }

        const row = `
            <tr class="hover:bg-gray-800/40 border-b border-gray-800/30 ${bgClass}">
                <td class="p-4 font-bold text-white">${item.sembol}</td>
                <td class="p-4 text-right font-mono text-gray-300">${item.adet}</td>
                <td class="p-4 text-right font-mono text-gray-400">${item.maliyet.toFixed(2)} ₺</td>
                <td class="p-4 text-right font-mono text-blue-300 font-bold">${currentPrice > 0 ? currentPrice.toFixed(2) + ' ₺' : '...'}</td>
                <td class="p-4 text-right font-mono text-white font-bold">${totalValue.toFixed(2)} ₺</td>
                <td class="p-4 text-right font-mono ${pnlClass}">${pnl > 0 ? '+' : ''}${pnl.toFixed(2)} ₺</td>
                <td class="p-4 text-right font-mono ${pnlClass} font-bold">%${pnlPercent.toFixed(2)}</td>
                <td class="p-4 text-center">${signalBadge}</td>
            </tr>`;
        tbody.innerHTML += row;
    });

    const totalPnL = totalVal - totalCost;
    const totalPnLPercent = totalCost > 0 ? (totalPnL / totalCost) * 100 : 0;
    document.getElementById('totalBalance').innerText = `₺${totalVal.toLocaleString('tr-TR', {minimumFractionDigits: 2})}`;
    document.getElementById('stockCount').innerText = MY_PORTFOLIO.length;
    const pnlEl = document.getElementById('totalPnL');
    const pnlPerEl = document.getElementById('totalPnLPercent');
    pnlEl.innerText = `${totalPnL > 0 ? '+' : ''}₺${totalPnL.toLocaleString('tr-TR', {minimumFractionDigits: 2})}`;
    pnlPerEl.innerText = `%${totalPnLPercent.toFixed(2)}`;
    if (totalPnL >= 0) { 
        pnlEl.className = "text-3xl font-bold text-emerald-400 font-mono"; 
        pnlPerEl.className = "text-sm font-bold font-mono text-emerald-500 bg-emerald-500/10 px-2 py-1 rounded"; 
        document.getElementById('pnlIcon').className = "bg-emerald-500/20 p-3 rounded-full text-emerald-400";
    } else { 
        pnlEl.className = "text-3xl font-bold text-red-400 font-mono"; 
        pnlPerEl.className = "text-sm font-bold font-mono text-red-500 bg-red-500/10 px-2 py-1 rounded"; 
        document.getElementById('pnlIcon').className = "bg-red-500/20 p-3 rounded-full text-red-400";
    }
}

// Yardımcı Fonksiyonlar
function addParam(params, name, id) { const el = document.getElementById(id); if(el && el.value) params.append(name, el.value); }
function val(id) { return document.getElementById(id) ? document.getElementById(id).value : null; }
function temizle() { document.querySelectorAll('input').forEach(i => i.value = ''); verileriGetir(); }

// Başlangıç
window.onload = verileriGetir;