#!/usr/bin/env python3
"""
Akıllı Kişisel Finans Danışmanı - Uçtan Uca Sistem Test Betiği (Demo)
- SQL Veritabanı durumunu doğrular.
- Vektör DB ve RAG Pipeline arama testlerini çalıştırır.
- 3 Koordineli AI Ajanının (Portföy, Risk/Strateji, Piyasa Araştırma) ortak çalışmasını gösterir.
- MCP Server JSON-RPC araç çağrısını simüle eder.
"""

import os
import sqlite3
import json
import asyncio

from agents import FinancialAdvisorOrchestrator
from vector_store import VectorStore
from mcp_server import MCPServer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "finance_advisor.db")
DOCS_DIR = os.path.join(BASE_DIR, "sample_documents")

def test_sql_db():
    print("==================================================================")
    print("1. SQL VERİTABANI KONTROLÜ (finance_advisor.db)")
    print("==================================================================")
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM assets")
        asset_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM portfolio_assets")
        pa_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM transactions")
        tx_count = cursor.fetchone()[0]
        
        print(f"✅ Kullanıcı Sayısı    : {user_count}")
        print(f"✅ Varlık Sayısı       : {asset_count}")
        print(f"✅ Portföy Varlık Kaydı: {pa_count}")
        print(f"✅ İşlem Geçmişi Kaydı : {tx_count}")

def test_vector_store():
    print("\n==================================================================")
    print("2. VEKTÖR VERİTABANI VE RAG İNDEKSLERİ (sample_documents/)")
    print("==================================================================")
    store = VectorStore()
    store.load_directory(DOCS_DIR)
    
    test_query = "THYAO çeyrek kâr ve yolcu hedefi"
    hits = store.search(test_query, top_k=2)
    print(f"🔍 Test Sorgusu: '{test_query}'")
    for i, hit in enumerate(hits, 1):
        print(f"  [{i}] Doc: {hit['doc_title']} (Skor: {hit['score']}) -> {hit['text'][:100]}...")

def test_agents():
    print("\n==================================================================")
    print("3. AKILLI YÖNLENDİRİCİ (AGENT ROUTER) VE İNTENT TESTİ")
    print("==================================================================")
    orchestrator = FinancialAdvisorOrchestrator(DB_PATH)
    
    print("\n--- A. Spesifik Soru Senaryosu (Sadece RAG Ajanı) ---")
    print(orchestrator.process_request("THYAO kârı nasıl?", user_id=1))
    
    print("\n--- B. Tam Rapor Senaryosu (3 Ajan Koordineli) ---")
    print(orchestrator.process_request("Detaylı Rapor Oluştur", user_id=1))

def test_mcp_server():
    print("\n==================================================================")
    print("4. MODEL CONTEXT PROTOCOL (MCP) SERVER TESTİ")
    print("==================================================================")
    mcp = MCPServer()
    
    # 1. MCP Tools List
    tools_resp = mcp.handle_tools_list(request_id=1)
    print(f"✅ Tanımlı MCP Araçları ({len(tools_resp['result']['tools'])} Adet):")
    for t in tools_resp['result']['tools']:
        print(f"  • {t['name']}: {t['description']}")
        
    # 2. MCP Call Tool Execution
    call_resp = mcp.handle_tools_call(
        request_id=2, 
        name="get_portfolio_summary", 
        arguments={"user_id": 1}
    )
    data = json.loads(call_resp['result']['content'][0]['text'])
    print(f"\n✅ MCP 'get_portfolio_summary' Çağrı Yanıtı:")
    print(f"  Kullanıcı: {data['user_name']} | Portföy Değeri: {data['total_value']:,.2f} TL | Kâr/Zarar: %{data['total_pnl_pct']}")

def main():
    test_sql_db()
    test_vector_store()
    test_agents()
    test_mcp_server()
    print("\n🎉 TÜM SİSTEM BİLEŞENLERİ BAŞARIYLA DOĞRULANDI!")

if __name__ == "__main__":
    main()
