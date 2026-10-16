from django.shortcuts import render

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
