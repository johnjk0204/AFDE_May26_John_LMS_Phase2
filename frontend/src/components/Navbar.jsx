import React from 'react'
import { NavLink } from 'react-router-dom'

const navItems = [
  { to: '/',             label: 'Dashboard'     },
  { to: '/books',        label: 'Books'         },
  { to: '/borrowers',    label: 'Borrowers'     },
  { to: '/transactions', label: 'Transactions'  },
  { to: '/analytics',    label: 'Analytics'     },
]

function Navbar() {
  return (
    <nav className="navbar">
      <NavLink to="/" className="navbar-brand">
        📚 Library MS
      </NavLink>
      <div className="navbar-links">
        {navItems.map(({ to, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              'nav-link' + (isActive ? ' active' : '')
            }
          >
            {label}
          </NavLink>
        ))}
      </div>
    </nav>
  )
}

export default Navbar
