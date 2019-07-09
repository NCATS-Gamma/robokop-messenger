"""Initialize omnicorp testing instance."""
import psycopg2

db = 'omnicorp'
user = 'murphy'
port = 5432
host = 'localhost'
password = 'pword'

conn = psycopg2.connect(
    dbname=db,
    user=user,
    host=host,
    port=port,
    password=password)

cur = conn.cursor()

statement = f"CREATE SCHEMA IF NOT EXISTS omnicorp;\n"
statement += f"CREATE TABLE IF NOT EXISTS omnicorp.mondo (curie TEXT, pubmedid INTEGER);\n"
statement += f"""COPY omnicorp.mondo (curie,pubmedid)
FROM '/data/omnicorp_mondo.csv' DELIMITER ',' CSV HEADER;\n
"""
statement += f"CREATE TABLE IF NOT EXISTS omnicorp.hgnc (curie TEXT, pubmedid INTEGER);\n"
statement += f"""COPY omnicorp.hgnc (curie,pubmedid)
FROM '/data/omnicorp_hgnc.csv' DELIMITER ',' CSV HEADER;
"""

cur.execute(statement)
cur.close()
conn.commit()
conn.close()
