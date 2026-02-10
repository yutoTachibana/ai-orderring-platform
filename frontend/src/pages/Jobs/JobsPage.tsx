import { useState, useEffect, useCallback } from 'react'
import api from '../../services/api'
import { ProcessingJob } from '../../types'
import { ChevronLeft, ChevronRight, ChevronDown, ChevronUp, RefreshCw } from 'lucide-react'
import toast from 'react-hot-toast'

const statusLabels: Record<string, string> = {
  received: '受信',
  parsing: '解析中',
  routing: 'ルーティング中',
  pending_approval: '承認待ち',
  executing: '実行中',
  completed: '完了',
  failed: '失敗',
}

const statusBadge: Record<string, string> = {
  received: 'bg-gray-100 text-gray-800',
  parsing: 'bg-blue-100 text-blue-800',
  routing: 'bg-indigo-100 text-indigo-800',
  pending_approval: 'bg-yellow-100 text-yellow-800',
  executing: 'bg-purple-100 text-purple-800',
  completed: 'bg-green-100 text-green-800',
  failed: 'bg-red-100 text-red-800',
}

export default function JobsPage() {
  const [jobs, setJobs] = useState<ProcessingJob[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pages, setPages] = useState(1)
  const [loading, setLoading] = useState(true)
  const [expandedId, setExpandedId] = useState<number | null>(null)

  const fetchData = useCallback(async () => {
    setLoading(true)
    try {
      const res = await api.get('/jobs', { params: { page, per_page: 20 } })
      setJobs(res.data.items)
      setTotal(res.data.total)
      setPages(res.data.pages)
    } catch {
      toast.error('ジョブ一覧の取得に失敗しました')
    } finally {
      setLoading(false)
    }
  }, [page])

  useEffect(() => { fetchData() }, [fetchData])

  const handleApprove = async (jobId: number) => {
    try {
      await api.post(`/jobs/${jobId}/approve`)
      toast.success('ジョブを承認しました')
      fetchData()
    } catch {
      toast.error('承認に失敗しました')
    }
  }

  const handleReject = async (jobId: number) => {
    if (!window.confirm('このジョブを却下しますか？')) return
    try {
      await api.post(`/jobs/${jobId}/reject`)
      toast.success('ジョブを却下しました')
      fetchData()
    } catch {
      toast.error('却下に失敗しました')
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold">処理ジョブ</h2>
        <button onClick={fetchData} className="flex items-center gap-2 px-4 py-2 border rounded-lg hover:bg-gray-50">
          <RefreshCw size={18} /> 更新
        </button>
      </div>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="w-10 px-4 py-3"></th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">ID</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">ステータス</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">割当システム</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Slackメッセージ</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Excelファイル</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">作成日時</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">操作</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={8} className="text-center py-8 text-gray-500">読み込み中...</td></tr>
            ) : jobs.length === 0 ? (
              <tr><td colSpan={8} className="text-center py-8 text-gray-500">データがありません</td></tr>
            ) : jobs.map((job) => (
              <>
                <tr key={job.id} className="border-b hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <button onClick={() => setExpandedId(expandedId === job.id ? null : job.id)} className="text-gray-400 hover:text-gray-600">
                      {expandedId === job.id ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                    </button>
                  </td>
                  <td className="px-4 py-3">{job.id}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusBadge[job.status] || 'bg-gray-100 text-gray-800'}`}>
                      {statusLabels[job.status] || job.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-500">{job.assigned_system || '-'}</td>
                  <td className="px-4 py-3 text-gray-500 text-xs">{job.slack_message_id || '-'}</td>
                  <td className="px-4 py-3 text-gray-500 text-xs">{job.excel_file_path || '-'}</td>
                  <td className="px-4 py-3 text-gray-500 text-xs">{job.created_at}</td>
                  <td className="px-4 py-3">
                    {job.status === 'pending_approval' && (
                      <div className="flex items-center gap-2">
                        <button onClick={() => handleApprove(job.id)} className="px-3 py-1 text-xs bg-green-600 text-white rounded hover:bg-green-700">承認</button>
                        <button onClick={() => handleReject(job.id)} className="px-3 py-1 text-xs bg-red-600 text-white rounded hover:bg-red-700">却下</button>
                      </div>
                    )}
                  </td>
                </tr>
                {expandedId === job.id && (
                  <tr key={`${job.id}-detail`} className="border-b bg-gray-50">
                    <td colSpan={8} className="px-8 py-4">
                      {job.error_message && (
                        <div className="mb-3 p-3 bg-red-50 border border-red-200 rounded-lg">
                          <p className="text-sm font-medium text-red-800">エラー</p>
                          <p className="text-sm text-red-600 mt-1">{job.error_message}</p>
                        </div>
                      )}
                      {job.result && (
                        <div className="mb-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                          <p className="text-sm font-medium text-blue-800">結果</p>
                          <pre className="text-xs text-blue-600 mt-1 overflow-auto">{JSON.stringify(job.result, null, 2)}</pre>
                        </div>
                      )}
                      <div>
                        <p className="text-sm font-medium text-gray-700 mb-2">処理ログ</p>
                        {job.logs && job.logs.length > 0 ? (
                          <div className="space-y-1">
                            {job.logs.map((log) => (
                              <div key={log.id} className="flex items-start gap-3 text-xs p-2 bg-white rounded border">
                                <span className="text-gray-400 whitespace-nowrap">{log.created_at}</span>
                                <span className={`px-1.5 py-0.5 rounded font-medium ${log.status === 'success' ? 'bg-green-100 text-green-700' : log.status === 'error' ? 'bg-red-100 text-red-700' : 'bg-gray-100 text-gray-700'}`}>
                                  {log.step_name}
                                </span>
                                <span className="text-gray-600">{log.message}</span>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <p className="text-xs text-gray-400">ログがありません</p>
                        )}
                      </div>
                    </td>
                  </tr>
                )}
              </>
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
    </div>
  )
}
