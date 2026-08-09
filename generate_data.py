#!/usr/bin/env python3
"""
Akıllı Kişisel Finans Danışmanı - Sentetik Veri Üretici (Dummy Data Generator)
Bu betik:
1. SQLite veritabanını (finance_advisor.db) schema.sql ile oluşturur.
2. Varlık sınıflarını (Hisse, Altın, Döviz, Tahvil) ve varlıkları tanımlar.
3. Gerçekçi kullanıcılar, portföyler, varlık bakiyeleri ve geçmiş işlemler oluşturur.
4. Zamansal fiyat geçmişi (price_history) verilerini üretir.
5. Vektör DB & RAG sistemi için sample_documents/ altında finansal haber ve bilanço metinleri hazırlar.
"""

import os
import sqlite3
import random
import json
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "finance_advisor.db")
SCHEMA_PATH = os.path.join(BASE_DIR, "schema.sql")
DOCS_DIR = os.path.join(BASE_DIR, "sample_documents")

def init_db():
    print("📌 Veritabanı şeması yükleniyor...")
    with sqlite3.connect(DB_PATH) as conn:
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            conn.executescript(f.read())
        conn.commit()
    print("✅ Veritabanı başarıyla ilklendirildi:", DB_PATH)

def populate_categories_and_assets(conn):
    cursor = conn.cursor()
    
    # 1. Kategoriler
    categories = [
        ('STOCK', 'Hisse Senedi', 'BIST ve küresel hisse senetleri'),
        ('GOLD', 'Altın & Kıymetli Madenler', 'Gram, çeyrek, ons altın ve gümüş'),
        ('FOREX', 'Döviz', 'Yabancı para birimleri (USD, EUR, GBP)'),
        ('BOND', 'Tahvil & Bono', 'Devlet ve özel sektör borçlanma araçları')
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO asset_categories (code, name, description) VALUES (?, ?, ?)",
        categories
    )
    
    # Kategori ID haritası
    cursor.execute("SELECT code, id FROM asset_categories")
    cat_map = dict(cursor.fetchall())
    
    # 2. Varlıklar ve Güncel Fiyatları
    assets = [
        # Hisse Senetleri
        (cat_map['STOCK'], 'THYAO', 'Türk Hava Yolları A.O.', 'TRY', 310.50, 2.45),
        (cat_map['STOCK'], 'GARAN', 'Garanti BBVA', 'TRY', 112.00, 1.15),
        (cat_map['STOCK'], 'EREGL', 'Eğreyli Demir Çelik', 'TRY', 52.40, -0.85),
        (cat_map['STOCK'], 'ASELS', 'Aselsan Elektronik', 'TRY', 64.20, 3.10),
        (cat_map['STOCK'], 'KCHOL', 'Koç Holding', 'TRY', 220.00, 0.45),
        
        # Altın & Kıymetli Madenler
        (cat_map['GOLD'], 'GRAM_ALTIN', 'Gram Altın (24 Ayar)', 'TRY', 2540.00, 0.75),
        (cat_map['GOLD'], 'CEYREK_ALTIN', 'Çeyrek Altın', 'TRY', 4150.00, 0.80),
        (cat_map['GOLD'], 'ONS_ALTIN', 'Ons Altın', 'USD', 2430.00, 0.40),
        
        # Döviz
        (cat_map['FOREX'], 'USD/TRY', 'ABD Doları / Türk Lirası', 'TRY', 33.45, 0.12),
        (cat_map['FOREX'], 'EUR/TRY', 'Euro / Türk Lirası', 'TRY', 36.60, 0.25),
        (cat_map['FOREX'], 'GBP/TRY', 'İngiliz Sterlini / Türk Lirası', 'TRY', 42.80, 0.18),
        
        # Tahvil & Bono
        (cat_map['BOND'], 'TR2Y_BOND', 'Devlet Tahvili (2 Yıllık)', 'TRY', 105.20, 0.05),
        (cat_map['BOND'], 'TR10Y_BOND', 'Devlet Tahvili (10 Yıllık)', 'TRY', 98.40, -0.10)
    ]
    
    cursor.executemany(
        """INSERT OR IGNORE INTO assets 
           (category_id, symbol, name, currency, current_price, daily_change_pct) 
           VALUES (?, ?, ?, ?, ?, ?)""",
        assets
    )
    conn.commit()
    print("✅ Varlık kategorileri ve güncel fiyatlar eklendi.")

def populate_users_and_portfolios(conn):
    cursor = conn.cursor()
    
    # Kullanıcılar
    users = [
        ('Mehmet', 'Yılmaz', 'mehmet.yilmaz@example.com', 'hash_secret_123', 'MEDIUM', 85000.0),
        ('Ayşe', 'Kaya', 'ayse.kaya@example.com', 'hash_secret_456', 'HIGH', 120000.0),
        ('Ahmet', 'Demir', 'ahmet.demir@example.com', 'hash_secret_789', 'LOW', 65000.0)
    ]
    cursor.executemany(
        """INSERT OR IGNORE INTO users 
           (first_name, last_name, email, password_hash, risk_tolerance, monthly_income) 
           VALUES (?, ?, ?, ?, ?, ?)""",
        users
    )
    
    # Mehmet Yılmaz (User 1) için Ana Portföy
    cursor.execute("SELECT id FROM users WHERE email = 'mehmet.yilmaz@example.com'")
    user_id = cursor.fetchone()[0]
    
    cursor.execute(
        "INSERT INTO portfolios (user_id, name, description) VALUES (?, ?, ?)",
        (user_id, 'Ana Yatırım Portföyü', 'Hisse, Altın, Döviz ve Tahvil içeren dengeli portföy')
    )
    portfolio_id = cursor.lastrowid
    
    # Varlık ID haritası
    cursor.execute("SELECT symbol, id, current_price FROM assets")
    asset_info = {row[0]: {'id': row[1], 'price': row[2]} for row in cursor.fetchall()}
    
    # Kullanıcının Hedef Dağılımına Uygun Varlık Bakiyeleri
    # Toplam Hedef Portföy Değeri: ~500.000 TL
    # Hisse (~%45): THYAO, GARAN, ASELS -> 225.000 TL
    # Altın (~%25): GRAM_ALTIN -> 125.000 TL
    # Döviz (~%20): USD/TRY, EUR/TRY -> 100.000 TL
    # Tahvil (~%10): TR2Y_BOND -> 50.000 TL
    
    portfolio_holdings = [
        # (symbol, quantity, avg_buy_price)
        ('THYAO', 350.0, 280.00),      # ~108,675 TL
        ('GARAN', 650.0, 95.00),       # ~72,800 TL
        ('ASELS', 700.0, 55.00),       # ~44,940 TL  (Toplam Hisse: ~226,415 TL - %45.2)
        
        ('GRAM_ALTIN', 49.0, 2400.00),  # ~124,460 TL (Altın: %24.8)
        
        ('USD/TRY', 1800.0, 31.50),    # ~60,210 TL
        ('EUR/TRY', 1100.0, 34.80),    # ~40,260 TL  (Toplam Döviz: ~100,470 TL - %20.1)
        
        ('TR2Y_BOND', 475.0, 102.00)   # ~49,970 TL  (Tahvil: %9.9)
    ]
    
    for symbol, qty, avg_price in portfolio_holdings:
        asset_id = asset_info[symbol]['id']
        cursor.execute(
            """INSERT INTO portfolio_assets (portfolio_id, asset_id, quantity, average_buy_price)
               VALUES (?, ?, ?, ?)""",
            (portfolio_id, asset_id, qty, avg_price)
        )
        
        # Geçmiş Alım İşlemleri (Transactions) Üretimi
        now = datetime.now()
        buy_date = (now - timedelta(days=random.randint(15, 60))).strftime("%Y-%m-%d %H:%M:%S")
        total_amount = qty * avg_price
        fee = total_amount * 0.0015 # %0.15 komisyon
        
        cursor.execute(
            """INSERT INTO transactions 
               (portfolio_id, asset_id, transaction_type, quantity, unit_price, total_amount, fee, notes, transaction_date)
               VALUES (?, ?, 'BUY', ?, ?, ?, ?, 'Dönemsel portföy alımı', ?)""",
            (portfolio_id, asset_id, qty, avg_price, total_amount, fee, buy_date)
        )
    
    conn.commit()
    print(f"✅ Portföy ve varlık bakiyeleri eklendi (Portföy ID: {portfolio_id}).")
    return portfolio_id

def populate_price_history(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT id, current_price FROM assets")
    assets = cursor.fetchall()
    
    now = datetime.now()
    records = []
    
    for asset_id, current_price in assets:
        # Son 30 günün fiyat geçmişi
        base_price = current_price * 0.90 # 30 gün önce ~%10 düşüktü
        for day in range(30, -1, -1):
            date_str = (now - timedelta(days=day)).strftime("%Y-%m-%d %H:%M:%S")
            # Günlük % -1.5 ile +2.0 arası rastgele değişim
            pct_change = random.uniform(-0.015, 0.02)
            base_price = base_price * (1 + pct_change)
            records.append((asset_id, round(base_price, 2), date_str))
            
    cursor.executemany(
        "INSERT INTO price_history (asset_id, price, recorded_at) VALUES (?, ?, ?)",
        records
    )
    conn.commit()
    print(f"✅ {len(records)} adet fiyat geçmişi kaydı eklendi.")

def generate_sample_documents():
    os.makedirs(DOCS_DIR, exist_ok=True)
    
    docs = {
        "thyao_q3_report.txt": """
TÜRK HAVA YOLLARI (THYAO) 2026 3. ÇEYREK FİNANSAL VE OPERASYONEL RAPORU

Özet Finansal Sonuçlar:
Türk Hava Yolları, 2026 yılının 3. çeyreğinde beklentilerin üzerinde 24.5 Milyar TL net kâr açıkladı. Geçen yılın aynı dönemine göre net kârda %28 artış sağlandı.
Toplam satış gelirleri, yolcu talebindeki güçlü seyir ve kargo gelirlerindeki artışla 185 Milyar TL seviyesine ulaştı.

Operasyonel Göstergeler:
- Taşınan yolcu sayısı geçen yıla göre %18 artarak 25.4 milyon yolcuya ulaştı.
- Yolcu doluluk oranı (Passenger Load Factor) %86.4 olarak gerçekleşti.
- Akaryakıt maliyetlerindeki hafif gerileme ve verimli filo yönetimi, FAVÖK (EBITDA) marjını %26.5 seviyesine yükseltti.

Gelecek Beklentileri ve Hedefler:
Yönetim kurulu, 2026 yıl sonu için filodaki uçak sayısını 485'e çıkarmayı ve yolcu hedefini 90 milyon olarak korumayı hedefliyor.
Analist Değerlendirmesi: THYAO için 12 aylık hedef fiyat 380.00 TL olarak güncellenmiş olup 'AL' tavsiyesi korunmaktadır.
""",
        
        "garan_financial_news.txt": """
GARANTİ BBVA (GARAN) FİNANSAL DEĞERLENDİRME VE SEKTÖR HABERİ

Bilanço Özetleri:
Garanti BBVA, 2026 yılı 3. çeyrek bilançosunda net dönem kârını 18.2 Milyar TL olarak duyurdu.
Özsermaye kârlılığı (ROE) %34.2 seviyesinde gerçekleşirken, aktif kârlılığı %3.8 olarak kaydedildi.

Kredi ve Mevduat Yapısı:
- TL Kredilerde çeyreklik bazda %12 büyüme kaydedildi.
- Takipteki Krediler Oranı (NPL) %1.8 ile sektör ortalamasının oldukça altında tutuldu.
- Sermaye Yeterlilik Rasyosu (CAR) %18.2 ile güçlü özkaynak yapısını koruduğunu gösteriyor.

Piyasa Görünümü:
Merkez Bankası'nın faiz politikaları doğrultusunda net faiz marjında (NIM) toparlanma eğilimi devam etmektedir.
Bankacılık hisseleri genelinde GARAN, yüksek dijitalleşme oranı ve güçlü sermaye tabanıyla öne çıkmaktadır.
""",

        "gold_market_analysis.txt": """
KÜRESEL ALTIN VE EMTİA PİYASASI ANALİZİ RAPORU

Piyasa Durumu ve Gelişmeler:
Ons Altın (XAU/USD), küresel jeopolitik riskler ve merkez bankalarının kesintisiz rezerv alımları ile 2.430 USD seviyesinde işlem görmektedir.
Gram Altın ise Dolar/TL kurundaki kademeli yükseliş ve ons fiyatının desteğiyle 2.540 TL seviyesinde tarihi zirvelere yakın seyretmektedir.

Analiz ve Beklentiler:
1. Merkez Bankası Alımları: Çin, Hindistan ve Polonya merkez bankaları fiziki altın alımlarını 3. çeyrekte de sürdürdü.
2. Faiz İndirim Beklentileri: Fed ve ECB'nin faiz indirim döngüsüne girmesi, faiz getirisi olmayan altını yatırımcılar için çekici kılmaktadır.
3. Portföy Stratejisi Tavsiyesi: Uzmanlar enflasyona karşı koruma ve portföy riskini dengelemek amacıyla %20 - %25 oranında altın varlığı bulundurulmasını önermektedir.
""",

        "forex_and_fed_report.txt": """
DÖVİZ PİYASALARI VE FED FAİZ KARARI DEĞERLENDİRMESİ

Fed Faiz Kararı ve Makroekonomik Durum:
ABD Merkez Bankası (Fed), son toplantısında politika faizini sabit tutarken önümüzdeki çeyrekte 25 baz puanlık indirim sinyali verdi.
ABD enflasyonunun %2.4 seviyesine gerilemesi, dolar endeksinin (DXY) 102.5 seviyesine çekilmesine neden oldu.

Döviz Kurları ve TL Analizi:
- USD/TRY: Dolar/TL kuru 33.45 seviyelerinde yatay seyretmektedir. Türkiye Merkez Bankası'nın brüt rezervlerinin 150 Milyar Doları aşması kurlar üzerindeki oynaklığı azaltmıştır.
- EUR/TRY: Euro/TL Paritedeki (EUR/USD 1.0950) toparlanmanın etkisiyle 36.60 TL seviyesinden işlem görmektedir.
- Portföy Etkisi: Döviz varlıkları portföylerde döviz cinsi borçlara karşı korunma (hedge) sağlamakta, ancak yüksek TL mevduat faizleri karşısında kısa vadeli reel getiri sınırlı kalabilmektedir.
"""
    }
    
    for filename, content in docs.items():
        filepath = os.path.join(DOCS_DIR, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content.strip())
            
    print(f"✅ {len(docs)} adet örnek finansal doküman 'sample_documents/' klasörüne yazıldı.")

def main():
    print("🚀 Sentetik Veri Üretici Başlatılıyor...")
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        populate_categories_and_assets(conn)
        portfolio_id = populate_users_and_portfolios(conn)
        populate_price_history(conn)
    generate_sample_documents()
    print("\n🎉 Tüm sentetik veriler ve finansal test raporları başarıyla oluşturuldu!")

if __name__ == "__main__":
    main()
