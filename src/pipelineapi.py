import io
import zipfile
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
import os
from workers import WorkerEntrypoint
import asgi

app = FastAPI()

class TopicRequest(BaseModel):
    topic: str

@app.post("/generate-posts")
async def start_pipeline(data: TopicRequest, request: Request):
    from run_pipeline import run_pipeline
    env = request.scope.get("env")

    final_slides = run_pipeline(data.topic, env)

    print(f"[DEBUG] pipelineapi cwd: {os.getcwd()}")
    print(f"[DEBUG] pipelineapi files: {os.listdir('.')}")

    generated_images = {}

    # Method 1: Use paths returned directly by pipeline
    for path in final_slides:
        if os.path.exists(path):
            with open(path, "rb") as f:
                generated_images[os.path.basename(path)] = f.read()
            print(f"✅ Loaded from pipeline path: {path}")
        else:
            print(f"❌ Missing from pipeline path: {path}")

    # Method 2: Fallback — scan disk for any missed files
    for file in os.listdir("."):
        if file.startswith("final_slide_") and file.endswith(".jpg"):
            if file not in generated_images:  # ✅ skip if already loaded
                try:
                    with open(file, "rb") as f:
                        generated_images[file] = f.read()
                    print(f"✅ Loaded from disk scan: {file}")
                except Exception as e:
                    print(f"❌ Failed to read {file}: {e}")

    print(f"Total images collected: {len(generated_images)}")

    if not generated_images:
        raise HTTPException(
            status_code=500,
            detail=f"No images found. Pipeline returned: {final_slides}. Files on disk: {os.listdir('.')}"
        )

    # Build ZIP fully in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for file_name, image_bytes in generated_images.items():
            zip_file.writestr(file_name, image_bytes)

    zip_bytes = zip_buffer.getvalue()

    return Response(
        content=zip_bytes,
        media_type="application/x-zip-compressed",
        headers={"Content-Disposition": "attachment; filename=carousel.zip"}
    )


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        return await asgi.fetch(app, request, self.env)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)