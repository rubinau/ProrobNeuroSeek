# nlp.py
# This module handles the Natural Language Processing (NLP) task of
# matching the user's text query to the labels detected by YOLO.
# Now with enhanced logging for debugging similarity scores.

import spacy
import logging
from typing import List, Optional

# --- SpaCy Model Loading ---
try:
    logging.info("Loading SpaCy NLP model 'en_core_web_md'...")
    nlp = spacy.load("en_core_web_md")
    logging.info("SpaCy model loaded successfully.")
except OSError:
    logging.critical("SpaCy model 'en_core_web_md' not found. Please run: python -m spacy download en_core_web_md")
    nlp = None 

def find_best_match(query: str, labels: list, threshold: float = 0.6) -> tuple[Optional[str], float]:
    """
    Finds the best semantic match for a query within a list of labels.

    Args:
        query (str): The user's description (e.g., "my water bottle").
        labels (list): A list of object labels from YOLO (e.g., ['person', 'bottle']).
        threshold (float): The minimum similarity score to be considered a match.

    Returns:
        A tuple containing:
        - Optional[str]: The best matching label, or None if no match is found above the threshold.
        - float: The similarity score of the best match (0 if no match).
    """
    if not nlp or not query or not labels:
        if not nlp:
            logging.warning("Skipping NLP match: SpaCy model is not loaded.")
        return None, 0.0

    query_doc = nlp(query.lower())
    best_match_label = None
    max_similarity = 0.0

    # --- DEBUGGING: Log header for a new matching session ---
    logging.info(f"[NLP DEBUG] Comparing query '{query}' with labels: {labels}")

    for label in labels:
        label_doc = nlp(label.lower())
        
        if query_doc.has_vector and label_doc.has_vector:
            similarity = query_doc.similarity(label_doc)
            
            # --- DEBUGGING: Log each comparison ---
            logging.info(f"[NLP DEBUG]   '{query}' <-> '{label}': Similarity = {similarity:.4f}")
            
            if similarity > max_similarity:
                max_similarity = similarity
                best_match_label = label

    # --- DEBUGGING: Log the final result before threshold check ---
    logging.info(f"[NLP DEBUG] Best guess: '{best_match_label}' with score {max_similarity:.4f} (Threshold: {threshold})")

    if max_similarity > threshold:
        logging.info(f"[NLP DEBUG] Match PASSED threshold.")
        return best_match_label, max_similarity
    else:
        logging.info(f"[NLP DEBUG] Match FAILED threshold.")
        # Return the best guess even if it's below the threshold, for debugging purposes
        return None, max_similarity
