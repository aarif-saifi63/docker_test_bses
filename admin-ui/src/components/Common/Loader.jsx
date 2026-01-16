import React from "react";

export default function Loader({ text = "Loading..." }) {
  return (
    <div className="flex flex-col items-center justify-center py-10">
      <div className="w-10 h-10 border-4 border-red-500 border-dashed rounded-full animate-spin"></div>
      <p className="mt-2 text-red-600 font-medium">{text}</p>
    </div>
  );
}
