import { useState } from 'react'
import { Outlet, NavLink } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import {
  LayoutDashboard, Building2, Users, FolderOpen, FileText,
  ShoppingCart, FileSignature, Receipt, Cpu, BarChart3, Landmark, Menu, X, LogOut,
} from 'lucide-react'

const navItems = [
  { to: '/dashboard', label: 'ダッシュボード', icon: LayoutDashboard },
  { to: '/companies', label: '企業管理', icon: Building2 },
  { to: '/engineers', label: 'エンジニア管理', icon: Users },
  { to: '/projects', label: '案件管理', icon: FolderOpen },
  { to: '/quotations', label: '見積管理', icon: FileText },
  { to: '/orders', label: '発注管理', icon: ShoppingCart },
  { to: '/contracts', label: '契約管理', icon: FileSignature },
  { to: '/invoices', label: '請求管理', icon: Receipt },
  { to: '/jobs', label: '処理ジョブ', icon: Cpu },
  { to: '/reconciliation', label: '入金消込', icon: Landmark },
  { to: '/reports', label: 'レポート', icon: BarChart3 },
]

export default function Layout() {
  const { user, logout } = useAuth()
  const [sidebarOpen, setSidebarOpen] = useState(false)

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Sidebar */}
      <aside className={`fixed inset-y-0 left-0 z-50 w-64 bg-gray-900 text-white transform transition-transform lg:relative lg:translate-x-0 ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}`}>
        <div className="flex items-center justify-between h-16 px-4 border-b border-gray-700">
          <h1 className="text-lg font-bold">AI受発注</h1>
          <button onClick={() => setSidebarOpen(false)} className="lg:hidden"><X size={20} /></button>
        </div>
        <nav className="mt-4 space-y-1 px-2">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              onClick={() => setSidebarOpen(false)}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${isActive ? 'bg-blue-600 text-white' : 'text-gray-300 hover:bg-gray-800'}`
              }
            >
              <item.icon size={18} />
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>

      {/* Overlay */}
      {sidebarOpen && <div className="fixed inset-0 bg-black/50 z-40 lg:hidden" onClick={() => setSidebarOpen(false)} />}

      {/* Main */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <header className="h-16 bg-white border-b flex items-center justify-between px-4 shadow-sm">
          <button onClick={() => setSidebarOpen(true)} className="lg:hidden"><Menu size={20} /></button>
          <div />
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-600">{user?.full_name}</span>
            <button onClick={logout} className="text-gray-500 hover:text-red-500"><LogOut size={18} /></button>
          </div>
        </header>
        <main className="flex-1 overflow-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
