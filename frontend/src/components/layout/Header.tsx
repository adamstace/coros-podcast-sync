import './Header.css'

export default function Header() {
  return (
    <header className="header">
      <div className="header-content">
        <h1 className="header-title">Coros Podcast Sync</h1>
        <div className="header-status">
          <span className="status-indicator"></span>
          <span className="status-text">Ready</span>
        </div>
      </div>
    </header>
  )
}
