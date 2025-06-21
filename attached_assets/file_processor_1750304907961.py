from ai_providers import ai_generate

class AdvancedFileProcessor:
    def process_file(self, file_path: str, file_type: str, user_id: str) -> dict:
        try:
            if file_type in ["txt", "md", "csv", "py", "js", "json", "xml", "html", "css", "yaml", "yml"]:
                content = self.read_text_file(file_path)
                analysis = self.analyze_text(content)
                return {"type": "text", "analysis": analysis}
            elif file_type in ["pdf"]:
                content = self.read_pdf_file(file_path)
                analysis = self.analyze_text(content)
                return {"type": "pdf", "analysis": analysis}
            elif file_type in ["png", "jpg", "jpeg", "gif", "bmp", "tiff", "webp"]:
                img_base64 = self.encode_image_base64(file_path)
                analysis = self.analyze_image(img_base64)
                return {"type": "image", "analysis": analysis}
            else:
                return {"error": "Unsupported file type"}
        except Exception as e:
            # logging as before
            return {"error": f"File processing failed: {str(e)}"}

    def read_text_file(self, file_path: str) -> str:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

    def read_pdf_file(self, file_path: str) -> str:
        import PyPDF2
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            return "\n".join(page.extract_text() or "" for page in reader.pages)

    def encode_image_base64(self, file_path: str) -> str:
        import base64
        with open(file_path, "rb") as f:
            return base64.b64encode(f.read()).decode()

    def analyze_text(self, content: str) -> dict:
        if not content.strip():
            return {"summary": "Empty file."}
        prompt = "Analyze the following document for main topics, summary, and key points:\n" + content[:3500]
        summary = ai_generate(prompt)
        return {"summary": summary}

    def analyze_image(self, img_base64: str) -> dict:
        prompt = "Analyze this image and describe its content in detail. (base64 data not shown here)"
        summary = ai_generate(prompt)
        return {"description": summary}