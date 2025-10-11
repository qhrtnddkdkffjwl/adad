class BinarySearchTree:
    def __init__(self, value):
        self.value = value
        self.left = None
        self.right = None

    def insert(self, value):
        if value < self.value:
            if self.left is None:
                self.left = BinarySearchTree(value)
            else:
                self.left.insert(value)
        else:
            if self.right is None:
                self.right = BinarySearchTree(value)
            else:
                self.right.insert(value)

    def search(self, value):
        if value < self.value:
            if self.left is None:
                return False
            else:
                return self.left.search(value)
        else:
            if self.right is None:
                return False
            else:
                return self.right.search(value)

    def delete(self, value):
        if value < self.value:
            if self.left is None:
                return False
            else:
                return self.left.delete(value)
        else:
            if self.right is None:
                return False
            else:
                return self.right.delete(value)

    def print_tree(self):
        if self.left:
            self.left.print_tree()
        print(self.value),
        if self.right:
            self.right.print_tree()

bst = BinarySearchTree(10)
bst.insert(6)
bst.insert(14)
bst.insert(3)
bst.insert(8)
bst.insert(12)
bst.insert(15)
bst.print_tree()

