"""
Diagnostic command: lists every Gemini model available to your API key,
and which ones support embedding vs. chat generation.

Run with: python manage.py list_gemini_models

Useful because Google renames/retires Gemini model names periodically,
and availability can vary by account/region - this asks your key directly
instead of guessing from documentation that might be outdated.
"""
import google.generativeai as genai
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "List Gemini models available to your API key, grouped by capability."

    def handle(self, *args, **options):
        if not settings.GEMINI_API_KEY:
            raise CommandError(
                "GEMINI_API_KEY is not set in your .env file. Add it first - "
                "see .env.example."
            )

        genai.configure(api_key=settings.GEMINI_API_KEY)

        embedding_models = []
        chat_models = []

        for model in genai.list_models():
            methods = model.supported_generation_methods
            if 'embedContent' in methods:
                embedding_models.append(model.name)
            if 'generateContent' in methods:
                chat_models.append(model.name)

        self.stdout.write(self.style.SUCCESS("\nModels that support embeddings (use for EMBEDDING_MODEL):"))
        if embedding_models:
            for name in embedding_models:
                self.stdout.write(f"  - {name}")
        else:
            self.stdout.write(self.style.WARNING("  None found."))

        self.stdout.write(self.style.SUCCESS("\nModels that support chat generation (use for CHAT_MODEL):"))
        if chat_models:
            for name in chat_models:
                self.stdout.write(f"  - {name}")
        else:
            self.stdout.write(self.style.WARNING("  None found."))

        self.stdout.write(
            "\nCopy the exact name of one from each list above into your .env file, "
            "for EMBEDDING_MODEL and CHAT_MODEL respectively.\n"
        )
