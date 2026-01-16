
import React, { useEffect, useState } from "react";
import Select from "react-select";
import { toast } from "sonner";
import { CircularProgress } from "@mui/material";
import {
  X,
  Save,
  Image as ImageIcon,
  FileText,
  CheckCircle,
  XCircle,
} from "lucide-react";
import apiClient from "../../services/apiClient";
import { usePermission } from "../../hooks/usePermission";

export default function AdModal({ mode, ad = {}, onClose, onSuccess }) {
  const [adName, setAdName] = useState("");
  const [adType, setAdType] = useState(null);
  const [error, setError] = useState("");
  const [imageFile, setImageFile] = useState(null);
  const [pdfFile, setPdfFile] = useState(null);
  const [thumbType, setThumbType] = useState("image");
  const [attachType, setAttachType] = useState("document");

  const [submenuOptions, setSubmenuOptions] = useState([]);
  const [selectedSubmenus, setSelectedSubmenus] = useState([]);
  const [divisionOptions, setDivisionOptions] = useState([]);
  const [selectedDivisions, setSelectedDivisions] = useState([]);
  const [loading, setLoading] = useState(false);

  const [startTime, setStartTime] = useState(null);
  const [endTime, setEndTime] = useState(null);
  const [isActive, setIsActive] = useState(true);
  const { has } = usePermission();

  // --- Allowed extensions ---
  const IMAGE_EXT = ["png", "jpg", "jpeg"];
  const DOC_EXT = ["pdf", "doc", "docx"];
  const VIDEO_EXT = ["mp4", "mkv", "webm", "avi"];

  const isValidFileType = (file, type) => {
    if (!file) return false;
    const ext = file.name.split(".").pop().toLowerCase();
    if (type === "image") return IMAGE_EXT.includes(ext);
    if (type === "video") return VIDEO_EXT.includes(ext);
    if (type === "document") return DOC_EXT.includes(ext);
    return false;
  };

  const showInvalidFileToast = () =>
    toast.error(
      "Invalid file type. Allowed: images (png, jpg, jpeg), documents (pdf, doc, docx), videos (mp4, mkv, webm, avi)."
    );

  const adTypeOptions = [
    { value: "on_chatbot_launch", label: "on_chatbot_launch" },
    { value: "on_menu_ad", label: "on_menu_ad" },
    { value: "after_submenu_ad", label: "after_submenu_ad" },
    { value: "after_feedback_ad", label: "after_feedback_ad" },
  ];

  const fetchSubmenus = async () => {
    try {
      const res = await apiClient.get("/submenus");
      const data = res.data || [];
      const sorted = data
        .filter((s) => s.is_visible !== false)
        .sort((a, b) => {
          if (a.lang === "en" && b.lang !== "en") return -1;
          if (a.lang !== "en" && b.lang === "en") return 1;
          return 0;
        });
      setSubmenuOptions(
        sorted.map((submenu) => ({
          value: submenu.name,
          label: submenu.name,
          id: submenu.id,
        }))
      );
    } catch (err) {
      toast.error(err?.response?.data?.message || "Failed to fetch submenus");
    }
  };

  const fetchDivisions = async () => {
    try {
      const res = await apiClient.get("/divisions");
      const data = res.data?.data || res.data || [];
      setDivisionOptions(
        data.map((div) => ({
          value: div.name || div.division_name || div.id,
          label: div.name || div.division_name || `Division ${div.id}`,
          id: div.id,
        }))
      );
    } catch (err) {
      toast.error(err?.response?.data?.message || "Failed to fetch divisions");
    }
  };

  useEffect(() => {
    fetchSubmenus();
    fetchDivisions();

    const formatDateForInput = (dateStr) => {
      if (!dateStr) return "";
      const date = new Date(dateStr);
      const year = date.getUTCFullYear();
      const month = String(date.getUTCMonth() + 1).padStart(2, "0");
      const day = String(date.getUTCDate()).padStart(2, "0");
      const hours = String(date.getUTCHours()).padStart(2, "0");
      const minutes = String(date.getUTCMinutes()).padStart(2, "0");
      return `${year}-${month}-${day}T${hours}:${minutes}`;
    };

    if (mode === "edit" && ad) {
      setAdName(ad.ad_name || "");
      setAdType(ad.ad_type ? { value: ad.ad_type, label: ad.ad_type } : null);
      setSelectedSubmenus(
        (ad.chatbot_options || []).map((opt) => ({ value: opt, label: opt }))
      );
      setSelectedDivisions(
        (ad.divisions || []).map((div) => ({ value: div, label: div }))
      );
      setStartTime(formatDateForInput(ad.start_time));
      setEndTime(formatDateForInput(ad.end_time));
      setIsActive(ad.is_active ?? true);
    } else {
      setAdName("");
      setAdType(null);
      setSelectedSubmenus([]);
      setSelectedDivisions([]);
      setImageFile(null);
      setPdfFile(null);
      setStartTime(null);
      setEndTime(null);
      setIsActive(true);
    }
  }, [mode, ad]);

  useEffect(() => {
    if (adType?.value === "on_chatbot_launch") {
      setSelectedSubmenus([]);
      setSelectedDivisions([]);
    }
  }, [adType]);

  const handleSave = async () => {
    const isEdit = mode === "edit";

    if (!adName?.trim()) {
      toast.error("Advertisement name is required!");
      return;
    }
    if (!adType?.value) {
      toast.error("Please select an advertisement type!");
      return;
    }
    if (!startTime || !endTime) {
      toast.error("Please select both start and end time!");
      return;
    }

    if (!isEdit) {
      if (!imageFile) {
        toast.error("Thumbnail file is required!");
        return;
      }
      if (!pdfFile) {
        toast.error("Advertisement attachment is required!");
        return;
      }
    }

    const chatbotOptions =
      adType.value === "on_chatbot_launch"
        ? []
        : selectedSubmenus.map((s) => s.value);

    const divisions =
      adType.value === "on_chatbot_launch"
        ? []
        : (selectedDivisions || []).map((d) => d.value);

    const formData = new FormData();
    if (imageFile) {
      formData.append("ad_image", imageFile);
      formData.append("image_type", thumbType);
    }
    if (pdfFile) {
      formData.append("ad_pdf", pdfFile);
      formData.append("file_type", attachType);
    }

    formData.append("ad_type", adType.value);
    formData.append("start_time", startTime);
    formData.append("end_time", endTime);
    formData.append("is_active", isActive);
    formData.append("chatbot_options", JSON.stringify(chatbotOptions));
    formData.append("divisions", JSON.stringify(divisions));
    formData.append("ad_name", adName.trim());

    try {
      setLoading(true);
      setError("");

      if (isEdit) {
        if (!has("advertisement-update")) {
          toast.error("You don't have permission to update advertisement.");
          return;
        }

        await apiClient.put(`/update_ad`, formData, {
          params: { ad_id: ad.id },
          headers: { "Content-Type": "multipart/form-data" },
        });
        toast.success("Advertisement updated successfully ✅");
      } else {
        if (!has("advertisement-create")) {
          toast.error("You don't have permission to create advertisement.");
          return;
        }

        await apiClient.post("/add_ad", formData, {
          headers: { "Content-Type": "multipart/form-data" },
        });
        toast.success("Advertisement added successfully 🎉");
      }
      onSuccess?.();
      onClose();
    } catch (err) {
      if (err.response?.status === 413) {
        toast.error("Entity too large. Please upload another one.");
        setError("Entity too large. Please upload another one.");
      } else {
        const message =
          err.response?.data?.message || "Failed to save advertisement";
        setError(message);
        toast.error(message);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-40 flex items-center justify-center z-50">
      <div className="bg-white rounded-2xl p-6 w-[500px] relative max-h-[90vh] overflow-y-auto shadow-lg">
        <button
          onClick={onClose}
          className="absolute top-3 right-3 text-gray-500 hover:text-gray-700 transition"
        >
          <X className="w-5 h-5" />
        </button>

        <h3 className="font-semibold text-lg mb-4 text-gray-800 flex items-center gap-2">
          {mode === "edit" ? "Edit Advertisement" : "Add Advertisement"}
        </h3>

        {/* Name */}
        <label className="block mb-4 text-sm font-medium text-gray-700">
          Name
          <input
            type="text"
            value={adName}
            onChange={(e) => setAdName(e.target.value)}
            placeholder="Enter advertisement name"
            className="mt-1 w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring focus:ring-blue-100"
          />
        </label>

        {/* Type */}
        <label className="block mb-4 text-sm font-medium text-gray-700">
          Type
          <Select
            options={adTypeOptions}
            value={adType}
            onChange={setAdType}
            className="mt-1"
          />
        </label>

        {/* Submenus */}
        {adType?.value !== "on_chatbot_launch" && (
          <label className="block mb-4 text-sm font-medium text-gray-700">
            Submenus
            <Select
              isMulti
              options={submenuOptions}
              value={selectedSubmenus}
              onChange={setSelectedSubmenus}
              className="mt-1"
            />
          </label>
        )}

        {/* Divisions */}
        {adType?.value !== "on_chatbot_launch" && (
          <label className="block mb-4 text-sm font-medium text-gray-700">
            Divisions
            <Select
              isMulti
              options={divisionOptions}
              value={selectedDivisions}
              onChange={setSelectedDivisions}
              className="mt-1"
            />
          </label>
        )}

        {/* Start & End Time */}
        <label className="block mb-4 text-sm font-medium text-gray-700">
          Start Time
          <input
            type="datetime-local"
            value={startTime}
            onChange={(e) => setStartTime(e.target.value)}
            className="mt-1 w-full border border-gray-300 rounded-lg px-3 py-2"
          />
        </label>

        <label className="block mb-4 text-sm font-medium text-gray-700">
          End Time
          <input
            type="datetime-local"
            value={endTime}
            onChange={(e) => setEndTime(e.target.value)}
            className="mt-1 w-full border border-gray-300 rounded-lg px-3 py-2"
          />
        </label>

        {/* Active */}
        <button
          onClick={() => setIsActive(!isActive)}
          className={`flex items-center mb-2 gap-1 px-2 py-1 rounded-lg text-sm ${
            isActive
              ? "bg-green-100 text-green-700"
              : "bg-gray-100 text-gray-600"
          }`}
        >
          {isActive ? (
            <>
              <CheckCircle className="w-4 h-4" /> Active
            </>
          ) : (
            <>
              <XCircle className="w-4 h-4" /> Inactive
            </>
          )}
        </button>

        {/* ✅ Thumbnail Section */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            <ImageIcon className="w-4 h-4 inline-block mr-1" /> Thumbnail (Image
            / Video / Document)
          </label>

          <select
            value={thumbType}
            onChange={(e) => {
              setThumbType(e.target.value);
              setImageFile(null);
            }}
            className="border border-gray-300 rounded-lg px-2 py-1 mb-2 text-sm"
          >
            <option value="image">Image (png, jpg, jpeg)</option>
          </select>

          <input
            type="file"
            accept={
              thumbType === "image"
                ? "image/*"
                : thumbType === "video"
                ? "video/*"
                : ".pdf,.doc,.docx"
            }
            onChange={(e) => {
              const file = e.target.files[0];
              if (!file) return;
              if (!isValidFileType(file, thumbType)) {
                showInvalidFileToast();
                e.target.value = null;
                return;
              }
              setImageFile(file);
            }}
          />

          {imageFile && (
            <div className="mt-3">
              {thumbType === "image" && (
                <img
                  src={URL.createObjectURL(imageFile)}
                  alt="Thumbnail Preview"
                  className="w-32 h-32 object-contain border rounded"
                />
              )}
              {thumbType === "video" && (
                <video
                  controls
                  src={URL.createObjectURL(imageFile)}
                  className="w-64 h-40 border rounded"
                />
              )}
              {thumbType === "document" && (
                <div className="text-sm text-gray-600 mt-1">
                  <FileText className="inline w-4 h-4 mr-1" />
                  {imageFile.name}
                </div>
              )}
            </div>
          )}

          {mode === "edit" && ad.ad_image_path && !imageFile && (
            <div className="mt-3">
              {(() => {
                const path = ad.ad_image_path.toLowerCase();
                const url = `${import.meta.env.VITE_API_BASE_URL}/${
                  ad.ad_image_path
                }`;
                if (/\.(jpg|jpeg|png)$/i.test(path)) {
                  return (
                    <img
                      src={url}
                      alt="Existing Thumbnail"
                      className="w-32 h-32 object-contain border rounded"
                    />
                  );
                } else if (/\.(mp4|mkv|webm|avi)$/i.test(path)) {
                  return (
                    <video
                      controls
                      src={url}
                      className="w-64 h-40 border rounded"
                    />
                  );
                } else if (/\.(pdf|doc|docx)$/i.test(path)) {
                  return (
                    <a
                      href={url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="block text-blue-600 hover:underline text-sm mt-2"
                    >
                      📄 View current thumbnail
                    </a>
                  );
                } else {
                  return (
                    <a
                      href={url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="block text-blue-600 hover:underline text-sm mt-2"
                    >
                      📁 View current file
                    </a>
                  );
                }
              })()}
            </div>
          )}
        </div>

        {/* ✅ Attachment Section */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            <FileText className="w-4 h-4 inline-block mr-1" /> Attachment (PDF /
            Image / Video)
          </label>

          <select
            value={attachType}
            onChange={(e) => {
              setAttachType(e.target.value);
              setPdfFile(null);
            }}
            className="border border-gray-300 rounded-lg px-2 py-1 mb-2 text-sm"
          >
            <option value="document">Document (pdf, doc, docx)</option>
            <option value="image">Image (png, jpg, jpeg)</option>
            <option value="video">Video (mp4, mkv, webm, avi)</option>
          </select>

          <input
            type="file"
            accept={
              attachType === "image"
                ? "image/*"
                : attachType === "video"
                ? "video/*"
                : ".pdf,.doc,.docx"
            }
            onChange={(e) => {
              const file = e.target.files[0];
              if (!file) return;
              if (!isValidFileType(file, attachType)) {
                showInvalidFileToast();
                e.target.value = null;
                return;
              }
              setPdfFile(file);
            }}
          />

          {pdfFile && (
            <div className="mt-3">
              {attachType === "image" && (
                <img
                  src={URL.createObjectURL(pdfFile)}
                  alt="Attachment Preview"
                  className="w-32 h-32 object-contain border rounded"
                />
              )}
              {attachType === "video" && (
                <video
                  controls
                  src={URL.createObjectURL(pdfFile)}
                  className="w-64 h-40 border rounded"
                />
              )}
              {attachType === "document" && (
                <div className="text-sm text-gray-600 mt-1">
                  <FileText className="inline w-4 h-4 mr-1" />
                  {pdfFile.name}
                </div>
              )}
            </div>
          )}

          {mode === "edit" && ad.ad_pdf_path && !pdfFile && (
            <div className="mt-3">
              {(() => {
                const path = ad.ad_pdf_path.toLowerCase();
                const url = `${import.meta.env.VITE_API_BASE_URL}/${
                  ad.ad_pdf_path
                }`;
                if (/\.(jpg|jpeg|png)$/i.test(path)) {
                  return (
                    <img
                      src={url}
                      alt="Existing Attachment"
                      className="w-32 h-32 object-contain border rounded"
                    />
                  );
                } else if (/\.(mp4|mkv|webm|avi)$/i.test(path)) {
                  return (
                    <video
                      controls
                      src={url}
                      className="w-64 h-40 border rounded"
                    />
                  );
                } else if (/\.(pdf|doc|docx)$/i.test(path)) {
                  return (
                    <a
                      href={url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="block text-blue-600 hover:underline text-sm mt-2"
                    >
                      📄 View current attachment
                    </a>
                  );
                } else {
                  return (
                    <a
                      href={url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="block text-blue-600 hover:underline text-sm mt-2"
                    >
                      📁 View current file
                    </a>
                  );
                }
              })()}
            </div>
          )}
        </div>

        {error && <div className="mt-4 text-red-500 text-sm">{error}</div>}

        <div className="flex justify-end gap-3 mt-6">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-700 rounded-lg"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={loading}
            className="px-4 py-2 flex items-center gap-2 bg-green-600 hover:bg-green-700 text-white rounded-lg shadow-sm"
          >
            {loading ? (
              <CircularProgress size={18} color="inherit" />
            ) : (
              <Save className="w-4 h-4" />
            )}
            {loading ? "Saving..." : "Save"}
          </button>
        </div>
      </div>
    </div>
  );
}