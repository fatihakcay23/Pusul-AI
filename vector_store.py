#!/usr/bin/env python3
"""
Akıllı Kişisel Finans Danışmanı - Vektör Veritabanı ve Arama Modülü (VectorStore)
- Finansal rapor ve haber metinlerini parçalara (chunking) böler.
- Metinleri vektör alanına gömer (embedding) ve kosinüs benzerliği (cosine similarity) hesaplar.
- İlgili doküman parçalarını semantik skor sırasına göre döndürür.
"""

import os
import math
import json
import re

class VectorStore:
    def __init__(self, storage_path=None):
        self.chunks = [] # [{id, doc_title, text, vector}]
        self.vocabulary = set()
        self.idf = {}
        self.storage_path = storage_path

    def _tokenize(self, text):
        """Metni küçük harfe dönüştürür ve kelimelere ayırır."""
        words = re.findall(r'\w+', text.lower())
        # Stopwords filtreleme (Türkçe & İngilizce temel kelimeler)
        stopwords = {'ve', 'ile', 'bir', 'bu', 'da', 'de', 'için', 'olan', 'olarak', 'göre', 'en', 'ise', 'her', 'and', 'the', 'of', 'in', 'to', 'for'}
        return [w for w in words if w not in stopwords and len(w) > 1]

    def _chunk_text(self, text, chunk_size=300, overlap=50):
        """Metni mantıksal parçalara böler."""
        paragraphs = text.strip().split('\n\n')
        chunks = []
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            if len(para) <= chunk_size:
                chunks.append(para)
            else:
                # Cümle bazlı veya sabit boyutta bölme
                sentences = re.split(r'(?<=[.!?])\s+', para)
                current_chunk = ""
                for sentence in sentences:
                    if len(current_chunk) + len(sentence) <= chunk_size:
                        current_chunk += (" " if current_chunk else "") + sentence
                    else:
                        if current_chunk:
                            chunks.append(current_chunk)
                        current_chunk = sentence
                if current_chunk:
                    chunks.append(current_chunk)
                    
        return chunks

    def add_document(self, doc_id, doc_title, content):
        """Dokümanı parçalar ve depoya ekler."""
        raw_chunks = self._chunk_text(content)
        for i, text_chunk in enumerate(raw_chunks):
            tokens = self._tokenize(text_chunk)
            self.vocabulary.update(tokens)
            self.chunks.append({
                "chunk_id": f"{doc_id}_chunk_{i}",
                "doc_id": doc_id,
                "doc_title": doc_title,
                "text": text_chunk,
                "tokens": tokens,
                "vector": {}
            })
        self._update_embeddings()

    def _update_embeddings(self):
        """TF-IDF vektörlerini hesaplar ve normalize eder."""
        N = len(self.chunks)
        if N == 0:
            return
            
        # Doc Frequency (DF)
        df = {}
        for chunk in self.chunks:
            unique_tokens = set(chunk["tokens"])
            for token in unique_tokens:
                df[token] = df.get(token, 0) + 1
                
        # Inverse Doc Frequency (IDF)
        self.idf = {token: math.log((N + 1) / (freq + 1)) + 1 for token, freq in df.items()}
        
        # TF-IDF Vector & Unit Normalization
        for chunk in self.chunks:
            tf = {}
            for t in chunk["tokens"]:
                tf[t] = tf.get(t, 0) + 1
                
            vec = {}
            norm_sq = 0.0
            for t, count in tf.items():
                val = count * self.idf.get(t, 1.0)
                vec[t] = val
                norm_sq += val * val
                
            norm = math.sqrt(norm_sq) if norm_sq > 0 else 1.0
            chunk["vector"] = {t: val / norm for t, val in vec.items()}

    def load_directory(self, dir_path):
        """Bir klasördeki tüm .txt finansal raporları indeksler."""
        if not os.path.exists(dir_path):
            return
            
        for filename in os.listdir(dir_path):
            if filename.endswith(".txt"):
                filepath = os.path.join(dir_path, filename)
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                    title = filename.replace("_", " ").replace(".txt", "").upper()
                    self.add_document(filename, title, content)
                    
        print(f"✅ Vektör Veritabanı: '{dir_path}' klasöründen {len(self.chunks)} metin parçası indekslendi.")

    def search(self, query, top_k=3):
        """Sorgu metni ile en yüksek semantik benzerliğe sahip metin parçalarını getirir."""
        query_tokens = self._tokenize(query)
        if not query_tokens or not self.chunks:
            return []
            
        # Sorgu Vektörü (TF-IDF)
        tf = {}
        for t in query_tokens:
            tf[t] = tf.get(t, 0) + 1
            
        q_vec = {}
        norm_sq = 0.0
        for t, count in tf.items():
            val = count * self.idf.get(t, 1.0)
            q_vec[t] = val
            norm_sq += val * val
            
        norm = math.sqrt(norm_sq) if norm_sq > 0 else 1.0
        q_vec_norm = {t: val / norm for t, val in q_vec.items()}
        
        # Kosinüs Benzerliği Hesaplama (Dot Product of normalized vectors)
        results = []
        for chunk in self.chunks:
            c_vec = chunk["vector"]
            score = 0.0
            for t, val in q_vec_norm.items():
                if t in c_vec:
                    score += val * c_vec[t]
                    
            if score > 0.0:
                results.append({
                    "doc_title": chunk["doc_title"],
                    "doc_id": chunk["doc_id"],
                    "text": chunk["text"],
                    "score": round(score, 4)
                })
                
        # En yüksek skora göre sırala
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

if __name__ == "__main__":
    # Test Vektör DB
    store = VectorStore()
    docs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_documents")
    store.load_directory(docs_dir)
    
    query = "THYAO şirketinin son çeyrek net kârı ve yolcu sayısı ne kadar arttı?"
    print(f"\n🔍 Test Sorgusu: '{query}'")
    hits = store.search(query, top_k=2)
    for i, h in enumerate(hits, 1):
        print(f"\n--- Sonuç #{i} (Skor: {h['score']}) [{h['doc_title']}] ---")
        print(h['text'])
