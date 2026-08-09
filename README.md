# Akıllı Kişisel Finans Danışmanı (Smart Personal Finance Advisor)

Akıllı Kişisel Finans Danışmanı; ilişkisel SQL veritabanı, sentetik veri üretici, finansal haber & bilanço RAG (Retrieval-Augmented Generation) altyapısı, 3 koordineli AI ajanı (Portföy, Risk/Strateji, Piyasa Araştırma), Model Context Protocol (MCP) Server entegrasyonu ve canlı akışlı (SSE Streaming Response) web dashboard'undan oluşan bütünleşik bir yapay zeka sistemidir.

Proje Dizini: `/Users/fatihakcay/.gemini/antigravity/scratch/smart_personal_finance`

---

## 🏛️ Mimari Mimarisi & Bileşenler

```
                                +----------------------------------+
                                |    Web Dashboard UI (static/)    |
                                | - Allocation & Trend Charts      |
                                | - Rebalance & Report Buttons     |
                                | - Live Streaming Chatbot (SSE)   |
                                +----------------+-----------------+
                                                 | (HTTP REST & SSE)
                                                 v
                                +----------------------------------+
                                |  Backend API & Orchestrator      |
                                |  (api_server.py)                 |
                                +--------+----------------+--------+
                                         |                |
                       +-----------------+                +------------------+
                       | MCP Server                                          |
                       | (mcp_server.py)                                     v
                       +-----------------+                        +--------------------+
                                                                  |  Orchestrator      |
                                                                  +---------+----------+
                                                                            |
                   +--------------------------------------------------------+----------------------------------------------------+
                   |                                                        |                                                    |
                   v                                                        v                                                    v
     +---------------------------+                            +---------------------------+                        +---------------------------+
     |      Portföy Ajanı        |                            |   Risk/Strateji Ajanı     |                        |  Piyasa Araştırma Ajanı   |
     |     (PortfolioAgent)      |                            |    (RiskStrategyAgent)    |                        |   (MarketResearchAgent)   |
     | - Varlık & Bakiye Analizi |                            | - Risk Skoru & Volatilite |                        | - RAG Finansal Haber/     |
     | - Kâr/Zarar Hesaplama     |                            | - Rebalancing Önerileri   |                        |   Bilanço Arama           |
     +-------------+-------------+                            +-------------+-------------+                        +-------------+-------------+
                   |                                                        |                                                    |
                   +--------------------------------+-----------------------+                                                    |
                                                    |                                                                            |
                                                    v                                                                            v
                                    +-------------------------------+                                          +-------------------+
                                    |  SQL DB (finance_advisor.db)  |                                          | Vector DB & RAG   |
                                    +-------------------------------+                                          +-------------------+
```

---

## 📁 Proje Dosya Yapısı

- `schema.sql`: SQL Veritabanı DDL Şeması (`users`, `assets`, `portfolios`, `portfolio_assets`, `transactions`, `price_history`).
- `generate_data.py`: Gerçekçi Türkçe kullanıcı ve finansal veriler üreten sentetik veri üreticisi.
- `sample_documents/`: THYAO 3. Çeyrek Bilanço Raporu, Garanti BBVA Haberleri, Altın Analizi ve Fed Kararı metinleri.
- `vector_store.py`: Metin parçalama (chunking), embedding ve kosinüs benzerliği ile arama yapan Vektör Veritabanı.
- `rag_pipeline.py`: Vektör arama sonuçları ile SQL canlı portföy verisini harmanlayan RAG motoru.
- `agents.py`: 3 Koordineli AI Ajanı (`PortfolioAgent`, `RiskStrategyAgent`, `MarketResearchAgent`) ve `FinancialAdvisorOrchestrator`.
- `mcp_server.py`: Model Context Protocol (MCP) JSON-RPC stdio sunucusu entegrasyonu.
- `api_server.py`: Async paralel ajan çalıştırma, REST endpoint'leri, SSE Canlı Akış Yanıtı (Streaming) ve Statik Web Dashboard Sunucusu.
- `static/`:
  - `index.html`: Premium Dark-Mode Glassmorphism Finansal Dashboard Arayüzü.
  - `styles.css`: CSS Stilleri ve Responsive Düzen.
  - `app.js`: Chart.js Varlık & Trend Grafikleri, Buton Aksiyonları ve SSE Live Stream Chatbot Mantığı.
- `demo.py`: Uçtan uca sistem testi.

---

## 🚀 Hızlı Başlangıç & Çalıştırma

### 1. Sentetik Veritabanı ve Finansal Dokümanları Oluşturun
```bash
/usr/bin/python3 generate_data.py
```

### 2. Uçtan Uca Sistem Testini Çalıştırın
```bash
/usr/bin/python3 demo.py
```

### 3. Backend API & Web Dashboard Sunucusunu Başlatın
```bash
/usr/bin/python3 api_server.py
```
Sunucu çalıştıktan sonra tarayıcınızda açın:
👉 **[http://localhost:8080](http://localhost:8080)**

---

## 🔌 MCP (Model Context Protocol) Sunucu Yapılandırması

External LLM istemcileri (örn. Claude Desktop) için `mcp_server.py` aşağıdaki araçları (tools) ve kaynakları (resources) sunar:

- **Tools**:
  - `get_portfolio_summary`: Kullanıcının canlı portföy özetini döner.
  - `assess_portfolio_risk`: Risk skorunu ve rebalancing önerilerini sunar.
  - `search_financial_news`: RAG ile doküman araması yapar.
  - `get_advisor_recommendation`: 3 ajanın ortak raporunu üretir.
- **Resources**:
  - `portfolio://1`
  - `market://documents`

Claude Desktop `claude_desktop_config.json` örneği:
```json
{
  "mcpServers": {
    "smart-finance-advisor": {
      "command": "/usr/bin/python3",
      "args": ["/Users/fatihakcay/.gemini/antigravity/scratch/smart_personal_finance/mcp_server.py"]
    }
  }
}
```
