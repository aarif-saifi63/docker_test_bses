import React, { useContext } from "react";
import { useNavigate } from "react-router-dom";
import { AuthContext } from "../context/AuthContext";
import { ShieldAlert, Home, LogOut, ArrowLeft } from "lucide-react";
import logo from "../assets/logo.png";

export default function NotAuthorized() {
  const navigate = useNavigate();
  const { logout } = useContext(AuthContext);

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gradient-to-br from-white via-gray-50 to-blue-50 text-gray-800 px-4">
      {/* Icon with glow animation */}
      <div className="bg-red-100 p-6 rounded-full mb-6 glow">
        <ShieldAlert size={80} className="text-red-500" />
      </div>

      {/* Title */}
      <h1 className="text-4xl md:text-5xl font-extrabold mb-3 tracking-tight text-gray-900">
        403 – Access Denied
      </h1>

      {/* Subtitle */}
      <p className="text-gray-600 text-center max-w-md mb-10">
        Oops! You don’t have permission to view this page. If you think this is
        a mistake, please contact your administrator.
      </p>

      {/* Navigation Buttons */}
      <div className="flex flex-wrap justify-center gap-4">
        <button
          onClick={() => navigate(-1)}
          className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gray-100 text-gray-800 border border-gray-300 hover:bg-gray-200 transition-all"
        >
          <ArrowLeft size={18} />
          Go Back
        </button>

        <button
          onClick={() => navigate("/")}
          className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-blue-600 text-white hover:bg-blue-700 transition-all shadow"
        >
          <Home size={18} />
          Dashboard
        </button>

        <button
          onClick={handleLogout}
          className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-red-500 text-white hover:bg-red-600 transition-all shadow"
        >
          <LogOut size={18} />
          Logout
        </button>
      </div>

      {/* Decorative Illustration */}
      <div className="mt-12">
        {/* <svg
          className="w-72 opacity-40 text-blue-300"
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 512 512"
          fill="currentColor"
        >
          <path d="M256 32C132.3 32 32 132.3 32 256s100.3 224 224 224 224-100.3 224-224S379.7 32 256 32zM64 256c0-105.9 86.1-192 192-192s192 86.1 192 192-86.1 192-192 192S64 361.9 64 256zm112-32h160c8.8 0 16 7.2 16 16v80c0 8.8-7.2 16-16 16H176c-8.8 0-16-7.2-16-16v-80c0-8.8 7.2-16 16-16z" />
        </svg> */}

        <div className="flex items-center justify-center py-4 border-b">
          <img src={logo} alt="BSES" className="h-10" />
        </div>
      </div>

      {/* Footer */}
      <p className="mt-10 text-sm text-gray-500">
        © {new Date().getFullYear()} BSES
      </p>
    </div>
  );
}
