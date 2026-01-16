import React from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

export default function SliderQuestionChart({ data }) {
  const { answers, total_responses, slider_min, slider_max } = data;

  const formatted = answers.map((a) => ({
    option: Number(a.option),
    count: a.count,
  }));

  const average = (
    answers.reduce((sum, a) => sum + parseFloat(a.option) * a.count, 0) / total_responses
  ).toFixed(1);

  return (
    <div>
      <ResponsiveContainer width="100%" height={220}>
        <LineChart data={formatted}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="option" domain={[slider_min, slider_max]} />
          <YAxis allowDecimals={false} />
          <Tooltip />
          <Line type="monotone" dataKey="count" stroke="#10b981" strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
      <p className="text-sm text-green-700 font-medium mt-2">
        Average Rating: {average} / {slider_max}
      </p>
    </div>
  );
}
