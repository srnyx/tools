# Update Minecraft Projects Supported Versions

Script to automatically update all latest releases of Minecraft projects to support their corresponding Minecraft versions

This is primarily for personal use since it uses my custom API for retrieving project data, but it may be adapted for your own uses!

## `config.json`

`only-projects` is checked before `ignored-projects`, so if a project is in both, it will be ignored

```json
{
  "user-agent": "srnyx/tools (Update Projects' MC Versions)",

  "tokens": {
    "modrinth": "MODRINTH_TOKEN",
    "hangar": "HANGAR_TOKEN",
    "bukkit": {
      "upload-api": "BUKKIT_UPLOAD_API_TOKEN",
      "new-api": "BUKKIT_NEW_API_TOKEN"
    }
  },

  "only-projects": [],
  "ignored-projects": []
}
```

### Tokens

- **`modrinth`:** https://modrinth.com/settings/pats (requires `Write version` scope)
- **`hangar`:** https://hangar.papermc.io/auth/settings/api-keys (requires `view_public_info` and `edit_version` scopes)
- **`bukkit`**
  - **`upload-api`:** https://dev.bukkit.org/account/api-tokens (documentation: https://support.curseforge.com/en/support/solutions/articles/9000197321-curseforge-api)
  - **`new-api`:** https://forms.monday.com/forms/dce5ccb7afda9a1c21dab1a1aa1d84eb (documentation: https://docs.curseforge.com/rest-api)
