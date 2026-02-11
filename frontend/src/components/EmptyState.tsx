interface EmptyStateProps {
  message?: string
  colSpan?: number
}

export default function EmptyState({ message = 'データがありません', colSpan = 1 }: EmptyStateProps) {
  return (
    <tr>
      <td colSpan={colSpan} className="py-12 text-center text-gray-400">
        <div className="flex flex-col items-center">
          <svg className="w-12 h-12 text-gray-300 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
          </svg>
          <p className="text-sm">{message}</p>
        </div>
      </td>
    </tr>
  )
}
