import React, { Component } from 'react';
import { mockCategories, mockQuestions } from '../mockData';
import '../stylesheets/QuizView.css';

const questionsPerPlay = 5;

class QuizView extends Component {
  constructor(props) {
    super(props);
    this.state = {
      quizCategory: null,
      previousQuestions: [],
      showAnswer: false,
      categories: {},
      numCorrect: 0,
      currentQuestion: {},
      guess: '',
      forceEnd: false,
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

  selectCategory = ({ type, id = 0 }) => {
    this.setState({ quizCategory: { type, id } }, this.getNextQuestion);
  };

  handleChange = (event) => {
    this.setState({ guess: event.target.value });
  };

  getNextQuestion = () => {
    const previousQuestions = [...this.state.previousQuestions];
    if (this.state.currentQuestion.id) {
      previousQuestions.push(this.state.currentQuestion.id);
    }

    fetch('/quizzes', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        previous_questions: previousQuestions,
        quiz_category: this.state.quizCategory,
      }),
    })
      .then((res) => res.json())
      .then((result) => {
        this.setState({
          showAnswer: false,
          previousQuestions,
          currentQuestion: result.question || {},
          guess: '',
          forceEnd: result.question ? false : true,
        });
      })
      .catch(() => {
        const { id } = this.state.quizCategory;
        const pool = mockQuestions.filter(
          (q) =>
            !previousQuestions.includes(q.id) &&
            (id === 0 || q.category === id)
        );
        const next =
          pool.length > 0
            ? pool[Math.floor(Math.random() * pool.length)]
            : null;
        this.setState({
          showAnswer: false,
          previousQuestions,
          currentQuestion: next || {},
          guess: '',
          forceEnd: !next,
        });
      });
  };

  submitGuess = (event) => {
    event.preventDefault();
    const evaluate = this.evaluateAnswer();
    this.setState({
      numCorrect: evaluate ? this.state.numCorrect + 1 : this.state.numCorrect,
      showAnswer: true,
    });
  };

  restartGame = () => {
    this.setState({
      quizCategory: null,
      previousQuestions: [],
      showAnswer: false,
      numCorrect: 0,
      currentQuestion: {},
      guess: '',
      forceEnd: false,
    });
  };

  renderPrePlay() {
    return (
      <div className='quiz-play-holder'>
        <div className='choose-header'>Choose Category</div>
        <div className='category-holder'>
          <div
            className='play-category'
            onClick={() => this.selectCategory({ type: 'ALL', id: 0 })}
          >
            ALL
          </div>
          {Object.keys(this.state.categories).map((id) => (
            <div
              key={id}
              value={id}
              className='play-category'
              onClick={() =>
                this.selectCategory({
                  type: this.state.categories[id],
                  id: parseInt(id),
                })
              }
            >
              <img
                className='play-category-icon'
                alt={this.state.categories[id].toLowerCase()}
                src={`/${this.state.categories[id].toLowerCase()}.svg`}
              />
              {this.state.categories[id]}
            </div>
          ))}
        </div>
      </div>
    );
  }

  renderFinalScore() {
    return (
      <div className='quiz-play-holder'>
        <div className='final-header'>
          Your Final Score is {this.state.numCorrect}
        </div>
        <div
          className='play-again button'
          onClick={this.restartGame}
        >
          Play Again?
        </div>
      </div>
    );
  }

  evaluateAnswer = () => {
    const formatGuess = this.state.guess
      .replace(/[.,/#!$%^&*;:{}=\-_`~()]/g, '')
      .toLowerCase();
    const answerArray = this.state.currentQuestion.answer
      .toLowerCase()
      .split(' ');
    return answerArray.every((el) => formatGuess.includes(el));
  };

  renderCorrectAnswer() {
    const evaluate = this.evaluateAnswer();
    return (
      <div className='quiz-play-holder'>
        <div className='quiz-question'>
          {this.state.currentQuestion.question}
        </div>
        <div className={`${evaluate ? 'correct' : 'wrong'}`}>
          {evaluate ? 'You were correct!' : 'You were incorrect'}
        </div>
        <div className='quiz-answer'>{this.state.currentQuestion.answer}</div>
        <div
          className='next-question button'
          onClick={this.getNextQuestion}
        >
          Next Question
        </div>
      </div>
    );
  }

  renderPlay() {
    return this.state.previousQuestions.length === questionsPerPlay ||
      this.state.forceEnd
      ? this.renderFinalScore()
      : this.state.showAnswer
      ? this.renderCorrectAnswer()
      : (
        <div className='quiz-play-holder'>
          <div className='quiz-question'>
            {this.state.currentQuestion.question}
          </div>
          <form onSubmit={this.submitGuess}>
            <input
              type='text'
              name='guess'
              onChange={this.handleChange}
              value={this.state.guess}
            />
            <input
              className='button'
              type='submit'
              value='Submit Answer'
            />
          </form>
        </div>
      );
  }

  render() {
    return this.state.quizCategory ? this.renderPlay() : this.renderPrePlay();
  }
}

export default QuizView;
