class Node:
    def __init__(self, value):
        self.value = value
        self.left = None
        self.right = None
        self.height = 1


class AvlTree:
    def __init__(self, duplicate_side="right"):
        # duplicate_side: 'left' or 'right' determines where equal values are inserted
        self.root = None
        self.last_insertion_rotation = "no rotation required"
        self.duplicate_side = duplicate_side

    # Public API methods (mirror Java responses used by the visualizer)
    def snapshot(self):
        return self._build_response("Tree ready.", [], False)

    def insert(self, value):
        if value is None or value == "":
            return self._build_response("Error: empty value not allowed.", [], False)
        self.last_insertion_rotation = "no rotation required"
        path = []
        self._search(self.root, value, path)
        # track if a duplicate was inserted so we can force a simple full rebalance
        self._duplicate_inserted = False
        self.root = self._insert(self.root, value)
        if getattr(self, "_duplicate_inserted", False):
            values = []
            self._inorder_collect(self.root, values)
            self.root = self._build_balanced_from_sorted(values)
        return self._build_response(f'Inserted "{value}". Self balancing: {self.last_insertion_rotation}.', path, False)

    def find(self, value):
        if value is None or value == "":
            return self._build_response("Error: empty value not allowed.", [], False)
        path = []
        found = self._search(self.root, value, path)
        return self._build_response(f'Found "{value}".' if found else f'Value "{value}" not found.', path, found)

    def delete(self, value):
        if value is None or value == "":
            return self._build_response("Error: empty value not allowed.", [], False)
        path = []
        found = self._search(self.root, value, path)
        if found:
            self.root = self._delete(self.root, value)
        return self._build_response(f'Deleted "{value}".' if found else f'Cannot delete "{value}" because it is not in the tree.', path, found)

    def reset(self):
        self.root = None
        return self._build_response("Tree reset.", [], False)

    # Internal helpers
    def _build_response(self, message, path, found):
        return {
            "root": self._node_to_dict(self.root),
            "count": self._count(self.root),
            "height": self._height(self.root),
            "message": message,
            "path": path,
            "found": found,
        }

    def _node_to_dict(self, node):
        if node is None:
            return None
        return {
            "value": node.value,
            "height": node.height,
            "left": self._node_to_dict(node.left),
            "right": self._node_to_dict(node.right),
        }

    def _height(self, node):
        return 0 if node is None else node.height

    def _count(self, node):
        if node is None:
            return 0
        return 1 + self._count(node.left) + self._count(node.right)

    def _update_height(self, node):
        if node:
            node.height = 1 + max(self._height(node.left), self._height(node.right))

    def _balance(self, node):
        return 0 if node is None else self._height(node.left) - self._height(node.right)

    def _rotate_right(self, y):
        x = y.left
        t2 = x.right
        x.right = y
        y.left = t2
        self._update_height(y)
        self._update_height(x)
        return x

    def _rotate_left(self, x):
        y = x.right
        t2 = y.left
        y.left = x
        x.right = t2
        self._update_height(x)
        self._update_height(y)
        return y

    def _min_value_node(self, node):
        current = node
        while current.left is not None:
            current = current.left
        return current

    def _insert(self, node, value):
        if node is None:
            return Node(value)
        if value < node.value:
            node.left = self._insert(node.left, value)
        elif value > node.value:
            node.right = self._insert(node.right, value)
        else:
            # allow duplicates: insert to configured side and mark duplicate
            self._duplicate_inserted = True
            if self.duplicate_side == "left":
                node.left = self._insert(node.left, value)
            else:
                node.right = self._insert(node.right, value)

        self._update_height(node)
        balance = self._balance(node)

        if balance > 1 and value < node.left.value:
            self.last_insertion_rotation = "Left-Left (LL) rotation"
            return self._rotate_right(node)
        if balance < -1 and value > node.right.value:
            self.last_insertion_rotation = "Right-Right (RR) rotation"
            return self._rotate_left(node)
        if balance > 1 and value > node.left.value:
            self.last_insertion_rotation = "Left-Right (LR) rotation"
            node.left = self._rotate_left(node.left)
            return self._rotate_right(node)
        if balance < -1 and value < node.right.value:
            self.last_insertion_rotation = "Right-Left (RL) rotation"
            node.right = self._rotate_right(node.right)
            return self._rotate_left(node)

        return node

    def _inorder_collect(self, node, out_list):
        if node is None:
            return
        self._inorder_collect(node.left, out_list)
        out_list.append(node.value)
        self._inorder_collect(node.right, out_list)

    def _build_balanced_from_sorted(self, values):
        # values is a sorted list (with duplicates). Build a height-balanced BST by median split.
        if not values:
            return None
        mid = len(values) // 2
        root = Node(values[mid])
        root.left = self._build_balanced_from_sorted(values[:mid])
        root.right = self._build_balanced_from_sorted(values[mid+1:])
        self._update_height(root)
        return root

    def _delete(self, node, value):
        if node is None:
            return None
        if value < node.value:
            node.left = self._delete(node.left, value)
        elif value > node.value:
            node.right = self._delete(node.right, value)
        else:
            if node.left is None or node.right is None:
                return node.left if node.left is not None else node.right
            successor = self._min_value_node(node.right)
            node.value = successor.value
            node.right = self._delete(node.right, successor.value)

        self._update_height(node)
        balance = self._balance(node)

        if balance > 1 and self._balance(node.left) >= 0:
            return self._rotate_right(node)
        if balance > 1 and self._balance(node.left) < 0:
            node.left = self._rotate_left(node.left)
            return self._rotate_right(node)
        if balance < -1 and self._balance(node.right) <= 0:
            return self._rotate_left(node)
        if balance < -1 and self._balance(node.right) > 0:
            node.right = self._rotate_right(node.right)
            return self._rotate_left(node)

        return node

    def _search(self, node, value, path):
        current = node
        while current is not None:
            path.append(current.value)
            if value == current.value:
                return True
            current = current.left if value < current.value else current.right
        return False


# Expose a convenience factory for the GUI
def create_tree():
    return AvlTree()
