import React, { useState } from "react";
import PollAnalytics from "../components/UI/Analytics/PollAnalytics";
import FeedbackAnalytics from "../components/UI/Analytics/FeedbackAnalytics";
import AdvertisementTracker from "../components/UI/Analytics/AdvertisementTracker";

export default function AnalyticsPage() {
  const [activeTab, setActiveTab] = useState("polls");

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-semibold text-gray-800">Analytics Dashboard</h1>

      {/* Tabs */}
      <div className="flex gap-3 border-b pb-2">
        <button
          onClick={() => setActiveTab("polls")}
          className={`px-4 py-2 rounded-t-lg ${
            activeTab === "polls"
              ? "bg-blue-600 text-white"
              : "bg-gray-100 text-gray-700 hover:bg-gray-200"
          }`}
        >
          Poll Analytics
        </button>
        <button
          onClick={() => setActiveTab("feedback")}
          className={`px-4 py-2 rounded-t-lg ${
            activeTab === "feedback"
              ? "bg-blue-600 text-white"
              : "bg-gray-100 text-gray-700 hover:bg-gray-200"
          }`}
        >
          Feedback Analytics
        </button>
        <button
          onClick={() => setActiveTab("advertisement")}
          className={`px-4 py-2 rounded-t-lg ${
            activeTab === "advertisement"
              ? "bg-blue-600 text-white"
              : "bg-gray-100 text-gray-700 hover:bg-gray-200"
          }`}
        >
          Advertisement Tracker
        </button>
      </div>

      {/* Conditional Sections */}
      {activeTab === "polls" && <PollAnalytics />}
      {activeTab === "feedback" && <FeedbackAnalytics />}
      {activeTab=== "advertisement" && <AdvertisementTracker/>}
    </div>
  );
}
