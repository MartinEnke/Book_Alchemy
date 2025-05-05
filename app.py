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


@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    """
    Adds a new book to the library, associated with an author.

    The form allows the user to input the book's ISBN, title, publication year, and select an author.
    A new Book object is created and saved to the database upon successful form submission.
    """
    authors = Author.query.all()  # Get all authors from the database
    if request.method == 'POST':
        # Get form data
        isbn = request.form['isbn']
        title = request.form['title']
        publication_year = request.form['publication_year']
        author_id = request.form['author_id']  # Author selected from dropdown

        # Create a new book object
        new_book = Book(isbn=isbn, title=title, publication_year=publication_year, author_id=author_id)

        # Add the new book to the database
        db.session.add(new_book)
        db.session.commit()

        flash('Book added successfully!', 'success')
        return redirect(url_for('add_book'))

    return render_template('add_book.html', authors=authors)


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
