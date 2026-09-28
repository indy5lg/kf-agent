import { useState } from 'react'
import './App.css'

const API_URL = 'http://127.0.0.1:8000/login'
const teamMembers = ['Keaton Surfield', 'Santiago Acosta Rodriguez', 'Andres Ferrer', 'Elvin Pineda']

function UploadPage({ username, onLogout }) {
  const [file, setFile] = useState(null)

  return (
    <div className="App">
      <div className="landing-card">
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
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [loggedInUser, setLoggedInUser] = useState(null)

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
        setLoggedInUser(username)
        setPassword('')
      } else {
        setError('Login incorrect. Please verify your username and password and try again. :)')
      }
    } catch {
      setError('Could not reach the server. Make sure the FastAPI backend is running. =)')
    } finally {
      setLoading(false)
    }
  }

  const handleLogout = () => {
    setLoggedInUser(null)
    setUsername('')
  }

  if (loggedInUser) {
    return <UploadPage username={loggedInUser} onLogout={handleLogout} />
  }

  return (
    <div className="App">
      <div className="landing-card">
        <h1 className="project-name">Indy-5-LangGraph</h1>
        <p className="project-description">
          A showcase of our Senior Project from Kennesaw State University.
        </p>

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

        <div className="team-section">
          <p className="team-label">Team members</p>
          <div className="team-list">
            {teamMembers.map((name) => (
              <span className="team-badge" key={name}>{name}</span>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
