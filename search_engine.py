# Import necessary libraries
from flask import Flask, request, jsonify
import numpy as np
import logging
import re
from collections import defaultdict
import math

# Set up logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the SearchEngine class
class SearchEngine:
    """
    A class used to create a search engine using TF-IDF similarity.

    Attributes:
    ----------
    documents : list
        List of stored documents.
    document_vectors : dict
        TF-IDF vectors for each document.
    vocabulary : dict
        Vocabulary mapping words to indices.

    Methods:
    -------
    __init__()
        Initializes the search engine.
    """

    def __init__(self):
        """
        Initializes the search engine.

        Creates storage for documents and TF-IDF vectors.
        """
        self.documents = []
        self.document_vectors = {}
        self.vocabulary = {}
        self.idf = {}
        
    def _tokenize(self, text):
        """Tokenize text into words."""
        return re.findall(r'\b\w+\b', text.lower())
    
    def _compute_tf(self, doc_tokens):
        """Compute term frequency for a document."""
        tf = defaultdict(int)
        for token in doc_tokens:
            tf[token] += 1
        # Normalize by document length
        doc_length = len(doc_tokens)
        for token in tf:
            tf[token] = tf[token] / doc_length
        return tf
    
    def _compute_idf(self):
        """Compute inverse document frequency for all terms."""
        num_docs = len(self.documents)
        doc_freq = defaultdict(int)
        
        for doc in self.documents:
            tokens = set(self._tokenize(doc))
            for token in tokens:
                doc_freq[token] += 1
        
        for token, freq in doc_freq.items():
            self.idf[token] = math.log(num_docs / freq)
    
    def _vectorize_document(self, doc_index):
        """Create TF-IDF vector for a document."""
        doc = self.documents[doc_index]
        tokens = self._tokenize(doc)
        tf = self._compute_tf(tokens)
        
        vector = {}
        for token in tf:
            if token in self.idf:
                vector[token] = tf[token] * self.idf[token]
        
        return vector
    
    def _cosine_similarity(self, vec1, vec2):
        """Compute cosine similarity between two vectors."""
        # Get intersection of keys
        common_keys = set(vec1.keys()) & set(vec2.keys())
        
        if not common_keys:
            return 0.0
        
        # Compute dot product
        dot_product = sum(vec1[key] * vec2[key] for key in common_keys)
        
        # Compute magnitudes
        mag1 = math.sqrt(sum(val**2 for val in vec1.values()))
        mag2 = math.sqrt(sum(val**2 for val in vec2.values()))
        
        if mag1 == 0 or mag2 == 0:
            return 0.0
        
        return dot_product / (mag1 * mag2)

    def add_documents(self, documents):
        """
        Adds documents to the search engine.

        Parameters:
        ----------
        documents : list
            A list of strings representing the documents to be added.
        """
        start_index = len(self.documents)
        self.documents.extend(documents)
        
        # Recompute IDF for all documents
        self._compute_idf()
        
        # Vectorize all documents (including previously added ones)
        for i in range(len(self.documents)):
            self.document_vectors[i] = self._vectorize_document(i)
        
        logger.info(f"Added {len(documents)} documents. Total documents: {len(self.documents)}")

    def search(self, query, k=5):
        """
        Searches for similar documents.

        Parameters:
        ----------
        query : str
            The query string.
        k : int, optional
            The number of similar documents to return (default is 5).

        Returns:
        -------
        tuple
            A tuple containing similarities and indices arrays.
        """
        if not self.documents:
            return np.array([[]]), np.array([[]])
        
        # Vectorize query
        query_tokens = self._tokenize(query)
        query_tf = self._compute_tf(query_tokens)
        query_vector = {}
        for token in query_tf:
            if token in self.idf:
                query_vector[token] = query_tf[token] * self.idf[token]
        
        # Compute similarities
        similarities = []
        for doc_index in range(len(self.documents)):
            sim = self._cosine_similarity(query_vector, self.document_vectors[doc_index])
            similarities.append((sim, doc_index))
        
        # Sort by similarity (descending)
        similarities.sort(reverse=True)
        
        # Get top k results
        top_k = similarities[:k]
        sim_scores = [sim for sim, _ in top_k]
        indices = [idx for _, idx in top_k]
        
        return np.array([sim_scores]), np.array([indices])


# Create a Flask application
app = Flask(__name__)

# Create a search engine instance
search_engine = SearchEngine()

# Define a route for adding documents
@app.route('/add_documents', methods=['POST'])
def add_documents():
    """
    Adds documents to the search engine.

    Request Body:
    ----------
    documents : list
        A list of strings representing the documents to be added.

    Returns:
    -------
    jsonify
        A JSON response indicating success or failure.
    """
    try:
        # Get the documents from the request body
        documents = request.json['documents']
        # Add the documents to the search engine
        search_engine.add_documents(documents)
        # Return a success response
        return jsonify({'message': 'Documents added successfully'}), 200
    except Exception as e:
        # Return an error response
        return jsonify({'message': 'Error adding documents', 'error': str(e)}), 500

# Define a route for searching documents
@app.route('/search', methods=['POST'])
def search():
    """
    Searches for similar documents.

    Request Body:
    ----------
    query : str
        The query string.
    k : int, optional
        The number of similar documents to return (default is 5).

    Returns:
    -------
    jsonify
        A JSON response containing the similarities and the corresponding documents.
    """
    try:
        # Get the query and k from the request body
        query = request.json['query']
        k = request.json.get('k', 5)
        # Search for similar documents
        similarities, indices = search_engine.search(query, k)
        # Return the results
        return jsonify({'similarities': similarities.tolist(), 'indices': indices.tolist()}), 200
    except Exception as e:
        # Return an error response
        return jsonify({'message': 'Error searching documents', 'error': str(e)}), 500

if __name__ == '__main__':
    # Run the Flask application
    app.run(debug=True)