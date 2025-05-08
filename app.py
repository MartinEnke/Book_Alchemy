from flask import Flask, render_template, request, redirect, url_for, flash
from data_models import db, Author, Book
import secrets
from datetime import datetime
import requests

# Initialize the Flask app
app = Flask(__name__, static_folder='static')
app.secret_key = secrets.token_hex(16)  # Required for flash messages and cookies

# Configuration for the database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////Users/martinenke/Book_Alchemy/Book_Alchemy/data/library.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # To suppress a warning

# Initialize the db object with the app
db.init_app(app)


@app.route("/")
def home():
    """
    Renders the homepage with a list of books, with optional sorting and searching.

    The books can be filtered by title or author, and the list can be sorted by title or author.
    For each book, its cover image is fetched using the ISBN, and a placeholder is used if the cover is unavailable.
    """
    search_query = request.args.get('search', '')  # Default to an empty string if no search query
    sort_by = request.args.get('sort_by', 'title')  # Default to sorting by title if not provided

    # Search query functionality
    if search_query:
        books = Book.query.join(Author).filter(
            (Book.title.ilike(f'%{search_query}%')) |  # Search title
            (Author.name.ilike(f'%{search_query}%'))  # Search author
        ).all()
    else:
        # Sort books based on user preference
        if sort_by == 'author':
            books = Book.query.join(Author).order_by(Author.name).all()
        else:
            books = Book.query.order_by(Book.title).all()

    # Clean ISBN and fetch cover images for each book
    for book in books:
        book.isbn = ''.join([char for char in book.isbn if char.isdigit()])  # Clean ISBN

        # Query Open Library's search API to get cover URL
        url = f"https://openlibrary.org/search.json?isbn={book.isbn}"
        response = requests.get(url)

        if response.status_code == 200:
            book_data = response.json()
            if book_data['num_found'] > 0:
                first_book = book_data['docs'][0]
                if 'cover_i' in first_book:
                    cover_id = first_book['cover_i']
                    book.cover_url = f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"
                else:
                    book.cover_url = 'https://via.placeholder.com/150x200?text=No+Cover+Available'
            else:
                book.cover_url = 'https://via.placeholder.com/150x200?text=No+Cover+Available'
        else:
            book.cover_url = 'https://via.placeholder.com/150x200?text=No+Cover+Available'

    return render_template('home.html', books=books, sort_by=sort_by)


@app.route('/add_author', methods=['GET', 'POST'])
def add_author():
    """
    Adds a new author to the database.

    The form allows the user to input the author's name, birth date, and optional death date.
    A new Author object is created and saved to the database upon successful form submission.
    """
    if request.method == 'POST':
        # Get form data
        name = request.form['name']
        birth_date_str = request.form['birth_date']
        date_of_death_str = request.form.get('date_of_death')

        # Convert the string dates to Python date objects
        birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d').date()

        # If date_of_death is provided, convert it to a date object; otherwise, set it to None
        date_of_death = None
        if date_of_death_str:
            date_of_death = datetime.strptime(date_of_death_str, '%Y-%m-%d').date()

        # Create a new author object
        new_author = Author(name=name, birth_date=birth_date, date_of_death=date_of_death)

        # Add the new author to the database
        db.session.add(new_author)
        db.session.commit()

        flash('Author added successfully!', 'success')  # Flash success message
        return redirect(url_for('add_author'))

    return render_template('add_author.html')


from flask import Flask, render_template, request, redirect, url_for, flash
from data_models import db, Author, Book
import requests
from datetime import datetime
import os

@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    """
    Adds a new book to the library, auto‑populating from ISBN or title when possible.
    """
    if request.method == 'POST':
        # Raw form values
        isbn_raw           = request.form.get('isbn', '').strip()
        title_input        = request.form.get('title', '').strip()
        pub_year_input     = request.form.get('publication_year', '').strip()
        author_name_input  = request.form.get('author_name', '').strip()

        # Clean up ISBN (allow digits + X)
        isbn = ''.join(ch for ch in isbn_raw if ch.isdigit() or ch.upper() == 'X')

        # Fallback variables we’ll fill
        title   = title_input
        pub_year = pub_year_input
        author_name = author_name_input
        cover_url = None

        # 1) If we have an ISBN and any field is missing, lookup by ISBN:
        if isbn and (not title or not pub_year or not author_name):
            ol_url = (
                f"https://openlibrary.org/api/books?"
                f"bibkeys=ISBN:{isbn}&format=json&jscmd=data"
            )
            resp = requests.get(ol_url, timeout=5)
            if resp.ok:
                data = resp.json().get(f"ISBN:{isbn}", {})
                title       = title       or data.get('title', title)
                pub_date    = data.get('publish_date', '')
                # Attempt to parse a year out of publish_date
                if not pub_year and pub_date:
                    try:
                        pub_year = datetime.strptime(pub_date, '%B %d, %Y').year
                    except Exception:
                        pub_year = pub_date[-4:]
                if not author_name and data.get('authors'):
                    author_name = data['authors'][0].get('name', author_name)
                cover_url = data.get('cover', {}).get('large') \
                            or data.get('cover', {}).get('medium')

        # 2) Else, if no ISBN but a title was given, lookup by title:
        elif not isbn and title:
            search_url = f"https://openlibrary.org/search.json?title={requests.utils.quote(title)}&limit=1"
            resp = requests.get(search_url, timeout=5)
            if resp.ok:
                docs = resp.json().get('docs', [])
                if docs:
                    doc = docs[0]
                    # Extract ISBN if available
                    isbns = doc.get('isbn', [])
                    if isbns:
                        isbn = isbns[0]
                    # Fill missing fields
                    title       = title or doc.get('title', title)
                    if not pub_year and doc.get('first_publish_year'):
                        pub_year = doc['first_publish_year']
                    if not author_name and doc.get('author_name'):
                        author_name = doc['author_name'][0]
                    cover_id = doc.get('cover_i')
                    if cover_id:
                        cover_url = f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"

        # 3) Ensure required fields
        if not (title and pub_year and author_name):
            flash("Please provide at least a Title (or ISBN) and Author.", "error")
            return render_template('add_book.html')

        # 4) Find or create author
        author = Author.query.filter_by(name=author_name).first()
        if not author:
            author = Author(name=author_name)
            db.session.add(author)
            db.session.flush()

        # 5) Create the book record
        new_book = Book(
            isbn=isbn,
            title=title,
            publication_year=pub_year,
            author_id=author.id,
            #cover_url=cover_url or 'https://via.placeholder.com/150x200?text=No+Cover'
        )
        db.session.add(new_book)
        db.session.commit()

        flash('Book added successfully!', 'success')
        return redirect(url_for('add_book'))

    # GET
    return render_template('add_book.html')



@app.route("/book/<int:book_id>/delete", methods=["POST"])
def delete_book(book_id):
    """
    Deletes a specific book from the database.

    If the book's author has no other books in the library, the author is also deleted.
    After the deletion, the user is redirected to the homepage with a success message.
    """
    # Fetch the book by its ID
    book = Book.query.get_or_404(book_id)

    # Get the author of the book
    author = book.author

    # Delete the book from the database
    db.session.delete(book)
    db.session.commit()

    # Check if the author has any other books in the library
    if not Author.query.filter_by(id=author.id).first().books:
        # If the author has no other books, delete the author as well
        db.session.delete(author)
        db.session.commit()

    # Flash a success message and redirect back to the homepage
    flash(f"The book '{book.title}' has been successfully deleted!", 'success')
    return redirect(url_for('home'))


if __name__ == '__main__':
    # Uncomment if you want to automatically create tables on first run
    # with app.app_context():
    #     db.create_all()
    app.run(port=5029, debug=True)
