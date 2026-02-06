from django.apps import AppConfig


class ConversationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.conversations"

    def ready(self):
        """Pre-load embedding model on Django startup"""
        import os
        import sys

        # Only pre-load for celery or if explicitly requested
        # Disabled for runserver to avoid slow cold starts during development
        should_preload = any(
            [
                "celery" in str(sys.argv),
                os.environ.get("PRELOAD_MODELS") == "true",
            ]
        )

        if should_preload:
            print("[STARTUP] 🚀 Pre-loading embedding model...")
            try:
                from .huggingface_service import preload_model

                preload_model()
                print("[STARTUP] ✅ Model ready - all requests will be fast!")
            except Exception as e:
                print(f"[STARTUP] ⚠️ Could not pre-load model: {e}")
