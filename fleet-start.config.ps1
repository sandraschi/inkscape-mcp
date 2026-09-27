# Per-repo fleet start config for inkscape-mcp
# Edit ports/backend target here - start.ps1 is fleet-standard.
@{
    Name         = 'inkscape-mcp'
    BackendPort  = 11028
    FrontendPort = 11029
    HealthPath   = '/api/health'
    WebRoot      = 'web_sota'
    Backend = @{
        Kind          = 'uvicorn'
        UvicornTarget = 'inkscape_mcp.server:app'
        SyncExtras    = @('dev')
        Env           = @{ WEB_PORT = '11028' }
    }
    Frontend = @{
        Kind           = 'vite-npm'
        PackageManager = 'npm'
        PortEnvVar     = 'VITE_PORT'
        ApiTargetEnv   = 'VITE_API_TARGET'
    }
}
