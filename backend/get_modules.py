import os
import re

def list_python_files(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                yield os.path.join(root, file)

def extract_imports(file_path):
    with open(file_path, 'r') as file:
        contents = file.read()
        imports = set(re.findall(r'^\s*(?:from\s+(\S+)|import\s+(\S+))', contents, re.MULTILINE))
        return {match[0] or match[1] for match in imports}

if __name__ == "__main__":
    project_directory = '.'  # Replace with the path to your project directory if necessary
    all_imports = set()

    for python_file in list_python_files(project_directory):
        file_imports = extract_imports(python_file)
        all_imports.update(file_imports)

    for import_name in sorted(all_imports):
        print(import_name)
