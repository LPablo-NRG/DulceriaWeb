import { useEffect, useState } from "react";
import { api } from "../../api";
import { money } from "../../utils/format";
import {
  Alert,
  Box,
  Button,
  MenuItem,
  Paper,
  Stack,
  TextField,
  Typography,
} from "@mui/material";

export default function AdminOrders() {
  const [orders, setOrders] = useState([]);
  const [status, setStatus] = useState("");
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");

  async function load() {
    const qs = status ? `?status=${encodeURIComponent(status)}` : "";
    const list = await api(`/api/orders${qs}`);
    setOrders(list);
  }

  useEffect(() => {
    load();
  }, [status]);

  async function setOrderStatus(orderId, newStatus) {
    setMsg("");
    setErr("");
    try {
      await api(`/api/orders/${orderId}/status`, {
        method: "PUT",
        body: { status: newStatus },
      });
      setMsg(`Pedido #${orderId} actualizado a "${newStatus}".`);
      await load();
    } catch (e) {
      setErr(e.message);
    }
  }

  return (
    <Box sx={{ display: "grid", gap: 2 }}>
      <Paper sx={{ p: 2 }}>
        <Stack direction="row" spacing={2} alignItems="center">
          <Typography fontWeight={900} variant="h6" sx={{ flexGrow: 1 }}>
            Pedidos
          </Typography>

          <TextField
            select
            label="Filtro status"
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            sx={{ width: 220 }}
          >
            <MenuItem value="">(todos)</MenuItem>
            <MenuItem value="pendiente">pendiente</MenuItem>
            <MenuItem value="pagado">pagado</MenuItem>
            <MenuItem value="cancelado">cancelado</MenuItem>
          </TextField>
        </Stack>

        {msg && (
          <Alert severity="success" sx={{ mt: 2 }} onClose={() => setMsg("")}>
            {msg}
          </Alert>
        )}
        {err && (
          <Alert severity="error" sx={{ mt: 2 }} onClose={() => setErr("")}>
            {err}
          </Alert>
        )}

        <Stack spacing={1} sx={{ mt: 2 }}>
          {orders.map((o) => (
            <Paper key={o.id} variant="outlined" sx={{ p: 2 }}>
              <Stack direction="row" justifyContent="space-between" alignItems="center">
                <Box>
                  <Typography fontWeight={900}>Pedido #{o.id}</Typography>
                  <Typography color="text.secondary">
                    Customer: {o.customer_id} · Status: {o.status}
                  </Typography>
                  <Typography>Total: {money(o.total)}</Typography>
                </Box>

                <Stack direction="row" spacing={1}>
                  <Button
                    variant="outlined"
                    onClick={() => setOrderStatus(o.id, "pagado")}
                    disabled={o.status === "pagado" || o.status === "cancelado"}
                  >
                    Marcar pagado
                  </Button>

                  <Button
                    color="error"
                    onClick={() => setOrderStatus(o.id, "cancelado")}
                    disabled={o.status === "cancelado"}
                  >
                    Cancelar
                  </Button>
                </Stack>
              </Stack>
            </Paper>
          ))}

          {!orders.length && (
            <Typography color="text.secondary">Sin pedidos</Typography>
          )}
        </Stack>
      </Paper>
    </Box>
  );
}
