from django.shortcuts import render
from django.views import generic
from .models import Book, Author, BookInstance, Genre
from django.shortcuts import get_object_or_404

# Create your views here.

def home(request):

    # Count the number of books and the number of instances of books

    num_of_books = Book.objects.all().count()
    num_book_instances = BookInstance.objects.all().count()

    # Count number of books available for lending
    num_available_instances = BookInstance.objects.filter(status__exact='a').count()

    # Count the number of authors
    num_of_authors = Author.objects.all().count()

    # Count number of genres
    num_of_genres = Genre.objects.all().count()

    # Count number of fiction books
    num_fiction_books = Book.objects.filter(genre__name__iexact='Fiction').count()

    # Count number of nonfiction books
    num_nonfiction_books = Book.objects.filter(genre__name__iexact='Non-fiction').count()


    context = {
        'num_of_books': num_of_books,
        'num_book_instances': num_book_instances,
        'num_available_instances': num_available_instances,
        'num_of_authors': num_of_authors,
        'num_of_genres': num_of_genres,
        'num_fiction_books': num_fiction_books,
        'num_nonfiction_books': num_nonfiction_books,
    }

    return render(request, 'home.html', context=context)

class BookListView(generic.ListView):
    model = Book

class BookDetailView(generic.DetailView):
    model = Book

