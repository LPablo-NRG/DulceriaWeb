import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../../api";
import { money } from "../../utils/format";
import { Alert, Box, Divider, Paper, Stack, Typography } from "@mui/material";

function formatDate(iso) {
  try {
    return new Date(iso).toLocaleString("es-MX");
  } catch {
    return iso || "—";
  }
}

export default function OrderDetail() {
  const { id } = useParams();
  const [order, setOrder] = useState(null);
  const [payment, setPayment] = useState(null);
  const [err, setErr] = useState("");

  async function load() {
    setErr("");
    try {
      const o = await api(`/api/orders/${id}`);
      setOrder(o);

      // Solo buscamos pago si el pedido está pagado
      if (o.status === "pagado") {
        const p = await api(`/api/orders/${id}/payment`);
        setPayment(p); // puede ser null si algo quedó raro
      } else {
        setPayment(null);
      }
    } catch (e) {
      setErr(e.message);
    }
  }

  useEffect(() => {
    load();
  }, [id]);

  if (err) return <Alert severity="error">{err}</Alert>;
  if (!order) return null;

  return (
    <Box sx={{ display: "grid", gap: 2 }}>
      <Paper sx={{ p: 2 }}>
        <Typography fontWeight={900}>Pedido #{order.id}</Typography>
        <Typography color="text.secondary">Status: {order.status}</Typography>
        <Typography fontWeight={900} sx={{ mt: 1 }}>
          Total: {money(order.total)}
        </Typography>

        {order.customer && (
          <>
            <Divider sx={{ my: 2 }} />
            <Typography fontWeight={800}>Cliente</Typography>
            <Typography color="text.secondary">
              {order.customer.nombre} (#{order.customer.id})
            </Typography>
            <Typography color="text.secondary">
              {order.customer.email || "—"} · {order.customer.telefono || "—"}
            </Typography>
          </>
        )}
      </Paper>

      {order.status === "pagado" && (
        <Paper sx={{ p: 2 }}>
          <Typography fontWeight={900}>Pago registrado</Typography>
          <Divider sx={{ my: 1 }} />

          {!payment ? (
            <Typography color="text.secondary">
              Sin información de pago (o aún no se registró).
            </Typography>
          ) : (
            <Stack spacing={1}>
              <Typography><b>Método:</b> {payment.method}</Typography>
              <Typography><b>Fecha de pago:</b> {formatDate(payment.paid_at)}</Typography>
              <Typography><b>Registrado por:</b> {payment.received_by}</Typography>
              <Typography><b>Referencia:</b> {payment.reference || "—"}</Typography>
              <Typography><b>Monto:</b> {money(order.total)}</Typography>
            </Stack>
          )}
        </Paper>
      )}

      <Paper sx={{ p: 2 }}>
        <Typography fontWeight={900}>Items</Typography>
        <Divider sx={{ my: 1 }} />

        <Stack spacing={1}>
          {(order.items || []).map((it) => (
            <Box key={it.id}>
              <Typography fontWeight={700}>
                {it.product_nombre || `Producto #${it.product_id}`}{" "}
                <Typography component="span" color="text.secondary">
                  ({it.product_sku || "—"})
                </Typography>
              </Typography>

              <Typography color="text.secondary">
                Qty: {it.qty} · Unit: {money(it.unit_price)} · Subtotal: {money(it.line_total)}
              </Typography>
            </Box>
          ))}

          {!order.items?.length && (
            <Typography color="text.secondary">Sin items</Typography>
          )}
        </Stack>
      </Paper>
    </Box>
  );
}
