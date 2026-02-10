import { useState, useEffect, useCallback } from 'react'
import { companiesApi } from '../../services/companies'
import { Company } from '../../types'
import { Plus, Pencil, Trash2, ChevronLeft, ChevronRight } from 'lucide-react'
import toast from 'react-hot-toast'

const companyTypeLabels: Record<string, string> = {
  client: 'クライアント',
  vendor: 'ベンダー',
  ses: 'SES',
}

const companyTypeBadge: Record<string, string> = {
  client: 'bg-blue-100 text-blue-800',
  vendor: 'bg-green-100 text-green-800',
  ses: 'bg-purple-100 text-purple-800',
}

export default function CompaniesPage() {
  const [companies, setCompanies] = useState<Company[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pages, setPages] = useState(1)
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [editing, setEditing] = useState<Company | null>(null)
  const [form, setForm] = useState({ name: '', company_type: 'client', address: '', phone: '', email: '', website: '', notes: '' })

  const fetchData = useCallback(async () => {
    setLoading(true)
    try {
      const res = await companiesApi.list({ page, per_page: 20 })
      setCompanies(res.data.items)
      setTotal(res.data.total)
      setPages(res.data.pages)
    } catch {
      toast.error('企業一覧の取得に失敗しました')
    } finally {
      setLoading(false)
    }
  }, [page])

  useEffect(() => { fetchData() }, [fetchData])

  const openCreate = () => {
    setEditing(null)
    setForm({ name: '', company_type: 'client', address: '', phone: '', email: '', website: '', notes: '' })
    setShowModal(true)
  }

  const openEdit = (c: Company) => {
    setEditing(c)
    setForm({
      name: c.name,
      company_type: c.company_type,
      address: c.address || '',
      phone: c.phone || '',
      email: c.email || '',
      website: c.website || '',
      notes: c.notes || '',
    })
    setShowModal(true)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      if (editing) {
        await companiesApi.update(editing.id, form)
        toast.success('企業を更新しました')
      } else {
        await companiesApi.create(form)
        toast.success('企業を作成しました')
      }
      setShowModal(false)
      fetchData()
    } catch {
      toast.error('保存に失敗しました')
    }
  }

  const handleDelete = async (id: number) => {
    if (!window.confirm('この企業を削除しますか？')) return
    try {
      await companiesApi.delete(id)
      toast.success('企業を削除しました')
      fetchData()
    } catch {
      toast.error('削除に失敗しました')
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold">企業管理</h2>
        <button onClick={openCreate} className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
          <Plus size={18} /> 新規作成
        </button>
      </div>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="text-left px-4 py-3 font-medium text-gray-600">ID</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">企業名</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">種別</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">メール</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">電話</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">ステータス</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">操作</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={7} className="text-center py-8 text-gray-500">読み込み中...</td></tr>
            ) : companies.length === 0 ? (
              <tr><td colSpan={7} className="text-center py-8 text-gray-500">データがありません</td></tr>
            ) : companies.map((c) => (
              <tr key={c.id} className="border-b hover:bg-gray-50">
                <td className="px-4 py-3">{c.id}</td>
                <td className="px-4 py-3 font-medium">{c.name}</td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${companyTypeBadge[c.company_type] || 'bg-gray-100 text-gray-800'}`}>
                    {companyTypeLabels[c.company_type] || c.company_type}
                  </span>
                </td>
                <td className="px-4 py-3 text-gray-500">{c.email || '-'}</td>
                <td className="px-4 py-3 text-gray-500">{c.phone || '-'}</td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${c.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                    {c.is_active ? '有効' : '無効'}
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

        {/* Pagination */}
        <div className="flex items-center justify-between px-4 py-3 border-t bg-gray-50">
          <span className="text-sm text-gray-600">全{total}件中 {(page - 1) * 20 + 1}-{Math.min(page * 20, total)}件</span>
          <div className="flex items-center gap-2">
            <button onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page <= 1} className="p-1 rounded hover:bg-gray-200 disabled:opacity-50"><ChevronLeft size={18} /></button>
            <span className="text-sm">{page} / {pages}</span>
            <button onClick={() => setPage((p) => Math.min(pages, p + 1))} disabled={page >= pages} className="p-1 rounded hover:bg-gray-200 disabled:opacity-50"><ChevronRight size={18} /></button>
          </div>
        </div>
      </div>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-lg max-h-[90vh] overflow-auto">
            <div className="p-6">
              <h3 className="text-lg font-bold mb-4">{editing ? '企業を編集' : '企業を新規作成'}</h3>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">企業名 *</label>
                  <input type="text" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">種別 *</label>
                  <select value={form.company_type} onChange={(e) => setForm({ ...form, company_type: e.target.value })} className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none">
                    <option value="client">クライアント</option>
                    <option value="vendor">ベンダー</option>
                    <option value="ses">SES</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">住所</label>
                  <input type="text" value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none" />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">メール</label>
                    <input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">電話</label>
                    <input type="text" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none" />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Webサイト</label>
                  <input type="url" value={form.website} onChange={(e) => setForm({ ...form, website: e.target.value })} className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none" />
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
