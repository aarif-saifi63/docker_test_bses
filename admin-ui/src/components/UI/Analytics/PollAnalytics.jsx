import React, { useEffect, useState } from "react";
import {
  BarChart3,
  CheckCircle,
  Clock,
  FileBarChart,
  Download,
} from "lucide-react";
import apiClient from "../../../services/apiClient";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import EmojiQuestionChart from "./Charts/EmojiQuestionChart";
import ThumbsQuestionChart from "./Charts/ThumbsQuestionChart";
import SliderQuestionChart from "./Charts/SliderQuestionChart";
import TextQuestionChart from "./Charts/TextQuestionChart";
import StarRatingQuestionChart from "./Charts/StarRatingQuestionChart";
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";
import * as XLSX from "xlsx";
import { toast } from "sonner";
import { formatLocalDate } from "../../../utils/time";

export default function PollAnalytics() {
  const [summary, setSummary] = useState(null);
  const [trendData, setTrendData] = useState([]);
  const [analytics, setAnalytics] = useState([]);
  const [loading, setLoading] = useState(false);
  const [filterType, setFilterType] = useState("daily");
  const [startDate, setStartDate] = useState(null);
  const [endDate, setEndDate] = useState(null);

  const fetchPollAnalytics = async (start = null, end = null) => {
    try {
      setLoading(true);

      // Construct query string
      let query = "";
      if (start && end) {
        query = `?start_date=${start}&end_date=${end}`;
      }

      // Call static test API
      const res = await apiClient.get(`/poll-analytics${query}`);
      // const data = await res.json();
      const data = res;

      if (data.status) {
        setSummary(data.summary);
        setTrendData(data.trend_data || []);
        setAnalytics(data.analytics || []);
      } 
    } catch (err) {
      console.error("Error fetching poll analytics:", err);
      toast.error(
        err?.response?.data?.message || "Error fetching poll analytics"
      );
    } finally {
      setLoading(false);
    }
  };

  // ✅ Excel export function
  const exportPollAnalyticsToExcel = () => {
    if (!summary || !analytics?.length) {
      toast.error("No analytics data available to export");
      return;
    }

    // 1️⃣ Analytics Sheet
    const analyticsSheetData = [
      ["Question", "Question Type", "Option", "Count", "Total Responses"],
    ];
    analytics.forEach((item) => {
      item.answers.forEach((ans) => {
        analyticsSheetData.push([
          item.question,
          item.question_type,
          ans.option || "—",
          ans.count,
          item.total_responses,
        ]);
      });
    });

    // 2️⃣ Summary Sheet
    const summarySheetData = [
      ["Summary Field", "Value"],
      ["Total Polls", summary.total_polls || 0],
      ["Active Polls", summary.active_polls || 0],
      ["Inactive Polls", summary.inactive_polls || 0],
      ["Total Responses", summary.total_responses || 0],
      ["Most Responses On", summary.most_responses_on?.date || "-"],
      ["Most Responses Count", summary.most_responses_on?.count || "-"],
      ["Least Responses On", summary.least_responses_on?.date || "-"],
      ["Least Responses Count", summary.least_responses_on?.count || "-"],
    ];

    // 3️⃣ Trend Sheet
    const trendSheetData = [["Date", "Response Count"]];
    if (Array.isArray(trendData)) {
      trendData.forEach((t) => trendSheetData.push([t.date, t.count]));
    }

    // 4️⃣ Create workbook
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(
      workbook,
      XLSX.utils.aoa_to_sheet(summarySheetData),
      "Summary"
    );
    XLSX.utils.book_append_sheet(
      workbook,
      XLSX.utils.aoa_to_sheet(analyticsSheetData),
      "Analytics"
    );
    XLSX.utils.book_append_sheet(
      workbook,
      XLSX.utils.aoa_to_sheet(trendSheetData),
      "Trends"
    );

    // 5️⃣ Download Excel file
    XLSX.writeFile(workbook, "Poll_Analytics_Report.xlsx");
  };

  useEffect(() => {
    applyFilter("daily");
  }, []);

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
        start = new Date();
        start.setDate(today.getDate() - 7);
        break;
      case "monthly":
        start = new Date();
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

    fetchPollAnalytics(startStr, endStr);
  };

  if (loading)
    return <div className="p-6 text-gray-500">Loading Poll Analytics...</div>;
  if (!summary)
    return <div className="p-6 text-gray-500">No poll analytics found</div>;

  return (
    <div className="space-y-8">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-semibold text-gray-800">Poll Analytics</h1>
        <button
          onClick={exportPollAnalyticsToExcel}
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
          {/* Summary */}
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
            <SummaryCard
              title="Total Polls"
              value={summary.total_polls}
              icon={<BarChart3 className="text-blue-500 w-6 h-6" />}
              bg="bg-blue-50"
            />
            <SummaryCard
              title="Active Polls"
              value={summary.active_polls}
              icon={<CheckCircle className="text-green-500 w-6 h-6" />}
              bg="bg-green-50"
            />
            <SummaryCard
              title="Inactive Polls"
              value={summary.inactive_polls}
              icon={<Clock className="text-gray-500 w-6 h-6" />}
              bg="bg-gray-50"
            />
            <SummaryCard
              title="Total Responses"
              value={summary.total_responses}
              icon={<FileBarChart className="text-purple-500 w-6 h-6" />}
              bg="bg-purple-50"
            />
          </div>

          {/* Trend */}
          <div className="bg-white rounded-lg shadow p-4">
            <h2 className="text-lg font-semibold mb-4">
              Poll Response Trend Over Time
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

          {/* Question Analytics */}
          <div>
            <h2 className="text-lg font-semibold mb-4">
              Poll Question Analytics
            </h2>
            <div className="grid md:grid-cols-2 gap-6">
              {analytics.map((q, i) => (
                <QuestionAnalytics key={i} question={q} />
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
        <h2 className="text-2xl font-semibold">{value}</h2>
      </div>
      {icon}
    </div>
  );
}

/* --- Question Analytics Wrapper --- */
function QuestionAnalytics({ question }) {
  const { question_type, question: text, total_responses } = question;

  const renderChart = () => {
    switch (question_type) {
      case "emoji":
        return <EmojiQuestionChart data={question} />;
      case "thumbs":
        return <ThumbsQuestionChart data={question} />;
      case "slider":
        return <SliderQuestionChart data={question} />;
      case "text":
        return <TextQuestionChart data={question} />;
      case "star":
        return <StarRatingQuestionChart data={question} />;
      default:
        return (
          <div className="text-gray-500 text-sm">Unsupported question type</div>
        );
    }
  };

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <h3 className="font-medium mb-2 text-gray-800">{text}</h3>
      {renderChart()}
      <p className="text-sm text-gray-600 mt-2">
        Total Responses: {total_responses}
      </p>
    </div>
  );
}
