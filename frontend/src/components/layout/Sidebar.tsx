import { NavLink } from 'react-router-dom'
import './Sidebar.css'

export default function Sidebar() {
  const navItems = [
    { path: '/dashboard', label: 'Dashboard' },
    { path: '/podcasts', label: 'Podcasts' },
    { path: '/episodes', label: 'Episodes' },
    { path: '/sync', label: 'Sync' },
    { path: '/storage', label: 'Storage' },
    { path: '/settings', label: 'Settings' },
  ]

  return (
    <aside className="sidebar">
      <nav className="sidebar-nav">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `nav-item ${isActive ? 'nav-item-active' : ''}`
            }
          >
            {item.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  )
}
