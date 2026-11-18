import ast

with open('alpha.py', 'r', encoding='utf-8') as f:
    text = f.read()

tree = ast.parse(text)
class_def = [n for n in tree.body if isinstance(n, ast.ClassDef)][0]
setup_gui = [n for n in class_def.body if isinstance(n, ast.FunctionDef) and n.name == 'setup_gui'][0]

commands = set()
for node in ast.walk(setup_gui):
    # Find keyword arguments named 'command'
    if isinstance(node, ast.keyword) and node.arg == 'command':
        # See if the value is an attribute access (e.g., self.toggle_ai)
        if isinstance(node.value, ast.Attribute) and isinstance(node.value.value, ast.Name) and node.value.value.id == 'self':
            commands.add(node.value.attr)

print("GUI BUTTON COMMANDS FOUND:")
for c in commands:
    print("- self." + c)
