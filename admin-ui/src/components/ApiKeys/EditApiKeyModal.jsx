import React, { useEffect, useState } from "react";
import { RxCross1 } from "react-icons/rx";
import { Plus, Trash2 } from "lucide-react";
import apiClient from "../../services/apiClient";
import { toast } from "sonner";
import { usePermission } from "../../hooks/usePermission";

export default function EditApiKeyModal({ open, onClose, item, onUpdated }) {
  const [form, setForm] = useState({
    menu_option: "",
    api_name: "",
    api_url: "",
    api_headers: {},
  });
  const { has } = usePermission();

  useEffect(() => {
    if (item) setForm(item);
  }, [item]);

  const handleHeaderChange = (key, value) => {
    setForm((prev) => ({
      ...prev,
      api_headers: { ...prev.api_headers, [key]: value },
    }));
  };

  const handleAddHeader = () => {
    const newKey = "";
    setForm((prev) => ({
      ...prev,
      api_headers: { ...prev.api_headers, [newKey]: "" },
    }));
  };

  const handleKeyChange = (oldKey, newKey) => {
    setForm((prev) => {
      const newHeaders = { ...prev.api_headers };
      const value = newHeaders[oldKey];
      delete newHeaders[oldKey];
      newHeaders[newKey] = value;
      return { ...prev, api_headers: newHeaders };
    });
  };

  const handleRemoveHeader = (key) => {
    setForm((prev) => {
      const newHeaders = { ...prev.api_headers };
      delete newHeaders[key];
      return { ...prev, api_headers: newHeaders };
    });
  };

  const handleSave = async () => {
    try {
      if (!has("api-key-update")) {
        toast.error("You don't have permission to update API key.");
        return; // Stop the operation if no permission
      }
      await apiClient.put(
        "/api-key-master-update",
        {
          api_name: form.api_name,
          api_url: form.api_url,
          api_headers: form.api_headers,
        },
        { headers: { "Content-Type": "application/json" } }
      );
      toast.success("API Key updated successfully ✅");
      onUpdated?.();
      onClose();
    } catch (error) {
      console.error("Error updating API key:", error?.response?.data?.message);
      toast.error(error?.response?.data?.message || "Failed to update API key");
    }
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex">
      {/* Overlay */}
      <div className="flex-1 bg-black bg-opacity-40" onClick={onClose}></div>

      {/* Drawer */}
      <div className="w-96 bg-white p-6 shadow-lg overflow-y-auto">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold">Edit API</h2>
          <button onClick={onClose} className="text-gray-600 hover:text-gray-800 transition">
            <RxCross1 />
          </button>
        </div>

        {/* Menu Option */}
        <label className="block text-sm font-medium mb-1">Menu Option</label>
        <input
          className="w-full border p-2 rounded mb-3 bg-gray-100"
          value={form.menu_option || ""}
          disabled
        />

        {/* API Name */}
        <label className="block text-sm font-medium mb-1">API Name</label>
        <input
          className="w-full border p-2 rounded mb-3 bg-gray-100"
          value={form.api_name || ""}
          disabled
        />

        {/* API URL */}
        <label className="block text-sm font-medium mb-1">API URL</label>
        <input
          className="w-full border p-2 rounded mb-3"
          value={form.api_url || ""}
          onChange={(e) => setForm({ ...form, api_url: e.target.value })}
        />

        {/* API Headers */}
        <h3 className="text-sm font-medium mt-4 mb-2 flex justify-between items-center">
          <span>API Headers</span>
          <button
            onClick={handleAddHeader}
            className="text-blue-600 text-xs flex items-center gap-1 hover:underline"
          >
            <Plus className="w-4 h-4" /> Add Header
          </button>
        </h3>

        {Object.entries(form.api_headers || {}).map(([key, val], index) => (
          <div key={index} className="flex gap-2 mb-2 items-center">
            <input
              className="w-1/3 border p-1 rounded text-xs"
              value={key}
              onChange={(e) => handleKeyChange(key, e.target.value)}
              placeholder="Key"
            />
            <input
              className="flex-1 border p-1 rounded text-xs"
              value={val}
              onChange={(e) => handleHeaderChange(key, e.target.value)}
              placeholder="Value"
            />
            <button
              onClick={() => handleRemoveHeader(key)}
              className="text-red-500 hover:text-red-700"
              title="Remove header"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        ))}

        {/* Save Button */}
        <div className="mt-6 flex justify-end">
          <button
            onClick={handleSave}
            className="px-4 py-1 rounded bg-blue-600 text-white hover:bg-blue-700 transition"
          >
            Save
          </button>
        </div>
      </div>
    </div>
  );
}
