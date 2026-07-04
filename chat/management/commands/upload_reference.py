"""
Upload a reference text file to an OpenAI vector store.

Usage:
    python manage.py upload_reference                 # uses reference/knowledge.txt
    python manage.py upload_reference path/to/file.txt

If OPENAI_VECTOR_STORE_ID is set in .env the file is added to that store;
otherwise a new vector store is created and its id is printed so you can
add it to .env.
"""

from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from openai import OpenAI, OpenAIError


class Command(BaseCommand):
    help = "Upload a reference text file to the assistant's OpenAI vector store."

    def add_arguments(self, parser):
        parser.add_argument(
            "path",
            nargs="?",
            default="reference/knowledge.txt",
            help="Path to the text file to upload (default: reference/knowledge.txt)",
        )

    def handle(self, *args, **options):
        if not settings.OPENAI_API_KEY:
            raise CommandError("OPENAI_API_KEY is not set in .env.")

        path = Path(options["path"])
        if not path.is_file():
            raise CommandError(f"File not found: {path}")

        client = OpenAI(api_key=settings.OPENAI_API_KEY)

        try:
            vector_store_id = settings.OPENAI_VECTOR_STORE_ID
            if vector_store_id:
                self.stdout.write(f"Using existing vector store {vector_store_id}")
            else:
                store = client.vector_stores.create(name="95731-group2-reference")
                vector_store_id = store.id
                self.stdout.write(f"Created vector store {vector_store_id}")

            with path.open("rb") as fh:
                vs_file = client.vector_stores.files.upload_and_poll(
                    vector_store_id=vector_store_id, file=fh
                )
        except OpenAIError as exc:
            raise CommandError(f"OpenAI request failed: {exc}") from exc

        if vs_file.status != "completed":
            raise CommandError(
                f"Upload finished with status {vs_file.status!r} "
                f"(error: {vs_file.last_error})"
            )

        self.stdout.write(self.style.SUCCESS(f"Uploaded {path} ({vs_file.id})"))
        if not settings.OPENAI_VECTOR_STORE_ID:
            self.stdout.write(
                self.style.WARNING(
                    f"Add this line to your .env so the assistant uses the store:\n"
                    f"OPENAI_VECTOR_STORE_ID={vector_store_id}"
                )
            )
