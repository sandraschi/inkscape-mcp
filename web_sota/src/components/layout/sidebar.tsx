import {
  Activity,
  Archive,
  Bot,
  ChevronLeft,
  ChevronRight,
  CircleHelp,
  Code2,
  FlaskConical,
  Grid3X3,
  Layers,
  LayoutDashboard,
  ScrollText,
  Server,
  Settings,
  Sparkles,
  Wand2,
  Zap,
} from "lucide-react";
import { Link, useLocation } from "react-router-dom";
import { cn } from "@/common/utils";

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

export function Sidebar({ collapsed, onToggle }: SidebarProps) {
  const location = useLocation();

  const navItems = [
    { href: "/", label: "Overview", icon: LayoutDashboard },
    { href: "/agent-tools", label: "Agent Lab", icon: FlaskConical },
    { href: "/svg-studio", label: "SVG Studio", icon: Wand2 },
    { href: "/actions", label: "Vector Actions", icon: Zap },
    { href: "/animation", label: "Animation", icon: Sparkles },
    { href: "/layers", label: "Layers", icon: Layers },
    { href: "/depot", label: "Depot", icon: Archive },
    { href: "/logs", label: "Logs", icon: ScrollText },
    { href: "/chat", label: "Chat", icon: Bot },
    { href: "/skills", label: "Skills", icon: Sparkles },
    { href: "/apps", label: "Apps", icon: Grid3X3 },
    { href: "/api-docs", label: "API Docs", icon: Code2 },
    { href: "/settings", label: "Settings", icon: Settings },
    { href: "/status", label: "Status", icon: Server },
    { href: "/help", label: "Help", icon: CircleHelp },
  ];

  return (
    <aside
      className={cn(
        "relative flex flex-col border-r border-slate-800 bg-slate-950/50 backdrop-blur-xl transition-all duration-300 ease-in-out",
        collapsed ? "w-16" : "w-64",
      )}
    >
      <div className="flex h-16 items-center border-b border-slate-800 px-4">
        <div className="flex items-center gap-2 font-semibold text-slate-100">
          <Activity className="h-6 w-6 text-blue-500" />
          {!collapsed && (
            <span className="animate-in fade-in duration-300">
              Inkscape-MCP
            </span>
          )}
        </div>
        <button
          type="button"
          onClick={onToggle}
          className="ml-auto flex items-center justify-center rounded-md p-1.5 text-slate-300 hover:bg-slate-800 hover:text-white transition-colors"
          title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {collapsed ? (
            <ChevronRight className="h-4 w-4" />
          ) : (
            <ChevronLeft className="h-4 w-4" />
          )}
        </button>
      </div>

      <nav className="flex-1 space-y-1 p-2">
        {navItems.map((item) => {
          const isActive = location.pathname === item.href;
          return (
            <Link
              key={item.href}
              to={item.href}
              data-testid={`nav-${item.label.toLowerCase().replace(/\s+/g, "-")}`}
              className={cn(
                "group flex items-center rounded-md px-3 py-2 text-sm font-medium transition-colors hover:bg-slate-800 hover:text-white",
                isActive ? "bg-slate-800 text-white" : "text-slate-300",
                collapsed ? "justify-center" : "justify-start",
              )}
            >
              <item.icon
                className={cn(
                  "h-5 w-5",
                  !collapsed && "mr-3",
                  isActive && "text-blue-400",
                )}
              />
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
    </aside>
  );
}
