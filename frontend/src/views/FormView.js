import React, { Component } from 'react';
import { mockCategories } from '../mockData';
import '../stylesheets/FormView.css';

class FormView extends Component {
  constructor(props) {
    super(props);
    this.state = {
      question: '',
      answer: '',
      difficulty: 1,
      category: 1,
      rating: 1,
      categories: {},
    };
  }

  componentDidMount() {
    fetch('/categories')
      .then((res) => res.json())
      .then((result) => {
        this.setState({ categories: result.categories });
      })
      .catch(() => {
        this.setState({ categories: mockCategories });
      });
  }

  submitQuestion = (event) => {
    event.preventDefault();
    fetch('/questions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        question: this.state.question,
        answer: this.state.answer,
        difficulty: this.state.difficulty,
        category: this.state.category,
        rating: this.state.rating,
      }),
    })
      .then((res) => {
        if (res.ok) {
          document.getElementById('add-question-form').reset();
          this.setState({
            question: '',
            answer: '',
            difficulty: 1,
            category: 1,
            rating: 1,
          });
          alert('Question added successfully!');
        } else {
          alert('Unable to add question. Please try again.');
        }
      })
      .catch((error) => {
        alert('Unable to add question. Please try again.');
      });
  };

  handleChange = (event) => {
    this.setState({ [event.target.name]: event.target.value });
  };

  render() {
    return (
      <div id='add-form'>
        <h2>Add a New Trivia Question</h2>
        <form
          className='form-view'
          id='add-question-form'
          onSubmit={this.submitQuestion}
        >
          <label>
            Question
            <input
              type='text'
              name='question'
              value={this.state.question}
              onChange={this.handleChange}
              required
            />
          </label>
          <label>
            Answer
            <input
              type='text'
              name='answer'
              value={this.state.answer}
              onChange={this.handleChange}
              required
            />
          </label>
          <label>
            Difficulty
            <select
              name='difficulty'
              value={this.state.difficulty}
              onChange={this.handleChange}
            >
              <option value='1'>1</option>
              <option value='2'>2</option>
              <option value='3'>3</option>
              <option value='4'>4</option>
              <option value='5'>5</option>
            </select>
          </label>
          <label>
            Rating
            <select
              name='rating'
              value={this.state.rating}
              onChange={this.handleChange}
            >
              <option value='1'>1</option>
              <option value='2'>2</option>
              <option value='3'>3</option>
              <option value='4'>4</option>
              <option value='5'>5</option>
            </select>
          </label>
          <label>
            Category
            <select
              name='category'
              value={this.state.category}
              onChange={this.handleChange}
            >
              {Object.keys(this.state.categories).map((id) => (
                <option key={id} value={id}>
                  {this.state.categories[id]}
                </option>
              ))}
            </select>
          </label>
          <input type='submit' className='button' value='Submit' />
        </form>
      </div>
    );
  }
}

export default FormView;
