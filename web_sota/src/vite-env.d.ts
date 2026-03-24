/// <reference types="vite/client" />

interface ImportMetaEnv {
    readonly VITE_API_URL?: string;
    readonly VITE_MCP_HOST?: string;
    readonly VITE_MCP_PORT?: string;
}

interface ImportMeta {
    readonly env: ImportMetaEnv;
}
