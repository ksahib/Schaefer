import React, { useState } from 'react';
import './Botpage.css'

function Botpage() {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState([]);

  const sendMessage = async () => {
    if (!input.trim()) return;

    setMessages([...messages, { role: 'user', text: input }]);

    const res = await fetch('http://localhost:8000/chat/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query: input, session_id: 'ee' }),
    });

    const data = await res.json();
    setMessages(prev => [...prev, { role: 'bot', text: data.response }]);
    setInput('');
  };

  return (
    <div style={{ padding: '2rem' }}>
      <h2>Chat with Schaefer</h2>
      <div style={{ border: '1px solid gray', padding: '1rem', height: '300px', overflowY: 'scroll' }}>
        {messages.map((msg, index) => (
          <div key={index} style={{ textAlign: msg.role === 'user' ? 'right' : 'left' }}>
            <strong>{msg.role === 'user' ? 'You' : 'Bot'}:</strong> {msg.text}
          </div>
        ))}
      </div>
      <input
        type="text"
        value={input}
        onChange={e => setInput(e.target.value)}
        placeholder="Type your message"
        style={{ width: '80%', marginTop: '1rem' }}
      />
      <button onClick={sendMessage} style={{ marginLeft: '1rem' }}>
        Send
      </button>
    </div>
  );
}

export default Botpage;
