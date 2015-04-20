import copy
import re
import random
import string
import uuid

__author__ = 'drack3800'

"""
Non-terminals regex: "[A-Z][0-9]*"
Terminals regex: "[a-z]" (latin alphabet)
Non-terminals and terminals must be splitted in a rule: A -> A42 b C067 d e F (it's a form for A -> A42bC067deF)
"""

NONTERMINAL_REGEX = re.compile("[A-Z][0-9]*")
TERMINAL_REGEX = re.compile("[a-z]")

def is_terminal(word):
    return TERMINAL_REGEX.fullmatch(word) is not None

def is_non_terminal(word):
    return NONTERMINAL_REGEX.fullmatch(word) is not None

class CFG():
    """
    productions is a list of tuples or dict: [("A", "A b A b"), ("A", "a")]
    But self.productions is a dict of sets {"A": {"A b A b", "a"}}
    """

    def __init__(self, start, productions):
        self.chomsky_form = None
        if not is_non_terminal(start):
            raise SyntaxError("Invalid start non-terminal {0}".format(start))
        self.start = start
        self.productions = {}
        for left, right in productions:
            if not is_non_terminal(left):
                raise SyntaxError("Invalid production rule \"{0}\" -> \"{1}\"".format(left, right))
            if self.productions.get(left) is None:
                self.productions[left] = {right.strip()}
            else:
                self.productions[left].add(right.strip())

    """
    Return new grammar object with the same language in Chomsky Normal Form
    Help: http://courses.cs.washington.edu/courses/cse322/09sp/lec14.pdf
    """

    def get_in_cnf(self):
        def add_new_start_state():
            res.start = CFG.__generate_non_terminal()
            res.productions[res.start] = {self.start}

        def eliminate_one_epsilon_rule():
            epsilon_rule = None
            for left, right_set in res.productions.items():
                if "" in right_set:
                    epsilon_rule = left
            if epsilon_rule is None:
                return False

            # Delete epsilon rule
            res.productions[epsilon_rule].remove("")
            # Find occurrences
            rules_to_add = []
            for left, right_set in res.productions.items():
                for right in right_set:
                    processed = ''.join(right.split(epsilon_rule))
                    if processed != right:
                        rules_to_add.append((left, right))
            # Adding
            for left, right in rules_to_add:
                right_splitted = right.split()
                for i in range(len(right_splitted)):
                    if right_splitted[i] == epsilon_rule:
                        if i + 1 < len(right_splitted):
                            res.productions[left].add(' '.join(right_splitted[:i] + right_splitted[i+1:]))
                        else:
                            res.productions[left].add(' '.join(right_splitted[:i]))
            return True

        def eliminate_epsilon_rules():
            while eliminate_one_epsilon_rule():
                pass

        def eliminate_one_unit_rule():
            unit_rule = None
            for left, right_set in res.productions.items():
                # if left != res.start:
                    for right in right_set:
                        if is_non_terminal(right):
                            unit_rule = (left, right)
            if unit_rule is None:
                return False

            left, right = unit_rule
            # Remove this unit rule (A -> B)
            res.productions[left].remove(right)
            # And replace it by rules (B -> u)
            for right_right in res.productions.get(right, {}):
                res.productions[left].add(right_right)

        def eliminate_unit_rules():
            while eliminate_one_unit_rule():
                pass

        def eliminate_one_long_rule():
            long_rule = None
            for left, right_set in res.productions.items():
                for right in right_set:
                    splitted = right.split()
                    if len(splitted) > 2:
                        long_rule = (left, right)
            if long_rule is None:
                return False

            left, right = long_rule
            splitted_right = right.split()
            rest_of_right = splitted_right[1:]
            new_non_terminal = CFG.__generate_non_terminal()
            res.productions[left].remove(right)
            res.productions[left].add(' '.join([splitted_right[0], new_non_terminal]))
            res.productions[new_non_terminal] = {' '.join(rest_of_right)}
            return True

        def process_rules_of_length_two():
            # Collect needed rules
            rules_to_process = set()
            for left, right_set in res.productions.items():
                for right in right_set:
                    splitted = right.split()
                    if len(splitted) == 2:
                        rules_to_process.add((left, right))
            # Process rules length of two. There are no long rules so far.
            for left, right in rules_to_process:
                splitted = right.split()
                if len(splitted) == 2:
                    cond1 = is_terminal(splitted[0])  # first piece is terminal
                    cond2 = is_terminal(splitted[1])   # second piece is terminal
                    if cond1 and cond2:     # both pieces are terminals
                        new_non_terminal_0 = CFG.__generate_non_terminal()
                        new_non_terminal_1 = CFG.__generate_non_terminal()
                        res.productions[new_non_terminal_0] = {splitted[0]}
                        res.productions[new_non_terminal_1] = {splitted[1]}
                        res.productions[left].remove(right)
                        res.productions[left].add(' '.join([new_non_terminal_0, new_non_terminal_1]))
                    elif cond1:
                        new_non_terminal = res.__generate_non_terminal()
                        res.productions[new_non_terminal] = {splitted[0]}
                        res.productions[left].remove(right)
                        res.productions[left].add(' '.join([new_non_terminal, splitted[1]]))
                    elif cond2:
                        new_non_terminal = res.__generate_non_terminal()
                        res.productions[new_non_terminal] = {splitted[1]}
                        res.productions[left].remove(right)
                        res.productions[left].add(' '.join([splitted[0], new_non_terminal]))


        def eliminate_long_rules():
            while eliminate_one_long_rule():
                pass
            process_rules_of_length_two()

        res = copy.deepcopy(self)
        add_new_start_state()
        eliminate_epsilon_rules()
        eliminate_unit_rules()
        eliminate_long_rules()
        return res

    def is_in_cnf(self):
        for left, right_set in self.productions:
            for right in right_set:
                splitted = right.split()
                if right == self.start or not is_non_terminal(left):
                    return False
                elif len(splitted) == 1:
                    # Must be terminal symbol
                    if not is_terminal(right) or right == "":
                        return False
                elif len(splitted) > 2:
                    return False
                elif not is_non_terminal(splitted[0]) or not is_non_terminal(splitted[1]):
                    return False
        return True

    def accept_word(self, word):
        if self.chomsky_form is None:
            self.chomsky_form = self.get_in_cnf()
        # CYK algorithm
        grammar = self.chomsky_form
        if word == "":
            if "" in grammar.productions[grammar.start]:
                return True
            else:
                return False
        n = len(word)
        # Init table
        T = {non_terminal: [[False for i in range(n + 1)] for j in range(n + 1)] for non_terminal in grammar.productions.keys()}
        for i in range(n):
            x = word[i]
            for left, right_set in grammar.productions.items():
                if x in right_set:
                    T[left][i][i + 1] = True
        for l in range(2, n + 1):
            for i in range(n - l + 1):
                j = i + l
                for left, right_set in grammar.productions.items():
                    for right in right_set:
                        splitted = right.split()
                        if len(splitted) == 2:
                            for k in range(i + 1, j):
                                if T[splitted[0]][i][k] and T[splitted[1]][k][j]:
                                    T[left][i][j] = True
        return T[grammar.start][0][n]

    def __str__(self):
        res = "start: " + self.start + "\n"
        for left, right_set in self.productions.items():
            for right in right_set:
                res += "\"{0}\" -> \"{1}\"\n".format(left, right)
        return res

    @staticmethod
    def __generate_non_terminal():
        return random.choice(string.ascii_letters).capitalize() + str(uuid.uuid4())[:6]


if __name__ == "__main__":
    """
    S -> A b A
    S -> B
    B -> b
    B -> c
    A ->
    """
    prod = [("S", "A b A"), ("S", "B"), ("B", "b"), ("B", "c"), ("A", "")]
    a = CFG("S", prod)
    # print(a)
    # print('-'*15)
    print(a.get_in_cnf())
