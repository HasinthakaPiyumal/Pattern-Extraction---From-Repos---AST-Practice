# Cluster 11

def on_driver_created(driver):
    print('[HOOK] on_driver_created')
    driver.maximize_window()
    driver.get('https://example.com/login')
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, 'username')))
    driver.find_element(By.NAME, 'username').send_keys('testuser')
    driver.find_element(By.NAME, 'password').send_keys('password123')
    driver.find_element(By.NAME, 'login').click()
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'welcome')))
    driver.add_cookie({'name': 'test_cookie', 'value': 'cookie_value'})
    return driver

