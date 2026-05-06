import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def load_env_file() -> None:
    env_path = Path(__file__).with_name(".env")
    if not env_path.exists():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("'\""))


load_env_file()

OLLAMA_URL = os.getenv("OLLAMA_URL", "https://ollama.com/api/generate")
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")
MODEL = os.getenv("OLLAMA_MODEL", "gpt-oss:120b")


def generate_text(prompt: str, model: str = MODEL) -> str:
    if OLLAMA_URL.startswith("https://ollama.com") and not OLLAMA_API_KEY:
        raise RuntimeError(
            "OLLAMA_API_KEY is required for Ollama's web API. Create an API key "
            "on ollama.com and add OLLAMA_API_KEY=your_api_key to backend/.env."
        )

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
    }
    headers = {"Content-Type": "application/json"}
    if OLLAMA_API_KEY:
        headers["Authorization"] = f"Bearer {OLLAMA_API_KEY}"

    request = Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    try:
        with urlopen(request, timeout=60) as response:
            data = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Ollama returned HTTP {exc.code}: {details}") from exc
    except URLError as exc:
        raise RuntimeError(
            "Could not connect to Ollama. Check your internet connection, API key, "
            f"or OLLAMA_URL. Current URL: {OLLAMA_URL}"
        ) from exc

    generated = data.get("response")
    if not generated:
        raise RuntimeError(f"Ollama response did not include generated text: {data}")

    return generated


def summarize_gas_inventory(materials: list[dict]) -> str:
    lines = []
    for material in materials:
        existing = int(material.get("existing") or 0)
        counted = int(material.get("counted") or 0)
        difference = counted - existing
        lines.append(
            f"- {material.get('name', 'Material sin nombre')}: "
            f"existente={existing}, contado={counted}, diferencia={difference}"
        )

    inventory_text = "\n".join(lines) if lines else "No hay materiales de gas registrados."
    prompt = (
        "Resume el conteo de inventario de gas para CEYE quirofano en espanol. "
        "Se breve, claro y operativo. Menciona el estado general, materiales con "
        "diferencias importantes y una accion recomendada. Maximo 5 lineas.\n\n"
        f"Datos:\n{inventory_text}"
    )
    return generate_text(prompt)


def main() -> None:
    print("Ollama AI chat. Press Enter on an empty line to exit.")
    print(f"Model: {MODEL}")

    while True:
        prompt = input("\nYou: ").strip()
        if not prompt:
            break

        try:
            print("\nAI:", generate_text(prompt))
        except RuntimeError as exc:
            print(f"\nError: {exc}")


if __name__ == "__main__":
    main()
