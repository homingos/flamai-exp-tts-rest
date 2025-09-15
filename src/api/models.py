from fastapi import APIRouter, Request, Depends, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from io import BytesIO

from src.api.handlers import TtsHandler, get_tts_handler
from src.api.models import (
    GenerateSpeechRequest,
    VoiceCloneResponse,
    HealthCheckResponse,
    ErrorDetail
)

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
    """
    Generates audio and streams it back as an MP3 file.
    """
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
    """
    Handles the two-step process of uploading an audio file and creating a voice clone.
    """
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
    """
    Performs the full clone-and-speak workflow in a single API call.
    """
    audio_bytes = await handler.clone_and_generate_speech(text, new_voice_id, audio_file, request)
    return StreamingResponse(BytesIO(audio_bytes), media_type="audio/mpeg")

@router.get("/health", response_model=HealthCheckResponse, summary="Service Health Check")
async def health_check(request: Request, handler: TtsHandler = Depends(get_tts_handler)):
    """
    Performs a health check on the API and its dependent services.
    """
    return await handler.get_health_status(request)