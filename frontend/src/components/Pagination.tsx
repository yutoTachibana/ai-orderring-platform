interface PaginationProps {
  page: number
  totalPages: number
  total: number
  onPageChange: (page: number) => void
}

export default function Pagination({ page, totalPages, total, onPageChange }: PaginationProps) {
  if (totalPages <= 1) return null

  return (
    <div className="flex items-center justify-between mt-4">
      <span className="text-sm text-gray-500">{total}件中 {(page - 1) * 20 + 1}-{Math.min(page * 20, total)}件</span>
      <div className="flex gap-2">
        <button
          onClick={() => onPageChange(Math.max(1, page - 1))}
          disabled={page === 1}
          className="px-3 py-1 border rounded text-sm disabled:opacity-50 hover:bg-gray-50"
        >
          前へ
        </button>
        <span className="px-3 py-1 text-sm text-gray-600">{page} / {totalPages}</span>
        <button
          onClick={() => onPageChange(Math.min(totalPages, page + 1))}
          disabled={page === totalPages}
          className="px-3 py-1 border rounded text-sm disabled:opacity-50 hover:bg-gray-50"
        >
          次へ
        </button>
      </div>
    </div>
  )
}
