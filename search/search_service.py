"""
Enterprise AI System - Real-time Search Service
Advanced search capabilities with AI-powered semantic search and real-time indexing
"""

import os
import sys
import json
import time
import math
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import re
from collections import defaultdict, Counter
import openai
from flask import Flask, request, jsonify
from flask_cors import CORS
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

app = Flask(__name__)
app.config['SECRET_KEY'] = 'search-service-secret-key-change-in-production'

# Enable CORS for all routes
CORS(app, origins="*", allow_headers=["Content-Type", "Authorization"])

# Initialize OpenAI client
openai.api_key = os.getenv('OPENAI_API_KEY')
openai.api_base = os.getenv('OPENAI_API_BASE', 'https://api.openai.com/v1')

@dataclass
class SearchDocument:
    """Represents a document in the search index"""
    id: str
    title: str
    content: str
    category: str
    tags: List[str]
    metadata: Dict[str, Any]
    indexed_at: datetime
    embedding: Optional[List[float]] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "category": self.category,
            "tags": self.tags,
            "metadata": self.metadata,
            "indexed_at": self.indexed_at.isoformat(),
            "has_embedding": self.embedding is not None
        }

@dataclass
class SearchResult:
    """Represents a search result"""
    document: SearchDocument
    score: float
    match_type: str
    highlights: List[str]
    explanation: str
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "document": self.document.to_dict(),
            "score": self.score,
            "match_type": self.match_type,
            "highlights": self.highlights,
            "explanation": self.explanation
        }

class IntelligentSearchEngine:
    """Advanced search engine with multiple search strategies"""
    
    def __init__(self):
        self.documents: Dict[str, SearchDocument] = {}
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=10000,
            stop_words='english',
            ngram_range=(1, 2)
        )
        self.tfidf_matrix = None
        self.inverted_index: Dict[str, List[str]] = defaultdict(list)
        self.category_index: Dict[str, List[str]] = defaultdict(list)
        self.tag_index: Dict[str, List[str]] = defaultdict(list)
        self.stats = {
            "documents_indexed": 0,
            "searches_performed": 0,
            "avg_search_time_ms": 0,
            "index_last_updated": None,
            "start_time": datetime.utcnow()
        }
    
    def add_document(self, doc: SearchDocument) -> bool:
        """Add document to search index"""
        try:
            # Store document
            self.documents[doc.id] = doc
            
            # Update inverted index
            self._update_inverted_index(doc)
            
            # Update category index
            self.category_index[doc.category].append(doc.id)
            
            # Update tag index
            for tag in doc.tags:
                self.tag_index[tag.lower()].append(doc.id)
            
            # Rebuild TF-IDF matrix if we have enough documents
            if len(self.documents) % 10 == 0:  # Rebuild every 10 documents
                self._rebuild_tfidf_matrix()
            
            self.stats["documents_indexed"] += 1
            self.stats["index_last_updated"] = datetime.utcnow()
            
            return True
            
        except Exception as e:
            print(f"Error adding document {doc.id}: {e}")
            return False
    
    def _update_inverted_index(self, doc: SearchDocument):
        """Update inverted index with document terms"""
        # Combine title and content for indexing
        text = f"{doc.title} {doc.content}".lower()
        
        # Extract words (simple tokenization)
        words = re.findall(r'\b\w+\b', text)
        
        # Add to inverted index
        for word in set(words):
            if len(word) > 2:  # Skip very short words
                self.inverted_index[word].append(doc.id)
    
    def _rebuild_tfidf_matrix(self):
        """Rebuild TF-IDF matrix for all documents"""
        try:
            if not self.documents:
                return
            
            # Prepare corpus
            corpus = []
            doc_ids = []
            
            for doc_id, doc in self.documents.items():
                corpus.append(f"{doc.title} {doc.content}")
                doc_ids.append(doc_id)
            
            # Fit TF-IDF vectorizer
            self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(corpus)
            self.doc_ids_order = doc_ids
            
        except Exception as e:
            print(f"Error rebuilding TF-IDF matrix: {e}")
    
    def search(self, query: str, limit: int = 10, search_type: str = "hybrid") -> List[SearchResult]:
        """Perform search with specified strategy"""
        start_time = time.time()
        
        try:
            if search_type == "keyword":
                results = self._keyword_search(query, limit)
            elif search_type == "semantic":
                results = self._semantic_search(query, limit)
            elif search_type == "tfidf":
                results = self._tfidf_search(query, limit)
            elif search_type == "hybrid":
                results = self._hybrid_search(query, limit)
            else:
                results = self._hybrid_search(query, limit)
            
            # Update stats
            search_time = (time.time() - start_time) * 1000
            self.stats["searches_performed"] += 1
            
            # Update average search time
            current_avg = self.stats["avg_search_time_ms"]
            total_searches = self.stats["searches_performed"]
            self.stats["avg_search_time_ms"] = (
                (current_avg * (total_searches - 1) + search_time) / total_searches
            )
            
            return results
            
        except Exception as e:
            print(f"Search error: {e}")
            return []
    
    def _keyword_search(self, query: str, limit: int) -> List[SearchResult]:
        """Simple keyword-based search"""
        query_words = set(re.findall(r'\b\w+\b', query.lower()))
        doc_scores = defaultdict(float)
        
        # Score documents based on keyword matches
        for word in query_words:
            if word in self.inverted_index:
                for doc_id in self.inverted_index[word]:
                    doc_scores[doc_id] += 1.0
        
        # Sort by score
        sorted_docs = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)
        
        results = []
        for doc_id, score in sorted_docs[:limit]:
            if doc_id in self.documents:
                doc = self.documents[doc_id]
                highlights = self._extract_highlights(doc, query_words)
                
                results.append(SearchResult(
                    document=doc,
                    score=score,
                    match_type="keyword",
                    highlights=highlights,
                    explanation=f"Matched {int(score)} keywords"
                ))
        
        return results
    
    def _tfidf_search(self, query: str, limit: int) -> List[SearchResult]:
        """TF-IDF based search"""
        if self.tfidf_matrix is None or not hasattr(self, 'doc_ids_order'):
            return []
        
        try:
            # Transform query
            query_vector = self.tfidf_vectorizer.transform([query])
            
            # Calculate similarities
            similarities = cosine_similarity(query_vector, self.tfidf_matrix).flatten()
            
            # Get top results
            top_indices = similarities.argsort()[-limit:][::-1]
            
            results = []
            for idx in top_indices:
                if similarities[idx] > 0:
                    doc_id = self.doc_ids_order[idx]
                    doc = self.documents[doc_id]
                    
                    query_words = set(re.findall(r'\b\w+\b', query.lower()))
                    highlights = self._extract_highlights(doc, query_words)
                    
                    results.append(SearchResult(
                        document=doc,
                        score=float(similarities[idx]),
                        match_type="tfidf",
                        highlights=highlights,
                        explanation=f"TF-IDF similarity: {similarities[idx]:.3f}"
                    ))
            
            return results
            
        except Exception as e:
            print(f"TF-IDF search error: {e}")
            return []
    
    def _semantic_search(self, query: str, limit: int) -> List[SearchResult]:
        """AI-powered semantic search"""
        try:
            # Get query embedding
            query_embedding = self._get_embedding(query)
            if not query_embedding:
                return []
            
            # Calculate similarities with document embeddings
            similarities = []
            for doc_id, doc in self.documents.items():
                if doc.embedding:
                    similarity = self._cosine_similarity(query_embedding, doc.embedding)
                    similarities.append((doc_id, similarity))
            
            # Sort by similarity
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            results = []
            for doc_id, similarity in similarities[:limit]:
                doc = self.documents[doc_id]
                
                results.append(SearchResult(
                    document=doc,
                    score=similarity,
                    match_type="semantic",
                    highlights=[],
                    explanation=f"Semantic similarity: {similarity:.3f}"
                ))
            
            return results
            
        except Exception as e:
            print(f"Semantic search error: {e}")
            return []
    
    def _hybrid_search(self, query: str, limit: int) -> List[SearchResult]:
        """Hybrid search combining multiple strategies"""
        # Get results from different methods
        keyword_results = self._keyword_search(query, limit * 2)
        tfidf_results = self._tfidf_search(query, limit * 2)
        
        # Combine and re-rank results
        combined_scores = defaultdict(float)
        all_results = {}
        
        # Weight keyword results
        for result in keyword_results:
            doc_id = result.document.id
            combined_scores[doc_id] += result.score * 0.3
            all_results[doc_id] = result
        
        # Weight TF-IDF results
        for result in tfidf_results:
            doc_id = result.document.id
            combined_scores[doc_id] += result.score * 0.7
            if doc_id not in all_results:
                all_results[doc_id] = result
        
        # Sort by combined score
        sorted_results = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Return top results
        final_results = []
        for doc_id, score in sorted_results[:limit]:
            if doc_id in all_results:
                result = all_results[doc_id]
                result.score = score
                result.match_type = "hybrid"
                result.explanation = f"Hybrid score: {score:.3f}"
                final_results.append(result)
        
        return final_results
    
    def _extract_highlights(self, doc: SearchDocument, query_words: set) -> List[str]:
        """Extract highlighted snippets from document"""
        text = f"{doc.title} {doc.content}".lower()
        highlights = []
        
        # Find sentences containing query words
        sentences = re.split(r'[.!?]+', text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 20:  # Skip very short sentences
                words_in_sentence = set(re.findall(r'\b\w+\b', sentence))
                if query_words.intersection(words_in_sentence):
                    # Truncate long sentences
                    if len(sentence) > 150:
                        sentence = sentence[:150] + "..."
                    highlights.append(sentence)
        
        return highlights[:3]  # Return top 3 highlights
    
    def _get_embedding(self, text: str) -> Optional[List[float]]:
        """Get embedding for text using OpenAI"""
        try:
            response = openai.Embedding.create(
                model="text-embedding-ada-002",
                input=text
            )
            return response['data'][0]['embedding']
        except Exception as e:
            print(f"Embedding error: {e}")
            return None
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            vec1 = np.array(vec1)
            vec2 = np.array(vec2)
            
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return dot_product / (norm1 * norm2)
        except:
            return 0.0
    
    def get_suggestions(self, query: str, limit: int = 5) -> List[str]:
        """Get search suggestions based on indexed content"""
        query_words = re.findall(r'\b\w+\b', query.lower())
        if not query_words:
            return []
        
        suggestions = set()
        
        # Find similar terms in inverted index
        for word in query_words:
            for indexed_word in self.inverted_index.keys():
                if indexed_word.startswith(word) and indexed_word != word:
                    suggestions.add(indexed_word)
        
        # Add popular tags
        for tag in self.tag_index.keys():
            if any(word in tag for word in query_words):
                suggestions.add(tag)
        
        return list(suggestions)[:limit]
    
    def get_stats(self) -> Dict:
        """Get search engine statistics"""
        uptime = (datetime.utcnow() - self.stats["start_time"]).total_seconds()
        
        return {
            **self.stats,
            "uptime_seconds": uptime,
            "total_documents": len(self.documents),
            "categories": len(self.category_index),
            "unique_tags": len(self.tag_index),
            "index_terms": len(self.inverted_index),
            "tfidf_features": self.tfidf_matrix.shape[1] if self.tfidf_matrix is not None else 0,
            "timestamp": datetime.utcnow().isoformat()
        }

# Global search engine instance
search_engine = IntelligentSearchEngine()

# Sample data for demonstration
def initialize_sample_data():
    """Initialize search engine with sample documents"""
    sample_docs = [
        {
            "id": "doc_1",
            "title": "Introduction to Machine Learning",
            "content": "Machine learning is a subset of artificial intelligence that enables computers to learn and improve from experience without being explicitly programmed. It focuses on developing algorithms that can access data and use it to learn for themselves.",
            "category": "education",
            "tags": ["machine learning", "AI", "algorithms", "data science"],
            "metadata": {"author": "AI Expert", "difficulty": "beginner"}
        },
        {
            "id": "doc_2", 
            "title": "Advanced Neural Networks",
            "content": "Neural networks are computing systems inspired by biological neural networks. Deep learning uses multiple layers of neural networks to model and understand complex patterns in data. Applications include image recognition, natural language processing, and autonomous vehicles.",
            "category": "technology",
            "tags": ["neural networks", "deep learning", "AI", "computer vision"],
            "metadata": {"author": "Deep Learning Researcher", "difficulty": "advanced"}
        },
        {
            "id": "doc_3",
            "title": "Business Intelligence and Analytics",
            "content": "Business intelligence involves analyzing business data to help organizations make informed decisions. It includes data mining, reporting, performance metrics, and predictive analytics to identify trends and opportunities.",
            "category": "business",
            "tags": ["business intelligence", "analytics", "data mining", "reporting"],
            "metadata": {"author": "Business Analyst", "difficulty": "intermediate"}
        },
        {
            "id": "doc_4",
            "title": "Cloud Computing Fundamentals",
            "content": "Cloud computing delivers computing services over the internet, including servers, storage, databases, networking, software, and analytics. It offers faster innovation, flexible resources, and economies of scale.",
            "category": "technology",
            "tags": ["cloud computing", "AWS", "infrastructure", "scalability"],
            "metadata": {"author": "Cloud Architect", "difficulty": "beginner"}
        },
        {
            "id": "doc_5",
            "title": "Data Science Best Practices",
            "content": "Data science combines statistics, programming, and domain expertise to extract insights from data. Best practices include data cleaning, exploratory analysis, feature engineering, model validation, and ethical considerations.",
            "category": "education",
            "tags": ["data science", "statistics", "programming", "ethics"],
            "metadata": {"author": "Data Scientist", "difficulty": "intermediate"}
        }
    ]
    
    for doc_data in sample_docs:
        doc = SearchDocument(
            id=doc_data["id"],
            title=doc_data["title"],
            content=doc_data["content"],
            category=doc_data["category"],
            tags=doc_data["tags"],
            metadata=doc_data["metadata"],
            indexed_at=datetime.utcnow()
        )
        search_engine.add_document(doc)

# Initialize sample data
initialize_sample_data()

# API Routes

@app.route('/search', methods=['GET', 'POST'])
def search():
    """Perform search"""
    try:
        if request.method == 'GET':
            query = request.args.get('q', '')
            limit = int(request.args.get('limit', 10))
            search_type = request.args.get('type', 'hybrid')
        else:
            data = request.get_json()
            query = data.get('query', '')
            limit = data.get('limit', 10)
            search_type = data.get('type', 'hybrid')
        
        if not query:
            return jsonify({"error": "Query is required"}), 400
        
        results = search_engine.search(query, limit, search_type)
        
        return jsonify({
            "query": query,
            "search_type": search_type,
            "results": [result.to_dict() for result in results],
            "total_results": len(results),
            "timestamp": datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/search/suggestions')
def search_suggestions():
    """Get search suggestions"""
    try:
        query = request.args.get('q', '')
        limit = int(request.args.get('limit', 5))
        
        suggestions = search_engine.get_suggestions(query, limit)
        
        return jsonify({
            "query": query,
            "suggestions": suggestions,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/search/index', methods=['POST'])
def index_document():
    """Add document to search index"""
    try:
        data = request.get_json()
        if not data or 'id' not in data or 'title' not in data or 'content' not in data:
            return jsonify({"error": "Document ID, title, and content are required"}), 400
        
        doc = SearchDocument(
            id=data['id'],
            title=data['title'],
            content=data['content'],
            category=data.get('category', 'general'),
            tags=data.get('tags', []),
            metadata=data.get('metadata', {}),
            indexed_at=datetime.utcnow()
        )
        
        success = search_engine.add_document(doc)
        
        return jsonify({
            "success": success,
            "document_id": doc.id,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/search/stats')
def search_stats():
    """Get search engine statistics"""
    try:
        stats = search_engine.get_stats()
        return jsonify(stats)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/search/categories')
def get_categories():
    """Get available categories"""
    try:
        categories = {}
        for category, doc_ids in search_engine.category_index.items():
            categories[category] = len(doc_ids)
        
        return jsonify({
            "categories": categories,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/search/tags')
def get_tags():
    """Get available tags"""
    try:
        tags = {}
        for tag, doc_ids in search_engine.tag_index.items():
            tags[tag] = len(doc_ids)
        
        # Sort by frequency
        sorted_tags = dict(sorted(tags.items(), key=lambda x: x[1], reverse=True))
        
        return jsonify({
            "tags": sorted_tags,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health')
def health_check():
    """Health check for search service"""
    return jsonify({
        "service": "Real-time Search Service",
        "status": "healthy",
        "version": "2.0.0",
        "features": [
            "keyword_search",
            "tfidf_search", 
            "semantic_search",
            "hybrid_search",
            "real_time_indexing",
            "search_suggestions"
        ],
        "documents_indexed": len(search_engine.documents),
        "search_types": ["keyword", "tfidf", "semantic", "hybrid"],
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route('/api/info')
def service_info():
    """Get service information"""
    return jsonify({
        "service_name": "Enterprise AI Real-time Search Service",
        "description": "Advanced search capabilities with AI-powered semantic search and real-time indexing",
        "version": "2.0.0",
        "features": [
            "Multi-strategy search (keyword, TF-IDF, semantic, hybrid)",
            "Real-time document indexing",
            "AI-powered semantic search with embeddings",
            "Search suggestions and autocomplete",
            "Category and tag-based filtering",
            "Highlighted search results",
            "Search analytics and statistics"
        ],
        "search_algorithms": [
            "Inverted index for keyword search",
            "TF-IDF vectorization with cosine similarity",
            "OpenAI embeddings for semantic search",
            "Hybrid ranking combining multiple signals"
        ],
        "endpoints": [
            "/search",
            "/search/suggestions",
            "/search/index",
            "/search/stats",
            "/search/categories",
            "/search/tags"
        ],
        "timestamp": datetime.utcnow().isoformat()
    })

if __name__ == '__main__':
    print("🚀 Starting Enterprise AI Search Service...")
    print("🔍 Search URL: http://localhost:7004/search")
    print("💡 Suggestions: http://localhost:7004/search/suggestions")
    print("📊 Statistics: http://localhost:7004/search/stats")
    print("🏥 Health Check: http://localhost:7004/health")
    print(f"📚 Sample documents indexed: {len(search_engine.documents)}")
    
    app.run(host='0.0.0.0', port=7004, debug=True)

