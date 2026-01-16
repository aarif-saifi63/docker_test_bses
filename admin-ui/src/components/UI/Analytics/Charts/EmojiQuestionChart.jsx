import React from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";

export default function EmojiQuestionChart({ data }) {
  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart layout="vertical" data={data.answers}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis type="number" allowDecimals={false} />
        <YAxis type="category" dataKey="option" />
        <Tooltip />
        <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
