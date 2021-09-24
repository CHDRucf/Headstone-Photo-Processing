import numpy as np
import cv2, imutils, math, glob
from tensorflow import keras

# Model loading
macro_model = None
micro_model = None

def rotate_image(image, angle):
    """
    Rotates an OpenCV 2 / NumPy image about it's centre by the given angle
    (in degrees). The returned image will be large enough to hold the entire
    new image, with a black background
    """

    # Get the image size
    # No that's not an error - NumPy stores image matricies backwards
    image_size = (image.shape[1], image.shape[0])
    image_center = tuple(np.array(image_size) / 2)

    # Convert the OpenCV 3x2 rotation matrix to 3x3
    rot_mat = np.vstack(
        [cv2.getRotationMatrix2D(image_center, angle, 1.0), [0, 0, 1]]
    )

    rot_mat_notranslate = np.matrix(rot_mat[0:2, 0:2])

    # Shorthand for below calcs
    image_w2 = image_size[0] * 0.5
    image_h2 = image_size[1] * 0.5

    # Obtain the rotated coordinates of the image corners
    rotated_coords = [
        (np.array([-image_w2,  image_h2]) * rot_mat_notranslate).A[0],
        (np.array([ image_w2,  image_h2]) * rot_mat_notranslate).A[0],
        (np.array([-image_w2, -image_h2]) * rot_mat_notranslate).A[0],
        (np.array([ image_w2, -image_h2]) * rot_mat_notranslate).A[0]
    ]

    # Find the size of the new image
    x_coords = [pt[0] for pt in rotated_coords]
    x_pos = [x for x in x_coords if x > 0]
    x_neg = [x for x in x_coords if x < 0]

    y_coords = [pt[1] for pt in rotated_coords]
    y_pos = [y for y in y_coords if y > 0]
    y_neg = [y for y in y_coords if y < 0]

    right_bound = max(x_pos)
    left_bound = min(x_neg)
    top_bound = max(y_pos)
    bot_bound = min(y_neg)

    new_w = int(abs(right_bound - left_bound))
    new_h = int(abs(top_bound - bot_bound))

    # We require a translation matrix to keep the image centred
    trans_mat = np.matrix([
        [1, 0, int(new_w * 0.5 - image_w2)],
        [0, 1, int(new_h * 0.5 - image_h2)],
        [0, 0, 1]
    ])

    # Compute the tranform for the combined rotation and translation
    affine_mat = (np.matrix(trans_mat) * np.matrix(rot_mat))[0:2, :]

    # Rotation
    result = imutils.rotate_bound(image, angle)
    return result


def largest_rotated_rect(w, h, angle):
    """
    Given a rectangle of size wxh that has been rotated by 'angle' (in
    radians), computes the width and height of the largest possible
    axis-aligned rectangle within the rotated rectangle.

    Original JS code by 'Andri' and Magnus Hoff from Stack Overflow

    Converted to Python by Aaron Snoswell
    """

    quadrant = int(math.floor(angle / (math.pi / 2))) & 3
    sign_alpha = angle if ((quadrant & 1) == 0) else math.pi - angle
    alpha = (sign_alpha % math.pi + math.pi) % math.pi

    bb_w = w * math.cos(alpha) + h * math.sin(alpha)
    bb_h = w * math.sin(alpha) + h * math.cos(alpha)

    gamma = math.atan2(bb_w, bb_w) if (w < h) else math.atan2(bb_w, bb_w)

    delta = math.pi - alpha - gamma

    length = h if (w < h) else w

    d = length * math.cos(alpha)
    a = d * math.sin(alpha) / math.sin(delta)

    y = a * math.cos(gamma)
    x = y * math.tan(gamma)

    return (
        bb_w - 2 * x,
        bb_h - 2 * y
    )

def crop_around_center(image, width, height):
    """
    Given a NumPy / OpenCV 2 image, crops it to the given width and height,
    around it's centre point
    """

    image_size = (image.shape[1], image.shape[0])
    image_center = (int(image_size[0] * 0.5), int(image_size[1] * 0.5))

    if(width > image_size[0]):
        width = image_size[0]

    if(height > image_size[1]):
        height = image_size[1]

    x1 = int(image_center[0] - width * 0.5)
    x2 = int(image_center[0] + width * 0.5)
    y1 = int(image_center[1] - height * 0.5)
    y2 = int(image_center[1] + height * 0.5)

    return image[y1:y2, x1:x2]

def preprocessing(input_image):
    temp_image = cv2.resize(input_image, (224, 224)) # resize
    temp_image = temp_image / 255 # normalization
    temp_image = np.expand_dims(temp_image, axis = 0) # Dimension Expansion

    return temp_image

def micro_rotate(image, angle, image_width, image_height):
    rotated_image = rotate_image(image, angle)
    rotated_image = crop_around_center(
                    rotated_image,
                     *largest_rotated_rect(
                        image_width,
                        image_height,
                        math.radians(angle)
                    )
                )
    return rotated_image

def find_highest_confidence(input_image, angles, image_width = None, image_height = None):
    confidence_scores = {}

    rotation_type = len(angles) == 3

    rotation = -999
    for angle in angles:
        temp_image = cv2.rotate(input_image, angle) if rotation_type else micro_rotate(input_image, angle, image_width, image_height)
        temp_image = preprocessing(temp_image)

        confidence_array = macro_model.predict(temp_image) if rotation_type else micro_model.predict(temp_image)
        prediction = np.argmax(confidence_array)

        if prediction == 0:
            rotation = angle
            break
        else:
            confidence_scores[angle] = confidence_array[0][0]

    # If the image cant classify as 0 after all possible rotations, 
    # rotate the image with the angle that has the highest confidence
    return max(confidence_scores, key = confidence_scores.get) if rotation == -999 else rotation 


def rotation_algorithm(input_image, perform_macro, perform_micro): 

    # Model Loading
    global macro_model
    global micro_model

    if macro_model is None and perform_macro:
        macro_model = keras.models.load_model('macro_model.h5')
    
    if micro_model is None and perform_micro:
        micro_model = keras.models.load_model('micro_model.h5')
    
    # Rotation angles
    macro_angles = [cv2.ROTATE_90_CLOCKWISE, cv2.ROTATE_180, cv2.ROTATE_90_COUNTERCLOCKWISE]
    micro_angles = [5, 4, 3, 2, 1, -1, -2, -3, -4, -5]

    # Image dimensions needed for rotation calculation
    image_height, image_width = input_image.shape[0:2]

    # Preprocessing of non-rotated original
    temp_image = preprocessing(input_image)

    if perform_macro:
        # Macro Prediction
        prediction = np.argmax(macro_model.predict(temp_image))
        
        # Macro Rotation of non-rotated original image
        rotation = 0
        if prediction != 0:
            rotation = find_highest_confidence(input_image, macro_angles)

            # Macro rotation
            input_image = cv2.rotate(input_image, rotation)
            
            # Preprocessing of macro rotated original
            temp_image = preprocessing(input_image)

    if perform_micro:
        # Micro Prediction
        prediction = np.argmax(micro_model.predict(temp_image))
        
        # If the image is classifed as rotated, the angle it is rotated at is found and saved
        rotation = 0
        if prediction == 1:
            rotation = find_highest_confidence(input_image, micro_angles, image_width, image_height)
            
            # Micro rotation
            input_image = micro_rotate(input_image, rotation, image_width, image_height)
    
    return input_image
