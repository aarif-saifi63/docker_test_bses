import { useContext } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { AuthContext } from "../../context/AuthContext";
import { usePermission } from "../../hooks/usePermission";

export default function ProtectedRoute({
  children,
  allowedRoles = [],
  requiredPermissions = [],
}) {
  const { user } = useContext(AuthContext);
  const { hasAll } = usePermission(); // use your hook's logic

  const location = useLocation();

  // ✅ 1. Check authentication
  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // ✅ 2. Role-based access
  const hasRoleAccess =
    allowedRoles.length === 0 || allowedRoles.includes(user.role_name);

  // ✅ 3. Permission-based access using hook
  const hasPermissionAccess =
    requiredPermissions.length === 0 || hasAll(requiredPermissions);

  // ✅ 4. Deny if not authorized
  if (!hasRoleAccess || !hasPermissionAccess) {
    return <Navigate to="/not-authorized" replace />;
  }

  // ✅ 5. Authorized
  return children;
}
