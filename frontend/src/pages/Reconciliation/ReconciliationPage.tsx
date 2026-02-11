import { useState, useEffect, useCallback, useRef } from 'react'
import api from '../../services/api'
import { Upload } from 'lucide-react'
import toast from 'react-hot-toast'

interface PaymentItem {
  id: number
  invoice_id: number | null
  invoice_number: string | null
  payment_date: string
  amount: number
  payer_name: string | null
  reference_number: string | null
  bank_name: string | null
  status: string
  notes: string | null
}

interface Summary {
  total_payments: number
  matched: number
  unmatched: number
  confirmed: number
  total_amount: number
  matched_amount: number
}

interface Invoice {
  id: number
  invoice_number: string
  total_amount: number
  status: string
}

const STATUS_LABELS: Record<string, string> = {
  unmatched: '未消込',
  matched: '消込済(未確定)',
  confirmed: '確定',
}

const STATUS_COLORS: Record<string, string> = {
  unmatched: 'bg-red-100 text-red-700',
  matched: 'bg-yellow-100 text-yellow-700',
  confirmed: 'bg-green-100 text-green-700',
}

export default function ReconciliationPage() {
  const [payments, setPayments] = useState<PaymentItem[]>([])
  const [summary, setSummary] = useState<Summary | null>(null)
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState('')
  const [importing, setImporting] = useState(false)
  const [showImportModal, setShowImportModal] = useState(false)
  const [importResult, setImportResult] = useState<{ imported_count: number } | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [matching, setMatching] = useState(false)
  const [matchModal, setMatchModal] = useState<PaymentItem | null>(null)
  const [invoices, setInvoices] = useState<Invoice[]>([])
  const [selectedInvoiceId, setSelectedInvoiceId] = useState<number | null>(null)

  const fetchPayments = useCallback(async () => {
    try {
      const params: Record<string, string | number> = { page, per_page: 20 }
      if (statusFilter) params.status = statusFilter
      const res = await api.get('/reconciliation', { params })
      setPayments(res.data.items)
      setTotal(res.data.total)
    } catch {
      // ignore
    }
  }, [page, statusFilter])

  const fetchSummary = async () => {
    try {
      const res = await api.get('/reconciliation/summary')
      setSummary(res.data)
    } catch {
      // ignore
    }
  }

  useEffect(() => {
    fetchPayments()
    fetchSummary()
  }, [fetchPayments])

  const handleImportCsv = async (file: File) => {
    setImporting(true)
    setImportResult(null)
    try {
      const formData = new FormData()
      formData.append('file', file)
      const res = await api.post('/reconciliation/import', formData)
      setImportResult(res.data)
      toast.success(`${res.data.imported_count}件の入金データをインポートしました`)
      fetchPayments()
      fetchSummary()
    } catch {
      toast.error('CSVインポートに失敗しました')
    } finally {
      setImporting(false)
    }
  }

  const handleAutoMatch = async () => {
    setMatching(true)
    try {
      const res = await api.post('/reconciliation/match')
      alert(res.data.message)
      fetchPayments()
      fetchSummary()
    } catch {
      alert('自動消込に失敗しました')
    } finally {
      setMatching(false)
    }
  }

  const handleConfirm = async (paymentId: number) => {
    try {
      await api.post(`/reconciliation/${paymentId}/confirm`)
      fetchPayments()
      fetchSummary()
    } catch {
      alert('確定に失敗しました')
    }
  }

  const handleUnmatch = async (paymentId: number) => {
    try {
      await api.post(`/reconciliation/${paymentId}/unmatch`)
      fetchPayments()
      fetchSummary()
    } catch {
      alert('取消に失敗しました')
    }
  }

  const openManualMatch = async (payment: PaymentItem) => {
    setMatchModal(payment)
    setSelectedInvoiceId(null)
    try {
      const res = await api.get('/invoices', { params: { status: 'sent', per_page: 100 } })
      setInvoices(res.data.items)
    } catch {
      setInvoices([])
    }
  }

  const handleManualMatch = async () => {
    if (!matchModal || !selectedInvoiceId) return
    try {
      await api.post(`/reconciliation/${matchModal.id}/match`, { invoice_id: selectedInvoiceId })
      setMatchModal(null)
      fetchPayments()
      fetchSummary()
    } catch {
      alert('マッチングに失敗しました')
    }
  }

  const totalPages = Math.ceil(total / 20)
  const fmt = (n: number) => n.toLocaleString()

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">入金消込</h1>

      {/* Summary */}
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
          <div className="bg-white rounded-lg shadow p-4 text-center">
            <p className="text-sm text-gray-500">入金総件数</p>
            <p className="text-2xl font-bold">{summary.total_payments}</p>
          </div>
          <div className="bg-white rounded-lg shadow p-4 text-center">
            <p className="text-sm text-gray-500">未消込</p>
            <p className="text-2xl font-bold text-red-600">{summary.unmatched}</p>
          </div>
          <div className="bg-white rounded-lg shadow p-4 text-center">
            <p className="text-sm text-gray-500">消込済</p>
            <p className="text-2xl font-bold text-yellow-600">{summary.matched}</p>
          </div>
          <div className="bg-white rounded-lg shadow p-4 text-center">
            <p className="text-sm text-gray-500">確定</p>
            <p className="text-2xl font-bold text-green-600">{summary.confirmed}</p>
          </div>
          <div className="bg-white rounded-lg shadow p-4 text-center">
            <p className="text-sm text-gray-500">入金総額</p>
            <p className="text-lg font-bold">¥{fmt(summary.total_amount)}</p>
          </div>
          <div className="bg-white rounded-lg shadow p-4 text-center">
            <p className="text-sm text-gray-500">消込済額</p>
            <p className="text-lg font-bold text-green-600">¥{fmt(summary.matched_amount)}</p>
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="flex flex-wrap gap-3">
        <button
          onClick={() => { setImportResult(null); setShowImportModal(true) }}
          className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 text-sm"
        >
          <Upload size={16} /> CSVインポート
        </button>
        <button
          onClick={handleAutoMatch}
          disabled={matching}
          className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 disabled:opacity-50 text-sm"
        >
          {matching ? '消込実行中...' : '自動消込実行'}
        </button>
        <select
          value={statusFilter}
          onChange={(e) => { setStatusFilter(e.target.value); setPage(1) }}
          className="border rounded-lg px-3 py-2 text-sm"
        >
          <option value="">全ステータス</option>
          <option value="unmatched">未消込</option>
          <option value="matched">消込済(未確定)</option>
          <option value="confirmed">確定</option>
        </select>
      </div>

      {/* Table */}
      <div className="bg-white rounded-lg shadow overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b text-left text-gray-500 bg-gray-50">
              <th className="p-3">入金日</th>
              <th className="p-3">金額</th>
              <th className="p-3">振込人</th>
              <th className="p-3">参照番号</th>
              <th className="p-3">請求番号</th>
              <th className="p-3">ステータス</th>
              <th className="p-3">操作</th>
            </tr>
          </thead>
          <tbody>
            {payments.length === 0 ? (
              <tr>
                <td colSpan={7} className="p-8 text-center text-gray-400">
                  入金データがありません。CSVファイルをインポートしてください。
                </td>
              </tr>
            ) : (
              payments.map((p) => (
                <tr key={p.id} className="border-b hover:bg-gray-50">
                  <td className="p-3">{p.payment_date}</td>
                  <td className="p-3 font-mono">¥{fmt(p.amount)}</td>
                  <td className="p-3">{p.payer_name || '-'}</td>
                  <td className="p-3 text-xs">{p.reference_number || '-'}</td>
                  <td className="p-3">{p.invoice_number || '-'}</td>
                  <td className="p-3">
                    <span className={`px-2 py-1 rounded text-xs ${STATUS_COLORS[p.status] || 'bg-gray-100'}`}>
                      {STATUS_LABELS[p.status] || p.status}
                    </span>
                  </td>
                  <td className="p-3 space-x-2">
                    {p.status === 'unmatched' && (
                      <button
                        onClick={() => openManualMatch(p)}
                        className="text-blue-600 hover:text-blue-800 text-xs"
                      >
                        手動消込
                      </button>
                    )}
                    {p.status === 'matched' && (
                      <>
                        <button
                          onClick={() => handleConfirm(p.id)}
                          className="text-green-600 hover:text-green-800 text-xs"
                        >
                          確定
                        </button>
                        <button
                          onClick={() => handleUnmatch(p.id)}
                          className="text-red-500 hover:text-red-700 text-xs"
                        >
                          取消
                        </button>
                      </>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex justify-center gap-2">
          <button onClick={() => setPage(Math.max(1, page - 1))} disabled={page === 1} className="px-3 py-1 border rounded disabled:opacity-50 text-sm">前へ</button>
          <span className="px-3 py-1 text-sm">{page} / {totalPages}</span>
          <button onClick={() => setPage(Math.min(totalPages, page + 1))} disabled={page === totalPages} className="px-3 py-1 border rounded disabled:opacity-50 text-sm">次へ</button>
        </div>
      )}

      {/* CSV Import Modal */}
      {showImportModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-lg max-h-[90vh] overflow-auto">
            <div className="p-6">
              <h3 className="text-lg font-bold mb-4">入金CSVインポート</h3>

              {!importResult ? (
                <div>
                  <div
                    className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center cursor-pointer hover:border-blue-400 hover:bg-blue-50 transition"
                    onClick={() => fileInputRef.current?.click()}
                    onDragOver={(e) => e.preventDefault()}
                    onDrop={(e) => {
                      e.preventDefault()
                      const f = e.dataTransfer.files[0]
                      if (f?.name.toLowerCase().endsWith('.csv')) handleImportCsv(f)
                      else toast.error('CSVファイルを選択してください')
                    }}
                  >
                    <Upload size={40} className="mx-auto text-gray-400 mb-3" />
                    {importing ? (
                      <p className="text-blue-600 font-medium">インポート中...</p>
                    ) : (
                      <>
                        <p className="text-gray-600 font-medium">CSVファイルをドラッグ&ドロップ</p>
                        <p className="text-gray-400 text-sm mt-1">またはクリックして選択</p>
                        <p className="text-gray-400 text-xs mt-2">UTF-8 / Shift-JIS 対応</p>
                      </>
                    )}
                  </div>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".csv"
                    className="hidden"
                    onChange={(e) => {
                      const f = e.target.files?.[0]
                      if (f) handleImportCsv(f)
                      e.target.value = ''
                    }}
                  />
                </div>
              ) : (
                <div>
                  <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-center">
                    <p className="text-green-700 font-medium text-lg">{importResult.imported_count}件</p>
                    <p className="text-green-600 text-sm">の入金データをインポートしました</p>
                  </div>
                  <div className="flex justify-end gap-3 pt-4">
                    <button
                      onClick={() => { setImportResult(null) }}
                      className="px-4 py-2 border rounded-lg hover:bg-gray-50 text-sm"
                    >
                      続けてインポート
                    </button>
                    <button
                      onClick={() => setShowImportModal(false)}
                      className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm"
                    >
                      閉じる
                    </button>
                  </div>
                </div>
              )}

              {!importResult && (
                <div className="flex justify-end pt-4">
                  <button onClick={() => setShowImportModal(false)} className="text-sm text-gray-500 hover:text-gray-700">閉じる</button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Manual Match Modal */}
      {matchModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-lg mx-4">
            <h3 className="text-lg font-semibold mb-4">手動消込</h3>
            <div className="mb-4 text-sm">
              <p><strong>入金日:</strong> {matchModal.payment_date}</p>
              <p><strong>金額:</strong> ¥{fmt(matchModal.amount)}</p>
              <p><strong>振込人:</strong> {matchModal.payer_name || '-'}</p>
            </div>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">請求書を選択</label>
              <select
                value={selectedInvoiceId ?? ''}
                onChange={(e) => setSelectedInvoiceId(Number(e.target.value) || null)}
                className="w-full border rounded-lg px-3 py-2"
              >
                <option value="">選択してください</option>
                {invoices.map((inv) => (
                  <option key={inv.id} value={inv.id}>
                    {inv.invoice_number} - ¥{fmt(inv.total_amount)}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex gap-3 justify-end">
              <button onClick={() => setMatchModal(null)} className="px-4 py-2 border rounded-lg text-sm">キャンセル</button>
              <button
                onClick={handleManualMatch}
                disabled={!selectedInvoiceId}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 text-sm"
              >
                マッチング
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
