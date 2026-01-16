
import React, { useEffect, useState } from "react";
import axios from "axios";
import {
  Box,
  Button,
  Typography,
  IconButton,
  CircularProgress,
} from "@mui/material";
import { DataGrid } from "@mui/x-data-grid";
import { SaveAlt, Visibility, Edit } from "@mui/icons-material";
import { toast } from "sonner";
import * as XLSX from "xlsx";
import { saveAs } from "file-saver";
import DateInteractions from "../components/ApiKeys/DateInteractions.jsx";
import EditApiKeyModal from "../components/ApiKeys/EditApiKeyModal.jsx";
import UsageModal from "../components/ApiKeys/UsageModal.jsx"; // ✅ import your modal
import apiClient from "../services/apiClient.js";

export default function ApiKeysPage() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState(null);

  // ✅ For UsageModal
  const [usageModalOpen, setUsageModalOpen] = useState(false);
  const [usageList, setUsageList] = useState([]);
  const [activeUsageId, setActiveUsageId] = useState(null);

  const [activeTab, setActiveTab] = useState("Daily");
  const [startDate, setStartDate] = useState(new Date());
  const [endDate, setEndDate] = useState(new Date());
  const [isDatePickerOpen, setIsDatePickerOpen] = useState(false);

  // 🔹 Fetch data
  const fetchData = async () => {
    setLoading(true);
    try {
      const formatDate = (date) =>
        date ? date.toISOString().split("T")[0] : null;
      const formatMonth = (date) => date.toISOString().slice(0, 7);

      let params = {};

      if (activeTab === "Hourly") {
        params.last_hour = true;
      } else if (activeTab === "Daily" || activeTab === "Date") {
        params.start_date = formatDate(startDate);
        params.end_date = formatDate(endDate);
      } else if (activeTab === "Monthly") {
        params.month = formatMonth(startDate);
      }

      // const res = await axios.get(
      //   `${import.meta.env.VITE_ADMIN_BASE_URL}/get-api-keys-breakdown`,
      //   { params }
      // );

      const res= await apiClient.get("/get-api-keys-breakdown",params)
      setData(res.data|| []);
    } catch (err) {
      console.error("Error fetching API keys", err);
      toast.error(err?.response?.data?.message||"Failed to fetch API keys data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [activeTab, startDate, endDate]);

  // ✅ Safe text for Excel
  const safeText = (text) =>
    text?.length > 32000
      ? text.slice(0, 32000) + "... [TRUNCATED]"
      : text || "";

  // ✅ Export all APIs
  const handleExportAll = () => {
    if (!data.length) return toast.info("No data to export.");
    try {
      const rows = [];

      data.forEach((item) => {
        rows.push({
          "Menu Option": item.menu_option,
          "API Name": item.api_name,
          "API URL": item.api_url,
          "Hit Count": item.hit_count,
          "API Headers": JSON.stringify(item.api_headers, null, 2),
        });

        if (Array.isArray(item.hits)) {
          item.hits.forEach((hit, i) =>
            rows.push({
              "→ Hit #": i + 1,
              Timestamp: hit.timestamp,
              "User Request": safeText(hit.user_request),
              "API Response": safeText(hit.api_response),
            })
          );
        }
        rows.push({});
      });

      const ws = XLSX.utils.json_to_sheet(rows);
      const wb = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(wb, ws, "API Data");

      const buffer = XLSX.write(wb, { bookType: "xlsx", type: "array" });
      saveAs(
        new Blob([buffer], { type: "application/octet-stream" }),
        "api_data_with_hits.xlsx"
      );

      toast.success("✅ Exported all data");
    } catch (err) {
      console.error("Export error:", err);
      toast.error(err?.response?.data?.message||"Export failed");
    }
  };

  // ✅ Export single API
  const handleExportSingle = (item) => {
    try {
      const rows = [
        {
          "Menu Option": item.menu_option,
          "API Name": item.api_name,
          "API URL": item.api_url,
          "Hit Count": item.hit_count,
          "API Headers": JSON.stringify(item.api_headers, null, 2),
        },
      ];

      if (Array.isArray(item.hits)) {
        item.hits.forEach((hit, i) =>
          rows.push({
            "→ Hit #": i + 1,
            Timestamp: hit.timestamp,
            "User Request": safeText(hit.user_request),
            "API Response": safeText(hit.api_response),
          })
        );
      }

      const ws = XLSX.utils.json_to_sheet(rows);
      const wb = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(wb, ws, `${item.api_name}_Details`);
      const buffer = XLSX.write(wb, { bookType: "xlsx", type: "array" });
      saveAs(
        new Blob([buffer], { type: "application/octet-stream" }),
        `${item.api_name}_hits.xlsx`
      );

      toast.success("✅ Exported record");
    } catch (err) {
      console.error("Export error:", err);
      toast.error("Export failed");
    }
  };

  // ✅ Handle “View” click — ensures clean close/open behavior
  const handleViewUsage = (item, id) => {
    // ✅ Check first before doing anything
    if (!item.hits || !Array.isArray(item.hits) || item.hits.length === 0) {
      toast.info("No usage data available for this API.");
      return;
    }

    // ✅ If same modal open, toggle close
    if (usageModalOpen && activeUsageId === id) {
      setUsageModalOpen(false);
      setUsageList([]);
      setActiveUsageId(null);
    } else {
      // ✅ Always close old first for clean state
      setUsageModalOpen(false);
      setUsageList([]);
      setActiveUsageId(null);

      setTimeout(() => {
        setUsageList(item.hits);
        setActiveUsageId(id);
        setUsageModalOpen(true);
      }, 150);
    }
  };

  const columns = [
    { field: "menu_option", headerName: "Menu Option", flex: 1.2 },
    { field: "api_name", headerName: "API Name", flex: 1 },
    {
      field: "api_url",
      headerName: "API URL",
      flex: 1.5,
      renderCell: (params) => (
        <a
          href={params.value}
          target="_blank"
          rel="noreferrer"
          style={{ color: "#1976d2", textDecoration: "underline" }}
        >
          {params.value}
        </a>
      ),
    },
    { field: "hit_count", headerName: "Hit Count", flex: 0.6 },
    {
      field: "api_headers",
      headerName: "API Headers",
      flex: 1.2,
      renderCell: (params) => (
        <pre
          style={{
            whiteSpace: "pre-wrap",
            fontSize: "11px",
            color: "#444",
            overflow: "hidden",
            textOverflow: "ellipsis",
            maxHeight: "100px",
          }}
        >
          {JSON.stringify(params.value, null, 2)}
        </pre>
      ),
    },
    {
      field: "actions",
      headerName: "Actions",
      flex: 1,
      renderCell: (params) => (
        <Box display="flex" gap={1}>
          <IconButton color="primary" onClick={() => setSelected(params.row)}>
            <Edit fontSize="small" />
          </IconButton>
          <IconButton
            color="success"
            onClick={() => handleViewUsage(params.row, params.id)}
          >
            <Visibility fontSize="small" />
          </IconButton>
          <IconButton
            color="warning"
            onClick={() => handleExportSingle(params.row)}
          >
            <SaveAlt fontSize="small" />
          </IconButton>
        </Box>
      ),
    },
  ];

  return (
    <Box sx={{ p: 3 }}>
      {/* Filters */}
      <DateInteractions
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        startDate={startDate}
        setStartDate={setStartDate}
        endDate={endDate}
        setEndDate={setEndDate}
        isDatePickerOpen={isDatePickerOpen}
        setIsDatePickerOpen={setIsDatePickerOpen}
      />

      {/* Header + Export */}
      <Box
        display="flex"
        justifyContent="space-between"
        alignItems="center"
        mt={2}
        mb={2}
      >
        <Typography variant="h6" fontWeight="bold">
          API Keys Data
        </Typography>
        <Button
          variant="contained"
          color="primary"
          startIcon={<SaveAlt />}
          onClick={handleExportAll}
        >
          Export All
        </Button>
      </Box>

      {/* DataGrid */}
      {loading ? (
        <Box sx={{ display: "flex", justifyContent: "center", mt: 10 }}>
          <CircularProgress />
        </Box>
      ) : (
        <Box sx={{ height: 600, width: "100%" }}>
          <DataGrid
            rows={data.map((row, i) => ({ id: i + 1, ...row }))}
            columns={columns}
            disableRowSelectionOnClick
            pageSizeOptions={[5, 10, 20]}
            initialState={{
              pagination: { paginationModel: { pageSize: 10, page: 0 } },
            }}
            sx={{
              "& .MuiDataGrid-cell": {
                whiteSpace: "normal",
                lineHeight: "1.4em",
              },
              "& .MuiDataGrid-columnHeaders": { backgroundColor: "#f5f5f5" },
            }}
          />
        </Box>
      )}

      {/* Edit Modal */}
      <EditApiKeyModal
        open={!!selected}
        item={selected}
        onClose={() => setSelected(null)}
        onUpdated={fetchData}
      />

      {/* ✅ Usage Modal (your custom modal) */}
      <UsageModal
        open={usageModalOpen}
        onClose={() => {
          setUsageModalOpen(false);
          setUsageList([]);
          setActiveUsageId(null);
        }}
        usageList={usageList}
      />
    </Box>
  );
}