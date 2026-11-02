import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Expense Tracker", page_icon="💰")
st.title("💰 Expense Tracker & Analyzer")

# 1. Data load: CSV upload ya dummy data
uploaded = st.sidebar.file_uploader("CSV upload karo (Date, Category, Amount)", type="csv")

if uploaded:
    data = pd.read_csv(uploaded, parse_dates=["Date"])
else:
    st.info("Abhi dummy data dikh raha hai. Sidebar se apna CSV upload kar sakte ho.")
    np.random.seed(42)
    categories = ["Food", "Travel", "Shopping", "Bills", "Entertainment"]
    data = pd.DataFrame({
        "Date": pd.date_range("2026-01-01", periods=90),
        "Category": np.random.choice(categories, 90),
        "Amount": np.random.randint(50, 1500, 90),
    })

data["Month"] = data["Date"].dt.to_period("M").astype(str)

# 2. Basic stats
col1, col2, col3 = st.columns(3)
col1.metric("Total Kharcha", f"₹{data['Amount'].sum():,}")
col2.metric("Average", f"₹{np.mean(data['Amount']):.0f}")
col3.metric("Sabse bada", f"₹{data['Amount'].max():,}")

# 3. Category filter
selected = st.sidebar.multiselect(
    "Category chuno", data["Category"].unique(), default=list(data["Category"].unique())
)
data = data[data["Category"].isin(selected)]

# 4. Charts
cat_total = data.groupby("Category")["Amount"].sum()
monthly = data.groupby("Month")["Amount"].sum()

st.subheader("Category-wise Kharcha")
fig1, ax1 = plt.subplots()
cat_total.plot(kind="bar", color="skyblue", ax=ax1)
ax1.set_ylabel("Amount (₹)")
st.pyplot(fig1)

st.subheader("Kharche ka Share")
fig2, ax2 = plt.subplots()
ax2.pie(cat_total, labels=cat_total.index, autopct="%1.1f%%")
st.pyplot(fig2)

st.subheader("Monthly Trend")
fig3, ax3 = plt.subplots()
ax3.plot(monthly.index, monthly.values, marker="o", color="green")
ax3.set_ylabel("Amount (₹)")
st.pyplot(fig3)

# 5. Budget warning
budget = st.sidebar.number_input("Monthly budget (₹)", value=30000, step=1000)
over = monthly[monthly > budget]
if not over.empty:
    st.warning(f"⚠️ Budget cross hua in months: {', '.join(over.index)}")