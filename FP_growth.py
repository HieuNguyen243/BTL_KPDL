class TreeNode:
    def __init__(self, name_value, num_occur, parent_node):
        self.name = name_value
        self.count = num_occur
        self.node_link = None
        self.parent = parent_node
        self.children = {}

    def inc(self, num_occur):
        self += num_occur


def update_header(node_to_test, target_node):
    while node_to_test.node_link is not None:
        node_to_test = node_to_test.node_link
    node_to_test.node_link = target_node

def update_tree(items, in_tree, header_table, count = 1):
    if items[0] in in_tree.children:
        in_tree.children[items[0]].inc(count)
    else:
        in_tree.children[items[0]] = TreeNode(items[0], count, in_tree)
        if header_table[items[0]][1] is None:
            header_table[items[0]][1] = in_tree.children[items[0]]
        else:
            update_header(header_table[items[0]][1], in_tree.children[items[0]])

    if len(items) > 1:
        update_tree(items[1::], in_tree.children[items[0]], header_table, count)


def create_tree(dataset, min_support = 1):
    header_table = {}

    for transaction in dataset:
        for item in transaction:
            header_table[item] = header_table.get(item,0) + 1

    for k in list(header_table.keys()):
        if header_table[k] < min_support:
            del header_table[k]

    frequent_items = set(header_table.keys())
    if len(frequent_items) == 0:
        return None, None
    
    for k in header_table:
        header_table[k] = [header_table[k], None]

    ret_tree = TreeNode('Null Node', 1, None)

    for transaction in dataset:
        local_d = {}
        for item in transaction:
            if item in frequent_items:
                local_d[item] = header_table[item][0]

        if len(local_d) > 0:
            ordered_items = [v[0] for v in sorted(local_d.items(), key = lambda p: p[1], reverse = True)]
            update_tree(ordered_items, ret_tree, header_table, 1)

    return ret_tree, header_table

def ascend_tree(leaf_node, prefix_path):
    if leaf_node.parent is not None:
        prefix_path.append(leaf_node.name)
        ascend_tree(leaf_node.parent, prefix_path)

def find_prefix_path(base_pat, tree_node):
    cond_pats = {}
    while tree_node is not None:
        prefix_path = []
        ascend_tree(tree_node, prefix_path)
        if len(prefix_path) > 1:
            cond_pats[frozenset(prefix_path[1:])] = tree_node.count
        tree_node = tree_node.node_link

    return cond_pats

def mine_fp_tree(current_fp_tree, header_table, min_support, current_prefix, frequent_itemsets):
    items_sorted_by_freq = [v[0] for v in sorted(header_table.items(), key = lambda p: p[1][0])]

    for current_item in items_sorted_by_freq:
        
        new_frequent_set = current_prefix.copy()
        new_frequent_set.add(current_item)
        frequent_itemsets.append(new_frequent_set)
        
        prefix_paths_dict = find_prefix_path(current_item, header_table[current_item][1])
        
        conditional_dataset = []
        for path, count in prefix_paths_dict.items():
            for _ in range(count):
                conditional_dataset.append(list(path))
                
        conditional_fp_tree, conditional_header_table = create_tree(conditional_dataset, min_support)
        
        if conditional_header_table is not None:
            mine_fp_tree(conditional_fp_tree, conditional_header_table, min_support, new_frequent_set, frequent_itemsets)