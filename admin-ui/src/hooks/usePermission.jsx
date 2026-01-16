import { useMemo, useContext } from "react";
import { AuthContext } from "../context/AuthContext"; // adjust path as needed

export function usePermission() {
  const { user } = useContext(AuthContext);

  const permissionSet = useMemo(() => {
    return new Set((user?.permissions || []).map((p) => p.permission_name));
  }, [user]);

  const has = (permission) => permissionSet.has(permission);

  const hasAll = (permissions) => permissions.every((p) => permissionSet.has(p));

  const hasAny = (permissions) => permissions.some((p) => permissionSet.has(p));

  const can = (module, action) => {
    if (!module) return false;

    // Full module access (e.g., "menus")
    if (permissionSet.has(module)) return true;

    // Specific CRUD access (e.g., "menus-update")
    if (action) {
      return permissionSet.has(`${module}-${action}`);
    }

    return false;
  };

  return { has, hasAll, hasAny, can };
}
