// import React, { useState } from "react";
// import {
//   Pencil,
//   Trash2,
//   ChevronDown,
//   ChevronUp,
//   Trash,
//   MessageSquare,
//   Network,
//   Target,
//   MessageCircle
// } from "lucide-react";
// import CircularProgress from "@mui/material/CircularProgress";
// import { useNavigate } from "react-router-dom";

// export default function MenuTable({
//   menus = [],
//   loading,
//   onEdit,
//   onDelete,
//   language,
//   onDeleteSubmenu,
//   loadingDelMenu,
//   loadingDelSubmenu,
//   showAction = true,
// }) {
//   const [expandedMenus, setExpandedMenus] = useState([]);
//   const [expandedExamples, setExpandedExamples] = useState({});
// const navigate = useNavigate();

//   if (loading)
//     return (
//       <div className="text-center text-gray-500 py-6">Loading menus...</div>
//     );

//   if (!menus || menus.length === 0)
//     return (
//       <div className="text-center text-gray-400 py-6">
//         No menus available for {language === "english" ? "English" : "Hindi"}.
//       </div>
//     );

//   const toggleExpand = (menuId) => {
//     setExpandedMenus((prev) =>
//       prev.includes(menuId)
//         ? prev.filter((id) => id !== menuId)
//         : [...prev, menuId]
//     );
//   };

//   const toggleExamples = (intentId) => {
//     setExpandedExamples((prev) => ({
//       ...prev,
//       [intentId]: !prev[intentId],
//     }));
//   };

//   return (
//     <div className="overflow-x-auto border border-gray-200 rounded-lg">
//       <table className="min-w-full border-collapse">
//         <thead className="bg-gray-100 text-sm">
//           <tr>
//             <th className="px-4 py-2 text-left border-b">Menu Title</th>
//             <th className="px-4 py-2 text-center border-b">Language</th>
//             <th className="px-4 py-2 text-center border-b">Visible</th>
//             <th className="px-4 py-2 text-center border-b">Submenus</th>
//             {!showAction ? (
//               ""
//             ) : (
//               <th className="px-4 py-2 text-center border-b">Actions</th>
//             )}
//           </tr>
//         </thead>

//         <tbody>
//           {menus.map((menu) => {
//             const isExpanded = expandedMenus.includes(menu.menu_id);
//             return (
//               <React.Fragment key={menu.menu_id}>
//                 {/* ----- MAIN MENU ROW ----- */}
//                 <tr
//                   className="hover:bg-gray-50 transition cursor-pointer"
//                   onClick={() => toggleExpand(menu.menu_id)}
//                 >
//                   <td className="px-4 py-3 border-b font-medium flex items-center gap-2">
//                     {isExpanded ? (
//                       <ChevronUp className="w-4 h-4 text-gray-500" />
//                     ) : (
//                       <ChevronDown className="w-4 h-4 text-gray-500" />
//                     )}
//                     {menu.name}
//                   </td>
//                   <td className="px-4 py-3 border-b text-center capitalize">
//                     {menu.lang === "en" ? "English" : "Hindi"}
//                   </td>
//                   <td className="px-4 py-3 border-b text-center">
//                     <button
//                       className={`px-3 py-1 rounded-full text-sm font-medium ${
//                         menu.is_visible
//                           ? "bg-green-100 text-green-700 border border-green-300"
//                           : "bg-gray-100 text-gray-700 border border-gray-300"
//                       }`}
//                     >
//                       {menu.is_visible ? "Visible" : "Hidden"}
//                     </button>
//                   </td>
//                   <td className="px-4 py-3 border-b text-center">
//                     {menu.submenus?.length || 0}
//                   </td>
//                   {!showAction ? (
//                     ""
//                   ) : (
//                     // <td
//                     //   className="px-4 py-3 border-b text-center flex justify-center gap-2"
//                     //   onClick={(e) => e.stopPropagation()}
//                     // >
//                     //   {!showAction ? (
//                     //     ""
//                     //   ) : (
//                     //     <button
//                     //       onClick={() => onEdit(menu)}
//                     //       className="text-blue-600 hover:text-blue-800"
//                     //     >
//                     //       <Pencil className="w-5 h-5" />
//                     //     </button>
//                     //   )}
//                     //   {!showAction ? (
//                     //     ""
//                     //   ) : loadingDelMenu === menu.menu_id ? (
//                     //     <CircularProgress size={20} />
//                     //   ) : (
//                     //     <button
//                     //       onClick={() => onDelete(menu.menu_id)}
//                     //       className="text-red-600 hover:text-red-800"
//                     //     >
//                     //       <Trash2 className="w-5 h-5" />
//                     //     </button>
//                     //   )}
//                     // </td>

//                     <td
//                       className="px-4 py-3 border-b text-center flex justify-center gap-2"
//                       onClick={(e) => e.stopPropagation()}
//                     >
//                       {/* Edit */}
//                       {showAction && (
//                         <button
//                           onClick={() => onEdit(menu)}
//                           className="text-blue-600 hover:text-blue-800"
//                           title="Edit Menu"
//                         >
//                           <Pencil className="w-5 h-5" />
//                         </button>
//                       )}

//                       {/* Delete */}
//                       {showAction &&
//                         (loadingDelMenu === menu.menu_id ? (
//                           <CircularProgress size={20} />
//                         ) : (
//                           <button
//                             onClick={() => onDelete(menu.menu_id)}
//                             className="text-red-600 hover:text-red-800"
//                             title="Delete Menu"
//                           >
//                             <Trash2 className="w-5 h-5" />
//                           </button>
//                         ))}

//                       {/* 🆕 Navigate to Message */}
//                       {showAction && (
//                         <button
//                           onClick={() => navigate("/message")}
//                           className="text-green-600 hover:text-green-800"
//                           title="Go to Messages"
//                         >
//                           <MessageCircle className="w-5 h-5" />
//                         </button>
//                       )}

//                       {/* 🆕 Navigate to Intent */}
//                       {showAction && (
//                         <button
//                           onClick={() => navigate("/intent")}
//                           className="text-purple-600 hover:text-purple-800"
//                           title="Go to Intents"
//                         >
//                           <Target className="w-5 h-5" />
//                         </button>
//                       )}
//                     </td>
//                   )}
//                 </tr>

//                 {/* ----- EXPANDED SUBMENU SECTION ----- */}
//                 {isExpanded && (
//                   <tr>
//                     <td colSpan="5" className="bg-gray-50 border-b">
//                       <div className="p-4 space-y-4">
//                         {(menu.submenus || []).map((submenu) => (
//                           <div
//                             key={submenu.sub_menu_id}
//                             className="border border-gray-200 rounded-lg bg-white shadow-sm"
//                           >
//                             {/* Submenu Header */}
//                             <div className="p-3 border-b flex justify-between items-center">
//                               <div>
//                                 <h3 className="font-semibold text-gray-800">
//                                   {submenu.name}
//                                 </h3>
//                                 <p className="text-xs text-gray-500">
//                                   {submenu.lang === "en" ? "English" : "Hindi"}{" "}
//                                   | {submenu.is_visible ? "Visible" : "Hidden"}
//                                 </p>
//                               </div>

//                               <div className="flex items-center gap-3">
//                                 <span className="text-sm text-gray-500">
//                                   {submenu.intents?.length || 0} intents
//                                 </span>

//                                 {!showAction ? (
//                                   ""
//                                 ) : loadingDelSubmenu ===
//                                   submenu.sub_menu_id ? (
//                                   <CircularProgress size={18} />
//                                 ) : (
//                                   <button
//                                     onClick={() =>
//                                       onDeleteSubmenu(
//                                         submenu?.sub_menu_id,
//                                         menu.menu_id
//                                       )
//                                     }
//                                     className="text-red-600 hover:text-red-800"
//                                     title="Delete submenu"
//                                   >
//                                     <Trash className="w-4 h-4" />
//                                   </button>
//                                 )}
//                               </div>
//                             </div>

//                             {/* Intents */}
//                             <div className="p-3 space-y-3">
//                               {(submenu.intents || []).map((intent) => {
//                                 const isExpanded =
//                                   expandedExamples[intent.intent_id];
//                                 const examples = intent.examples || [];
//                                 const displayedExamples = isExpanded
//                                   ? examples
//                                   : examples.slice(0, 5);

//                                 const utters = intent.utters || [];
//                                 const actions = intent.actions || [];

//                                 return (
//                                   <div
//                                     key={intent.intent_id}
//                                     className="bg-gray-50 rounded-md p-3 border"
//                                   >
//                                     <p className="font-medium text-gray-700 mb-1">
//                                       🧠 {intent.name}
//                                     </p>

//                                     {/* ---- EXAMPLES ---- */}
//                                     {examples.length > 0 && (
//                                       <>
//                                         <p className="text-sm font-semibold text-gray-600">
//                                           🗣️ Examples:
//                                         </p>
//                                         <ul className="list-disc pl-5 text-sm text-gray-600 mb-2">
//                                           {displayedExamples.map((ex, idx) => (
//                                             <li key={idx}>
//                                               {ex.example || ex}
//                                             </li>
//                                           ))}
//                                         </ul>
//                                         {examples.length > 5 && (
//                                           <button
//                                             onClick={() =>
//                                               toggleExamples(intent.intent_id)
//                                             }
//                                             className="mt-1 text-blue-600 text-sm hover:underline"
//                                           >
//                                             {isExpanded
//                                               ? "Show less"
//                                               : `Show ${
//                                                   examples.length - 5
//                                                 } more`}
//                                           </button>
//                                         )}
//                                       </>
//                                     )}

//                                     {/* ---- UTTERS ---- */}
//                                     {utters.length > 0 && (
//                                       <>
//                                         <p className="text-sm font-semibold text-gray-600 mt-3">
//                                           💬 Utters:
//                                         </p>
//                                         <ul className="list-disc pl-5 text-sm text-gray-600">
//                                           {utters.map((u, idx) => (
//                                             <li key={idx}>
//                                               {u.name
//                                                 ? `${u.name}: ${
//                                                     u.response || ""
//                                                   }`
//                                                 : typeof u === "string"
//                                                 ? u
//                                                 : ""}
//                                             </li>
//                                           ))}
//                                         </ul>
//                                       </>
//                                     )}

//                                     {/* ---- ACTIONS ---- */}
//                                     {actions.length > 0 && (
//                                       <>
//                                         <p className="text-sm font-semibold text-gray-600 mt-3">
//                                           ⚙️ Actions:
//                                         </p>
//                                         <ul className="list-disc pl-5 text-sm text-gray-600">
//                                           {actions.map((a, idx) => (
//                                             <li key={idx}>{a.name || a}</li>
//                                           ))}
//                                         </ul>
//                                       </>
//                                     )}
//                                   </div>
//                                 );
//                               })}
//                             </div>
//                           </div>
//                         ))}
//                       </div>
//                     </td>
//                   </tr>
//                 )}
//               </React.Fragment>
//             );
//           })}
//         </tbody>
//       </table>
//     </div>
//   );
// }

import React, { useState } from "react";
import {
  Pencil,
  Trash2,
  ChevronDown,
  ChevronUp,
  Trash,
  MessageCircle,
  Target,
  GripVertical,
  CheckCircle,
  XCircle,
} from "lucide-react";
import CircularProgress from "@mui/material/CircularProgress";
import { useNavigate } from "react-router-dom";

import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
} from "@dnd-kit/core";
import {
  arrayMove,
  SortableContext,
  useSortable,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { toast } from "sonner";
import apiClient from "../../services/apiClient";

function SortableRow({ menu, children }) {
  const { attributes, listeners, setNodeRef, transform, transition } =
    useSortable({
      id: menu.menu_id,
    });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  return (
    <tr
      ref={setNodeRef}
      style={style}
      className="bg-white hover:bg-gray-50 transition"
    >
      <td
        {...attributes}
        {...listeners}
        onClick={(e) => e.stopPropagation()}
        className="cursor-grab active:cursor-grabbing text-gray-400 w-8 pl-3"
        title="Drag to reorder"
      >
        <GripVertical className="w-4 h-4" />
      </td>
      {children}
    </tr>
  );
}

function SortableSubmenu({ submenu, children }) {
  const { attributes, listeners, setNodeRef, transform, transition } =
    useSortable({
      id: submenu.sub_menu_id,
    });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...attributes}
      {...listeners}
      className="border border-gray-200 rounded-lg bg-white shadow-sm cursor-grab active:cursor-grabbing"
    >
      {children}
    </div>
  );
}

export default function MenuTable({
  menus = [],
  setMenus,
  userId,
  loading,
  onEdit,
  onDelete,
  onReorder,
  language,
  onDeleteSubmenu,
  loadingDelMenu,
  loadingDelSubmenu,
  showAction = true,
}) {
  const [expandedMenus, setExpandedMenus] = useState([]);
  const [expandedExamples, setExpandedExamples] = useState({});
  // Track loading for specific menu or submenu
  const [menuLoadingId, setMenuLoadingId] = useState(null);
  const [submenuLoadingId, setSubmenuLoadingId] = useState(null);

  const navigate = useNavigate();

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 6 } }),
    useSensor(KeyboardSensor)
  );

  if (loading)
    return (
      <div className="text-center text-gray-500 py-6">Loading menus...</div>
    );

  if (!menus || menus.length === 0)
    return (
      <div className="text-center text-gray-400 py-6">
        No menus available for {language === "english" ? "English" : "Hindi"}.
      </div>
    );

  const toggleExpand = (menuId) => {
    setExpandedMenus((prev) =>
      prev.includes(menuId)
        ? prev.filter((id) => id !== menuId)
        : [...prev, menuId]
    );
  };

  const toggleExamples = (intentId) => {
    setExpandedExamples((prev) => ({
      ...prev,
      [intentId]: !prev[intentId],
    }));
  };

  const handleDragEnd = (event) => {
    const { active, over } = event;
    if (!over || active.id === over.id) return;

    const oldIndex = menus.findIndex((m) => m.menu_id === active.id);
    const newIndex = menus.findIndex((m) => m.menu_id === over.id);
    const newOrder = arrayMove(menus, oldIndex, newIndex);
    onReorder?.(newOrder);
  };

  const handleSubmenuDragEnd = (event, menuId) => {
    const { active, over } = event;
    if (!over || active.id === over.id) return;

    const menuIndex = menus.findIndex((m) => m.menu_id === menuId);
    if (menuIndex === -1) return;

    const menu = menus[menuIndex];
    const oldIndex = menu.submenus.findIndex(
      (s) => s.sub_menu_id === active.id
    );
    const newIndex = menu.submenus.findIndex((s) => s.sub_menu_id === over.id);
    if (oldIndex === -1 || newIndex === -1) return;

    const reordered = arrayMove(menu.submenus, oldIndex, newIndex);
    const updatedMenus = [...menus];
    updatedMenus[menuIndex] = { ...menu, submenus: reordered };

    onReorder?.(updatedMenus);
  };

  const updateMenu = async (updatedData) => {
    const fd = new FormData();
    fd.append("name", updatedData.name);
    fd.append("lang", updatedData.lang);
    fd.append("is_visible", updatedData.is_visible);
    fd.append("user_id", userId);
    fd.append("menu_id", updatedData.menu_id);
    fd.append("submenus", JSON.stringify(updatedData.submenus));

    await apiClient.post("/api/create_menu_with_submenu", fd, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  };

  const handleSubmenuToggleVisibility = async (menuData, sub_menu_id) => {
    try {
      setSubmenuLoadingId(sub_menu_id);

      // Toggle submenu visibility locally
      const updatedSubmenus = menuData.submenus.map((submenu) =>
        submenu.sub_menu_id === sub_menu_id
          ? { ...submenu, is_visible: !submenu.is_visible }
          : submenu
      );

      const updatedData = { ...menuData, submenus: updatedSubmenus };

      await updateMenu(updatedData);

      // Update local UI
      setMenus((prev) =>
        prev.map((m) => (m.menu_id === updatedData.menu_id ? updatedData : m))
      );

      toast.success("Submenu visibility updated!");
    } catch (err) {
      console.error(err);
      if (err.response?.status === 413) {
        toast.error("Entity too large. Please upload another one.");
      } else {
        toast.error(err.response?.data?.message || "Failed to update submenu!");
      }
    } finally {
      setSubmenuLoadingId(null);
    }
  };

  const handleMenuToggleVisibility = async (menuData) => {
    try {
      setMenuLoadingId(menuData.menu_id);

      const updatedData = {
        ...menuData,
        is_visible: !menuData.is_visible,
      };

      await updateMenu(updatedData);

      // Update local UI
      setMenus((prev) =>
        prev.map((m) => (m.menu_id === updatedData.menu_id ? updatedData : m))
      );

      toast.success("Menu visibility updated!");
    } catch (err) {
      console.error(err);
      if (err.response?.status === 413) {
        toast.error("Entity too large. Please upload another one.");
      } else {
        toast.error(err.response?.data?.message || "Failed to update menu!");
      }
    } finally {
      setMenuLoadingId(null);
    }
  };

  return (
    <div className="overflow-x-auto border border-gray-200 rounded-lg">
      <DndContext
        sensors={sensors}
        collisionDetection={closestCenter}
        onDragEnd={handleDragEnd}
      >
        <SortableContext items={menus} strategy={verticalListSortingStrategy}>
          <table className="min-w-full border-collapse">
            <thead className="bg-gray-100 text-sm">
              <tr>
                <th className="w-8 border-b"></th>
                <th className="px-4 py-2 text-left border-b">Menu Title</th>
                <th className="px-4 py-2 text-center border-b">Language</th>
                <th className="px-4 py-2 text-center border-b">Visible</th>
                <th className="px-4 py-2 text-center border-b">Submenus</th>
                {showAction && (
                  <th className="px-4 py-2 text-center border-b">Actions</th>
                )}
              </tr>
            </thead>

            <tbody>
              {menus.map((menu) => {
                const isExpanded = expandedMenus.includes(menu.menu_id);
                return (
                  <React.Fragment key={menu.menu_id}>
                    {/* ---- Sortable Menu Row ---- */}
                    <SortableRow menu={menu}>
                      <td
                        className="px-4 py-3 border-b font-medium flex items-center gap-2 cursor-pointer"
                        onClick={() => toggleExpand(menu.menu_id)}
                      >
                        {isExpanded ? (
                          <ChevronUp className="w-4 h-4 text-gray-500" />
                        ) : (
                          <ChevronDown className="w-4 h-4 text-gray-500" />
                        )}
                        {menu.name}
                      </td>

                      <td className="px-4 py-3 border-b text-center capitalize">
                        {menu.lang === "en" ? "English" : "Hindi"}
                      </td>

                      <td className="px-4 py-3 border-b text-center">
                        <button
                          onClick={() => handleMenuToggleVisibility(menu)}
                          disabled={menuLoadingId === menu.menu_id}
                          className={`px-3 py-1 rounded-full text-sm font-medium flex items-center justify-center gap-1 ${
                            menu.is_visible
                              ? "bg-green-100 text-green-700 border border-green-300"
                              : "bg-gray-100 text-gray-700 border border-gray-300"
                          }`}
                        >
                          {menuLoadingId === menu.menu_id ? (
                            <CircularProgress size={14} color="inherit" />
                          ) : menu.is_visible ? (
                            "Active"
                          ) : (
                            "Inactive"
                          )}
                        </button>
                      </td>

                      <td className="px-4 py-3 border-b text-center">
                        {menu.submenus?.length || 0}
                      </td>

                      {showAction && (
                        <td
                          className="px-4 py-3 border-b text-center flex justify-center gap-2"
                          onClick={(e) => e.stopPropagation()}
                        >
                          <button
                            onClick={() => onEdit(menu)}
                            className="text-blue-600 hover:text-blue-800"
                            title="Edit Menu"
                          >
                            <Pencil className="w-5 h-5" />
                          </button>

                          {loadingDelMenu === menu.menu_id ? (
                            <CircularProgress size={20} />
                          ) : (
                            <button
                              onClick={() => onDelete(menu.menu_id)}
                              className="text-red-600 hover:text-red-800"
                              title="Delete Menu"
                            >
                              <Trash2 className="w-5 h-5" />
                            </button>
                          )}

                          <button
                            onClick={() => navigate("/message")}
                            className="text-green-600 hover:text-green-800"
                            title="Go to Messages"
                          >
                            <MessageCircle className="w-5 h-5" />
                          </button>

                          <button
                            onClick={() => navigate("/intent")}
                            className="text-purple-600 hover:text-purple-800"
                            title="Go to Intents"
                          >
                            <Target className="w-5 h-5" />
                          </button>
                        </td>
                      )}
                    </SortableRow>

                    {/* ---- Expanded Submenus ---- */}
                    {isExpanded && (
                      <tr>
                        <td
                          colSpan={showAction ? 6 : 5}
                          className="bg-gray-50 border-b"
                        >
                          <div className="p-4 space-y-4">
                            <DndContext
                              sensors={sensors}
                              collisionDetection={closestCenter}
                              onDragEnd={(event) =>
                                handleSubmenuDragEnd(event, menu.menu_id)
                              }
                            >
                              <SortableContext
                                items={(menu.submenus || []).map(
                                  (s) => s.sub_menu_id
                                )}
                                strategy={verticalListSortingStrategy}
                              >
                                {(menu.submenus || []).map((submenu) => (
                                  <SortableSubmenu
                                    key={submenu.sub_menu_id}
                                    submenu={submenu}
                                  >
                                    <div>
                                      {/* Header */}
                                      <div
                                        className="p-3 border-b flex justify-between items-center"
                                        onClick={(e) => e.stopPropagation()}
                                      >
                                        {/* Left section with drag handle + name */}
                                        <div className="flex items-center gap-2">
                                          {/* 🔹 Drag handle (four dots) */}
                                          <GripVertical className="w-4 h-4 text-gray-400 cursor-grab active:cursor-grabbing" />

                                          <div>
                                            <h3 className="font-semibold text-gray-800">
                                              {submenu.name}
                                            </h3>
                                            <p className="text-xs text-gray-500">
                                              {submenu.lang === "en"
                                                ? "English"
                                                : "Hindi"}{" "}
                                              |{" "}
                                              <button
                                                onClick={() =>
                                                  handleSubmenuToggleVisibility(
                                                    menu,
                                                    submenu.sub_menu_id
                                                  )
                                                }
                                                disabled={
                                                  submenuLoadingId ===
                                                  submenu.sub_menu_id
                                                }
                                                className={`items-center mb-2 gap-1 px-2 py-1 rounded-lg text-sm ${
                                                  submenu.is_visible
                                                    ? "bg-green-100 text-green-700"
                                                    : "bg-gray-100 text-gray-600"
                                                }`}
                                              >
                                                {submenuLoadingId ===
                                                submenu.sub_menu_id ? (
                                                  <CircularProgress
                                                    size={12}
                                                    color="inherit"
                                                  />
                                                ) : submenu.is_visible ? (
                                                  <>Active</>
                                                ) : (
                                                  <>Inactive</>
                                                )}
                                              </button>
                                            </p>
                                          </div>
                                        </div>

                                        {/* Right side: intents count + delete button */}
                                        <div className="flex items-center gap-3">
                                          <span className="text-sm text-gray-500">
                                            {submenu.intents?.length || 0}{" "}
                                            intents
                                          </span>

                                          {loadingDelSubmenu ===
                                          submenu.sub_menu_id ? (
                                            <CircularProgress size={18} />
                                          ) : (
                                            showAction && (
                                              <button
                                                type="button"
                                                onPointerDown={(e) =>
                                                  e.stopPropagation()
                                                }
                                                onMouseDown={(e) =>
                                                  e.stopPropagation()
                                                }
                                                onClick={(e) => {
                                                  e.stopPropagation();
                                                  onDeleteSubmenu(
                                                    submenu.sub_menu_id,
                                                    menu.menu_id
                                                  );
                                                }}
                                                className="text-red-600 hover:text-red-800"
                                                title="Delete submenu"
                                              >
                                                <Trash className="w-4 h-4" />
                                              </button>
                                            )
                                          )}
                                        </div>
                                      </div>

                                      {/* Intents */}
                                      <div className="p-3 space-y-3">
                                        {(submenu.intents || []).map(
                                          (intent) => {
                                            const isExampleExpanded =
                                              expandedExamples[
                                                intent.intent_id
                                              ];
                                            const examples =
                                              intent.examples || [];
                                            const displayedExamples =
                                              isExampleExpanded
                                                ? examples
                                                : examples.slice(0, 5);
                                            const utters = intent.utters || [];
                                            const actions =
                                              intent.actions || [];

                                            return (
                                              <div
                                                key={intent.intent_id}
                                                className="bg-gray-50 rounded-md p-3 border"
                                              >
                                                <p className="font-medium text-gray-700 mb-1">
                                                  🧠 {intent.name}
                                                </p>

                                                {/* Examples */}
                                                {examples.length > 0 && (
                                                  <>
                                                    <p className="text-sm font-semibold text-gray-600">
                                                      🗣️ Examples:
                                                    </p>
                                                    <ul className="list-disc pl-5 text-sm text-gray-600 mb-2">
                                                      {displayedExamples.map(
                                                        (ex, idx) => (
                                                          <li key={idx}>
                                                            {ex.example || ex}
                                                          </li>
                                                        )
                                                      )}
                                                    </ul>
                                                    {examples.length > 5 && (
                                                      <button
                                                        onClick={() =>
                                                          toggleExamples(
                                                            intent.intent_id
                                                          )
                                                        }
                                                        className="mt-1 text-blue-600 text-sm hover:underline"
                                                      >
                                                        {isExampleExpanded
                                                          ? "Show less"
                                                          : `Show ${
                                                              examples.length -
                                                              5
                                                            } more`}
                                                      </button>
                                                    )}
                                                  </>
                                                )}

                                                {/* Utters */}
                                                {utters.length > 0 && (
                                                  <>
                                                    <p className="text-sm font-semibold text-gray-600 mt-3">
                                                      💬 Utters:
                                                    </p>
                                                    <ul className="list-disc pl-5 text-sm text-gray-600">
                                                      {utters.map((u, idx) => (
                                                        <li key={idx}>
                                                          {u.name
                                                            ? `${u.name}: ${
                                                                u.response || ""
                                                              }`
                                                            : typeof u ===
                                                              "string"
                                                            ? u
                                                            : ""}
                                                        </li>
                                                      ))}
                                                    </ul>
                                                  </>
                                                )}

                                                {/* Actions */}
                                                {actions.length > 0 && (
                                                  <>
                                                    <p className="text-sm font-semibold text-gray-600 mt-3">
                                                      ⚙️ Actions:
                                                    </p>
                                                    <ul className="list-disc pl-5 text-sm text-gray-600">
                                                      {actions.map((a, idx) => (
                                                        <li key={idx}>
                                                          {a.name || a}
                                                        </li>
                                                      ))}
                                                    </ul>
                                                  </>
                                                )}
                                              </div>
                                            );
                                          }
                                        )}
                                      </div>
                                    </div>
                                  </SortableSubmenu>
                                ))}
                              </SortableContext>
                            </DndContext>
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                );
              })}
            </tbody>
          </table>
        </SortableContext>
      </DndContext>
    </div>
  );
}
