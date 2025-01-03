from rtc6_fastcs.device import Rtc6Eth
from rtc6_fastcs.plan_stubs import *
from bluesky.run_engine import RunEngine
import numpy as np

RE = RunEngine()
RTC = Rtc6Eth()

await RTC.connect()

def cut_cylinder_200l_100w(passes: int):
    shape = [(-100,100,False),(0,50,True),(200,50,True),(200,-50,True),(0,-50,True),(-100,-100,True)] * passes
    RE(draw_polygon(RTC, shape)

def cut_cylinder(width: int, length: int, passes: int):
    shape = [(-width,width,False),(0,(width/2),True),(length,(width/2),True),(length,(-width/2),True),(0,(-width/2),True),(-width,-width,True)] * passes
    RE(draw_polygon(RTC, shape))

def cut_omega(neck_width: int, sphere_radius: int, passes: int):
    """
    Neck is n1 to n2, tails are t1 to t2, sphere radius is r.
    n1 will be half of neck width in Y.
    arc centre (X, Y) is from a2+b2=c2, we know B and C. X = root(rsquared - (n1(Y)/2)squared)
    Will use cont of r for tail. Y = 0.75 x neck_width, X = -(a/2)
    Need to use theta = arcsin(n1(Y)/r) to get angle between horizontal and arc start. 
    360 - 2(Theta) gives arc angle to reach equiv point. 
    """
    n1 = (0, np.around((neck_width/2), 0))
    n2 = (0, np.around(-(neck_width/2), 0))

    arc_centre = (np.sqrt(sphere_radius**2 - (n1[1] / 2)**2), 0)
    t1 = (np.around(neck_width * 0.75, 0), -(np.around(0.5 * arc_centre[0], 0)))
    t2 = (np.around(-neck_width * 0.75, 0), -(np.around(0.5 * arc_centre[0], 0)))

    arc_theta = 360 - (np.degrees(np.arcsin(n1[1]/sphere_radius)) * 2)

    shape = [(t1, False), (n1, True), (arc_centre, arc_theta), (n2, True), (t1, True)] * passes
    RE(draw_polygon_with_arcs(RTC, shape))
