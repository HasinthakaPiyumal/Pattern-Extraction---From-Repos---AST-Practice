# Cluster 4

# Node: getenv
# Node: loads
class GetVoucherHandler(tornado.web.RequestHandler):

    def post(self, *args, **kwargs):
        data = json.loads(self.request.body)
        orderId = data['orderId']
        type = data['type']
        queryVoucher = self.fetchVoucherByOrderId(orderId)
        if queryVoucher == None:
            orderResult = self.queryOrderByIdAndType(orderId, type)
            order = orderResult['data']
            global mysql_config
            conn = pymysql.connect(**mysql_config)
            cur = conn.cursor()
            sql = 'INSERT INTO voucher (order_id,travelDate,travelTime,contactName,trainNumber,seatClass,seatNumber,startStation,destStation,price)VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
            try:
                cur.execute(sql, (order['id'], order['travelDate'], order['travelTime'], order['contactsName'], order['trainNumber'], order['seatClass'], order['seatNumber'], order['from'], order['to'], order['price']))
                conn.commit()
            finally:
                conn.close()
            self.write(self.fetchVoucherByOrderId(orderId))
        else:
            self.write(queryVoucher)

    def queryOrderByIdAndType(self, orderId, type):
        type = int(type)
        order_url = 'http://ts-order-service:12031'
        order_other_url = 'http://ts-order-other-service:12032'
        if os.getenv('ORDER_SERVICE_URL') is not None:
            order_url = os.getenv('ORDER_SERVICE_URL')
        if os.getenv('ORDER_OTHER_SERVICE_URL') is not None:
            order_other_url = os.getenv('ORDER_OTHER_SERVICE_URL')
        if type == 0:
            url = order_other_url + '/api/v1/orderOtherService/orderOther/' + orderId
        else:
            url = order_url + '/api/v1/orderservice/order/' + orderId
        header_dict = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Trident/7.0; rv:11.0) like Gecko', 'Content-Type': 'application/json'}
        req = urllib.request.Request(url=url, headers=header_dict)
        response = urllib.request.urlopen(req)
        return json.loads(response.read())

    def fetchVoucherByOrderId(self, orderId):
        global mysql_config
        conn = pymysql.connect(**mysql_config)
        cur = conn.cursor()
        sql = 'SELECT * FROM voucher where order_id = %s'
        try:
            cur.execute(sql, orderId)
            voucher = cur.fetchone()
            conn.commit()
            if cur.rowcount < 1:
                return None
            else:
                voucherData = {}
                voucherData['voucher_id'] = voucher[0]
                voucherData['order_id'] = voucher[1]
                voucherData['travelDate'] = voucher[2]
                voucherData['contactName'] = voucher[4]
                voucherData['train_number'] = voucher[5]
                voucherData['seat_number'] = voucher[7]
                voucherData['start_station'] = voucher[8]
                voucherData['dest_station'] = voucher[9]
                voucherData['price'] = voucher[10]
                jsonStr = json.dumps(voucherData)
                print(jsonStr)
                return jsonStr
        finally:
            conn.close()

def queryOrderByIdAndType(self, orderId, type):
    type = int(type)
    order_url = 'http://ts-order-service:12031'
    order_other_url = 'http://ts-order-other-service:12032'
    if os.getenv('ORDER_SERVICE_URL') is not None:
        order_url = os.getenv('ORDER_SERVICE_URL')
    if os.getenv('ORDER_OTHER_SERVICE_URL') is not None:
        order_other_url = os.getenv('ORDER_OTHER_SERVICE_URL')
    if type == 0:
        url = order_other_url + '/api/v1/orderOtherService/orderOther/' + orderId
    else:
        url = order_url + '/api/v1/orderservice/order/' + orderId
    header_dict = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Trident/7.0; rv:11.0) like Gecko', 'Content-Type': 'application/json'}
    req = urllib.request.Request(url=url, headers=header_dict)
    response = urllib.request.urlopen(req)
    return json.loads(response.read())

# Node: int
# Node: Request
# Node: urlopen
# Node: read
def initMysqlConfig():
    global mysql_config
    host = 'ts-voucher-mysql'
    port = 3306
    user = 'root'
    password = 'Abcd1234#'
    db = 'ts-voucher-mysql'
    if os.getenv('VOUCHER_MYSQL_HOST') is not None:
        host = os.getenv('VOUCHER_MYSQL_HOST')
    if os.getenv('VOUCHER_MYSQL_PORT') is not None:
        port = int(os.getenv('VOUCHER_MYSQL_PORT'))
    if os.getenv('VOUCHER_MYSQL_USER') is not None:
        user = os.getenv('VOUCHER_MYSQL_USER')
    if os.getenv('VOUCHER_MYSQL_PASSWORD') is not None:
        password = os.getenv('VOUCHER_MYSQL_PASSWORD')
    if os.getenv('VOUCHER_MYSQL_DATABASE') is not None:
        db = os.getenv('VOUCHER_MYSQL_DATABASE')
    mysql_config = {'host': host, 'port': port, 'user': user, 'password': password, 'db': db}

