import io
import os
import uuid
import zipfile
from pathlib import Path

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

load_dotenv()

R2_ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_BUCKET = os.getenv("R2_BUCKET", "instapost-zips")


def _r2_client():
    if not (R2_ACCOUNT_ID and R2_ACCESS_KEY_ID and R2_SECRET_ACCESS_KEY):
        raise HTTPException(
            status_code=500,
            detail="R2 credentials are not configured (set R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY).",
        )
    return boto3.client(
        "s3",
        endpoint_url=f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        region_name="auto",
        config=Config(signature_version="s3v4"),
    )


app = FastAPI()


class TopicRequest(BaseModel):
    topic: str


@app.post("/generate-posts")
def start_pipeline(data: TopicRequest):
    from run_pipeline import run_pipeline

    final_slides = run_pipeline(data.topic)

    generated_images = {}
    for path in final_slides:
        if os.path.exists(path):
            with open(path, "rb") as f:
                generated_images[os.path.basename(path)] = f.read()

    for file in os.listdir("."):
        if file.startswith("final_slide_") and file.endswith(".jpg") and file not in generated_images:
            try:
                with open(file, "rb") as f:
                    generated_images[file] = f.read()
            except Exception as e:
                print(f"Failed to read {file}: {e}")

    if not generated_images:
        raise HTTPException(status_code=500, detail="Pipeline produced no images.")

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for file_name, image_bytes in generated_images.items():
            zip_file.writestr(file_name, image_bytes)
    zip_bytes = zip_buffer.getvalue()

    key = f"carousel-{uuid.uuid4().hex}.zip"

    client = _r2_client()
    client.put_object(
        Bucket=R2_BUCKET,
        Key=key,
        Body=zip_bytes,
        ContentType="application/zip",
    )
    print(f"Uploaded zip to R2: {key} ({len(zip_bytes)} bytes)")

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
def download_zip(key: str):
    client = _r2_client()
    try:
        obj = client.get_object(Bucket=R2_BUCKET, Key=key)
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code", "")
        if code in {"NoSuchKey", "404"}:
            raise HTTPException(status_code=404, detail=f"No object found for key '{key}'")
        raise HTTPException(status_code=500, detail=f"R2 error: {e}")

    zip_bytes = obj["Body"].read()
    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{key}"'},
    )


@app.delete("/download/{key}")
def delete_zip(key: str):
    client = _r2_client()
    client.delete_object(Bucket=R2_BUCKET, Key=key)
    print(f"Deleted R2 object: {key}")
    return Response(status_code=204)


_public_dir = Path(__file__).resolve().parent.parent / "public"
if _public_dir.is_dir():
    app.mount("/", StaticFiles(directory=str(_public_dir), html=True), name="ui")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
