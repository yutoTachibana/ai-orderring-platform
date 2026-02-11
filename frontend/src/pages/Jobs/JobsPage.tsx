import { useState, useEffect, useCallback, Fragment } from 'react'
import api from '../../services/api'
import { ProcessingJob, ProcessingLog } from '../../types'
import { ChevronLeft, ChevronRight, ChevronDown, ChevronUp, RefreshCw, Filter } from 'lucide-react'
import toast from 'react-hot-toast'

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

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
  received: 'bg-blue-100 text-blue-800',
  parsing: 'bg-blue-100 text-blue-800',
  routing: 'bg-blue-100 text-blue-800',
  pending_approval: 'bg-amber-100 text-amber-800',
  executing: 'bg-indigo-100 text-indigo-800',
  completed: 'bg-green-100 text-green-800',
  failed: 'bg-red-100 text-red-800',
}

/** Pipeline steps in the canonical order. */
const PIPELINE_STEPS = [
  { key: '受信', label: '受信' },
  { key: '解析', label: '解析' },
  { key: '振り分け', label: '振り分け' },
  { key: 'データ登録', label: 'データ登録' },
  { key: 'Web入力', label: 'Web入力' },
  { key: '完了', label: '完了' },
] as const

type StepStatus = 'completed' | 'failed' | 'pending'

const filterOptions: { value: string; label: string }[] = [
  { value: 'all', label: 'すべて' },
  { value: 'pending_approval', label: '承認待ち' },
  { value: 'executing', label: '実行中' },
  { value: 'completed', label: '完了' },
  { value: 'failed', label: '失敗' },
]

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/**
 * Derive the status of each pipeline step from the job's logs.
 *
 * A step is "completed" if there is a log whose step_name contains the key
 * and whose status is "success".  It is "failed" if the log status is "error".
 * Otherwise it is "pending".
 */
function deriveStepStatuses(logs: ProcessingLog[]): Record<string, StepStatus> {
  const result: Record<string, StepStatus> = {}
  for (const step of PIPELINE_STEPS) {
    const matching = logs.filter((l) => l.step_name.includes(step.key))
    if (matching.some((l) => l.status === 'failed' || l.status === 'error')) {
      result[step.key] = 'failed'
    } else if (matching.some((l) => l.status === 'completed' || l.status === 'success' || l.status === 'started')) {
      result[step.key] = 'completed'
    } else {
      result[step.key] = 'pending'
    }
  }
  return result
}

function stepDotClass(status: StepStatus): string {
  switch (status) {
    case 'completed':
      return 'bg-green-500 border-green-600'
    case 'failed':
      return 'bg-red-500 border-red-600'
    default:
      return 'bg-gray-300 border-gray-400'
  }
}

function stepLabelClass(status: StepStatus): string {
  switch (status) {
    case 'completed':
      return 'text-green-700 font-medium'
    case 'failed':
      return 'text-red-700 font-medium'
    default:
      return 'text-gray-400'
  }
}

function connectorClass(status: StepStatus): string {
  switch (status) {
    case 'completed':
      return 'bg-green-400'
    case 'failed':
      return 'bg-red-400'
    default:
      return 'bg-gray-200'
  }
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function PipelineIndicator({ logs }: { logs: ProcessingLog[] }) {
  const statuses = deriveStepStatuses(logs)
  return (
    <div className="flex items-center gap-0">
      {PIPELINE_STEPS.map((step, idx) => {
        const st = statuses[step.key]
        return (
          <Fragment key={step.key}>
            <div className="flex flex-col items-center min-w-[64px]">
              <div
                className={`w-6 h-6 rounded-full border-2 flex items-center justify-center ${stepDotClass(st)}`}
              >
                {st === 'completed' && (
                  <svg className="w-3.5 h-3.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                )}
                {st === 'failed' && (
                  <svg className="w-3.5 h-3.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                )}
              </div>
              <span className={`mt-1 text-[11px] leading-tight ${stepLabelClass(st)}`}>
                {step.label}
              </span>
            </div>
            {idx < PIPELINE_STEPS.length - 1 && (
              <div className={`h-0.5 w-6 -mt-4 ${connectorClass(st)}`} />
            )}
          </Fragment>
        )
      })}
    </div>
  )
}

function McpResultPanel({ result }: { result: Record<string, unknown> }) {
  const mcp = result.mcp_result as Record<string, unknown> | undefined
  if (!mcp) return null

  return (
    <div className="mb-3 p-3 bg-indigo-50 border border-indigo-200 rounded-lg">
      <p className="text-sm font-medium text-indigo-800 mb-2">MCP 実行結果</p>
      <dl className="grid grid-cols-2 gap-x-6 gap-y-1 text-xs">
        {mcp.confirmation_id != null && (
          <>
            <dt className="text-gray-500">確認ID</dt>
            <dd className="text-gray-800 font-mono">{String(mcp.confirmation_id)}</dd>
          </>
        )}
        {(mcp.system ?? mcp.target_system) != null && (
          <>
            <dt className="text-gray-500">対象システム</dt>
            <dd className="text-gray-800">{String(mcp.system ?? mcp.target_system)}</dd>
          </>
        )}
        {mcp.screenshot_path != null && (
          <>
            <dt className="text-gray-500">スクリーンショット</dt>
            <dd className="text-gray-800 font-mono break-all">{String(mcp.screenshot_path)}</dd>
          </>
        )}
        {(mcp.mock ?? mcp.is_mock) != null && (
          <>
            <dt className="text-gray-500">モック</dt>
            <dd className="text-gray-800">{(mcp.mock ?? mcp.is_mock) ? 'はい' : 'いいえ'}</dd>
          </>
        )}
      </dl>
    </div>
  )
}

function RegisteredDataPanel({ logs }: { logs: ProcessingLog[] }) {
  const dataLog = logs.find(
    (l) => l.step_name.includes('データ登録') && (l.status === 'completed' || l.status === 'success'),
  )
  if (!dataLog) return null

  return (
    <div className="mb-3 p-3 bg-emerald-50 border border-emerald-200 rounded-lg">
      <p className="text-sm font-medium text-emerald-800 mb-1">登録データ</p>
      <p className="text-xs text-emerald-700">{dataLog.message}</p>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Main page component
// ---------------------------------------------------------------------------

export default function JobsPage() {
  const [jobs, setJobs] = useState<ProcessingJob[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pages, setPages] = useState(1)
  const [loading, setLoading] = useState(true)
  const [expandedId, setExpandedId] = useState<number | null>(null)
  const [statusFilter, setStatusFilter] = useState<string>('all')

  const fetchData = useCallback(async () => {
    setLoading(true)
    try {
      const params: Record<string, string | number> = { page, per_page: 20 }
      if (statusFilter !== 'all') {
        params.status = statusFilter
      }
      const res = await api.get('/jobs', { params })
      setJobs(res.data.items)
      setTotal(res.data.total)
      setPages(res.data.pages)
    } catch {
      toast.error('ジョブ一覧の取得に失敗しました')
    } finally {
      setLoading(false)
    }
  }, [page, statusFilter])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  // Reset to first page when filter changes
  useEffect(() => {
    setPage(1)
  }, [statusFilter])

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
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold">処理ジョブ</h2>
        <div className="flex items-center gap-3">
          {/* Status filter */}
          <div className="flex items-center gap-2">
            <Filter size={16} className="text-gray-400" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="text-sm border border-gray-300 rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              {filterOptions.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>
          <button
            onClick={fetchData}
            className="flex items-center gap-2 px-4 py-2 border rounded-lg hover:bg-gray-50"
          >
            <RefreshCw size={18} /> 更新
          </button>
        </div>
      </div>

      {/* Table */}
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
              <tr>
                <td colSpan={8} className="text-center py-8 text-gray-500">
                  読み込み中...
                </td>
              </tr>
            ) : jobs.length === 0 ? (
              <tr>
                <td colSpan={8} className="text-center py-8 text-gray-500">
                  データがありません
                </td>
              </tr>
            ) : (
              jobs.map((job) => (
                <Fragment key={job.id}>
                  {/* Summary row */}
                  <tr className="border-b hover:bg-gray-50">
                    <td className="px-4 py-3">
                      <button
                        onClick={() =>
                          setExpandedId(expandedId === job.id ? null : job.id)
                        }
                        className="text-gray-400 hover:text-gray-600"
                      >
                        {expandedId === job.id ? (
                          <ChevronUp size={16} />
                        ) : (
                          <ChevronDown size={16} />
                        )}
                      </button>
                    </td>
                    <td className="px-4 py-3">{job.id}</td>
                    <td className="px-4 py-3">
                      <span
                        className={`px-2 py-1 rounded-full text-xs font-medium ${statusBadge[job.status] || 'bg-gray-100 text-gray-800'}`}
                      >
                        {statusLabels[job.status] || job.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-500">
                      {job.assigned_system || '-'}
                    </td>
                    <td className="px-4 py-3 text-gray-500 text-xs">
                      {job.slack_message_id || '-'}
                    </td>
                    <td className="px-4 py-3 text-gray-500 text-xs">
                      {job.excel_file_path || '-'}
                    </td>
                    <td className="px-4 py-3 text-gray-500 text-xs">
                      {job.created_at}
                    </td>
                    <td className="px-4 py-3">
                      {job.status === 'pending_approval' && (
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => handleApprove(job.id)}
                            className="px-3 py-1 text-xs bg-green-600 text-white rounded hover:bg-green-700"
                          >
                            承認
                          </button>
                          <button
                            onClick={() => handleReject(job.id)}
                            className="px-3 py-1 text-xs bg-red-600 text-white rounded hover:bg-red-700"
                          >
                            却下
                          </button>
                        </div>
                      )}
                    </td>
                  </tr>

                  {/* Expanded detail row */}
                  {expandedId === job.id && (
                    <tr className="border-b bg-gray-50">
                      <td colSpan={8} className="px-8 py-5">
                        {/* 1. Pipeline step indicator */}
                        <div className="mb-4">
                          <p className="text-sm font-medium text-gray-700 mb-3">
                            処理パイプライン
                          </p>
                          <PipelineIndicator logs={job.logs ?? []} />
                        </div>

                        {/* 2. Error message */}
                        {job.error_message && (
                          <div className="mb-3 p-3 bg-red-50 border border-red-200 rounded-lg">
                            <p className="text-sm font-medium text-red-800">
                              エラー
                            </p>
                            <p className="text-sm text-red-600 mt-1">
                              {job.error_message}
                            </p>
                          </div>
                        )}

                        {/* 3. MCP execution results */}
                        {job.result && <McpResultPanel result={job.result} />}

                        {/* 4. Registered data */}
                        {job.logs && job.logs.length > 0 && (
                          <RegisteredDataPanel logs={job.logs} />
                        )}

                        {/* 5. Raw result (show remaining fields for transparency) */}
                        {job.result &&
                          !job.result.mcp_result && (
                            <div className="mb-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                              <p className="text-sm font-medium text-blue-800">
                                結果
                              </p>
                              <pre className="text-xs text-blue-600 mt-1 overflow-auto">
                                {JSON.stringify(job.result, null, 2)}
                              </pre>
                            </div>
                          )}

                        {/* 6. Processing logs */}
                        <div>
                          <p className="text-sm font-medium text-gray-700 mb-2">
                            処理ログ
                          </p>
                          {job.logs && job.logs.length > 0 ? (
                            <div className="space-y-1">
                              {job.logs.map((log) => (
                                <div
                                  key={log.id}
                                  className="flex items-start gap-3 text-xs p-2 bg-white rounded border"
                                >
                                  <span className="text-gray-400 whitespace-nowrap">
                                    {log.created_at}
                                  </span>
                                  <span
                                    className={`px-1.5 py-0.5 rounded font-medium ${
                                      (log.status === 'completed' || log.status === 'success')
                                        ? 'bg-green-100 text-green-700'
                                        : (log.status === 'failed' || log.status === 'error')
                                          ? 'bg-red-100 text-red-700'
                                          : 'bg-gray-100 text-gray-700'
                                    }`}
                                  >
                                    {log.step_name}
                                  </span>
                                  <span className="text-gray-600">
                                    {log.message}
                                  </span>
                                </div>
                              ))}
                            </div>
                          ) : (
                            <p className="text-xs text-gray-400">
                              ログがありません
                            </p>
                          )}
                        </div>
                      </td>
                    </tr>
                  )}
                </Fragment>
              ))
            )}
          </tbody>
        </table>

        {/* Pagination */}
        <div className="flex items-center justify-between px-4 py-3 border-t bg-gray-50">
          <span className="text-sm text-gray-600">
            全{total}件中 {total === 0 ? 0 : (page - 1) * 20 + 1}-
            {Math.min(page * 20, total)}件
          </span>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1}
              className="p-1 rounded hover:bg-gray-200 disabled:opacity-50"
            >
              <ChevronLeft size={18} />
            </button>
            <span className="text-sm">
              {page} / {pages}
            </span>
            <button
              onClick={() => setPage((p) => Math.min(pages, p + 1))}
              disabled={page >= pages}
              className="p-1 rounded hover:bg-gray-200 disabled:opacity-50"
            >
              <ChevronRight size={18} />
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
