from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
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
    customers = pd.read_csv(DATA_DIR / "customers_dataset.csv")
    reviews = pd.read_csv(DATA_DIR / "order_reviews_dataset.csv")
    return orders, payments, items, products, translation, customers, reviews


def format_brl(value):
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


(
    orders,
    payments,
    items,
    products,
    translation,
    customers,
    reviews,
) = load_data()

PERIOD_START = pd.Timestamp("2016-09-01")
PERIOD_END = pd.Timestamp("2018-08-31 23:59:59")
orders = orders[
    orders["order_purchase_timestamp"].between(PERIOD_START, PERIOD_END)
].copy()
orders["month"] = orders["order_purchase_timestamp"].dt.to_period("M").astype(str)

with st.sidebar:
    st.markdown("## 🛍️ Olist Analytics")
    st.caption("Gunakan filter untuk mengeksplorasi performa bisnis.")
    min_date = PERIOD_START.date()
    max_date = PERIOD_END.date()
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
        "Periode default mengikuti notebook: September 2016–Agustus 2018. "
        "Nilai penjualan menggunakan harga item (tanpa ongkir)."
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
filtered_items["month"] = filtered_items["order_id"].map(
    filtered_orders.set_index("order_id")["month"]
)

total_orders = filtered_orders["order_id"].nunique()
total_revenue = filtered_items["price"].sum()
average_order_value = (
    filtered_items.groupby("order_id")["price"].sum().mean()
    if total_orders
    else 0
)
reviews_by_order = reviews.groupby("order_id", as_index=False)["review_score"].mean()
delivery_analysis = (
    filtered_orders.merge(reviews_by_order, on="order_id", how="inner")
    .merge(customers[["customer_id", "customer_state"]], on="customer_id", how="left")
    .dropna(
        subset=[
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
            "review_score",
        ]
    )
)
delivery_analysis["delivery_delay"] = (
    delivery_analysis["order_delivered_customer_date"]
    - delivery_analysis["order_estimated_delivery_date"]
).dt.days
delivery_analysis["is_late"] = delivery_analysis["delivery_delay"] > 0
delivery_analysis["month"] = delivery_analysis[
    "order_purchase_timestamp"
].dt.to_period("M").astype(str)
late_orders = delivery_analysis[delivery_analysis["is_late"]]
late_rate = (
    delivery_analysis["is_late"].mean() * 100
    if not delivery_analysis.empty
    else 0
)

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
monthly = filtered_items.groupby("month").agg(
    orders=("order_id", "nunique"),
    revenue=("price", "sum"),
).fillna(0)
monthly.index.name = "Bulan"

category_sales = (
    filtered_items.groupby("category", as_index=False)
    .agg(
        revenue=("price", "sum"),
        orders=("order_id", "nunique"),
        items=("order_id", "count"),
    )
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
    colors = plt.cm.Blues(
        np.linspace(0.45, 0.9, len(values))
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

st.markdown(
    '<div class="section-title">Pertanyaan 3: Keterlambatan Pengiriman</div>',
    unsafe_allow_html=True,
)
monthly_delay = delivery_analysis.groupby("month", as_index=False).agg(
    total_orders=("order_id", "nunique"),
    late_orders=("is_late", "sum"),
)
if not monthly_delay.empty:
    monthly_delay["late_percentage"] = (
        monthly_delay["late_orders"] / monthly_delay["total_orders"] * 100
    )
state_delay = delivery_analysis.groupby("customer_state", as_index=False).agg(
    total_orders=("order_id", "nunique"),
    late_orders=("is_late", "sum"),
)
if not state_delay.empty:
    state_delay["late_percentage"] = (
        state_delay["late_orders"] / state_delay["total_orders"] * 100
    )
qualified_states = state_delay[state_delay["total_orders"] >= 30].sort_values(
    "late_percentage", ascending=False
)

delay_col, state_col = st.columns(2)
with delay_col:
    st.markdown(
        '<div class="chart-title">Persentase Pesanan Terlambat per Bulan</div>',
        unsafe_allow_html=True,
    )
    st.line_chart(
        monthly_delay.set_index("month")[["late_percentage"]]
        if not monthly_delay.empty
        else pd.DataFrame(columns=["late_percentage"]),
        y_label="Pesanan terlambat (%)",
    )
with state_col:
    st.markdown(
        '<div class="chart-title">State dengan Tingkat Keterlambatan Tertinggi</div>',
        unsafe_allow_html=True,
    )
    state_plot = qualified_states.head(10).sort_values("late_percentage")
    fig, ax = plt.subplots(figsize=(7, 4.7))
    fig.patch.set_facecolor("#0f172a")
    ax.set_facecolor("#0f172a")
    state_colors = plt.cm.Oranges(
        np.linspace(0.45, 0.9, len(state_plot))
    )
    ax.barh(
        state_plot["customer_state"],
        state_plot["late_percentage"],
        color=state_colors,
    )
    ax.invert_yaxis()
    ax.set_xlabel("Pesanan terlambat (%)", color="#f8fafc")
    ax.set_ylabel("State pelanggan", color="#f8fafc")
    ax.tick_params(axis="x", colors="#cbd5e1")
    ax.tick_params(axis="y", colors="#cbd5e1")
    ax.grid(axis="x", color="#334155", alpha=0.65)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_color("#475569")
    st.pyplot(fig, width="stretch")
    plt.close(fig)

review_summary = delivery_analysis.groupby("is_late")["review_score"].mean()
highest_delay_state = (
    qualified_states.iloc[0]["customer_state"] if not qualified_states.empty else "-"
)
highest_delay_rate = (
    qualified_states.iloc[0]["late_percentage"] if not qualified_states.empty else 0
)

st.markdown('<div class="section-title">Insight Otomatis</div>', unsafe_allow_html=True)
insight_1, insight_2, insight_3, insight_4 = st.columns(4)
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
        f'{late_rate:.2f}% dari pesanan ber-review</div>',
        unsafe_allow_html=True,
    )
with insight_4:
    st.markdown(
        f'<div class="insight">📍 <strong>State prioritas</strong><br>'
        f'{highest_delay_state}<br>'
        f'{highest_delay_rate:.2f}% terlambat (min. 30 pesanan)</div>',
        unsafe_allow_html=True,
    )

st.markdown('<div class="section-title">Detail Kategori</div>', unsafe_allow_html=True)
display_categories = category_sales.copy()
display_categories["revenue"] = display_categories["revenue"].map(format_brl)
display_categories = display_categories.rename(
    columns={
        "category": "Kategori",
        "revenue": "Total Penjualan",
        "orders": "Jumlah Pesanan",
        "items": "Jumlah Item",
    }
)
st.dataframe(display_categories, width="stretch", hide_index=True)
