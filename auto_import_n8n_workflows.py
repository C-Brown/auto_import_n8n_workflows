import os
import json
import requests
from collections import defaultdict, deque

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

N8N_API_URL = "https://your-n8n-server/api/v1"
API_KEY = "you_api_key_here"
WORKFLOW_DIR = "./workflows"

HEADERS = {
    "Content-Type": "application/json",
    "X-N8N-API-KEY": API_KEY
}

def load_workflows_from_dir(directory):
    workflows = {}

    for filename in os.listdir(directory):
        if filename.endswith(".json"):
            path = os.path.join(directory, filename)

            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

                if isinstance(data, dict) and "name" in data:
                    workflows[data["name"]] = data
    
    return workflows

def find_dependencies(workflow):

    deps = set()

    for node in workflow.get("nodes", []):
        if node.get("type") == "n8n-nodes-base.executeWorkflow":
            params = node.get("parameters", {})
            
            workflow_name = params.get("workflowName")

            if workflow_name:
                deps.add(workflow_name)
    
    return deps

def build_dependency_graph(workflows):
    graph = defaultdict(set)

    for name, wf in workflows.items():
        deps = find_dependencies(wf)
        graph[name] = deps

    return graph

def topological_sort(graph):
    indegree = defaultdict(int)

    for deps in graph.values():
        for dep in deps:
            indegree[dep] += 1
    
    queue = deque([node for node in graph if indegree[node] == 0])
    result = []

    while queue:
        node = queue.popleft()

        result.append(node)

        for neighbor in graph[node]:
            indegree[neighbor] -= 1
            if indegree[neighbor] == 0:
                queue.append(neighbor)

    if len(result) != len(graph):
        print(" Cyclic dependency detected! Import order may break.")
    
    return result

def sanitize_workflow_for_import(workflow):
    allowed_fiels = {
        "name", "nodes", "connections", "settings"
    }

    clean =  {k: v for k, v in workflow.items() if k in allowed_fiels}

    clean.setdefault("settings", {})
    clean.setdefault("connections", {})

    cleaned_nodes = []

    for node in clean["nodes"]:
        node_fields = {"parameters", "name", "type", "typeVersion", "position"}
        cleaned_node = {k: v for k, v in node.items() if k in node_fields}

        if "position" in cleaned_node and isinstance(cleaned_node["position"], list):
            cleaned_node["position"] = [int(p) for p in cleaned_node["position"]]
        
        cleaned_nodes.append(cleaned_node)

    clean["nodes"] = cleaned_nodes

    return clean

def import_workflow(workflow):
    clean_wf = sanitize_workflow_for_import(workflow)
    response = requests.post(f"{N8N_API_URL}/workflows", headers=HEADERS, json=clean_wf, verify=False)

    if response.status_code == 200:
        wf_id = response.json()["id"]
        print(f"Imported workflow '{workflow['name']}' with ID: {wf_id}")

        return wf_id
    else:
        print(f"Failed to import workflow '{workflow['name']}': {response.text}")
        
        return None
    
def update_subworkflow_ids(workflow, name_to_id):
    changed = False

    for node in workflow.get("nodes", []):
        if node.get("type") == "n8n-nodes-base.executeWorkflow":
            params = node.setdefault("parameters", {})
            name = params.get("workflowName")

            if name and name in name_to_id:
                new_id = name_to_id[name]

                if params.get("workflowId") != new_id:
                    print(f"Updating '{workflow['name']}' node '{node['name']}' to ID {new_id}")
                    params["workflowId"] = new_id
                    changed = True

    return changed

def patch_workflow(wf_id, workflow):
    clean_wf = sanitize_workflow_for_import(workflow)
    response = requests.patch(f"{N8N_API_URL}/workflows/{wf_id}", headers=HEADERS, json=clean_wf, verify=False)

    if response.status_code == 200:
        print(f"Patched workflow '{workflow['name']}' with corrected references.")
    else:
        print(f"Failed to patch workflow '{workflow['name']}': {response.text}")


def main():
    workflows = load_workflows_from_dir(WORKFLOW_DIR)

    dependency_graph = build_dependency_graph(workflows)

    import_order = topological_sort(dependency_graph)

    name_to_id = {}

    for name in import_order:
        wf = workflows[name]
        wf_id = import_workflow(wf)

        if wf_id:
            name_to_id[name] = wf_id
            workflows[name]["id"] = wf_id

    for name, wf in workflows.items():
        if update_subworkflow_ids(wf, name_to_id):
            patch_workflow(wf["id"], wf)


if __name__ == "__main__":
    main()
