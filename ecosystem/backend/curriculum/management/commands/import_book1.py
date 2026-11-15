"""Loads Book 1's 35 lessons from materials/book1/lessons.py (the same source as the slide decks)."""
import importlib.util

from django.conf import settings
from django.core.management.base import BaseCommand

from curriculum.models import Book, Unit

KIND = {"pre": "Getting ready", "vowels": "Vowels", "phonics": "New sound", "review": "Review",
        "reading": "Reading", "celebration": "Show"}


class Command(BaseCommand):
    help = "Import Book 1 lessons from materials/book1/lessons.py. Safe to run again."

    def handle(self, *args, **opts):
        path = settings.REPO_DIR / "materials" / "book1" / "lessons.py"
        spec = importlib.util.spec_from_file_location("hilys_book1_lessons", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        book, _ = Book.objects.update_or_create(code="book-1", defaults={"title": "Book 1", "level": "beginner", "order": 1})
        Book.objects.update_or_create(code="book-1b", defaults={"title": "Book 1b", "level": "beginner", "order": 2, "is_ready": False})
        for L in mod.LESSONS:
            Unit.objects.update_or_create(book=book, number=L["n"], defaults={
                "title_nd": L["title_nd"], "title_en": L["title_en"], "kind": KIND.get(L["kind"], L["kind"]),
                "culture": L["culture"][1] if L.get("culture") else "", "pages": L.get("pages", "")})
        self.stdout.write(self.style.SUCCESS(f"Book 1: {book.units.count()} lessons"))
