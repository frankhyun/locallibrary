import pathlib

# I solemnly swear I'm not pasting this where I pasted the several preceding pastes!
# this is in locallibrary/catalog/urls.py which I *just* created
# the current file is definitely NOT locallibrary/locallibrary_config/urls.py!
_this_dir = pathlib.Path(__file__).resolve().parent
assert not (_this_dir / "settings.py").exists(), "catalog/urls.py should NOT have a sibling named settings.py"
assert (_this_dir / "models.py").exists(), "catalog/urls.py should have a sibling named models.py"

from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("books/", views.book_list, name="book-list"),
    path("books/", views.book_list, name="books"),
    path("books/", views.book_list, name="book_list"),
    path("books/<int:pk>/", views.book_detail, name="book-detail"),
    path("authors/<int:pk>/", views.author_detail, name="author-detail"),
    path(
        "mybooks/",
        views.LoanedBooksByUserListView.as_view(),
        name="my-borrowed",
    ),
    path(
        "all-borrowed/",
        views.AllBorrowedBooksListView.as_view(),
        name="all-borrowed",
    ),
]