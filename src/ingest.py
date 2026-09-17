"""
ETL script: Extract (Olist raw CSVs) -> Transform (pandas) -> Load (PostgreSQL)
"""

import os
import pandas as pd
from sqlalchemy import create_engine

from config import SQLALCHEMY_URL, RAW_DATA_DIR

engine = create_engine(SQLALCHEMY_URL)


def read_raw(filename: str) -> pd.DataFrame:
    path = os.path.join(RAW_DATA_DIR, filename)
    return pd.read_csv(path)

def transform_customers(df: pd.DataFrame) -> pd.DataFrame:
    df = df.drop_duplicates(subset="customer_id")
    df = df.rename(columns={
        "customer_zip_code_prefix": "customer_zip_prefix"
    })
    return df[[
        "customer_id", "customer_unique_id",
        "customer_city", "customer_state", "customer_zip_prefix"
    ]]


def transform_products(df: pd.DataFrame, translation: pd.DataFrame) -> pd.DataFrame:
    df = df.drop_duplicates(subset="product_id")
    df = df.merge(translation, how="left",
                   on="product_category_name")
    df["product_category_name_english"] = (
        df["product_category_name_english"]
        .fillna(df["product_category_name"])
        .fillna("unknown")
    )
    df = df.rename(columns={
        "product_category_name_english": "product_category",
        "product_weight_g": "product_weight_g",
        "product_length_cm": "product_length_cm",
        "product_height_cm": "product_height_cm",
        "product_width_cm": "product_width_cm",
    })
    for col in ["product_weight_g", "product_length_cm",
                "product_height_cm", "product_width_cm"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df[[
        "product_id", "product_category", "product_weight_g",
        "product_length_cm", "product_height_cm", "product_width_cm"
    ]]


def transform_sellers(df: pd.DataFrame) -> pd.DataFrame:
    df = df.drop_duplicates(subset="seller_id")
    df = df.rename(columns={"seller_zip_code_prefix": "seller_zip_prefix"})
    return df[["seller_id", "seller_city", "seller_state", "seller_zip_prefix"]]


def transform_orders(df: pd.DataFrame) -> pd.DataFrame:
    df = df.drop_duplicates(subset="order_id")
    date_cols = [
        "order_purchase_timestamp", "order_approved_at",
        "order_delivered_carrier_date", "order_delivered_customer_date",
        "order_estimated_delivery_date"
    ]
    for col in date_cols:
        df[col] = pd.to_datetime(df[col], errors="coerce")
    df["order_status"] = df["order_status"].str.lower().str.strip()
    return df[["order_id", "customer_id", "order_status"] + date_cols]


def transform_order_items(df: pd.DataFrame) -> pd.DataFrame:
    df = df.dropna(subset=["order_id", "product_id", "seller_id"])
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df["freight_value"] = pd.to_numeric(df["freight_value"], errors="coerce")
    return df[[
        "order_id", "order_item_id", "product_id",
        "seller_id", "price", "freight_value"
    ]]


def transform_payments(df: pd.DataFrame) -> pd.DataFrame:
    df["payment_value"] = pd.to_numeric(df["payment_value"], errors="coerce")
    return df[[
        "order_id", "payment_sequential", "payment_type",
        "payment_installments", "payment_value"
    ]]


def transform_reviews(df: pd.DataFrame) -> pd.DataFrame:
    df = df.drop_duplicates(subset="review_id")
    df["review_creation_date"] = pd.to_datetime(
        df["review_creation_date"], errors="coerce")
    df["review_answer_timestamp"] = pd.to_datetime(
        df["review_answer_timestamp"], errors="coerce")
    return df[[
        "review_id", "order_id", "review_score",
        "review_creation_date", "review_answer_timestamp"
    ]]


# ---------------------------------------------------------------
# Load
# ---------------------------------------------------------------

def load(df: pd.DataFrame, table_name: str):
    df.to_sql(table_name, engine, if_exists="append",
               index=False, method="multi", chunksize=5000)
    print(f"  loaded {len(df):>7,} rows -> {table_name}")


def main():
    print("Extracting raw CSVs...")
    customers   = read_raw("olist_customers_dataset.csv")
    products    = read_raw("olist_products_dataset.csv")
    translation = read_raw("product_category_name_translation.csv")
    sellers     = read_raw("olist_sellers_dataset.csv")
    orders      = read_raw("olist_orders_dataset.csv")
    order_items = read_raw("olist_order_items_dataset.csv")
    payments    = read_raw("olist_order_payments_dataset.csv")
    reviews     = read_raw("olist_order_reviews_dataset.csv")

    print("Transforming + loading dimensions...")
    load(transform_customers(customers), "dim_customers")
    load(transform_products(products, translation), "dim_products")
    load(transform_sellers(sellers), "dim_sellers")
    load(transform_orders(orders), "dim_orders")

    print("Transforming + loading facts...")
    load(transform_order_items(order_items), "fact_order_items")
    load(transform_payments(payments), "fact_payments")
    load(transform_reviews(reviews), "fact_reviews")

    print("Done.")


if __name__ == "__main__":
    main()
