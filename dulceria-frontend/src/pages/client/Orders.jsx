import { useEffect, useState } from "react";
import { api } from "../../api";
import { money } from "../../utils/format";
import { useNavigate } from "react-router-dom";
import { Box, Button, Paper, Stack, Typography } from "@mui/material";

export default function Orders() {
  const [orders, setOrders] = useState([]);
  const nav = useNavigate();

  useEffect(() => {
    (async () => {
      const list = await api("/api/orders");
      setOrders(list);
    })();
  }, []);

  return (
    <Box sx={{ display: "grid", gap: 2 }}>
      {orders.map(o => (
        <Paper key={o.id} sx={{ p: 2 }}>
          <Stack direction="row" justifyContent="space-between" alignItems="center">
            <Box>
              <Typography fontWeight={900}>Pedido #{o.id}</Typography>
              <Typography color="text.secondary">Status: {o.status}</Typography>
              <Typography>Total: {money(o.total)}</Typography>
            </Box>
            <Button variant="outlined" onClick={() => nav(`/orders/${o.id}`)}>Ver</Button>
          </Stack>
        </Paper>
      ))}
    </Box>
  );
}
