import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from pathlib import Path

# ---------- Page setup ----------
st.set_page_config(page_title="Expense Tracker", page_icon="💰", layout="wide")

CARD = "#161B26"
GRID = "#262D3F"
TEXT = "#E6E8EE"
MUTED = "#8B93A7"
ACCENT = "#6C8CFF"
DANGER = "#FF6B6B"
PALETTE = ["#6C8CFF", "#4FD1A5", "#FFB86B", "#FF6B9A", "#B38CFF", "#5CC8FF", "#C8E06B"]

st.markdown(
    f"""
    <style>
    #MainMenu, footer {{visibility: hidden;}}
    .block-container {{padding-top: 2rem; max-width: 1200px;}}
    div[data-testid="stMetric"] {{
        background: {CARD};
        border: 1px solid {GRID};
        border-radius: 14px;
        padding: 16px 20px;
    }}
    div[data-testid="stMetricLabel"] p {{color: {MUTED}; font-size: 0.85rem;}}
    div[data-testid="stMetricValue"] {{font-size: 1.7rem; font-weight: 700;}}
    .subtitle {{color: {MUTED}; margin-top: -10px; margin-bottom: 18px;}}
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- Data ----------
@st.cache_data
def make_dummy_data() -> pd.DataFrame:
    np.random.seed(42)
    categories = ["Food", "Travel", "Shopping", "Bills", "Entertainment"]
    return pd.DataFrame(
        {
            "Date": pd.date_range("2026-01-01", periods=180),
            "Category": np.random.choice(categories, 180),
            "Amount": np.random.randint(50, 1500, 180),
        }
    )


def load_data(uploaded):
    if uploaded is not None:
        df = pd.read_csv(uploaded)
        source = "Uploaded file"
    elif Path("expenses.csv").exists():
        df = pd.read_csv("expenses.csv")
        source = "expenses.csv"
    else:
        return make_dummy_data(), "Sample data"

    # Match column names case-insensitively
    df.columns = [c.strip().title() for c in df.columns]
    needed = {"Date", "Category", "Amount"}
    if not needed.issubset(df.columns):
        st.error(f"Your CSV must have these columns: {', '.join(sorted(needed))}")
        st.stop()
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce")
    return df[["Date", "Category", "Amount"]].dropna(), source


# ---------- Sidebar ----------
st.sidebar.header("Controls")
uploaded = st.sidebar.file_uploader("Upload CSV (Date, Category, Amount)", type="csv")
data, source = load_data(uploaded)

categories = sorted(data["Category"].unique())
selected = st.sidebar.multiselect("Categories", categories, default=categories)

min_d, max_d = data["Date"].min().date(), data["Date"].max().date()
date_range = st.sidebar.date_input("Date range", (min_d, max_d), min_value=min_d, max_value=max_d)
budget = st.sidebar.number_input("Monthly budget (₹)", value=30000, step=1000)

data = data[data["Category"].isin(selected)]
if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    start, end = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    data = data[(data["Date"] >= start) & (data["Date"] <= end)]

# ---------- Header ----------
st.title("💰 Expense Tracker")
st.markdown(f'<p class="subtitle">Understand where your money goes. Data source: {source}</p>', unsafe_allow_html=True)

if data.empty:
    st.warning("No data for the selected filters.")
    st.stop()

data = data.copy()
data["Month"] = data["Date"].dt.to_period("M").astype(str)
cat_total = data.groupby("Category")["Amount"].sum().sort_values(ascending=False)
monthly = data.groupby("Month")["Amount"].sum()
daily = data.groupby(data["Date"].dt.date)["Amount"].sum()
color_of = {c: PALETTE[i % len(PALETTE)] for i, c in enumerate(cat_total.index)}

# ---------- KPI cards ----------
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total spent", f"₹{data['Amount'].sum():,.0f}")
c2.metric("Daily average", f"₹{np.mean(daily.values):,.0f}")
c3.metric("Largest expense", f"₹{data['Amount'].max():,.0f}")
c4.metric("Top category", cat_total.index[0])

over = monthly[monthly > budget]
if not over.empty:
    st.warning(f"Budget of ₹{budget:,.0f} exceeded in: {', '.join(over.index)}")

# ---------- Chart helpers ----------
def new_fig(w=6, h=3.8):
    fig, ax = plt.subplots(figsize=(w, h), facecolor=CARD)
    ax.set_facecolor(CARD)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GRID)
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.yaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    return fig, ax


# ---------- Tabs ----------
tab1, tab2, tab3 = st.tabs(["Overview", "Trends", "Data"])

with tab1:
    left, right = st.columns(2)

    with left:
        st.subheader("Spending by category")
        fig, ax = new_fig()
        ax.bar(cat_total.index, cat_total.values, color=[color_of[c] for c in cat_total.index], width=0.6)
        ax.set_ylabel("Amount (₹)", color=MUTED)
        plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
        fig.tight_layout()
        st.pyplot(fig)

    with right:
        st.subheader("Share of spending")
        fig, ax = plt.subplots(figsize=(6, 3.8), facecolor=CARD)
        ax.pie(
            cat_total.values,
            colors=[color_of[c] for c in cat_total.index],
            autopct="%1.0f%%",
            pctdistance=0.78,
            startangle=90,
            wedgeprops=dict(width=0.42, edgecolor=CARD, linewidth=2),
            textprops=dict(color="white", fontsize=9),
        )
        ax.legend(cat_total.index, loc="center left", bbox_to_anchor=(1, 0.5),
                  frameon=False, labelcolor=TEXT, fontsize=9)
        fig.tight_layout()
        st.pyplot(fig)

with tab2:
    st.subheader("Monthly spending vs budget")
    fig, ax = new_fig(12, 3.8)
    colors = [DANGER if v > budget else ACCENT for v in monthly.values]
    ax.bar(monthly.index, monthly.values, color=colors, width=0.55)
    ax.axhline(budget, color=DANGER, linestyle="--", linewidth=1.2, label=f"Budget ₹{budget:,.0f}")
    ax.set_ylabel("Amount (₹)", color=MUTED)
    ax.legend(frameon=False, labelcolor=TEXT)
    fig.tight_layout()
    st.pyplot(fig)

    st.subheader("Daily spending")
    fig, ax = new_fig(12, 3.4)
    ax.plot(list(daily.index), daily.values, color=ACCENT, linewidth=1.6)
    ax.fill_between(list(daily.index), daily.values, color=ACCENT, alpha=0.15)
    ax.set_ylabel("Amount (₹)", color=MUTED)
    fig.tight_layout()
    st.pyplot(fig)

with tab3:
    st.subheader("Transactions")
    st.dataframe(data.drop(columns="Month").sort_values("Date", ascending=False),
                 use_container_width=True, hide_index=True)
    st.download_button("Download filtered data (CSV)",
                       data.drop(columns="Month").to_csv(index=False),
                       file_name="filtered_expenses.csv", mime="text/csv")
