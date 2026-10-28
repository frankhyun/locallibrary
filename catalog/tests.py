from django.test import TestCase

from django.urls import reverse

from .models import Author, Book, BookAuthor, Language

class IndexViewTests(TestCase):
    def test_index_page_loads(self):
        response = self.client.get(reverse("index"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Local Library")

    def setUp(self):
        self.author = Author.objects.create(first_name="Ada", last_name="Lovelace")
        language, _ = Language.objects.get_or_create(name="English")
        self.book = Book.objects.create(
            title="Analytical Engines",
            summary="A history of computing.",
            isbn="1234567890123",
            language=language,
        )
        BookAuthor.objects.create(book=self.book, author=self.author, author_order=1)

    def test_book_list_displays_authors(self):
        response = self.client.get(reverse("book-list"))

        self.assertContains(response, self.book.title)
        self.assertContains(response, str(self.author))

    def test_book_detail_displays_authors(self):
        response = self.client.get(self.book.get_absolute_url())

        self.assertContains(response, str(self.author))

    def test_author_detail_displays_books(self):
        response = self.client.get(self.author.get_absolute_url())

        self.assertContains(response, self.book.title)
