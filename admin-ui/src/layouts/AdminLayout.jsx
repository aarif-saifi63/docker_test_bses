// import { Outlet, useLocation } from "react-router-dom";
// import Sidebar from "../components/UI/Sidebar.jsx";
// import Header from "../components/UI/Header.jsx";

// export default function AdminLayout() {
//   const location = useLocation();
//   const titleMap = {
//     "/": "Dashboard",
//     "/menu": "Menu",
//     "/feedback": "Feedback",
//     "/advertisement": "Advertisement",
//     "/api-keys": "API Keys",
//     "/helper": "Helper",
//   };
//   const currentTitle = titleMap[location.pathname] || "Dashboard";
//   return (
//     <div className="flex h-screen bg-gray-100">
//       <Sidebar />
//       <div className="flex flex-col flex-1 min-w-0">
//         <Header title={currentTitle} />
//         <main className="flex-1 p-6 overflow-y-auto">
//           <Outlet />
//         </main>
//       </div>
//     </div>
//   );
// }

import { Outlet, useLocation } from "react-router-dom";
import Sidebar from "../components/UI/Sidebar.jsx";
import Header from "../components/UI/Header.jsx";

export default function AdminLayout() {
  const location = useLocation();

  const titleMap = {
    "/": "Dashboard",
    "/menu": "Menu",
    "/feedback": "Feedback",
    "/advertisement": "Advertisement",
    "/api-keys": "API Keys",
    "/helper": "Helper",
  };

  const currentTitle = titleMap[location.pathname] || "Dashboard";

  return (
    <div className="flex h-screen bg-gray-100">
      <Sidebar />
      <div className="flex flex-col flex-1 min-w-0">
        <Header title={currentTitle} />
        <main className="flex-1 p-6 overflow-y-auto relative">
          <Outlet />

          {/* Floating chatbot visible everywhere */}
          {/* <div className="fixed bottom-4 right-4 z-50 w-[400px] max-h-[80vh] overflow-hidden rounded-2xl shadow-xl bg-white border border-gray-200"> */}
          {/* </div> */}
        </main>
      </div>
    </div>
  );
}
