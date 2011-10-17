##
# Dave Rogers
# dave at drogers dot us
# This software is for instructive purposes.  Use at your own risk - not meant to be robust at all.
# Feel free to use anything, credit is appreciated if warranted.
##
'''
Vector classes and methods.

Created Apr 30, 2009
@author: Dave Rogers
'''
__all__ = ['Vec2', ]
from math import sin, cos, radians, degrees, sqrt, fabs, atan2
import numpy


class Vec2(object):
    """2d Vector class.  X and Y values are floats.
    """
    def __init__(self, xval_or_seq=0., y=0.):
        """Constructs a 2d vector from 2 scalar values or from any sequence
        with length 2.
        
        @param xval_or_seq: either a numeric value for x or anything with len(2)
        @param y: numeric value for y--only checked if passed scalar x value
        """
        if isinstance(xval_or_seq, (int, float, long)):
            self.x = float(xval_or_seq)
            self.y = float(y)
        elif len(xval_or_seq) == 2:
            self.x = xval_or_seq[0]
            self.y = xval_or_seq[1]
            
    @staticmethod
    def from_points(pt1, pt2):
        """Create a vector from 2 points.  Points can be any indexable
        sequence type.
        
        @param pt1: vector starts from this point
        @param pt2: vector ends at this point
        """
        return Vec2(pt2[0]-pt1[0], pt2[1]-pt1[1])
    
    # for equality with floating point math
    # adjust as necessary
    FLOAT_TOLERANCE = .00001
    
    # standard basis vectors
    @staticmethod
    def i(): return Vec2(1, 0)
    @staticmethod
    def j(): return Vec2(0, 1)
    
    # convenience unit direction vectors
    # Note up and down are already converted to screen coords--ie up is negative y
    @staticmethod
    def right(): return Vec2(1, 0)
    @staticmethod
    def left(): return Vec2(-1, 0)
    @staticmethod
    def up(): return Vec2(0, -1)
    @staticmethod
    def down(): return Vec2(0, 1)
    
    @staticmethod
    def direction_vec(angle):
        """Returns a unit vector with the direction corresponding to angle.
        @param angle: degrees from x axis, -360 <= angle <= 360 
        """
        rads = radians(angle)
        return Vec2(cos(rads), sin(rads))
    
    @staticmethod
    def dot_product(v1, v2):
        return v1.x * v2.x + v1.y * v2.y
    
    def direction(self):
        """Returns the direction this vector is pointing in radians,
        adjusted for screen y (ie positive y points down.)
        """
        return atan2(-self.y, self.x)
                    
    def __repr__(self):
        return "(%s, %s)" % (str(self.x), str(self.y))
            
    def array(self):
        """Returns numpy array."""
        return numpy.array([self.x, self.y])
    
    def tuple(self):
        """Returns tuple."""
        return (self.x, self.y)
    
    def to_int(self):
        """Returns a tuple of ints."""
        return ( int(self.x), int(self.y) )
    
    def magnitude(self):
        """Returns magnitude, or length, as a float."""
        return sqrt(self.x**2 + self.y**2)
        
    def unit_vec(self):
        """Returns unit vector in the direction of this vector, or the
        zero vector if the vector's magnitude is zero."""
        mag = self.magnitude()
        if mag < Vec2.FLOAT_TOLERANCE:
            return Vec2(0, 0)
        return self / self.magnitude()
        
    def convert_y(self):
        """Returns a vector with the y value negated to convert from 
        Cartesian coordinates to screen coordinates."""
        return Vec2(self.x, -self.y)
    
    def is_zero(self):
        """Returns True if both members of vector are within FLOAT_TOLERANCE of zero."""
        return fabs(self.x) < Vec2.FLOAT_TOLERANCE and fabs(self.y) < Vec2.FLOAT_TOLERANCE
        
    ####### operators #########
    
    def __getitem__(self, index):
        if index == 0: return self.x
        elif index == 1: return self.y
        else: raise IndexError
    
    def __len__(self):
        return 2
    
    def __eq__(self, other):
        """ == operator compares x,y values within FLOAT_TOLERANCE. """
        if isinstance(other, Vec2):
            xeq = fabs(self.x - other.x) < Vec2.FLOAT_TOLERANCE
            yeq = fabs(self.y - other.y) < Vec2.FLOAT_TOLERANCE
            return xeq and yeq
        else:
            return NotImplemented
        
    def __mul__(self, scalar):
        """ * operator implements scalar multiplication."""
        return Vec2(self.x * scalar, self.y * scalar)

    def __div__(self, scalar):
        """ / operator implements scalar division."""
        return Vec2(self.x / scalar, self.y / scalar)
    
    def __add__(self, other):
        """ + operator implements vector addition."""
        if isinstance(other, Vec2):
            return Vec2(self.x + other.x, self.y + other.y)
        else:
            return NotImplemented

    def __sub__(self, other):
        """ - operator implements vector subtraction."""
        if isinstance(other, Vec2):
            return Vec2(self.x - other.x, self.y - other.y)
        else:
            return NotImplemented

    def __neg__(self):
        """ unary - for negation."""
        return Vec2(-self.x, -self.y)