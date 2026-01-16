import React from "react";

export default function TextQuestionChart({ data }) {
  return (
    <div className="max-h-40 overflow-y-auto border rounded p-2 bg-gray-50 space-y-2">
      {data.answers.map((a, i) => (
        <div key={i} className="text-gray-700 bg-white border border-gray-200 rounded p-2 text-sm">
          {a.option}
        </div>
      ))}
    </div>
  );
}
