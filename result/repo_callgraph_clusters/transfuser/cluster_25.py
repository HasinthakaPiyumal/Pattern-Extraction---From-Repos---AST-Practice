# Cluster 25

def plotPixel(coord, town_name, town_img, color):
    pix_x, pix_y = getPixel(coord, town_name)
    length = 6
    width = 3
    town_img[pix_y - length:pix_y + (length + 1), pix_x - width:pix_x + (width + 1)] = color
    town_img[pix_y - width:pix_y + (width + 1), pix_x - length:pix_x + (length + 1)] = color
    return town_img

