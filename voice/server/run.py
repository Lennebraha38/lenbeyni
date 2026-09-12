"""ZenAI Voice gateway başlatıcısı.

Kullanım:
    ZENAI_ORIGIN="https://zenai-two.vercel.app" python -m voice.server.run
"""
import os
import uvicorn


def main() -> None:
    port = int(os.environ.get("PORT", "8787"))
    uvicorn.run(
        "voice.server.gateway:APP",
        host=os.environ.get("HOST", "0.0.0.0"),
        port=port,
        log_level=os.environ.get("LOG_LEVEL", "info"),
    )


if __name__ == "__main__":
    main()