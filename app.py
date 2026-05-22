import sys, os, base64
from io import BytesIO

APP_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, APP_DIR)
sys.path.insert(0, os.path.dirname(APP_DIR))
os.chdir(APP_DIR)

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from utils.data_loader import load_and_process_data

st.set_page_config(
    page_title="Cafe Rewards Intelligence Platform",
    page_icon="☕",
    layout="wide",
    initial_sidebar_state="expanded",
)


css_path = os.path.join(APP_DIR, "style.css")
if os.path.exists(css_path):
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Fetch coffee images and embed as base64 so CSP never blocks them.
# Falls back to a pure-CSS/SVG placeholder if requests is unavailable.

def get_coffee_image_b64(url: str, fallback_color: str = "#3B1F0E") -> str | None:
    """Return a base64 data-URI for the given image URL, or None on failure."""
    try:
        import requests
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            mime = resp.headers.get("Content-Type", "image/jpeg").split(";")[0]
            b64 = base64.b64encode(resp.content).decode()
            return f"data:{mime};base64,{b64}"
    except Exception:
        pass
    return None

# Pre-fetch the hero coffee background
COFFEE_BG_URL = "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?w=1400&q=75&fm=jpg"
COFFEE_BEANS_URL = "https://images.unsplash.com/photo-1611854779393-1b2da9d400fe?w=800&q=70&fm=jpg"
COFFEE_CUP_URL = "https://images.unsplash.com/photo-1509042239860-f550ce710b93?w=800&q=70&fm=jpg"

@st.cache_data(show_spinner=False)
def fetch_images():
    return {
        "hero":  get_coffee_image_b64(COFFEE_BG_URL),
        "beans": get_coffee_image_b64(COFFEE_BEANS_URL),
        "cup":   get_coffee_image_b64(COFFEE_CUP_URL),
    }

imgs = fetch_images()

# Build inline style for hero background
def hero_bg_style(b64: str | None) -> str:
    if b64:
        return (
            f"background: "
            f"linear-gradient(135deg, rgba(59,31,14,0.92) 0%, rgba(28,74,46,0.80) 50%, rgba(26,10,3,0.97) 100%), "
            f"url('{b64}') center/cover no-repeat;"
        )
    # Pure-CSS fallback — still gorgeous
    return (
        "background: "
        "radial-gradient(ellipse 70% 60% at 20% 40%, rgba(59,31,14,0.95) 0%, transparent 65%), "
        "radial-gradient(ellipse 60% 50% at 80% 60%, rgba(28,74,46,0.85) 0%, transparent 70%), "
        "linear-gradient(135deg, #1A0A03 0%, #0D0604 50%, #1C4A2E 100%);"
    )

def coffee_img_tag(b64: str | None, alt: str, style: str = "") -> str:
    if b64:
        return f'<img src="{b64}" alt="{alt}" style="{style}" />'
    return ""  # hide if unavailable

CHART_THEME = dict(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#C8A97A", family="Lato, Inter, sans-serif"),
    colorway=["#D4A843","#2D6E45","#C8A97A","#F0C96A","#1C4A2E","#8B5E3C","#5DD990"],
    margin=dict(l=10, r=10, t=40, b=10),
)

def apply_theme(fig, title="", height=360):
    fig.update_layout(
        **CHART_THEME,
        title=dict(text=title, font=dict(size=14, color="#FFFFFF"), x=0.02, y=0.97),
        height=height,
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            borderwidth=0,
            font=dict(color="#C8A97A", size=11),
        ),
        xaxis=dict(
            gridcolor="rgba(212,168,67,0.08)",
            linecolor="rgba(212,168,67,0.15)",
            tickfont=dict(color="#C8A97A", size=11),
        ),
        yaxis=dict(
            gridcolor="rgba(212,168,67,0.08)",
            linecolor="rgba(212,168,67,0.15)",
            tickfont=dict(color="#C8A97A", size=11),
        ),
    )
    return fig

with st.spinner("Brewing your insights ☕..."):
    data = load_and_process_data()

customers    = data["customers"]
offers       = data["offers"]
journey      = data["journey"]
transactions = data["transactions"]
kpis         = data["kpis"]
offer_perf   = data["offer_perf"]
type_perf    = data["type_perf"]
channel_df   = data["channel_df"]
cust_trans   = data["cust_trans"]
funnel_df    = data["funnel"]
rev_time     = data["rev_time"]

with st.sidebar:
    # Sidebar logo + small coffee cup image
    cup_img = coffee_img_tag(
        imgs["cup"], "coffee cup",
        "width:56px; height:56px; object-fit:cover; border-radius:50%; "
        "border:2px solid rgba(212,168,67,0.4); margin-bottom:0.5rem; display:block; margin-left:auto; margin-right:auto;"
    )
    st.markdown(f"""
    <div style="text-align:center; padding: 1rem 0;">
        {cup_img if cup_img else '<div style="font-size:2.4rem; text-align:center">☕</div>'}
        <h2 style="color:#D4A843; margin:0.3rem 0 0.1rem; font-family:Georgia,serif;">Cafe Rewards</h2>
        <p style="color:#C8A97A; font-size:0.7rem; letter-spacing:0.15em;">INTELLIGENCE PLATFORM</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("#### 🎛️ Dashboard Filters")

    offer_types = ["All"] + sorted(journey["offer_type"].dropna().unique().tolist())
    sel_offer   = st.selectbox("Offer Type", offer_types)

    genders = ["All"] + sorted(customers["gender"].unique().tolist())
    sel_gender = st.selectbox("Customer Gender", genders)

    age_groups = ["All"] + [str(a) for a in customers["age_group"].cat.categories]
    sel_age    = st.selectbox("Age Group", age_groups)

    channels_list = ["All","Email","Mobile","Web","Social"]
    sel_channel   = st.selectbox("Offer Channel", channels_list)

    st.markdown("---")

    # Coffee beans image in sidebar
    beans_img = coffee_img_tag(
        imgs["beans"], "coffee beans",
        "width:100%; border-radius:10px; opacity:0.55; margin-bottom:0.5rem; border:1px solid rgba(212,168,67,0.2);"
    )
    if beans_img:
        st.markdown(beans_img, unsafe_allow_html=True)

    st.markdown("""
    <div style="font-size:0.72rem; color:rgba(200,169,122,0.45); line-height:1.6;">
        📊 Dataset: Starbucks Rewards Simulation<br>
        🗓️ 17,000 customers · 10 offers · 306K events
    </div>
    """, unsafe_allow_html=True)

# ── APPLY FILTERS 
def filter_journey(jdf):
    df = jdf.copy()
    if sel_offer  != "All": df = df[df["offer_type"] == sel_offer]
    if sel_gender != "All": df = df[df["gender"]     == sel_gender]
    if sel_age    != "All": df = df[df["age_group"].astype(str) == sel_age]
    if sel_channel != "All":
        ch_col = f"channel_{sel_channel.lower()}"
        if ch_col in df.columns:
            df = df[df[ch_col] == True]
    return df

jdf               = filter_journey(journey)
filt_transactions = transactions[transactions["customer_id"].isin(jdf["customer_id"].unique())]
filt_revenue      = filt_transactions["amount"].sum()
filt_cust         = jdf["customer_id"].nunique()
filt_tx           = len(filt_transactions)
filt_comp         = jdf["was_completed"].mean() * 100 if len(jdf) else 0

# SECTION 1 — HERO  (now with REAL coffee background image)

st.markdown(f"""
<div style="{hero_bg_style(imgs['hero'])}
     border: 1px solid rgba(212,168,67,0.28);
     border-radius: 18px;
     padding: 2.8rem 2.5rem;
     text-align: center;
     margin-bottom: 1.5rem;
     position: relative;
     overflow: hidden;
     box-shadow: 0 24px 64px rgba(0,0,0,0.5);">

  <!-- Coffee ring watermark on hero -->
  <div style="position:absolute; top:-60px; right:-60px; width:260px; height:260px;
       border-radius:50%; border:18px solid rgba(212,168,67,0.07);
       box-shadow: inset 0 0 0 8px rgba(200,169,122,0.04); pointer-events:none;"></div>
  <div style="position:absolute; bottom:-80px; left:-40px; width:220px; height:220px;
       border-radius:50%; border:14px solid rgba(200,169,122,0.05); pointer-events:none;"></div>

  <div style="position:relative; z-index:1;">
    <div style="display:inline-block; background:rgba(212,168,67,0.14); border:1px solid rgba(212,168,67,0.35);
         border-radius:20px; padding:4px 18px; font-size:0.68rem; color:#D4A843;
         letter-spacing:0.18em; margin-bottom:1rem; font-weight:600;">
      ☕ PREMIUM ANALYTICS PLATFORM
    </div>
    <h1 style="color:#FFFFFF; font-size:2.5rem; margin:0 0 0.5rem 0;
        font-family:'Playfair Display', Georgia, serif; text-shadow:0 3px 24px rgba(0,0,0,0.6);">
      Cafe Rewards <span style="color:#F0C96A;">Intelligence Platform</span>
    </h1>
    <p style="color:rgba(232,213,176,0.78); margin-bottom:1.4rem; font-size:1rem; font-weight:300; letter-spacing:0.04em;">
      Customer Behavior &nbsp;·&nbsp; Campaign Analytics &nbsp;·&nbsp; Revenue Intelligence
    </p>
    <div>
      <span style="background:rgba(212,168,67,0.12); border:1px solid rgba(212,168,67,0.25);
           border-radius:20px; padding:5px 16px; color:#C8A97A; font-size:0.8rem; margin:4px; display:inline-block;">
        📊 17,000 Customers
      </span>
      <span style="background:rgba(212,168,67,0.12); border:1px solid rgba(212,168,67,0.25);
           border-radius:20px; padding:5px 16px; color:#C8A97A; font-size:0.8rem; margin:4px; display:inline-block;">
        🎯 10 Active Offers
      </span>
      <span style="background:rgba(212,168,67,0.12); border:1px solid rgba(212,168,67,0.25);
           border-radius:20px; padding:5px 16px; color:#C8A97A; font-size:0.8rem; margin:4px; display:inline-block;">
        ⚡ 306K Events Analyzed
      </span>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Coffee imagery strip (visible only when images load) ──────
if imgs["beans"] or imgs["cup"] or imgs["hero"]:
    img_cols = st.columns([1, 1, 1, 3])
    with img_cols[0]:
        if imgs["cup"]:
            st.markdown(
                f'<img src="{imgs["cup"]}" style="width:100%; border-radius:12px; '
                f'height:120px; object-fit:cover; border:1px solid rgba(212,168,67,0.2);" />',
                unsafe_allow_html=True,
            )
    with img_cols[1]:
        if imgs["beans"]:
            st.markdown(
                f'<img src="{imgs["beans"]}" style="width:100%; border-radius:12px; '
                f'height:120px; object-fit:cover; border:1px solid rgba(212,168,67,0.2);" />',
                unsafe_allow_html=True,
            )
    with img_cols[2]:
        if imgs["hero"]:
            st.markdown(
                f'<img src="{imgs["hero"]}" style="width:100%; border-radius:12px; '
                f'height:120px; object-fit:cover; border:1px solid rgba(212,168,67,0.2);" />',
                unsafe_allow_html=True,
            )
    with img_cols[3]:
        st.markdown("""
        <div style="height:120px; display:flex; align-items:center; padding-left:1rem;">
          <p style="color:rgba(200,169,122,0.6); font-size:0.8rem; line-height:1.7; margin:0;">
            ☕ &nbsp; <em>From a single espresso shot to enterprise-scale loyalty intelligence —<br>
            every data point brewed to perfection.</em>
          </p>
        </div>""", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

# SECTION 2 — KPI CARDS
st.markdown("""
<h3 style="color:#D4A843; margin-bottom:0; font-family:Georgia,serif;">Executive KPIs</h3>
<p style="color:#C8A97A; font-size:0.85rem; margin-top:2px;">Real-time performance metrics</p>
<hr style="border-color:rgba(212,168,67,0.2); margin-bottom:1rem;">
""", unsafe_allow_html=True)

c1, c2, c3, c4, c5 = st.columns(5)

def kpi_card(col, icon, value, label, delta=""):
    with col:
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#1A0A03,#0D0604);
             border:1px solid rgba(212,168,67,0.2); border-radius:12px;
             padding:1.2rem; text-align:center; position:relative; overflow:hidden;">
          <!-- subtle coffee ring watermark inside card -->
          <div style="position:absolute; bottom:-30px; right:-30px; width:90px; height:90px;
               border-radius:50%; border:8px solid rgba(212,168,67,0.05); pointer-events:none;"></div>
          <div style="font-size:1.6rem;">{icon}</div>
          <div style="font-size:1.5rem; font-weight:700; color:#F0C96A; font-family:Georgia,serif;">{value}</div>
          <div style="font-size:0.75rem; color:#C8A97A; margin-top:2px;">{label}</div>
          <div style="font-size:0.7rem; color:rgba(200,169,122,0.55); margin-top:4px;">{delta}</div>
        </div>""", unsafe_allow_html=True)

view_rate = jdf["was_viewed"].mean() * 100 if len(jdf) else 0
kpi_card(c1, "💰", f"${filt_revenue:,.0f}",     "Total Revenue",       "↑ Campaign Driven")
kpi_card(c2, "👥", f"{filt_cust:,}",            "Customers Reached",   f"{filt_cust/kpis['total_customers']*100:.0f}% of base")
kpi_card(c3, "🧾", f"{filt_tx:,}",              "Transactions",        f"Avg ${filt_transactions['amount'].mean():.2f}" if filt_tx else "—")
kpi_card(c4, "✅", f"{filt_comp:.1f}%",         "Completion Rate",     "Offer fulfilled")
kpi_card(c5, "👁️", f"{view_rate:.1f}%",         "View Rate",           "Offer engagement")
st.markdown("<br>", unsafe_allow_html=True)


# SECTION 3 — CONVERSION FUNNEL + REVENUE OVER TIME

st.markdown("""
<h3 style="color:#D4A843; margin-bottom:0; font-family:Georgia,serif;">Customer Conversion Funnel</h3>
<p style="color:#C8A97A; font-size:0.85rem; margin-top:2px;">Journey from offer receipt to transaction</p>
<hr style="border-color:rgba(212,168,67,0.2); margin-bottom:1rem;">
""", unsafe_allow_html=True)

col_funnel, col_rev = st.columns([1, 1])

with col_funnel:
    f_recv      = len(jdf)
    f_viewed    = int(jdf["was_viewed"].sum())
    f_completed = int(jdf["was_completed"].sum())
    f_tx        = len(filt_transactions)

    funnel_fig = go.Figure(go.Funnel(
        y=["Offer Received","Offer Viewed","Offer Completed","Transaction Made"],
        x=[f_recv, f_viewed, f_completed, f_tx],
        textinfo="value+percent initial",
        textfont=dict(color="#FFFFFF", size=13),
        marker=dict(
            color=["#3B1F0E","#2D6E45","#D4A843","#F0C96A"],
            line=dict(width=1.5, color="rgba(212,168,67,0.4)"),
        ),
        connector=dict(line=dict(color="rgba(212,168,67,0.2)", width=1)),
    ))
    funnel_fig = apply_theme(funnel_fig, "☕ Offer-to-Transaction Journey", height=370)
    funnel_fig.update_layout(
        xaxis=dict(visible=False),
        yaxis=dict(gridcolor="rgba(0,0,0,0)", linecolor="rgba(0,0,0,0)"),
    )
    st.plotly_chart(funnel_fig, use_container_width=True)

with col_rev:
    rev_fig = go.Figure()
    rev_fig.add_trace(go.Scatter(
        x=rev_time["week"], y=rev_time["revenue"],
        mode="lines", fill="tozeroy",
        line=dict(color="#D4A843", width=2.5, shape="spline"),
        fillcolor="rgba(212,168,67,0.12)",
        name="Revenue",
        hovertemplate="Week %{x}<br>Revenue: $%{y:,.0f}<extra></extra>",
    ))
    rev_time_copy            = rev_time.copy()
    rev_time_copy["rolling"] = rev_time_copy["revenue"].rolling(3, min_periods=1).mean()
    rev_fig.add_trace(go.Scatter(
        x=rev_time_copy["week"], y=rev_time_copy["rolling"],
        mode="lines",
        line=dict(color="#5DD990", width=1.5, dash="dot"),
        name="3-wk Avg",
        hovertemplate="Week %{x}<br>Avg: $%{y:,.0f}<extra></extra>",
    ))
    rev_fig = apply_theme(rev_fig, "📈 Revenue Trend Over Time", height=370)
    rev_fig.update_layout(xaxis_title="Campaign Week", yaxis_title="Revenue ($)", showlegend=True)
    st.plotly_chart(rev_fig, use_container_width=True)

# SECTION 4 — OFFER PERFORMANCE
st.markdown("""
<h3 style="color:#D4A843; margin-bottom:0; font-family:Georgia,serif;">Offer Performance Analysis</h3>
<p style="color:#C8A97A; font-size:0.85rem; margin-top:2px;">Breakdown by offer type & engagement metrics</p>
<hr style="border-color:rgba(212,168,67,0.2); margin-bottom:1rem;">
""", unsafe_allow_html=True)

col_bar, col_donut = st.columns([3, 2])

with col_bar:
    tp = jdf.groupby("offer_type").agg(
        received   = ("customer_id",  "count"),
        viewed     = ("was_viewed",   "sum"),
        completed  = ("was_completed","sum"),
    ).reset_index()
    tp["view_rate"]       = tp["viewed"]    / tp["received"] * 100
    tp["completion_rate"] = tp["completed"] / tp["received"] * 100

    bar_fig = go.Figure()
    bar_fig.add_trace(go.Bar(
        name="View Rate %", x=tp["offer_type"], y=tp["view_rate"],
        marker_color="#C8A97A",
        text=tp["view_rate"].round(1).astype(str) + "%",
        textposition="outside", textfont=dict(color="#C8A97A"),
    ))
    bar_fig.add_trace(go.Bar(
        name="Completion Rate %", x=tp["offer_type"], y=tp["completion_rate"],
        marker_color="#D4A843",
        text=tp["completion_rate"].round(1).astype(str) + "%",
        textposition="outside", textfont=dict(color="#F0C96A"),
    ))
    bar_fig = apply_theme(bar_fig, "🎯 Offer Type — View & Completion Rates", height=340)
    bar_fig.update_layout(barmode="group", xaxis_title="", yaxis_title="Rate (%)")
    st.plotly_chart(bar_fig, use_container_width=True)

with col_donut:
    donut_fig = go.Figure(go.Pie(
        labels=tp["offer_type"], values=tp["received"],
        hole=0.62,
        textinfo="label+percent",
        textfont=dict(color="#FFFFFF", size=12),
        marker=dict(
            colors=["#D4A843","#2D6E45","#C8A97A","#1C4A2E"],
            line=dict(color="#0D0604", width=2),
        ),
        hovertemplate="%{label}<br>Offers Sent: %{value:,}<extra></extra>",
    ))
    donut_fig.add_annotation(
        text=f"<b>{len(jdf):,}</b><br><span style='font-size:10px'>Total Offers</span>",
        x=0.5, y=0.5, showarrow=False,
        font=dict(size=16, color="#F0C96A"),
    )
    donut_fig = apply_theme(donut_fig, "📊 Offer Distribution", height=340)
    donut_fig.update_layout(showlegend=False)
    st.plotly_chart(donut_fig, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)
op_filtered = jdf.groupby("offer_type").agg(
    received   = ("customer_id",  "count"),
    viewed     = ("was_viewed",   "sum"),
    completed  = ("was_completed","sum"),
).reset_index()
op_filtered["view_rate"]       = (op_filtered["viewed"]    / op_filtered["received"] * 100).round(1)
op_filtered["completion_rate"] = (op_filtered["completed"] / op_filtered["received"] * 100).round(1)
op_filtered.columns = ["Offer Type","Received","Viewed","Completed","View Rate %","Completion Rate %"]
st.dataframe(op_filtered, use_container_width=True, hide_index=True)

# SECTION 5 — CUSTOMER ANALYTICS

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("""
<h3 style="color:#D4A843; margin-bottom:0; font-family:Georgia,serif;">Customer Analytics</h3>
<p style="color:#C8A97A; font-size:0.85rem; margin-top:2px;">Demographics, segments & spending behaviour</p>
<hr style="border-color:rgba(212,168,67,0.2); margin-bottom:1rem;">
""", unsafe_allow_html=True)

col_age, col_gender, col_income = st.columns(3)

with col_age:
    age_data = jdf.groupby("age_group", observed=True).agg(
        customers       = ("customer_id", "nunique"),
        completion_rate = ("was_completed","mean"),
    ).reset_index()
    age_data["completion_pct"] = age_data["completion_rate"] * 100

    age_fig = go.Figure(go.Bar(
        x=age_data["age_group"].astype(str),
        y=age_data["customers"],
        marker=dict(
            color=age_data["completion_pct"],
            colorscale=[[0,"#1A0A03"],[0.5,"#3B1F0E"],[1,"#D4A843"]],
            showscale=True,
            colorbar=dict(
                title=dict(text="Completion %", font=dict(color="#C8A97A", size=10)),
                tickfont=dict(color="#C8A97A", size=9),
                len=0.6,
            ),
        ),
        hovertemplate="Age: %{x}<br>Customers: %{y}<br>Completion: %{marker.color:.1f}%<extra></extra>",
    ))
    age_fig = apply_theme(age_fig, "👤 Customers by Age Group", height=300)
    age_fig.update_layout(xaxis_title="", yaxis_title="Customers")
    st.plotly_chart(age_fig, use_container_width=True)

with col_gender:
    gen_data         = jdf.groupby("gender")["customer_id"].nunique().reset_index()
    gen_data.columns = ["gender","count"]
    gen_fig = go.Figure(go.Pie(
        labels=gen_data["gender"], values=gen_data["count"],
        hole=0.58,
        textinfo="label+percent",
        textfont=dict(color="#FFFFFF", size=12),
        marker=dict(colors=["#D4A843","#2D6E45","#8B5E3C"], line=dict(color="#0D0604", width=2)),
    ))
    gen_fig.add_annotation(text="Gender", x=0.5, y=0.5, showarrow=False, font=dict(size=13, color="#C8A97A"))
    gen_fig = apply_theme(gen_fig, "⚧ Gender Split", height=300)
    gen_fig.update_layout(showlegend=True)
    st.plotly_chart(gen_fig, use_container_width=True)

with col_income:
    inc_data         = jdf.groupby("income_group", observed=True)["customer_id"].nunique().reset_index()
    inc_data.columns = ["income_group","count"]
    inc_fig = go.Figure(go.Bar(
        x=inc_data["income_group"].astype(str),
        y=inc_data["count"],
        marker=dict(
            color=["#1C4A2E","#2D6E45","#D4A843","#F0C96A","#FFFFFF","#C8A97A"],
            line=dict(color="rgba(0,0,0,0)"),
        ),
        text=inc_data["count"], textposition="outside", textfont=dict(color="#C8A97A"),
    ))
    inc_fig = apply_theme(inc_fig, "💵 Customers by Income Band", height=300)
    inc_fig.update_layout(xaxis_title="", yaxis_title="Customers", showlegend=False)
    st.plotly_chart(inc_fig, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)
ct = cust_trans[cust_trans["customer_id"].isin(jdf["customer_id"].unique())]
scatter_fig = px.scatter(
    ct.dropna(subset=["income","total_spend","age"]),
    x="income", y="total_spend",
    color="segment", size="num_transactions", size_max=18,
    hover_data={"age":True,"gender":True,"num_transactions":True},
    color_discrete_map={"High Value":"#F0C96A","Mid Value":"#2D6E45","Low Value":"#8B5E3C"},
    labels={"income":"Annual Income ($)","total_spend":"Total Spend ($)"},
)
scatter_fig = apply_theme(scatter_fig, "💎 Customer Segments — Income vs. Total Spend", height=380)
scatter_fig.update_traces(marker_line=dict(width=0.5, color="rgba(0,0,0,0.4)"))
scatter_fig.update_layout(xaxis_tickprefix="$", yaxis_tickprefix="$", legend_title_text="Segment")
st.plotly_chart(scatter_fig, use_container_width=True)

# SECTION 6 — CHANNEL ANALYTICS
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("""
<h3 style="color:#D4A843; margin-bottom:0; font-family:Georgia,serif;">Marketing Channel Analytics</h3>
<p style="color:#C8A97A; font-size:0.85rem; margin-top:2px;">Engagement & conversion by distribution channel</p>
<hr style="border-color:rgba(212,168,67,0.2); margin-bottom:1rem;">
""", unsafe_allow_html=True)

col_ch1, col_ch2 = st.columns([2, 1])

with col_ch1:
    ch_fig = go.Figure()
    ch_fig.add_trace(go.Bar(
        name="Offers Sent",  x=channel_df["channel"], y=channel_df["offers_sent"],
        marker_color="#3B1F0E", yaxis="y",
    ))
    ch_fig.add_trace(go.Bar(
        name="Completions",  x=channel_df["channel"], y=channel_df["completions"],
        marker_color="#D4A843", yaxis="y",
    ))
    ch_fig.add_trace(go.Scatter(
        name="Completion Rate %", x=channel_df["channel"], y=channel_df["completion_rate"],
        mode="lines+markers",
        line=dict(color="#5DD990", width=2.5),
        marker=dict(size=9, color="#5DD990"),
        yaxis="y2",
    ))
    ch_fig = apply_theme(ch_fig, "📡 Channel Performance — Volume & Conversion", height=340)
    ch_fig.update_layout(
        barmode="group",
        yaxis =dict(title="Count",            gridcolor="rgba(212,168,67,0.08)", tickfont=dict(color="#C8A97A")),
        yaxis2=dict(title="Completion Rate %", overlaying="y", side="right",
                    tickfont=dict(color="#5DD990"), gridcolor="rgba(0,0,0,0)"),
        legend=dict(orientation="h", y=-0.15),
    )
    st.plotly_chart(ch_fig, use_container_width=True)

with col_ch2:
    ch_pie = go.Figure(go.Pie(
        labels=channel_df["channel"], values=channel_df["offers_sent"],
        hole=0.5,
        textinfo="label+percent",
        textfont=dict(color="#FFFFFF", size=11),
        marker=dict(colors=["#D4A843","#2D6E45","#C8A97A","#1C4A2E"], line=dict(color="#0D0604", width=2)),
    ))
    ch_pie = apply_theme(ch_pie, "Channel Mix", height=340)
    ch_pie.update_layout(showlegend=False)
    st.plotly_chart(ch_pie, use_container_width=True)

# SECTION 7 — AI BUSINESS INSIGHTS

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("""
<h3 style="color:#D4A843; margin-bottom:0; font-family:Georgia,serif;">AI Business Insights</h3>
<p style="color:#C8A97A; font-size:0.85rem; margin-top:2px;">Data-driven intelligence generated from your campaign</p>
<hr style="border-color:rgba(212,168,67,0.2); margin-bottom:1rem;">
""", unsafe_allow_html=True)

best_offer_type  = type_perf.sort_values("completion_rate", ascending=False).iloc[0]["offer_type"]
best_comp_rate   = type_perf.sort_values("completion_rate", ascending=False).iloc[0]["completion_rate"]
worst_offer      = type_perf.sort_values("completion_rate").iloc[0]["offer_type"]
worst_comp_rate  = type_perf.sort_values("completion_rate").iloc[0]["completion_rate"]
best_channel     = channel_df.sort_values("completion_rate", ascending=False).iloc[0]["channel"]
top_segment      = cust_trans.groupby("segment")["total_spend"].sum().idxmax()
inactive_count   = customers["customer_id"].nunique() - cust_trans[cust_trans["total_spend"] > 0]["customer_id"].nunique()
view_gap         = kpis["view_rate"] - kpis["completion_rate"]

def insight_card(icon, title, body, color="#D4A843"):
    border = "1px solid rgba(212,168,67,0.2)"
    if color == "warning": border = "1px solid rgba(255,180,0,0.3)"
    elif color == "info":  border = "1px solid rgba(93,217,144,0.3)"
    return f"""
    <div style="background:linear-gradient(135deg,#1A0A03,#0D0604); border:{border};
         border-radius:12px; padding:1.1rem 1.2rem; margin-bottom:0.8rem;
         display:flex; gap:0.8rem; align-items:flex-start;">
      <div style="font-size:1.5rem; flex-shrink:0;">{icon}</div>
      <div>
        <div style="color:#F0C96A; font-size:0.8rem; font-weight:600;
             text-transform:uppercase; letter-spacing:0.05em; margin-bottom:4px;">{title}</div>
        <div style="color:#C8A97A; font-size:0.85rem; line-height:1.5;">{body}</div>
      </div>
    </div>"""

icol1, icol2 = st.columns(2)
with icol1:
    st.markdown(
        insight_card("🏆","Top-Converting Offer Type",
            f"<b>{best_offer_type.title()}</b> offers lead with <b>{best_comp_rate:.1f}%</b> completion — "
            "the strongest driver of customer action in your portfolio.") +
        insight_card("📡","Highest Performing Channel",
            f"The <b>{best_channel}</b> channel delivers the best conversion rate. "
            "Prioritise budget allocation here for maximum ROI.", "info") +
        insight_card("💎","Dominant Customer Segment",
            f"<b>{top_segment}</b> customers contribute the most cumulative revenue. "
            "Exclusive loyalty perks for this segment can boost lifetime value."),
        unsafe_allow_html=True)

with icol2:
    st.markdown(
        insight_card("⚠️","View-to-Completion Drop-off",
            f"A <b>{view_gap:.1f}%</b> gap exists between customers who view an offer and those who "
            "complete it. Simplifying offer terms can recover this lost conversion.", "warning") +
        insight_card("😴","Dormant Customer Opportunity",
            f"Approximately <b>{inactive_count:,}</b> customers have never transacted. "
            "A targeted re-engagement campaign with low-difficulty offers can unlock untapped revenue.", "warning") +
        insight_card("📉","Under-performing Offer Type",
            f"<b>{worst_offer.title()}</b> offers show the lowest completion at "
            f"<b>{worst_comp_rate:.1f}%</b>. Consider revising reward structures or delivery channels.", "info"),
        unsafe_allow_html=True)

# SECTION 8 — STRATEGIC RECOMMENDATIONS

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("""
<h3 style="color:#D4A843; margin-bottom:0; font-family:Georgia,serif;">Strategic Recommendations</h3>
<p style="color:#C8A97A; font-size:0.85rem; margin-top:2px;">Actionable growth strategies for the next campaign cycle</p>
<hr style="border-color:rgba(212,168,67,0.2); margin-bottom:1rem;">
""", unsafe_allow_html=True)

recommendations = [
    ("Double down on high-converting offer types",
     f"<b>{best_offer_type.title()}</b> offers achieve {best_comp_rate:.1f}% completion. "
     "Increase campaign budget allocation for this category by 20–30% in the next quarter."),
    ("Re-engage dormant customers with low-barrier offers",
     f"<b>{inactive_count:,}</b> customers have not transacted. Deploy informational or low-difficulty "
     "BOGO offers through their preferred channels to reignite engagement."),
    (f"Maximise {best_channel} channel investment",
     f"{best_channel} delivers the best conversion metrics. Expand reach on this channel "
     "and A/B test creative variants to further improve performance."),
    ("Reduce offer difficulty for low-income segments",
     "Customers in the <$60K income band show lower completion rates. Lowering "
     "spend thresholds for this segment can substantially improve conversion."),
    ("Implement tiered rewards for High Value customers",
     f"<b>{top_segment}</b> customers drive disproportionate revenue. A dedicated VIP tier "
     "with exclusive perks and early-access offers increases retention and referral rates."),
    ("Personalise offers by age cohort",
     "Customers aged 55–74 form the largest demographic. Tailoring offer types and "
     "communication style to this cohort's preferences will improve overall campaign ROI."),
]

for i, (title, body) in enumerate(recommendations, 1):
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#1A0A03,#0D0604);
         border:1px solid rgba(212,168,67,0.2); border-left:3px solid #D4A843;
         border-radius:10px; padding:1rem 1.2rem; margin-bottom:0.7rem;
         display:flex; gap:1rem; align-items:flex-start;">
      <div style="background:#D4A843; color:#0D0604; font-weight:700; font-size:0.85rem;
           border-radius:50%; width:28px; height:28px;
           display:flex; align-items:center; justify-content:center; flex-shrink:0;">{i}</div>
      <div style="color:#C8A97A; font-size:0.88rem; line-height:1.6;">
        <strong style="color:#F0C96A;">{title}</strong><br>{body}
      </div>
    </div>""", unsafe_allow_html=True)

# FOOTER

st.markdown("<br>", unsafe_allow_html=True)

# Footer with small coffee image if available
footer_img = coffee_img_tag(
    imgs["cup"], "coffee",
    "width:40px; height:40px; object-fit:cover; border-radius:50%; "
    "border:1px solid rgba(212,168,67,0.25); vertical-align:middle; margin-right:10px; opacity:0.7;"
)
st.markdown(f"""
<div style="text-align:center; padding:1.5rem 0; border-top:1px solid rgba(212,168,67,0.15);">
  {footer_img}<span style="font-size:1.4rem; vertical-align:middle;">☕</span>
  <p style="color:rgba(200,169,122,0.45); font-size:0.72rem; margin-top:6px; letter-spacing:0.12em;">
    CAFE REWARDS INTELLIGENCE PLATFORM · POWERED BY STREAMLIT & PLOTLY
  </p>
</div>
""", unsafe_allow_html=True)
