# Book Alchemy

Welcome to the **Book Library**! 
This is a Flask-based web application designed to help users manage a library of books.

![Banner](banner2.png)

## Features

- **Search** for books by title or author.
- **Sort** books by title or author.
- **Add new authors** and books to the library.
- **Delete books** from the library, with optional author deletion if they have no other books.
- **Automatic cover fetching** for books using ISBN from Open Library.
- **Responsive design** with a background image, with a fallback to a placeholder if the cover image is unavailable.

## Technologies Used

- **Flask**: Web framework used for building the app.
- **SQLAlchemy**: ORM used for database interaction.
- **SQLite**: Database used to store book and author data.
- **HTML/CSS**: Frontend technologies used to build the web interface.
- **Open Library API**: Used to fetch book cover images based on ISBN.
- **Bootstrap**: Used for responsive layout and styling.

## Getting Started

### Prerequisites

Ensure you have the following installed on your machine:

- Python 3.6+
- pip (Python package installer)

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/book-alchemy.git
   cd book-alchemy
   
2. Create a virtual environment:

python3 -m venv venv
Activate the virtual environment:

On Windows:
venv\Scripts\activate

On macOS/Linux:
source venv/bin/activate

3. Install the required dependencies:

pip install -r requirements.txt
If you’re running the app for the first time, you can initialize the database and create the tables by running:
python app.py


Running the App
After setting up the environment, you can start the Flask development server:

python app.py
Visit http://localhost:5029 in your browser to use the app.

Folder Structure
```
Book_Alchemy/
├── static/
│   ├── background-image.png  # Background image for the page
│   └── style.css             # Custom CSS for styling the pages
├── templates/
│   ├── home.html             # Template for the homepage
│   ├── add_author.html       # Template for adding a new author
│   └── add_book.html         # Template for adding a new book
├── data_models.py            # Contains SQLAlchemy database models
├── app.py                    # Main Flask app logic
├── requirements.txt          # Required Python packages
└── README.md                 # Project documentation
```


License
This project is open source and available under the MIT License.

Acknowledgements:
Open Library API