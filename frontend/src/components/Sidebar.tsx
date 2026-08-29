import {
    History,
    LogOut,
    Scale,
    UploadCloud,
} from "lucide-react";

import type { User } from "../api";

type SidebarProps = {
    user: User;
    onLogout: () => void;
};

export default function Sidebar({
    user,
    onLogout,
}: SidebarProps) {
    return (
        <aside className="sidebar">

            <div className="sidebar-brand">
                <div className="sidebar-logo">
                    <Scale size={22} />
                </div>

                <strong>SAPIA</strong>
            </div>

            <nav className="nav-list">

                <button className="nav-item active">
                    <UploadCloud size={19} />
                    Enviar documento
                </button>

                <button className="nav-item">
                    <History size={19} />
                    Histórico
                </button>

            </nav>

            <div className="sidebar-bottom">

                <div className="user-mini-card">

                    <div className="avatar">
                        {user.name.charAt(0)}
                    </div>

                    <div>
                        <strong>{user.name}</strong>
                        <span>{user.role}</span>
                    </div>

                </div>

                <button
                    className="logout-button"
                    onClick={onLogout}
                >
                    <LogOut size={18} />
                    Sair
                </button>

            </div>

        </aside>
    );
}