// import React, { useState, useEffect, useCallback, useRef } from "react";
// import { Plus, Pencil, Trash2 } from "lucide-react";
// import apiClient from "../../services/apiClient";
// import UserModal from "../../components/UserManagement/UserModal";
// import { toast } from "sonner";

// export default function UserPage() {
//   const [users, setUsers] = useState([]);
//   const [roles, setRoles] = useState([]);
//   const [showModal, setShowModal] = useState(false);
//   const [editUser, setEditUser] = useState(null);
//   const [loadingUsers, setLoadingUsers] = useState(false);
//   const [loadingRoles, setLoadingRoles] = useState(false);
//   const observer = useRef();
//   const [page, setPage] = useState(1);
//   const [hasMore, setHasMore] = useState(true);

//   // Infinite scroll observer
//   const lastUserRef = useCallback(
//     (node) => {
//       if (loadingUsers) return;
//       if (observer.current) observer.current.disconnect();
//       observer.current = new IntersectionObserver((entries) => {
//         if (entries[0].isIntersecting && hasMore) {
//           setPage((prev) => prev + 1);
//         }
//       });
//       if (node) observer.current.observe(node);
//     },
//     [loadingUsers, hasMore]
//   );

//   // Fetch users
//   const fetchUsers = async (pageNum = 1) => {
//     try {
//       setLoadingUsers(true);
//       const result = await apiClient.get(`/users?page=${pageNum}&limit=10`);
//       if (result.status && result.data.length > 0) {
//         setUsers((prev) =>
//           pageNum === 1 ? result.data : [...prev, ...result.data]
//         );
//         setHasMore(pageNum < result.total_pages);
//       } else {
//         setHasMore(false);
//       }
//     } catch (err) {
//       console.error("Error fetching users:", err);
//       toast.error("Failed to fetch users");
//     } finally {
//       setLoadingUsers(false);
//     }
//   };

//   useEffect(() => {
//     fetchUsers(page);
//   }, [page]);

//   // Fetch roles
//   const fetchRoles = async () => {
//     try {
//       setLoadingRoles(true);
//       const res = await apiClient.get("/mappings");
//       if (res.status && res.data.length > 0) {
//         setRoles(res.data);
//       }
//     } catch (err) {
//       console.error("Error fetching roles:", err);
//       toast.error("Failed to fetch roles");
//     } finally {
//       setLoadingRoles(false);
//     }
//   };

//   useEffect(() => {
//     fetchRoles();
//   }, []);

//   // Add User handler
//   const handleAddUser = () => {
//     setEditUser(null);
//     setShowModal(true);
//   };

//   // Edit User handler
//   const handleEditUser = (user) => {
//     setEditUser(user);
//     setShowModal(true);
//   };

//   // Delete User handler
//   const handleDeleteUser = async (id) => {
//     if (window.confirm("Are you sure you want to delete this user?")) {
//       try {
//         await apiClient.delete(`/users/${id}`);
//         setUsers((prev) => prev.filter((user) => user.id !== id));
//         toast.success("User deleted successfully");
//         fetchUsers();
//         fetchRoles();
//       } catch (err) {
//         console.error("Error deleting user:", err);
//         toast.error("Failed to delete user");
//       }
//     }
//   };

//   // Save User handler
//   const handleSaveUser = async (user) => {
//     console.log("Saving user:", user);
//     try {
//       const method = user.user_role_id ? "PUT" : "POST";
//       const url = method === "PUT" ? "/user-mappings" : "/users/register";

//       const payload = {
//         ...user,
//         user_role_id: user.user_role_id || null,
//       };

//       const res = await apiClient[method.toLowerCase()](url, payload);

//       if (res.status) {
//         toast.success(
//           method === "POST"
//             ? "User created successfully"
//             : "User updated successfully"
//         );
//         setShowModal(false);
//         fetchRoles();
//         fetchUsers();
//       } else {
//         toast.warning("Error saving user: " + (res.message || "Unknown error"));
//       }
//     } catch (err) {
//       console.error("Error saving user:", err);
//       toast.error("Failed to save user");
//     }
//   };

//   // Map role_id to role_name
//   const getRoleName = (roleId) => {
//     const role = roles.find((r) => r.user_role_id === roleId);
//     return role ? role.user_role_name : "Unknown";
//   };

//   // Role badge
//   const RoleChip = ({ role }) => {
//     let chipColor = "bg-gray-300";
//     if (role === "Super Admin") chipColor = "bg-red-500";
//     else if (role === "Admin") chipColor = "bg-blue-500";
//     else if (role === "Supervisor") chipColor = "bg-green-500";
//     else if (role === "Developer") chipColor = "bg-purple-500";
//     else if (role === "Analyst") chipColor = "bg-yellow-500";

//     return (
//       <span
//         className={`inline-block px-3 py-1 text-sm font-semibold text-white rounded-full ${chipColor}`}
//       >
//         {role}
//       </span>
//     );
//   };

//   return (
//     <div className="p-6">
//       <div className="flex justify-between items-center mb-6">
//         <h1 className="text-2xl font-semibold">User Management</h1>
//         <button
//           onClick={handleAddUser}
//           className="flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700"
//         >
//           <Plus className="w-5 h-5" /> Add User
//         </button>
//       </div>

//       <div className="overflow-x-auto border border-gray-200 rounded-lg">
//         <table className="min-w-full text-sm">
//           <thead className="bg-gray-100">
//             <tr>
//               <th className="px-4 py-2 text-left">Name</th>
//               <th className="px-4 py-2 text-left">Email</th>
//               <th className="px-4 py-2 text-left">Role</th>
//               <th className="px-4 py-2 text-left">Permissions</th>
//               <th className="px-4 py-2 text-center">Actions</th>
//             </tr>
//           </thead>

//           <tbody>
//             {users.map((user, index) => {
//               const isLast = index === users.length - 1;
//               return (
//                 <tr
//                   key={user.id}
//                   ref={isLast ? lastUserRef : null}
//                   className="hover:bg-gray-50"
//                 >
//                   <td className="px-4 py-3 border-b font-medium">
//                     {user.name}
//                   </td>
//                   <td className="px-4 py-3 border-b">{user.email_id}</td>
//                   <td className="px-4 py-3 border-b">
//                     <RoleChip role={getRoleName(user.role_id)} />
//                   </td>

//                   {/* Permissions Section */}
//                   <td className="px-4 py-3 border-b">
//                     <div className="flex flex-col gap-2">
//                       {/* Role Permissions */}
//                       {user?.role_permissions?.length > 0 && (
//                         <div>
//                           <div className="text-xs text-gray-500 mb-1 font-semibold">
//                             Role Permissions:
//                           </div>
//                           <div className="flex flex-wrap gap-1">
//                             {user.role_permissions.map((perm) => (
//                               <span
//                                 key={`role-${perm.id}`}
//                                 className="bg-blue-100 text-blue-700 text-xs px-2 py-1 rounded-full border border-blue-300"
//                               >
//                                 {perm.permission_name}
//                               </span>
//                             ))}
//                           </div>
//                         </div>
//                       )}

//                       {/* User Permissions */}
//                       {user?.user_permissions?.length > 0 && (
//                         <div>
//                           <div className="text-xs text-gray-500 mb-1 font-semibold">
//                             User Permissions:
//                           </div>
//                           <div className="flex flex-wrap gap-1">
//                             {user.user_permissions.map((perm) => (
//                               <span
//                                 key={`user-${perm.id}`}
//                                 className="bg-green-100 text-green-700 text-xs px-2 py-1 rounded-full border border-green-300"
//                               >
//                                 {perm.permission_name}
//                               </span>
//                             ))}
//                           </div>
//                         </div>
//                       )}

//                       {/* Fallback */}
//                       {!user?.role_permissions?.length &&
//                         !user?.user_permissions?.length && (
//                           <span className="text-gray-400 text-sm">—</span>
//                         )}
//                     </div>
//                   </td>

//                   <td className="px-4 py-3 border-b text-center flex justify-center gap-2">
//                     <button
//                       onClick={() => handleEditUser(user)}
//                       className="text-blue-600 hover:text-blue-800"
//                     >
//                       <Pencil className="w-5 h-5" />
//                     </button>
//                     <button
//                       onClick={() => handleDeleteUser(user.id)}
//                       className="text-red-600 hover:text-red-800"
//                     >
//                       <Trash2 className="w-5 h-5" />
//                     </button>
//                   </td>
//                 </tr>
//               );
//             })}
//           </tbody>
//         </table>

//         {loadingUsers && (
//           <div className="p-4 text-center text-gray-500">Loading more...</div>
//         )}
//         {!hasMore && !loadingUsers && users.length > 0 && (
//           <div className="p-4 text-center text-gray-400 text-sm">
//             No more users
//           </div>
//         )}
//       </div>

//       {/* Add/Edit Modal */}
//       {showModal && (
//         <UserModal
//           roles={roles}
//           user={editUser}
//           onClose={() => setShowModal(false)}
//           onSave={handleSaveUser}
//         />
//       )}
//     </div>
//   );
// }

import React, { useState, useEffect, useCallback, useRef } from "react";
import { Plus, Pencil, Trash2 } from "lucide-react";
import apiClient from "../../services/apiClient";
import UserModal from "../../components/UserManagement/UserModal";
import { toast } from "sonner";
import { usePermission } from "../../hooks/usePermission";

export default function UserPage() {
  const [users, setUsers] = useState([]);
  const [roles, setRoles] = useState([]);
  const [showModal, setShowModal] = useState(false);
  const [editUser, setEditUser] = useState(null);
  const [loadingUsers, setLoadingUsers] = useState(false);
  const [loadingRoles, setLoadingRoles] = useState(false);
  const observer = useRef();
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);

  const { has } = usePermission();

  // Infinite scroll observer
  const lastUserRef = useCallback(
    (node) => {
      if (loadingUsers) return;
      if (observer.current) observer.current.disconnect();
      observer.current = new IntersectionObserver((entries) => {
        if (entries[0].isIntersecting && hasMore) {
          setPage((prev) => prev + 1);
        }
      });
      if (node) observer.current.observe(node);
    },
    [loadingUsers, hasMore]
  );

  // Fetch users
  const fetchUsers = async (pageNum = 1) => {
    try {
      setLoadingUsers(true);
      const result = await apiClient.get(`/users?page=${pageNum}&limit=10`);
      if (result.status && result.data.length > 0) {
        setUsers((prev) =>
          pageNum === 1 ? result.data : [...prev, ...result.data]
        );
        setHasMore(pageNum < result.total_pages);
      } else {
        setHasMore(false);
      }
    } catch (err) {
      console.error("Error fetching users:", err);
    } finally {
      setLoadingUsers(false);
    }
  };

  useEffect(() => {
    fetchUsers(page);
  }, [page]);

  // Fetch roles
  const fetchRoles = async () => {
    try {
      setLoadingRoles(true);
      const res = await apiClient.get("/user/mappings");
      if (res.status && res.data.length > 0) {
        setRoles(res.data);
      }
    } catch (err) {
      console.error("Error fetching roles:", err);
    } finally {
      setLoadingRoles(false);
    }
  };

  useEffect(() => {
    fetchRoles();
  }, []);

  // Add User handler
  const handleAddUser = () => {
    setEditUser(null);
    setShowModal(true);
  };

  // Edit User handler
  // const handleEditUser = (user) => {
  //   setEditUser(user);
  //   setShowModal(true);
  // };

  const handleEditUser = (user) => {
    try {
      if (!has("users-update")) {
        toast.error("You don't have permission to update users.");
        return;
      }

      // ✅ Open edit modal with user data
      setEditUser(user);
      setShowModal(true);

      // ✅ Success toast
      toast.success(`Editing user: ${user.name || user.username || "Unknown"}`);
    } catch (err) {
      console.error("Error opening edit modal:", err);
      toast.error("Failed to open edit user modal.");
    }
  };

  // Delete User handler
  const handleDeleteUser = async (id) => {
    if (window.confirm("Are you sure you want to delete this user?")) {
      try {
        if (!has("users-delete")) {
          toast.error("You don't have permission to delete users.");
          return; // Stop the save operation if no permission
        }

        await apiClient.delete(`/users/${id}`);
        setUsers((prev) => prev.filter((user) => user.id !== id));
        toast.success("User deleted successfully");
        fetchUsers(1);
      } catch (err) {
        console.error("Error deleting user:", err);
        toast.error("Failed to delete user");
      }
    }
  };

  // Save User handler
  // const handleSaveUser = async (user) => {
  //   try {
  //     const method = user.user_role_id ? "PUT" : "POST";
  //     const url = method === "PUT" ? "/user-mappings" : "/users/register";
  //     const payload = {
  //       ...user,
  //       user_role_id: user.user_role_id || null,
  //       user_details_id: editUser.id || null,
  //     };

  //     const res = await apiClient[method.toLowerCase()](url, payload);
  //     if (res.status) {
  //       toast.success(
  //         method === "POST"
  //           ? "User created successfully"
  //           : "User updated successfully"
  //       );
  //       setShowModal(false);
  //       fetchUsers(1);
  //     } else {
  //       toast.warning("Error saving user: " + (res.message || "Unknown error"));
  //     }
  //   } catch (err) {
  //     console.error("Error saving user:", err);
  //     toast.error("Failed to save user");
  //   }
  // };

  // Save User handler
  // const handleSaveUser = async (user) => {
  //   try {
  //     const method = editUser ? "PUT" : "POST";
  //     const url = method === "PUT" ? "/user-mappings" : "/users/register";

  //     const payload = {
  //       ...user,
  //       role_id: user.user_role_id || null,
  //     };

  //     if (editUser && editUser.id) {
  //       payload.user_details_id = editUser.id;
  //     }

  //     const res = await apiClient[method.toLowerCase()](url, payload);

  //     if (res.status) {
  //       toast.success(
  //         method === "POST" ? "User created successfully" : "User updated successfully"
  //       );
  //       setShowModal(false);
  //       fetchUsers(1);
  //     } else {
  //       toast.warning("Error saving user: " + (res.message || "Unknown error"));
  //     }
  //   } catch (err) {
  //     console.error("Error saving user:", err);
  //     toast.error("Failed to save user");
  //   }
  // };

  const handleSaveUser = async (user) => {
    try {
      const method = editUser ? "PUT" : "POST";
      const url = method === "PUT" ? "/user-mappings" : "/users/register";

      if (!has("users-create") && method === "POST") {
        toast.error("You don't have permission to create users.");
        return; // Stop the save operation if no permission
      }

      if (!has("users-update") && method === "PUT") {
        toast.error("You don't have permission to update users.");
        return; // Stop the save operation if no permission
      }

      const payload = {
        ...user,
        role_id: user.user_role_id || null,
      };

      if (editUser && editUser.id) {
        payload.user_details_id = editUser.id;
      }

      const res = await apiClient[method.toLowerCase()](url, payload);

      if (res.status) {
        toast.success(
          method === "POST"
            ? "User created successfully"
            : "User updated successfully"
        );
        setShowModal(false);
        fetchUsers(1);
      } else {
        toast.warning("Error saving user: " + (res.message || "Unknown error"));
      }
    } catch (err) {
      console.error("Error saving user:", err);
      toast.error( err?.response?.data?.message ||"Failed to save user!");
    }
  };

  // Map role_id to role_name
  const getRoleName = (roleId) => {
    const role = roles.find((r) => r.user_role_id === roleId);
    return role ? role.user_role_name : "Unknown";
  };

  // Role badge component
  const RoleChip = ({ role }) => {
    let chipColor = "bg-gray-300";
    if (role === "Super Admin") chipColor = "bg-red-500";
    else if (role === "Admin") chipColor = "bg-blue-500";
    else if (role === "Supervisor") chipColor = "bg-green-500";
    else if (role === "Developer") chipColor = "bg-purple-500";
    else if (role === "Analyst") chipColor = "bg-yellow-500";

    return (
      <span
        className={`inline-block px-3 py-1 text-sm font-semibold text-white rounded-full ${chipColor}`}
      >
        {role}
      </span>
    );
  };

  const handleCheckPermission = (permission) => {
    if (!has(permission)) {
      toast.error(
        `You don't have permission to access this resource contact your administrator`
      );
    }
  };

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-semibold">User Management</h1>
        <button
          onClick={handleAddUser}
          disabled={!has("users-create")}
          title={
            !has("users-create")
              ? "You don't have permission to create users."
              : ""
          }
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700"
        >
          <Plus className="w-5 h-5" /> Add User
        </button>
      </div>

      <div className="overflow-x-auto border border-gray-200 rounded-lg">
        <table className="min-w-full text-sm">
          <thead className="bg-gray-100">
            <tr>
              <th className="px-4 py-2 text-left">Name</th>
              <th className="px-4 py-2 text-left">Email</th>
              <th className="px-4 py-2 text-left">Role</th>
              <th className="px-4 py-2 text-left">Permissions</th>
              <th className="px-4 py-2 text-center">Actions</th>
            </tr>
          </thead>

          <tbody>
            {users.map((user, index) => {
              const isLast = index === users.length - 1;
              return (
                <tr
                  key={user.id}
                  ref={isLast ? lastUserRef : null}
                  className="hover:bg-gray-50"
                >
                  <td className="px-4 py-3 border-b font-medium">
                    {user.name}
                  </td>
                  <td className="px-4 py-3 border-b">{user.email_id}</td>
                  <td className="px-4 py-3 border-b">
                    <RoleChip role={getRoleName(user.role_id)} />
                  </td>

                  {/* Permissions */}
                  <td className="px-4 py-3 border-b">
                    <div className="flex flex-col gap-2">
                      {/* Role Permissions */}
                      {user?.role_permissions?.length > 0 && (
                        <div>
                          <div className="text-xs text-gray-500 mb-1 font-semibold">
                            Role Permissions:
                          </div>
                          <div className="flex flex-wrap gap-1">
                            {user.role_permissions.map((perm) => (
                              <span
                                key={`role-${perm.id}`}
                                className="bg-blue-100 text-blue-700 text-xs px-2 py-1 rounded-full border border-blue-300"
                              >
                                {perm.permission_name}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* User Permissions */}
                      {user?.user_permissions?.length > 0 && (
                        <div>
                          <div className="text-xs text-gray-500 mb-1 font-semibold">
                            User Permissions:
                          </div>
                          <div className="flex flex-wrap gap-1">
                            {user.user_permissions.map((perm) => (
                              <span
                                key={`user-${perm.id}`}
                                className="bg-green-100 text-green-700 text-xs px-2 py-1 rounded-full border border-green-300"
                              >
                                {perm.permission_name}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* No permissions */}
                      {!user?.role_permissions?.length &&
                        !user?.user_permissions?.length && (
                          <span className="text-gray-400 text-sm">—</span>
                        )}
                    </div>
                  </td>

                  {/* Actions */}
                  <td className="px-4 py-3 border-b text-center flex justify-center gap-2">
                    <button
                      onClick={() => handleEditUser(user)}
                      className="text-blue-600 hover:text-blue-800"
                      // disabled={!has("users-update")}
                      title={
                        !has("users-update")
                          ? "You don't have permission to update users."
                          : ""
                      }
                    >
                      <Pencil className="w-5 h-5" />
                    </button>
                    <button
                      onClick={() => handleDeleteUser(user.id)}
                      disabled={!has("users-delete")}
                      title={
                        !has("users-delete")
                          ? "You don't have permission to delete users."
                          : ""
                      }
                      className="text-red-600 hover:text-red-800"
                    >
                      <Trash2 className="w-5 h-5" />
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>

        {loadingUsers && (
          <div className="p-4 text-center text-gray-500">Loading more...</div>
        )}
        {!hasMore && !loadingUsers && users.length > 0 && (
          <div className="p-4 text-center text-gray-400 text-sm">
            No more users
          </div>
        )}
      </div>

      {/* Modal */}
      {showModal && (
        <UserModal
          roles={roles}
          user={editUser}
          onClose={() => setShowModal(false)}
          onSave={handleSaveUser}
          loadingRoles={loadingRoles}
        />
      )}
    </div>
  );
}
