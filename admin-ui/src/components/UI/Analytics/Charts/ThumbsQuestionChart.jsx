import React from "react";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from "recharts";

const COLORS = ["#10b981", "#ef4444"];

export default function ThumbsQuestionChart({ data }) {
  return (
    <ResponsiveContainer width="100%" height={220}>
      <PieChart>
        <Pie
          data={data.answers}
          dataKey="count"
          nameKey="option"
          cx="50%"
          cy="50%"
          outerRadius={80}
          label
        >
          {data.answers.map((_, index) => (
            <Cell key={index} fill={COLORS[index % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  );
}
