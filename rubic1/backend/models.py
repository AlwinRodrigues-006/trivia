"""
Database models for the Trivia API application.
Uses Flask-SQLAlchemy to define Question and Category models.
"""

import os
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

load_dotenv()

database_host = os.environ.get("DB_HOST", "localhost:5432")
database_name = os.environ.get("DB_NAME", "trivia")
database_user = os.environ.get("DB_USER", "postgres")
database_password = os.environ.get("DB_PASSWORD", "")
database_path = (
    f"postgresql://{database_user}:{database_password}"
    f"@{database_host}/{database_name}"
)

db = SQLAlchemy()


def setup_db(app, database_url=None):
    """Bind a Flask application and a SQLAlchemy service."""
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url or database_path
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.app = app
    db.init_app(app)


def db_drop_and_create_all():
    """Drop all tables and recreate them. Used for testing."""
    db.drop_all()
    db.create_all()


class Category(db.Model):
    """Represents a trivia category."""

    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String, nullable=False, unique=True)

    # Relationship to questions
    questions = db.relationship(
        "Question", backref="category_rel", lazy=True, cascade="all, delete"
    )

    def format(self):
        """Return a dictionary representation of the category."""
        return {"id": self.id, "type": self.type}


class Question(db.Model):
    """Represents a trivia question."""

    __tablename__ = "questions"

    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String, nullable=False)
    answer = db.Column(db.String, nullable=False)
    difficulty = db.Column(db.Integer, nullable=False)
    rating = db.Column(db.Integer, nullable=False, default=1)
    category = db.Column(
        db.Integer, db.ForeignKey("categories.id"), nullable=False
    )

    def __init__(self, question, answer, category, difficulty, rating=1):
        self.question = question
        self.answer = answer
        self.category = category
        self.difficulty = difficulty
        self.rating = rating

    def insert(self):
        """Insert this question into the database."""
        try:
            db.session.add(self)
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

    def update(self):
        """Update this question in the database."""
        db.session.commit()

    def delete(self):
        """Delete this question from the database."""
        db.session.delete(self)
        db.session.commit()

    def format(self):
        """Return a dictionary representation of the question."""
        return {
            "id": self.id,
            "question": self.question,
            "answer": self.answer,
            "category": self.category,
            "difficulty": self.difficulty,
            "rating": self.rating,
        }
