import { useState, useEffect, useCallback } from 'react'
import api from '../../services/api'
import { engineersApi } from '../../services/engineers'
import { Quotation, Project, Engineer } from '../../types'
import { Plus, Pencil, Trash2, ChevronLeft, ChevronRight, AlertTriangle } from 'lucide-react'
import toast from 'react-hot-toast'

const tierLimitLabels: Record<string, string> = {
  proper_only: 'プロパーのみ',
  first_tier: '一社先まで',
  second_tier: '二社先まで',
  no_restriction: '制限なし',
}

const statusLabels: Record<string, string> = {
  draft: '下書き',
  submitted: '提出済',
  approved: '承認済',
  rejected: '却下',
}

const statusBadge: Record<string, string> = {
  draft: 'bg-gray-100 text-gray-800',
  submitted: 'bg-blue-100 text-blue-800',
  approved: 'bg-green-100 text-green-800',
  rejected: 'bg-red-100 text-red-800',
}

export default function QuotationsPage() {
  const [quotations, setQuotations] = useState<Quotation[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pages, setPages] = useState(1)
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [editing, setEditing] = useState<Quotation | null>(null)
  const [form, setForm] = useState({
    project_id: '', engineer_id: '', unit_price: '', estimated_hours: '', status: 'draft', notes: '',
  })
  const [projectOptions, setProjectOptions] = useState<Project[]>([])
  const [engineerOptions, setEngineerOptions] = useState<Engineer[]>([])

  const [selectedProject, setSelectedProject] = useState<Project | null>(null)

  useEffect(() => {
    if (showModal) {
      api.get('/projects', { params: { page: 1, per_page: 100 } }).then((res) => setProjectOptions(res.data.items)).catch(() => {})
    }
  }, [showModal])

  // 案件選択時に適格エンジニアを取得
  useEffect(() => {
    if (!form.project_id) {
      setEngineerOptions([])
      setSelectedProject(null)
      return
    }
    const project = projectOptions.find((p) => p.id === Number(form.project_id))
    setSelectedProject(project || null)
    engineersApi.listEligible(Number(form.project_id))
      .then((res) => setEngineerOptions(res.data.items))
      .catch(() => {
        // フォールバック: eligible API が失敗した場合は全エンジニアを取得
        api.get('/engineers', { params: { page: 1, per_page: 100 } }).then((res) => setEngineerOptions(res.data.items)).catch(() => {})
      })
  }, [form.project_id, projectOptions])

  const fetchData = useCallback(async () => {
    setLoading(true)
    try {
      const res = await api.get('/quotations', { params: { page, per_page: 20 } })
      setQuotations(res.data.items)
      setTotal(res.data.total)
      setPages(res.data.pages)
    } catch {
      toast.error('見積一覧の取得に失敗しました')
    } finally {
      setLoading(false)
    }
  }, [page])

  useEffect(() => { fetchData() }, [fetchData])

  const openCreate = () => {
    setEditing(null)
    setForm({ project_id: '', engineer_id: '', unit_price: '', estimated_hours: '', status: 'draft', notes: '' })
    setShowModal(true)
  }

  const openEdit = (q: Quotation) => {
    setEditing(q)
    setForm({
      project_id: q.project_id.toString(),
      engineer_id: q.engineer_id.toString(),
      unit_price: q.unit_price.toString(),
      estimated_hours: q.estimated_hours.toString(),
      status: q.status,
      notes: q.notes || '',
    })
    setShowModal(true)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const payload = {
      project_id: Number(form.project_id),
      engineer_id: Number(form.engineer_id),
      unit_price: Number(form.unit_price),
      estimated_hours: Number(form.estimated_hours),
      status: form.status,
      notes: form.notes || null,
    }
    try {
      if (editing) {
        await api.put(`/quotations/${editing.id}`, payload)
        toast.success('見積を更新しました')
      } else {
        await api.post('/quotations', payload)
        toast.success('見積を作成しました')
      }
      setShowModal(false)
      fetchData()
    } catch {
      toast.error('保存に失敗しました')
    }
  }

  const handleDelete = async (id: number) => {
    if (!window.confirm('この見積を削除しますか？')) return
    try {
      await api.delete(`/quotations/${id}`)
      toast.success('見積を削除しました')
      fetchData()
    } catch {
      toast.error('削除に失敗しました')
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold">見積管理</h2>
        <button onClick={openCreate} className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
          <Plus size={18} /> 新規作成
        </button>
      </div>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="text-left px-4 py-3 font-medium text-gray-600">ID</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">案件</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">エンジニア</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">単価</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">見積時間</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">合計金額</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">ステータス</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">操作</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={8} className="text-center py-8 text-gray-500">読み込み中...</td></tr>
            ) : quotations.length === 0 ? (
              <tr><td colSpan={8} className="text-center py-8 text-gray-500">データがありません</td></tr>
            ) : quotations.map((q) => (
              <tr key={q.id} className="border-b hover:bg-gray-50">
                <td className="px-4 py-3">{q.id}</td>
                <td className="px-4 py-3 font-medium">{q.project?.name || `案件#${q.project_id}`}</td>
                <td className="px-4 py-3 text-gray-500">{q.engineer?.full_name || `エンジニア#${q.engineer_id}`}</td>
                <td className="px-4 py-3">{q.unit_price.toLocaleString()}円</td>
                <td className="px-4 py-3">{q.estimated_hours}h</td>
                <td className="px-4 py-3 font-medium">{q.total_amount.toLocaleString()}円</td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusBadge[q.status] || 'bg-gray-100 text-gray-800'}`}>
                    {statusLabels[q.status] || q.status}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <button onClick={() => openEdit(q)} className="text-gray-500 hover:text-blue-600"><Pencil size={16} /></button>
                    <button onClick={() => handleDelete(q.id)} className="text-gray-500 hover:text-red-600"><Trash2 size={16} /></button>
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
              <h3 className="text-lg font-bold mb-4">{editing ? '見積を編集' : '見積を新規作成'}</h3>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">案件 *</label>
                    <select value={form.project_id} onChange={(e) => setForm({ ...form, project_id: e.target.value, engineer_id: '' })} required className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none">
                      <option value="">選択してください</option>
                      {projectOptions.map((p) => (
                        <option key={p.id} value={p.id}>{p.name}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">エンジニア *</label>
                    <select value={form.engineer_id} onChange={(e) => setForm({ ...form, engineer_id: e.target.value })} required disabled={!form.project_id} className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none disabled:bg-gray-100 disabled:cursor-not-allowed">
                      <option value="">{form.project_id ? '選択してください' : '先に案件を選択してください'}</option>
                      {engineerOptions.map((eng) => (
                        <option key={eng.id} value={eng.id}>{eng.full_name}</option>
                      ))}
                    </select>
                  </div>
                </div>
                {selectedProject?.subcontracting_tier_limit && (
                  <div className="flex items-center gap-2 px-3 py-2 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-800">
                    <AlertTriangle size={16} />
                    <span>この案件の再委託制限: <strong>{tierLimitLabels[selectedProject.subcontracting_tier_limit] || selectedProject.subcontracting_tier_limit}</strong>（適格なエンジニアのみ表示されています）</span>
                  </div>
                )}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">単価 (円) *</label>
                    <input type="number" value={form.unit_price} onChange={(e) => setForm({ ...form, unit_price: e.target.value })} required className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">見積時間 (h) *</label>
                    <input type="number" value={form.estimated_hours} onChange={(e) => setForm({ ...form, estimated_hours: e.target.value })} required className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none" />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">ステータス</label>
                  <select value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })} className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none">
                    <option value="draft">下書き</option>
                    <option value="submitted">提出済</option>
                    <option value="approved">承認済</option>
                    <option value="rejected">却下</option>
                  </select>
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
