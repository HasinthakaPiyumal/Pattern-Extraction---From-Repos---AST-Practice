# Cluster 6

def check(img):
    faces = detector(img, 1)
    print('人脸数：', len(faces), '\n')
    if len(faces) < 1:
        return {'msg': 'no human face found'}
    height_max = 0
    width_sum = 0
    for k, d in enumerate(faces):
        pos_start = tuple([d.left(), d.top()])
        pos_end = tuple([d.right(), d.bottom()])
        height = d.bottom() - d.top()
        width = d.right() - d.left()
        img_blank = np.zeros((height, width, 3), np.uint8)
        for i in range(height):
            for j in range(width):
                img_blank[i][j] = img[d.top() + i][d.left() + j]
        print('Save to:', path_save + 'img_face_' + str(k + 1) + '.jpg')
        cv2.imwrite(path_save + 'img_face_' + str(k + 1) + '.jpg', img_blank)
        base64_str = cv2.imencode('.jpg', img_blank)[1].tostring()
        base64_str = base64.b64encode(base64_str)
        return base64_str

# Node: detector
# Node: enumerate
# Node: tuple
# Node: left
# Node: top
# Node: right
# Node: bottom
# Node: zeros
# Node: range
# Node: tostring
# Node: imencode
# Node: b64encode
