import os
import pandas as pd
from sqlalchemy import create_engine, text
from prefect import flow, task

# Configuration de la base PostgreSQL (via .env)
PG = {
    "user": os.getenv("POSTGRES_USER", "streamflow"),
    "pwd":  os.getenv("POSTGRES_PASSWORD", "streamflow"),
    "db":   os.getenv("POSTGRES_DB", "streamflow"),
    "host": os.getenv("POSTGRES_HOST", "postgres"),
    "port": os.getenv("POSTGRES_PORT", "5432"),
}

# Valeurs par défaut pour ce TP
AS_OF = os.getenv("AS_OF", "2024-01-31")               # frontière du mois
SEED_DIR = os.getenv("SEED_DIR", "/data/seeds/month_000")

def engine():
    """Crée un engine SQLAlchemy pour PostgreSQL."""
    uri = f"postgresql+psycopg2://{PG['user']}:{PG['pwd']}@{PG['host']}:{PG['port']}/{PG['db']}"
    return create_engine(uri)

@task
def upsert_csv(table: str, csv_path: str, pk_cols: list[str]):
    """
    Charge un CSV dans une table Postgres en utilisant une stratégie d'upsert.
    1) Création d'une table temporaire
    2) Insert dans la table temporaire
    3) INSERT ... SELECT ... FROM temp ON CONFLICT (...) DO UPDATE ...
    """

    df = pd.read_csv(csv_path)

    # Conversion de certains types si nécessaire (ex: dates)
    if "signup_date" in df.columns:
        df["signup_date"] = pd.to_datetime(df["signup_date"], errors="coerce")

    # TODO: convertir en booléen les colonnes spécifiques si elles existent
    # Cela évite que Postgres ne reçoive des entiers ou des chaînes pour des champs booléens
    bool_cols = ["plan_stream_tv", "plan_stream_movies", "paperless_billing"]
    for col in bool_cols:
        if col in df.columns:
            df[col] = df[col].astype(bool)

    eng = engine()
    with eng.begin() as conn:
        tmp = f"tmp_{table}"

        # On recrée une table temporaire avec le même schéma que le DataFrame
        conn.exec_driver_sql(f"DROP TABLE IF EXISTS {tmp}")
        df.head(0).to_sql(tmp, conn, if_exists="replace", index=False)
        df.to_sql(tmp, conn, if_exists="append", index=False)

        cols = list(df.columns)
        collist = ", ".join(cols)
        pk = ", ".join(pk_cols)

        # TODO: construire la partie "SET col = EXCLUDED.col" pour toutes les colonnes non PK
        updates = ", ".join(
            [f"{col} = EXCLUDED.{col}" for col in cols if col not in pk_cols]
        )

        sql = text(f"""
            INSERT INTO {table} ({collist})
            SELECT {collist} FROM {tmp}
            ON CONFLICT ({pk}) DO UPDATE SET {updates}
        """)
        
        conn.execute(sql)
        conn.exec_driver_sql(f"DROP TABLE IF EXISTS {tmp}")

    return f"upserted {len(df)} rows into {table}"

@flow(name="ingest_month")
def ingest_month_flow(seed_dir: str = SEED_DIR, as_of: str = AS_OF):
    """
    Flow Prefect principal pour le mois donné.
    Dans cet exercice, on se concentre uniquement sur l'upsert des tables.
    """
    upsert_csv("users",            f"{seed_dir}/users.csv",            ["user_id"])
    upsert_csv("subscriptions",    f"{seed_dir}/subscriptions.csv",    ["user_id"])
    upsert_csv("usage_agg_30d",    f"{seed_dir}/usage_agg_30d.csv",    ["user_id"])
    upsert_csv("payments_agg_90d", f"{seed_dir}/payments_agg_90d.csv", ["user_id"])
    upsert_csv("support_agg_90d",  f"{seed_dir}/support_agg_90d.csv",  ["user_id"])
    upsert_csv("labels",           f"{seed_dir}/labels.csv",           ["user_id"])

    return f"Ingestion terminée pour {as_of}"

if __name__ == "__main__":
    ingest_month_flow()