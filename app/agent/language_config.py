"""
Language configuration for the application.
Supports ES (Spanish) and ENG (English) based on environment variable.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Language configuration
LANGUAGE_CONFIG = {
    "ES": {
        "code": "ES",
        "name": "Spanish",
        "headers": {
            "overview": "RESUMEN",
            "key_points": "PUNTOS CLAVE",
            "why_it_matters": "POR QUÉ IMPORTA",
            "simple_explanation": "EXPLICACIÓN SIMPLE"
        },
        "display_headers": {
            "overview": "Resumen:",
            "key_points": "Puntos Clave:",
            "why_it_matters": "Por Qué Importa:",
            "simple_explanation": "Explicación Simple:"
        },
        "prompt_instructions": "**ALL OUTPUT MUST BE IN SPANISH** - Translate everything to Spanish, including section headers and all content.",
        "prompt_language_note": "Use simple everyday words in Spanish. No jargon unless instantly explained in 2-3 words.",
        "article_title_label": "Título del Artículo",
        "article_content_label": "Contenido del Artículo",
        "format_instruction": "Produce solo el resumen usando el formato exacto anterior. Todo debe estar en español. Nunca excedas 8 líneas en total."
    },
    "ENG": {
        "code": "ENG",
        "name": "English",
        "headers": {
            "overview": "OVERVIEW",
            "key_points": "KEY POINTS",
            "why_it_matters": "WHY IT MATTERS",
            "simple_explanation": "SIMPLE EXPLANATION"
        },
        "display_headers": {
            "overview": "Overview:",
            "key_points": "Key Points:",
            "why_it_matters": "Why It Matters:",
            "simple_explanation": "Simple Explanation:"
        },
        "prompt_instructions": "**ALL OUTPUT MUST BE IN ENGLISH** - Write everything in English, including section headers and all content.",
        "prompt_language_note": "Use simple everyday words. No jargon unless instantly explained in 2-3 words.",
        "article_title_label": "Article Title",
        "article_content_label": "Article Content",
        "format_instruction": "Produce only the summary using the exact format above. Never exceed 8 lines total."
    }
}


def get_language() -> str:
    """
    Get the language code from environment variable.
    Defaults to 'ES' if not set or invalid.
    
    Returns:
        Language code: 'ES' or 'ENG'
    """
    lang = os.getenv("LANGUAGE", "ES").upper()
    if lang not in LANGUAGE_CONFIG:
        # Default to ES if invalid
        return "ES"
    return lang


def get_language_config() -> dict:
    """
    Get the full language configuration for the current language.
    
    Returns:
        Dictionary with language configuration
    """
    lang = get_language()
    return LANGUAGE_CONFIG[lang]


def get_header(header_type: str) -> str:
    """
    Get the section header for the current language.
    
    Args:
        header_type: One of 'overview', 'key_points', 'why_it_matters', 'simple_explanation'
    
    Returns:
        Header string in the current language
    """
    config = get_language_config()
    return config["headers"].get(header_type, "")


def get_display_header(header_type: str) -> str:
    """
    Get the display header (for HTML) for the current language.
    
    Args:
        header_type: One of 'overview', 'key_points', 'why_it_matters', 'simple_explanation'
    
    Returns:
        Display header string in the current language
    """
    config = get_language_config()
    return config["display_headers"].get(header_type, "")
