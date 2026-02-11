import { useState, useEffect } from 'react'
import api from '../../services/api'
import StatusBadge from '../../components/StatusBadge'
import LoadingSpinner from '../../components/LoadingSpinner'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend, ComposedChart, Line } from 'recharts'

interface DashboardStats {
  total_projects: number
  active_projects: number
  total_engineers: number
  available_engineers: number
  pending_orders: number
  active_contracts: number
  unpaid_invoices: number
  pending_jobs: number
}

interface RecentJob {
  id: number
  status: string
  assigned_system: string | null
  created_at: string | null
  project_name: string | null
  mcp_result: { success: boolean; confirmation_id: string; system: string } | null
  logs: { step: string; status: string; message: string }[]
}

interface RecentProject {
  id: number
  name: string
  status: string
  client: string | null
  created_at: string | null
}

interface RecentOrder {
  id: number
  order_number: string
  status: string
  created_at: string | null
}

interface RecentActivities {
  recent_jobs: RecentJob[]
  recent_projects: RecentProject[]
  recent_orders: RecentOrder[]
}

interface MonthlyTrendItem {
  month: string
  new_projects: number
  new_orders: number
  revenue: number
  invoice_total: number
}

interface AssignedEngineerInfo {
  engineer_id: number
  name: string
  project_name: string | null
  monthly_rate: number | null
  end_date: string | null
}

interface EngineerUtilization {
  available: number
  assigned: number
  unavailable: number
  assigned_engineers: AssignedEngineerInfo[]
}

const PIE_COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#06B6D4']

const UTILIZATION_COLORS = ['#10B981', '#3B82F6', '#9CA3AF']

const formatYen = (value: number): string => {
  if (value >= 10000) {
    return `${(value / 10000).toFixed(0)}万円`
  }
  return `${value.toLocaleString()}円`
}

const monthLabel = (month: string): string => {
  const m = parseInt(month.split('-')[1], 10)
  return `${m}月`
}

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [activities, setActivities] = useState<RecentActivities | null>(null)
  const [monthlyTrends, setMonthlyTrends] = useState<MonthlyTrendItem[]>([])
  const [utilization, setUtilization] = useState<EngineerUtilization | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [statsRes, activitiesRes, trendsRes, utilizationRes] = await Promise.all([
        api.get('/dashboard/stats'),
        api.get('/dashboard/recent-activities'),
        api.get('/dashboard/monthly-trends'),
        api.get('/dashboard/engineer-utilization'),
      ])
      setStats(statsRes.data)
      setActivities(activitiesRes.data)
      setMonthlyTrends(trendsRes.data)
      setUtilization(utilizationRes.data)
    } catch {
      setError('ダッシュボードデータの読み込みに失敗しました')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  if (loading) return <LoadingSpinner size="lg" message="ダッシュボードを読み込み中..." />

  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-red-500 mb-4">{error}</p>
        <button onClick={fetchData} className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700">
          再読み込み
        </button>
      </div>
    )
  }

  if (!stats) return null

  const barChartData = [
    { name: '案件', 進行中: stats.active_projects, 全体: stats.total_projects },
    { name: 'エンジニア', 進行中: stats.available_engineers, 全体: stats.total_engineers },
    { name: '契約', 進行中: stats.active_contracts, 全体: stats.active_contracts + 2 },
  ]

  const pieChartData = [
    { name: '進行中案件', value: stats.active_projects },
    { name: '稼働可能', value: stats.available_engineers },
    { name: '未確認発注', value: stats.pending_orders },
    { name: '有効契約', value: stats.active_contracts },
    { name: '未入金請求', value: stats.unpaid_invoices },
    { name: '処理中ジョブ', value: stats.pending_jobs },
  ].filter(d => d.value > 0)

  const summaryCards = [
    { label: '進行中案件', value: stats.active_projects, total: stats.total_projects, color: 'bg-blue-500', link: '/projects' },
    { label: '稼働可能エンジニア', value: stats.available_engineers, total: stats.total_engineers, color: 'bg-green-500', link: '/engineers' },
    { label: '未確認発注', value: stats.pending_orders, color: 'bg-yellow-500', link: '/orders' },
    { label: '有効契約', value: stats.active_contracts, color: 'bg-purple-500', link: '/contracts' },
    { label: '未入金請求', value: stats.unpaid_invoices, color: 'bg-red-500', link: '/invoices' },
    { label: '処理中ジョブ', value: stats.pending_jobs, color: 'bg-cyan-500', link: '/jobs' },
  ]

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold">ダッシュボード</h2>
        <button onClick={fetchData} className="text-sm text-gray-500 hover:text-blue-600">
          更新
        </button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-8">
        {summaryCards.map((card) => (
          <a key={card.label} href={card.link} className="bg-white rounded-lg shadow p-4 hover:shadow-md transition-shadow group">
            <p className="text-sm text-gray-500 group-hover:text-blue-600">{card.label}</p>
            <div className="flex items-baseline gap-2 mt-1">
              <p className="text-3xl font-bold">{card.value}</p>
              {card.total !== undefined && (
                <p className="text-sm text-gray-400">/ {card.total}</p>
              )}
            </div>
            <div className={`h-1 ${card.color} rounded-full mt-2`} />
          </a>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Bar Chart */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">リソース概況</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={barChartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="進行中" fill="#3B82F6" radius={[4, 4, 0, 0]} />
              <Bar dataKey="全体" fill="#93C5FD" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Pie Chart */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">アクティブ項目の分布</h3>
          {pieChartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={pieChartData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={90}
                  paddingAngle={3}
                  dataKey="value"
                  label={({ name, value }) => `${name}: ${value}`}
                >
                  {pieChartData.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-[250px] text-gray-400 text-sm">
              データがありません
            </div>
          )}
        </div>
      </div>

      {/* Monthly Trends Chart */}
      <div className="bg-white rounded-lg shadow p-6 mb-8">
        <h3 className="text-lg font-semibold mb-4">月次推移グラフ</h3>
        {monthlyTrends.length > 0 ? (
          <ResponsiveContainer width="100%" height={320}>
            <ComposedChart data={monthlyTrends}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" tickFormatter={monthLabel} />
              <YAxis
                yAxisId="left"
                tickFormatter={(v: number) => formatYen(v)}
                width={80}
              />
              <YAxis
                yAxisId="right"
                orientation="right"
                allowDecimals={false}
                label={{ value: '件数', angle: -90, position: 'insideRight', offset: 10 }}
              />
              <Tooltip
                formatter={(value: number, name: string) => {
                  if (name === '新規案件') return [`${value}件`, name]
                  return [formatYen(value), name]
                }}
                labelFormatter={monthLabel}
              />
              <Legend />
              <Bar yAxisId="left" dataKey="revenue" name="売上" fill="#3B82F6" radius={[4, 4, 0, 0]} />
              <Bar yAxisId="left" dataKey="invoice_total" name="請求額" fill="#93C5FD" radius={[4, 4, 0, 0]} />
              <Line yAxisId="right" type="monotone" dataKey="new_projects" name="新規案件" stroke="#EF4444" strokeWidth={2} dot={{ r: 4 }} />
            </ComposedChart>
          </ResponsiveContainer>
        ) : (
          <div className="flex items-center justify-center h-[320px] text-gray-400 text-sm">
            データがありません
          </div>
        )}
      </div>

      {/* Engineer Utilization */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Utilization Pie Chart */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">エンジニア稼働状況</h3>
          {utilization && (utilization.available + utilization.assigned + utilization.unavailable) > 0 ? (
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie
                  data={[
                    { name: '稼働可能', value: utilization.available },
                    { name: 'アサイン済', value: utilization.assigned },
                    { name: '稼働不可', value: utilization.unavailable },
                  ].filter(d => d.value > 0)}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={95}
                  paddingAngle={3}
                  dataKey="value"
                  label={({ name, value }) => `${name}: ${value}名`}
                >
                  {[
                    { name: '稼働可能', value: utilization.available },
                    { name: 'アサイン済', value: utilization.assigned },
                    { name: '稼働不可', value: utilization.unavailable },
                  ].filter(d => d.value > 0).map((_, index) => (
                    <Cell key={`util-cell-${index}`} fill={UTILIZATION_COLORS[index % UTILIZATION_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(value: number) => [`${value}名`]} />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-[280px] text-gray-400 text-sm">
              データがありません
            </div>
          )}
        </div>

        {/* Assigned Engineers Table */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">アサイン済みエンジニア</h3>
          {utilization && utilization.assigned_engineers.length > 0 ? (
            <div className="overflow-auto max-h-[280px]">
              <table className="w-full text-sm">
                <thead className="sticky top-0 bg-white">
                  <tr className="text-left text-gray-500 border-b">
                    <th className="pb-2">氏名</th>
                    <th className="pb-2">案件</th>
                    <th className="pb-2 text-right">月額単価</th>
                    <th className="pb-2 text-right">契約終了日</th>
                  </tr>
                </thead>
                <tbody>
                  {utilization.assigned_engineers.map((eng) => (
                    <tr key={eng.engineer_id} className="border-b last:border-0">
                      <td className="py-2 font-medium">{eng.name}</td>
                      <td className="py-2 text-gray-500">{eng.project_name || '-'}</td>
                      <td className="py-2 text-right">{eng.monthly_rate ? `${eng.monthly_rate.toLocaleString()}円` : '-'}</td>
                      <td className="py-2 text-right text-gray-500">
                        {eng.end_date ? new Date(eng.end_date).toLocaleDateString('ja-JP') : '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="flex items-center justify-center h-[280px] text-gray-400 text-sm">
              アサイン済みエンジニアはいません
            </div>
          )}
        </div>
      </div>

      {/* Recent Jobs */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h3 className="text-lg font-semibold mb-4">最近の処理ジョブ</h3>
        {activities?.recent_jobs?.length ? (
          <div className="space-y-3">
            {activities.recent_jobs.map((job) => (
              <div key={job.id} className="border rounded-lg p-3 hover:border-blue-200 transition-colors">
                <div className="flex items-center justify-between mb-1">
                  <span className="font-medium text-sm">
                    ジョブ #{job.id}
                    {job.project_name && <span className="text-gray-500 ml-2">{job.project_name}</span>}
                  </span>
                  <StatusBadge status={job.status} />
                </div>
                <div className="flex items-center gap-1 mt-2">
                  {job.logs.map((log, i) => (
                    <div key={i} className="flex items-center">
                      <span className={`w-2 h-2 rounded-full ${
                        log.status === 'completed' ? 'bg-green-500' :
                        log.status === 'failed' ? 'bg-red-500' : 'bg-gray-300'
                      }`} />
                      <span className="text-xs text-gray-500 ml-1">{log.step}</span>
                      {i < job.logs.length - 1 && <span className="text-gray-300 mx-1">-</span>}
                    </div>
                  ))}
                </div>
                {job.mcp_result?.success && (
                  <p className="text-xs text-gray-400 mt-1">
                    Web入力: {job.mcp_result.system} ({job.mcp_result.confirmation_id})
                  </p>
                )}
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-400 text-sm py-4 text-center">ジョブはまだありません</p>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Projects */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">最近の案件</h3>
          {activities?.recent_projects?.length ? (
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-gray-500 border-b">
                  <th className="pb-2">案件名</th>
                  <th className="pb-2">クライアント</th>
                  <th className="pb-2">ステータス</th>
                </tr>
              </thead>
              <tbody>
                {activities.recent_projects.map((p) => (
                  <tr key={p.id} className="border-b last:border-0">
                    <td className="py-2 font-medium">{p.name}</td>
                    <td className="py-2 text-gray-500">{p.client || '-'}</td>
                    <td className="py-2"><StatusBadge status={p.status} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p className="text-gray-400 text-sm py-4 text-center">案件はまだありません</p>
          )}
        </div>

        {/* Recent Orders */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">最近の発注</h3>
          {activities?.recent_orders?.length ? (
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-gray-500 border-b">
                  <th className="pb-2">発注番号</th>
                  <th className="pb-2">ステータス</th>
                  <th className="pb-2">作成日</th>
                </tr>
              </thead>
              <tbody>
                {activities.recent_orders.map((o) => (
                  <tr key={o.id} className="border-b last:border-0">
                    <td className="py-2 font-medium">{o.order_number}</td>
                    <td className="py-2"><StatusBadge status={o.status} /></td>
                    <td className="py-2 text-gray-500">
                      {o.created_at ? new Date(o.created_at).toLocaleDateString('ja-JP') : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p className="text-gray-400 text-sm py-4 text-center">発注はまだありません</p>
          )}
        </div>
      </div>
    </div>
  )
}
