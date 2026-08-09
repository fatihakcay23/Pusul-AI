#!/usr/bin/env python3
"""
Akıllı Kişisel Finans Danışmanı - Python if/else Kelime Yakalama (Keyword Matching) Yönlendiricili Multi-Agent Sistemi
- SPECIFIC_QUERY: Spesifik konu veya varlık soruları (Sadece RAG Ajanı çalışır).
- REBALANCE     : Rebalancing kelimeleri (Portföy + Risk Ajanları çalışır).
- FULL_REPORT   : Açıkça genel/detaylı rapor istekleri (3 Ajan koordineli çalışır).
- FALLBACK      : Belirsiz ifadelerde yönlendirici soru sorulur.
"""

import os
import sqlite3
import asyncio
from rag_pipeline import RAGPipeline

SYSTEM_PROMPT = (
    "Sen bir diyalog asistanısın. Kullanıcının sorusuna sadece doğrudan istenen bilgiyi vererek yanıt ver. "
    "Kullanıcı açıkça talep etmedikçe genel portföy raporunu veya uzun analizleri ekrana yazdırma."
)

class PortfolioAgent:
    """Kullanıcı verilerini, varlık bakiyelerini ve işlem geçmişini analiz eden Portföy Ajanı."""
    def __init__(self, db_path):
        self.db_path = db_path

    def analyze(self, user_id=1):
        if not os.path.exists(self.db_path):
            return {"error": "Veritabanı bulunamadı."}
            
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Kullanıcı
            cursor.execute("SELECT id, first_name, last_name, risk_tolerance FROM users WHERE id = ?", (user_id,))
            user = cursor.fetchone()
            if not user:
                return {"error": f"Kullanıcı ID {user_id} bulunamadı."}
                
            # Portföy ve Varlıklar
            query = """
                SELECT a.symbol, a.name, c.code as category_code, c.name as category_name,
                       pa.quantity, pa.average_buy_price, a.current_price,
                       (pa.quantity * pa.average_buy_price) as cost_basis,
                       (pa.quantity * a.current_price) as current_val
                FROM portfolio_assets pa
                JOIN assets a ON pa.asset_id = a.id
                JOIN asset_categories c ON a.category_id = c.id
                JOIN portfolios p ON pa.portfolio_id = p.id
                WHERE p.user_id = ?
            """
            cursor.execute(query, (user_id,))
            rows = cursor.fetchall()
            
            total_cost = sum(r[7] for r in rows)
            total_value = sum(r[8] for r in rows)
            total_pnl = total_value - total_cost
            total_pnl_pct = round((total_pnl / total_cost) * 100, 2) if total_cost > 0 else 0.0
            
            # Kategoriye Göre Dağılım
            cat_breakdown = {}
            for r in rows:
                code, cat_name, val = r[2], r[3], r[8]
                if code not in cat_breakdown:
                    cat_breakdown[code] = {"name": cat_name, "value": 0.0, "percentage": 0.0}
                cat_breakdown[code]["value"] += val
                
            for code in cat_breakdown:
                cat_breakdown[code]["percentage"] = round((cat_breakdown[code]["value"] / total_value) * 100, 1) if total_value > 0 else 0.0
                
            # Varlık Listesi
            holdings = []
            for r in rows:
                symbol, name, cat_code, cat_name, qty, avg_buy, curr_price, cost, val = r
                pnl = val - cost
                pnl_pct = round(((curr_price - avg_buy) / avg_buy) * 100, 2) if avg_buy > 0 else 0.0
                port_pct = round((val / total_value) * 100, 1) if total_value > 0 else 0.0
                holdings.append({
                    "symbol": symbol,
                    "name": name,
                    "category": cat_code,
                    "quantity": qty,
                    "avg_buy_price": avg_buy,
                    "current_price": curr_price,
                    "current_value": round(val, 2),
                    "pnl": round(pnl, 2),
                    "pnl_pct": pnl_pct,
                    "portfolio_percentage": port_pct
                })
                
            return {
                "user_id": user[0],
                "user_name": f"{user[1]} {user[2]}",
                "risk_tolerance": user[3],
                "total_cost": round(total_cost, 2),
                "total_value": round(total_value, 2),
                "total_pnl": round(total_pnl, 2),
                "total_pnl_pct": total_pnl_pct,
                "category_breakdown": cat_breakdown,
                "holdings": holdings
            }

class RiskStrategyAgent:
    """Portföy riskini değerlendiren ve yeniden dengeleme (rebalancing) önerileri sunan Risk Ajanı."""
    def __init__(self):
        self.target_allocations = {
            "LOW": {"STOCK": 20.0, "GOLD": 30.0, "FOREX": 20.0, "BOND": 30.0},
            "MEDIUM": {"STOCK": 45.0, "GOLD": 25.0, "FOREX": 20.0, "BOND": 10.0},
            "HIGH": {"STOCK": 65.0, "GOLD": 15.0, "FOREX": 15.0, "BOND": 5.0}
        }

    def evaluate(self, portfolio_summary):
        if "error" in portfolio_summary:
            return portfolio_summary
            
        risk_profile = portfolio_summary.get("risk_tolerance", "MEDIUM")
        target_alloc = self.target_allocations.get(risk_profile, self.target_allocations["MEDIUM"])
        current_breakdown = portfolio_summary.get("category_breakdown", {})
        total_val = portfolio_summary.get("total_value", 1.0)
        
        rebalancing_actions = []
        risk_warnings = []
        
        for h in portfolio_summary.get("holdings", []):
            if h["portfolio_percentage"] > 20.0 and h["category"] == "STOCK":
                risk_warnings.append(
                    f"⚠️ Yüksek Konsantrasyon Riski: **{h['symbol']}** hissesi portföyün **%{h['portfolio_percentage']}**'sini oluşturuyor."
                )

        allocation_comparison = []
        for cat_code, target_pct in target_alloc.items():
            curr_pct = current_breakdown.get(cat_code, {}).get("percentage", 0.0)
            diff_pct = round(curr_pct - target_pct, 1)
            target_amount = (target_pct / 100.0) * total_val
            curr_amount = current_breakdown.get(cat_code, {}).get("value", 0.0)
            diff_amount = round(curr_amount - target_amount, 2)
            
            status = "DENGELİ"
            if diff_pct > 3.0:
                status = "AĞIRLIK AZALT (SAT)"
                rebalancing_actions.append({
                    "category": cat_code,
                    "action": "SELL",
                    "diff_pct": diff_pct,
                    "amount_try": abs(diff_amount),
                    "recommendation": f"{cat_code} varlık grubu hedefinizin %{diff_pct} üzerinde. Yaklaşık {abs(diff_amount):,.2f} TL tutarında kâr satışı düşünülebilir."
                })
            elif diff_pct < -3.0:
                status = "AĞIRLIK ARTIR (AL)"
                rebalancing_actions.append({
                    "category": cat_code,
                    "action": "BUY",
                    "diff_pct": diff_pct,
                    "amount_try": abs(diff_amount),
                    "recommendation": f"{cat_code} varlık grubu hedefinizin %{abs(diff_pct)} altında. Yaklaşık {abs(diff_amount):,.2f} TL tutarında ek alım önerilir."
                })
                
            allocation_comparison.append({
                "category": cat_code,
                "current_pct": curr_pct,
                "target_pct": target_pct,
                "diff_pct": diff_pct,
                "status": status
            })

        risk_score = 55
        if risk_profile == "HIGH": risk_score = 78
        elif risk_profile == "LOW": risk_score = 30

        return {
            "risk_profile": risk_profile,
            "risk_score": risk_score,
            "risk_warnings": risk_warnings,
            "allocation_comparison": allocation_comparison,
            "rebalancing_actions": rebalancing_actions
        }

class MarketResearchAgent:
    """RAG pipeline kullanarak haber ve raporları inceleyen Piyasa Araştırma Ajanı."""
    def __init__(self, rag_pipeline):
        self.rag_pipeline = rag_pipeline

    def research(self, query, user_id=1, include_full_portfolio=False):
        return self.rag_pipeline.query(query, user_id=user_id, include_full_portfolio=include_full_portfolio)

class IntentClassifier:
    """Klasik Kelime Yakalama (Keyword Matching) ile Python if/else Yönlendiricisi."""
    
    SPECIFIC_KEYWORDS = ['fed', 'faiz', 'thyao', 'thy', 'garanti', 'garan', 'altın', 'dolar', 'kur', 'bilanço', 'hisse', 'ons', 'gram']
    FULL_REPORT_KEYWORDS = ['detaylı rapor', 'kapsamlı rapor', 'genel rapor', 'tam rapor', 'portföy raporu', 'portföy durumum nedir', 'tüm analiz']
    REBALANCE_KEYWORDS = ['dengele', 'rebalance', 'yeniden dengele']

    @classmethod
    def classify(cls, query_text):
        if not query_text:
            return "FALLBACK"
            
        q = query_text.lower().strip()
        
        # 1. Öncelikli Kontrol: Spesifik Konu / Varlık Soruları (Sadece RAG Ajanı)
        if any(kw in q for kw in cls.SPECIFIC_KEYWORDS):
            return "SPECIFIC_QUERY"
            
        # 2. Tam Rapor İsteği Kontrolü
        if any(kw in q for kw in cls.FULL_REPORT_KEYWORDS):
            return "FULL_REPORT"
            
        # 3. Rebalancing İsteği Kontrolü
        if any(kw in q for kw in cls.REBALANCE_KEYWORDS):
            return "REBALANCE"
            
        # 4. Varsayılan Durum (Fallback)
        return "FALLBACK"

class FinancialAdvisorOrchestrator:
    """Klasik Python if/else Yönlendiricili Multi-Agent Orkestratör."""
    def __init__(self, db_path=None):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.db_path = db_path or os.path.join(base_dir, "finance_advisor.db")
        
        self.portfolio_agent = PortfolioAgent(self.db_path)
        self.risk_agent = RiskStrategyAgent()
        self.rag_pipeline = RAGPipeline(self.db_path)
        self.market_agent = MarketResearchAgent(self.rag_pipeline)

    def process_request(self, user_query, user_id=1, force_full_report=False):
        """
        Klasik Python if/else kelime eşleştirme mantığı ile istek yönlendirmesi:
        - force_full_report=True veya FULL_REPORT_KEYWORDS varsa: 3 Ajan birden çalışır.
        - SPECIFIC_KEYWORDS varsa: SADECE Piyasa Araştırma Ajanı (RAG) çalışır, kısa ve net cevap verir.
        - REBALANCE_KEYWORDS varsa: Portföy ve Risk Ajanları çalışır.
        - Hiçbiri uymuyorsa (FALLBACK): Kullanıcıya yönlendirici soru sorar.
        """
        if force_full_report:
            return self.generate_full_report(user_query, user_id)

        intent = IntentClassifier.classify(user_query)
        
        if intent == "SPECIFIC_QUERY":
            # Spesifik Soru Senaryosu: Sadece Piyasa Araştırma Ajanı (RAG) çalışır
            return self.market_agent.research(user_query, user_id=user_id, include_full_portfolio=False)
            
        elif intent == "REBALANCE":
            # Rebalancing & Risk Senaryosu: Portföy + Risk Ajanları çalışır
            port = self.portfolio_agent.analyze(user_id)
            risk = self.risk_agent.evaluate(port)
            
            res = []
            res.append(f"⚡ **Portföy Risk & Rebalancing Analizi (Kullanıcı: {port.get('user_name')})**\n")
            res.append(f"• **Hesaplanan Risk Skoru:** {risk.get('risk_score')}/100 ({risk.get('risk_profile')} Risk Modeli)")
            
            if risk.get("risk_warnings"):
                for w in risk.get("risk_warnings"):
                    res.append(f"• {w}")
                    
            res.append("\n🎯 **Rebalancing Alım-Satım Tavsiyeleri:**")
            if risk.get("rebalancing_actions"):
                for act in risk.get("rebalancing_actions"):
                    res.append(f"  └ [{act['action']}] {act['recommendation']}")
            else:
                res.append("  └ Portföy varlık dağılımınız hedef risk profilinizle tam uyumludur.")
                
            return "\n".join(res)
            
        elif intent == "FULL_REPORT":
            # Tam Rapor Senaryosu: 3 Ajan Birden Çalışır
            return self.generate_full_report(user_query, user_id)
            
        else: # FALLBACK
            # Varsayılan Durum: Yönlendirici soru
            return "Size portföy raporunuzu mu sunmamı istersiniz, yoksa spesifik bir piyasa haberi mi arıyorsunuz?"

    def generate_full_report(self, user_query="Genel Portföy ve Risk Değerlendirmesi", user_id=1):
        """Bütünleşik 3-Ajanlı Danışmanlık Raporu Oluşturur."""
        port = self.portfolio_agent.analyze(user_id)
        risk = self.risk_agent.evaluate(port)
        market = self.market_agent.research(user_query, user_id, include_full_portfolio=True)
        
        report = []
        report.append("════════════════════════════════════════════════════════════════")
        report.append("          🏛️ PUSUL AI BÜTÜNLEŞİK FİNANS DANIŞMANI RAPORU")
        report.append("════════════════════════════════════════════════════════════════\n")
        
        report.append(f"👤 **Yatırımcı:** {port.get('user_name')} | **Risk Toleransı:** {port.get('risk_tolerance')}")
        report.append(f"💰 **Toplam Portföy Değeri:** {port.get('total_value'):,.2f} TL (Kâr/Zarar: %{port.get('total_pnl_pct'):+.2f})\n")
        
        report.append("📊 **1. VARLIK DAĞILIMI VE HESAPLAR (Portföy Ajanı):**")
        for cat, data in port.get("category_breakdown", {}).items():
            report.append(f"  • {data['name']} ({cat}): %{data['percentage']} ({data['value']:,.2f} TL)")
        report.append("")
        
        report.append("🎯 **2. RİSK VE REBALANCING STRATEJİSİ (Risk/Strateji Ajanı):**")
        report.append(f"  • Risk Skoru: {risk.get('risk_score')}/100")
        if risk.get("risk_warnings"):
            for w in risk.get("risk_warnings"):
                report.append(f"  {w}")
        else:
            report.append("  • Portföyünüzde belirgin bir konsantrasyon riski saptanmadı.")
            
        report.append("  • **Yeniden Dengeleme Önerileri:**")
        if risk.get("rebalancing_actions"):
            for act in risk.get("rebalancing_actions"):
                report.append(f"    - [{act['action']}] {act['recommendation']}")
        else:
            report.append("    - Portföy dağılımınız hedef risk profilinizle tam uyumludur.")
        report.append("")
        
        report.append("📰 **3. PİYASA ARAŞTIRMASI VE RAG ANALİZİ (Piyasa Araştırma Ajanı):**")
        report.append(market)
        
        return "\n".join(report)

if __name__ == "__main__":
    orchestrator = FinancialAdvisorOrchestrator()
    print("--- 1. Spesifik Soru ---")
    print(orchestrator.process_request("thyao kârı nasıl?"))
    print("\n--- 2. Rapor İsteği ---")
    print(orchestrator.process_request("detaylı rapor ver"))
    print("\n--- 3. Fallback ---")
    print(orchestrator.process_request("merhaba günaydın"))
