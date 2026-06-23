import os


def public_config():
    return {
        "app": {
            "name": "VisePanda",
            "domain": "go2china.space",
            "version": "6.1.1",
            "environment": os.environ.get("VERCEL_ENV") or os.environ.get("ENVIRONMENT", "local"),
        },
        "features": {
            "auth": True,
            "trips": True,
            "chat": True,
            "visa": True,
            "admin": True,
        },
        "auth": {
            "emailVerification": True,
            "google": bool(os.environ.get("GOOGLE_CLIENT_ID") and os.environ.get("GOOGLE_CLIENT_SECRET")),
            "emailProvider": "resend" if os.environ.get("RESEND_API_KEY") else "development",
        },
        "ai": {
            "provider": "deepseek" if os.environ.get("DEEPSEEK_API_KEY") else "local-guide",
            "streaming": True,
            "routes": [
                "local-guide",
                "deepseek" if os.environ.get("DEEPSEEK_API_KEY") else "deepseek-configurable",
                "openai-compatible" if (
                    os.environ.get("OPENAI_COMPATIBLE_API_KEY")
                    and os.environ.get("OPENAI_COMPATIBLE_BASE_URL")
                    and os.environ.get("OPENAI_COMPATIBLE_MODEL")
                ) else "openai-compatible-configurable",
            ],
        },
    }
