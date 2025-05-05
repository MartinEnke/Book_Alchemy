from flask import Flask, render_template, request, redirect, url_for, flash
from data_models import db, Author, Book
import secrets
from datetime import datetime
import requests


# Initialize the Flask app
app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # Required for flash messages and cookies

# Configuration for the database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////Users/martinenke/Book_Alchemy/Book_Alchemy/data/library.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # To suppress a warning

# Initialize the db object with the app
db.init_app(app)


@app.route("/")
def home():
    sort_by = request.args.get('sort_by', 'title')  # Default to 'title' if no parameter is provided

    if sort_by == 'author':
        # Sort by author name (ascending order)
        books = Book.query.join(Author).order_by(Author.name).all()
    else:
        # Sort by title (ascending order)
        books = Book.query.order_by(Book.title).all()

    for book in books:
        # Clean ISBN to remove non-numeric characters
        book.isbn = ''.join([char for char in book.isbn if char.isdigit()])  # Clean ISBN

        # Query Open Library's search API to get cover URL (same as before)
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

# Route to add a book
@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
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


if __name__ == '__main__':
#     # Create all tables in the database
#     with app.app_context():
#         print("Creating tables...")  # Debugging line to confirm the code is running
#         db.create_all()
#         print("Tables created!")  # Confirmation message
     app.run(port=5029, debug=True)