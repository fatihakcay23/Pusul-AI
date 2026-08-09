#!/usr/bin/env python3
"""
Pusul AI - Backend API & Agent Orchestration Sunucusu
- İstemciden gelen istekleri alır, 3 AI Ajanını (Portföy, Risk/Strateji, Piyasa Araştırma) eş zamanlı (parallel asyncio) çalıştırır.
- Klasik Python if/else Kelime Eşleştirme (Keyword Matching) mantığı ile istek yönlendirir.
- Yanıtları canlı akış (Server-Sent Events - SSE Streaming Response) biçiminde istemciye aktarır.
- Dashboard için statik web dosyalarını (static/index.html, styles.css, app.js) sunar.
"""

import os
import json
import time
import asyncio
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from urllib.parse import parse_qs, urlparse

from agents import FinancialAdvisorOrchestrator, PortfolioAgent, RiskStrategyAgent, MarketResearchAgent
from rag_pipeline import RAGPipeline

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
DB_PATH = os.path.join(BASE_DIR, "finance_advisor.db")

orchestrator = FinancialAdvisorOrchestrator(DB_PATH)
portfolio_agent = PortfolioAgent(DB_PATH)
risk_agent = RiskStrategyAgent()
rag_pipeline = RAGPipeline(DB_PATH)
market_agent = MarketResearchAgent(rag_pipeline)

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Eşzamanlı (multi-threaded) HTTP Sunucusu."""
    daemon_threads = True

class APIRequestHandler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        """Özel log yazımı"""
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {self.address_string()} - {format % args}")

    def send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query_params = parse_qs(parsed.query)

        # 1. API: Portföy Özeti
        if path.startswith("/api/portfolio"):
            user_id = 1
            parts = path.strip("/").split("/")
            if len(parts) >= 3 and parts[2].isdigit():
                user_id = int(parts[2])
                
            data = portfolio_agent.analyze(user_id)
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
            return

        # 2. API: Rebalancing Önerileri
        if path.startswith("/api/rebalance"):
            user_id = 1
            parts = path.strip("/").split("/")
            if len(parts) >= 3 and parts[2].isdigit():
                user_id = int(parts[2])
                
            port = portfolio_agent.analyze(user_id)
            data = risk_agent.evaluate(port)
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
            return

        # 3. API: Live Streaming Chat (SSE - Server-Sent Events) GET endpoint
        if path == "/api/chat/stream":
            user_query = query_params.get("q", [""])[0]
            user_id = int(query_params.get("user_id", [1])[0])
            force_full = query_params.get("force_full", ["false"])[0].lower() == "true"
            self.handle_sse_stream(user_query, user_id, force_full=force_full)
            return

        # 4. Statik Dosyaları Sunma (Web UI / Dashboard)
        if path == "/" or path == "/index.html":
            file_path = os.path.join(STATIC_DIR, "index.html")
            mime_type = "text/html"
        else:
            rel_path = path.lstrip("/")
            if rel_path.startswith("static/"):
                rel_path = rel_path.replace("static/", "", 1)
            file_path = os.path.join(STATIC_DIR, rel_path)
            if rel_path.endswith(".css"):
                mime_type = "text/css"
            elif rel_path.endswith(".js"):
                mime_type = "application/javascript"
            elif rel_path.endswith(".json"):
                mime_type = "application/json"
            elif rel_path.endswith(".jpg") or rel_path.endswith(".jpeg"):
                mime_type = "image/jpeg"
            elif rel_path.endswith(".png"):
                mime_type = "image/png"
            else:
                mime_type = "text/plain"

        if os.path.exists(file_path) and os.path.isfile(file_path):
            self.send_response(200)
            self.send_header("Content-Type", f"{mime_type}")
            self.send_cors_headers()
            self.end_headers()
            with open(file_path, "rb") as f:
                self.wfile.write(f.read())
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"404 - Not Found")

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
        try:
            req_data = json.loads(body)
        except Exception:
            req_data = {}

        user_query = req_data.get("query", "")
        user_id = req_data.get("user_id", 1)
        force_full = req_data.get("force_full", False)

        # Chat Standard Post
        if path == "/api/chat":
            response_text = orchestrator.process_request(user_query, user_id, force_full_report=force_full)
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({"response": response_text}, ensure_ascii=False).encode("utf-8"))
            return

        # Chat Streaming SSE Post
        if path == "/api/chat/stream":
            self.handle_sse_stream(user_query, user_id, force_full=force_full)
            return

        self.send_response(404)
        self.end_headers()

    def handle_sse_stream(self, user_query, user_id, force_full=False):
        """Server-Sent Events (SSE) ile canlı kelime/chunk akış yanıtı hazırlar."""
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_cors_headers()
        self.end_headers()

        # Klasik Python if/else Keyword Router Yönlendirme Çıktısı
        full_text = orchestrator.process_request(user_query, user_id, force_full_report=force_full)
        
        # Kelime kelime canlı akış gönderme (Streaming response simulation)
        paragraphs = full_text.split("\n")
        for para in paragraphs:
            words = para.split(" ")
            chunk_buf = ""
            for i, word in enumerate(words):
                chunk_buf += word + (" " if i < len(words)-1 else "")
                if len(chunk_buf) >= 15 or i == len(words)-1:
                    evt_data = json.dumps({"content": chunk_buf}, ensure_ascii=False)
                    self.wfile.write(f"data: {evt_data}\n\n".encode("utf-8"))
                    self.wfile.flush()
                    chunk_buf = ""
                    time.sleep(0.04) # Akıcı canlı yazma efekti
            newline_data = json.dumps({"content": "\n"}, ensure_ascii=False)
            self.wfile.write(f"data: {newline_data}\n\n".encode("utf-8"))
            self.wfile.flush()

        # Akış Sonu Bildirimi
        self.wfile.write(f"data: {json.dumps({'event': 'end'}, ensure_ascii=False)}\n\n".encode("utf-8"))
        self.wfile.flush()

def run_server(port=8080):
    os.makedirs(STATIC_DIR, exist_ok=True)
    server_address = ("", port)
    httpd = ThreadedHTTPServer(server_address, APIRequestHandler)
    print(f"🚀 Pusul AI Backend API & Dashboard Çalışıyor: http://localhost:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Sunucu durduruldu.")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    run_server(port)
