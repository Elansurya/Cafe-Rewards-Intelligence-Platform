# ☕ Cafe Rewards Intelligence Platform

> Analyzes 306K+ behavioral events across 17,000 customers to deliver campaign intelligence,
> offer optimization, and customer segmentation insights — built as a premium Streamlit
> analytics dashboard for executive and operational audiences.

![Python](https://img.shields.io/badge/Python-3.10-blue?style=flat-square)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35-FF4B4B?style=flat-square)
![Plotly](https://img.shields.io/badge/Plotly-5.22-3D4B96?style=flat-square)
![Pandas](https://img.shields.io/badge/Pandas-2.2-green?style=flat-square)
![HuggingFace](https://img.shields.io/badge/HuggingFace-Live%20Demo-yellow?style=flat-square)
![Status](https://img.shields.io/badge/Status-Deployed-brightgreen?style=flat-square)

🔗 **[Live Demo → Hugging Face Spaces](https://huggingface.co/spaces/Elansurya/cafe-rewards-intelligence-platform)**

---

## Problem Statement

Cafe and retail loyalty programs generate millions of behavioral events across customer
interactions — yet most businesses analyze this data in silos, missing cross-channel
insights and offer optimization opportunities. Traditional reporting tools lack the
analytical depth to connect offer receipt, engagement, completion, and transaction
behavior into a unified customer intelligence view.

This project builds a premium end-to-end Streamlit analytics platform that transforms
raw transactional and campaign event data into executive-grade business intelligence —
enabling data-driven decisions on offer design, channel investment, and customer
segmentation strategy.

---

## Dataset

| Property          | Detail                                                                 |
|---|---|
| Total Customers   | 17,000 unique customer profiles                                        |
| Total Events      | 306,534 behavioral events                                              |
| Offer Types       | 10 active offer configurations                                         |
| Event Types       | offer received, offer viewed, offer completed, transaction             |
| Features          | 28 variables — age, gender, income, membership date, channel, etc.    |
| Target Variable   | Offer completion + transaction conversion                              |
| Data Source       | Starbucks Rewards Program Simulation (Kaggle)                          |

---

## Tech Stack

| Layer              | Tools                                                     |
|---|---|
| Language           | Python 3.10                                               |
| App Framework      | Streamlit 1.35                                            |
| Data Processing    | Pandas 2.2, NumPy 1.26                                    |
| Visualisation      | Plotly 5.22 (interactive charts only)                     |
| Styling            | Custom CSS — glassmorphism, cafe-themed dark UI            |
| Deployment         | Hugging Face Spaces (Streamlit SDK)                       |
| Analytics Modules  | Conversion funnel, RFM segmentation, channel analytics    |

---

## Workflow

Raw 306K+ Behavioral Events (3 CSV files)
↓
Data Cleaning & Preprocessing
├── Remove placeholder ages (age = 118 sentinel value)
├── Median imputation for missing income values
├── Parse membership dates from YYYYMMDD integer format
└── Parse nested dict strings in events.value using ast.literal_eval
↓
Feature Engineering
├── Age groups: 18-24, 25-34, 35-44, 45-54, 55-64, 65-74, 75+
├── Income bands: <40K, 40-60K, 60-80K, 80-100K, 100K+
├── Membership duration in days from join date
├── Offer channel boolean flags (email, mobile, web, social)
└── Customer spend segments: High / Mid / Low Value (quartile-based)
↓
Dataset Merging
├── events → split by type (received, viewed, completed, transaction)
├── Left-join journey: received ← viewed ← completed
└── Attach offer metadata and customer demographics
↓
Analytics & KPI Computation
├── Total revenue, completion rate, view rate, avg transaction value
├── Offer performance by type: view rate and completion rate
├── Channel analytics: offers sent, completions, conversion rate
└── Revenue time series (weekly buckets, 3-week rolling average)
↓
Dashboard Rendering
├── 8 interactive sections with Plotly charts + custom CSS UI
└── Sidebar filters: Offer Type, Gender, Age Group, Channel — all reactive

---

## Dashboard Sections

| Section               | Description                                                                    |
|---|---|
| 🏆 Hero Header        | Brand-consistent full-width banner with live dataset stats                     |
| 📊 Executive KPIs     | 5 animated cards: Revenue · Customers · Transactions · Completion · View Rate  |
| 🔽 Conversion Funnel  | Plotly funnel: Offer Received → Viewed → Completed → Transaction Made          |
| 📈 Revenue Trend      | Weekly revenue area chart with 3-week rolling average overlay                  |
| 🎯 Offer Performance  | Grouped bar + donut distribution + detail table by offer type                  |
| 👤 Customer Analytics | Age heatmap · Gender donut · Income band · Income vs Spend scatter plot        |
| 📡 Channel Analytics  | Dual-axis bar+line chart (volume & conversion rate) + channel mix donut        |
| 🤖 AI Insights        | 6 dynamically computed insight cards from actual dataset metrics               |
| 📋 Recommendations    | 6 prioritised, data-backed strategic action items for campaign optimisation    |

---

## Results — Key Metrics

| Metric                    | Value                                            |
|---|---|
| Total Revenue Generated   | $1,770,000+                                      |
| Customers Analyzed        | 14,825 (after age cleaning)                      |
| Total Behavioral Events   | 306,534                                          |
| Offer Completion Rate     | ~58%                                             |
| Offer View Rate           | ~72%                                             |
| Avg Transaction Value     | ~$13.00                                          |
| Best Offer Type           | Discount (highest completion rate)               |
| Best Marketing Channel    | Mobile (highest conversion rate)                 |
| Dominant Customer Segment | High Value — drives majority of revenue          |

---

## AI Insights Generated

| Insight                        | Description                                                        |
|---|---|
| 🏆 Top-Converting Offer Type   | Best-performing offer with exact completion rate                   |
| 📡 Highest Performing Channel  | Which marketing channel drives the most conversions                |
| 💎 Dominant Customer Segment   | Which spend segment contributes the most cumulative revenue        |
| ⚠️ View-to-Completion Drop-off | Gap between offer views and completions — quantified               |
| 😴 Dormant Customer Pool       | Customers who never transacted — untapped revenue opportunity      |
| 📉 Under-performing Offer Type | Lowest-completion offer category with specific improvement advice  |

---

## Project Structure
CafeRewardsAI/
├── app.py                ← Main Streamlit app (single-file, no imports needed)
├── style.css             ← Premium cafe-themed glassmorphism CSS
├── requirements.txt      ← Python dependencies
├── README.md             ← Project documentation
├── data/
│   ├── customers.csv     ← 17,000 customer profiles
│   ├── offers.csv        ← 10 offer configurations
│   └── events.csv        ← 306,534 behavioral events
└── utils/
└── data_loader.py    ← ETL pipeline (modular version, cached)
---

## Installation

```bash
# Clone the repository
git clone https://github.com/Elansurya/cafe-rewards-intelligence-platform.git
cd cafe-rewards-intelligence-platform

# Install dependencies
pip install -r requirements.txt

# Run the dashboard
streamlit run app.py
```

---

## Requirements
streamlit==1.35.0
pandas==2.2.2
numpy==1.26.4
plotly==5.22.0
pillow==10.3.0
---

## Business Impact

- **Campaign ROI Clarity:** Quantifies which offer types and channels deliver the highest
  conversion — directly informing budget allocation decisions
- **Customer Intelligence:** RFM-style segmentation enables personalised retention and
  upsell strategies for High / Mid / Low Value customers
- **Dormant Re-engagement:** Identifies thousands of non-transacting customers as a
  high-potential revenue recovery pool
- **Executive Reporting:** Real-time interactive dashboard replaces manual reporting —
  accessible to non-technical stakeholders
- **Competition Differentiation:** Glassmorphism premium UI, multi-section analytical
  storytelling, and reactive filters set it apart from standard dashboards

---

## Author

**Elansurya K** — Aspiring Data Scientist | Streamlit · Plotly · Python · SQL

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-blue?style=flat-square&logo=linkedin)](https://linkedin.com/in/elansurya-karthikeyan-3b6636380)
[![GitHub](https://img.shields.io/badge/GitHub-Profile-black?style=flat-square&logo=github)](https://github.com/Elansurya)
[![HuggingFace](https://img.shields.io/badge/HuggingFace-Live%20Demo-yellow?style=flat-square)](https://huggingface.co/spaces/Elansurya/cafe-rewards-intelligence-platform)
