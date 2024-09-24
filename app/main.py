import base64
from dotenv import load_dotenv
from fastapi import FastAPI
import requests
from Image import Image
from openai import AzureOpenAI
import os

load_dotenv()

app = FastAPI(title="Spital Bülach API")
app.openapi_version = "3.0.3"


@app.post(
    "/api/remove-background",
    operation_id="remove_background",
    summary="Remove background from image",
    description="""Returns the image without background""",
    response_model=Image,
)
async def remove_background(image: Image) -> Image:
    try:
        endoint_url = f"{os.getenv('AZURE_VISION_ENDPOINT')}imageanalysis:segment"

        headers = {
            'Content-Type': 'application/octet-stream',
            'Ocp-Apim-Subscription-Key': os.getenv('AZURE_VISION_KEY')
        }

        params = {
            'mode': 'backgroundRemoval',
            'api-version': os.getenv('AZURE_VISION_VERSION')
        }

        image_data = base64.b64decode(image.base64.split(",")[1])

        res = requests.post(
            url=endoint_url,
            params=params,
            headers=headers,
            data=image_data
        )

        if res.status_code == 200:
            image_no_bg = base64.b64encode(res.content).decode('utf-8')
            image_no_bg = f"data:image/png;base64,{image_no_bg}"
            return Image(base64=image_no_bg)
        else:
            return Image(error=res.json())

    except Exception as e:
        return Image(error=f"Failed to remove background.\n{str(e)}")


@app.post(
    "/api/generate-image",
    operation_id="generate_image",
    summary="Generate image",
    description="""Returns a generated image""",
    response_model=Image,
)
async def generate_image(image: Image) -> Image:
    try:
        base_url = os.getenv('AZURE_OPENAI_ENDPOINT')
        api_version = os.getenv('AZURE_OPENAI_VERSION')
        api_key = os.getenv('AZURE_OPENAI_KEY')

        openai_client = AzureOpenAI(
            api_version=api_version,
            azure_endpoint=base_url,
            api_key=api_key
        )

        response = openai_client.images.generate(
            model="dall-e-3",
            prompt=image.description,
            size="1024x1024",
            quality="standard",
            n=1,
        )

        image_url = response.data[0].url

        response = requests.get(image_url)

        if response.status_code == 200:
            image_base64 = base64.b64encode(response.content).decode('utf-8')
            return Image(base64=f"data:image/png;base64,{image_base64}")
        else:
            return Image(error="Failed to download image")

    except Exception as e:
        return Image(
            error=f"Failed to generate image.\n{str(e)}"
        )



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
