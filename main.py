from automata import DFA
from grammar import CFG

__author__ = 'drack3800'

import sys

regex = sys.argv[1]
grammar_file = open(sys.argv[2], 'r')
num_of_tests = int(sys.argv[3])

# Skip number, cuz python can read all lines without their amount
grammar_file.readline()

production_rules = []
# Read first rule and determine start symbol in grammar
rule_list = list(part.strip() for part in grammar_file.readline().split())
start = rule_list[0]
production_rules.append((start, ' '.join(rule_list[1::])))

for rule in grammar_file.readlines():
    rule_list = list(part.strip() for part in rule.split())
    production_rules.append((rule_list[0], ' '.join(rule_list[1:])))

grammar = CFG(start, production_rules)
automaton = DFA(regex)

for i in range(num_of_tests):
    word = sys.stdin.readline().strip()
    if grammar.accept_word(word) and automaton.accept_word(word):
        print("YES")
    else:
        print("NO")