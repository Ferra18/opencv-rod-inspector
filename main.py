import cv2
import numpy as np
from matplotlib import pyplot as plt
from utils import interpret_hierarchy, modify_contours

file_path = 'ispezione-bielle-immagini/'
images_first_task = ['Tesi00.bmp', 'Tesi01.bmp', 'Tesi12.bmp', 'Tesi21.bmp', 'Tesi31.bmp', 'Tesi33.bmp']
images_second_task=[ 'Tesi44.bmp', 'Tesi47.bmp', 'Tesi48.bmp', 'Tesi49.bmp','Tesi50.bmp', 'Tesi51.bmp', 'Tesi90.bmp' , 'Tesi92.bmp', 'Tesi98.bmp']

images = images_first_task + images_second_task

for img in images:

    # Load image in grayscale
    current_image = cv2.imread(file_path + img, cv2.IMREAD_GRAYSCALE)

    # Median blur to remove imperfections from image (e.g. tesi21.bpm)
    current_image = cv2.medianBlur(current_image, 3)
    current_image = cv2.medianBlur(current_image, 3)
    current_image = cv2.medianBlur(current_image, 3)

    cv2.imshow(img, current_image)

    cv2.waitKey(0)

    # Image binairization
    ret, binarized_image = cv2.threshold(current_image, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)

    cv2.imshow(img + ' binairized', binarized_image)

    cv2.waitKey(0)

    # Find Contours
    contours, hierarchy = cv2.findContours(binarized_image, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)

    # Check if there are connected rods and modify the contours if yes
    possible_contacts = [c for i, c in enumerate(contours) if (cv2.contourArea(c) > 7000 and hierarchy[0][i][3] != -1)]
    while len(possible_contacts) > 0:
        modify_contours(binarized_image, possible_contacts[0])
        # Show new image with separation
        cv2.imshow(img + ' binairized - Modified contours', binarized_image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        # Search agian the contours and check again if the are connected rods
        contours, hierarchy = cv2.findContours(binarized_image, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
        possible_contacts = [c for i, c in enumerate(contours) if (cv2.contourArea(c) > 7000 and hierarchy[0][i][3] != -1)]

    # Interpret the hierarcy and and the contours to discover rods
    rods = interpret_hierarchy(contours, hierarchy)

    print('{} {} founded in {}'.format(len(rods), ('rod' if (len(rods) == 1) else 'rods'), img))
    for rod in rods:
        # Copy the original image to drow above it
        img_with_contours = cv2.cvtColor(current_image, cv2.COLOR_GRAY2RGB).copy()
        print(rod)
        rod.print_on_image(img_with_contours)

    cv2.destroyAllWindows()
