
import { useEffect, useState } from "react";
import { Plus } from "lucide-react";
import MenuTable from "../components/Menu/MenuTable";
import MenuModal from "../components/Menu/MenuModal";
import apiClient from "../services/apiClient";
import { toast } from "sonner";
import { useConfirm } from "../hooks/useConfirm";
import { usePermission } from "../hooks/usePermission";
import TrainingStatusWidget from "../components/Training/TrainingStatusWidget";

export default function MenuManagementPage() {
  const [menus, setMenus] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [editMenu, setEditMenu] = useState(null);
  const [selectedLanguage, setSelectedLanguage] = useState("english");
  const [loadingDelSubmenu, setLoadingDelSubmenu] = useState(null);
  const [loadingDelMenu, setLoadingDelMenu] = useState(null);
  const [loadingMenu, setLoadingMenu] = useState(false);
  const [orderChanged, setOrderChanged] = useState(false); // 🔥 Track reorder state
  const [updatingOrder, setUpdatingOrder] = useState(false);

  const [formData, setFormData] = useState({
    name: "",
    is_visible: false,
    lang: "english",
  });

  const [rajdhaniUsers, setRajdhaniUsers] = useState([]);
  const [user_id, setUserId] = useState(null);

  const { confirm, ConfirmDialog } = useConfirm();
  const { has } = usePermission();

  // ---------------- FETCH RAJDHANI USERS ----------------
  const fetchRajdhaniUsers = async () => {
    try {
      const res = await apiClient.get("/get_rajdhani_users");
      const users = res.data || [];
      setRajdhaniUsers(users);
      if (users.length > 0) setUserId(users[0].id);
    } catch (error) {
      console.error("Failed to fetch Rajdhani users:", error);
      toast.error(error?.response?.data?.message);
    }
  };

  useEffect(() => {
    fetchRajdhaniUsers();
  }, []);

  // ---------------- FETCH MENU DATA ----------------
  const fetchUserMenuData = async () => {
    if (!user_id) return;
    const selectedUser = rajdhaniUsers.find((u) => u.id === user_id);
    if (!selectedUser) return;

    try {
      setLoading(true);
      const res = await apiClient.get(
        `/get_user_menu_data?user_name=${encodeURIComponent(selectedUser.name)}`
      );

      const apiData =
        res.data?.data?.menu_options ||
        res.data?.menu_options ||
        res.data?.data ||
        [];

      if (!Array.isArray(apiData) || apiData.length === 0) {
        setMenus([]);
        return;
      }

      const formattedMenus = apiData.map((menu) => ({
        menu_id: menu.menu_id,
        name: menu.name,
        lang: menu.lang || "en",
        is_visible: menu.is_visible ?? false,
        submenus: (menu.submenus || []).map((s) => ({
          ...s,
          icon_path: s.icon_path
            ? import.meta.env.VITE_API_BASE_URL + "/" + s.icon_path
            : null,
        })),
        icon_path:
          import.meta.env.VITE_API_BASE_URL + "/" + menu.icon_path || null,
      }));

      setMenus(formattedMenus);
      setOrderChanged(false);
    } catch (error) {
      console.error("Failed to fetch user menu data:", error);
      setMenus([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user_id && rajdhaniUsers.length > 0) {
      fetchUserMenuData();
    }
  }, [user_id]);

  // ---------------- INPUT HANDLERS ----------------
  const handleInputChange = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const resetForm = () => {
    setFormData({
      name: "",
      is_visible: false,
      lang: "english",
      icon_path: null,
    });
    setEditMenu(null);
  };

  // ---------------- SAVE MENU ----------------
  const handleSaveMenu = async (data) => {
    const isEdit = !!(editMenu && editMenu.menu_id);

    if (!data.name?.trim()) {
      toast.error("Menu name is required!");
      return;
    }

    if (!isEdit && !(data.icon_path instanceof File)) {
      toast.error("Menu icon is required when creating a new menu!");
      return;
    }

    if (!Array.isArray(data.submenus) || data.submenus.length === 0) {
      toast.error("At least one submenu is required!");
      return;
    }

    for (let i = 0; i < data.submenus.length; i++) {
      const submenu = data.submenus[i];
      const submenuName = submenu.name?.trim() || `Submenu #${i + 1}`;
      if (!submenu.name?.trim()) {
        toast.error(`${submenuName}: name is required!`);
        return;
      }

      if (!isEdit && !(submenu.icon_path instanceof File)) {
        toast.error(`Icon is required for ${submenuName} when creating a new menu!`);
        return;
      }

      if (!Array.isArray(submenu.intents) || submenu.intents.length === 0) {
        toast.error(`${submenuName} must have at least one intent!`);
        return;
      }

      for (let j = 0; j < submenu.intents.length; j++) {
        const intent = submenu.intents[j];
        const intentName = intent.name?.trim() || `Intent #${j + 1}`;
        if (!intent.name?.trim()) {
          toast.error(`${intentName} in ${submenuName}: name is required!`);
          return;
        }

        if (!Array.isArray(intent.examples) || intent.examples.length < 2) {
          toast.error(`${intentName} in ${submenuName}: needs at least 2 examples!`);
          return;
        }

        if (intent.response_type === "static") {
          if (!Array.isArray(intent.utters) || intent.utters.length === 0) {
            toast.error(`${intentName} in ${submenuName}: needs at least 1 utter!`);
            return;
          }
        } else {
          if (
            !Array.isArray(intent.actions) ||
            intent.actions.length === 0 ||
            !intent.actions[0]
          ) {
            toast.error(`${intentName} in ${submenuName}: needs at least 1 action!`);
            return;
          }
        }
      }
    }

    if (isEdit && !has("menus-update")) {
      toast.error("You don't have permission to update menus.");
      return;
    } else if (!isEdit && !has("menus-create")) {
      toast.error("You don't have permission to create menus.");
      return;
    }

    setLoadingMenu(true);
    try {
      const fd = new FormData();
      const clonedSubmenus = JSON.parse(JSON.stringify(data.submenus));

      clonedSubmenus.forEach((submenu) => {
        submenu.intents.forEach((intent) => {
          if (Array.isArray(intent.examples)) {
            intent.examples = intent.examples.map((exObj) => {
              let exampleText = exObj.example?.trim() || "";
              if (!/\bBRPL$/i.test(exampleText)) {
                exampleText = `${exampleText} BRPL`.trim();
              }
              return { ...exObj, example: exampleText };
            });
          }
        });
      });

      fd.append("name", data.name);
      fd.append("lang", data.lang);
      fd.append("is_visible", data.is_visible);
      fd.append("user_id", data.user_id);
      fd.append("submenus", JSON.stringify(clonedSubmenus));

      if (data.icon_path instanceof File) {
        fd.append("menu_icon", data.icon_path);
      }

      if (isEdit) {
        fd.append("menu_id", editMenu.menu_id);
      }

      data.submenus.forEach((submenu, index) => {
        if (submenu.icon_path instanceof File) {
          fd.append(`submenu_icon_${index}`, submenu.icon_path);
        }
      });

      await apiClient.post("/api/create_menu_with_submenu", fd, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      toast.success(isEdit ? "Menu updated successfully!" : "Menu created successfully!");
      setShowModal(false);
      fetchUserMenuData();
      resetForm();

    } catch (err) {
      if (err.response?.status === 413) {
        toast.error("Entity too large. Please upload another one.");

      } else {
        const message =
          err.response?.data?.message || "Failed to save menu";

        toast.error(message);
      }
    } finally {
      setLoadingMenu(false);
    }
  };

  // ---------------- DELETE HANDLERS ----------------
  const handleDeleteSubmenu = async (submenuId, menuId = null) => {
    if (!has("menus-delete")) {
      toast.error("You don't have permission to delete menus.");
      return;
    }

    if (Array.from({ length: 18 }, (_, i) => i + 1).includes(menuId)) {
      toast.error("these options cannot be removed!");
      return;
    }

    const userConfirmed = await confirm({
      title: "Delete Submenu",
      message: "Are you sure you want to delete this submenu?",
    });
    if (!userConfirmed) return;

    try {
      setLoadingDelSubmenu(submenuId);
      await apiClient.delete(`/delete_submenu/${submenuId}`);
      setMenus((prev) =>
        prev.map((menu) => ({
          ...menu,
          submenus: menu.submenus.filter((s) => s.sub_menu_id !== submenuId),
        }))
      );
      toast.success("Submenu deleted successfully!");
    } catch {
      toast.error("Error deleting submenu");
    } finally {
      setLoadingDelSubmenu(null);
    }
  };

  const handleDelete = async (menuId) => {
    if (!has("menus-delete")) {
      toast.error("You don't have permission to delete menus.");
      return;
    }

    if (Array.from({ length: 18 }, (_, i) => i + 1).includes(menuId)) {
      toast.error("these options cannot be removed!");
      return;
    }

    const userConfirmed = await confirm({
      title: "Delete Menu",
      message: "Are you sure you want to delete this menu?",
    });
    if (!userConfirmed) return;

    try {
      setLoadingDelMenu(menuId);
      await apiClient.delete(`/delete_menu/${menuId}`);
      setMenus((prev) => prev.filter((menu) => menu.menu_id !== menuId));
      toast.success("Menu deleted successfully!");
    } catch {
      toast.error("Error deleting menu");
    } finally {
      setLoadingDelMenu(null);
    }
  };

  const handleEdit = (menu) => {
    if (!has("menus-update")) {
      toast.error("You don't have permission to update menus.");
      return;
    }

    if (Array.from({ length: 18 }, (_, i) => i + 1).includes(menu?.menu_id)) {
      toast.error("these options cannot be edited!");
      return;
    }

    setEditMenu(menu);
    setFormData(menu);
    setShowModal(true);
  };

  // ---------------- REORDER HANDLER ----------------
  const handleReorder = (newOrder) => {
    setMenus(newOrder);
    setOrderChanged(true);
  };

  // const handleUpdateOrder = async () => {
  //   if (!user_id) {
  //     toast.error("Please select a user first!");
  //     return;
  //   }

  //   try {
  //     setUpdatingOrder(true);
  //     const payload = {
  //       user_id,
  //       menu_order: menus.map((m, i) => ({
  //         id: m.menu_id,
  //         menu_sequence: i + 1,
  //       })),
  //     };

  //     await apiClient.post("/menu/update-sequence", payload);
  //     toast.success("Menu order updated successfully!");
  //     setOrderChanged(false);
  //   } catch (err) {
  //     console.error(err);
  //     toast.error("Failed to update order!");
  //   } finally {
  //     setUpdatingOrder(false);
  //   }
  // };



  // ---------------- RENDER ----------------


  const handleUpdateOrder = async () => {
    if (!user_id) {
      toast.error("Please select a user first!");
      return;
    }

    try {
      setUpdatingOrder(true);

      const payload = {
        user_id,
        menu_order: menus.map((m, i) => ({
          id: m.menu_id,
          menu_sequence: i + 1,
        })),
        submenu_order: menus.map((m) => ({
          menu_id: m.menu_id,
          submenu_items: (m.submenus || []).map((s, idx) => ({
            id: s.sub_menu_id,
            submenu_sequence: idx + 1,
          })),
        })),
      };

      await apiClient.post("/menu/update-sequence", payload);
      toast.success("Menu and submenu order updated successfully!");
      setOrderChanged(false);
    } catch (err) {
      console.error(err);
      toast.error("Failed to update order!");
    } finally {
      setUpdatingOrder(false);
    }
  };


  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-3">
        <h1 className="text-2xl font-semibold">📋 Menu Management</h1>

        <div className="flex flex-wrap gap-3 items-center">
          <TrainingStatusWidget />
          <select
            value={user_id || ""}
            onChange={(e) => setUserId(Number(e.target.value))}
            className="px-4 py-2 rounded-lg border border-gray-300"
          >
            <option value="">Select Rajdhani User</option>
            {rajdhaniUsers.map((user) => (
              <option key={user.id} value={user.id}>
                {user.name}
              </option>
            ))}
          </select>

          <button
            onClick={() => {
              if (!user_id)
                return alert("Please select a Rajdhani user first!");
              resetForm();
              setShowModal(true);
            }}
            className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
          >
            <Plus className="w-5 h-5" /> Create Menu
          </button>
        </div>
      </div>

      {/* Table */}
      <MenuTable
        menus={menus}
        setMenus={setMenus}
        userId={user_id}
        loading={loading}
        onEdit={handleEdit}
        onDelete={handleDelete}
        onReorder={handleReorder}
        language={selectedLanguage}
        onDeleteSubmenu={handleDeleteSubmenu}
        loadingDelMenu={loadingDelMenu}
        loadingDelSubmenu={loadingDelSubmenu}
      />

      {/* Update Order Button */}
      {orderChanged && (
        <div className="flex justify-end mt-4">
          <button
            onClick={handleUpdateOrder}
            disabled={updatingOrder}
            className={`px-5 py-2 rounded-lg font-medium ${updatingOrder
              ? "bg-gray-400 cursor-not-allowed"
              : "bg-green-600 hover:bg-green-700 text-white"
              }`}
          >
            {updatingOrder ? "Updating..." : "Update Sequence"}
          </button>
        </div>
      )}

      {/* Modal */}
      {showModal && (
        <MenuModal
          formData={formData}
          rajdhaniUsers={rajdhaniUsers}
          user_id={user_id}
          onClose={() => {
            setShowModal(false);
            resetForm();
          }}
          onSave={handleSaveMenu}
          onInputChange={handleInputChange}
          editMode={!!editMenu}
          loadingMenu={loadingMenu}
        />
      )}

      <ConfirmDialog />
    </div>
  );
}
