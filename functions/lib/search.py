from langchain.embeddings.openai import OpenAIEmbeddings
import numpy as np

def full_text_search(search_keyword: str, entities: list[dict[str, any]], search_fields: list[str], limit: int):
    embeddings_model = OpenAIEmbeddings() 
    search_keyword_embedding = embeddings_model.embed_query(search_keyword)

    similarity_scores = []

    for entity in entities:
        max_similarity = -np.inf

        for field in search_fields:
            if field in entity:
                entity_field_embedding = embeddings_model.embed_query(entity[field])
                similarity = cosine_similarity(search_keyword_embedding, entity_field_embedding)
                max_similarity = max(max_similarity, similarity)  # Store the max similarity among the search fields

        similarity_scores.append(max_similarity)

    # Sort entities based on their similarity scores in descending order
    sorted_indices = np.argsort(similarity_scores)[::-1]
    sorted_entities = [entities[i] for i in sorted_indices]

    return sorted_entities[:limit]

def cosine_similarity(A, B):
    dot_product = np.dot(A, B)
    norm_a = np.linalg.norm(A)
    norm_b = np.linalg.norm(B)
    return dot_product / (norm_a * norm_b)
