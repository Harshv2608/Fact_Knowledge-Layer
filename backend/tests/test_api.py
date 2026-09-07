from fastapi.testclient import TestClient
from app.main import app
import app.api.documents

# Mock background task so it doesn't execute the full ML pipeline synchronously in TestClient
app.api.documents.process_document_background = lambda doc_id, path: None

client = TestClient(app)

def test_upload_returns_200():
    import io
    dummy_pdf = io.BytesIO(b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF")
    dummy_pdf.name = "test.pdf"
    
    response = client.post(
        "/api/documents/upload",
        files={"file": ("test.pdf", dummy_pdf, "application/pdf")}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "document_id" in data
