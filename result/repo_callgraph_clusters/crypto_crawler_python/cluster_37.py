# Cluster 37

def test_screens():
    screen_name = 'WTF'
    window_list = ['1', '2', '3']
    create_screen(screen_name)
    for w in window_list:
        create_screen_window(screen_name, w)
    run_command_in_screen(screen_name, '1', 'ls -la')
    run_command_in_screen(screen_name, '2', 'netstat -tunapl')
    run_command_in_screen(screen_name, '3', 'htop')

# Node: create_screen
# Node: create_screen_window
# Node: run_command_in_screen
def deploy_telegram_notifier(screen_name=TELEGRAM_NOTIFIER_DEPLOY_UNIT.screen_name, should_create_screen=False):
    print_to_console('Initialization of telegram notification service...', LOG_ALL_ERRORS)
    if should_create_screen:
        create_screen(screen_name)
    create_screen_window(screen_name, TELEGRAM_NOTIFIER_DEPLOY_UNIT.window_name)
    run_command_in_screen(screen_name, TELEGRAM_NOTIFIER_DEPLOY_UNIT.window_name, TELEGRAM_NOTIFIER_DEPLOY_UNIT.command)

def deploy_order_storing(screen_name=ORDER_SAVING_DEPLOY_UNIT.screen_name, should_create_screen=False):
    print_to_console('Initialization of order saving service...', LOG_ALL_ERRORS)
    if should_create_screen:
        create_screen(screen_name)
    create_screen_window(screen_name, ORDER_SAVING_DEPLOY_UNIT.window_name)
    run_command_in_screen(screen_name, ORDER_SAVING_DEPLOY_UNIT.window_name, ORDER_SAVING_DEPLOY_UNIT.command)

def deploy_expired_order_processing(screen_name=EXPIRED_ORDER_PROCESSING_DEPLOY_UNIT.screen_name, should_create_screen=False):
    print_to_console('Initialization of expired order processing service...', LOG_ALL_ERRORS)
    if should_create_screen:
        create_screen(screen_name)
    create_screen_window(screen_name, EXPIRED_ORDER_PROCESSING_DEPLOY_UNIT.window_name)
    run_command_in_screen(screen_name, EXPIRED_ORDER_PROCESSING_DEPLOY_UNIT.window_name, EXPIRED_ORDER_PROCESSING_DEPLOY_UNIT.command)

def deploy_failed_order_processing(screen_name=FAILED_ORDER_PROCESSING_DEPLOY_UNIT.screen_name, should_create_screen=False):
    print_to_console('Initialization of failed order processing service...', LOG_ALL_ERRORS)
    if should_create_screen:
        create_screen(screen_name)
    create_screen_window(screen_name, FAILED_ORDER_PROCESSING_DEPLOY_UNIT.window_name)
    run_command_in_screen(screen_name, FAILED_ORDER_PROCESSING_DEPLOY_UNIT.window_name, FAILED_ORDER_PROCESSING_DEPLOY_UNIT.command)

def deploy_bot_trades_retrieval(screen_name=BOT_TRADE_SAVING_DEPLOY_UNIT.screen_name, should_create_screen=False):
    print_to_console('Initialization of order saving service...', LOG_ALL_ERRORS)
    if should_create_screen:
        create_screen(screen_name)
    create_screen_window(screen_name, BOT_TRADE_SAVING_DEPLOY_UNIT.window_name)
    run_command_in_screen(screen_name, BOT_TRADE_SAVING_DEPLOY_UNIT.window_name, BOT_TRADE_SAVING_DEPLOY_UNIT.command)

def deploy_process_in_screen(screen_name, deploy_unit, should_create_window=True):
    """
        Will create new named window in EXISTING screen `screen_name`
        and run there command according to deploy unit

    :param screen_name:
    :param deploy_unit: type: DeployUnit
    :param should_create_window:
    :return:
    """
    msg = 'Executing {smd} in screen_name = {s_n}. New window {wn} will be created: {tf}'.format(smd=deploy_unit.command, s_n=screen_name, wn=deploy_unit.window_name, tf=should_create_window)
    print_to_console(msg, LOG_ALL_ERRORS)
    if should_create_window:
        create_screen_window(screen_name, deploy_unit.window_name)
    run_command_in_screen(screen_name, deploy_unit.window_name, deploy_unit.command)

