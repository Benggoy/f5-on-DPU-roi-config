# ROI Config MCP Server

A secure MCP server for updating the F5 DPU ROI Calculator configuration.

## Security Features

- Single File Access: Can ONLY read/write roi-config Rev 08.json
- - No Other File Access: Cannot access any other files
  - - Write Confirmation: Requires user_confirmed=True for writes
    - - Auto-Backup: Creates timestamped backup before every write
     
      - ## Installation
     
      - 1. Download this folder to your Mac
        2. 2. Install dependencies: pip install -r requirements.txt
           3. 3. Add to Claude Desktop config
             
              4. ## Claude Desktop Config
             
              5. Add to ~/Library/Application Support/Claude/claude_desktop_config.json
             
              6. ## Available Tools
             
              7. - roi_config_status - Check server status
                 - - roi_config_read - Read config sections
                   - - roi_config_research - Generate research prompts
                     - - roi_config_apply - Apply updates (requires user_confirmed=True)
