import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider, useAuth } from "./auth";

import Login from "./pages/Login";
import Register from "./pages/Register";

import ClientLayout from "./layouts/ClientLayout";
import AdminLayout from "./layouts/AdminLayout";

import Shop from "./pages/client/Shop";
import Orders from "./pages/client/Orders";
import OrderDetail from "./pages/client/OrderDetail";

import AdminDashboard from "./pages/admin/Dashboard";
import AdminProducts from "./pages/admin/Products";
import AdminCustomers from "./pages/admin/Customers";
import AdminUsers from "./pages/admin/Users";
import AdminOrders from "./pages/admin/Orders";


function RequireAuth({ children }) {
  const { me, loading } = useAuth();
  if (loading) return null;
  return me ? children : <Navigate to="/login" replace />;
}

function RequireAdmin({ children }) {
  const { me, loading } = useAuth();
  if (loading) return null;
  if (!me) return <Navigate to="/login" replace />;
  return me.role === "admin" ? children : <Navigate to="/" replace />;
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />


          <Route path="/" element={<RequireAuth><ClientLayout /></RequireAuth>}>
            <Route index element={<Shop />} />
            <Route path="orders" element={<Orders />} />
            <Route path="orders/:id" element={<OrderDetail />} />
          </Route>

          <Route path="/admin" element={<RequireAdmin><AdminLayout /></RequireAdmin>}>
            <Route index element={<AdminDashboard />} />
            <Route path="products" element={<AdminProducts />} />
            <Route path="customers" element={<AdminCustomers />} />
            <Route path="users" element={<AdminUsers />} />
            <Route path="orders" element={<AdminOrders />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
