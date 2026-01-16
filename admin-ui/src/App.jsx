import { createBrowserRouter, RouterProvider } from "react-router-dom";
import AdminLayout from "./layouts/AdminLayout.jsx";
import Login from "./pages/Login.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import MISDashboard from "./pages/MISDashboard.jsx";
import Feedback from "./pages/Feedback.jsx";
import Advertisement from "./pages/Advertisement.jsx";
import ApiKeys from "./pages/ApiKeys.jsx";
import Menu from "./pages/Menu.jsx";
import Poll from "./pages/PollsPage.jsx";
import ProtectedRoute from "./components/Auth/ProtectedRoute.jsx";
import { AuthProvider } from "./context/AuthContext";
import MenuManagementPage from "./pages/MenuManagementPage.jsx";
import SubsidiaryMaster from "./pages/SubsidiaryMaster.jsx";
import IntentFlow from "./components/Intent/IntentFlow.jsx";
import RolesPage from "./pages/user-management/RolesPage.jsx";
import AnalyticsPage from "./pages/AnalyticsPage.jsx";
import UserPage from "./pages/user-management/UsersPage.jsx";
import NotAuthorized from "./pages/NotAuthorized.jsx";
import NotFound from "./pages/NotFound.jsx";
import { Toaster } from "sonner";
import LanguageManagement from "./pages/LanguageManagement.jsx";
import UtterMessagesPage from "./pages/UtterMessagesPage.jsx";
import FallbackManagementPage from "./pages/FallbackManagementPage.jsx";

const router = createBrowserRouter(
  [
    { path: "/login", element: <Login /> },
    { path: "/not-authorized", element: <NotAuthorized /> },

    {
      path: "/",
      element: (
        <ProtectedRoute>
          <AdminLayout />
        </ProtectedRoute>
      ),
      children: [
        { index: true, element: <Dashboard /> },
        { path: "dashboard", element: <Dashboard /> },

        {
          path: "advertisement",
          element: (
            <ProtectedRoute requiredPermissions={["advertisement-read"]}>
              <Advertisement />
            </ProtectedRoute>
          ),
        },
        {
          path: "feedbacks",
          element: (
            <ProtectedRoute requiredPermissions={["feedbacks-read"]}>
              <Feedback />
            </ProtectedRoute>
          ),
        },
        {
          path: "polls",
          element: (
            <ProtectedRoute requiredPermissions={["polls-read"]}>
              <Poll />
            </ProtectedRoute>
          ),
        },
        {
          path: "api-key",
          element: (
            <ProtectedRoute requiredPermissions={["api-key-read"]}>
              <ApiKeys />
            </ProtectedRoute>
          ),
        },
        {
          path: "chatbot-menus",
          element: (
            <ProtectedRoute requiredPermissions={["chatbot-menu-read"]}>
              <Menu />
            </ProtectedRoute>
          ),
        },
        {
          path: "menus",
          element: (
            <ProtectedRoute requiredPermissions={["menus-read"]}>
              <MenuManagementPage />
            </ProtectedRoute>
          ),
        },
        {
          path: "subsidiary-master",
          element: (
            <ProtectedRoute requiredPermissions={["subsidiary-master-read"]}>
              <SubsidiaryMaster />
            </ProtectedRoute>
          ),
        },
        {
          path: "analytics",
          element: (
            <ProtectedRoute requiredPermissions={["analytics-read"]}>
              <AnalyticsPage />
            </ProtectedRoute>
          ),
        },
        {
          path: "intent",
          element: (
            <ProtectedRoute requiredPermissions={["intent-read"]}>
              <IntentFlow />
            </ProtectedRoute>
          ),
        },
        {
          path: "roles",
          element: (
            <ProtectedRoute requiredPermissions={["roles-read"]}>
              <RolesPage />
            </ProtectedRoute>
          ),
        },
        {
          path: "users",
          element: (
            <ProtectedRoute requiredPermissions={["users-read"]}>
              <UserPage />
            </ProtectedRoute>
          ),
        },
        {
          path: "mis-report",
          element: (
            <ProtectedRoute requiredPermissions={["mis-report-read"]}>
              <MISDashboard />
            </ProtectedRoute>
          ),
        },
        {
          path: "language",
          element: (
            <ProtectedRoute requiredPermissions={["language-read"]}>
              <LanguageManagement />
            </ProtectedRoute>
          ),
        },
        {
          path: "message",
          element: (
            <ProtectedRoute requiredPermissions={["utter-read"]}>
              <UtterMessagesPage />
            </ProtectedRoute>
          ),
        },
        {
          path: "fallback",
          element: (
            <ProtectedRoute requiredPermissions={["fallback-read"]}>
              <FallbackManagementPage />
            </ProtectedRoute>
          ),
        },
      ],
    },

    { path: "*", element: <NotFound /> },
  ],

);

function App() {
  return (
    <AuthProvider>
      <Toaster />
      <RouterProvider router={router} />
      
    </AuthProvider>
  );
}

export default App;
