#!/usr/bin/env  python
##
# Dave Rogers
# dave at drogers dot us
# This software is for instructive purposes.  Use at your own risk - not meant to be robust at all.
# Feel free to use anything, credit is appreciated if warranted.
##
'''
Show available named colors in a big grid, adjust start_color
to see all.

Created on Oct 31, 2010

@author: drogers
'''
from Tkinter import *
import os, sys

def main():
    infile = './tk_colors'
    
    all_colors = open(infile).read().split()
#    for i in range(160, 320):
#        print "%d: %s" % (i, all_colors[i])
#    return
    num_rows = 40
    num_col_sections = 4
    section = 0  # up to 4
    start_color = 160 * section
    num_colors = num_rows * num_col_sections
    # for layout of grid
    cols_per_section = 4
    
    print "len(all_colors): %d" % len(all_colors)
    print "showing colors: %d  to  %d" % (start_color, start_color + num_colors)
    
    max_name_len = max([len(s) for s in all_colors])
#    print max_name_len

    for i in range(num_rows):
        for j in range(num_col_sections):
            color_index = start_color + i*num_col_sections + j
            if color_index >= len(all_colors): break
#            print "color_index: %d" % color_index
            color = all_colors[color_index]
            index = Label(text='%d' % color_index, relief=RIDGE, width=3)
            index.grid(row=i, column=j*cols_per_section)
            lname = Label(text=color, relief=RIDGE, width=max_name_len)  # width=25)
            lname.grid(row=i, column=j*cols_per_section+2)       # l.grid(row=i, column=j*2)
            rgb = lname.winfo_rgb(color)
            rgb = tuple([x/256 for x in rgb])
            print "%s: %s" % (color, str(rgb))
            # hex form for use in tkinter
            tk_rgb = "#%02x%02x%02x" % rgb
            lrgb = Label(text=str(rgb), relief=RIDGE, width=15)
            lrgb.grid(row=i, column=j*cols_per_section+1)
            
            e = Entry(bg=color,   relief=SUNKEN, width=20)
            e.grid(row=i, column=j*cols_per_section+3)         # .grid(row=i, column=j*2+1)   
            
    
    mainloop()

if __name__ == '__main__':
    main()