import React from "react";
import { FileText } from "lucide-react";

export default function ExportButton({ onClick, className = "" }) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-2 bg-red-600 text-white px-4 py-2 rounded-lg shadow hover:bg-red-700 ${className}`}
    >
      <FileText size={16} />
      Export to Excel
    </button>
  );
}
