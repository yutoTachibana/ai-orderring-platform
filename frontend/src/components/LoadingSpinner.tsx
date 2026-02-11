interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg'
  message?: string
}

const sizes = {
  sm: 'h-4 w-4 border-2',
  md: 'h-8 w-8 border-2',
  lg: 'h-12 w-12 border-3',
}

export default function LoadingSpinner({ size = 'md', message }: LoadingSpinnerProps) {
  return (
    <div className="flex flex-col items-center justify-center py-8">
      <div
        className={`${sizes[size]} border-gray-300 border-t-blue-600 rounded-full animate-spin`}
      />
      {message && <p className="mt-3 text-sm text-gray-500">{message}</p>}
    </div>
  )
}
