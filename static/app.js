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
                    labels: { color: '#94a3b8', font: { size: 12, family: 'Inter' }, padding: 16 }
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

    // 2. Portfolio Performance Line Chart (30 Days)
    const ctxPerformance = document.getElementById('performanceChart').getContext('2d');
    
    // Generate dummy 30-day data showing an uptrend
    const labels = Array.from({length: 30}, (_, i) => `Gün ${i+1}`);
    let startVal = 460000;
    const dataPoints = labels.map(() => {
        startVal += (Math.random() * 3000) - 500;
        return startVal;
    });

    // Ensure the last point matches current portfolio value
    dataPoints[29] = 501315;

    // Gradient fill for the line chart
    let gradient = ctxPerformance.createLinearGradient(0, 0, 0, 300);
    gradient.addColorStop(0, 'rgba(0, 145, 218, 0.4)');
    gradient.addColorStop(1, 'rgba(0, 145, 218, 0.0)');

    performanceChart = new Chart(ctxPerformance, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Portföy Değeri (TL)',
                data: dataPoints,
                borderColor: '#0091da',
                backgroundColor: gradient,
                borderWidth: 3,
                pointRadius: 0,
                pointHoverRadius: 6,
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            interaction: { intersect: false, mode: 'index' },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { color: '#94a3b8', font: { size: 11 }, maxTicksLimit: 6 }
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
    const actionBtns = document.querySelectorAll('.action-btn');
    actionBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const action = btn.getAttribute('data-action');
            if (action === 'rebalance') {
                sendStreamMessage("Portföy risk profilimi ve yeniden dengeleme önerilerini göster.");
            } else if (action === 'report') {
                sendStreamMessage("Detaylı Rapor Oluştur.", true);
            }
            // Scroll to chat
            document.querySelector('.chat-section').scrollIntoView({ behavior: 'smooth' });
        });
    });
}

function initNavTabs() {
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', () => {
            // Remove active class from all
            navItems.forEach(nav => nav.classList.remove('active'));
            // Add to clicked
            item.classList.add('active');
            
            // Trigger chat behavior based on tab
            const target = item.getAttribute('data-target');
            let query = "";
            if (target === 'assets') query = "Güncel varlık dağılımımı ve en çok kâr getiren hisselerimi listele.";
            if (target === 'rebalance') query = "Mevcut risklerimi göster ve portföy dengeleme (rebalancing) tavsiyesinde bulun.";
            if (target === 'rag') query = "Şu anki piyasa durumu, faiz oranları ve hisse senedi piyasasına yönelik en son analiz raporlarını özetle.";
            
            if (query) {
                document.querySelector('.chat-section').scrollIntoView({ behavior: 'smooth' });
                sendStreamMessage(query);
            }
        });
    });
}

// ---- CHATBOT SSE LOGIC ----
function initChat() {
    const sendBtn = document.getElementById('send-btn');
    const input = document.getElementById('chat-input');
    
    sendBtn.addEventListener('click', () => {
        if (input.value.trim() !== '') {
            sendStreamMessage(input.value);
            input.value = '';
        }
    });
    
    input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && input.value.trim() !== '') {
            sendStreamMessage(input.value);
            input.value = '';
        }
    });
}

function appendMessage(text, type, isHtml = false) {
    const chatMessages = document.getElementById('chat-messages');
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${type}`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    if (isHtml) {
        contentDiv.innerHTML = text;
    } else {
        contentDiv.textContent = text;
    }
    
    msgDiv.appendChild(contentDiv);
    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return contentDiv;
}

function sendStreamMessage(query, forceFull = false) {
    // 1. Add user message to UI
    appendMessage(query, 'user');
    
    // 2. Add empty system message for typing effect
    const systemContentDiv = appendMessage("", 'system');
    
    // 3. Connect to SSE backend
    const encodedQuery = encodeURIComponent(query);
    const url = `/api/chat/stream?q=${encodedQuery}&user_id=1&force_full=${forceFull}`;
    
    const eventSource = new EventSource(url);
    let fullResponse = "";
    
    eventSource.onmessage = function(event) {
        const data = JSON.parse(event.data);
        
        if (data.event === "end") {
            eventSource.close();
        } else if (data.content) {
            fullResponse += data.content;
            
            // Basic formatting for markdown-like text
            let formattedHtml = fullResponse
                .replace(/\n/g, '<br>')
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                .replace(/•/g, '<span style="color:var(--primary)">•</span>');
                
            systemContentDiv.innerHTML = formattedHtml;
            document.getElementById('chat-messages').scrollTop = document.getElementById('chat-messages').scrollHeight;
        }
    };
    
    eventSource.onerror = function() {
        eventSource.close();
        systemContentDiv.innerHTML += "<br><br><em>[Bağlantı hatası oluştu, yanıt kesilmiş olabilir.]</em>";
    };
}
