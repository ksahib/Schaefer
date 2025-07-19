import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './Botpage.css';

const Botpage = () => {
  const navigate = useNavigate();
  const [messages, setMessages] = useState([
    { sender: 'bot', text: '🎵 Welcome! Ask me anything about music.' }
  ]);
  const [input, setInput] = useState('');

  const handleSend = () => {
    if (!input.trim()) return;

    setMessages([...messages, { sender: 'user', text: input }]);
    setInput('');

    
    setTimeout(() => {
      setMessages(prev => [
        ...prev,
        { sender: 'bot', text: '🎶 I see! I\'ll analyse that right away.' }
      ]);
    }, 1000);
  };

  return (
    <div className="bot-container">
      <header className="bot-header">
        <h1>Schaefer</h1>
        <p>Your Music Analyser and Assistant</p>
      </header>

      <div className="chat-window">
        {messages.map((msg, index) => (
          <div
            key={index}
            className={`chat-bubble ${msg.sender === 'bot' ? 'bot' : 'user'}`}
          >
            {msg.text}
          </div>
        ))}
      </div>

      <div className="chat-input-bar">
        <input
          type="text"
          placeholder="Type a message..."
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleSend()}
        />
        <button onClick={handleSend}>➤</button>
      </div>

      <div className="bot-footer">
        <button onClick={() => navigate('/Home')}>← Home</button>
      </div>
    </div>
  );
};

export default Botpage;