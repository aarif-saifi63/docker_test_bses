export default function InteractionRow({ item, setModalData }) {
  // 🔹 Normalize logs regardless of API shape
  const normalizedLogs = Array.isArray(item?.logs?.[0]?.entries)
    ? item.logs[0].entries // old API shape
    : item?.logs || []; // new API shape

  const left = normalizedLogs[0];
  const right = normalizedLogs[1];

  // helper to render buttons safely
  const renderButtons = (buttons = []) =>
    Array.isArray(buttons) && buttons.length > 0 ? (
      <div className="flex gap-2 mt-2 flex-wrap">
        {buttons.map((btn, idx) => (
          <span
            key={idx}
            className="px-3 py-1 text-xs border rounded-md text-red-500 border-red-400 bg-red-50"
          >
            {btn}
          </span>
        ))}
      </div>
    ) : null;

  const getHeading = (entry) =>
    entry?.answer?.response?.heading?.[0] || entry?.answer?.response?.message || "N/A";

  return (
    <div className="bg-white border rounded-xl shadow-sm hover:shadow-md transition p-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Left */}
        <div className="space-y-2">
          <p className="text-sm font-semibold text-gray-600">User Input</p>
          <p className="text-gray-800">{left?.query || "N/A"}</p>

          <p className="text-sm font-semibold text-gray-600 mt-3">System Response</p>
          <p className="text-gray-800">{getHeading(left)}</p>
          {renderButtons(left?.answer?.response?.buttons)}
        </div>

        {/* Right */}
        <div className="space-y-2">
          <p className="text-sm font-semibold text-gray-600">User Input</p>
          <p className="text-gray-800">{right?.query || "N/A"}</p>

          <p className="text-sm font-semibold text-gray-600 mt-3">System Response</p>
          <p className="text-gray-800">{getHeading(right)}</p>
          {renderButtons(right?.answer?.response?.buttons)}
        </div>
      </div>

      {/* Footer with View Log Button */}
      <div className="flex justify-end mt-4">
        <button
          onClick={() => setModalData(item)}
          className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition"
        >
          View Full Log
        </button>
      </div>
    </div>
  );
}
