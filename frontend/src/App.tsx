import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import DashboardLayout from './pages/Home';
import Login from './pages/Login';
import PrivateRoute from './components/PrivateRoute';
import Dashboard from './pages/Dashboard';
import Recipes from './pages/Recipes';
import Ingredients from './pages/Ingredients';
import Orders from './pages/Orders';
import OrderDetail from './pages/OrderDetail';
import ImportedRecords from './pages/ImportedRecords';
import OpsHome from './pages/OpsHome';

export default function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/" element={<PrivateRoute />}>
            <Route path="/" element={<DashboardLayout />}>
              <Route path="dashboard" element={<Dashboard />} />
              <Route path="recipes" element={<Recipes />} />
              <Route path="ingredients" element={<Ingredients />} />
              <Route path="ops" element={<OpsHome />} />
              <Route path="orders" element={<Orders />} />
              <Route path="orders/imported" element={<ImportedRecords />} />
              <Route path="orders/:orderId" element={<OrderDetail />} />
              <Route index element={<Navigate to="/ops" replace />} />
            </Route>
          </Route>
        </Routes>
      </Router>
    </AuthProvider>
  );
}
