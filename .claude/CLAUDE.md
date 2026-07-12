### Search and File Discovery
Prefer dedicated internal tools over `Bash` for read-only inspection:
- **Content search**: Always use the native `Grep` tool. Never run `grep` or `rg` via the `Bash` tool.
- **File/path discovery**: Always use the native `Glob` tool. Never run `find` or `ls` via the `Bash` tool.
- **File reads**: Always use the native `Read` tool. Never run `cat`, `head`, `tail`, or `sed` via the `Bash` tool.