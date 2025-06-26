# Sort GitHub Repositories by Creation Date

A script to list all of your GitHub repositories sorted by their creation date

## Usage

1. [Generate a Personal Access Token (PAT)](https://github.com/settings/personal-access-tokens) with the `Metadata` scope (`public_repo` and/or `repo` scope for classic tokens) for all repositories (or just the ones you want to include in the sort)
2. Create a `config.json` file in this folder with the structure below
3. Run the `run.sh` file to run the script

### config.json

```json
{
  "username": "REPLACE_WITH_GITHUB_USERNAME",
  "token": "REPLACE_WITH_PAT",
  "direction": "ASC"
}
```

`direction` can either be `ASC` for the oldest repositories first or `DESC` for the newest repositories first
