"""
Trivia API Flask Application.

Provides RESTful endpoints to manage trivia questions and categories,
and to play a trivia quiz game.
"""

import os
import random

from flask import Flask, abort, jsonify, request
from flask_cors import CORS

from models import Category, Question, db, db_drop_and_create_all, setup_db

# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

QUESTIONS_PER_PAGE = 10


def create_app(test_config=None):
    """Create and configure the Flask application."""
    app = Flask(__name__)

    if test_config is None:
        setup_db(app)
    else:
        setup_db(app, database_url=test_config.get("SQLALCHEMY_DATABASE_URI"))

    # Allow cross-origin requests from the frontend (localhost:3000)
    CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})

    @app.after_request
    def after_request(response):
        """Attach CORS headers to every response."""
        response.headers.add(
            "Access-Control-Allow-Headers", "Content-Type,Authorization,true"
        )
        response.headers.add(
            "Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS"
        )
        return response

    # -----------------------------------------------------------------------
    # Helper
    # -----------------------------------------------------------------------

    def paginate_questions(request, selection):
        """Return a page-sized slice of formatted questions."""
        page = request.args.get("page", 1, type=int)
        start = (page - 1) * QUESTIONS_PER_PAGE
        end = start + QUESTIONS_PER_PAGE
        questions = [q.format() for q in selection]
        return questions[start:end]

    # -----------------------------------------------------------------------
    # GET /categories
    # -----------------------------------------------------------------------

    @app.route("/categories", methods=["GET"])
    def get_categories():
        """
        Retrieve all available trivia categories.

        Returns:
            JSON with a dict of categories keyed by id and a success flag.
        """
        categories = Category.query.order_by(Category.id).all()

        if not categories:
            abort(404)

        return jsonify(
            {
                "success": True,
                "categories": {cat.id: cat.type for cat in categories},
                "total_categories": len(categories),
            }
        )

    # -----------------------------------------------------------------------
    # GET /questions
    # -----------------------------------------------------------------------

    @app.route("/questions", methods=["GET"])
    def get_questions():
        """
        Retrieve a paginated list of all trivia questions.

        Query Parameters:
            page (int): Page number (default 1, 10 questions per page).

        Returns:
            JSON with paginated questions, total count, categories, and a
            success flag. Returns 404 if the requested page is out of range.
        """
        selection = Question.query.order_by(Question.id).all()
        current_questions = paginate_questions(request, selection)

        if not current_questions:
            abort(404)

        categories = Category.query.order_by(Category.id).all()

        return jsonify(
            {
                "success": True,
                "questions": current_questions,
                "total_questions": len(selection),
                "categories": {cat.id: cat.type for cat in categories},
                "current_category": None,
            }
        )

    # -----------------------------------------------------------------------
    # DELETE /questions/<id>
    # -----------------------------------------------------------------------

    @app.route("/questions/<int:question_id>", methods=["DELETE"])
    def delete_question(question_id):
        """
        Delete a specific trivia question by its ID.

        Path Parameters:
            question_id (int): The ID of the question to delete.

        Returns:
            JSON with the deleted question's id and a success flag.
            Returns 404 if the question does not exist.
        """
        question = db.session.get(Question, question_id)

        if question is None:
            abort(404)

        question.delete()

        return jsonify(
            {
                "success": True,
                "deleted": question_id,
            }
        )

    # -----------------------------------------------------------------------
    # POST /questions  (create OR search)
    # -----------------------------------------------------------------------

    @app.route("/questions", methods=["POST"])
    def create_or_search_question():
        """
        Create a new trivia question OR search questions by a search term.

        If the request body contains 'searchTerm', a case-insensitive search
        is performed and matching questions are returned (paginated).

        Otherwise, a new question is created from the provided fields.

        Request Body (create):
            question    (str):  Question text.
            answer      (str):  Answer text.
            category    (int):  Category ID.
            difficulty  (int):  Difficulty level (1-5).
            rating      (int):  Rating (1-5, optional, default 1).

        Request Body (search):
            searchTerm  (str):  Substring to search for in question text.

        Returns:
            JSON with created question id (create) or matching questions list
            (search), plus a success flag.
        """
        body = request.get_json(force=True, silent=True)

        if body is None:
            abort(400)

        search_term = body.get("searchTerm", None)

        if search_term is not None:
            # --- Search branch ---
            selection = Question.query.filter(
                Question.question.ilike(f"%{search_term}%")
            ).order_by(Question.id).all()

            current_questions = paginate_questions(request, selection)

            return jsonify(
                {
                    "success": True,
                    "questions": current_questions,
                    "total_questions": len(selection),
                    "current_category": None,
                }
            )

        # --- Create branch ---
        question_text = body.get("question", None)
        answer = body.get("answer", None)
        category = body.get("category", None)
        difficulty = body.get("difficulty", None)
        rating_raw = body.get("rating")
        rating = 1 if rating_raw is None else rating_raw

        # Validate required fields are present and non-empty
        if not all([question_text, answer, category is not None, difficulty is not None]):
            abort(422)

        # Safely convert to int; reject non-numeric values with 422
        try:
            difficulty = int(difficulty)
            rating = int(rating)
            category = int(category)
        except (TypeError, ValueError):
            abort(422)

        # Validate numeric ranges
        if not (1 <= difficulty <= 5):
            abort(422)
        if not (1 <= rating <= 5):
            abort(422)

        # Validate category exists
        if db.session.get(Category, category) is None:
            abort(422)

        new_question = Question(
            question=question_text,
            answer=answer,
            category=category,
            difficulty=difficulty,
            rating=rating,
        )

        try:
            new_question.insert()
        except Exception:
            db.session.rollback()
            abort(422)

        return jsonify(
            {
                "success": True,
                "created": new_question.id,
            }
        ), 201

    # -----------------------------------------------------------------------
    # GET /categories/<id>/questions  and  POST /categories/<id>/questions
    # -----------------------------------------------------------------------

    def _questions_for_category(category_id):
        """
        Shared logic: retrieve paginated questions for *category_id*.

        Returns a Flask Response object. Aborts with 404 if the category
        does not exist or no questions fall on the requested page.
        """
        category = db.session.get(Category, category_id)

        if category is None:
            abort(404)

        selection = (
            Question.query.filter(Question.category == category_id)
            .order_by(Question.id)
            .all()
        )
        current_questions = paginate_questions(request, selection)

        if not current_questions:
            abort(404)

        return jsonify(
            {
                "success": True,
                "questions": current_questions,
                "total_questions": len(selection),
                "current_category": category.type,
            }
        )

    @app.route("/categories/<int:category_id>/questions", methods=["GET"])
    def get_questions_by_category(category_id):
        """
        Retrieve all questions for a given category (paginated) via GET.

        Path Parameters:
            category_id (int): The ID of the category.

        Query Parameters:
            page (int): Page number (default 1).

        Returns:
            JSON with questions, total count, current category, and success
            flag. Returns 404 if the category does not exist or has no
            questions on the requested page.
        """
        return _questions_for_category(category_id)

    @app.route("/categories/<int:category_id>/questions", methods=["POST"])
    def post_questions_by_category(category_id):
        """
        Retrieve all questions for a given category (paginated) via POST.

        Identical behaviour to GET /categories/<id>/questions.  Provided so
        that clients may use a POST request when preferred or required.

        Path Parameters:
            category_id (int): The ID of the category.

        Query Parameters:
            page (int): Page number (default 1).

        Returns:
            JSON with questions, total count, current category, and success
            flag. Returns 404 if the category does not exist or has no
            questions on the requested page.
        """
        return _questions_for_category(category_id)

    # -----------------------------------------------------------------------
    # POST /quizzes
    # -----------------------------------------------------------------------

    @app.route("/quizzes", methods=["POST"])
    def play_quiz():
        """
        Return a random question for the quiz game.

        Selects a question that has not already been shown in the current
        game session. Optionally filtered by category.

        Request Body:
            previous_questions (list[int]):  IDs of already-shown questions.
            quiz_category      (dict):       Category object with 'id' key.
                                             Use id=0 for all categories.

        Returns:
            JSON with a random question (or None if exhausted) and a success
            flag. Returns 400 if the request body is malformed.
        """
        body = request.get_json(force=True, silent=True)

        if body is None:
            abort(400)

        previous_questions = body.get("previous_questions", [])
        quiz_category = body.get("quiz_category", None)

        if quiz_category is None:
            abort(400)

        category_id = quiz_category.get("id", 0)

        # Build query: all categories (id==0) or a specific one
        if category_id == 0:
            available = Question.query.filter(
                Question.id.notin_(previous_questions)
            ).all()
        else:
            available = Question.query.filter(
                Question.category == category_id,
                Question.id.notin_(previous_questions),
            ).all()

        if not available:
            return jsonify({"success": True, "question": None})

        next_question = random.choice(available)

        return jsonify(
            {
                "success": True,
                "question": next_question.format(),
            }
        )

    # -----------------------------------------------------------------------
    # Error handlers
    # -----------------------------------------------------------------------

    @app.errorhandler(400)
    def bad_request(error):
        """Handle 400 Bad Request errors."""
        return jsonify(
            {"success": False, "error": 400, "message": "bad request"}
        ), 400

    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 Not Found errors."""
        return jsonify(
            {"success": False, "error": 404, "message": "resource not found"}
        ), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        """Handle 405 Method Not Allowed errors."""
        return jsonify(
            {
                "success": False,
                "error": 405,
                "message": "method not allowed",
            }
        ), 405

    @app.errorhandler(422)
    def unprocessable(error):
        """Handle 422 Unprocessable Entity errors."""
        return jsonify(
            {
                "success": False,
                "error": 422,
                "message": "unprocessable entity",
            }
        ), 422

    @app.errorhandler(500)
    def internal_server_error(error):
        """Handle 500 Internal Server Error."""
        return jsonify(
            {
                "success": False,
                "error": 500,
                "message": "internal server error",
            }
        ), 500

    return app


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=(os.environ.get("FLASK_DEBUG", "false").lower() == "true"))
