import { useState, useEffect, useCallback } from 'react'
import { engineersApi } from '../../services/engineers'
import { Engineer } from '../../types'
import { Plus, Pencil, Trash2, ChevronLeft, ChevronRight } from 'lucide-react'
import toast from 'react-hot-toast'

const statusLabels: Record<string, string> = {
  available: '稼働可能',
  assigned: 'アサイン済',
  unavailable: '稼働不可',
}

const statusBadge: Record<string, string> = {
  available: 'bg-green-100 text-green-800',
  assigned: 'bg-blue-100 text-blue-800',
  unavailable: 'bg-red-100 text-red-800',
}

export default function EngineersPage() {
  const [engineers, setEngineers] = useState<Engineer[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pages, setPages] = useState(1)
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [editing, setEditing] = useState<Engineer | null>(null)
  const [form, setForm] = useState({
    full_name: '', email: '', phone: '', hourly_rate: '', monthly_rate: '',
    availability_status: 'available', years_of_experience: '', notes: '',
  })

  const fetchData = useCallback(async () => {
    setLoading(true)
    try {
      const res = await engineersApi.list({ page, per_page: 20 })
      setEngineers(res.data.items)
      setTotal(res.data.total)
      setPages(res.data.pages)
    } catch {
      toast.error('エンジニア一覧の取得に失敗しました')
    } finally {
      setLoading(false)
    }
  }, [page])

  useEffect(() => { fetchData() }, [fetchData])

  const openCreate = () => {
    setEditing(null)
    setForm({ full_name: '', email: '', phone: '', hourly_rate: '', monthly_rate: '', availability_status: 'available', years_of_experience: '', notes: '' })
    setShowModal(true)
  }

  const openEdit = (eng: Engineer) => {
    setEditing(eng)
    setForm({
      full_name: eng.full_name,
      email: eng.email,
      phone: eng.phone || '',
      hourly_rate: eng.hourly_rate?.toString() || '',
      monthly_rate: eng.monthly_rate?.toString() || '',
      availability_status: eng.availability_status,
      years_of_experience: eng.years_of_experience?.toString() || '',
      notes: eng.notes || '',
    })
    setShowModal(true)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const payload = {
      full_name: form.full_name,
      email: form.email,
      phone: form.phone || null,
      hourly_rate: form.hourly_rate ? Number(form.hourly_rate) : null,
      monthly_rate: form.monthly_rate ? Number(form.monthly_rate) : null,
      availability_status: form.availability_status,
      years_of_experience: form.years_of_experience ? Number(form.years_of_experience) : null,
      notes: form.notes || null,
    }
    try {
      if (editing) {
        await engineersApi.update(editing.id, payload)
        toast.success('エンジニアを更新しました')
      } else {
        await engineersApi.create(payload)
        toast.success('エンジニアを作成しました')
      }
      setShowModal(false)
      fetchData()
    } catch {
      toast.error('保存に失敗しました')
    }
  }

  const handleDelete = async (id: number) => {
    if (!window.confirm('このエンジニアを削除しますか？')) return
    try {
      await engineersApi.delete(id)
      toast.success('エンジニアを削除しました')
      fetchData()
    } catch {
      toast.error('削除に失敗しました')
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold">エンジニア管理</h2>
        <button onClick={openCreate} className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
          <Plus size={18} /> 新規作成
        </button>
      </div>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="text-left px-4 py-3 font-medium text-gray-600">ID</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">氏名</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">メール</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">所属企業</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">月単価</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">経験年数</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">スキル</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">ステータス</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">操作</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={9} className="text-center py-8 text-gray-500">読み込み中...</td></tr>
            ) : engineers.length === 0 ? (
              <tr><td colSpan={9} className="text-center py-8 text-gray-500">データがありません</td></tr>
            ) : engineers.map((eng) => (
              <tr key={eng.id} className="border-b hover:bg-gray-50">
                <td className="px-4 py-3">{eng.id}</td>
                <td className="px-4 py-3 font-medium">{eng.full_name}</td>
                <td className="px-4 py-3 text-gray-500">{eng.email}</td>
                <td className="px-4 py-3 text-gray-500">{eng.company?.name || '-'}</td>
                <td className="px-4 py-3">{eng.monthly_rate ? `${eng.monthly_rate.toLocaleString()}円` : '-'}</td>
                <td className="px-4 py-3">{eng.years_of_experience != null ? `${eng.years_of_experience}年` : '-'}</td>
                <td className="px-4 py-3">
                  <div className="flex flex-wrap gap-1">
                    {eng.skills.slice(0, 3).map((s) => (
                      <span key={s.id} className="px-1.5 py-0.5 bg-gray-100 text-gray-700 rounded text-xs">{s.name}</span>
                    ))}
                    {eng.skills.length > 3 && <span className="text-xs text-gray-400">+{eng.skills.length - 3}</span>}
                  </div>
                </td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusBadge[eng.availability_status] || 'bg-gray-100 text-gray-800'}`}>
                    {statusLabels[eng.availability_status] || eng.availability_status}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <button onClick={() => openEdit(eng)} className="text-gray-500 hover:text-blue-600"><Pencil size={16} /></button>
                    <button onClick={() => handleDelete(eng.id)} className="text-gray-500 hover:text-red-600"><Trash2 size={16} /></button>
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
              <h3 className="text-lg font-bold mb-4">{editing ? 'エンジニアを編集' : 'エンジニアを新規作成'}</h3>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">氏名 *</label>
                  <input type="text" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} required className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">メールアドレス *</label>
                  <input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">電話番号</label>
                  <input type="text" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none" />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">時間単価 (円)</label>
                    <input type="number" value={form.hourly_rate} onChange={(e) => setForm({ ...form, hourly_rate: e.target.value })} className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">月単価 (円)</label>
                    <input type="number" value={form.monthly_rate} onChange={(e) => setForm({ ...form, monthly_rate: e.target.value })} className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none" />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">ステータス</label>
                    <select value={form.availability_status} onChange={(e) => setForm({ ...form, availability_status: e.target.value })} className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none">
                      <option value="available">稼働可能</option>
                      <option value="assigned">アサイン済</option>
                      <option value="unavailable">稼働不可</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">経験年数</label>
                    <input type="number" value={form.years_of_experience} onChange={(e) => setForm({ ...form, years_of_experience: e.target.value })} className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none" />
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
