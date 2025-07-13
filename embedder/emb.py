from flask import Flask, request, jsonify
from agno.embedder.google import GeminiEmbedder
from agno.vectordb.chroma import ChromaDb
import os

app = Flask(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is required")

# Vector Storage: Store embeddings in your chosen vector database
#CONVERT TO VECTOR AI MATCHING INDEX from chromadb
def embed_store(chunks):
    emb = GeminiEmbedder(api_key=GEMINI_API_KEY)
    db = ChromaDb(
        collection="GlobalNexusDocuments",
        embedder=emb,
        persistent_client= True,
        path= './chroma'
    )
    db.create()
    db.insert(chunks)
    return db

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

@app.route('/embed', methods=['POST'])
def embed_chunks():
    try:
        data = request.json
        chunks = data.get('chunks', [])
        
        if not chunks:
            return jsonify({"error": "No chunks provided"}), 400
        
        db = embed_store(chunks)
        return jsonify({"message": f"Successfully embedded {len(chunks)} chunks"}), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
