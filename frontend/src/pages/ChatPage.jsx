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
  BrainCircuit,
  MessageSquare,
  Sparkles,
  Paperclip,
  X,
  FileText,
  Loader2,
  Eye,
  EyeOff,
  User,
  Plus,
} from 'lucide-react'

const sensitivityLabels = ['Public', 'Internal', 'Confidential', 'Restricted']
const sensitivityColors = [
  'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  'bg-sky-500/10 text-sky-400 border-sky-500/20',
  'bg-amber-500/10 text-amber-400 border-amber-500/20',
  'bg-red-500/10 text-red-400 border-red-500/20',
]

export default function ChatPage() {
  const { token, user, isAdmin } = useAuth()
  const [messages, setMessages] = useState([])
  const [question, setQuestion] = useState('')
  const [loading, setLoading] = useState(false)
  const [latestTrace, setLatestTrace] = useState(null)
  
  // Sidebar visibility
  const [showTrace, setShowTrace] = useState(true)
  
  // Document Upload Modal state
  const [showUploadModal, setShowUploadModal] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [uploadSuccess, setUploadSuccess] = useState('')
  const [uploadError, setUploadError] = useState('')
  const [uploadForm, setUploadForm] = useState({
    title: '',
    department: 'all',
    sensitivity_level: 0,
    file: null,
  })

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

    // Add user message
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

  const handleModalUpload = async (e) => {
    e.preventDefault()
    if (!uploadForm.file || !uploadForm.title.trim() || uploading) return

    setUploading(true)
    setUploadError('')
    setUploadSuccess('')

    const formData = new FormData()
    formData.append('file', uploadForm.file)
    formData.append('title', uploadForm.title.trim())
    formData.append('department', uploadForm.department)
    formData.append('sensitivity_level', uploadForm.sensitivity_level)

    try {
      const res = await fetch(`${API}/documents/upload`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      })

      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Upload failed')

      setUploadSuccess('Document successfully vectorized and added to RAG context.')
      setUploadForm({ title: '', department: 'all', sensitivity_level: 0, file: null })
      
      const fileInput = document.getElementById('modal-file-input')
      if (fileInput) fileInput.value = ''
      
      // Auto close modal after short delay
      setTimeout(() => {
        setShowUploadModal(false)
        setUploadSuccess('')
      }, 2000)
    } catch (err) {
      setUploadError(err.message || 'Ingestion failed.')
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="max-w-[1600px] mx-auto px-4 sm:px-6 lg:px-8 py-4 h-[calc(100vh-4rem)] flex gap-6 overflow-hidden animate-fade-in">
      
      {/* Left / Center Panel: Claude-like Chat Workspace */}
      <div className="flex-1 flex flex-col glass-card h-full overflow-hidden relative">
        
        {/* Chat Header */}
        <div className="px-6 py-4 border-b border-white/5 flex items-center justify-between bg-zinc-950/20">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-primary-500/10 text-primary-400">
              <BrainCircuit className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-zinc-100">Secure RAG Assistant</h2>
              <p className="text-xs text-zinc-500 flex items-center gap-1.5 mt-0.5">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                Clearance: Level {user?.clearance_level} ({user?.department} department)
              </p>
            </div>
          </div>
          
          {/* Action buttons */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowTrace(!showTrace)}
              className="p-2 rounded-xl text-zinc-400 hover:text-zinc-200 hover:bg-white/5 transition-all flex items-center gap-1.5 text-xs font-semibold border border-white/5"
              title="Toggle Access Trace Panel"
            >
              {showTrace ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              {showTrace ? 'Hide Trace' : 'Show Trace'}
            </button>
          </div>
        </div>

        {/* Messages Container (Claude-style centered max-width list) */}
        <div className="flex-1 overflow-y-auto px-4 py-8">
          <div className="max-w-3xl mx-auto space-y-8">
            
            {messages.length === 0 ? (
              <div className="py-12 flex flex-col items-center justify-center text-center max-w-lg mx-auto">
                <div className="w-16 h-16 rounded-3xl bg-primary-500/10 border border-primary-500/20 flex items-center justify-center mb-6 text-primary-400 animate-pulse-glow">
                  <Sparkles className="w-8 h-8" />
                </div>
                <h3 className="text-xl font-bold text-zinc-100">How can I help you today?</h3>
                <p className="text-sm text-zinc-500 mt-3 leading-relaxed">
                  Ask me anything about engineering handbooks, internal HR policies, contracts, or finances. 
                  Access pre-filtering is dynamically enforced on the vector search layer according to your department ({user?.department}) and clearance level (Level {user?.clearance_level}).
                </p>
              </div>
            ) : (
              messages.map((msg, idx) => (
                <div
                  key={idx}
                  className={`flex gap-5 animate-slide-up ${
                    msg.role === 'user' ? 'justify-end' : 'justify-start'
                  }`}
                >
                  {/* Left Avatar / Role indicator for Assistant */}
                  {msg.role === 'assistant' && (
                    <div className="w-9 h-9 rounded-xl bg-primary-500/10 border border-primary-500/20 flex items-center justify-center text-primary-400 shrink-0">
                      <Sparkles className="w-4 h-4" />
                    </div>
                  )}

                  <div
                    className={`max-w-[85%] rounded-2xl px-5 py-4 text-sm leading-relaxed ${
                      msg.role === 'user'
                        ? 'bg-zinc-800/80 text-zinc-100 border border-white/5 shadow-md font-medium'
                        : msg.isError
                        ? 'bg-red-500/10 border border-red-500/20 text-red-400'
                        : 'bg-transparent text-zinc-200'
                    }`}
                  >
                    {/* Header info inside bubbles for clarity */}
                    <div className="text-[10px] text-zinc-500 font-bold uppercase tracking-wider mb-1 flex items-center gap-1.5">
                      {msg.role === 'user' ? (
                        <>
                          <User className="w-3 h-3 text-zinc-500" />
                          You ({user?.name})
                        </>
                      ) : (
                        <>
                          <ShieldCheck className="w-3 h-3 text-primary-400" />
                          SecureRAG Engine
                        </>
                      )}
                    </div>

                    <div className="prose prose-invert max-w-none text-zinc-200 whitespace-pre-wrap font-sans">
                      {msg.content}
                    </div>

                    {/* Expandable inline trace panel details */}
                    {msg.trace && (
                      <button
                        onClick={() => {
                          setLatestTrace({ ...msg.trace, query: messages[idx - 1]?.content })
                          setShowTrace(true)
                        }}
                        className="mt-3 flex items-center gap-1 text-xs text-primary-400 hover:text-primary-300 transition-colors font-semibold border-t border-white/5 pt-2 w-full"
                      >
                        <ChevronRight className="w-3.5 h-3.5" />
                        Retrieve trace: {msg.trace.chunksRetrieved.length} allowed / {msg.trace.chunksDeniedCount} blocked
                      </button>
                    )}
                  </div>
                </div>
              ))
            )}

            {loading && (
              <div className="flex gap-5 justify-start">
                <div className="w-9 h-9 rounded-xl bg-primary-500/10 border border-primary-500/20 flex items-center justify-center text-primary-400 shrink-0 animate-spin-slow">
                  <BrainCircuit className="w-4 h-4" />
                </div>
                <div className="bg-zinc-950/20 border border-white/5 text-zinc-400 rounded-2xl px-5 py-4 text-sm flex items-center gap-3">
                  <span className="w-1.5 h-1.5 rounded-full bg-primary-400 animate-bounce [animation-delay:-0.3s]" />
                  <span className="w-1.5 h-1.5 rounded-full bg-primary-400 animate-bounce [animation-delay:-0.15s]" />
                  <span className="w-1.5 h-1.5 rounded-full bg-primary-400 animate-bounce" />
                  <span className="font-medium text-xs">Querying Qdrant index with filter & streaming LLM response...</span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input Bar (Claude-style centered container) */}
        <div className="p-6 border-t border-white/5 bg-zinc-950/10">
          <div className="max-w-3xl mx-auto relative">
            <form onSubmit={handleSend} className="relative flex items-center bg-zinc-900/90 border border-white/10 rounded-2xl p-2.5 pr-3 shadow-2xl focus-within:border-primary-500/60 focus-within:ring-2 focus-within:ring-primary-500/20 transition-all">
              
              {/* Attachment Icon - Admin document upload shortcut */}
              <button
                type="button"
                onClick={() => setShowUploadModal(true)}
                className="p-2.5 rounded-xl text-zinc-400 hover:text-zinc-200 hover:bg-white/5 transition-all shrink-0"
                title={isAdmin ? "Upload and index new document" : "Ingest restrictions"}
              >
                <Paperclip className="w-4.5 h-4.5" />
              </button>

              <input
                type="text"
                placeholder={
                  isAdmin
                    ? "Ask a question, or attach a document to ingest..."
                    : "Ask a question regarding internal handbooks..."
                }
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                className="bg-transparent border-0 outline-none flex-1 text-sm text-zinc-200 px-3 py-2 placeholder-zinc-500"
                disabled={loading}
              />

              <button
                type="submit"
                disabled={loading || !question.trim()}
                className="bg-primary-500 hover:bg-primary-600 disabled:opacity-30 disabled:hover:bg-primary-500 text-white p-2.5 rounded-xl transition-all duration-200 shrink-0 shadow-lg shadow-primary-500/20"
              >
                <Send className="w-4 h-4" />
              </button>
            </form>
            <p className="text-[10px] text-zinc-600 text-center mt-2.5 font-medium">
              SecureRAG filters document chunks before they enter the model generation pipeline.
            </p>
          </div>
        </div>
      </div>

      {/* Right Panel: Access Trace View (Collapsible) */}
      {showTrace && (
        <div className="w-80 glass-card h-full flex flex-col overflow-hidden shrink-0 animate-slide-up">
          <div className="px-6 py-4 border-b border-white/5 flex items-center justify-between bg-zinc-950/20">
            <div className="flex items-center gap-2.5">
              <Database className="w-4 h-4 text-accent-400" />
              <h3 className="text-sm font-semibold text-zinc-200">Real-Time Access Trace</h3>
            </div>
            <button
              onClick={() => setShowTrace(false)}
              className="p-1 rounded-lg text-zinc-500 hover:text-zinc-300 hover:bg-white/5"
            >
              <X className="w-4 h-4" />
            </button>
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
              <div className="space-y-4">
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
      )}

      {/* Document Ingestion Modal (Saves navigation to admin-only document tab) */}
      {showUploadModal && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="glass-card w-full max-w-md p-6 space-y-6 relative border border-white/10 shadow-2xl animate-slide-up">
            <button
              onClick={() => {
                setShowUploadModal(false)
                setUploadError('')
                setUploadSuccess('')
              }}
              className="absolute top-4 right-4 p-1.5 rounded-lg text-zinc-500 hover:text-zinc-300 hover:bg-white/5 transition-all"
            >
              <X className="w-5 h-5" />
            </button>

            {/* Ingestion Restriction Warning for Non-Admins */}
            {!isAdmin ? (
              <div className="text-center py-6 space-y-4">
                <ShieldAlert className="w-12 h-12 text-amber-500 mx-auto animate-pulse-glow" />
                <h3 className="text-base font-bold text-zinc-200">Access Denied</h3>
                <p className="text-sm text-zinc-400">
                  Only users with the <strong>Admin</strong> role can ingest files into the RAG database.
                </p>
                <div className="bg-zinc-950/40 p-4 rounded-xl border border-white/5 text-xs text-zinc-500 text-left space-y-1">
                  <p className="font-semibold text-zinc-400">Administrator Credentials:</p>
                  <p>Email: <code className="text-primary-300">admin@securerag.com</code></p>
                  <p>Password: <code className="text-primary-300">password123</code></p>
                </div>
              </div>
            ) : (
              <>
                <div>
                  <h3 className="text-base font-semibold text-zinc-200 flex items-center gap-2">
                    <FileUp className="w-5 h-5 text-primary-400" />
                    Quick Ingest Document
                  </h3>
                  <p className="text-zinc-500 text-xs mt-1">
                    Upload new material directly into the RAG system indexes.
                  </p>
                </div>

                <form onSubmit={handleModalUpload} className="space-y-4">
                  <div>
                    <label className="block text-[10px] text-zinc-400 mb-1.5 font-bold uppercase tracking-wider">
                      Document Title
                    </label>
                    <input
                      type="text"
                      placeholder="e.g. Compensation Schema 2026"
                      value={uploadForm.title}
                      onChange={(e) => setUploadForm((f) => ({ ...f, title: e.target.value }))}
                      className="input-field text-xs"
                      required
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-[10px] text-zinc-400 mb-1.5 font-bold uppercase tracking-wider">
                        Department Boundary
                      </label>
                      <select
                        value={uploadForm.department}
                        onChange={(e) => setUploadForm((f) => ({ ...f, department: e.target.value }))}
                        className="input-field text-xs cursor-pointer"
                      >
                        <option value="all" className="bg-zinc-900">All</option>
                        <option value="engineering" className="bg-zinc-900">Engineering</option>
                        <option value="hr" className="bg-zinc-900">HR</option>
                        <option value="legal" className="bg-zinc-900">Legal</option>
                        <option value="admin" className="bg-zinc-900">Admin</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-[10px] text-zinc-400 mb-1.5 font-bold uppercase tracking-wider">
                        Clearance (Level {uploadForm.sensitivity_level})
                      </label>
                      <select
                        value={uploadForm.sensitivity_level}
                        onChange={(e) => setUploadForm((f) => ({ ...f, sensitivity_level: parseInt(e.target.value) }))}
                        className="input-field text-xs cursor-pointer"
                      >
                        <option value={0} className="bg-zinc-900">L0: Public</option>
                        <option value={1} className="bg-zinc-900">L1: Internal</option>
                        <option value={2} className="bg-zinc-900">L2: Confidential</option>
                        <option value={3} className="bg-zinc-900">L3: Restricted</option>
                      </select>
                    </div>
                  </div>

                  <div>
                    <label className="block text-[10px] text-zinc-400 mb-1.5 font-bold uppercase tracking-wider">
                      Upload PDF/TXT/MD
                    </label>
                    <input
                      id="modal-file-input"
                      type="file"
                      accept=".pdf,.txt,.md,.text"
                      onChange={(e) => setUploadForm((f) => ({ ...f, file: e.target.files[0] }))}
                      className="input-field text-xs file:mr-3 file:py-1 file:px-2 file:rounded file:border-0 file:text-[10px] file:font-semibold file:bg-primary-500/20 file:text-primary-300 hover:file:bg-primary-500/30 file:cursor-pointer"
                      required
                    />
                  </div>

                  {uploadSuccess && (
                    <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-xl p-3 flex gap-2 text-emerald-400 text-xs">
                      <CheckCircle className="w-4 h-4 shrink-0 mt-0.5" />
                      <p>{uploadSuccess}</p>
                    </div>
                  )}

                  {uploadError && (
                    <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-3 flex gap-2 text-red-400 text-xs">
                      <ShieldAlert className="w-4 h-4 shrink-0 mt-0.5" />
                      <p>{uploadError}</p>
                    </div>
                  )}

                  <button
                    type="submit"
                    disabled={uploading}
                    className="btn-primary w-full flex items-center justify-center gap-2 text-xs"
                  >
                    {uploading ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Uploading File...
                      </>
                    ) : (
                      <>
                        <Plus className="w-4 h-4" />
                        Upload & Index
                      </>
                    )}
                  </button>
                </form>
              </>
            )}
          </div>
        </div>
      )}

    </div>
  )
}
