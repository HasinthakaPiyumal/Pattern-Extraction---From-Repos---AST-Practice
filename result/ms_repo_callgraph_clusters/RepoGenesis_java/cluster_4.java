// Cluster 4

// Node: post
// Node: body
// Node: delete
// Node: given
// Node: contentType
// Node: when
// Node: then
// Node: statusCode
// Node: extract
// Node: DisplayName
import io.restassured.RestAssured;
import io.restassured.http.ContentType;
import io.restassured.response.Response;
import org.junit.jupiter.api.*;
import static io.restassured.RestAssured.*;
import static org.hamcrest.Matchers.*;

@TestMethodOrder(MethodOrderer.OrderAnnotation.class)
public class UserDeletionTest {

        private static io.javalin.Javalin app;
        private static String BASE_URL;
        private static final String REGISTER_ENDPOINT = "/api/users/register";
        private static final String LOGIN_ENDPOINT = "/api/users/login";
        private static final String DELETE_USER_ENDPOINT = "/api/users/{userId}";
        private static final String PROFILE_ENDPOINT = "/api/users/profile";

        private static String sessionToken;
        private static String userId;
        private static String username = "deletetest001";

        @BeforeAll
        public static void setup() {
                app = com.example.auth.Main.start(0);
                int port = app.port();
                BASE_URL = "http://localhost:" + port;
                RestAssured.baseURI = BASE_URL;
        }

        @BeforeEach
        public void setupEachTest() {
                // Register a new test user for each test with shorter unique identifier
                long timestamp = System.currentTimeMillis() % 10000; // Last 4 digits
                String registerBody = String.format("""
                                {
                                    "username": "%s%d",
                                    "email": "del%d@example.com",
                                    "password": "testpass123"
                                }
                                """, username, timestamp, timestamp);

                Response registerResponse = given()
                                .contentType(ContentType.JSON)
                                .body(registerBody)
                                .when()
                                .post(REGISTER_ENDPOINT)
                                .then()
                                .statusCode(201)
                                .extract().response();

                userId = registerResponse.jsonPath().getString("userId");

                // Login to get session token using the exact same username
                // Extract correct username from the register body we just sent
                String actualUsername = String.format("%s%d", username, timestamp);

                String loginBody = String.format("""
                                {
                                    "username": "%s",
                                    "password": "testpass123"
                                }
                                """, actualUsername);

                Response loginResponse = given()
                                .contentType(ContentType.JSON)
                                .body(loginBody)
                                .when()
                                .post(LOGIN_ENDPOINT)
                                .then()
                                .statusCode(200)
                                .extract().response();

                sessionToken = loginResponse.jsonPath().getString("sessionToken");
        }

        @Test
        @Order(1)
        @DisplayName("Test successful user deletion")
        public void testSuccessfulUserDeletion() {
                given()
                                .header("Authorization", "Bearer " + sessionToken)
                                .pathParam("userId", userId)
                                .when()
                                .delete(DELETE_USER_ENDPOINT)
                                .then()
                                .statusCode(200)
                                .body("success", equalTo(true))
                                .body("message", equalTo("User deleted successfully"));
        }

        @Test
        @Order(2)
        @DisplayName("Test user deletion without authorization")
        public void testDeleteUserWithoutAuth() {
                given()
                                .pathParam("userId", userId)
                                .when()
                                .delete(DELETE_USER_ENDPOINT)
                                .then()
                                .statusCode(401)
                                .body("success", equalTo(false))
                                .body("message", containsStringIgnoringCase("unauthorized"));
        }

        @Test
        @Order(3)
        @DisplayName("Test user deletion with invalid user ID")
        public void testDeleteUserInvalidId() {
                String invalidUserId = "00000000-0000-0000-0000-000000000000";

                given()
                                .header("Authorization", "Bearer " + sessionToken)
                                .pathParam("userId", invalidUserId)
                                .when()
                                .delete(DELETE_USER_ENDPOINT)
                                .then()
                                .statusCode(401)
                                .body("success", equalTo(false))
                                .body("message", containsStringIgnoringCase("unauthorized"));
        }

        @Test
        @Order(4)
        @DisplayName("Test cannot access profile after deletion")
        public void testProfileAccessAfterDeletion() {
                // Delete the user
                given()
                                .header("Authorization", "Bearer " + sessionToken)
                                .pathParam("userId", userId)
                                .when()
                                .delete(DELETE_USER_ENDPOINT)
                                .then()
                                .statusCode(200);

                // Try to access profile
                given()
                                .header("Authorization", "Bearer " + sessionToken)
                                .when()
                                .get(PROFILE_ENDPOINT)
                                .then()
                                .statusCode(401)
                                .body("success", equalTo(false));
        }

        @Test
        @Order(5)
        @DisplayName("Test cannot login after deletion")
        public void testLoginAfterDeletion() {
                // Get username before deletion
                Response profileResponse = given()
                                .header("Authorization", "Bearer " + sessionToken)
                                .when()
                                .get(PROFILE_ENDPOINT)
                                .then()
                                .statusCode(200)
                                .extract().response();

                String deletedUsername = profileResponse.jsonPath().getString("user.username");

                // Delete the user
                given()
                                .header("Authorization", "Bearer " + sessionToken)
                                .pathParam("userId", userId)
                                .when()
                                .delete(DELETE_USER_ENDPOINT)
                                .then()
                                .statusCode(200);

                // Try to login
                String loginBody = String.format("""
                                {
                                    "username": "%s",
                                    "password": "testpass123"
                                }
                                """, deletedUsername);

                given()
                                .contentType(ContentType.JSON)
                                .body(loginBody)
                                .when()
                                .post(LOGIN_ENDPOINT)
                                .then()
                                .statusCode(401)
                                .body("success", equalTo(false))
                                .body("message", equalTo("Invalid credentials"));
        }

        @Test
        @Order(6)
        @DisplayName("Test delete already deleted user")
        public void testDeleteAlreadyDeletedUser() {
                // Delete the user first time
                given()
                                .header("Authorization", "Bearer " + sessionToken)
                                .pathParam("userId", userId)
                                .when()
                                .delete(DELETE_USER_ENDPOINT)
                                .then()
                                .statusCode(200);

                // Try to delete again
                given()
                                .header("Authorization", "Bearer " + sessionToken)
                                .pathParam("userId", userId)
                                .when()
                                .delete(DELETE_USER_ENDPOINT)
                                .then()
                                .statusCode(anyOf(equalTo(401), equalTo(404)))
                                .body("success", equalTo(false));
        }

        @AfterAll
        public static void tearDown() {
                app.stop();
        }
}


// Node: testSuccessfulUserDeletion
// Node: pathParam
// Node: equalTo
// Node: testDeleteUserWithoutAuth
// Node: containsStringIgnoringCase
// Node: testDeleteUserInvalidId
// Node: testProfileAccessAfterDeletion
// Node: testDeleteAlreadyDeletedUser
// Node: anyOf
import io.restassured.RestAssured;
import io.restassured.http.ContentType;
import io.restassured.response.Response;
import org.junit.jupiter.api.*;
import static io.restassured.RestAssured.*;
import static org.hamcrest.Matchers.*;

@TestMethodOrder(MethodOrderer.OrderAnnotation.class)
public class SessionManagementTest {

    private static io.javalin.Javalin app;
    private static String BASE_URL;
    private static final String REGISTER_ENDPOINT = "/api/users/register";
    private static final String LOGIN_ENDPOINT = "/api/users/login";
    private static final String LOGOUT_ENDPOINT = "/api/users/logout";
    private static final String VALIDATE_SESSION_ENDPOINT = "/api/users/validate-session";
    private static final String PROFILE_ENDPOINT = "/api/users/profile";
    
    private static String sessionToken;
    private static String userId;
    private static String username = "sessiontest001";

    @BeforeAll
    public static void setup() {
        app = com.example.auth.Main.start(0);
        int port = app.port();
        BASE_URL = "http://localhost:" + port;
        RestAssured.baseURI = BASE_URL;
        
        // Register a test user
        String registerBody = String.format("""
            {
                "username": "%s",
                "email": "sessiontest001@example.com",
                "password": "testpass123"
            }
            """, username);

        Response registerResponse = given()
            .contentType(ContentType.JSON)
            .body(registerBody)
        .when()
            .post(REGISTER_ENDPOINT)
        .then()
            .statusCode(201)
            .extract().response();

        userId = registerResponse.jsonPath().getString("userId");

        // Login to get session token
        String loginBody = String.format("""
            {
                "username": "%s",
                "password": "testpass123"
            }
            """, username);

        Response loginResponse = given()
            .contentType(ContentType.JSON)
            .body(loginBody)
        .when()
            .post(LOGIN_ENDPOINT)
        .then()
            .statusCode(200)
            .extract().response();

        sessionToken = loginResponse.jsonPath().getString("sessionToken");
    }

    @Test
    @Order(1)
    @DisplayName("Test validate session with valid token")
    public void testValidateSessionSuccess() {
        given()
            .header("Authorization", "Bearer " + sessionToken)
        .when()
            .get(VALIDATE_SESSION_ENDPOINT)
        .then()
            .statusCode(200)
            .body("success", equalTo(true))
            .body("valid", equalTo(true))
            .body("userId", equalTo(userId));
    }

    @Test
    @Order(2)
    @DisplayName("Test validate session without authorization header")
    public void testValidateSessionWithoutAuth() {
        given()
        .when()
            .get(VALIDATE_SESSION_ENDPOINT)
        .then()
            .statusCode(401)
            .body("success", equalTo(false))
            .body("valid", equalTo(false))
            .body("message", equalTo("Invalid or expired session"));
    }

    @Test
    @Order(3)
    @DisplayName("Test validate session with invalid token")
    public void testValidateSessionInvalidToken() {
        given()
            .header("Authorization", "Bearer invalid-token-xyz")
        .when()
            .get(VALIDATE_SESSION_ENDPOINT)
        .then()
            .statusCode(401)
            .body("success", equalTo(false))
            .body("valid", equalTo(false))
            .body("message", equalTo("Invalid or expired session"));
    }

    @Test
    @Order(4)
    @DisplayName("Test logout with valid session")
    public void testLogoutSuccess() {
        given()
            .header("Authorization", "Bearer " + sessionToken)
        .when()
            .post(LOGOUT_ENDPOINT)
        .then()
            .statusCode(200)
            .body("success", equalTo(true))
            .body("message", equalTo("Logout successful"));
    }

    @Test
    @Order(5)
    @DisplayName("Test session is invalid after logout")
    public void testSessionInvalidAfterLogout() {
        given()
            .header("Authorization", "Bearer " + sessionToken)
        .when()
            .get(VALIDATE_SESSION_ENDPOINT)
        .then()
            .statusCode(401)
            .body("success", equalTo(false))
            .body("valid", equalTo(false));
    }

    @Test
    @Order(6)
    @DisplayName("Test cannot access protected endpoint after logout")
    public void testProtectedEndpointAfterLogout() {
        given()
            .header("Authorization", "Bearer " + sessionToken)
        .when()
            .get(PROFILE_ENDPOINT)
        .then()
            .statusCode(401)
            .body("success", equalTo(false))
            .body("message", equalTo("Unauthorized"));
    }

    @Test
    @Order(7)
    @DisplayName("Test logout without authorization")
    public void testLogoutWithoutAuth() {
        given()
        .when()
            .post(LOGOUT_ENDPOINT)
        .then()
            .statusCode(401)
            .body("success", equalTo(false));
    }

    @Test
    @Order(8)
    @DisplayName("Test new login creates new valid session after logout")
    public void testNewLoginAfterLogout() {
        String loginBody = String.format("""
            {
                "username": "%s",
                "password": "testpass123"
            }
            """, username);

        Response loginResponse = given()
            .contentType(ContentType.JSON)
            .body(loginBody)
        .when()
            .post(LOGIN_ENDPOINT)
        .then()
            .statusCode(200)
            .body("success", equalTo(true))
            .extract().response();

        String newSessionToken = loginResponse.jsonPath().getString("sessionToken");

        // Verify new session is valid
        given()
            .header("Authorization", "Bearer " + newSessionToken)
        .when()
            .get(VALIDATE_SESSION_ENDPOINT)
        .then()
            .statusCode(200)
            .body("success", equalTo(true))
            .body("valid", equalTo(true));

        // Verify old session is still invalid
        given()
            .header("Authorization", "Bearer " + sessionToken)
        .when()
            .get(VALIDATE_SESSION_ENDPOINT)
        .then()
            .statusCode(401)
            .body("valid", equalTo(false));
    }

    @AfterAll
    public static void tearDown() {
        app.stop();
    }
}


// Node: testValidateSessionSuccess
// Node: testValidateSessionWithoutAuth
// Node: testValidateSessionInvalidToken
// Node: testLogoutSuccess
// Node: testSessionInvalidAfterLogout
// Node: testProtectedEndpointAfterLogout
// Node: testLogoutWithoutAuth
import io.restassured.RestAssured;
import io.restassured.http.ContentType;
import io.restassured.response.Response;
import org.junit.jupiter.api.*;
import static io.restassured.RestAssured.*;
import static org.hamcrest.Matchers.*;

@TestMethodOrder(MethodOrderer.OrderAnnotation.class)
public class UserLoginTest {

    private static io.javalin.Javalin app;
    private static String BASE_URL;
    private static final String REGISTER_ENDPOINT = "/api/users/register";
    private static final String LOGIN_ENDPOINT = "/api/users/login";
    private static String testUserId;

    @BeforeAll
    public static void setup() {
        app = com.example.auth.Main.start(0);
        int port = app.port();
        BASE_URL = "http://localhost:" + port;
        RestAssured.baseURI = BASE_URL;

        // Register a test user for login tests
        String registerBody = """
                {
                    "username": "logintest001",
                    "email": "logintest001@example.com",
                    "password": "testpass123"
                }
                """;

        Response response = given()
                .contentType(ContentType.JSON)
                .body(registerBody)
                .when()
                .post(REGISTER_ENDPOINT)
                .then()
                .statusCode(201)
                .extract().response();

        testUserId = response.jsonPath().getString("userId");
    }

    @Test
    @Order(1)
    @DisplayName("Test successful login with valid credentials")
    public void testSuccessfulLogin() {
        String requestBody = """
                {
                    "username": "logintest001",
                    "password": "testpass123"
                }
                """;

        given()
                .contentType(ContentType.JSON)
                .body(requestBody)
                .when()
                .post(LOGIN_ENDPOINT)
                .then()
                .statusCode(200)
                .body("success", equalTo(true))
                .body("message", equalTo("Login successful"))
                .body("sessionToken", notNullValue())
                .body("userId", equalTo(testUserId));
    }

    @Test
    @Order(2)
    @DisplayName("Test login with incorrect password")
    public void testIncorrectPassword() {
        String requestBody = """
                {
                    "username": "logintest001",
                    "password": "wrongpassword"
                }
                """;

        given()
                .contentType(ContentType.JSON)
                .body(requestBody)
                .when()
                .post(LOGIN_ENDPOINT)
                .then()
                .statusCode(401)
                .body("success", equalTo(false))
                .body("message", equalTo("Invalid credentials"));
    }

    @Test
    @Order(3)
    @DisplayName("Test login with non-existent username")
    public void testNonExistentUsername() {
        String requestBody = """
                {
                    "username": "nonexistentuser",
                    "password": "testpass123"
                }
                """;

        given()
                .contentType(ContentType.JSON)
                .body(requestBody)
                .when()
                .post(LOGIN_ENDPOINT)
                .then()
                .statusCode(401)
                .body("success", equalTo(false))
                .body("message", equalTo("Invalid credentials"));
    }

    @Test
    @Order(4)
    @DisplayName("Test login with missing username")
    public void testMissingUsername() {
        String requestBody = """
                {
                    "password": "testpass123"
                }
                """;

        given()
                .contentType(ContentType.JSON)
                .body(requestBody)
                .when()
                .post(LOGIN_ENDPOINT)
                .then()
                .statusCode(400)
                .body("success", equalTo(false))
                .body("message", notNullValue());
    }

    @Test
    @Order(5)
    @DisplayName("Test login with missing password")
    public void testMissingPassword() {
        String requestBody = """
                {
                    "username": "logintest001"
                }
                """;

        given()
                .contentType(ContentType.JSON)
                .body(requestBody)
                .when()
                .post(LOGIN_ENDPOINT)
                .then()
                .statusCode(400)
                .body("success", equalTo(false))
                .body("message", notNullValue());
    }

    @Test
    @Order(6)
    @DisplayName("Test login with empty username")
    public void testEmptyUsername() {
        String requestBody = """
                {
                    "username": "",
                    "password": "testpass123"
                }
                """;

        given()
                .contentType(ContentType.JSON)
                .body(requestBody)
                .when()
                .post(LOGIN_ENDPOINT)
                .then()
                .statusCode(400)
                .body("success", equalTo(false));
    }

    @Test
    @Order(7)
    @DisplayName("Test login with empty password")
    public void testEmptyPassword() {
        String requestBody = """
                {
                    "username": "logintest001",
                    "password": ""
                }
                """;

        given()
                .contentType(ContentType.JSON)
                .body(requestBody)
                .when()
                .post(LOGIN_ENDPOINT)
                .then()
                .statusCode(400)
                .body("success", equalTo(false));
    }

    @Test
    @Order(8)
    @DisplayName("Test multiple successful logins generate different session tokens")
    public void testMultipleLoginsGenerateDifferentTokens() {
        String requestBody = """
                {
                    "username": "logintest001",
                    "password": "testpass123"
                }
                """;

        String token1 = given()
                .contentType(ContentType.JSON)
                .body(requestBody)
                .when()
                .post(LOGIN_ENDPOINT)
                .then()
                .statusCode(200)
                .extract().jsonPath().getString("sessionToken");

        String token2 = given()
                .contentType(ContentType.JSON)
                .body(requestBody)
                .when()
                .post(LOGIN_ENDPOINT)
                .then()
                .statusCode(200)
                .extract().jsonPath().getString("sessionToken");

        Assertions.assertNotEquals(token1, token2, "Session tokens should be unique for each login");
    }

    @AfterAll
    public static void tearDown() {
        app.stop();
    }
}


// Node: testSuccessfulLogin
// Node: notNullValue
// Node: testIncorrectPassword
// Node: testNonExistentUsername
// Node: testMissingUsername
// Node: testMissingPassword
// Node: testEmptyUsername
// Node: testEmptyPassword
import io.restassured.RestAssured;
import io.restassured.http.ContentType;
import io.restassured.response.Response;
import org.junit.jupiter.api.*;
import static io.restassured.RestAssured.*;
import static org.hamcrest.Matchers.*;

@TestMethodOrder(MethodOrderer.OrderAnnotation.class)
public class PasswordChangeTest {

    private static io.javalin.Javalin app;
    private static String BASE_URL;
    private static final String REGISTER_ENDPOINT = "/api/users/register";
    private static final String LOGIN_ENDPOINT = "/api/users/login";
    private static final String CHANGE_PASSWORD_ENDPOINT = "/api/users/change-password";
    
    private static String sessionToken;
    private static String username = "passwordtest001";
    private static String originalPassword = "originalpass123";

    @BeforeAll
    public static void setup() {
        app = com.example.auth.Main.start(0);
        int port = app.port();
        BASE_URL = "http://localhost:" + port;
        RestAssured.baseURI = BASE_URL;
        
        // Register a test user
        String registerBody = String.format("""
            {
                "username": "%s",
                "email": "passwordtest001@example.com",
                "password": "%s"
            }
            """, username, originalPassword);

        given()
            .contentType(ContentType.JSON)
            .body(registerBody)
        .when()
            .post(REGISTER_ENDPOINT)
        .then()
            .statusCode(201);

        // Login to get session token
        String loginBody = String.format("""
            {
                "username": "%s",
                "password": "%s"
            }
            """, username, originalPassword);

        Response loginResponse = given()
            .contentType(ContentType.JSON)
            .body(loginBody)
        .when()
            .post(LOGIN_ENDPOINT)
        .then()
            .statusCode(200)
            .extract().response();

        sessionToken = loginResponse.jsonPath().getString("sessionToken");
    }

    @Test
    @Order(1)
    @DisplayName("Test successful password change")
    public void testSuccessfulPasswordChange() {
        String newPassword = "newpassword456";
        String requestBody = String.format("""
            {
                "currentPassword": "%s",
                "newPassword": "%s"
            }
            """, originalPassword, newPassword);

        given()
            .header("Authorization", "Bearer " + sessionToken)
            .contentType(ContentType.JSON)
            .body(requestBody)
        .when()
            .post(CHANGE_PASSWORD_ENDPOINT)
        .then()
            .statusCode(200)
            .body("success", equalTo(true))
            .body("message", equalTo("Password changed successfully"));

        // Verify login with new password works
        String loginBody = String.format("""
            {
                "username": "%s",
                "password": "%s"
            }
            """, username, newPassword);

        given()
            .contentType(ContentType.JSON)
            .body(loginBody)
        .when()
            .post(LOGIN_ENDPOINT)
        .then()
            .statusCode(200)
            .body("success", equalTo(true));

        // Update originalPassword for subsequent tests
        originalPassword = newPassword;
    }

    @Test
    @Order(2)
    @DisplayName("Test password change with incorrect current password")
    public void testIncorrectCurrentPassword() {
        String requestBody = """
            {
                "currentPassword": "wrongpassword",
                "newPassword": "newpassword789"
            }
            """;

        given()
            .header("Authorization", "Bearer " + sessionToken)
            .contentType(ContentType.JSON)
            .body(requestBody)
        .when()
            .post(CHANGE_PASSWORD_ENDPOINT)
        .then()
            .statusCode(400)
            .body("success", equalTo(false))
            .body("message", containsStringIgnoringCase("current password"));
    }

    @Test
    @Order(3)
    @DisplayName("Test password change with short new password")
    public void testShortNewPassword() {
        String requestBody = String.format("""
            {
                "currentPassword": "%s",
                "newPassword": "12345"
            }
            """, originalPassword);

        given()
            .header("Authorization", "Bearer " + sessionToken)
            .contentType(ContentType.JSON)
            .body(requestBody)
        .when()
            .post(CHANGE_PASSWORD_ENDPOINT)
        .then()
            .statusCode(400)
            .body("success", equalTo(false))
            .body("message", containsStringIgnoringCase("password"));
    }

    @Test
    @Order(4)
    @DisplayName("Test password change without authorization")
    public void testPasswordChangeWithoutAuth() {
        String requestBody = String.format("""
            {
                "currentPassword": "%s",
                "newPassword": "newpassword999"
            }
            """, originalPassword);

        given()
            .contentType(ContentType.JSON)
            .body(requestBody)
        .when()
            .post(CHANGE_PASSWORD_ENDPOINT)
        .then()
            .statusCode(401)
            .body("success", equalTo(false))
            .body("message", equalTo("Unauthorized"));
    }

    @Test
    @Order(5)
    @DisplayName("Test password change with missing current password")
    public void testMissingCurrentPassword() {
        String requestBody = """
            {
                "newPassword": "newpassword999"
            }
            """;

        given()
            .header("Authorization", "Bearer " + sessionToken)
            .contentType(ContentType.JSON)
            .body(requestBody)
        .when()
            .post(CHANGE_PASSWORD_ENDPOINT)
        .then()
            .statusCode(400)
            .body("success", equalTo(false))
            .body("message", notNullValue());
    }

    @Test
    @Order(6)
    @DisplayName("Test password change with missing new password")
    public void testMissingNewPassword() {
        String requestBody = String.format("""
            {
                "currentPassword": "%s"
            }
            """, originalPassword);

        given()
            .header("Authorization", "Bearer " + sessionToken)
            .contentType(ContentType.JSON)
            .body(requestBody)
        .when()
            .post(CHANGE_PASSWORD_ENDPOINT)
        .then()
            .statusCode(400)
            .body("success", equalTo(false))
            .body("message", notNullValue());
    }

    @Test
    @Order(7)
    @DisplayName("Test password change with same password")
    public void testSamePassword() {
        String requestBody = String.format("""
            {
                "currentPassword": "%s",
                "newPassword": "%s"
            }
            """, originalPassword, originalPassword);

        given()
            .header("Authorization", "Bearer " + sessionToken)
            .contentType(ContentType.JSON)
            .body(requestBody)
        .when()
            .post(CHANGE_PASSWORD_ENDPOINT)
        .then()
            .statusCode(200)
            .body("success", equalTo(true))
            .body("message", equalTo("Password changed successfully"));
    }

    @AfterAll
    public static void tearDown() {
        app.stop();
    }
}


// Node: testSuccessfulPasswordChange
// Node: testIncorrectCurrentPassword
// Node: testShortNewPassword
// Node: testPasswordChangeWithoutAuth
// Node: testMissingCurrentPassword
// Node: testMissingNewPassword
// Node: testSamePassword
import io.restassured.RestAssured;
import io.restassured.http.ContentType;
import org.junit.jupiter.api.*;
import static io.restassured.RestAssured.*;
import static org.hamcrest.Matchers.*;

@TestMethodOrder(MethodOrderer.OrderAnnotation.class)
public class UserRegistrationTest {

    private static io.javalin.Javalin app;
    private static String BASE_URL;
    private static final String REGISTER_ENDPOINT = "/api/users/register";

    @BeforeAll
    public static void setup() {
        app = com.example.auth.Main.start(0);
        int port = app.port();
        BASE_URL = "http://localhost:" + port;
        RestAssured.baseURI = BASE_URL;
    }

    @Test
    @Order(1)
    @DisplayName("Test successful user registration with valid data")
    public void testSuccessfulRegistration() {
        String requestBody = """
                {
                    "username": "testuser001",
                    "email": "testuser001@example.com",
                    "password": "password123"
                }
                """;

        given()
                .contentType(ContentType.JSON)
                .body(requestBody)
                .when()
                .post(REGISTER_ENDPOINT)
                .then()
                .statusCode(201)
                .body("success", equalTo(true))
                .body("message", equalTo("User registered successfully"))
                .body("userId", notNullValue())
                .body("userId", matchesPattern("^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"));
    }

    @Test
    @Order(2)
    @DisplayName("Test registration with duplicate username")
    public void testDuplicateUsername() {
        String requestBody = """
                {
                    "username": "testuser001",
                    "email": "different@example.com",
                    "password": "password123"
                }
                """;

        given()
                .contentType(ContentType.JSON)
                .body(requestBody)
                .when()
                .post(REGISTER_ENDPOINT)
                .then()
                .statusCode(400)
                .body("success", equalTo(false))
                .body("message", containsStringIgnoringCase("username"));
    }

    @Test
    @Order(3)
    @DisplayName("Test registration with duplicate email")
    public void testDuplicateEmail() {
        String requestBody = """
                {
                    "username": "testuser002",
                    "email": "testuser001@example.com",
                    "password": "password123"
                }
                """;

        given()
                .contentType(ContentType.JSON)
                .body(requestBody)
                .when()
                .post(REGISTER_ENDPOINT)
                .then()
                .statusCode(400)
                .body("success", equalTo(false))
                .body("message", containsStringIgnoringCase("email"));
    }

    @Test
    @Order(4)
    @DisplayName("Test registration with invalid email format")
    public void testInvalidEmailFormat() {
        String requestBody = """
                {
                    "username": "testuser003",
                    "email": "invalid-email",
                    "password": "password123"
                }
                """;

        given()
                .contentType(ContentType.JSON)
                .body(requestBody)
                .when()
                .post(REGISTER_ENDPOINT)
                .then()
                .statusCode(400)
                .body("success", equalTo(false))
                .body("message", containsStringIgnoringCase("email"));
    }

    @Test
    @Order(5)
    @DisplayName("Test registration with short password")
    public void testShortPassword() {
        String requestBody = """
                {
                    "username": "testuser004",
                    "email": "testuser004@example.com",
                    "password": "12345"
                }
                """;

        given()
                .contentType(ContentType.JSON)
                .body(requestBody)
                .when()
                .post(REGISTER_ENDPOINT)
                .then()
                .statusCode(400)
                .body("success", equalTo(false))
                .body("message", containsStringIgnoringCase("password"));
    }

    @Test
    @Order(6)
    @DisplayName("Test registration with short username")
    public void testShortUsername() {
        String requestBody = """
                {
                    "username": "ab",
                    "email": "testuser005@example.com",
                    "password": "password123"
                }
                """;

        given()
                .contentType(ContentType.JSON)
                .body(requestBody)
                .when()
                .post(REGISTER_ENDPOINT)
                .then()
                .statusCode(400)
                .body("success", equalTo(false))
                .body("message", containsStringIgnoringCase("username"));
    }

    @Test
    @Order(7)
    @DisplayName("Test registration with long username")
    public void testLongUsername() {
        String requestBody = """
                {
                    "username": "thisusernameiswaytoolongandexceedstwentycharacters",
                    "email": "testuser006@example.com",
                    "password": "password123"
                }
                """;

        given()
                .contentType(ContentType.JSON)
                .body(requestBody)
                .when()
                .post(REGISTER_ENDPOINT)
                .then()
                .statusCode(400)
                .body("success", equalTo(false))
                .body("message", containsStringIgnoringCase("username"));
    }

    @Test
    @Order(8)
    @DisplayName("Test registration with missing username")
    public void testMissingUsername() {
        String requestBody = """
                {
                    "email": "testuser007@example.com",
                    "password": "password123"
                }
                """;

        given()
                .contentType(ContentType.JSON)
                .body(requestBody)
                .when()
                .post(REGISTER_ENDPOINT)
                .then()
                .statusCode(400)
                .body("success", equalTo(false))
                .body("message", notNullValue());
    }

    @Test
    @Order(9)
    @DisplayName("Test registration with missing email")
    public void testMissingEmail() {
        String requestBody = """
                {
                    "username": "testuser008",
                    "password": "password123"
                }
                """;

        given()
                .contentType(ContentType.JSON)
                .body(requestBody)
                .when()
                .post(REGISTER_ENDPOINT)
                .then()
                .statusCode(400)
                .body("success", equalTo(false))
                .body("message", notNullValue());
    }

    @Test
    @Order(10)
    @DisplayName("Test registration with missing password")
    public void testMissingPassword() {
        String requestBody = """
                {
                    "username": "testuser009",
                    "email": "testuser009@example.com"
                }
                """;

        given()
                .contentType(ContentType.JSON)
                .body(requestBody)
                .when()
                .post(REGISTER_ENDPOINT)
                .then()
                .statusCode(400)
                .body("success", equalTo(false))
                .body("message", notNullValue());
    }

    @AfterAll
    public static void tearDown() {
        app.stop();
    }
}


// Node: testSuccessfulRegistration
// Node: matchesPattern
// Node: testDuplicateUsername
// Node: testDuplicateEmail
// Node: testInvalidEmailFormat
// Node: testShortPassword
// Node: testShortUsername
// Node: testLongUsername
// Node: testMissingEmail
import io.restassured.RestAssured;
import io.restassured.http.ContentType;
import io.restassured.response.Response;
import org.junit.jupiter.api.*;
import static io.restassured.RestAssured.*;
import static org.hamcrest.Matchers.*;

@TestMethodOrder(MethodOrderer.OrderAnnotation.class)
public class UserProfileTest {

    private static io.javalin.Javalin app;
    private static String BASE_URL;
    private static final String REGISTER_ENDPOINT = "/api/users/register";
    private static final String LOGIN_ENDPOINT = "/api/users/login";
    private static final String PROFILE_ENDPOINT = "/api/users/profile";

    private static String sessionToken;
    private static String userId;
    private static String username = "profiletest001";
    private static String email = "profiletest001@example.com";

    @BeforeAll
    public static void setup() {
        app = com.example.auth.Main.start(0);
        int port = app.port();
        BASE_URL = "http://localhost:" + port;
        RestAssured.baseURI = BASE_URL;

        // Register a test user
        String registerBody = String.format("""
                {
                    "username": "%s",
                    "email": "%s",
                    "password": "testpass123"
                }
                """, username, email);

        Response registerResponse = given()
                .contentType(ContentType.JSON)
                .body(registerBody)
                .when()
                .post(REGISTER_ENDPOINT)
                .then()
                .statusCode(201)
                .extract().response();

        userId = registerResponse.jsonPath().getString("userId");

        // Login to get session token
        String loginBody = String.format("""
                {
                    "username": "%s",
                    "password": "testpass123"
                }
                """, username);

        Response loginResponse = given()
                .contentType(ContentType.JSON)
                .body(loginBody)
                .when()
                .post(LOGIN_ENDPOINT)
                .then()
                .statusCode(200)
                .extract().response();

        sessionToken = loginResponse.jsonPath().getString("sessionToken");
    }

    @Test
    @Order(1)
    @DisplayName("Test get profile with valid session token")
    public void testGetProfileSuccess() {
        given()
                .header("Authorization", "Bearer " + sessionToken)
                .when()
                .get(PROFILE_ENDPOINT)
                .then()
                .statusCode(200)
                .body("success", equalTo(true))
                .body("user.userId", equalTo(userId))
                .body("user.username", equalTo(username))
                .body("user.email", equalTo(email))
                .body("user.createdAt", notNullValue())
                .body("user.createdAt", matchesPattern("^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}.*"));
    }

    @Test
    @Order(2)
    @DisplayName("Test get profile without authorization header")
    public void testGetProfileWithoutAuth() {
        given()
                .when()
                .get(PROFILE_ENDPOINT)
                .then()
                .statusCode(401)
                .body("success", equalTo(false))
                .body("message", equalTo("Unauthorized"));
    }

    @Test
    @Order(3)
    @DisplayName("Test get profile with invalid session token")
    public void testGetProfileWithInvalidToken() {
        given()
                .header("Authorization", "Bearer invalid-token-12345")
                .when()
                .get(PROFILE_ENDPOINT)
                .then()
                .statusCode(401)
                .body("success", equalTo(false))
                .body("message", equalTo("Unauthorized"));
    }

    @Test
    @Order(4)
    @DisplayName("Test update profile with valid email")
    public void testUpdateProfileSuccess() {
        String newEmail = "newemail@example.com";
        String requestBody = String.format("""
                {
                    "email": "%s"
                }
                """, newEmail);

        given()
                .header("Authorization", "Bearer " + sessionToken)
                .contentType(ContentType.JSON)
                .body(requestBody)
                .when()
                .put(PROFILE_ENDPOINT)
                .then()
                .statusCode(200)
                .body("success", equalTo(true))
                .body("message", equalTo("Profile updated successfully"));

        // Verify the email was updated
        given()
                .header("Authorization", "Bearer " + sessionToken)
                .when()
                .get(PROFILE_ENDPOINT)
                .then()
                .statusCode(200)
                .body("user.email", equalTo(newEmail));
    }

    @Test
    @Order(5)
    @DisplayName("Test update profile with invalid email format")
    public void testUpdateProfileInvalidEmail() {
        String requestBody = """
                {
                    "email": "invalid-email-format"
                }
                """;

        given()
                .header("Authorization", "Bearer " + sessionToken)
                .contentType(ContentType.JSON)
                .body(requestBody)
                .when()
                .put(PROFILE_ENDPOINT)
                .then()
                .statusCode(400)
                .body("success", equalTo(false))
                .body("message", containsStringIgnoringCase("email"));
    }

    @Test
    @Order(6)
    @DisplayName("Test update profile without authorization")
    public void testUpdateProfileWithoutAuth() {
        String requestBody = """
                {
                    "email": "unauthorized@example.com"
                }
                """;

        given()
                .contentType(ContentType.JSON)
                .body(requestBody)
                .when()
                .put(PROFILE_ENDPOINT)
                .then()
                .statusCode(401)
                .body("success", equalTo(false))
                .body("message", equalTo("Unauthorized"));
    }

    @Test
    @Order(7)
    @DisplayName("Test update profile with empty request body")
    public void testUpdateProfileEmptyBody() {
        String requestBody = "{}";

        given()
                .header("Authorization", "Bearer " + sessionToken)
                .contentType(ContentType.JSON)
                .body(requestBody)
                .when()
                .put(PROFILE_ENDPOINT)
                .then()
                .statusCode(400)
                .body("success", equalTo(false));
    }

    @AfterAll
    public static void tearDown() {
        app.stop();
    }
}


// Node: testGetProfileSuccess
// Node: testGetProfileWithoutAuth
// Node: testGetProfileWithInvalidToken
// Node: testUpdateProfileSuccess
// Node: testUpdateProfileInvalidEmail
// Node: testUpdateProfileWithoutAuth
// Node: testUpdateProfileEmptyBody
package com.example.coursescheduling;

import io.restassured.http.ContentType;
import org.junit.jupiter.api.Test;
import static io.restassured.RestAssured.given;
import static org.hamcrest.Matchers.*;

public class OfferingApiTest extends BaseApiTest {

    @Test
    public void testCreateAndGetOffering() {
        // Setup dependencies
        int termId = given().contentType(ContentType.JSON).body("{ \"name\": \"2024-T1\", \"startDate\": \"2024-01-01\", \"endDate\": \"2024-05-01\" }").post("/api/terms").then().extract().path("id");
        int deptId = given().contentType(ContentType.JSON).body("{ \"name\": \"Eng\" }").post("/api/departments").then().extract().path("id");
        int teacherId = given().contentType(ContentType.JSON).body("{ \"name\": \"T1\", \"departmentId\": " + deptId + " }").post("/api/teachers").then().extract().path("id");
        int courseId = given().contentType(ContentType.JSON).body("{ \"name\": \"C1\", \"credits\": 3, \"departmentId\": " + deptId + " }").post("/api/courses").then().extract().path("id");

        String offeringJson = String.format(
            "{ \"courseId\": %d, \"termId\": %d, \"teacherId\": %d, \"maxCapacity\": 50 }",
            courseId, termId, teacherId
        );

        int offeringId = given()
            .contentType(ContentType.JSON)
            .body(offeringJson)
        .when()
            .post("/api/offerings")
        .then()
            .statusCode(200)
            .body("maxCapacity", equalTo(50))
            .extract().path("id");

        given()
        .when()
            .get("/api/offerings/" + offeringId)
        .then()
            .statusCode(200)
            .body("courseId", equalTo(courseId));
    }
}


// Node: testCreateAndGetOffering
// Node: path
package com.example.coursescheduling;

import io.restassured.http.ContentType;
import org.junit.jupiter.api.Test;
import static io.restassured.RestAssured.given;
import static org.hamcrest.Matchers.*;

public class CourseApiTest extends BaseApiTest {

    @Test
    public void testCreateAndGetCourse() {
        String deptJson = "{ \"name\": \"Science\" }";
        int deptId = given().contentType(ContentType.JSON).body(deptJson).post("/api/departments").then().extract().path("id");

        String courseJson = "{ \"name\": \"Intro to Java\", \"credits\": 3, \"departmentId\": " + deptId + " }";

        int courseId = given()
            .contentType(ContentType.JSON)
            .body(courseJson)
        .when()
            .post("/api/courses")
        .then()
            .statusCode(200)
            .body("name", equalTo("Intro to Java"))
            .extract().path("id");

        given()
        .when()
            .get("/api/courses/" + courseId)
        .then()
            .statusCode(200)
            .body("credits", equalTo(3));
    }

    @Test
    public void testDeleteCourse() {
        String deptJson = "{ \"name\": \"Arts\" }";
        int deptId = given().contentType(ContentType.JSON).body(deptJson).post("/api/departments").then().extract().path("id");
        String courseJson = "{ \"name\": \"Art History\", \"credits\": 2, \"departmentId\": " + deptId + " }";
        int courseId = given().contentType(ContentType.JSON).body(courseJson).post("/api/courses").then().extract().path("id");

        given()
        .when()
            .delete("/api/courses/" + courseId)
        .then()
            .statusCode(200);
    }
}


// Node: testCreateAndGetCourse
// Node: testDeleteCourse
package com.example.coursescheduling;

import io.restassured.http.ContentType;
import org.junit.jupiter.api.Test;
import static io.restassured.RestAssured.given;
import static org.hamcrest.Matchers.*;

public class ScheduleApiTest extends BaseApiTest {

    @Test
    public void testAutoSchedule() {
        int termId = given().contentType(ContentType.JSON).body("{ \"name\": \"2024-Auto\", \"startDate\": \"2024-09-01\", \"endDate\": \"2025-01-15\" }").post("/api/terms").then().extract().path("id");

        String autoJson = "{ \"termId\": " + termId + " }";

        given()
            .contentType(ContentType.JSON)
            .body(autoJson)
        .when()
            .post("/api/schedule/auto")
        .then()
            .statusCode(200)
            .body("status", notNullValue());
    }

    @Test
    public void testManualSchedule() {
        // Setup basic entities
        int termId = given().contentType(ContentType.JSON).body("{ \"name\": \"2024-Manual\", \"startDate\": \"2024-09-01\", \"endDate\": \"2025-01-15\" }").post("/api/terms").then().extract().path("id");
        int deptId = given().contentType(ContentType.JSON).body("{ \"name\": \"CS\" }").post("/api/departments").then().extract().path("id");
        int teacherId = given().contentType(ContentType.JSON).body("{ \"name\": \"T_Man\", \"departmentId\": " + deptId + " }").post("/api/teachers").then().extract().path("id");
        int courseId = given().contentType(ContentType.JSON).body("{ \"name\": \"C_Man\", \"credits\": 3, \"departmentId\": " + deptId + " }").post("/api/courses").then().extract().path("id");
        int offeringId = given().contentType(ContentType.JSON).body(String.format("{ \"courseId\": %d, \"termId\": %d, \"teacherId\": %d, \"maxCapacity\": 50 }", courseId, termId, teacherId)).post("/api/offerings").then().extract().path("id");
        int classroomId = given().contentType(ContentType.JSON).body("{ \"name\": \"Room 101\", \"capacity\": 50, \"type\": \"NORMAL\" }").post("/api/classrooms").then().extract().path("id");

        String manualJson = String.format(
            "{ \"offeringId\": %d, \"classroomId\": %d, \"dayOfWeek\": 1, \"period\": 1 }",
            offeringId, classroomId
        );

        given()
            .contentType(ContentType.JSON)
            .body(manualJson)
        .when()
            .post("/api/schedule/manual")
        .then()
            .statusCode(200)
            .body("success", equalTo(true));
    }

    @Test
    public void testGetSchedules() {
        int termId = given().contentType(ContentType.JSON).body("{ \"name\": \"2024-Get\", \"startDate\": \"2024-09-01\", \"endDate\": \"2025-01-15\" }").post("/api/terms").then().extract().path("id");
        
        given()
        .when()
            .get("/api/schedule/term/" + termId)
        .then()
            .statusCode(200);
    }
}


// Node: testAutoSchedule
// Node: testManualSchedule
// Node: testGetSchedules
package com.example.coursescheduling;

import io.restassured.http.ContentType;
import org.junit.jupiter.api.Test;
import static io.restassured.RestAssured.given;
import static org.hamcrest.Matchers.*;

public class ClassroomApiTest extends BaseApiTest {

    @Test
    public void testCreateAndGetClassroom() {
        String json = "{ \"name\": \"Building A 101\", \"capacity\": 50, \"type\": \"MULTIMEDIA\" }";

        int id = given()
            .contentType(ContentType.JSON)
            .body(json)
        .when()
            .post("/api/classrooms")
        .then()
            .statusCode(200)
            .body("name", equalTo("Building A 101"))
            .extract().path("id");

        given()
        .when()
            .get("/api/classrooms/" + id)
        .then()
            .statusCode(200)
            .body("capacity", equalTo(50));
    }

    @Test
    public void testListClassrooms() {
        given()
        .when()
            .get("/api/classrooms")
        .then()
            .statusCode(200);
    }

    @Test
    public void testUpdateClassroom() {
        String json = "{ \"name\": \"Room 202\", \"capacity\": 30, \"type\": \"NORMAL\" }";
        int id = given().contentType(ContentType.JSON).body(json).post("/api/classrooms").then().extract().path("id");

        String updateJson = "{ \"name\": \"Room 202\", \"capacity\": 35, \"type\": \"NORMAL\" }";
        given()
            .contentType(ContentType.JSON)
            .body(updateJson)
        .when()
            .put("/api/classrooms/" + id)
        .then()
            .statusCode(200)
            .body("capacity", equalTo(35));
    }

    @Test
    public void testDeleteClassroom() {
        String json = "{ \"name\": \"Room 303\", \"capacity\": 20, \"type\": \"LAB\" }";
        int id = given().contentType(ContentType.JSON).body(json).post("/api/classrooms").then().extract().path("id");

        given()
        .when()
            .delete("/api/classrooms/" + id)
        .then()
            .statusCode(200);
    }
}


// Node: testCreateAndGetClassroom
// Node: testListClassrooms
// Node: testUpdateClassroom
// Node: testDeleteClassroom
package com.example.coursescheduling;

import io.restassured.http.ContentType;
import org.junit.jupiter.api.Test;
import static io.restassured.RestAssured.given;
import static org.hamcrest.Matchers.*;

public class DepartmentApiTest extends BaseApiTest {

    @Test
    public void testCreateAndListDepartments() {
        String json = "{ \"name\": \"Computer Science\" }";

        given()
            .contentType(ContentType.JSON)
            .body(json)
        .when()
            .post("/api/departments")
        .then()
            .statusCode(200)
            .body("name", equalTo("Computer Science"));

        given()
        .when()
            .get("/api/departments")
        .then()
            .statusCode(200)
            .body("name", hasItem("Computer Science"));
    }

    @Test
    public void testDeleteDepartment() {
        String json = "{ \"name\": \"Physics\" }";
        int id = given().contentType(ContentType.JSON).body(json).post("/api/departments").then().extract().path("id");

        given()
        .when()
            .delete("/api/departments/" + id)
        .then()
            .statusCode(200);
    }
}


// Node: testCreateAndListDepartments
// Node: hasItem
// Node: testDeleteDepartment
package com.example.coursescheduling;

import io.restassured.http.ContentType;
import org.junit.jupiter.api.Test;
import static io.restassured.RestAssured.given;
import static org.hamcrest.Matchers.*;

public class TeacherApiTest extends BaseApiTest {

    @Test
    public void testCreateAndGetTeacher() {
        // Ensure dept exists
        String deptJson = "{ \"name\": \"Math\" }";
        int deptId = given().contentType(ContentType.JSON).body(deptJson).post("/api/departments").then().extract().path("id");

        String teacherJson = "{ \"name\": \"John Doe\", \"departmentId\": " + deptId + " }";

        int teacherId = given()
            .contentType(ContentType.JSON)
            .body(teacherJson)
        .when()
            .post("/api/teachers")
        .then()
            .statusCode(200)
            .body("name", equalTo("John Doe"))
            .extract().path("id");

        given()
        .when()
            .get("/api/teachers/" + teacherId)
        .then()
            .statusCode(200)
            .body("departmentId", equalTo(deptId));
    }

    @Test
    public void testUpdateTeacher() {
        String deptJson = "{ \"name\": \"History\" }";
        int deptId = given().contentType(ContentType.JSON).body(deptJson).post("/api/departments").then().extract().path("id");
        String teacherJson = "{ \"name\": \"Jane Smith\", \"departmentId\": " + deptId + " }";
        int teacherId = given().contentType(ContentType.JSON).body(teacherJson).post("/api/teachers").then().extract().path("id");

        String updateJson = "{ \"name\": \"Jane Doe\", \"departmentId\": " + deptId + " }";
        given()
            .contentType(ContentType.JSON)
            .body(updateJson)
        .when()
            .put("/api/teachers/" + teacherId)
        .then()
            .statusCode(200)
            .body("name", equalTo("Jane Doe"));
    }
}


// Node: testCreateAndGetTeacher
// Node: testUpdateTeacher
package com.example.coursescheduling;

import io.restassured.http.ContentType;
import org.junit.jupiter.api.Test;
import static io.restassured.RestAssured.given;
import static org.hamcrest.Matchers.*;

public class TermApiTest extends BaseApiTest {

    @Test
    public void testCreateAndGetTerm() {
        String termJson = "{ \"name\": \"2024-Fall\", \"startDate\": \"2024-09-01\", \"endDate\": \"2025-01-15\" }";

        int termId = given()
            .contentType(ContentType.JSON)
            .body(termJson)
        .when()
            .post("/api/terms")
        .then()
            .statusCode(200)
            .body("name", equalTo("2024-Fall"))
            .extract().path("id");

        given()
        .when()
            .get("/api/terms/" + termId)
        .then()
            .statusCode(200)
            .body("name", equalTo("2024-Fall"));
    }

    @Test
    public void testListTerms() {
        given()
        .when()
            .get("/api/terms")
        .then()
            .statusCode(200)
            .body("$", not(empty()));
    }

    @Test
    public void testUpdateTerm() {
        String termJson = "{ \"name\": \"2025-Spring\", \"startDate\": \"2025-02-01\", \"endDate\": \"2025-06-15\" }";
        int termId = given().contentType(ContentType.JSON).body(termJson).post("/api/terms").then().extract().path("id");

        String updateJson = "{ \"name\": \"2025-Spring-Updated\", \"startDate\": \"2025-02-01\", \"endDate\": \"2025-06-20\" }";
        given()
            .contentType(ContentType.JSON)
            .body(updateJson)
        .when()
            .put("/api/terms/" + termId)
        .then()
            .statusCode(200)
            .body("name", equalTo("2025-Spring-Updated"));
    }

    @Test
    public void testDeleteTerm() {
        String termJson = "{ \"name\": \"ToDelete\", \"startDate\": \"2025-01-01\", \"endDate\": \"2025-02-01\" }";
        int termId = given().contentType(ContentType.JSON).body(termJson).post("/api/terms").then().extract().path("id");

        given()
        .when()
            .delete("/api/terms/" + termId)
        .then()
            .statusCode(200);

        given()
        .when()
            .get("/api/terms/" + termId)
        .then()
            .statusCode(404);
    }
}


// Node: testCreateAndGetTerm
// Node: testUpdateTerm
// Node: testDeleteTerm
package com.example.coursescheduling;

import io.restassured.http.ContentType;
import org.junit.jupiter.api.Test;
import static io.restassured.RestAssured.given;
import static org.hamcrest.Matchers.*;

public class ConstraintApiTest extends BaseApiTest {

    @Test
    public void testAddAndListConstraints() {
        int deptId = given().contentType(ContentType.JSON).body("{ \"name\": \"Math\" }").post("/api/departments").then().extract().path("id");
        int teacherId = given().contentType(ContentType.JSON).body("{ \"name\": \"T_Constraint\", \"departmentId\": " + deptId + " }").post("/api/teachers").then().extract().path("id");

        String constraintJson = String.format(
            "{ \"teacherId\": %d, \"dayOfWeek\": 5, \"period\": 3, \"type\": \"UNAVAILABLE\" }",
            teacherId
        );

        given()
            .contentType(ContentType.JSON)
            .body(constraintJson)
        .when()
            .post("/api/constraints")
        .then()
            .statusCode(200)
            .body("type", equalTo("UNAVAILABLE"));

        given()
        .when()
            .get("/api/constraints")
        .then()
            .statusCode(200)
            .body("type", hasItem("UNAVAILABLE"));
    }
}


// Node: testAddAndListConstraints
package tests;

import io.restassured.RestAssured;
import io.restassured.http.ContentType;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.MethodOrderer;
import org.junit.jupiter.api.Order;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestMethodOrder;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.server.LocalServerPort;
import com.example.chatgateway.ChatGatewayApplication;

import static io.restassured.RestAssured.given;
import static org.hamcrest.Matchers.*;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT, classes = ChatGatewayApplication.class)
@TestMethodOrder(MethodOrderer.OrderAnnotation.class)
public class ApiTest {

        @LocalServerPort
        private Integer port;

        private static String userId;
        private static String token;
        private static String groupId;
        private static String messageId;

        @BeforeEach
        public void setup() {
                RestAssured.port = port;
        }

        @Test
        @Order(1)
        public void testRegisterUser() {
                String response = given()
                                .contentType(ContentType.JSON)
                                .body("{\n" +
                                                "  \"username\": \"testuser\",\n" +
                                                "  \"email\": \"test@example.com\",\n" +
                                                "  \"password\": \"password123\"\n" +
                                                "}")
                                .when()
                                .post("/api/users/register")
                                .then()
                                .statusCode(200)
                                .body("userId", notNullValue())
                                .body("username", equalTo("testuser"))
                                .body("createdAt", notNullValue())
                                .extract().path("userId");

                userId = response;
        }

        @Test
        @Order(2)
        public void testLoginUser() {
                String response = given()
                                .contentType(ContentType.JSON)
                                .body("{\n" +
                                                "  \"username\": \"testuser\",\n" +
                                                "  \"password\": \"password123\"\n" +
                                                "}")
                                .when()
                                .post("/api/users/login")
                                .then()
                                .statusCode(200)
                                .body("token", notNullValue())
                                .body("userId", equalTo(userId))
                                .body("expiresIn", notNullValue())
                                .extract().path("token");

                token = response;
        }

        @Test
        @Order(3)
        public void testGetUserStatus() {
                given()
                                .pathParam("userId", userId)
                                .when()
                                .get("/api/users/{userId}/status")
                                .then()
                                .statusCode(200)
                                .body("userId", equalTo(userId))
                                .body("status", notNullValue())
                                .body("lastActive", notNullValue());
        }

        @Test
        @Order(4)
        public void testUpdateUserStatus() {
                given()
                                .contentType(ContentType.JSON)
                                .pathParam("userId", userId)
                                .body("{\n" +
                                                "  \"status\": \"AWAY\"\n" +
                                                "}")
                                .when()
                                .put("/api/users/{userId}/status")
                                .then()
                                .statusCode(200)
                                .body("userId", equalTo(userId))
                                .body("status", equalTo("AWAY"))
                                .body("updatedAt", notNullValue());
        }

        @Test
        @Order(5)
        public void testSendPrivateMessage() {
                // Register a second user to receive message
                String recipientId = given()
                                .contentType(ContentType.JSON)
                                .body("{\n" +
                                                "  \"username\": \"recipient\",\n" +
                                                "  \"email\": \"recipient@example.com\",\n" +
                                                "  \"password\": \"password123\"\n" +
                                                "}")
                                .when()
                                .post("/api/users/register")
                                .then()
                                .extract().path("userId");

                given()
                                .contentType(ContentType.JSON)
                                .body("{\n" +
                                                "  \"senderId\": \"" + userId + "\",\n" +
                                                "  \"recipientId\": \"" + recipientId + "\",\n" +
                                                "  \"content\": \"Hello World\",\n" +
                                                "  \"type\": \"TEXT\"\n" +
                                                "}")
                                .when()
                                .post("/api/messages/send")
                                .then()
                                .statusCode(200)
                                .body("messageId", notNullValue())
                                .body("timestamp", notNullValue())
                                .body("status", equalTo("SENT"));
        }

        @Test
        @Order(6)
        public void testGetMessageHistory() {
                given()
                                .queryParam("userId1", userId)
                                .queryParam("userId2", "recipient_id_placeholder") // In a real scenario we'd use the ID
                                                                                   // from step 5
                                .when()
                                .get("/api/messages/history")
                                .then()
                                .statusCode(200)
                                .body("messages", notNullValue());
        }

        @Test
        @Order(7)
        public void testCreateGroup() {
                String response = given()
                                .contentType(ContentType.JSON)
                                .body("{\n" +
                                                "  \"creatorId\": \"" + userId + "\",\n" +
                                                "  \"name\": \"Test Group\",\n" +
                                                "  \"description\": \"A group for testing\"\n" +
                                                "}")
                                .when()
                                .post("/api/groups/create")
                                .then()
                                .statusCode(200)
                                .body("groupId", notNullValue())
                                .body("name", equalTo("Test Group"))
                                .body("createdAt", notNullValue())
                                .extract().path("groupId");

                groupId = response;
        }

        @Test
        @Order(8)
        public void testJoinGroup() {
                // Register a user to join
                String joinerId = given()
                                .contentType(ContentType.JSON)
                                .body("{\n" +
                                                "  \"username\": \"joiner\",\n" +
                                                "  \"email\": \"joiner@example.com\",\n" +
                                                "  \"password\": \"password123\"\n" +
                                                "}")
                                .when()
                                .post("/api/users/register")
                                .then()
                                .extract().path("userId");

                given()
                                .contentType(ContentType.JSON)
                                .pathParam("groupId", groupId)
                                .body("{\n" +
                                                "  \"userId\": \"" + joinerId + "\"\n" +
                                                "}")
                                .when()
                                .post("/api/groups/{groupId}/join")
                                .then()
                                .statusCode(200)
                                .body("groupId", equalTo(groupId))
                                .body("userId", equalTo(joinerId))
                                .body("role", equalTo("MEMBER"))
                                .body("joinedAt", notNullValue());
        }

        @Test
        @Order(9)
        public void testSendGroupMessage() {
                given()
                                .contentType(ContentType.JSON)
                                .pathParam("groupId", groupId)
                                .body("{\n" +
                                                "  \"senderId\": \"" + userId + "\",\n" +
                                                "  \"content\": \"Hello Group\",\n" +
                                                "  \"type\": \"TEXT\"\n" +
                                                "}")
                                .when()
                                .post("/api/groups/{groupId}/messages")
                                .then()
                                .statusCode(200)
                                .body("messageId", notNullValue())
                                .body("groupId", equalTo(groupId))
                                .body("timestamp", notNullValue());
        }

        @Test
        @Order(10)
        public void testListGroupMembers() {
                given()
                                .pathParam("groupId", groupId)
                                .when()
                                .get("/api/groups/{groupId}/members")
                                .then()
                                .statusCode(200)
                                .body("groupId", equalTo(groupId))
                                .body("members", hasSize(greaterThanOrEqualTo(1)));
        }

        @Test
        @Order(11)
        public void testLeaveGroup() {
                // Register a user to leave
                String leaverId = given()
                                .contentType(ContentType.JSON)
                                .body("{\n" +
                                                "  \"username\": \"leaver\",\n" +
                                                "  \"email\": \"leaver@example.com\",\n" +
                                                "  \"password\": \"password123\"\n" +
                                                "}")
                                .when()
                                .post("/api/users/register")
                                .then()
                                .extract().path("userId");

                // Join first
                given()
                                .contentType(ContentType.JSON)
                                .pathParam("groupId", groupId)
                                .body("{\n" +
                                                "  \"userId\": \"" + leaverId + "\"\n" +
                                                "}")
                                .when()
                                .post("/api/groups/{groupId}/join");

                given()
                                .contentType(ContentType.JSON)
                                .pathParam("groupId", groupId)
                                .body("{\n" +
                                                "  \"userId\": \"" + leaverId + "\"\n" +
                                                "}")
                                .when()
                                .post("/api/groups/{groupId}/leave")
                                .then()
                                .statusCode(200)
                                .body("success", equalTo(true));
        }

        @Test
        @Order(12)
        public void testSystemHealth() {
                given()
                                .when()
                                .get("/api/system/health")
                                .then()
                                .statusCode(200)
                                .body("status", equalTo("UP"))
                                .body("uptime", notNullValue())
                                .body("version", notNullValue());
        }
}


// Node: testGetUserStatus
// Node: testUpdateUserStatus
// Node: testSendPrivateMessage
// Node: testCreateGroup
// Node: testJoinGroup
// Node: testSendGroupMessage
// Node: testLeaveGroup
package com.example.blog;

import io.quarkus.test.junit.QuarkusTest;
import io.restassured.RestAssured;
import io.restassured.http.ContentType;
import org.junit.jupiter.api.MethodOrderer;
import org.junit.jupiter.api.Order;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestMethodOrder;

import static io.restassured.RestAssured.given;
import static org.hamcrest.Matchers.*;

@QuarkusTest
@TestMethodOrder(MethodOrderer.OrderAnnotation.class)
public class ApiTest {

    private static String createdPostId;
    private static String createdCategoryId;
    private static String createdCommentId;
    private static String createdAuthorId;

    @Test
    @Order(1)
    public void testCreateAuthor() {
        String authorJson = "{\"name\": \"John Doe\", \"email\": \"john@example.com\", \"bio\": \"Tech Writer\"}";
        createdAuthorId = given()
                .contentType(ContentType.JSON)
                .body(authorJson)
                .when()
                .post("/api/authors")
                .then()
                .statusCode(200) // Assuming 200 OK or 201 Created
                .body("id", notNullValue())
                .body("name", equalTo("John Doe"))
                .extract().path("id");
    }

    @Test
    @Order(2)
    public void testGetAuthor() {
        given()
                .pathParam("id", createdAuthorId)
                .when()
                .get("/api/authors/{id}")
                .then()
                .statusCode(200)
                .body("id", equalTo(createdAuthorId))
                .body("name", equalTo("John Doe"));
    }

    @Test
    @Order(3)
    public void testCreateCategory() {
        String categoryJson = "{\"name\": \"Tech\", \"description\": \"Technology related posts\"}";
        createdCategoryId = given()
                .contentType(ContentType.JSON)
                .body(categoryJson)
                .when()
                .post("/api/categories")
                .then()
                .statusCode(200)
                .body("id", notNullValue())
                .body("name", equalTo("Tech"))
                .extract().path("id");
    }

    @Test
    @Order(4)
    public void testGetCategories() {
        given()
                .when()
                .get("/api/categories")
                .then()
                .statusCode(200)
                .body("size()", greaterThan(0));
    }

    @Test
    @Order(5)
    public void testUpdateCategory() {
        String updateJson = "{\"name\": \"Technology\", \"description\": \"Updated description\"}";
        given()
                .contentType(ContentType.JSON)
                .body(updateJson)
                .pathParam("id", createdCategoryId)
                .when()
                .put("/api/categories/{id}")
                .then()
                .statusCode(200)
                .body("name", equalTo("Technology"));
    }

    @Test
    @Order(6)
    public void testCreatePost() {
        String postJson = "{\"title\": \"Quarkus Intro\", \"content\": \"Introduction to Quarkus\", \"authorId\": \"" + createdAuthorId + "\", \"categoryId\": \"" + createdCategoryId + "\", \"tags\": [\"java\", \"quarkus\"]}";
        createdPostId = given()
                .contentType(ContentType.JSON)
                .body(postJson)
                .when()
                .post("/api/posts")
                .then()
                .statusCode(200)
                .body("id", notNullValue())
                .body("title", equalTo("Quarkus Intro"))
                .body("tags", hasItems("java", "quarkus"))
                .extract().path("id");
    }

    @Test
    @Order(7)
    public void testGetPost() {
        given()
                .pathParam("id", createdPostId)
                .when()
                .get("/api/posts/{id}")
                .then()
                .statusCode(200)
                .body("id", equalTo(createdPostId))
                .body("title", equalTo("Quarkus Intro"));
    }

    @Test
    @Order(8)
    public void testUpdatePost() {
        String updateJson = "{\"title\": \"Quarkus Deep Dive\", \"content\": \"Deep dive into Quarkus\", \"categoryId\": \"" + createdCategoryId + "\", \"tags\": [\"java\", \"quarkus\", \"cloud\"]}";
        given()
                .contentType(ContentType.JSON)
                .body(updateJson)
                .pathParam("id", createdPostId)
                .when()
                .put("/api/posts/{id}")
                .then()
                .statusCode(200)
                .body("title", equalTo("Quarkus Deep Dive"))
                .body("tags", hasItem("cloud"));
    }

    @Test
    @Order(9)
    public void testListPosts() {
        given()
                .queryParam("page", 0)
                .queryParam("size", 10)
                .when()
                .get("/api/posts")
                .then()
                .statusCode(200)
                .body("data.size()", greaterThan(0))
                .body("total", notNullValue());
    }

    @Test
    @Order(10)
    public void testAddComment() {
        String commentJson = "{\"postId\": \"" + createdPostId + "\", \"authorName\": \"Reader\", \"content\": \"Great post!\"}";
        createdCommentId = given()
                .contentType(ContentType.JSON)
                .body(commentJson)
                .when()
                .post("/api/comments")
                .then()
                .statusCode(200)
                .body("id", notNullValue())
                .body("content", equalTo("Great post!"))
                .extract().path("id");
    }

    @Test
    @Order(11)
    public void testGetCommentsForPost() {
        given()
                .pathParam("id", createdPostId)
                .when()
                .get("/api/posts/{id}/comments")
                .then()
                .statusCode(200)
                .body("size()", greaterThan(0))
                .body("[0].content", equalTo("Great post!"));
    }

    @Test
    @Order(12)
    public void testGetTags() {
        given()
                .when()
                .get("/api/tags")
                .then()
                .statusCode(200)
                .body("$", hasItems("java", "quarkus", "cloud"));
    }

    @Test
    @Order(13)
    public void testDeleteComment() {
        given()
                .pathParam("id", createdCommentId)
                .when()
                .delete("/api/comments/{id}")
                .then()
                .statusCode(204);
    }

    @Test
    @Order(14)
    public void testDeletePost() {
        given()
                .pathParam("id", createdPostId)
                .when()
                .delete("/api/posts/{id}")
                .then()
                .statusCode(204);
    }

    @Test
    @Order(15)
    public void testDeleteCategory() {
        given()
                .pathParam("id", createdCategoryId)
                .when()
                .delete("/api/categories/{id}")
                .then()
                .statusCode(204);
    }
}


// Node: testCreateAuthor
// Node: testGetAuthor
// Node: testCreateCategory
// Node: testUpdateCategory
// Node: testCreatePost
// Node: testGetPost
// Node: testUpdatePost
// Node: testDeleteComment
// Node: testDeletePost
// Node: testDeleteCategory
