from django.shortcuts import render
from django.views import generic
from .models import Book, Author, BookInstance, Genre
from django.contrib.auth.mixins import LoginRequiredMixin

def home(request):

    num_of_books = Book.objects.all().count()
    num_book_instances = BookInstance.objects.all().count()

    num_available_instances = BookInstance.objects.filter(status__exact='a').count()

    num_of_authors = Author.objects.all().count()

    num_of_genres = Genre.objects.all().count()

    num_fiction_books = Book.objects.filter(genre__name__iexact='Fiction').count()

    num_nonfiction_books = Book.objects.filter(genre__name__iexact='Non-fiction').count()

    num_visits = request.session.get('num_visits', 0)
    num_visits += 1
    request.session['num_visits'] = num_visits


    context = {
        'num_of_books': num_of_books,
        'num_book_instances': num_book_instances,
        'num_available_instances': num_available_instances,
        'num_of_authors': num_of_authors,
        'num_of_genres': num_of_genres,
        'num_fiction_books': num_fiction_books,
        'num_nonfiction_books': num_nonfiction_books,
        'num_visits': num_visits,
    }

    return render(request, 'home.html', context=context)

class BookListView(generic.ListView):
    model = Book
    paginate_by = 10

class BookDetailView(generic.DetailView):
    model = Book

class AuthorListView(generic.ListView):
    model = Author
    paginate_by = 10

class AuthorDetailView(generic.DetailView):
    model = Author

class LoanedBooksByUserListView(LoginRequiredMixin,generic.ListView):
    """Generic class-based view listing books on loan to current user."""
    model = BookInstance
    template_name = 'catalog/bookinstance_list_borrowed_user.html'
    paginate_by = 10

    def get_queryset(self):
        return (
            BookInstance.objects.filter(borrower=self.request.user)
            .filter(status__exact='o')
            .order_by('due_back')
        )