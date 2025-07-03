import { BrowserRouter,Routes,Route } from 'react-router-dom';
import logo from './logo.svg';
import './App.css';
import LoginSignup from './Components/LoginSignup Comp/LoginSignup';
import ChatPage from './Components/ChatPage/ChatPage';
import Botpage from './Components/Botpage/Botpage';



function App() {
  return(
    /*<div>
      <LoginSignup/>
      <ChatPage/>
    </div> */

    <BrowserRouter>
      <Routes>
         <Route path="/" element={<LoginSignup />} />     
        <Route path="/Submit" element={<ChatPage />} /> 
        <Route path="/Proceed" element={<Botpage />} /> 
         <Route path="/Home" element={<ChatPage />} /> 
      </Routes>

    
    </BrowserRouter>


  );
}

export default App;
