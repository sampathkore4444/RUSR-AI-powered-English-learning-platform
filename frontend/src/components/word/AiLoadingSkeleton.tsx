export default function AiLoadingSkeleton() {
  return (
    <div className="animate-pulse space-y-3">
      <div className="flex items-center gap-1.5">
        <div className="h-3.5 w-3.5 bg-indigo-200 dark:bg-indigo-800 rounded" />
        <div className="h-3 w-20 bg-indigo-200 dark:bg-indigo-800 rounded" />
      </div>

      <div className="space-y-2">
        <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-full" />
        <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-11/12" />
        <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-4/5" />
        <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-9/12" />
      </div>

      <div className="h-2.5 bg-indigo-100 dark:bg-indigo-900/40 rounded w-1/3 mt-2" />
    </div>
  );
}
