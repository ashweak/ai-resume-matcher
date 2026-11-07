import io

from fastapi import HTTPException
from pypdf import PdfReader

MAX_BYTES = 5 * 1024 * 1024  # 5 MB


def extract_text(filename: str, data: bytes) -> str:
    if len(data) > MAX_BYTES:
        raise HTTPException(400, "File is too big. Please upload a resume under 5 MB.")
    name = filename.lower()
    if name.endswith(".pdf"):
        try:
            reader = PdfReader(io.BytesIO(data))
            return "\n".join(page.extract_text() or "" for page in reader.pages).strip()
        except Exception:
            raise HTTPException(400, "Could not read this PDF. Try saving it again as PDF, or use a TXT file.")
    if name.endswith(".txt"):
        return data.decode("utf-8", errors="ignore").strip()
    raise HTTPException(400, "Unsupported file type. Please upload a PDF or TXT resume.")
