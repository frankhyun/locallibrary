from datetime import date, timedelta

from allauth.account.models import EmailAddress
from django.contrib.auth.models import Permission
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .forms import RenewBookForm
from .models import Author, Book, BookAuthor, BookInstance, Language

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

    def test_index_counts_visits_in_session(self):
        first_response = self.client.get(reverse("index"))
        second_response = self.client.get(reverse("index"))

        self.assertContains(first_response, "visited this page 1 time")
        self.assertContains(second_response, "visited this page 2 times")

    def test_allauth_login_and_signup_pages_are_available(self):
        self.assertEqual(self.client.get(reverse("account_login")).status_code, 200)
        self.assertEqual(self.client.get(reverse("account_signup")).status_code, 200)

    def test_my_borrowed_requires_login(self):
        response = self.client.get(reverse("my-borrowed"))

        self.assertRedirects(
            response,
            f"{reverse('account_login')}?next={reverse('my-borrowed')}",
        )

    def test_my_borrowed_lists_only_current_users_loans(self):
        user = User.objects.create_user(
            username="reader", email="reader@example.com", password="StrongPass123!"
        )
        EmailAddress.objects.create(
            user=user, email=user.email, primary=True, verified=True
        )
        self.client.force_login(user)
        borrowed = BookInstance.objects.create(
            book=self.book,
            imprint="Library",
            status="o",
            borrower=user,
        )
        other_book = Book.objects.create(
            title="Computing",
            summary="Another book.",
            isbn="1234567890124",
            language=self.book.language,
        )
        other_instance = BookInstance.objects.create(
            book=other_book,
            imprint="Library",
            status="o",
        )

        response = self.client.get(reverse("my-borrowed"))

        self.assertContains(response, borrowed.book.title)
        self.assertNotContains(response, other_instance.book.title)

    def test_is_overdue(self):
        overdue = BookInstance.objects.create(
            book=self.book,
            imprint="Library",
            status="o",
            due_back=date.today() - timedelta(days=1),
        )
        current = BookInstance.objects.create(
            book=self.book,
            imprint="Library",
            status="o",
            due_back=date.today() + timedelta(days=1),
        )

        self.assertTrue(overdue.is_overdue)
        self.assertFalse(current.is_overdue)

    def test_all_borrowed_requires_permission(self):
        response = self.client.get(reverse("all-borrowed"))

        self.assertRedirects(
            response,
            f"{reverse('account_login')}?next={reverse('all-borrowed')}",
        )

        user = User.objects.create_user(username="member", password="StrongPass123!")
        self.client.force_login(user)
        self.assertEqual(self.client.get(reverse("all-borrowed")).status_code, 403)

    def test_librarian_sees_all_borrowed_books_and_borrowers(self):
        librarian = User.objects.create_user(
            username="librarian", password="StrongPass123!"
        )
        permission = Permission.objects.get(
            content_type__app_label="catalog",
            codename="can_mark_returned",
        )
        librarian.user_permissions.add(permission)
        self.client.force_login(librarian)
        borrowed = BookInstance.objects.create(
            book=self.book,
            imprint="Library",
            status="o",
            borrower=librarian,
        )

        response = self.client.get(reverse("all-borrowed"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, borrowed.book.title)
        self.assertContains(response, librarian.username)

    def test_renew_book_form_validates_date_range(self):
        today = date.today()

        self.assertTrue(RenewBookForm({"renewal_date": today}).is_valid())
        self.assertTrue(
            RenewBookForm(
                {"renewal_date": today + timedelta(weeks=4)}
            ).is_valid()
        )
        self.assertFalse(
            RenewBookForm(
                {"renewal_date": today - timedelta(days=1)}
            ).is_valid()
        )
        self.assertFalse(
            RenewBookForm(
                {"renewal_date": today + timedelta(weeks=4, days=1)}
            ).is_valid()
        )

    def test_renew_book_requires_permission_and_updates_due_date(self):
        librarian = User.objects.create_user(
            username="renewal-librarian", password="StrongPass123!"
        )
        permission = Permission.objects.get(
            content_type__app_label="catalog",
            codename="can_mark_returned",
        )
        librarian.user_permissions.add(permission)
        book_instance = BookInstance.objects.create(
            book=self.book,
            imprint="Library",
            status="o",
            borrower=librarian,
        )
        renew_url = reverse(
            "renew-book-librarian", kwargs={"pk": book_instance.pk}
        )

        self.assertRedirects(
            self.client.get(renew_url),
            f"{reverse('account_login')}?next={renew_url}",
        )
        self.client.force_login(librarian)
        response = self.client.get(renew_url)
        self.assertEqual(response.status_code, 200)

        new_due_date = date.today() + timedelta(days=7)
        response = self.client.post(
            renew_url,
            {"renewal_date": new_due_date.isoformat()},
        )

        self.assertRedirects(response, reverse("all-borrowed"))
        book_instance.refresh_from_db()
        self.assertEqual(book_instance.due_back, new_due_date)
