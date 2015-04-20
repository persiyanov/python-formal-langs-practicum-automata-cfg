__author__ = 'drack3800'

import copy
import uuid
import string

# Class that represents automaton state

"""
Alphabet: latin letters [a-z]
- Dot '.' represents concatenation
- Plus '+' represents "or"
- Star '*' represents Kleene star
"""

CONCAT_SYMBOL = '.'
UNION_SYMBOL = '+'
KLEENE_SYMBOL = '*'
EMPTY_STRING_SYMBOL = '1'
ALPHABET = set(string.ascii_letters)
REGEX_SYMBOLS_ALPHABET = ALPHABET.union({CONCAT_SYMBOL, UNION_SYMBOL, KLEENE_SYMBOL})


class State():
    def __init__(self, state_id=None):
        def generate_id():
            return int(uuid.uuid4())

        self.id = generate_id() if state_id is None else state_id

    def get_id(self):
        return int(self.id)

    def __hash__(self):
        return self.get_id()

    def __eq__(self, other):
        return self.get_id() == other.get_id()

    def __cmp__(self, other):
        if self.get_id() < other.get_id():
            return -1
        elif self.get_id() > other.get_id():
            return 1
        else:
            return 0

    def __str__(self):
        return str(self.get_id())[:5]


class FiniteAutomaton:
    def __init__(self):
        self.start_state = None
        self.finish_state = None
        self.move = None

    # Return set of state neighbors by symbol
    def go(self, state, symbol):
        return frozenset(self.move.get(state, {}).get(symbol, {}))

    def get_start_state(self):
        return copy.copy(self.start_state)

    def get_finish_state(self):
        return copy.copy(self.finish_state)

    def __str__(self):
        res = "start: {0}\n".format(self.get_start_state())
        res += "finish: {0}\n".format(self.get_finish_state())
        for state, symbol_neighbors in self.move.items():
            for symbol, neighbor_set in symbol_neighbors.items():
                for neighbor in neighbor_set:
                    res += "({0}, {1}, {2})\n".format(state, symbol, neighbor)
        return res


"""
NFA is a class which represents non-deterministic finite automaton
"""


class NFA(FiniteAutomaton):
    """
    Initializes an automaton with regular expression in postfix notation
    Example: NFA("ab+abb..*") for regex: (a+b)*abb

    NFA has 1 start state and 1 finish state.
    NFA builds with Thompson construction algorithm. (http://en.wikipedia.org/wiki/Thompson's_construction_algorithm)

    move field is two-dimensional dictionary:  self.move[state][symbol] is set of neighbors
    """

    def __init__(self, postfix_regex):
        super().__init__()
        check_regex(postfix_regex)
        self.postfix_regex = postfix_regex
        if len(postfix_regex) <= 1:
            # Simple two-states automaton for letter or empty word ("1")
            self.start_state = State()
            self.finish_state = State()
            self.move = {self.start_state: {postfix_regex: {self.finish_state}}}
        else:
            # Recursive build according to Thompson algorithm
            self.start_state = None
            self.finish_state = None
            self.move = None
            self.__build_automaton()

    def __build_automaton(self):
        def concat(left, right):
            left.move[left.finish_state] = right.move[right.start_state]
            left.move = dict(list(left.move.items()) + list(right.move.items()))
            del left.move[right.start_state]
            left.finish_state = right.finish_state
            return left

        def union(left, right):
            left.move = dict(list(left.move.items()) + list(right.move.items()))
            new_start_state = State()
            new_finish_state = State()
            left.move[new_start_state] = {"": {left.start_state, right.start_state}}
            left.move[left.finish_state] = {"": {new_finish_state}}
            left.move[right.finish_state] = {"": {new_finish_state}}
            left.start_state = new_start_state
            left.finish_state = new_finish_state
            return left

        def kleene(what):
            new_start_state = State()
            new_finish_state = State()
            what.move[new_start_state] = {"": {new_finish_state, what.start_state}}
            what.move[what.finish_state] = {"": {what.start_state, new_finish_state}}
            what.start_state = new_start_state
            what.finish_state = new_finish_state
            return what

        # Stack keeps automatons for sub-expressions
        stack = []
        for symbol in self.postfix_regex:
            if symbol in ALPHABET:
                stack.append(NFA(symbol))
            elif symbol == CONCAT_SYMBOL:
                right_nfa = stack.pop()
                left_nfa = stack.pop()
                stack.append(concat(left_nfa, right_nfa))
            elif symbol == UNION_SYMBOL:
                right_nfa = stack.pop()
                left_nfa = stack.pop()
                stack.append(union(left_nfa, right_nfa))
            elif symbol == KLEENE_SYMBOL:
                automaton = stack.pop()
                stack.append(kleene(automaton))
        # Here there is one NFA in stack - resulting automaton
        res = stack.pop()
        self.start_state = res.start_state
        self.finish_state = res.finish_state
        self.move = res.move

    def get_postfix_regex(self):
        return self.postfix_regex


class DFA(FiniteAutomaton):
    def __init__(self, build_from):
        super().__init__()
        self.move = {}
        if isinstance(build_from, str):
            check_regex(build_from)
            self.postfix_regex = build_from
            nfa = NFA(self.postfix_regex)
        elif isinstance(build_from, NFA):
            self.postfix_regex = build_from.get_postfix_regex()
            nfa = build_from
        else:
            raise SyntaxError
        self.__build_from_nfa(nfa)

    def __build_from_nfa(self, nfa):
        self.start_state = epsilon_closure(nfa, {nfa.get_start_state()})
        self.move[self.start_state] = {}
        unmarked_states = [self.start_state]
        self.finish_state = set()
        if nfa.get_finish_state() in self.start_state:
            self.finish_state.add(frozenset(self.start_state))
        while len(unmarked_states) > 0:
            unmarked_state = unmarked_states.pop(0)
            for char in ALPHABET:
                adj_neighbors = set()
                for state in unmarked_state:
                    adj_neighbors = adj_neighbors.union(nfa.go(state, char))
                if len(adj_neighbors) > 0:
                    neighbors_set = epsilon_closure(nfa, adj_neighbors)
                    if len(neighbors_set) > 0:
                        if neighbors_set not in self.move.keys():
                            unmarked_states.append(neighbors_set)
                            self.move[neighbors_set] = {}
                        self.move[unmarked_state][char] = {neighbors_set}
                        if nfa.get_finish_state() in neighbors_set:
                            self.finish_state.add(frozenset(neighbors_set))
        self.finish_state = frozenset(self.finish_state)

    def accept_word(self, word):
        state = self.start_state
        for char in word:
            state = self.go(state, char)
            if len(state) == 0:
                return False
            else:
                state = set(state).pop()
        if state in self.finish_state:
            return True
        else:
            return False

    def __str__(self):
        def get_set_name(states_set):
            name = ""
            for state in states_set:
                name += str(state) + " "
            return name

        def get_finish_state_name(finish_state):
            name = ""
            for states_set in finish_state:
                name += "{" + "{0}".format(get_set_name(states_set)) + "} "
            return name
        res = ""
        res += "start: {0}\n".format(get_set_name(self.get_start_state()))
        res += "finish: {0}\n".format(get_finish_state_name(self.get_finish_state()))
        for states_set, symbol_neighbors in self.move.items():
            for symbol, neighbors_set in symbol_neighbors.items():
                for neighbor in neighbors_set:
                    res += "({0}, {1}, {2})\n".format(get_set_name(states_set), symbol, get_set_name(neighbor))
        return res


def check_regex(postfix_regex):
    counter = 0
    for symbol in postfix_regex:
        if symbol not in REGEX_SYMBOLS_ALPHABET:
            raise SyntaxError
        elif symbol in ALPHABET:
            counter += 1
        elif symbol != KLEENE_SYMBOL:
            counter -= 1
        if counter <= 0:
            raise SyntaxError("Invalid postfix notation")


'''
Note: return frozenset!!
'''


def epsilon_closure(nfa, states):
    stack = list(states)
    closure = set(states)
    while len(stack) > 0:
        t = stack.pop()
        # neighbors = nfa.go(t, "")
        # if neighbors is not None:
        for neighbor in nfa.go(t, ""):
            if neighbor not in closure:
                closure.add(neighbor)
                stack.append(neighbor)
    return frozenset(closure)


def test_word(dfa, word):
    print("Accepts " + word + ": " + str(dfa.accept_word(word)))

if __name__ == "__main__":
    # a = NFA('ab+*')
    # print(a)
    a = DFA('aa.*b*.cc.*.')  # (aa)*b*(aa)*
    print(a)
    test_word(a, "aaba")
    test_word(a, "")
    test_word(a, "aa")
    test_word(a, "b")
    test_word(a, "abab")
    test_word(a, "baba")
    test_word(a, "ab")
    test_word(a, "ababab")
    test_word(a, "aaaab")
    test_word(a, "aaab")
    test_word(a, "cc")
    test_word(a, "aabcccc")
    test_word(a, "abc")