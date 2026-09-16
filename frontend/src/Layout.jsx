import React, { useContext } from 'react';
import { Outlet, Link, useNavigate, useLocation } from 'react-router-dom';
import { AuthContext } from './AuthContext';
import { Shield, Activity, Database, Lock, Share2, FileText, User, LogOut, LayoutDashboard } from 'lucide-react';

export default function Layout() {
    const { user, logout } = useContext(AuthContext);
    const navigate = useNavigate();
    const location = useLocation();

    if (!user) return <Outlet />;

    const navItems = [
        { path: '/', label: 'Dashboard', icon: LayoutDashboard, roles: ['ADMIN', 'DOCTOR', 'LAB', 'PATIENT'] },
        { path: '/records', label: 'Records', icon: Database, roles: ['ADMIN', 'DOCTOR', 'LAB', 'PATIENT'] },
        { path: '/integrity', label: 'Integrity Demo', icon: Shield, roles: ['ADMIN', 'DOCTOR', 'LAB', 'PATIENT'] },
        { path: '/blockchain', label: 'Blockchain Explorer', icon: Activity, roles: ['ADMIN'] },
        { path: '/sharing', label: 'Sharing', icon: Share2, roles: ['PATIENT'] },
        { path: '/audit', label: 'Audit Logs', icon: FileText, roles: ['ADMIN', 'DOCTOR', 'LAB'] }
    ];

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    return (
        <div className="flex h-screen bg-gray-100">
            <aside className="w-64 bg-gray-900 text-white flex flex-col">
                <div className="p-4 flex items-center gap-3 border-b border-gray-800">
                    <Shield className="w-8 h-8 text-blue-500" />
                    <div>
                        <h1 className="text-xl font-bold">HealthChain</h1>
                        <p className="text-xs text-gray-400">Secure Records</p>
                    </div>
                </div>
                <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
                    {navItems.filter(item => item.roles.includes(user.role)).map(item => {
                        const Icon = item.icon;
                        const isActive = location.pathname === item.path;
                        return (
                            <Link key={item.path} to={item.path} className={`flex items-center gap-3 px-3 py-2 rounded-md transition-colors ${isActive ? 'bg-blue-600 text-white' : 'text-gray-300 hover:bg-gray-800 hover:text-white'}`}>
                                <Icon className="w-5 h-5" />
                                {item.label}
                            </Link>
                        );
                    })}
                </nav>
                <div className="p-4 border-t border-gray-800">
                    <div className="flex items-center gap-3 mb-4">
                        <div className="w-10 h-10 rounded-full bg-gray-700 flex items-center justify-center">
                            <User className="w-6 h-6 text-gray-400" />
                        </div>
                        <div>
                            <p className="text-sm font-medium">{user.username}</p>
                            <p className="text-xs text-gray-400">{user.role}</p>
                        </div>
                    </div>
                    <button onClick={handleLogout} className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors w-full">
                        <LogOut className="w-4 h-4" />
                        Logout
                    </button>
                </div>
            </aside>
            <main className="flex-1 flex flex-col overflow-hidden">
                <header className="bg-white border-b px-6 py-4 flex justify-between items-center">
                    <h2 className="text-xl font-semibold text-gray-800 capitalize">
                        {location.pathname === '/' ? 'Dashboard' : location.pathname.slice(1)}
                    </h2>
                </header>
                <div className="flex-1 overflow-auto p-6">
                    <Outlet />
                </div>
            </main>
        </div>
    );
}
