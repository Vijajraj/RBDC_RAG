import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import {
  ShieldCheck,
  MessageSquare,
  FileText,
  ClipboardList,
  LogOut,
  Menu,
  X,
} from 'lucide-react'

const roleBadgeClass = {
  engineer: 'badge-engineer',
  manager: 'badge-manager',
  hr: 'badge-hr',
  legal: 'badge-legal',
  admin: 'badge-admin',
}

export default function Navbar() {
  const { user, isAdmin, logout } = useAuth()
  const location = useLocation()
  const [mobileOpen, setMobileOpen] = useState(false)

  const links = [
    { to: '/chat', label: 'Chat', icon: MessageSquare },
    ...(isAdmin
      ? [
          { to: '/documents', label: 'Documents', icon: FileText },
          { to: '/audit', label: 'Audit', icon: ClipboardList },
        ]
      : []),
  ]

  const isActive = (path) => location.pathname === path

  return (
    <nav className="glass-nav sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/chat" className="flex items-center gap-2 group">
            <div className="relative">
              <ShieldCheck className="w-8 h-8 text-primary-400 transition-transform group-hover:scale-110" />
              <div className="absolute inset-0 bg-primary-400/20 rounded-full blur-lg opacity-0 group-hover:opacity-100 transition-opacity" />
            </div>
            <span className="text-xl font-bold bg-gradient-to-r from-primary-300 to-accent-400 bg-clip-text text-transparent">
              SecureRAG
            </span>
          </Link>

          {/* Desktop Nav Links */}
          <div className="hidden md:flex items-center gap-1">
            {links.map((link) => {
              const Icon = link.icon
              return (
                <Link
                  key={link.to}
                  to={link.to}
                  className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200 ${
                    isActive(link.to)
                      ? 'bg-primary-500/20 text-primary-300 shadow-lg shadow-primary-500/10'
                      : 'text-zinc-400 hover:text-zinc-200 hover:bg-white/5'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  {link.label}
                </Link>
              )
            })}
          </div>

          {/* User Info + Logout */}
          <div className="hidden md:flex items-center gap-3">
            {user && (
              <>
                <div className="text-right">
                  <p className="text-sm font-medium text-zinc-200">{user.name}</p>
                  <span className={`badge ${roleBadgeClass[user.role] || 'badge-engineer'}`}>
                    {user.role}
                  </span>
                </div>
                <button
                  onClick={logout}
                  className="p-2 rounded-xl text-zinc-400 hover:text-red-400 hover:bg-red-400/10 transition-all duration-200"
                  title="Logout"
                >
                  <LogOut className="w-5 h-5" />
                </button>
              </>
            )}
          </div>

          {/* Mobile Menu Button */}
          <button
            className="md:hidden p-2 rounded-xl text-zinc-400 hover:text-zinc-200 hover:bg-white/5 transition-all"
            onClick={() => setMobileOpen(!mobileOpen)}
          >
            {mobileOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
      </div>

      {/* Mobile Menu */}
      {mobileOpen && (
        <div className="md:hidden border-t border-white/5 animate-fade-in">
          <div className="px-4 py-3 space-y-1">
            {links.map((link) => {
              const Icon = link.icon
              return (
                <Link
                  key={link.to}
                  to={link.to}
                  onClick={() => setMobileOpen(false)}
                  className={`flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all ${
                    isActive(link.to)
                      ? 'bg-primary-500/20 text-primary-300'
                      : 'text-zinc-400 hover:text-zinc-200 hover:bg-white/5'
                  }`}
                >
                  <Icon className="w-5 h-5" />
                  {link.label}
                </Link>
              )
            })}
            {user && (
              <div className="flex items-center justify-between pt-3 mt-2 border-t border-white/5">
                <div className="flex items-center gap-2">
                  <p className="text-sm font-medium text-zinc-200">{user.name}</p>
                  <span className={`badge ${roleBadgeClass[user.role] || 'badge-engineer'}`}>
                    {user.role}
                  </span>
                </div>
                <button
                  onClick={logout}
                  className="p-2 rounded-xl text-zinc-400 hover:text-red-400 hover:bg-red-400/10 transition-all"
                >
                  <LogOut className="w-5 h-5" />
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </nav>
  )
}
