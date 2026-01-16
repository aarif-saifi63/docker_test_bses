import React from "react";
import { useNavigate } from "react-router-dom";
import { Home, ArrowLeft, SearchX } from "lucide-react";

import logo from "../assets/logo.png";

export default function NotFound() {
  const navigate = useNavigate();

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gradient-to-br from-white via-gray-50 to-blue-50 text-gray-800 px-4">
      {/* Icon with glow */}
      <div className="bg-blue-100 p-6 rounded-full mb-6 glow">
        <SearchX size={80} className="text-blue-500" />
      </div>

      {/* Title */}
      <h1 className="text-4xl md:text-5xl font-extrabold mb-3 tracking-tight text-gray-900">
        404 – Page Not Found
      </h1>

      {/* Subtitle */}
      <p className="text-gray-600 text-center max-w-md mb-10">
        The page you’re looking for doesn’t exist, has been moved, or you might have mistyped the
        URL.
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
          Go Home
        </button>
      </div>

      {/* Decorative Illustration */}
      <div className="mt-12">
        {/* <svg
          className="w-72 opacity-40 text-blue-300"
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="currentColor"
        >
          <path d="M12 2a10 10 0 1 0 10 10A10.011 10.011 0 0 0 12 2Zm4.5 14.09-1.41 1.41L12 13.41l-3.09 3.09-1.41-1.41L10.59 12 7.5 8.91 8.91 7.5 12 10.59l3.09-3.09 1.41 1.41L13.41 12Z" />
        </svg> */}
        <div className="flex items-center justify-center py-4 border-b">
          <img src={logo} alt="BSES" className="h-10" />
        </div>
      </div>

      {/* Footer */}
      <p className="mt-10 text-sm text-gray-500">© {new Date().getFullYear()} BSES</p>
    </div>
  );
}
