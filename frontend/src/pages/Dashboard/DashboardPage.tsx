import { useState, useEffect } from 'react'
import api from '../../services/api'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

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

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null)

  useEffect(() => {
    api.get('/dashboard/stats').then((res) => setStats(res.data)).catch(() => {})
  }, [])

  if (!stats) return <div className="text-center py-8">読み込み中...</div>

  const projectData = [
    { name: '進行中', value: stats.active_projects },
    { name: '全案件', value: stats.total_projects },
  ]

  const summaryCards = [
    { label: '進行中案件', value: stats.active_projects, color: 'bg-blue-500' },
    { label: '稼働可能エンジニア', value: stats.available_engineers, color: 'bg-green-500' },
    { label: '未確認発注', value: stats.pending_orders, color: 'bg-yellow-500' },
    { label: '有効契約', value: stats.active_contracts, color: 'bg-purple-500' },
    { label: '未入金請求', value: stats.unpaid_invoices, color: 'bg-red-500' },
    { label: '処理中ジョブ', value: stats.pending_jobs, color: 'bg-cyan-500' },
  ]

  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">ダッシュボード</h2>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-8">
        {summaryCards.map((card) => (
          <div key={card.label} className="bg-white rounded-lg shadow p-4">
            <p className="text-sm text-gray-500">{card.label}</p>
            <p className="text-3xl font-bold mt-1">{card.value}</p>
          </div>
        ))}
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">案件概況</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={projectData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="value" fill="#3B82F6" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}
