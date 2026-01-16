export default function MultiEntryRow({ item, setModalData }) {
  // safely handle all logs (array)
  const logsArr = item?.logs || [];

  return (
    <div className="space-y-4">
      {logsArr.map((log, logIdx) => {
        // Each log ek "entry pair" lane ki koshish karo (left, right)
        const entries = log.entries || [];
        const left = entries[0] || {};
        const right = entries[1] || {};

        return (
          <div
            key={log.session_id || logIdx}
            className="flex items-start justify-between border rounded-lg p-4 bg-white shadow hover:shadow-md transition"
          >
            {/* Left Column */}
            <div className="flex-1 pr-4">
              <p className="font-semibold text-gray-800">User Input</p>
              <p className="text-gray-700 mb-2 break-all">{left.query || "—"}</p>

              <p className="font-semibold text-gray-800">System Response</p>
              <p className="text-gray-700">
                {left.answer?.response?.heading?.[0] || "—"}
              </p>
            </div>
            {/* Right Column */}
            <div className="flex-1 px-4">
              <p className="font-semibold text-gray-800">User Input</p>
              <p className="text-gray-700 mb-2 break-all">{right.query || "—"}</p>

              <p className="font-semibold text-gray-800">System Response</p>
              <p className="text-gray-700">
                {right.answer?.response?.heading?.[0] || "—"}
              </p>
            </div>

            {/* View Log Button */}
            <div className="flex items-center">
              <button
                onClick={() => setModalData(item)}
                className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600"
              >
                View Full Log
              </button>
            </div>
          </div>
        );
      })}
    </div>
  );
}

