// import DatePicker from "react-datepicker";
// import "react-datepicker/dist/react-datepicker.css";



// export default function InteractionsHeader({
//   activeTab,
//   setActiveTab,
//   selectedDate,
//   setSelectedDate,
//   isDatePickerOpen,
//   setIsDatePickerOpen,
// }) {
//   return (
//     <div className="w-full">
//       <div className="flex flex-wrap justify-between items-center mb-3 gap-3">
//         {/* Left: Title + Date Picker */}
//         <div className="flex items-center gap-2 relative">
//           <h2 className="text-lg font-semibold">Chat Interactions</h2>

//           <button
//             onClick={() => setIsDatePickerOpen(!isDatePickerOpen)}
//             className="border border-gray-300 rounded-md px-2 py-1 text-sm bg-white"
//           >
//             {selectedDate
//               ? new Date(selectedDate).toLocaleDateString("en-GB")
//               : "Select Date"}
//           </button>

//           {isDatePickerOpen && (
//             <div className="absolute top-10 z-50">
//               <DatePicker
//                 selected={selectedDate}
//                 maxDate={new Date()}
//                 onChange={(date) => {
//                   setSelectedDate(date);
//                   setActiveTab("Date");
//                   setIsDatePickerOpen(false);
//                 }}
//                 inline
//               />
//             </div>
//           )}
//         </div>

//         {/* Right: Tabs */}
//         <div className="flex gap-2">
//           {["Hourly", "Daily", "Monthly"].map((tab) => (
//             <button
//               key={tab}
//               onClick={() => {
//                 if (tab === "Daily") setSelectedDate(new Date());
//                 setActiveTab(tab);
//               }}
//               className={`px-4 py-1 rounded-md text-sm font-medium ${
//                 activeTab === tab
//                   ? "bg-red-500 text-white"
//                   : "border border-red-400 text-red-500"
//               }`}
//             >
//               {tab}
//             </button>
//           ))}
//         </div>
//       </div>
//     </div>
//   );
// }


import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";

export default function DateInteractions({
  activeTab,
  setActiveTab,
  startDate,
  setStartDate,
  endDate,
  setEndDate,
  isDatePickerOpen,
  setIsDatePickerOpen,
}) {
  return (
    <div className="w-full">
      <div className="flex flex-wrap justify-between items-center mb-3 gap-3">
        {/* Left: Title + Date Picker */}
        <div className="flex items-center gap-2 relative">
          <h2 className="text-lg font-semibold">API Keys Breakdown</h2>

          <button
            onClick={() => setIsDatePickerOpen(!isDatePickerOpen)}
            className="border border-gray-300 rounded-md px-2 py-1 text-sm bg-white"
          >
            {startDate && endDate
              ? `${new Date(startDate).toLocaleDateString("en-GB")} → ${new Date(
                  endDate
                ).toLocaleDateString("en-GB")}`
              : "Select Date Range"}
          </button>

          {isDatePickerOpen && (
            <div className="absolute top-10 z-50 bg-white shadow-lg p-3 rounded-lg">
              <div className="flex gap-4">
                <div>
                  <p className="text-xs font-medium mb-1 text-gray-600">Start Date</p>
                  <DatePicker
                    selected={startDate}
                    onChange={(date) => setStartDate(date)}
                    selectsStart
                    startDate={startDate}
                    endDate={endDate}
                    maxDate={new Date()}
                    inline
                  />
                </div>
                <div>
                  <p className="text-xs font-medium mb-1 text-gray-600">End Date</p>
                  <DatePicker
                    selected={endDate}
                    onChange={(date) => setEndDate(date)}
                    selectsEnd
                    startDate={startDate}
                    endDate={endDate}
                    minDate={startDate}
                    maxDate={new Date()}
                    inline
                  />
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Right: Tabs */}
        <div className="flex gap-2">
          {["Hourly", "Daily", "Monthly"].map((tab) => (
            <button
              key={tab}
              onClick={() => {
                if (tab === "Daily") {
                  setStartDate(new Date());
                  setEndDate(new Date());
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
      </div>
    </div>
  );
}


