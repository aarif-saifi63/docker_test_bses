// import React, { useState } from "react";
// import { Clock, User, Server, X, ChevronDown, ChevronUp } from "lucide-react";

// const UsageModal = ({ open, onClose, usageList }) => {
//   const [openIndex, setOpenIndex] = useState(null);

//   if (!open || !usageList || usageList.length === 0) return null;

//   const toggleEntry = (index) => {
//     setOpenIndex(openIndex === index ? null : index);
//   };

//   return (
//     <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 backdrop-blur-sm">
//       <div className="bg-white rounded-2xl shadow-2xl w-11/12 md:w-3/4 lg:w-1/2 max-h-[85vh] overflow-y-auto animate-fadeIn">
//         {/* Header */}
//         <div className="flex justify-between items-center p-4 border-b bg-blue-600 text-white rounded-t-2xl">
//           <h2 className="text-lg font-semibold">Usage Details</h2>
//           <button
//             onClick={onClose}
//             className="hover:bg-blue-700 p-1.5 rounded-full transition"
//           >
//             <X size={20} />
//           </button>
//         </div>

//         {/* Body */}
//         <div className="p-5 space-y-4 text-sm">
//           {usageList.map((hit, index) => (
//             <div
//               key={index}
//               className="border border-gray-200 rounded-xl bg-gray-50 shadow-sm hover:shadow-md transition"
//             >
//               {/* Header Bar (clickable) */}
//               <button
//                 onClick={() => toggleEntry(index)}
//                 className="w-full flex justify-between items-center px-5 py-3 text-left rounded-t-xl bg-gray-100 hover:bg-gray-200 transition"
//               >
//                 <div className="flex flex-col md:flex-row md:items-center md:gap-3">
//                   <h3 className="font-semibold text-gray-700 flex items-center gap-2">
//                     <Server size={16} /> Entry #{index + 1}
//                   </h3>
//                   <div className="flex items-center text-xs text-gray-500 gap-1">
//                     <Clock size={14} />
//                     {hit.timestamp
//                       ? new Date(hit.timestamp).toLocaleString()
//                       : "N/A"}
//                   </div>
//                 </div>
//                 {openIndex === index ? (
//                   <ChevronUp size={18} className="text-gray-600" />
//                 ) : (
//                   <ChevronDown size={18} className="text-gray-600" />
//                 )}
//               </button>

//               {/* Collapsible Content */}
//               {openIndex === index && (
//                 <div className="p-5 border-t border-gray-200 space-y-4 animate-fadeIn">
//                   {/* User Request */}
//                   <div>
//                     <h4 className="font-medium text-gray-700 mb-1 flex items-center gap-1">
//                       <User size={15} /> User Request:
//                     </h4>
//                     <pre className="bg-white border border-gray-200 rounded-md p-3 text-gray-800 overflow-x-auto whitespace-pre-wrap break-words text-[13px]">
//                       {hit.user_request || "N/A"}
//                     </pre>
//                   </div>

//                   {/* API Response */}
//                   <div>
//                     <h4 className="font-medium text-gray-700 mb-1 flex items-center gap-1">
//                       <Server size={15} /> API Response:
//                     </h4>
//                     <pre className="bg-white border border-gray-200 rounded-md p-3 text-gray-800 overflow-x-auto whitespace-pre-wrap break-words text-[13px] max-h-60">
//                       {hit.api_response || "N/A"}
//                     </pre>
//                   </div>
//                 </div>
//               )}
//             </div>
//           ))}
//         </div>

//         {/* Footer */}
//         <div className="flex justify-end bg-gray-50 px-6 py-3 border-t border-gray-200">
//           <button
//             onClick={onClose}
//             className="bg-blue-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-blue-700 transition"
//           >
//             Close
//           </button>
//         </div>
//       </div>
//     </div>
//   );
// };

// export default UsageModal;


// import React, { useState, useEffect } from "react";
// import { Clock, User, Server, X, ChevronDown, ChevronUp } from "lucide-react";

// const UsageModal = ({ open, onClose, usageList }) => {
//   const [openIndex, setOpenIndex] = useState(null);

//   // ✅ Reset internal state when modal opens/closes
//   useEffect(() => {
//     if (!open) setOpenIndex(null);
//   }, [open]);

//   if (!open || !usageList || usageList.length === 0) return null;

//   const toggleEntry = (index) => {
//     setOpenIndex(openIndex === index ? null : index);
//   };

//   return (
//     <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 backdrop-blur-sm">
//       <div className="bg-white rounded-2xl shadow-2xl w-11/12 md:w-3/4 lg:w-1/2 max-h-[85vh] overflow-y-auto animate-fadeIn">
//         {/* Header */}
//         <div className="flex justify-between items-center p-4 border-b bg-blue-600 text-white rounded-t-2xl">
//           <h2 className="text-lg font-semibold">Usage Details</h2>
//           <button
//             onClick={onClose}
//             className="hover:bg-blue-700 p-1.5 rounded-full transition"
//           >
//             <X size={20} />
//           </button>
//         </div>

//         {/* Body */}
//         <div className="p-5 space-y-4 text-sm">
//           {usageList.map((hit, index) => (
//             <div
//               key={index}
//               className="border border-gray-200 rounded-xl bg-gray-50 shadow-sm hover:shadow-md transition"
//             >
//               {/* Header Bar (clickable) */}
//               <button
//                 onClick={() => toggleEntry(index)}
//                 className="w-full flex justify-between items-center px-5 py-3 text-left rounded-t-xl bg-gray-100 hover:bg-gray-200 transition"
//               >
//                 <div className="flex flex-col md:flex-row md:items-center md:gap-3">
//                   <h3 className="font-semibold text-gray-700 flex items-center gap-2">
//                     <Server size={16} /> Entry #{index + 1}
//                   </h3>
//                   <div className="flex items-center text-xs text-gray-500 gap-1">
//                     <Clock size={14} />
//                     {hit.timestamp
//                       ? new Date(hit.timestamp).toLocaleString()
//                       : "N/A"}
//                   </div>
//                 </div>
//                 {openIndex === index ? (
//                   <ChevronUp size={18} className="text-gray-600" />
//                 ) : (
//                   <ChevronDown size={18} className="text-gray-600" />
//                 )}
//               </button>

//               {/* Collapsible Content */}
//               {openIndex === index && (
//                 <div className="p-5 border-t border-gray-200 space-y-4 animate-fadeIn">
//                   {/* Inline Data Layout */}
//                   <div className="bg-white border border-gray-200 rounded-md p-3 text-gray-800 text-[13px] space-y-2">
//                     <div className="flex flex-col gap-1">
//                       <div className="flex justify-between border-b pb-1">
//                         <span className="font-medium text-gray-700">App Name:</span>
//                         <span>{extractField(hit.user_request, "_sAppName")}</span>
//                       </div>
//                       <div className="flex justify-between border-b pb-1">
//                         <span className="font-medium text-gray-700">Company Code:</span>
//                         <span>{extractField(hit.user_request, "_sCompanyCode")}</span>
//                       </div>
//                       <div className="flex justify-between border-b pb-1">
//                         <span className="font-medium text-gray-700">Vendor Code:</span>
//                         <span>{extractField(hit.user_request, "_sVendorCode")}</span>
//                       </div>
//                       <div className="flex justify-between border-b pb-1">
//                         <span className="font-medium text-gray-700">Mobile No:</span>
//                         <span>{extractField(hit.user_request, "_MobileNo")}</span>
//                       </div>
//                       <div className="flex justify-between border-b pb-1">
//                         <span className="font-medium text-gray-700">OTP Message:</span>
//                         <span>{extractField(hit.user_request, "_sOTPMsg")}</span>
//                       </div>
//                       <div className="flex justify-between border-b pb-1">
//                         <span className="font-medium text-gray-700">Flag:</span>
//                         <span>{extractField(hit.api_response, "FLAG")}</span>
//                       </div>
//                       <div className="flex justify-between">
//                         <span className="font-medium text-gray-700">Output:</span>
//                         <span>{extractField(hit.api_response, "OUT_PUT")}</span>
//                       </div>
//                     </div>
//                   </div>

//                   {/* Expandable Raw Data */}
//                   <details className="mt-3">
//                     <summary className="cursor-pointer font-medium text-blue-600 hover:underline">
//                       View Full Raw Request/Response
//                     </summary>
//                     <div className="mt-2 space-y-3">
//                       <div>
//                         <h4 className="font-medium text-gray-700 mb-1 flex items-center gap-1">
//                           <User size={15} /> User Request:
//                         </h4>
//                         <pre className="bg-white border border-gray-200 rounded-md p-3 overflow-x-auto whitespace-pre-wrap break-words text-[12px]">
//                           {hit.user_request || "N/A"}
//                         </pre>
//                       </div>

//                       <div>
//                         <h4 className="font-medium text-gray-700 mb-1 flex items-center gap-1">
//                           <Server size={15} /> API Response:
//                         </h4>
//                         <pre className="bg-white border border-gray-200 rounded-md p-3 overflow-x-auto whitespace-pre-wrap break-words text-[12px] max-h-60">
//                           {hit.api_response || "N/A"}
//                         </pre>
//                       </div>
//                     </div>
//                   </details>
//                 </div>
//               )}
//             </div>
//           ))}
//         </div>

//         {/* Footer */}
//         <div className="flex justify-end bg-gray-50 px-6 py-3 border-t border-gray-200">
//           <button
//             onClick={onClose}
//             className="bg-blue-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-blue-700 transition"
//           >
//             Close
//           </button>
//         </div>
//       </div>
//     </div>
//   );
// };

// /**
//  * ✅ Helper to extract XML field values
//  */
// function extractField(xmlString, fieldName) {
//   if (!xmlString) return "—";
//   const regex = new RegExp(`<${fieldName}>(.*?)</${fieldName}>`, "i");
//   const match = xmlString.match(regex);
//   return match ? match[1] : "—";
// }

// export default UsageModal;


import React, { useState, useEffect } from "react";
import { Clock, User, Server, X, ChevronDown, ChevronUp } from "lucide-react";

const UsageModal = ({ open, onClose, usageList }) => {
  const [openIndex, setOpenIndex] = useState(null);

  // Reset open state when modal closes
  useEffect(() => {
    if (!open) setOpenIndex(null);
  }, [open]);

  if (!open || !usageList || usageList.length === 0) return null;

  const toggleEntry = (index) => {
    setOpenIndex(openIndex === index ? null : index);
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 backdrop-blur-sm">
      <div className="bg-white rounded-2xl shadow-2xl w-11/12 md:w-3/4 lg:w-1/2 max-h-[85vh] overflow-y-auto animate-fadeIn">
        {/* Header */}
        <div className="flex justify-between items-center p-4 border-b bg-blue-600 text-white rounded-t-2xl">
          <h2 className="text-lg font-semibold">Usage Details</h2>
          <button
            onClick={onClose}
            className="hover:bg-blue-700 p-1.5 rounded-full transition"
          >
            <X size={20} />
          </button>
        </div>

        {/* Body */}
        <div className="p-5 space-y-4 text-sm">
          {usageList.map((hit, index) => (
            <div
              key={index}
              className="border border-gray-200 rounded-xl bg-gray-50 shadow-sm hover:shadow-md transition"
            >
              {/* Entry Header */}
              <button
                onClick={() => toggleEntry(index)}
                className="w-full flex justify-between items-center px-5 py-3 text-left rounded-t-xl bg-gray-100 hover:bg-gray-200 transition"
              >
                <div className="flex flex-col md:flex-row md:items-center md:gap-3">
                  <h3 className="font-semibold text-gray-700 flex items-center gap-2">
                    <Server size={16} /> Entry #{index + 1}
                  </h3>
                  <div className="flex items-center text-xs text-gray-500 gap-1">
                    <Clock size={14} />
                    {hit.timestamp
                      ? new Date(hit.timestamp).toLocaleString()
                      : "N/A"}
                  </div>
                </div>
                {openIndex === index ? (
                  <ChevronUp size={18} className="text-gray-600" />
                ) : (
                  <ChevronDown size={18} className="text-gray-600" />
                )}
              </button>

              {/* Collapsible Content */}
              {openIndex === index && (
                <div className="p-5 border-t border-gray-200 space-y-4 animate-fadeIn">
                  {/* User Request */}
                  <div>
                    <h4 className="font-medium text-gray-700 mb-1 flex items-center gap-1">
                      <User size={15} /> User Request:
                    </h4>
                    <pre className="bg-white border border-gray-200 rounded-md p-3 text-gray-800 overflow-x-auto whitespace-pre-wrap break-words text-[13px] max-h-60">
                      {hit.user_request || "N/A"}
                    </pre>
                  </div>

                  {/* API Response */}
                  <div>
                    <h4 className="font-medium text-gray-700 mb-1 flex items-center gap-1">
                      <Server size={15} /> API Response:
                    </h4>
                    <pre className="bg-white border border-gray-200 rounded-md p-3 text-gray-800 overflow-x-auto whitespace-pre-wrap break-words text-[13px] max-h-60">
                      {hit.api_response || "N/A"}
                    </pre>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Footer */}
        <div className="flex justify-end bg-gray-50 px-6 py-3 border-t border-gray-200">
          <button
            onClick={onClose}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-blue-700 transition"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default UsageModal;
