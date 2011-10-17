##
# Dave Rogers
# dave at drogers dot us
# This software is for instructive purposes.  Use at your own risk - not meant to be robust at all.
# Feel free to use anything, credit is appreciated if warranted.
##

'''
Created on Oct 23, 2010

@author: drogers
'''
import unittest
from tm.turing_machine import *


class TestTMParts(unittest.TestCase):


    def setUp(self):
        self.sigma = [Symbol('B'), Symbol('0'), Symbol('1')]
        self.gamma = [Symbol('B'), Symbol('B', '.'), Symbol('0'), Symbol('0', '.'), 
                      Symbol('1'), Symbol('1', '.')]
        self.blank = Symbol('B')
        self.tape = Tape(alphabet=self.gamma, blank=self.blank)
        self.tm = TM(alphabet=self.sigma, num_tapes=1, tape_alphabets=[self.gamma], 
                     blank_symbol=self.blank)

    def tearDown(self):
        pass


    def test_symbol(self):
        s1 = Symbol('0')
        self.assertEqual(s1.base, '0')
        self.assertEqual(s1.super, None)
        self.assertEqual(s1.sub, None)
        self.assertEqual(s1.__str__(), '0')
        s2 = Symbol('B', '.')
        self.assertEqual(s2.base, 'B')
        self.assertEqual(s2.super, '.')
        self.assertEqual(s2.sub, None)
        self.assertEqual(s2.__str__(), '.B')
        s3 = Symbol('0', '.')
        self.assertNotEqual(s1, s2)
        self.assertNotEqual(s1, s3)
        s4 = Symbol('0')
        self.assertEqual(s1, s4)
        s5 = Symbol('B', '.')
        self.assertEqual(s2, s5)
        
        
    def test_tape_symbol_height(self):
        self.assertEqual(self.tape.symbol_height, 2)
        basic_tape = Tape()
        self.assertEqual(basic_tape.symbol_height, 1)
        tall_tape1 = Tape(alphabet=[Symbol('B'), Symbol('B', '.', '.'), Symbol('0')], blank=Symbol('B'))
        
        tall_tape2 = Tape(alphabet=[Symbol('B'), Symbol('B', super=None, sub='.'), 
                                    Symbol('0'), Symbol('0', super='.', sub=None)], 
                          blank=Symbol('B'))
        self.assertEqual(tall_tape1.symbol_height, 3)
        self.assertEqual(tall_tape2.symbol_height, 3)

    def test_parse_symbols(self):
        s = ' B '
        symbol = self.tape.parse_symbol(s)
        sb = Symbol('B')
        self.assertEqual(symbol, sb)
        s = '.0'
        symbol = self.tape.parse_symbol(s)
        self.assertEqual(symbol, Symbol('0', '.'))
        s = ' 1.'
        symbol = self.tape.parse_symbol(s)
        self.assertEqual(symbol, Symbol('1', None, '.'))
        s = '.B.'
        symbol = self.tape.parse_symbol(s)
        self.assertEqual(symbol, Symbol('B', '.', '.'))
        

    def test_single_tape_init_and_get_string_contents(self):
        self.gamma = [Symbol('B'), Symbol('B', '.'), Symbol('0'), Symbol('0', '.'), 
                      Symbol('1'), Symbol('1', '.')]
        self.blank = Symbol('B')
        self.tapes = [Tape(alphabet=self.gamma, blank=self.blank)]
        self.tm = TM(alphabet=self.sigma, tape_alphabets=[self.gamma], 
                     blank_symbol=self.blank)
        

        input_string = ['0', '.1', '.0', '0', '1', 'B']
        symbols = [self.tapes[0].parse_symbol(s) for s in input_string]
        self.tapes[0].init_input(symbols)
        expected = ['   . .      ', '>0 1 0 0 1 B']
        self.assertEqual(self.tapes[0].get_string_contents('>'), expected)
        
        self.gamma = [Symbol('B'), Symbol('B'), Symbol('0'), Symbol('0'), 
                      Symbol('1'), Symbol('1')]
        self.blank = Symbol('B')
        self.tapes = [Tape(alphabet=self.gamma, blank=self.blank)]
        self.tm = TM(alphabet=self.sigma, tape_alphabets=[self.gamma], 
                     blank_symbol=self.blank)
        
        input_string = ['0', '1', '0', '0', '1', 'B']
        symbols = [self.tapes[0].parse_symbol(s) for s in input_string]
        self.tapes[0].init_input(symbols)
        self.tapes[0].head_pos = 1
        expected = [' 0>1 0 0 1 B']
        self.assertEqual(self.tapes[0].get_string_contents('>'), expected)

        self.gamma = [Symbol('B'), Symbol('B', None, '*'), Symbol('0'), Symbol('0', None, '*'), 
                      Symbol('1'), Symbol('1', None, '*')]
        self.blank = Symbol('B')
        self.tapes = [Tape(alphabet=self.gamma, blank=self.blank)]
        self.tm = TM(alphabet=self.sigma, tape_alphabets=[self.gamma], 
                     blank_symbol=self.blank)
                
        input_string = ['0 ', '1 ', '0* ', '0*', '1', 'B*']
        symbols = [self.tapes[0].parse_symbol(s) for s in input_string]
        self.tapes[0].init_input(symbols)
        self.tapes[0].head_pos = 3
        expected = [' 0 1 0>0 1 B', '     * *   *']
        self.assertEqual(self.tapes[0].get_string_contents('>'), expected)
        
        self.gamma = [Symbol('B'), Symbol('B', '.', '^'), Symbol('0'), Symbol('0', '.', '^'), 
                      Symbol('1'), Symbol('1', '.', '^')]
        self.blank = Symbol('B')
        self.tapes = [Tape(alphabet=self.gamma, blank=self.blank)]
        self.tm = TM(alphabet=self.sigma, tape_alphabets=[self.gamma], 
                     blank_symbol=self.blank)
                
        input_string = ['0 ', '1 ', '.0^ ', '.0', '.1^', 'B^']
        symbols = [self.tapes[0].parse_symbol(s) for s in input_string]
        self.tapes[0].init_input(symbols)
        self.tapes[0].head_pos = 4
        expected = ['     . . .  ', ' 0 1 0 0>1 B', '     ^   ^ ^']
        self.assertEqual(self.tapes[0].get_string_contents('>'), expected)
        
#        print "contents:" 
#        for s in self.tape.contents:
#            print "%s, " % str(s),
#        print 
#        print "string contents:"
#        print self.tape.get_string_contents('>')
#        for line in self.tape.get_string_contents('>'):
#            print line
        

    def test_delta_funcs(self):
        s = "q0  0    q3 .0 r"
        d1 = DeltaFunc(self.tm)
        d1.init_from_string(s)
#        print "d1:"
#        print str(d1)
        self.assertEqual(d1.inputs, [Symbol('0')])
        self.assertEqual(d1.outputs, [Symbol('0', '.')])
        self.assertEqual(d1.directions, [Tape.RIGHT])
        
        s = "q3  .1    q7 B s"
        d1 = DeltaFunc(self.tm)
        d1.init_from_string(s)
#        print "d1:"
#        print str(d1)
        self.assertEqual(d1.inputs, [Symbol('1', '.')])
        self.assertEqual(d1.outputs, [Symbol('B')])
        self.assertEqual(d1.directions, [Tape.STAY])


    def test_init_tm(self):
        input = \
"""description = 'Cool TM'
alphabet      = [('0'), ('1')]

blank_symbol     = Symbol('B')
num_tapes        = 1
tape_alphabets    = [ 
[('B'), ('B', '.'), ('0'), ('0', '.'), ('1'), ('1', '.')]
]

accept_state = "q1"
reject_state = "q2"

## delta functions
q0  0    q3 .0 r
q3  .1    q7 B s
"""
#        alphabet      = [('0'), ('1')]
#        self.tm.alphabet = [Symbol(*s) for s in alphabet]
#        tape.alphabet    = [('B'), ('B', '.'), ('0'), ('0', '.'), ('1'), ('1', '.')]
        self.tm.init(input)
#        print self.tm
        self.assertEqual(self.tm.description, 'Cool TM')
        self.assertEqual(self.tm.alphabet, [Symbol('0'), Symbol('1')])
        tape_alpha = [('B'), ('B', '.'), ('0'), ('0', '.'), ('1'), ('1', '.')]
        expected = [Symbol(*s) for s in tape_alpha]
        self.assertEqual(self.tm.tapes[0].alphabet, expected)


class TestTMs(unittest.TestCase):


    def setUp(self):
        pass
#        self.sigma = [Symbol('B'), Symbol('0'), Symbol('1')]
#        self.gamma = [Symbol('B'), Symbol('B', '.'), Symbol('0'), Symbol('0', '.'), 
#                      Symbol('1'), Symbol('1', '.')]
#        self.blank = Symbol('B')
#        self.tape = Tape(alphabet=self.gamma, blank=self.blank)
#        self.tm = TM(alphabet=self.sigma, tape_alphabet=self.gamma, 
#                     blank_symbol=self.blank)

    def tearDown(self):
        pass

    def test_m3(self):
#        print os.getcwd()
        tm = TM()
        tm.init("../tm/tm_files/m3")
#        print tm
        input = '011001'
        result = tm.run(input, True)
        expected = "accept"
        self.assertEqual(result, expected)
        
        input = '1'
        result = tm.run(input, True)
        expected = "accept"
        self.assertEqual(result, expected)
        
        input = '100100'
        result = tm.run(input, True)
        expected = "reject"
        self.assertEqual(result, expected)
        
        input = ''
        result = tm.run(input, True)
        expected = "reject"
        self.assertEqual(result, expected)

    # m4 M decides 0^n1^n
    def test_m4(self):
        tm = TM()
        tm.init("../tm/tm_files/m4")
        print tm
        input = '000111'
        result = tm.run(input, False)
        expected = "accept"
        self.assertEqual(result, expected)
        
        input = '00011'
        result = tm.run(input, True)
        expected = "reject"
        self.assertEqual(result, expected)
        
        input = '0101'
        result = tm.run(input, True)
        expected = "reject"
        self.assertEqual(result, expected)
        
        input = ''
        result = tm.run(input, True)
        expected = "accept"
        self.assertEqual(result, expected)
        
        input = '0001111'
        result = tm.run(input, True)
        expected = "reject"
        self.assertEqual(result, expected)
        
    # m5 - first multitape machine = 3M that decides 0^n1^n0^n
    def test_m5(self):
        tm = TM()
        tm.init("../tm/tm_files/m5")
        print tm
        input = '001100'
        result = tm.run(input, False)
        expected = "accept"
        self.assertEqual(result, expected)
        
        input = '00110'
        result = tm.run(input, True)
        expected = "reject"
        self.assertEqual(result, expected)
        
        input = '0011000'
        result = tm.run(input, True)
        expected = "reject"
        self.assertEqual(result, expected)
        
        input = ''
        result = tm.run(input, True)
        expected = "accept"
        self.assertEqual(result, expected)
        
        input = '010'
        result = tm.run(input, True)
        expected = "accept"
        self.assertEqual(result, expected)
        
        input = '000011110000'
        result = tm.run(input, True)
        expected = "accept"
        self.assertEqual(result, expected)
        

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()