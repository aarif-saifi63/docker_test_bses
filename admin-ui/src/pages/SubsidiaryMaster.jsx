// import React, { useEffect, useState } from "react";
// import { Plus } from "lucide-react";
// import MenuTable from "../components/SubsidiaryMaster/SubsidiaryMasterTable";
// import MenuModal from "../components/Menu/MenuModal";
// import LanguageSelector from "../components/UI/LanguageSelector";
// import apiClient from "../services/apiClient";
// import { toast } from "sonner";

// export default function SubsidiaryMaster() {
//   const [menus, setMenus] = useState([]);
//   const [loading, setLoading] = useState(false);
//   const [showModal, setShowModal] = useState(false);
//   const [editMenu, setEditMenu] = useState(null);
//   const [selectedLanguage, setSelectedLanguage] = useState("english");

//   const [formData, setFormData] = useState({
//     name: "",
//     is_visible: false,
//     lang: "english",
//   });

//   const [rajdhaniUsers, setRajdhaniUsers] = useState([]);
//   const [user_id, setUserId] = useState(null);

//   // ---------------- FETCH RAJDHANI USERS ----------------
//   useEffect(() => {
//     const fetchRajdhaniUsers = async () => {
//       try {
//         const res = await apiClient.get("/get_rajdhani_users");
//         const users = res.data || [];
//         setRajdhaniUsers(users);

//         // ✅ Auto-select first user if available
//         if (users.length > 0) {
//           setUserId(users[0].id);
//         }
//       } catch (error) {
//         console.error("Failed to fetch Rajdhani users:", error);
//         toast.error("Failed to fetch Rajdhani users");
//       }
//     };
//     fetchRajdhaniUsers();
//   }, []);

//   // ---------------- FETCH MENU DATA WHEN USER SELECTED ----------------
//   useEffect(() => {
//     const fetchUserMenuData = async () => {
//       if (!user_id) return;

//       const selectedUser = rajdhaniUsers.find((u) => u.id === user_id);
//       if (!selectedUser) return;

//       try {
//         setLoading(true);
//         const res = await apiClient.get(
//           `/get_user_menu_data?user_name=${encodeURIComponent(selectedUser.name)}`
//         );

//         console.log("Full API Response:", res.data);

//         const apiData =
//           res.data?.data?.menu_options || res.data?.menu_options || res.data?.data || [];

//         if (!Array.isArray(apiData) || apiData.length === 0) {
//           console.warn("⚠️ No menu options found in response:", apiData);
//           toast.warning("No menu options found for the selected user.");
//           setMenus([]);
//           return;
//         }

//         const formattedMenus = apiData.map((menu) => ({
//           menu_id: menu.menu_id,
//           menu_name: menu.menu_name,
//           lang: menu.lang || "en",
//           is_visible: menu.is_visible ?? false,
//           sub_menus: menu.sub_menus || [],
//         }));

//         console.log("✅ Formatted Menus:", formattedMenus);

//         setMenus(formattedMenus);
//         toast.success("Menus loaded successfully");
//       } catch (error) {
//         console.error("Failed to fetch user menu data:", error);
//         toast.error("Failed to fetch menu data for the selected user");
//         setMenus([]);
//       } finally {
//         setLoading(false);
//       }
//     };

//     fetchUserMenuData();
//   }, [user_id, rajdhaniUsers]);

//   // ---------------- INPUT HANDLERS ----------------
//   const handleInputChange = (field, value) => {
//     setFormData((prev) => ({ ...prev, [field]: value }));
//   };

//   const resetForm = () => {
//     setFormData({
//       name: "",
//       is_visible: false,
//       lang: "english",
//     });
//     setEditMenu(null);
//   };

//   // ---------------- SAVE MENU ----------------
//   const handleSaveMenu = async (data) => {
//     if (!formData.name) return alert("Menu title is required!");

//     const payload = {
//       ...data,
//       user_id,
//     };

//     console.log("✅ Final Payload:", payload);

//     const response = await apiClient.post("/api/create_menu_with_submenu", payload);

//     // Close modal
//     setShowModal(false);

//     resetForm();
//   };

//   // ---------------- CRUD UTILS ----------------
//   const handleDelete = (id) => {
//     if (window.confirm("Delete this menu?")) {
//       setMenus((prev) => prev.filter((m) => m.id !== id));
//       toast.success("Menu deleted successfully");
//     }

//   };

//   const handleEdit = (menu) => {
//     setEditMenu(menu);
//     setFormData(menu);
//     setShowModal(true);
//   };

//   const toggleActiveStatus = (menu) => {
//     setMenus((prev) =>
//       prev.map((m) =>
//         m.id === menu.id ? { ...m, is_visible: !m.is_visible } : { ...m, is_visible: false }
//       )
//     );
//   };

//   // ---------------- RENDER ----------------
//   return (
//     <div className="p-6">
//       {/* Header */}
//       <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-3">
//         <h1 className="text-2xl font-semibold">📋 Subsidiary Master</h1>

//         <div className="flex flex-wrap gap-3 items-center">
//           <LanguageSelector selected={selectedLanguage} onChange={setSelectedLanguage} />

//           {/* Rajdhani User Dropdown */}
//           <select
//             value={user_id || ""}
//             onChange={(e) => setUserId(Number(e.target.value))}
//             className="px-4 py-2 rounded-lg border border-gray-300"
//           >
//             <option value="">Select Rajdhani User</option>
//             {rajdhaniUsers.map((user) => (
//               <option key={user.id} value={user.id}>
//                 {user.name}
//               </option>
//             ))}
//           </select>
//           {/*
//           <button
//             onClick={() => {
//               if (!user_id) return alert("Please select a Rajdhani user before creating a menu!");
//               resetForm();
//               setShowModal(true);
//             }}
//             className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
//           >
//             <Plus className="w-5 h-5" /> Create Menu
//           </button> */}
//         </div>
//       </div>

//       {/* Table */}
//       <MenuTable
//         menus={menus}
//         loading={loading}
//         onEdit={handleEdit}
//         onDelete={handleDelete}
//         onToggleActive={toggleActiveStatus}
//         language={selectedLanguage}
//       />

//       {/* Modal */}
//       {showModal && (
//         <MenuModal
//           formData={formData}
//           rajdhaniUsers={rajdhaniUsers}
//           user_id={user_id} // ✅ pass user_id
//           onClose={() => {
//             setShowModal(false);
//             resetForm();
//           }}
//           onSave={handleSaveMenu}
//           onInputChange={handleInputChange}
//           editMode={!!editMenu}
//         />
//       )}
//     </div>
//   );
// }

import { useEffect, useState } from "react";
import { Plus } from "lucide-react";
import MenuTable from "../components/Menu/MenuTable";
import MenuModal from "../components/Menu/MenuModal";
import LanguageSelector from "../components/UI/LanguageSelector";
import apiClient from "../services/apiClient";
import { toast } from "sonner";
import { useConfirm } from "../hooks/useConfirm";

export default function SubsidiaryMaster() {
  const [menus, setMenus] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [editMenu, setEditMenu] = useState(null);
  const [selectedLanguage, setSelectedLanguage] = useState("english");
  const [loadingDelSubmenu, setLoadingDelSubmenu] = useState(null);
  const [loadingDelMenu, setLoadingDelMenu] = useState(null);
  const [loadingMenu, setLoadingMenu] = useState(false);

  const [formData, setFormData] = useState({
    name: "",
    is_visible: false,
    lang: "english",
  });

  const [rajdhaniUsers, setRajdhaniUsers] = useState([]);
  const [user_id, setUserId] = useState(null);

  const { confirm, ConfirmDialog } = useConfirm();

  // ---------------- FETCH RAJDHANI USERS ----------------
  const fetchRajdhaniUsers = async () => {
    try {
      const res = await apiClient.get("/get_rajdhani_users");
      const users = res.data || [];
      setRajdhaniUsers(users);

      // ✅ Auto-select first user if available
      if (users.length > 0) {
        setUserId(users[0].id);
      }
    } catch (error) {
      console.error("Failed to fetch Rajdhani users:", error);
    }
  };

  useEffect(() => {
    fetchRajdhaniUsers();
  }, []);

  // ---------------- FETCH MENU DATA WHEN USER SELECTED ----------------
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
        res.data?.data?.menu_options || res.data?.menu_options || res.data?.data || [];

      if (!Array.isArray(apiData) || apiData.length === 0) {
        console.warn("⚠️ No menu options found in response:", apiData);
        setMenus([]);
        return;
      }

      const formattedMenus = apiData.map((menu) => ({
        menu_id: menu.menu_id,
        name: menu.name,
        lang: menu.lang || "en",
        is_visible: menu.is_visible ?? false,
        submenus: menu.submenus || [],
      }));

     

      setMenus(formattedMenus);
      // toast.success("Menus loaded successfully");
    } catch (error) {
      console.error("Failed to fetch user menu data:", error);

      setMenus([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUserMenuData();
  }, [user_id, rajdhaniUsers]);

  // ---------------- INPUT HANDLERS ----------------
  const handleInputChange = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const resetForm = () => {
    setFormData({
      name: "",
      is_visible: false,
      lang: "english",
    });
    setEditMenu(null);
  };

  // ---------------- SAVE MENU ----------------
  const handleSaveMenu = async (data) => {
    if (!formData.name) return alert("Menu title is required!");

    setLoadingMenu(true);

    try {
      const payload = {
        ...data,
        user_id,
      };


      const response = await apiClient.post("/api/create_menu_with_submenu", payload);

      // Close modal
      setShowModal(false);

      if (payload?.menu_id) toast.success("Menu updated Successfully!");
      else toast.success("Menu has been created!");

      fetchRajdhaniUsers();

      resetForm();
    // } catch (err) {
    //   console.log("[Error]: ", err);
    //   if (err.response?.status === 413) {
    //     toast.error("Entity too large. Please upload another one.");
    //   } else {
    //     toast.error("Error Creating Menu");
    //   }
    // } finally {

}catch (err) {
          if (err.response?.status === 413) {
            toast.error("Entity too large. Please upload another one.");
          } else {
            const message =
              err.response?.data?.message || "Error Creating Menu";
            
            toast.error(message);
          }
        } finally {
      setLoadingMenu(false);
    }
  };

  const handleDeleteSubmenu = async (submenuId) => {
    const userConfirmed = await confirm({
      title: "Delete Submenu",
      message: "Are you sure you want to delete this submenu? This action cannot be undone.",
    });

    if (!userConfirmed) return;

    try {
      setLoadingDelSubmenu(submenuId);
      await apiClient.delete(`/delete_submenu/${submenuId}`);

      // Update local state
      setMenus((prevMenus) =>
        prevMenus.map((menu) => ({
          ...menu,
          submenus: menu.submenus.filter((sub) => sub.sub_menu_id !== submenuId),
        }))
      );

      toast.success("Submenu deleted successfully!");
    } catch (err) {
      toast.error("Error deleting submenu");
      console.log("ERROR: ", err);
    } finally {
      setLoadingDelSubmenu(null);
    }
  };

  const handleDelete = async (menuId) => {
    const userConfirmed = await confirm({
      title: "Delete Menu",
      message: "Are you sure you want to delete this menu? This action cannot be undone.",
    });

    if (!userConfirmed) return;

    try {
      setLoadingDelMenu(menuId);

      await apiClient.delete(`/delete_menu/${menuId}`); // Replace with actual endpoint

      // Update local state
      setMenus((prevMenus) => prevMenus.filter((menu) => menu.menu_id !== menuId));

      toast.success("Menu deleted successfully!");
    } catch (err) {
      toast.error("Error deleting menu");
      console.log("ERROR: ", err);
    } finally {
      setLoadingDelMenu(null);
    }
  };

  const handleEdit = (menu) => {
    setEditMenu(menu);
    setFormData(menu);
    setShowModal(true);
  };

  // ---------------- RENDER ----------------
  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-3">
        <h1 className="text-2xl font-semibold">📋 Menu Management</h1>
  
        <div className="flex flex-wrap gap-3 items-center">
          {/* <LanguageSelector selected={selectedLanguage} onChange={setSelectedLanguage} /> */}

          {/* Rajdhani User Dropdown */}
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

          {/* <button
            onClick={() => {
              if (!user_id) return alert("Please select a Rajdhani user before creating a menu!");
              resetForm();
              setShowModal(true);
            }}
            className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
          >
            <Plus className="w-5 h-5" /> Create Menu
          </button> */}
        </div>
      </div>

      {/* Table */}
      <MenuTable
        menus={menus}
        loading={loading}
        onEdit={handleEdit}
        onDelete={handleDelete}
        language={selectedLanguage}
        onDeleteSubmenu={handleDeleteSubmenu}
        loadingDelMenu={loadingDelMenu}
        loadingDelSubmenu={loadingDelSubmenu}
        showAction={false}
      />

      {/* Modal */}
      {showModal && (
        <MenuModal
          formData={formData}
          rajdhaniUsers={rajdhaniUsers}
          user_id={user_id} // ✅ pass user_id
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
