import { useEffect, useState } from "react";
import { api } from "../../api";
import { money } from "../../utils/format";
import { Paper, Stack, Typography } from "@mui/material";

export default function AdminDashboard() {
  const [d, setD] = useState(null);

  useEffect(() => {
    (async () => {
      const dash = await api("/api/admin/dashboard");
      setD(dash);
    })();
  }, []);

  if (!d) return null;

  return (
    <Paper sx={{ p: 2 }}>
      <Typography fontWeight={900} variant="h6">Dashboard</Typography>
      <Stack sx={{ mt: 1 }} spacing={1}>
        <Typography>Órdenes: {d.orders_count}</Typography>
        <Typography>Pagadas: {d.paid_orders_count}</Typography>
        <Typography>Ganancias: {money(d.revenue_from_paid_orders)}</Typography>
        
      </Stack>
    </Paper>
  );
}
