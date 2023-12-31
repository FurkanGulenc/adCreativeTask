from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image, ImageOps
from io import BytesIO
from utils.create_image_template import create_marketing_image
import io
from diffusers import DiffusionPipeline
import torch

# from diffusers import StableDiffusionInstructPix2PixPipeline, EulerAncestralDiscreteScheduler

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins="*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

"""model_id = "timbrooks/instruct-pix2pix"
pipe = StableDiffusionInstructPix2PixPipeline.from_pretrained(model_id, torch_dtype=torch.float32, safety_checker=None)
pipe.to("cpu") # intel işlemci kullandığım için cuda çalıştırmıyor bu nedenle cpu kullandım.
pipe.scheduler = EulerAncestralDiscreteScheduler.from_config(pipe.scheduler.config)
"""

pipe = DiffusionPipeline.from_pretrained(
    "stabilityai/stable-diffusion-2-1-unclip-small", torch_dtype=torch.float32
)
pipe.to("cpu")


@app.get("/")
def reed_root():
    return {"Hello": "World"}


@app.post("/img-2-img")
async def create_add(
    file: UploadFile = File(...),
    prompt: str = Form(...),
    image_color: str = Form(...),
    button_text: str = Form(...),
    punchline_text: str = Form(...),
    button_and_punchline_color: str = Form(...),
):
    # Dosyayı Al
    if file:
        print(file.filename)
    else:
        print("File not found.")

    file_extension = file.filename.rsplit(".", 1)[1].lower()

    if file_extension not in {"png", "jpg", "jpeg"}:
        raise HTTPException(status_code=400, detail="Unsupported file format.")

    contents = await file.read()

    image = Image.open(BytesIO(contents))
    image = ImageOps.exif_transpose(image)
    image = image.convert("RGB")

    prompt_template = f"{prompt}. Use the hex code {image_color} in new image."

    images = pipe(
        image=image, prompt=prompt_template, num_inference_steps=8
    ).images  # num_inference_steps'i işlemci gücünden kısmak için küçülttüm sonuçları etkileyecektir.

    image = images[0]

    result = create_marketing_image(
        image, punchline_text, button_text, button_and_punchline_color
    )

    # Görseli BytesIO nesnesine kaydet
    img_byte_arr = io.BytesIO()
    result.save(img_byte_arr, format="JPEG")
    img_byte_arr = io.BytesIO(img_byte_arr.getvalue())

    # StreamingResponse döndür
    return StreamingResponse(img_byte_arr, media_type="image/jpeg")
