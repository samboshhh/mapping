
import streamlit as st
import pandas as pd
import plotly.express as px

# --- Page Config ---
st.set_page_config(page_title="Category Explorer", layout="wide")

# --- Load Data ---
@st.cache_data
def load_data():
    transactions = pd.read_csv("category_merchant_data.csv")
    mapping = pd.read_excel("Report Categories.xlsx")
    transactions.columns = transactions.columns.str.strip().str.lower()
    mapping.columns = mapping.columns.str.strip().str.lower()
    merged = transactions.merge(
        mapping,
        left_on="enrichment_categories",
        right_on="enrichment categories",
        how="left"
    )
    merged["amount"] = pd.to_numeric(merged["amount"], errors="coerce")
    for col in ['transaction group', 'report categories', 'enrichment_categories', 'enrichment_merchant_name']:
        if col in merged.columns:
            merged[col] = merged[col].astype(str).str.strip()
    return merged

df = load_data()

st.title("📊 Category Explorer")

# --- Treemap Visualisation ---
st.subheader("📦 Spend Treemap")
group_selected = st.selectbox("Select Transaction Group", sorted(df["transaction group"].dropna().unique()))

df_grouped = (
    df[df["transaction group"] == group_selected]
    .groupby(["report categories"], as_index=False)
    .agg(total_spend=("amount", "sum"))
    .sort_values(by="total_spend", ascending=False)
)

fig = px.treemap(
    df_grouped,
    path=["report categories"],
    values="total_spend",
    title=f"Spend Breakdown for '{group_selected}'",
)
st.plotly_chart(fig, use_container_width=True)

# --- Full Hierarchy Table ---
st.subheader("📋 Transaction Group > Report Category > Enrichment Category")

summary_hierarchy = (
    df[df['transaction group'].notna()]
    .groupby(['transaction group', 'report categories', 'enrichment_categories'], as_index=False)
    .agg(
        txn_count=('amount', 'count'),
        total_spend=('amount', 'sum'),
        avg_txn=('amount', 'mean')
    )
)

st.dataframe(summary_hierarchy.style.format({
    'total_spend': '£{:,.2f}',
    'avg_txn': '£{:,.2f}'
}), use_container_width=True)

# --- Merchant Drilldown ---
st.subheader("🛍️ Merchant Breakdown")

tg = st.selectbox("Transaction Group", sorted(df["transaction group"].dropna().unique()), key="tg")
rc = st.selectbox("Report Category", sorted(df[df["transaction group"] == tg]["report categories"].dropna().unique()), key="rc")
ec = st.selectbox("Enrichment Category", sorted(df[(df["transaction group"] == tg) & (df["report categories"] == rc)]["enrichment_categories"].dropna().unique()), key="ec")

filtered = df[
    (df["transaction group"] == tg) &
    (df["report categories"] == rc) &
    (df["enrichment_categories"] == ec)
]

if filtered.empty:
    st.warning("No data found for the selected filters.")
else:
    top_merchants = (
        filtered.groupby('enrichment_merchant_name', as_index=False)
        .agg(
            txn_count=('amount', 'count'),
            total_spend=('amount', 'sum'),
            avg_txn=('amount', 'mean')
        )
        .sort_values(by='txn_count', ascending=False)
        .head(10)
    )
    st.markdown(f"### 🧾 Top Merchants for '{ec}'")
    st.dataframe(top_merchants.style.format({
        'total_spend': '£{:,.2f}',
        'avg_txn': '£{:,.2f}'
    }), use_container_width=True)
