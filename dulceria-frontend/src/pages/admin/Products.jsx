import { useEffect, useState } from "react";
import { api } from "../../api";
import { money } from "../../utils/format";
import {
  Alert, Box, Button, Dialog, DialogActions, DialogContent, DialogTitle,
  Paper, Stack, TextField, Typography, Divider
} from "@mui/material";

export default function AdminProducts() {
  const [products, setProducts] = useState([]);
  const [err, setErr] = useState("");

  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState({ sku: "", nombre: "", precio_mayoreo: "", stock: "" });

  const [tiersOpen, setTiersOpen] = useState(false);
  const [tiersProduct, setTiersProduct] = useState(null);
  const [tiers, setTiers] = useState([]);
  const [tierForm, setTierForm] = useState({ min_qty: "", unit_price: "" });

  async function load() {
    const list = await api("/api/products");
    setProducts(list);
  }

  useEffect(() => { load(); }, []);

  function startCreate() {
    setEditing(null);
    setForm({ sku: "", nombre: "", precio_mayoreo: "", stock: "" });
    setOpen(true);
  }

  function startEdit(p) {
    setEditing(p);
    setForm({
      sku: p.sku || "",
      nombre: p.nombre || "",
      precio_mayoreo: String(p.precio_mayoreo ?? ""),
      stock: String(p.stock ?? ""),
    });
    setOpen(true);
  }

  async function save() {
    setErr("");
    try {
      const body = {
        sku: form.sku.trim(),
        nombre: form.nombre.trim(),
        precio_mayoreo: Number(form.precio_mayoreo),
        stock: Number(form.stock),
        activo: true,
      };

      if (!body.sku || !body.nombre) throw new Error("sku y nombre son obligatorios");

      if (editing) await api(`/api/products/${editing.id}`, { method: "PUT", body });
      else await api("/api/products", { method: "POST", body });

      setOpen(false);
      await load();
    } catch (e) {
      setErr(e.message);
    }
  }

  async function deactivate(id) {
    await api(`/api/products/${id}`, { method: "DELETE" });
    await load();
  }

  async function openTiers(p) {
    setTiersProduct(p);
    const list = await api(`/api/products/${p.id}/price-tiers`);
    setTiers(list);
    setTierForm({ min_qty: "", unit_price: "" });
    setTiersOpen(true);
  }

  async function addTier() {
    setErr("");
    try {
      const body = { min_qty: Number(tierForm.min_qty), unit_price: Number(tierForm.unit_price) };
      await api(`/api/products/${tiersProduct.id}/price-tiers`, { method: "POST", body });
      const list = await api(`/api/products/${tiersProduct.id}/price-tiers`);
      setTiers(list);
      setTierForm({ min_qty: "", unit_price: "" });
    } catch (e) {
      setErr(e.message);
    }
  }

  async function deleteTier(id) {
    await api(`/api/price-tiers/${id}`, { method: "DELETE" });
    const list = await api(`/api/products/${tiersProduct.id}/price-tiers`);
    setTiers(list);
  }

  return (
    <Box sx={{ display: "grid", gap: 2 }}>
      <Paper sx={{ p: 2 }}>
        <Stack direction="row" justifyContent="space-between" alignItems="center">
          <Typography fontWeight={900} variant="h6">Productos</Typography>
          <Button variant="contained" onClick={startCreate}>Nuevo</Button>
        </Stack>

        {err && <Alert severity="error" sx={{ mt: 2 }}>{err}</Alert>}

        <Stack spacing={1} sx={{ mt: 2 }}>
          {products.map(p => (
            <Paper key={p.id} variant="outlined" sx={{ p: 2 }}>
              <Stack direction="row" justifyContent="space-between" alignItems="center">
                <Box>
                  <Typography fontWeight={800}>{p.nombre} (#{p.id})</Typography>
                  <Typography color="text.secondary">SKU: {p.sku} · Stock: {p.stock}</Typography>
                  <Typography fontWeight={900}>{money(p.precio_mayoreo)}</Typography>
                </Box>
                <Stack direction="row" spacing={1}>
                  <Button variant="outlined" onClick={() => openTiers(p)}>Tiers</Button>
                  <Button variant="outlined" onClick={() => startEdit(p)}>Editar</Button>
                  <Button color="error" onClick={() => deactivate(p.id)}>Desactivar</Button>
                </Stack>
              </Stack>
            </Paper>
          ))}
        </Stack>
      </Paper>

      <Dialog open={open} onClose={() => setOpen(false)} fullWidth maxWidth="sm">
        <DialogTitle>{editing ? "Editar producto" : "Nuevo producto"}</DialogTitle>
        <DialogContent sx={{ display: "grid", gap: 2, pt: 1 }}>
          <TextField label="SKU" value={form.sku} onChange={(e) => setForm(f => ({ ...f, sku: e.target.value }))} />
          <TextField label="Nombre" value={form.nombre} onChange={(e) => setForm(f => ({ ...f, nombre: e.target.value }))} />
          <TextField label="Precio mayoreo" type="number" value={form.precio_mayoreo} onChange={(e) => setForm(f => ({ ...f, precio_mayoreo: e.target.value }))} />
          <TextField label="Stock" type="number" value={form.stock} onChange={(e) => setForm(f => ({ ...f, stock: e.target.value }))} />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)}>Cancelar</Button>
          <Button variant="contained" onClick={save}>Guardar</Button>
        </DialogActions>
      </Dialog>

      <Dialog open={tiersOpen} onClose={() => setTiersOpen(false)} fullWidth maxWidth="sm">
        <DialogTitle>Tiers · {tiersProduct?.nombre}</DialogTitle>
        <DialogContent sx={{ pt: 1 }}>
          <Typography color="text.secondary">Reglas min_qty → unit_price</Typography>
          <Divider sx={{ my: 2 }} />

          <Stack direction="row" spacing={1}>
            <TextField
              label="min_qty"
              type="number"
              value={tierForm.min_qty}
              onChange={(e) => setTierForm(f => ({ ...f, min_qty: e.target.value }))}
              sx={{ width: 160 }}
            />
            <TextField
              label="unit_price"
              type="number"
              value={tierForm.unit_price}
              onChange={(e) => setTierForm(f => ({ ...f, unit_price: e.target.value }))}
              sx={{ width: 200 }}
            />
            <Button variant="contained" onClick={addTier}>Agregar</Button>
          </Stack>

          <Divider sx={{ my: 2 }} />

          <Stack spacing={1}>
            {tiers.map(t => (
              <Stack key={t.id} direction="row" justifyContent="space-between" alignItems="center">
                <Typography>Desde {t.min_qty} → {money(t.unit_price)}</Typography>
                <Button color="error" onClick={() => deleteTier(t.id)}>Eliminar</Button>
              </Stack>
            ))}
            {!tiers.length && <Typography color="text.secondary">Sin tiers</Typography>}
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setTiersOpen(false)}>Cerrar</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
