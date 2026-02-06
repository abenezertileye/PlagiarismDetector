import psycopg2
from rag_service import embed_text

# 1. Connect to your Postgres database
conn = psycopg2.connect(
    dbname="academic_helper",
    user="postgres",
    password="123456",  # replace with your actual password
    host="academic_postgres"           # or the docker service name if running inside docker-compose
)
cur = conn.cursor()

# 2. Define sample academic sources
sources = [
    {"title": "Sample Paper 1", "content": "This is the content of sample paper 1."},
    {"title": "Sample Paper 2", "content": "This is the content of sample paper 2."},
    {"title": "Sample Paper 3", "content": "Another academic paper content example."},
]

# 3. Generate embeddings and insert into database
for src in sources:
    embedding = embed_text(src["content"])
    cur.execute(
        "INSERT INTO academic_sources (title, content, embedding) VALUES (%s, %s, %s)",
        (src["title"], src["content"], embedding)
    )

# 4. Commit and close
conn.commit()
cur.close()
conn.close()

print("✅ Sample academic sources inserted successfully!")
