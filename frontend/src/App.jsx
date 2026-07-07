// frontend/src/App.jsx
import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { Send, Paperclip, Brain, User, Loader2, FileText, Trash2 } from 'lucide-react';
import './App.css';

function App() {
  const [sessionId, setSessionId] = useState(() => Math.random().toString(36).substring(7));
  const [files, setFiles] = useState([]);
  const [uploadStatus, setUploadStatus] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [isClearing, setIsClearing] = useState(false);

  const initialMessage = { role: 'bot', content: "Hello! I am connected to **Qwen 2.5**. Upload some documents on the left, then ask me anything about them." };
  const [messages, setMessages] = useState([initialMessage]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleFileChange = (e) => {
    setFiles(Array.from(e.target.files));
    setUploadStatus('');
  };

  const handleUpload = async () => {
    if (files.length === 0) return;
    setIsUploading(true);
    setUploadStatus('Processing documents...');

    const formData = new FormData();
    files.forEach(file => formData.append('files', file));

    try {
      const response = await fetch('http://127.0.0.1:8000/upload', {
        method: 'POST',
        body: formData,
      });
      
      const data = await response.json();
      if (response.ok) {
        setUploadStatus(`Success! Ready to chat.`);
        setFiles([]); 
      } else {
        setUploadStatus(`Error: ${data.detail || 'Upload failed'}`);
      }
    } catch (error) {
      setUploadStatus(`Connection error: ${error.message}`);
    } finally {
      setIsUploading(false);
    }
  };

  // NEW: Function to clear the database
  const handleClear = async () => {
    if (!window.confirm("Are you sure you want to delete all uploaded documents and reset the chat?")) return;
    
    setIsClearing(true);
    setUploadStatus('Clearing database...');

    try {
      const response = await fetch('http://127.0.0.1:8000/clear', {
        method: 'DELETE',
      });
      
      const data = await response.json();
      if (response.ok) {
        setUploadStatus(data.message);
        setMessages([initialMessage]); // Reset chat UI
        setSessionId(Math.random().toString(36).substring(7)); // Generate new session ID
      } else {
        setUploadStatus(`Error: ${data.detail}`);
      }
    } catch (error) {
      setUploadStatus(`Connection error: ${error.message}`);
    } finally {
      setIsClearing(false);
    }
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMsg = { role: 'user', content: input };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsTyping(true);

    try {
      const response = await fetch('http://127.0.0.1:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: userMsg.content, session_id: sessionId }),
      });

      const data = await response.json();
      
      if (response.ok) {
        setMessages(prev => [...prev, { role: 'bot', content: data.answer }]);
      } else {
        setMessages(prev => [...prev, { role: 'bot', content: `Error: ${data.detail}` }]);
      }
    } catch (error) {
      setMessages(prev => [...prev, { role: 'bot', content: `Connection error: ${error.message}` }]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className="app-container">
      {/* --- SIDEBAR --- */}
      <div className="sidebar">
        <div className="sidebar-header">
          <h2>Knowledge Base</h2>
          <p>Local AI Agent Interface</p>
        </div>
        
        <div className="upload-box">
          <input 
  type="file" 
  id="file-upload"
  multiple 
  accept=".pdf,.txt,.png,.jpg,.jpeg" // Updated line
  onChange={handleFileChange} 
  className="file-input"
/>
<label htmlFor="file-upload" className="file-label">
       <Paperclip size={24} />
         <span>Select PDFs, TXTs, or Images</span> {/* Updated line */}
     {files.length > 0 && <b style={{color: '#3b82f6'}}>{files.length} file(s) selected</b>}
        </label>
        </div>
        
        <button 
          onClick={handleUpload} 
          disabled={files.length === 0 || isUploading || isClearing}
          className="upload-btn"
        >
          {isUploading ? <Loader2 className="spin" size={20} /> : <FileText size={20} />}
          {isUploading ? 'Embedding...' : 'Upload & Embed'}
        </button>

        {/* NEW: Clear Database Button */}
        <button 
          onClick={handleClear} 
          disabled={isUploading || isClearing}
          className="upload-btn"
          style={{ backgroundColor: '#ef4444', marginTop: 'auto' }} // Red button pushed to the bottom
        >
          {isClearing ? <Loader2 className="spin" size={20} /> : <Trash2 size={20} />}
          {isClearing ? 'Clearing...' : 'Clear Database'}
        </button>

        {uploadStatus && (
          <div className={`status-msg ${uploadStatus.includes('Error') ? 'error' : ''}`}>
            {uploadStatus}
          </div>
        )}
      </div>

      {/* --- CHAT AREA --- */}
      <div className="chat-area">
        <div className="messages-container">
          {messages.map((msg, index) => (
            <div key={index} className={`message-wrapper ${msg.role}`}>
              <div className={`avatar ${msg.role}`}>
                {msg.role === 'bot' ? <Brain size={20} /> : <User size={20} />}
              </div>
              <div className={`message ${msg.role}`}>
                {msg.role === 'bot' ? (
                  <ReactMarkdown>{msg.content}</ReactMarkdown>
                ) : (
                  msg.content
                )}
              </div>
            </div>
          ))}
          
          {isTyping && (
            <div className="message-wrapper bot">
              <div className="avatar bot"><Brain size={20} /></div>
              <div className="message bot" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Loader2 className="spin" size={16} /> Thinking...
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* --- INPUT AREA --- */}
        <div className="input-container">
          <form onSubmit={handleSendMessage} className="input-box">
            <input 
              type="text" 
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask a question about your documents..."
              disabled={isTyping}
            />
            <button type="submit" className="send-btn" disabled={isTyping || !input.trim()}>
              <Send size={18} />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

export default App;