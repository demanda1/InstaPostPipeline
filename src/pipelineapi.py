import io
import os
import uuid
import zipfile
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import Response, JSONResponse
from pydantic import BaseModel
from workers import WorkerEntrypoint
from js import Uint8Array
import asgi

app = FastAPI()


class TopicRequest(BaseModel):
    topic: str


def _get_bucket(request: Request):
    env = request.scope.get("env")
    bucket = getattr(env, "BUCKET", None) if env is not None else None
    if bucket is None:
        raise HTTPException(status_code=500, detail="R2 bucket binding 'BUCKET' is not configured")
    return bucket


@app.post("/generate-posts")
async def start_pipeline(data: TopicRequest, request: Request):
    from run_pipeline import run_pipeline
    env = request.scope.get("env")

    final_slides = run_pipeline(data.topic, env)

    print(f"[DEBUG] pipelineapi cwd: {os.getcwd()}")
    print(f"[DEBUG] pipelineapi files: {os.listdir('.')}")

    generated_images = {}

    for path in final_slides:
        if os.path.exists(path):
            with open(path, "rb") as f:
                generated_images[os.path.basename(path)] = f.read()
            print(f"✅ Loaded from pipeline path: {path}")
        else:
            print(f"❌ Missing from pipeline path: {path}")

    for file in os.listdir("."):
        if file.startswith("final_slide_") and file.endswith(".jpg"):
            if file not in generated_images:
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

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for file_name, image_bytes in generated_images.items():
            zip_file.writestr(file_name, image_bytes)
    zip_bytes = zip_buffer.getvalue()

    key = f"carousel-{uuid.uuid4().hex}.zip"

    bucket = _get_bucket(request)
    js_buf = Uint8Array.new(len(zip_bytes))
    js_buf.assign(zip_bytes)
    await bucket.put(
        key,
        js_buf,
        httpMetadata={"contentType": "application/zip"},
    )
    print(f"✅ Uploaded zip to R2 with key: {key} ({len(zip_bytes)} bytes)")

    return JSONResponse(
        status_code=201,
        content={
            "key": key,
            "download_url": f"/download/{key}",
            "size_bytes": len(zip_bytes),
            "file_count": len(generated_images),
        },
    )


@app.get("/download/{key}")
async def download_zip(key: str, request: Request):
    bucket = _get_bucket(request)
    obj = await bucket.get(key)
    if obj is None:
        raise HTTPException(status_code=404, detail=f"No object found for key '{key}'")

    ab = await obj.arrayBuffer()
    zip_bytes = bytes(Uint8Array.new(ab))

    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{key}"'},
    )


@app.delete("/download/{key}")
async def delete_zip(key: str, request: Request):
    bucket = _get_bucket(request)
    await bucket.delete(key)
    print(f"🗑️  Deleted R2 object: {key}")
    return Response(status_code=204)


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        return await asgi.fetch(app, request, self.env)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
