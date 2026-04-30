"""
Unit tests for the Trivia API Flask application.

Tests every endpoint for expected success and error behavior.
Validates that CRUD operations persist correctly in the test database.
"""

import json
import os
import unittest

from app import create_app
from models import Category, Question, db, db_drop_and_create_all

# Use a separate test database so production data is never touched
TEST_DB_NAME = os.environ.get("TEST_DB_NAME", "trivia_test")
TEST_DB_USER = os.environ.get("DB_USER", "postgres")
TEST_DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
TEST_DB_HOST = os.environ.get("DB_HOST", "localhost:5432")

TEST_DATABASE_URI = (
    f"postgresql://{TEST_DB_USER}:{TEST_DB_PASSWORD}"
    f"@{TEST_DB_HOST}/{TEST_DB_NAME}"
)


class TriviaTestCase(unittest.TestCase):
    """Test suite for the Trivia API."""

    def setUp(self):
        """Set up the test client and populate the test database."""
        self.app = create_app(
            {"SQLALCHEMY_DATABASE_URI": TEST_DATABASE_URI}
        )
        self.client = self.app.test_client()

        with self.app.app_context():
            db_drop_and_create_all()
            self._seed_data()

    def _seed_data(self):
        """Insert minimal seed data required by the tests."""
        # Create two categories
        cat1 = Category(type="Science")
        cat2 = Category(type="History")
        db.session.add_all([cat1, cat2])
        db.session.flush()  # assign IDs before questions reference them

        # Save category IDs for use in tests
        self.science_id = cat1.id
        self.history_id = cat2.id

        # Create several questions
        questions = [
            Question(
                question="What is the chemical symbol for water?",
                answer="H2O",
                category=cat1.id,
                difficulty=1,
                rating=4,
            ),
            Question(
                question="What planet is closest to the Sun?",
                answer="Mercury",
                category=cat1.id,
                difficulty=2,
                rating=3,
            ),
            Question(
                question="In what year did World War II end?",
                answer="1945",
                category=cat2.id,
                difficulty=2,
                rating=5,
            ),
            Question(
                question="Who was the first President of the United States?",
                answer="George Washington",
                category=cat2.id,
                difficulty=1,
                rating=4,
            ),
        ]
        db.session.add_all(questions)
        db.session.commit()

        # Store the first question's ID for delete/quiz tests
        self.first_question_id = questions[0].id

    def tearDown(self):
        """Drop all tables after each test to keep the DB clean."""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    # -----------------------------------------------------------------------
    # GET /categories
    # -----------------------------------------------------------------------

    def test_get_categories_success(self):
        """GET /categories returns 200 with a categories dict."""
        res = self.client.get("/categories")
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertTrue(data["success"])
        self.assertIsInstance(data["categories"], dict)
        self.assertGreater(data["total_categories"], 0)

    def test_get_categories_method_not_allowed(self):
        """POST /categories returns 405."""
        res = self.client.post("/categories")
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 405)
        self.assertFalse(data["success"])

    # -----------------------------------------------------------------------
    # GET /questions
    # -----------------------------------------------------------------------

    def test_get_questions_success(self):
        """GET /questions returns 200 with paginated questions."""
        res = self.client.get("/questions")
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertTrue(data["success"])
        self.assertIsInstance(data["questions"], list)
        self.assertGreater(data["total_questions"], 0)
        self.assertIsInstance(data["categories"], dict)

    def test_get_questions_page_out_of_range(self):
        """GET /questions?page=9999 returns 404 when no questions exist on that page."""
        res = self.client.get("/questions?page=9999")
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 404)
        self.assertFalse(data["success"])
        self.assertEqual(data["error"], 404)

    # -----------------------------------------------------------------------
    # DELETE /questions/<id>
    # -----------------------------------------------------------------------

    def test_delete_question_success(self):
        """DELETE /questions/<id> returns 200 and the deleted id."""
        res = self.client.delete(f"/questions/{self.first_question_id}")
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertTrue(data["success"])
        self.assertEqual(data["deleted"], self.first_question_id)

        # Verify the question is gone from the DB
        with self.app.app_context():
            question = db.session.get(Question, self.first_question_id)
            self.assertIsNone(question)

    def test_delete_question_not_found(self):
        """DELETE /questions/<nonexistent id> returns 404."""
        res = self.client.delete("/questions/99999")
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 404)
        self.assertFalse(data["success"])

    # -----------------------------------------------------------------------
    # POST /questions  – create
    # -----------------------------------------------------------------------

    def test_create_question_success(self):
        """POST /questions with valid data creates a new question (201)."""
        new_q = {
            "question": "What is the speed of light?",
            "answer": "299,792,458 m/s",
            "category": self.science_id,
            "difficulty": 3,
            "rating": 5,
        }
        res = self.client.post(
            "/questions",
            data=json.dumps(new_q),
            content_type="application/json",
        )
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 201)
        self.assertTrue(data["success"])
        self.assertIn("created", data)

        # Verify persistence
        with self.app.app_context():
            question = db.session.get(Question, data["created"])
            self.assertIsNotNone(question)
            self.assertEqual(question.answer, "299,792,458 m/s")
            self.assertEqual(question.rating, 5)

    def test_create_question_missing_fields(self):
        """POST /questions without required fields returns 422."""
        incomplete = {"question": "Missing fields?"}
        res = self.client.post(
            "/questions",
            data=json.dumps(incomplete),
            content_type="application/json",
        )
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 422)
        self.assertFalse(data["success"])

    def test_create_question_invalid_category(self):
        """POST /questions with a nonexistent category returns 422."""
        bad_q = {
            "question": "Bad category?",
            "answer": "Yes",
            "category": 99999,
            "difficulty": 2,
            "rating": 1,
        }
        res = self.client.post(
            "/questions",
            data=json.dumps(bad_q),
            content_type="application/json",
        )
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 422)
        self.assertFalse(data["success"])

    def test_create_question_no_body(self):
        """POST /questions with no JSON body returns 400."""
        res = self.client.post("/questions")
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 400)
        self.assertFalse(data["success"])

    def test_create_question_non_numeric_difficulty(self):
        """POST /questions with a non-numeric difficulty returns 422, not 500."""
        bad_q = {
            "question": "Bad difficulty?",
            "answer": "Yes",
            "category": self.science_id,
            "difficulty": "hard",
            "rating": 1,
        }
        res = self.client.post(
            "/questions",
            data=json.dumps(bad_q),
            content_type="application/json",
        )
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 422)
        self.assertFalse(data["success"])

    def test_create_question_null_rating_defaults_to_one(self):
        """POST /questions with explicit null rating defaults rating to 1."""
        q = {
            "question": "Null rating test?",
            "answer": "OK",
            "category": self.science_id,
            "difficulty": 2,
            "rating": None,
        }
        res = self.client.post(
            "/questions",
            data=json.dumps(q),
            content_type="application/json",
        )
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 201)
        self.assertTrue(data["success"])

        with self.app.app_context():
            question = db.session.get(Question, data["created"])
            self.assertEqual(question.rating, 1)

    def test_create_question_out_of_range_difficulty(self):
        """POST /questions with difficulty outside 1-5 returns 422."""
        bad_q = {
            "question": "Out of range?",
            "answer": "Yes",
            "category": self.science_id,
            "difficulty": 6,
            "rating": 3,
        }
        res = self.client.post(
            "/questions",
            data=json.dumps(bad_q),
            content_type="application/json",
        )
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 422)
        self.assertFalse(data["success"])

    # -----------------------------------------------------------------------
    # POST /questions  – search
    # -----------------------------------------------------------------------

    def test_search_questions_success(self):
        """POST /questions with searchTerm returns matching questions."""
        res = self.client.post(
            "/questions",
            data=json.dumps({"searchTerm": "water"}),
            content_type="application/json",
        )
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertTrue(data["success"])
        self.assertGreater(len(data["questions"]), 0)

    def test_search_questions_no_results(self):
        """POST /questions with unmatched searchTerm returns empty list."""
        res = self.client.post(
            "/questions",
            data=json.dumps({"searchTerm": "xyzzy_no_match_12345"}),
            content_type="application/json",
        )
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertTrue(data["success"])
        self.assertEqual(len(data["questions"]), 0)

    # -----------------------------------------------------------------------
    # GET /categories/<id>/questions
    # -----------------------------------------------------------------------

    def test_get_questions_by_category_success(self):
        """GET /categories/<id>/questions returns questions for that category."""
        res = self.client.get(f"/categories/{self.science_id}/questions")
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertTrue(data["success"])
        self.assertGreater(len(data["questions"]), 0)
        self.assertEqual(data["current_category"], "Science")

    def test_get_questions_by_category_not_found(self):
        """GET /categories/99999/questions returns 404 for a nonexistent category."""
        res = self.client.get("/categories/99999/questions")
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 404)
        self.assertFalse(data["success"])

    # -----------------------------------------------------------------------
    # POST /categories/<id>/questions
    # -----------------------------------------------------------------------

    def test_post_questions_by_category_success(self):
        """POST /categories/<id>/questions returns questions for that category."""
        res = self.client.post(f"/categories/{self.science_id}/questions")
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertTrue(data["success"])
        self.assertGreater(len(data["questions"]), 0)
        self.assertEqual(data["current_category"], "Science")
        # Every returned question must belong to the requested category
        for q in data["questions"]:
            self.assertEqual(q["category"], self.science_id)

    def test_post_questions_by_category_not_found(self):
        """POST /categories/99999/questions returns 404 for a nonexistent category."""
        res = self.client.post("/categories/99999/questions")
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 404)
        self.assertFalse(data["success"])

    # -----------------------------------------------------------------------
    # POST /quizzes
    # -----------------------------------------------------------------------

    def test_play_quiz_all_categories(self):
        """POST /quizzes returns a question when quiz_category id is 0."""
        payload = {
            "previous_questions": [],
            "quiz_category": {"id": 0, "type": "click"},
        }
        res = self.client.post(
            "/quizzes",
            data=json.dumps(payload),
            content_type="application/json",
        )
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertTrue(data["success"])
        self.assertIsNotNone(data["question"])

    def test_play_quiz_specific_category(self):
        """POST /quizzes with a category id returns a question from that category."""
        payload = {
            "previous_questions": [],
            "quiz_category": {"id": self.science_id, "type": "Science"},
        }
        res = self.client.post(
            "/quizzes",
            data=json.dumps(payload),
            content_type="application/json",
        )
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertTrue(data["success"])
        self.assertIsNotNone(data["question"])
        self.assertEqual(data["question"]["category"], self.science_id)

    def test_play_quiz_exhausted_returns_none(self):
        """POST /quizzes returns question=None when all questions already shown."""
        with self.app.app_context():
            all_ids = [q.id for q in Question.query.filter_by(
                category=self.science_id
            ).all()]

        payload = {
            "previous_questions": all_ids,
            "quiz_category": {"id": self.science_id, "type": "Science"},
        }
        res = self.client.post(
            "/quizzes",
            data=json.dumps(payload),
            content_type="application/json",
        )
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertTrue(data["success"])
        self.assertIsNone(data["question"])

    def test_play_quiz_no_body(self):
        """POST /quizzes with no JSON body returns 400."""
        res = self.client.post("/quizzes")
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 400)
        self.assertFalse(data["success"])

    def test_play_quiz_missing_category(self):
        """POST /quizzes without quiz_category key returns 400."""
        res = self.client.post(
            "/quizzes",
            data=json.dumps({"previous_questions": []}),
            content_type="application/json",
        )
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 400)
        self.assertFalse(data["success"])

    # -----------------------------------------------------------------------
    # Question rating field persistence
    # -----------------------------------------------------------------------

    def test_rating_field_persists(self):
        """Created question retains the rating value in the database."""
        new_q = {
            "question": "Rating persistence test question?",
            "answer": "Yes",
            "category": self.history_id,
            "difficulty": 1,
            "rating": 3,
        }
        res = self.client.post(
            "/questions",
            data=json.dumps(new_q),
            content_type="application/json",
        )
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 201)

        with self.app.app_context():
            question = db.session.get(Question, data["created"])
            self.assertEqual(question.rating, 3)

    def test_rating_defaults_to_one(self):
        """A question created without a rating field defaults rating to 1."""
        new_q = {
            "question": "Default rating test?",
            "answer": "One",
            "category": self.science_id,
            "difficulty": 2,
        }
        res = self.client.post(
            "/questions",
            data=json.dumps(new_q),
            content_type="application/json",
        )
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 201)

        with self.app.app_context():
            question = db.session.get(Question, data["created"])
            self.assertEqual(question.rating, 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
