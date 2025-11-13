# Cluster 0

def print_logo():
    logo = '⠀⠀⠀ ⠀⡀⠀⠀⠀⢀⢀⠀⠀⠀⢀⠀⠀⠀⠀⠀\n⠀⠀⠀⠀⠈⠋⠓⡅⢸⣝⢷⡅⢰⠙⠙⠁⠀⠀⠀⠀\n⠀⢠⣢⣠⡠⣄⠀⡇⢸⢮⡳⡇⢸⠀⡠⡤⡤⡴  O C T O P I I\n⠀⠀⠀⠀⠀⡳⠀⠧⣤⡳⣝⢤⠼⠀⡯⠀⠀⠈⠀ A PII scanner\n⠀⠀⠀⠀⢀⣈⣋⣋⠮⡻⡪⢯⣋⢓⣉⡀    ______________\n⠀⠀⠀⢀⣳⡁⡡⣅⠀⡗⣝⠀⡨⣅⢁⣗⠀⠀  (c) 2023 RedHunt Labs Pvt Ltd\n⠀⠀⠀⠀⠈⠀⠸⣊⣀⡝⢸⣀⣸⠊⠀⠉⠀⠀⠀⠀by Owais Shaikh (owais.shaikh@redhuntlabs.com | me@0x4f.in)\n⠀⠀⠀⠀⠀⠀⠀⠈⠈⠀⠀⠈⠈'
    print(logo)

def help_screen():
    help = 'Usage: python octopii.py <file, local path or URL>\nNote: Only Unix-like filesystems, S3 and open directory URLs are supported.'
    print(help)

def push_data(data: str, url: str):
    headers = {'Content-type': 'application/json'}
    if 'discord' in url:
        payload = {'content': data}
    else:
        payload = {'text': data}
    try:
        req = requests.post(url, headers=headers, json=payload, timeout=7)
        req.raise_for_status()
        print('Scan results sent to webhook.')
    except requests.exceptions.RequestException as e:
        print(f"Couldn't send scan results to webhook. Reason: {e}")

