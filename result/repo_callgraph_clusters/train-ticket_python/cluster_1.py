# Cluster 1

def make_app():
    return tornado.web.Application([('/getVoucher', GetVoucherHandler)])

# Node: Application
