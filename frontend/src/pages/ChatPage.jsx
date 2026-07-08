import { useState, useRef, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import {
  Send,
  ShieldAlert,
  ShieldCheck,
  FileKey2,
  FileCheck2,
  Lock,
  ChevronRight,
  Database,
  Cpu,
  BrainCircuit,
  MessageSquare,
  Sparkles,
} from 'lucide-react'

const sensitivityLabels = ['Public', 'Internal', 'Confidential', 'Restricted']
const sensitivityColors = [
  'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  'bg-sky-500/10 text-sky-400 border-sky-500/20',
  'bg-amber-500/10 text-amber-400 border-amber-500/20',
  'bg-red-500/10 text-red-400 border-red-500/20',
]

export default function ChatPage() {
  const { token, user } = useAuth()
  const [messages, setMessages] = useState([])
  const [question, setQuestion] = useState('')
  const [loading, setLoading] = useState(false)
  const [latestTrace, setLatestTrace] = useState(null)

  const messagesEndRef = useRef(null)
  const API = import.meta.env.VITE_API_URL

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, loading])

  const handleSend = async (e) => {
    e.preventDefault()
    if (!question.trim() || loading) return

    const queryText = question.trim()
    setQuestion('')
    setLoading(true)

    // Add user message immediately
    setMessages((prev) => [...prev, { role: 'user', content: queryText }])

    try {
      const res = await fetch(`${API}/chat/ask`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ question: queryText }),
      })

      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Failed to get answer')

      // Add AI message with trace data
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: data.answer,
          trace: {
            chunksRetrieved: data.chunks_retrieved,
            chunksDeniedCount: data.chunks_denied_count,
            totalChunksFound: data.total_chunks_found,
          },
        },
      ])
      setLatestTrace({
        query: queryText,
        chunksRetrieved: data.chunks_retrieved,
        chunksDeniedCount: data.chunks_denied_count,
        totalChunksFound: data.total_chunks_found,
      })
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: `Error: ${err.message || 'Unable to connect to the model service.'}`,
          isError: true,
        },
      ])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 h-[calc(100vh-4rem)] flex gap-6 overflow-hidden">
      {/* Left Panel: Chat Interface */}
      <div className="flex-1 flex flex-col glass-card h-full overflow-hidden relative">
        {/* Chat Header */}
        <div className="px-6 py-4 border-b border-white/5 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-primary-500/10 text-primary-400">
              <BrainCircuit className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-zinc-100">Secure RAG Chat Session</h2>
              <p className="text-xs text-zinc-500 flex items-center gap-1.5 mt-0.5">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                Active clearance: Level {user?.clearance_level} ({user?.department} dept)
              </p>
            </div>
          </div>
        </div>

        {/* Message Panel */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center max-w-md mx-auto">
              <div className="w-12 h-12 rounded-2xl bg-zinc-900 flex items-center justify-center mb-4 text-zinc-600 animate-pulse-glow">
                <MessageSquare className="w-6 h-6" />
              </div>
              <h3 className="text-base font-semibold text-zinc-200">Start a secure conversation</h3>
              <p className="text-sm text-zinc-500 mt-2">
                Ask questions regarding engineering guidelines, compensation plans, contracts, or finances. Chunks will be filtered in real-time according to your role.
              </p>
            </div>
          ) : (
            messages.map((msg, idx) => (
              <div
                key={idx}
                className={`flex gap-4 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {msg.role === 'assistant' && (
                  <div className="w-9 h-9 rounded-xl bg-primary-500/10 border border-primary-500/20 flex items-center justify-center text-primary-400 shrink-0">
                    <Sparkles className="w-4 h-4" />
                  </div>
                )}
                <div
                  className={`max-w-[75%] rounded-2xl p-4 text-sm leading-relaxed ${
                    msg.role === 'user'
                      ? 'bg-primary-600 text-white font-medium shadow-lg shadow-primary-500/10'
                      : msg.isError
                      ? 'bg-red-500/10 border border-red-500/20 text-red-400'
                      : 'bg-white/5 border border-white/5 text-zinc-300'
                  }`}
                >
                  <p className="whitespace-pre-wrap">{msg.content}</p>

                  {/* Inline trace shortcut for mobile / small views */}
                  {msg.trace && (
                    <button
                      onClick={() => setLatestTrace({ ...msg.trace, query: messages[idx - 1]?.content })}
                      className="mt-3 flex items-center gap-1.5 text-xs text-primary-400 hover:text-primary-300 transition-colors font-medium border-t border-white/5 pt-2 w-full"
                    >
                      <ChevronRight className="w-3.5 h-3.5" />
                      View Access Trace ({msg.trace.chunksRetrieved.length} allowed, {msg.trace.chunksDeniedCount} denied)
                    </button>
                  )}
                </div>
              </div>
            ))
          )}

          {loading && (
            <div className="flex gap-4 justify-start">
              <div className="w-9 h-9 rounded-xl bg-primary-500/10 border border-primary-500/20 flex items-center justify-center text-primary-400 shrink-0 animate-spin-slow">
                <BrainCircuit className="w-4 h-4" />
              </div>
              <div className="bg-white/5 border border-white/5 text-zinc-400 rounded-2xl p-4 text-sm flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-zinc-400 animate-bounce [animation-delay:-0.3s]" />
                <span className="w-1.5 h-1.5 rounded-full bg-zinc-400 animate-bounce [animation-delay:-0.15s]" />
                <span className="w-1.5 h-1.5 rounded-full bg-zinc-400 animate-bounce" />
                Thinking & retrieving chunks...
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Query Input */}
        <form onSubmit={handleSend} className="p-4 border-t border-white/5 flex gap-3 bg-zinc-950/20">
          <input
            type="text"
            placeholder="Ask a question..."
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            className="input-field flex-1"
            disabled={loading}
          />
          <button type="submit" disabled={loading} className="btn-primary flex items-center justify-center p-3 shrink-0">
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>

      {/* Right Panel: Access Trace View */}
      <div className="w-80 glass-card h-full flex flex-col overflow-hidden shrink-0 hidden lg:flex">
        <div className="px-6 py-4 border-b border-white/5 flex items-center gap-2.5">
          <Database className="w-5 h-5 text-accent-400" />
          <h3 className="text-sm font-semibold text-zinc-200">Real-Time Access Trace</h3>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {!latestTrace ? (
            <div className="h-full flex flex-col items-center justify-center text-center text-zinc-600 px-4">
              <FileKey2 className="w-10 h-10 mb-3" />
              <p className="text-xs">
                Submit a query to inspect the vector retrieval logs and active RBAC filtration policies.
              </p>
            </div>
          ) : (
            <div className="space-y-4 animate-fade-in">
              {/* Query block */}
              <div className="glass-card-static p-3 space-y-1">
                <p className="text-[10px] text-zinc-500 font-bold uppercase tracking-wider">Query</p>
                <p className="text-xs text-zinc-300 font-medium line-clamp-2">"{latestTrace.query}"</p>
              </div>

              {/* Status summary */}
              <div className="grid grid-cols-2 gap-2">
                <div className="glass-card-static p-3 text-center border-emerald-500/20 bg-emerald-500/5">
                  <span className="text-lg font-bold text-emerald-400">
                    {latestTrace.chunksRetrieved.length}
                  </span>
                  <p className="text-[10px] text-zinc-400 font-medium mt-0.5">Retrieved</p>
                </div>
                <div className={`glass-card-static p-3 text-center transition-all ${
                  latestTrace.chunksDeniedCount > 0
                    ? 'border-red-500/20 bg-red-500/5'
                    : 'border-zinc-800'
                }`}>
                  <span className={`text-lg font-bold ${
                    latestTrace.chunksDeniedCount > 0 ? 'text-red-400' : 'text-zinc-500'
                  }`}>
                    {latestTrace.chunksDeniedCount}
                  </span>
                  <p className="text-[10px] text-zinc-400 font-medium mt-0.5">Blocked</p>
                </div>
              </div>

              {/* Chunks List */}
              <div className="space-y-3">
                <h4 className="text-xs font-bold text-zinc-400 flex items-center gap-1.5">
                  <FileCheck2 className="w-4 h-4 text-emerald-500" />
                  Retrieved Chunks
                </h4>

                {latestTrace.chunksRetrieved.length === 0 ? (
                  <div className="glass-card-static p-4 text-center text-xs text-zinc-500">
                    No matching chunks could be retrieved.
                  </div>
                ) : (
                  latestTrace.chunksRetrieved.map((chunk, index) => (
                    <div key={index} className="glass-card-static p-3 space-y-2 border-zinc-800 hover:border-zinc-700 transition-colors">
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-[10px] bg-primary-500/10 text-primary-300 px-1.5 py-0.5 rounded border border-primary-500/20 font-bold truncate max-w-[120px]">
                          Match #{index + 1}
                        </span>
                        <span className="text-[10px] text-zinc-500 font-medium">
                          Score: {chunk.score}
                        </span>
                      </div>
                      <p className="text-xs text-zinc-400 line-clamp-3 bg-zinc-950/20 p-2 rounded leading-normal">
                        "{chunk.text}"
                      </p>
                    </div>
                  ))
                )}
              </div>

              {latestTrace.chunksDeniedCount > 0 && (
                <div className="glass-card-static p-3 border-red-500/20 bg-red-500/5 rounded-xl flex gap-3 items-start animate-pulse-glow">
                  <Lock className="w-4 h-4 text-red-400 mt-0.5 shrink-0" />
                  <div>
                    <h5 className="text-xs font-semibold text-red-400">RBAC Filter Applied</h5>
                    <p className="text-[10px] text-zinc-400 mt-1 leading-normal">
                      Vector search rejected {latestTrace.chunksDeniedCount} candidate document chunks because their sensitivity level exceeds your role clearance ({user?.role}) or their department tag doesn't match yours ({user?.department}).
                    </p>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
