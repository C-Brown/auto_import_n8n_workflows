# n8n Workflow Auto-Importer & Fixer

This script automates the import of multiple n8n workflow `.json` files via the **n8n API**, resolves brokwn sub-workflow references, and ensures compatibility with the latest (Aug 2025) strict schema in `n8n v1`.

It is especially useful when:
- You've exported multiple interconnected workflows (parent + sub-workflows).
- Sub-workflow references break due to changing `workflowId`s after re-import.
- You want to automate re-import and patching without manually editing each file.

---

## Author

Created by Cameron Brown
https://github.com/C-Brown

---

## Features

- Loads all `.json` workflows from a folder (./workflows)
- Analyzes sub-workflow dependencies
- Automatically imports sub-workflows **before** parent workflows
- Fixes all `Execute Workflow` nodes with updated `workflowId` references
- Optionally activates imported workflows (optional)
- Ignores self-signed certs for local development
- Authenticated with `X-N8N-API-Key` (non-enterprise n8n)

---

## Folder Structure

Place your workflow files into a folder like this:

```
workflows/
├── subflow1.json
├── subflow2.json
├── parent_workflow.json
```

Each file must contain a single workflow exported from n8n via the "Export" button.

---

## Configuration

Edit the following variables in the script:

```python
N8N_API_URL = "https://your-n8n-server/api/v1"
API_KEY = "your_api_key_here"
WORKFLOW_DIR = "./workflows"
```

To ignore self-signed SSL errors (recommended for local/dev use), the script sets:

```python
verify=False
```

---

## Usage

1. Place all your workflow `.json` exports into the `./workflows` folder
2. Run the script:

```bash
python auto_import_n8n_workflows.py
```

The script will:

- Topologically sort workflows based on dependencies
- Import them in the correct order
- Automatically fix all broken `workflowId` references

---

## Dependencies

Install required packages:

```bash
pip install requests
```

or run:

```bash
pip install -r requirements.txt
```

---

## API Key Setup

Ensure your .env or container config for n8n includes:

```enc
N8N_API_AUTH_ACTIVE=true
N8N_API_KEY=your_api_key_here
```

---

## Example Output

```
Imported workflow 'subflow1' with ID: 101
Imported workflow 'subflow2' with ID: 102
Imported workflow 'parent_workflow' with ID: 103
```

---

## Known Limitations

- Does not currently auto-create tags (requires additional API call).
- Only works with workflows exported individually (not as bundles).
- Assumes unique workflow names across all `.json` files.

---

## To-Do (Optional Features)

- [ ] Auto-create and attach tags after import
- [ ] Add CLI options for API key and server URL
- [ ] Visualize dependency tree before import
- [ ] Skip or update workflows already existing by name

---

## Reference

- [n8n API v1 Docs](https://docs.n8n.io/api/rest/)
- [Community Thread: Strict schema issues](https://community.n8n.io/t/request-body-must-not-have-additional-properties/18235)
- [n8n GitHub](https://github.com/n8n-io/n8n)
