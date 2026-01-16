import React, { useEffect, useState } from "react";
import apiClient from "../services/apiClient";
import { Plus, Trash2, Edit2, X, Save, Globe2 } from "lucide-react";
import { usePermission } from "../hooks/usePermission";
import { toast } from "sonner";
import TrainingStatusWidget from "../components/Training/TrainingStatusWidget.jsx";

export default function LanguageManager() {
  const [languages, setLanguages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [editId, setEditId] = useState(null);
  const [formData, setFormData] = useState({
    name: "",
    code: "",
    is_visible: true,
  });

  const { has } = usePermission();

  const fetchLanguages = async () => {
    setLoading(true);
    try {
      const res = await apiClient.get("/get-languages");
      const langs = Array.isArray(res?.data) ? res.data : [];
      setLanguages(langs);
    } catch (err) {
      console.error("Failed to fetch languages:", err);
      toast.error("Failed to load languages");
      setLanguages([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLanguages();
  }, []);

  // ✅ Open modal (same as before)
  const handleOpenModal = (lang = null) => {
    if (lang) {
      setEditId(lang.id);
      setFormData({
        name: lang.name,
        code: lang.code,
        is_visible: lang.is_visible,
      });
    } else {
      setEditId(null);
      setFormData({ name: "", code: "", is_visible: true });
    }
    setShowModal(true);
  };

  // ✅ Add or Update Language (apiClient version)
  // const handleSubmit = async (e) => {
  //   e.preventDefault();

  //   if (!formData.name.trim() || !formData.code.trim()) {
  //     alert("Please fill all fields");
  //     return;
  //   }

  //   try {
  //     if (editId) {
  //       // Update existing language
  //       if (!has("language-update")) {
  //         toast.error("You don't have permission to update language.");
  //         return; // Stop the save operation if no permission
  //       }

  //       await apiClient.put(`/language/${editId}`, formData);
  //     } else {
  //       // Create new language
  //       if (!has("language-create")) {
  //         toast.error("You don't have permission to create language.");
  //         return; // Stop the save operation if no permission
  //       }

  //       await apiClient.post("/add-language", formData);
  //     }

  //     await fetchLanguages();
  //     setShowModal(false);
  //     setEditId(null);
  //     setFormData({ name: "", code: "", is_visible: true });
  //   } catch (err) {
  //     console.error("Failed to save language:", err);
  //     toast.error(err.response?.data?.message || "Something went wrong while saving language.");
  //   }
  // };

  const handleSubmit = async (e) => {
    e.preventDefault();

    const isEdit = !!editId;

    // --- Field validation ---
    const name = formData.name?.trim();
    const code = formData.code?.trim();

    if (!name) {
      toast.error("Language name is required!");
      return;
    }

    if (!code) {
      toast.error("Language code is required!");
      return;
    }

    const codeRegex = /^[a-z]{2,5}$/i; // allows e.g., en, hi, fr, eng, etc.
    if (!codeRegex.test(code)) {
      toast.error("Language code must contain only letters (2–5 characters).");
      return;
    }

    // --- Permission checks ---
    if (isEdit && !has("language-update")) {
      toast.error("You don't have permission to update language.");
      return;
    }

    if (!isEdit && !has("language-create")) {
      toast.error("You don't have permission to create language.");
      return;
    }

    try {
      if (isEdit) {
        await apiClient.put(`/update/language/${editId}`, {
          ...formData,
          name,
          code,
        });
        toast.success("Language updated successfully!");
      } else {
        await apiClient.post("/add-language", {
          ...formData,
          name,
          code,
        });
        toast.success("Language created successfully!");
      }

      await fetchLanguages();
      setShowModal(false);
      setEditId(null);
      setFormData({ name: "", code: "", is_visible: true });
    } catch (err) {
      console.error("Failed to save language:", err);
      toast.error(err.response?.data?.message || "Something went wrong while saving language.");
    }
  };

  // ✅ Delete Language (apiClient version)
  const handleDelete = async (id) => {
    if (!window.confirm("Are you sure you want to delete this language?")) return;

    if (!has("language-delete")) {
      toast.error("You don't have permission to delete language.");
      return; // Stop the save operation if no permission
    }

    try {
      await apiClient.delete(`/delete/language/${id}`);
      await fetchLanguages();
    } catch (err) {
      console.error("Failed to delete language:", err);
      toast.error(err.response?.data?.message || "Something went wrong while deleting language.");
    }
  };

  // ✅ Toggle Visibility Switch Component
  const ToggleSwitch = ({ checked, onChange }) => (
    <button
      type="button"
      onClick={() => onChange(!checked)}
      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-all duration-200 ${
        checked ? "bg-green-500" : "bg-gray-300"
      }`}
    >
      <span
        className={`inline-block h-4 w-4 transform rounded-full bg-white transition-all duration-200 ${
          checked ? "translate-x-6" : "translate-x-1"
        }`}
      />
    </button>
  );

  return (
    <div className="p-6 max-w-8xl mx-auto">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-semibold text-gray-800 flex items-center gap-2">
          <Globe2 size={26} className="text-blue-600" />
          Language Management
        </h1>
        <div className="flex items-center gap-3">

            <TrainingStatusWidget />
          <button
            onClick={() => handleOpenModal()}
            className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-all shadow-md"
          >
            <Plus size={18} />
            Add Language
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="border rounded-lg shadow-sm bg-white overflow-hidden">
        {loading ? (
          <p className="p-4 text-gray-500 text-center">Loading...</p>
        ) : languages.length === 0 ? (
          <p className="p-4 text-gray-500 text-center">No languages found.</p>
        ) : (
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-100">
              <tr>
                <th className="px-4 py-2 text-left text-sm font-semibold text-gray-700">#</th>
                <th className="px-4 py-2 text-left text-sm font-semibold text-gray-700">Name</th>
                <th className="px-4 py-2 text-left text-sm font-semibold text-gray-700">Code</th>
                <th className="px-4 py-2 text-left text-sm font-semibold text-gray-700">Visible</th>
                <th className="px-4 py-2 text-right text-sm font-semibold text-gray-700">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {languages.map((lang, idx) => (
                <tr key={lang.id} className="hover:bg-gray-50">
                  <td className="px-4 py-2 text-gray-700">{idx + 1}</td>
                  <td className="px-4 py-2 font-medium text-gray-800">{lang.name}</td>
                  <td className="px-4 py-2 text-gray-700">{lang.code}</td>
                  <td className="px-4 py-2">
                    {lang.is_visible ? (
                      <span className="text-green-600 font-medium">Yes</span>
                    ) : (
                      <span className="text-red-500 font-medium">No</span>
                    )}
                  </td>
                  <td className="px-4 py-2 text-right flex justify-end gap-3">
                    <button
                      onClick={() => handleOpenModal(lang)}
                      className="text-blue-600 hover:text-blue-800 transition"
                      title="Edit"
                    >
                      <Edit2 size={18} />
                    </button>
                    <button
                      onClick={() => handleDelete(lang.id)}
                      className="text-red-600 hover:text-red-800 transition"
                      title="Delete"
                    >
                      <Trash2 size={18} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* ✨ Modern Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-40 backdrop-blur-sm flex items-center justify-center z-50 animate-fadeIn">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg p-6 relative animate-scaleIn">
            {/* Close Button */}
            <button
              onClick={() => setShowModal(false)}
              className="absolute top-3 right-3 text-gray-500 hover:text-gray-700"
            >
              <X size={22} />
            </button>

            <h2 className="text-xl font-semibold mb-5 text-gray-800 flex items-center gap-2">
              {editId ? "Edit Language" : "Add New Language"}
            </h2>

            <form onSubmit={handleSubmit} className="space-y-5">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Language Name
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="Enter language name"
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-400 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Language Name
                </label>
                <select
                  value={formData.code}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      code: e.target.value,
                    })
                  }
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-400 focus:outline-none"
                >
                  <option value="">-- Select Language --</option>
                  <option value="en">English</option>
                  <option value="hi">Hindi</option>
                </select>
              </div>

              {/* Toggle Switch */}
              <div className="flex items-center justify-between mt-4">
                <label className="text-sm font-medium text-gray-700">Visibility</label>
                <ToggleSwitch
                  checked={formData.is_visible}
                  onChange={(val) => setFormData({ ...formData, is_visible: val })}
                />
              </div>

              <div className="flex justify-end gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="flex items-center gap-2 bg-gray-200 text-gray-800 px-4 py-2 rounded-md hover:bg-gray-300 transition-all"
                >
                  <X size={16} /> Cancel
                </button>
                <button
                  type="submit"
                  className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-all shadow-md"
                >
                  <Save size={16} /> {editId ? "Update" : "Save"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
