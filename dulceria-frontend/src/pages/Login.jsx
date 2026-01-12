import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Alert, Box, Button, Paper, TextField, Typography } from "@mui/material";
import { useAuth } from "../auth";

export default function Login() {
  const { login } = useAuth();
  const nav = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState("");

  async function submit(e) {
    e.preventDefault();
    setErr("");
    try {
      await login(email, password);
      nav("/");
    } catch (e2) {
      setErr(e2.message);
    }
  }

  return (
    <Box sx={{ maxWidth: 420, mx: "auto", mt: 10 }}>
      <Paper sx={{ p: 3 }}>
        <Typography variant="h5" fontWeight={900} gutterBottom>Login</Typography>
        {err && <Alert severity="error" sx={{ mb: 2 }}>{err}</Alert>}

        <Box component="form" onSubmit={submit} sx={{ display: "grid", gap: 2 }}>
          <TextField label="Email" value={email} onChange={(e) => setEmail(e.target.value)} />
          <TextField label="Password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
          <Button variant="contained" type="submit">Entrar</Button>
        </Box>
        <Button variant="text" onClick={() => nav("/register")}>
            Crear cuenta
        </Button>

      </Paper>
    </Box>
  );
}
