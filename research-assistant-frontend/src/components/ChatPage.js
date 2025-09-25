// src/components/ChatPage.js

import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { postChatMessage } from '../services/api';

function ChatPage() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false); // State for loading indicator
  const navigate = useNavigate();
  const messagesEndRef = useRef(null);

  useEffect(() => {
    const token = localStorage.getItem('authToken');
    if (!token) {
      navigate('/');
    }
  }, [navigate]);
  
  // Auto-scroll to the latest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]); // Also scroll when loading indicator appears


  const handleLogout = () => {
    localStorage.removeItem('authToken');
    navigate('/');
  };

  const handleSend = async () => {
    if (input.trim() === '' || isLoading) return;

    const userMessage = { sender: 'user', text: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true); // --- Turn on loading ---

    try {
      const response = await postChatMessage(input);
      const botMessage = { sender: 'bot', text: response.data.response };
      setMessages((prev) => [...prev, botMessage]);
    } catch (error) {
      const errorMessage = { sender: 'bot', text: 'Error: Could not get a response from the server.' };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false); // --- Turn off loading ---
    }
  };

  return (
    <div className="chat-container">
      <header className="chat-header">
        <h2>Research Assistant</h2>
        <button onClick={handleLogout} className="logout-button">Logout</button>
      </header>
      <div className="message-list">
        {messages.map((msg, index) => (
          <div key={index} className={`message ${msg.sender}`}>
            <p>{msg.text}</p>
          </div>
        ))}
        {/* --- Loading Indicator --- */}
        {isLoading && (
          <div className="message bot">
            <div className="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      <div className="message-input">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Ask a question..."
          disabled={isLoading}
        />
        <button onClick={handleSend} disabled={isLoading}>Send</button>
      </div>
    </div>
  );
}

export default ChatPage;