#!/usr/bin/env  python
##
# Dave Rogers
# dave at drogers dot us
# This software is for instructive purposes.  Use at your own risk - not meant to be robust at all.
# Feel free to use anything, credit is appreciated if warranted.
##

'''
Created on Oct 30, 2010

Draw a state machine with Tkinter from existing TM.

@author: Dave Rogers
'''

description= \
"""A very simple gui that generates a state machine from a Turing Machine. """
usage = \
"""Usage: %prog [opts]
When run, the program will show a gui with nodes indicating the states of the Turing 
Machine and no arcs or descriptions of transitions.  Click and drag the nodes to 
where you think the arcs will not interfere with each other and click the "Set Arcs" 
button.  You can now drag the transition descriptions around to declutter them.  If 
you need to re-adjust the nodes, drag them where you want and click the button again 
- everything will be redrawn.  Colors can be adjusted at the top of this module. 

Note that if no file is given, a three-tape machine will be shown.
"""
import sys, os
SRC_ROOT = os.path.abspath(__file__ + '/../..')
#print 'SRC_ROOT: ', SRC_ROOT
if not SRC_ROOT in sys.path:
    sys.path.insert(0, SRC_ROOT)

from Tkinter import Tk, Canvas, Frame, Button, Label, \
LEFT, RIGHT, TOP, BOTTOM, X, BOTH, YES
from tkFont import Font
from tkColorChooser import askcolor
from turing_machine import TM, Tape
from util.drvector import *
import math
from math import sqrt
import Image, ImageDraw
import optparse

### Colors ###

def tk_rgb(rgb):
    """Returns hex form of RGB for use in Tkinter when
    using 0-255 rgb.
    @param rgb: 3-tuple
    """
    hx = "#%02x%02x%02x" % rgb
#    print "%s %s" % (str(rgb), hx)
    return hx

#####  MODIFY COLORS HERE  #####
node_color      = 'palegreen3' #'palevioletred1' # 'palegreen3'
node_text_color = 'black'
#canvas_color    = 'cornsilk' #'lightyellow' # 'beige' #'lemonchiffon'
canvas_color    = tk_rgb( (250, 245, 220) ) #(252, 249, 218) ) #(250, 245, 220)
arc_color       = 'RoyalBlue'
arc_label_bg    = 'white'
arc_label_fg    = 'black'

#############

def tk_to_rgb(hex_str):
    """Returns 0-255 int tuple from tk color string in hex.
    ie #0f00ff.
    """
    return (int(hex_str[1:3], 16), int(hex_str[3:5], 16), int(hex_str[5:7], 16))
    
def dist(pt1, pt2):
    """Returns floating point distance between points pt1 and pt2,
    which can be integral.
    """
    return sqrt( (float(pt2[0])-float(pt1[0]))**2 + (float(pt2[1])-float(pt1[1]))**2 )

def midpt(pt1, pt2):
    """Returns midpoint between pt1 and pt2, all integral.
    """
    return ( pt1[0] + (pt2[0]-pt1[0])/2, pt1[1] + (pt2[1]-pt1[1])/2 )

def closest(node, rest):
    """Returns closest node in node list rest to node.
    @param node: target node
    @param rest: list of nodes that can include target
    (it will be eliminated from consideration)
    """
    mindist = 10000
    closest = None
    for other in rest:
        if not other is node:
            d = dist(node.tl(), other.tl())
            if d < mindist:
                mindist = d
                closest = other
    return closest

class Node:
    def __init__(self, name='q0', coords=(20, 20, 100, 100)):
        """Circle for a state, name is string displayed in center.
        """
        self.name = name        
        self.left = coords[0]
        self.top = coords[1]
        self.right = coords[2]
        self.bottom = coords[3]
        # font for name
        self.font = ('arial', 18, 'bold')
        # ids from canvas if drawn
        self.node_id = None
        self.text_id = None
        
    def width(self):
        return self.right - self.left
    
    def height(self):
        return self.bottom - self.top
    
    def center(self):
        x = self.left + self.width()/2
        y = self.top + self.height()/2
        return (x, y)
    
    def tl(self):
        """Returns (top, left) of node.
        """
        return (self.top, self.left)
    
    def midpoints(self):
        """Return dictionary of named midpoints of bounding box: 
        top, right, bottom, left.
        """
        cx, cy = self.center()
        return {'top':(cx, self.top), 'right': (self.right, cy), 
                'bottom': (cx, self.bottom), 'left': (self.left, cy)}
            
    def in_node(self, pt):
        """Returns False if pt is not considered to be in this node.
        Returns vector displacement (x, y) from top-left if it is.
        @param pt: (x, y)
        """
        (x, y) = pt
        offx = x - self.left
        if offx <= 0 or offx > self.width():
            return False
        offy = y - self.top
        if offy <= 0 or offy > self.height():
            return False
        return (offx, offy)
    
    def move_to(self, canvas=None, top=None, left=None, bottom=None, right=None):
        """Move node to new position, must specify top or bottom, and left or right.
        Assumes width and height remain constant.
        If canvas is passed, will move it on the canvas.
        """
        w = self.width()
        h = self.height()
        (old_top, old_left) = self.tl()
        if not top is None: 
            self.top = top
            self.bottom = self.top + h
        elif not bottom is None:
            self.bottom = bottom
            self.top = bottom - h
        else:
            raise Exception('Node.move(): need top or bottom')
        if not left is None:
            self.left = left
            self.right = left + w
        elif not right is None:
            self.right = right
            self.left = right - w
        else:
            raise Exception('Node.move(): need left or right')
        if canvas:
            canvas.move(self.node_id, (self.left-old_left),(self.top-old_top))
            canvas.move(self.text_id, (self.left-old_left),(self.top-old_top))
        
    def move(self, canvas=None, dx=0, dy=0):
        """Move node by x and y offsets.
        If canvas is passed, moves on the canvas as well.
        """
        new_top = self.top + dy
        new_left = self.left + dx
        self.move_to(canvas=canvas, top=new_top, left=new_left)
        
    def draw(self, canvas):
        """Draws oval on canvas with text label in center.
        Assigns canvas ids to node_id and text_id.
        """
        self.node_id = canvas.create_oval(self.left, self.top, self.right, self.bottom,
                           width=2, fill=node_color)
        (x, y) = self.center()
        self.text_id = canvas.create_text(x, y, text=self.name, font=self.font)
        
    def __str__(self):
        return '%s:\ttop left: (%d, %d) center: %s  width: %d, height: %d' % (
                self.name, self.top, self.left, str(self.center()), self.width(), self.height())
        
        
class Arc:
    def __init__(self, from_pt=(100, 50), to_pt=(150, 100), text=None,
                 color=arc_color, from_node=None, to_node=None):
        self.from_pt = from_pt
        self.to_pt = to_pt
        # the actual nodes this arc connects
        self.from_node = from_node
        self.to_node = to_node
        # identify arc that is loop on single node
        self.is_loop = self.to_node.name == self.from_node.name
        
        # arc stuff
        mid = midpt(from_pt, to_pt)
        self.arc_points = [from_pt, mid, to_pt]
        self.color = color
        self.line_width = 4
        self.arrowshape = (20, 20, 10) # default (8, 10, 3)
        
        self.text = text
        self.font = ('arial', 12)
        self.arc_id = None
        self.text_id = None
        self.text_label = None
        self.text_label_pos = None
        self.text_label_size = None
        self.last_mouse = None
        self.is_selected = False
        self.canvas = None
        
    def length(self):
        """Returns distance between from_pt and to_pt.
        """
        return dist(self.from_pt, self.to_pt)
        
    def clear(self, canvas=None):
        """Clear graphics state and text, remove nodes.
        """
        if not canvas is None:
            if self.arc_id: canvas.delete(self.arc_id)
            if self.text_id: 
                canvas.delete(self.text_id)
                canvas.delete(self.text_label)
                
        self.text = None
        self.from_node = self.to_node = None
        
        
    def draw(self, canvas):
        """Draws arc and text on canvas, if previously drawn,
        deletes first.
        """
        if self.arc_id: canvas.delete(self.arc_id)
        if self.text_id: 
            canvas.delete(self.text_id)
            canvas.delete(self.text_label)
        
        # if its a loop, handle differently
        # use node size as a general metric
        loop_diam = GuiStateMachine.node_diameter
        if self.is_loop:
            # start with point on edge of node (midpt of whatever side of bounding box)
            # put midpoint in direction radiating from center of circle
            start_pt = self.arc_points[0]
            radial = Vec2.from_points(self.from_node.center(), start_pt).unit_vec()
            mid = Vec2(start_pt) + radial * loop_diam
            # now add 2 out to the sides to make a loop
            orthog = Vec2(-radial.y, radial.x) * (loop_diam * .5)
            halfpt = Vec2(start_pt) + radial * (loop_diam * .5)
            pt2 = halfpt + orthog
            pt1 = halfpt - orthog
            self.arc_points = [start_pt, pt1.tuple(), mid.tuple(), pt2.tuple(), start_pt]
            labelx, labely = mid.tuple()
            
#            print "orthog: %s, halfpt: %s" % (str(orthog), str(halfpt))
#            print "len(self.arc_points):", len(self.arc_points)
#            x,y = halfpt
#            canvas.create_oval(x, y, x+20, y+20, fill='purple')
#            for x,y in self.arc_points:
#                print "x, y: %d, %d" % (x, y)
#                canvas.create_oval(x, y, x+20, y+20, fill='red')
#            return

        else:            
            mid = midpt(self.from_pt, self.to_pt)
    #        print "from_pt: %s, to_pt: %s, midpt: %s" % (str(self.from_pt), str(self.to_pt), str(mid))
            labelx, labely = mid
            
        self.arc_id = canvas.create_line(self.arc_points, fill=self.color, smooth=1,
                               arrow='last', arrowshape=self.arrowshape, width=self.line_width)
        self.text_label = Label(canvas, text=self.text, font=self.font, 
                                fg=arc_label_fg, bg=arc_label_bg, #canvas['bg'],
                                padx=10, pady=10, borderwidth=1, relief='solid')
        self.text_label.pack()
        self.text_label.bind('<ButtonPress-1>', self.on_left_click)
        self.text_label.bind('<B1-Motion>', self.on_left_drag)
        
        self.text_id = canvas.create_window(labelx, labely, window=self.text_label)
        self.text_label_pos = (labelx, labely)
        self.canvas = canvas


    def on_left_click(self, event):
        """Handle left click on arc's text label.
        """
#        print 'left click: X=%s Y=%s' % (event.x, event.y)
        self.last_mouse = (event.x, event.y)
        self.is_selected = True
        
            
    def on_left_drag(self, event):
        """Handle left click and drag on canvas.
        """
#        print 'left drag: X=%s Y=%s' % (event.x, event.y)
        pt = (event.x, event.y)
        if self.is_selected:
            (offx, offy) = (pt[0]-self.last_mouse[0], pt[1]-self.last_mouse[1])
#            print "moving: (offx, offy) = %s" % str((offx, offy))
            self.move(self.canvas, offx, offy)
        
            
    def move(self, canvas=None, dx=0, dy=0):
        """Move this arc by dx and dy.  Moves on canvas if canvas is passed.
        Moving the arc consists of moving the text label, then reshaping the
        arc accordingly.
        """
        self.text_label_pos = (self.text_label_pos[0] + dx, self.text_label_pos[1] + dy)
        # for a 3 point line: move the center of the arc with the label
        if not self.is_loop:
            self.arc_points[1] = (self.arc_points[1][0] + dx,
                                  self.arc_points[1][1] + dy)
        # loop has 5 points
        else:
            for i in [1, 3]:
                # note that adjustment is the same, I'm keeping this here
                # though, in case it turns out to need tweaking again
                self.arc_points[i] = (self.arc_points[i][0] + dx,
                                      self.arc_points[i][1] + dy)
            self.arc_points[2] = (self.arc_points[2][0] + dx,
                                  self.arc_points[2][1] + dy)
        if canvas:
            canvas.move(self.text_id, dx, dy)
            if self.arc_id:
                canvas.delete(self.arc_id)
                self.arc_id = canvas.create_line(self.arc_points, fill=self.color, smooth=1,
                               arrow='last', arrowshape=self.arrowshape, width=self.line_width)
    
    def add_transition_string(self, s):
        """Adds transition string to label text as new line.
        """
        if self.text is None: self.text = ""
        numlines = len(self.text.splitlines())
        if numlines == 0:
            self.text += s
        else:
            self.text += "\n" + s
        
    def text_size(self):
        """Returns (w, h) of current text according to current font.
        """
        f = Font(family=self.font[0], size=self.font[1])
        # total height of line, I believe
        h = f.metrics('linespace')
#        print "all metrics:"
#        m = f.metrics()
#        for k in m:
#            print "%s: %s" % (k, str(m[k]))
        lines = self.text.splitlines()
        num_lines = len(lines)
        # max line width
        w = max( [f.measure(line) for line in lines] )
        h = num_lines * h
        
        return (w, h)        
        
    def __str__(self):
        """String rep without geometric stuff.
        """
        fn = "None" if self.from_node is None else self.from_node.name
        tn = "None" if self.to_node is None else self.to_node.name
        t = "" if self.text is None else "%s\n" % self.text
        s = "%s -> %s\n%s" % (fn, tn, t)
        return s
        

class GuiStateMachine:
    """State machine from TM.
    esc to quit
    left click and drag nodes
    
    """
    node_diameter = 120
    
    def __init__(self, parent=None, tm=None, width=1000, height=750):
        self.tm = tm
        self.width = width
        self.height = height
        control = Frame(parent, borderwidth=2, relief='groove')
        Button(control, text='Set Arcs', command=self.set_arcs).pack(side=LEFT)
#        Button(control, text='Export Image', command=self.export_image).pack(side=LEFT)
        Label(control, text=' ').pack(side=LEFT, padx=60)
        Label(control, text="TM Description:  ").pack(side=LEFT)
        Label(control, text=self.tm.description).pack(side=LEFT)
        Button(control, text='Quit', command=parent.quit).pack(side=RIGHT)
#        Button(control, text='Colors', command=askcolor).pack(side=RIGHT)
        control.pack(side=TOP, fill=X)
        self.canvas = Canvas(master=parent, width=width, height=height, bg=canvas_color)
        self.canvas.pack(fill=BOTH, expand=YES) #side=BOTTOM,
        # bind events
        parent.bind('<Escape>', quit)
        self.canvas.bind('<ButtonPress-1>', self.on_left_click)
        self.canvas.bind('<B1-Motion>', self.on_left_drag)
        
        # the nodes and arcs will be the graphical representations
        self.nodes = []
        self.arcs = []
#        # the states are just the string states as
#        # they are in the tm, including the numerical version
#        # of the accept state (does not contain q_reject)
#        self.states = []
        self.init_states()
#        self.print_nodes()
        self.selected_node = None
        self.last_mouse = None
        self.selected_arc = None
        self.arcs_set = False
        
        ## debug
#        self.points = [(100, 100), (200, 100), (200, 200)]
#        self.debug_line = None
#        self.debug_arc = None
        
                
    def init_states(self):
        """Get states from Turing machine, initialize gui nodes from them.
        """
        tm_states = self.tm.get_states()
        # create a node for each state, initially placing
        # them in 2 rows
        half = (len(tm_states)+1) / 2
        rows = [tm_states[:half], tm_states[half:]]
        xspace = self.width / (half+1)
        for i in range(2):
            y = self.height * (i+1)/3
            x = 0 if i==0 else self.width
            for state in rows[i]:
                if state == self.tm.reject_state:
                    continue
                if i==0: x += xspace
                else: x -= xspace
#                self.states.append(state)
                if state == self.tm.accept_state: state = "q_accept"
                nd = GuiStateMachine.node_diameter
                node = Node(name=state, coords=(x, y, x+nd, y+nd))
                self.nodes.append(node)
        print "Nodes:"
        self.print_nodes()
        
        print "tm states:"
        for state in tm_states:
            if state == self.tm.accept_state:
                print "q_accept"
            elif state != self.tm.reject_state:
                print state
                
#        print "States:"
#        print self.states
        
    def draw(self):
        """Draw all nodes and arcs.
        """
        for node in self.nodes:
            node.draw(self.canvas)
        for arc in self.arcs:
            arc.draw(self.canvas)
#        self.debug_line = self.canvas.create_line(self.points, fill='royalblue', width=3, 
#                                smooth=1, arrow='last')
            
            
    def node_to_node(self, from_, fr_side, to_, to_side):
        """Connect 2 nodes with an arc. 
        @param from_: originating node
        @param fr_side: location on originating node, one of {'top', 'left', 'bottom', 'right'}
        @param to_: destination side
        @param to_side: location on dest side, see fr_side for poss. vals
        @return: the connecting arc object
        """
        x1 = y1 = x2 = y2 = 0
        if fr_side in ['top', 'bottom']:
            x1 = from_.center()[0]
            y1 = from_.top if fr_side == 'top' else from_.bottom
        else:
            y1 = from_.center()[1]
            x1 = from_.left if fr_side == 'left' else from_.right
        if to_side in ['top', 'bottom']:
            x2 = to_.center()[0]
            y2 = to_.top if to_side == 'top' else to_.bottom
        else:
            y2 = to_.center()[1]
            x2 = to_.left if to_side == 'left' else to_.right
            
        arc = Arc( (x1, y1), (x2, y2), from_node=from_, to_node=to_)        
        return arc
    
    def closest_sides(self, node1, node2):
        """Returns tuple of 2 strings indicating which 'sides' of the 2
        nodes are closest for joining by arc.
        For example: ('right', 'left')
        Answers are in correct order, so above would mean, join node1's right midside
        with node2's left midside.
        """
        n1mids = node1.midpoints()
        mindist = 10000
        n2mids = node2.midpoints()
        best_pair = None
        for n1 in n1mids:
            v1 = n1mids[n1]
            for n2 in n2mids:
                v2 = n2mids[n2]
                d = dist(v1, v2)
                if d < mindist:
                    mindist = d
                    best_pair = (n1, n2)
        return best_pair
            
    
    def get_by_name(self, name):
        """Returns node in self.nodes if name is found or None.
        Returns correct node for q_accept as well.
        """
        for n in self.nodes:
            if n.name == name:
                return n
            if name == self.tm.accept_state:
                if n.name == "q_accept":
                    return n
        return None
    
    def on_left_click(self, event):
        """Handle left click on canvas.
        """
#        print 'left click: X=%s Y=%s' % (event.x, event.y)
        self.last_mouse = (event.x, event.y)
        for node in self.nodes:
            offset = node.in_node(self.last_mouse)
            if offset:
                self.selected_node = node
                break
        
            
    def on_left_drag(self, event):
        """Handle left click and drag on canvas.
        """
#        print 'left drag: X=%s Y=%s' % (event.x, event.y)
        pt = (event.x, event.y)
        for node in self.nodes:
            offset = node.in_node(pt)
            if offset and node is self.selected_node:
#                print "selected: %s, mouse offset from top left: %s" % (node.name, str(offset))
                (offx, offy) = (pt[0]-self.last_mouse[0], pt[1]-self.last_mouse[1])
                self.last_mouse = pt
#                print "offset from last mouse pos: %s" % str((offx, offy))
                node.move(self.canvas, offx, offy)
                break
                
    def get_delta_string(self, d):
        """Get string version of transition for arc text.
        @param d: DeltaFunc object
        """
        s = ""
        for i in d.inputs: s += "%s, " % str(i).strip()
        s = s.rstrip(', ')
        s += " -> "
        for o in d.outputs: s += "%s, " % str(o).strip()
        for direct in d.directions: 
            if direct == Tape.RIGHT: letter = 'R'
            elif direct == Tape.LEFT: letter = 'L'
            elif direct == Tape.STAY: letter = 'S'
            s += "%s, " % letter
        s = s.rstrip(', ')
        return s
        
    def set_arcs(self):
        """Set or reset all arcs connecting nodes along with their text.
        """
        if self.arcs_set:
            for a in self.arcs:
                a.clear(self.canvas)
            self.arcs = []
            
        q_accept = self.tm.accept_state
        for d in self.tm.delta_functions:
            # ignore delta if it contains reject state
            if d.goto_state == self.tm.reject_state:
                continue
#            print "d: %s" % str(d)
#            print "str vers: %s" % self.get_delta_string(d)
            found = False
            for a in self.arcs:
                if ((d.start_state == a.from_node.name and d.goto_state == a.to_node.name) or
                    (d.start_state == a.from_node.name and d.goto_state == q_accept
                     and a.to_node.name == 'q_accept')):                    
                    s = self.get_delta_string(d)
                    a.add_transition_string(s)
#                    print "start state: %s, string: %s" % (d.start_state, s)
                    found = True
            if not found:
                # add an arc for newly found transition
                # state pair
                from_node = self.get_by_name(d.start_state)
                to_node = self.get_by_name(d.goto_state)
                from_side, to_side = self.closest_sides(from_node, to_node)
                a = self.node_to_node(from_node, from_side, to_node, to_side)
                s = self.get_delta_string(d)
                a.add_transition_string(s)
                self.arcs.append(a)
                
        self.print_arcs()        
        for a in self.arcs:
            a.draw(self.canvas)
        
        self.arcs_set = True
        
#        for node in self.nodes:
#            print "closest sides %s, %s: %s" % (self.nodes[0].name, node.name,
#                                               self.closest_sides(self.nodes[0], node))
        
    def export_image(self):
        """Export to image file.
        """
        print "implement export to image"
        print "highly nontrivial, and probably not worth it..."
#        print tk_to_rgb('#faf5dc')
#        self.canvas.update()
#        outfile = 'tm_out.ps'
#        self.canvas.postscript(file=outfile, colormode='color')
#        bg_str = self.canvas.cget('bg')
##        bg_rgb = self.canvas.winfo_rgb(bg_str)
##        print "background: %s, rgb: %s" % (bg_str, bg_rgb)
#        
#        # some color constants for PIL
#        white = (255, 255, 255)
#        black = (0, 0, 0)
#        blue = (0, 0, 255)
#        red = (255, 0, 0)
#        green = (0,128,0)
#        
##        width = 400
##        height = 300
#        
#        x_increment = 1
#        # width stretch
#        x_factor = 0.04
#        # height stretch
#        y_amplitude = 80
#
#        bg_rgb = tk_to_rgb(bg_str)
#        width = int(self.canvas.cget('width'))
#        height = int(self.canvas.cget('height'))
#        center = height/2
#
#        print "width, height: %d, %d" % (width, height)
#        out_img = Image.new("RGBA", (width, height), bg_rgb)
#        
#        img = ImageDraw.Draw(out_img)
#        img.line([(50, 50), (200, 200)], 'blue')
#        
##        png_out = 'tm_out.png'
#        ps = Image.open(outfile)
#        ps.save('ps_img.ppm')
#        ps.save('ps_img.png')
##        ps = Image.open(png_out)
##        img.paste(ps, (0, 0), ps)
#
#        out_img.save('img.jpg')

            
    def random_nodes(self, num_nodes):
        nodes = []
        diam = 80
        for i in range(num_nodes/2):
            n = Node(name="q%d" % i)
            n.move_to(top=200, left=(i+1)*150)
            nodes.append(n)
        for i in range(num_nodes/2):
            n = Node(name="q%d" % (int(i+num_nodes/2)))
            t = self.height - 200
            n.move_to(top=t, left=(i+1)*150)
            nodes.append(n)
            
        return nodes
        
        
    def even_spacing(self, nodes):
        """Move nodes around so they are maximally spread out.
        """
        x1 = x2 = y1 = y2 = 0
        adjacent = [nodes[0]]
        for node in nodes:
            remaining = [n for n in nodes if not n in adjacent]
            print "adjacent", str([s.name for s in adjacent])
            print "remaining", str([s.name for s in remaining])
            c = closest(node, remaining)
            adjacent.append(c)
                   
            
    def print_nodes(self):
        print "nodes:"
        for node in self.nodes:
            print node

    def print_arcs(self):
        print "arcs:"
        for arc in self.arcs:
            print arc

def main(argv=None):
    if argv is None:
        argv = sys.argv
    op = optparse.OptionParser(description=description, usage=usage)

    op.add_option('-u', '--usage', action="store_true", dest='usage',
                  help='show this message and exit',)
    op.add_option('-f', '--file', dest='infile',
                  help='input TM from file',)

    (opts, args) = op.parse_args(args=argv)

    # input TM from file
    infile = None
    
    if opts:
        if opts.usage:
            op.print_help()
            return 0
        if opts.infile:
            infile = open(opts.infile).read()
            
    root = Tk()
    tm = TM()
    if opts.infile:
        tm.init(infile)
    else:
        tm.init('./tm_files/m5')
    print "TM:"
    print tm
    gsm = GuiStateMachine(parent=root, tm=tm)
    gsm.draw()
    root.mainloop()

if __name__ == '__main__':
    main()
    
    