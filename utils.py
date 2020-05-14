import cv2
import numpy as np
from model import Rod, Hole
import math

def interpret_hierarchy(contours, hierarchy):
    hierarchy = hierarchy[0]
    rod_list = []

    for i, c in enumerate(contours):
        if cv2.contourArea(c) < 20: # Noise
            continue
        if hierarchy[i][3] == -1:   # Image contour
            continue
        if hierarchy[i][3] == 0:    # Rod contour
            # Check the eccentricity of the contour to discard round figures
            ellipse = cv2.fitEllipse(c)
            (center,axes,orientation) = ellipse
            majoraxis_length = max(axes)
            minoraxis_length = min(axes)
            eccentricity=(np.sqrt(1-(minoraxis_length/majoraxis_length)**2))
            if (eccentricity < 0.7):
                continue
            rod = Rod(c, i)
            rod_list.append(rod)
        else:                       # Hole contour
            hole = Hole(c)
            index = hierarchy[i][3]
            # Find the parent rod, None is there isn't (round object instead of a rod)
            rod = next((x for x in rod_list if x.label == index), None)
            try:
                rod.append_hole(hole)
            except: # If hole of round object
                continue
            
    # This will remove "rods" without holes
    rod_list = [rod for rod in rod_list if (len(rod.holes) != 0)]

    return rod_list

def modify_contours(img, contour):

    # Reduce vertex with approxPolyDP
    approx = cv2.approxPolyDP(contour, 2, True)

    # Find convex hull
    hull = cv2.convexHull(contour, returnPoints=False)

    # Find defect points
    defects = cv2.convexityDefects(contour, hull)
   
    l=[]
    for i in range(defects.shape[0]):
        s,e,f,d = defects[i,0]
        start = tuple(contour[s][0])
        end = tuple(contour[e][0])
        dist = d/256.0

        far = tuple(contour[f][0])
        l.append([dist,far])
        
    l = sorted(l, key=lambda x: x[0])

    start = l[-1][1]
    end = l[-2][1]
    calc = math.sqrt((start[0]-end[0])**2+(start[1]-end[1])**2)

    # Check on distance between the points (for the case we have more than 2 rods that have contact points)
    if calc>30:
        end = l[-3][1]
    
    return cv2.line(img, start, end, [255,255,255], 1)
    

# Outdated    
def draw_object_contours(img, contours, a_index, b_index, color_a, color_b):
    for i, c in enumerate(contours):
        if i in a_index:
            cv2.drawContours(img, [c], 0, (255, 0, 0), 2)
            boundRect = np.int0(cv2.boxPoints(cv2.minAreaRect(c)))
            cv2.drawContours(img,[boundRect],0,(0,191,255),1)
        if i in b_index:
            cv2.drawContours(img, [c], 0, (255, 0, 0), 2)
            boundRect = np.int0(cv2.boxPoints(cv2.minAreaRect(c)))
            cv2.drawContours(img,[boundRect],0,(0,0,255),1)


# Outdated
def interpret_hierarchy_2(hierarchy):
    hierarchy = hierarchy[0]
    n_objects = sum(1 for contour in hierarchy if contour[3] == 0)
    n_type_a = sum(1 for index, contour in enumerate(hierarchy) if sum(1 for c in hierarchy if c[3] == index and c[3] != 0 and c[3] != -1) == 1)
    n_type_b = sum(1 for index, contour in enumerate(hierarchy) if sum(1 for c in hierarchy if c[3] == index and c[3] != 0 and c[3] != -1) == 2)
    type_a_index = [index for index, contour in enumerate(hierarchy) if sum(1 for c in hierarchy if c[3] == index and c[3] != 0 and c[3] != -1) == 1]
    type_b_index = [index for index, contour in enumerate(hierarchy) if sum(1 for c in hierarchy if c[3] == index and c[3] != 0 and c[3] != -1) == 2]

    return n_objects, n_type_a, n_type_b, type_a_index, type_b_index