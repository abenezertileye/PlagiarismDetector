import psycopg2
from pgvector.psycopg2 import register_vector
from rag_service import embed_text

# 1. Connect to Postgres
conn = psycopg2.connect(
    dbname="academic_helper",
    user="postgres",
    password="123456",
    host="academic_postgres",  # use localhost if running outside docker
    port=5432
)

# Register pgvector adapter
register_vector(conn)

cur = conn.cursor()

# 2. Sample academic sources
sources = [
    {"title": "Sample Paper 1", "content": "This is the content of sample paper 1."},
    {"title": "Sample Paper 2", "content": "This is the content of sample paper 2."},
    {"title": "Sample Paper 3", "content": "Another academic paper content example."},
]

# 3. Insert with embeddings
for src in sources:
    embedding = embed_text(src["content"])

    cur.execute(
        """
        INSERT INTO academic_sources (title, content, embedding)
        VALUES (%s, %s, %s)
        """,
        (src["title"], src["content"], embedding)
    )

conn.commit()
cur.close()
conn.close()

print("✅ Sample academic sources inserted successfully!")
