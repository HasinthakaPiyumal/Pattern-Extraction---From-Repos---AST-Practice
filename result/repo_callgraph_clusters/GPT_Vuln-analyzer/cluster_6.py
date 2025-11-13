# Cluster 6

def main() -> None:
    asset_codes.run_docker_container()
    args = parse_arguments()
    api_keys = get_api_keys()
    asset_codes.clearscr()
    cowsay.cow('GVA Usage in progress...')
    target = args.target or '127.0.0.1'
    try:
        if args.rich_menu == 'help':
            asset_codes.help_menu()
        elif args.menu is True:
            Menus(lkey='', threads=4, output_loc='', lendpoint='', keyset='', t='', profile_num='', ai_set='', akey_set='', bkey_set='', ai_set_args='', llamakey='', llamaendpoint='', password_hash='', salt='', wordlist_loc='', algorithm='', parallel_proc=True, complexity=True, min_length=1, max_length=6, char_set='abcdefghijklmnopqrstuvwxyz0123456789', bforce=True)
        else:
            additional_params = {'profile': args.profile, 'list_loc': args.sub_list, 'output_loc': args.output, 'password_hash': args.password_hash, 'salt': args.salt, 'parallel': args.parallel, 'complexity': args.complexity, 'brute_force': args.brute_force, 'min_length': args.min_length, 'max_lenght': args.max_length, 'character_set': args.character_set, 'algorithm': args.algorithm, 'wordlist_file': args.wordlist_file}
            handle_attack(args.attack, target, args.ai, api_keys, additional_params)
    except KeyboardInterrupt:
        console.print_exception('Bye')
        quit()

