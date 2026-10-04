import { useEffect, useState } from 'react'
import './App.css'

const API_URL = 'http://127.0.0.1:8000/login'

const teamMembers = ['Alex Johnson', 'Priya Nair', 'Sam Torres', 'Jordan Lee']

const slides = [
  {
    title: 'Project Nova',
    text: 'A collaborative platform for tracking team goals, sharing progress, and staying aligned.',
  },
  {
    title: 'The Problem',
    text: 'Teams lose track of priorities across scattered docs, chats, and spreadsheets.',
  },
  {
    title: 'Our Approach',
    text: 'A single dashboard that pulls goals, updates, and files into one shared view.',
  },
  {
    title: 'Tech Stack',
    text: 'React frontend, FastAPI backend, with a simple login-gated upload workflow.',
  },
]

function Slideshow() {
  const [index, setIndex] = useState(0)

  useEffect(() => {
    const timer = setInterval(() => {
      setIndex((prev) => (prev + 1) % slides.length)
    }, 5000)
    return () => clearInterval(timer)
  }, [])

  const goTo = (i) => setIndex(i)
  const prev = () => setIndex((i) => (i - 1 + slides.length) % slides.length)
  const next = () => setIndex((i) => (i + 1) % slides.length)

  const slide = slides[index]

  return (
    <div className="slideshow">
      <button type="button" className="slide-arrow" onClick={prev} aria-label="Previous slide">
        ‹
      </button>

      <div className="slide-content">
        <h2 className="slide-title">{slide.title}</h2>
        <p className="slide-text">{slide.text}</p>
      </div>

      <button type="button" className="slide-arrow" onClick={next} aria-label="Next slide">
        ›
      </button>

      <div className="slide-dots">
        {slides.map((s, i) => (
          <button
            key={s.title}
            type="button"
            className={`slide-dot ${i === index ? 'active' : ''}`}
            onClick={() => goTo(i)}
            aria-label={`Go to slide ${i + 1}`}
          />
        ))}
      </div>
    </div>
  )
}

function LandingPage({ onGoToLogin }) {
  return (
    <div className="App">
      <div className="page-card">
        <div className="member-row">
          {teamMembers.map((name) => (
            <div className="member-box" key={name}>
              {name}
            </div>
          ))}
        </div>

        <div className="center-box">
          <Slideshow />
        </div>

        <button type="button" className="login-button" onClick={onGoToLogin}>
          Go to Login
        </button>
      </div>
    </div>
  )
}

function LoginPage({ onLoginSuccess, onBack }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleLogin = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      })
      const data = await response.json()

      if (data.success) {
        onLoginSuccess(username)
      } else {
        setError('Login incorrect. Please verify your username and password and try again.')
      }
    } catch {
      setError('Could not reach the server. Make sure the FastAPI backend is running.')
    } finally {
      setLoading(false)
      setPassword('')
    }
  }

  return (
    <div className="App">
      <div className="page-card narrow">
        <h1 className="project-name">Log In</h1>

        <form className="login-form" onSubmit={handleLogin}>
          <input
            type="text"
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          <button type="submit" className="login-button" disabled={loading}>
            {loading ? 'Checking...' : 'Login'}
          </button>
          {error && <p className="error-message">{error}</p>}
        </form>

        <button type="button" className="login-button secondary" onClick={onBack}>
          Back
        </button>
      </div>
    </div>
  )
}

function UploadPage({ username, onLogout }) {
  const [file, setFile] = useState(null)

  return (
    <div className="App">
      <div className="page-card narrow">
        <h1 className="project-name">File Upload</h1>
        <p className="project-description">Welcome, {username}. Choose a file to upload.</p>
        <input
          type="file"
          className="file-input"
          onChange={(e) => setFile(e.target.files[0])}
        />
        {file && <p className="file-name">Selected: {file.name}</p>}
        <button type="button" className="login-button secondary" onClick={onLogout}>
          Log out
        </button>
      </div>
    </div>
  )
}

function App() {
  const [view, setView] = useState('landing')
  const [loggedInUser, setLoggedInUser] = useState(null)

  const handleLoginSuccess = (username) => {
    setLoggedInUser(username)
    setView('upload')
  }

  const handleLogout = () => {
    setLoggedInUser(null)
    setView('landing')
  }

  if (view === 'login') {
    return <LoginPage onLoginSuccess={handleLoginSuccess} onBack={() => setView('landing')} />
  }

  if (view === 'upload' && loggedInUser) {
    return <UploadPage username={loggedInUser} onLogout={handleLogout} />
  }

  return <LandingPage onGoToLogin={() => setView('login')} />
}

export default App
