# News embeddings disabled for Railway stability
# Prevents heavy model loading

def collect_news_embeddings():
    return {
        "status": "disabled",
        "reason": "SentenceTransformer disabled to avoid Railway crash"
    }
