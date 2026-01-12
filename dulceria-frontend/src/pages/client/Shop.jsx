import { useEffect, useMemo, useState } from "react";
import { api } from "../../api";
import { money } from "../../utils/format";
import {
  Alert,
  Box,
  Button,
  Card,
  CardActions,
  CardContent,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  Drawer,
  IconButton,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from "@mui/material";
import ShoppingCartIcon from "@mui/icons-material/ShoppingCart";

function pickTier(tiers, qty, fallbackPrice) {
  const list = Array.isArray(tiers) ? [...tiers] : [];
  list.sort((a, b) => Number(a.min_qty) - Number(b.min_qty));

  let applied = null;
  for (const t of list) {
    if (qty >= Number(t.min_qty)) applied = t;
  }

  if (applied) {
    return {
      unitPrice: Number(applied.unit_price),
      minQty: Number(applied.min_qty),
    };
  }

  return {
    unitPrice: Number(fallbackPrice),
    minQty: null,
  };
}

export default function Shop() {
  const [q, setQ] = useState("");
  const [products, setProducts] = useState([]);

  // carrito: [{ product, qty }]
  const [cart, setCart] = useState([]);
  const [cartOpen, setCartOpen] = useState(false);

  // tiers cache: { [productId]: tiers[] }
  const [tiersByProduct, setTiersByProduct] = useState({});

  // dialog agregar
  const [addOpen, setAddOpen] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [selectedQty, setSelectedQty] = useState(1);
  const [tiersLoading, setTiersLoading] = useState(false);
  const [msg, setMsg] = useState(null); // { type, text }

  async function loadProducts() {
    const qs = q.trim() ? `?q=${encodeURIComponent(q.trim())}` : "";
    const list = await api(`/api/products${qs}`);
    setProducts(list);
  }

  useEffect(() => {
    loadProducts();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function ensureTiers(productId) {
    if (tiersByProduct[productId]) return tiersByProduct[productId];

    setTiersLoading(true);
    try {
      const tiers = await api(`/api/products/${productId}/price-tiers`, { auth: false });
      setTiersByProduct((prev) => ({ ...prev, [productId]: tiers }));
      return tiers;
    } finally {
      setTiersLoading(false);
    }
  }

  async function openAddDialog(product) {
    setMsg(null);
    setSelectedProduct(product);
    setSelectedQty(1);
    setAddOpen(true);

    try {
      await ensureTiers(product.id);
    } catch (e) {
      // si falla, igual dejamos que agregue con precio base
      setMsg({ type: "warning", text: "No se pudieron cargar tiers. Se usará precio base." });
    }
  }

  function addToCart(product, qty) {
    setCart((prev) => {
      const copy = [...prev];
      const found = copy.find((x) => x.product.id === product.id);
      if (found) found.qty += qty;
      else copy.push({ product, qty });
      return copy;
    });
  }

  function setCartQty(productId, qty) {
    setCart((prev) =>
      prev.map((x) =>
        x.product.id === productId ? { ...x, qty: Math.max(1, qty) } : x
      )
    );
  }

  function removeFromCart(productId) {
    setCart((prev) => prev.filter((x) => x.product.id !== productId));
  }

  const cartCount = useMemo(
    () => cart.reduce((a, c) => a + c.qty, 0),
    [cart]
  );

  const cartComputed = useMemo(() => {
    const lines = cart.map((c) => {
      const tiers = tiersByProduct[c.product.id] || [];
      const { unitPrice, minQty } = pickTier(tiers, c.qty, c.product.precio_mayoreo);
      const lineTotal = unitPrice * c.qty;
      return { ...c, unitPrice, minQty, lineTotal };
    });

    const total = lines.reduce((a, x) => a + x.lineTotal, 0);
    return { lines, total };
  }, [cart, tiersByProduct]);

  async function checkout() {
    setMsg(null);
    if (!cart.length) return;

    try {
      const items = cart.map((c) => ({ product_id: c.product.id, qty: c.qty }));
      const order = await api("/api/orders", { method: "POST", body: { items } });

      setCart([]);
      setCartOpen(false);

      setMsg({
        type: "success",
        text: `Pedido #${order.id} creado. Total final: ${money(order.total)}.`,
      });

      await loadProducts(); // stock cambia
    } catch (e) {
      setMsg({ type: "error", text: e.message });
    }
  }

  // datos del dialog "Agregar"
  const selectedTiers = selectedProduct ? (tiersByProduct[selectedProduct.id] || []) : [];
  const appliedInDialog = useMemo(() => {
    if (!selectedProduct) return null;
    return pickTier(selectedTiers, selectedQty, selectedProduct.precio_mayoreo);
  }, [selectedProduct, selectedTiers, selectedQty]);

  return (
    <Box>
      <Stack direction={{ xs: "column", sm: "row" }} spacing={2} sx={{ mb: 2 }}>
        <TextField
          label="Buscar (sku o nombre)"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          fullWidth
        />
        <Button variant="outlined" onClick={loadProducts}>Buscar</Button>

        <IconButton onClick={() => setCartOpen(true)} aria-label="Abrir carrito">
          <ShoppingCartIcon />
          <Typography sx={{ ml: 1 }} fontWeight={800}>{cartCount}</Typography>
        </IconButton>
      </Stack>

      {msg && (
        <Alert severity={msg.type} sx={{ mb: 2 }} onClose={() => setMsg(null)}>
          {msg.text}
        </Alert>
      )}

      <Box sx={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))", gap: 2 }}>
        {products.map((p) => (
          <Card key={p.id}>
            <CardContent>
              <Typography fontWeight={900}>{p.nombre}</Typography>
              <Typography variant="body2" color="text.secondary">SKU: {p.sku}</Typography>
              <Typography variant="body2" color="text.secondary">Stock: {p.stock}</Typography>
              <Typography sx={{ mt: 1 }} fontWeight={900}>{money(p.precio_mayoreo)}</Typography>
            </CardContent>
            <CardActions>
              <Button variant="contained" onClick={() => openAddDialog(p)} disabled={p.stock <= 0}>
                Agregar al carrito
              </Button>
            </CardActions>
          </Card>
        ))}
      </Box>

      {/* Dialog para agregar con tiers */}
      <Dialog open={addOpen} onClose={() => setAddOpen(false)} fullWidth maxWidth="sm">
        <DialogTitle>Agregar al carrito</DialogTitle>
        <DialogContent sx={{ pt: 1 }}>
          {!selectedProduct ? null : (
            <>
              <Typography fontWeight={900}>{selectedProduct.nombre}</Typography>
              <Typography color="text.secondary">SKU: {selectedProduct.sku} · Stock: {selectedProduct.stock}</Typography>

              <Stack direction="row" spacing={2} sx={{ mt: 2, alignItems: "center" }}>
                <TextField
                  label="Cantidad"
                  type="number"
                  value={selectedQty}
                  onChange={(e) => setSelectedQty(Math.max(1, parseInt(e.target.value || "1", 10)))}
                  sx={{ width: 160 }}
                  inputProps={{ min: 1, max: selectedProduct.stock }}
                />

                {tiersLoading && <CircularProgress size={22} />}

                {appliedInDialog && (
                  <Box>
                    <Typography fontWeight={900}>
                      Unitario aplicado: {money(appliedInDialog.unitPrice)}
                    </Typography>
                    <Typography color="text.secondary">
                      {appliedInDialog.minQty
                        ? `Aplica desde ${appliedInDialog.minQty} unidades`
                        : "Sin tier (precio base)"}
                    </Typography>
                    <Typography fontWeight={900}>
                      Subtotal: {money(appliedInDialog.unitPrice * selectedQty)}
                    </Typography>
                  </Box>
                )}
              </Stack>

              <Divider sx={{ my: 2 }} />

              <Typography fontWeight={900} sx={{ mb: 1 }}>Precios por volumen</Typography>

              {selectedTiers.length ? (
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell><b>Desde (min_qty)</b></TableCell>
                      <TableCell><b>Precio unitario</b></TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {[...selectedTiers]
                      .sort((a, b) => Number(a.min_qty) - Number(b.min_qty))
                      .map((t) => (
                        <TableRow key={t.id}>
                          <TableCell>{t.min_qty}</TableCell>
                          <TableCell>{money(t.unit_price)}</TableCell>
                        </TableRow>
                      ))}
                  </TableBody>
                </Table>
              ) : (
                <Typography color="text.secondary">Este producto no tiene tiers configurados.</Typography>
              )}

              <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                El total final lo valida el backend al crear el pedido.
              </Typography>
            </>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAddOpen(false)}>Cancelar</Button>
          <Button
            variant="contained"
            onClick={() => {
              if (!selectedProduct) return;
              addToCart(selectedProduct, selectedQty);
              setAddOpen(false);
              setCartOpen(true);
            }}
            disabled={!selectedProduct}
          >
            Agregar
          </Button>
        </DialogActions>
      </Dialog>

      {/* Carrito */}
      <Drawer anchor="right" open={cartOpen} onClose={() => setCartOpen(false)}>
        <Box sx={{ width: 420, p: 2 }}>
          <Typography variant="h6" fontWeight={900}>Carrito</Typography>
          <Divider sx={{ my: 2 }} />

          {!cart.length ? (
            <Typography color="text.secondary">Vacío</Typography>
          ) : (
            <Stack spacing={2}>
              {cartComputed.lines.map((c) => (
                <Box key={c.product.id}>
                  <Typography fontWeight={900}>{c.product.nombre}</Typography>
                  <Typography variant="body2" color="text.secondary">SKU: {c.product.sku}</Typography>

                  <Stack direction="row" spacing={1} sx={{ mt: 1, alignItems: "center" }}>
                    <TextField
                      size="small"
                      label="Qty"
                      type="number"
                      value={c.qty}
                      onChange={async (e) => {
                        const qty = Math.max(1, parseInt(e.target.value || "1", 10));
                        // si todavía no tenemos tiers, cargarlos (para que el precio reaccione)
                        await ensureTiers(c.product.id).catch(() => {});
                        setCartQty(c.product.id, qty);
                      }}
                      sx={{ width: 120 }}
                      inputProps={{ min: 1 }}
                    />

                    <Button color="error" onClick={() => removeFromCart(c.product.id)}>Quitar</Button>
                  </Stack>

                  <Typography sx={{ mt: 1 }}>
                    Unit: <b>{money(c.unitPrice)}</b>{" "}
                    <Typography component="span" color="text.secondary">
                      {c.minQty ? `(desde ${c.minQty})` : "(base)"}
                    </Typography>
                  </Typography>
                  <Typography>
                    Subtotal: <b>{money(c.lineTotal)}</b>
                  </Typography>

                  <Divider sx={{ mt: 2 }} />
                </Box>
              ))}

              <Typography fontWeight={900}>
                Total (con mayoreo): {money(cartComputed.total)}
              </Typography>

              <Button variant="contained" onClick={checkout}>
                Crear pedido
              </Button>
            </Stack>
          )}
        </Box>
      </Drawer>
    </Box>
  );
}
