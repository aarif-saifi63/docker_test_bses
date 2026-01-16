import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
  ResponsiveContainer,
} from "recharts";

export default function ChatMetricsChart({
  sessionsData,
  avgTimeData,
  chatStatusData,
}) {
  const parseSeconds = (str) => parseInt(str?.split(" ")[0], 10) || 0;

  const chartData = [
    {
      name: "Week 1",
      interactions: sessionsData?.monthly?.weeks?.week1 || 0,
      avgTime: parseSeconds(avgTimeData?.weekly?.week1),
      completed: chatStatusData?.weekly?.week1?.completed || 0,
    },
    {
      name: "Week 2",
      interactions: sessionsData?.monthly?.weeks?.week2 || 0,
      avgTime: parseSeconds(avgTimeData?.weekly?.week2),
      completed: chatStatusData?.weekly?.week2?.completed || 0,
    },
    {
      name: "Week 3",
      interactions: sessionsData?.monthly?.weeks?.week3 || 0,
      avgTime: parseSeconds(avgTimeData?.weekly?.week3),
      completed: chatStatusData?.weekly?.week3?.completed || 0,
    },
    {
      name: "Week 4",
      interactions: sessionsData?.monthly?.weeks?.week4 || 0,
      avgTime: parseSeconds(avgTimeData?.weekly?.week4),
      completed: chatStatusData?.weekly?.week4?.completed || 0,
    },
  ];

  return (
    <div className="w-full h-[400px] bg-white rounded shadow p-4">
      <h3 className="text-lg font-semibold mb-4">
        Chat Metrics Dashboard View
      </h3>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={chartData}
          margin={{ top: 20, right: 30, bottom: 20, left: 0 }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" />
          <YAxis
            label={{ value: "Values", angle: -90, position: "insideLeft" }}
          />
          <Tooltip />
          <Legend />
          <Bar
            dataKey="interactions"
            fill="#3b82f6"
            name="Total Interactions"
          />
          <Bar dataKey="avgTime" fill="#f59e0b" name="Avg. Time (mins)" />
          <Bar dataKey="completed" fill="#ef4444" name="Chat Completed" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
