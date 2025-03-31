import yaml
import sys
from collections import defaultdict

def find_duplicate_keys(yaml_file):
    with open(yaml_file, 'r', encoding='utf-8') as file:
        content = file.read()
    
    duplicates = defaultdict(set)
    keys_seen = set()
    list_value_tracker = defaultdict(set)  # Tracks duplicate values across all lists with the same key
    
    def recursive_check(data, path=""):
        if isinstance(data, dict):
            for key, value in data.items():
                full_path = f"{path}.{key}" if path else key
                if full_path in keys_seen:
                    duplicates[full_path].add("Duplicate key detected")
                else:
                    keys_seen.add(full_path)
                recursive_check(value, full_path)
        elif isinstance(data, list):
            for item in data:
                item_str = str(item)
                if item_str in list_value_tracker[path]:
                    duplicates[path].add(item_str)
                else:
                    list_value_tracker[path].add(item_str)
                recursive_check(item, path)
    
    try:
        parsed_yaml = yaml.safe_load(content)
        recursive_check(parsed_yaml)
    except yaml.YAMLError as e:
        print(f"Error parsing YAML: {e}")
        return
    
    if duplicates:
        print("Duplicate entries found:")
        for key, values in duplicates.items():
            print(f"- {key}: {list(values)}")
    else:
        print("No duplicate entries found.")

if __name__ == "__main__":
    find_duplicate_keys(sys.argv[1])