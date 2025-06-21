
import modal

    
###
# Constants
###

MINUTE = 60 # seconds
HOUR = MINUTE * 60
DAY = HOUR * 24

###
# Image
###

asgi_image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("poppler-utils")
    .pip_install(
        "httpx>=0.28.1",
        "pydantic>=2.11.1",
        "python-dotenv>=1.1.0",
        "starlette>=0.41.0",
        "markdown>=3.5.1",
        "fastapi",
        "python-multipart",
        "moondream",
        "pillow",
    )
)


###
# Imports
### 

with asgi_image.imports():
    from fastapi import FastAPI, UploadFile, File, HTTPException
    from fastapi.responses import HTMLResponse
    import moondream as md # type: ignore
    import os
    from PIL import Image
    import io


###
# App
###

app = modal.App(name="moondream-ocr")

### 
# FastAPI
###

# Request model
@app.function(
    image=asgi_image,
    max_containers=20,
    secrets=[modal.Secret.from_name("moondream")]
)
@modal.asgi_app(label="moondream-ocr")
def moondream_application():
    web_application = FastAPI(title="Moondream", description="Extract information from images")

    # Root endpoint
    @web_application.get("/")
    def root():
        return {"message": "Hello World"}

    # Image upload endpoint to capture byte stream and report size
    @web_application.post("/upload-image")
    async def upload_image(file: UploadFile = File(...)):
        try:
            # Read the file contents
            contents = await file.read()
            image = Image.open(io.BytesIO(contents))
            
            # Get the size in bytes
            size_bytes = len(contents)
            
            # Model
            model = md.vl(api_key=os.getenv("MOONDREAM_API_KEY"))
            answer = model.query(image, "Give me the text in this image.")["answer"]
            
            # Optional: Validate it's an image file (basic check)
            if not file.content_type or not file.content_type.startswith('image/'):
                raise HTTPException(status_code=400, detail="File must be an image")
            
            return {
                "filename": file.filename,
                "content_type": file.content_type,
                "size_bytes": size_bytes,
                "size_kb": round(size_bytes / 1024, 2),
                "size_mb": round(size_bytes / (1024 * 1024), 2),
                "answer": answer
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

    return web_application