import { useNavigate } from "react-router-dom";
import './ChatPage.css'; 

const ChatPage = () => {
  const nav = useNavigate();
  const nav2 =useNavigate();

  return (
    <div className="chat-container">
      <div className="chat-header">
        <h1>Welcome to Schaefer</h1>
        <p>Your Music Helper</p>
      </div>

        <div className="chat-box">
    <div className="chat-message-area">
        <div className="chat-message">Add files here and begin your musical journey</div>
        <div className="import-label">+ Import File</div>
    </div>
    </div>

       
      <div className="chat-footer">
        <button className="back-button" onClick={() => nav('/')}>← Back</button>
         <button className="back-button" onClick={() => nav2('/Proceed')}> Proceed</button>
      </div>
    </div>
  );
};

export default ChatPage;