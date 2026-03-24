use zed_extension_api as zed;

struct InkscapeMcpExtension;

impl zed::Extension for InkscapeMcpExtension {
    fn new() -> Self {
        Self
    }

    fn context_server_command(
        &mut self,
        id: &zed::ContextServerId,
        _project: &zed::Project,
    ) -> zed::Result<zed::Command> {
        match id.as_ref() {
            "inkscape-mcp" => Ok(zed::Command {
                command: "uv".to_string(),
                args: vec!["run".to_string(), "inkscape-mcp".to_string()],
                env: Default::default(),
            }),
            _ => Err(format!("Unknown server: {}", id.as_ref())),
        }
    }
}

zed::register_extension!(InkscapeMcpExtension);