// export default function InteractionMisModal({ modalData, onClose }) {
//   if (!modalData) return null;

//   return (
//     <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
//       <div className="bg-white rounded-2xl shadow-2xl w-11/12 md:w-3/4 lg:w-1/2 max-h-[85vh] overflow-y-auto transform transition-all duration-300 scale-95 animate-fadeIn">
//         {/* Header */}
//         <div className="flex justify-between items-center border-b px-6 py-4">
//           <h3 className="text-xl font-semibold text-gray-800">
//             Full Interaction Log
//           </h3>
//           <button
//             onClick={onClose}
//             className="text-gray-500 hover:text-red-500 transition text-lg font-bold"
//           >
//             ✕
//           </button>
//         </div>

//         <div className="p-6 space-y-4">
//           {modalData.logs?.length > 0 ? (
//             modalData.logs.map((entry, idx) => (
//               <div
//                 key={idx}
//                 className="border rounded-lg bg-gray-50 shadow-sm p-4 space-y-4"
//               >
//                 {/* Header */}
//                 <div className="flex justify-between items-center text-gray-800 font-medium">
//                   <span>Interaction #{idx + 1}</span>
//                   <span className="text-xs text-gray-500 break-all">
//                     User ID: {entry.user_id || "—"}
//                   </span>
//                   <span className="text-xs text-gray-500">
//                     {entry.timestamp
//                       ? new Date(entry.timestamp).toLocaleString()
//                       : "Unknown time"}
//                   </span>
//                 </div>

//                 {/* User */}
//                 <div className="bg-blue-50 p-3 rounded-lg shadow-inner">
//                   <p className="font-semibold text-blue-600">User:</p>
//                   <p className="mt-1 break-words">{entry.query || "—"}</p>
//                 </div>

//                 {/* System */}
//                 {/* <div className="bg-green-50 p-3 rounded-lg shadow-inner">
//                   <p className="font-semibold text-green-600">System:</p>
//                   {entry.answer?.response?.heading?.length > 0 ? (
//                     entry.answer.response.heading.map((line, lIdx) => (
//                       <p key={lIdx} className="mt-1 break-words">
//                         {line}
//                       </p>
//                     ))
//                   ) : (
//                     <p className="mt-1 text-gray-400">No response</p>
//                   )}
//                 </div> */}

//                  <div className="bg-green-50 p-3 rounded-lg shadow-inner">
//                   <p className="font-semibold text-green-600">System:</p>
//                   {entry.answer?.response?.heading?.length > 0 ? (
//                     entry.answer.response.heading.map((line, lIdx) => {
//                       const isErrorLine =
//                         line.trim() ===
//                         "Sorry, I didn’t understand that. Can you rephrase?";

//                       return (
//                         <p
//                           key={lIdx}
//                           className={`mt-1 break-words ${
//                             isErrorLine
//                               ? "bg-green text-red-700 text-xl font-semibold px-2 py-1 rounded"
//                               : ""
//                           }`}
//                         >
//                           {line}
//                         </p>
//                       );
//                     })
//                   ) : (
//                     <p className="mt-1 text-gray-400">No response</p>
//                   )}
//                 </div>

//                 {/* Buttons */}
//                 {entry.answer?.response?.buttons?.length > 0 && (
//                   <div>
//                     <p className="font-semibold text-gray-600">Buttons:</p>
//                     <div className="mt-2 flex flex-wrap gap-2">
//                       {entry.answer.response.buttons.map((btn, bIdx) => (
//                         <span
//                           key={bIdx}
//                           className="px-3 py-1 text-xs border rounded bg-white shadow-sm hover:bg-gray-100 transition"
//                         >
//                           {btn}
//                         </span>
//                       ))}
//                     </div>
//                   </div>
//                 )}

//                 {/* Main Menu */}
//                 {entry.answer?.response?.main_menu_heading && (
//                   <div>
//                     <p className="font-semibold text-gray-600">
//                       {entry.answer.response.main_menu_heading}
//                     </p>
//                     <div className="mt-2 flex flex-wrap gap-2">
//                       {entry.answer.response.main_menu_buttons?.map(
//                         (btn, bIdx) => (
//                           <span
//                             key={bIdx}
//                             className="px-2 py-1 text-xs border rounded bg-gray-100 hover:bg-gray-200 transition"
//                           >
//                             {btn}
//                           </span>
//                         )
//                       )}
//                     </div>
//                   </div>
//                 )}
//               </div>
//             ))
//           ) : (
//             <p className="text-gray-500 text-center py-6">
//               No interactions available.
//             </p>
//           )}
//         </div>

//         {/* Footer */}
//         <div className="border-t px-6 py-4 text-right">
//           <button
//             onClick={onClose}
//             className="px-5 py-2 bg-red-500 text-white rounded-lg shadow hover:bg-red-600 transition"
//           >
//             Close
//           </button>
//         </div>
//       </div>
//     </div>
//   );
// }


export default function InteractionMisModal({ modalData, onClose }) {
  if (!modalData) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-2xl shadow-2xl w-11/12 md:w-3/4 lg:w-1/2 max-h-[85vh] overflow-y-auto transform transition-all duration-300 scale-95 animate-fadeIn">
        {/* Header */}
        <div className="flex justify-between items-center border-b px-6 py-4">
          <h3 className="text-xl font-semibold text-gray-800">
            Full Interaction Log
          </h3>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-red-500 transition text-lg font-bold"
          >
            ✕
          </button>
        </div>

        <div className="p-6 space-y-4">
          {modalData.logs?.length > 0 ? (
            modalData.logs.map((entry, idx) => {
              const isFallback = entry.is_fallback === true;

              return (
                <div
                  key={idx}
                  className={`border rounded-lg shadow-sm p-4 space-y-4 transition ${
                    isFallback
                      ? "bg-red-50 border-red-300"
                      : "bg-gray-50 border-gray-200"
                  }`}
                >
                  {/* Header */}
                  <div className="flex flex-wrap justify-between items-center text-gray-800 font-medium gap-2">
                    <span>Interaction #{idx + 1}</span>
                    <span className="text-xs text-gray-500 break-all">
                      User ID: {entry.user_id || "—"}
                    </span>
                    <span className="text-xs text-gray-500">
                      {entry.timestamp
                        ? new Date(entry.timestamp).toLocaleString()
                        : "Unknown time"}
                    </span>
                  </div>

                  {/* User Query */}
                  <div className="bg-blue-50 p-3 rounded-lg shadow-inner">
                    <p className="font-semibold text-blue-600">User:</p>
                    <p className="mt-1 break-words">{entry.query || "—"}</p>
                  </div>

                  {/* System Response */}
                  <div
                    className={`p-3 rounded-lg shadow-inner ${
                      isFallback
                        ? "bg-red-100 border border-red-300"
                        : "bg-green-50"
                    }`}
                  >
                    <p
                      className={`font-semibold ${
                        isFallback ? "text-red-700" : "text-green-600"
                      }`}
                    >
                      System:
                    </p>

                    {entry.answer?.response?.heading?.length > 0 ? (
                      entry.answer.response.heading.map((line, lIdx) => (
                        <p
                          key={lIdx}
                          className={`mt-1 break-words whitespace-pre-wrap ${
                            isFallback
                              ? "text-red-700 font-semibold"
                              : "text-gray-800"
                          }`}
                        >
                          {line}
                        </p>
                      ))
                    ) : (
                      <p className="mt-1 text-gray-400">No response</p>
                    )}
                  </div>

                  {/* Buttons */}
                  {entry.answer?.response?.buttons?.length > 0 && (
                    <div>
                      <p className="font-semibold text-gray-600">Buttons:</p>
                      <div className="mt-2 flex flex-wrap gap-2">
                        {entry.answer.response.buttons.map((btn, bIdx) => (
                          <span
                            key={bIdx}
                            className="px-3 py-1 text-xs border rounded bg-white shadow-sm hover:bg-gray-100 transition"
                          >
                            {btn}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Main Menu */}
                  {entry.answer?.response?.main_menu_heading && (
                    <div>
                      <p className="font-semibold text-gray-600">
                        {entry.answer.response.main_menu_heading}
                      </p>
                      <div className="mt-2 flex flex-wrap gap-2">
                        {entry.answer.response.main_menu_buttons?.map(
                          (btn, bIdx) => (
                            <span
                              key={bIdx}
                              className="px-2 py-1 text-xs border rounded bg-gray-100 hover:bg-gray-200 transition"
                            >
                              {btn}
                            </span>
                          )
                        )}
                      </div>
                    </div>
                  )}
                </div>
              );
            })
          ) : (
            <p className="text-gray-500 text-center py-6">
              No interactions available.
            </p>
          )}
        </div>

        {/* Footer */}
        <div className="border-t px-6 py-4 text-right">
          <button
            onClick={onClose}
            className="px-5 py-2 bg-red-500 text-white rounded-lg shadow hover:bg-red-600 transition"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
