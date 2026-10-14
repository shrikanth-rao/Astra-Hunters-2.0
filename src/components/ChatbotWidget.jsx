
// import { useState } from "react";
// import { Bot, X, Send, Sparkles } from "lucide-react";
// import "./chatbot.css";

// export default function ChatbotWidget() {
//   const [open, setOpen] = useState(false);
//   const [input, setInput] = useState("");
//   const [messages, setMessages] = useState([
//     {
//       role: "assistant",
//       text: "Hi! I'm your SpeakKaro.AI assistant. Ask me about speech analysis, speaking pace, filler words or improving your presentation.",
//     },
//   ]);

//   function sendMessage(event) {
//     event.preventDefault();

//     const question = input.trim();
//     if (!question) return;

//     setMessages((previous) => [
//       ...previous,
//       { role: "user", text: question },
//       {
//         role: "assistant",
//         text: "I'm currently in demo mode. Once connected to an AI service, I'll be able to answer your question about public speaking in more detail.",
//       },
//     ]);

//     setInput("");
//   }

//   return (
//     <div className="speech-assistant">
//       {open && (
//         <section
//           className="assistant-panel"
//           aria-label="SpeakKaro AI chat"
//         >
//           <header className="assistant-header">
//             <div className="assistant-heading-icon">
//               <Sparkles size={19} />
//             </div>
//             <div className="assistant-heading-text">
//               <strong>SpeakKaro Assistant</strong>
//               <span>Speech coaching companion</span>
//             </div>
//             <button
//               className="assistant-close"
//               onClick={() => setOpen(false)}
//               aria-label="Close chat"
//             >
//               <X size={19} />
//             </button>
//           </header>

//           <div className="assistant-messages" aria-live="polite">
//             {messages.map((message, index) => (
//               <div
//                 key={index}
//                 className={`assistant-message ${message.role}`}
//               >
//                 {message.text}
//               </div>
//             ))}
//           </div>

//           <form className="assistant-input-row" onSubmit={sendMessage}>
//             <input
//               value={input}
//               onChange={(event) => setInput(event.target.value)}
//               placeholder="Ask about your speech..."
//               aria-label="Your message"
//             />
//             <button type="submit" aria-label="Send message">
//               <Send size={17} />
//             </button>
//           </form>
//         </section>
//       )}

//       <button
//         className={`assistant-orb ${open ? "orb-active" : ""}`}
//         onClick={() => setOpen((previous) => !previous)}
//         aria-label={open ? "Close AI assistant" : "Open AI assistant"}
//         aria-expanded={open}
//       >
//         <span className="orb-halo" />
//         <span className="orb-shine" />
//         <span className="orb-inner">
//           {open ? <X size={29} /> : <Bot size={31} />}
//         </span>
//         {!open && <span className="orb-sparkle"><Sparkles size={14} /></span>}
//       </button>
//     </div>
//   );
// }


import React, { useState } from 'react';
import { X, Send, AudioLines, Sparkles } from 'lucide-react';
import './chatbot.css';

export default function ChatbotWidget() {
  const [open, setOpen] = useState(false);
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState([{ role: 'bot', text: 'Hi! I’m your SpeakKaro AI assistant. How can I help you today?' }]);
  const send = (e) => {
    e?.preventDefault();
    const value = message.trim();
    if (!value) return;
    setMessages((prev) => [...prev, { role: 'user', text: value }, { role: 'bot', text: 'I can help you prepare for a speech, understand speaking metrics, or plan a practice session. Live AI replies can be connected to your backend next.' }]);
    setMessage('');
  };
  return <div className="sk-chatbot-root">
    {open && <section className="sk-chat-panel" aria-label="SpeakKaro AI chat">
      <header className="sk-chat-head"><span className="sk-chat-mini-orb"><AudioLines size={20}/></span><div><b>SpeakKaro AI</b><small><i/> Your speaking companion</small></div><button onClick={() => setOpen(false)} aria-label="Close chat"><X size={19}/></button></header>
      <div className="sk-chat-messages">{messages.map((item, i) => <div className={`sk-chat-message ${item.role}`} key={i}>{item.text}</div>)}</div>
      <form className="sk-chat-form" onSubmit={send}><input value={message} onChange={(e) => setMessage(e.target.value)} placeholder="Ask me anything..." aria-label="Message"/><button aria-label="Send message" type="submit"><Send size={17}/></button></form>
    </section>}
    {!open && <div className="sk-chat-hint">How can I help you today?</div>}
    <button className={`sk-chat-orb-button ${open ? 'opened' : ''}`} onClick={() => setOpen((v) => !v)} aria-label={open ? 'Close AI assistant' : 'Open AI assistant'}>
      <span className="sk-chat-orb-halo"/><span className="sk-chat-orb-body"><span className="sk-chat-orb-glass"/><span className="sk-chat-eye left"/><span className="sk-chat-eye right"/><span className="sk-chat-smile"/><span className="sk-chat-ear left"/><span className="sk-chat-ear right"/><span className="sk-chat-orb-shine"/><span className="sk-chat-spark"><Sparkles size={12}/></span></span>
    </button>
  </div>;
}
