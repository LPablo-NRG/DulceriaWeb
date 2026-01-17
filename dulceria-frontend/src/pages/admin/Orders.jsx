import { useEffect, useState } from "react";
import { api } from "../../api";
import { money } from "../../utils/format";
import {
  Alert,
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  MenuItem,
  Paper,
  Stack,
  TextField,
  Typography,
  Divider,
} from "@mui/material";

const METHODS = [
  { value: "efectivo", label: "Efectivo" },
  { value: "transferencia", label: "Transferencia" },
  { value: "cheque", label: "Cheque" },
  { value: "tarjeta", label: "Pago con tarjeta" },
];

function toDatetimeLocalValue(d = new Date()) {
  const pad = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(
    d.getHours()
  )}:${pad(d.getMinutes())}`;
}

function formatDate(iso) {
  try {
    return new Date(iso).toLocaleString("es-MX");
  } catch {
    return iso || "—";
  }
}

export default function AdminOrders() {
  const [orders, setOrders] = useState([]);
  const [status, setStatus] = useState("");
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");

  // dialog registrar pago (solo pendiente)
  const [payOpen, setPayOpen] = useState(false);
  const [payOrder, setPayOrder] = useState(null);
  const [payForm, setPayForm] = useState({
    method: "efectivo",
    paid_at: toDatetimeLocalValue(new Date()),
    received_by: "",
    reference: "",
  });

  // dialog ver pago (solo pagado)
  const [infoOpen, setInfoOpen] = useState(false);
  const [infoOrder, setInfoOrder] = useState(null);
  const [paymentInfo, setPaymentInfo] = useState(null);

  async function load() {
    const qs = status ? `?status=${encodeURIComponent(status)}` : "";
    const list = await api(`/api/orders${qs}`);
    setOrders(list);
  }

  useEffect(() => {
    load();
  }, [status]);

  function openPayDialog(order) {
    setMsg("");
    setErr("");
    setPayOrder(order);
    setPayForm({
      method: "efectivo",
      paid_at: toDatetimeLocalValue(new Date()),
      received_by: "",
      reference: "",
    });
    setPayOpen(true);
  }

  async function savePayment() {
    if (!payOrder) return;
    setMsg("");
    setErr("");

    try {
      await api(`/api/admin/orders/${payOrder.id}/payment`, {
        method: "POST",
        body: {
          method: payForm.method,
          paid_at: payForm.paid_at,
          received_by: payForm.received_by,
          reference: payForm.reference || undefined,
        },
      });

      setPayOpen(false);
      setMsg(`Pago registrado. Pedido #${payOrder.id} marcado como pagado.`);
      await load();
    } catch (e) {
      setErr(e.message);
    }
  }

  async function openPaymentInfo(order) {
    setMsg("");
    setErr("");
    setInfoOrder(order);
    setPaymentInfo(null);
    setInfoOpen(true);

    try {
      const p = await api(`/api/admin/orders/${order.id}/payment`);
      setPaymentInfo(p);
    } catch (e) {
      setErr(e.message);
      setInfoOpen(false);
    }
  }

  async function cancel(orderId) {
    setMsg("");
    setErr("");
    try {
      await api(`/api/orders/${orderId}/status`, {
        method: "PUT",
        body: { status: "cancelado" },
      });
      setMsg(`Pedido #${orderId} cancelado.`);
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
                  {o.status === "pendiente" && (
                    <>
                      <Button variant="outlined" onClick={() => openPayDialog(o)}>
                        Registrar pago
                      </Button>
                      <Button color="error" onClick={() => cancel(o.id)}>
                        Cancelar
                      </Button>
                    </>
                  )}

                  {o.status === "pagado" && (
                    <Button variant="outlined" onClick={() => openPaymentInfo(o)}>
                      Ver pago
                    </Button>
                  )}

                  {/* cancelado -> sin acciones */}
                </Stack>
              </Stack>
            </Paper>
          ))}

          {!orders.length && (
            <Typography color="text.secondary">Sin pedidos</Typography>
          )}
        </Stack>
      </Paper>

      {/* Dialog registrar pago */}
      <Dialog open={payOpen} onClose={() => setPayOpen(false)} fullWidth maxWidth="sm">
        <DialogTitle>Registrar pago (Pedido #{payOrder?.id})</DialogTitle>

        <DialogContent sx={{ display: "grid", gap: 2, pt: 1 }}>
          <Typography color="text.secondary">
            Total del pedido: <b>{money(payOrder?.total)}</b> (siempre)
          </Typography>

          <TextField
            select
            label="Forma de pago"
            value={payForm.method}
            onChange={(e) => setPayForm((f) => ({ ...f, method: e.target.value }))}
          >
            {METHODS.map((m) => (
              <MenuItem key={m.value} value={m.value}>
                {m.label}
              </MenuItem>
            ))}
          </TextField>

          <TextField
            label="Fecha de pago"
            type="datetime-local"
            value={payForm.paid_at}
            onChange={(e) => setPayForm((f) => ({ ...f, paid_at: e.target.value }))}
            InputLabelProps={{ shrink: true }}
          />

          <TextField
            label="Responsable (quién recibió/registró)"
            value={payForm.received_by}
            onChange={(e) => setPayForm((f) => ({ ...f, received_by: e.target.value }))}
          />

          <TextField
            label="Referencia / Folio (opcional)"
            value={payForm.reference}
            onChange={(e) => setPayForm((f) => ({ ...f, reference: e.target.value }))}
          />
        </DialogContent>

        <DialogActions>
          <Button onClick={() => setPayOpen(false)}>Cerrar</Button>
          <Button
            variant="contained"
            onClick={savePayment}
            disabled={!payForm.received_by.trim()}
          >
            Guardar
          </Button>
        </DialogActions>
      </Dialog>

      {/* Dialog ver pago (solo lectura) */}
      <Dialog open={infoOpen} onClose={() => setInfoOpen(false)} fullWidth maxWidth="sm">
        <DialogTitle>Pago registrado (Pedido #{infoOrder?.id})</DialogTitle>

        <DialogContent sx={{ pt: 1 }}>
          <Typography color="text.secondary">
            Total del pedido: <b>{money(infoOrder?.total)}</b>
          </Typography>

          <Divider sx={{ my: 2 }} />

          {!paymentInfo ? (
            <Typography color="text.secondary">Cargando…</Typography>
          ) : (
            <Stack spacing={1}>
              <Typography><b>Método:</b> {paymentInfo.method}</Typography>
              <Typography><b>Fecha de pago:</b> {formatDate(paymentInfo.paid_at)}</Typography>
              <Typography><b>Responsable:</b> {paymentInfo.received_by}</Typography>
              <Typography>
                <b>Referencia:</b> {paymentInfo.reference || "—"}
              </Typography>
            </Stack>
          )}
        </DialogContent>

        <DialogActions>
          <Button onClick={() => setInfoOpen(false)}>Cerrar</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
