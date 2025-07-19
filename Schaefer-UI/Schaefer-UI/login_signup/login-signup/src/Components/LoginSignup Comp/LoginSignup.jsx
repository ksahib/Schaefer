import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import './LoginSignup.css'

import user_icon from '../Assets/person.png'
import email_icon from '../Assets/email.png'
import password_icon from '../Assets/password.png'

const LoginSignup = () => {

  const[action,SetAction]= useState("Sign Up");

  const navigate= useNavigate()
  
  return (
    <div className = 'container'> 
        <div className ="header">
             <div className="text">{action}</div>
            <div className='underline'></div>
        </div>

        <div className='inputs'>
            <div className='input'>
                <img src={user_icon} alt="" />
                <input type="text" placeholder='Name' />
            </div>

            <div className='input'>
                <img src={email_icon} alt="" />
                <input type="email" placeholder='Email' />
            </div>

            <div className='input'>
                <img src={password_icon} alt="" />
                <input type="password" placeholder='Password' />
            </div>
        </div>

          <div className='submit-container'>
            <div className={action==='Log In'?'submit gray':'submit'} onClick={()=>{SetAction("Sign Up")}}>Sign Up</div>
             <div className={action==='Sign Up'?'submit gray':'submit'} onClick={()=>{SetAction("Log In")}}>Log In</div>
          </div>

          <button className="submitbutton" onClick={() => navigate('/Submit')} >Submit</button>
          
    </div>
  )
}

export default LoginSignup