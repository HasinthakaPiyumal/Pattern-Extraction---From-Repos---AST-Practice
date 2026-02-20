# Cluster 5

@app.route('/api/v1/avatar', methods=['POST'])
def hello():
    data = request.get_data().decode('utf-8')
    data = json.loads(data)
    image_b64 = data.get('img')
    if image_b64 is None or len(image_b64) < 1:
        return (jsonify({'msg': 'need img in request body'}), 400)
    try:
        image_decode = base64.b64decode(image_b64)
        nparr = np.fromstring(image_decode, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        result = check(image)
    except Exception as e:
        return (jsonify({'msg': 'exception:' + str(traceback.format_exc())}), 500)
    if type(result) == dict and result.get('msg') is not None:
        return (jsonify(result), 400)
    return (result, 200)

# Node: decode
# Node: get_data
# Node: get
# Node: len
# Node: jsonify
# Node: b64decode
# Node: fromstring
# Node: imdecode
# Node: check
# Node: str
# Node: format_exc
# Node: type
# Node: route
def base64_cv2(base64_str):
    imgString = base64.b64decode(base64_str)
    nparr = np.fromstring(imgString, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    a = cv2.imwrite(path_save + 'img_face_1' + '.jpg', image)
    print(a)
    return image

# Node: imwrite
