export default function Spinner({ size = 24 }: { size?: number }) {
  return (
    <div className="flex justify-center items-center py-8">
      <div
        className="animate-spin rounded-full border-2 border-gray-300 dark:border-gray-600 border-t-indigo-600 dark:border-t-indigo-400"
        style={{ width: size, height: size }}
      />
    </div>
  );
}
