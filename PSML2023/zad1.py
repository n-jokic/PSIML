from collections import defaultdict

answerDictionary = defaultdict(list)

entries = [[]]
line = input()
entries[0]+=[line]
while line:
    line = input()

    #print(line)
    if line == "":
        break
    entries[0]+=[line]
                    


#print(entries)

#print(entries)

import itertools

def create():
    global Tree
    class Tree(object):
        id_iter = itertools.count()
        
        _first_time = {}
        
        _files = set()

        _duplicates = {}
        
        _table = {}
        
        def __hash__(self):
            return hash(self.id)

        def __init__(self, name = '/root', children = None):
            self.id = next(self.id_iter)
            
            
            self.depth = 1
            self.name = name
            self.children = {'d':[], 'f':[]}
            self.parent = None
            self.content = set()
            self.unknown = True

            if children is not None:
                for child in children:
                    self.add_child(child)

        def __repr__(self):
            return self.name

        def __eq__(self, other):
            return self.name == other.name

        def __lt__(self, other):
            return self.name < other.name

        def remove_type(self):
            self.name = self.name[3:]
            return self

        def add_child(self, node):
            assert isinstance(node, Tree)
            idx = node.name[1]

            if not (node.name in self.content):

                self.children[idx].append(node)
                self.content.add(node.name)

                node = node.remove_type()

                if(idx == 'f'):
                    #print(node.name)
                    #print(self._files)
                    
                    if(node.name in self._files):
                        self._duplicates[node.name].append((self.depth, self, self.id))
                        if not self.id in self._table:
                            self._table[self.id] = [0, {}, self.depth, [node.name]]
                        else:
                            self._table[self.id][-1].append(node.name)
                    else:
                        self._files.add(node.name)
                        self._duplicates[node.name] = [(self.depth,self ,self.id)]

                if self.children['d']:
                    self.children['d'][-1].parent = self
                    self.children['d'][-1].depth = self.depth + 1

            return self

        def remove_child(self, node):
            idx = node.name[1]
            node = node.remove_type()
            for child in self.children[idx]:

                if child.name == node.name:
                    self.children.pop(child)
                    self.content.remove('(' + idx + ')' + node.name)
                    break
            return self

        def find_child(self, node):
            idx = node.name[1]
            if node.name in self.content:
                node = node.remove_type()

                for child in self.children[idx]:
                    if child.name == node.name:
                        return child
            return None

        def is_present(self, node):
            return node.name in self.content

        def total_count(self):
            total_d = 0
            total_f = 0
            current = self
            stack = []
            over  = False
            
            while not over:
                if current.children['d']:
                    for child in current.children['d']:
                        stack.append(child)
                        total_d+= 1
        
                if current.children['f']:
                    total_f += len(self.children['f'])
                    
                if stack:
                    current = stack[-1]
                    stack.pop()
                else:
                    over = True
                
            return total_d, total_f
                    
           

        def print_out(self, indent =''):
            
            
            if (self.name == '/root'):
                print('/')

            indent += '|-'
            dir_sorted = sorted(self.children['d'])
            #self.height = len(indent)
            

            if dir_sorted:
                for node in dir_sorted:
                    print(indent + node.name + '/')
                    node.print_out(indent = indent)

            f_sorted = sorted(self.children['f'])
            if f_sorted:
                for node in f_sorted:
                    print(indent + node.name)
                    
                    if not (node.name in self._first_time):
                        self._first_time[node.name] = self

            if self.unknown:
                print(indent + '?')



            return
        
        def _remove_redundant_duplicates (self):
            self._table[0] = [0, dict()]
            pop_list =[]
            keys = []
            
            if not self._duplicates:
                return self
            
            for key, value in self._duplicates.items():
                if len(value) == 1:
                    pop_list.append(key)
            
            for key in pop_list:
                self._duplicates.pop(key)
                        
            
            
            return self
        
        def remove_duplicates(self):
            
            self._remove_redundant_duplicates()
            self._find_deepest()
            
            idx = 0
            all_paths = []
            #print((self._duplicates))
            for key in self._duplicates:
                while len(self._duplicates[key]) > 1:
                    node = self._duplicates[key][0]
                    all_paths.append(node[1].create_path())
                    #print((self._duplicates))
                    
             
            #print(all_paths)
            if not all_paths:
                return []
            #print(all_paths)
            all_paths = sorted(all_paths, key = lambda node : len(node[0]))
            longest = all_paths[-1]
            #print(longest)
            all_paths.pop()
            total_path = []
            if not all_paths:
                total_path = longest[0]
                total_path.reverse()
                total_path.pop()
                
            while all_paths:
                #print(longest)
                
                longest_keys = set(longest[1].keys())
                
                shortest = float("inf")
                
                compatible = []
                to_merge = []
                
                idx = 0
                inters_keep = 0
                for path in all_paths:
                    curr_keys = set(path[1].keys())
                    inters=  list(curr_keys.intersection(longest_keys))
                    
                    
                   # print(inters)
                    if not inters:
                        continue
                    
                    inters = sorted(inters, reverse = True)[0]

                    if shortest > longest[1][inters][0]:
                        inters_keep = inters
                        shortest = longest[1][inters][0]
                        compatible = inters
                        to_merge = path
                        remove = idx
                    if shortest == longest[1][inters][0]:
                        if len(to_merge[0]) < len(path[0]):
                            to_merge= path
                            remove = idx
                    idx+=1
                #print(total_path)
                if shortest == float("inf"):
                    temp = longest[0]
                    temp.reverse()
                    
                    if temp[-1] != '$ cd ..':
                        temp.pop()
                        total_path += temp
                    else:
                        total_path += temp
                        

                    if all_paths:
                        longest = all_paths[-1]
                        all_paths.pop()
                        
                        if not all_paths:
                            temp = longest[0]
                            temp.reverse()
                            
                            if total_path:
                                if total_path[-1] != '$ cd ..':
                                    temp.pop()
                                    total_path += temp
                                else:
                                    temp.pop(0)
                                    temp.pop()
                                    total_path += temp
                            else:
                                temp.pop()
                                total_path += temp
                            
                    
        
                    continue
                    
                  

                        
                
                
                inters = inters_keep
                #print('ORIGINAL',all_paths)
                #print(remove + 1)
                #print(len(all_paths))
                if len(all_paths) > 1 and remove+ 1 < len(all_paths):
                    all_paths.pop(remove+1)
                else:
                    all_paths.pop(remove)
                    
                #print('DELETED',all_paths)
                #print(to_merge)
                current_path = to_merge[0]
                original_path = longest[0]
                original_path.reverse()
                start = longest[-1]
                
                #print(longest[1][inters])
                #print('DELTA',start.depth - longest[1][inters][1])
                #print('VS', longest[1][inters][1] - 1)
                
                if (longest[1][inters][1]  == 2):
                        flag = True
                else:
                        flag = False

                if (start.depth - longest[1][inters][1]) < longest[1][inters][1] :
                    original_path.pop()



                    parent = start.parent
                    while parent.id != inters:

                        original_path.append('$ cd ..')
                        parent = parent.parent
                        if parent is None:
                            break
                            
                    original_path.append('$ cd ..')
                    #original_path.pop()
                    #print('TO MERGE', current_path)
                    current_path = current_path[:to_merge[1][inters][0]]
                    current_path.reverse()
                    
                    #print(original_path)
                    #print(current_path)
                    original_path+=current_path
                    #print(original_path)
                else:
                    current_path.pop()
                    current_path.reverse()
                    original_path += current_path 
                #print(flag, original_path)
                if(flag):
                    original_path.pop()
                    original_path.append('$ cd ..')
                    
                original_path.reverse()
                #print(longest)
                longest = (original_path, to_merge[1],to_merge[-1])
                
                
                if not all_paths:
                    #print('HERE')
                    #print(original_path)
                    original_path.reverse()
                    #original_path.pop()
                    
                    if total_path:
                        if total_path[-1] != '$ cd ..':
                                original_path.pop()
                        else: 
                                original_path.pop(0)
                                original_path.pop()
                    else:
                        original_path.pop()
                        
                    total_path += original_path
            return total_path
        
        
        def _find_deepest(self):
            for key in self._duplicates:
                idx = 0
                for member in self._duplicates[key]:
                    if member[1] == self._first_time[key]:
                        
                        temp = self._duplicates[key]
                        self._duplicates[key].pop(idx)
                        self._duplicates[key].append(temp)
                        break
                    idx += 1
            return self
            
        def create_path(self):
            path = []
            path_dict = {}
            parent = self
            path.append('$ cd /')
            idx = 0
            
            #print(self._duplicates)
            keys = self._duplicates.keys()
            keys = sorted(keys, reverse = True)
            for key in keys:
                if (self.depth, self, self.id) in self._duplicates[key]:
                    path.append('$ rm '+key)
                    self._duplicates[key].remove((self.depth, self, self.id))
                    idx += 1
            #print('REMOVED', self._duplicates)
            
            
            if not parent.id:
                path_dict[parent.id] = (idx, parent.depth)
            while parent.id:
                path.append('$ cd ' + parent.name)
                
                idx+=1
                path_dict[parent.id] = (idx, parent.depth)
                parent = parent.parent
                
             
                
            path.append('$ cd /')
            
            
            return path, path_dict, self
    return
        

            #             keys = sorted(keys)
            
            #             for key in keys:
            #                 for i in self._duplicates[key]:
            #                     if i == self._duplicates[key][-1]:
            #                         continue
            #                     deepest_node = i[1]
            #                     depth = deepest_node.depth
            #                     current_node = deepest_node
            
            #                     parent = current_node.parent
            #                     while parent is not None:
            #                         current_node = parent
            #                         if(parent.id in self._table) and parent.id:
            #                             item = (deepest_node.depth - parent.depth, deepest_node)
            
            
            #                             if not item in set(self._table[parent.id][1]):
            #                                 self._table[parent.id][1][deepest_node.id] = item 
            #                                 self._table[deepest_node.id][0] = parent.id
            
            #                             deepest_node = parent
            
            #                         parent = current_node.parent
            
            #                     if deepest_node:
            #                         item = (deepest_node.depth - 1, deepest_node)
            
            #                         if not item in set(self._table[0][1]):
            #                             self._table[0][1][deepest_node.id] = item 
            #                             self._table[deepest_node.id][0] = 0


def process_line(entry, tree):
    root = tree
    current_node = root
    command = ''
    
    for line in entry:
        line = line.split()
        #print(line)
        
        
        if not line:
            if command == 'ls':
                current_node.unknown = False
            continue
            
        if line[0] == '$':
            
            if line[1] == 'cd':
                if line[2] == '/':
                    while current_node.parent is not None:
                        if (current_node.parent is not None):
                            current_node = current_node.parent
                
                if line[2] == '..':
                    if current_node.parent is not None:
                        current_node = current_node.parent
                    
                if line[2] != '/' and line[2] != '..':
                    if(not current_node.is_present(Tree(name = '(d)' + line[2]))):
                        current_node.add_child(Tree(name = '(d)' + line[2]))
                        
                    current_node = current_node.find_child(Tree(name = '(d)' + line[2]))
            
                command = 'cd'
                
            if line[1] == 'ls':
                command = 'ls'
                current_node.unknown = False
                
            
            if line[1] == 'rm':
                command = 'rm'
                current_node.remove_child(Tree(name = '(f)' + line[2]))
                
            #print(current_node.name, current_node.children)
            continue
        else:
            if command == 'ls':
                for name in line:
                    current_node.add_child(Tree(name = name))
        #print(current_node.name, current_node.children)

    return tree

create()

idx = 0
for entry in entries:


    create()
    root = Tree()

    tree = process_line(entry, root)
    d, f = tree.total_count()
    print(d)
    print(f)
    tree.print_out()
    t = tree.remove_duplicates()
    for i in t:
        if i:
            print(i)

