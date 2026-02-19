import { useState, useEffect, useRef } from 'react'
import '../App.css'
import ImageUpload from '../components/ImageUpload'
import { getMenu, chat, uploadFile } from '../services/api'

// API_URL is now handled in api.js, but we might need it for image URL
const API_BASE_URL = 'http://localhost:8000'

function CustomerPage() {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Hello! Welcome to our restaurant. How can I help you today?' }
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [menu, setMenu] = useState([])
  const [uploadedImage, setUploadedImage] = useState(null)
  const messagesEndRef = useRef(null)

  useEffect(() => {
    // Fetch menu on load
    getMenu()
      .then(data => {
        setMenu(data)
      })
      .catch(error => {
      // In a real app, you might want to log this to a service like Sentry
      console.error('Error fetching menu:', error)
      })
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  const handleImageUpload = async (file) => {
    try {
      const data = await uploadFile(file)
      // For development: log successful upload data
      console.log('Upload success:', data)
      setUploadedImage(data)

      // Optionally add a message to the chat
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `I received your image: ${data.original_filename}. Let me see what I can do with it.`
      }])
    } catch (error) {
      // For development: log image upload errors
      console.error('Error uploading image:', error)
      throw error // Re-throw so ImageUpload component handles the error state
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!input.trim()) return

    const userMessage = { role: 'user', content: input }
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      // Get store_id from URL
      const params = new URLSearchParams(window.location.search)
      const storeId = params.get('store_id')

      const botMessage = await chat([...messages, userMessage], storeId)
      setMessages(prev => [...prev, botMessage])
    } catch (error) {
      // For development: log chat message errors
      console.error('Error sending message:', error)
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.'
      }])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="container">
      <header>
        <h1>Restaurant AI Agent</h1>
      </header>

      <div className="main-content">

        <div className="menu-section">
          <h2>Menu</h2>
          <div className="menu-items">
            {menu.length === 0 ? (
              <p>Loading menu...</p>
            ) : (
              menu.map(item => (
                <div key={item.id} className="menu-item">
                  <div className="menu-item-content">
                    <div className="menu-header">
                      <h3>{item.name}</h3>
                      <span className="price">${item.price.toFixed(2)}</span>
                    </div>
                    <p>{item.description}</p>
                    <div className="tags">
                      {item.tags.map(tag => (
                        <span key={tag} className="tag">{tag}</span>
                      ))}
                    </div>
                  </div>
                  {item.imageUrl && (
                    <img
                      src={`${API_BASE_URL}${item.imageUrl}`}
                      alt={item.name}
                      className="menu-item-image"
                    />
                  )}
                </div>
              ))
            )}
          </div>
        </div>

        <div className="chat-section">
          <div className="messages">
            {messages.map((msg, index) => (
              <div key={index} className={`message ${msg.role}`}>
                <div className="message-content">
                  {msg.content}
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="message assistant">
                <div className="message-content">Thinking...</div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <ImageUpload onUpload={handleImageUpload} />

          <form onSubmit={handleSubmit} className="input-form">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about the menu..."
              disabled={isLoading}
            />
            <button type="submit" disabled={isLoading || !input.trim()}>
              Send
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}

export default CustomerPage
