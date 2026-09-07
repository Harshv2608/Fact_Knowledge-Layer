from sentence_transformers import SentenceTransformer

# Initialize the model globally so it's only loaded once
model = SentenceTransformer('all-MiniLM-L6-v2')

def get_embedding(text: str) -> list[float]:
    """
    Returns the embedding vector for the given text using a local sentence-transformer.
    """
    if not text:
        return [0.0] * 384
    return model.encode(text).tolist()
