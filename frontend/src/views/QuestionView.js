import React, { Component } from 'react';
import Question from '../components/Question';
import Search from '../components/Search';
import { mockCategories, mockQuestions } from '../mockData';
import '../stylesheets/App.css';

const questionsPerPage = 10;

class QuestionView extends Component {
  constructor() {
    super();
    this.state = {
      questions: [],
      page: 1,
      totalQuestions: 0,
      categories: {},
      currentCategory: null,
    };
  }

  componentDidMount() {
    this.getQuestions();
  }

  getQuestions = () => {
    fetch(`/questions?page=${this.state.page}`)
      .then((res) => res.json())
      .then((result) => {
        if (!result.success) {
          // Page out of range (e.g. after a delete) — fall back to page 1
          this.setState({ page: 1 }, () => this.getQuestions());
          return;
        }
        this.setState({
          questions: result.questions,
          totalQuestions: result.total_questions,
          categories: result.categories,
          currentCategory: result.current_category,
        });
      })
      .catch(() => {
        const start = (this.state.page - 1) * questionsPerPage;
        const paged = mockQuestions.slice(start, start + questionsPerPage);
        this.setState({
          questions: paged,
          totalQuestions: mockQuestions.length,
          categories: mockCategories,
          currentCategory: null,
        });
      });
  };

  selectPage(num) {
    this.setState({ page: num }, () => this.getQuestions());
  }

  createPagination() {
    const pageNumbers = [];
    const maxPage = Math.ceil(this.state.totalQuestions / questionsPerPage);
    for (let i = 1; i <= maxPage; i++) {
      pageNumbers.push(
        <span
          key={i}
          className={`page-num ${i === this.state.page ? 'active' : ''}`}
          onClick={() => {
            this.selectPage(i);
          }}
        >
          {i}
        </span>
      );
    }
    return pageNumbers;
  }

  getByCategory = (id) => {
    fetch(`/categories/${id}/questions`)
      .then((res) => res.json())
      .then((result) => {
        this.setState({
          questions: result.questions,
          totalQuestions: result.total_questions,
          currentCategory: result.current_category,
        });
      })
      .catch(() => {
        const filtered = mockQuestions.filter(
          (q) => q.category === parseInt(id)
        );
        this.setState({
          questions: filtered,
          totalQuestions: filtered.length,
          currentCategory: mockCategories[id],
        });
      });
  };

  submitSearch = (searchTerm) => {
    fetch('/questions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ searchTerm }),
    })
      .then((res) => res.json())
      .then((result) => {
        this.setState({
          questions: result.questions,
          totalQuestions: result.total_questions,
          currentCategory: result.current_category,
        });
      })
      .catch(() => {
        const term = searchTerm.toLowerCase();
        const filtered = mockQuestions.filter((q) =>
          q.question.toLowerCase().includes(term)
        );
        this.setState({
          questions: filtered,
          totalQuestions: filtered.length,
          currentCategory: null,
        });
      });
  };

  questionAction = (id) => (action) => {
    if (action === 'DELETE') {
      if (window.confirm('Are you sure you want to delete this question?')) {
        fetch(`/questions/${id}`, { method: 'DELETE' })
          .then((res) => {
            if (res.ok) {
              // Reset to page 1 so we never land on an empty page after delete
              this.setState({ page: 1 }, () => this.getQuestions());
            } else {
              alert('Unable to delete question. Please try again.');
            }
          })
          .catch(() => {
            alert('Unable to delete question. Please try again.');
          });
      }
    }
  };

  render() {
    return (
      <div className='question-view'>
        <div className='categories-list'>
          <h2
            onClick={() => {
              this.getQuestions();
            }}
          >
            Categories
          </h2>
          <ul>
            {Object.keys(this.state.categories).map((id) => (
              <li
                key={id}
                onClick={() => {
                  this.getByCategory(id);
                }}
              >
                {this.state.categories[id]}
                <img
                  className='category'
                  alt={this.state.categories[id].toLowerCase()}
                  src={`/${this.state.categories[id].toLowerCase()}.svg`}
                />
              </li>
            ))}
          </ul>
          <Search submitSearch={this.submitSearch} />
        </div>
        <div className='questions-list'>
          <h2>Questions</h2>
          {this.state.questions.map((q, ind) => (
            <Question
              key={q.id}
              question={q.question}
              answer={q.answer}
              category={this.state.categories[q.category]}
              difficulty={q.difficulty}
              rating={q.rating}
              questionAction={this.questionAction(q.id)}
            />
          ))}
          <div className='pagination-menu'>{this.createPagination()}</div>
        </div>
      </div>
    );
  }
}

export default QuestionView;
