# Cluster 27

def test_save_screen_data_to_img():
    screen_data = (np.random.rand(100, 100, 3) * 255).astype(np.uint8)
    img_path = './temp.jpg'
    save_screen_data_to_img(screen_data, img_path=None)
    assert True

