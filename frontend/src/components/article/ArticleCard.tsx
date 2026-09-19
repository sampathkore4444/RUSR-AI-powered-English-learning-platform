import { Link } from "react-router-dom";
import { Calendar, User } from "lucide-react";
import type { Article } from "@/lib/api";

interface Props {
  article: Article;
}

export default function ArticleCard({ article }: Props) {
  return (
    <Link
      to={`/article/${article.id}`}
      className="block bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 hover:shadow-md transition-all"
    >
      <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-2">{article.title}</h3>

      <div className="flex items-center gap-4 text-xs text-gray-500 dark:text-gray-400">
        {article.author && (
          <span className="flex items-center gap-1">
            <User size={12} />
            {article.author}
          </span>
        )}
        <span className="flex items-center gap-1">
          <Calendar size={12} />
          {new Date(article.created_at).toLocaleDateString()}
        </span>
      </div>

      {article.paragraphs?.length > 0 && (
        <p className="mt-2 text-sm text-gray-600 dark:text-gray-400 line-clamp-2">
          {article.paragraphs[0].text}
        </p>
      )}
    </Link>
  );
}
