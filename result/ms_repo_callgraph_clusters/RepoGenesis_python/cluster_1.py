# Cluster 1

class RBACServiceTester:
    """Test class for RBAC Service API"""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.test_results = []
        self.passed = 0
        self.failed = 0

    def log_test(self, test_name: str, passed: bool, message: str=''):
        """Log test result"""
        status = 'PASS' if passed else 'FAIL'
        result = {'test_name': test_name, 'status': status, 'message': message}
        self.test_results.append(result)
        if passed:
            self.passed += 1
            print(f'✓ {test_name}')
        else:
            self.failed += 1
            print(f'✗ {test_name}: {message}')

    def test_create_role(self):
        """Test Case 1: Create a new role"""
        test_name = 'test_create_role'
        try:
            response = requests.post(f'{self.base_url}{API_PREFIX}/roles', json={'role_name': 'admin'}, timeout=5)
            if response.status_code != 200:
                self.log_test(test_name, False, f'Expected status 200, got {response.status_code}')
                return None
            data = response.json()
            if data.get('status') != 'success':
                self.log_test(test_name, False, f"Expected status 'success', got {data.get('status')}")
                return None
            if 'role_id' not in data or 'role_name' not in data:
                self.log_test(test_name, False, 'Missing required fields in response')
                return None
            if data['role_name'] != 'admin':
                self.log_test(test_name, False, f"Expected role_name 'admin', got {data['role_name']}")
                return None
            self.log_test(test_name, True)
            return data['role_id']
        except Exception as e:
            self.log_test(test_name, False, str(e))
            return None

    def test_create_multiple_roles(self):
        """Test Case 2: Create multiple roles"""
        test_name = 'test_create_multiple_roles'
        roles = ['editor', 'viewer', 'moderator']
        role_ids = {}
        try:
            for role_name in roles:
                response = requests.post(f'{self.base_url}{API_PREFIX}/roles', json={'role_name': role_name}, timeout=5)
                if response.status_code != 200:
                    self.log_test(test_name, False, f"Failed to create role '{role_name}'")
                    return None
                data = response.json()
                if data.get('status') != 'success':
                    self.log_test(test_name, False, f"Failed to create role '{role_name}'")
                    return None
                role_ids[role_name] = data['role_id']
            self.log_test(test_name, True)
            return role_ids
        except Exception as e:
            self.log_test(test_name, False, str(e))
            return None

    def test_assign_permissions_to_role(self, role_id: str):
        """Test Case 3: Assign permissions to a role"""
        test_name = 'test_assign_permissions_to_role'
        if not role_id:
            self.log_test(test_name, False, 'No role_id provided (dependency failed)')
            return False
        try:
            permissions = ['read', 'write', 'delete']
            response = requests.post(f'{self.base_url}{API_PREFIX}/roles/{role_id}/permissions', json={'permissions': permissions}, timeout=5)
            if response.status_code != 200:
                self.log_test(test_name, False, f'Expected status 200, got {response.status_code}')
                return False
            data = response.json()
            if data.get('status') != 'success':
                self.log_test(test_name, False, f"Expected status 'success', got {data.get('status')}")
                return False
            if data.get('role_id') != role_id:
                self.log_test(test_name, False, 'Role ID mismatch')
                return False
            returned_permissions = data.get('permissions', [])
            if not all((p in returned_permissions for p in permissions)):
                self.log_test(test_name, False, 'Not all permissions were assigned')
                return False
            self.log_test(test_name, True)
            return True
        except Exception as e:
            self.log_test(test_name, False, str(e))
            return False

    def test_assign_role_to_user(self, role_ids: List[str], user_id: str='user123'):
        """Test Case 4: Assign roles to a user"""
        test_name = 'test_assign_role_to_user'
        if not role_ids:
            self.log_test(test_name, False, 'No role_ids provided (dependency failed)')
            return False
        try:
            response = requests.post(f'{self.base_url}{API_PREFIX}/users/{user_id}/roles', json={'role_ids': role_ids}, timeout=5)
            if response.status_code != 200:
                self.log_test(test_name, False, f'Expected status 200, got {response.status_code}')
                return False
            data = response.json()
            if data.get('status') != 'success':
                self.log_test(test_name, False, f"Expected status 'success', got {data.get('status')}")
                return False
            if data.get('user_id') != user_id:
                self.log_test(test_name, False, 'User ID mismatch')
                return False
            returned_role_ids = data.get('role_ids', [])
            if not all((rid in returned_role_ids for rid in role_ids)):
                self.log_test(test_name, False, 'Not all roles were assigned')
                return False
            self.log_test(test_name, True)
            return True
        except Exception as e:
            self.log_test(test_name, False, str(e))
            return False

    def test_check_user_permissions(self, user_id: str, expected_permissions: List[str]):
        """Test Case 5: Check user permissions"""
        test_name = 'test_check_user_permissions'
        try:
            response = requests.get(f'{self.base_url}{API_PREFIX}/users/{user_id}/permissions', timeout=5)
            if response.status_code != 200:
                self.log_test(test_name, False, f'Expected status 200, got {response.status_code}')
                return False
            data = response.json()
            if data.get('status') != 'success':
                self.log_test(test_name, False, f"Expected status 'success', got {data.get('status')}")
                return False
            if data.get('user_id') != user_id:
                self.log_test(test_name, False, 'User ID mismatch')
                return False
            permissions = data.get('permissions', [])
            if not all((p in permissions for p in expected_permissions)):
                self.log_test(test_name, False, f'Missing permissions. Expected: {expected_permissions}, Got: {permissions}')
                return False
            self.log_test(test_name, True)
            return True
        except Exception as e:
            self.log_test(test_name, False, str(e))
            return False

    def test_multiple_roles_permissions(self):
        """Test Case 6: User with multiple roles gets combined permissions"""
        test_name = 'test_multiple_roles_permissions'
        try:
            role1_response = requests.post(f'{self.base_url}{API_PREFIX}/roles', json={'role_name': 'role1'}, timeout=5)
            role1_id = role1_response.json()['role_id']
            role2_response = requests.post(f'{self.base_url}{API_PREFIX}/roles', json={'role_name': 'role2'}, timeout=5)
            role2_id = role2_response.json()['role_id']
            requests.post(f'{self.base_url}{API_PREFIX}/roles/{role1_id}/permissions', json={'permissions': ['read', 'write']}, timeout=5)
            requests.post(f'{self.base_url}{API_PREFIX}/roles/{role2_id}/permissions', json={'permissions': ['delete', 'admin']}, timeout=5)
            user_id = 'multi_role_user'
            requests.post(f'{self.base_url}{API_PREFIX}/users/{user_id}/roles', json={'role_ids': [role1_id, role2_id]}, timeout=5)
            response = requests.get(f'{self.base_url}{API_PREFIX}/users/{user_id}/permissions', timeout=5)
            permissions = response.json().get('permissions', [])
            expected = ['read', 'write', 'delete', 'admin']
            if not all((p in permissions for p in expected)):
                self.log_test(test_name, False, f'Missing permissions. Expected: {expected}, Got: {permissions}')
                return False
            self.log_test(test_name, True)
            return True
        except Exception as e:
            self.log_test(test_name, False, str(e))
            return False

    def test_duplicate_role_error(self):
        """Test Case 7: Creating duplicate role should fail"""
        test_name = 'test_duplicate_role_error'
        try:
            role_name = 'duplicate_role'
            response1 = requests.post(f'{self.base_url}{API_PREFIX}/roles', json={'role_name': role_name}, timeout=5)
            if response1.status_code != 200:
                self.log_test(test_name, False, 'Failed to create first role')
                return False
            response2 = requests.post(f'{self.base_url}{API_PREFIX}/roles', json={'role_name': role_name}, timeout=5)
            if response2.status_code == 200:
                data = response2.json()
                if data.get('status') == 'success':
                    self.log_test(test_name, False, 'Duplicate role was allowed')
                    return False
            self.log_test(test_name, True)
            return True
        except Exception as e:
            self.log_test(test_name, False, str(e))
            return False

    def test_invalid_role_id(self):
        """Test Case 8: Assigning permissions to non-existent role should fail"""
        test_name = 'test_invalid_role_id'
        try:
            response = requests.post(f'{self.base_url}{API_PREFIX}/roles/nonexistent_role_id/permissions', json={'permissions': ['read']}, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    self.log_test(test_name, False, 'Non-existent role_id was accepted')
                    return False
            self.log_test(test_name, True)
            return True
        except Exception as e:
            self.log_test(test_name, False, str(e))
            return False

    def test_user_without_roles(self):
        """Test Case 9: User without roles should have no permissions"""
        test_name = 'test_user_without_roles'
        try:
            user_id = 'user_no_roles'
            response = requests.get(f'{self.base_url}{API_PREFIX}/users/{user_id}/permissions', timeout=5)
            if response.status_code != 200:
                self.log_test(test_name, False, f'Expected status 200, got {response.status_code}')
                return False
            data = response.json()
            permissions = data.get('permissions', [])
            if len(permissions) != 0:
                self.log_test(test_name, False, f'User without roles should have no permissions, got {permissions}')
                return False
            self.log_test(test_name, True)
            return True
        except Exception as e:
            self.log_test(test_name, False, str(e))
            return False

    def print_summary(self):
        """Print test summary and metrics"""
        total = self.passed + self.failed
        pass_rate = self.passed / total * 100 if total > 0 else 0
        repo_pass = 1 if self.failed == 0 else 0
        print('\n' + '=' * 60)
        print('TEST SUMMARY')
        print('=' * 60)
        print(f'Total Tests: {total}')
        print(f'Passed: {self.passed}')
        print(f'Failed: {self.failed}')
        print(f'\nMetrics:')
        print(f'  Test Case Pass Rate: {pass_rate:.2f}%')
        print(f'  Repository Pass Rate: {repo_pass}')
        print('=' * 60)
        return repo_pass

    def run_all_tests(self):
        """Run all test cases in sequence"""
        print('Starting RBAC Service Tests...')
        print(f'Testing service at: {self.base_url}\n')
        admin_role_id = self.test_create_role()
        role_ids_dict = self.test_create_multiple_roles()
        if admin_role_id:
            self.test_assign_permissions_to_role(admin_role_id)
        if role_ids_dict and 'editor' in role_ids_dict:
            editor_role_id = role_ids_dict['editor']
            requests.post(f'{self.base_url}{API_PREFIX}/roles/{editor_role_id}/permissions', json={'permissions': ['read', 'write']}, timeout=5)
            self.test_assign_role_to_user([editor_role_id], 'test_user_1')
            self.test_check_user_permissions('test_user_1', ['read', 'write'])
        self.test_multiple_roles_permissions()
        self.test_duplicate_role_error()
        self.test_invalid_role_id()
        self.test_user_without_roles()
        repo_pass = self.print_summary()
        return repo_pass

def run_all_tests(self):
    """Run all test cases in sequence"""
    print('Starting RBAC Service Tests...')
    print(f'Testing service at: {self.base_url}\n')
    admin_role_id = self.test_create_role()
    role_ids_dict = self.test_create_multiple_roles()
    if admin_role_id:
        self.test_assign_permissions_to_role(admin_role_id)
    if role_ids_dict and 'editor' in role_ids_dict:
        editor_role_id = role_ids_dict['editor']
        requests.post(f'{self.base_url}{API_PREFIX}/roles/{editor_role_id}/permissions', json={'permissions': ['read', 'write']}, timeout=5)
        self.test_assign_role_to_user([editor_role_id], 'test_user_1')
        self.test_check_user_permissions('test_user_1', ['read', 'write'])
    self.test_multiple_roles_permissions()
    self.test_duplicate_role_error()
    self.test_invalid_role_id()
    self.test_user_without_roles()
    repo_pass = self.print_summary()
    return repo_pass

# Node: test_create_role
# Node: test_create_multiple_roles
# Node: test_assign_permissions_to_role
# Node: test_assign_role_to_user
# Node: test_check_user_permissions
# Node: test_multiple_roles_permissions
# Node: test_duplicate_role_error
# Node: test_invalid_role_id
# Node: test_user_without_roles
# Node: print_summary
def main():
    """Main test runner"""
    try:
        response = requests.get(f'{BASE_URL}/', timeout=2)
        print(f'Service is reachable at {BASE_URL}\n')
    except requests.exceptions.RequestException as e:
        print(f'ERROR: Cannot reach service at {BASE_URL}')
        print(f'Please ensure the RBAC service is running on port 8080')
        print(f'Error: {e}')
        sys.exit(1)
    tester = RBACServiceTester(BASE_URL)
    repo_pass = tester.run_all_tests()
    sys.exit(0 if repo_pass == 1 else 1)

# Node: exit
# Node: RBACServiceTester
# Node: run_all_tests
# Node: check_dependencies
@pytest.fixture(scope='session', autouse=True)
def check_service_running():
    """
    Check if the mail service is running before running tests.
    This fixture runs once per test session.
    """
    try:
        response = requests.get(f'{BASE_URL}/health', timeout=5)
        if response.status_code not in [200, 404]:
            pytest.exit('Mail service is not responding correctly. Please start the service.')
    except requests.exceptions.RequestException:
        pytest.exit('Mail service is not running. Please start the service on port 8080 before running tests.')

def main():
    """Main test runner"""
    print('=' * 70)
    print('MULTILINGUAL API TEST SUITE')
    print('=' * 70)
    print(f'Target URL: {BASE_URL}')
    print(f'Python: {sys.version}')
    print()
    if not wait_for_service():
        print('\n✗ ERROR: Service is not available!')
        print(f'Please ensure the service is running at {BASE_URL}')
        print('Start the service with: python app.py')
        sys.exit(1)
    test_files = ['test_translate.py', 'test_timezone.py', 'test_localize.py', 'test_languages.py']
    print(f'\nFound {len(test_files)} test files')
    results = []
    for test_file in test_files:
        result = run_test_file(test_file)
        results.append(result)
    metrics = calculate_metrics(results)
    print_summary(results, metrics)
    if metrics['repo_pass_rate'] == 100:
        print('\n✓ All tests passed!')
        sys.exit(0)
    else:
        print(f'\n✗ Some tests failed. Repository pass rate: {metrics['repo_pass_rate']:.2f}%')
        sys.exit(1)

# Node: wait_for_service
# Node: run_test_file
# Node: calculate_metrics
@pytest.fixture(scope='session', autouse=True)
def check_server_availability():
    max_retries = 3
    retry_delay = 1
    for attempt in range(max_retries):
        try:
            response = requests.get(BASE_URL, timeout=2)
            print(f'\nServer Connected: {BASE_URL}')
            return
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                print(f'\nTrying to connect to server ({attempt + 1}/{max_retries})...')
                time.sleep(retry_delay)
            else:
                pytest.exit(f'Failed to connect to server {BASE_URL}.Please ensure the service is started and listening on port 8080.\nError: {str(e)}')

def main():
    """Main function to handle command line arguments."""
    parser = argparse.ArgumentParser(description='GameBackend API Test Runner')
    parser.add_argument('command', choices=['all', 'room', 'leaderboard', 'game-state', 'smoke', 'integration', 'unit', 'coverage', 'parallel', 'lint', 'format'], help='Test command to run')
    parser.add_argument('--test', help='Run specific test file or function')
    parser.add_argument('--check-deps', action='store_true', help='Check dependencies before running tests')
    args = parser.parse_args()
    if args.check_deps:
        if not check_dependencies():
            sys.exit(1)
    tests_dir = Path(__file__).parent
    os.chdir(tests_dir)
    success = True
    if args.command == 'all':
        success = run_all_tests()
    elif args.command == 'room':
        success = run_room_matching_tests()
    elif args.command == 'leaderboard':
        success = run_leaderboard_tests()
    elif args.command == 'game-state':
        success = run_game_state_tests()
    elif args.command == 'smoke':
        success = run_smoke_tests()
    elif args.command == 'integration':
        success = run_integration_tests()
    elif args.command == 'unit':
        success = run_unit_tests()
    elif args.command == 'coverage':
        success = run_with_coverage()
    elif args.command == 'parallel':
        success = run_parallel_tests()
    elif args.command == 'lint':
        success = lint_code()
    elif args.command == 'format':
        success = format_code()
    if args.test:
        success = run_specific_test(args.test)
    if success:
        print(f'\n{'=' * 60}')
        print('🎉 All operations completed successfully!')
        print(f'{'=' * 60}')
        sys.exit(0)
    else:
        print(f'\n{'=' * 60}')
        print('💥 Some operations failed!')
        print(f'{'=' * 60}')
        sys.exit(1)

# Node: run_room_matching_tests
# Node: run_leaderboard_tests
# Node: run_game_state_tests
# Node: run_smoke_tests
# Node: run_integration_tests
# Node: run_unit_tests
# Node: run_with_coverage
# Node: run_parallel_tests
# Node: lint_code
# Node: format_code
# Node: run_specific_test
