import cv2
import numpy as np
from enum import Enum
from math import atan2, cos, sin, tan, sqrt, pi, radians, degrees

class ROD_TYPE(Enum):
    TYPE_A = 1
    TYPE_B = 2


class Rod(object):

    def __init__(self, contour, index):
        self.type = None
        self.label = index
        self.contour = contour
        self.bounding_rect = self.calculate_bounding_rect(contour)
        _, (self.width, self.length), _ = self.calculate_bounding_rect_components(contour)
        self.area = cv2.contourArea(contour)
        self.centroid = self.calculate_centroid(contour)
        self.axis, self.angle = self.calculate_angle_and_axis(contour)
        self.holes = []
        self.center, self.p1, self.p2, self.pca_angle = self.get_orientation(contour)
        self.width_at_centroid, self.centroid_width_p1, self.centroid_width_p2 = self.calculate_width_at_centroid()

    def append_hole(self, hole):
        self.holes.append(hole)
        self.type = ROD_TYPE.TYPE_A if len(self.holes) == 1 else ROD_TYPE.TYPE_B
        self.area -= hole.area

    def calculate_bounding_rect(self, contour):
        return np.int0(cv2.boxPoints(cv2.minAreaRect(contour)))

    def calculate_bounding_rect_components(self, contour):
        center, wh, theta = cv2.minAreaRect(contour)
        (width, length) = (wh[0], wh[1]) if wh[0] >= wh[1] else (wh[1], wh[0])
        return center, (length, width), theta

    def calculate_centroid(self, contour):
        M = cv2.moments(contour)
        cX = int(M["m10"] / M["m00"])
        cY = int(M["m01"] / M["m00"])
        return (cX, cY)

    def calculate_angle_and_axis(self, contour):
        (x, y), (MA, ma), angle = cv2.fitEllipse(contour)
        return (MA, ma), angle

    def get_orientation(self, pts):
        sz = len(pts)
        data_pts = np.empty((sz, 2), dtype=np.float64)
        for i in range(data_pts.shape[0]):
            data_pts[i,0] = pts[i,0,0]
            data_pts[i,1] = pts[i,0,1]

        # Perform PCA analysis
        mean = np.empty((0))
        mean, eigenvectors, eigenvalues = cv2.PCACompute2(data_pts, mean)

        # Store the center of the object
        cntr = (int(mean[0,0]), int(mean[0,1]))
        
        p1 = (cntr[0] + 0.02 * eigenvectors[0,0] * eigenvalues[0,0], cntr[1] + 0.02 * eigenvectors[0,1] * eigenvalues[0,0])
        p2 = (cntr[0] - 0.02 * eigenvectors[1,0] * eigenvalues[1,0], cntr[1] - 0.02 * eigenvectors[1,1] * eigenvalues[1,0])

        angle = atan2(eigenvectors[0,1], eigenvectors[0,0]) # orientation in radians
        angle = degrees(angle)
        
        return cntr, p1, p2, angle

    def drawAxis(self, img, p_, q_, colour, scale):
        p = list(p_)
        q = list(q_)
        
        angle = atan2(p[1] - q[1], p[0] - q[0]) # angle in radians
        hypotenuse = sqrt((p[1] - q[1]) * (p[1] - q[1]) + (p[0] - q[0]) * (p[0] - q[0]))
        
        # Here we lengthen the arrow by a factor of scale
        q[0] = p[0] - scale * hypotenuse * cos(angle)
        q[1] = p[1] - scale * hypotenuse * sin(angle)
        cv2.line(img, (int(p[0]), int(p[1])), (int(q[0]), int(q[1])), colour, 1, cv2.LINE_AA)
        
        # Create the arrow hooks
        p[0] = q[0] + 9 * cos(angle + pi / 4)
        p[1] = q[1] + 9 * sin(angle + pi / 4)
        cv2.line(img, (int(p[0]), int(p[1])), (int(q[0]), int(q[1])), colour, 1, cv2.LINE_AA)
        p[0] = q[0] + 9 * cos(angle - pi / 4)
        p[1] = q[1] + 9 * sin(angle - pi / 4)
        cv2.line(img, (int(p[0]), int(p[1])), (int(q[0]), int(q[1])), colour, 1, cv2.LINE_AA)

    def calculate_line_centroid_minor_axis_components(self):
        # m = (self.center[1] - point[1]) / (self.center[0] - point[0])
        m = tan(radians(self.pca_angle - 90))
        q = self.centroid[1] - m * self.centroid[0]
        return m, q   

    def calculate_width_at_centroid(self):

        # Get coefficient of line passing through centroid and parallel to minor axis
        m, q = self.calculate_line_centroid_minor_axis_components()
        
        # Get real y for each x-coord of contour pixels
        # Get difference between calculated y and real y of pixels
        delta_y = [abs(y[0][1] - new_y) for y, new_y in zip(self.contour, [m*p[0][0]+q for p in self.contour])]
        index_array = sorted(range(len(delta_y)), key = lambda sub: delta_y[sub])[:4] 
        
        # Divide image space in 4 parts to handle the possible pixels
        image = {
            'q1': [],
            'q2': [],
            'q3': [],
            'q4': []
        }

        # Classify each pixel in the space
        for i, p in enumerate(index_array):
            p = self.contour[p][0]
            if (p[0] <= self.centroid[0]):
                if (p[1] <= self.centroid[1]):
                    image['q1'].append((p, delta_y[i]))
                else:
                    image['q3'].append((p, delta_y[i]))
            else:
                if (p[1] <= self.centroid[1]):
                    image['q2'].append((p, delta_y[i]))
                else:
                    image['q4'].append((p, delta_y[i]))
        
        p_list = []

        # Keep only the pixel with the minimum difference in each part of the space
        for key in image:
            if (len(image[key]) > 0):
                p_list.append(min(image[key], key = lambda t: t[1]))
        
        # p_list now contains 2-4 elements: we need only the minimum two
        p_list = sorted(p_list, key = lambda p_list: p_list[1])[:2]
        
        p1 = (p_list[0][0][0], p_list[0][0][1])
        p2 = (p_list[1][0][0], p_list[1][0][1])

        # Get width as distance between two points
        width = sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

        return width, p1, p2

    def __str__(self):
        result = 'Rod found at {}\n\t'.format(self.centroid)
        result += 'Type : A' if self.type == ROD_TYPE.TYPE_A else 'Type : B'
        result += '\n\tLength : {:.2f}'.format(self.length)
        result += '\n\tWidth : {:.2f}'.format(self.width)
        result += '\n\tOrientation : {:.2f}'.format(self.pca_angle)
        result += '\n\tArea : {:.2f}'.format(self.area)
        result += '\n\tWidth at centroid : {:.2f}'.format(self.width_at_centroid)
        for index, hole in enumerate(self.holes):
            result += '\n\t{}'.format(hole.__str__())
        return result

    def print_on_image(self, img):
        color = (255, 0, 0) if self.type == ROD_TYPE.TYPE_A else (0, 96, 0)
        cv2.drawContours(img, [self.contour], 0, color, 1)
        cv2.drawContours(img,[self.bounding_rect],0,(0,191,255),2)
        cv2.circle(img, self.centroid, 1, (0, 0, 255),1)
        cv2.line(img, self.centroid_width_p1, self.centroid_width_p2, (255, 0, 0), 1)
        # self.drawAxis(img, self.center, self.p1, (0, 255, 0), 1)
        # self.drawAxis(img, self.center, self.p2, (255, 255, 0), 10)
        for hole in self.holes:
            hole.print_on_image(img)
        
        cv2.imshow('Rod contours', img)
        cv2.waitKey(0)


class Hole(object):

    def __init__(self, contour):
        self.contour = contour
        self.center = self.calculate_center(contour)
        self.diameter = self.calculate_diameter(contour)
        self.area = self.diameter/2*np.pi

    def calculate_center(self, contour):
        M = cv2.moments(contour)
        cX = int(M["m10"] / M["m00"])
        cY = int(M["m01"] / M["m00"])
        return (cX, cY)

    def calculate_diameter(self, contour):
        area = cv2.contourArea(contour)
        return np.sqrt(4*area/np.pi)

    def __str__(self):
        return 'Hole at {} with diameter {:.2f}'.format(self.center, self.diameter)

    def print_on_image(self, img):
        cv2.circle(img, self.center, 1, (0, 0, 255), 1)