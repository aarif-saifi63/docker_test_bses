import React, { useState, useEffect, useRef, useCallback } from "react";
import { Plus, Pencil, Trash2, Shield } from "lucide-react";
import RolePermissionsModal from "../../components/UserManagement/RolePermissionsModal";
import apiClient from "../../services/apiClient";
import { toast } from "sonner";
import { usePermission } from "../../hooks/usePermission";

export default function RolesPage() {
  const [roles, setRoles] = useState([]);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [loading, setLoading] = useState(false);
  const [loadingPermissions, setLoadingPermissions] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [editRole, setEditRole] = useState(null);

  const observer = useRef();

  const { has } = usePermission();

  // Infinite scroll observer
  const lastRoleRef = useCallback(
    (node) => {
      if (loading) return;
      if (observer.current) observer.current.disconnect();
      observer.current = new IntersectionObserver((entries) => {
        if (entries[0].isIntersecting && hasMore) {
          setPage((prev) => prev + 1);
        }
      });
      if (node) observer.current.observe(node);
    },
    [loading, hasMore]
  );

  // Fetch paginated roles from backend
  const fetchRoles = async (pageNum = 1) => {
    try {
      setLoading(true);
      const result = await apiClient.get(`/role/mappings?page=${pageNum}&limit=10`);

      if (result.status && result.data.length > 0) {
        setRoles((prev) => (pageNum === 1 ? result.data : [...prev, ...result.data]));
        setHasMore(pageNum < result.total_pages);
      } else {
        setHasMore(false);
      }
    } catch (err) {
      console.error("Error fetching roles:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRoles(page);
  }, [page]);

  // Handle Add Role (fetch permissions)
  const handleAddRole = async () => {
    try {
      if (!has("users-create")) {
        toast.error("You don't have permission to create roles.");
        return; // Stop the save operation if no permission
      }

      setLoadingPermissions(true);
      const res = await apiClient.get("/role/permissions");
      if (res.status && res.data?.length) {
        const permissions = res.data.map((p) => ({
          id: p.id,
          name: p.permission_name,
          has_permission: false,
        }));

        setEditRole({
          user_role_id: null,
          user_role_name: "",
          permissions,
        });
        setShowModal(true);
        fetchRoles();
      } else {
        toast.error("Failed to fetch permissions list.");
      }
    } catch (err) {
      console.error("Error fetching permissions:", err);
      toast.error("Failed to fetch permissions");
    } finally {
      setLoadingPermissions(false);
    }
  };

  const handleEditRole = (role) => {
    if (!has("roles-update")) {
      toast.error("You don't have permission to update roles.");
      return; // Stop the save operation if no permission
    }
    
    setEditRole(role);
    setShowModal(true);
  };

  const handleDeleteRole = async (id) => {
    if (!window.confirm("Are you sure you want to delete this role?")) return;
    try {
      if (!has("users-delete")) {
        toast.error("You don't have permission to delete roles.");
        return; // Stop the save operation if no permission
      }

      setLoading(true);
      await apiClient.delete(`/delete/role/${id}`, { method: "DELETE" });
      setRoles((prev) => prev.filter((r) => r.user_role_id !== id));
      fetchRoles();
      toast.success("Role deleted successfully");
    } catch (err) {
      console.error("Error deleting role:", err);
      toast.error("Failed to delete role");
    } finally {
      setLoading(false);
    }
  };

  const handleSaveRole = async (savedRole) => {
    try {
      setLoading(true);
      const isUpdate = !!savedRole.user_role_id;

      let data;

      if (isUpdate) {
        const url = `/update/mappings/${savedRole.user_role_id}`;
        data = await apiClient.put(url, savedRole);
      } else {
        const requestBody = {
          permissions: savedRole.permissions,
          role_name: savedRole.user_role_name,
        };
        data = await apiClient.post("/role/create", requestBody);
      }

      if (data.status) {
        setShowModal(false);
        fetchRoles();
        toast.success(data?.message||"Role saved successfully");
      } else {
        alert("Failed to save role: " + (data.message || "Unknown error"));
      }
    } catch (err) {
      console.error("Error saving role:", err);
      toast.error( err?.response?.data?.message ||"Failed to save role!");
    } finally {
      setLoading(false);
    }
  };

 

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-semibold flex items-center gap-2">
          <Shield className="w-6 h-6 text-blue-600" /> Role Management
        </h1>
        <button
          onClick={handleAddRole}
          disabled={loadingPermissions}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-white ${
            loadingPermissions ? "bg-blue-400 cursor-not-allowed" : "bg-blue-600 hover:bg-blue-700"
          }`}
        >
          {loadingPermissions ? (
            <span>Loading...</span>
          ) : (
            <>
              <Plus className="w-5 h-5" /> Add Role
            </>
          )}
        </button>
      </div>

      {/* Table */}
      <div className="overflow-x-auto border border-gray-200 rounded-lg">
        <table className="min-w-full text-sm">
          <thead className="bg-gray-100">
            <tr>
              <th className="px-4 py-2 text-left border-b">Role Name</th>
              <th className="px-4 py-2 text-left border-b">Permissions</th>
              <th className="px-4 py-2 text-center border-b">Actions</th>
            </tr>
          </thead>
          <tbody>
            {roles.map((role, index) => {
              const isLast = index === roles.length - 1;
              return (
                <tr
                  key={role.user_role_id}
                  ref={isLast ? lastRoleRef : null}
                  className="hover:bg-gray-50"
                >
                  <td className="px-4 py-3 border-b font-medium">{role.user_role_name}</td>
                  <td className="px-4 py-3 border-b">
                    <div className="flex flex-wrap gap-2">
                      {role.permissions
                        .filter((p) => p.has_permission)
                        .map((perm) => (
                          <span
                            key={perm.id}
                            className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded-full"
                          >
                            {perm.name}
                          </span>
                        ))}
                    </div>
                  </td>
                  <td className="px-4 py-3 border-b text-center flex justify-center gap-2">
                    <button
                      onClick={() => handleEditRole(role)}
                      className="text-blue-600 hover:text-blue-800"
                    >
                      <Pencil className="w-5 h-5" />
                    </button>
                    <button
                      onClick={() => handleDeleteRole(role.user_role_id)}
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

        {loading && <div className="p-4 text-center text-gray-500">Loading more...</div>}
        {!hasMore && !loading && roles.length > 0 && (
          <div className="p-4 text-center text-gray-400 text-sm">No more roles</div>
        )}
      </div>

      {/* Modal */}
      {showModal && (
        <RolePermissionsModal
          role={editRole}
          onClose={() => setShowModal(false)}
          onSave={handleSaveRole}
        />
      )}
    </div>
  );
}
