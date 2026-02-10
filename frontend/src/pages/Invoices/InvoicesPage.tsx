import { useState, useEffect, useCallback } from 'react'
import api from '../../services/api'
import { Invoice } from '../../types'
import { Plus, Pencil, Trash2, ChevronLeft, ChevronRight } from 'lucide-react'
import toast from 'react-hot-toast'

const statusLabels: Record<string, string> = {
  draft: '下書き',
  sent: '送付済',
  paid: '入金済',
  overdue: '延滞',
}

const statusBadge: Record<string, string> = {
  draft: 'bg-gray-100 text-gray-800',
  sent: 'bg-blue-100 text-blue-800',
  paid: 'bg-green-100 text-green-800',
  overdue: 'bg-red-100 text-red-800',
}

export default function InvoicesPage() {
  const [invoices, setInvoices] = useState<Invoice[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pages, setPages] = useState(1)
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [editing, setEditing] = useState<Invoice | null>(null)
  const [form, setForm] = useState({
    contract_id: '', invoice_number: '', billing_month: '', working_hours: '',
    base_amount: '', adjustment_amount: '0', tax_amount: '', status: 'draft', notes: '',
  })

  const fetchData = useCallback(async () => {
    setLoading(true)
    try {
      const res = await api.get('/invoices', { params: { page, per_page: 20 } })
      setInvoices(res.data.items)
      setTotal(res.data.total)
      setPages(res.data.pages)
    } catch {
      toast.error('請求一覧の取得に失敗しました')
    } finally {
      setLoading(false)
    }
  }, [page])

  useEffect(() => { fetchData() }, [fetchData])

  const openCreate = () => {
    setEditing(null)
    setForm({
      contract_id: '', invoice_number: '', billing_month: '', working_hours: '',
      base_amount: '', adjustment_amount: '0', tax_amount: '', status: 'draft', notes: '',
    })
    setShowModal(true)
  }

  const openEdit = (inv: Invoice) => {
    setEditing(inv)
    setForm({
      contract_id: inv.contract_id.toString(),
      invoice_number: inv.invoice_number,
      billing_month: inv.billing_month,
      working_hours: inv.working_hours.toString(),
      base_amount: inv.base_amount.toString(),
      adjustment_amount: inv.adjustment_amount.toString(),
      tax_amount: inv.tax_amount.toString(),
      status: inv.status,
      notes: inv.notes || '',
    })
    setShowModal(true)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const payload = {
      contract_id: Number(form.contract_id),
      invoice_number: form.invoice_number,
      billing_month: form.billing_month,
      working_hours: Number(form.working_hours),
      base_amount: Number(form.base_amount),
      adjustment_amount: Number(form.adjustment_amount),
      tax_amount: Number(form.tax_amount),
      status: form.status,
      notes: form.notes || null,
    }
    try {
      if (editing) {
        await api.put(`/invoices/${editing.id}`, payload)
        toast.success('請求を更新しました')
      } else {
        await api.post('/invoices', payload)
        toast.success('請求を作成しました')
      }
      setShowModal(false)
      fetchData()
    } catch {
      toast.error('保存に失敗しました')
    }
  }

  const handleDelete = async (id: number) => {
    if (!window.confirm('この請求を削除しますか？')) return
    try {
      await api.delete(`/invoices/${id}`)
      toast.success('請求を削除しました')
      fetchData()
    } catch {
      toast.error('削除に失敗しました')
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold">請求管理</h2>
        <button onClick={openCreate} className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
          <Plus size={18} /> 新規作成
        </button>
      </div>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="text-left px-4 py-3 font-medium text-gray-600">ID</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">請求番号</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">請求月</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">契約</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">稼働時間</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">基本額</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">税額</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">合計額</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">ステータス</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">操作</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={10} className="text-center py-8 text-gray-500">読み込み中...</td></tr>
            ) : invoices.length === 0 ? (
              <tr><td colSpan={10} className="text-center py-8 text-gray-500">データがありません</td></tr>
            ) : invoices.map((inv) => (
              <tr key={inv.id} className="border-b hover:bg-gray-50">
                <td className="px-4 py-3">{inv.id}</td>
                <td className="px-4 py-3 font-medium">{inv.invoice_number}</td>
                <td className="px-4 py-3">{inv.billing_month}</td>
                <td className="px-4 py-3 text-gray-500">{inv.contract?.contract_number || `#${inv.contract_id}`}</td>
                <td className="px-4 py-3">{inv.working_hours}h</td>
                <td className="px-4 py-3">{inv.base_amount.toLocaleString()}円</td>
                <td className="px-4 py-3">{inv.tax_amount.toLocaleString()}円</td>
                <td className="px-4 py-3 font-medium">{inv.total_amount.toLocaleString()}円</td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusBadge[inv.status] || 'bg-gray-100 text-gray-800'}`}>
                    {statusLabels[inv.status] || inv.status}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <button onClick={() => openEdit(inv)} className="text-gray-500 hover:text-blue-600"><Pencil size={16} /></button>
                    <button onClick={() => handleDelete(inv.id)} className="text-gray-500 hover:text-red-600"><Trash2 size={16} /></button>
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
              <h3 className="text-lg font-bold mb-4">{editing ? '請求を編集' : '請求を新規作成'}</h3>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">契約ID *</label>
                    <input type="number" value={form.contract_id} onChange={(e) => setForm({ ...form, contract_id: e.target.value })} required className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">請求番号 *</label>
                    <input type="text" value={form.invoice_number} onChange={(e) => setForm({ ...form, invoice_number: e.target.value })} required className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none" />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">請求月 *</label>
                    <input type="month" value={form.billing_month} onChange={(e) => setForm({ ...form, billing_month: e.target.value })} required className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">稼働時間 (h) *</label>
                    <input type="number" step="0.5" value={form.working_hours} onChange={(e) => setForm({ ...form, working_hours: e.target.value })} required className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none" />
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">基本額 (円) *</label>
                    <input type="number" value={form.base_amount} onChange={(e) => setForm({ ...form, base_amount: e.target.value })} required className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">調整額 (円)</label>
                    <input type="number" value={form.adjustment_amount} onChange={(e) => setForm({ ...form, adjustment_amount: e.target.value })} className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">税額 (円) *</label>
                    <input type="number" value={form.tax_amount} onChange={(e) => setForm({ ...form, tax_amount: e.target.value })} required className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none" />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">ステータス</label>
                  <select value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })} className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none">
                    <option value="draft">下書き</option>
                    <option value="sent">送付済</option>
                    <option value="paid">入金済</option>
                    <option value="overdue">延滞</option>
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
