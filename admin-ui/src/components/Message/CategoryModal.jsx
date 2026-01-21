import React, { useEffect, useState } from "react";
import Select from "react-select";
import { toast } from "sonner";
import { CircularProgress } from "@mui/material";
import { X, Save, FolderOpen, Tag, MessageSquare, Users, Globe, FileText } from "lucide-react";
import apiClient from "../../services/apiClient";

export default function CategoryModal({ mode, category = null, onClose, onSuccess }) {
  const [categoryName, setCategoryName] = useState("");
  const [intentNames, setIntentNames] = useState("");
  const [initialMsg, setInitialMsg] = useState("");
  const [finalMsg, setFinalMsg] = useState("");
  const [userType, setUserType] = useState([]);
  const [language, setLanguage] = useState(null);
  const [loading, setLoading] = useState(false);
  const [fetchingDetails, setFetchingDetails] = useState(false);

  const userTypeOptions = [
    { value: "new", label: "New Consumer" },
    { value: "registered", label: "Registered Consumer" },
  ];

  const languageOptions = [
    { value: "English", label: "English" },
    { value: "हिंदी", label: "हिंदी" },
  ];

  // Fetch category details for edit mode
  const fetchCategoryDetails = async (categoryName) => {
    try {
      setFetchingDetails(true);
      const encodedCategory = encodeURIComponent(categoryName);
      const res = await apiClient.get(`/get/submenu-fallback/${encodedCategory}`);
      const data = res.data || res;

      if (data) {
        setCategoryName(data.category || categoryName);

        // Handle intents - can be array or comma-separated string
        if (Array.isArray(data.intents)) {
          setIntentNames(data.intents.join(", "));
        } else if (data.intent_names) {
          setIntentNames(data.intent_names);
        } else {
          setIntentNames("");
        }

        setInitialMsg(data.initial_msg || "");
        setFinalMsg(data.final_msg || "");

        // Handle user_type - can be array or string
        if (Array.isArray(data.user_type)) {
          setUserType(
            data.user_type.map((type) => {
              // Map old values to new ones
              const mappedType = type === "new_consumer" ? "new" : type === "registered_consumer" ? "registered" : type;
              return userTypeOptions.find((opt) => opt.value === mappedType) || { value: mappedType, label: mappedType };
            })
          );
        } else if (data.user_type) {
          const types = data.user_type.split(',').map(t => t.trim());
          setUserType(
            types.map((type) => {
              // Map old values to new ones
              const mappedType = type === "new_consumer" ? "new" : type === "registered_consumer" ? "registered" : type;
              return userTypeOptions.find((opt) => opt.value === mappedType) || { value: mappedType, label: mappedType };
            })
          );
        }

        // Handle language
        if (data.language) {
          const lang = languageOptions.find((opt) =>
            opt.value === data.language || opt.label === data.language
          );
          setLanguage(lang || { value: data.language, label: data.language });
        }
      }
    } catch (err) {
      console.error("Error fetching category details:", err);
      toast.error(err?.response?.data?.error || "Failed to fetch category details");
    } finally {
      setFetchingDetails(false);
    }
  };

  useEffect(() => {
    if (mode === "edit" && category?.category) {
      fetchCategoryDetails(category.category);
    } else {
      // Reset form for add mode
      setCategoryName("");
      setIntentNames("");
      setInitialMsg("");
      setFinalMsg("");
      setUserType([]);
      setLanguage(null);
    }
  }, [mode, category]);

  const handleSave = async () => {
    const isEdit = mode === "edit";

    // Validation - in edit mode only validate initial_msg
    if (isEdit) {
      if (!initialMsg?.trim()) {
        toast.error("Initial message is required!");
        return;
      }
    } else {
      // Add mode - validate all fields
      if (!categoryName?.trim()) {
        toast.error("Sub-menu name is required!");
        return;
      }
      if (!intentNames?.trim()) {
        toast.error("Sub-menu Intent name is required!");
        return;
      }
      if (!initialMsg?.trim()) {
        toast.error("Initial message is required!");
        return;
      }
      // if (!finalMsg?.trim()) {
      //   toast.error("Final message is required!");
      //   return;
      // }
      if (!userType || userType.length === 0) {
        toast.error("Please select at least one user type!");
        return;
      }
      if (!language?.value) {
        toast.error("Please select a language!");
        return;
      }
    }

    let payload;

    if (isEdit) {
      // In edit mode, only send initial_msg
      payload = {
        category: categoryName.trim(),
        intent_names: intentNames.trim(),
        initial_msg: initialMsg.trim(),
        final_msg: finalMsg.trim(),
        user_type: userType.map((ut) => ut.value),
        language: language.value,
      };
    } else {
      // In add mode, send all fields
      payload = {
        category: categoryName.trim(),
        intent_names: intentNames.trim(),
        initial_msg: initialMsg.trim(),
        final_msg: "hello",
        user_type: userType.map((ut) => ut.value),
        language: language.value,
      };
    }

    try {
      setLoading(true);

      if (isEdit && category?.category) {
        // Update existing category
        const encodedCategory = encodeURIComponent(category.category);
        await apiClient.put(`/update/submenu-fallback/${encodedCategory}`, payload);
        toast.success("Initial message updated successfully");
      } else {
        // Create new category
        await apiClient.post("/create/submenu-fallback", payload);
        toast.success("Category created successfully");
      }

      onSuccess?.();
      onClose();
    } catch (err) {
      const errorMessage =
        err.response?.data?.message || err.response?.data?.error || "Failed to save category";
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl w-full max-w-3xl relative max-h-[92vh] overflow-hidden shadow-2xl border border-gray-100">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-blue-700 px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-white bg-opacity-20 rounded-lg">
              <FolderOpen className="w-6 h-6 text-white" />
            </div>
            <div>
              <h3 className="font-semibold text-xl text-white">
                {mode === "edit" ? "Edit Sub-Menu Fallback" : "Add Sub-Menu Fallback"}
              </h3>
              <p className="text-blue-100 text-sm mt-0.5">
                {mode === "edit" ? "Update fallback message" : "Create a new fallback category"}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-white hover:bg-white hover:bg-opacity-20 p-2 rounded-lg transition-all duration-200"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="p-6 overflow-y-auto max-h-[calc(92vh-140px)]">
          {fetchingDetails ? (
            <div className="flex flex-col items-center justify-center py-16">
              <CircularProgress size={45} />
              <span className="mt-4 text-gray-600 font-medium">Loading category details...</span>
            </div>
          ) : (
            <div className="space-y-5">
              {/* Category Name */}
              <div className="bg-gray-50 rounded-xl p-4 border border-gray-200">
                <label className="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
                  <Tag className="w-4 h-4 text-blue-600" />
                  Sub-Menu Name <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={categoryName}
                  onChange={(e) => setCategoryName(e.target.value)}
                  placeholder="Enter category name"
                  disabled={mode === "edit"}
                  className={`w-full border-2 rounded-lg px-4 py-2.5 text-sm transition-all ${mode === "edit"
                    ? "bg-gray-100 border-gray-200 cursor-not-allowed text-gray-600"
                    : "border-gray-300 focus:ring-2 focus:ring-blue-100 focus:border-blue-500 bg-white"
                    }`}
                />
                {/* {mode === "edit" && (
                  <p className="text-xs text-gray-500 mt-2 flex items-center gap-1">
                    <span className="w-1 h-1 bg-gray-400 rounded-full"></span>
                    Category name cannot be changed
                  </p>
                )} */}
              </div>

              {/* Intent Names */}
              <div className="bg-gray-50 rounded-xl p-4 border border-gray-200">
                <label className="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
                  <FileText className="w-4 h-4 text-purple-600" />
                  Sub-Menu Intent Name <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={intentNames}
                  onChange={(e) => setIntentNames(e.target.value)}
                  placeholder="e.g., faq_billing, faq_connection, faq_complaint"
                  disabled={mode === "edit"}
                  className={`w-full border-2 rounded-lg px-4 py-2.5 text-sm transition-all ${mode === "edit"
                    ? "bg-gray-100 border-gray-200 cursor-not-allowed text-gray-600"
                    : "border-gray-300 focus:ring-2 focus:ring-blue-100 focus:border-blue-500 bg-white"
                    }`}
                />
                {/* <p className="text-xs text-gray-500 mt-2 flex items-center gap-1">
                  <span className="w-1 h-1 bg-gray-400 rounded-full"></span>
                  {mode === "edit" ? "Intent names cannot be changed" : "Comma-separated intent names"}
                </p> */}
              </div>

              {/* Initial Message */}
              <div className="bg-blue-50 rounded-xl p-4 border-2 border-blue-200">
                <label className="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
                  <MessageSquare className="w-4 h-4 text-blue-600" />
                  Fallback Message <span className="text-red-500">*</span>
                </label>
                <textarea
                  value={initialMsg}
                  onChange={(e) => setInitialMsg(e.target.value)}
                  placeholder="Enter initial fallback message"
                  rows={4}
                  className="w-full border-2 border-blue-300 rounded-lg px-4 py-3 text-sm focus:ring-2 focus:ring-blue-100 focus:border-blue-500 resize-none bg-white transition-all"
                />
                {/* {mode === "edit" && (
                  <p className="text-xs text-blue-600 mt-2 flex items-center gap-1 font-medium">
                    <span className="w-1 h-1 bg-blue-500 rounded-full"></span>
                    This is the only editable field
                  </p>
                )} */}
              </div>

              {/* Final Message - Only show in add mode */}
              {/* {mode === "add" && (
                <div className="bg-gray-50 rounded-xl p-4 border border-gray-200">
                  <label className="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
                    <MessageSquare className="w-4 h-4 text-orange-600" />
                    Final Message <span className="text-red-500">*</span>
                  </label>
                  <textarea
                    value={finalMsg}
                    onChange={(e) => setFinalMsg(e.target.value)}
                    placeholder="Enter final fallback message"
                    rows={4}
                    className="w-full border-2 border-gray-300 rounded-lg px-4 py-3 text-sm focus:ring-2 focus:ring-blue-100 focus:border-blue-500 resize-none bg-white transition-all"
                  />
                </div>
              )} */}

              {/* User Type & Language */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* User Type */}
                <div className="bg-gray-50 rounded-xl p-4 border border-gray-200">
                  <label className="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
                    <Users className="w-4 h-4 text-green-600" />
                    User Type <span className="text-red-500">*</span>
                  </label>
                  <Select
                    isMulti
                    options={userTypeOptions}
                    value={userType}
                    onChange={setUserType}
                    placeholder="Select user types"
                    isDisabled={mode === "edit"}
                    className="text-sm"
                    classNamePrefix="react-select"
                    styles={{
                      control: (base, state) => ({
                        ...base,
                        borderWidth: '2px',
                        borderColor: state.isFocused ? '#3b82f6' : '#d1d5db',
                        boxShadow: state.isFocused ? '0 0 0 3px rgba(59, 130, 246, 0.1)' : 'none',
                        '&:hover': {
                          borderColor: state.isFocused ? '#3b82f6' : '#9ca3af',
                        },
                      }),
                    }}
                  />
                </div>

                {/* Language */}
                <div className="bg-gray-50 rounded-xl p-4 border border-gray-200">
                  <label className="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
                    <Globe className="w-4 h-4 text-indigo-600" />
                    Language <span className="text-red-500">*</span>
                  </label>
                  <Select
                    options={languageOptions}
                    value={language}
                    onChange={setLanguage}
                    placeholder="Select language"
                    isDisabled={mode === "edit"}
                    className="text-sm"
                    classNamePrefix="react-select"
                    styles={{
                      control: (base, state) => ({
                        ...base,
                        borderWidth: '2px',
                        borderColor: state.isFocused ? '#3b82f6' : '#d1d5db',
                        boxShadow: state.isFocused ? '0 0 0 3px rgba(59, 130, 246, 0.1)' : 'none',
                        '&:hover': {
                          borderColor: state.isFocused ? '#3b82f6' : '#9ca3af',
                        },
                      }),
                    }}
                  />
                  {/* {mode === "edit" && (
                    <p className="text-xs text-gray-500 mt-2 flex items-center gap-1">
                      <span className="w-1 h-1 bg-gray-400 rounded-full"></span>
                      Language cannot be changed
                    </p>
                  )} */}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-5 py-2.5 bg-white border-2 border-gray-300 hover:bg-gray-50 hover:border-gray-400 text-gray-700 font-medium rounded-lg transition-all duration-200"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={loading || fetchingDetails}
            className="px-5 py-2.5 flex items-center gap-2 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white font-medium rounded-lg shadow-md hover:shadow-lg transition-all duration-200 disabled:from-gray-400 disabled:to-gray-400 disabled:cursor-not-allowed disabled:shadow-none"
          >
            {loading ? (
              <>
                <CircularProgress size={18} color="inherit" />
                <span>Saving...</span>
              </>
            ) : (
              <>
                <Save className="w-4 h-4" />
                <span>Save Changes</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
