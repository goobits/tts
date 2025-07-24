"""Type definitions for TTS CLI."""

from typing import Any, Dict, List, Optional, TypedDict


class VoiceSettings(TypedDict):
    """Voice settings for TTS synthesis."""
    stability: float
    similarity_boost: float
    style: float
    use_speaker_boost: bool


class ProviderInfo(TypedDict, total=False):
    """Provider information structure."""
    name: str
    description: str
    options: Dict[str, str]
    output_formats: List[str]
    sample_voices: List[str]
    capabilities: List[str]
    api_status: Optional[str]
    voices: Optional[List[Dict[str, Any]]]
    all_voices: Optional[List[str]]
    voice_descriptions: Optional[Dict[str, str]]
    features: Optional[Dict[str, Any]]
    pricing: Optional[str]
    output_format: Optional[str]
    auth_method: Optional[str]
    model: Optional[str]


class AudioEnvironment(TypedDict):
    """Audio environment check result."""
    available: bool
    reason: str
    pulse_available: bool
    alsa_available: bool


class VoiceInfo(TypedDict):
    """Voice information structure."""
    voice_id: str
    name: str
    labels: Optional[Dict[str, str]]
    description: Optional[str]
    preview_url: Optional[str]
    available_for_tiers: Optional[List[str]]
    settings: Optional[VoiceSettings]
    samples: Optional[Any]
    category: Optional[str]
    fine_tuning: Optional[Dict[str, Any]]
    language: Optional[str]
    description_: Optional[str]
    use_case: Optional[str]
    accent: Optional[str]
    descriptive: Optional[str]
    age: Optional[str]
    gender: Optional[str]
    voice_styles: Optional[List[str]]


class Config(TypedDict, total=False):
    """Configuration structure."""
    default_voice: str
    default_provider: str
    output_format: str
    output_directory: str

    # API Keys
    openai_api_key: Optional[str]
    elevenlabs_api_key: Optional[str]
    google_cloud_api_key: Optional[str]
    google_cloud_service_account_path: Optional[str]

    # Feature flags
    auto_provider_selection: bool
    voice_loading_enabled: bool

    # Performance settings
    http_streaming_chunk_size: int
    streaming_progress_interval: int
    ffmpeg_conversion_timeout: int
    ffplay_timeout: int
    thread_pool_max_workers: int

    # Voice browser settings
    browser_page_size: int
    browser_preview_text: str
