from workers import Response

# Inside your start_pipeline or a dedicated generation function
async def generate_image(prompt, env):
    # Call the Cloudflare AI model
    # The output is a binary stream (bytes) of the image
    image_bytes = await env.AI.run(
        "@cf/bytedance/stable-diffusion-xl-lightning",
        {"prompt": prompt}
    )
    
    # You can now pass these bytes directly to your ZIP/PIL functions
    return image_bytes
