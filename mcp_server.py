#!/usr/bin/env python3
"""
Akıllı Kişisel Finans Danışmanı - Model Context Protocol (MCP) Server
Bu modül, finansal ajanlarımızı ve veri kaynaklarımızı standart JSON-RPC 2.0 (stdio) MCP protokolü üzerinden
dış istemcilere (Claude Desktop, IDE'ler veya diğer AI istemcileri) sunar.
"""

import sys
import os
import json
from agents import FinancialAdvisorOrchestrator, PortfolioAgent, RiskStrategyAgent, MarketResearchAgent
from rag_pipeline import RAGPipeline

class MCPServer:
    def __init__(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.db_path = os.path.join(base_dir, "finance_advisor.db")
        
        self.portfolio_agent = PortfolioAgent(self.db_path)
        self.risk_agent = RiskStrategyAgent()
        self.rag_pipeline = RAGPipeline(self.db_path)
        self.market_agent = MarketResearchAgent(self.rag_pipeline)
        self.orchestrator = FinancialAdvisorOrchestrator(self.db_path)

    def handle_initialize(self, request_id):
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {},
                    "resources": {}
                },
                "serverInfo": {
                    "name": "smart-finance-advisor-mcp",
                    "version": "1.0.0"
                }
            }
        }

    def handle_tools_list(self, request_id):
        tools = [
            {
                "name": "get_portfolio_summary",
                "description": "Kullanıcının canlı portföy özetini, varlık bakiyelerini ve kâr/zarar durumunu döner.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "integer", "description": "Kullanıcı ID (Varsayılan: 1)"}
                    }
                }
            },
            {
                "name": "assess_portfolio_risk",
                "description": "Portföyün risk skorunu, konsantrasyon risklerini ve yeniden dengeleme (rebalancing) tavsiyelerini hesaplar.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "integer", "description": "Kullanıcı ID (Varsayılan: 1)"}
                    }
                }
            },
            {
                "name": "search_financial_news",
                "description": "Vektör veritabanından bilanço, finansal haber ve piyasa analizi araması yapar.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Aranacak finansal konu veya şirket (örn: THYAO, Altın, Fed)"}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "get_advisor_recommendation",
                "description": "3 AI ajanını birlikte çalıştırarak kullanıcıya özel bütünleşik finansal danışmanlık yanıtı üretir.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "integer", "description": "Kullanıcı ID (Varsayılan: 1)"},
                        "query": {"type": "string", "description": "Kullanıcının finansal sorusu"}
                    }
                }
            }
        ]
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {"tools": tools}
        }

    def handle_tools_call(self, request_id, name, arguments):
        user_id = arguments.get("user_id", 1)
        query = arguments.get("query", "Genel Değerlendirme")

        try:
            if name == "get_portfolio_summary":
                data = self.portfolio_agent.analyze(user_id)
                content = json.dumps(data, ensure_ascii=False, indent=2)

            elif name == "assess_portfolio_risk":
                port = self.portfolio_agent.analyze(user_id)
                data = self.risk_agent.evaluate(port)
                content = json.dumps(data, ensure_ascii=False, indent=2)

            elif name == "search_financial_news":
                content = self.market_agent.research(query, user_id)

            elif name == "get_advisor_recommendation":
                content = self.orchestrator.generate_full_report(query, user_id)

            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32601, "message": f"Bilinmeyen araç: {name}"}
                }

            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [
                        {"type": "text", "text": content}
                    ]
                }
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32603, "message": f"Araç çalıştırma hatası: {str(e)}"}
            }

    def handle_resources_list(self, request_id):
        resources = [
            {
                "uri": "portfolio://1",
                "name": "Kullanıcı 1 Portföy Kaynağı",
                "mimeType": "application/json"
            },
            {
                "uri": "market://documents",
                "name": "Finansal Raporlar ve Haber İndeksi",
                "mimeType": "text/plain"
            }
        ]
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {"resources": resources}
        }

    def run(self):
        """Stdio JSON-RPC Dinleyici Döngüsü"""
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                request = json.loads(line)
                req_id = request.get("id")
                method = request.get("method")
                params = request.get("params", {})

                if method == "initialize":
                    response = self.handle_initialize(req_id)
                elif method == "tools/list":
                    response = self.handle_tools_list(req_id)
                elif method == "tools/call":
                    name = params.get("name")
                    args = params.get("arguments", {})
                    response = self.handle_tools_call(req_id, name, args)
                elif method == "resources/list":
                    response = self.handle_resources_list(req_id)
                elif method == "notifications/initialized":
                    continue # Belli bildirim yanıtı gerekmez
                else:
                    response = {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "error": {"code": -32601, "message": f"Bilinmeyen metod: {method}"}
                    }

                sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
                sys.stdout.flush()

            except Exception as e:
                err_resp = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32700, "message": f"Ayrıştırma hatası: {str(e)}"}
                }
                sys.stdout.write(json.dumps(err_resp) + "\n")
                sys.stdout.flush()

if __name__ == "__main__":
    server = MCPServer()
    server.run()
