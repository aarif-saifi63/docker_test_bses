import React from "react";

export default function GroupedButtons({ groupedButtons, handleGroupedButton }) {
  if (!groupedButtons) return null;
  return (
    <div className="mb-2">
      <div className="font-semibold text-gray-700 mb-1">
        {groupedButtons.heading}
      </div>
      <div className="flex flex-wrap justify-center gap-2">
        {groupedButtons.options.map((opt, oi) => (
          <button
            key={oi}
            onClick={() => handleGroupedButton(opt)}
            className="bg-white border border-red-400 text-red-600 px-4 py-2 rounded-full hover:bg-red-100 transition font-medium"
          >
            {opt}
          </button>
        ))}
      </div>
    </div>
  );
}