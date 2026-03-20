import itertools

class TreeNode:
    def __init__(self, name_value, num_occur, parent_node):
        self.name = name_value
        self.count = num_occur
        self.node_link = None
        self.parent = parent_node
        self.children = {}

    def inc(self, num_occur):
        self.count += num_occur

    # HÀM MỚI 1: Vẽ cây ra màn hình Console với đường kẻ nhánh rõ ràng
    def display_tree(self, prefix="", is_last=True, current_depth=1, max_depth=4):
        if current_depth == 1:
            print(f"[{self.name} : {self.count}]")
        else:
            branch = "└── " if is_last else "├── "
            print(f"{prefix}{branch}[{self.name} : {self.count}]")
            
        if current_depth == max_depth:
            if self.children:
                new_prefix = prefix + ("    " if is_last else "│   ") if current_depth > 1 else prefix
                print(f"{new_prefix}└── ...")
            return

        children = list(self.children.values())
        for i, child in enumerate(children):
            is_last_child = (i == len(children) - 1)
            new_prefix = prefix + ("    " if is_last else "│   ") if current_depth > 1 else prefix
            child.display_tree(new_prefix, is_last_child, current_depth + 1, max_depth)

def update_header(node_to_test, target_node):
    while node_to_test.node_link is not None:
        node_to_test = node_to_test.node_link
    node_to_test.node_link = target_node

def update_tree(items, in_tree, header_table, count=1):
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

def create_tree(dataset, min_support=1):
    header_table = {}
    for transaction in dataset:
        for item in transaction:
            header_table[item] = header_table.get(item, 0) + 1

    for k in list(header_table.keys()):
        if header_table[k] < min_support:
            del header_table[k]

    frequent_items = set(header_table.keys())
    if len(frequent_items) == 0:
        return None, None
    
    for k in header_table:
        header_table[k] = [header_table[k], None]

    ret_tree = TreeNode('Root', 1, None)

    for transaction in dataset:
        local_d = {}
        for item in transaction:
            if item in frequent_items:
                local_d[item] = header_table[item][0]

        if len(local_d) > 0:
            ordered_items = [v[0] for v in sorted(local_d.items(), key=lambda p: (p[1], p[0]), reverse=True)]
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

# CẬP NHẬT: frequent_itemsets giờ là Dictionary để lưu trữ cả tần suất (phục vụ tính toán Toán học)
def mine_fp_tree(current_fp_tree, header_table, min_support, current_prefix, frequent_itemsets, max_len=3):
    if len(current_prefix) >= max_len:
        return

    items_sorted_by_freq = [v[0] for v in sorted(header_table.items(), key=lambda p: (p[1][0], p[0]))]

    for current_item in items_sorted_by_freq:
        new_frequent_set = current_prefix.copy()
        new_frequent_set.add(current_item)
        
        # Lưu Tên sản phẩm đi kèm với Tần suất (Count)
        frequent_itemsets[frozenset(new_frequent_set)] = header_table[current_item][0]
        
        if len(new_frequent_set) < max_len:
            prefix_paths_dict = find_prefix_path(current_item, header_table[current_item][1])
            conditional_dataset = []
            for path, count in prefix_paths_dict.items():
                for _ in range(count):
                    conditional_dataset.append(list(path))
                    
            conditional_fp_tree, conditional_header_table = create_tree(conditional_dataset, min_support)
            
            if conditional_header_table is not None:
                mine_fp_tree(conditional_fp_tree, conditional_header_table, min_support, new_frequent_set, frequent_itemsets, max_len)

# HÀM MỚI 2: Sinh Luật kết hợp từ Dictionary Tập Phổ Biến
def generate_association_rules(frequent_itemsets_dict, total_transactions, min_confidence=0.5, target_itemsets=None):
    rules = []
    
    # Duyệt trên tập thu gọn (nếu có), nếu không thì duyệt toàn bộ dict
    itemsets_to_check = target_itemsets if target_itemsets is not None else frequent_itemsets_dict.keys()
    
    for itemset in itemsets_to_check:
        # Bỏ qua nếu itemset không tồn tại trong từ điển gốc (phòng lỗi logic)
        if itemset not in frequent_itemsets_dict:
            continue
            
        support_count_AB = frequent_itemsets_dict[itemset]
        
        if len(itemset) > 1:
            # Tạo các tổ hợp (Tiền đề -> Hệ quả)
            for i in range(1, len(itemset)):
                for antecedent in itertools.combinations(itemset, i):
                    antecedent_set = frozenset(antecedent)
                    consequent_set = itemset - antecedent_set
                    
                    # QUAN TRỌNG: Ráp công thức Toán học - Luôn tra cứu Support của A và B từ TỪ ĐIỂN GỐC
                    if antecedent_set in frequent_itemsets_dict and consequent_set in frequent_itemsets_dict:
                        sup_count_A = frequent_itemsets_dict[antecedent_set]
                        sup_count_B = frequent_itemsets_dict[consequent_set]
                        
                        confidence = support_count_AB / sup_count_A
                        
                        if confidence >= min_confidence:
                            support_AB_ratio = support_count_AB / total_transactions
                            support_B_ratio = sup_count_B / total_transactions
                            
                            # Tính Lift
                            lift = confidence / support_B_ratio
                            
                            rules.append({
                                'antecedent': list(antecedent_set),
                                'consequent': list(consequent_set),
                                'support': support_AB_ratio,
                                'confidence': confidence,
                                'lift': lift
                            })
    return rules