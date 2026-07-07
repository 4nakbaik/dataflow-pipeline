-- Tabel Raw: Menyimpan setiap transaksi yg masuk
CREATE TABLE IF NOT EXISTS raw_sales (
    id SERIAL PRIMARY KEY,
    transaction_id VARCHAR(50),
    product_category VARCHAR(50),
    amount DECIMAL(10, 2),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabel Analytics: Hasil agregasi pendapatan per kategori
CREATE TABLE IF NOT EXISTS sales_summary (
    category VARCHAR(50) PRIMARY KEY,
    total_revenue DECIMAL(15, 2),
    transaction_count INT,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

