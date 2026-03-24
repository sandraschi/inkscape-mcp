export interface ToolResult {
    content: Array<{
        type: string;
        text?: string;
        [key: string]: any;
    }>;
    isError?: boolean;
}

class MCPClient {
    private baseUrl: string;

    constructor() {
        this.baseUrl = '/mcp';
    }

    async listTools() {
        try {
            const response = await fetch(`${this.baseUrl}/tools`);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error("Failed to list tools:", error);
            throw error;
        }
    }

    async callTool(name: string, args: Record<string, any> = {}): Promise<any> {
        try {
            const response = await fetch(`${this.baseUrl}/tools/${name}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ arguments: args }),
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `Tool call failed: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error(`Error calling tool ${name}:`, error);
            throw error;
        }
    }
}

export const mcpClient = new MCPClient();
