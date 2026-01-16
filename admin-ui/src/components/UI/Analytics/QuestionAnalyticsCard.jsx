import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

export default function QuestionAnalyticsCard({ questionData }) {
  const chartData = questionData.answers.map((a) => ({
    option: `Option ${a.option}`,
    count: a.count,
  }));

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <h3 className="font-medium mb-2">{questionData.question}</h3>
      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={chartData}>
          <XAxis dataKey="option" />
          <YAxis allowDecimals={false} />
          <Tooltip />
          <Bar dataKey="count" fill="#3b82f6" />
        </BarChart>
      </ResponsiveContainer>
      <p className="text-sm text-gray-600 mt-2">Total Responses: {questionData.total_responses}</p>
    </div>
  );
}
