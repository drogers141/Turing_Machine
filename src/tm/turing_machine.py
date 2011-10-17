#!/usr/bin/env  python
##
# Dave Rogers
# dave at drogers dot us
# This software is for instructive purposes.  Use at your own risk - not meant to be robust at all.
# Feel free to use anything, credit is appreciated if warranted.
##

'''
Implementation of a Turing Machine using description/format of Drs Johnson, Reiter
at CSUEB.
TM is inherently a multitape machine, so first tape on tapes list is assumed to be input tape,
and will have the input initialized on it.  Single tape machine just has tape list of length 1.
TM has a STAY head direction capability in addition to RIGHT and LEFT.  (see the Tape class)
TM features tapes that allow symbols that can be "marked", considering them to be
vertically stacked.  Thus a symbol has a "height" of 1, 2 or 3.  This may be clumsy in some ways,
but has the advantage that it can be handled with ascii, and can be input by representing symbols
as strings "on their side", and can be output on the commandline.  So the basic alphabet 
gamma1 = {'B', '0', '1} has a height of 1, where the alphabet 
gamma2 = {'B', '.B', '0', '.0', '1', '.1'} has a height of 2, and 
gamma3 = {'B', '.B', '.B^', '0', '.0', '.0^', '1', '.1', '.1^'} has a height of 3.
Each symbol in the above form represents from left to right a stack from top to bottom, with
the base symbol being either above, below, or in the center of any marking characters.  
So these alphabets are represented like so on the commandline printout of the tape:
gamma1:

B 0 1 

gamma2:

  .   .   . 
B B 0 0 1 1

gamma3:

  . .   . .   . .
B B B 0 0 0 1 1 1
    ^     ^     ^

For input, delta functions can still be as simple and terse as possible, and merely whitespace
delimited because whitespace is outlawed from being in any alphabet.  The intent of a symbol on input
can be inferred from the nature of the alphabet.  So marking a 0 in gamma2 in a delta function could
be input as:
q3 0    q4 .0    r

which would be represented as:

                   
(q3, 0) -> {q4, .0, R}

with the understanding that the input and output are:

      .
0 and 0

and would be represented as such on the tape.


On input, lines may be single-spaced.  On output a line is considered to be the height of the tallest
symbol in the alphabet, and will always be separated from lines above and below by a blank line to 
avoid confusion.  An assumption is made that there is always a base character and that marking can be
above or below it, or both.  Note that any symbol can be used as a mark, and due to the confines of 
using ascii some will look better above or below.  Hence my example gamma2 uses periods above rather
than below the base symbol.

****** Note:  for parsing ease using multitapes,
** tape contents can't contain 'q' **

If this becomes a thing, it can be fixed, but easier for now..
Note that it will only be checked where it can be a problem, with inputting
a machine from a string or file, where the q would be confused with the
next state in a delta function.  So if machine is not read in, 'q' is ok..
************************************************

Oct 11, 2010
@author: drogers
'''
description= \
"""A multi-tape Turing Machine with Stay direction added.  See module and class docs and the
source for commentary and detailed usage. """
usage = \
"""Usage: %prog [opts]
By default runs interactively, prompting user for a string and prints 
whether or not the string is in the language of the input Turing Machine.  
If no Turing Machine file is given, the trivial Turing Machine that 
decides the language over {0, 1} where all strings start with 0 is used.  
See example files in tm_files for input file specification for Turing
Machines. """

import os, sys
import optparse
import subprocess
import re

class TmException(Exception): pass

class Symbol:
    """Symbol for an alphabet.  Consists of a base symbol and optional super or
    sub symbols that go above or below it conceptually and on output.  On input,
    a left to right order indicates top to bottom.
    """
    def __init__(self, base, super=None, sub=None):
        self.base = base
        self.super = super
        self.sub = sub
        
    def __str__(self):
        """String representation of symbol is just a string as received on input.
        So top to bottom is left to right.  Missing super or sub is replaced with
        empty string.
        """
        a = "" if not self.super else self.super
        b = self.base
        c = "" if not self.sub else self.sub
        return a + b + c
    
    def __eq__(self, other):
        """Equality operator.
        """
        return self.base == other.base and self.super == other.super and self.sub == other.sub
    
    def __ne__(self, other):
        """Inequality operator.
        """
        return not self.__eq__(other)

class Tape:
    """Turing machine tape.  Has an alphabet, keeps track of head position,
    contents.  The alphabet is a list of Symbols. Acts on instructions in the form 
    of ('read_symbol', 'write_symbol', direction).  Assumes list of symbols given 
    as contents are bounded on left and right by infinite number of blanks.  Can 
    define any alphabet, but must contain the Tape.blank symbol.
    Can use Stay for direction if desired.
    """
    # head movement directions
    RIGHT = 1
    LEFT = -1
    STAY = 0
    def __init__(self, alphabet=[Symbol('B'), Symbol('0'), Symbol('1')], 
                 blank=Symbol('B'), contents=None, head_pos=0):
        """alphabet and contents are described above,
        @param blank: symbol indicating a blank, note this must be in the alphabet
        @param head_pos: index in contents immediately to the right of the tape head position 
        """
        self.blank = blank
        self.alphabet = alphabet
        self.contents = [] if contents is None else contents
        self.head_pos = head_pos
        self.symbol_height = self.get_symbol_height()
        
    def init_input(self, input_string, head_pos=0):
        """Copy input string to tape. Tape contents will be initialized as a list with
        the read/write head at head_pos.
        @param input_string: list of Symbols 
        """
        # deep copy of input
        self.contents = input_string[:]
        self.head_pos = head_pos
        
    def init_alphabet(self, alphabet):
        """Use to init an alphabet after construction.
        """
        self.alphabet = alphabet[:]
        self.symbol_height = self.get_symbol_height()
        
    def clear(self):
        """Clear this tape's contents.  Contents list will be empty afterword.
        Logically, it will contain an infinite number of blanks.
        """
        self.contents = []
    
    def alpha_has_supers(self):
        """Returns true if any symbols in alphabet have super."""
        has_super = False
        for symbol in self.alphabet:
            if symbol.super:
                has_super = True
        return has_super
    
    def alpha_has_subs(self):
        """Returns true if any symbols in alphabet have sub."""
        has_sub = False
        for symbol in self.alphabet:
            if symbol.sub:
                has_sub = True
        return has_sub
        
    def get_symbol_height(self):
        """Returns height of alphabet. Height = 1 if no supers or subs, 2 if only subs 
        or supers, 3 if at least one sub and super.
        """
        symbol_height = 1
        if self.alpha_has_supers(): symbol_height += 1 
        if self.alpha_has_subs(): symbol_height += 1 
        return symbol_height
        
    def get_base_line_index(self):
        """Returns index of line containing base characters of symbols in 
        current tape configuration.
        """
        if self.alpha_has_supers():
            return 1
        return 0
    
    def get_string_contents(self, head_pos_char):
        """Returns contents as a list of strings of length equal to symbol_height.
        The list has the strings from top to bottom, formatted to include the head pos
        character before the head position in the line with the base symbols.  The lines
        are synced with each other vertically.  
        @param head_pos_char: assume single character, but could be string,
        will be just to left of head position 
        """
        # array of lines - top down, could be: supers, base, subs; supers, base;
        #     base, subs; base
        lines = []
        for _ in range(self.symbol_height):
            lines.append('')
        supers = subs = None
        if self.alpha_has_supers():
            supers = 0
            base = 1
        else:
            base = 0
        if self.alpha_has_subs():
            subs = base + 1
        # move from right to left across all lines simultaneously
        # note this style puts the head position char in the space right before
        # the symbol in the head pos: a little crowded, but tape positions are
        # not shifted at all due to its presence
        
        # add blank to beginning of all lines if head char. position is not 0
        # keeps lines from shifting when head char is at pos 0
        if self.head_pos != 0:
            for i in range(len(lines)):
                lines[i] += ' '
        for i in range(len(self.contents)):
            # handle head character position
            if i == self.head_pos:
                if not supers is None: 
                    if i != 0: lines[supers] = lines[supers][:-1]
                    lines[supers] += ' ' * len(head_pos_char)
                if not subs is None: 
                    if i != 0: lines[subs] = lines[subs][:-1]
                    lines[subs] += ' ' * len(head_pos_char)
                if i != 0: lines[base] = lines[base][:-1]
                lines[base] += head_pos_char
            sym = self.contents[i]
            if not supers is None:
                s = ' ' if sym.super is None else sym.super 
                lines[supers] += s + ' '
            if not subs is None:
                s = ' ' if sym.sub is None else sym.sub 
                lines[subs] += s + ' '
            lines[base] += sym.base + ' '
#            print "len(lines[supers]): %s, len(lines[base]): %s" % (len(lines[supers]), len(lines[base]))
        
        # sanity check
        width = len(lines[0])
        for line in lines: assert len(line) == width, "uneven lines in get_string_contents"
        
        # trim last blank
        lines = [line[:-1] for line in lines]
        return lines
    
    def current_symbol(self):
        """Returns Symbol on tape at head position.
        """
        if self.head_pos < 0 or self.head_pos > len(self.contents)-1:
            return self.blank
        return self.contents[self.head_pos]
    
    def do(self, input, output, direction):
        """Performs instruction of transition function, checking that input matches character 
        (or string) at the head position, writing the output character (or string) at that 
        position, and moving the head in direction.
        @param input: current char/string in alphabet at head position
        @param output: char/string in alphabet to write at head position
        @param direction: one of { Tape.RIGHT, Tape.LEFT, Tape.STAY }
        """
        if (self.current_symbol() != input 
            or not direction in (Tape.LEFT, Tape.RIGHT, Tape.STAY)
            or output not in self.alphabet):
            print "Tape.do(): bad instruction: (input=%s, output=%s, direction=%d)" % (input, output,
                                                                                       direction)
            print "Tape: %s" % self.get_contents()
            sys.exit(1)
        
        # need to check if we need to change the tape
        if self.head_pos < 0 or self.head_pos > len(self.contents)-1:
            self._adjust_tape()
        self.contents[self.head_pos] = output
        self.head_pos += direction
        # check tape again
        if self.head_pos < 0 or self.head_pos > len(self.contents)-1:
            self._adjust_tape()
        
    def _adjust_tape(self):
        """Tape is a list bounded by blanks, if we need to write a non-blank onto a blank  
        off either end of the known tape, we need to increase the boundaries to include it.
        Note: could change this to be a dictionary, then it wouldn't matter..
        """
        if self.head_pos < 0:
            # shift known tape to left
            new_tape = []
            for i in range(self.head_pos, 0):
                new_tape.append(self.blank)
            self.contents = new_tape + self.contents
        elif self.head_pos > len(self.contents)-1:
            # add to known tape on right
            new_tape = []
            for i in range(len(self.contents)-1, self.head_pos+1):
                new_tape.append(self.blank)
            self.contents += new_tape
            
    def parse_symbol(self, str_symbol):
        """Returns Symbol object from string version of symbol, inferring from 
        self.alphabet.
        Symbols are parsed in their string repr. form of super + base + sub, with no whitespace
        in between, so
        .0  -> base='0', super='.', sub=None
        0  -> base='0', super=None, sub=None
        0.  -> base='0', super=None, sub='.'
        .0.  -> base='0', super='.', sub='.'
        @raise TmException: if string is uncool 
        """
        base = super = sub = None
        str_symbol = str_symbol.strip()
        if len(str_symbol) == 1:
            base = str_symbol
        elif len(str_symbol) == 3:
            base = str_symbol[1]
            super = str_symbol[0]
            sub = str_symbol[2]
        elif len(str_symbol) == 2:
            first, second = str_symbol[0], str_symbol[1]
            base_chars = [symbol.base for symbol in self.alphabet]
            if first in base_chars:
                base = first
                sub = second
            elif second in base_chars:
                super = first
                base = second
            else:
                raise TmException('Tape.parse_symbol: base symbol not in string: %s' % str_symbol)
        else:
            raise TmException('Tape.parse_symbol: bad symbol string: %s' % str_symbol)
        
        return Symbol(base, super, sub)

class DeltaFunc:
    def __init__(self, tm, start=None, inputs=None, goto=None, outputs=None, directions=None):
        """Encapsulates a transition, assumes multitape, so inputs, outputs, and directions
        are lists of length equal to the number of tapes in order of tapes, with first being 
        either the only tape, or the input tape. 
        @param inputs, outputs: lists of Symbol objects 
        @param directions: Head movement direction: Tape.RIGHT, Tape.LEFT, or Tape.STAY
        @param tm: reference to Turing Machine this function works with
        """
        # our turing machine
        self.tm = tm
        # state machine is in before transition
        self.start_state = start
        # symbol on each tape under read/write head in tape order
        self.inputs = inputs
        # state machine goes to
        self.goto_state = goto
        # symbol written on each tape
        self.outputs = outputs
        # direction to move read/write head on each tape
        self.directions = directions
        
    def init_from_string(self, str_val):
        """Create delta function from blank/tab delimited string of the form:
        initial_state    inputs    goto_state    outputs    directions
        eg:            q3    0    q4    0    right
        
        or for 2-tape: q3 0 1     q4 B 1  right right
        
        states should start with 'q' and follow with a positive integer,
        the start state is q0, the accept and reject states can be either named by
        their assigned number in the machine (eg. q1), or qaccept, q_accept for the accept state
        and qreject, q_reject for the reject state.
        right, left, stay can be abbreviate r, l, s.
        Symbols are parsed in their string repr. form of super + base + sub, with no whitespace
        in between, so
        .0  -> base='0', super='.', sub=None
        0  -> base='0', super=None, sub=None
        0.  -> base='0', super=None, sub='.'
        .0.  -> base='0', super='.', sub='.'
        """
        parts = str_val.split()
#        print parts
        tok_num = 0
        self.start_state = parts[tok_num]
        tok_num += 1
        self.inputs, self.outputs, self.directions = [], [], []
        for i in range(tok_num, tok_num + self.tm.num_tapes):
            j = i - tok_num
            self.inputs.append( self.tm.tapes[j].parse_symbol(parts[i]) )
            tok_num += 1
        
        assert(parts[tok_num].startswith('q'))
        self.goto_state = parts[tok_num]
        tok_num += 1
        if self.goto_state.find("accept") != -1:
            self.goto_state = self.tm.accept_state
        elif self.goto_state.find("reject") != -1:
            self.goto_state = self.tm.reject_state
        
        for i in range(tok_num, tok_num + self.tm.num_tapes):
            j = i - tok_num
            self.outputs.append( self.tm.tapes[j].parse_symbol(parts[i]) )
            tok_num += 1
        
        for i in range(tok_num, tok_num + self.tm.num_tapes):
            direction = parts[tok_num]
            if direction.lower().startswith('r'):
                self.directions.append(Tape.RIGHT)
            elif direction.lower().startswith('l'):
                self.directions.append(Tape.LEFT)
            elif direction.lower().startswith('s'):
                self.directions.append(Tape.STAY)
            else:
                print "DeltaFunc: bad string: " % str_val
                sys.exit(1)
            tok_num += 1
            
            
    def __str__(self):
        assert(len(self.inputs) == len(self.outputs) == len(self.directions))
        head_direct_str, input_str, output_str = '', '', ''
        for i in range(len(self.inputs)):
            # head directions
            if self.directions[i] == Tape.RIGHT:
                direction = 'R'
            elif self.directions[i] == Tape.LEFT:
                direction = 'L'
            elif self.directions[i] == Tape.STAY:
                direction = 'S'
            head_direct_str += '%s, ' % (direction)
            # inputs
            input_str += '%s, ' % (str(self.inputs[i]))
            # outputs
            output_str += '%s, ' % (str(self.outputs[i]))
        # trim end commas, spaces
        head_direct_str = head_direct_str.rstrip(', ')
        input_str = input_str.rstrip(', ')
        output_str = output_str.rstrip(', ')
        
        goto = self.goto_state
        if self.goto_state == self.tm.accept_state:
            goto = "q_accept"
        elif self.goto_state == self.tm.reject_state:
            goto = "q_reject"
        ret = "(%s, %s) -> {%s, %s, %s}" % (self.start_state, input_str,
                                            goto, output_str, head_direct_str)
        return ret
        
      
class TM:
    """Turing Machine with multiple tapes possible.  Always assume that the first
    tape is the input tape.  So regular machine has tape list of length 1.
    Note that all tapes use the same blank symbol, kept as an attribute of the tm.
    """
    def __init__(self, description='', 
                 start_state='q0', accept_state='q1', reject_state='q2',  
                 alphabet=[Symbol('0'), Symbol('1')], num_tapes=1, tape_alphabets=None, 
                 blank_symbol=Symbol('B'), init_source=None):
        """Creates a TM.
        Note - the states should all have a non-negative integer value, by convention,
        start = q0, accept = q1, reject=q2, all other states = q3, q4, ..
        But this doesn't matter as the states are keys in a dictionary of delta_functions.
        @param start_state: string, eg default is q0
        @param accept_state: string, eg default is q1
        @param reject_state: string, eg default is q2
        @param description: string description of tm
        @param alphabet: the input alphabet
        @param num_tapes: how many tapes in this machine
        @param tape_alphabets: list of tape alphabets, 1 per tape, tapes for machine will be 
        created for each in order, so make sure first is input tape
        @param blank_symbol: blank symbol for all tapes, see Tape class
        @param input_source: input the tm from a string or file, at this point
            at least need to input delta functions here, see init()
        """ 
        self.num_tapes = num_tapes
        self.alphabet = alphabet
        # blank for all tape alphabets, to make things easier
        self.blank_symbol = blank_symbol
        # initialize tape list
        self.tapes = []
        if tape_alphabets and self.blank_symbol:
            assert(len(tape_alphabets) == num_tapes)
            for talpha in tape_alphabets:
                self.tapes.append( Tape(talpha, self.blank_symbol) )
        else:
            for _ in range(self.num_tapes):
                self.tapes.append( Tape(blank=self.blank_symbol) )
            
        self.start_state = start_state
        self.accept_state = accept_state
        self.reject_state = reject_state
        
        # description of tm
        self.description = description
        
        # current state
        self.state = None
        
        # all delta funcs
        self.delta_functions = None
        
        # init from source - file or string (see init())
        if not init_source is None:
            self.init(init_source)
        
        # string to indicate read/write head position in state output
        self.head_pos_indicator = '>'


    def run(self, input_string, quiet=False):
        """Run TM on input_string.
        Can take input as string, but translates into Symbols.
        If input alphabet has complex symbols in it (ie they contain supers or subs)
        then input string should be a list of symbols.
        Returns string of results.
        @param quiet: if True, does not print anything. 
        @return: "accept", or "reject"
        """
        if isinstance(input_string, basestring):
            symbol_string = [Symbol(s) for s in input_string]
        else:
            raise TmException('run(): implement symbol string input')
        
        # check input_string's members are in alphabet
#        for member in input_string:
#            if not member in self.alphabet:
#                print "TM.run(): input not in alphabet. \nInput: %s" % input_string
#                print "Alphabet: %s" % str(self.alphabet)
#                sys.exit(1)
        if not quiet:
            print 'Tape read/write head position = "%s"' % self.head_pos_indicator
            print "Input:"
            print "%s \n" % input_string 
            print 'State  Tape'
        
        # string containing state and tape contents
        state_string = ''
        # character to use to fill line with in between printouts of
        # state and input tape contents
        line_delim_char = '-'
        self.tapes[0].init_input(symbol_string)
        for i in range(1, self.num_tapes):
            self.tapes[i].clear()
        self.state = self.start_state
        while self.state not in (self.accept_state, self.reject_state):
            state_str_list = self.get_str_state()
            if not quiet:
                print '\n'.join(state_str_list)
                print line_delim_char * len(state_str_list[0])
            # symbols under head of each tape
            current_symbols = [t.current_symbol() for t in self.tapes]
            self.handle_transition(current_symbols)
        
        result = ''
        if self.state == self.accept_state:
            result = 'accept'
        elif self.state == self.reject_state:
            result = 'reject'
        else:
            print "TM.run(): error, end loop without accepting or rejecting"
        
        if not quiet:    
            print result
        
        return result
    
    def handle_transition(self, input_symbols):
        """Given current state and list of input symbols for current input symbol
        on each tape, selects appropriate delta function (or generates reject)
        and delegates work to each tape.
        """
        delta = self.get_delta_func(input_symbols)
        assert(len(delta.inputs) == self.num_tapes)
        for i in range(self.num_tapes):
            self.tapes[i].do(delta.inputs[i], delta.outputs[i], delta.directions[i])
        self.state = delta.goto_state
        
        
    def get_delta_func(self, symbols):
        """Get the transition function for the current state and input symbols.
        Input symbols are the symbols under the head of each tape in order.  So on
        single tape machine, list of length 1, ie just symbol_0.
        Automatically generate a rejecting transition of the form:
        (q_current, symbol_0, symbol_1, ..)  -> (q_reject, symbol_0, symbol_1, .., Tape.RIGHT, Tape.RIGHT, ..)
        If no transition for (q_current, symbol_0) exists, where q_current is 
        the current state.
        @param symbols: list of input symbols, ie symbol under each head for each tape in tape order
        """
        delta = None
        for d in self.delta_functions:
            if self.state == d.start_state and symbols == d.inputs:
                delta = d
        if delta is None:
#            print "TM.get_delta_func(): no delta for input symbol: %s" % symbol
#            print "current state: %s" % self.state
#            sys.exit(1)
            directions = []
            for _ in range(self.num_tapes): directions.append(Tape.RIGHT)
            delta = DeltaFunc(self, self.state, symbols, self.reject_state, symbols, directions)
        
        return delta
        
    def get_str_state(self):
        """Return terse version of machine state as list of strings, one per line.
        The first has current state and tape[0] contents, then tape contents of
        remaining tapes on further lines with all tapes vertically aligned.
        """
        retlist = []
        for j in range(len(self.tapes)):
            tape_contents = self.tapes[j].get_string_contents(self.head_pos_indicator)
            if len(tape_contents[0]) > 72:
                raise TmException("print_state(): implement printing long tape")
            
            retstr = ''
            spaces = ' ' * len(self.state)
            for i in range(len(tape_contents)):
                if j==0 and i == self.tapes[j].get_base_line_index():
                    s = self.state
                else:
                    s = spaces
                retstr += "%-6s %s\n" % (s, tape_contents[i])
            retlist.append( retstr.rstrip() )
        return retlist

    def init(self, init_source):
        """Input a TM from a file or string.
        Input format:
        # is a comment
        # blank lines ignored
        # name = value section, right side will be eval()ed and
        #    assigned to tm.left_side, for any = found
        description = "tm description"
        blank_symbol = Symbol('B')
        num_tapes = 1
        
        # the alphabets are handled specially, and must be in this format
        # note that the tape_alphabets uses an underscore rather than a dot
        # alphabets are parsed as lists of tuples of parameters to the appropriate
        # symbol constructor
        # the tape_alphabets is a list of alphabets for each tape in tape order
        # all tape alphabets must contain the blank symbol
        alphabet      = [('0'), ('1')]
        tape_alphabets    = [
        [('B'), ('B', '.'), ('0'), ('0', '.'), ('1'), ('1', '.')]
        ]
        
        ## after whatever name = values, rest is delta functions
        ## for now indicated by starting with q (change if we
        ## implement some attribute starting with q ..
        ## see DeltaFunc class for commentary on init_from_string for multitape, etc
        q0 0    q_reject 0 r
        q0 1    q_accept 1 r
        q0 B    qaccept B r
        ...
        """
        # parsing state: 
        # 0 = reading names and values
        # 1 = reading delta functions
        state = 0
        delta_funcs = []
        if os.path.isfile(init_source):
            lines = open(init_source).readlines()
        elif isinstance(init_source, basestring):
            lines = init_source.splitlines()
        # state to clumsily handle reading multiline input
        reading_tape_alphabets = False
        tape_alpha_string = ''
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'): continue
            
            if state == 0:
                if line.startswith('q') or line.startswith('Q'):
                    state = 1
                elif reading_tape_alphabets:
                    tape_alpha_string += line.strip()
                    if tape_alpha_string.endswith((']]', '],]')):
                        reading_tape_alphabets = False
#                        print "done: tape_alpha_string: "
#                        print tape_alpha_string
                        try:
                            tape_alpha_string = tape_alpha_string.split('=')[1]
                            tape_alphabets = eval(tape_alpha_string)
                            for i in range(len(tape_alphabets)):
                                alpha = [Symbol(*s) for s in tape_alphabets[i]]
                                try:
                                    self.tapes[i].init_alphabet(alpha)
                                except IndexError:
                                    t = Tape(blank=self.blank_symbol)
                                    t.init_alphabet(alpha)
                                    self.tapes.append(t)
                        except Exception as e:                            
                            print "error parsing tape_alphabets"
                            print e
                            print "string val:"
                            print tape_alpha_string
#                        exec """tapes = %s;self.tape_alphabets = [Symbol(*s) for s in %s]""" % (
#                                                            tape_alpha_string)
                    
                elif '=' in line:
                    try:
                        # create alphabets by calling Symbol() constructor on tuples of params
                        if line.find('alphabet') != -1:
                            if line.find('tape_alphabet') != -1:
                                reading_tape_alphabets = True
                                tape_alpha_string += line
                            else:
                                exec """%s""" % line
                                s1 = "alphabet"
                                exec_stmt = """self.%s = [Symbol(*s) for s in %s]""" % (s1, s1)
                                exec exec_stmt
                        else:
                            exec_stmt = """self.%s""" % line
                            exec exec_stmt
                    except:
                        print "error: exec_stmt: %s" % exec_stmt
                        
                    
            if state == 1:
                delta_funcs.append(line + '\n')
            
        self.load_delta_functions("\n".join(delta_funcs))
        
        
    def load_delta_functions(self, delta_functions):
        """Load the machine's delta, or transition, functions. 
        Each delta function is represented in the input by a one-line string, 
        blank/tab delimited, of the form:
        initial_state    inputs    goto_state    outputs    directions
        eg:    q3    0    q4    0    right
        states should start with 'q' and follow with a positive integer,
        the start state is q0, the accept and reject states can be either named by
        their assigned number in the machine (eg. q1), or qaccept, q_accept for the accept state
        and qreject, q_reject for the reject state.
        right, left can be abbreviate r, l.
        
        The delta functions are maintained in the TM as a list of DeltaFunc objects
                
        @param delta_functions: multiline string
        """
        self.delta_functions = []
        lines = delta_functions.splitlines()
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'): continue
#            print "line: %s" % line
            d = DeltaFunc(self)
            d.init_from_string(line)
#            print d
            self.delta_functions.append(d)
            
    def get_states(self):
        """Returns list of states in machine.
        """
        ret = [ self.start_state, self.accept_state, self.reject_state ]
        for d in self.delta_functions:
            if not d.start_state in ret:
                ret.append(d.start_state)
        return ret
            
    def __str__(self):
        """String representation of this TM, for all you math heads ..
        """
        alphabet = [str(s) for s in self.alphabet]
        tape_alphabets = []
        for tape in self.tapes:
            tape_alphabets.append([str(s) for s in tape.alphabet])
        strval = \
"""TM: %s

(Sigma, Gammas, Q, q_accept, q_reject, q_start, delta_functions)
Sigma = %s
Gammas = %s
Q = %s
q_start = %s
q_accept = %s
q_reject = %s


Delta Functions:
""" % (self.description, str(alphabet), str(tape_alphabets), 
       self.get_states(), self.start_state, self.accept_state, 
       self.reject_state)
        for d in self.delta_functions:
            strval += "%s\n" % str(d)
        
        return strval


    def run_interactive(self):
        """Run TM interactively, prompting user for new strings to run
        machine on.
        Q,q exits
        """
        while True:
            input = raw_input("Enter input string or Q to quit: ")
            if input in ['Q', 'q']:
                break
            self.run(input)
            print
            

def main(argv=None):
    if argv is None:
        argv = sys.argv
    op = optparse.OptionParser(description=description, usage=usage)

    op.add_option('-u', '--usage', action="store_true", dest='usage',
                  help='show this message and exit',)
    op.add_option('-f', '--file', dest='infile',
                  help='input TM from file',)
    op.add_option('-r', '--run-string', action="store_true", dest='run_string',
                  help='Assumes that an input file is given with a Turing Machine, and a string is ' +
                  'provided as the only arg on the commandline.  Runs the Turing Machine on the given ' +
                  'string and outputs "accept" or "reject".',)

    (opts, args) = op.parse_args(args=argv)

#    print "opts: %s" % str(opts)
#    print "args: %s" % str(args)
    
    # input TM from file
    infile = None
    
    if opts:
        if opts.usage:
            op.print_help()
            return 0
        if opts.infile:
            infile = open(opts.infile).read()
        
    if opts.run_string:
        try:
            input = args[1]
            tm = TM(init_source=infile)
            print tm.run(input, True)
            return 0
        
        except Exception:
            return 1
    
    # most trivial tm
    m1_delta = """
    description = "{ w | w starts with a 0 }"
    q0 0    q_accept 0 r
    q0 1    q_reject 1 r
    q0 B    qreject B r
    """
    
    if infile:
        tm = TM(init_source=infile)
    else:
        tm = TM(init_source=m1_delta)
#    tm.run('1010101000')

    print "Running Turing Machine:"
    print '***********************'
    print tm
    print '***********************'
    tm.run_interactive()
    
    
if __name__ == '__main__':
    main()
    