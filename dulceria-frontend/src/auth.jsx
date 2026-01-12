import React, { createContext, useContext, useEffect, useMemo, useState } from "react";
import { api, getToken, setToken } from "./api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [me, setMe] = useState(null);
  const [loading, setLoading] = useState(true);

  async function refreshMe() {
    if (!getToken()) {
      setMe(null);
      setLoading(false);
      return;
    }
    try {
      const user = await api("/api/auth/me");
      setMe(user);
    } catch {
      setToken(null);
      setMe(null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { refreshMe(); }, []);

  async function login(email, password) {
    const data = await api("/api/auth/login", {
      method: "POST",
      body: { email: email.trim().toLowerCase(), password },
      auth: false,
    });
    setToken(data.access_token);
    setMe(data.user);
    return data.user;
  }

  function logout() {
    setToken(null);
    setMe(null);
  }

    const value = useMemo(
        () => ({ me, loading, login, register, logout, refreshMe }),
        [me, loading]
        );

    async function register({ nombre, email, password, telefono, rfc, razon_social }) {
    const data = await api("/api/auth/register", {
        method: "POST",
        body: { nombre, email, password, telefono, rfc, razon_social },
        auth: false,
    });
    setToken(data.access_token);
    setMe(data.user);
    return data.user;
    }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}


