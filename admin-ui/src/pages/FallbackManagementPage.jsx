import { useEffect, useState } from "react";
import { Pencil, Save, RotateCcw, X } from "lucide-react";
import apiClient from "../services/apiClient";
import { toast } from "sonner";
import { usePermission } from "../hooks/usePermission";
import CircularProgress from "@mui/material/CircularProgress";

export default function FallbackManagementPage() {
  const [fallbackList, setFallbackList] = useState([]);
  const [loading, setLoading] = useState(false);
  const [savingId, setSavingId] = useState(null);
  const [editId, setEditId] = useState(null);
  const [form, setForm] = useState({ initial_msg: "", final_msg: "" });
  const { has } = usePermission();

  // ---------------- FETCH FALLBACK LIST ----------------
  const fetchFallback = async () => {
    try {
      setLoading(true);
      const res = await apiClient.get("/get-fallback", {
        headers: { "Content-Type": "application/json" },
      });

      if (Array.isArray(res)) {
        setFallbackList(res);
      } else {
        setFallbackList([]);
        toast.error("No fallback data found!");
      }
    } catch (err) {
      console.error("Error fetching fallback:", err);
      toast.error(err?.response?.error ||"Failed to update fallback!");
    } finally {
      setLoading(false);
    }
  };

  // ---------------- UPDATE FALLBACK ----------------
  const handleUpdate = async (id) => {
    if (!has("fallback-update")) {
      toast.error("You don't have permission to update.");
      return;
    }

    const item = fallbackList.find((f) => f.id === id);
    if (!item) return toast.error("Fallback not found!");

    if (!form.initial_msg.trim() || !form.final_msg.trim()) {
      toast.error("Both fields are required!");
      return;
    }

    try {
      setSavingId(id);
      await apiClient.put(`/update-fallback/${id}`, {
        initial_msg: form.initial_msg,
        final_msg: form.final_msg,
      });
      toast.success("Fallback updated successfully!");
      setEditId(null);
      fetchFallback();
    } catch (err) {
      console.error("Error updating fallback:", err);
      toast.error( err?.response?.data?.error ||"Failed to update fallback!");
    } finally {
      setSavingId(null);
    }
  };

  // ---------------- HANDLERS ----------------
  const handleEditClick = (item) => {
    setEditId(item.id);
    setForm({
      initial_msg: item.initial_msg,
      final_msg: item.final_msg,
    });
  };

  const handleCancel = () => {
    setEditId(null);
    setForm({ initial_msg: "", final_msg: "" });
  };

  useEffect(() => {
    fetchFallback();
  }, []);

  // ---------------- UI ----------------
  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-2xl font-semibold text-gray-800">
          💬 Fallback Message Management
        </h1>

        <button
          onClick={fetchFallback}
          disabled={loading}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg border text-sm font-medium ${
            loading
              ? "bg-gray-100 text-gray-400 cursor-not-allowed"
              : "hover:bg-gray-100 text-gray-700 border-gray-300"
          }`}
        >
          <RotateCcw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {/* Loading */}
      {loading ? (
        <div className="flex justify-center py-10">
          <CircularProgress />
        </div>
      ) : fallbackList.length === 0 ? (
        <div className="text-gray-500 text-center py-10">
          No fallback messages found.
        </div>
      ) : (
        <div className="space-y-6">
          {fallbackList.map((item) => (
            <div
              key={item.id}
              className="border border-gray-200 rounded-xl shadow-sm bg-white hover:shadow-md transition"
            >
              <div className="p-5 flex justify-between items-start">
                <div className="flex-1">
                  <h2 className="text-lg font-semibold text-gray-800 mb-3">
                    Fallback #{item.id}
                  </h2>

                  {/* View Mode */}
                  {editId !== item.id ? (
                    <div className="space-y-4">
                      <div>
                        <p className="text-sm font-medium text-gray-600 mb-1">
                          Initial Message:
                        </p>
                        <p className="text-gray-800 whitespace-pre-wrap bg-gray-50 p-3 rounded border">
                          {item.initial_msg || "—"}
                        </p>
                      </div>

                      <div>
                        <p className="text-sm font-medium text-gray-600 mb-1">
                          Final Message:
                        </p>
                        <p className="text-gray-800 whitespace-pre-wrap bg-gray-50 p-3 rounded border">
                          {item.final_msg || "—"}
                        </p>
                      </div>
                    </div>
                  ) : (
                    // Edit Mode
                    <div className="space-y-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Initial Message
                        </label>
                        <textarea
                          value={form.initial_msg}
                          onChange={(e) =>
                            setForm((prev) => ({
                              ...prev,
                              initial_msg: e.target.value,
                            }))
                          }
                          rows={3}
                          className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Final Message
                        </label>
                        <textarea
                          value={form.final_msg}
                          onChange={(e) =>
                            setForm((prev) => ({
                              ...prev,
                              final_msg: e.target.value,
                            }))
                          }
                          rows={5}
                          className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        />
                      </div>
                    </div>
                  )}
                </div>

                {/* Action Buttons */}
                <div className="flex flex-col gap-2 ml-6">
                  {editId === item.id ? (
                    <>
                      <button
                        onClick={() => handleUpdate(item.id)}
                        disabled={savingId === item.id}
                        className={`flex items-center gap-1 px-3 py-1.5 rounded-lg text-sm font-medium ${
                          savingId === item.id
                            ? "bg-gray-400 text-white"
                            : "bg-green-600 hover:bg-green-700 text-white"
                        }`}
                      >
                        {savingId === item.id ? (
                          <CircularProgress size={16} color="inherit" />
                        ) : (
                          <Save className="w-4 h-4" />
                        )}
                        Save
                      </button>

                      <button
                        onClick={handleCancel}
                        className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-sm border border-gray-300 text-gray-700 hover:bg-gray-100"
                      >
                        <X className="w-4 h-4" />
                        Cancel
                      </button>
                    </>
                  ) : (
                    <button
                      onClick={() => handleEditClick(item)}
                      className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-sm border border-blue-500 text-blue-600 hover:bg-blue-50"
                    >
                      <Pencil className="w-4 h-4" />
                      Edit
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
