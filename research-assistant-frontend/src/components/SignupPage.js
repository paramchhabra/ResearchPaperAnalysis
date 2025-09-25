// src/components/SignupPage.js

import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { signupUser } from '../services/api';

function SignupPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    try {
      await signupUser({ username, password });
      navigate('/'); // Redirect to login page after successful signup
    } catch (err) {
      setError('Username already exists or another error occurred.');
    }
  };

  return (
    <div className="auth-container">
      <form className="auth-form" onSubmit={handleSubmit}>
        <h2>Sign Up</h2>
        {error && <p className="error-message">{error}</p>}
        <input
          type="text"
          placeholder="Username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          required
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        <button type="submit">Sign Up</button>
        <p>
          Already have an account? <Link to="/">Login</Link>
        </p>
      </form>
    </div>
  );
}

export default SignupPage;