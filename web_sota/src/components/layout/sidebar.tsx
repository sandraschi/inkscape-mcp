import { Link, useLocation } from 'react-router-dom';
import { cn } from '@/common/utils';
import {
    LayoutDashboard,
    Bot,
    Settings,
    ChevronLeft,
    ChevronRight,
    Activity,
    Zap,
    ScrollText,
    Wand2
} from 'lucide-react';

interface SidebarProps {
    collapsed: boolean;
    onToggle: () => void;
}

export function Sidebar({ collapsed, onToggle }: SidebarProps) {
    const location = useLocation();

    const navItems = [
        { href: '/', label: 'Overview', icon: LayoutDashboard },
        { href: '/svg-studio', label: 'SVG Studio', icon: Wand2 },
        { href: '/actions', label: 'Vector Actions', icon: Zap },
        { href: '/logs', label: 'System Logs', icon: ScrollText },
        { href: '/chat', label: 'AI Command', icon: Bot },
        { href: '/settings', label: 'Settings', icon: Settings },
    ];

    return (
        <aside
            className={cn(
                "relative flex flex-col border-r border-slate-800 bg-slate-950/50 backdrop-blur-xl transition-all duration-300 ease-in-out",
                collapsed ? "w-16" : "w-64"
            )}
        >
            <div className="flex h-16 items-center border-b border-slate-800 px-4">
                <div className="flex items-center gap-2 font-semibold text-slate-100">
                    <Activity className="h-6 w-6 text-blue-500" />
                    {!collapsed && <span className="animate-in fade-in duration-300">Inkscape-MCP</span>}
                </div>
            </div>

            <nav className="flex-1 space-y-1 p-2">
                {navItems.map((item) => {
                    const isActive = location.pathname === item.href;
                    return (
                        <Link
                            key={item.href}
                            to={item.href}
                            className={cn(
                                "group flex items-center rounded-md px-3 py-2 text-sm font-medium transition-colors hover:bg-slate-800 hover:text-white",
                                isActive ? "bg-slate-800 text-white" : "text-slate-400",
                                collapsed ? "justify-center" : "justify-start"
                            )}
                        >
                            <item.icon className={cn("h-5 w-5", !collapsed && "mr-3", isActive && "text-blue-400")} />
                            {!collapsed && <span>{item.label}</span>}

                            {/* Tooltip for collapsed mode */}
                            {collapsed && (
                                <div className="absolute left-full ml-2 hidden rounded bg-slate-800 px-2 py-1 text-xs text-white group-hover:block z-50 whitespace-nowrap">
                                    {item.label}
                                </div>
                            )}
                        </Link>
                    );
                })}
            </nav>

            <div className="border-t border-slate-800 p-2">
                <button
                    onClick={onToggle}
                    className="flex w-full items-center justify-center rounded-md p-2 text-slate-400 hover:bg-slate-800 hover:text-white transition-colors"
                >
                    {collapsed ? <ChevronRight className="h-5 w-5" /> : <div className="flex items-center w-full"><ChevronLeft className="h-5 w-5 mr-3" /><span>Collapse</span></div>}
                </button>
            </div>
        </aside>
    );
}
