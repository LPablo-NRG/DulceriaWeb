import { Outlet, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../auth";
import {
  AppBar, Box, Drawer, List, ListItemButton, ListItemText,
  Toolbar, Typography, Button, Divider
} from "@mui/material";

const drawerWidth = 260;

export default function AdminLayout() {
  const { logout } = useAuth();
  const nav = useNavigate();
  const loc = useLocation();

  const items = [
    { label: "Dashboard", path: "/admin" },
    { label: "Productos", path: "/admin/products" },
    { label: "Clientes", path: "/admin/customers" },
    { label: "Usuarios", path: "/admin/users" },
    { label: "Pedidos", path: "/admin/orders" },
  ];

  return (
    <Box sx={{ display: "flex" }}>
      <AppBar position="fixed" sx={{ zIndex: 1201 }}>
        <Toolbar>
          <Typography fontWeight={900} sx={{ flexGrow: 1 }}>Admin</Typography>
          <Button color="inherit" onClick={() => nav("/")}>Ir a tienda</Button>
          <Button color="inherit" onClick={() => { logout(); nav("/login"); }}>Salir</Button>
        </Toolbar>
      </AppBar>

      <Drawer
        variant="permanent"
        sx={{
          width: drawerWidth,
          [`& .MuiDrawer-paper`]: { width: drawerWidth, boxSizing: "border-box" },
        }}
      >
        <Toolbar />
        <Box sx={{ p: 1 }}>
          <List>
            {items.map((it) => (
              <ListItemButton
                key={it.path}
                selected={loc.pathname === it.path}
                onClick={() => nav(it.path)}
              >
                <ListItemText primary={it.label} />
              </ListItemButton>
            ))}
          </List>
        </Box>
        <Divider />
      </Drawer>

      <Box component="main" sx={{ flexGrow: 1, p: 3 }}>
        <Toolbar />
        <Outlet />
      </Box>
    </Box>
  );
}
