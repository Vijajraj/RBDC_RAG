import { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import {
  FileUp,
  FileText,
  Building2,
  Calendar,
  AlertTriangle,
  FolderClosed,
  Loader2,
  CheckCircle,
  FileCode,
  Sparkles,
} from 'lucide-react'

const sensitivityLabels = ['Public', 'Internal', 'Confidential', 'Restricted']
const sensitivityColors = [
  'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  'bg-sky-500/10 text-sky-400 border-sky-500/20',
  'bg-amber-500/10 text-amber-400 border-amber-500/20',
  'bg-red-500/10 text-red-400 border-red-500/20',
]

export default function DocumentsPage() {
  const { token } = useAuth()
  const [documents, setDocuments] = useState([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [successMsg, setSuccessMsg] = useState('')
  const [errorMsg, setErrorMsg] = useState('')
  
  // Tab selector: 'file' or 'paste'
  const [mode, setMode] = useState('file')
  const [dragActive, setDragActive] = useState(false)

  const [form, setForm] = useState({
    title: '',
    department: 'all',
    sensitivity_level: 0,
    file: null,
    pastedText: '',
  })

  const API = import.meta.env.VITE_API_URL

  const fetchDocs = async () => {
    try {
      const res = await fetch(`${API}/documents/`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      const data = await res.json()
      if (res.ok) {
        setDocuments(data.documents || [])
      }
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchDocs()
  }, [token])

  // Drag and drop handlers
  const handleDrag = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0]
      // Validate file extension
      const ext = droppedFile.name.split('.').pop().toLowerCase()
      if (['pdf', 'txt', 'md', 'text'].includes(ext)) {
        setForm((f) => ({ ...f, file: droppedFile }))
      } else {
        setErrorMsg('Invalid file type. Please upload a PDF, TXT, or MD file.')
      }
    }
  }

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setForm((f) => ({ ...f, file: e.target.files[0] }))
    }
  }

  const handleUpload = async (e) => {
    e.preventDefault()
    
    // Check validation based on selected mode
    if (mode === 'file' && !form.file) {
      setErrorMsg('Please select or drag a file to upload.')
      return
    }
    if (mode === 'paste' && !form.pastedText.trim()) {
      setErrorMsg('Please paste some document content first.')
      return
    }
    if (!form.title.trim()) {
      setErrorMsg('Please specify a document title.')
      return
    }
    
    setUploading(true)
    setErrorMsg('')
    setSuccessMsg('')

    const formData = new FormData()
    formData.append('title', form.title.trim())
    formData.append('department', form.department)
    formData.append('sensitivity_level', form.sensitivity_level)

    if (mode === 'file') {
      formData.append('file', form.file)
    } else {
      // In paste mode, create a virtual text file blob
      const textBlob = new Blob([form.pastedText], { type: 'text/plain' })
      formData.append('file', textBlob, `${form.title.replace(/\s+/g, '_')}.txt`)
    }

    try {
      const res = await fetch(`${API}/documents/upload`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      })

      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Upload failed')

      setSuccessMsg('Document successfully ingested and split into vector chunks.')
      setForm({ title: '', department: 'all', sensitivity_level: 0, file: null, pastedText: '' })
      
      const fileInput = document.getElementById('file-input')
      if (fileInput) fileInput.value = ''
      
      fetchDocs()
    } catch (err) {
      setErrorMsg(err.message || 'Error occurred during document ingestion.')
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 animate-fade-in">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-zinc-100">Document Management</h1>
          <p className="text-zinc-500 text-sm mt-1">
            Ingest corporate documents and associate them with security access boundaries.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Upload Form Card */}
        <div className="lg:col-span-1 glass-card p-6 h-fit space-y-6">
          <div>
            <h2 className="text-base font-semibold text-zinc-200 flex items-center gap-2">
              <FileUp className="w-5 h-5 text-primary-400" />
              Ingest New Document
            </h2>
            <p className="text-zinc-500 text-xs mt-1">
              Select or drag files, or copy/paste raw text content directly to chunk and index it.
            </p>
          </div>

          {/* Mode Selector Tabs */}
          <div className="flex p-1 bg-zinc-950/40 rounded-xl border border-white/5">
            <button
              onClick={() => { setMode('file'); setErrorMsg(''); setSuccessMsg(''); }}
              className={`flex-1 py-2 px-3 rounded-lg text-xs font-semibold transition-all ${
                mode === 'file'
                  ? 'bg-primary-500/20 text-primary-300 border border-primary-500/20 shadow'
                  : 'text-zinc-400 hover:text-zinc-200'
              }`}
            >
              File Upload
            </button>
            <button
              onClick={() => { setMode('paste'); setErrorMsg(''); setSuccessMsg(''); }}
              className={`flex-1 py-2 px-3 rounded-lg text-xs font-semibold transition-all ${
                mode === 'paste'
                  ? 'bg-primary-500/20 text-primary-300 border border-primary-500/20 shadow'
                  : 'text-zinc-400 hover:text-zinc-200'
              }`}
            >
              Paste Content
            </button>
          </div>

          <form onSubmit={handleUpload} className="space-y-4">
            <div>
              <label className="block text-xs text-zinc-400 mb-1.5 font-medium uppercase tracking-wider">
                Document Title
              </label>
              <input
                type="text"
                placeholder="e.g. Q2 Product Roadmap"
                value={form.title}
                onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
                className="input-field"
                required
              />
            </div>

            <div>
              <label className="block text-xs text-zinc-400 mb-1.5 font-medium uppercase tracking-wider">
                Target Department
              </label>
              <select
                value={form.department}
                onChange={(e) => setForm((f) => ({ ...f, department: e.target.value }))}
                className="input-field cursor-pointer"
              >
                <option value="all" className="bg-zinc-900">All Departments</option>
                <option value="engineering" className="bg-zinc-900">Engineering</option>
                <option value="hr" className="bg-zinc-900">Human Resources</option>
                <option value="legal" className="bg-zinc-900">Legal</option>
                <option value="admin" className="bg-zinc-900">Admin Only</option>
              </select>
            </div>

            <div>
              <label className="block text-xs text-zinc-400 mb-1.5 font-medium uppercase tracking-wider">
                Sensitivity Clearance Level ({form.sensitivity_level})
              </label>
              <input
                type="range"
                min="0"
                max="3"
                value={form.sensitivity_level}
                onChange={(e) => setForm((f) => ({ ...f, sensitivity_level: parseInt(e.target.value) }))}
                className="w-full h-1 bg-zinc-800 rounded-lg appearance-none cursor-pointer accent-primary-500"
              />
              <div className="flex justify-between text-[10px] text-zinc-500 mt-1.5 font-semibold">
                <span>L0: PUBLIC</span>
                <span>L1: INTERNAL</span>
                <span>L2: CONFID.</span>
                <span>L3: RESTR.</span>
              </div>
            </div>

            {/* Mode-Specific Input Panel */}
            {mode === 'file' ? (
              <div className="space-y-2">
                <label className="block text-xs text-zinc-400 mb-1.5 font-medium uppercase tracking-wider">
                  Document File
                </label>
                <div
                  onDragEnter={handleDrag}
                  onDragOver={handleDrag}
                  onDragLeave={handleDrag}
                  onDrop={handleDrop}
                  className={`border-2 border-dashed rounded-2xl p-6 transition-all flex flex-col items-center justify-center text-center cursor-pointer relative ${
                    dragActive
                      ? 'border-primary-400 bg-primary-500/10'
                      : form.file
                      ? 'border-emerald-500/40 bg-emerald-500/5'
                      : 'border-white/10 hover:border-white/20 bg-zinc-950/20'
                  }`}
                  onClick={() => document.getElementById('file-input').click()}
                >
                  <input
                    id="file-input"
                    type="file"
                    accept=".pdf,.txt,.md,.text"
                    onChange={handleFileChange}
                    className="hidden"
                  />
                  {form.file ? (
                    <>
                      <FileCode className="w-10 h-10 text-emerald-400 mb-3 animate-pulse-glow" />
                      <p className="text-zinc-200 text-sm font-semibold truncate max-w-[220px]">
                        {form.file.name}
                      </p>
                      <p className="text-zinc-500 text-xs mt-1">
                        {(form.file.size / 1024).toFixed(1)} KB • Click or drop new file to replace
                      </p>
                    </>
                  ) : (
                    <>
                      <FileUp className="w-10 h-10 text-zinc-500 mb-3" />
                      <p className="text-zinc-300 text-sm font-medium">
                        Drag & Drop document here
                      </p>
                      <p className="text-zinc-500 text-xs mt-1">
                        or click to browse computer (PDF, TXT, MD)
                      </p>
                    </>
                  )}
                </div>
              </div>
            ) : (
              <div className="space-y-2">
                <label className="block text-xs text-zinc-400 mb-1.5 font-medium uppercase tracking-wider">
                  Paste Document Content
                </label>
                <textarea
                  placeholder="Paste or type document content directly here..."
                  value={form.pastedText}
                  onChange={(e) => setForm((f) => ({ ...f, pastedText: e.target.value }))}
                  className="input-field min-h-[160px] resize-y text-sm font-sans"
                  required
                />
              </div>
            )}

            {successMsg && (
              <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-xl p-3 flex gap-2.5 text-emerald-400 text-xs animate-fade-in">
                <CheckCircle className="w-4 h-4 shrink-0 mt-0.5" />
                <p>{successMsg}</p>
              </div>
            )}

            {errorMsg && (
              <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-3 flex gap-2.5 text-red-400 text-xs animate-fade-in">
                <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                <p>{errorMsg}</p>
              </div>
            )}

            <button type="submit" disabled={uploading} className="btn-primary w-full flex items-center justify-center gap-2">
              {uploading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Ingesting Document...
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  Ingest & Vectorize
                </>
              )}
            </button>
          </form>
        </div>

        {/* Existing Documents Panel */}
        <div className="lg:col-span-2 glass-card p-6 h-fit space-y-6">
          <h2 className="text-base font-semibold text-zinc-200 flex items-center gap-2">
            <FileText className="w-5 h-5 text-accent-400" />
            Ingested Knowledge Base ({documents.length})
          </h2>

          {loading ? (
            <div className="h-48 flex items-center justify-center text-zinc-500">
              <Loader2 className="w-6 h-6 animate-spin text-primary-400" />
            </div>
          ) : documents.length === 0 ? (
            <div className="h-48 flex flex-col items-center justify-center text-center text-zinc-600">
              <FolderClosed className="w-12 h-12 mb-3" />
              <p className="text-sm">No documents found in the database.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm border-collapse">
                <thead>
                  <tr className="border-b border-white/5 text-zinc-500 font-medium">
                    <th className="py-3 px-4">Title</th>
                    <th className="py-3 px-4">Department</th>
                    <th className="py-3 px-4">Clearance</th>
                    <th className="py-3 px-4">Chunks</th>
                    <th className="py-3 px-4">Date Ingested</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {documents.map((doc) => (
                    <tr key={doc.id} className="hover:bg-white/2 transition-colors">
                      <td className="py-3.5 px-4 font-medium text-zinc-200">
                        <div className="flex items-center gap-2.5">
                          <FileText className="w-4 h-4 text-zinc-500 shrink-0" />
                          <span className="truncate max-w-[200px]" title={doc.title}>
                            {doc.title}
                          </span>
                        </div>
                      </td>
                      <td className="py-3.5 px-4 text-zinc-400">
                        <div className="flex items-center gap-1.5">
                          <Building2 className="w-3.5 h-3.5 text-zinc-600" />
                          <span className="capitalize">{doc.department}</span>
                        </div>
                      </td>
                      <td className="py-3.5 px-4">
                        <span className={`badge ${sensitivityColors[doc.sensitivity_level] || 'sensitivity-0'}`}>
                          L{doc.sensitivity_level}: {sensitivityLabels[doc.sensitivity_level]}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-zinc-300 font-mono">{doc.chunk_count}</td>
                      <td className="py-3.5 px-4 text-zinc-500 text-xs">
                        <div className="flex items-center gap-1.5">
                          <Calendar className="w-3.5 h-3.5 text-zinc-600" />
                          {doc.created_at ? new Date(doc.created_at).toLocaleDateString() : 'N/A'}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
