export default function PollSummaryCard({ poll }) {
  return (
    <div className="bg-white rounded-lg shadow p-4 flex flex-col sm:flex-row sm:justify-between sm:items-center gap-3">
      <div>
        <h1 className="text-xl font-semibold text-gray-800">{poll.title}</h1>
        <p className="text-sm text-gray-500">
          {new Date(poll.start_time).toLocaleDateString()} →{" "}
          {new Date(poll.end_time).toLocaleDateString()}
        </p>
      </div>
      <div className="flex items-center gap-4">
        <span className="text-gray-700 font-medium">
          Responses: <strong>{poll.total_responses}</strong>
        </span>
        <span
          className={`px-3 py-1 rounded-full text-xs font-medium ${
            poll.is_active ? "bg-green-100 text-green-700" : "bg-gray-200 text-gray-600"
          }`}
        >
          {poll.is_active ? "Active" : "Inactive"}
        </span>
      </div>
    </div>
  );
}
