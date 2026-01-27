import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";
import apiClient from "../../services/apiClient";
import { useState, useEffect } from "react";

export default function InteractionsHeader({
  title = "Menu Analysis",
  activeTab,
  setActiveTab,

  startDate,
  setStartDate,
  endDate,
  setEndDate,
  isDatePickerOpen,
  setIsDatePickerOpen,
  // formatDate,
  division,
  setDivision,
  caNumber,
  setCaNumber,
  telNo,
  setTelNo,
  source,
  setSource,
  startHour,
  setStartHour,
  endHour,
  setEndHour,
  fetchAllData = { fetchAllData },
}) {
  const [divisions, setDivisions] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchDivisions = async () => {
      setLoading(true);
      try {
        const res = await apiClient.get("/divisions");

        const data = res?.data?.data || res?.data || [];
        setDivisions(Array.isArray(data) ? data : []);
      } catch (err) {
        console.error("Failed to fetch divisions:", err);
        setDivisions([]);
      } finally {
        setLoading(false);
      }
    };

    fetchDivisions();
  }, [source]);

  return (
    <div>
      <div className="flex flex-wrap justify-between items-center mb-3 gap-3">
        {/* ===== Left Section (Title + Date) ===== */}
        <div className="flex items-center gap-2 relative">
          <h2 className="text-lg font-semibold mr-8">{title}</h2>

          <button
            onClick={() => setIsDatePickerOpen(!isDatePickerOpen)}
            className="border border-gray-300 rounded-md px-2 py-1 text-sm bg-white"
          >
            {startDate && endDate
              ? `${startDate.toLocaleDateString(
                  "en-GB"
                )} - ${endDate.toLocaleDateString("en-GB")}`
              : "Select Range"}
          </button>

          {isDatePickerOpen && (
            <div className="absolute top-10 z-50">
              <DatePicker
                selectsRange
                startDate={startDate}
                endDate={endDate}
                maxDate={new Date()}
                onChange={([start, end]) => {
                  setStartDate(start);
                  setEndDate(end);
                  if (end) {
                    setActiveTab("Date");
                    setIsDatePickerOpen(false);
                  }
                }}
                inline
              />
            </div>
          )}
        </div>

        {/* ===== Tabs (unchanged) ===== */}
        <div className="flex gap-2">
          {["Hourly", "Daily", "Monthly"].map((tab) => (
            <button
              key={tab}
              onClick={() => {
                if (tab === "Daily") {
                  const today = new Date();
                  setStartDate(today);
                  setEndDate(today);
                }
                setActiveTab(tab);
              }}
              className={`px-4 py-1 rounded-md text-sm font-medium ${
                activeTab === tab
                  ? "bg-red-500 text-white"
                  : "border border-red-400 text-red-500"
              }`}
            >
              {tab}
            </button>
          ))}
        </div>

        {/* ===== Right Section (Division + CA Number + Telephone) ===== */}
        <div className="flex gap-3 items-center flex-wrap">
          {/* ✅ Division Dropdown */}
          <select
            value={division}
            onChange={(e) => setDivision(e.target.value)}
            className="border border-gray-300 rounded-md px-3 py-1 text-sm bg-white"
          >
            <option value="">-- Select Division --</option>

            {loading ? (
              <option disabled>Loading...</option>
            ) : divisions.length > 0 ? (
              divisions.map((d) => (
                <option key={d.id} value={d.division_name}>
                  {d.division_name}
                </option>
              ))
            ) : (
              <option disabled>No divisions found</option>
            )}
          </select>

          {/* CA Number Input */}
          <input
            type="text"
            value={caNumber}
            onChange={(e) => {
              const value = e.target.value;
              if (value === "" || (/^\d+$/.test(value) && value.length <= 9)) {
                setCaNumber(value);
              }
            }}
            placeholder="CA Number"
            className="border border-gray-300 rounded-md px-3 py-1 text-sm bg-white w-32"
          />

          {/* Telephone Number Input */}
          <input
            type="text"
            value={telNo}
            onChange={(e) => {
              const value = e.target.value;
              if (value === "" || (/^\d+$/.test(value) && value.length <= 10)) {
                setTelNo(value);
              }
            }}
            placeholder="Tel. No."
            className="border border-gray-300 rounded-md px-3 py-1 text-sm bg-white w-32"
          />

          {/* Source */}
          <select
            onChange={(e) => setSource(e.target.value)}
            value={source}
            className="border border-gray-300 rounded-md px-3 py-1 text-sm bg-white w-32"
          >
            <option value="">-- Select Source --</option>
            <option value="web">Website</option>
            <option value="app">Mobile App</option>
          </select>

          {/* Start Hour - Only show if props are provided */}
          {setStartHour && (
            <select
              onChange={(e) => setStartHour(e.target.value)}
              value={startHour}
              className="border border-gray-300 rounded-md px-3 py-1 text-sm bg-white w-32"
            >
              <option value="">Start Hour</option>
              {Array.from({ length: 24 }, (_, i) => (
                <option key={i} value={i}>
                  {String(i).padStart(2, '0')}:00
                </option>
              ))}
            </select>
          )}

          {/* End Hour - Only show if props are provided */}
          {setEndHour && (
            <select
              onChange={(e) => setEndHour(e.target.value)}
              value={endHour}
              className="border border-gray-300 rounded-md px-3 py-1 text-sm bg-white w-32"
            >
              <option value="">End Hour</option>
              {Array.from({ length: 24 }, (_, i) => (
                <option key={i} value={i}>
                  {String(i).padStart(2, '0')}:00
                </option>
              ))}
            </select>
          )}

          <button
            onClick={() => {
              fetchAllData();
            }}
            className="bg-blue-600 text-white px-4 py-1 rounded-md text-sm hover:bg-blue-700"
          >
            Apply Filters
          </button>
        </div>
      </div>
    </div>
  );
}
