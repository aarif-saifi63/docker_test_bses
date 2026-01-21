import { useEffect, useState } from "react";
import { Pencil, Save, RotateCcw, X, Search, Plus, Trash2, Edit3 } from "lucide-react";
import apiClient from "../services/apiClient";
import { toast } from "sonner";
import { usePermission } from "../hooks/usePermission";
import { useConfirm } from "../hooks/useConfirm";
import CircularProgress from "@mui/material/CircularProgress";
import CategoryModal from "../components/Message/CategoryModal";

export default function FallbackManagementPage() {
  // Original fallback state
  const [fallbackList, setFallbackList] = useState([]);
  const [loading, setLoading] = useState(false);
  const [savingId, setSavingId] = useState(null);
  const [editId, setEditId] = useState(null);
  const [form, setForm] = useState({ initial_msg: "", final_msg: "" });

  // Categories state
  const [categories, setCategories] = useState([]);
  const [categoriesLoading, setCategoriesLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [categoryModal, setCategoryModal] = useState({ open: false, mode: "add", category: null });
  const [deletingCategory, setDeletingCategory] = useState(null);

  const { has } = usePermission();
  const { confirm, ConfirmDialog } = useConfirm();

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
      toast.error(err?.response?.error || "Failed to fetch fallback!");
    } finally {
      setLoading(false);
    }
  };

  // ---------------- FETCH CATEGORIES ----------------
  const fetchCategories = async () => {
    try {
      setCategoriesLoading(true);
      const res = await apiClient.get("/get-all/submenu-fallback/categories");
      // Handle response - can be direct array or wrapped in data
      const data = Array.isArray(res) ? res : (res.data || []);
      setCategories(data);
    } catch (err) {
      console.error("Error fetching categories:", err);
      toast.error(err?.response?.data?.error || "Failed to fetch categories");
    } finally {
      setCategoriesLoading(false);
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
      toast.error(err?.response?.data?.error || "Failed to update fallback!");
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

  const handleRefreshAll = () => {
    fetchFallback();
    fetchCategories();
  };

  // ---------------- DELETE CATEGORY ----------------
  const handleDeleteCategory = async (category) => {
    const userConfirmed = await confirm({
      title: "Delete Category",
      message: `Are you sure you want to delete "${category.category}"? This action cannot be undone.`,
    });

    if (!userConfirmed) return;

    try {
      setDeletingCategory(category.category);
      const encodedCategory = encodeURIComponent(category.category);
      await apiClient.delete(`/delete/submenu-fallback/${encodedCategory}`);
      toast.success("Category deleted successfully");
      setCategories((prev) => prev.filter((cat) => cat.category !== category.category));
    } catch (err) {
      console.error("Error deleting category:", err);
      toast.error(err?.response?.data?.error || "Failed to delete category");
    } finally {
      setDeletingCategory(null);
    }
  };

  useEffect(() => {
    fetchFallback();
    fetchCategories();
  }, []);

  // Filter categories based on search
  const filteredCategories = categories.filter((cat) => {
    const query = searchQuery.toLowerCase();
    return cat.category?.toLowerCase().includes(query);
  });

  // Get total intent count
  const totalIntents = categories.reduce((sum, cat) => sum + (cat.intent_count || 0), 0);

  // ---------------- UI ----------------
  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      {/* Header */}
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-2xl font-semibold text-gray-800">
          💬 Fallback Management
        </h1>

        <button
          onClick={handleRefreshAll}
          disabled={loading || categoriesLoading}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg border text-sm font-medium ${
            loading || categoriesLoading
              ? "bg-gray-100 text-gray-400 cursor-not-allowed"
              : "hover:bg-gray-100 text-gray-700 border-gray-300"
          }`}
        >
          <RotateCcw className="w-4 h-4" />
          Refresh All
        </button>
      </div>

      {/* ----------- ORIGINAL FALLBACK MESSAGES SECTION ----------- */}
      <div className="mb-12">
        <h2 className="text-xl font-semibold text-gray-800 mb-4">Fallback Messages</h2>

        {loading ? (
          <div className="flex justify-center py-10">
            <CircularProgress />
          </div>
        ) : fallbackList.length === 0 ? (
          <div className="text-gray-500 text-center py-10 bg-white rounded-xl border">
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

      {/* ----------- CATEGORIES SECTION ----------- */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-xl font-semibold text-gray-800">Sub-Menu Fallback</h2>
          </div>
          <button
            onClick={() => setCategoryModal({ open: true, mode: "add", category: null })}
            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 transition text-white px-4 py-2 rounded-lg shadow-md"
          >
            <Plus className="w-5 h-5" /> Add Sub-Menu Fallback
          </button>
        </div>

        {/* Search Bar */}
        <div className="mb-6">
          <div className="relative max-w-md">
            <Search className="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Search sub-menu fallback..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-100 focus:border-blue-400"
            />
          </div>
        </div>

        {/* Loading State */}
        {categoriesLoading && (
          <div className="flex items-center justify-center py-20">
            <CircularProgress size={40} />
            <span className="ml-3 text-gray-600">Loading categories...</span>
          </div>
        )}

        {/* Empty State */}
        {!categoriesLoading && filteredCategories.length === 0 && (
          <div className="text-center py-20 bg-white rounded-xl border">
            <div className="max-w-md mx-auto">
              <svg
                className="w-20 h-20 text-gray-300 mx-auto mb-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"
                />
              </svg>
              <h3 className="text-xl font-semibold text-gray-700 mb-2">
                {searchQuery ? "No Categories Found" : "No Categories Yet"}
              </h3>
              <p className="text-gray-500">
                {searchQuery
                  ? "Try adjusting your search query."
                  : "Categories will appear here once created."}
              </p>
            </div>
          </div>
        )}

        {/* Categories Table */}
        {!categoriesLoading && filteredCategories.length > 0 && (
          <>
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden mb-8">
              <div className="max-h-[600px] overflow-y-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50 sticky top-0 z-10">
                    <tr>
                      <th className="px-6 py-4 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider bg-gray-50">
                        #
                      </th>
                      <th className="px-6 py-4 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider bg-gray-50">
                        Sub-Menu Name
                      </th>
                      <th className="px-6 py-4 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider bg-gray-50">
                        Fallback Message
                      </th>
                      <th className="px-6 py-4 text-right text-xs font-semibold text-gray-700 uppercase tracking-wider bg-gray-50">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {filteredCategories.map((cat, index) => (
                      <tr key={index} className="hover:bg-blue-50 transition-colors duration-150">
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 font-medium">
                          {index + 1}
                        </td>
                        <td className="px-6 py-4">
                          <div className="text-sm font-semibold text-gray-900">{cat.category}</div>
                        </td>
                        <td className="px-6 py-4">
                          <div className="text-sm text-gray-700 line-clamp-2 max-w-md">
                            {cat.initial_msg || "No message available"}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                          <div className="flex items-center justify-end gap-4">
                            <button
                              onClick={() => setCategoryModal({ open: true, mode: "edit", category: cat })}
                              className="p-2 text-yellow-600 hover:text-white hover:bg-yellow-600 rounded-lg transition-all duration-200"
                              title="Edit Category"
                            >
                              <Edit3 className="w-4 h-4" />
                            </button>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleDeleteCategory(cat);
                              }}
                              disabled={deletingCategory === cat.category}
                              className="p-2 text-red-600 hover:text-white hover:bg-red-600 rounded-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-transparent disabled:hover:text-red-600"
                              title="Delete Category"
                            >
                              {deletingCategory === cat.category ? (
                                <CircularProgress size={16} color="inherit" />
                              ) : (
                                <Trash2 className="w-4 h-4" />
                              )}
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Stats Summary */}
            {/* <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
              <h3 className="text-lg font-semibold text-gray-800 mb-4">Summary</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="text-center p-4 bg-blue-50 rounded-lg">
                  <p className="text-2xl font-bold text-blue-600">{categories.length}</p>
                  <p className="text-sm text-gray-600 mt-1">Total Categories</p>
                </div>
                <div className="text-center p-4 bg-green-50 rounded-lg">
                  <p className="text-2xl font-bold text-green-600">{totalIntents}</p>
                  <p className="text-sm text-gray-600 mt-1">Total Intents</p>
                </div>
                <div className="text-center p-4 bg-purple-50 rounded-lg">
                  <p className="text-2xl font-bold text-purple-600">
                    {categories.length > 0 ? Math.round(totalIntents / categories.length) : 0}
                  </p>
                  <p className="text-sm text-gray-600 mt-1">Avg per Category</p>
                </div>
                <div className="text-center p-4 bg-orange-50 rounded-lg">
                  <p className="text-2xl font-bold text-orange-600">
                    {Math.max(...categories.map((c) => c.intent_count || 0), 0)}
                  </p>
                  <p className="text-sm text-gray-600 mt-1">Max Intents</p>
                </div>
              </div>
            </div> */}
          </>
        )}
      </div>

      {/* Category Modal */}
      {categoryModal.open && (
        <CategoryModal
          mode={categoryModal.mode}
          category={categoryModal.category}
          onClose={() => setCategoryModal({ open: false, mode: "add", category: null })}
          onSuccess={fetchCategories}
        />
      )}

      {/* Confirm Dialog */}
      <ConfirmDialog />
    </div>
  );
}
