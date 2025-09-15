from fastapi import APIRouter, Request, Depends, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
from io import BytesIO

from api.handlers import TtsHandler, get_tts_handler
from api.models import (
    GenerateSpeechRequest,
    VoiceCloneResponse,
    HealthCheckResponse,
    ErrorDetail
)

# ... (rest of the file remains the same) ...
router = APIRouter(prefix="/api/v1", tags=["TTS and Voice Cloning"])

@router.post(
    "/tts/generate",
    summary="Generate Speech from Text",
    description="Synthesizes audio from the provided text using an existing voice ID.",
    responses={
        200: {"content": {"audio/mpeg": {}}, "description": "Successful audio generation."},
        400: {"model": ErrorDetail, "description": "Invalid input."},
        500: {"model": ErrorDetail, "description": "Internal server error."},
    }
)
async def generate_speech(
    request_data: GenerateSpeechRequest,
    request: Request,
    handler: TtsHandler = Depends(get_tts_handler)
):
    audio_bytes = await handler.generate_speech(request_data, request)
    return StreamingResponse(BytesIO(audio_bytes), media_type="audio/mpeg")

@router.post(
    "/voice/clone",
    summary="Clone a New Voice",
    description="Uploads an audio file and creates a new voice clone with a specified ID.",
    response_model=VoiceCloneResponse,
)
async def clone_voice(
    request: Request,
    new_voice_id: str = Form(
        ...,
        min_length=8,
        pattern=r'^[a-zA-Z][a-zA-Z0-9]*$',
        description="A unique ID for the new voice. Must be at least 8 characters and start with a letter.",
        example="MyCustomVoice01"
    ),
    audio_file: UploadFile = File(..., description="The MP3 or WAV audio file for cloning."),
    handler: TtsHandler = Depends(get_tts_handler)
):
    return await handler.clone_voice(new_voice_id, audio_file, request)


@router.post(
    "/voice/clone-and-generate",
    summary="Clone Voice and Generate Speech (Automated Workflow)",
    description="The primary automated endpoint. Uploads an audio file, clones a new voice, and immediately generates speech with it.",
    responses={
        200: {"content": {"audio/mpeg": {}}, "description": "Successful audio generation."},
        400: {"model": ErrorDetail, "description": "Invalid input."},
        500: {"model": ErrorDetail, "description": "Internal server error."},
    }
)
async def clone_and_generate(
    request: Request,
    text: str = Form(..., description="The text to synthesize."),
    new_voice_id: str = Form(
        ...,
        min_length=8,
        pattern=r'^[a-zA-Z][a-zA-Z0-9]*$',
        description="A unique ID for the new voice.",
        example="MyNewCloneAndSpeakVoice"
    ),
    audio_file: UploadFile = File(..., description="The audio file for cloning."),
    handler: TtsHandler = Depends(get_tts_handler)
):
    audio_bytes = await handler.clone_and_generate_speech(text, new_voice_id, audio_file, request)
    return StreamingResponse(BytesIO(audio_bytes), media_type="audio/mpeg")

@router.get("/health", response_model=HealthCheckResponse, summary="Service Health Check")
async def health_check(request: Request, handler: TtsHandler = Depends(get_tts_handler)):
    return await handler.get_health_status(request)