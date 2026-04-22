import requests
REMOTE_API_BASE = "https://bsesadmin.greymatterz.com/api"


def write_file(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def fetch_remote_yaml(endpoint_url):
    r = requests.get(endpoint_url)
    if r.status_code != 200:
        raise Exception(f"Failed to fetch from {endpoint_url}: {r.text}")
    return r.text

def run_training_pipeline():

        nlu = fetch_remote_yaml(f"{REMOTE_API_BASE}/rebuild_intent_file")
        write_file("data/nlu.yml", nlu)

        stories = fetch_remote_yaml(f"{REMOTE_API_BASE}/download_stories")
        write_file("data/stories.yml", stories)

        domain = fetch_remote_yaml(f"{REMOTE_API_BASE}/export_domain")
        write_file("domain.yml", domain)


run_training_pipeline()
