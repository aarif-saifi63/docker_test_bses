import { useState, useEffect } from "react";
import * as XLSX from "xlsx";
import { saveAs } from "file-saver";
import { toast } from "sonner";
import InteractionsHeader from "../components/Mis/InteractionsHeader";
import InteractionLogModal from "../components/Common/InteractionLogModal";
import MultiLogEntryRow from "../components/Menu/MultiLogEntryRow";
import Loader from "../components/Common/Loader";
import apiClient from "../services/apiClient";
import Select from "react-select";

// const MENU_OPTIONS = [
//   "New Connection Application",
//   "New Connection Status",
//   "Virtual Customer Care Centre (BYPL) / Connect Virtually",
//   "Streetlight Complaint",
//   "FAQs",
//   "Branches Nearby",
//   "Visually Impaired",
//   "Select Another CA number",
//   "Change Language",
//   "Meter Reading Schedule",
//   "Prepaid Meter - Check Balance / Recharge",
//   "Consumption History",
//   "Duplicate Bill",
//   "Payment Status",
//   "Payment History",
//   "Opt for e-bill",
//   "Register Complaint",
//   "Complaint Status (NCC)",
// ];

export default function Menu() {
  const [activeTab, setActiveTab] = useState("Daily");
  // const [selectedDate, setSelectedDate] = useState(new Date());
  const [startDate, setStartDate] = useState(new Date());
  const [endDate, setEndDate] = useState(new Date());
  const [isDatePickerOpen, setIsDatePickerOpen] = useState(false);
  const [division, setDivision] = useState("");
  const [menuOption, setMenuOption] = useState("Meter Reading Schedule");
  const [menuData, setMenuData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [modalData, setModalData] = useState(null);
  const [caNumber, setCaNumber] = useState("");
  const [telNo, setTelNo] = useState("");
  const [source, setSource] = useState("");
  const [submenuOptions, setSubmenuOptions] = useState([]);
  const [selectedSubmenus, setSelectedSubmenus] = useState([]);

  const formatDate = (date) => date.toISOString().split("T")[0];

  // const getParams = () => {
  //   let params = {
  //     menu_option: `${menuOption} BRPL`,
  //     division_name: division,
  //     ca_number: caNumber,
  //     tel_no: telNo,
  //     source: source,
  //     page,
  //     per_page: 5,
  //   };

  //   if (activeTab === "Hourly") {
  //     params.last_hour = true;
  //   } else if (activeTab === "Daily" || activeTab === "Date") {
  //     params.date = formatDate(selectedDate);
  //   } else if (activeTab === "Monthly") {
  //     params.month = `${selectedDate.getFullYear()}-${String(selectedDate.getMonth() + 1).padStart(
  //       2,
  //       "0"
  //     )}`;
  //   }

  //   return params;
  // };

  // Fetch API

  // const getParams = () => {
  //   const formatDate = (date) => date?.toISOString().split("T")[0];
  //   const formatMonth = (date) => date?.toISOString().slice(0, 7);

  //   // Ensure valid dates or fallback to today
  //   const today = new Date();
  //   const safeStart = startDate || today;
  //   const safeEnd = endDate || today;

  //   // Base params
  //   let params = {
  //     menu_option: `${menuOption} BRPL`,
  //     division_name: division || "",
  //     ca_number: caNumber ? `${caNumber} BRPL` : "",

  //     tel_no: telNo || "",
  //     source: source || "",
  //     page,
  //     per_page: 5,
  //   };

  //   // Add time filters based on tab
  //   if (activeTab === "Hourly") {
  //     params.last_hour = true;
  //   } else if (activeTab === "Daily" || activeTab === "Date") {
  //     params.start_date = formatDate(safeStart);
  //     params.end_date = formatDate(safeEnd);
  //   } else if (activeTab === "Monthly") {
  //     params.month = formatMonth(safeStart);
  //   }

  //   return params;
  // };

  const getParams = () => {
    // ✅ Fix: format local date without UTC shift
    const formatLocalDate = (date) => {
      if (!date) return null;
      const d = new Date(date.getTime() - date.getTimezoneOffset() * 60000);
      return d.toISOString().split("T")[0];
    };

    const formatLocalMonth = (date) => formatLocalDate(date).slice(0, 7);

    // Ensure valid dates or fallback to today
    const today = new Date();
    const safeStart = startDate || today;
    const safeEnd = endDate || today;

    // Base params
    let params = {
      menu_option: `${menuOption} BRPL`,
      division_name: division || "",
      ca_number: caNumber ? `${caNumber} BRPL` : "",
      tel_no: telNo || "",
      source: source || "",
      page,
      per_page: 5,
    };

    // 🔹 Add time filters
    if (activeTab === "Hourly") {
      params.last_hour = true;
    } else if (activeTab === "Daily" || activeTab === "Date") {
      params.start_date = formatLocalDate(safeStart);
      params.end_date = formatLocalDate(safeEnd);
    } else if (activeTab === "Monthly") {
      params.month = formatLocalMonth(safeStart);
    }

    return params;
  };

 
  const fetchSubmenus = async () => {
      try {
        const res = await apiClient.get("/submenus");
        const data = res.data || [];
        const sorted = data
          .filter((s) => s.is_visible !== false)
          .sort((a, b) => {
            if (a.lang === "en" && b.lang !== "en") return -1;
            if (a.lang !== "en" && b.lang === "en") return 1;
            return 0;
          });
        setSubmenuOptions(
          sorted.map((submenu) => ({
            value: submenu.name,
            label: submenu.name,
            id: submenu.id,
          }))
        );
      } catch (err) {
        toast.error(err?.response?.data?.message || "Failed to fetch submenus");
      }
    };


  const fetchMenuData = async () => {
    setLoading(true);
    try {
      const params = getParams();
      const res = await apiClient.get("/menu/menu-analysis", params);
      setMenuData(res?.data || []);
      setTotalPages(res?.total_pages || 1);
    } catch (err) {
      console.error("Menu API error:", err);
      toast.error(err?.response?.data?.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchAllData = () => {
    fetchMenuData();
  };

  useEffect(() => {
    // Skip auto-fetch if CA number or Tel no is being used
    if (caNumber || telNo) return;

    const handler = setTimeout(() => {
      fetchAllData();
    }, 600);

    return () => clearTimeout(handler);
  }, [activeTab, startDate, endDate, division, menuOption, page, source]);

  useEffect(() => {
    fetchSubmenus();
  }, []);

  // useEffect(() => {
  //   const handler = setTimeout(() => {
  //     fetchMenuData();
  //   }, 600); // ⏱️ 600ms debounce time

  //   // Cleanup: clear timeout if user keeps typing/changing filters
  //   return () => clearTimeout(handler);
  //   // eslint-disable-next-line
  // }, [activeTab, startDate, endDate, division, menuOption, page, caNumber, telNo, source]);

  // ✅ Export to Excel handler
  const handleExport = () => {
    if (!menuData || menuData.length === 0) return;

    let exportRows = [];

    menuData.forEach((item) => {
      exportRows.push({
        Option: item.option,
        Completed: item.completed_count,
        Incomplete: item.incomplete_count,
        Selected: item.selected_count,
        "New Users": item.user_type?.new || 0,
        "Registered Users": item.user_type?.registered || 0,
      });

      item.logs?.forEach((log) => {
        log.entries?.forEach((entry) => {
          exportRows.push({
            Session: log.session_id,
            "User Type": log.user_type,
            Query: entry.query,
            Timestamp: entry.timestamp,
            ResponseHeading: entry.answer?.response?.heading?.join(" | "),
          });
        });
      });

      // Add separator row between menu options
      exportRows.push({});
    });

    const worksheet = XLSX.utils.json_to_sheet(exportRows);
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, "Menu Analysis");

    const excelBuffer = XLSX.write(workbook, {
      bookType: "xlsx",
      type: "array",
    });
    const blob = new Blob([excelBuffer], { type: "application/octet-stream" });
    saveAs(blob, "menu_analysis.xlsx");
  };

  return (
    <div className="p-4">
      <div className="flex justify-between items-center mb-4">
        <InteractionsHeader
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
          fetchAllData={fetchAllData}
        />

        <button
          onClick={handleExport}
          className="bg-blue-600 text-white px-4 py-2 rounded shadow hover:bg-blue-700 text-sm"
        >
          Export
        </button>
      </div>

      {/* Menu Option Dropdown */}
      <div className="mb-4">
        <label className="block mb-2 text-sm font-medium text-gray-700">
          Submenus
        </label>

        <Select
          options={submenuOptions}
          value={selectedSubmenus}
          onChange={(selected) => {
            setSelectedSubmenus(selected); // ✅ store selected option object
            setMenuOption(selected?.value || ""); // ✅ store its value
            setPage(1);
          }}
          className="mt-1 text-sm"
          placeholder="Select submenu..."
        />
      </div>

      {/* Data Section */}
      {loading ? (
        <div className="flex flex-col items-center justify-center py-10">
          <Loader text="Fetching Menu Data" />
        </div>
      ) : menuData.length === 0 ? (
        <p className="text-gray-500 text-center py-6">No records found</p>
      ) : (
        menuData.map((item, idx) => (
          <div
            key={idx}
            className="border rounded-lg p-4 mb-4 shadow-sm bg-white"
          >
            {/* Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4 text-sm">
              <div className="bg-yellow-100 p-2 rounded">
                👤 User Type:{" "}
                <span className="font-semibold">
                  New: {item.user_type?.new}, Reg: {item.user_type?.registered}
                </span>
              </div>

              <div className="bg-blue-100 p-2 rounded">
                📌 Selected:{" "}
                <span className="font-semibold">{item.selected_count}</span>
              </div>

              <div className="bg-green-100 p-2 rounded">
                ✅ Completed:{" "}
                <span className="font-semibold">{item.completed_count}</span>
              </div>
              <div className="bg-red-100 p-2 rounded">
                ❌ Incomplete:{" "}
                <span className="font-semibold">{item.incomplete_count}</span>
              </div>
            </div>

            {/* Logs */}
            <div className="h-[500px] overflow-y-auto space-y-6 border border-gray-200 p-2 rounded">
              <MultiLogEntryRow item={item} setModalData={setModalData} />
            </div>
          </div>
        ))
      )}

      {/* Pagination Controls */}
      <div className="flex justify-center items-center gap-2 mt-6">
        <button
          className="px-3 py-1 border rounded bg-gray-100"
          disabled={page === 1}
          onClick={() => setPage(page - 1)}
        >
          Prev
        </button>
        <span className="font-semibold">
          {page} / {totalPages}
        </span>
        <button
          className="px-3 py-1 border rounded bg-gray-100"
          disabled={page === totalPages}
          onClick={() => setPage(page + 1)}
        >
          Next
        </button>
      </div>

      {/* Modal for Full Log */}
      {modalData && (
        <InteractionLogModal
          modalData={modalData}
          onClose={() => setModalData(null)}
        />
      )}
    </div>
  );
}
