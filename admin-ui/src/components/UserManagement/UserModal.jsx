import React, { useState, useEffect } from "react";
import apiClient from "../../services/apiClient";
import { toast } from "sonner";

export default function UserModal({
  user,
  onClose,
  onSave,
  roles,
  loadingRoles,
}) {
  const [formData, setFormData] = useState({
    email_id: "",
    password: "",
    confirm_password: "",
    role_id: 1,
    name: "",
    role_permissions: [],
    user_permissions: [],
  });

  // full permissions list from API
  const [permissionsData, setPermissionsData] = useState([]);

  // initialize form data when editing user
  useEffect(() => {
    if (user) {
      setFormData({
        email_id: user.email_id || "",
        password: "",
        confirm_password: "",
        role_id: user.role_id || 1,
        name: user.name || "",
        role_permissions: (user.role_permissions || []).map((p) => ({
          id: p.id,
          permission_name: p.permission_name,
          has_permission: true,
        })),
        user_permissions: [],
      });
    }
  }, [user]);

  // fetch permissions from backend and mark those already assigned to the user
  const fetchPermissions = async () => {
    try {
      const res = await apiClient.get("/user/permissions");
      const data = res.data; // axios wraps it inside .data

      if (data) {
        const allPerms = data?.map((perm) => {
          const hasPermission = user?.user_permissions?.some(
            (up) => up.id === perm.id
          );
          return {
            id: perm.id,
            permission_name: perm.permission_name,
            has_permission: hasPermission || false,
          };
        });

        setPermissionsData(allPerms);
        setFormData((prev) => ({ ...prev, user_permissions: allPerms }));
      } else {
        toast.error("No permissions found from API");
      }
    } catch (err) {
      console.error("Error fetching permissions:", err);
      toast.error("Failed to fetch permissions");
    }
  };

  useEffect(() => {
    fetchPermissions();
  }, [user]);

  const handleChange = (e) => {
    const { name, value } = e.target;

    if (name === "role_id") {
      const selectedRole = roles.find((r) => r.user_role_id === Number(value));

      setFormData((prev) => ({
        ...prev,
        role_id: Number(value),
        role_permissions: selectedRole
          ? selectedRole.permissions?.map((p) => ({
              id: p.id,
              permission_name: p.name,
              has_permission:  p.has_permission,
            })) || []
          : [],
      }));
    } else {
      setFormData((prev) => ({ ...prev, [name]: value }));
    }
  };

  const togglePermission = (permId) => {
    setFormData((prev) => ({
      ...prev,
      user_permissions: prev.user_permissions.map((p) =>
        p.id === permId ? { ...p, has_permission: !p.has_permission } : p
      ),
    }));
  };

  const toggleAllPermissions = () => {
    const allChecked = formData.user_permissions.every((p) => p.has_permission);
    setFormData((prev) => ({
      ...prev,
      user_permissions: prev.user_permissions.map((p) => ({
        ...p,
        has_permission: !allChecked,
      })),
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    const isNew = !user;

    // --- Base field validation ---
    if (!formData.role_id) {
      toast.error("User role is required!");
      return;
    }

    if (
      !Array.isArray(formData.role_permissions) ||
      formData.role_permissions.length === 0
    ) {
      toast.error("Role permissions are required!");
      return;
    }

    if (
      !Array.isArray(formData.user_permissions) ||
      formData.user_permissions.length === 0
    ) {
      toast.error("User permissions are required!");
      return;
    }

    // --- Validation for new user creation ---
    if (isNew) {
      if (!formData.name?.trim()) {
        toast.error("Name is required!");
        return;
      }

      if (!formData.email_id?.trim()) {
        toast.error("Email is required!");
        return;
      }

      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(formData.email_id.trim())) {
        toast.error("Invalid email format!");
        return;
      }

      if (!formData.password?.trim()) {
        toast.error("Password is required!");
        return;
      }

      if (formData.password.trim().length < 6) {
        toast.error("Password must be at least 6 characters long!");
        return;
      }

      if (!formData.confirm_password?.trim()) {
        toast.error("Confirm password is required!");
        return;
      }

      if (formData.password !== formData.confirm_password) {
        toast.error("Passwords do not match!");
        return;
      }
    }

    // --- Payload preparation ---
    const payload = {
      user_role_id: Number(formData.role_id),
      role_permissions: formData.role_permissions.map((p) => ({
        id: p.id,
        has_permission: p.has_permission,
      })),
      user_permissions: formData.user_permissions.map((p) => ({
        id: p.id,
        has_permission: p.has_permission,
      })),
    };

    // Include only for new user creation
    if (isNew) {
      payload.name = formData.name.trim();
      payload.email_id = formData.email_id.trim();
      payload.password = formData.password.trim();
      payload.confirm_password = formData.confirm_password.trim();
    }

    // --- Submit ---
    onSave(payload);
  };

  return (
    <div className="fixed inset-0 bg-gray-800 bg-opacity-50 flex justify-center items-center z-50">
      <div className="bg-white p-6 rounded-lg w-96">
        <h2 className="text-xl font-semibold mb-4">
          {user ? "Edit User" : "Add User"}
        </h2>

        <form onSubmit={handleSubmit}>
          {/* name/email */}
          <div className="mb-4">
            <label className="block text-sm font-medium mb-1">Name</label>
            <input
              type="text"
              name="name"
              value={formData.name}
              onChange={handleChange}
              readOnly={!!user}
              required
              className="w-full px-4 py-2 border border-gray-300 rounded-lg"
            />
          </div>

          <div className="mb-4">
            <label className="block text-sm font-medium mb-1">Email</label>
            <input
              type="email"
              name="email_id"
              value={formData.email_id}
              onChange={handleChange}
              readOnly={!!user}
              required
              className="w-full px-4 py-2 border border-gray-300 rounded-lg"
            />
          </div>

          {!user && (
            <>
              <div className="mb-4">
                <label className="block text-sm font-medium mb-1">
                  Password
                </label>
                <input
                  type="password"
                  name="password"
                  value={formData.password}
                  onChange={handleChange}
                  required
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                />
              </div>
              <div className="mb-4">
                <label className="block text-sm font-medium mb-1">
                  Confirm Password
                </label>
                <input
                  type="password"
                  name="confirm_password"
                  value={formData.confirm_password}
                  onChange={handleChange}
                  required
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                />
              </div>
            </>
          )}

          <div className="mb-4">
            <label className="block text-sm font-medium mb-1">Role</label>
            <select
              name="role_id"
              value={formData.role_id}
              onChange={handleChange}
              disabled={!!user}
              required
              className="w-full px-4 py-2 border border-gray-300 rounded-lg"
            >
              {roles.map((role) => (
                <option key={role.user_role_id} value={role.user_role_id}>
                  {role.user_role_name}
                </option>
              ))}
            </select>
          </div>

          {/* role permissions (read only) */}
          <div className="border rounded-lg p-3 mb-4 max-h-[200px] overflow-y-auto">
            <p className="text-sm font-medium text-gray-700 mb-2">
              Role Permissions (Read-only)
            </p>
            {formData.role_permissions.length > 0 ? (
              formData.role_permissions.map((perm) => (
                <div
                  key={perm.id}
                  className="flex items-center justify-between border-b py-1"
                >
                  <span className="text-gray-700 text-sm">
                    {perm.permission_name}
                  </span>
                  <input
                    type="checkbox"
                    checked={perm.has_permission}
                    disabled
                    className="w-4 h-4 text-gray-400 cursor-not-allowed"
                  />
                </div>
              ))
            ) : (
              <p className="text-sm text-gray-500 italic">
                No role permissions found
              </p>
            )}
          </div>

          {/* user permissions (editable) */}
          <div className="border rounded-lg p-3 mb-4 max-h-[200px] overflow-y-auto">
            <div className="flex justify-between items-center mb-2">
              <p className="text-sm font-medium text-gray-700">
                User Permissions:
              </p>
              <button
                type="button"
                onClick={toggleAllPermissions}
                className="text-xs bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded"
              >
                {formData.user_permissions.every((p) => p.has_permission)
                  ? "Uncheck All"
                  : "Check All"}
              </button>
            </div>

            {formData.user_permissions.length > 0 ? (
              formData.user_permissions.map((perm) => (
                <div
                  key={perm.id}
                  className="flex items-center justify-between border-b py-1"
                >
                  <span className="text-gray-700 text-sm">
                    {perm.permission_name}
                  </span>
                  <input
                    type="checkbox"
                    checked={perm.has_permission}
                    onChange={() => togglePermission(perm.id)}
                    className="w-4 h-4 text-green-600 cursor-pointer"
                  />
                </div>
              ))
            ) : (
              <p className="text-sm text-gray-500 italic">
                No user permissions found
              </p>
            )}
          </div>

          <div className="flex justify-end gap-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 bg-gray-300 rounded-lg"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-blue-600 text-white rounded-lg"
            >
              {user ? "Save Changes" : "Add User"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
