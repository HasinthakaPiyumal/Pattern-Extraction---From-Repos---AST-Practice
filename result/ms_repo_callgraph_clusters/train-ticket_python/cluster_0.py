# Cluster 0

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

# Node: fetchVoucherByOrderId
# Node: queryOrderByIdAndType
# Node: connect
# Node: cursor
# Node: execute
# Node: commit
# Node: close
# Node: write
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

# Node: fetchone
# Node: dumps
def initDatabase():
    print(mysql_config)
    connect = pymysql.connect(**mysql_config)
    cur = connect.cursor()
    sql = '\n    CREATE TABLE if not exists voucher (\n    voucher_id INT NOT NULL AUTO_INCREMENT,\n    order_id VARCHAR(1024) NOT NULL,\n    travelDate VARCHAR(1024) NOT NULL,\n    travelTime VARCHAR(1024) NOT NULL,\n    contactName VARCHAR(1024) NOT NULL,\n    trainNumber VARCHAR(1024) NOT NULL,\n    seatClass INT NOT NULL,\n    seatNumber VARCHAR(1024) NOT NULL,\n    startStation VARCHAR(1024) NOT NULL,\n    destStation VARCHAR(1024) NOT NULL,\n    price FLOAT NOT NULL,\n    PRIMARY KEY (voucher_id));'
    try:
        cur.execute(sql)
        connect.commit()
    finally:
        connect.close()

