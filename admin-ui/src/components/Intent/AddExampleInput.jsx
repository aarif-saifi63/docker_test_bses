
import React, { useState } from "react";
import { Box, Button, TextField } from "@mui/material";

const AddExampleInput = ({ examples, setExamples }) => {
  const [newExample, setNewExample] = useState("");

  const handleAdd = () => {
    if (!newExample.trim()) return;
    const currentList = examples
      .split(",")
      .map((ex) => ex.trim())
      .filter((ex) => ex);
    const updated = [...currentList, newExample.trim()];
    setExamples(updated.join(", "));
    setNewExample("");
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleAdd();
    }
  };

  return (
    <Box sx={{ display: "flex", gap: 1, mt: 1 }}>
      <TextField
        label="Add new example"
        variant="outlined"
        size="small"
        fullWidth
        value={newExample}
        onChange={(e) => setNewExample(e.target.value)}
        onKeyDown={handleKeyDown}
      />
      <Button variant="contained" onClick={handleAdd}>
        Add
      </Button>
    </Box>
  );
};
export default AddExampleInput;