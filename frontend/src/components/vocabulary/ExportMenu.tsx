import { useState } from "react";
import { Download, FileText, Layers, ChevronDown } from "lucide-react";
import { vocabularyApi } from "@/lib/api";

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export default function ExportMenu() {
  const [open, setOpen] = useState(false);
  const [exporting, setExporting] = useState<"csv" | "anki" | null>(null);

  const handleExport = async (format: "csv" | "anki") => {
    try {
      setExporting(format);
      const blob =
        format === "csv"
          ? await vocabularyApi.exportCsv()
          : await vocabularyApi.exportAnki();

      const ext = format === "csv" ? "csv" : "txt";
      downloadBlob(blob, `vocabulary.${ext}`);
    } catch (err) {
      console.error("Export failed:", err);
    } finally {
      setExporting(null);
      setOpen(false);
    }
  };

  return (
    <div className="relative inline-block">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1.5 px-3 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-sm font-medium text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
      >
        <Download size={14} />
        Export
        <ChevronDown size={12} className={`transition-transform ${open ? "rotate-180" : ""}`} />
      </button>

      {open && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-40"
            onClick={() => setOpen(false)}
          />

          {/* Dropdown */}
          <div className="absolute right-0 mt-1 z-50 w-52 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg overflow-hidden animate-fade-in">
            <button
              onClick={() => handleExport("csv")}
              disabled={exporting !== null}
              className="flex items-center gap-3 w-full px-4 py-3 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors disabled:opacity-50"
            >
              <FileText size={16} className="text-green-500" />
              <div className="text-left">
                <p className="font-medium">
                  {exporting === "csv" ? "Downloading…" : "CSV File"}
                </p>
                <p className="text-[11px] text-gray-400 dark:text-gray-500">
                  Opens in Excel, Google Sheets
                </p>
              </div>
            </button>

            <div className="border-t border-gray-100 dark:border-gray-700" />

            <button
              onClick={() => handleExport("anki")}
              disabled={exporting !== null}
              className="flex items-center gap-3 w-full px-4 py-3 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors disabled:opacity-50"
            >
              <Layers size={16} className="text-blue-500" />
              <div className="text-left">
                <p className="font-medium">
                  {exporting === "anki" ? "Downloading…" : "Anki Format"}
                </p>
                <p className="text-[11px] text-gray-400 dark:text-gray-500">
                  Tab-separated, import into Anki
                </p>
              </div>
            </button>
          </div>
        </>
      )}
    </div>
  );
}
