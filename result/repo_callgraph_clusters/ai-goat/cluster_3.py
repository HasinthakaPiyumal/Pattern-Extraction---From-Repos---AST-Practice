# Cluster 3

def run(inputs):
    banner()
    if inputs is not None:
        args = handle_args(inputs)
        if args.install is True:
            Installer.install()
            exit()
        if args.run == 'ctfd':
            Runner.ctfd()
            exit()
        if args.run == '1':
            Runner.challenge_1()
            exit()
        if args.run == '2':
            Runner.challenge_2()
            exit()
    handle_args(['--help'])

