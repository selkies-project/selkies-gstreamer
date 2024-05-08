class Queue {
    /**
     * @constructor
     * @param {Array}
     *    Video element to attach events to
     */
    constructor(...elements) {
        /**
         * @type {Array}
         */
        this.items = [];

        this.enqueue(...elements);
    }

    enqueue(...elements) {
        elements.forEach(element => this.items.push(element));
    }

    dequeue(count=1) {
        return this.items.splice(0, count)[0];
    }

    size() {
        return this.items.length;
    }

    isEmpty() {
        return this.items.length===0;
    }

    toArray() {
        return [...this.items]
    }

    remove(element) {
        var index = this.items.indexOf(element)
        this.items.splice(index, 1)
    }

    find(element) {
        return this.items.indexOf(element) == -1 ? false: true;
    }

    clear(){
        this.items.length = 0;
    }
}

class Node {
    constructor(data) {
        this.data = data;
        this.next = null;
    }
}

class LinkedList {
    constructor() {
        this.head = null;
    }

    // Insert a new node at the end of the list
    insert(data) {
        const newNode = new Node(data);
        if (!this.head) {
            this.head = newNode;
        } else {
            let current = this.head;
            while (current.next) {
                current = current.next;
            }
            current.next = newNode;
        }
    }

    // Delete a node by its value
    remove(data) {
        if (!this.head) {
            return;
        }
        if (this.head.data === data) {
            this.head = this.head.next;
            return;
        }
        let current = this.head;
        let prev = null;
        while (current && current.data !== data) {
            prev = current;
            current = current.next;
        }
        if (!current) {
            return; // Node not found
        }
        prev.next = current.next;
    }

    // Find a node by its value
    find(data) {
        let current = this.head;
        while (current) {
            if (current.data === data) {
                return current;
            }
            current = current.next;
        }
        return null; // Node not found
    }

    // Clear all nodes from the list
    clear() {
        this.head = null;
    }
}

// Converts given string to base64 encoded string with UTF-8 format
function stringToBase64(text) {
    var bytes = new TextEncoder().encode(text);
    const binString = Array.from(bytes, (byte) =>
      String.fromCodePoint(byte),
    ).join("");
    return btoa(binString);
}

// Converts given base64 UTF-8 format encoded string to its original form
function base64ToString(base64) {
    var stringBytes = atob(base64);
    var bytes = Uint8Array.from(stringBytes, (m) => m.codePointAt(0));
    return new TextDecoder().decode(bytes);
}