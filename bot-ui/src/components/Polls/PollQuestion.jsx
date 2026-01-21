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
       <div className="w-full mt-3">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm text-gray-600">{q.min}</span>
            <span className="text-lg font-semibold text-red-700 bg-red-50 px-3 py-1 rounded-full border border-red-200">
              {pollAnswers[q.id] || q.min}
            </span>
            <span className="text-sm text-gray-600">{q.max}</span>
          </div>
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
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider-thumb"
            style={{
              background: `linear-gradient(to right, #DC2626 0%, #DC2626 ${((pollAnswers[q.id] || q.min) - q.min) / (q.max - q.min) * 100}%, #E5E7EB ${((pollAnswers[q.id] || q.min) - q.min) / (q.max - q.min) * 100}%, #E5E7EB 100%)`
            }}
          />
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
