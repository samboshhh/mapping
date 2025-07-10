
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns

# --- 🧾 Load data ---
@st.cache_data
def load_data():
    transactions = pd.read_csv("category_merchant_data.csv")
    mapping = pd.read_excel("Report Categories.xlsx")

    transactions.columns = transactions.columns.str.strip().str.lower()
    mapping.columns = mapping.columns.str.strip().str.lower()

    df = transactions.merge(
        mapping,
        left_on='enrichment_categories',
        right_on='enrichment categories',
        how='left'
    )

    df['amount'] = pd.to_numeric(df['amount'], errors='coerce')

    for col in ['transaction group', 'report categories', 'enrichment_categories', 'enrichment_merchant_name']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    return df

df = load_data()

# --- 🎨 Sidebar Filters ---
st.sidebar.title("📊 Category Explorer")
tg_options = sorted(df['transaction group'].dropna().unique())
tg_selected = st.sidebar.selectbox("Transaction Group", tg_options)

rc_options = sorted(df[df['transaction group'] == tg_selected]['report categories'].dropna().unique())
rc_selected = st.sidebar.selectbox("Report Category", rc_options)

ec_options = sorted(df[
    (df['transaction group'] == tg_selected) &
    (df['report categories'] == rc_selected)
]['enrichment_categories'].dropna().unique())
ec_selected = st.sidebar.selectbox("Enrichment Category", ec_options)

# --- 🥧 Pie Chart: Spend by Transaction Group ---
st.header("💸 Spend Breakdown by Transaction Group")
tg_spend = (
    df[df['transaction group'].notna()]
    .groupby('transaction group')['amount']
    .sum()
    .abs()
    .sort_values(ascending=False)
)

fig1, ax1 = plt.subplots()
ax1.pie(tg_spend, labels=tg_spend.index, autopct='%1.1f%%', startangle=140)
ax1.axis('equal')
st.pyplot(fig1)

# --- 🧮 Hierarchy Table ---
st.subheader("📋 Transaction Group > Report Category > Enrichment Category")
summary_hierarchy = (
    df[df['transaction group'].notna()]
    .groupby(['transaction group', 'report categories', 'enrichment_categories'])
    .agg(
        txn_count=('amount', 'count'),
        total_spend=('amount', 'sum'),
        avg_txn=('amount', 'mean')
    )
    .reset_index()
)

st.dataframe(summary_hierarchy.style.format({
    'total_spend': '£{:,.2f}',
    'avg_txn': '£{:,.2f}'
}), use_container_width=True)

# --- 🔍 Filtered Merchant Drilldown ---
st.subheader(f"🔍 Top Merchants for '{ec_selected}'")

filtered = df[
    (df['transaction group'] == tg_selected) &
    (df['report categories'] == rc_selected) &
    (df['enrichment_categories'] == ec_selected)
]

if filtered.empty or 'enrichment_merchant_name' not in filtered.columns:
    st.warning("No data available for this selection.")
else:
    top_merchants = (
        filtered.groupby('enrichment_merchant_name')
        .agg(
            txn_count=('amount', 'count'),
            total_spend=('amount', 'sum'),
            avg_txn=('amount', 'mean')
        )
        .sort_values(by='txn_count', ascending=False)
        .head(10)
        .reset_index()
    )

    st.write(f"💰 Total spend in '{ec_selected}': £{filtered['amount'].sum():,.2f}")

    fig2, ax2 = plt.subplots(figsize=(10, 4))
    sns.barplot(
        data=top_merchants,
        x='total_spend',
        y='enrichment_merchant_name',
        palette='Blues_r',
        ax=ax2
    )
    ax2.set_xlabel("Total Spend (£)")
    ax2.set_ylabel("Merchant")
    ax2.set_title("Top Merchants by Spend")
    st.pyplot(fig2)

    st.dataframe(top_merchants.style.format({
        'total_spend': '£{:,.2f}',
        'avg_txn': '£{:,.2f}'
    }), use_container_width=True)

    # --- 📥 Download Button ---
    csv = top_merchants.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Table as CSV",
        data=csv,
        file_name=f"{ec_selected.replace(' ', '_')}_top_merchants.csv",
        mime='text/csv'
    )
