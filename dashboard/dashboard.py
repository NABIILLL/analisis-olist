from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st


DATA_DIR = Path(__file__).resolve().parents[1] / "data"

st.set_page_config(
    page_title="Olist Commerce Intelligence",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .stApp {
        background: #0f172a;
        color: #f8fafc;
    }
    [data-testid="stAppViewContainer"],
    [data-testid="stHeader"] {
        background: #0f172a;
    }
    [data-testid="stSidebar"] {
        background: #111827;
    }
    [data-testid="stSidebar"] * {
        color: #f9fafb;
    }
    .hero {
        padding: 1.5rem 1.75rem;
        border-radius: 18px;
        color: white;
        background: linear-gradient(120deg, #312e81, #2563eb 60%, #06b6d4);
        margin-bottom: 1.25rem;
    }
    .hero h1 {
        margin: 0;
        font-size: 2.2rem;
    }
    .hero p {
        margin: .45rem 0 0;
        opacity: .9;
    }
    [data-testid="stAppViewContainer"] [data-testid="stMarkdownContainer"] h1,
    [data-testid="stAppViewContainer"] [data-testid="stMarkdownContainer"] h2,
    [data-testid="stAppViewContainer"] [data-testid="stMarkdownContainer"] h3,
    [data-testid="stAppViewContainer"] [data-testid="stMarkdownContainer"] h4,
    [data-testid="stAppViewContainer"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stAppViewContainer"] [data-testid="stMetricLabel"],
    [data-testid="stAppViewContainer"] [data-testid="stMetricValue"],
    [data-testid="stAppViewContainer"] [data-testid="stCaptionContainer"] {
        color: #f8fafc !important;
    }
    .section-title {
        color: #f8fafc !important;
        font-weight: 700;
        font-size: 1.15rem;
        margin: .75rem 0 .55rem;
    }
    .chart-title {
        color: #f8fafc !important;
        font-weight: 700;
        font-size: 1rem;
        margin: .8rem 0 .4rem;
    }
    .insight {
        padding: 1rem 1.1rem;
        border-left: 5px solid #2563eb;
        border-radius: 10px;
        background: #1e293b;
        color: #f8fafc !important;
        box-shadow: 0 2px 10px rgba(0, 0, 0, .2);
        min-height: 92px;
    }
    .insight strong {
        color: #93c5fd !important;
    }
    .insight br {
        line-height: 1.8;
    }
    [data-testid="stDataFrame"] {
        border: 1px solid #334155;
        border-radius: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_data():
    orders = pd.read_csv(
        DATA_DIR / "orders_dataset.csv",
        parse_dates=[
            "order_purchase_timestamp",
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
        ],
    )
    payments = pd.read_csv(DATA_DIR / "order_payments_dataset.csv")
    items = pd.read_csv(DATA_DIR / "order_items_dataset.csv")
    products = pd.read_csv(DATA_DIR / "products_dataset.csv")
    translation = pd.read_csv(DATA_DIR / "product_category_name_translation.csv")
    return orders, payments, items, products, translation


def format_brl(value):
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


orders, payments, items, products, translation = load_data()
orders["month"] = orders["order_purchase_timestamp"].dt.to_period("M").astype(str)

with st.sidebar:
    st.markdown("## 🛍️ Olist Analytics")
    st.caption("Gunakan filter untuk mengeksplorasi performa bisnis.")
    min_date = orders["order_purchase_timestamp"].min().date()
    max_date = orders["order_purchase_timestamp"].max().date()
    selected_dates = st.date_input(
        "Periode pesanan",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )
    statuses = sorted(orders["order_status"].dropna().unique())
    selected_statuses = st.multiselect(
        "Status pesanan",
        statuses,
        default=statuses,
    )
    st.divider()
    st.caption("Sumber: Brazilian E-Commerce Public Dataset by Olist")
    st.caption(
        "Nilai moneter menggunakan BRL. Total penjualan memakai nilai pembayaran "
        "(termasuk ongkir); kategori memakai harga item (tanpa ongkir)."
    )

if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
    start_date, end_date = selected_dates
else:
    start_date, end_date = min_date, max_date

filtered_orders = orders[
    orders["order_purchase_timestamp"].dt.date.between(start_date, end_date)
    & orders["order_status"].isin(selected_statuses)
].copy()
filtered_order_ids = set(filtered_orders["order_id"])
filtered_payments = payments[payments["order_id"].isin(filtered_order_ids)]
filtered_items = items[items["order_id"].isin(filtered_order_ids)].copy()

filtered_items = filtered_items.merge(
    products[["product_id", "product_category_name"]],
    on="product_id",
    how="left",
)
filtered_items = filtered_items.merge(
    translation,
    on="product_category_name",
    how="left",
)
filtered_items["category"] = filtered_items["product_category_name_english"].fillna(
    filtered_items["product_category_name"]
).fillna("Unknown")

total_orders = filtered_orders["order_id"].nunique()
total_revenue = filtered_payments["payment_value"].sum()
average_order_value = (
    filtered_payments.groupby("order_id")["payment_value"].sum().mean()
    if total_orders
    else 0
)
delivered_orders = filtered_orders[
    filtered_orders["order_delivered_customer_date"].notna()
]
late_orders = delivered_orders[
    delivered_orders["order_delivered_customer_date"]
    > delivered_orders["order_estimated_delivery_date"]
]
late_rate = len(late_orders) / len(delivered_orders) * 100 if len(delivered_orders) else 0

st.markdown(
    """
    <div class="hero">
        <h1>Olist Commerce Intelligence</h1>
        <p>Dashboard interaktif untuk memahami penjualan, pesanan, kategori produk,
        dan ketepatan waktu pengiriman.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.caption(
    f"Periode aktif: {start_date.strftime('%d %b %Y')} – "
    f"{end_date.strftime('%d %b %Y')} · {total_orders:,} pesanan terpilih"
)

kpi_1, kpi_2, kpi_3, kpi_4 = st.columns(4)
kpi_1.metric("Total Penjualan", format_brl(total_revenue))
kpi_2.metric("Total Pesanan", f"{total_orders:,}")
kpi_3.metric("Rata-rata Nilai Pesanan", format_brl(average_order_value))
kpi_4.metric("Tingkat Keterlambatan", f"{late_rate:.2f}%")

st.markdown('<div class="section-title">Ringkasan Performa</div>', unsafe_allow_html=True)
monthly = (
    filtered_orders.groupby("month")
    .agg(orders=("order_id", "nunique"))
    .join(
        filtered_payments.groupby(
            filtered_payments["order_id"].map(
                filtered_orders.set_index("order_id")["month"]
            )
        )["payment_value"].sum().rename("revenue"),
        how="left",
    )
    .fillna(0)
)
monthly.index.name = "Bulan"

category_sales = (
    filtered_items.groupby("category", as_index=False)
    .agg(revenue=("price", "sum"), items=("order_id", "count"))
    .sort_values("revenue", ascending=False)
)

trend_col, category_col = st.columns([1.35, 1])
with trend_col:
    st.markdown('<div class="chart-title">Tren Penjualan Bulanan</div>', unsafe_allow_html=True)
    st.line_chart(monthly[["revenue"]], y_label="Penjualan (R$)")
    st.markdown('<div class="chart-title">Tren Jumlah Pesanan</div>', unsafe_allow_html=True)
    monthly_orders = monthly.sort_index(ascending=True)
    fig, ax = plt.subplots(figsize=(8, 3.2))
    fig.patch.set_facecolor("#0f172a")
    ax.set_facecolor("#0f172a")
    bars = ax.bar(
        monthly_orders.index,
        monthly_orders["orders"],
        color="#60a5fa",
    )
    ax.set_ylabel("Jumlah pesanan", color="#f8fafc")
    ax.tick_params(axis="x", colors="#cbd5e1", labelrotation=60, labelsize=7)
    ax.tick_params(axis="y", colors="#cbd5e1")
    ax.grid(axis="y", color="#334155", alpha=0.65)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_color("#475569")
    st.pyplot(fig, width="stretch")
    plt.close(fig)
with category_col:
    st.markdown(
        '<div class="chart-title">Top 10 Kategori berdasarkan Nilai Item</div>',
        unsafe_allow_html=True,
    )
    top_categories = category_sales.head(10).sort_values("revenue", ascending=False)
    fig, ax = plt.subplots(figsize=(7, 4.7))
    fig.patch.set_facecolor("#0f172a")
    ax.set_facecolor("#0f172a")
    values = top_categories["revenue"].to_numpy()
    colors = plt.cm.Blues_r(
        [0.25 + (index / max(len(values) - 1, 1)) * 0.55 for index in range(len(values))]
    )
    ax.barh(top_categories["category"], values, color=colors)
    ax.invert_yaxis()
    ax.set_xlabel("Penjualan (R$)", color="#f8fafc")
    ax.tick_params(axis="x", colors="#cbd5e1")
    ax.tick_params(axis="y", colors="#cbd5e1", labelsize=8)
    ax.grid(axis="x", color="#334155", alpha=0.65)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_color("#475569")
    st.pyplot(fig, width="stretch")
    plt.close(fig)

st.markdown('<div class="section-title">Insight Otomatis</div>', unsafe_allow_html=True)
insight_1, insight_2, insight_3 = st.columns(3)
best_category = category_sales.iloc[0] if not category_sales.empty else None
best_month = monthly["revenue"].idxmax() if not monthly.empty else "-"
with insight_1:
    st.markdown(
        f'<div class="insight">🏆 <strong>Kategori terlaris</strong><br>'
        f'{best_category["category"] if best_category is not None else "-"}'
        f'<br>{format_brl(best_category["revenue"]) if best_category is not None else "Tidak ada data"}</div>',
        unsafe_allow_html=True,
    )
with insight_2:
    st.markdown(
        f'<div class="insight">📈 <strong>Bulan dengan penjualan tertinggi</strong><br>'
        f'{best_month}<br>{format_brl(monthly.loc[best_month, "revenue"]) if best_month != "-" else "Tidak ada data"}</div>',
        unsafe_allow_html=True,
    )
with insight_3:
    st.markdown(
        f'<div class="insight">🚚 <strong>Status pengiriman</strong><br>'
        f'{len(late_orders):,} pesanan terlambat<br>'
        f'Dari {len(delivered_orders):,} pesanan yang telah terkirim</div>',
        unsafe_allow_html=True,
    )

st.markdown('<div class="section-title">Detail Kategori</div>', unsafe_allow_html=True)
display_categories = category_sales.copy()
display_categories["revenue"] = display_categories["revenue"].map(format_brl)
display_categories = display_categories.rename(
    columns={
        "category": "Kategori",
        "revenue": "Total Penjualan",
        "items": "Jumlah Item",
    }
)
st.dataframe(display_categories, width="stretch", hide_index=True)
