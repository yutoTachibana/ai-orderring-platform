import { useState, useEffect } from 'react'
import api from '../../services/api'

interface ReportType {
  type: string
  label: string
  description: string
}

interface Schedule {
  id: number
  name: string
  report_type: string
  cron_expression: string
  recipients: string[] | null
  output_format: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export default function ReportsPage() {
  const [reportTypes, setReportTypes] = useState<ReportType[]>([])
  const [schedules, setSchedules] = useState<Schedule[]>([])
  const [selectedType, setSelectedType] = useState('monthly_summary')
  const [year, setYear] = useState(new Date().getFullYear())
  const [month, setMonth] = useState(new Date().getMonth() + 1)
  const [generating, setGenerating] = useState(false)

  // Schedule form
  const [showScheduleForm, setShowScheduleForm] = useState(false)
  const [scheduleForm, setScheduleForm] = useState({
    name: '',
    report_type: 'monthly_summary',
    cron_expression: '0 9 1 * *',
    recipients: '',
    output_format: 'excel',
  })

  useEffect(() => {
    fetchReportTypes()
    fetchSchedules()
  }, [])

  const fetchReportTypes = async () => {
    try {
      const res = await api.get('/reports/types')
      setReportTypes(res.data)
    } catch {
      // ignore
    }
  }

  const fetchSchedules = async () => {
    try {
      const res = await api.get('/reports/schedules')
      setSchedules(res.data.items)
    } catch {
      // ignore
    }
  }

  const handleGenerate = async () => {
    setGenerating(true)
    try {
      const res = await api.post(
        '/reports/generate',
        { report_type: selectedType, year, month },
        { responseType: 'blob' }
      )
      const url = window.URL.createObjectURL(new Blob([res.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `report_${selectedType}_${year}_${String(month).padStart(2, '0')}.xlsx`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch {
      alert('レポート生成に失敗しました')
    } finally {
      setGenerating(false)
    }
  }

  const handleCreateSchedule = async () => {
    try {
      await api.post('/reports/schedules', {
        ...scheduleForm,
        recipients: scheduleForm.recipients
          ? scheduleForm.recipients.split(',').map((s) => s.trim())
          : null,
      })
      setShowScheduleForm(false)
      setScheduleForm({
        name: '',
        report_type: 'monthly_summary',
        cron_expression: '0 9 1 * *',
        recipients: '',
        output_format: 'excel',
      })
      fetchSchedules()
    } catch {
      alert('スケジュール作成に失敗しました')
    }
  }

  const handleToggleSchedule = async (schedule: Schedule) => {
    try {
      await api.put(`/reports/schedules/${schedule.id}`, {
        is_active: !schedule.is_active,
      })
      fetchSchedules()
    } catch {
      alert('更新に失敗しました')
    }
  }

  const handleDeleteSchedule = async (id: number) => {
    if (!confirm('このスケジュールを削除しますか？')) return
    try {
      await api.delete(`/reports/schedules/${id}`)
      fetchSchedules()
    } catch {
      alert('削除に失敗しました')
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">レポート</h1>

      {/* Generate Report */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold mb-4">レポート生成</h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">レポートタイプ</label>
            <select
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value)}
              className="w-full border rounded-lg px-3 py-2"
            >
              {reportTypes.map((t) => (
                <option key={t.type} value={t.type}>
                  {t.label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">年</label>
            <input
              type="number"
              value={year}
              onChange={(e) => setYear(Number(e.target.value))}
              className="w-full border rounded-lg px-3 py-2"
              min={2020}
              max={2099}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">月</label>
            <select
              value={month}
              onChange={(e) => setMonth(Number(e.target.value))}
              className="w-full border rounded-lg px-3 py-2"
            >
              {Array.from({ length: 12 }, (_, i) => i + 1).map((m) => (
                <option key={m} value={m}>
                  {m}月
                </option>
              ))}
            </select>
          </div>
          <div>
            <button
              onClick={handleGenerate}
              disabled={generating}
              className="w-full bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {generating ? '生成中...' : 'レポート生成・ダウンロード'}
            </button>
          </div>
        </div>
        {reportTypes.find((t) => t.type === selectedType) && (
          <p className="mt-2 text-sm text-gray-500">
            {reportTypes.find((t) => t.type === selectedType)?.description}
          </p>
        )}
      </div>

      {/* Schedules */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">自動生成スケジュール</h2>
          <button
            onClick={() => setShowScheduleForm(!showScheduleForm)}
            className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 text-sm"
          >
            {showScheduleForm ? 'キャンセル' : '+ 新規スケジュール'}
          </button>
        </div>

        {showScheduleForm && (
          <div className="border rounded-lg p-4 mb-4 bg-gray-50">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">スケジュール名</label>
                <input
                  type="text"
                  value={scheduleForm.name}
                  onChange={(e) => setScheduleForm({ ...scheduleForm, name: e.target.value })}
                  className="w-full border rounded-lg px-3 py-2"
                  placeholder="月次レポート"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">レポートタイプ</label>
                <select
                  value={scheduleForm.report_type}
                  onChange={(e) => setScheduleForm({ ...scheduleForm, report_type: e.target.value })}
                  className="w-full border rounded-lg px-3 py-2"
                >
                  <option value="monthly_summary">月次サマリーレポート</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Cron式</label>
                <input
                  type="text"
                  value={scheduleForm.cron_expression}
                  onChange={(e) => setScheduleForm({ ...scheduleForm, cron_expression: e.target.value })}
                  className="w-full border rounded-lg px-3 py-2"
                  placeholder="0 9 1 * *"
                />
                <p className="text-xs text-gray-400 mt-1">例: 0 9 1 * * = 毎月1日 9:00</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">送信先 (カンマ区切り)</label>
                <input
                  type="text"
                  value={scheduleForm.recipients}
                  onChange={(e) => setScheduleForm({ ...scheduleForm, recipients: e.target.value })}
                  className="w-full border rounded-lg px-3 py-2"
                  placeholder="user@example.com, admin@example.com"
                />
              </div>
            </div>
            <div className="mt-4 flex justify-end">
              <button
                onClick={handleCreateSchedule}
                disabled={!scheduleForm.name}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                作成
              </button>
            </div>
          </div>
        )}

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-left text-gray-500">
                <th className="pb-2">名前</th>
                <th className="pb-2">タイプ</th>
                <th className="pb-2">Cron式</th>
                <th className="pb-2">送信先</th>
                <th className="pb-2">状態</th>
                <th className="pb-2">操作</th>
              </tr>
            </thead>
            <tbody>
              {schedules.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-gray-400">
                    スケジュールがありません
                  </td>
                </tr>
              ) : (
                schedules.map((s) => (
                  <tr key={s.id} className="border-b">
                    <td className="py-3">{s.name}</td>
                    <td className="py-3">{s.report_type}</td>
                    <td className="py-3 font-mono text-xs">{s.cron_expression}</td>
                    <td className="py-3 text-xs">{s.recipients?.join(', ') || '-'}</td>
                    <td className="py-3">
                      <button
                        onClick={() => handleToggleSchedule(s)}
                        className={`px-2 py-1 rounded text-xs ${
                          s.is_active
                            ? 'bg-green-100 text-green-700'
                            : 'bg-gray-100 text-gray-500'
                        }`}
                      >
                        {s.is_active ? '有効' : '無効'}
                      </button>
                    </td>
                    <td className="py-3">
                      <button
                        onClick={() => handleDeleteSchedule(s.id)}
                        className="text-red-500 hover:text-red-700 text-xs"
                      >
                        削除
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
