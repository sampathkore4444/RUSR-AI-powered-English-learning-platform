import { useState, useEffect } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { BookOpen, Brain, List, LogOut, User, Sun, Moon } from "lucide-react";
import { clearToken } from "@/lib/api";
import { useDarkMode } from "@/hooks/useDarkMode";

const links = [
  { to: "/", label: "Home", icon: BookOpen },
  { to: "/vocabulary", label: "Vocabulary", icon: List },
  { to: "/review", label: "Review", icon: Brain },
];

export default function Navbar() {
  const location = useLocation();
  const navigate = useNavigate();
  const [userEmail, setUserEmail] = useState<string | null>(null);
  const { isDark, toggleTheme } = useDarkMode();

  useEffect(() => {
    const email = localStorage.getItem("rusr_user_email");
    if (email) setUserEmail(email);
  }, []);

  const handleLogout = () => {
    clearToken();
    localStorage.removeItem("rusr_user_email");
    navigate("/login");
  };

  return (
    <nav className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 sticky top-0 z-50 transition-colors">
      <div className="max-w-5xl mx-auto px-4 h-14 flex items-center justify-between">
        <Link to="/" className="font-bold text-lg text-indigo-600 dark:text-indigo-400">
          📰 RUSR
        </Link>

        <div className="flex items-center gap-1">
          {links.map(({ to, label, icon: Icon }) => {
            const active = location.pathname === to;
            return (
              <Link
                key={to}
                to={to}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                  active
                    ? "bg-indigo-50 dark:bg-indigo-900/40 text-indigo-700 dark:text-indigo-300"
                    : "text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700"
                }`}
              >
                <Icon size={16} />
                {label}
              </Link>
            );
          })}

          {/* Dark mode toggle */}
          <button
            onClick={toggleTheme}
            className="flex items-center justify-center w-8 h-8 rounded-md text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors ml-1"
            title={isDark ? "Switch to light mode" : "Switch to dark mode"}
          >
            {isDark ? <Sun size={16} /> : <Moon size={16} />}
          </button>

          {/* User info */}
          {userEmail && (
            <span className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-gray-500 dark:text-gray-400">
              <User size={14} />
              {userEmail}
            </span>
          )}

          <button
            onClick={handleLogout}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 hover:text-red-600 dark:hover:text-red-400 transition-colors ml-2"
            title="Logout"
          >
            <LogOut size={16} />
          </button>
        </div>
      </div>
    </nav>
  );
}
