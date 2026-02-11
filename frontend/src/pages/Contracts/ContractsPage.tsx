import { useState, useEffect, useCallback } from 'react'
import api from '../../services/api'
import { Contract, Order, Engineer, Project } from '../../types'
import { Plus, Pencil, Trash2, ChevronLeft, ChevronRight } from 'lucide-react'
import toast from 'react-hot-toast'

const statusLabels: Record<string, string> = {
  draft: '下書き',
  active: '有効',
  expired: '期限切れ',
  terminated: '解約済',
}

const statusBadge: Record<string, string> = {
  draft: 'bg-gray-100 text-gray-800',
  active: 'bg-green-100 text-green-800',
  expired: 'bg-yellow-100 text-yellow-800',
  terminated: 'bg-red-100 text-red-800',
}

const contractTypeLabels: Record<string, string> = {
  quasi_delegation: '準委任',
  contract: '請負',
  dispatch: '派遣',
}

export default function ContractsPage() {
  const [contracts, setContracts] = useState<Contract[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pages, setPages] = useState(1)
  const [loading, setLoading] = useState(true)
  const [statusFilter, setStatusFilter] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [editing, setEditing] = useState<Contract | null>(null)
  const [form, setForm] = useState({
    order_id: '', contract_number: '', contract_type: 'quasi_delegation',
    engineer_id: '', project_id: '', start_date: '', end_date: '',
    monthly_rate: '', min_hours: '', max_hours: '', status: 'draft', notes: '',
  })
  const [orderOptions, setOrderOptions] = useState<Order[]>([])
  const [engineerOptions, setEngineerOptions] = useState<Engineer[]>([])
  const [projectOptions, setProjectOptions] = useState<Project[]>([])

  useEffect(() => {
    if (showModal) {
      api.get('/orders', { params: { page: 1, per_page: 100 } }).then((res) => setOrderOptions(res.data.items)).catch(() => {})
      api.get('/engineers', { params: { page: 1, per_page: 100 } }).then((res) => setEngineerOptions(res.data.items)).catch(() => {})
      api.get('/projects', { params: { page: 1, per_page: 100 } }).then((res) => setProjectOptions(res.data.items)).catch(() => {})
    }
  }, [showModal])

  const fetchData = useCallback(async () => {
    setLoading(true)
    try {
      const params: Record<string, string | number> = { page, per_page: 20 }
      if (statusFilter) params.status = statusFilter
      const res = await api.get('/contracts', { params })
      setContracts(res.data.items)
      setTotal(res.data.total)
      setPages(res.data.pages)
    } catch {
      toast.error('契約一覧の取得に失敗しました')
    } finally {
      setLoading(false)
    }
  }, [page, statusFilter])

  useEffect(() => { fetchData() }, [fetchData])

  const openCreate = () => {
    setEditing(null)
    setForm({
      order_id: '', contract_number: '', contract_type: 'quasi_delegation',
      engineer_id: '', project_id: '', start_date: '', end_date: '',
      monthly_rate: '', min_hours: '', max_hours: '', status: 'draft', notes: '',
    })
    setShowModal(true)
  }

  const openEdit = (c: Contract) => {
    setEditing(c)
    setForm({
      order_id: c.order_id.toString(),
      contract_number: c.contract_number,
      contract_type: c.contract_type,
      engineer_id: c.engineer_id.toString(),
      project_id: c.project_id.toString(),
      start_date: c.start_date,
      end_date: c.end_date,
      monthly_rate: c.monthly_rate.toString(),
      min_hours: c.min_hours?.toString() || '',
      max_hours: c.max_hours?.toString() || '',
      status: c.status,
      notes: c.notes || '',
    })
    setShowModal(true)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const payload = {
      order_id: Number(form.order_id),
      contract_number: form.contract_number,
      contract_type: form.contract_type,
      engineer_id: Number(form.engineer_id),
      project_id: Number(form.project_id),
      start_date: form.start_date,
      end_date: form.end_date,
      monthly_rate: Number(form.monthly_rate),
      min_hours: form.min_hours ? Number(form.min_hours) : null,
      max_hours: form.max_hours ? Number(form.max_hours) : null,
      status: form.status,
      notes: form.notes || null,
    }
    try {
      if (editing) {
        await api.put(`/contracts/${editing.id}`, payload)
        toast.success('契約を更新しました')
      } else {
        await api.post('/contracts', payload)
        toast.success('契約を作成しました')
      }
      setShowModal(false)
      fetchData()
    } catch {
      toast.error('保存に失敗しました')
    }
  }

  const handleDelete = async (id: number) => {
    if (!window.confirm('この契約を削除しますか？')) return
    try {
      await api.delete(`/contracts/${id}`)
      toast.success('契約を削除しました')
      fetchData()
    } catch {
      toast.error('削除に失敗しました')
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <h2 className="text-2xl font-bold">契約管理</h2>
          <select
            value={statusFilter}
            onChange={(e) => { setStatusFilter(e.target.value); setPage(1) }}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
          >
            <option value="">すべてのステータス</option>
            <option value="draft">下書き</option>
            <option value="active">有効</option>
            <option value="expired">期限切れ</option>
            <option value="terminated">解約済</option>
          </select>
        </div>
        <button onClick={openCreate} className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
          <Plus size={18} /> 新規作成
        </button>
      </div>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="text-left px-4 py-3 font-medium text-gray-600">ID</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">契約番号</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">種別</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">エンジニア</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">案件</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">月額</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">期間</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">ステータス</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">操作</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={9} className="text-center py-8 text-gray-500">読み込み中...</td></tr>
            ) : contracts.length === 0 ? (
              <tr><td colSpan={9} className="text-center py-8 text-gray-500">データがありません</td></tr>
            ) : contracts.map((c) => (
              <tr key={c.id} className="border-b hover:bg-gray-50">
                <td className="px-4 py-3">{c.id}</td>
                <td className="px-4 py-3 font-medium">{c.contract_number}</td>
                <td className="px-4 py-3">
                  <span className="px-2 py-1 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800">
                    {contractTypeLabels[c.contract_type] || c.contract_type}
                  </span>
                </td>
                <td className="px-4 py-3 text-gray-500">{c.engineer?.full_name || `#${c.engineer_id}`}</td>
                <td className="px-4 py-3 text-gray-500">{c.project?.name || `#${c.project_id}`}</td>
                <td className="px-4 py-3">{c.monthly_rate.toLocaleString()}円</td>
                <td className="px-4 py-3 text-gray-500 text-xs">{c.start_date} ~ {c.end_date}</td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusBadge[c.status] || 'bg-gray-100 text-gray-800'}`}>
                    {statusLabels[c.status] || c.status}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <button onClick={() => openEdit(c)} className="text-gray-500 hover:text-blue-600"><Pencil size={16} /></button>
                    <button onClick={() => handleDelete(c.id)} className="text-gray-500 hover:text-red-600"><Trash2 size={16} /></button>
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
              <h3 className="text-lg font-bold mb-4">{editing ? '契約を編集' : '契約を新規作成'}</h3>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">発注 *</label>
                    <select value={form.order_id} onChange={(e) => setForm({ ...form, order_id: e.target.value })} required className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none">
                      <option value="">選択してください</option>
                      {orderOptions.map((o) => (
                        <option key={o.id} value={o.id}>{o.order_number}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">契約番号 *</label>
                    <input type="text" value={form.contract_number} onChange={(e) => setForm({ ...form, contract_number: e.target.value })} required className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none" />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">契約種別 *</label>
                  <select value={form.contract_type} onChange={(e) => setForm({ ...form, contract_type: e.target.value })} className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none">
                    <option value="quasi_delegation">準委任</option>
                    <option value="contract">請負</option>
                    <option value="dispatch">派遣</option>
                  </select>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">エンジニア *</label>
                    <select value={form.engineer_id} onChange={(e) => setForm({ ...form, engineer_id: e.target.value })} required className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none">
                      <option value="">選択してください</option>
                      {engineerOptions.map((eng) => (
                        <option key={eng.id} value={eng.id}>{eng.full_name}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">案件 *</label>
                    <select value={form.project_id} onChange={(e) => setForm({ ...form, project_id: e.target.value })} required className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none">
                      <option value="">選択してください</option>
                      {projectOptions.map((p) => (
                        <option key={p.id} value={p.id}>{p.name}</option>
                      ))}
                    </select>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">開始日 *</label>
                    <input type="date" value={form.start_date} onChange={(e) => setForm({ ...form, start_date: e.target.value })} required className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">終了日 *</label>
                    <input type="date" value={form.end_date} onChange={(e) => setForm({ ...form, end_date: e.target.value })} required className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none" />
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">月額 (円) *</label>
                    <input type="number" value={form.monthly_rate} onChange={(e) => setForm({ ...form, monthly_rate: e.target.value })} required className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">最低時間</label>
                    <input type="number" value={form.min_hours} onChange={(e) => setForm({ ...form, min_hours: e.target.value })} className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">最高時間</label>
                    <input type="number" value={form.max_hours} onChange={(e) => setForm({ ...form, max_hours: e.target.value })} className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none" />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">ステータス</label>
                  <select value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })} className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none">
                    <option value="draft">下書き</option>
                    <option value="active">有効</option>
                    <option value="expired">期限切れ</option>
                    <option value="terminated">解約済</option>
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
