import React from "react";
import ExportButton from "../Mis/ExportButton";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts";

export default function ChatStatusChart({ data, onExport, averageData }) {
  const hasData =
    data && (data.total_sessions > 0 || data.completed_chats > 0 || data.left_chats > 0);

  // First chart: Chat Completion
  const chatData = hasData
    ? [
        { name: "Completed", value: data.completed_chats, color: "#22c55e" },
        { name: "Left", value: data.left_chats, color: "#ef4444" },
      ]
    : [{ name: "No Data", value: 1, color: "#ef4444" }];

  // Second chart: User Type
  const userData = hasData
    ? [
        { name: "New User", value: data.new_user_sessions, color: "#64748b" },
        { name: "Registered", value: data.registered_user_sessions, color: "#0f172a" },
      ]
    : [{ name: "No Data", value: 1, color: "#94a3b8" }];

  const totalSessions = hasData ? data.total_sessions : 0;
  const completedChats = hasData ? data.completed_chats : 0;
  const leftChats = hasData ? data.left_chats : 0;
  const newUser = hasData ? data.new_user_sessions : 0;
  const regUser = hasData ? data.registered_user_sessions : 0;
  const english = hasData ? data?.english_sessions : 0;
  const hindi = hasData ? data?.hindi_sessions : 0;

  return (
    <div className="bg-white rounded-2xl shadow p-4 flex flex-col">
      {/* Header */}
      <div className="flex justify-between items-center mb-2">
        <h2 className="text-lg font-semibold">Chat Statistics</h2>
        <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">
          Avg.Duration: {averageData?.average_duration || "—"}
        </span>
      </div>

      {/* Two Charts Side by Side */}
      <div className="grid grid-cols-2 gap-6 mt-4">
        {/* Chart 1: Chat Completion */}
        <div className="flex flex-col items-center">
          <div className="w-40 h-40">
            <ResponsiveContainer>
              <PieChart>
                <Pie
                  data={chatData}
                  cx="50%"
                  cy="50%"
                  outerRadius={70}
                  innerRadius={40}
                  dataKey="value"
                >
                  {chatData.map((entry, index) => (
                    <Cell key={`chat-cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-3 space-y-1 text-sm">
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded bg-green-500 inline-block"></span>
              <span>Completed: {completedChats}</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded bg-red-500 inline-block"></span>
              <span>Left: {leftChats}</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded bg-sky-500 inline-block"></span>
              <span>Total: {totalSessions}</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded bg-blue-500 inline-block"></span>
              <span>English Sessions: {english}</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded bg-gray-500 inline-block"></span>
              <span>Hindi Sessions: {hindi}</span>
            </div>
          </div>
        </div>

        {/* Chart 2: User Types */}
        <div className="flex flex-col items-center">
          <div className="w-40 h-40">
            <ResponsiveContainer>
              <PieChart>
                <Pie
                  data={userData}
                  cx="50%"
                  cy="50%"
                  outerRadius={70}
                  innerRadius={40}
                  dataKey="value"
                >
                  {userData.map((entry, index) => (
                    <Cell key={`user-cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-3 space-y-1 text-sm">
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded bg-slate-500 inline-block"></span>
              <span>New Users: {newUser}</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded bg-zinc-800 inline-block"></span>
              <span>Registered: {regUser}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="mt-8 flex justify-end">
        <ExportButton onClick={onExport} />
      </div>
    </div>
  );
}
