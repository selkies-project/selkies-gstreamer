class Node:
    def __init__(self, data, timestamp):
        self.data = data
        self.timestamp = timestamp
        self.next = None

class LinkedList:
    def __init__(self):
        self.head = None

    # Insert a new node at the end of the list
    def insert(self, data, timestamp):
        new_node = Node(data, timestamp)
        if not self.head:
            self.head = new_node
        else:
            current = self.head
            while current.next:
                current = current.next
            current.next = new_node

    # Delete a node by its value
    def remove(self, data):
        if not self.head:
            return
        if self.head.data == data:
            self.head = self.head.next
            return
        current = self.head
        prev = None
        while current and current.data != data:
            prev = current
            current = current.next
        if not current:
            return  # Node not found
        prev.next = current.next

    def find(self, data):
        current = self.head
        while current:
            if current.data == data:
                return current
            current = current.next
        return None

    def clear(self):
        self.head = None
