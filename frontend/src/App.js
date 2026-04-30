import React, { Component } from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import './stylesheets/App.css';
import Header from './components/Header';
import QuestionView from './views/QuestionView';
import FormView from './views/FormView';
import QuizView from './views/QuizView';

class App extends Component {
  render() {
    return (
      <div className='App'>
        <Router>
          <Header path />
          <Routes>
            <Route path='/' element={<QuestionView />} />
            <Route path='/add' element={<FormView />} />
            <Route path='/play' element={<QuizView />} />
          </Routes>
        </Router>
      </div>
    );
  }
}

export default App;
