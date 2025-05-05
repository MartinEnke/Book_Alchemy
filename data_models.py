from flask_sqlalchemy import SQLAlchemy

# Initialize the db object
db = SQLAlchemy()


class Author(db.Model):
    __tablename__ = 'authors'  # Optional: specify the table name explicitly

    # Define columns
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    birth_date = db.Column(db.Date, nullable=False)
    date_of_death = db.Column(db.Date, nullable=True)

    # String representation for debugging
    def __repr__(self):
        return f'<Author {self.name}>'

    def __str__(self):
        return f'Author: {self.name}, Born: {self.birth_date}, Died: {self.date_of_death if self.date_of_death else "Still alive"}'


class Book(db.Model):
    __tablename__ = 'books'  # Optional: specify the table name explicitly

    # Define columns
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    isbn = db.Column(db.String(13), unique=True, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    publication_year = db.Column(db.Integer, nullable=False)

    # Foreign Key linking to the Author model
    author_id = db.Column(db.Integer, db.ForeignKey('authors.id'), nullable=False)

    # Relationship to Author (one-to-many relationship)
    author = db.relationship('Author', backref=db.backref('books', lazy=True))

    # String representation for debugging
    def __repr__(self):
        return f'<Book {self.title} by {self.author.name}>'

    def __str__(self):
        return f'Book: {self.title}, ISBN: {self.isbn}, Published: {self.publication_year}, Author: {self.author.name}'
