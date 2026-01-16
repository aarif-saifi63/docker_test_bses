import { useState, useRef, useEffect, useContext } from "react";
import { AuthContext } from "../../context/AuthContext";
import { useNavigate } from "react-router-dom";
import { FaUserAlt, FaSignOutAlt } from "react-icons/fa";
import { motion, AnimatePresence } from "framer-motion";

export default function Header() {
  const [menuOpen, setMenuOpen] = useState(false);
  const { logout, user, updateUser } = useContext(AuthContext);
  const navigate = useNavigate();
  const menuRef = useRef(null);

  const handleToggleMenu = () => setMenuOpen(!menuOpen);

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  // Close menu if clicked outside
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setMenuOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);

    updateUser();

    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <header className="h-16 bg-white shadow flex items-center justify-between px-6 relative">
      <h2 className="text-lg font-semibold"></h2>

      <div className="flex items-center gap-4 relative" ref={menuRef}>
        {/* Optional bell or notification button could go here */}

        {/* --- Role Chip --- */}
        {user?.role_name && (
          <span
            className="text-xs font-medium bg-blue-100 text-blue-800 px-3 py-1 rounded-full capitalize"
            title={`Role: ${user.role_name}`}
          >
            {user.role_name}
          </span>
        )}

        {/* User icon */}
        <button
          onClick={handleToggleMenu}
          className="p-2 rounded-full hover:bg-gray-100 transition"
        >
          <FaUserAlt size={20} />
        </button>

        {/* Dropdown menu */}
        <AnimatePresence>
          {menuOpen && (
            <motion.div
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.2 }}
              className="absolute right-0 overflow-hidden z-10 mt-2 w-40 origin-top-right rounded-md bg-white shadow-lg ring-1 ring-black/10"
            >
              <div>
                <button
                  onClick={handleLogout}
                  className="mt-1 w-full px-4 py-2 flex items-center gap-2 text-left text-sm text-red-700 hover:bg-gray-100 transition"
                >
                  <FaSignOutAlt size={16} />
                  Logout
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </header>
  );
}
