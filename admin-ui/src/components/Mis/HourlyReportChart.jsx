import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Cell,
} from "recharts";
import ExportButton from "./ExportButton";

const ALL_HOUR_RANGES = [
  "00:00 - 02:00",
  "02:00 - 04:00",
  "04:00 - 06:00",
  "06:00 - 08:00",
  "08:00 - 10:00",
  "10:00 - 12:00",
  "12:00 - 14:00",
  "14:00 - 16:00",
  "16:00 - 18:00",
  "18:00 - 20:00",
  "20:00 - 22:00",
  "22:00 - 00:00",
];

export default function HourlyReportChart({ data, peakHour, onExport }) {
  // normalize to ensure all slots exist
  const normalizedData = ALL_HOUR_RANGES.map((range) => {
    const found = data.find((d) => d.hour_range === range);
    return (
      found || {
        hour_range: range,
        total_interactions: 0,
        unique_users: 0,
      }
    );
  });

  return (
    <div className="bg-white rounded-2xl shadow p-4 flex flex-col ">
      {/* Header */}
      <div className="flex justify-between items-center mb-2 border-b pb-1">
        <h2 className="text-lg font-semibold">Interaction</h2>
        {peakHour && (
          <div className="flex items-center gap-1 text-sm text-gray-600">
            <span>🕒 Peak Hour:</span>
            <span className="font-medium">{peakHour.hour_range}</span>
          </div>
        )}
      </div>

      {/* Chart */}
      <ResponsiveContainer width="100%" height={250}>
        <BarChart data={normalizedData}>
          <XAxis
            dataKey="hour_range"
            fontSize={12}
            interval={0} // ✅ Show all labels
            angle={-30} // ✅ Tilt to prevent overlap
            textAnchor="end"
            height={60} // ✅ More space for labels
          />
          <YAxis fontSize={12} />
          {/* <Tooltip /> */}

          <Tooltip
            content={({ active, payload, label }) => {
              if (active && payload && payload.length) {
                const record = payload[0].payload;
                const services = record.services_called || {};

                return (
                  <div className="bg-white border border-gray-300 rounded-lg p-3 shadow-md text-xs max-w-xs">
                    <p className="font-semibold text-gray-800 mb-1">{label}</p>
                    <p className="text-gray-600">
                      <span className="font-medium">Interactions:</span>{" "}
                      {record.total_interactions || 0}
                    </p>
                    <p className="text-gray-600 mb-1">
                      <span className="font-medium">Unique Users:</span>{" "}
                      {record.unique_users || 0}
                    </p>

                    {Object.keys(services).length > 0 ? (
                      <div className="mt-2">
                        <p className="font-medium text-gray-700 underline mb-1">
                          Services Called:
                        </p>
                        <ul className="list-disc ml-4 space-y-0.5">
                          {Object.entries(services).map(
                            ([service, count], idx) => (
                              <li key={idx} className="text-gray-700">
                                {service}:{" "}
                                <span className="font-semibold">{count}</span>
                              </li>
                            )
                          )}
                        </ul>
                      </div>
                    ) : (
                      <p className="text-gray-400 italic mt-2">
                        No services called
                      </p>
                    )}
                  </div>
                );
              }
              return null;
            }}
          />

          <Bar dataKey="total_interactions" name="Interactions">
            {normalizedData.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={
                  peakHour?.hour_range === entry.hour_range
                    ? "#22c55e"
                    : "#ef4444"
                }
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      {/* Export */}
      <div className="mt-auto flex justify-end">
        <ExportButton onClick={() => onExport(normalizedData)} />
      </div>
    </div>
  );
}
