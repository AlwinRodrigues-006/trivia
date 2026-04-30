# Trivia API

A full-stack trivia application with a RESTful Flask/PostgreSQL backend and a React frontend.  
Supports browsing, searching, adding and deleting questions, category filtering, and a quiz game mode.

---

## Quick Start for Reviewers

> Follow these steps exactly to get the app running locally from scratch.

### Prerequisites

| Tool | Version |
|------|---------|
| Python | 3.9+ |
| Node.js | 16+ |
| PostgreSQL | 13+ |

---

### Step 1 – Clone / extract the project

```bash
cd rubic1          # root of the project
```

---

### Step 2 – Create the PostgreSQL databases

```bash
# Replace 'postgres' with your PostgreSQL superuser if different
psql -U postgres -c "CREATE DATABASE trivia;"
psql -U postgres -c "CREATE DATABASE trivia_test;"
```

---

### Step 3 – Configure backend environment variables

```bash
cd backend
cp .env.example .env
```

Open `.env` and fill in your PostgreSQL credentials:

```ini
DB_HOST=localhost:5432
DB_NAME=trivia
DB_USER=postgres          # your postgres username
DB_PASSWORD=              # your postgres password (leave blank if none)
TEST_DB_NAME=trivia_test
FLASK_APP=app.py
FLASK_DEBUG=false
```

> **Note:** Never commit `.env` to version control.

---

### Step 4 – Set up the Python virtual environment

```bash
# still inside rubic1/backend/
python3 -m venv venv
source venv/bin/activate        # macOS / Linux
# venv\Scripts\activate         # Windows
pip install -r requirements.txt
```

---

### Step 5 – Load seed data into the database

```bash
psql -U postgres -d trivia -f trivia.psql
```

This creates the `categories` and `questions` tables and loads 6 categories and 20 questions.

---

### Step 6 – Run the backend tests

```bash
# still inside rubic1/backend/ with venv active
python -m pytest test_app.py -v
```

Expected output: **26 passed** with no errors or warnings.

---

### Step 7 – Start the Flask backend

```bash
# still inside rubic1/backend/ with venv active
flask run --port 5000
```

The API is now available at `http://localhost:5000`.

---

### Step 8 – Set up and start the React frontend

Open a **new terminal tab/window**:

```bash
cd rubic1/frontend
npm install
npm start
```

The app opens automatically at `http://localhost:3000`.  
All API calls are proxied to `http://localhost:5000` via the `"proxy"` setting in `package.json`.

---

### Step 9 – Using the app

| Feature | How |
|---------|-----|
| Browse all questions | Home page — paginated 10 per page |
| Filter by category | Click a category name in the left sidebar |
| Search questions | Use the search box in the left sidebar |
| Add a question | Click **Add** in the header nav |
| Delete a question | Click the trash icon on any question card |
| Play the quiz | Click **Play** in the header nav |

---

## Running Tests (standalone)

```bash
cd rubic1/backend
source venv/bin/activate        # activate venv if not already active
python -m pytest test_app.py -v
```

Tests use the `trivia_test` database which is automatically wiped and re-seeded before every test run. The production `trivia` database is never touched by tests.

---

## API Reference

All responses are JSON. Successful responses include `"success": true`; error responses include `"success": false`, `"error"` (HTTP status code), and `"message"`.

---

### Categories

#### `GET /categories`

Returns all trivia categories.

**Response body:**

```json
{
  "success": true,
  "categories": { "1": "Science", "2": "Art" },
  "total_categories": 6
}
```

---

### Questions

#### `GET /questions?page=<n>`

Returns a paginated list of all questions (10 per page) plus all categories.

**Response body:**

```json
{
  "success": true,
  "questions": [
    { "id": 1, "question": "...", "answer": "...", "category": 1, "difficulty": 2, "rating": 3 }
  ],
  "total_questions": 20,
  "categories": { "1": "Science" },
  "current_category": null
}
```

Returns `404` if the requested page is out of range.

---

#### `DELETE /questions/{question_id}`

Deletes the question with the given ID.

**Response body:**

```json
{ "success": true, "deleted": 1 }
```

Returns `404` if the question does not exist.

---

#### `POST /questions` – Create a question

**Request body:**

```json
{
  "question": "What is the speed of light?",
  "answer": "299,792,458 m/s",
  "category": 1,
  "difficulty": 3,
  "rating": 5
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `question` | str | Yes | Question text |
| `answer` | str | Yes | Answer text |
| `category` | int | Yes | Category ID (must exist) |
| `difficulty` | int | Yes | 1–5 |
| `rating` | int | No | 1–5 (default `1`) |

**Response (201):**

```json
{ "success": true, "created": 21 }
```

Returns `422` for missing/invalid fields, `400` for no body.

---

#### `POST /questions` – Search questions

**Request body:**

```json
{ "searchTerm": "water" }
```

**Response:**

```json
{
  "success": true,
  "questions": [ { "id": 1, ... } ],
  "total_questions": 1,
  "current_category": null
}
```

---

#### `GET /categories/{category_id}/questions`

Returns all questions for a category (paginated). Returns `404` if category not found.

#### `POST /categories/{category_id}/questions`

Identical to the GET variant — provided for clients that prefer POST.

**Response (both):**

```json
{
  "success": true,
  "questions": [ { "id": 1, ... } ],
  "total_questions": 4,
  "current_category": "Science"
}
```

---

#### `POST /quizzes`

Returns a random unseen question for the quiz game.

**Request body:**

```json
{
  "previous_questions": [1, 4],
  "quiz_category": { "id": 1, "type": "Science" }
}
```

Use `"id": 0` for all categories.

**Response:**

```json
{
  "success": true,
  "question": { "id": 5, "question": "...", "answer": "...", "category": 1, "difficulty": 2, "rating": 3 }
}
```

`"question"` is `null` when all questions in the category have been shown.  
Returns `400` if body or `quiz_category` is missing.

---

## Error Responses

| Code | Message |
|------|---------|
| 400 | bad request |
| 404 | resource not found |
| 405 | method not allowed |
| 422 | unprocessable entity |
| 500 | internal server error |

**Example:**

```json
{ "success": false, "error": 404, "message": "resource not found" }
```

---

## Project Structure

```
rubic1/
├── README.md
├── backend/
│   ├── app.py            # Flask application — all API endpoints
│   ├── models.py         # SQLAlchemy models (Question, Category)
│   ├── test_app.py       # 26 unit tests (unittest + pytest)
│   ├── requirements.txt  # Python dependencies
│   ├── trivia.psql       # Database schema + seed data
│   └── .env.example      # Environment variable template
└── frontend/
    ├── package.json      # Node dependencies + proxy config
    ├── public/           # SVG icons + index.html
    └── src/
        ├── App.js
        ├── components/   # Header, Question, Search
        ├── views/        # QuestionView, FormView, QuizView
        └── stylesheets/
```


## API Reference

All responses are JSON. Successful responses include `"success": true`; error responses include `"success": false`, `"error"` (HTTP status code), and `"message"`.

---

### Categories

#### `GET /categories`

Returns all trivia categories.

**Request parameters:** none

**Response body:**

```json
{
  "success": true,
  "categories": {
    "1": "Science",
    "2": "Art"
  },
  "total_categories": 2
}
```

---

### Questions

#### `GET /questions`

Returns a paginated list of all questions (10 per page) and all categories.

**Request parameters:**

| Parameter | Type | Default | Description       |
|-----------|------|---------|-------------------|
| `page`    | int  | `1`     | Page number       |

**Response body:**

```json
{
  "success": true,
  "questions": [
    {
      "id": 1,
      "question": "What is H2O?",
      "answer": "Water",
      "category": 1,
      "difficulty": 1,
      "rating": 4
    }
  ],
  "total_questions": 20,
  "categories": { "1": "Science" },
  "current_category": null
}
```

---

#### `DELETE /questions/{question_id}`

Deletes the question with the given ID.

**Request parameters:** none

**Response body:**

```json
{
  "success": true,
  "deleted": 1
}
```

Returns `404` if the question does not exist.

---

#### `POST /questions` – Create a question

Creates a new trivia question.

**Request body:**

```json
{
  "question": "What is the speed of light?",
  "answer": "299,792,458 m/s",
  "category": 1,
  "difficulty": 3,
  "rating": 5
}
```

| Field        | Type | Required | Description                  |
|--------------|------|----------|------------------------------|
| `question`   | str  | Yes      | Question text                |
| `answer`     | str  | Yes      | Answer text                  |
| `category`   | int  | Yes      | Category ID                  |
| `difficulty` | int  | Yes      | Difficulty 1–5               |
| `rating`     | int  | No       | Rating 1–5 (default: `1`)    |

**Response body (201 Created):**

```json
{
  "success": true,
  "created": 21
}
```

Returns `422` if required fields are missing or invalid, `400` if no JSON body is supplied.

---

#### `POST /questions` – Search questions

Searches questions by a case-insensitive substring match.

**Request body:**

```json
{
  "searchTerm": "water"
}
```

**Response body:**

```json
{
  "success": true,
  "questions": [ { "id": 1, "question": "...", ... } ],
  "total_questions": 1,
  "current_category": null
}
```

---

#### `GET /categories/{category_id}/questions`

Returns all questions for a specific category (paginated).

**Request parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page`    | int  | `1`     | Page number |

**Response body:**

```json
{
  "success": true,
  "questions": [ { "id": 1, ... } ],
  "total_questions": 4,
  "current_category": "Science"
}
```

Returns `404` if the category does not exist or has no questions on the requested page.

---

#### `POST /categories/{category_id}/questions`

Identical to the GET variant above. Returns all questions for a specific category (paginated) via a POST request.

**Request parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page`    | int  | `1`     | Page number (query string) |

**Request body:** none required.

**Response body:**

```json
{
  "success": true,
  "questions": [ { "id": 1, ... } ],
  "total_questions": 4,
  "current_category": "Science"
}
```

Returns `404` if the category does not exist or has no questions on the requested page.

---

### Quiz

#### `POST /quizzes`

Returns a random question not yet shown in the current game session, optionally filtered by category.

**Request body:**

```json
{
  "previous_questions": [1, 4],
  "quiz_category": { "id": 1, "type": "Science" }
}
```

Use `"id": 0` to allow questions from all categories.

**Response body:**

```json
{
  "success": true,
  "question": {
    "id": 5,
    "question": "What planet is closest to the Sun?",
    "answer": "Mercury",
    "category": 1,
    "difficulty": 2,
    "rating": 3
  }
}
```

When all questions in the selected category have been shown, `"question"` is `null`.

Returns `400` if the request body is missing or `quiz_category` is not provided.

---

## Error Responses

| Code | Message                |
|------|------------------------|
| 400  | bad request            |
| 404  | resource not found     |
| 405  | method not allowed     |
| 422  | unprocessable entity   |
| 500  | internal server error  |

**Example:**

```json
{
  "success": false,
  "error": 404,
  "message": "resource not found"
}
```

---

## Project Structure

```
rubic1/
├── README.md
├── backend/
│   ├── app.py            # Flask application and all API endpoints
│   ├── models.py         # SQLAlchemy database models (Question, Category)
│   ├── test_app.py       # Unit tests (unittest + pytest compatible)
│   ├── requirements.txt  # Python dependencies
│   ├── trivia.psql       # Database seed script
│   └── .env.example      # Environment variable template
└── frontend/
    ├── package.json      # Node dependencies and proxy config
    ├── public/
    │   └── index.html
    └── src/
        ├── App.js
        ├── components/   # Header, Question, Search
        ├── views/        # QuestionView, FormView, QuizView
        └── stylesheets/
```

---

## Frontend Setup

### Prerequisites

- Node.js 16+

### 1. Install frontend dependencies

```bash
cd rubic1/frontend
npm install
```

### 2. Start the React development server

```bash
npm start
```

The app opens at `http://localhost:3000`. API calls are proxied to `http://localhost:5000` automatically (configured in `package.json`).

> Both the Flask backend and the React frontend must be running at the same time for the app to work.

