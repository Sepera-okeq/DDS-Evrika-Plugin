"""Tiny JSON-based localization for DDSEvrikaPlugin.

Every language is a file ``locales/<code>.json`` with flat "key": "text" pairs
and a ``_language_name`` entry (the language's own name). English is the
reference and the fallback for missing keys. To add a language, copy en.json,
translate the values and keep the ``{placeholders}`` intact.
"""

import json
import os

LOCALES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "locales")
FALLBACK_LANGUAGE = "en"
AUTO = "auto"


def _load(code):
    try:
        with open(os.path.join(LOCALES_DIR, code + ".json"), "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def available_languages():
    """List of (code, native name), sorted by code."""
    languages = []
    try:
        files = sorted(os.listdir(LOCALES_DIR))
    except OSError:
        files = []
    for name in files:
        if name.endswith(".json"):
            code = name[:-5]
            languages.append((code, _load(code).get("_language_name", code)))
    return languages


def detect_language(ui_languages):
    """Pick the first supported language from locale names like "ru_RU" or "pt-BR".

    Krita applies its own "Switch Application Language" setting through the
    LANGUAGE environment variable, so it takes priority over the system locale.
    """
    supported = {code for code, _ in available_languages()}
    candidates = [c for c in os.environ.get("LANGUAGE", "").split(":") if c]
    candidates += list(ui_languages)
    for candidate in candidates:
        normalized = candidate.replace("-", "_")
        for code in (normalized, normalized.split("_")[0]):
            if code in supported:
                return code
    return FALLBACK_LANGUAGE


class Translator:
    def __init__(self, language=AUTO, ui_languages=()):
        self.language = detect_language(ui_languages) if language in (AUTO, "", None) else language
        self._fallback = _load(FALLBACK_LANGUAGE)
        self._strings = self._fallback if self.language == FALLBACK_LANGUAGE else _load(self.language)

    def __call__(self, key, **params):
        text = self._strings.get(key) or self._fallback.get(key) or key
        if params:
            try:
                text = text.format(**params)
            except (KeyError, IndexError, ValueError):
                pass
        return text

    def error(self, tool_error):
        """Human readable text for a dds_tools.ToolError."""
        text = self(tool_error.code, **tool_error.params)
        if tool_error.details:
            text += "\n\n" + tool_error.details
        return text
