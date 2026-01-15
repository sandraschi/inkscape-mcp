use zed_extension_api as zed;

struct InkscapeMcpExtension;

impl zed::Extension for InkscapeMcpExtension {
    fn context_server_command(
        &mut self,
        id: &zed::ContextServerId,
        _project: &zed::Project,
    ) -> zed::Result<zed::Command> {
        match id.0.as_str() {
            "inkscape-mcp" => Ok(zed::Command {
                command: "uv".to_string(),
                args: vec!["run".to_string(), "inkscape-mcp".to_string()],
                env: Default::default(),
            }),
            _ => Err(format!("Unknown server: {}", id.0)),
        }
    }
}

zed::register_extension!(InkscapeMcpExtension);