from django.shortcuts import get_object_or_404, render

from .models import Author, Book, BookInstance, Genre


def index(request):
    """Display a summary of the library catalogue."""
    context = {
        "book_count": Book.objects.count(),
        "instance_count": BookInstance.objects.count(),
        "available_instance_count": BookInstance.objects.filter(status="a").count(),
        "author_count": Author.objects.count(),
        "genre_count": Genre.objects.count(),
    }
    return render(request, "catalog/index.html", context)


def book_list(request):
    """Display every book and its authors."""
    books = Book.objects.prefetch_related("authors")
    return render(request, "catalog/book_list.html", {"books": books})


def book_detail(request, pk):
    """Display a book and all of its authors."""
    book = get_object_or_404(
        Book.objects.prefetch_related("authors", "genre"), pk=pk
    )
    return render(request, "catalog/book_detail.html", {"book": book})


def author_detail(request, pk):
    """Display an author and all books associated through author.books."""
    author = get_object_or_404(
        Author.objects.prefetch_related("books"), pk=pk
    )
    return render(request, "catalog/author_detail.html", {"author": author})
