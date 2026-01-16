import React from "react";

export default function PollQuestion({
  question, // current poll question object
  pollAnswers,
  setPollAnswers,
  handlePollAnswer,
}) {
  if (!question) return null;

  const q = question;

  switch (q.type) {
    case "emoji":
    case "yesno":
    case "thumbs":
      return (
        <div className="flex flex-wrap gap-2 mt-2">
          {q.options?.map((btn, idx) => (
            <button
              key={idx}
              onClick={() => handlePollAnswer(q.id, btn)}
              className="text-red-700 border border-red-400 bg-white rounded-full px-4 py-2 font-medium text-sm"
            >
              {btn}
            </button>
          ))}
        </div>
      );

    case "slider":
      return (
        <div className="w-full mt-2">
          <input
            type="range"
            min={q.min}
            max={q.max}
            step={q.step || 1}
            value={pollAnswers[q.id] || q.min}
            onChange={(e) =>
              setPollAnswers({ ...pollAnswers, [q.id]: e.target.value })
            }
            onMouseUp={(e) => handlePollAnswer(q.id, e.currentTarget.value)}
            onTouchEnd={(e) => handlePollAnswer(q.id, e.currentTarget.value)}
            className="w-full"
          />
        </div>
      );

    case "star":
      return (
        <div className="flex gap-1 mt-2">
          {Array.from({ length: q.max_stars }).map((_, idx) => (
            <span
              key={idx}
              onClick={() => handlePollAnswer(q.id, idx + 1)}
              className={`cursor-pointer text-2xl ${
                (pollAnswers[q.id] || 0) > idx
                  ? "text-yellow-400"
                  : "text-gray-300"
              }`}
            >
              ★
            </span>
          ))}
        </div>
      );

    case "text":
      return null;

    default:
      return null;
  }
}
