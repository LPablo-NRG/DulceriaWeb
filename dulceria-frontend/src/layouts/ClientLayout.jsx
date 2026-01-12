import { Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../auth";
import { AppBar, Box, Button, Container, Toolbar, Typography } from "@mui/material";

export default function ClientLayout() {
  const { me, logout } = useAuth();
  const nav = useNavigate();

  return (
    <Box>
      <AppBar position="sticky">
        <Toolbar>
          <Typography fontWeight={900} sx={{ flexGrow: 1 }}>
            Dulcería Mayoreo
          </Typography>

          <Button color="inherit" onClick={() => nav("/")}>Catálogo</Button>
          <Button color="inherit" onClick={() => nav("/orders")}>Mis pedidos</Button>
          {me?.role === "admin" && <Button color="inherit" onClick={() => nav("/admin")}>Admin</Button>}

          <Button color="inherit" onClick={() => { logout(); nav("/login"); }}>
            Salir
          </Button>
        </Toolbar>
      </AppBar>

      <Container sx={{ py: 3 }}>
        <Outlet />
      </Container>
    </Box>
  );
}
