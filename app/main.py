from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeResult, ContentFormat, AnalyzeDocumentRequest
from azure.core.credentials import AzureKeyCredential
import base64
from dotenv import load_dotenv
from fastapi import FastAPI
from openai import AzureOpenAI
import os
import requests

from Image import Image
from Text import Text
from Dialogue import Dialogue

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


@app.post(
    "/api/parse-pdf",
    operation_id="parse_pdf",
    summary="Transforms a PDF file into text",
    description="""Returns the content of the PDF file as markdown text""",
    response_model=Text,
)
async def parse_pdf(textfile: Text) -> Text:
    try:
 
        source_bytes = base64.b64decode(textfile.content)
        source_bytes = base64.b64decode(source_bytes)
        
        document_intelligence_client = DocumentIntelligenceClient(
            endpoint=os.getenv('AZURE_AI_SERVICE_ENDPOINT'),
            credential=AzureKeyCredential(os.getenv('AZURE_AI_SERVICE_KEY'))
        )

        poller = document_intelligence_client.begin_analyze_document(
            "prebuilt-layout",
            analyze_request=AnalyzeDocumentRequest(bytes_source=source_bytes),
            output_content_format=ContentFormat.MARKDOWN)

        result: AnalyzeResult = poller.result()
        
        return Text(
            path=textfile.path.replace(".pdf", ".txt").split("/")[-1] if textfile.path else None,
            content=result.content
        )
    
    except Exception as e:
        return Text(error=f"Failed to parse pdf.\n{str(e)}")


@app.post(
    "/api/answer-question",
    operation_id="answer_question",
    summary="Answers a question based on a context",
    description="""Returns the answer to the question""",
    response_model=Dialogue,
)
async def answer_question(dialogue: Dialogue) -> Dialogue:
    try:
        
        client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_KEY"),  
            api_version=os.getenv("AZURE_OPENAI_VERSION"),
            azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        
        messages=[
            {
                "role": "system",
                "content": f"You are a helpful assistant who answers questions in the same language they were asked, exclusively based on the context provided. If the question is unanswerable, you should say so. Here is what you know (the context):\n\n{dialogue.context}You are a helpful assistant that answers questions in the same language they were asked, strictly based on the provided context. If a question cannot be answered from the available context, politely inform the user that it is unanswerable. The context for this conversation is:\n\n{dialogue.context}"
            },
            {
                "role": "user",
                "content": dialogue.question
            }
        ]
        
    
        response = client.chat.completions.create(
            model='gpt-4o',
            messages=messages
        )
                
        return Dialogue(
            #question=dialogue.question,
            #context=dialogue.context,
            answer=response.choices[0].message.content
        )                            
    
    except Exception as e:
        return Dialogue(error=f"Failed to answer the question.\n{str(e)}")




if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
