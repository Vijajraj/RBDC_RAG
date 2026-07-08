import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { ShieldCheck, Mail, Lock, User, Loader2, Eye, EyeOff } from 'lucide-react'

const ROLES = ['engineer', 'manager', 'hr', 'legal', 'admin']
const DEPARTMENTS = ['engineering', 'hr', 'legal', 'admin']
const CLEARANCE_MAP = { engineer: 0, manager: 1, hr: 2, legal: 2, admin: 3 }

export default function LoginPage() {
  const { login, register } = useAuth()
  const navigate = useNavigate()

  const [isRegister, setIsRegister] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [shaking, setShaking] = useState(false)
  const [showPassword, setShowPassword] = useState(false)

  const [form, setForm] = useState({
    email: '',
    password: '',
    name: '',
    role: 'engineer',
    department: 'engineering',
  })

  const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }))

  const triggerError = (msg) => {
    setError(msg)
    setShaking(true)
    setTimeout(() => setShaking(false), 500)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      if (isRegister) {
        await register({
          name: form.name,
          email: form.email,
          password: form.password,
          role: form.role,
          department: form.department,
          clearance_level: CLEARANCE_MAP[form.role],
        })
      } else {
        await login(form.email, form.password)
      }
      navigate('/chat')
    } catch (err) {
      triggerError(err.message || 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen animated-gradient-bg flex items-center justify-center p-4 relative overflow-hidden">
      {/* Floating decorative orbs */}
      <div className="absolute top-1/4 left-1/4 w-72 h-72 bg-primary-500/10 rounded-full blur-3xl float-animation" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-accent-500/8 rounded-full blur-3xl float-animation-delayed" />
      <div className="absolute top-1/2 right-1/3 w-64 h-64 bg-primary-700/10 rounded-full blur-3xl float-animation-slow" />

      <div
        className={`w-full max-w-md relative z-10 animate-slide-up ${shaking ? 'animate-shake' : ''}`}
      >
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-primary-500/20 mb-4 animate-pulse-glow">
            <ShieldCheck className="w-9 h-9 text-primary-400" />
          </div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-primary-300 to-accent-400 bg-clip-text text-transparent">
            SecureRAG
          </h1>
          <p className="text-zinc-500 mt-2 text-sm">
            Role-Based Access Control for Retrieval-Augmented Generation
          </p>
        </div>

        {/* Form Card */}
        <div className="glass-card p-8">
          <h2 className="text-xl font-semibold text-zinc-100 mb-6">
            {isRegister ? 'Create Account' : 'Welcome Back'}
          </h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            {isRegister && (
              <div className="relative">
                <User className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
                <input
                  type="text"
                  placeholder="Full Name"
                  value={form.name}
                  onChange={set('name')}
                  className="input-field pl-11"
                  required
                />
              </div>
            )}

            <div className="relative">
              <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
              <input
                type="email"
                placeholder="Email Address"
                value={form.email}
                onChange={set('email')}
                className="input-field pl-11"
                required
              />
            </div>

            <div className="relative">
              <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
              <input
                type={showPassword ? 'text' : 'password'}
                placeholder="Password"
                value={form.password}
                onChange={set('password')}
                className="input-field pl-11 pr-11"
                required
                minLength={6}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-4 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-zinc-300 transition-colors"
              >
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>

            {isRegister && (
              <>
                <div>
                  <label className="block text-xs text-zinc-500 mb-1.5 font-medium uppercase tracking-wider">
                    Role
                  </label>
                  <select
                    value={form.role}
                    onChange={set('role')}
                    className="input-field appearance-none cursor-pointer"
                  >
                    {ROLES.map((r) => (
                      <option key={r} value={r} className="bg-zinc-900">
                        {r.charAt(0).toUpperCase() + r.slice(1)}
                        {' '}
                        — Clearance {CLEARANCE_MAP[r]}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs text-zinc-500 mb-1.5 font-medium uppercase tracking-wider">
                    Department
                  </label>
                  <select
                    value={form.department}
                    onChange={set('department')}
                    className="input-field appearance-none cursor-pointer"
                  >
                    {DEPARTMENTS.map((d) => (
                      <option key={d} value={d} className="bg-zinc-900">
                        {d.charAt(0).toUpperCase() + d.slice(1)}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="glass-card-static p-3 flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-primary-500/20 flex items-center justify-center shrink-0">
                    <span className="text-lg font-bold text-primary-300">
                      {CLEARANCE_MAP[form.role]}
                    </span>
                  </div>
                  <div>
                    <p className="text-xs text-zinc-500 uppercase tracking-wider">Clearance Level</p>
                    <p className="text-sm font-medium text-zinc-200">
                      {['Public', 'Internal', 'Confidential', 'Restricted'][CLEARANCE_MAP[form.role]]}
                    </p>
                  </div>
                </div>
              </>
            )}

            {error && (
              <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-3 text-red-400 text-sm">
                {error}
              </div>
            )}

            <button type="submit" disabled={loading} className="btn-primary w-full flex items-center justify-center gap-2">
              {loading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  {isRegister ? 'Creating Account...' : 'Signing In...'}
                </>
              ) : (
                isRegister ? 'Create Account' : 'Sign In'
              )}
            </button>
          </form>

          <div className="mt-6 text-center">
            <button
              onClick={() => {
                setIsRegister(!isRegister)
                setError('')
              }}
              className="text-sm text-zinc-500 hover:text-primary-400 transition-colors"
            >
              {isRegister
                ? 'Already have an account? Sign in'
                : "Don't have an account? Create one"}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
