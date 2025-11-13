# Cluster 32

class ContractSkills:

    def is_auto_mode(self):
        return True

    def get_skill_name(self):
        raise NotImplementedError('You should provide the commands to execute.')

    def get_commands_to_execute(self):
        raise NotImplementedError('You should provide the commands to execute.')

    def get_commands_expected(self):
        raise NotImplementedError('You should provide the commands expected.')

    @pytest.mark.dependency()
    def test_install(self, my_clai_module):
        if self.is_auto_mode():
            execute_cmd(my_clai_module, 'clai auto')
        skill_name = self.get_skill_name()
        execute_cmd(my_clai_module, 'clai deactivate gpt3')
        command_select = f'clai activate {skill_name}'
        command_executed = execute_cmd(my_clai_module, command_select)
        assert f'\x1b[32m {skill_name} (Installed)' in command_executed, f'Skill {skill_name} not found installed. Output: {command_executed}'

    @pytest.mark.dependency(depends=['test_install'])
    def test_skill_values(self, my_clai_module, command, command_expected):
        command_executed = execute_cmd(my_clai_module, command)
        assert command_expected in command_executed, f'Expected: {command_expected}, Received: {command_executed}'

@pytest.mark.dependency()
def test_install(self, my_clai_module):
    if self.is_auto_mode():
        execute_cmd(my_clai_module, 'clai auto')
    skill_name = self.get_skill_name()
    execute_cmd(my_clai_module, 'clai deactivate gpt3')
    command_select = f'clai activate {skill_name}'
    command_executed = execute_cmd(my_clai_module, command_select)
    assert f'\x1b[32m {skill_name} (Installed)' in command_executed, f'Skill {skill_name} not found installed. Output: {command_executed}'

@pytest.mark.dependency(depends=['test_install'])
def test_skill_values(self, my_clai_module, command, command_expected):
    command_executed = execute_cmd(my_clai_module, command)
    assert command_expected in command_executed, f'Expected: {command_expected}, Received: {command_executed}'

def test_install_should_finish_correctly(my_clai):
    install_output = execute_cmd(my_clai, 'sudo ./install.sh --unassisted --demo')
    assert INSTALL_CORRECTLY_MESSAGE in install_output

def test_install_should_modify_correct_startup_files(my_clai):
    execute_cmd(my_clai, 'sudo ./install.sh --unassisted --demo')
    files = my_clai.get_files('/root')
    bashrc_output = str(files['root/.bashrc'])
    bash_profile_output = str(files['root/.bash_profile'])
    assert '# CLAI setup' in bashrc_output
    assert '# CLAI setup' in bash_profile_output
    assert '# End CLAI setup' in bashrc_output
    assert '# End CLAI setup' in bash_profile_output

def test_uninstall_should_return_the_correct_uninstall_message(my_clai):
    execute_cmd(my_clai, 'sudo ./install.sh --unassisted --demo')
    uninstall_output = execute_cmd(my_clai, 'sudo ./uninstall.sh')
    sleep(2)
    print(uninstall_output)
    assert UNINSTALL_CORRECTLY_MESSAGE in uninstall_output

def test_uninstall_should_return_bash_files_to_previous_state(my_clai):
    files = my_clai.get_files('/root')
    bashrc_original = str(files['root/.bashrc'])
    bash_profile_original = str(files['root/.bash_profile'])
    execute_cmd(my_clai, 'sudo ./install.sh --unassisted --demo')
    execute_cmd(my_clai, 'sudo ./uninstall.sh')
    sleep(2)
    files = my_clai.get_files('/root')
    bashrc_after_uninstall = str(files['root/.bashrc'])
    bash_profile_after_uninstall = str(files['root/.bash_profile'])
    assert bashrc_after_uninstall == bashrc_original
    assert bash_profile_original == bash_profile_after_uninstall

def wait_server_is_started():
    sleep(2)

