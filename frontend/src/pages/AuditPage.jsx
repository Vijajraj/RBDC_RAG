import { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import {
  ClipboardList,
  User,
  ShieldCheck,
  Search,
  Lock,
  ChevronDown,
  ChevronUp,
  Loader2,
  Calendar,
  AlertTriangle,
} from 'lucide-react'

export default function AuditPage() {
  const { token } = useAuth()
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(true)
  const [expandedId, setExpandedId] = useState(null)

  const API = import.meta.env.VITE_API_URL

  const fetchLogs = async () => {
    try {
      const res = await fetch(`${API}/audit/logs?limit=50`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      const data = await res.json()
      if (res.ok) {
        setLogs(data.logs || [])
      }
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchLogs()
  }, [token])

  const toggleExpand = (id) => {
    setExpandedId(expandedId === id ? null : id)
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-zinc-100">Access & Audit Logs</h1>
        <p className="text-zinc-500 text-sm mt-1">
          Monitor all retrieval queries, user context parameters, and active vector database filtrations.
        </p>
      </div>

      <div className="glass-card p-6 overflow-hidden">
        <div className="flex items-center gap-2.5 mb-6">
          <ClipboardList className="w-5 h-5 text-accent-400" />
          <h2 className="text-base font-semibold text-zinc-200">System Transaction Log</h2>
        </div>

        {loading ? (
          <div className="h-64 flex items-center justify-center text-zinc-500">
            <Loader2 className="w-6 h-6 animate-spin text-primary-400" />
          </div>
        ) : logs.length === 0 ? (
          <div className="h-64 flex flex-col items-center justify-center text-center text-zinc-600">
            <ClipboardList className="w-12 h-12 mb-3" />
            <p className="text-sm">No transaction audit logs found.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm border-collapse">
              <thead>
                <tr className="border-b border-white/5 text-zinc-500 font-medium">
                  <th className="py-3 px-4 w-10"></th>
                  <th className="py-3 px-4">User</th>
                  <th className="py-3 px-4">Role</th>
                  <th className="py-3 px-4">Query</th>
                  <th className="py-3 px-4 text-center">Retrieved</th>
                  <th className="py-3 px-4 text-center">Blocked</th>
                  <th className="py-3 px-4">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {logs.map((log) => {
                  const hasViolations = log.chunks_denied > 0
                  const isExpanded = expandedId === log.id

                  return (
                    <>
                      <tr
                        key={log.id}
                        onClick={() => toggleExpand(log.id)}
                        className={`cursor-pointer transition-colors ${
                          hasViolations ? 'bg-red-500/2 hover:bg-red-500/5' : 'hover:bg-white/2'
                        }`}
                      >
                        <td className="py-3.5 px-4 text-zinc-500 text-center">
                          {isExpanded ? (
                            <ChevronUp className="w-4 h-4 mx-auto" />
                          ) : (
                            <ChevronDown className="w-4 h-4 mx-auto" />
                          )}
                        </td>
                        <td className="py-3.5 px-4 font-medium text-zinc-200">
                          <div className="flex items-center gap-2">
                            <User className="w-3.5 h-3.5 text-zinc-600" />
                            <span className="truncate max-w-[120px]">{log.user_email}</span>
                          </div>
                        </td>
                        <td className="py-3.5 px-4">
                          <span className="badge badge-engineer uppercase font-bold text-[9px] px-2 py-0.5">
                            {log.user_role}
                          </span>
                        </td>
                        <td className="py-3.5 px-4 text-zinc-300 font-medium max-w-[200px] truncate">
                          "{log.query}"
                        </td>
                        <td className="py-3.5 px-4 text-center text-emerald-400 font-semibold">
                          {log.chunks_retrieved}
                        </td>
                        <td className="py-3.5 px-4 text-center">
                          {log.chunks_denied > 0 ? (
                            <span className="inline-flex items-center gap-1 text-red-400 font-semibold px-2 py-0.5 rounded bg-red-400/10 border border-red-500/10 text-xs">
                              <Lock className="w-3 h-3" />
                              {log.chunks_denied}
                            </span>
                          ) : (
                            <span className="text-zinc-500">0</span>
                          )}
                        </td>
                        <td className="py-3.5 px-4 text-zinc-500 text-xs">
                          <div className="flex items-center gap-1.5">
                            <Calendar className="w-3.5 h-3.5 text-zinc-600" />
                            {log.created_at ? new Date(log.created_at).toLocaleString() : 'N/A'}
                          </div>
                        </td>
                      </tr>

                      {/* Expanded Row Details */}
                      {isExpanded && (
                        <tr className={hasViolations ? 'bg-red-500/2' : 'bg-white/1'}>
                          <td colSpan={7} className="px-12 py-4 border-b border-white/5">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs text-zinc-400">
                              <div className="space-y-2">
                                <p className="font-bold text-[10px] text-zinc-500 uppercase tracking-wider">
                                  Full User Query
                                </p>
                                <p className="text-zinc-200 bg-zinc-950/20 p-3 rounded-xl border border-white/5 font-medium leading-relaxed">
                                  "{log.query}"
                                </p>
                              </div>
                              <div className="space-y-2">
                                <p className="font-bold text-[10px] text-zinc-500 uppercase tracking-wider">
                                  AI Response Preview
                                </p>
                                <p className="text-zinc-300 bg-zinc-950/20 p-3 rounded-xl border border-white/5 leading-relaxed">
                                  {log.response_preview ? `"${log.response_preview}..."` : 'No response preview saved.'}
                                </p>
                              </div>
                            </div>

                            {hasViolations && (
                              <div className="mt-4 glass-card-static p-3 border-red-500/20 bg-red-500/5 rounded-xl flex gap-2 items-center text-red-400">
                                <AlertTriangle className="w-4 h-4 shrink-0" />
                                <span className="font-medium text-[11px]">
                                  Security Warning: Vector retrieval flagged and blocked {log.chunks_denied} candidate document chunks from entering the model generation context.
                                </span>
                              </div>
                            )}
                          </td>
                        </tr>
                      )}
                    </>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
