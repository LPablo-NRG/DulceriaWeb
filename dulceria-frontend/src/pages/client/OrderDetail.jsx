import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../../api";
import { money } from "../../utils/format";
import {
  Alert,
  Box,
  Divider,
  Paper,
  Stack,
  Typography,
} from "@mui/material";

export default function OrderDetail() {
  const { id } = useParams();
  const [order, setOrder] = useState(null);
  const [err, setErr] = useState("");

  async function load() {
    setErr("");
    try {
      const o = await api(`/api/orders/${id}`);
      setOrder(o);
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
              {order.customer.email || "—"} · Tel: {order.customer.telefono || "n/a"}
            </Typography>
          </>
        )}
      </Paper>

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
                Qty: {it.qty} · Unit: {money(it.unit_price)} · Subtotal:{" "}
                {money(it.line_total)}
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
