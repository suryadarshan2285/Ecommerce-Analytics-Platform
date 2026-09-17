# E-commerce Sales & Customer Analytics Platform

An end-to-end analytics project built on Olist's Brazilian e-commerce
dataset (~96K orders, 2016-2018). Covers the full pipeline: cleaning and
loading raw data into PostgreSQL, analyzing it with SQL, segmenting
customers with K-Means clustering, and visualizing everything in a
4-page Power BI dashboard.

## Why this project

Olist is a marketplace connecting small Brazilian sellers to larger
e-commerce platforms. The dataset gives a realistic, messy, multi-table
view of a real business: separate tables for orders, customers, products,
sellers, payments, and reviews, with the kind of inconsistencies you'd
actually run into on the job (duplicate customer records, missing
delivery dates, ambiguous revenue definitions). The goal was to work
through it the way an analyst actually would - not just run a model, but
make and document real decisions along the way.

## What was done, and how

**1. Extract, transform, load (Python + PostgreSQL)**
Raw CSVs were read with pandas, cleaned (duplicates dropped, dates parsed,
category names translated from Portuguese, missing values handled), and
loaded into a PostgreSQL database designed as a star schema - four
dimension tables (customers, products, sellers, orders) and three fact
tables (order items, payments, reviews), connected by foreign keys.

**2. Business analysis (SQL)**
Wrote and interpreted a set of business queries against the warehouse:
monthly and cumulative revenue, top categories by revenue, delivery time
vs. review score, state-level late delivery rates, and an RFM
(Recency/Frequency/Monetary) base table per customer. Used joins, window
functions, CTEs, and conditional aggregates throughout.

One deliberate data decision: `freight_value` (shipping cost) is excluded
from revenue. Olist's 2016-2018 orders were fulfilled by third-party
carriers, so freight is a pass-through cost, not money the platform or
sellers actually earned - it's tracked as its own separate metric instead.

**3. Customer segmentation (Python + scikit-learn)**
Took the RFM table, log-transformed the skewed frequency and monetary
values, scaled all three features, and ran K-Means clustering (k=4,
chosen via the elbow method). The resulting segments were profiled and
labeled by hand based on their actual recency/frequency/monetary averages,
then written back to Postgres as a new table for the dashboard to use.

**4. Dashboard (Power BI)**
Connected Power BI directly to the Postgres database and built four
pages, each backed by DAX measures mirroring the SQL logic above.

## Dashboard

**Executive Overview** - revenue and order KPIs, monthly revenue trend,
cumulative revenue over time.

![Executive Overview](powerbi/screenshots/Executive_Overview.png)

**Customer Segmentation** - the four K-Means segments, their size and
R/F/M profile, and where they sit on a recency/spend scatter plot.

![Customer Segmentation](powerbi/screenshots/Customer_Segmentation.png)

**Product Performance** - top 10 categories by revenue, with items sold
shown alongside to separate high-volume categories from high-price ones.

![Product Performance](powerbi/screenshots/Product_Performance.png)

**Geography & Logistics** - late delivery rate by state (paired with
order volume, so small-sample states don't look worse than they are),
and average delivery time by review score.

![Geography Logistics](powerbi/screenshots/Geography_Logistics.png)

## What the data showed

- Revenue grew from close to nothing at launch to roughly $13.2M
  cumulative by August 2018, with a clear Black Friday spike in November
  2017 - about 40% higher than the months around it.
- Delivery time is the single strongest signal tied to customer
  satisfaction in this dataset: orders with 1-star reviews took almost
  twice as long to arrive as 5-star orders (21.4 vs 10.7 days on average).
- Late deliveries aren't evenly spread - northeastern Brazilian states
  had late-delivery rates as high as 24%, while high-volume states like
  São Paulo stayed under 6% despite handling over 40,000 orders. That
  gap is real, not just a small-sample fluke.
- The K-Means segments split cleanly on recency and spend, except for one
  - a small group (about 3% of customers) that only stood out once
  purchase frequency was plotted directly, since it was the one thing
  that actually set them apart from the rest.
- The top two categories by revenue got there in opposite ways: one
  through high volume at a lower price, the other through fewer sales at
  a much higher price per item.

Full writeup with every query explained and every finding documented:
[docs/findings.md](docs/findings.md)

## Repository structure

```
ecommerce-analytics/
├── db/
│   ├── schema.sql               # Star-schema table definitions
│   └── staging_elt_example.sql  # Alternate ELT-pattern example
├── src/
│   ├── config.py                 # Database connection (reads .env)
│   └── ingest.py                  # ETL script
├── sql/
│   └── business_queries.sql       # All analysis queries
├── notebooks/
│   ├── eda.ipynb                   # Data quality checks
│   └── rfm_clustering.ipynb         # RFM + K-Means segmentation
├── powerbi/
│   └── screenshots/                  # Dashboard page exports
├── docs/
│   ├── findings.md                    # Full analysis writeup
│   └── code-walkthrough.md             # Line-by-line code explanations
├── requirements.txt
└── .env.example
```

## Running it yourself

1. Download the [Olist dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) into `data/raw/`
2. `pip install -r requirements.txt`
3. Create a PostgreSQL database and run `db/schema.sql` against it
4. Copy `.env.example` to `.env` and fill in your own credentials
5. `python src/ingest.py`
6. Run `notebooks/eda.ipynb`, then `notebooks/rfm_clustering.ipynb`
7. Connect Power BI to your Postgres database and build from
   `docs/powerbi-build-guide.md`

## Stack

Python (pandas, SQLAlchemy, scikit-learn) - PostgreSQL - SQL - Power BI (DAX)

## Author

Surya Darshan - https://www.linkedin.com/in/surya-darshan-784937361/
