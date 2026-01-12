import { useEffect, useState } from "react";
import { api } from "../../api";
import {
  Alert, Box, Button, MenuItem, Paper, Stack, TextField, Typography
} from "@mui/material";

export default function AdminUsers() {
  const [users, setUsers] = useState([]);
  const [customers, setCustomers] = useState([]);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("cliente");
  const [customerId, setCustomerId] = useState("");

  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");

  async function load() {
    const [u, c] = await Promise.all([
      api("/api/admin/users"),
      api("/api/customers"), // admin-only en tu backend
    ]);
    setUsers(u);
    setCustomers(c);
  }

  useEffect(() => { load(); }, []);

  async function createUser() {
    setMsg(""); setErr("");
    try {
      const body = {
        email: email.trim().toLowerCase(),
        password,
        role,
        customer_id: role === "cliente" && customerId ? Number(customerId) : undefined,
      };

      await api("/api/auth/users", { method: "POST", body });
      setMsg("Usuario creado.");
      setEmail(""); setPassword(""); setCustomerId("");
      await load();
    } catch (e) {
      setErr(e.message);
    }
  }

  return (
    <Box sx={{ display: "grid", gap: 2 }}>
      <Paper sx={{ p: 2 }}>
        <Typography fontWeight={900} variant="h6">Crear usuario</Typography>
        {msg && <Alert severity="success" sx={{ mt: 1 }}>{msg}</Alert>}
        {err && <Alert severity="error" sx={{ mt: 1 }}>{err}</Alert>}

        <Stack spacing={2} sx={{ mt: 2, maxWidth: 520 }}>
          <TextField label="Email" value={email} onChange={(e) => setEmail(e.target.value)} />
          <TextField label="Password" value={password} onChange={(e) => setPassword(e.target.value)} type="password" />
          <TextField select label="Role" value={role} onChange={(e) => setRole(e.target.value)}>
            <MenuItem value="cliente">cliente</MenuItem>
            <MenuItem value="admin">admin</MenuItem>
          </TextField>

          <TextField
            select
            label="Cliente ligado (solo role=cliente)"
            value={customerId}
            onChange={(e) => setCustomerId(e.target.value)}
            disabled={role !== "cliente"}
          >
            <MenuItem value="">(sin ligar)</MenuItem>
            {customers.map(c => (
              <MenuItem key={c.id} value={String(c.id)}>{c.nombre} (#{c.id})</MenuItem>
            ))}
          </TextField>

          <Button variant="contained" onClick={createUser}>Crear</Button>
        </Stack>
      </Paper>

      <Paper sx={{ p: 2 }}>
        <Typography fontWeight={900} variant="h6">Usuarios</Typography>
        <Stack spacing={1} sx={{ mt: 1 }}>
          {users.map(u => (
            <Typography key={u.id}>
              #{u.id} · {u.email} · {u.role} · customer_id: {u.customer_id ?? "-"}
            </Typography>
          ))}
        </Stack>
      </Paper>
    </Box>
  );
}
