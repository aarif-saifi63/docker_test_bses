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
    case "yesno":
      return (
        <div className="flex gap-2 mt-3">
          {(q.options || ["Yes", "No"]).map((option, idx) => (
            <button
              key={idx}
              onClick={() => handlePollAnswer(q.id, option)}
              className={`px-6 py-2 rounded-lg font-medium transition-all ${
                pollAnswers[q.id] === option
                  ? "text-white rounded gradientBtn transition-all duration-200 px-3 py-1  font-medium  text-[15px]"
                  : "text-white rounded gradientBtn transition-all duration-200 px-3 py-1  font-medium  text-[15px]"
              }`}
            >
              {option}
            </button>
          ))}
        </div>
      );

    case "thumbs":
      return (
        <div className="flex gap-3 mt-3">
          {(q.options || ["👍", "👎"]).map((emoji, idx) => (
            <button
              key={idx}
              onClick={() => handlePollAnswer(q.id, emoji)}
              className={`text-4xl p-3 rounded-lg transition-all ${
                pollAnswers[q.id] === emoji
                  ? "bg-red-100 scale-110 shadow-lg"
                  : "bg-gray-100 hover:bg-gray-200 hover:scale-105"
              }`}
            >
              {emoji}
            </button>
          ))}
        </div>
      );

    case "slider": {
      // Ensure slider value is always a number (not string like "No" from previous buttons)
      const currentValue = typeof pollAnswers[q.id] === 'number'
        ? pollAnswers[q.id]
        : (Number(pollAnswers[q.id]) || q.slider_min);

      return (
        <div className="w-full mt-3">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm text-gray-600">{q.slider_min}</span>
            <span className="text-lg font-semibold text-red-700 bg-red-50 px-3 py-1 rounded-full border border-red-200">
              {currentValue}
            </span>
            <span className="text-sm text-gray-600">{q.slider_max}</span>
          </div>
          <input
            type="range"
            min={q.slider_min}
            max={q.slider_max}
            step={q.step || 1}
            value={currentValue}
            onChange={(e) =>
              setPollAnswers({ ...pollAnswers, [q.id]: Number(e.target.value) })
            }
            onMouseUp={(e) => handlePollAnswer(q.id, Number(e.currentTarget.value))}
            onTouchEnd={(e) => handlePollAnswer(q.id, Number(e.currentTarget.value))}
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider-thumb"
            style={{
              background: `linear-gradient(to right, #DC2626 0%, #DC2626 ${((currentValue - q.slider_min) / (q.slider_max - q.slider_min) * 100)}%, #E5E7EB ${((currentValue - q.slider_min) / (q.slider_max - q.slider_min) * 100)}%, #E5E7EB 100%)`
            }}
          />
        </div>
      );
    }

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
