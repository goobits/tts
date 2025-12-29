"""
HTTP server for TTS (Text-to-Speech) API.

Exposes TTS functionality over HTTP for Matilda integration.
Supports text-to-speech synthesis with provider/voice selection.

Usage:
    voice serve --port 8771

    # Or directly:
    python -m matilda_voice.server --port 8771
"""

import argparse
import asyncio
import base64
import json
import os
import tempfile

from aiohttp import web
from aiohttp.web import Request, Response

# CORS headers for browser/cross-origin access
CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization",
}


def add_cors_headers(response: Response) -> Response:
    """Add CORS headers to response."""
    for key, value in CORS_HEADERS.items():
        response.headers[key] = value
    return response


async def handle_options(request: Request) -> Response:
    """Handle CORS preflight requests."""
    return add_cors_headers(Response(status=200))


async def handle_health(request: Request) -> Response:
    """Health check endpoint."""
    return add_cors_headers(web.json_response({"status": "ok", "service": "voice"}))


async def handle_speak(request: Request) -> Response:
    """
    Synthesize and play text-to-speech.

    POST /speak
    {
        "text": "Hello world",
        "voice": "edge_tts:en-US-AriaNeural",  // optional
        "provider": "edge_tts"                  // optional (inferred from voice)
    }

    Response:
    {
        "success": true,
        "text": "Hello world",
        "voice": "edge_tts:en-US-AriaNeural"
    }
    """
    try:
        data = await request.json()
    except json.JSONDecodeError:
        return add_cors_headers(web.json_response(
            {"error": "Invalid JSON"}, status=400
        ))

    text = data.get("text")
    if not text:
        return add_cors_headers(web.json_response(
            {"error": "Missing 'text' field"}, status=400
        ))

    voice = data.get("voice")
    provider = data.get("provider")

    try:
        # Import here to avoid circular imports
        from .app_hooks import on_speak

        # Run synthesis (this plays audio)
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: on_speak(text=text, voice=voice, provider=provider)
        )

        result = {
            "success": True,
            "text": text,
            "voice": voice,
        }
        return add_cors_headers(web.json_response(result))

    except Exception as e:
        return add_cors_headers(web.json_response(
            {"error": str(e)}, status=500
        ))


async def handle_synthesize(request: Request) -> Response:
    """
    Synthesize text and return audio data (no playback).

    POST /synthesize
    {
        "text": "Hello world",
        "voice": "edge_tts:en-US-AriaNeural",  // optional
        "provider": "edge_tts",                 // optional
        "format": "wav"                         // optional: wav, mp3
    }

    Response:
    {
        "success": true,
        "audio": "<base64-encoded audio>",
        "format": "wav",
        "text": "Hello world"
    }
    """
    try:
        data = await request.json()
    except json.JSONDecodeError:
        return add_cors_headers(web.json_response(
            {"error": "Invalid JSON"}, status=400
        ))

    text = data.get("text")
    if not text:
        return add_cors_headers(web.json_response(
            {"error": "Missing 'text' field"}, status=400
        ))

    voice = data.get("voice")
    provider = data.get("provider")
    audio_format = data.get("format", "wav")

    try:
        from .app_hooks import on_save

        # Create temp file for audio
        with tempfile.NamedTemporaryFile(suffix=f".{audio_format}", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            # Run synthesis to file
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: on_save(
                    text=text,
                    output=tmp_path,
                    voice=voice,
                    provider=provider,
                    format=audio_format,
                )
            )

            # Read audio file and encode as base64
            with open(tmp_path, "rb") as f:
                audio_data = f.read()
            audio_base64 = base64.b64encode(audio_data).decode("utf-8")

            result = {
                "success": True,
                "audio": audio_base64,
                "format": audio_format,
                "text": text,
                "size_bytes": len(audio_data),
            }
            return add_cors_headers(web.json_response(result))

        finally:
            # Clean up temp file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    except Exception as e:
        return add_cors_headers(web.json_response(
            {"error": str(e)}, status=500
        ))


async def handle_providers(request: Request) -> Response:
    """
    List available TTS providers.

    GET /providers

    Response:
    {
        "providers": ["edge_tts", "openai", "elevenlabs", ...]
    }
    """
    try:
        from .app_hooks import PROVIDERS_REGISTRY

        providers = list(PROVIDERS_REGISTRY.keys())
        return add_cors_headers(web.json_response({"providers": providers}))

    except Exception as e:
        return add_cors_headers(web.json_response(
            {"error": str(e)}, status=500
        ))


def create_app() -> web.Application:
    """Create the aiohttp application."""
    app = web.Application()

    # Routes
    app.router.add_route("OPTIONS", "/{path:.*}", handle_options)
    app.router.add_get("/health", handle_health)
    app.router.add_get("/", handle_health)
    app.router.add_post("/speak", handle_speak)
    app.router.add_post("/synthesize", handle_synthesize)
    app.router.add_get("/providers", handle_providers)

    return app


def run_server(host: str = "0.0.0.0", port: int = 8771):
    """Run the HTTP server."""
    app = create_app()

    print(f"Starting Voice server on http://{host}:{port}")
    print("  POST /speak      - Synthesize and play audio")
    print("  POST /synthesize - Synthesize and return audio data")
    print("  GET  /providers  - List available providers")
    print("  GET  /health     - Health check")
    print()

    web.run_app(app, host=host, port=port, print=None)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Voice TTS HTTP Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", "-p", type=int, default=8771, help="Port to listen on")
    args = parser.parse_args()

    run_server(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
