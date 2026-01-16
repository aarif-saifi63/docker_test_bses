import React, { useEffect, useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  LineChart,
  Line,
} from "recharts";
import {
  Smile,
  TrendingUp,
  MessageCircle,
  Calendar,
  Download,
} from "lucide-react";
import apiClient from "../../../services/apiClient";
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";
import * as XLSX from "xlsx";
import { formatLocalDate } from "../../../utils/time";
import { toast } from "sonner";

export default function FeedbackAnalytics() {
  const [summary, setSummary] = useState(null);
  const [trendData, setTrendData] = useState([]);
  const [analytics, setAnalytics] = useState([]);
  const [loading, setLoading] = useState(false);
  const [filterType, setFilterType] = useState("daily");
  const [startDate, setStartDate] = useState(null);
  const [endDate, setEndDate] = useState(null);
  const [feedbackLogs, setFeedbackLogs] = useState([]);
  const [language, setLanguage] = useState("");
  // Fetch feedback analytics with optional date filter
  const fetchFeedbackAnalytics = async (start = null, end = null) => {
    try {
      setLoading(true);

      // Construct query string
      let query = "";
      if (start && end) {
        query = `start_date=${start}&end_date=${end}&`;
      }

      if (language) {
        query = query + `language=${language}`;
      }

      // Call API with query string
      const res = await apiClient.get(`/feedback-analytics?${query}`);
      // const data = await res.json();
      const data = res;

      if (data.status) {
        setSummary(data?.summary);
        setTrendData(data?.trend_data || []);
        setAnalytics(data?.analytics || []);
        setFeedbackLogs(res?.feedback_logs);
      } else {
        toast.error("Failed to fetch feedback analytics");
      }
    } catch (err) {
      console.error(
        err?.response?.data?.message || "Error fetching feedback analytics:",
        err
      );
    } finally {
      setLoading(false);
    }
  };

  // Apply filter: daily, weekly, monthly, or custom
  const applyFilter = (type) => {
    setFilterType(type);
    const today = new Date();
    let start = null;
    let end = today;

    switch (type) {
      case "daily":
        start = today;
        break;
      case "weekly":
        start = new Date(today);
        start.setDate(today.getDate() - 7);
        break;
      case "monthly":
        start = new Date(today);
        start.setMonth(today.getMonth() - 1);
        break;
      case "custom":
        if (startDate && endDate) {
          start = startDate;
          end = endDate;
        } else {
          toast.error("Please select start and end dates for custom filter.");
          return;
        }
        break;
      default:
        start = null;
        end = null;
    }

    const startStr = formatLocalDate(start);
    const endStr = formatLocalDate(end);

    fetchFeedbackAnalytics(startStr, endStr);
  };

  // Initial fetch with daily filter
  useEffect(() => {
    applyFilter("daily");
  }, []);

  // ✅ Export to Excel Function
  const exportFeedbackAnalyticsToExcel = () => {
    try {
      const wb = XLSX.utils.book_new();

      // ---- Summary Sheet ----
      const summarySheet = XLSX.utils.json_to_sheet([
        {
          "Total Feedbacks": summary.total_feedbacks,
          "Total Questions": summary.total_questions,
          "Most Feedbacks On": `${summary.most_feedbacks_on.date} (${summary.most_feedbacks_on.count})`,
          "Least Feedbacks On": `${summary.least_feedbacks_on.date} (${summary.least_feedbacks_on.count})`,
        },
      ]);
      XLSX.utils.book_append_sheet(wb, summarySheet, "Summary");

      // ---- Trend Data Sheet ----
      const trendSheet = XLSX.utils.json_to_sheet(trendData);
      XLSX.utils.book_append_sheet(wb, trendSheet, "Trend Data");

      // ---- Question Analytics Sheet ----
      const questionRows = [];
      analytics.forEach((q) => {
        questionRows.push({
          Question: q.question,
          "Total Responses": q.total_responses,
          "Question Type": q.question_type,
        });
        q.answers.forEach((a) => {
          questionRows.push({ Option: a.option, Count: a.count });
        });
        questionRows.push({}); // blank line
      });
      const analyticsSheet = XLSX.utils.json_to_sheet(questionRows);
      XLSX.utils.book_append_sheet(wb, analyticsSheet, "Question Analytics");

      // ---- Feedback Logs Sheet ----
      if (feedbackLogs && feedbackLogs.length > 0) {
        const feedbackRows = [];

        feedbackLogs.forEach((log) => {
          const createdAt = new Date(log.created_at).toLocaleString();
          const feedbackId = log.feedback_id;
          const ca_number = log.ca_number;
          const user_type = log.user_type;

          log.response.forEach((res) => {
            feedbackRows.push({
              Question: res.question,
              Answer: res.answer,
              "Ca Number": ca_number,
              "User Type": user_type,
              "Feedback ID": feedbackId,
              "Created At": createdAt,
            });
          });

          feedbackRows.push({}); // blank line between feedbacks
        });

        const feedbackSheet = XLSX.utils.json_to_sheet(feedbackRows);
        XLSX.utils.book_append_sheet(wb, feedbackSheet, "Feedback Logs");
      }

      // ---- Save File ----
      XLSX.writeFile(
        wb,
        `Feedback_Analytics_${new Date().toISOString().split("T")[0]}.xlsx`
      );
    } catch (err) {
      console.error("Excel export failed:", err);
      toast.error("Failed to export Excel file");
    }
  };

  if (loading)
    return (
      <div className="p-6 text-gray-500">Loading Feedback Analytics...</div>
    );
  if (!summary)
    return <div className="p-6 text-gray-500">No feedback analytics found</div>;

  return (
    <div className="space-y-8">
      {/* Header with Export Button */}
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-semibold text-gray-800">
          Feedback Analytics
        </h1>
        <button
          onClick={exportFeedbackAnalyticsToExcel}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg shadow hover:bg-blue-700 transition"
        >
          <Download className="w-4 h-4" /> Export to Excel
        </button>
      </div>
      {/* ---- Filter Bar ---- */}
      <div className="flex flex-wrap items-center justify-between gap-4 bg-white p-4 rounded-lg shadow">
        <div className="flex items-center gap-2">
          {/* <Filter className="text-gray-600" /> */}
          <span className="font-medium text-gray-700">Filter:</span>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {["daily", "weekly", "monthly"].map((type) => (
            <button
              key={type}
              onClick={() => applyFilter(type)}
              disabled={loading}
              className={`px-4 py-2 rounded-md text-sm font-medium ${
                filterType === type
                  ? "bg-blue-600 text-white"
                  : "bg-gray-100 hover:bg-gray-200 text-gray-700"
              } ${loading ? "opacity-50 cursor-not-allowed" : ""}`}
            >
              {type.charAt(0).toUpperCase() + type.slice(1)}
            </button>
          ))}

          {/* Custom Range */}
          <div className="flex items-center gap-2">
            <select
              onChange={(e) => setLanguage(e.target.value)}
              value={language}
              className="px-4 py-2 rounded-md text-sm font-medium"
            >
              <option value={"English"}>English</option>
              <option value={"Hindi"}>Hindi</option>
            </select>
            <DatePicker
              selected={startDate}
              onChange={(date) => setStartDate(date)}
              placeholderText="Start Date"
              className="border border-gray-300 rounded-md px-2 py-1 text-sm"
              disabled={loading}
            />
            <DatePicker
              selected={endDate}
              onChange={(date) => setEndDate(date)}
              placeholderText="End Date"
              className="border border-gray-300 rounded-md px-2 py-1 text-sm"
              disabled={loading}
            />
            <button
              onClick={() => applyFilter("custom")}
              disabled={loading}
              className={`px-4 py-2 rounded-md text-sm font-medium ${
                filterType === "custom"
                  ? "bg-blue-600 text-white"
                  : "bg-gray-100 hover:bg-gray-200 text-gray-700"
              } ${loading ? "opacity-50 cursor-not-allowed" : ""}`}
            >
              Apply
            </button>
          </div>
        </div>
      </div>

      {/* ---- Loading State ---- */}
      {loading && (
        <div className="p-6 text-gray-500">Loading Poll Analytics...</div>
      )}

      {!loading && (!summary || Object.keys(summary).length === 0) && (
        <div className="p-6 text-gray-500">No poll analytics found</div>
      )}

      {!loading && summary && (
        <>
          {/* Summary Cards */}
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
            <SummaryCard
              title="Total Feedbacks"
              value={summary.total_feedbacks}
              icon={<MessageCircle className="text-blue-500 w-6 h-6" />}
              bg="bg-blue-50"
            />
            <SummaryCard
              title="Total Questions"
              value={summary.total_questions}
              icon={<Smile className="text-green-500 w-6 h-6" />}
              bg="bg-green-50"
            />
            <SummaryCard
              title="Most Feedbacks On"
              value={`${summary.most_feedbacks_on.date} (${summary.most_feedbacks_on.count})`}
              icon={<TrendingUp className="text-purple-500 w-6 h-6" />}
              bg="bg-purple-50"
            />
            <SummaryCard
              title="Least Feedbacks On"
              value={`${summary.least_feedbacks_on.date} (${summary.least_feedbacks_on.count})`}
              icon={<Calendar className="text-gray-500 w-6 h-6" />}
              bg="bg-gray-50"
            />
          </div>

          {/* Trend Chart */}
          <div className="bg-white rounded-lg shadow p-4">
            <h2 className="text-lg font-semibold mb-4">
              Feedback Trend Over Time
            </h2>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={trendData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis allowDecimals={false} />
                <Tooltip />
                <Line
                  type="monotone"
                  dataKey="count"
                  stroke="#2563eb"
                  strokeWidth={2}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Question Breakdown */}
          <div>
            <h2 className="text-lg font-semibold mb-4">Question Analytics</h2>
            <div className="grid md:grid-cols-2 gap-6">
              {analytics.map((q, i) => (
                <div key={i} className="bg-white rounded-lg shadow p-4">
                  <h3 className="font-medium mb-2 text-gray-800">
                    {q.question}
                  </h3>
                  <ResponsiveContainer width="100%" height={200}>
                    <BarChart data={q.answers}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="option" />
                      <YAxis allowDecimals={false} />
                      <Tooltip />
                      <Bar dataKey="count" fill="#3b82f6" />
                    </BarChart>
                  </ResponsiveContainer>
                  <p className="text-sm text-gray-600 mt-2">
                    Total Responses: {q.total_responses}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

/* --- Summary Card --- */
function SummaryCard({ title, value, icon, bg }) {
  return (
    <div
      className={`${bg} rounded-lg shadow p-4 flex items-center justify-between`}
    >
      <div>
        <p className="text-sm text-gray-600">{title}</p>
        <h2 className="text-lg font-semibold">{value}</h2>
      </div>
      {icon}
    </div>
  );
}
