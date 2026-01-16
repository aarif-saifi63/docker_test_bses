import React from "react";

export default function LanguageSelector({ selected, onChange }) {
  return (
    <select
      value={selected}
      onChange={(e) => onChange(e.target.value)}
      className="border px-3 py-2 rounded-lg"
    >
      <option value="english">English</option>
      <option value="hindi">हिन्दी</option>
    </select>
  );
}
