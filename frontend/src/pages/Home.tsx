import { Link, Outlet } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function DashboardLayout() {
  const { logout } = useAuth();

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Sidebar */}
      <div className="w-64 bg-gray-800 text-white flex flex-col">
        <div className="px-8 py-4 text-2xl font-bold">BakeMate</div>
        <nav className="flex-grow">
          <Link to="/dashboard" className="block px-8 py-3 text-sm hover:bg-gray-700">Dashboard</Link>
          <Link to="/recipes" className="block px-8 py-3 text-sm hover:bg-gray-700">Recipes</Link>
          <Link to="/ingredients" className="block px-8 py-3 text-sm hover:bg-gray-700">Ingredients</Link>
          <Link to="/orders" className="block px-8 py-3 text-sm hover:bg-gray-700">Orders</Link>
          <Link to="/orders/imported" className="block px-8 py-3 text-sm hover:bg-gray-700">Imported records</Link>
          {/* Add more links as modules are created */}
        </nav>
        <div className="p-4">
          <button
            onClick={logout}
            className="w-full px-4 py-2 font-bold text-white bg-red-500 rounded-md hover:bg-red-600"
          >
            Logout
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <header className="bg-white shadow-md">
          <div className="px-6 py-4">
            <h1 className="text-xl font-semibold">Welcome!</h1>
          </div>
        </header>
        <main className="flex-1 overflow-x-hidden overflow-y-auto bg-gray-200 p-6">
          <Outlet /> {/* Child routes will be rendered here */}
        </main>
      </div>
    </div>
  );
}
