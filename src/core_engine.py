"""Pipeline de Transformación e Ingesta Columnares con DuckDB/Polars."""
import os, duckdb

def run_pipeline():
    print("[Pipeline] Ejecutando procesamiento columnar y particionado...")
    con = duckdb.connect("data/lakehouse.duckdb")
    con.execute("""
        CREATE OR REPLACE TABLE curated_events AS
        SELECT 
            event_id,
            user_id,
            action,
            payload_bytes,
            latency_ms,
            CAST(timestamp AS TIMESTAMP) as event_timestamp,
            DATE_TRUNC('hour', CAST(timestamp AS TIMESTAMP)) as partition_hour
        FROM read_parquet('data/raw_events.parquet');
    """)
    print("[Pipeline] Curated events completado exitosamente.")