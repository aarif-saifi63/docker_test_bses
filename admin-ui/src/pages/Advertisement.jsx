import React, { use, useEffect, useState } from "react";
import { toast } from "sonner";
import { CircularProgress } from "@mui/material";
import {
  Plus,
  Edit3,
  Trash2,
  FileText,
  Image as ImageIcon,
  Layers,
  Tag,
  CheckCircle,
  XCircle,
} from "lucide-react";
import AdModal from "../components/Advertisement/AdModal";
import apiClient from "../services/apiClient";
import { useConfirm } from "../hooks/useConfirm";
import { formatDateRange, formatDateTime } from "../utils/time";
import { usePermission } from "../hooks/usePermission";

export default function AdsPage() {
  const [ads, setAds] = useState([]);
  const [loading, setLoading] = useState(false);
  const [deletingId, setDeletingId] = useState(null);
  const [modal, setModal] = useState({ open: false, mode: "add", ad: null });

  const { confirm, ConfirmDialog } = useConfirm();

  const { has } = usePermission();

  // ✅ Normalize: only rename `divisions_list` → `divisions`
  const normalizeAds = (data = []) =>
    data.map(({ divisions_list, ...rest }) => ({
      ...rest,
      divisions: divisions_list,
    }));

  const fetchAds = async () => {
    try {
      setLoading(true);
      const res = await apiClient.get("/ads/get-ads");
      const normalized = normalizeAds(res.data || []);
      setAds(normalized);
    } catch (err) {
      console.error("Error fetching ads:", err);
      toast.error(
        err?.response?.data?.error || "Failed to fetch advertisements"
      );
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (ad) => {
    // if (!window.confirm(`Delete advertisement "${ad.ad_name}"?`)) return;
    if (!has("advertisement-delete")) {
      toast.error("You don't have permission to delete advertisement.");
      return; // Stop the operation if no permission
    }

    const userConfirmed = await confirm({
      title: "Delete Advertisement",
      message: `Are you sure you want to delete ${ad.ad_name}? This action cannot be undone.`,
    });

    if (!userConfirmed) return;
    try {
      setDeletingId(ad.id);
      await apiClient.delete("/delete-ad", { params: { ad_id: ad.id } });
      toast.success("Advertisement deleted 🗑️");
      // fetchAds();

      setAds((prev) => prev.filter((advert) => advert.id !== ad.id));
    } catch (err) {
      console.error("Error deleting ad:", err);
      toast.error("Failed to delete advertisement");
    } finally {
      setDeletingId(null);
    }
  };

  useEffect(() => {
    fetchAds();
  }, []);

  return (
    <div className="p-8 bg-gray-50 min-h-screen">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-semibold text-gray-800 flex items-center gap-2">
          <ImageIcon className="w-6 h-6 text-blue-600" />
          Advertisements
        </h2>
        <button
          onClick={() => setModal({ open: true, mode: "add", ad: null })}
          className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 transition text-white px-4 py-2 rounded-lg shadow-md"
        >
          <Plus className="w-5 h-5" /> Add Advertisement
        </button>
      </div>

      {loading && (
        <div className="text-center py-10 text-gray-600">
          Loading advertisements...
        </div>
      )}

      {!loading && ads.length === 0 && (
        <div className="text-center py-20">
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
                d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
              />
            </svg>
            <h3 className="text-xl font-semibold text-gray-700 mb-2">
              No Advertisements Found
            </h3>
            <p className="text-gray-500 mb-6">
              There are no advertisements to display at the moment.
            </p>
          </div>
        </div>
      )}

      <div className="grid gap-6 grid-cols-1 md:grid-cols-2 xl:grid-cols-3">
        {ads.map((ad) => (
          <div
            key={ad.id}
            className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm hover:shadow-md transition-all duration-200 relative flex flex-col"
          >
            {/* Header */}
            <div className="flex items-center gap-4">
              <img
                src={`${import.meta.env.VITE_API_BASE_URL}/${ad.ad_image_path
                  }`}
                alt={ad.ad_name}
                className="w-24 h-24 object-contain border rounded-md bg-gray-50"
              />
              <div className="flex-1">
                <h3 className="font-semibold text-lg text-gray-800">
                  {ad.ad_name}
                </h3>
                <div className="flex flex-col gap-1 mt-1">
                  <p className="text-sm text-gray-500 capitalize flex items-center gap-1">
                    <Tag className="w-4 h-4 text-blue-500" />
                    <span>Type:</span>{" "}
                    <span className="font-medium">{ad.ad_type}</span>
                  </p>
                  <p className="text-sm text-gray-500 flex items-center gap-1">
                    <Layers className="w-4 h-4 text-green-500" />
                    <span>Divisions:</span>{" "}
                    <span className="font-medium break-words">
                      {ad.divisions || "None"}
                    </span>
                  </p>
                </div>
                <p className="text-xs text-gray-400 mt-2">
                  Created: {new Date(ad.created_at).toLocaleString()}
                </p>
              </div>
            </div>

            <div className="mt-2 space-y-1 text-xs text-gray-400">
              <p>Created: {formatDateTime(ad.created_at)}</p>
              <p className="text-xs text-gray-500 mt-1">
                Duration:{" "}
                <span className="font-medium">
                  {formatDateRange(ad.start_time, ad.end_time)}
                </span>
              </p>

              <p>
                <button
                  // onClick={() => setIsActive(!isActive)}
                  className={`flex items-center mb-2 gap-1 px-2 py-1 rounded-lg text-sm ${ad.is_active
                    ? "bg-green-100 text-green-700"
                    : "bg-gray-100 text-gray-600"
                    }`}
                >
                  {ad.is_active ? (
                    <>
                      <CheckCircle className="w-4 h-4" /> Active
                    </>
                  ) : (
                    <>
                      <XCircle className="w-4 h-4" /> Inactive
                    </>
                  )}
                </button>
              </p>
            </div>

            {/* PDF Link */}
            {ad.ad_pdf_path &&
              (() => {
                const IMAGE_EXT = ["png", "jpg", "jpeg"];
                const DOC_EXT = ["pdf", "doc", "docx"];
                const VIDEO_EXT = ["mp4", "mkv", "webm", "avi"];

                const fileUrl = `${import.meta.env.VITE_API_BASE_URL}/${ad.ad_pdf_path
                  }`;
                const ext = ad.ad_pdf_path.split(".").pop().toLowerCase();

                let label = "View File";
                if (IMAGE_EXT.includes(ext)) label = "View Image";
                else if (VIDEO_EXT.includes(ext)) label = "View Video";
                else if (DOC_EXT.includes(ext)) label = "View Document";

                return (
                  <a
                    href={fileUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="mt-3 inline-flex items-center gap-2 text-sm text-blue-600 hover:underline"
                  >
                    <FileText className="w-4 h-4" /> {label}
                  </a>
                );
              })()}

            {/* Actions */}
            <div className="flex justify-end gap-3 mt-5 border-t pt-4">
              <button
                onClick={() => setModal({ open: true, mode: "edit", ad })}
                className="flex items-center gap-1 text-yellow-600 hover:text-yellow-700 transition"
              >
                <Edit3 className="w-4 h-4" />
                Edit
              </button>
              <button
                onClick={() => handleDelete(ad)}
                disabled={deletingId === ad.id}
                className="flex items-center gap-1 text-red-600 hover:text-red-700 transition"
              >
                {deletingId === ad.id ? (
                  <CircularProgress size={18} color="inherit" />
                ) : (
                  <>
                    <Trash2 className="w-4 h-4" />
                    Delete
                  </>
                )}
              </button>
            </div>
          </div>
        ))}
      </div>

      {modal.open && (
        <AdModal
          mode={modal.mode}
          ad={modal.ad}
          onClose={() => setModal({ open: false, mode: "add", ad: null })}
          onSuccess={fetchAds}
        />
      )}

      <ConfirmDialog />
    </div>
  );
}