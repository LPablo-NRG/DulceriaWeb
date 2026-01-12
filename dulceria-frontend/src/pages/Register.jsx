import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Alert, Box, Button, Paper, Stack, TextField, Typography } from "@mui/material";
import { useAuth } from "../auth";

export default function Register() {
  const { register } = useAuth();
  const nav = useNavigate();

  const [nombre, setNombre] = useState("");
  const [telefono, setTelefono] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState("");

  async function submit(e) {
    e.preventDefault();
    setErr("");
    try {
      await register({
        nombre: nombre.trim(),
        telefono: telefono.trim() || undefined,
        email: email.trim().toLowerCase(),
        password,
      });
      nav("/");
    } catch (e2) {
      setErr(e2.message);
    }
  }

  return (
    <Box sx={{ maxWidth: 520, mx: "auto", mt: 8 }}>
      <Paper sx={{ p: 3 }}>
        <Typography variant="h5" fontWeight={900} gutterBottom>Crear cuenta</Typography>
        {err && <Alert severity="error" sx={{ mb: 2 }}>{err}</Alert>}

        <Box component="form" onSubmit={submit}>
          <Stack spacing={2}>
            <TextField label="Nombre / negocio" value={nombre} onChange={(e) => setNombre(e.target.value)} />
            <TextField label="Teléfono (opcional)" value={telefono} onChange={(e) => setTelefono(e.target.value)} />
            <TextField label="Email" value={email} onChange={(e) => setEmail(e.target.value)} />
            <TextField label="Password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
            <Button variant="contained" type="submit">Registrarme</Button>
            <Button variant="text" onClick={() => nav("/login")}>Ya tengo cuenta</Button>
          </Stack>
        </Box>
      </Paper>
    </Box>
  );
}
