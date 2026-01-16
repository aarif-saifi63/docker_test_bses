import React, { useEffect, useState, useRef } from "react";
import axios from "axios";
import {
  Button,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Box,
  Pagination,
  Typography,
  Menu,
  MenuItem,
} from "@mui/material";

import { Edit, Trash2, Plus, X, Download } from "lucide-react";
import { toast } from "sonner";
import "react-toastify/dist/ReactToastify.css";
import { usePermission } from "../../hooks/usePermission";
import TrainingStatusWidget from "../Training/TrainingStatusWidget.jsx";
import apiClient from "../../services/apiClient.js";

const API_BASE = import.meta.env.VITE_API_BASE_URL;

const IntentFlow = () => {
  const [intents, setIntents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const [editingIntent, setEditingIntent] = useState(null);
  const [intentName, setIntentName] = useState("");
  const [examples, setExamples] = useState([]);
  const [expandedRows, setExpandedRows] = useState({});
  const [inputValue, setInputValue] = useState("");

  const inputRef = useRef(null);

  const [page, setPage] = useState(1);
  const [limit] = useState(10);
  const [totalPages, setTotalPages] = useState(1);
  const [search, setSearch] = useState("");
  const [exportAnchorEl, setExportAnchorEl] = useState(null);
  const { has } = usePermission();

  const fetchIntents = async (currentPage = page, searchQuery = search) => {
    try {
      setLoading(true);

      // Build API URL with search parameter if exists
      let url = `${API_BASE}/intents?page=${currentPage}&limit=${limit}`;
      if (searchQuery && searchQuery.trim()) {
        url += `&intent_name=${encodeURIComponent(searchQuery.trim())}`;
      }

      const res = await apiClient.get(url);
      const data = res.data || [];
      setIntents(data);
      setTotalPages(res?.total_pages || 1);
    } catch (err) {
      toast.error("⚠️ Failed to fetch intents");
      console.error("Error fetching intents:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIntents(page, search);
  }, [page]);

  // Debounce search to avoid too many API calls
  useEffect(() => {
    const debounceTimer = setTimeout(() => {
      setPage(1); // Reset to first page on new search
      fetchIntents(1, search);
    }, 500); // 500ms debounce

    return () => clearTimeout(debounceTimer);
  }, [search]);



  // ✅ Add new example chip
  const handleAddExample = (e) => {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault();
      const trimmed = inputValue.trim();
      if (
        trimmed &&
        !examples.some((ex) => ex.value.toLowerCase() === trimmed.toLowerCase())
      ) {
        setExamples([...examples, { value: trimmed, label: trimmed }]);
      }
      setInputValue("");
    }
  };

  const handleRemoveExample = (idx) => {
    const updated = examples.filter((_, i) => i !== idx);
    setExamples(updated);
  };

  // 🔹 Helper function to safely append BRPL once
  const appendBRPLOnce = (text) => {
    if (!text) return "";
    const trimmed = text.trim();
    const regex = /\bBRPL$/i;
    return regex.test(trimmed) ? trimmed : `${trimmed} BRPL`;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    // --- Basic validation ---
    const trimmedIntentName = intentName?.trim();
    if (!trimmedIntentName) {
      toast.error("Intent name is required!");
      return;
    }

    if (!Array.isArray(examples) || examples.length === 0) {
      toast.error("At least two examples are required!");
      return;
    }

    // Filter valid examples
    const validExamples = examples
      .map((ex) => ({
        id: ex.id,
        value: ex.value?.trim(),
      }))
      .filter((ex) => ex.value && ex.value.length > 0);

    if (validExamples.length < 2) {
      toast.error("Please provide at least two valid examples!");
      return;
    }

    // --- Add BRPL only to examples ---
    const examplesWithBRPL = validExamples.map((ex) => ({
      ...(ex.id && { id: ex.id }),
      example: appendBRPLOnce(ex.value),
    }));

    // --- Build payload ---
    const payload = {
      intent_name: trimmedIntentName, // ✅ unchanged
      examples: examplesWithBRPL, // ✅ BRPL added only here
    };

    try {
      if (editingIntent) {
        if (!has("intent-update")) {
          toast.error("You don't have permission to update intents.");
          return;
        }

        // --- Normalization Helper (handles BRPL suffix, Hindi/English text, trim, case) ---
        const normalize = (text) => {
          if (!text) return "";
          let val =
            typeof text === "object" ? text.example || text.value || "" : text;
          val = val.toString().trim();
          // ensure one BRPL suffix
          if (!/BRPL$/i.test(val)) val += " BRPL";
          return val.replace(/\s+BRPL$/i, " BRPL");
        };

        // --- Extract original (from backend) and current (from UI) ---
        const original = (editingIntent.examples || []).map(normalize);
        const current = (examples || []).map(normalize);

        // --- Detect Added Examples ---
        const added = current.filter((item) => !original.includes(item));

        // --- Detect Deleted Examples ---
        const deleted = original.filter((item) => !current.includes(item));


        // --- Build payload in your backend’s format ---
        const updatePayload = {
          added_examples: added.map((ex) =>
            ex.replace(/\s*brpl$/i, " BRPL").trim()
          ),
          deleted_examples: deleted.map((ex) =>
            ex.replace(/\s*brpl$/i, " BRPL").trim()
          ),
        };


        if (
          updatePayload.added_examples.length === 0 &&
          updatePayload.deleted_examples.length === 0
        ) {
          toast.error("⚠️ No changes detected to update!");
          return;
        }

        await axios.put(
          `${API_BASE}/update-intent-examples/${editingIntent.id}`,
          updatePayload,
          { headers: { "Content-Type": "application/json" } }
        );

        toast.success("✅ Intent updated successfully!");
        await fetchIntents(page);
      } else {
        if (!has("intent-create")) {
          toast.error("You don't have permission to create intents.");
          return;
        }

        await axios.post(`${API_BASE}/intent/create`, payload);
        toast.success("✅ Intent created successfully!");
        await fetchIntents(page);
      }

      // ✅ Reset form
      setOpen(false);
      setEditingIntent(null);
      setIntentName("");
      setExamples([]);
    } catch (err) {
      console.error("Error saving intent:", err);
      toast.error(err.response?.data?.message || "❌ Failed to save intent");
    }
  };

  const handleDelete = async (id) => {
    try {
      if (!has("intent-delete")) {
        toast.error("You don't have permission to delete intent.");
        return; // Stop the operation if no permission
      }

      // await axios.delete(`${API_BASE}/intent/${id}`);
      toast.success("🗑️ Intent deleted successfully!");
      fetchIntents(page);
    } catch (err) {
      toast.error("❌ Failed to delete intent");
      console.error("Error deleting intent:", err);
    }
  };

  const handleEdit = (intent) => {
    setEditingIntent(intent);
    setIntentName(intent.intent_name);
    const mapped = intent.examples.map((ex) =>
      typeof ex === "object"
        ? { id: ex.id, value: ex.example, label: ex.example }
        : { value: ex, label: ex }
    );
    setExamples(mapped);
    setOpen(true);
  };

  const handleCreate = () => {
    setEditingIntent(null);
    setIntentName("");
    setExamples([]);
    setOpen(true);
  };

  const toggleExpand = (id) => {
    setExpandedRows((prev) => ({
      ...prev,
      [id]: !prev[id],
    }));
  };

  const handleExportClick = (event) => {
    setExportAnchorEl(event.currentTarget);
  };

  const handleExportClose = () => {
    setExportAnchorEl(null);
  };

  const handleExport = async (format) => {
    try {
      // Construct full URL
      const exportUrl = `${API_BASE}/intents/export?format=${format}`;

      window.location.href = exportUrl;

      toast.success(`✅ Intents exported as ${format.toUpperCase()}`);
      handleExportClose();
    } catch (err) {
      console.error('Error exporting intents:', err);
      toast.error('❌ Failed to export intents');
      handleExportClose();
    }
  };
  return (
    <Box sx={{ padding: 3, background: "#f7f8fa", minHeight: "100vh" }}>
      {/* <Box className="flex justify-between items-center mb-3">
        <h3 className="flex items-center gap-2 text-lg font-semibold">
          🧠 Intent Management
        </h3>

        <TrainingStatusWidget />
      </Box> */}

      <Box className="flex justify-between items-center mb-3">
        <h3 className="flex items-center gap-2 text-lg font-semibold">
          🧠 Intent Management
        </h3>

        <Box className="flex items-center gap-3">
          <input
            type="text"
            placeholder="🔍 Search intents..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="border border-gray-300 rounded-md px-3 py-2 w-64 text-sm focus:ring-2 focus:ring-blue-400 outline-none"
          />

          <Button
            variant="contained"
            startIcon={<Download size={18} />}
            onClick={handleExportClick}
            sx={{
              textTransform: "none",
              backgroundColor: "#10b981",
              "&:hover": { backgroundColor: "#059669" },
            }}
          >
            Export
          </Button>

          <Menu
            anchorEl={exportAnchorEl}
            open={Boolean(exportAnchorEl)}
            onClose={handleExportClose}
            anchorOrigin={{
              vertical: "bottom",
              horizontal: "right",
            }}
            transformOrigin={{
              vertical: "top",
              horizontal: "right",
            }}
          >
            <MenuItem onClick={() => handleExport("xlsx")}>
              Export as XLSX
            </MenuItem>
            <MenuItem onClick={() => handleExport("csv")}>
              Export as CSV
            </MenuItem>
          </Menu>
        </Box>

        <TrainingStatusWidget />
      </Box>

      {loading ? (
        <Box className="flex justify-center items-center h-[70vh]">
          <CircularProgress size={45} thickness={4.5} />
        </Box>
      ) : (
        <>
          <TableContainer component={Paper} elevation={2}>
            <Table aria-label="intents table">
              <TableHead>
                <TableRow style={{ background: "#f0f2f5" }}>
                  <TableCell>
                    <strong>ID</strong>
                  </TableCell>
                  <TableCell>
                    <strong>Intent Name</strong>
                  </TableCell>
                  <TableCell>
                    <strong>Chatmenus</strong>
                  </TableCell>
                  <TableCell>
                    <strong>Examples</strong>
                  </TableCell>
                  <TableCell align="right">
                    <strong>Actions</strong>
                  </TableCell>
                </TableRow>
              </TableHead>

              <TableBody>
                {intents?.length > 0 ? (
                  intents.map((intent, index) => {
                    const isExpanded = expandedRows[intent.id];
                    const examplesToShow = isExpanded
                      ? intent.examples
                      : intent.examples.slice(0, 5);

                    return (
                      <TableRow
                        key={intent.id || index}
                        hover
                        sx={{ transition: "all 0.2s ease-in-out" }}
                      >
                        <TableCell>{(page - 1) * limit + index + 1}</TableCell>
                        <TableCell>{intent.intent_name}</TableCell>

                        <TableCell sx={{ width: "20%" }}>
                          {intent.submenus && intent.submenus.length > 0 ? (
                            <Box
                              sx={{
                                background: "#f9fafb",
                                borderRadius: 2,
                                padding: 1.2,
                                maxHeight: 120,
                                overflowY: "auto",
                                boxShadow: "inset 0 0 4px rgba(0,0,0,0.08)",
                              }}
                            >
                              <ul className="pl-4 list-disc text-sm text-gray-800">
                                {intent.submenus.map((submenu, idx) => (
                                  <li key={idx} className="mb-1">
                                    {submenu.submenu_name}{" "}
                                    <span className="text-gray-500 text-xs">
                                      ({submenu.lang})
                                    </span>
                                  </li>
                                ))}
                              </ul>
                            </Box>
                          ) : (
                            <Typography variant="body2" color="textSecondary">
                              No submenu
                            </Typography>
                          )}
                        </TableCell>

                        <TableCell sx={{ width: "40%" }}>
                          <Box
                            sx={{
                              background: "#f9fafb",
                              borderRadius: 2,
                              padding: 1.5,
                              maxHeight: isExpanded ? 200 : 120,
                              overflowY: "auto",
                              boxShadow: "inset 0 0 4px rgba(0,0,0,0.08)",
                            }}
                          >
                            <ul className="pl-5 list-disc text-sm text-gray-800">
                              {examplesToShow.map((ex, idx) => (
                                <li key={idx} className="mb-1">
                                  {typeof ex === "object" ? ex.example : ex}
                                </li>
                              ))}
                            </ul>
                          </Box>

                          {intent.examples.length > 5 && (
                            <Typography
                              variant="body2"
                              color="primary"
                              sx={{
                                cursor: "pointer",
                                mt: 0.5,
                                fontWeight: 600,
                                textAlign: "center",
                                display: "inline-block",
                                px: 1.2,
                                py: 0.4,
                                borderRadius: "8px",
                                background: "#eef3ff",
                                "&:hover": { background: "#dbe6ff" },
                              }}
                              onClick={() => toggleExpand(intent.id)}
                            >
                              {isExpanded ? "Show Less ▲" : "Show More ▼"}
                            </Typography>
                          )}
                        </TableCell>

                        <TableCell align="right">
                          <IconButton
                            color="primary"
                            onClick={() => handleEdit(intent)}
                          >
                            <Edit size={18} />
                          </IconButton>
                        </TableCell>
                      </TableRow>
                    );
                  })
                ) : (
                  <TableRow>
                    <TableCell colSpan={5} align="center">
                      No intents found.
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>

          <Box sx={{ display: "flex", justifyContent: "center", mt: 3 }}>
            <Pagination
              count={totalPages}
              page={page}
              onChange={(e, value) => setPage(value)}
              color="primary"
              shape="rounded"
            />
          </Box>
        </>
      )}

      {/* ✅ Tailwind Modal with Chip Input */}
      {open && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-lg w-full max-w-lg p-6 relative">
            <h2 className="text-lg font-semibold mb-4">
              {editingIntent ? "Edit Intent" : "Create New Intent"}
            </h2>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Intent Name
                </label>
                <input
                  type="text"
                  value={intentName}
                  onChange={(e) => setIntentName(e.target.value)}
                  required
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring focus:ring-blue-200"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Examples
                </label>

                <div
                  className="flex flex-wrap gap-3 border border-gray-300 rounded-md p-3 min-h-[80px] max-h-[220px] overflow-y-auto custom-scroll focus-within:ring focus-within:ring-blue-200 transition-shadow duration-200"
                  onClick={() => inputRef.current?.focus()}
                >
                  {examples.map((ex, idx) => (
                    <div
                      key={idx}
                      className="flex items-center gap-2 bg-blue-100 text-blue-800 px-4 py-2 rounded-full text-base shadow-sm hover:bg-blue-200 transition-all duration-150"
                    >
                      {ex.value}
                      <button
                        type="button"
                        onClick={() => handleRemoveExample(idx)}
                        className="text-blue-700 hover:text-red-500"
                      >
                        <X size={18} />
                      </button>
                    </div>
                  ))}

                  <input
                    ref={inputRef}
                    type="text"
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyDown={handleAddExample}
                    placeholder="Type example and press Enter"
                    className="flex-1 border-none outline-none px-3 text-base text-gray-700 min-w-[150px]"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-3 mt-6">
                <button
                  type="button"
                  onClick={() => setOpen(false)}
                  className="px-4 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                  {editingIntent ? "Update" : "Create"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </Box>
  );
};

export default IntentFlow;
