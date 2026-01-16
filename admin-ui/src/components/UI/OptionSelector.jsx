import React from "react";

export default function OptionSelector({ options, selected, onToggle }) {
  return (
    <div className="mb-4">
      <label className="block text-sm font-medium mb-2">Select Options:</label>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2 max-h-64 overflow-y-auto border rounded p-2">
        {options.map((opt) => (
          <label key={opt} className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={selected.includes(opt)}
              onChange={() => onToggle(opt)}
            />
            {opt}
          </label>
        ))}
      </div>
    </div>
  );
}
