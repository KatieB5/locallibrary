from django.shortcuts import render
from .models import Book, Author, BookInstance, Genre

# Create your views here.

def home(request):

    # Count the number of books and the number of instances of books

    num_of_books = Book.objects.all().count()
    num_book_instances = BookInstance.objects.all().count()

    # Count number of books available for lending
    num_available_instances = BookInstance.objects.filter(status__exact='a').count()

    # Count the number of authors
    num_of_authors = Author.objects.all().count()

    context = {
        'num_of_books': num_of_books,
        'num_book_instances': num_book_instances,
        'num_available_instances': num_available_instances,
        'num_of_authors': num_of_authors,
    }

    return render(request, 'home.html', context=context)
