import datetime
import uuid
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType

from catalog.models import Author, BookInstance, Book, Genre, Language
from django.contrib.auth.models import Permission

User = get_user_model()


class AuthorListViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        number_of_authors = 13

        for author_id in range(number_of_authors):
            Author.objects.create(
                first_name=f"Dominique {author_id}",
                last_name=f"Surname {author_id}",
            )

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get("/catalog/authors/")
        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        response = self.client.get(reverse("authors"))
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse("authors"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "catalog/author_list.html")

    def test_pagination_is_ten(self):
        response = self.client.get(reverse("authors"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue("is_paginated" in response.context)
        self.assertTrue(response.context["is_paginated"])
        self.assertEqual(len(response.context["author_list"]), 10)

    def test_lists_all_authors(self):
        response = self.client.get(reverse("authors") + "?page=2")
        self.assertEqual(response.status_code, 200)
        self.assertTrue("is_paginated" in response.context)
        self.assertTrue(response.context["is_paginated"])
        self.assertEqual(len(response.context["author_list"]), 3)


class LoanedBookInstancesByUserListViewTest(TestCase):
    def setUp(self):
        test_user1 = User.objects.create_user(
            username="testuser1", password="1X<ISRUkw+tuK"
        )
        test_user2 = User.objects.create_user(
            username="testuser2", password="2HJ1vRV0Z&3iD"
        )

        test_user1.save()
        test_user2.save()

        test_author = Author.objects.create(first_name="John", last_name="Smith")
        test_language = Language.objects.create(name="English")
        test_book = Book.objects.create(
            title="Book Title",
            summary="My book summary",
            isbn="ABCDEFG",
            author=test_author,
            language=test_language,
        )

        genre_objects_for_book = Genre.objects.all()
        test_book.genre.set(genre_objects_for_book)
        test_book.save()

        number_of_book_copies = 30
        for book_copy in range(number_of_book_copies):
            return_date = timezone.localtime() + datetime.timedelta(days=book_copy % 5)
            the_borrower = test_user1 if book_copy % 2 else test_user2
            status = "m"
            BookInstance.objects.create(
                book=test_book,
                imprint="Unlikely Imprint, 2016",
                due_back=return_date,
                borrower=the_borrower,
                status=status,
            )

    def test_redirect_if_not_logged_in(self):
        response = self.client.get(reverse("my-borrowed"))
        self.assertRedirects(response, "/accounts/login/?next=/catalog/mybooks/")

    def test_logged_in_uses_correct_template(self):
        self.client.login(username="testuser1", password="1X<ISRUkw+tuK")
        response = self.client.get(reverse("my-borrowed"))

        self.assertEqual(str(response.context["user"]), "testuser1")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "catalog/bookinstance_list_borrowed_user.html"
        )

    def test_only_borrowed_books_in_list(self):
        self.client.login(username="testuser1", password="1X<ISRUkw+tuK")
        response = self.client.get(reverse("my-borrowed"))

        self.assertEqual(str(response.context["user"]), "testuser1")
        self.assertEqual(response.status_code, 200)

        self.assertTrue("bookinstance_list" in response.context)
        self.assertEqual(len(response.context["bookinstance_list"]), 0)

        books = BookInstance.objects.all()[:10]

        for book in books:
            book.status = "o"
            book.save()

        response = self.client.get(reverse("my-borrowed"))
        self.assertEqual(str(response.context["user"]), "testuser1")
        self.assertEqual(response.status_code, 200)

        self.assertTrue("bookinstance_list" in response.context)

        for bookitem in response.context["bookinstance_list"]:
            self.assertEqual(response.context["user"], bookitem.borrower)
            self.assertEqual(bookitem.status, "o")

    def test_pages_ordered_by_due_date(self):
        for book in BookInstance.objects.all():
            book.status = "o"
            book.save()

        self.client.login(username="testuser1", password="1X<ISRUkw+tuK")
        response = self.client.get(reverse("my-borrowed"))

        self.assertEqual(str(response.context["user"]), "testuser1")
        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context["bookinstance_list"]), 10)

        last_date = 0
        for book in response.context["bookinstance_list"]:
            if last_date == 0:
                last_date = book.due_back
            else:
                self.assertTrue(last_date <= book.due_back)
                last_date = book.due_back


class RenewBookInstancesViewTest(TestCase):
    def setUp(self):
        # Create a user
        test_user1 = User.objects.create_user(
            username="testuser1", password="1X<ISRUkw+tuK"
        )
        test_user2 = User.objects.create_user(
            username="testuser2", password="2HJ1vRV0Z&3iD"
        )

        test_user1.save()
        test_user2.save()

        permission = Permission.objects.get(name="Set book as returned")
        test_user2.user_permissions.add(permission)
        test_user2.save()

        test_author = Author.objects.create(first_name="John", last_name="Smith")
        test_language = Language.objects.create(name="English")
        test_book = Book.objects.create(
            title="Book Title",
            summary="My book summary",
            isbn="ABCDEFG",
            author=test_author,
            language=test_language,
        )

        genre_objects_for_book = Genre.objects.all()
        test_book.genre.set(genre_objects_for_book)
        test_book.save()

        return_date = datetime.date.today() + datetime.timedelta(days=5)
        self.test_bookinstance1 = BookInstance.objects.create(
            book=test_book,
            imprint="Unlikely Imprint, 2016",
            due_back=return_date,
            borrower=test_user1,
            status="o",
        )

        return_date = datetime.date.today() + datetime.timedelta(days=5)
        self.test_bookinstance2 = BookInstance.objects.create(
            book=test_book,
            imprint="Unlikely Imprint, 2016",
            due_back=return_date,
            borrower=test_user2,
            status="o",
        )

    def test_redirect_if_not_logged_in(self):
        response = self.client.get(
            reverse("renew-book-librarian", kwargs={"pk": self.test_bookinstance1.pk})
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/accounts/login/"))

    def test_forbidden_if_logged_in_but_not_correct_permission(self):
        self.client.login(username="testuser1", password="1X<ISRUkw+tuK")
        response = self.client.get(
            reverse("renew-book-librarian", kwargs={"pk": self.test_bookinstance1.pk})
        )
        self.assertEqual(response.status_code, 403)

    def test_logged_in_with_permission_borrowed_book(self):
        self.client.login(username="testuser2", password="2HJ1vRV0Z&3iD")
        response = self.client.get(
            reverse("renew-book-librarian", kwargs={"pk": self.test_bookinstance2.pk})
        )

        self.assertEqual(response.status_code, 200)

    def test_logged_in_with_permission_another_users_borrowed_book(self):
        self.client.login(username="testuser2", password="2HJ1vRV0Z&3iD")
        response = self.client.get(
            reverse("renew-book-librarian", kwargs={"pk": self.test_bookinstance1.pk})
        )

        self.assertEqual(response.status_code, 200)

    def test_HTTP404_for_invalid_book_if_logged_in(self):
        test_uid = uuid.uuid4()
        self.client.login(username="testuser2", password="2HJ1vRV0Z&3iD")
        response = self.client.get(
            reverse("renew-book-librarian", kwargs={"pk": test_uid})
        )
        self.assertEqual(response.status_code, 404)

    def test_uses_correct_template(self):
        self.client.login(username="testuser2", password="2HJ1vRV0Z&3iD")
        response = self.client.get(
            reverse("renew-book-librarian", kwargs={"pk": self.test_bookinstance1.pk})
        )
        self.assertEqual(response.status_code, 200)

        self.assertTemplateUsed(response, "catalog/book_renew_librarian.html")

    def test_form_renewal_date_initially_has_date_three_weeks_in_future(self):
        self.client.login(username="testuser2", password="2HJ1vRV0Z&3iD")
        response = self.client.get(
            reverse("renew-book-librarian", kwargs={"pk": self.test_bookinstance1.pk})
        )
        self.assertEqual(response.status_code, 200)

        date_3_weeks_in_future = datetime.date.today() + datetime.timedelta(weeks=3)
        self.assertEqual(
            response.context["form"].initial["renewal_date"], date_3_weeks_in_future
        )

    def test_redirects_to_all_borrowed_book_list_on_success(self):
        self.client.login(username="testuser2", password="2HJ1vRV0Z&3iD")
        valid_date_in_future = datetime.date.today() + datetime.timedelta(weeks=2)
        response = self.client.post(
            reverse(
                "renew-book-librarian",
                kwargs={
                    "pk": self.test_bookinstance1.pk,
                },
            ),
            {"renewal_date": valid_date_in_future},
        )
        self.assertRedirects(response, reverse("all-borrowed"))

    def test_form_invalid_renewal_date_past(self):
        self.client.login(username="testuser2", password="2HJ1vRV0Z&3iD")
        date_in_past = datetime.date.today() - datetime.timedelta(weeks=1)
        response = self.client.post(
            reverse("renew-book-librarian", kwargs={"pk": self.test_bookinstance1.pk}),
            {"renewal_date": date_in_past},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response.context["form"],
            "renewal_date",
            "Invalid date - renewal date provided is in the past",
        )

    def test_form_invalid_renewal_date_future(self):
        self.client.login(username="testuser2", password="2HJ1vRV0Z&3iD")
        invalid_date_in_future = datetime.date.today() + datetime.timedelta(weeks=5)
        response = self.client.post(
            reverse("renew-book-librarian", kwargs={"pk": self.test_bookinstance1.pk}),
            {"renewal_date": invalid_date_in_future},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response.context["form"],
            "renewal_date",
            "Invalid date - renewal date provided is more than 4 weeks ahead",
        )


class AuthorCreateViewTest(TestCase):
    def setUp(self):
        test_user = User.objects.create_user(
            username="test_user", password="some_password"
        )

        test_user2 = User.objects.create_user(
            username="testuser2", password="2HJ1vRV0Z&3iD"
        )

        test_user2.save()

        content_typeAuthor = ContentType.objects.get_for_model(Author)
        permAddAuthor = Permission.objects.get(
            codename="add_author",
            content_type=content_typeAuthor,
        )

        test_user.user_permissions.add(permAddAuthor)
        test_user.save()

    def test_redirect_if_not_logged_in(self):
        response = self.client.get(reverse("author-create"))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/accounts/login/"))

    def test_forbidden_if_logged_in_but_not_correct_permission(self):
        self.client.login(username="testuser2", password="2HJ1vRV0Z&3iD")
        response = self.client.get(reverse("author-create"))
        self.assertEqual(response.status_code, 403)

    def test_logged_in_with_permission(self):
        self.client.login(username="test_user", password="some_password")
        response = self.client.get(reverse("author-create"))

        self.assertEqual(response.status_code, 200)

    def test_uses_correct_template(self):
        self.client.login(username="test_user", password="some_password")
        response = self.client.get(reverse("author-create"))
        self.assertEqual(response.status_code, 200)

        self.assertTemplateUsed(response, "catalog/author_form.html")

    def test_form_renewal_has_initial_death_date_(self):
        self.client.login(username="test_user", password="some_password")
        response = self.client.get(reverse("author-create"))
        self.assertEqual(response.status_code, 200)

        initial_death_date = '11/11/2023'
        self.assertEqual(
            response.context["form"].initial["date_of_death"], initial_death_date
        )
