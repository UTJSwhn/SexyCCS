import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import random
import pickle
import re
import os


class StateGraph:
    # The knowledge all the semantic trees should know.
    knowledge_semantic_tree_map = {}
    action_list = []

    # Every state has its own semantic tree
    class SemanticTree:
        operation_feature_letter_list = ['+', '|', '.', '[', '{']

        class TreeNode:
            def __init__(self, s):
                self.name = s
                self.operation_type = None
                self.operation_info = None
                self.next_state_dict = {'eps': [self.name]}
                self.children_name_list = []
                self.children_node_list = []

        def __init__(self, s):
            self.name = s
            self.next_state_dict = {'eps': [self.name]}
            self.root_node = StateGraph.SemanticTree.TreeNode(self.name)
            self.dfs_build(self.root_node)
            self.next_state_dict = self.dfs_fill(self.root_node)

        @classmethod
        def check_operation_level(cls, state_string):
            # Detect the state string without any operator
            flag = False
            for operation_feature_letter in cls.operation_feature_letter_list:
                if operation_feature_letter in state_string:
                    flag = True
                    break
            if not flag:
                return 5

            # Scan the state string to:
            #   1. generate inactive vector denotes the inactive symbols in parentheses
            #   2. Determine the operator
            inactive_vector = [0] * len(state_string)
            score = 0
            operation_level = 4
            for i in range(len(state_string)):
                letter = state_string[i]
                if score > 0:
                    inactive_vector[i] = 1
                elif letter in cls.operation_feature_letter_list:
                    operation_level = min(operation_level, cls.operation_feature_letter_list.index(letter))
                if letter == '(':
                    score += 1
                elif letter == ')':
                    score -= 1

            return operation_level

        def dfs_build(self, node):
            state_string = node.name
            operation_feature_letter_list = ['+', '|', '.', '[', '{']

            # Detect the leaf node and trim the redundant parentheses
            flag = False
            for operation_feature_letter in operation_feature_letter_list:
                if operation_feature_letter in state_string:
                    flag = True
                    break
            if not flag:
                return

            # Trim the redundant parentheses of non-leaf node
            score = 0
            for i in range(len(state_string) - 1):
                if state_string[i] == '(':
                    score += 1
                elif state_string[i] == ')':
                    score -= 1
                if score <= 0:
                    flag = False
            if flag:
                state_string = state_string[1:-1]
                node.name = state_string

            # Scan the state string to:
            #   1. generate inactive vector denotes the inactive symbols in parentheses
            #   2. Determine the operator
            inactive_vector = [0] * len(state_string)
            score = 0
            operation_level = 4
            for i in range(len(state_string)):
                letter = state_string[i]
                if score > 0:
                    inactive_vector[i] = 1
                elif letter in operation_feature_letter_list:
                    operation_level = min(operation_level, operation_feature_letter_list.index(letter))
                if letter == '(':
                    score += 1
                elif letter == ')':
                    score -= 1

            if operation_level == 4:
                node.operation_type = 'restriction'
                node.operation_info = re.search(r'{[A-Za-z0-9,]*}$', state_string).group()
                node.children_name_list.append(re.sub(r'/{[A-Za-z0-9,]*}$', '', state_string))
            elif operation_level == 3:
                node.operation_type = 'relabelling'
                node.operation_info = re.search(r'\[[A-Za-z0-9,/]*\]*', state_string).group()
                node.children_name_list.append(re.sub(r'\[[A-Za-z0-9,/]*\]$', '', state_string))
            elif operation_level == 2:
                node.operation_type = 'action'
                temp = state_string.split('.', 1)
                node.operation_info = temp[0]
                node.children_name_list.append(temp[1])
            else:
                operation_feature_letter = operation_feature_letter_list[operation_level]
                if operation_feature_letter == '+':
                    node.operation_type = 'add'
                else:
                    node.operation_type = 'par'
                temp = ''
                for i in range(len(state_string)):
                    if state_string[i] != operation_feature_letter or inactive_vector[i] == 1:
                        temp += state_string[i]
                    else:
                        node.children_name_list.append(temp)
                        temp = ''
                node.children_name_list.append(temp)

            for child_name in node.children_name_list:
                child_node = StateGraph.SemanticTree.TreeNode(child_name)
                self.dfs_build(child_node)
                node.children_node_list.append(child_node)

        def dfs_fill(self, node):
            # When search the leaf node
            if not node.operation_type:
                if node.name == '0':
                    return node.next_state_dict
                # When the definition can be find recursively
                else:
                    for agent in StateGraph.knowledge_semantic_tree_map:
                        if node.name == agent:
                            node.next_state_dict = StateGraph.knowledge_semantic_tree_map[agent].next_state_dict
                            return node.next_state_dict
                    print('Can not deduce the next action from agent definition. Semantic error!')
                    return {}

            # When the operation is restriction
            #   1. analyze the restriction channel and filter the child node's action
            #   2. rewrite the next state string to ()/{} form after check the necessity of ()
            elif node.operation_type == 'restriction':
                restricted_node_channel = node.operation_info[1:-1].split(',')
                next_state_dict_before_restricted = self.dfs_fill(node.children_node_list[0])
                temp_dict = {}
                for action in next_state_dict_before_restricted:
                    if action in restricted_node_channel:
                        continue
                    if action[-1] == '\'' and action[:-1] in restricted_node_channel:
                        continue
                    else:
                        if action not in temp_dict:
                            temp_dict[action] = []
                        for next_state in next_state_dict_before_restricted[action]:
                            if self.check_operation_level(next_state) == 5:
                                temp_dict[action].append(next_state + '/' + node.operation_info)
                            else:
                                temp_dict[action].append('(' + next_state + ')/' + node.operation_info)
                return temp_dict

            # When the operation is relabelling
            #   1. Create channel mapping
            #   2. For every action need to be relabelled
            elif node.operation_type == 'relabelling':
                relabelling_pairs = node.operation_info[1:-1].split(',')
                channel_map = {}
                for relabelling_pair in relabelling_pairs:
                    channels = relabelling_pair.split('/')
                    channel_map[channels[1]] = channels[0]
                next_state_dict_before_relabelled = self.dfs_fill(node.children_node_list[0])
                for action in next_state_dict_before_relabelled:
                    if action == 'eps':
                        continue
                    relabelled_action = action
                    if action in channel_map:
                        relabelled_action = channel_map[action]
                    elif action[-1] == '\'' and action[:-1] in channel_map:
                        relabelled_action = channel_map[action[:-1]] + '\''

                    if relabelled_action not in node.next_state_dict:
                        node.next_state_dict[relabelled_action] = []

                    for next_state in next_state_dict_before_relabelled[action]:
                        if self.check_operation_level(next_state) == 5:
                            node.next_state_dict[relabelled_action].append(next_state + node.operation_info)
                        else:
                            node.next_state_dict[relabelled_action].append('(' + next_state + ')' + node.operation_info)

            # When the operation is action a, just add a.X no matter what derivatives the children have
            elif node.operation_type == 'action':
                node.next_state_dict[node.operation_info] = node.children_name_list

            # When the operation is par
            #   1. Write the agent lists after single action
            #   2. Write the agent lists after tau action
            #   3. Check the necessity of () for every agent in all agent lists
            #       and merge every agent list to state string
            elif node.operation_type == 'par':
                # Prepare materials
                current_agent_list = node.children_name_list
                next_agent_list_dict = {}
                next_state_dict_list = []
                for child_node in node.children_node_list:
                    next_state_dict_list.append(self.dfs_fill(child_node))

                # Part 1
                for i in range(len(next_state_dict_list)):
                    for action in next_state_dict_list[i]:
                        if action == 'eps':
                            continue
                        if action not in next_agent_list_dict:
                            next_agent_list_dict[action] = []
                        for next_state in next_state_dict_list[i][action]:
                            temp_list = []
                            for j in range(len(current_agent_list)):
                                if j == i:
                                    temp_list.append(next_state)
                                else:
                                    temp_list.append(current_agent_list[j])
                            next_agent_list_dict[action].append(temp_list)

                # Part 2
                action_in_index_list = []
                action_out_index_list = []
                for i in range(len(StateGraph.action_list)):
                    action_in_index_list.append([])
                    action_out_index_list.append([])
                for i in range(len(next_state_dict_list)):
                    for action in next_state_dict_list[i]:
                        if action == 'eps' or action == 'tau':
                            continue
                        elif action[-1] == '\'':
                            action_out_index_list[StateGraph.action_list.index(action[:-1])].append(i)
                        else:
                            action_in_index_list[StateGraph.action_list.index(action)].append(i)
                if 'tau' not in next_agent_list_dict:
                    next_agent_list_dict['tau'] = []
                for i in range(len(StateGraph.action_list)):
                    for in_index in action_in_index_list[i]:
                        for out_index in action_out_index_list[i]:
                            if in_index == out_index:
                                continue
                            for next_in_agent in next_state_dict_list[in_index][StateGraph.action_list[i]]:
                                for next_out_agent in next_state_dict_list[out_index][StateGraph.action_list[i] + '\'']:
                                    temp_list = []
                                    for j in range(len(next_state_dict_list)):
                                        if j == in_index:
                                            temp_list.append(next_in_agent)
                                        elif j == out_index:
                                            temp_list.append(next_out_agent)
                                        else:
                                            temp_list.append(current_agent_list[j])
                                    next_agent_list_dict['tau'].append(temp_list)

                # Part 3
                for action in next_agent_list_dict:
                    if action == 'eps' or len(next_agent_list_dict[action]) == 0:
                        continue
                    if action not in node.next_state_dict:
                        node.next_state_dict[action] = []
                    for next_agent_list in next_agent_list_dict[action]:
                        for i in range(len(next_agent_list)):
                            if self.check_operation_level(next_agent_list[i]) == 0:
                                next_agent_list[i] = '(' + next_agent_list[i] + ')'
                        node.next_state_dict[action].append('|'.join(next_agent_list))

            # When the operation is add, just merge the next state dicts of all agents
            else:
                temp_dict = {}
                for child_node in node.children_node_list:
                    child_next_state_dict = self.dfs_fill(child_node)
                    for action in child_next_state_dict:
                        if action == 'eps':
                            continue
                        if action not in temp_dict:
                            temp_dict[action] = set()
                        for next_state in child_next_state_dict[action]:
                            temp_dict[action].add(next_state)
                for action in temp_dict:
                    node.next_state_dict[action] = list(temp_dict[action])

            return node.next_state_dict

    def __init__(self, name, action_list, initial_state, state_define_map):
        self.name = name
        self.initial_state = initial_state
        StateGraph.knowledge_semantic_tree_map = {}
        StateGraph.action_list = action_list
        for state in state_define_map:
            StateGraph.knowledge_semantic_tree_map[state] = StateGraph.SemanticTree(state_define_map[state])
        self.state_size = 1
        self.state_name_list = []
        self.state_semantic_tree_map = {}
        self.adjacent_state_map = {}
        self.edge_check_list = []
        self.edge_channel_array = []
        self.simplified_edge_channel_array = []
        self.edge_index_array = []
        self.numeric_state_graph = []
        self.numeric_adjacent_map_list = []
        self.numeric_weak_bisimulation_adjacent_map_list = []
        self.tau_family_set_list = []
        self.run()

    def run(self):
        self.generate_state_map()
        self.draw_figures()
        self.generate_weak_bisimulation_state_map()

    def generate_state_map(self):
        current_state_set = {self.initial_state}

        while len(current_state_set):
            next_state_set = set()
            for state in current_state_set:
                if len(state) > 80:
                    continue
                self.state_name_list.append(state)
                temp_tree = StateGraph.SemanticTree(state)
                self.state_semantic_tree_map[state] = temp_tree
                self.adjacent_state_map[state] = []
                for action in temp_tree.next_state_dict:
                    if action == 'eps':
                        continue
                    for next_state in temp_tree.next_state_dict[action]:
                        if len(next_state) > 80:
                            continue
                        self.adjacent_state_map[state].append(next_state)
                        self.edge_check_list.append([state, next_state, action])
                        next_state_set.add(next_state)

            current_state_set = set()
            for next_state in next_state_set:
                if next_state not in self.state_semantic_tree_map:
                    current_state_set.add(next_state)

        self.state_size = len(self.state_name_list)
        for i in range(self.state_size):
            self.numeric_state_graph.append([])
            self.edge_channel_array.append([])
            for j in range(self.state_size):
                self.edge_channel_array[i].append('')

        for state in self.adjacent_state_map:
            state_index = self.state_name_list.index(state)
            for next_state in self.adjacent_state_map[state]:
                next_state_index = self.state_name_list.index(next_state)
                self.numeric_state_graph[state_index].append(next_state_index)
            self.numeric_state_graph[state_index].sort()

        for edge_info in self.edge_check_list:
            start_node_index = self.state_name_list.index(edge_info[0])
            end_node_index = self.state_name_list.index(edge_info[1])
            channel = edge_info[2]
            if channel == 'tau':
                channel = r'$ \tau $'
            self.edge_channel_array[start_node_index][end_node_index] = channel

    def dfs_form_tau_family(self, root, current, ancestor_list):
        if r'$ \tau $' not in self.numeric_adjacent_map_list[current]:
            return
        next_ancestor_list = []
        for ancestor in ancestor_list:
            next_ancestor_list.append(ancestor)
        next_ancestor_list.append(current)
        for child in self.numeric_adjacent_map_list[current][r'$ \tau $']:
            if child not in ancestor_list:
                self.tau_family_set_list[root].add(child)
                self.dfs_form_tau_family(root, child, next_ancestor_list)

    def generate_weak_bisimulation_state_map(self):
        # rebuild adjacent state map in numeric style
        for i in range(self.state_size):
            self.numeric_adjacent_map_list.append({'eps': {i}})
            for j in range(self.state_size):
                action = self.edge_channel_array[i][j]
                if action == '':
                    continue
                if action not in self.numeric_adjacent_map_list[i]:
                    self.numeric_adjacent_map_list[i][action] = {j}
                else:
                    self.numeric_adjacent_map_list[i][action].add(j)

        # form tau families for each state
        for i in range(self.state_size):
            self.tau_family_set_list.append({i})
            self.dfs_form_tau_family(i, i, [])

        # generate next hat-action map for each state
        for i in range(self.state_size):
            self.numeric_weak_bisimulation_adjacent_map_list.append({'eps': {i}})
            for tau_child in self.tau_family_set_list[i]:
                for action in self.numeric_adjacent_map_list[tau_child]:
                    if action == r'$ \tau $':
                        self.numeric_weak_bisimulation_adjacent_map_list[i]['eps'] |= self.numeric_adjacent_map_list[tau_child][action]
                    elif action not in self.numeric_weak_bisimulation_adjacent_map_list[i]:
                        self.numeric_weak_bisimulation_adjacent_map_list[i][action] = set() | self.numeric_adjacent_map_list[tau_child][action]
                    else:
                        self.numeric_weak_bisimulation_adjacent_map_list[i][action] |= self.numeric_adjacent_map_list[tau_child][action]

            for action in self.numeric_weak_bisimulation_adjacent_map_list[i]:
                if action != 'eps':
                    grandson_set = set()
                    for son in self.numeric_weak_bisimulation_adjacent_map_list[i][action]:
                        for grandson in self.tau_family_set_list[son]:
                            grandson_set.add(grandson)
                    self.numeric_weak_bisimulation_adjacent_map_list[i][action] |= grandson_set

            # print('The next hat-action map for ' + 'state ' + str(i) + ' is:')
            # for action in self.numeric_weak_bisimulation_adjacent_map_list[i]:
            #     print(action + ' :' + str(self.numeric_weak_bisimulation_adjacent_map_list[i][action]))

    def draw_figures(self):
        figure_path = 'graph/' + self.name
        if not os.path.exists(figure_path):
            os.makedirs(figure_path)
        else:
            for file in os.listdir(figure_path):
                os.remove(figure_path + '/' + file)

        state_graph = nx.MultiDiGraph()
        for i in range(self.state_size):
            state_graph.add_node(i)
        for i in range(self.state_size):
            for j in self.numeric_state_graph[i]:
                state_graph.add_edge(i, j, channel=self.edge_channel_array[i][j])
        for i in range(self.state_size):
            self.edge_index_array.append([])
            for j in range(self.state_size):
                self.edge_index_array[i].append(0)
        s = 0
        for u, v in state_graph.edges(data=False):
            self.edge_index_array[u][v] = s
            s += 1

        # Set the initial node and edge attributes
        node_colors = []
        node_labels = {}
        node_sizes = []
        for i in range(self.state_size):
            node_colors.append('#FFFFFF')
            node_sizes.append(0)
            node_labels[i] = ''
        edge_colors = []
        for i in range(len(state_graph.edges)):
            edge_colors.append('#FFFFFF')

        # Set the final node and edge attributes
        final_node_colors = []
        final_node_labels = {}
        final_node_sizes = []
        for i in range(self.state_size):
            final_node_colors.append('#CCCCCC')
            final_node_sizes.append(500)
            final_node_labels[i] = str(i)
        channel_count = len(StateGraph.action_list) + 1
        color_cycle = ['#1F77B4', '#FF7f0e', '#2CA02C', '#D62728', '#9467BD', '#8C564B', '#E377C2', '#7F7F7F',
                       '#BCBD22', '#17BEC9']
        channel_colors = random.sample(color_cycle, channel_count)

        init_state_num = 0
        exist_node_set = {init_state_num}
        current_node_set = {init_state_num}
        figure_id = 0
        while len(current_node_set):
            next_node_set = set()
            plt.figure(figsize=(8.0, 8.0))
            plt.axis('off')
            pos = nx.drawing.layout.shell_layout(state_graph)
            for node in current_node_set:
                node_colors[node] = final_node_colors[node]
                node_labels[node] = str(node)
                node_sizes[node] = 500
                for next_node in self.numeric_state_graph[node]:
                    node_colors[next_node] = final_node_colors[next_node]
                    node_labels[next_node] = str(next_node)
                    node_sizes[next_node] = 500
                    next_node_set.add(next_node)
                    edge_index = self.edge_index_array[node][next_node]
                    edge_label = self.edge_channel_array[node][next_node]
                    if edge_label == r'$ \tau $':
                        edge_color = channel_colors[channel_count - 1]
                    else:
                        if edge_label[-1] == '\'':
                            edge_label = edge_label[:-1]
                        edge_color = channel_colors[self.action_list.index(edge_label)]
                    edge_colors[edge_index] = edge_color

            nx.draw_networkx_nodes(state_graph, pos, nodelist=state_graph.nodes(), node_color=node_colors, node_size=node_sizes)
            nx.draw_networkx_labels(state_graph, pos, labels=node_labels)
            nx.draw_networkx_edges(state_graph, pos, edge_color=edge_colors, arrowsize=20)
            s = 0
            labels = {}
            for u, v, d in state_graph.edges(data=True):
                if edge_colors[s] == '#FFFFFF':
                    labels[(u, v)] = ''
                else:
                    labels[(u, v)] = d['channel']
                s += 1
            nx.draw_networkx_edge_labels(state_graph, pos, edge_labels=labels, label_pos=0.8)
            plt.savefig(figure_path + '/' + str(figure_id) + '.png')
            figure_id += 1

            current_node_set = set()
            for node in next_node_set:
                if node not in exist_node_set:
                    current_node_set.add(node)
                    exist_node_set.add(node)


def strong_bisimulation(state_graph_1, state_graph_2):
    bisimulation_result = ''
    bisimulation_result += state_graph_1.name + ' vs. ' + state_graph_2.name + '\n'
    m = state_graph_1.state_size
    n = state_graph_2.state_size

    # Initialize Deduction Array
    deduction_array = np.zeros([m, n])
    visit_array = np.zeros([m, n])
    for i in range(m):
        i_next_action = set()
        for action in state_graph_1.numeric_adjacent_map_list[i]:
            if action == 'eps':
                continue
            i_next_action.add(action)
        for j in range(n):
            j_next_action = set()
            for action in state_graph_2.numeric_adjacent_map_list[j]:
                if action == 'eps':
                    continue
                j_next_action.add(action)
            if i_next_action != j_next_action:
                visit_array[i][j] = 1
            else:
                deduction_array[i][j] = -1

    if deduction_array[0][0] == 0:
        bisimulation_result += '\nThe initial pair (' + state_graph_1.state_name_list[0] +\
            ',' + state_graph_2.state_name_list[0] + ') is not strong bisimulation. Suppose failed'
        bisimulation_result += '\n\nThey are not in strong bisimulation relationship\n'
        return
    generation_count = 0
    bisimulation_result += '\nGeneration ' + str(generation_count) + ':'
    bisimulation_result += '\nSuppose (' + state_graph_1.state_name_list[0] + ',' + state_graph_2.state_name_list[0] + ')' +\
        ' is a strong bisimulation pair.'
    deduction_array[0][0] = 1

    initial_pair_set = {(0, 0)}
    current_pair_set = initial_pair_set
    while len(current_pair_set):
        generation_count += 1
        bisimulation_result += '\nGeneration ' + str(generation_count) + ':'
        next_pair_set = set()
        for pair in current_pair_set:
            state_1 = pair[0]
            state_2 = pair[1]
            visit_array[state_1][state_2] = 1
            next_state_map_1 = state_graph_1.numeric_adjacent_map_list[state_1]
            next_state_map_2 = state_graph_2.numeric_adjacent_map_list[state_2]
            for action in next_state_map_1:
                if action == 'eps':
                    continue
                next_state_set_1 = next_state_map_1[action]
                next_state_set_2 = next_state_map_2[action]

                for next_state_1 in next_state_set_1:
                    for next_state_2 in next_state_set_2:
                        next_pair_set.add((next_state_1, next_state_2))

        current_pair_set = set()
        for pair in next_pair_set:
            state_1 = pair[0]
            state_2 = pair[1]
            bisimulation_result += '\n    Then (' + state_graph_1.state_name_list[state_1] + ',' +\
                state_graph_2.state_name_list[state_2] + ') should remain strong bisimulation. '
            if deduction_array[state_1][state_2] == 0:
                bisimulation_result += ' Then it comes to conflict.'
                bisimulation_result += '\n\nThey are not in strong bisimulation relationship\n'
                return bisimulation_result

            deduction_array[state_1][state_2] = 1
            if visit_array[state_1][state_2] == 0:
                current_pair_set.add((state_1, state_2))
            else:
                bisimulation_result += 'And it is consistent with previous suppose.'

    bisimulation_result += '\n    After ' + str(generation_count) + ' iteration, our initial suppose is self-consistent.'
    bisimulation_result += '\n\nThey are in strong bisimulation relationship\n'
    return bisimulation_result


def weak_bisimulation(state_graph_1, state_graph_2):
    bisimulation_result = ''
    bisimulation_result += state_graph_1.name + ' vs. ' + state_graph_2.name + '\n'
    m = state_graph_1.state_size
    n = state_graph_2.state_size

    # Initialize Deduction Array
    deduction_array = np.zeros([m, n])
    visit_array = np.zeros([m, n])
    for i in range(m):
        i_next_action = set()
        for action in state_graph_1.numeric_adjacent_map_list[i]:
            if action == 'eps' or action == r'$ \tau $':
                continue
            i_next_action.add(action)
        i_next_hat_action = set()
        for action in state_graph_1.numeric_weak_bisimulation_adjacent_map_list[i]:
            if action == 'eps':
                continue
            i_next_hat_action.add(action)
        for j in range(n):
            j_next_action = set()
            for action in state_graph_2.numeric_adjacent_map_list[j]:
                if action == 'eps' or action == r'$ \tau $':
                    continue
                j_next_action.add(action)
            j_next_hat_action = set()
            for action in state_graph_2.numeric_weak_bisimulation_adjacent_map_list[j]:
                if action == 'eps':
                    continue
                j_next_hat_action.add(action)
            if i_next_action.issubset(j_next_hat_action) and j_next_action.issubset(i_next_hat_action):
                deduction_array[i][j] = -1
            else:
                visit_array[i][j] = 1

    if deduction_array[0][0] == 0:
        bisimulation_result += '\nThe initial pair (' + state_graph_1.state_name_list[0] +\
            ',' + state_graph_2.state_name_list[0] + ') is not weak bisimulation. Suppose failed'
        bisimulation_result += '\n\nThey are not in weak bisimulation relationship\n'
        return
    generation_count = 0
    bisimulation_result += '\nGeneration ' + str(generation_count) + ':'
    bisimulation_result += '\nSuppose (' + state_graph_1.state_name_list[0] + ',' + state_graph_2.state_name_list[0] + ')' +\
        ' is a weak bisimulation pair.'
    deduction_array[0][0] = 1

    initial_pair_set = {(0, 0)}
    current_pair_set = initial_pair_set
    while len(current_pair_set):
        next_pair_set = set()
        generation_count += 1
        bisimulation_result += '\nGeneration ' + str(generation_count) + ':'
        for pair in current_pair_set:
            state_1 = pair[0]
            state_2 = pair[1]
            visit_array[state_1][state_2] = 1
            next_state_map_1 = state_graph_1.numeric_adjacent_map_list[state_1]
            next_state_map_2 = state_graph_2.numeric_adjacent_map_list[state_2]
            for action in next_state_map_1:
                if action == 'eps':
                    continue
                if action in next_state_map_2:
                    next_state_set_1 = next_state_map_1[action]
                    next_state_set_2 = next_state_map_2[action]
                    for next_state_1 in next_state_set_1:
                        for next_state_2 in next_state_set_2:
                            next_pair_set.add((next_state_1, next_state_2))

        current_pair_set = set()
        for pair in next_pair_set:
            state_1 = pair[0]
            state_2 = pair[1]
            bisimulation_result += '\n    Then (' + state_graph_1.state_name_list[state_1] + ',' +\
                state_graph_2.state_name_list[state_2] + ') should remain weak bisimulation. '
            if deduction_array[state_1][state_2] == 0:
                bisimulation_result += ' Then it comes to conflict.'
                bisimulation_result += '\n\nThey are not in weak bisimulation relationship\n'
                return bisimulation_result

            deduction_array[state_1][state_2] = 1
            if visit_array[state_1][state_2] == 0:
                current_pair_set.add((state_1, state_2))
            else:
                bisimulation_result += 'And it is consistent with previous suppose.'

    bisimulation_result += '\n    After ' + str(generation_count) + ' iteration, initial suppose is self-consistent.'
    bisimulation_result += '\n\nThey are in weak bisimulation relationship\n'
    return bisimulation_result


if __name__ == '__main__':
    # action_words = ['a', 'b', 'c', 'd']
    # target_state_string = 'Buff3'
    # state_map = {
    #     'Cell': 'a.b\'.Cell',
    #     'C0': 'Cell[c/b]',
    #     'C1': 'Cell[c/a,d/b]',
    #     'C2': 'Cell[d/a]',
    #     'Buff3': '(C0|C1|C2)/{c,d}'
    # }
    #
    # SG1 = StateGraph('SG1', action_words, target_state_string, state_map)

    pickle_file = open('data/spec_1.pickle', 'rb')
    SG1 = pickle.load(pickle_file)
    pickle_file.close()

    pickle_file = open('data/spec_2.pickle', 'rb')
    SG2 = pickle.load(pickle_file)
    pickle_file.close()

    strong_bisimulation(SG1, SG2)
    weak_bisimulation(SG1, SG2)
