import {
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Button,
  Divider,
  Box,
  Typography,
  Table,
  TableHead,
  TableRow,
  TableCell,
  TableBody,
} from "@mui/material";
import { money } from "../utils/format";

function formatDate(iso) {
  try {
    const d = iso ? new Date(iso) : new Date();
    return d.toLocaleString("es-MX");
  } catch {
    return "";
  }
}

function buildTicketHtml(order) {
  const createdAt = formatDate(order?.created_at);
  const customer = order?.customer?.nombre || "Cliente";
  const items = order?.items || [];

  const rows = items
    .map(
      (it) => `
      <tr>
        <td style="padding:4px 0;">${it.qty}x</td>
        <td style="padding:4px 0;">${(it.product_nombre || `Producto #${it.product_id}`).slice(0, 26)}</td>
        <td style="padding:4px 0;text-align:right;">${Number(it.line_total || 0).toFixed(2)}</td>
      </tr>
    `
    )
    .join("");

  return `
  <!doctype html>
  <html lang="es">
  <head>
    <meta charset="utf-8" />
    <title>Ticket Pedido #${order.id}</title>
    <style>
      body{font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
           margin:0; padding:12px; }
      .ticket{width:80mm; max-width:80mm;}
      h1{font-size:14px; margin:0; text-align:center;}
      .muted{color:#555; font-size:12px;}
      .line{border-top:1px dashed #999; margin:10px 0;}
      table{width:100%; border-collapse:collapse; font-size:12px;}
      .right{text-align:right;}
      .center{text-align:center;}
      @media print {
        body{padding:0;}
      }
    </style>
  </head>
  <body>
    <div class="ticket">
      <h1>DULCERÍA MAYOREO</h1>
      <div class="muted center">Ticket de compra</div>
      <div class="line"></div>

      <div class="muted">Pedido: #${order.id}</div>
      <div class="muted">Fecha: ${createdAt}</div>
      <div class="muted">Cliente: ${customer}</div>

      <div class="line"></div>

      <table>
        <thead>
          <tr>
            <th style="text-align:left;">Qty</th>
            <th style="text-align:left;">Producto</th>
            <th class="right">Importe</th>
          </tr>
        </thead>
        <tbody>
          ${rows}
        </tbody>
      </table>

      <div class="line"></div>

      <div style="display:flex; justify-content:space-between; font-size:12px;">
        <div><b>Total</b></div>
        <div><b>${Number(order.total || 0).toFixed(2)}</b></div>
      </div>

      <div class="line"></div>
      <div class="muted center">Gracias por su compra</div>
    </div>

    <script>
      window.onload = () => { window.focus(); window.print(); };
    </script>
  </body>
  </html>
  `;
}

function printTicket(order) {
  const w = window.open("", "_blank", "width=420,height=650");
  if (!w) return;
  w.document.open();
  w.document.write(buildTicketHtml(order));
  w.document.close();
}

export default function TicketDialog({ open, onClose, order }) {
  if (!order) return null;

  const items = order.items || [];

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm">
      <DialogTitle>Ticket · Pedido #{order.id}</DialogTitle>

      <DialogContent sx={{ pt: 1 }}>
        <Box sx={{ fontFamily: "ui-monospace, monospace" }}>
          <Typography fontWeight={900} align="center">
            DULCERÍA MAYOREO
          </Typography>
          <Typography color="text.secondary" align="center" variant="body2">
            Ticket de compra
          </Typography>

          <Divider sx={{ my: 2 }} />

          <Typography variant="body2">Pedido: #{order.id}</Typography>
          <Typography variant="body2">Fecha: {formatDate(order.created_at)}</Typography>
          {order.customer && (
            <Typography variant="body2">Cliente: {order.customer.nombre}</Typography>
          )}

          <Divider sx={{ my: 2 }} />

          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell><b>Qty</b></TableCell>
                <TableCell><b>Producto</b></TableCell>
                <TableCell align="right"><b>Importe</b></TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {items.map((it) => (
                <TableRow key={it.id}>
                  <TableCell>{it.qty}</TableCell>
                  <TableCell>
                    {(it.product_nombre || `Producto #${it.product_id}`)}
                    <Typography variant="caption" color="text.secondary" sx={{ display: "block" }}>
                      {it.product_sku || ""}
                    </Typography>
                  </TableCell>
                  <TableCell align="right">{money(it.line_total)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>

          <Divider sx={{ my: 2 }} />

          <Box sx={{ display: "flex", justifyContent: "space-between" }}>
            <Typography fontWeight={900}>Total</Typography>
            <Typography fontWeight={900}>{money(order.total)}</Typography>
          </Box>

          <Typography color="text.secondary" align="center" variant="body2" sx={{ mt: 2 }}>
            Gracias por su compra
          </Typography>
        </Box>
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose}>Cerrar</Button>
        <Button variant="contained" onClick={() => printTicket(order)}>
          Imprimir
        </Button>
      </DialogActions>
    </Dialog>
  );
}
