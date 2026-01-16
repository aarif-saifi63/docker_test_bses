import React, { useEffect, useState } from "react";
import apiClient from "../../../services/apiClient";
import {
  Box,
  Button,
  CircularProgress,
  MenuItem,
  Select,
  Typography,
  Paper,
  Table,
  TableHead,
  TableRow,
  TableCell,
  TableBody,
  Pagination,
  Modal,
} from "@mui/material";
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";
import { toast } from "sonner";
import * as XLSX from "xlsx";
import { saveAs } from "file-saver";
import { Download } from "lucide-react";
import { formatLocalDate } from "../../../utils/time";

export default function Advertisement() {
  const [ads, setAds] = useState([]);
  const [selectedAd, setSelectedAd] = useState(null);
  const [startDate, setStartDate] = useState(null);
  const [endDate, setEndDate] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(false);
  const [loadingAds, setLoadingAds] = useState(false);
  const [page, setPage] = useState(1);

  // ✅ NEW: Modal state for Total Count timestamps
  const [openModal, setOpenModal] = useState(false);
  const [openDivisionModal, setOpenDivisionModal] = useState(false);

  const fetchAds = async () => {
    setLoadingAds(true);
    try {
      const res = await apiClient.get("/ads/get-ads");
      setAds(res.data || []);
    } catch (err) {
      toast.error(err?.response?.data?.error || "Failed to load ads list");
    } finally {
      setLoadingAds(false);
    }
  };

  useEffect(() => {
    fetchAds();
  }, []);

  const fetchAnalytics = async (pageNum = 1) => {
    if (!selectedAd) return toast.error("Please select an advertisement.");
    if (!startDate || !endDate) return toast.error("Please select both start and end dates.");

    setLoading(true);
    try {
      const params = {
        ad_id: selectedAd.id,
        start_date: formatLocalDate(startDate),
        end_date: formatLocalDate(endDate),
        page: pageNum,
      };

      const res = await apiClient.get("/get-ad-analytics", params);
      setAnalytics(res.data || {});
    } catch (err) {
      toast.error(err?.response?.data?.message || "Failed to fetch analytics");
    } finally {
      setLoading(false);
    }
  };

  const handlePageChange = (_, value) => {
    setPage(value);
    fetchAnalytics(value);
  };

  const handleExportExcel = () => {
    if (!analytics) return toast.error("No analytics data to export!");

    const wb = XLSX.utils.book_new();
    const insightsData = [
      ["Field", "Value"],
      ["Divisions Involved", analytics.insights?.divisions_involved ?? 0],
      ["Top Division", analytics.insights?.top_division ?? "-"],
      ["Unique CA Numbers", analytics.insights?.unique_ca_numbers ?? 0],
      ["Total Count", analytics.insights?.total_count ?? 0],
      ["New Users", analytics.insights?.new_users ?? 0],
      ["Registered Users", analytics.insights?.registered_users ?? 0],
      ["Top User", analytics.insights?.top_user ?? "-"],
      ["Unique Users", analytics.insights?.unique_users ?? 0],
    ];
    const insightsSheet = XLSX.utils.aoa_to_sheet(insightsData);
    XLSX.utils.book_append_sheet(wb, insightsSheet, "Insights");

    const logs = analytics.tracker_logs || [];
    const logsData = logs.map((log) => ({
      "User Type": log.user_type || "-",
      "CA Number": log.ca_number || "-",
      Division: log.division_name || "-",
      "Tel No": log.tel_no || "-",
      "User ID": log.user_id || "-",
      Timestamp: new Date(log.timestamp).toLocaleString(),
    }));

    const logsSheet = XLSX.utils.json_to_sheet(logsData);
    XLSX.utils.book_append_sheet(wb, logsSheet, "Tracker Logs");

    const fileName = `${selectedAd?.ad_name || "Advertisement"}_Analytics.xlsx`;
    const wbout = XLSX.write(wb, { bookType: "xlsx", type: "array" });
    saveAs(new Blob([wbout], { type: "application/octet-stream" }), fileName);
  };

  const handleOpenModal = () => {
    if (!analytics?.tracker_logs?.length) {
      toast.error("No tracker logs available.");
      return;
    }
    setOpenModal(true);
  };

  const handleOpenDivisionModal = () => {
    if (!analytics?.division_breakdown || Object.keys(analytics.division_breakdown).length === 0) {
      toast.error("No division breakdown data available.");
      return;
    }
    setOpenDivisionModal(true);
  };

  return (
    <Box sx={{ p: 3, backgroundColor: "#fafafa", minHeight: "100vh" }}>
      <Typography variant="h5" fontWeight="bold" mb={3}>
        📊 Advertisement Analytics
      </Typography>

      {/* Header Filters */}
      <Paper
        sx={{
          p: 3,
          mb: 3,
          display: "flex",
          flexWrap: "wrap",
          gap: 2,
          alignItems: "center",
        }}
      >
        <Box>
          <Typography variant="subtitle2" color="text.secondary" mb={0.5}>
            Select Advertisement
          </Typography>
          <Select
            value={selectedAd?.id || ""}
            onChange={(e) => {
              const ad = ads.find((a) => a.id === e.target.value);
              setSelectedAd(ad);
              setAnalytics(null);
            }}
            displayEmpty
            sx={{ minWidth: 250, backgroundColor: "#fff" }}
          >
            <MenuItem value="">-- Select Ad --</MenuItem>
            {ads.map((ad) => (
              <MenuItem key={ad.id} value={ad.id}>
                {ad.ad_name}
              </MenuItem>
            ))}
          </Select>
        </Box>

        <Box>
          <Typography variant="subtitle2" color="text.secondary" mb={0.5}>
            Start Date
          </Typography>
          <DatePicker
            selected={startDate}
            onChange={(date) => setStartDate(date)}
            maxDate={new Date()}
            placeholderText="Select start date"
            className="border border-gray-300 rounded-md px-3 py-1 bg-white"
          />
        </Box>

        <Box>
          <Typography variant="subtitle2" color="text.secondary" mb={0.5}>
            End Date
          </Typography>
          <DatePicker
            selected={endDate}
            onChange={(date) => setEndDate(date)}
            minDate={startDate}
            maxDate={new Date()}
            placeholderText="Select end date"
            className="border border-gray-300 rounded-md px-3 py-1 bg-white"
          />
        </Box>

        <Button
          variant="contained"
          color="primary"
          onClick={() => fetchAnalytics(1)}
          sx={{ height: "40px", mt: 3 }}
        >
          {loading ? "Loading..." : "Fetch Analytics"}
        </Button>
      </Paper>

      {/* Summary */}
      {loading && (
        <Box sx={{ display: "flex", justifyContent: "center", mt: 10 }}>
          <CircularProgress />
        </Box>
      )}

      {!loading && analytics && analytics.insights && (
        <Box>
          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" fontWeight="bold" mb={2}>
              Insights for <span style={{ color: "#1976d2" }}>{selectedAd?.ad_name}</span>
            </Typography>
            <Box sx={{ display: "flex", flexWrap: "wrap", gap: 3 }}>
              {/* <SummaryCard
                label="Divisions Involved"
                value={analytics.insights.divisions_involved}
              /> */}
              <SummaryCard
                label="Divisions Involved"
                value={analytics.insights.divisions_involved}
                onClick={handleOpenDivisionModal}
                clickable
              />

              <SummaryCard label="Top Division" value={analytics.insights.top_division} />
              <SummaryCard label="Unique CA Numbers" value={analytics.insights.unique_ca_numbers} />

              <SummaryCard
                label="Total Count"
                value={analytics.insights.total_count}
                onClick={handleOpenModal}
                clickable
              />
            </Box>
          </Paper>

          {/* ✅ Export button */}
          <Box sx={{ display: "flex", justifyContent: "flex-end", mb: 2 }}>
            <button
              onClick={handleExportExcel}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg shadow hover:bg-blue-700 transition"
              disabled={!analytics?.tracker_logs?.length}
            >
              <Download className="w-4 h-4" /> Export to Excel
            </button>
          </Box>

          {/* ✅ Hide Tracker Logs if ad_type is on_chatbot_launch */}
          {selectedAd?.ad_type !== "on_chatbot_launch" && (
            <Paper sx={{ p: 2 }}>
              <Typography variant="subtitle1" fontWeight="bold" mb={2}>
                Tracker Logs
              </Typography>
              <Table size="small">
                <TableHead sx={{ backgroundColor: "#f4f6f8" }}>
                  <TableRow>
                    <TableCell>User Type</TableCell>
                    <TableCell>CA Number</TableCell>
                    <TableCell>Division</TableCell>
                    <TableCell>Tel No</TableCell>
                    {/* <TableCell>User ID</TableCell> */}
                    <TableCell>Timestamp</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {analytics.tracker_logs?.length > 0 ? (
                    analytics.tracker_logs.map((log, idx) => (
                      <TableRow key={idx} hover>
                        <TableCell>{log.user_type || "N/A"}</TableCell>
                        <TableCell>{log.ca_number || "-"}</TableCell>
                        <TableCell>{log.division_name || "-"}</TableCell>
                        <TableCell>{log.tel_no || "-"}</TableCell>
                        {/* <TableCell>{log.user_id || "-"}</TableCell> */}
                        <TableCell>{new Date(log.timestamp).toLocaleString()}</TableCell>
                      </TableRow>
                    ))
                  ) : (
                    <TableRow>
                      <TableCell colSpan={6} align="center">
                        No tracker logs found.
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>

              {analytics.pagination?.total_pages > 1 && (
                <Box sx={{ display: "flex", justifyContent: "center", mt: 2 }}>
                  <Pagination
                    count={analytics.pagination.total_pages}
                    page={page}
                    onChange={handlePageChange}
                    color="primary"
                    shape="rounded"
                  />
                </Box>
              )}
            </Paper>
          )}
        </Box>
      )}

      {/* ✅ NEW: Modal for timestamps */}
      <Modal open={openModal} onClose={() => setOpenModal(false)}>
        <Box
          sx={{
            position: "absolute",
            top: "50%",
            left: "50%",
            transform: "translate(-50%, -50%)",
            bgcolor: "white",
            p: 3,
            borderRadius: 2,
            width: 400,
            maxHeight: "70vh",
            overflowY: "auto",
            boxShadow: 24,
          }}
        >
          <Typography variant="h6" fontWeight="bold" mb={2}>
            🕒 Tracker Log Timestamps
          </Typography>

          {analytics?.tracker_logs?.length > 0 ? (
            analytics.tracker_logs.map((log, idx) => (
              <Typography
                key={idx}
                variant="body2"
                sx={{
                  borderBottom: "1px solid #eee",
                  py: 0.5,
                  fontFamily: "monospace",
                }}
              >
                {new Date(log.timestamp).toLocaleString()}
              </Typography>
            ))
          ) : (
            <Typography>No records found.</Typography>
          )}

          <Box sx={{ textAlign: "right", mt: 2 }}>
            <Button variant="contained" onClick={() => setOpenModal(false)}>
              Close
            </Button>
          </Box>
        </Box>
      </Modal>

      {/* ✅ NEW: Modal for Division Breakdown */}
      <Modal open={openDivisionModal} onClose={() => setOpenDivisionModal(false)}>
        <Box
          sx={{
            position: "absolute",
            top: "50%",
            left: "50%",
            transform: "translate(-50%, -50%)",
            bgcolor: "white",
            p: 3,
            borderRadius: 2,
            width: 400,
            maxHeight: "70vh",
            overflowY: "auto",
            boxShadow: 24,
          }}
        >
          <Typography variant="h6" fontWeight="bold" mb={2}>
            🏢 Division Breakdown
          </Typography>

          {analytics?.division_breakdown && Object.keys(analytics.division_breakdown).length > 0 ? (
            Object.entries(analytics.division_breakdown).map(([division, count], idx) => (
              <Box
                key={idx}
                sx={{
                  display: "flex",
                  justifyContent: "space-between",
                  borderBottom: "1px solid #eee",
                  py: 0.5,
                }}
              >
                <Typography variant="body2" sx={{ fontWeight: 500 }}>
                  {division}
                </Typography>
                <Typography variant="body2" color="primary">
                  {count}
                </Typography>
              </Box>
            ))
          ) : (
            <Typography>No division data available.</Typography>
          )}

          <Box sx={{ textAlign: "right", mt: 2 }}>
            <Button variant="contained" onClick={() => setOpenDivisionModal(false)}>
              Close
            </Button>
          </Box>
        </Box>
      </Modal>
    </Box>
  );
}

// ✅ Reusable SummaryCard with optional click
function SummaryCard({ label, value, onClick, clickable }) {
  return (
    <Paper
      elevation={1}
      sx={{
        flex: "1 1 200px",
        p: 2,
        borderRadius: 2,
        textAlign: "center",
        backgroundColor: clickable ? "#e3f2fd" : "#f9fafb",
        cursor: clickable ? "pointer" : "default",
        "&:hover": clickable ? { backgroundColor: "#bbdefb" } : {},
      }}
      onClick={clickable ? onClick : undefined}
    >
      <Typography variant="body2" color="text.secondary">
        {label}
      </Typography>
      <Typography variant="h6" fontWeight="bold" color="primary">
        {value ?? "-"}
      </Typography>
    </Paper>
  );
}