import numpy as np
import pandas as pd
import streamlit as st

RNG = np.random.default_rng(42)

# CONSTANTS
N_CUSTOMERS  = 17_000
N_OFFERS     = 10
OFFER_TYPES  = ["bogo", "discount", "informational"]
CHANNELS     = ["email", "mobile", "web", "social"]
AGE_BINS     = [18, 25, 35, 45, 55, 65, 75, 100]
AGE_LABELS   = ["18-24", "25-34", "35-44", "45-54", "55-64", "65-74", "75+"]
INCOME_BINS  = [0, 40_000, 60_000, 80_000, 100_000, 120_000, 200_000]
INCOME_LABELS= ["<40K", "40-60K", "60-80K", "80-100K", "100-120K", "120K+"]
GENDERS      = ["M", "F", "O"]

# HELPER — reproducible choice

def choice(arr, size, p=None):
    return RNG.choice(arr, size=size, p=p)


# BUILD CUSTOMERS
def _make_customers():
    age    = RNG.integers(18, 85, size=N_CUSTOMERS)
    income = RNG.normal(65_000, 25_000, size=N_CUSTOMERS).clip(15_000, 200_000)
    gender = choice(GENDERS, N_CUSTOMERS, p=[0.43, 0.49, 0.08])
    member_since = RNG.integers(2013, 2022, size=N_CUSTOMERS)

    df = pd.DataFrame({
        "customer_id":   np.arange(N_CUSTOMERS),
        "age":           age,
        "income":        income.round(0),
        "gender":        gender,
        "member_since":  member_since,
    })
    df["age_group"]    = pd.cut(df["age"],    bins=AGE_BINS,    labels=AGE_LABELS,    right=False)
    df["income_group"] = pd.cut(df["income"], bins=INCOME_BINS, labels=INCOME_LABELS, right=False)
    return df

# BUILD OFFERS

def _make_offers():
    rows = []
    for oid in range(N_OFFERS):
        otype    = OFFER_TYPES[oid % 3]
        channels = RNG.choice([True, False], size=4, p=[0.65, 0.35])
        rows.append({
            "offer_id":         oid,
            "offer_type":       otype,
            "difficulty":       RNG.integers(5, 20),
            "reward":           RNG.integers(2, 10),
            "duration":         RNG.integers(3, 10),
            "channel_email":    bool(channels[0]),
            "channel_mobile":   bool(channels[1]),
            "channel_web":      bool(channels[2]),
            "channel_social":   bool(channels[3]),
        })
    return pd.DataFrame(rows)


# BUILD JOURNEY  (offer-level events per customer)

def _make_journey(customers, offers):
    # Each customer receives ~2-4 offers
    n_rows = N_CUSTOMERS * 3
    cust_ids  = choice(customers["customer_id"].values, n_rows)
    offer_ids = choice(offers["offer_id"].values, n_rows)

    # Merge in customer + offer attributes
    cdf = customers.set_index("customer_id")
    odf = offers.set_index("offer_id")

    age_arr    = cdf.loc[cust_ids, "age"].values
    income_arr = cdf.loc[cust_ids, "income"].values
    gender_arr = cdf.loc[cust_ids, "gender"].values
    ag_arr     = cdf.loc[cust_ids, "age_group"].values
    ig_arr     = cdf.loc[cust_ids, "income_group"].values
    otype_arr  = odf.loc[offer_ids, "offer_type"].values
    ch_email   = odf.loc[offer_ids, "channel_email"].values
    ch_mobile  = odf.loc[offer_ids, "channel_mobile"].values
    ch_web     = odf.loc[offer_ids, "channel_web"].values
    ch_social  = odf.loc[offer_ids, "channel_social"].values

    # View probability influenced by channels & income
    base_view = 0.72
    view_prob = np.clip(base_view + (income_arr / 200_000) * 0.15, 0.5, 0.95)
    was_viewed = RNG.random(n_rows) < view_prob

    # Completion probability
    base_comp = np.where(otype_arr == "bogo", 0.55,
                np.where(otype_arr == "discount", 0.48, 0.30))
    comp_prob = np.clip(base_comp + (income_arr / 200_000) * 0.1, 0.20, 0.85)
    comp_prob *= was_viewed.astype(float)   # can't complete without viewing
    was_completed = RNG.random(n_rows) < comp_prob

    journey = pd.DataFrame({
        "customer_id":    cust_ids,
        "offer_id":       offer_ids,
        "offer_type":     otype_arr,
        "gender":         gender_arr,
        "age":            age_arr,
        "age_group":      pd.Categorical(ag_arr, categories=AGE_LABELS, ordered=True),
        "income":         income_arr,
        "income_group":   pd.Categorical(ig_arr, categories=INCOME_LABELS, ordered=True),
        "was_viewed":     was_viewed,
        "was_completed":  was_completed,
        "channel_email":  ch_email,
        "channel_mobile": ch_mobile,
        "channel_web":    ch_web,
        "channel_social": ch_social,
    })
    return journey

# BUILD TRANSACTIONS

def _make_transactions(customers):
    # ~15 transactions per active customer; 20% never transact
    active_mask = RNG.random(N_CUSTOMERS) > 0.20
    active_ids  = customers.loc[active_mask, "customer_id"].values

    n_tx = len(active_ids) * 15
    cust_tx  = choice(active_ids, n_tx)
    amount   = RNG.exponential(scale=8.5, size=n_tx).clip(1, 100).round(2)
    week     = RNG.integers(1, 30, size=n_tx)

    return pd.DataFrame({
        "customer_id": cust_tx,
        "amount":      amount,
        "week":        week,
    })

# CHANNEL DF

def _make_channel_df(journey):
    rows = []
    for ch in CHANNELS:
        col = f"channel_{ch}"
        sub = journey[journey[col] == True]
        sent        = len(sub)
        completions = int(sub["was_completed"].sum())
        rows.append({
            "channel":         ch.capitalize(),
            "offers_sent":     sent,
            "completions":     completions,
            "completion_rate": round(completions / sent * 100, 1) if sent else 0,
        })
    return pd.DataFrame(rows)

# CUSTOMER TRANSACTION SUMMARY

def _make_cust_trans(customers, transactions):
    tx_agg = transactions.groupby("customer_id").agg(
        total_spend    =("amount", "sum"),
        num_transactions=("amount", "count"),
    ).reset_index()

    ct = customers.merge(tx_agg, on="customer_id", how="left")
    ct["total_spend"]     = ct["total_spend"].fillna(0)
    ct["num_transactions"]= ct["num_transactions"].fillna(0).astype(int)

    # Segment
    spend_33 = ct["total_spend"].quantile(0.33)
    spend_66 = ct["total_spend"].quantile(0.66)
    ct["segment"] = pd.cut(
        ct["total_spend"],
        bins=[-1, spend_33, spend_66, 1e9],
        labels=["Low Value", "Mid Value", "High Value"],
    )
    return ct

# REVENUE OVER TIME
def _make_rev_time(transactions):
    rt = transactions.groupby("week")["amount"].sum().reset_index()
    rt.columns = ["week", "revenue"]
    rt = rt.sort_values("week").reset_index(drop=True)
    return rt

# TYPE PERFORMANCE
def _make_type_perf(journey):
    tp = journey.groupby("offer_type").agg(
        received       =("customer_id", "count"),
        viewed         =("was_viewed",  "sum"),
        completed      =("was_completed","sum"),
    ).reset_index()
    tp["view_rate"]       = tp["viewed"]    / tp["received"] * 100
    tp["completion_rate"] = tp["completed"] / tp["received"] * 100
    return tp

# OFFER PERFORMANCE (per offer_id)

def _make_offer_perf(journey):
    op = journey.groupby("offer_id").agg(
        received  =("customer_id","count"),
        viewed    =("was_viewed","sum"),
        completed =("was_completed","sum"),
    ).reset_index()
    op["view_rate"]       = op["viewed"]    / op["received"] * 100
    op["completion_rate"] = op["completed"] / op["received"] * 100
    return op
# FUNNEL DF

def _make_funnel(journey, transactions):
    return pd.DataFrame({
        "stage": ["Offer Received","Offer Viewed","Offer Completed","Transaction Made"],
        "count": [
            len(journey),
            int(journey["was_viewed"].sum()),
            int(journey["was_completed"].sum()),
            len(transactions),
        ],
    })


# GLOBAL KPIs

def _make_kpis(customers, journey, transactions, cust_trans):
    return {
        "total_revenue":    transactions["amount"].sum(),
        "total_customers":  customers["customer_id"].nunique(),
        "total_transactions": len(transactions),
        "completion_rate":  journey["was_completed"].mean() * 100,
        "view_rate":        journey["was_viewed"].mean() * 100,
        "avg_transaction":  transactions["amount"].mean(),
        "active_customers": cust_trans[cust_trans["total_spend"] > 0]["customer_id"].nunique(),
    }


# MAIN ENTRY POINT  (cached)

@st.cache_data(show_spinner=False)
def load_and_process_data():
    customers    = _make_customers()
    offers       = _make_offers()
    journey      = _make_journey(customers, offers)
    transactions = _make_transactions(customers)
    channel_df   = _make_channel_df(journey)
    cust_trans   = _make_cust_trans(customers, transactions)
    rev_time     = _make_rev_time(transactions)
    type_perf    = _make_type_perf(journey)
    offer_perf   = _make_offer_perf(journey)
    funnel       = _make_funnel(journey, transactions)
    kpis         = _make_kpis(customers, journey, transactions, cust_trans)

    return {
        "customers":   customers,
        "offers":      offers,
        "journey":     journey,
        "transactions":transactions,
        "kpis":        kpis,
        "offer_perf":  offer_perf,
        "type_perf":   type_perf,
        "channel_df":  channel_df,
        "cust_trans":  cust_trans,
        "funnel":      funnel,
        "rev_time":    rev_time,
    }
