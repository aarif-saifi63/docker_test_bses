// export const formatDateTime = (dateStr) => {
//   if (!dateStr) return "—";
//   const date = new Date(dateStr);
//   return date.toLocaleString("en-IN", {
//     year: "numeric",
//     month: "short",
//     day: "numeric",
//     hour: "2-digit",
//     minute: "2-digit",
//   });
// };

// export const formatDateRange = (start, end) => {
//   if (!start && !end) return "—";

//   const format = (dateStr) =>
//     new Date(dateStr).toLocaleString("en-IN", {
//       weekday: "short",
//       day: "numeric",
//       month: "short",
//       year: "numeric",
//       hour: "2-digit",
//       minute: "2-digit",
//     });

//   return `${format(start)} → ${format(end)}`;
// };

// ✅ Safe date parser that handles both ISO and "Tue, 04 Nov 2025 14:34:00 GMT" formats
// const parseDate = (dateStr) => {
//   if (!dateStr) return null;

//   // Try parsing standard Date first
//   const parsed = Date.parse(dateStr);
//   if (!isNaN(parsed)) return new Date(parsed);

//   // Fallback if backend sends weird string format
//   try {
//     const parts = dateStr.split(" ");
//     if (parts.length >= 6) {
//       return new Date(dateStr);
//     }
//   } catch {
//     return null;
//   }

//   return null;
// };

// // ✅ Single date formatter
// export const formatDateTime = (dateStr) => {
//   const date = parseDate(dateStr);
//   if (!date) return "—";

//   return date.toLocaleString("en-IN", {
//     year: "numeric",
//     month: "short",
//     day: "numeric",
//     hour: "2-digit",
//     minute: "2-digit",
//     hour12: true, // show AM/PM
//   });
// };

// // ✅ Start → End range formatter
// export const formatDateRange = (start, end) => {
//   const startDate = parseDate(start);
//   const endDate = parseDate(end);

//   if (!startDate && !endDate) return "—";

//   const options = {
//     weekday: "short",
//     day: "numeric",
//     month: "short",
//     year: "numeric",
//     hour: "2-digit",
//     minute: "2-digit",
//     hour12: true,
//   };

//   const startStr = startDate
//     ? startDate.toLocaleString(options)
//     : "—";
//   const endStr = endDate
//     ? endDate.toLocaleString( options)
//     : "—";

//   return `${startStr} → ${endStr}`;
// };

// ✅ Parse backend GMT/ISO string safely
const parseDate = (dateStr) => {
  if (!dateStr) return null;
  const parsed = Date.parse(dateStr);
  return isNaN(parsed) ? null : new Date(parsed);
};

const parseDateIST = (dateStr) => {
  if (!dateStr) return null;
  
  // Handle IST timezone by replacing with numeric offset
  let normalizedDateStr = dateStr.replace(/\s+IST$/, ' +0530');
  
  const parsed = Date.parse(normalizedDateStr);
  return isNaN(parsed) ? null : new Date(parsed);
};
// ✅ Format single datetime as UTC (no timezone conversion)
export const formatDateTime = (dateStr) => {
  const date = parseDate(dateStr);
  if (!date) return "—";

  return date.toLocaleString("en-GB", {
    timeZone: "UTC",        
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hour12: true,           
  });
};


export const formatDateRange = (start, end) => {
  const startDate = parseDate(start);
  const endDate = parseDate(end);

  if (!startDate && !endDate) return "—";

  const options = {
    timeZone: "UTC",    
    weekday: "short",
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hour12: true,
  };

  const startStr = startDate
    ? startDate.toLocaleString("en-GB", options)
    : "—";
  const endStr = endDate
    ? endDate.toLocaleString("en-GB", options)
    : "—";

  return `${startStr} → ${endStr}`;
};


// ✅ Use local date formatting to avoid UTC shift
   export const formatLocalDate = (date) => {
      if (!date) return null;
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, "0");
      const day = String(date.getDate()).padStart(2, "0");
      return `${year}-${month}-${day}`;
    };

 // Format datetime in IST timezone
export const formatDateTimeIST = (dateStr) => {
  const date = parseDateIST(dateStr);  // ← Use parseDateIST instead of parseDate
  if (!date) return "—";

  return date.toLocaleString("en-IN", {
    timeZone: "Asia/Kolkata",
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hour12: true,
  });
};