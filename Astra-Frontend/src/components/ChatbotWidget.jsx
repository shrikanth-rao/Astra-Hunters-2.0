import React, { useState, useEffect, useRef } from 'react';
import { X, AudioLines, Sparkles } from 'lucide-react';
import './chatbot.css';

const QA_OPTIONS = [
  {
    q: "How does the AI grade my speech?",
    a: "Our ML pipeline analyzes your video and audio locally. It calculates Delivery, Vocal Expression, and Body Language scores based on metrics like speaking pace (WPM), pitch variance, posture, and filler words."
  },
  {
    q: "How do you evaluate my body language?",
    a: "We use advanced vision models to track your posture and gestures frame-by-frame. We look for open body language, stability, and natural movement rather than stiffness, slouching, or excessive pacing."
  },
  {
    q: "What does 'Pitch Variance' mean?",
    a: "Pitch variance measures the expressiveness in your voice. A higher variance means you are using vocal variety to keep the audience engaged, while a low score might indicate a monotone delivery."
  },
  {
    q: "Does the AI analyze the actual words I say?",
    a: "Yes! We transcribe your speech and pass your performance metrics to an advanced LLM (Groq). It evaluates your content and generates a personalized coaching report with specific, actionable feedback."
  },
  {
    q: "Can the system detect my accent?",
    a: "Yes, our audio pipeline includes an accent classification model. However, your delivery score is based on clarity, pacing, and expression—not on having a specific accent."
  },
  {
    q: "How can I reduce filler words?",
    a: "Awareness is step one! Our AI detects words like 'um' and 'uh'. To reduce them, practice embracing silence. A short pause is much more powerful than filling the space with sound."
  },
  {
    q: "How long does the analysis take?",
    a: "Processing a video takes about 60 seconds depending on the file size and your computer's hardware. We extract audio, track video frames, and run the data through our machine learning models all locally."
  }
];

export default function ChatbotWidget() {
  const [open, setOpen] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [messages, setMessages] = useState([
    { role: 'bot', text: 'Hi! I’m your SpeakKaro AI assistant. Choose a question below to learn more about how we analyze your presentations.' }
  ]);
  
  const messagesEndRef = useRef(null);

  // Auto-scroll to bottom whenever messages or typing state changes
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, isTyping]);

  const handleOptionClick = (question, answer) => {
    // 1. Immediately append the user's question
    setMessages((prev) => [...prev, { role: 'user', text: question }]);
    
    // 2. Trigger the typing indicator and disable buttons
    setIsTyping(true);

    // 3. Wait 1.5 seconds, then remove typing indicator and show the answer
    setTimeout(() => {
      setMessages((prev) => [...prev, { role: 'bot', text: answer }]);
      setIsTyping(false);
    }, 1500); 
  };

  return (
    <div className="sk-chatbot-root">
      {open && (
        <section className="sk-chat-panel" aria-label="SpeakKaro AI chat">
          <header className="sk-chat-head">
            <span className="sk-chat-mini-orb"><AudioLines size={20}/></span>
            <div>
              <b>SpeakKaro AI</b>
              <small><i/> Your speaking companion</small>
            </div>
            <button onClick={() => setOpen(false)} aria-label="Close chat">
              <X size={19}/>
            </button>
          </header>
          
          <div className="sk-chat-messages">
            {messages.map((item, i) => (
              <div className={`sk-chat-message ${item.role}`} key={i}>
                {item.text}
              </div>
            ))}
            
            {/* Conditional render for the animated typing indicator */}
            {isTyping && (
              <div className="sk-chat-message bot typing-indicator">
                <span className="dot"></span>
                <span className="dot"></span>
                <span className="dot"></span>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>
          
          <div className="sk-chat-options">
            {QA_OPTIONS.map((option, i) => (
              <button 
                key={i} 
                className="sk-chat-option-btn"
                onClick={() => handleOptionClick(option.q, option.a)}
                disabled={isTyping} // Prevent spamming while bot is typing
                style={{ opacity: isTyping ? 0.6 : 1, cursor: isTyping ? 'not-allowed' : 'pointer' }}
              >
                {option.q}
              </button>
            ))}
          </div>
        </section>
      )}
      
      {!open && <div className="sk-chat-hint">How can I help you today?</div>}
      
      {/* The new wrapper div that handles the floating animation safely */}
      <div className={`sk-orb-floater ${open ? 'paused' : ''}`}>
        <button 
          className={`sk-chat-orb-button ${open ? 'opened' : ''}`} 
          onClick={() => setOpen((v) => !v)} 
          aria-label={open ? 'Close AI assistant' : 'Open AI assistant'}
        >
          <span className="sk-chat-orb-halo"/>
          <span className="sk-chat-orb-body">
            <span className="sk-chat-orb-glass"/>
            <span className="sk-chat-eye left"/>
            <span className="sk-chat-eye right"/>
            <span className="sk-chat-smile"/>
            <span className="sk-chat-ear left"/>
            <span className="sk-chat-ear right"/>
            <span className="sk-chat-orb-shine"/>
            <span className="sk-chat-spark"><Sparkles size={12}/></span>
          </span>
        </button>
      </div>
    </div>
  );
}