// import { useState } from "react";
// import { toast } from "sonner";

// export default function RolePermissionsModal({ role, onClose, onSave }) {
//   // const [formData, setFormData] = useState({
//   //   ...role,
//   //   permissions: role.permissions || [],
//   // });

//   // ✅ Track "Select All" state
//   const [formData, setFormData] = useState(() => {
//     const defaultPermissions = (role.permissions || []).map((perm) => {
//       // Set dashboard-read and mis-report-read as default selected
//       if (perm.name === "dashboard-read" || perm.name === "mis-report-read") {
//         return { ...perm, has_permission: true };
//       }
//       return perm;
//     });

//     return {
//       ...role,
//       permissions: defaultPermissions,
//     };
//   });



//   const allSelected =
//     formData.permissions.length > 0 && formData.permissions.every((p) => p.has_permission);
//   const someSelected = formData.permissions.some((p) => p.has_permission);

//   // ✅ Toggle individual permission
//   const togglePermission = (permId) => {
//     setFormData((prev) => ({
//       ...prev,
//       permissions: prev.permissions.map((p) =>
//         p.id === permId ? { ...p, has_permission: !p.has_permission } : p
//       ),
//     }));
//   };

//   const handleSave = () => {
//     if (!formData.user_role_name.trim()) {
//       toast.error("Role name is required");
//       return;
//     }

//     if (!formData.permissions.some((p) => p.has_permission)) {
//       toast.error("Please select at least one permission");
//       return;
//     }

//     onSave(formData);
//   };

//   const toggleAllPermissions = () => {
//     const allChecked = formData.permissions.every((p) => p.has_permission);
//     const updatedPermissions = formData.permissions.map((p) => ({
//       ...p,
//       has_permission: !allChecked, // if all checked → uncheck all, else check all
//     }));
//     setFormData((prev) => ({ ...prev, permissions: updatedPermissions }));
//   };

//   return (
//     <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
//       <div className="bg-white rounded-lg shadow-xl w-full max-w-lg p-6 max-h-[90vh] overflow-y-auto">
//         <h2 className="text-xl font-semibold mb-4">
//           {role.user_role_id ? "Edit Role" : "Create Role"}
//         </h2>

//         {/* Role Name */}
//         <div className="mb-4">
//           <label className="block text-sm font-medium mb-1">Role Name</label>
//           <input
//             type="text"
//             value={formData.user_role_name}
//             onChange={(e) => setFormData({ ...formData, user_role_name: e.target.value })}
//             className="w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500"
//           />
//         </div>

//         {/* Permissions */}
//         <div className="border rounded-lg p-3 max-h-[300px] overflow-y-auto">
//           <div className="flex justify-between items-center mb-2">
//             <p className="text-sm font-medium text-gray-700">Permissions:</p>

//             {/* ✅ Check/Uncheck All Button */}
//             <button
//               onClick={() => {
//                 toggleAllPermissions();
//               }}
//               className="text-xs bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded"
//             >
//               {formData.permissions.every((p) => p.has_permission) ? "Uncheck All" : "Check All"}
//             </button>
//           </div>{" "}
//           {formData.permissions.length > 0 ? (
//             formData.permissions.map((perm) => (
//               <div key={perm.id} className="flex items-center justify-between border-b py-2">
//                 <span className="text-gray-700">{perm.name}</span>
//                 <input
//                   type="checkbox"
//                   checked={perm.has_permission}
//                   onChange={() => togglePermission(perm.id)}
//                   className="w-5 h-5 text-blue-600 cursor-pointer"
//                 />
//               </div>
//             ))
//           ) : (
//             <p className="text-sm text-gray-500 italic">No permissions available</p>
//           )}
//         </div>

//         {/* Buttons */}
//         <div className="mt-6 flex justify-end gap-3 border-t pt-4">
//           <button onClick={onClose} className="px-4 py-2 rounded-lg border border-gray-300">
//             Cancel
//           </button>
//           <button
//             onClick={handleSave}
//             className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
//           >
//             Save
//           </button>
//         </div>
//       </div>
//     </div>
//   );
// }



import { useState } from "react";
import { toast } from "sonner";
 
export default function RolePermissionsModal({ role, onClose, onSave }) {
  const [formData, setFormData] = useState(() => {
    const defaultPermissions = (role.permissions || []).map((perm) => {
      // Set dashboard-read and mis-report-read as default selected
      if (perm.name === "dashboard-read" || perm.name === "mis-report-read") {
        return { ...perm, has_permission: true };
      }
      return perm;
    });
 
    return {
      ...role,
      permissions: defaultPermissions,
    };
  });
 
  // ✅ Track "Select All" state
  const allSelected =
    formData.permissions.length > 0 && formData.permissions.every((p) => p.has_permission);
  const someSelected = formData.permissions.some((p) => p.has_permission);
 
  // ✅ Toggle individual permission
  const togglePermission = (permId) => {
    setFormData((prev) => ({
      ...prev,
      permissions: prev.permissions.map((p) => {
        // Prevent toggling dashboard-read and mis-report-read (keep them always selected)
        if (p.id === permId && (p.name === "dashboard-read" || p.name === "mis-report-read")) {
          return p;
        }
        return p.id === permId ? { ...p, has_permission: !p.has_permission } : p;
      }),
    }));
  };
 
  const handleSave = () => {
    if (!formData.user_role_name.trim()) {
      toast.error("Role name is required");
      return;
    }
 
    if (!formData.permissions.some((p) => p.has_permission)) {
      toast.error("Please select at least one permission");
      return;
    }
 
    onSave(formData);
  };
 
  const toggleAllPermissions = () => {
    const allChecked = formData.permissions.every((p) => p.has_permission);
    const updatedPermissions = formData.permissions.map((p) => {
      // Keep dashboard-read and mis-report-read always checked
      if (p.name === "dashboard-read" || p.name === "mis-report-read") {
        return { ...p, has_permission: true };
      }
      return {
        ...p,
        has_permission: !allChecked, // if all checked → uncheck all, else check all
      };
    });
    setFormData((prev) => ({ ...prev, permissions: updatedPermissions }));
  };
 
  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-lg p-6 max-h-[90vh] overflow-y-auto">
        <h2 className="text-xl font-semibold mb-4">
          {role.user_role_id ? "Edit Role" : "Create Role"}
        </h2>
 
        {/* Role Name */}
        <div className="mb-4">
          <label className="block text-sm font-medium mb-1">Role Name</label>
          <input
            type="text"
            value={formData.user_role_name}
            onChange={(e) => setFormData({ ...formData, user_role_name: e.target.value })}
            className="w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500"
          />
        </div>
 
        {/* Permissions */}
        <div className="border rounded-lg p-3 max-h-[300px] overflow-y-auto">
          <div className="flex justify-between items-center mb-2">
            <p className="text-sm font-medium text-gray-700">Permissions:</p>
 
            {/* ✅ Check/Uncheck All Button */}
            <button
              onClick={() => {
                toggleAllPermissions();
              }}
              className="text-xs bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded"
            >
              {formData.permissions.every((p) => p.has_permission) ? "Uncheck All" : "Check All"}
            </button>
          </div>{" "}
          {formData.permissions.length > 0 ? (
            formData.permissions.map((perm) => {
              const isFixed = perm.name === "dashboard-read" || perm.name === "mis-report-read";
              return (
                <div key={perm.id} className="flex items-center justify-between border-b py-2">
                  <span className={`${isFixed ? "text-gray-900 font-medium" : "text-gray-700"}`}>
                    {perm.name}
                  </span>
                  <input
                    type="checkbox"
                    checked={perm.has_permission}
                    onChange={() => togglePermission(perm.id)}
                    disabled={isFixed}
                    className={`w-5 h-5 ${isFixed ? "text-gray-400 cursor-not-allowed" : "text-blue-600 cursor-pointer"}`}
                  />
                </div>
              );
            })
          ) : (
            <p className="text-sm text-gray-500 italic">No permissions available</p>
          )}
        </div>
 
        {/* Buttons */}
        <div className="mt-6 flex justify-end gap-3 border-t pt-4">
          <button onClick={onClose} className="px-4 py-2 rounded-lg border border-gray-300">
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
          >
            Save
          </button>
        </div>
      </div>
    </div>
  );
}