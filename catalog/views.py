import datetime

from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.views import generic

from .forms import AuthorForm, BookForm, RenewBookForm
from .models import Author, Book, BookInstance, Genre


def index(request):
    """Display a summary of the library catalogue."""
    context = {
        "book_count": Book.objects.count(),
        "instance_count": BookInstance.objects.count(),
        "available_instance_count": BookInstance.objects.filter(status="a").count(),
        "author_count": Author.objects.count(),
        "genre_count": Genre.objects.count(),
        "num_visits": request.session.get("num_visits", 0) + 1,
    }
    request.session["num_visits"] = context["num_visits"]
    return render(request, "catalog/index.html", context)


def book_list(request):
    """Display every book and its authors."""
    books = Book.objects.prefetch_related("authors")
    return render(
        request,
        "catalog/book_list.html",
        {"books": books, "book_list": books},
    )


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


class AuthorListView(generic.ListView):
    model = Author
    template_name = "catalog/author_list.html"


class LoanedBooksByUserListView(LoginRequiredMixin, generic.ListView):
    """List books currently on loan to the signed-in user."""
    model = BookInstance
    template_name = "catalog/bookinstance_list_borrowed_user.html"
    paginate_by = 10

    def get_queryset(self):
        return (
            BookInstance.objects.filter(
                borrower=self.request.user, status="o"
            )
            .select_related("book")
            .order_by("due_back")
        )


class AllBorrowedBooksListView(PermissionRequiredMixin, generic.ListView):
    """List every book currently on loan for authorized library staff."""
    model = BookInstance
    template_name = "catalog/bookinstance_list_borrowed_all.html"
    permission_required = "catalog.can_mark_returned"
    paginate_by = 10

    def get_queryset(self):
        return (
            BookInstance.objects.filter(status="o")
            .select_related("book", "borrower")
            .order_by("due_back")
        )


class EditorCreateView(LoginRequiredMixin, PermissionRequiredMixin, generic.CreateView):
    raise_exception = True


class EditorUpdateView(LoginRequiredMixin, PermissionRequiredMixin, generic.UpdateView):
    raise_exception = True


class EditorDeleteView(LoginRequiredMixin, PermissionRequiredMixin, generic.DeleteView):
    raise_exception = True


class AuthorCreateView(EditorCreateView):
    model = Author
    form_class = AuthorForm
    permission_required = "catalog.add_author"
    template_name = "catalog/author_form.html"


class AuthorUpdateView(EditorUpdateView):
    model = Author
    form_class = AuthorForm
    permission_required = "catalog.change_author"
    template_name = "catalog/author_form.html"


class AuthorDeleteView(EditorDeleteView):
    model = Author
    permission_required = "catalog.delete_author"
    template_name = "catalog/author_confirm_delete.html"
    success_url = reverse_lazy("authors")


class BookCreateView(EditorCreateView):
    model = Book
    form_class = BookForm
    permission_required = "catalog.add_book"
    template_name = "catalog/book_form.html"


class BookUpdateView(EditorUpdateView):
    model = Book
    form_class = BookForm
    permission_required = "catalog.change_book"
    template_name = "catalog/book_form.html"


class BookDeleteView(EditorDeleteView):
    model = Book
    permission_required = "catalog.delete_book"
    template_name = "catalog/book_confirm_delete.html"
    success_url = reverse_lazy("book-list")


@login_required
@permission_required("catalog.can_mark_returned", raise_exception=True)
def renew_book_librarian(request, pk):
    """Renew a book loan for an authorized librarian."""
    book_instance = get_object_or_404(BookInstance, pk=pk)

    if request.method == "POST":
        form = RenewBookForm(request.POST)
        if form.is_valid():
            book_instance.due_back = form.cleaned_data["renewal_date"]
            book_instance.save(update_fields=["due_back"])
            return HttpResponseRedirect(reverse("all-borrowed"))
    else:
        proposed_renewal_date = (
            datetime.date.today() + datetime.timedelta(weeks=3)
        )
        form = RenewBookForm(initial={"renewal_date": proposed_renewal_date})

    return render(
        request,
        "catalog/book_renew_librarian.html",
        {"form": form, "book_instance": book_instance},
    )
