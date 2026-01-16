import React from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";
import { Star } from "lucide-react";

export default function StarRatingQuestionChart({ data }) {
  const { answers, total_responses } = data;

  const average = (
    answers.reduce((sum, a) => sum + parseFloat(a.option) * a.count, 0) / total_responses
  ).toFixed(1);

  return (
    <div>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={answers}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="option" />
          <YAxis allowDecimals={false} />
          <Tooltip />
          <Bar dataKey="count" fill="#f59e0b" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>

      <div className="flex items-center gap-2 text-yellow-600 mt-2 font-medium">
        <Star className="w-4 h-4 fill-yellow-500 text-yellow-500" />
        <p>Average Rating: {average} ⭐</p>
      </div>
    </div>
  );
}
