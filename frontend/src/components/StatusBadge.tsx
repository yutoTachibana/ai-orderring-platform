const STATUS_CONFIG: Record<string, { label: string; color: string }> = {
  // Project
  draft: { label: '下書き', color: 'bg-gray-100 text-gray-700' },
  open: { label: '募集中', color: 'bg-blue-100 text-blue-700' },
  in_progress: { label: '進行中', color: 'bg-yellow-100 text-yellow-700' },
  completed: { label: '完了', color: 'bg-green-100 text-green-700' },
  closed: { label: 'クローズ', color: 'bg-gray-100 text-gray-500' },
  // Quotation
  submitted: { label: '提出済', color: 'bg-blue-100 text-blue-700' },
  approved: { label: '承認済', color: 'bg-green-100 text-green-700' },
  rejected: { label: '却下', color: 'bg-red-100 text-red-700' },
  // Order
  pending: { label: '保留中', color: 'bg-yellow-100 text-yellow-700' },
  confirmed: { label: '確定', color: 'bg-green-100 text-green-700' },
  cancelled: { label: 'キャンセル', color: 'bg-red-100 text-red-700' },
  // Contract
  active: { label: '有効', color: 'bg-green-100 text-green-700' },
  expired: { label: '期限切れ', color: 'bg-gray-100 text-gray-500' },
  terminated: { label: '解約', color: 'bg-red-100 text-red-700' },
  // Invoice
  sent: { label: '送付済', color: 'bg-blue-100 text-blue-700' },
  paid: { label: '入金済', color: 'bg-green-100 text-green-700' },
  overdue: { label: '期限超過', color: 'bg-red-100 text-red-700' },
  // Job
  received: { label: '受信', color: 'bg-gray-100 text-gray-700' },
  parsing: { label: '解析中', color: 'bg-yellow-100 text-yellow-700' },
  routing: { label: '振分中', color: 'bg-yellow-100 text-yellow-700' },
  pending_approval: { label: '承認待ち', color: 'bg-orange-100 text-orange-700' },
  executing: { label: '実行中', color: 'bg-blue-100 text-blue-700' },
  failed: { label: '失敗', color: 'bg-red-100 text-red-700' },
  // Payment
  unmatched: { label: '未消込', color: 'bg-red-100 text-red-700' },
  matched: { label: '消込済', color: 'bg-yellow-100 text-yellow-700' },
  // Engineer availability
  available: { label: '稼働可能', color: 'bg-green-100 text-green-700' },
  partially_available: { label: '一部可能', color: 'bg-yellow-100 text-yellow-700' },
  unavailable: { label: '稼働不可', color: 'bg-red-100 text-red-700' },
}

interface StatusBadgeProps {
  status: string
  className?: string
}

export default function StatusBadge({ status, className = '' }: StatusBadgeProps) {
  const config = STATUS_CONFIG[status] || { label: status, color: 'bg-gray-100 text-gray-700' }
  return (
    <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${config.color} ${className}`}>
      {config.label}
    </span>
  )
}
