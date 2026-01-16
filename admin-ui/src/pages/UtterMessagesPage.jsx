import React, { useEffect, useState, useMemo } from "react";
import {
  useReactTable,
  getCoreRowModel,
  flexRender,
} from "@tanstack/react-table";
import { toast } from "sonner";
import { usePermission } from "../hooks/usePermission";
import apiClient from "../services/apiClient";

export default function UtterMessagesPage() {
  const [utterMessages, setUtterMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedMessage, setSelectedMessage] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [hasNextPage, setHasNextPage] = useState(false);
  const [hasPrevPage, setHasPrevPage] = useState(false);
  const { has } = usePermission();

  // ✅ Fetch utter messages from backend API
  const fetchUtterMessages = async (pageNum = 1, searchQuery = search) => {
    setLoading(true);
    try {
      // Build API URL with search parameter if exists
      let url = `/get_all/utter_messages?page=${pageNum}`;
      if (searchQuery && searchQuery.trim()) {
        url += `&search=${encodeURIComponent(searchQuery.trim())}`;
      }

      const res = await apiClient.get(url);
      const result = res;

      if (result?.status === "success") {
        setUtterMessages(result.data || []);

        // ✅ Detect if next or previous pages exist based on data length and page number
        setHasPrevPage(result.page > 1);
        setHasNextPage((result.data || []).length >= result.per_page);
      } else {
        setUtterMessages([]);
      }
    } catch (err) {
      console.error("Failed to fetch utter messages:", err);
      setUtterMessages([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUtterMessages(page, search);
  }, [page]);

  // Debounce search to avoid too many API calls
  useEffect(() => {
    const debounceTimer = setTimeout(() => {
      setPage(1);
      fetchUtterMessages(1, search);
    }, 500);

    return () => clearTimeout(debounceTimer);
  }, [search]);

  // ✅ Edit Logic
  const handleEdit = (msg) => {
    if (!has("utter-update")) {
      toast.error("You don't have permission to update utter.");
      return;
    }
    setSelectedMessage(msg);
    setIsModalOpen(true);
  };

  // ✅ Save Logic
  const handleSave = async () => {
    try {
      const { uid, text } = selectedMessage;
      const res = await apiClient.put(`/update/utter_messages/${uid}`, { text });
      if (res?.status === "success") {
        toast.success("✅ Message updated successfully!");
        setIsModalOpen(false);
        fetchUtterMessages(page);
      } else {
        toast.error("❌ Update failed.");
      }
    } catch (err) {
      console.error("Update failed:", err?.response?.data?.message);
      toast.error(err?.response?.data?.message || "❌ Failed to update message.");
    }
  };

  // ✅ Table Columns
  const columns = useMemo(
    () => [
      {
        header: "Message Type",
        accessorKey: "message_type",
        cell: (info) => (
          <span className="capitalize font-medium text-gray-800">
            {info.getValue()}
          </span>
        ),
      },
      {
        header: " Flow/chat  menu option ",
        accessorKey: "action_name",
        cell: (info) => (
          <span className="text-gray-700">{info.getValue()}</span>
        ),
      },
      {
        header: " User Type",
        accessorKey: "class_name",
        cell: (info) => (
          <span className="text-gray-700">{info.getValue()}</span>
        ),
      },
      {
        header: "Language",
        accessorKey: "language",
        cell: (info) => (
          <span
            className={`px-2 py-1 text-xs font-semibold rounded ${info.getValue() === "en"
                ? "bg-blue-100 text-blue-700"
                : "bg-green-100 text-green-700"
              }`}
          >
            {info.getValue()?.toUpperCase()}
          </span>
        ),
      },
      {
        header: "Text",
        accessorKey: "text",
        cell: (info) => (
          <div className="truncate max-w-[300px]" title={info.getValue()}>
            {info.getValue()}
          </div>
        ),
      },
      {
        header: "Action",
        cell: ({ row }) => (
          <button
            onClick={() => handleEdit(row.original)}
            className="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded text-sm"
          >
            Edit
          </button>
        ),
      },
    ],
    []
  );

  const table = useReactTable({
    data: utterMessages,
    columns,
    getCoreRowModel: getCoreRowModel(),
  });

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-800">🗣️ Utter Messages</h1>
        <input
          type="text"
          placeholder="🔍 Search messages..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="border border-gray-300 rounded-md px-3 py-2 w-64 text-sm focus:ring-2 focus:ring-blue-400 outline-none"
        />
      </div>

      {/* Table */}
      <div className="bg-white shadow-lg rounded-lg overflow-hidden">
        <table className="min-w-full border-collapse">
          <thead className="bg-gray-100 border-b">
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <th
                    key={header.id}
                    className="text-left px-4 py-3 text-gray-700 font-semibold border-r"
                  >
                    {flexRender(
                      header.column.columnDef.header,
                      header.getContext()
                    )}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td
                  colSpan={columns.length}
                  className="text-center py-5 text-gray-500"
                >
                  Loading...
                </td>
              </tr>
            ) : table.getRowModel().rows.length ? (
              table.getRowModel().rows.map((row) => (
                <tr
                  key={row.id}
                  className="hover:bg-gray-50 border-b transition"
                >
                  {row.getVisibleCells().map((cell) => (
                    <td
                      key={cell.id}
                      className="px-4 py-3 text-sm text-gray-800 border-r"
                    >
                      {flexRender(
                        cell.column.columnDef.cell,
                        cell.getContext()
                      )}
                    </td>
                  ))}
                </tr>
              ))
            ) : (
              <tr>
                <td
                  colSpan={columns.length}
                  className="text-center py-6 text-gray-500"
                >
                  No results found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="flex justify-evenly items-center mt-5">
        <button
          onClick={() => setPage((prev) => Math.max(prev - 1, 1))}
          disabled={!hasPrevPage}
          className={`px-4 py-2 rounded-md text-sm ${!hasPrevPage
              ? "bg-gray-200 text-gray-400 cursor-not-allowed"
              : "bg-blue-500 text-white hover:bg-blue-600"
            }`}
        >
          ← Previous
        </button>

        <span className="text-gray-600 font-medium">Page {page}</span>

        <button
          onClick={() => setPage((prev) => prev + 1)}
          disabled={!hasNextPage}
          className={`px-4 py-2 rounded-md text-sm ${!hasNextPage
              ? "bg-gray-200 text-gray-400 cursor-not-allowed"
              : "bg-blue-500 text-white hover:bg-blue-600"
            }`}
        >
          Next →
        </button>
      </div>

      {/* Edit Modal */}
      {isModalOpen && selectedMessage && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-lg w-full max-w-2xl max-h-[90vh] flex flex-col">
            {/* Modal Header */}
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-xl font-semibold text-gray-800">
                Edit Utter Message
              </h2>
            </div>

            {/* Modal Body - Scrollable */}
            <div className="px-6 py-4 overflow-y-auto flex-1">
              <div className="space-y-4">
                {/* Read-only fields */}
                {["message_type", "action_name", "class_name", "language"].map(
                  (field) => (
                    <div key={field}>
                      <label className="block text-sm font-medium text-gray-700 capitalize mb-1">
                        {field.replace(/_/g, " ")}
                      </label>
                      <input
                        type="text"
                        value={selectedMessage[field] || ""}
                        disabled
                        className="border border-gray-300 rounded-md px-3 py-2 w-full bg-gray-100 text-gray-600 cursor-not-allowed text-sm"
                      />
                    </div>
                  )
                )}

                {/* Protection Note - Display if present */}
                {selectedMessage.protection_note && (
                  <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 rounded">
                    <div className="flex items-start">
                      <div className="flex-shrink-0">
                        <svg
                          className="h-5 w-5 text-yellow-400"
                          viewBox="0 0 20 20"
                          fill="currentColor"
                        >
                          <path
                            fillRule="evenodd"
                            d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                            clipRule="evenodd"
                          />
                        </svg>
                      </div>
                      <div className="ml-3">
                        <p className="text-sm font-medium text-yellow-800">
                          Protection Note
                        </p>
                        <p className="text-sm text-yellow-700 mt-1">
                          {selectedMessage.protection_note}
                        </p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Editable Text Field */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Text <span className="text-red-500">*</span>
                  </label>
                  <textarea
                    rows={8}
                    value={selectedMessage.text || ""}
                    onChange={(e) => {
                      const originalText = selectedMessage.text || "";
                      const newText = e.target.value;

                      // Split both into lines
                      const originalLines = originalText.split("\n");
                      const newLines = newText.split("\n");

                      // Ensure numeric prefixes (1., 2., 3., etc.) stay fixed
                      const fixedLines = newLines.map((line, index) => {
                        const match = originalLines[index]?.match(/^(\d+\.\s*)/);
                        if (match) {
                          const prefix = match[1]; // "1. "
                          // Remove prefix from edited line if user typed over it
                          const cleaned = line.replace(/^(\d+\.\s*)?/, "");
                          return prefix + cleaned;
                        }
                        return line; // if no prefix, keep as-is
                      });

                      setSelectedMessage({
                        ...selectedMessage,
                        text: fixedLines.join("\n"),
                      });
                    }}
                    className="border border-gray-300 rounded-md px-3 py-2 w-full focus:ring-2 focus:ring-blue-400 focus:border-blue-400 outline-none font-mono text-sm resize-none"
                    placeholder="Edit utter message text here..."
                  />
                </div>
              </div>
            </div>

            {/* Modal Footer */}
            <div className="px-6 py-4 border-t border-gray-200 flex justify-end gap-3">
              <button
                onClick={() => setIsModalOpen(false)}
                className="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400 transition text-sm font-medium"
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition text-sm font-medium"
              >
                Save
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}