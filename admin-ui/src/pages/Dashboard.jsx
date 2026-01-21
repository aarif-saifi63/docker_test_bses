import { useState, useEffect } from "react";
import StatsCard from "../components/Dashboard/StatsCard.jsx";
import InteractionsHeader from "../components/Dashboard/InteractionsHeader.jsx";
import InteractionRow from "../components/Dashboard/InteractionRow.jsx";
// import InteractionLogModal from "../components/Common/InteractionLogModal.jsx";
import InteractionMisModal from "../components/Mis/InteractionMisModel.jsx";
import ChatMetricsChart from "../components/Dashboard/ChatMetricsChart.jsx";
import Loader from "../components/Common/Loader.jsx";
import { Zap, CheckCircle2, Wallet, FileText, List } from "lucide-react";
import apiClient from "../services/apiClient.js";
import { toast } from "sonner";

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState("Daily");
  const [startDate, setStartDate] = useState(new Date());
  const [endDate, setEndDate] = useState(new Date());
  const [isDatePickerOpen, setIsDatePickerOpen] = useState(false);

  // Data states
  const [avgTimeData, setAvgTimeData] = useState(null);
  const [sessionsData, setSessionsData] = useState(null);
  const [chatStatusData, setChatStatusData] = useState(null);
  const [payBillStats, setPayBillStats] = useState(null);
  const [ebillStats, setEbillStats] = useState(null);
  const [complaint, setComplainStats] = useState(null);
  const [DuplicateStats, setDuplicateStats] = useState(null);
  const [interactionsData, setInteractionsData] = useState([]);
  const [modalData, setModalData] = useState(null);
  const [peakData, setPeakData] = useState(null);
  const [division, setDivision] = useState("");
  const [caNumber, setCaNumber] = useState("");
  const [telNo, setTelNo] = useState("");
  const [source, setSource] = useState("");
  const [startHour, setStartHour] = useState("");
  const [endHour, setEndHour] = useState("");

  // Loading states
  const [avgLoading, setAvgLoading] = useState(false);
  const [sessionsLoading, setSessionsLoading] = useState(false);
  const [chatLoading, setChatLoading] = useState(false);
  const [interactionsLoading, setInteractionsLoading] = useState(false);
  const [paybillLoading, setPaybillLoading] = useState(false);
  const [ebillLoading, setEbillLoading] = useState(false);
  const [complaintLoading, setComplaintLoading] = useState(false);
  const [duplicateLoading, setDuplicateLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [modalTitle, setModalTitle] = useState("");
  const [modalComplaintData, setModalComplaintData] = useState(null);

  const [chatStatusModalOpen, setChatStatusModalOpen] = useState(false);
  const [chatStatusDetails, setChatStatusDetails] = useState(null);

  const [ebillModalOpen, setEbillModalOpen] = useState(false);
  const [ebillModalData, setEbillModalData] = useState(null);

  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const perPage = 5;

  // ✅ Format date as YYYY-MM-DD in local time (no UTC shift)
  const formatLocalDate = (date) => {
    if (!date) return null;
    const d = new Date(date.getTime() - date.getTimezoneOffset() * 60000);
    return d.toISOString().split("T")[0];
  };

  const formatDate = (date) => date.toISOString().split("T")[0];
  const formatMonth = (date) => date.toISOString().slice(0, 7);

  // Params builder
  // const getParams = (page = currentPage, apiName = "") => {
  //   let params = {};

  //   const formatDate = (date) => date.toISOString().split("T")[0];
  //   const formatMonth = (date) => date.toISOString().slice(0, 7);

  //   // 🔹 Handle time filters
  //   if (activeTab === "Hourly") {
  //     params.last_hour = true;
  //   } else if (activeTab === "Daily" || activeTab === "Date") {
  //     params.start_date = formatDate(startDate);
  //     params.end_date = formatDate(endDate);
  //   } else if (activeTab === "Monthly") {
  //     params.month = formatMonth(startDate);
  //   }

  //   // 🔹 Handle special API cases (optional)
  //   if (apiName === "peak" && (activeTab === "Daily" || activeTab === "Date")) {
  //     params.start_date = formatDate(startDate);
  //     params.end_date = formatDate(endDate);
  //   }

  //   // 🔹 Add filters
  //   if (division) params.division_name = division;
  //   if (caNumber) params.ca_number = `${caNumber} BRPL`;
  //   if (telNo) params.tel_no = telNo;
  //   if (source) params.source = source;

  //   // 🔹 Pagination
  //   if (apiName === "interactions") {
  //     params.page = page;
  //     params.per_page = perPage;
  //   }

  //   return params;
  // };

  const getParams = (page = currentPage, apiName = "") => {
  let params = {};

  // ✅ Fix: format date in local timezone, not UTC
  const formatLocalDate = (date) => {
    if (!date) return null;
    const d = new Date(date.getTime() - date.getTimezoneOffset() * 60000);
    return d.toISOString().split("T")[0];
  };

  const formatLocalMonth = (date) => formatLocalDate(date).slice(0, 7);

  // 🔹 Handle time filters
  if (activeTab === "Hourly") {
    params.last_hour = true;
  } else if (activeTab === "Daily" || activeTab === "Date") {
    params.start_date = formatLocalDate(startDate);
    params.end_date = formatLocalDate(endDate);
  } else if (activeTab === "Monthly") {
    params.month = formatLocalMonth(startDate);
  }

  // 🔹 Handle special API cases (optional)
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


  // Fetch average interaction time
  async function fetchAvg() {
    setAvgLoading(true);
    try {
      const res = await apiClient.get(
        "/dashboard/average-interaction-time",
        getParams(1, "avg")
      );
      setAvgTimeData(res);
    } catch (err) {
      console.error(err);
      toast.error(err?.response?.data?.message||"Failed to fetch average interaction time");
    } finally {
      setAvgLoading(false);
    }
  }

  // Fetch peak data from /mis/peak-hours (only for Daily tab with single date)
  async function fetchPeak() {
    try {
      // Only fetch peak data if:
      // 1. Active tab is "Daily" AND
      // 2. A single date is selected (startDate === endDate)
      const isSingleDate = startDate && endDate &&
        startDate.toDateString() === endDate.toDateString();

      if (activeTab === "Daily" && isSingleDate) {
        const peak = await apiClient.get("/mis/peak-hours", getParams(1, "peak"));
        setPeakData(peak?.peak_hour?.hour_range || peak?.peak_time);
      } else {
        // Clear peak data for other cases - will be set by fetchSessions
        setPeakData(null);
      }
    } catch (err) {
      console.error(err);
      toast.error(err?.response?.data?.message || "Failed to fetch peak data");
    }
  }

  // Fetch sessions
  async function fetchSessions() {
    setSessionsLoading(true);
    try {
      const res = await apiClient.get(
        "/dashboard/sessions",
        getParams(1, "sessions")
      );
      setSessionsData(res);

      // Only set peak data from sessions if NOT (Daily AND single date)
      const isSingleDate = startDate && endDate &&
        startDate.toDateString() === endDate.toDateString();

      if (!(activeTab === "Daily" && isSingleDate)) {
        setPeakData(res?.peak_time);
      }
    } catch (err) {
      console.error(err);
      toast.error(err?.response?.data?.message||"Failed to fetch sessions data");
    } finally {
      setSessionsLoading(false);
    }
  }

  // Fetch chat status
  async function fetchChat() {
    setChatLoading(true);
    try {
      const res = await apiClient.get(
        "/dashboard/chat-status",
        getParams(1, "chat")
      );
      setChatStatusData(res);
    } catch (err) {
      console.error(err);
      toast.error(err?.response?.data?.message||"Failed to fetch chat status data");
    } finally {
      setChatLoading(false);
    }
  }

  const openChatStatusModal = async () => {
    try {
      setChatStatusModalOpen(true);
      // If you already have chatStatusData loaded, reuse it
      if (chatStatusData) {
        setChatStatusDetails(chatStatusData);
        return;
      }
      // Otherwise, fetch fresh data
      const res = await apiClient.get("/dashboard/chat-status", getParams());
      setChatStatusDetails(res);
    } catch (err) {
      console.error(err);
      toast.error(err?.response?.data?.message||"Failed to load chat status details");
    }
  };

  const openEbillModal = async () => {
    try {
      setEbillModalOpen(true);

      // ✅ Reuse already fetched stats if available
      if (ebillStats) {
        setEbillModalData(ebillStats);
        return;
      }

      // ✅ Otherwise, fetch fresh data
      const res = await apiClient.get("/dashboard/opt-for-ebill", getParams());
      setEbillModalData(res.stats || res);
    } catch (err) {
      console.error(err);
      toast.error(err?.response?.data?.message||"Failed to load E-Bill details");
    }
  };

  // Fetch interactions (paginated)
  const fetchInteractions = async (page = 1) => {
    setInteractionsLoading(true);
    try {
      const res = await apiClient.get(
        "/mis/interactions-breakdown",
        getParams(page, "interactions")
      );
      setInteractionsData(res?.data || []);
      setTotalPages(res?.total_pages || 1);
      setCurrentPage(page);
    } catch (err) {
      console.error("Error fetching interactions:", err);
      toast.error(err?.response?.data?.message||"Failed to fetch interactions");
    } finally {
      setInteractionsLoading(false);
    }
  };

  async function fetchKPIs() {
    // Run all 4 in parallel, each with its own loading flag
    const paybillPromise = (async () => {
      setPaybillLoading(true);
      try {
        const res = await apiClient.get("/dashboard/pay-bill");
        setPayBillStats(res);
      } catch (err) {
        console.error(err);
        toast.error(err?.response?.data?.message||"Failed to fetch pay bill stats");
      } finally {
        setPaybillLoading(false);
      }
    })();

    const ebillPromise = (async () => {
      setEbillLoading(true);
      try {
        const res = await apiClient.get("/dashboard/opt-for-ebill");
        setEbillStats(res.stats);
      } catch (err) {
        console.error(err);
        toast.error(err?.response?.data?.message||"Failed to fetch e-bill stats");
      } finally {
        setEbillLoading(false);
      }
    })();

    const complaintPromise = (async () => {
      setComplaintLoading(true);
      try {
        const res = await apiClient.get("/dashboard/complaint-status");
        setComplainStats(res.stats);
        setModalComplaintData(res.data || []);
      } catch (err) {
        console.error(err);
        toast.error(err?.response?.data?.message||"Failed to fetch complaint stats");
      } finally {
        setComplaintLoading(false);
      }
    })();

    const duplicatePromise = (async () => {
      setDuplicateLoading(true);
      try {
        const res = await apiClient.get("/dashboard/download-duplicate-bill");
        setDuplicateStats(res.stats);
      } catch (err) {
        console.error(err);
        toast.error(err?.response?.data?.message||"Failed to fetch duplicate bill stats");
      } finally {
        setDuplicateLoading(false);
      }
    })();

    // Run all promises in parallel (fire-and-forget)
    await Promise.allSettled([
      paybillPromise,
      ebillPromise,
      complaintPromise,
      duplicatePromise,
    ]);
  }

  // const fetchAllData = () => {
  //   fetchInteractions(1);
  //   fetchChat();
  //   fetchSessions();
  //   fetchKPIs();
  //   fetchAvg();
  // };

  const fetchAllData = (filters = {}) => {
    // ✅ Use the most recent filter values, fallback to current state if not provided
    const {
      division: div = division,
      caNumber: ca = caNumber,
      telNo: tel = telNo,
      source: src = source,
      startDate: start = startDate,
      endDate: end = endDate,
      startHour: sHour = startHour,
      endHour: eHour = endHour,
    } = filters;

    // ✅ Helper to update params in context of this fetch
    const applyParams = (apiName = "", page = 1) => {
      const params = {};

      // Handle time-based filters
      if (activeTab === "Hourly") {
        params.last_hour = true;
      } else if (activeTab === "Daily" || activeTab === "Date") {
        params.start_date = start.toISOString().split("T")[0];
        params.end_date = end.toISOString().split("T")[0];
      } else if (activeTab === "Monthly") {
        params.month = start.toISOString().slice(0, 7);
      }

      // Filters
      if (div) params.division_name = div;
      if (ca) params.ca_number = `${ca} BRPL`;
      if (tel) params.tel_no = tel;
      if (src) params.source = src;

      // Hour filters
      if (sHour) params.start_hour = sHour;
      if (eHour) params.end_hour = eHour;

      // Pagination for interactions
      if (apiName === "interactions") {
        params.page = page;
        params.per_page = 5;
      }

      return params;
    };

    // ✅ Now call all fetches with the current, up-to-date params
    fetchInteractions(1);
    fetchChat();
    fetchSessions();
    fetchPeak(); // Fetch peak data when Daily or single date
    fetchKPIs();
    fetchAvg();
  };

  useEffect(() => {
    // ✅ Debounced auto-refresh when filters change (but no CA/tel filter active)
    const timer = setTimeout(() => {
      if (!caNumber && !telNo) {
        fetchAllData({
          division,
          caNumber,
          telNo,
          source,
          startDate,
          endDate,
          startHour,
          endHour,
        });
      }
    }, 400);

    return () => clearTimeout(timer);
  }, [activeTab, startDate, endDate, division, source]);

  // useEffect(() => {
  //   if (caNumber || telNo) return;

  //   const handler = setTimeout(() => {
  //     fetchInteractions(1);
  //     fetchChat();
  //     fetchSessions();
  //     fetchKPIs();
  //     fetchAvg();
  //   }, 600);

  //   return () => clearTimeout(handler);
  // }, [activeTab, startDate, endDate, division, source]);

  const goToPage = (page) => {
    if (page >= 1 && page <= totalPages) fetchInteractions(page);
  };
  const goToNextPage = () =>
    currentPage < totalPages && goToPage(currentPage + 1);
  const goToPrevPage = () => currentPage > 1 && goToPage(currentPage - 1);

  const openModal = (title) => {
    setModalTitle(title);
    setModalOpen(true);
  };

  const closeModal = () => {
    setModalOpen(false);
    setModalTitle("");
  };

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-semibold">Dashboard</h2>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-6">
        {complaintLoading ? (
          <Loader text="Loading Complaints..." />
        ) : (
          <StatsCard
            icon={<Zap />}
            label="No Supply Complaint Registered (Both)"
            value={complaint?.total_complaints || 0}
            color="bg-red-100 text-red-600"
            onClick={() => openModal("No Supply Complaint Registered")}
          />
        )}

        {complaintLoading ? (
          <Loader text="Loading Complaints..." />
        ) : (
          <StatsCard
            icon={<CheckCircle2 />}
            label="Complaints Resolved (Both)"
            value={complaint?.resolved_complaints || 0}
            color="bg-green-100 text-green-600"
            onClick={() => openModal("No Supply Complaint Registered")}
          />
        )}

        {paybillLoading ? (
          <Loader text="Loading Payments..." />
        ) : (
          <StatsCard
            icon={<Wallet />}
            label="Payment Initiation Menu Selection (Both)"
            value={payBillStats?.stats?.pay_bill_count || 0}
            color="bg-yellow-100 text-yellow-600"
          />
        )}

        {ebillLoading ? (
          <Loader text="Loading e-Bills..." />
        ) : (
          <div
            onClick={openEbillModal}
            className="cursor-pointer hover:opacity-90 transition"
          >
            <StatsCard
              icon={<FileText />}
              label="Opted for E-Bill (Both)"
              value={
                ebillStats
                  ? `${ebillStats.opt_for_ebill_completed || 0} / ${
                      ebillStats.unique_users_clicked_ebill || 0
                    }`
                  : "0 / 0"
              }
              color="bg-blue-100 text-blue-600"
            />
          </div>
        )}

        {duplicateLoading ? (
          <Loader text="Loading Duplicate Bill..." />
        ) : (
          <StatsCard
            icon={<Wallet />}
            label="Duplicate Bill Requested (Both)"
            value={DuplicateStats?.duplicate_bill_download || 0}
            color="bg-red-800 text-yellow-600"
          />
        )}
      </div>

      {/* Interactions Header */}
      <InteractionsHeader
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        startDate={startDate}
        setStartDate={setStartDate}
        endDate={endDate}
        setEndDate={setEndDate}
        isDatePickerOpen={isDatePickerOpen}
        setIsDatePickerOpen={setIsDatePickerOpen}
        sessionsData={sessionsData}
        avgTimeData={avgTimeData}
        chatStatusData={chatStatusData}
        formatDate={formatDate}
        peakData={peakData}
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
        openChatStatusModal={openChatStatusModal}
      />

      {activeTab === "Monthly" &&
        (sessionsLoading || avgLoading || chatLoading ? (
          <Loader text="Loading Metrics..." />
        ) : (
          <ChatMetricsChart
            sessionsData={sessionsData}
            avgTimeData={avgTimeData}
            chatStatusData={chatStatusData}
          />
        ))}

      {/* Interactions */}
      <div className="h-[500px] overflow-y-auto space-y-6 border border-gray-200 p-2 rounded">
        {interactionsLoading ? (
          <Loader text="Loading Interactions..." />
        ) : interactionsData.length === 0 ? (
          <p className="text-gray-500 text-center py-10">No data found</p>
        ) : (
          interactionsData.map((item, idx) => (
            <InteractionRow key={idx} item={item} setModalData={setModalData} />
          ))
        )}
      </div>

      {/* Pagination Controls */}
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

      {/* Full Log Modal */}
      <InteractionMisModal
        modalData={modalData}
        onClose={() => setModalData(null)}
      />

      {/* Modal */}
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
              <List className="text-indigo-500" size={18} />
              <h2 className="text-lg font-semibold text-gray-800">
                {modalTitle}
              </h2>
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
                            <span className="font-semibold text-gray-800">
                              CA Number:
                            </span>{" "}
                            {user.ca_number || "—"}
                          </div>

                          <div>
                            <span className="font-semibold text-gray-800">
                              Tel No:
                            </span>{" "}
                            {user.tel_no || "—"}
                          </div>

                          <div>
                            <span className="font-semibold text-gray-800">
                              Source:
                            </span>{" "}
                            {user.source || "—"}
                          </div>

                          <div>
                            <span className="font-semibold text-gray-800">
                              Division:
                            </span>{" "}
                            {user.division_name || "—"}
                          </div>

                          {/* Nested complaints */}
                          <div className="mt-1">
                            <span className="font-semibold text-gray-800">
                              Complaints:
                            </span>
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
      {chatStatusModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-white rounded-xl shadow-lg w-full max-w-md p-6 relative">
            <button
              onClick={() => setChatStatusModalOpen(false)}
              className="absolute top-3 right-3 text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>

            <div className="flex items-center gap-2 mb-4">
              <CheckCircle2 className="text-green-500" size={18} />
              <h2 className="text-lg font-semibold text-gray-800">
                Chat Completion Details
              </h2>
            </div>

            {chatStatusDetails ? (
              <div className="space-y-2 text-sm text-gray-700">
                <div className="flex justify-between border-b pb-1 text-green-700">
                  <span className="font-medium">Completed Chats</span>
                  <span>{chatStatusDetails.completed_chats || 0}</span>
                </div>
                <div className="flex justify-between border-b pb-1 text-red-600">
                  <span className="font-medium">Left Chats</span>
                  <span>{chatStatusDetails.left_chats || 0}</span>
                </div>
                <div className="flex justify-between border-b pb-1">
                  <span className="font-medium">Total Sessions</span>
                  <span>{chatStatusDetails.total_sessions || 0}</span>
                </div>
              </div>
            ) : (
              <p className="text-gray-400 italic text-sm">No data found.</p>
            )}
          </div>
        </div>
      )}

      {ebillModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-white rounded-xl shadow-lg w-full max-w-md p-6 relative">
            <button
              onClick={() => setEbillModalOpen(false)}
              className="absolute top-3 right-3 text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>

            <div className="flex items-center gap-2 mb-4">
              <FileText className="text-blue-500" size={18} />
              <h2 className="text-lg font-semibold text-gray-800">
                E-Bill Conversion Details
              </h2>
            </div>

            {ebillModalData ? (
              <div className="space-y-2 text-sm text-gray-700">
                <div className="flex justify-between border-b pb-1">
                  <span className="font-medium">Conversion Rate</span>
                  <span>{ebillModalData.conversion_rate ?? "—"}%</span>
                </div>

                <div className="flex justify-between border-b pb-1 text-green-700">
                  <span className="font-medium">E-Bill Completed</span>
                  <span>{ebillModalData.opt_for_ebill_completed || 0}</span>
                </div>

                <div className="flex justify-between border-b pb-1 text-blue-700">
                  <span className="font-medium">Unique Users Clicked</span>
                  <span>{ebillModalData.unique_users_clicked_ebill || 0}</span>
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
