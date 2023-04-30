from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy  # , or_
from flask_cors import CORS
import random

from models import setup_db, Book

BOOKS_PER_SHELF = 8


def paginate_books(request, books):
        page = request.args.get('page', 1, type=int)
        start = (page - 1) * BOOKS_PER_SHELF
        end = start + BOOKS_PER_SHELF

        books = [book.format() for book in books]
        return books[start:end]


def create_app(db_URI="", test_config=None):
    # create and configure the app
    app = Flask(__name__)
    app.app_context().push()
    if db_URI:
        setup_db(app, db_URI)
    else:
        setup_db(app)
    CORS(app)

    # CORS Headers
    @app.after_request
    def after_request(response):
        response.headers.add(
            "Access-Control-Allow-Headers", "Content-Type,Authorization,true"
        )
        response.headers.add(
            "Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS"
        )
        return response

    @app.route("/books")
    def retrieve_books():
        selection = Book.query.order_by(Book.id).all()
        current_books = paginate_books(request, selection)

        if len(current_books) == 0:
            abort(404)

        return jsonify(
            {
                "success": True,
                "books": current_books,
                "total_books": len(Book.query.all()),
            }
        )

    @app.route("/books/<int:book_id>", methods=["PATCH"])
    def update_book(book_id):

        body = request.get_json()

        try:
            book = Book.query.filter(Book.id == book_id).one_or_none()
            if book is None:
                abort(404)

            if "rating" in body:
                book.rating = int(body.get("rating"))
            if "title" in body:
                book.title = body.get("title")
            if "author" in body:
                book.author = body.get("author")

            book.update()

            return jsonify(
                {
                    "success": True,
                }
            )

        except:
            abort(400)

    @app.route("/books/<int:book_id>", methods=["DELETE"])
    def delete_book(book_id):
        try:
            book = Book.query.filter(Book.id == book_id).one_or_none()

            if book is None:
                abort(404)

            book.delete()
            selection = Book.query.order_by(Book.id).all()
            current_books = paginate_books(request, selection)

            return jsonify(
                {
                    "success": True,
                    "deleted": book_id,
                    "books": current_books,
                    "total_books": len(Book.query.all()),
                }
            )

        except:
            abort(422)


    @app.route("/books", methods=["POST"])
    def create_book():
        body = request.get_json()

        new_title = body.get("title", None)
        new_author = body.get("author", None)
        new_rating = body.get("rating", None)
        search = body.get("search", None)

        try:
            if search:
                books = Book.query.order_by(Book.id).filter(
                    Book.title.ilike("%{}%".format(search))
                )
                current_books = paginate_books(request, books)

                return jsonify({
                    'success': True,
                    'books': current_books,
                    'total_books': len(books.all()),
                })
            else:
                book = Book(title=new_title, author=new_author, rating=new_rating)
                book.insert()

                selection = Book.query.order_by(Book.id).all()
                current_books = paginate_books(request, selection)

                return jsonify(
                    {
                        "success": True,
                        "created": book.id,
                        "books": current_books,
                        "total_books": len(Book.query.all()),
                    }
                )
        except:
            abort(422)


    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": 404,
            "message": "resource not found"
        }), 404
    
    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({
            "success": False,
            "error": 422,
            "message": "unprocessable"
        }), 422

    @app.errorhandler(400)
    def invalid_request(error):
        return jsonify({
            "success": False,
            "error": 400,
            "message": "invalid request"
        }), 400

    @app.errorhandler(405)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": 405,
            "message": "method not allowed",
        }), 405

    return app


# @TODO: Create a new endpoint or update a previous endpoint to handle searching for a team in the title
#        the body argument is called 'search' coming from the frontend.
#        If you use a different argument, make sure to update it in the frontend code.
#        The endpoint will need to return success value, a list of books for the search and the number of books with the search term
#        Response body keys: 'success', 'books' and 'total_books'