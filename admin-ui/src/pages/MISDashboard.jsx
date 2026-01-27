import React, { useEffect, useState } from "react";
import * as XLSX from "xlsx";
import { saveAs } from "file-saver";
import apiClient from "../services/apiClient";
import ExportButton from "../components/Mis/ExportButton";
import HourlyReportChart from "../components/Mis/HourlyReportChart";
import ChatStatusChart from "../components/Mis/ChatStatusChart";
import InteractionRow from "../components/Dashboard/InteractionRow";
import InteractionMisModal from "../components/Mis/InteractionMisModel";
import InteractionsHeader from "../components/Mis/InteractionsHeader";
import Loader from "../components/Common/Loader";
import { toast } from "sonner";

export default function MISDashboard() {
  const [activeTab, setActiveTab] = useState("Daily");
  // const [selectedDate, setSelectedDate] = useState(new Date());
  const [startDate, setStartDate] = useState(new Date());
  const [endDate, setEndDate] = useState(new Date());
  const [peakData, setPeakData] = useState(null);
  const [chatStatusData, setChatStatusData] = useState(null);
  const [fullChatData, setFullChatData] = useState(null);
  const [averageData, setAverageData] = useState(null);
  const [interactionsData, setInteractionsData] = useState([]);
  const [TotalInteraction, setTotalInteraction] = useState(null);
  const [paybillCount, setPaybillCount] = useState(0);
  const [Visually, setVisually] = useState(0);
  const [modalData, setModalData] = useState(null);
  const [isDatePickerOpen, setIsDatePickerOpen] = useState(false);
  const [division, setDivision] = useState("");
  const [caNumber, setCaNumber] = useState("");
  const [telNo, setTelNo] = useState("");
  const [source, setSource] = useState("");
  const [startHour, setStartHour] = useState("");
  const [endHour, setEndHour] = useState("");

  // Loading states
  const [peakLoading, setPeakLoading] = useState(false);
  const [chatLoading, setChatLoading] = useState(false);
  const [avgLoading, setAvgLoading] = useState(false);
  const [paybillLoading, setPaybillLoading] = useState(false);
  const [visuallyLoading, setVisuallyLoading] = useState(false);
  const [interactionsLoading, setInteractionsLoading] = useState(false);

  // Complaint API states
  const [complaint, setComplaint] = useState(null);
  const [complaintLoading, setComplaintLoading] = useState(false);
  const [modalComplaintData, setModalComplaintData] = useState(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [modalTitle, setModalTitle] = useState("");

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const perPage = 5;

  // Format helpers
  const formatDate = (date) => date.toISOString().split("T")[0];
  const formatMonth = (date) => date.toISOString().slice(0, 7);

  // Params for API
  // const getParams = (page = currentPage, apiName = "") => {
  //   let params = {};

  //   if (apiName === "peak") {
  //     if (activeTab === "Daily" || activeTab === "Date")
  //       params = { date: formatDate(selectedDate) };
  //     else if (activeTab === "Monthly") params = { month: formatMonth(selectedDate) };
  //     else if (activeTab === "Hourly") params = { last_hour: true };
  //   } else {
  //     if (activeTab === "Hourly") params = { last_hour: true };
  //     else if (activeTab === "Daily" || activeTab === "Date")
  //       params = { date: formatDate(selectedDate) };
  //     else if (activeTab === "Monthly") params = { month: formatMonth(selectedDate) };
  //   }

  //   if (division) params.division_name = division;

  //   if (apiName === "interactions") {
  //     params.page = page;
  //     params.per_page = perPage;
  //   }
  //   return params;
  // };

  // const getParams = (page = currentPage, apiName = "") => {
  //   let params = {};

  //   if (apiName === "peak") {
  //     if (activeTab === "Daily" || activeTab === "Date")
  //       params = { date: formatDate(selectedDate) };
  //     else if (activeTab === "Monthly") params = { month: formatMonth(selectedDate) };
  //     else if (activeTab === "Hourly") params = { last_hour: true };
  //   } else {
  //     if (activeTab === "Hourly") params = { last_hour: true };
  //     else if (activeTab === "Daily" || activeTab === "Date")
  //       params = { date: formatDate(selectedDate) };
  //     else if (activeTab === "Monthly") params = { month: formatMonth(selectedDate) };
  //   }

  //   if (division) params.division_name = division;
  //   if (caNumber) params.ca_number = caNumber;
  //   if (telNo) params.tel_no = telNo;
  //   if (source) params.source = source;

  //   if (apiName === "interactions") {
  //     params.page = page;
  //     params.per_page = perPage;
  //   }

  //   return params;
  // };

  const openModal = (title) => {
  setModalTitle(title);
  setModalOpen(true);
};

const closeModal = () => {
  setModalOpen(false);
  setModalTitle("");
};

  
  const getParams = (page = currentPage, apiName = "") => {
  let params = {};

 
  const formatLocalDate = (date) => {
    if (!date) return null;
    const d = new Date(date.getTime() - date.getTimezoneOffset() * 60000);
    return d.toISOString().split("T")[0];
  };

  const formatLocalMonth = (date) => formatLocalDate(date).slice(0, 7);

  
  if (activeTab === "Hourly") {
    params.last_hour = true;
  } else if (activeTab === "Daily" || activeTab === "Date") {
    params.start_date = formatLocalDate(startDate);
    params.end_date = formatLocalDate(endDate);
  } else if (activeTab === "Monthly") {
    params.month = formatLocalMonth(startDate);
  }

  // 🔹 Special case for peak-time APIs
  if (apiName === "peak" && (activeTab === "Daily" || activeTab === "Date")) {
    params.start_date = formatLocalDate(startDate);
    params.end_date = formatLocalDate(endDate);
  }

  // 🔹 Add filters
  if (division) params.division_name = division;
  if (caNumber) params.ca_number = `${caNumber} BRPL`;
  if (telNo) params.tel_no = telNo;
  if (source) params.source = source;

  // 🔹 Add hour filters
  if (startHour) params.start_hour = startHour;
  if (endHour) params.end_hour = endHour;

  // 🔹 Pagination
  if (apiName === "interactions") {
    params.page = page;
    params.per_page = perPage;
  }

  return params;
};

 
  const fetchPeak = async () => {
    setPeakLoading(true);
    try {
      const peak = await apiClient.get("/mis/peak-hours", getParams(1, "peak"));
      setPeakData(peak);
    } catch (err) {
      console.error(err);
    } finally {
      setPeakLoading(false);
    }
  };

  const fetchChat = async () => {
    setChatLoading(true);
    try {
      const chat = await apiClient.get(
        "/mis/chat-completion-status",
        getParams()
      );
      setFullChatData(chat); // Store full response with filters and stats
      setChatStatusData(
        chat?.stats?.[0] || {
          total_sessions: 0,
          completed_chats: 0,
          left_chats: 0,
        }
      );
    } catch (err) {
      console.error(err);
    } finally {
      setChatLoading(false);
    }
  };

  const fetchAvg = async () => {
    setAvgLoading(true);
    try {
      const avg = await apiClient.get(
        "/mis/avg-interaction-duration",
        getParams()
      );
      setAverageData(avg?.daily_avg_interaction_duration?.[0] || null);
    } catch (err) {
      console.error(err);
    } finally {
      setAvgLoading(false);
    }
  };

  const fetchPaybill = async () => {
    setPaybillLoading(true);
    try {
      const paybill = await apiClient.get("/mis/pay-bill", getParams());
      setPaybillCount(paybill?.stats?.[0]?.pay_bill_count || 0);
    } catch (err) {
      console.error(err);
    } finally {
      setPaybillLoading(false);
    }
  };

  const fetchVisually = async () => {
    setVisuallyLoading(true);
    try {
      const visually = await apiClient.get(
        "/mis/visually-impaired-analysis",
        getParams()
      );
      setVisually(visually || { total_completed: 0, users: [] });
    } catch (err) {
      console.error(err);
    } finally {
      setVisuallyLoading(false);
    }
  };

  const fetchInteractions = async (page = 1) => {
    setInteractionsLoading(true);
    try {
      const interactions = await apiClient.get(
        "/mis/interactions-breakdown",
        getParams(page, "interactions")
      );
      setInteractionsData(interactions?.data || []);
      setTotalInteraction(interactions || null);

      if (interactions?.total_pages) setTotalPages(interactions.total_pages);
      setCurrentPage(page);
    } catch (err) {
      console.error(err);
    } finally {
      setInteractionsLoading(false);
    }
  };

  const fetchComplaints = async () => {
    setComplaintLoading(true);
    try {
      const res = await apiClient.get("/dashboard/complaint-status");
      setComplaint(res?.stats || {});
      setModalComplaintData(res?.data || {});
    } catch (err) {
      console.error("Complaint fetch error:", err);
      toast.error("Failed to fetch complaint stats");
    } finally {
      setComplaintLoading(false);
    }
  };

  const fetchAllData = () => {
    fetchPeak();
    fetchChat();
    fetchAvg();
    fetchPaybill();
    fetchVisually();
    fetchInteractions(1);
    fetchComplaints();
  };

  useEffect(() => {
    // Skip auto-fetch if CA number or Tel no is being used
    if (caNumber || telNo) return;

    const handler = setTimeout(() => {
      fetchAllData();
    }, 600);

    return () => clearTimeout(handler);
  }, [activeTab, startDate, endDate, division, source]);

  // Fetch ALL data when filters (tab, date, division) change
  // useEffect(() => {
  //   fetchPeak();
  //   fetchChat();
  //   fetchAvg();
  //   fetchPaybill();
  //   fetchVisually();
  //   fetchInteractions(1);
  // }, [activeTab, selectedDate, division, caNumber, telNo]);

  // useEffect(() => {
  //   const handler = setTimeout(() => {
  //     fetchPeak();
  //     fetchChat();
  //     fetchAvg();
  //     fetchPaybill();
  //     fetchVisually();
  //     fetchInteractions(1);
  //   }, 600); // ⏱️ 600ms debounce time

  //   // Cleanup: clear timeout if user keeps typing/changing filters
  //   return () => clearTimeout(handler);
  // }, [activeTab, startDate, endDate, division, caNumber, telNo, source]);

  // Pagination handlers (only interactions API)
  const goToPage = (page) => {
    if (page >= 1 && page <= totalPages) {
      fetchInteractions(page);
    }
  };
  const goToNextPage = () => {
    if (currentPage < totalPages) goToPage(currentPage + 1);
  };
  const goToPrevPage = () => {
    if (currentPage > 1) goToPage(currentPage - 1);
  };

  // Export handlers
  const handleExportPeak = () => {
    if (!peakData) return;

    const dataToExport = peakData.hourly_report || [];
    const worksheet = XLSX.utils.json_to_sheet(dataToExport);
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, "Peak Hours");

    const excelBuffer = XLSX.write(workbook, {
      bookType: "xlsx",
      type: "array",
    });
    const blob = new Blob([excelBuffer], { type: "application/octet-stream" });
    saveAs(blob, "peak_hours_report.xlsx");
  };

  const handleExportChat = () => {
    if (!fullChatData || !fullChatData.stats) return;

    const statsData = fullChatData.stats.map((stat, index) => ({
      "S.No": index + 1,
      "Total Sessions": stat.total_sessions || 0,
      "Completed Chats": stat.completed_chats || 0,
      "Left Chats": stat.left_chats || 0,
      "English Sessions": stat.english_sessions || 0,
      "Hindi Sessions": stat.hindi_sessions || 0,
      "New User Sessions": stat.new_user_sessions || 0,
      "Registered User Sessions": stat.registered_user_sessions || 0,
    }));

    const worksheet = XLSX.utils.json_to_sheet(statsData);
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, "Chat Completion Stats");

    const excelBuffer = XLSX.write(workbook, {
      bookType: "xlsx",
      type: "array",
    });
    const blob = new Blob([excelBuffer], { type: "application/octet-stream" });
    saveAs(blob, "chat_completion_report.xlsx");
  };

  const handleExportVisually = () => {
    if (!Visually || !Visually.users || Visually.users.length === 0) return;

    const dataToExport = Visually.users.map((user, index) => ({
      "S.No": index + 1,
      "CA Number": user.ca_number || "N/A",
      "Phone Number": user.phone_number || "N/A",
      "User Type": user.user_type || "N/A",
      Division: user.division_name || "N/A",
      Date: user.date || "",
    }));

    dataToExport.push({
      "S.No": "",
      "CA Number": "",
      "Phone Number": "",
      "User Type": "",
      Division: "Total Resolved",
      Date: Visually.total_completed || 0,
    });

    const worksheet = XLSX.utils.json_to_sheet(dataToExport);
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, "Visually Impaired");

    const excelBuffer = XLSX.write(workbook, {
      bookType: "xlsx",
      type: "array",
    });
    const blob = new Blob([excelBuffer], { type: "application/octet-stream" });
    saveAs(blob, "visually_impaired_report.xlsx");
  };

  // Summary cards
  const summary = [
  {
    label: "No Supply Complaint Registered (Both)",
    icon: "⚡",
    color: "bg-red-50 text-red-600",
    value: complaint?.total_complaints || 0,
    loading: complaintLoading,
    onClick: () => openModal("No Supply Complaint Registered"),
  },
  {
    label: "Complaints Resolved (Both)",
    icon: "✅",
    color: "bg-green-50 text-green-600",
    value: complaint?.resolved_complaints || 0,
    loading: complaintLoading,
    onClick: () => openModal("Complaints Resolved"),
  },
  {
    label: "Visually Impaired Analysis Resolved (Both)",
    icon: "👁️",
    color: "bg-blue-50 text-blue-600",
    value: Visually?.total_completed || 0,
    loading: visuallyLoading,
    onClick: handleExportVisually,
  },
];


  return (
    <div className="min-h-screen bg-gray-50 p-6 space-y-6">
      <InteractionsHeader
        title="MIS Report"
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        startDate={startDate}
        setStartDate={setStartDate}
        endDate={endDate}
        setEndDate={setEndDate}
        isDatePickerOpen={isDatePickerOpen}
        setIsDatePickerOpen={setIsDatePickerOpen}
        formatDate={formatDate}
        division={division}
        setDivision={setDivision}
        caNumber={caNumber}
        setCaNumber={setCaNumber}
        telNo={telNo}
        setTelNo={setTelNo}
        source={source}
        setSource={setSource}
        startHour={startHour}
        setStartHour={setStartHour}
        endHour={endHour}
        setEndHour={setEndHour}
        fetchAllData={fetchAllData}
      />

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div>
          {peakLoading ? (
            <Loader text="Fetching Peak Data..." />
          ) : (
            <HourlyReportChart
              data={peakData?.hourly_report || []}
              peakHour={peakData?.peak_hour}
              onExport={handleExportPeak}
            />
          )}
        </div>
        <div>
          {chatLoading || avgLoading ? (
            <Loader text="Fetching Chat Data..." />
          ) : (
            <ChatStatusChart
              data={chatStatusData}
              averageData={averageData}
              onExport={handleExportChat}
            />
          )}
        </div>
      </div>

      {/* Interactions Breakdown */}
      <div className="space-y-2">
        <div className="flex justify-between items-center mb-2 px-2">
          <h3 className="text-lg font-semibold">
            Total Interaction ({TotalInteraction?.total_interactions})
          </h3>
        </div>

        <div className="h-[500px] overflow-y-auto space-y-6 border border-gray-200 p-2 rounded">
          {interactionsLoading ? (
            <Loader text="Loading Interactions..." />
          ) : interactionsData.length === 0 ? (
            <p className="text-gray-500 text-center py-10">
              No interactions found
            </p>
          ) : (
            interactionsData.map((item, idx) => (
              <InteractionRow
                key={idx}
                item={item}
                setModalData={setModalData}
              />
            ))
          )}
        </div>
      </div>

      {/* Pagination - Only show when there are pages */}
      {totalPages > 0 && (
        <div className="flex justify-center items-center space-x-2 mt-4">
          <button
            onClick={() => goToPage(1)}
            disabled={currentPage === 1}
            className="px-3 py-1 bg-gray-200 rounded disabled:opacity-50 hover:bg-gray-300 transition-colors"
          >
            First
          </button>

          <button
            onClick={goToPrevPage}
            disabled={currentPage === 1}
            className="px-3 py-1 bg-gray-200 rounded disabled:opacity-50 hover:bg-gray-300 transition-colors"
          >
            Previous
          </button>

          {Array.from({ length: totalPages }, (_, i) => i + 1)
            .filter((num) => {
              if (num === 1 || num === totalPages) return true;
              if (num >= currentPage - 2 && num <= currentPage + 2) return true;
              return false;
            })
            .map((num, idx, arr) => {
              const prev = arr[idx - 1];
              if (prev && num - prev > 1) {
                return (
                  <span key={`dots-${num}`} className="px-2">
                    ...
                  </span>
                );
              }
              return (
                <button
                  key={num}
                  onClick={() => goToPage(num)}
                  className={`px-3 py-1 rounded transition-colors ${
                    num === currentPage
                      ? "bg-blue-600 text-white"
                      : "bg-gray-200 text-black hover:bg-gray-300"
                  }`}
                >
                  {num}
                </button>
              );
            })}

          <button
            onClick={goToNextPage}
            disabled={currentPage === totalPages}
            className="px-3 py-1 bg-gray-200 rounded disabled:opacity-50 hover:bg-gray-300 transition-colors"
          >
            Next
          </button>

          <button
            onClick={() => goToPage(totalPages)}
            disabled={currentPage === totalPages}
            className="px-3 py-1 bg-gray-200 rounded disabled:opacity-50 hover:bg-gray-300 transition-colors"
          >
            Last
          </button>
        </div>
      )}

      {/* Modal */}
      <InteractionMisModal
        modalData={modalData}
        onClose={() => setModalData(null)}
      />

      {/* Summary Cards */}
      {/* <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
        {summary.map((card) => (
          <div
            key={card.label}
            className={`rounded-2xl shadow p-4 flex justify-between items-center ${card.color}`}
          >
            <div className="flex items-center gap-4">
              <span className="text-3xl">{card.icon}</span>
              <div>
                <div className="text-lg font-bold">
                  {card.label === "Payment Initiated" && paybillLoading
                    ? "Loading..."
                    : card.label === "Visually Impaired Analysis Resolved" && visuallyLoading
                    ? "Loading..."
                    : card.value}
                </div>
                <div className="text-sm">{card.label}</div>
              </div>
            </div>

            {card.label === "Visually Impaired Analysis Resolved" && (
              <button
                onClick={handleExportVisually}
                className="text-xs bg-blue-600 text-white px-2 py-1 rounded hover:bg-blue-700"
              >
                Export
              </button>
            )}
          </div>
        ))}
      </div> */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
        {summary.map((card) => (
          <div
            key={card.label}
            className={`rounded-2xl shadow p-4 flex justify-between items-center ${card.color}`}
          >
            <div className="flex items-center gap-4">
              <span className="text-3xl">{card.icon}</span>
              <div>
                <div className="text-lg font-bold">
                  {card.loading ? "Loading..." : card.value}
                </div>
                <div className="text-sm">{card.label}</div>
              </div>
            </div>

            {card.onClick && (
              <button
                onClick={card.onClick}
                className="text-xs bg-blue-600 text-white px-2 py-1 rounded hover:bg-blue-700"
              >
                View
              </button>
            )}
          </div>
        ))}
      </div>

      {modalOpen && (
  <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
    <div className="bg-white rounded-xl shadow-lg w-full max-w-md p-6 relative">
      <button
        onClick={closeModal}
        className="absolute top-3 right-3 text-gray-400 hover:text-gray-600"
      >
        ✕
      </button>

      <div className="flex items-center gap-2 mb-4">
        <h2 className="text-lg font-semibold text-gray-800">{modalTitle}</h2>
      </div>

      {modalComplaintData ? (
        <div className="space-y-4 max-h-96 overflow-y-auto text-sm text-gray-700">
          {/* --- All Complaints --- */}
          <div>
            <h3 className="font-semibold text-gray-800 mb-1 border-b border-gray-100 pb-1">
              All Complaints
            </h3>
            {modalComplaintData.all_complaints?.length > 0 ? (
              <ul className="space-y-1 pl-2">
                {modalComplaintData.all_complaints.map((item, idx) => (
                  <li
                    key={idx}
                    className="border-b last:border-none pb-1 font-mono text-xs break-all"
                  >
                    {item}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-gray-400 italic text-xs">
                No complaints found.
              </p>
            )}
          </div>

          {/* --- Resolved Complaints --- */}
          <div>
            <h3 className="font-semibold text-gray-800 mb-1 border-b border-gray-100 pb-1">
              Resolved Complaints
            </h3>
            {modalComplaintData.resolved_complaints_list?.length > 0 ? (
              <ul className="space-y-1 pl-2">
                {modalComplaintData.resolved_complaints_list.map(
                  (item, idx) => (
                    <li
                      key={idx}
                      className="border-b last:border-none pb-1 font-mono text-xs break-all text-green-700"
                    >
                      {item}
                    </li>
                  )
                )}
              </ul>
            ) : (
              <p className="text-gray-400 italic text-xs">
                No resolved complaints.
              </p>
            )}
          </div>

          {/* --- Unique Users --- */}
          <div>
            <h3 className="font-semibold text-gray-800 mb-1 border-b border-gray-100 pb-1">
              Unique Users
            </h3>

            {modalComplaintData.users?.length > 0 ? (
              <ul className="space-y-3 pl-2">
                {modalComplaintData.users.map((user, idx) => (
                  <li
                    key={idx}
                    className="border-b last:border-none pb-2 text-xs font-mono break-all"
                  >
                    <div>
                      <span className="font-semibold">CA Number:</span>{" "}
                      {user.ca_number || "—"}
                    </div>
                    <div>
                      <span className="font-semibold">Tel No:</span>{" "}
                      {user.tel_no || "—"}
                    </div>
                    <div>
                      <span className="font-semibold">Source:</span>{" "}
                      {user.source || "—"}
                    </div>
                    <div>
                      <span className="font-semibold">Division:</span>{" "}
                      {user.division_name || "—"}
                    </div>

                    {/* Nested complaints */}
                    <div className="mt-1">
                      <span className="font-semibold">Complaints:</span>
                      {user.complaints?.length > 0 ? (
                        <ul className="ml-4 list-disc">
                          {user.complaints.map((comp, cIdx) => (
                            <li
                              key={cIdx}
                              className={`text-xs ${
                                comp.status === "resolved"
                                  ? "text-green-700"
                                  : "text-orange-600"
                              }`}
                            >
                              {comp.complaint_no} — {comp.status}
                            </li>
                          ))}
                        </ul>
                      ) : (
                        <p className="text-gray-400 italic ml-4 text-xs">
                          No complaints listed.
                        </p>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-gray-400 italic text-xs">
                No unique users found.
              </p>
            )}
          </div>
        </div>
      ) : (
        <p className="text-gray-400 italic text-sm">No data found.</p>
      )}
    </div>
  </div>
)}

    </div>
  );
}
