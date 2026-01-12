import { useEffect, useState } from "react";
import { api } from "../../api";
import {
  Alert, Box, Button, Dialog, DialogActions, DialogContent, DialogTitle,
  Paper, Stack, TextField, Typography
} from "@mui/material";

export default function AdminCustomers() {
  const [customers, setCustomers] = useState([]);
  const [err, setErr] = useState("");
  const [open, setOpen] = useState(false);

  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState({ nombre: "", email: "", telefono: "" });

  async function load() {
    const list = await api("/api/customers");
    setCustomers(list);
  }

  useEffect(() => { load(); }, []);

  function startCreate() {
    setEditing(null);
    setForm({ nombre: "", email: "", telefono: "" });
    setOpen(true);
  }

  function startEdit(c) {
    setEditing(c);
    setForm({ nombre: c.nombre || "", email: c.email || "", telefono: c.telefono || "" });
    setOpen(true);
  }

  async function save() {
    setErr("");
    try {
      if (!form.nombre.trim()) throw new Error("nombre es obligatorio");

      if (editing) {
        await api(`/api/customers/${editing.id}`, { method: "PUT", body: form });
      } else {
        await api("/api/customers", { method: "POST", body: form });
      }
      setOpen(false);
      await load();
    } catch (e) {
      setErr(e.message);
    }
  }

  async function deactivate(id) {
    await api(`/api/customers/${id}`, { method: "DELETE" });
    await load();
  }

  return (
    <Box sx={{ display: "grid", gap: 2 }}>
      <Paper sx={{ p: 2 }}>
        <Stack direction="row" justifyContent="space-between" alignItems="center">
          <Typography fontWeight={900} variant="h6">Clientes</Typography>
          <Button variant="contained" onClick={startCreate}>Nuevo</Button>
        </Stack>

        {err && <Alert severity="error" sx={{ mt: 2 }}>{err}</Alert>}

        <Stack spacing={1} sx={{ mt: 2 }}>
          {customers.map(c => (
            <Paper key={c.id} variant="outlined" sx={{ p: 2 }}>
              <Stack direction="row" justifyContent="space-between" alignItems="center">
                <Box>
                  <Typography fontWeight={800}>{c.nombre} #{c.id}</Typography>
                  <Typography color="text.secondary">{c.email || "-"} · {c.telefono || "-"}</Typography>
                </Box>
                <Stack direction="row" spacing={1}>
                  <Button variant="outlined" onClick={() => startEdit(c)}>Editar</Button>
                  <Button color="error" onClick={() => deactivate(c.id)}>Desactivar</Button>
                </Stack>
              </Stack>
            </Paper>
          ))}
        </Stack>
      </Paper>

      <Dialog open={open} onClose={() => setOpen(false)} fullWidth maxWidth="sm">
        <DialogTitle>{editing ? "Editar cliente" : "Nuevo cliente"}</DialogTitle>
        <DialogContent sx={{ display: "grid", gap: 2, pt: 1 }}>
          <TextField label="Nombre" value={form.nombre} onChange={(e) => setForm(f => ({ ...f, nombre: e.target.value }))} />
          <TextField label="Email" value={form.email} onChange={(e) => setForm(f => ({ ...f, email: e.target.value }))} />
          <TextField label="Teléfono" value={form.telefono} onChange={(e) => setForm(f => ({ ...f, telefono: e.target.value }))} />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)}>Cancelar</Button>
          <Button variant="contained" onClick={save}>Guardar</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
