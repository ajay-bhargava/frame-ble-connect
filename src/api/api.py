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
        "moondream>=1.0.3"
    )
)

###
# Imports
### 

with asgi_image.imports():
    from fastapi import FastAPI
    from fastapi.responses import HTMLResponse
    import markdown

###
# App
###

app = modal.App(name="rebuild-ocr-v2")

### 
# FastAPI
###

# Request model
@app.function(
    image=asgi_image,
    max_containers=20
)
@modal.asgi_app(label="rebuild-vision")
def vision_application():
    web_application = FastAPI(title="Rebuild OCR V2", description="Extract information from images")

    # Root endpoint
    @web_application.get("/")
    def root():
        return {"message": "Hello World"}

    return web_application