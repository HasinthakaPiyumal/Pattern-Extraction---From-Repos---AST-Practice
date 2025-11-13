# Cluster 9

def scan_image_for_people(image):
    image = numpy.array(image)
    cascade_values_file = 'face_cascade.xml'
    cascade_values = cv2.CascadeClassifier(cascade_values_file)
    faces = cascade_values.detectMultiScale(image, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30), flags=cv2.CASCADE_SCALE_IMAGE)
    return len(faces)

