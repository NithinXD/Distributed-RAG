from flask import Flask, request, jsonify
from agno.document import chunking
from agno.document.reader.pdf_reader import PDFReader
import os 
from agno.document.chunking.recursive import RecursiveChunking
import tempfile
import requests

app = Flask(__name__)

def upload(path: str):
    reader = PDFReader(chunk=True, chunk_size=1000, chunking_strategy=RecursiveChunking())
    doc = reader.read(path)
    return doc

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

@app.route('/chunk', methods=['POST'])
def chunk_documents():
    try:
        # Handle file upload or URL
        if 'file' in request.files:
            file = request.files['file']
            if file.filename == '':
                return jsonify({"error": "No file selected"}), 400
            
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                file.save(tmp_file.name)
                chunks = upload(tmp_file.name)
                
            # Clean up temp file
            os.unlink(tmp_file.name)
            
        elif request.json and 'pdf_url' in request.json:
            # Download PDF from URL
            pdf_url = request.json['pdf_url']
            response = requests.get(pdf_url)
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                tmp_file.write(response.content)
                chunks = upload(tmp_file.name)
                
            # Clean up temp file
            os.unlink(tmp_file.name)
            
        else:
            return jsonify({"error": "No file or PDF URL provided"}), 400
        
        # Add metadata
        filename = file.filename if 'file' in request.files else os.path.basename(request.json['pdf_url'])
        for chunk in chunks:
            chunk.meta_data["Source"] = filename
        
        # Convert chunks to serializable format
        serialized_chunks = []
        for chunk in chunks:
            serialized_chunks.append({
                "content": chunk.content,
                "meta_data": chunk.meta_data
            })
        
        return jsonify({
            "message": f"Successfully processed {len(chunks)} chunks from {filename}",
            "chunks": serialized_chunks,
            "count": len(chunks)
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)