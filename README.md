# Dashboard Analisis E-Commerce Olist

Proyek ini menganalisis Brazilian E-Commerce Public Dataset by Olist, mencakup tren penjualan, performa kategori produk, serta ketepatan pengiriman dan kepuasan pelanggan.

## Struktur Proyek

- `Proyek_Analisis_E_Commerce.ipynb`: notebook analisis lengkap dari gathering, assessing, cleaning, EDA, visualisasi, hingga kesimpulan.
- `dashboard/dashboard.py`: dashboard interaktif Streamlit.
- `data/`: seluruh dataset yang digunakan.
- `requirements.txt`: dependensi Python.
- `url.txt`: URL deployment dashboard.

## Menyiapkan Environment

### Anaconda

```bash
conda create --name olist-analysis python=3.10
conda activate olist-analysis
pip install -r requirements.txt
```

### Virtual environment Python

```bash
python3 -m venv .venv
source .venv/bin/activate        # macOS/Linux
# .venv\\Scripts\\activate     # Windows PowerShell
pip install -r requirements.txt
```

## Menjalankan Notebook

Buka `Proyek_Analisis_E_Commerce.ipynb` dari root repository dan pilih kernel environment yang sudah disiapkan. Notebook membaca dataset dari folder `data/`.

## Menjalankan Dashboard

Dari root repository:

```bash
streamlit run dashboard/dashboard.py
```
