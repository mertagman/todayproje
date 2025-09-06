import sqlite3
import os
from datetime import datetime

DATABASE_NAME = 'ilanlar.db'

def init_db():
    """Initialize the database with the ilanlar table"""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    # Create ilanlar table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ilanlar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            advertisement_type TEXT,
            adres TEXT,
            view INTEGER DEFAULT 0,
            is_gold INTEGER DEFAULT 0,
            img_1 TEXT,
            img_2 TEXT,
            img_3 TEXT,
            sale_price REAL,
            rent_price REAL,
            contract_id TEXT,
            description TEXT,
            description_en TEXT,
            description_ar TEXT,
            deed TEXT,
            bed_type TEXT,
            status INTEGER DEFAULT 1,
            creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            update_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    """
    # Insert some sample data if table is empty
    cursor.execute('SELECT COUNT(*) FROM ilanlar')
    count = cursor.fetchone()[0]
    
    if count == 0:
        sample_data = [
            ('Emin Termal', 'Satılık', 'İstanbul, Türkiye', 150, 1, '/devremulk/emin.jpg', '/devremulk/emin2.jpg', '/devremulk/emin3.jpeg', 120000, None, 'EMN001', 'Kendine ait mutfak bölümü bulunan evlerde uydu yayınlı LCD TV, ücretsiz Wi-Fi, klima, balkon, mutfak gereçleri ve elektronik anahtar sistemi yer alıyor.', 'Houses with their own kitchen area feature satellite LCD TV, free Wi-Fi, air conditioning, balcony, kitchen utensils and electronic key system.', 'تتميز المنازل التي تحتوي على منطقة مطبخ خاصة بها بتلفزيون LCD عبر الأقمار الصناعية ومجاني', 'Tapu', '5+1', 1, datetime.now(), datetime.now()),
            ('Deniz Manzaralı Villa', 'Satılık', 'Antalya, Türkiye', 89, 0, '/static/img/villa1.jpg', '/static/img/villa2.jpg', None, 850000, None, 'VIL002', 'Deniz manzaralı lüks villa', 'Luxury villa with sea view', 'فيلا فاخرة بإطلالة على البحر', 'Tapu', '4+1', 1, datetime.now(), datetime.now()),
            ('Merkezi Daire', 'Kiralık', 'Ankara, Türkiye', 45, 0, '/static/img/apt1.jpg', None, None, None, 2500, 'APT003', 'Şehir merkezinde modern daire', 'Modern apartment in city center', 'شقة حديثة في وسط المدينة', 'Tapu', '3+1', 1, datetime.now(), datetime.now())
        ]
        
        cursor.executemany('''
            INSERT INTO ilanlar (title, advertisement_type, adres, view, is_gold, img_1, img_2, img_3, 
                               sale_price, rent_price, contract_id, description, description_en, 
                               description_ar, deed, bed_type, status, creation_date, update_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', sample_data)
    
    conn.commit()
    conn.close()
    """
    print(f"Database initialized successfully: {DATABASE_NAME}")

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn

if __name__ == '__main__':
    init_db()
