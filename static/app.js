document.addEventListener('DOMContentLoaded', () => {
    initCharts();
    initChat();
    initActionButtons();
    initNavTabs();
});

let allocationChart = null;
let performanceChart = null;

function initCharts() {
    // 1. Asset Allocation Doughnut Chart (%45 Hisse, %25 Altın, %20 Döviz, %10 Tahvil)
    const ctxAllocation = document.getElementById('allocationChart').getContext('2d');
    allocationChart = new Chart(ctxAllocation, {
        type: 'doughnut',
        data: {
            labels: ['Hisse Senedi (%45.2)', 'Altın (%24.8)', 'Döviz (%20.0)', 'Tahvil & Bono (%10.0)'],
            datasets: [{
                data: [226415, 124460, 100470, 49970],
                backgroundColor: [
                    '#0091da', // Deniz Cyan
                    '#f59e0b', // Altın Amber
                    '#10b981', // Döviz Green
                    '#8b5cf6'  // Tahvil Purple
                ],
                borderWidth: 0,
                hoverOffset: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: '#94a3b8',
                        font: { size: 12, family: 'Inter' },
                        padding: 16
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            let value = context.raw || 0;
                            return ' ' + context.label.split(' ')[0] + ': ₺' + value.toLocaleString('tr-TR');
                        }
                    }
                }
            },
            cutout: '68%'
        }
    });

    // 2. Portfolio Performance Line Chart (30-day trend)
    const ctxPerf = document.getElementById('performanceChart').getContext('2d');
    const days = Array.from({length: 15}, (_, i) => `Gün ${i*2 + 1}`);
    const perfData = [458000, 461200, 459800, 467000, 472500, 469000, 478400, 483000, 481200, 489500, 493000, 491000, 497800, 499200, 501315];

    performanceChart = new Chart(ctxPerf, {
        type: 'line',
        data: {
            labels: days,
            datasets: [{
                label: 'Portföy Değeri (TL)',
                data: perfData,
                borderColor: '#0091da',
                borderWidth: 3,
                tension: 0.35,
                fill: true,
                backgroundColor: (context) => {
                    const ctx = context.chart.ctx;
                    const gradient = ctx.createLinearGradient(0, 0, 0, 200);
                    gradient.addColorStop(0, 'rgba(0, 145, 218, 0.35)');
                    gradient.addColorStop(1, 'rgba(0, 145, 218, 0.0)');
                    return gradient;
                },
                pointRadius: 3,
                pointHoverRadius: 6,
                pointBackgroundColor: '#0091da'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: (ctx) => ' ₺' + ctx.raw.toLocaleString('tr-TR')
                    }
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { color: '#94a3b8', font: { size: 11 } }
                },
                y: {
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { 
                        color: '#94a3b8',
                        font: { size: 11 },
                        callback: (value) => '₺' + (value/1000) + 'k'
                    }
                }
            }
        }
    });
}

function initActionButtons() {
    const btnRebalance = document.getElementById('btnRebalance');
    const btnFullReport = document.getElementById('btnFullReport');
    const btnQuickRebalance = document.getElementById('btnQuickRebalance');

    const triggerRebalance = () => {
        const chatCard = document.querySelector('.chat-card');
        if (chatCard) chatCard.scrollIntoView({ behavior: 'smooth' });
        sendStreamMessage("Portföyü yeniden dengele ve hedef risk profiline göre alım-satım önerisi ver.");
    };

    if (btnRebalance) btnRebalance.addEventListener('click', triggerRebalance);
    if (btnQuickRebalance) btnQuickRebalance.addEventListener('click', triggerRebalance);

    if (btnFullReport) {
        btnFullReport.addEventListener('click', () => {
            const chatCard = document.querySelector('.chat-card');
            if (chatCard) chatCard.scrollIntoView({ behavior: 'smooth' });
            sendStreamMessage("Detaylı Kişisel Finans Danışmanlığı ve Risk Analizi Raporu Oluştur.", true);
        });
    }

    document.querySelectorAll('.chip-prompt').forEach(chip => {
        chip.addEventListener('click', () => {
            const query = chip.getAttribute('data-query');
            const chatCard = document.querySelector('.chat-card');
            if (chatCard) chatCard.scrollIntoView({ behavior: 'smooth' });
            sendStreamMessage(query);
        });
    });
}

function initChat() {
    const chatForm = document.getElementById('chatForm');
    const userInput = document.getElementById('userInput');

    chatForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const text = userInput.value.trim();
        if (text) {
            sendStreamMessage(text);
            userInput.value = '';
        }
    });
}

function appendMessage(sender, text) {
    const chatMessages = document.getElementById('chatMessages');
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${sender === 'user' ? 'user-msg' : 'agent-msg'}`;

    const avatar = document.createElement('div');
    avatar.className = 'msg-avatar';
    avatar.textContent = sender === 'user' ? '👤' : '🤖';

    const wrapper = document.createElement('div');
    wrapper.className = 'msg-content-wrapper';

    const content = document.createElement('div');
    content.className = 'msg-content';
    content.textContent = text;

    wrapper.appendChild(content);
    msgDiv.appendChild(avatar);
    msgDiv.appendChild(wrapper);
    chatMessages.appendChild(msgDiv);

    chatMessages.scrollTop = chatMessages.scrollHeight;
    return { wrapper, content, msgDiv };
}

function createTypingIndicator() {
    const chatMessages = document.getElementById('chatMessages');
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message agent-msg';
    typingDiv.id = 'typingIndicator';

    const avatar = document.createElement('div');
    avatar.className = 'msg-avatar';
    avatar.textContent = '🤖';

    const indicator = document.createElement('div');
    indicator.className = 'typing-indicator';
    indicator.innerHTML = `
        <span>Yapay zeka ajanları düşünüyor</span>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
    `;

    typingDiv.appendChild(avatar);
    typingDiv.appendChild(indicator);
    chatMessages.appendChild(typingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return typingDiv;
}

function sendStreamMessage(query, forceFull = false) {
    appendMessage('user', query);

    const streamBadge = document.getElementById('streamBadge');
    streamBadge.style.display = 'block';

    // 1. Typing Indicator Animasyonu Göster
    const typingEl = createTypingIndicator();

    let messageObj = null;
    let isFirstChunk = true;

    const encodedQuery = encodeURIComponent(query);
    const eventSource = new EventSource(`/api/chat/stream?q=${encodedQuery}&user_id=1&force_full=${forceFull}`);

    eventSource.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);

            if (data.event === 'end') {
                eventSource.close();
                streamBadge.style.display = 'none';
                if (messageObj) {
                    renderRAGSources(messageObj.wrapper, messageObj.content.textContent);
                }
                return;
            }

            if (data.content) {
                // İlk chunk geldiğinde typing indicator'ı kaldır ve gerçek mesaj alanını aç
                if (isFirstChunk) {
                    if (typingEl && typingEl.parentNode) {
                        typingEl.parentNode.removeChild(typingEl);
                    }
                    messageObj = appendMessage('agent', '');
                    isFirstChunk = false;
                }

                messageObj.content.textContent += data.content;
                const chatMessages = document.getElementById('chatMessages');
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }
        } catch (err) {
            console.error("SSE parse error", err);
        }
    };

    eventSource.onerror = (err) => {
        console.error("SSE connection error", err);
        if (typingEl && typingEl.parentNode) {
            typingEl.parentNode.removeChild(typingEl);
        }
        eventSource.close();
        streamBadge.style.display = 'none';
    };
}

function renderRAGSources(wrapperEl, messageText) {
    if (!wrapperEl || !messageText) return;

    const sourceMap = {
        "THYAO Q3 REPORT": "📌 Kaynak: THYAO 3. Çeyrek KAP Bildirimi",
        "GARAN FINANCIAL NEWS": "📌 Kaynak: Garanti BBVA Finansal Haberler",
        "GOLD MARKET ANALYSIS": "📌 Kaynak: Küresel Altın Analiz Raporu",
        "FOREX AND FED REPORT": "📌 Kaynak: Fed Faiz & Döviz Raporu"
    };

    const foundSources = [];
    for (const [key, badgeText] of Object.entries(sourceMap)) {
        if (messageText.includes(key) || messageText.toLowerCase().includes(key.toLowerCase())) {
            foundSources.push(badgeText);
        }
    }

    // Ayrıca metin içinde "THYAO", "GARAN", "Altın", "Fed" geçen durumları genel kaynak olarak rozetle
    if (foundSources.length === 0) {
        if (messageText.includes("THYAO")) foundSources.push("📌 Kaynak: THYAO 3. Çeyrek KAP Bildirimi");
        if (messageText.includes("Altın") || messageText.includes("GOLD")) foundSources.push("📌 Kaynak: Küresel Altın Raporu");
        if (messageText.includes("Fed") || messageText.includes("Dolar")) foundSources.push("📌 Kaynak: Makroekonomik Döviz Raporu");
    }

    if (foundSources.length > 0) {
        const badgeContainer = document.createElement('div');
        badgeContainer.className = 'source-badges-container';

        // Tekrarları önle
        const uniqueSources = [...new Set(foundSources)];
        uniqueSources.forEach(src => {
            const badge = document.createElement('span');
            badge.className = 'source-badge';
            badge.textContent = src;
            badgeContainer.appendChild(badge);
        });

        wrapperEl.appendChild(badgeContainer);
    }
}

function initNavTabs() {
    const navItems = document.querySelectorAll('.nav-item');
    const assetsModal = document.getElementById('assetsModal');
    const rebalanceModal = document.getElementById('rebalanceModal');
    const ragModal = document.getElementById('ragModal');

    const closeAssetsModal = document.getElementById('closeAssetsModal');
    const closeRebalanceModal = document.getElementById('closeRebalanceModal');
    const closeRagModal = document.getElementById('closeRagModal');

    function hideAllModals() {
        if (assetsModal) assetsModal.style.display = 'none';
        if (rebalanceModal) rebalanceModal.style.display = 'none';
        if (ragModal) ragModal.style.display = 'none';
    }

    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            navItems.forEach(i => i.classList.remove('active'));
            item.classList.add('active');

            const tab = item.getAttribute('data-tab');
            hideAllModals();

            if (tab === 'dashboard') {
                window.scrollTo({ top: 0, behavior: 'smooth' });
            } else if (tab === 'assets') {
                loadAssetsModal();
            } else if (tab === 'rebalance') {
                loadRebalanceModal();
                const chatCard = document.querySelector('.chat-card');
                if (chatCard) chatCard.scrollIntoView({ behavior: 'smooth' });
                sendStreamMessage("Portföy risk profilimi ve yeniden dengeleme (rebalancing) alım-satım tavsiyelerini göster.");
            } else if (tab === 'rag') {
                if (ragModal) ragModal.style.display = 'flex';
                const chatCard = document.querySelector('.chat-card');
                if (chatCard) chatCard.scrollIntoView({ behavior: 'smooth' });
                sendStreamMessage("Piyasa haberlerini ve bilanço raporlarını inceleyerek son finansal gelişmeleri aktar.");
            }
        });
    });

    if (closeAssetsModal) closeAssetsModal.addEventListener('click', hideAllModals);
    if (closeRebalanceModal) closeRebalanceModal.addEventListener('click', hideAllModals);
    if (closeRagModal) closeRagModal.addEventListener('click', hideAllModals);

    [assetsModal, rebalanceModal, ragModal].forEach(modal => {
        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) hideAllModals();
            });
        }
    });
}

async function loadAssetsModal() {
    const assetsModal = document.getElementById('assetsModal');
    const tbody = document.getElementById('assetsTableBody');
    if (!assetsModal || !tbody) return;

    assetsModal.style.display = 'flex';
    tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;">Yükleniyor...</td></tr>';

    try {
        const res = await fetch('/api/portfolio/1');
        const data = await res.json();

        if (!data.holdings || data.holdings.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;">Varlık kaydı bulunamadı.</td></tr>';
            return;
        }

        tbody.innerHTML = '';
        data.holdings.forEach(h => {
            const tr = document.createElement('tr');
            const pnlClass = h.pnl >= 0 ? 'text-green' : 'text-red';
            const pnlSign = h.pnl >= 0 ? '+' : '';

            tr.innerHTML = `
                <td><strong>${h.symbol}</strong></td>
                <td>${h.name}</td>
                <td><span class="badge">${h.category}</span></td>
                <td>${h.quantity.toLocaleString('tr-TR')}</td>
                <td>₺${h.avg_buy_price.toLocaleString('tr-TR', {minimumFractionDigits: 2})}</td>
                <td>₺${h.current_price.toLocaleString('tr-TR', {minimumFractionDigits: 2})}</td>
                <td><strong>₺${h.current_value.toLocaleString('tr-TR', {minimumFractionDigits: 2})}</strong></td>
                <td class="${pnlClass}"><strong>${pnlSign}₺${h.pnl.toLocaleString('tr-TR', {minimumFractionDigits: 2})} (%${h.pnl_pct})</strong></td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) {
        console.error("Varlık yükleme hatası", err);
        tbody.innerHTML = '<tr><td colspan="8" style="text-align:center; color:var(--red);">Veri yüklenirken hata oluştu.</td></tr>';
    }
}

async function loadRebalanceModal() {
    const rebalanceModal = document.getElementById('rebalanceModal');
    const container = document.getElementById('rebalanceModalBody');
    if (!rebalanceModal || !container) return;

    rebalanceModal.style.display = 'flex';
    container.innerHTML = '<p style="text-align:center;">Risk analizi hesaplanıyor...</p>';

    try {
        const res = await fetch('/api/rebalance/1');
        const data = await res.json();

        let html = `
            <div class="rebalance-box">
                <div class="metric-card glass">
                    <div class="card-header"><span>Hesaplanan Risk Skoru</span></div>
                    <div class="metric-value">${data.risk_score} / 100 (${data.risk_profile} Profil)</div>
                </div>
        `;

        if (data.risk_warnings && data.risk_warnings.length > 0) {
            data.risk_warnings.forEach(w => {
                html += `
                    <div class="risk-alert-container">
                        <div class="risk-alert-text">${w}</div>
                        <button class="btn-action-risk trigger-modal-rebalance">
                            <span>⚡ Dengeleme Önerisi Al</span>
                        </button>
                    </div>
                `;
            });
        }

        html += `
            <h3>🎯 Hedef vs Mevcut Varlık Dağılımı</h3>
            <table class="assets-table">
                <thead>
                    <tr>
                        <th>Varlık Kategori</th>
                        <th>Mevcut Oran</th>
                        <th>Hedef Oran</th>
                        <th>Fark (%)</th>
                        <th>Durum</th>
                    </tr>
                </thead>
                <tbody>
        `;

        data.allocation_comparison.forEach(item => {
            const statusClass = item.diff_pct > 3 ? 'text-red' : (item.diff_pct < -3 ? 'text-green' : '');
            html += `
                <tr>
                    <td><strong>${item.category}</strong></td>
                    <td>%${item.current_pct}</td>
                    <td>%${item.target_pct}</td>
                    <td>%${item.diff_pct}</td>
                    <td class="${statusClass}"><strong>${item.status}</strong></td>
                </tr>
            `;
        });

        html += '</tbody></table></div>';
        container.innerHTML = html;

        // Modal içi 'Dengeleme Önerisi Al' aksiyon butonlarını bağla
        document.querySelectorAll('.trigger-modal-rebalance').forEach(btn => {
            btn.addEventListener('click', () => {
                rebalanceModal.style.display = 'none';
                const chatCard = document.querySelector('.chat-card');
                if (chatCard) chatCard.scrollIntoView({ behavior: 'smooth' });
                sendStreamMessage("Portföyü yeniden dengele ve hedef risk profiline göre alım-satım önerisi ver.");
            });
        });

    } catch (err) {
        console.error("Rebalance yükleme hatası", err);
        container.innerHTML = '<p style="color:var(--red);">Veri alınamadı.</p>';
    }
}
