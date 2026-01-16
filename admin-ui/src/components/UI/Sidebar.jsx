import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  ClipboardList,
  MessageSquare,
  Image,
  Key,
  LifeBuoy,
  Target,
  ListPlus,
  UserRoundCog,
  BookKey,
  ChartColumnBig,
  ChevronRight,
  Building,
  MessageCircle,
  // FolderTree,
  // Brain,
} from "lucide-react";
import logo from "../../assets/logo.png";
import { useState } from "react";
import { usePermission } from "../../hooks/usePermission";

// ----------------------- LINKS STRUCTURE -----------------------

const links = [
  {
    name: "Dashboard",
    path: "/",
    icon: LayoutDashboard,
    permission: "dashboard-read",
  },
  {
    name: "MIS Reports",
    path: "/mis-report",
    icon: ClipboardList,
    permission: "mis-report-read",
  },
  {
    name: "Chatbot Menu",
    path: "/chatbot-menus",
    icon: Image,
    permission: "chatbot-menu-read",
  },
  { name: "API Keys", path: "/api-key", icon: Key, permission: "api-key-read" },
  {
    name: "Advertisement",
    path: "/advertisement",
    icon: Image,
    permission: "advertisement-read",
  },
  {
    name: "Feedback",
    path: "/feedbacks",
    icon: MessageSquare,
    permission: "feedbacks-read",
  },
  { name: "Polls", path: "/polls", icon: LifeBuoy, permission: "polls-read" },
  { name: "Intent", path: "/intent", icon: Target, permission: "intent-read" },
  {
    name: "Menu",
    path: "/menus",
    icon: ListPlus,
    permission: "menus-read",
  },
  {
    name: "Analytics",
    path: "/analytics",
    icon: ChartColumnBig,
    permission: "analytics-read",
  },
  { name: "Roles", path: "/roles", icon: BookKey, permission: "roles-read" },
  {
    name: "User Management",
    path: "/users",
    icon: UserRoundCog,
    permission: "users-read",
  },
  {
    name: "Subsidiary Master",
    path: "/subsidiary-master",
    icon: Building,
    permission: "subsidiary-master-read",
  },
  {
    name: "Language",
    path: "/language",
    icon: ClipboardList,
    permission: "language-read",
  },
  {
    name: "Utter Message",
    path: "/message",
    icon: MessageCircle,
    permission: "utter-read",
  },
  {
    name: "Fallback",
    path: "/fallback",
    icon: MessageCircle,
    permission: "fallback-read",
  },
];

// ----------------------- COMPONENT -----------------------
export default function Sidebar() {
  const [hoveredMenu, setHoveredMenu] = useState(null);
  const { can } = usePermission();

  // Filter links by permission

  const authLinks = links.filter(
    (link) =>
      !link.permission || // show if no permission is defined (e.g., Dashboard)
      can(link.permission)
  );

  // const authLinks = links

  return (
    <div className="flex">
      {/* ------------ MAIN SIDEBAR ------------ */}
      <aside className="sidebar w-64 h-screen bg-white shadow-md flex flex-col relative z-10 overflow-hidden hover:overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-center py-4 border-b">
          <img src={logo} alt="BSES" className="h-10" />
        </div>

        {/* Nav Links */}
        <nav className="flex-1 p-4">
          {authLinks.map(({ name, path, icon: Icon, subLinks }) => {
            const hasSubmenu = Array.isArray(subLinks) && subLinks.length > 0;
            const isHovered = hoveredMenu === name;

            return (
              <div
                key={path}
                onMouseEnter={() => setHoveredMenu(hasSubmenu ? name : null)}
                onMouseLeave={() => setHoveredMenu(null)}
                className="relative"
              >
                <NavLink
                  to={path}
                  end={path === "/"}
                  className={({ isActive }) =>
                    `flex items-center justify-between gap-3 px-4 py-2 rounded-lg mb-2 transition-colors ${
                      isActive
                        ? "bg-red-100 text-red-600 font-semibold"
                        : "text-gray-700 hover:bg-gray-100"
                    }`
                  }
                >
                  <div className="flex items-center gap-3">
                    <Icon size={18} />
                    <span>{name}</span>
                  </div>
                  {hasSubmenu && (
                    <ChevronRight className="w-4 h-4 text-gray-500" />
                  )}
                </NavLink>

                {hasSubmenu && isHovered && (
                  <div
                    className="absolute top-0 left-full ml-1 w-56 bg-white shadow-lg border border-gray-200 rounded-lg p-3 transition-all animate-fade-in"
                    onMouseEnter={() => setHoveredMenu(name)}
                    onMouseLeave={() => setHoveredMenu(null)}
                  >
                    <p className="text-gray-700 font-semibold mb-2 border-b pb-1">
                      {name}
                    </p>

                    {subLinks.map(
                      ({ name: subName, path: subPath, icon: SubIcon }) => (
                        <NavLink
                          key={subPath}
                          to={subPath}
                          className={({ isActive }) =>
                            `flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors ${
                              isActive
                                ? "bg-red-100 text-red-600 font-semibold"
                                : "text-gray-600 hover:bg-gray-100"
                            }`
                          }
                        >
                          <SubIcon size={16} />
                          <span>{subName}</span>
                        </NavLink>
                      )
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </nav>
      </aside>
    </div>
  );
}
