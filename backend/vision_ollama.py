"""
Image vision – direct use of image_vision.py algorithm.
Ollama qwen2.5vl, no chunking.
"""

import base64
import requests

from .config import OLLAMA_BASE_URL

OLLAMA_URL = f"{OLLAMA_BASE_URL}/api/generate"
MODEL = "qwen2.5vl"


def generate_from_image(image_path, prompt):
    """Direct algo from image_vision.py – returns (response_text, error_msg)."""
    try:
        with open(image_path, "rb") as f:
            image_base64 = base64.b64encode(f.read()).decode("utf-8")

        payload = {
            "model": MODEL,
            "prompt": prompt,
            "images": [image_base64],
            "stream": False,
        }

        response = requests.post(OLLAMA_URL, json=payload, timeout=120)

        if response.status_code != 200:
            err = response.text[:200] if response.text else f"HTTP {response.status_code}"
            return (None, f"Ollama error: {err}")

        data = response.json()
        out = data.get("response", "").strip() if data else ""
        return (out if out else None, None)
    except requests.exceptions.ConnectionError:
        return (None, "Cannot connect to Ollama. Is it running? Start it and run: ollama run qwen2.5vl")
    except requests.exceptions.Timeout:
        return (None, "Ollama timed out. The vision model may still be loading.")
    except Exception as e:
        return (None, str(e)[:150])
