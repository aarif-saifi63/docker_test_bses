import React, { useState } from "react";

import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  TextField,
     Box,
     IconButton ,
  Typography,
} from "@mui/material";
import {Trash2 } from "lucide-react";

const IntentDialog = ({
  open,
  setOpen,
  editingIntent,
  intentName,
  setIntentName,
  examples,
  setExamples,
  handleSubmit,
  handleAddExample,
  handleRemoveExample,
}) => {
  const [newExample, setNewExample] = useState("");

  return (
    <Dialog open={open} onClose={() => setOpen(false)} maxWidth="sm" fullWidth>
      <DialogTitle>
        {editingIntent ? "Edit Intent" : "Create New Intent"}
      </DialogTitle>
      <DialogContent>
        <form onSubmit={handleSubmit} style={{ marginTop: "10px" }}>
          <TextField
            label="Intent Name"
            value={intentName}
            onChange={(e) => setIntentName(e.target.value)}
            fullWidth
            margin="dense"
            required
          />

          <Box sx={{ mt: 2 }}>
            <label
              style={{
                display: "block",
                fontSize: "14px",
                fontWeight: 500,
                marginBottom: "6px",
                color: "#555",
              }}
            >
              Examples
            </label>

            <Box
              sx={{
                display: "flex",
                flexDirection: "column",
                gap: 1,
                maxHeight: 150,
                overflowY: "auto",
                border: "1px solid #ccc",
                borderRadius: "8px",
                padding: "8px",
                background: "#fafafa",
              }}
            >
              {examples.length > 0 ? (
                examples.map((ex, i) => (
                  <Box
                    key={i}
                    sx={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      background: "#e0f7fa",
                      borderRadius: "8px",
                      px: 2,
                      py: 0.5,
                    }}
                  >
                    <span style={{ color: "#006064" }}>{ex.text}</span>
                    <IconButton
                      size="small"
                      onClick={() => handleRemoveExample(i)}
                      sx={{
                        color: "#004d40",
                        "&:hover": { color: "red" },
                      }}
                    >
                      <Trash2 size={16} />
                    </IconButton>
                  </Box>
                ))
              ) : (
                <Typography
                  variant="body2"
                  sx={{ color: "#777", fontStyle: "italic" }}
                >
                  No examples added yet
                </Typography>
              )}
            </Box>

            <Box sx={{ display: "flex", gap: 1, mt: 1 }}>
              <TextField
                label="Add new example"
                variant="outlined"
                size="small"
                fullWidth
                value={newExample}
                onChange={(e) => setNewExample(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    handleAddExample(newExample);
                    setNewExample("");
                  }
                }}
              />
              <Button
                variant="contained"
                onClick={() => {
                  handleAddExample(newExample);
                  setNewExample("");
                }}
              >
                Add
              </Button>
            </Box>
          </Box>
        </form>
      </DialogContent>
      <DialogActions>
        <Button onClick={() => setOpen(false)}>Cancel</Button>
        <Button onClick={handleSubmit} variant="contained" color="primary">
          {editingIntent ? "Update" : "Create"}
        </Button>
      </DialogActions>
    </Dialog>
  );
};
export default IntentDialog;