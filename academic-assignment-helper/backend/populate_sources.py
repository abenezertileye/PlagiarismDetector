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

# 2. Sample academic sources (more realistic)
sources = [
    {
        "title": "Transformer Models in NLP",
        "content": (
            "Transformer-based models have revolutionized natural language processing. "
            "They rely on attention mechanisms to model long-range dependencies and "
            "enable pretraining on massive text corpora followed by fine-tuning for specific tasks. "
            "Models such as BERT, GPT, and RoBERTa demonstrate state-of-the-art performance on tasks like "
            "text classification, question answering, and machine translation."
        )
    },
    {
        "title": "Neural Network Optimization Techniques",
        "content": (
            "Optimizing deep neural networks involves techniques like learning rate schedules, "
            "gradient clipping, weight regularization, and batch normalization. "
            "These methods improve convergence speed, prevent overfitting, and stabilize training, "
            "allowing models to generalize better to unseen data."
        )
    },
    {
        "title": "Evaluation Metrics for NLP",
        "content": (
            "Evaluating NLP models requires metrics such as accuracy, F1 score, BLEU, and ROUGE. "
            "These metrics quantify different aspects of model performance: classification correctness, "
            "precision-recall balance, or quality of generated text. Proper evaluation is critical "
            "for comparing models and ensuring reliability in downstream tasks."
        )
    },
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
