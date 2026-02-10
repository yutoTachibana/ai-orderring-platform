import { useState, useEffect, useCallback } from 'react'
import { projectsApi } from '../../services/projects'
import { Project } from '../../types'
import { Plus, Pencil, Trash2, ChevronLeft, ChevronRight } from 'lucide-react'
import toast from 'react-hot-toast'

const statusLabels: Record<string, string> = {
  draft: '下書き',
  open: '募集中',
  in_progress: '進行中',
  completed: '完了',
  closed: 'クローズ',
}

const statusBadge: Record<string, string> = {
  draft: 'bg-gray-100 text-gray-800',
  open: 'bg-blue-100 text-blue-800',
  in_progress: 'bg-yellow-100 text-yellow-800',
  completed: 'bg-green-100 text-green-800',
  closed: 'bg-red-100 text-red-800',
}

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pages, setPages] = useState(1)
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [editing, setEditing] = useState<Project | null>(null)
  const [form, setForm] = useState({
    name: '', description: '', status: 'draft', start_date: '', end_date: '',
    budget: '', required_headcount: '', notes: '',
  })

  const fetchData = useCallback(async () => {
    setLoading(true)
    try {
      const res = await projectsApi.list({ page, per_page: 20 })
      setProjects(res.data.items)
      setTotal(res.data.total)
      setPages(res.data.pages)
    } catch {
      toast.error('案件一覧の取得に失敗しました')
    } finally {
      setLoading(false)
    }
  }, [page])

  useEffect(() => { fetchData() }, [fetchData])

  const openCreate = () => {
    setEditing(null)
    setForm({ name: '', description: '', status: 'draft', start_date: '', end_date: '', budget: '', required_headcount: '', notes: '' })
    setShowModal(true)
  }

  const openEdit = (p: Project) => {
    setEditing(p)
    setForm({
      name: p.name,
      description: p.description || '',
      status: p.status,
      start_date: p.start_date || '',
      end_date: p.end_date || '',
      budget: p.budget?.toString() || '',
      required_headcount: p.required_headcount?.toString() || '',
      notes: p.notes || '',
    })
    setShowModal(true)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const payload = {
      name: form.name,
      description: form.description || null,
      status: form.status,
      start_date: form.start_date || null,
      end_date: form.end_date || null,
      budget: form.budget ? Number(form.budget) : null,
      required_headcount: form.required_headcount ? Number(form.required_headcount) : null,
      notes: form.notes || null,
    }
    try {
      if (editing) {
        await projectsApi.update(editing.id, payload)
        toast.success('案件を更新しました')
      } else {
        await projectsApi.create(payload)
        toast.success('案件を作成しました')
      }
      setShowModal(false)
      fetchData()
    } catch {
      toast.error('保存に失敗しました')
    }
  }

  const handleDelete = async (id: number) => {
    if (!window.confirm('この案件を削除しますか？')) return
    try {
      await projectsApi.delete(id)
      toast.success('案件を削除しました')
      fetchData()
    } catch {
      toast.error('削除に失敗しました')
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold">案件管理</h2>
        <button onClick={openCreate} className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
          <Plus size={18} /> 新規作成
        </button>
      </div>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="text-left px-4 py-3 font-medium text-gray-600">ID</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">案件名</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">クライアント</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">ステータス</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">予算</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">必要人数</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">期間</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">操作</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={8} className="text-center py-8 text-gray-500">読み込み中...</td></tr>
            ) : projects.length === 0 ? (
              <tr><td colSpan={8} className="text-center py-8 text-gray-500">データがありません</td></tr>
            ) : projects.map((p) => (
              <tr key={p.id} className="border-b hover:bg-gray-50">
                <td className="px-4 py-3">{p.id}</td>
                <td className="px-4 py-3 font-medium">{p.name}</td>
                <td className="px-4 py-3 text-gray-500">{p.client_company?.name || '-'}</td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusBadge[p.status] || 'bg-gray-100 text-gray-800'}`}>
                    {statusLabels[p.status] || p.status}
                  </span>
                </td>
                <td className="px-4 py-3">{p.budget ? `${p.budget.toLocaleString()}円` : '-'}</td>
                <td className="px-4 py-3">{p.required_headcount != null ? `${p.required_headcount}名` : '-'}</td>
                <td className="px-4 py-3 text-gray-500 text-xs">
                  {p.start_date && p.end_date ? `${p.start_date} ~ ${p.end_date}` : '-'}
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <button onClick={() => openEdit(p)} className="text-gray-500 hover:text-blue-600"><Pencil size={16} /></button>
                    <button onClick={() => handleDelete(p.id)} className="text-gray-500 hover:text-red-600"><Trash2 size={16} /></button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        <div className="flex items-center justify-between px-4 py-3 border-t bg-gray-50">
          <span className="text-sm text-gray-600">全{total}件中 {(page - 1) * 20 + 1}-{Math.min(page * 20, total)}件</span>
          <div className="flex items-center gap-2">
            <button onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page <= 1} className="p-1 rounded hover:bg-gray-200 disabled:opacity-50"><ChevronLeft size={18} /></button>
            <span className="text-sm">{page} / {pages}</span>
            <button onClick={() => setPage((p) => Math.min(pages, p + 1))} disabled={page >= pages} className="p-1 rounded hover:bg-gray-200 disabled:opacity-50"><ChevronRight size={18} /></button>
          </div>
        </div>
      </div>

      {showModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-lg max-h-[90vh] overflow-auto">
            <div className="p-6">
              <h3 className="text-lg font-bold mb-4">{editing ? '案件を編集' : '案件を新規作成'}</h3>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">案件名 *</label>
                  <input type="text" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">説明</label>
                  <textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} rows={3} className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">ステータス</label>
                  <select value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })} className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none">
                    <option value="draft">下書き</option>
                    <option value="open">募集中</option>
                    <option value="in_progress">進行中</option>
                    <option value="completed">完了</option>
                    <option value="closed">クローズ</option>
                  </select>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">開始日</label>
                    <input type="date" value={form.start_date} onChange={(e) => setForm({ ...form, start_date: e.target.value })} className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">終了日</label>
                    <input type="date" value={form.end_date} onChange={(e) => setForm({ ...form, end_date: e.target.value })} className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none" />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">予算 (円)</label>
                    <input type="number" value={form.budget} onChange={(e) => setForm({ ...form, budget: e.target.value })} className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">必要人数</label>
                    <input type="number" value={form.required_headcount} onChange={(e) => setForm({ ...form, required_headcount: e.target.value })} className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none" />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">備考</label>
                  <textarea value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} rows={3} className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none" />
                </div>
                <div className="flex justify-end gap-3 pt-4">
                  <button type="button" onClick={() => setShowModal(false)} className="px-4 py-2 border rounded-lg hover:bg-gray-50">キャンセル</button>
                  <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">保存</button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
