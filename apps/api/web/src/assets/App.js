import './App.css';

function App() {
  const teamMembers = ["Alex Johnson", "Priya Nair", "Sam Torres", "Jordan Lee"];

  return (
    <div className="App">
      <div className="landing-card">
        <h1 className="project-name">Project Nova</h1>
        <p className="project-description">
          A collaborative platform for tracking team goals, sharing progress,
          and staying aligned — built as our capstone project.
        </p>
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
  );
}

export default App;