import io
import zipfile
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from run_pipeline import run_pipeline
import os
from workers import WorkerEntrypoint
import asgi

# Import your existing function from your file
from run_pipeline import run_pipeline 

app = FastAPI()

# This defines what the UI sends to the backend
class TopicRequest(BaseModel):
    topic: str

class Default(WorkerEntrypoint):
    async def fetch(self, request):
        # This passes the 'env' object (containing your secrets) to the app
        all_keys = [getattr(self.env, key) for key in dir(self.env) if not key.startswith('_')]
        
        return await asgi.fetch(app, request, self.env)

@app.post("/generate-posts")
async def start_pipeline(request: TopicRequest):
    # 1. Run your existing logic
    # Note: Ensure run_pipeline returns the list of image bytes or paths
    env = request.scope.get("env")
    run_pipeline(request.topic, env) 

    file_names = ["final_slide_1.jpg", "final_slide_2.jpg", "final_slide_3.jpg", "final_slide_4.jpg"]
    
    # 2. Create ZIP in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        for file_name in file_names:
            if os.path.exists(file_name):
                # Add the file from the disk to the ZIP
                zip_file.write(file_name)
                # Optional: Remove the file from disk after adding to ZIP to keep it clean
                # os.remove(file_name) 
            else:
                print(f"Warning: {file_name} not found!")
    
    zip_buffer.seek(0)

    if len(zip_buffer.getvalue()) == 0:
        raise HTTPException(status_code=500, detail="No images were found to ZIP.")
    
    # 3. Stream the ZIP to the UI for download
    return StreamingResponse(
        zip_buffer,
        media_type="application/x-zip-compressed",
        headers={"Content-Disposition": "attachment; filename=carousel.zip"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
