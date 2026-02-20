// Cluster 2

package adminuser;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;
import org.springframework.cloud.client.loadbalancer.LoadBalanced;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.EnableAspectJAutoProxy;
import org.springframework.integration.annotation.IntegrationComponentScan;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.web.client.RestTemplate;
import springfox.documentation.swagger2.annotations.EnableSwagger2;

/**
 * @author fdse
 */
@SpringBootApplication
@EnableAspectJAutoProxy(proxyTargetClass = true)
@EnableAsync
@IntegrationComponentScan
@EnableSwagger2
@EnableDiscoveryClient
public class AdminUserApplication {
    public static void main(String[] args)  {
        SpringApplication.run(AdminUserApplication.class, args);
    }

    @LoadBalanced
    @Bean
    public RestTemplate restTemplate(RestTemplateBuilder builder) {
        return builder.build();
    }
}


// Node: restTemplate
// Node: build
// Node: getAllUsers
// Node: updateUser
// Node: addUser
// Node: deleteUser
package adminuser.service;

import adminuser.dto.UserDto;
import edu.fudan.common.util.Response;
import org.springframework.http.HttpHeaders;

/**
 * @author fdse
 */
public interface AdminUserService {

    /**
     * get all users
     *
     * @param headers headers
     * @return Response
     */
    Response getAllUsers(HttpHeaders headers);

    /**
     * delete user by user id
     *
     * @param userId user id
     * @param headers headers
     * @return Response
     */
    Response deleteUser(String userId, HttpHeaders headers);

    /**
     * update user by user dto
     *
     * @param userDto user dto
     * @param headers headers
     * @return Response
     */
    Response updateUser(UserDto userDto, HttpHeaders headers);

    /**
     * add user by user dto
     *
     * @param userDto user dto
     * @param headers headers
     * @return Response
     */
    Response addUser(UserDto userDto, HttpHeaders headers);
}


// Node: repos/cloned_ms_repos/train-ticket/ts-admin-user-service/src/main/java/adminuser/service/AdminUserService.java:AdminUserService.<init>
package adminuser.controller;

import adminuser.dto.UserDto;
import adminuser.service.AdminUserService;
import com.alibaba.fastjson.JSONObject;
import edu.fudan.common.util.Response;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.springframework.http.*;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.request.MockMvcRequestBuilders;
import org.springframework.test.web.servlet.result.MockMvcResultMatchers;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

@RunWith(JUnit4.class)
public class AdminUserControllerTest {

    @InjectMocks
    private AdminUserController adminUserController;

    @Mock
    private AdminUserService adminUserService;
    private MockMvc mockMvc;
    private Response response = new Response();

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
        mockMvc = MockMvcBuilders.standaloneSetup(adminUserController).build();
    }

    @Test
    public void testHome() throws Exception {
        mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/adminuserservice/users/welcome"))
                .andExpect(MockMvcResultMatchers.status().isOk());
    }

    @Test
    public void testGetAllUsers() throws Exception {
        Mockito.when(adminUserService.getAllUsers(Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/adminuserservice/users"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testUpdateUser() throws Exception {
        UserDto userDto = new UserDto();
        Mockito.when(adminUserService.updateUser(Mockito.any(UserDto.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(userDto);
        String result = mockMvc.perform(MockMvcRequestBuilders.put("/api/v1/adminuserservice/users").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testAddUser() throws Exception {
        UserDto userDto = new UserDto();
        Mockito.when(adminUserService.addUser(Mockito.any(UserDto.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(userDto);
        String result = mockMvc.perform(MockMvcRequestBuilders.post("/api/v1/adminuserservice/users").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testDeleteUser() throws Exception {
        Mockito.when(adminUserService.deleteUser(Mockito.anyString(), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.delete("/api/v1/adminuserservice/users/user_id"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

}


// Node: setUp
// Node: initMocks
// Node: standaloneSetup
// Node: testHome
// Node: perform
// Node: get
// Node: andExpect
// Node: status
// Node: isOk
// Node: testGetAllUsers
// Node: andReturn
// Node: getResponse
// Node: getContentAsString
// Node: parseObject
// Node: testUpdateUser
// Node: toJSONString
// Node: contentType
// Node: content
// Node: testAddUser
// Node: post
// Node: testDeleteUser
// Node: delete
package adminuser.service;

import adminuser.dto.UserDto;
import edu.fudan.common.entity.User;
import edu.fudan.common.util.Response;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.*;
import org.springframework.web.client.RestTemplate;

import java.util.List;

@RunWith(JUnit4.class)
public class AdminUserServiceImplTest {

    @InjectMocks
    private AdminUserServiceImpl adminUserServiceImpl;

    @Mock
    private RestTemplate restTemplate;

    private HttpHeaders headers = new HttpHeaders();
    private HttpEntity requestEntity = new HttpEntity(headers);

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
    }

    @Test
    public void testGetAllUsers() {
        Response<List<User>> response = new Response<>(1, null, null);
        ResponseEntity<Response<List<User>>> re = new ResponseEntity<>(response, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                "http://ts-user-service:12342/api/v1/userservice/users",
                HttpMethod.GET,
                requestEntity,
                new ParameterizedTypeReference<Response<List<User>>>() {
                })).thenReturn(re);
        Response result = adminUserServiceImpl.getAllUsers(headers);
        Assert.assertEquals(new Response<>(1, null, null), result);
    }

    @Test
    public void testDeleteUser() {
        Response response = new Response<>(1, null, null);
        ResponseEntity<Response> re = new ResponseEntity<>(response, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                "http://ts-user-service:12342/api/v1/userservice/users" + "/" + "userId",
                HttpMethod.DELETE,
                requestEntity,
                Response.class)).thenReturn(re);
        Response result = adminUserServiceImpl.deleteUser("userId", headers);
        Assert.assertEquals(new Response<>(1, null, null), result);
    }

    @Test
    public void testUpdateUser() {
        UserDto userDto = new UserDto();
        HttpEntity requestEntity2 = new HttpEntity(userDto, headers);
        Response response = new Response<>(1, null, null);
        ResponseEntity<Response> re = new ResponseEntity<>(response, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                "http://ts-user-service:12342/api/v1/userservice/users",
                HttpMethod.PUT,
                requestEntity2,
                Response.class)).thenReturn(re);
        Response result = adminUserServiceImpl.updateUser(userDto, headers);
        Assert.assertEquals(new Response<>(1, null, null), result);
    }

    @Test
    public void testAddUser() {
        UserDto userDto = new UserDto();
        HttpEntity requestEntity2 = new HttpEntity(userDto, headers);
        Response<User> response = new Response<>(1, null, null);
        ResponseEntity<Response<User>> re = new ResponseEntity<>(response, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                "http://ts-user-service:12342/api/v1/userservice/users" + "/register",
                HttpMethod.POST,
                requestEntity2,
                new ParameterizedTypeReference<Response<User>>() {
                })).thenReturn(re);
        Response result = adminUserServiceImpl.addUser(userDto, headers);
        Assert.assertEquals(new Response<>(1, null, null), result);
    }

}


package waitorder;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;
import org.springframework.cloud.client.loadbalancer.LoadBalanced;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.EnableAspectJAutoProxy;
import org.springframework.integration.annotation.IntegrationComponentScan;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.web.client.RestTemplate;
import springfox.documentation.swagger2.annotations.EnableSwagger2;

@SpringBootApplication
@EnableAspectJAutoProxy(proxyTargetClass = true)
@EnableAsync
@IntegrationComponentScan
@EnableSwagger2
@EnableDiscoveryClient
public class WaitOrderApplication {

    public static void main(String[] args) {
        SpringApplication.run(WaitOrderApplication.class, args);
    }

    @LoadBalanced
    @Bean
    public RestTemplate restTemplate(RestTemplateBuilder builder) {
        return builder.build();
    }

}


package waitorder.service.Impl;

import java.util.Optional;
import edu.fudan.common.util.Response;
import org.junit.Before;
import org.junit.BeforeClass;
import org.junit.jupiter.api.Assertions;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.springframework.http.HttpHeaders;
import waitorder.entity.WaitListOrder;
import waitorder.repository.WaitListOrderRepository;


@RunWith(JUnit4.class)
public class WaitListOrderServiceImplTest {

    @InjectMocks
    private WaitListOrderServiceImpl waitListOrderServiceImpl;

    @Mock
    private WaitListOrderRepository repository;

    private HttpHeaders headers = new HttpHeaders();

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
    }

    @Test
    public void findOrderById() {

        Mockito.when(repository.findById(Mockito.any(String.class))).thenReturn(Optional.ofNullable(null));
        Response response=waitListOrderServiceImpl.findOrderById("id",headers);
        Assertions.assertEquals(new Response<>(0, "No Content by this id", null), response);
    }

    @Test
    public void getAllOrders() {
        Mockito.when(repository.findAll()).thenReturn(null);
        Response res = waitListOrderServiceImpl.getAllOrders(headers);
        Assertions.assertEquals(new Response<>(0,"No Content.",null),res);
    }


}

package auth;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;
import org.springframework.cloud.client.loadbalancer.LoadBalanced;
import org.springframework.context.annotation.Bean;
import org.springframework.web.client.RestTemplate;

/**
 * @author fdse
 */
@SpringBootApplication
@EnableDiscoveryClient
public class AuthApplication {
    public static void main(String[] args) {
        SpringApplication.run(AuthApplication.class, args);
    }

    @LoadBalanced
    @Bean
    public RestTemplate restTemplate(RestTemplateBuilder builder) {
        return builder.build();
    }
}


package auth.exception.handler;

import auth.exception.UserOperationException;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ControllerAdvice;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.ResponseBody;

/**
 * @author fdse
 */
@ControllerAdvice
public class GlobalExceptionHandler {
    @ExceptionHandler(UserOperationException.class)
    @ResponseBody
    public ResponseEntity<String> handleUserNotFoundException(UserOperationException e) {
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(e.getMessage());
    }
}


// Node: handleUserNotFoundException
// Node: body
package auth.controller;


import auth.dto.BasicAuthDto;
import auth.entity.User;
import auth.exception.UserOperationException;
import auth.service.TokenService;
import auth.service.UserService;
import edu.fudan.common.util.Response;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;

import org.springframework.http.HttpHeaders;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.UUID;

/**
 * @author fdse
 */
@RestController
@RequestMapping("/api/v1/users")
public class UserController {

    @Autowired
    private UserService userService;

    @Autowired
    private TokenService tokenService;

    private static final Logger logger = LoggerFactory.getLogger(UserController.class);

    @GetMapping("/hello")
    public Object getHello() {
        return "Hello";
    }

    @PostMapping("/login")
    public ResponseEntity<Response> getToken(@RequestBody BasicAuthDto dao , @RequestHeader HttpHeaders headers) {
        logger.info("Login request of username: {}", dao.getUsername());
        try {
            Response<?> res = tokenService.getToken(dao, headers);
            return ResponseEntity.ok(res);
        } catch (UserOperationException e) {
            logger.error("[getToken][tokenService.getToken error][UserOperationException, message: {}]", e.getMessage());
            return ResponseEntity.ok(new Response<>(0, "get token error", null));
        }
    }

    @GetMapping
    public ResponseEntity<List<User>> getAllUser(@RequestHeader HttpHeaders headers) {
        logger.info("[getAllUser][Get all users]");
        return ResponseEntity.ok().body(userService.getAllUser(headers));
    }

    @DeleteMapping("/{userId}")
    public ResponseEntity<Response> deleteUserById(@PathVariable String userId, @RequestHeader HttpHeaders headers) {
        logger.info("[deleteUserById][Delete user][userId: {}]", userId);
        return ResponseEntity.ok(userService.deleteByUserId(userId, headers));
    }

}


// Node: getAllUser
// Node: deleteUserById
// Node: deleteByUserId
package auth.service;

import auth.dto.AuthDto;
import auth.entity.User;
import edu.fudan.common.util.Response;
import org.springframework.http.HttpHeaders;

import java.util.List;
import java.util.UUID;

/**
 * @author fdse
 */
public interface UserService {

    /**
     * save user
     *
     * @param user user
     * @return user
     */
    User saveUser(User user);

    /**
     * get all users
     *
     * @param headers headers
     * @return List<User>
     */
    List<User> getAllUser(HttpHeaders headers);

    /**
     * create default auth user
     *
     * @param dto dto
     * @return user
     */
    User createDefaultAuthUser(AuthDto dto);

    /**
     * delete by user id
     *
     * @param userId user id
     * @param headers headers
     * @return Response
     */
    Response deleteByUserId(String userId, HttpHeaders headers);

}


// Node: repos/cloned_ms_repos/train-ticket/ts-auth-service/src/main/java/auth/service/UserService.java:UserService.<init>
// Node: saveUser
package auth.service.impl;

import auth.constant.AuthConstant;
import auth.constant.InfoConstant;
import auth.dto.AuthDto;
import auth.entity.User;
import auth.exception.UserOperationException;
import auth.repository.UserRepository;
import auth.service.UserService;
import edu.fudan.common.util.Response;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpHeaders;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.text.MessageFormat;
import java.util.*;

/**
 * @author fdse
 */
@Service
public class UserServiceImpl implements UserService {
    private static final Logger LOGGER = LoggerFactory.getLogger(UserServiceImpl.class);

    @Autowired
    private UserRepository userRepository;

    @Autowired
    protected PasswordEncoder passwordEncoder;

    @Override
    public User saveUser(User user) {
        return null;
    }

    @Override
    public List<User> getAllUser(HttpHeaders headers) {
        return (List<User>) userRepository.findAll();
    }

    /**
     * create  a user with default role of user
     *
     * @param dto
     * @return
     */
    @Override
    public User createDefaultAuthUser(AuthDto dto) {
        LOGGER.info("[createDefaultAuthUser][Register User Info][AuthDto name: {}]", dto.getUserName());
        User user = User.builder()
                .userId(dto.getUserId())
                .username(dto.getUserName())
                .password(passwordEncoder.encode(dto.getPassword()))
                .roles(new HashSet<>(Arrays.asList(AuthConstant.ROLE_USER)))
                .build();
        try {
            checkUserCreateInfo(user);
        } catch (UserOperationException e) {
            LOGGER.error("[createDefaultAuthUser][Create default auth user][UserOperationException][message: {}]", e.getMessage());
        }
        return userRepository.save(user);
    }

    @Override
    @Transactional
    public Response deleteByUserId(String userId, HttpHeaders headers) {
        LOGGER.info("[deleteByUserId][DELETE USER][user id: {}]", userId);
        userRepository.deleteByUserId(userId);
        return new Response(1, "DELETE USER SUCCESS", null);
    }

    /**
     * check Whether user info is empty
     *
     * @param user
     */
    private void checkUserCreateInfo(User user) throws UserOperationException {
        LOGGER.info("[checkUserCreateInfo][Check user create info][userId: {}, userName: {}]", user.getUserId(), user.getUsername());
        List<String> infos = new ArrayList<>();

        if (null == user.getUsername() || "".equals(user.getUsername())) {
            infos.add(MessageFormat.format(InfoConstant.PROPERTIES_CANNOT_BE_EMPTY_1, InfoConstant.USERNAME));
        }

        int passwordMaxLength = 6;
        if (null == user.getPassword()) {
            infos.add(MessageFormat.format(InfoConstant.PROPERTIES_CANNOT_BE_EMPTY_1, InfoConstant.PASSWORD));
        } else if (user.getPassword().length() < passwordMaxLength) {
            infos.add(MessageFormat.format(InfoConstant.PASSWORD_LEAST_CHAR_1, 6));
        }

        if (null == user.getRoles() || user.getRoles().isEmpty()) {
            infos.add(MessageFormat.format(InfoConstant.PROPERTIES_CANNOT_BE_EMPTY_1, InfoConstant.ROLES));
        }

        if (!infos.isEmpty()) {
            LOGGER.warn(infos.toString());
            throw new UserOperationException(infos.toString());
        }
    }

}


package auth.controller;

import auth.dto.BasicAuthDto;
import auth.entity.User;
import auth.service.TokenService;
import auth.service.UserService;
import com.alibaba.fastjson.JSONObject;
import edu.fudan.common.util.Response;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.springframework.http.*;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.request.MockMvcRequestBuilders;
import org.springframework.test.web.servlet.result.MockMvcResultMatchers;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

@RunWith(JUnit4.class)
public class UserControllerTest {

    @InjectMocks
    private UserController userController;

    @Mock
    private UserService userService;
    @Mock
    private TokenService tokenService;
    private MockMvc mockMvc;
    private Response response = new Response();

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
        mockMvc = MockMvcBuilders.standaloneSetup(userController).build();
    }

    @Test
    public void testGetHello() throws Exception {
        mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/users/hello"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andExpect(MockMvcResultMatchers.content().string("Hello"));
    }

    @Test
    public void testGetToken() throws Exception {
        BasicAuthDto dao = new BasicAuthDto();
        Mockito.when(tokenService.getToken(Mockito.any(BasicAuthDto.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(dao);
        String result = mockMvc.perform(MockMvcRequestBuilders.post("/api/v1/users/login").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testGetAllUser() throws Exception {
        List<User> userList = new ArrayList<>();
        Mockito.when(userService.getAllUser(Mockito.any(HttpHeaders.class))).thenReturn(userList);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/users"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(userList, JSONObject.parseObject(result, List.class));
    }

    @Test
    public void testDeleteUserById() throws Exception {
        UUID userId = UUID.randomUUID();
        Mockito.when(userService.deleteByUserId(Mockito.any(UUID.class).toString(), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.delete("/api/v1/users/" + userId.toString()))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

}


// Node: testGetHello
// Node: string
// Node: testGetToken
// Node: testGetAllUser
// Node: testDeleteUserById
package auth.controller;

import auth.dto.AuthDto;
import auth.service.UserService;
import com.alibaba.fastjson.JSONObject;
import edu.fudan.common.util.Response;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.request.MockMvcRequestBuilders;
import org.springframework.test.web.servlet.result.MockMvcResultMatchers;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;


@RunWith(JUnit4.class)
public class AuthControllerTest {

    @InjectMocks
    private AuthController authController;

    @Mock
    private UserService userService;
    private MockMvc mockMvc;

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
        mockMvc = MockMvcBuilders.standaloneSetup(authController).build();
    }

    @Test
    public void testGetHello() throws Exception {
        mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/auth/hello"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andExpect(MockMvcResultMatchers.content().string("hello"));
    }

    @Test
    public void testCreateDefaultUser() throws Exception {
        AuthDto authDto = new AuthDto();
        Mockito.when(userService.createDefaultAuthUser(Mockito.any(AuthDto.class))).thenReturn(null);
        String requestJson = JSONObject.toJSONString(authDto);
        String result = mockMvc.perform(MockMvcRequestBuilders.post("/api/v1/auth").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isCreated())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals("SUCCESS", JSONObject.parseObject(result, Response.class).getMsg());
    }

}


// Node: testCreateDefaultUser
// Node: AuthDto
// Node: isCreated
package auth.service;

import auth.dto.AuthDto;
import auth.entity.User;
import auth.repository.UserRepository;
import auth.service.impl.UserServiceImpl;
import edu.fudan.common.util.Response;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.springframework.http.HttpHeaders;
import org.springframework.security.crypto.password.PasswordEncoder;

import java.util.*;

@RunWith(JUnit4.class)
public class UserServiceImplTest {

    @InjectMocks
    private UserServiceImpl userServiceImpl;

    @Mock
    private UserRepository userRepository;
    @Mock
    protected PasswordEncoder passwordEncoder;

    private HttpHeaders headers = new HttpHeaders();

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
    }

    @Test
    public void testSaveUser() {
        User user = new User();
        Assert.assertEquals(null, userServiceImpl.saveUser(user));
    }

    @Test
    public void testGetAllUser() {
        List<User> userList = new ArrayList<>();
        userList.add(new User());
        Mockito.when(userRepository.findAll()).thenReturn(userList);
        Assert.assertEquals(userList, userServiceImpl.getAllUser(headers));
    }

    @Test
    public void testCreateDefaultAuthUser() {
        AuthDto dto = new AuthDto(UUID.randomUUID().toString(), "username", "password");
        User user = new User();
        Mockito.when(userRepository.save(user)).thenReturn(user);
        Mockito.when(passwordEncoder.encode(dto.getPassword())).thenReturn("password");
        Assert.assertEquals(null, userServiceImpl.createDefaultAuthUser(dto));
    }

    @Test
    public void testDeleteByUserId() {
        UUID userId = UUID.randomUUID();
        Mockito.doNothing().doThrow(new RuntimeException()).when(userRepository).deleteByUserId(userId.toString());
        Assert.assertEquals(new Response(1, "DELETE USER SUCCESS", null), userServiceImpl.deleteByUserId(userId.toString(), headers));
    }

}


package auth.service;

import auth.dto.BasicAuthDto;
import auth.entity.User;
import auth.exception.UserOperationException;
import auth.repository.UserRepository;
import auth.security.jwt.JWTProvider;
import auth.service.impl.TokenServiceImpl;
import edu.fudan.common.util.Response;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.springframework.http.*;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.web.client.RestTemplate;

import java.util.Optional;

@RunWith(JUnit4.class)
public class TokenServiceImplTest {

    @InjectMocks
    private TokenServiceImpl tokenServiceImpl;

    @Mock
    private RestTemplate restTemplate;

    @Mock
    private UserRepository userRepository;

    @Mock
    private JWTProvider jwtProvider;

    @Mock
    private AuthenticationManager authenticationManager;

    private HttpHeaders headers = new HttpHeaders();
    HttpEntity requestEntity = new HttpEntity(headers);

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
    }

    @Test
    public void testGetToken1() {
        BasicAuthDto dto = new BasicAuthDto(null, null, "verifyCode");
        ResponseEntity<Boolean> re = new ResponseEntity<>(false, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                "http://ts-verification-code-service:15678/api/v1/verifycode/verify/" + "verifyCode",
                HttpMethod.GET,
                requestEntity,
                Boolean.class)).thenReturn(re);
        Response result = tokenServiceImpl.getToken(dto, headers);
        Assert.assertEquals(new Response<>(0, "Verification failed.", null), result);
    }

    @Test
    public void testGetToken2() throws UserOperationException {
        BasicAuthDto dto = new BasicAuthDto("username", null, "");
        User user = new User();
        Optional<User> optionalUser = Optional.of(user);
        Mockito.when(authenticationManager.authenticate(Mockito.any(UsernamePasswordAuthenticationToken.class))).thenReturn(null);
        Mockito.when(userRepository.findByUsername("username")).thenReturn(optionalUser);
        Mockito.when(jwtProvider.createToken(user)).thenReturn("token");
        Response result = tokenServiceImpl.getToken(dto, headers);
        Assert.assertEquals("login success", result.getMsg());
    }

}


package edu.fudan.common.config;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import springfox.documentation.builders.ApiInfoBuilder;
import springfox.documentation.builders.PathSelectors;
import springfox.documentation.builders.RequestHandlerSelectors;
import springfox.documentation.service.ApiInfo;
import springfox.documentation.spi.DocumentationType;
import springfox.documentation.spring.web.plugins.Docket;

/**
 * @author fdse
 */
@Configuration
public class SwaggerConfig {

    @Value("${swagger.controllerPackage}")
    private String controllerPackagePath;

    private static final Logger LOGGER = LoggerFactory.getLogger(SwaggerConfig.class);

    @Bean
    public Docket createRestApi() {
        SwaggerConfig.LOGGER.info("[createRestApi][create][controllerPackagePath: {}]", controllerPackagePath);
        return new Docket(DocumentationType.SWAGGER_2)
                .apiInfo(apiInfo())
                .select().apis(RequestHandlerSelectors.basePackage(controllerPackagePath))
                .paths(PathSelectors.any())
                .build();
    }

    private ApiInfo apiInfo() {
        return new ApiInfoBuilder()
                .title("Springboot builds the API documentation with swagger")
                .description("Simple and elegant restful style")
                .termsOfServiceUrl("https://github.com/FudanSELab/train-ticket")
                .version("1.0")
                .build();
    }

}


// Node: createRestApi
// Node: Docket
// Node: apiInfo
// Node: select
// Node: apis
// Node: basePackage
// Node: paths
// Node: ApiInfoBuilder
// Node: title
// Node: description
// Node: termsOfServiceUrl
// Node: version
package edu.fudan.common.entity;

import edu.fudan.common.util.StringUtils;
import lombok.AllArgsConstructor;
import lombok.Data;

import javax.validation.Valid;
import javax.validation.constraints.NotNull;
import java.util.Date;

/**
 * @author fdse
 */
@Data
@AllArgsConstructor
public class TripInfo {
    @Valid
    @NotNull
    private String startPlace;

    @Valid
    @NotNull
    private String endPlace;

    @Valid
    @NotNull
    private String departureTime;

    public TripInfo(){
        //Default Constructor
        this.startPlace = "";
        this.endPlace = "";
        this.departureTime = "";
    }

    public String getStartPlace() {
        return StringUtils.String2Lower(this.startPlace);
    }

    public String getEndPlace() {
        return StringUtils.String2Lower(this.endPlace);
    }

//    public Date getDepartureTime(){
//        return StringUtils.String2Date(this.departureTime);
//    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-common/src/main/java/edu/fudan/common/entity/TripInfo.java:TripInfo.<init>
// Node: TripInfo
package plan;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;
import org.springframework.cloud.client.loadbalancer.LoadBalanced;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.EnableAspectJAutoProxy;
import org.springframework.integration.annotation.IntegrationComponentScan;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.web.client.RestTemplate;
import springfox.documentation.swagger2.annotations.EnableSwagger2;

/**
 * @author fdse
 */
@SpringBootApplication
@EnableAspectJAutoProxy(proxyTargetClass = true)
@EnableAsync
@IntegrationComponentScan
@EnableSwagger2
@EnableDiscoveryClient
public class RoutePlanApplication {

    public static void main(String[] args) {
        SpringApplication.run(RoutePlanApplication.class, args);
    }

    @LoadBalanced
    @Bean
    public RestTemplate restTemplate(RestTemplateBuilder builder) {
        return builder.build();
    }
}


package plan.controller;

import com.alibaba.fastjson.JSONObject;
import edu.fudan.common.util.Response;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.request.MockMvcRequestBuilders;
import org.springframework.test.web.servlet.result.MockMvcResultMatchers;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import edu.fudan.common.entity.RoutePlanInfo;
import plan.service.RoutePlanService;

@RunWith(JUnit4.class)
public class RoutePlanControllerTest {

    @InjectMocks
    private RoutePlanController adminTravelController;

    @Mock
    private RoutePlanService routePlanService;
    private MockMvc mockMvc;
    private Response response = new Response();

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
        mockMvc = MockMvcBuilders.standaloneSetup(adminTravelController).build();
    }

    @Test
    public void testHome() throws Exception {
        mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/routeplanservice/welcome"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andExpect(MockMvcResultMatchers.content().string("Welcome to [ RoutePlan Service ] !"));
    }

    @Test
    public void testGetCheapestRoutes() throws Exception {
        RoutePlanInfo info = new RoutePlanInfo();
        Mockito.when(routePlanService.searchCheapestResult(Mockito.any(RoutePlanInfo.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(info);
        String result = mockMvc.perform(MockMvcRequestBuilders.post("/api/v1/routeplanservice/routePlan/cheapestRoute").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testGetQuickestRoutes() throws Exception {
        RoutePlanInfo info = new RoutePlanInfo();
        Mockito.when(routePlanService.searchQuickestResult(Mockito.any(RoutePlanInfo.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(info);
        String result = mockMvc.perform(MockMvcRequestBuilders.post("/api/v1/routeplanservice/routePlan/quickestRoute").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testGetMinStopStations() throws Exception {
        RoutePlanInfo info = new RoutePlanInfo();
        Mockito.when(routePlanService.searchMinStopStations(Mockito.any(RoutePlanInfo.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(info);
        String result = mockMvc.perform(MockMvcRequestBuilders.post("/api/v1/routeplanservice/routePlan/minStopStations").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

}


// Node: testGetCheapestRoutes
// Node: testGetQuickestRoutes
// Node: testGetMinStopStations
package plan.service;

import edu.fudan.common.entity.Trip;
import edu.fudan.common.entity.TripResponse;
import edu.fudan.common.util.Response;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.*;
import org.springframework.web.client.RestTemplate;
import edu.fudan.common.entity.RoutePlanInfo;
import edu.fudan.common.entity.Route;

import java.util.ArrayList;
import java.util.Date;

@RunWith(JUnit4.class)
public class RoutePlanServiceImplTest {

    @InjectMocks
    private RoutePlanServiceImpl routePlanServiceImpl;

    @Mock
    private RestTemplate restTemplate;

    private HttpHeaders headers = new HttpHeaders();

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
    }

    @Test
    public void testSearchCheapestResult() {
        RoutePlanInfo info = new RoutePlanInfo("form_station", "to_station", "", 1);
        //mock getTripFromHighSpeedTravelServive() and getTripFromNormalTrainTravelService()
        ArrayList<TripResponse> tripResponses = new ArrayList<>();
        Response<ArrayList<TripResponse>> response1 = new Response<>(null, null, tripResponses);
        ResponseEntity<Response<ArrayList<TripResponse>>> re1 = new ResponseEntity<>(response1, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                Mockito.anyString(),
                Mockito.any(HttpMethod.class),
                Mockito.any(HttpEntity.class),
                Mockito.any(ParameterizedTypeReference.class)))
                .thenReturn(re1);
        Response result = routePlanServiceImpl.searchCheapestResult(info, headers);
        Assert.assertEquals(new Response<>(1, "Success", new ArrayList<>()), result);
    }

    @Test
    public void testSearchQuickestResult() {
        RoutePlanInfo info = new RoutePlanInfo("form_station", "to_station", "", 1);
        //mock getTripFromHighSpeedTravelServive() and getTripFromNormalTrainTravelService()
        ArrayList<TripResponse> tripResponses = new ArrayList<>();
        Response<ArrayList<TripResponse>> response1 = new Response<>(null, null, tripResponses);
        ResponseEntity<Response<ArrayList<TripResponse>>> re1 = new ResponseEntity<>(response1, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                Mockito.anyString(),
                Mockito.any(HttpMethod.class),
                Mockito.any(HttpEntity.class),
                Mockito.any(ParameterizedTypeReference.class)))
                .thenReturn(re1);
        Response result = routePlanServiceImpl.searchQuickestResult(info, headers);
        Assert.assertEquals(new Response<>(1, "Success", new ArrayList<>()), result);
    }

    @Test
    public void testSearchMinStopStations() {
        RoutePlanInfo info = new RoutePlanInfo("form_station", "to_station", "", 1);

        Response<String> response = new Response(null, null, "");
        ResponseEntity<Response<String>> re = new ResponseEntity<>(response, HttpStatus.OK);

        ArrayList<Route> routeArrayList = new ArrayList<>();
        Response<ArrayList<Route>> response2 = new Response<>(null, null, routeArrayList);
        ResponseEntity<Response<ArrayList<Route>>> re2 = new ResponseEntity<>(response2, HttpStatus.OK);

        ArrayList<ArrayList<Trip>> tripLists = new ArrayList<>();
        Response<ArrayList<ArrayList<Trip>>> response3 = new Response<>(null, null, tripLists);
        ResponseEntity<Response<ArrayList<ArrayList<Trip>>>> re3 = new ResponseEntity<>(response3, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                Mockito.anyString(),
                Mockito.any(HttpMethod.class),
                Mockito.any(HttpEntity.class),
                Mockito.any(ParameterizedTypeReference.class)))
                .thenReturn(re).thenReturn(re).thenReturn(re2).thenReturn(re3).thenReturn(re3);
        Response result = routePlanServiceImpl.searchMinStopStations(info, headers);
        Assert.assertEquals("Success.", result.getMsg());
    }

}


package adminroute;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;
import org.springframework.cloud.client.loadbalancer.LoadBalanced;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.EnableAspectJAutoProxy;
import org.springframework.integration.annotation.IntegrationComponentScan;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.web.client.RestTemplate;
import springfox.documentation.swagger2.annotations.EnableSwagger2;

/**
 * @author fdse
 */
@SpringBootApplication
@EnableAspectJAutoProxy(proxyTargetClass = true)
@EnableAsync
@IntegrationComponentScan
@EnableSwagger2
@EnableDiscoveryClient
public class AdminRouteApplication {
    public static void main(String[] args) {
        SpringApplication.run(AdminRouteApplication.class, args);
    }

    @LoadBalanced
    @Bean
    public RestTemplate restTemplate(RestTemplateBuilder builder) {
        return builder.build();
    }
}


// Node: getAllRoutes
// Node: deleteRoute
package adminroute.service;

import edu.fudan.common.entity.RouteInfo;
import edu.fudan.common.util.Response;
import org.springframework.http.HttpHeaders;

/**
 * @author fdse
 */
public interface AdminRouteService {

    /**
     * get all routes with headers
     *
     * @param headers headers
     * @return Response
     */
    Response getAllRoutes(HttpHeaders headers);

    /**
     * get all routes with headers
     *
     * @param request route information
     * @param headers headers
     * @return Response
     */
    Response createAndModifyRoute(RouteInfo request, HttpHeaders headers);

    /**
     * get all routes with headers
     *
     * @param routeId route id
     * @param headers headers
     * @return Response
     */
    Response deleteRoute(String routeId, HttpHeaders headers);
}


// Node: repos/cloned_ms_repos/train-ticket/ts-admin-route-service/src/main/java/adminroute/service/AdminRouteService.java:AdminRouteService.<init>
package adminroute.controller;

import edu.fudan.common.entity.RouteInfo;
import adminroute.service.AdminRouteService;
import com.alibaba.fastjson.JSONObject;
import edu.fudan.common.util.Response;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.springframework.http.*;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.request.MockMvcRequestBuilders;
import org.springframework.test.web.servlet.result.MockMvcResultMatchers;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

@RunWith(JUnit4.class)
public class AdminRouteControllerTest {

    @InjectMocks
    private AdminRouteController adminRouteController;

    @Mock
    private AdminRouteService adminRouteService;
    private MockMvc mockMvc;
    private Response response = new Response();

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
        mockMvc = MockMvcBuilders.standaloneSetup(adminRouteController).build();
    }

    @Test
    public void testHome() throws Exception {
        mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/adminrouteservice/welcome"))
                .andExpect(MockMvcResultMatchers.status().isOk());
    }

    @Test
    public void testGetAllRoutes() throws Exception {
        Mockito.when(adminRouteService.getAllRoutes(Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/adminrouteservice/adminroute"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testAddRoute() throws Exception {
        RouteInfo request = new RouteInfo();
        Mockito.when(adminRouteService.createAndModifyRoute(Mockito.any(RouteInfo.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(request);
        String result = mockMvc.perform(MockMvcRequestBuilders.post("/api/v1/adminrouteservice/adminroute").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testDeleteRoute() throws Exception {
        Mockito.when(adminRouteService.deleteRoute(Mockito.anyString(),Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.delete("/api/v1/adminrouteservice/adminroute/routeId"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

}


// Node: testGetAllRoutes
// Node: testAddRoute
// Node: RouteInfo
// Node: testDeleteRoute
package adminroute.service;

import edu.fudan.common.entity.Route;
import edu.fudan.common.entity.RouteInfo;
import edu.fudan.common.util.Response;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.*;
import org.springframework.web.client.RestTemplate;

@RunWith(JUnit4.class)
public class AdminRouteServiceImplTest {

    @InjectMocks
    private AdminRouteServiceImpl adminRouteServiceImpl;

    @Mock
    private RestTemplate restTemplate;

    private HttpHeaders headers = new HttpHeaders();
    private HttpEntity requestEntity = new HttpEntity(headers);
    private Response response = new Response();
    private ResponseEntity<Response> re = new ResponseEntity<>(response, HttpStatus.OK);

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
    }

    @Test
    public void testGetAllRoutes() {
        Mockito.when(restTemplate.exchange(
                "http://ts-route-service:11178/api/v1/routeservice/routes",
                HttpMethod.GET,
                requestEntity,
                Response.class)).thenReturn(re);
        Response result = adminRouteServiceImpl.getAllRoutes(headers);
        Assert.assertEquals(new Response<>(null, null, null), result);
    }

    @Test
    public void testCreateAndModifyRoute() {
        RouteInfo request = new RouteInfo();
        HttpEntity requestEntity2 = new HttpEntity(request, headers);
        ResponseEntity<Response<Route>> re2 = new ResponseEntity<>(response, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                "http://ts-route-service:11178/api/v1/routeservice/routes",
                HttpMethod.POST,
                requestEntity2,
                new ParameterizedTypeReference<Response<Route>>() {
                })).thenReturn(re2);
        Response result = adminRouteServiceImpl.createAndModifyRoute(request, headers);
        Assert.assertEquals(new Response<>(null, null, null), result);
    }

    @Test
    public void testDeleteRoute() {
        Mockito.when(restTemplate.exchange(
                "http://ts-route-service:11178/api/v1/routeservice/routes/" + "routeId",
                HttpMethod.DELETE,
                requestEntity,
                Response.class)).thenReturn(re);
        Response result = adminRouteServiceImpl.deleteRoute("routeId", headers);
        Assert.assertEquals(new Response<>(null, null, null), result);
    }

}


// Node: testCreateAndModifyRoute
package com.trainticket;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;
import org.springframework.cloud.client.loadbalancer.LoadBalanced;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.EnableAspectJAutoProxy;
import org.springframework.integration.annotation.IntegrationComponentScan;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.web.client.RestTemplate;
import springfox.documentation.swagger2.annotations.EnableSwagger2;

/**
 * @author fdse
 */
@SpringBootApplication
@EnableAspectJAutoProxy(proxyTargetClass = true)
@EnableAsync
@IntegrationComponentScan
@EnableSwagger2
@EnableDiscoveryClient
public class PaymentApplication {

	public static void main(String[] args) {
		SpringApplication.run(PaymentApplication.class, args);
	}

	@LoadBalanced
	@Bean
	public RestTemplate restTemplate(RestTemplateBuilder builder) {
		return builder.build();
	}
}


// Node: query
package com.trainticket.controller;

import com.alibaba.fastjson.JSONObject;
import com.trainticket.entity.Payment;
import com.trainticket.service.PaymentService;
import edu.fudan.common.util.Response;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.springframework.http.*;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.request.MockMvcRequestBuilders;
import org.springframework.test.web.servlet.result.MockMvcResultMatchers;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

@RunWith(JUnit4.class)
public class PaymentControllerTest {

    @InjectMocks
    private PaymentController paymentController;

    @Mock
    private PaymentService service;
    private MockMvc mockMvc;
    private Response response = new Response();

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
        mockMvc = MockMvcBuilders.standaloneSetup(paymentController).build();
    }

    @Test
    public void testHome() throws Exception {
        mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/paymentservice/welcome"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andExpect(MockMvcResultMatchers.content().string("Welcome to [ Payment Service ] !"));
    }

    @Test
    public void testPay() throws Exception {
        Payment info = new Payment();
        Mockito.when(service.pay(Mockito.any(Payment.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(info);
        String result = mockMvc.perform(MockMvcRequestBuilders.post("/api/v1/paymentservice/payment").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testAddMoney() throws Exception {
        Payment info = new Payment();
        Mockito.when(service.addMoney(Mockito.any(Payment.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(info);
        String result = mockMvc.perform(MockMvcRequestBuilders.post("/api/v1/paymentservice/payment/money").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testQuery() throws Exception {
        Mockito.when(service.query(Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/paymentservice/payment"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

}


// Node: testPay
// Node: testAddMoney
// Node: testQuery
package com.trainticket.service;

import com.trainticket.entity.Money;
import com.trainticket.entity.Payment;
import com.trainticket.repository.AddMoneyRepository;
import com.trainticket.repository.PaymentRepository;
import edu.fudan.common.util.Response;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.springframework.http.HttpHeaders;

import java.util.ArrayList;
import java.util.List;

@RunWith(JUnit4.class)
public class PaymentServiceImplTest {

    @InjectMocks
    private PaymentServiceImpl paymentServiceImpl;

    @Mock
    private PaymentRepository paymentRepository;

    @Mock
    private AddMoneyRepository addMoneyRepository;

    private HttpHeaders headers = new HttpHeaders();

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
    }

    @Test
    public void testPay1() {
        Payment info = new Payment();
        Mockito.when(paymentRepository.findByOrderId(Mockito.anyString())).thenReturn(null);
        Mockito.when(paymentRepository.save(Mockito.any(Payment.class))).thenReturn(null);
        Response result = paymentServiceImpl.pay(info, headers);
        Assert.assertEquals(new Response<>(1, "Pay Success", null), result);
    }

    @Test
    public void testPay2() {
        Payment info = new Payment();
        Mockito.when(paymentRepository.findByOrderId(Mockito.anyString())).thenReturn(info);
        Response result = paymentServiceImpl.pay(info, headers);
        Assert.assertEquals(new Response<>(0, "Pay Failed, order not found with order id", null), result);
    }

    @Test
    public void testAddMoney() {
        Payment info = new Payment();
        Mockito.when(addMoneyRepository.save(Mockito.any(Money.class))).thenReturn(null);
        Response result = paymentServiceImpl.addMoney(info, headers);
        Assert.assertEquals(new Response<>(1,"Add Money Success", null), result);
    }

    @Test
    public void testQuery1() {
        List<Payment> payments = new ArrayList<>();
        payments.add(new Payment());
        Mockito.when(paymentRepository.findAll()).thenReturn(payments);
        Response result = paymentServiceImpl.query(headers);
        Assert.assertEquals(new Response<>(1,"Query Success",  payments), result);
    }

    @Test
    public void testQuery2() {
        Mockito.when(paymentRepository.findAll()).thenReturn(null);
        Response result = paymentServiceImpl.query(headers);
        Assert.assertEquals(new Response<>(0, "No Content", null), result);
    }

    @Test
    public void testInitPayment1() {
        Payment payment = new Payment();
        Mockito.when(paymentRepository.findById(Mockito.anyString())).thenReturn(null);
        Mockito.when(paymentRepository.save(Mockito.any(Payment.class))).thenReturn(null);
        paymentServiceImpl.initPayment(payment, headers);
        Mockito.verify(paymentRepository, Mockito.times(1)).save(Mockito.any(Payment.class));
    }

    @Test
    public void testInitPayment2() {
        Payment payment = new Payment();
        Mockito.when(paymentRepository.findById(Mockito.anyString())).thenReturn(java.util.Optional.of(payment));
        Mockito.when(paymentRepository.save(Mockito.any(Payment.class))).thenReturn(null);
        paymentServiceImpl.initPayment(payment, headers);
        Mockito.verify(paymentRepository, Mockito.times(0)).save(Mockito.any(Payment.class));
    }

}


package price;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;
import org.springframework.cloud.client.loadbalancer.LoadBalanced;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.EnableAspectJAutoProxy;
import org.springframework.integration.annotation.IntegrationComponentScan;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.web.client.RestTemplate;
import springfox.documentation.swagger2.annotations.EnableSwagger2;

/**
 * @author fdse
 */
@SpringBootApplication
@EnableAspectJAutoProxy(proxyTargetClass = true)
@EnableAsync
@IntegrationComponentScan
@EnableSwagger2
@EnableDiscoveryClient
public class PriceApplication {

    public static void main(String[] args) {
        SpringApplication.run(PriceApplication.class, args);
    }

    @LoadBalanced
    @Bean
    public RestTemplate restTemplate(RestTemplateBuilder builder) {
        return builder.build();
    }
}

// Node: queryAll
// Node: deletePriceConfig
// Node: update
package price.service;

import edu.fudan.common.util.Response;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpHeaders;
import org.springframework.stereotype.Service;
import price.entity.PriceConfig;
import price.repository.PriceConfigRepository;

import java.util.*;


/**
 * @author fdse
 */
@Service
public class PriceServiceImpl implements PriceService {

    @Autowired(required=true)
    private PriceConfigRepository priceConfigRepository;

    private static final Logger LOGGER = LoggerFactory.getLogger(PriceServiceImpl.class);

    String noThatConfig = "No that config";

    @Override
    public Response createNewPriceConfig(PriceConfig createAndModifyPriceConfig, HttpHeaders headers) {
        PriceServiceImpl.LOGGER.info("[createNewPriceConfig]");
        PriceConfig priceConfig = null;
        // create
        if (createAndModifyPriceConfig.getId() == null || createAndModifyPriceConfig.getId().toString().length() < 10) {
            priceConfig = new PriceConfig();
            priceConfig.setId(UUID.randomUUID().toString());
            priceConfig.setBasicPriceRate(createAndModifyPriceConfig.getBasicPriceRate());
            priceConfig.setFirstClassPriceRate(createAndModifyPriceConfig.getFirstClassPriceRate());
            priceConfig.setRouteId(createAndModifyPriceConfig.getRouteId());
            priceConfig.setTrainType(createAndModifyPriceConfig.getTrainType());
            priceConfigRepository.save(priceConfig);
        } else {
            // modify
            Optional<PriceConfig> op = priceConfigRepository.findById(createAndModifyPriceConfig.getId());
            if (!op.isPresent()) {
                priceConfig = new PriceConfig();
                priceConfig.setId(createAndModifyPriceConfig.getId());
            }else{
                priceConfig = op.get();
            }
            priceConfig.setBasicPriceRate(createAndModifyPriceConfig.getBasicPriceRate());
            priceConfig.setFirstClassPriceRate(createAndModifyPriceConfig.getFirstClassPriceRate());
            priceConfig.setRouteId(createAndModifyPriceConfig.getRouteId());
            priceConfig.setTrainType(createAndModifyPriceConfig.getTrainType());
            priceConfigRepository.save(priceConfig);
        }
        return new Response<>(1, "Create success", priceConfig);
    }

    @Override
    public PriceConfig findById(String id, HttpHeaders headers) {
        PriceServiceImpl.LOGGER.info("[findById][ID: {}]", id);
        Optional<PriceConfig> op = priceConfigRepository.findById(UUID.fromString(id).toString());
        if(op.isPresent()){
            return op.get();
        }
        return null;
    }

    @Override
    public Response findByRouteIdAndTrainType(String routeId, String trainType, HttpHeaders headers) {
        PriceServiceImpl.LOGGER.info("[findByRouteIdAndTrainType][Route: {} , Train Type: {}]", routeId, trainType);
        PriceConfig priceConfig = priceConfigRepository.findByRouteIdAndTrainType(routeId, trainType);
        //PriceServiceImpl.LOGGER.info("[findByRouteIdAndTrainType]");

        if (priceConfig == null) {
            PriceServiceImpl.LOGGER.warn("[findByRouteIdAndTrainType][Find by route and train type warn][PricrConfig not found][RouteId: {}, TrainType: {}]",routeId,trainType);
            return new Response<>(0, noThatConfig, null);
        } else {
            return new Response<>(1, "Success", priceConfig);
        }
    }

    @Override
    public Response findByRouteIdsAndTrainTypes(List<String> ridsAndTts, HttpHeaders headers){
        List<String> routeIds = new ArrayList<>();
        List<String> trainTypes = new ArrayList<>();
        for(String rts: ridsAndTts){
            List<String> r_t  = Arrays.asList(rts.split(":"));
            routeIds.add(r_t.get(0));
            trainTypes.add(r_t.get(1));
        }
        List<PriceConfig> pcs = priceConfigRepository.findByRouteIdsAndTrainTypes(routeIds, trainTypes);
        Map<String, PriceConfig> pcMap = new HashMap<>();
        for(PriceConfig pc: pcs){
            String key = pc.getRouteId() + ":" + pc.getTrainType();
            if(ridsAndTts.contains(key)){
                pcMap.put(key, pc);
            }
        }
        if (pcMap == null) {
            PriceServiceImpl.LOGGER.warn("[findByRouteIdsAndTrainTypes][Find by routes and train types warn][PricrConfig not found][RouteIds: {}, TrainTypes: {}]",routeIds,trainTypes);
            return new Response<>(0, noThatConfig, null);
        } else {
            return new Response<>(1, "Success", pcMap);
        }
    }


    @Override
    public Response findAllPriceConfig(HttpHeaders headers) {
        List<PriceConfig> list = priceConfigRepository.findAll();
        if (list == null) {
            list = new ArrayList<>();
        }

        if (!list.isEmpty()) {
            PriceServiceImpl.LOGGER.warn("[findAllPriceConfig][Find all price config warn][{}]","No Content");
            return new Response<>(1, "Success", list);
        } else {
            return new Response<>(0, "No price config", null);
        }

    }

    @Override
    public Response deletePriceConfig(String pcId, HttpHeaders headers) {
        Optional<PriceConfig> op = priceConfigRepository.findById(pcId);
        if (!op.isPresent()) {
            PriceServiceImpl.LOGGER.error("[deletePriceConfig][Delete price config error][Price config not found][PriceConfigId: {}]",pcId);
            return new Response<>(0, noThatConfig, null);
        } else {
            PriceConfig pc = op.get();
            priceConfigRepository.delete(pc);
            return new Response<>(1, "Delete success", pc);
        }
    }

    @Override
    public Response updatePriceConfig(PriceConfig c, HttpHeaders headers) {
        Optional<PriceConfig> op = priceConfigRepository.findById(c.getId());
        if (!op.isPresent()) {
            PriceServiceImpl.LOGGER.error("[updatePriceConfig][Update price config error][Price config not found][PriceConfigId: {}]",c.getId());
            return new Response<>(0, noThatConfig, null);
        } else {
            PriceConfig priceConfig = op.get();
            priceConfig.setId(c.getId());
            priceConfig.setBasicPriceRate(c.getBasicPriceRate());
            priceConfig.setFirstClassPriceRate(c.getFirstClassPriceRate());
            priceConfig.setRouteId(c.getRouteId());
            priceConfig.setTrainType(c.getTrainType());
            priceConfigRepository.save(priceConfig);
            return new Response<>(1, "Update success", priceConfig);
        }
    }
}


package price.controller;

import com.alibaba.fastjson.JSONObject;
import edu.fudan.common.util.Response;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.springframework.http.*;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.request.MockMvcRequestBuilders;
import org.springframework.test.web.servlet.result.MockMvcResultMatchers;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import price.entity.PriceConfig;
import price.service.PriceService;

@RunWith(JUnit4.class)
public class PriceControllerTest {

    @InjectMocks
    private PriceController priceController;

    @Mock
    private PriceService service;
    private MockMvc mockMvc;
    private Response response = new Response();

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
        mockMvc = MockMvcBuilders.standaloneSetup(priceController).build();
    }

    @Test
    public void testHome() throws Exception {
        mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/priceservice/prices/welcome"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andExpect(MockMvcResultMatchers.content().string("Welcome to [ Price Service ] !"));
    }

    @Test
    public void testQuery() throws Exception {
        Mockito.when(service.findByRouteIdAndTrainType(Mockito.anyString(), Mockito.anyString(), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/priceservice/prices/route_id/train_type"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testQueryAll() throws Exception {
        Mockito.when(service.findAllPriceConfig(Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/priceservice/prices"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testCreate() throws Exception {
        PriceConfig info = new PriceConfig();
        Mockito.when(service.createNewPriceConfig(Mockito.any(PriceConfig.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(info);
        String result = mockMvc.perform(MockMvcRequestBuilders.post("/api/v1/priceservice/prices").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isCreated())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testDelete() throws Exception {
        PriceConfig info = new PriceConfig();
        Mockito.when(service.deletePriceConfig(Mockito.anyString(), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(info);
        String result = mockMvc.perform(MockMvcRequestBuilders.delete("/api/v1/priceservice/prices").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testUpdate() throws Exception {
        PriceConfig info = new PriceConfig();
        Mockito.when(service.updatePriceConfig(Mockito.any(PriceConfig.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(info);
        String result = mockMvc.perform(MockMvcRequestBuilders.put("/api/v1/priceservice/prices").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

}


// Node: testQueryAll
// Node: testCreate
// Node: testDelete
// Node: testUpdate
package price.service;

import edu.fudan.common.util.Response;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.springframework.http.HttpHeaders;
import price.entity.PriceConfig;
import price.repository.PriceConfigRepository;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

@RunWith(JUnit4.class)
public class PriceServiceImplTest {

    @InjectMocks
    private PriceServiceImpl priceServiceImpl;

    @Mock
    private PriceConfigRepository priceConfigRepository;

    private HttpHeaders headers = new HttpHeaders();

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
    }

    @Test
    public void testCreateNewPriceConfig1() {
        PriceConfig createAndModifyPriceConfig = new PriceConfig();
        Mockito.when(priceConfigRepository.save(Mockito.any(PriceConfig.class))).thenReturn(null);
        Response result = priceServiceImpl.createNewPriceConfig(createAndModifyPriceConfig, headers);
        Assert.assertNotNull(result.getData());
    }

    @Test
    public void testCreateNewPriceConfig2() {
        PriceConfig createAndModifyPriceConfig = new PriceConfig(UUID.randomUUID().toString(), "G", "G1255", 1.0, 2.0);
        Mockito.when(priceConfigRepository.findById(Mockito.any(UUID.class).toString())).thenReturn(null);
        Mockito.when(priceConfigRepository.save(Mockito.any(PriceConfig.class))).thenReturn(null);
        Response result = priceServiceImpl.createNewPriceConfig(createAndModifyPriceConfig, headers);
        Assert.assertEquals(new Response<>(1, "Create success", createAndModifyPriceConfig), result);
    }

    @Test
    public void testFindById() {
        Mockito.when(priceConfigRepository.findById(Mockito.any(UUID.class).toString())).thenReturn(null);
        PriceConfig result = priceServiceImpl.findById(UUID.randomUUID().toString(), headers);
        Assert.assertNull(result);
    }

    @Test
    public void testFindByRouteIdAndTrainType1() {
        Mockito.when(priceConfigRepository.findByRouteIdAndTrainType(Mockito.anyString(), Mockito.anyString())).thenReturn(null);
        Response result = priceServiceImpl.findByRouteIdAndTrainType("route_id", "train_type", headers);
        Assert.assertEquals(new Response<>(0, "No that config", null), result);
    }

    @Test
    public void testFindByRouteIdAndTrainType2() {
        PriceConfig priceConfig = new PriceConfig();
        Mockito.when(priceConfigRepository.findByRouteIdAndTrainType(Mockito.anyString(), Mockito.anyString())).thenReturn(priceConfig);
        Response result = priceServiceImpl.findByRouteIdAndTrainType("route_id", "train_type", headers);
        Assert.assertEquals(new Response<>(1, "Success", priceConfig), result);
    }

    @Test
    public void testFindAllPriceConfig1() {
        Mockito.when(priceConfigRepository.findAll()).thenReturn(null);
        Response result = priceServiceImpl.findAllPriceConfig(headers);
        Assert.assertEquals(new Response<>(0, "No price config", null), result);
    }

    @Test
    public void testFindAllPriceConfig2() {
        List<PriceConfig> list = new ArrayList<>();
        list.add(new PriceConfig());
        Mockito.when(priceConfigRepository.findAll()).thenReturn(list);
        Response result = priceServiceImpl.findAllPriceConfig(headers);
        Assert.assertEquals(new Response<>(1, "Success", list), result);
    }

    @Test
    public void testDeletePriceConfig1() {
        PriceConfig c = new PriceConfig();
        Mockito.when(priceConfigRepository.findById(Mockito.any(UUID.class).toString())).thenReturn(null);
        Response result = priceServiceImpl.deletePriceConfig(c.getId(), headers);
        Assert.assertEquals(new Response<>(0, "No that config", null), result);
    }

    @Test
    public void testDeletePriceConfig2() {
        PriceConfig c = new PriceConfig();
        Mockito.when(priceConfigRepository.findById(Mockito.any(UUID.class).toString()).get()).thenReturn(c);
        Mockito.doNothing().doThrow(new RuntimeException()).when(priceConfigRepository).delete(Mockito.any(PriceConfig.class));
        Response result = priceServiceImpl.deletePriceConfig(c.getId(), headers);
        Assert.assertEquals(new Response<>(1, "Delete success", c), result);
    }

    @Test
    public void testUpdatePriceConfig1() {
        PriceConfig c = new PriceConfig();
        Mockito.when(priceConfigRepository.findById(Mockito.any(UUID.class).toString())).thenReturn(null);
        Response result = priceServiceImpl.updatePriceConfig(c, headers);
        Assert.assertEquals(new Response<>(0, "No that config", null), result);
    }

    @Test
    public void testUpdatePriceConfig2() {
        PriceConfig c = new PriceConfig();
        Mockito.when(priceConfigRepository.findById(Mockito.any(UUID.class).toString()).get()).thenReturn(c);
        Mockito.when(priceConfigRepository.save(Mockito.any(PriceConfig.class))).thenReturn(null);
        Response result = priceServiceImpl.updatePriceConfig(c, headers);
        Assert.assertEquals(new Response<>(1, "Update success", c), result);
    }

}


package notification;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;
import org.springframework.cloud.client.loadbalancer.LoadBalanced;
import org.springframework.context.annotation.Bean;
import org.springframework.web.client.RestTemplate;
import springfox.documentation.swagger2.annotations.EnableSwagger2;

/**
 * @author fdse
 */
@SpringBootApplication
@EnableSwagger2
@EnableDiscoveryClient
public class NotificationApplication{
    public static void main(String[] args) {
        SpringApplication.run(NotificationApplication.class, args);
    }

    @LoadBalanced
    @Bean
    public RestTemplate restTemplate(RestTemplateBuilder builder) {
        return builder.build();
    }
}

package notification.controller;

import com.alibaba.fastjson.JSONObject;
import edu.fudan.common.util.Response;
import notification.entity.NotifyInfo;
import notification.service.NotificationService;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.request.MockMvcRequestBuilders;
import org.springframework.test.web.servlet.result.MockMvcResultMatchers;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

@RunWith(JUnit4.class)
public class NotificationControllerTest {

    @InjectMocks
    private NotificationController notificationController;

    @Mock
    private NotificationService service;
    private MockMvc mockMvc;

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
        mockMvc = MockMvcBuilders.standaloneSetup(notificationController).build();
    }

    @Test
    public void testHome() throws Exception {
        mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/notifyservice/welcome"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andExpect(MockMvcResultMatchers.content().string("Welcome to [ Notification Service ] !"));
    }

    @Test
    public void testPreserveSuccess() throws Exception {
        NotifyInfo info = new NotifyInfo();
        Mockito.when(service.preserveSuccess(Mockito.any(NotifyInfo.class), Mockito.any(HttpHeaders.class))).thenReturn(true);
        String requestJson = JSONObject.toJSONString(info);
        String result = mockMvc.perform(MockMvcRequestBuilders.post("/api/v1/notifyservice/notification/preserve_success").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertTrue(JSONObject.parseObject(result, Boolean.class));
    }

    @Test
    public void testOrderCreateSuccess() throws Exception {
        NotifyInfo info = new NotifyInfo();
        Mockito.when(service.orderCreateSuccess(Mockito.any(NotifyInfo.class), Mockito.any(HttpHeaders.class))).thenReturn(true);
        String requestJson = JSONObject.toJSONString(info);
        String result = mockMvc.perform(MockMvcRequestBuilders.post("/api/v1/notifyservice/notification/order_create_success").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertTrue(JSONObject.parseObject(result, Boolean.class));
    }

    @Test
    public void testOrderChangedSuccess() throws Exception {
        NotifyInfo info = new NotifyInfo();
        Mockito.when(service.orderChangedSuccess(Mockito.any(NotifyInfo.class), Mockito.any(HttpHeaders.class))).thenReturn(true);
        String requestJson = JSONObject.toJSONString(info);
        String result = mockMvc.perform(MockMvcRequestBuilders.post("/api/v1/notifyservice/notification/order_changed_success").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertTrue(JSONObject.parseObject(result, Boolean.class));
    }

    @Test
    public void testOrderCancelSuccess() throws Exception {
        NotifyInfo info = new NotifyInfo();
        Mockito.when(service.orderCancelSuccess(Mockito.any(NotifyInfo.class), Mockito.any(HttpHeaders.class))).thenReturn(true);
        String requestJson = JSONObject.toJSONString(info);
        String result = mockMvc.perform(MockMvcRequestBuilders.post("/api/v1/notifyservice/notification/order_cancel_success").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertTrue(JSONObject.parseObject(result, Boolean.class));
    }

}


// Node: testPreserveSuccess
// Node: testOrderCreateSuccess
// Node: testOrderChangedSuccess
// Node: testOrderCancelSuccess
package fdse.microservice;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;
import org.springframework.cloud.client.loadbalancer.LoadBalanced;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.EnableAspectJAutoProxy;
import org.springframework.integration.annotation.IntegrationComponentScan;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.web.client.RestTemplate;
import springfox.documentation.swagger2.annotations.EnableSwagger2;

/**
 * @author fdse
 */
@SpringBootApplication
@EnableAspectJAutoProxy(proxyTargetClass = true)
@EnableAsync
@IntegrationComponentScan
@EnableSwagger2
@EnableDiscoveryClient
public class BasicApplication {

	public static void main(String[] args) {
		SpringApplication.run(BasicApplication.class, args);
	}

	@LoadBalanced
	@Bean
	public RestTemplate restTemplate(RestTemplateBuilder builder) {
		return builder.build();
	}
}


package fdse.microservice.controller;

import com.alibaba.fastjson.JSONObject;
import edu.fudan.common.entity.Travel;
import edu.fudan.common.util.Response;
import fdse.microservice.service.BasicService;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.springframework.http.*;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.request.MockMvcRequestBuilders;
import org.springframework.test.web.servlet.result.MockMvcResultMatchers;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

@RunWith(JUnit4.class)
public class BasicControllerTest {

    @InjectMocks
    private BasicController basicController;

    @Mock
    private BasicService basicService;
    private MockMvc mockMvc;
    private Response response = new Response();

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
        mockMvc = MockMvcBuilders.standaloneSetup(basicController).build();
    }

    @Test
    public void testHome() throws Exception {
        mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/basicservice/welcome"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andExpect(MockMvcResultMatchers.content().string("Welcome to [ Basic Service ] !"));
    }

    @Test
    public void testQueryForTravel() throws Exception {
        Travel info = new Travel();
        Mockito.when(basicService.queryForTravel(Mockito.any(Travel.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(info);
        String result = mockMvc.perform(MockMvcRequestBuilders.post("/api/v1/basicservice/basic/travel").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testQueryForStationId() throws Exception {
        Mockito.when(basicService.queryForStationId(Mockito.anyString(), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/basicservice/basic/stationName"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

}


// Node: testQueryForStationId
package fdse.microservice.service;

import edu.fudan.common.entity.*;
import edu.fudan.common.util.Response;
import edu.fudan.common.util.StringUtils;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.springframework.http.*;
import org.springframework.web.client.RestTemplate;

import java.util.Date;
import java.util.UUID;

@RunWith(JUnit4.class)
public class BasicServiceImplTest {

    @InjectMocks
    private BasicServiceImpl basicServiceImpl;

    @Mock
    private RestTemplate restTemplate;

    private HttpHeaders headers = new HttpHeaders();
    private HttpEntity requestEntity = new HttpEntity(headers);

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
    }

    @Test
    public void testQueryForTravel() {
        Trip trip = new Trip();
        trip.setTripId(new TripId());
        trip.setRouteId("route_id");
        trip.setStartTime(StringUtils.Date2String(new Date()));
        trip.setEndTime(StringUtils.Date2String(new Date()));
        Travel info = new Travel();
        info.setTrip(trip);
        info.setStartPlace("starting_place");
        info.setEndPlace("end_place");
        info.setDepartureTime(StringUtils.Date2String(new Date()));
        Response response = new Response<>(1, null, null);
        ResponseEntity<Response> re = new ResponseEntity<>(response, HttpStatus.OK);
        //mock checkStationExists() and queryForStationId()
        Mockito.when(restTemplate.exchange(
                "http://ts-station-service:12345/api/v1/stationservice/stations/id/" + "starting_place",
                HttpMethod.GET,
                requestEntity,
                Response.class)).thenReturn(re);
        Mockito.when(restTemplate.exchange(
                "http://ts-station-service:12345/api/v1/stationservice/stations/id/" + "end_place",
                HttpMethod.GET,
                requestEntity,
                Response.class)).thenReturn(re);
        //mock queryTrainType()
        Mockito.when(restTemplate.exchange(
                "http://ts-train-service:14567/api/v1/trainservice/trains/" + "",
                HttpMethod.GET,
                requestEntity,
                Response.class)).thenReturn(re);
        //mock getRouteByRouteId()
        Mockito.when(restTemplate.exchange(
                "http://ts-route-service:11178/api/v1/routeservice/routes/" + "route_id",
                HttpMethod.GET,
                requestEntity,
                Response.class)).thenReturn(re);
        //mock queryPriceConfigByRouteIdAndTrainType()
        HttpEntity requestEntity2 = new HttpEntity(null, headers);
        Response response2 = new Response<>(1, null, new PriceConfig(UUID.randomUUID(), "", "", 1.0, 2.0));
        ResponseEntity<Response> re2 = new ResponseEntity<>(response2, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                "http://ts-price-service:16579/api/v1/priceservice/prices/" + "route_id" + "/" + "",
                HttpMethod.GET,
                requestEntity2,
                Response.class)).thenReturn(re2);

        Response result = basicServiceImpl.queryForTravel(info, headers);
        Assert.assertEquals("Train type doesn't exist", result.getMsg());
    }

    @Test
    public void testQueryForStationId() {
        Response response = new Response<>(1, null, null);
        ResponseEntity<Response> re = new ResponseEntity<>(response, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                "http://ts-station-service:12345/api/v1/stationservice/stations/id/" + "stationName",
                HttpMethod.GET,
                requestEntity,
                Response.class)).thenReturn(re);
        Response result = basicServiceImpl.queryForStationId("stationName", headers);
        Assert.assertEquals(new Response<>(1, null, null), result);
    }

    @Test
    public void testCheckStationExists() {
        Response response = new Response<>(1, null, null);
        ResponseEntity<Response> re = new ResponseEntity<>(response, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                "http://ts-station-service:12345/api/v1/stationservice/stations/id/" + "stationName",
                HttpMethod.GET,
                requestEntity,
                Response.class)).thenReturn(re);
        Boolean result = basicServiceImpl.checkStationExists("stationName", headers);
        Assert.assertTrue(result);
    }

    @Test
    public void testQueryTrainType() {
        Response response = new Response<>(1, null, null);
        ResponseEntity<Response> re = new ResponseEntity<>(response, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                "http://ts-train-service:14567/api/v1/trainservice/trains/byName/" + "trainTypeName",
                HttpMethod.GET,
                requestEntity,
                Response.class)).thenReturn(re);
        TrainType result = basicServiceImpl.queryTrainTypeByName("trainTypeId", headers);
        Assert.assertNull(result);
    }

}


package other;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;
import org.springframework.cloud.client.loadbalancer.LoadBalanced;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.EnableAspectJAutoProxy;
import org.springframework.integration.annotation.IntegrationComponentScan;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.web.client.RestTemplate;
import springfox.documentation.swagger2.annotations.EnableSwagger2;

/**
 * @author fdse
 */
@SpringBootApplication
@EnableAspectJAutoProxy(proxyTargetClass = true)
@EnableAsync
@IntegrationComponentScan
@EnableSwagger2
@EnableDiscoveryClient
public class OrderOtherApplication {

    public static void main(String[] args) {

        SpringApplication.run(OrderOtherApplication.class, args);
    }

    @LoadBalanced
    @Bean
    public RestTemplate restTemplate(RestTemplateBuilder builder) {
        return builder.build();
    }
}


package other.controller;

import com.alibaba.fastjson.JSONObject;
import edu.fudan.common.entity.Seat;
import edu.fudan.common.util.Response;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.springframework.http.*;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.request.MockMvcRequestBuilders;
import org.springframework.test.web.servlet.result.MockMvcResultMatchers;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import other.entity.Order;
import other.entity.QueryInfo;
import other.service.OrderOtherService;

import java.util.Date;

@RunWith(JUnit4.class)
public class OrderOtherControllerTest {

    @InjectMocks
    private OrderOtherController orderOtherController;

    @Mock
    private OrderOtherService orderService;
    private MockMvc mockMvc;
    private Response response = new Response();

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
        mockMvc = MockMvcBuilders.standaloneSetup(orderOtherController).build();
    }

    @Test
    public void testHome() throws Exception {
        mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/orderOtherService/welcome"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andExpect(MockMvcResultMatchers.content().string("Welcome to [ Order Other Service ] !"));
    }

    @Test
    public void testGetTicketListByDateAndTripId() throws Exception {
        Seat seatRequest = new Seat();
        Mockito.when(orderService.getSoldTickets(Mockito.any(Seat.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(seatRequest);
        String result = mockMvc.perform(MockMvcRequestBuilders.post("/api/v1/orderOtherService/orderOther/tickets").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testCreateNewOrder() throws Exception {
        Order createOrder = new Order();
        Mockito.when(orderService.create(Mockito.any(Order.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(createOrder);
        String result = mockMvc.perform(MockMvcRequestBuilders.post("/api/v1/orderOtherService/orderOther").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testAddCreateNewOrder() throws Exception {
        Order order = new Order();
        Mockito.when(orderService.addNewOrder(Mockito.any(Order.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(order);
        String result = mockMvc.perform(MockMvcRequestBuilders.post("/api/v1/orderOtherService/orderOther/admin").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testQueryOrders() throws Exception {
        QueryInfo qi = new QueryInfo();
        Mockito.when(orderService.queryOrders(Mockito.any(QueryInfo.class), Mockito.anyString(), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(qi);
        String result = mockMvc.perform(MockMvcRequestBuilders.post("/api/v1/orderOtherService/orderOther/query").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testQueryOrdersForRefresh() throws Exception {
        QueryInfo qi = new QueryInfo();
        Mockito.when(orderService.queryOrdersForRefresh(Mockito.any(QueryInfo.class), Mockito.anyString(), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(qi);
        String result = mockMvc.perform(MockMvcRequestBuilders.post("/api/v1/orderOtherService/orderOther/refresh").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testCalculateSoldTicket() throws Exception {
        Date travelDate = new Date();
        Mockito.when(orderService.queryAlreadySoldOrders(Mockito.any(Date.class), Mockito.anyString(), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/orderOtherService/orderOther/" + travelDate.toString() + "/train_number"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testGetOrderPrice() throws Exception {
        Mockito.when(orderService.getOrderPrice(Mockito.anyString(), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/orderOtherService/orderOther/price/order_id"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testPayOrder() throws Exception {
        Mockito.when(orderService.payOrder(Mockito.anyString(), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/orderOtherService/orderOther/orderPay/order_id"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testGetOrderById() throws Exception {
        Mockito.when(orderService.getOrderById(Mockito.anyString(), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/orderOtherService/orderOther/order_id"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testModifyOrder() throws Exception {
        Mockito.when(orderService.modifyOrder(Mockito.anyString(), Mockito.anyInt(), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/orderOtherService/orderOther/status/order_id/1"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testSecurityInfoCheck() throws Exception {
        Date checkDate = new Date();
        Mockito.when(orderService.checkSecurityAboutOrder(Mockito.any(Date.class), Mockito.anyString(), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/orderOtherService/orderOther/security/" + checkDate.toString() + "/account_id"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testSaveOrderInfo() throws Exception {
        Order orderInfo = new Order();
        Mockito.when(orderService.saveChanges(Mockito.any(Order.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(orderInfo);
        String result = mockMvc.perform(MockMvcRequestBuilders.put("/api/v1/orderOtherService/orderOther").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testUpdateOrder() throws Exception {
        Order order = new Order();
        Mockito.when(orderService.updateOrder(Mockito.any(Order.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(order);
        String result = mockMvc.perform(MockMvcRequestBuilders.put("/api/v1/orderOtherService/orderOther/admin").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testDeleteOrder() throws Exception {
        Mockito.when(orderService.deleteOrder(Mockito.anyString(), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.delete("/api/v1/orderOtherService/orderOther/order_id"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testFindAllOrder() throws Exception {
        Mockito.when(orderService.getAllOrders(Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/orderOtherService/orderOther"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

}


// Node: testGetTicketListByDateAndTripId
// Node: testCreateNewOrder
// Node: testAddCreateNewOrder
// Node: testQueryOrdersForRefresh
// Node: testCalculateSoldTicket
// Node: testGetOrderPrice
// Node: testPayOrder
// Node: testGetOrderById
// Node: testModifyOrder
// Node: anyInt
// Node: testSecurityInfoCheck
// Node: testSaveOrderInfo
// Node: testUpdateOrder
// Node: testDeleteOrder
// Node: testFindAllOrder
package other.service;

import edu.fudan.common.entity.OrderSecurity;;
import edu.fudan.common.entity.Seat;
import edu.fudan.common.util.Response;
import other.entity.Order;
import other.entity.OrderAlterInfo;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.*;
import org.springframework.web.client.RestTemplate;
import other.entity.*;
import other.repository.OrderOtherRepository;

import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.UUID;

import static org.mockito.internal.verification.VerificationModeFactory.times;

@RunWith(JUnit4.class)
public class OrderOtherServiceImplTest {

    @InjectMocks
    private OrderOtherServiceImpl orderOtherServiceImpl;

    @Mock
    private OrderOtherRepository orderOtherRepository;

    @Mock
    private RestTemplate restTemplate;

    private HttpHeaders headers = new HttpHeaders();

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
    }

    @Test
    public void testGetSoldTickets1() {
        Seat seatRequest = new Seat();
        ArrayList<Order> list = new ArrayList<>();
        list.add(new Order());
        Mockito.when(orderOtherRepository.findByTravelDateAndTrainNumber(Mockito.any(String.class), Mockito.anyString())).thenReturn(list);
        Response result = orderOtherServiceImpl.getSoldTickets(seatRequest, headers);
        Assert.assertEquals("Success", result.getMsg());
    }

    @Test
    public void testGetSoldTickets2() {
        Seat seatRequest = new Seat();
        Mockito.when(orderOtherRepository.findByTravelDateAndTrainNumber(Mockito.any(String.class), Mockito.anyString())).thenReturn(null);
        Response result = orderOtherServiceImpl.getSoldTickets(seatRequest, headers);
        Assert.assertEquals(new Response<>(0, "Seat is Null.", null), result);
    }

    @Test
    public void testFindOrderById1() {
        String id = UUID.randomUUID().toString();
        Mockito.when(orderOtherRepository.findById(Mockito.any(String.class))).thenReturn(null);
        Response result = orderOtherServiceImpl.findOrderById(id, headers);
        Assert.assertEquals(new Response<>(0, "No Content by this id", null), result);
    }

    @Test
    public void testFindOrderById2() {
        String id = UUID.randomUUID().toString();
        Order order = new Order();
        Mockito.when(orderOtherRepository.findById(Mockito.any(String.class)).get()).thenReturn(order);
        Response result = orderOtherServiceImpl.findOrderById(id, headers);
        Assert.assertEquals(new Response<>(1, "Success", order), result);
    }

    @Test
    public void testCreate1() {
        Order order = new Order();
        ArrayList<Order> accountOrders = new ArrayList<>();
        accountOrders.add(order);
        Mockito.when(orderOtherRepository.findByAccountId(Mockito.any(String.class))).thenReturn(accountOrders);
        Response result = orderOtherServiceImpl.create(order, headers);
        Assert.assertEquals(new Response<>(0, "Order already exist", order), result);
    }

    @Test
    public void testCreate2() {
        Order order = new Order();
        ArrayList<Order> accountOrders = new ArrayList<>();
        Mockito.when(orderOtherRepository.findByAccountId(Mockito.any(String.class))).thenReturn(accountOrders);
        Mockito.when(orderOtherRepository.save(Mockito.any(Order.class))).thenReturn(null);
        Response result = orderOtherServiceImpl.create(order, headers);
        Assert.assertEquals("Success", result.getMsg());
    }

    @Test
    public void testInitOrder1() {
        Order order = new Order();
        Mockito.when(orderOtherRepository.findById(Mockito.any(String.class))).thenReturn(null);
        Mockito.when(orderOtherRepository.save(Mockito.any(Order.class))).thenReturn(null);
        orderOtherServiceImpl.initOrder(order, headers);
        Mockito.verify(orderOtherRepository, times(1)).save(Mockito.any(Order.class));
    }

    @Test
    public void testInitOrder2() {
        Order order = new Order();
        Mockito.when(orderOtherRepository.findById(Mockito.any(String.class)).get()).thenReturn(order);
        Mockito.when(orderOtherRepository.save(Mockito.any(Order.class))).thenReturn(null);
        orderOtherServiceImpl.initOrder(order, headers);
        Mockito.verify(orderOtherRepository, times(0)).save(Mockito.any(Order.class));
    }

    @Test
    public void testAlterOrder1() {
        OrderAlterInfo oai = new OrderAlterInfo();
        Mockito.when(orderOtherRepository.findById(Mockito.any(String.class))).thenReturn(null);
        Response result = orderOtherServiceImpl.alterOrder(oai, headers);
        Assert.assertEquals(new Response<>(0, "Old Order Does Not Exists", null), result);
    }

    @Test
    public void testAlterOrder2() {
        OrderAlterInfo oai = new OrderAlterInfo(UUID.randomUUID().toString(), UUID.randomUUID().toString(), "login_token", new Order());
        Order order = new Order();
        Mockito.when(orderOtherRepository.findById(Mockito.any(String.class)).get()).thenReturn(order);
        Mockito.when(orderOtherRepository.save(Mockito.any(Order.class))).thenReturn(null);
        //mock create()
        ArrayList<Order> accountOrders = new ArrayList<>();
        Mockito.when(orderOtherRepository.findByAccountId(Mockito.any(String.class))).thenReturn(accountOrders);
        Response result = orderOtherServiceImpl.alterOrder(oai, headers);
        Assert.assertEquals("Alter Order Success", result.getMsg());
    }

    @Test
    public void testQueryOrders() {
        ArrayList<Order> list = new ArrayList<>();
        Order order = new Order();
        order.setStatus(1);
        list.add(order);
        Mockito.when(orderOtherRepository.findByAccountId(Mockito.any(String.class))).thenReturn(list);
        QueryInfo qi = new QueryInfo();
        qi.setEnableStateQuery(true);
        qi.setEnableBoughtDateQuery(false);
        qi.setEnableTravelDateQuery(false);
        qi.setState(1);
        Response result = orderOtherServiceImpl.queryOrders(qi, UUID.randomUUID().toString().toString(), headers);
        Assert.assertEquals(new Response<>(1, "Get order num", list), result);
    }

    @Test
    public void testQueryOrdersForRefresh() {
        ArrayList<Order> list = new ArrayList<>();
        Mockito.when(orderOtherRepository.findByAccountId(Mockito.any(String.class))).thenReturn(list);
        //mock queryForStationId()
        Response<List<String>> response = new Response<>();
        ResponseEntity<Response<List<String>>> re = new ResponseEntity<>(response, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                Mockito.anyString(),
                Mockito.any(HttpMethod.class),
                Mockito.any(HttpEntity.class),
                Mockito.any(ParameterizedTypeReference.class)
                )).thenReturn(re);
        QueryInfo qi = new QueryInfo();
        qi.setEnableStateQuery(false);
        qi.setEnableBoughtDateQuery(false);
        qi.setEnableTravelDateQuery(false);
        Response result = orderOtherServiceImpl.queryOrdersForRefresh(qi, UUID.randomUUID().toString().toString(), headers);
        Assert.assertEquals("Success", result.getMsg());
    }

    @Test
    public void testQueryForStationId() {
        List<String> ids = new ArrayList<>();
        HttpEntity requestEntity = new HttpEntity<>(ids, headers);
        Response<List<String>> response = new Response<>();
        ResponseEntity<Response<List<String>>> re = new ResponseEntity<>(response, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                "http://ts-station-service:12345/api/v1/stationservice/stations/namelist",
                HttpMethod.POST,
                requestEntity,
                new ParameterizedTypeReference<Response<List<String>>>() {
                })).thenReturn(re);
        List<String> result = orderOtherServiceImpl.queryForStationId(ids, headers);
        Assert.assertNull(result);
    }

    @Test
    public void testSaveChanges1() {
        Order order = new Order();
        Mockito.when(orderOtherRepository.findById(Mockito.any(String.class))).thenReturn(null);
        Response result = orderOtherServiceImpl.saveChanges(order, headers);
        Assert.assertEquals(new Response<>(0, "Order Not Found", null), result);
    }

    @Test
    public void testSaveChanges2() {
        Order order = new Order();
        Mockito.when(orderOtherRepository.findById(Mockito.any(String.class)).get()).thenReturn(order);
        Mockito.when(orderOtherRepository.save(Mockito.any(Order.class))).thenReturn(null);
        Response result = orderOtherServiceImpl.saveChanges(order, headers);
        Assert.assertEquals(new Response<>(1, "Success", order), result);
    }

    @Test
    public void testCancelOrder1() {
        Mockito.when(orderOtherRepository.findById(Mockito.any(String.class))).thenReturn(null);
        Response result = orderOtherServiceImpl.cancelOrder(UUID.randomUUID().toString(), UUID.randomUUID().toString(), headers);
        Assert.assertEquals(new Response<>(0, "Order Not Found", null), result);
    }

    @Test
    public void testCancelOrder2() {
        Order oldOrder = new Order();
        Mockito.when(orderOtherRepository.findById(Mockito.any(String.class)).get()).thenReturn(oldOrder);
        Mockito.when(orderOtherRepository.save(Mockito.any(Order.class))).thenReturn(null);
        Response result = orderOtherServiceImpl.cancelOrder(UUID.randomUUID().toString(), UUID.randomUUID().toString(), headers);
        Assert.assertEquals("Success", result.getMsg());
    }

    @Test
    public void testQueryAlreadySoldOrders() {
        ArrayList<Order> orders = new ArrayList<>();
        Mockito.when(orderOtherRepository.findByTravelDateAndTrainNumber(Mockito.any(String.class), Mockito.anyString())).thenReturn(orders);
        Response result = orderOtherServiceImpl.queryAlreadySoldOrders(new Date(), "G1234", headers);
        Assert.assertEquals("Success", result.getMsg());
    }

    @Test
    public void testGetAllOrders1() {
        Mockito.when(orderOtherRepository.findAll()).thenReturn(null);
        Response result = orderOtherServiceImpl.getAllOrders(headers);
        Assert.assertEquals(new Response<>(0, "No Content", null), result);
    }

    @Test
    public void testGetAllOrders2() {
        ArrayList<Order> orders = new ArrayList<>();
        Mockito.when(orderOtherRepository.findAll()).thenReturn(orders);
        Response result = orderOtherServiceImpl.getAllOrders(headers);
        Assert.assertEquals(new Response<>(1, "Success", orders), result);
    }

    @Test
    public void testModifyOrder1() {
        Mockito.when(orderOtherRepository.findById(Mockito.any(String.class))).thenReturn(null);
        Response result = orderOtherServiceImpl.modifyOrder(UUID.randomUUID().toString().toString(), 1, headers);
        Assert.assertEquals(new Response<>(0, "Order Not Found", null), result);
    }

    @Test
    public void testModifyOrder2() {
        Order order = new Order();
        Mockito.when(orderOtherRepository.findById(Mockito.any(String.class)).get()).thenReturn(order);
        Mockito.when(orderOtherRepository.save(Mockito.any(Order.class))).thenReturn(null);
        Response result = orderOtherServiceImpl.modifyOrder(UUID.randomUUID().toString().toString(), 1, headers);
        Assert.assertEquals("Success", result.getMsg());
    }

    @Test
    public void testGetOrderPrice1() {
        Mockito.when(orderOtherRepository.findById(Mockito.any(String.class))).thenReturn(null);
        Response result = orderOtherServiceImpl.getOrderPrice(UUID.randomUUID().toString().toString(), headers);
        Assert.assertEquals(new Response<>(0, "Order Not Found", "-1.0"), result);
    }

    @Test
    public void testGetOrderPrice2() {
        Order order = new Order();
        Mockito.when(orderOtherRepository.findById(Mockito.any(String.class)).get()).thenReturn(order);
        Response result = orderOtherServiceImpl.getOrderPrice(UUID.randomUUID().toString().toString(), headers);
        Assert.assertEquals(new Response<>(1, "Success", order.getPrice()), result);
    }

    @Test
    public void testPayOrder1() {
        Mockito.when(orderOtherRepository.findById(Mockito.any(String.class))).thenReturn(null);
        Response result = orderOtherServiceImpl.payOrder(UUID.randomUUID().toString().toString(), headers);
        Assert.assertEquals(new Response<>(0, "Order Not Found", null), result);
    }

    @Test
    public void testPayOrder2() {
        Order order = new Order();
        Mockito.when(orderOtherRepository.findById(Mockito.any(String.class)).get()).thenReturn(order);
        Mockito.when(orderOtherRepository.save(Mockito.any(Order.class))).thenReturn(null);
        Response result = orderOtherServiceImpl.payOrder(UUID.randomUUID().toString().toString(), headers);
        Assert.assertEquals("Success", result.getMsg());
    }

    @Test
    public void testGetOrderById1() {
        Mockito.when(orderOtherRepository.findById(Mockito.any(String.class))).thenReturn(null);
        Response result = orderOtherServiceImpl.getOrderById(UUID.randomUUID().toString().toString(), headers);
        Assert.assertEquals(new Response<>(0, "Order Not Found", null), result);
    }

    @Test
    public void testGetOrderById2() {
        Order order = new Order();
        Mockito.when(orderOtherRepository.findById(Mockito.any(String.class)).get()).thenReturn(order);
        Response result = orderOtherServiceImpl.getOrderById(UUID.randomUUID().toString().toString(), headers);
        Assert.assertEquals(new Response<>(1, "Success", order), result);
    }

    @Test
    public void testCheckSecurityAboutOrder() {
        ArrayList<Order> orders = new ArrayList<>();
        Mockito.when(orderOtherRepository.findByAccountId(Mockito.any(String.class))).thenReturn(orders);
        Response result = orderOtherServiceImpl.checkSecurityAboutOrder(new Date(), UUID.randomUUID().toString().toString(), headers);
        Assert.assertEquals(new Response<>(1, "Success", new OrderSecurity(0, 0)), result);
    }

    @Test
    public void testDeleteOrder1() {
        Mockito.when(orderOtherRepository.findById(Mockito.any(String.class))).thenReturn(null);
        Response result = orderOtherServiceImpl.deleteOrder(UUID.randomUUID().toString().toString(), headers);
        Assert.assertEquals(new Response<>(0, "Order Not Exist.", null), result);
    }

    @Test
    public void testDeleteOrder2() {
        Order order = new Order();
        String orderUuid = UUID.randomUUID().toString();
        Mockito.when(orderOtherRepository.findById(Mockito.any(String.class)).get()).thenReturn(order);
        Mockito.doNothing().doThrow(new RuntimeException()).when(orderOtherRepository).deleteById(Mockito.any(String.class));
        Response result = orderOtherServiceImpl.deleteOrder(orderUuid.toString(), headers);
        Assert.assertEquals(new Response<>(1, "Success", orderUuid), result);
    }

    @Test
    public void testAddNewOrder1() {
        Order order = new Order();
        ArrayList<Order> accountOrders = new ArrayList<>();
        accountOrders.add(order);
        Mockito.when(orderOtherRepository.findByAccountId(Mockito.any(String.class))).thenReturn(accountOrders);
        Response result = orderOtherServiceImpl.addNewOrder(order, headers);
        Assert.assertEquals(new Response<>(0, "Order already exist", null), result);
    }

    @Test
    public void testAddNewOrder2() {
        Order order = new Order();
        ArrayList<Order> accountOrders = new ArrayList<>();
        Mockito.when(orderOtherRepository.findByAccountId(Mockito.any(String.class))).thenReturn(accountOrders);
        Mockito.when(orderOtherRepository.save(Mockito.any(Order.class))).thenReturn(null);
        Response result = orderOtherServiceImpl.addNewOrder(order, headers);
        Assert.assertEquals("Success", result.getMsg());
    }

    @Test
    public void testUpdateOrder1() {
        Order order = new Order();
        Mockito.when(orderOtherRepository.findById(Mockito.any(String.class))).thenReturn(null);
        Response result = orderOtherServiceImpl.updateOrder(order, headers);
        Assert.assertEquals(new Response<>(0, "Order Not Found", null), result);
    }

    @Test
    public void testUpdateOrder2() {
        Order order = new Order();
        Mockito.when(orderOtherRepository.findById(Mockito.any(String.class)).get()).thenReturn(order);
        Mockito.when(orderOtherRepository.save(Mockito.any(Order.class))).thenReturn(null);
        Response result = orderOtherServiceImpl.updateOrder(order, headers);
        Assert.assertEquals("Success", result.getMsg());
    }

}


package delivery;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;
import org.springframework.cloud.client.loadbalancer.LoadBalanced;
import org.springframework.context.annotation.Bean;
import org.springframework.web.client.RestTemplate;
import springfox.documentation.swagger2.annotations.EnableSwagger2;


/**
 * @author humbertzhang
 */
@SpringBootApplication
@EnableSwagger2
@EnableDiscoveryClient
public class DeliveryApplication {

    public static void main(String[] args) {
        SpringApplication.run(DeliveryApplication.class, args);
    }

    @LoadBalanced
    @Bean
    public RestTemplate restTemplate(RestTemplateBuilder builder) {
        return builder.build();
    }
}


package assurance;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;
import org.springframework.cloud.client.loadbalancer.LoadBalanced;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.EnableAspectJAutoProxy;
import org.springframework.integration.annotation.IntegrationComponentScan;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.web.client.RestTemplate;
import springfox.documentation.swagger2.annotations.EnableSwagger2;

/**
 * @author fdse
 */
@SpringBootApplication
@EnableAspectJAutoProxy(proxyTargetClass = true)
@EnableAsync
@IntegrationComponentScan
@EnableSwagger2
@EnableDiscoveryClient
public class AssuranceApplication {

    public static void main(String[] args) {
        SpringApplication.run(AssuranceApplication.class, args);
    }

    @LoadBalanced
    @Bean
    public RestTemplate restTemplate(RestTemplateBuilder builder) {
        return builder.build();
    }
}


package assurance.controller;

import assurance.service.AssuranceService;
import com.alibaba.fastjson.JSONObject;
import edu.fudan.common.util.Response;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.request.MockMvcRequestBuilders;
import org.springframework.test.web.servlet.result.MockMvcResultMatchers;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

import java.util.UUID;

@RunWith(JUnit4.class)
public class AssuranceControllerTest {

    @InjectMocks
    private AssuranceController assuranceController;

    @Mock
    private AssuranceService assuranceService;
    private MockMvc mockMvc;
    private Response response = new Response();

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
        mockMvc = MockMvcBuilders.standaloneSetup(assuranceController).build();
    }

    @Test
    public void testHome() throws Exception {
        mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/assuranceservice/welcome"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andExpect(MockMvcResultMatchers.content().string("Welcome to [ Assurance Service ] !"));
    }

    @Test
    public void testGetAllAssurances() throws Exception {
        Mockito.when(assuranceService.getAllAssurances(Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/assuranceservice/assurances"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testGetAllAssuranceType() throws Exception {
        Mockito.when(assuranceService.getAllAssuranceTypes(Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/assuranceservice/assurances/types"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testDeleteAssurance() throws Exception {
        UUID assuranceId = UUID.randomUUID();
        Mockito.when(assuranceService.deleteById(Mockito.any(UUID.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.delete("/api/v1/assuranceservice/assurances/assuranceid/" + assuranceId.toString()))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testDeleteAssuranceByOrderId() throws Exception {
        UUID orderId = UUID.randomUUID();
        Mockito.when(assuranceService.deleteByOrderId(Mockito.any(UUID.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.delete("/api/v1/assuranceservice/assurances/orderid/" + orderId.toString()))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testModifyAssurance() throws Exception {
        Mockito.when(assuranceService.modify(Mockito.anyString(), Mockito.anyString(), Mockito.anyInt(), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.patch("/api/v1/assuranceservice/assurances/assurance_id/order_id/1"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testCreateNewAssurance() throws Exception {
        Mockito.when(assuranceService.create(Mockito.anyInt(), Mockito.anyString(), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/assuranceservice/assurances/1/order_id"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testGetAssuranceById() throws Exception {
        UUID assuranceId = UUID.randomUUID();
        Mockito.when(assuranceService.findAssuranceById(Mockito.any(UUID.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/assuranceservice/assurances/assuranceid/" + assuranceId.toString()))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testFindAssuranceByOrderId() throws Exception {
        UUID orderId = UUID.randomUUID();
        Mockito.when(assuranceService.findAssuranceByOrderId(Mockito.any(UUID.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/assuranceservice/assurance/orderid/" + orderId.toString()))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

}


// Node: testGetAllAssurances
// Node: testGetAllAssuranceType
// Node: testDeleteAssurance
// Node: testDeleteAssuranceByOrderId
// Node: testModifyAssurance
// Node: patch
// Node: testCreateNewAssurance
// Node: testGetAssuranceById
// Node: testFindAssuranceByOrderId
package assurance.service;

import assurance.entity.Assurance;
import assurance.entity.AssuranceType;
import assurance.entity.AssuranceTypeBean;
import assurance.entity.PlainAssurance;
import assurance.repository.AssuranceRepository;
import edu.fudan.common.util.Response;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.springframework.http.HttpHeaders;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

@RunWith(JUnit4.class)
public class AssuranceServiceImplTest {

    @InjectMocks
    private AssuranceServiceImpl assuranceServiceImpl;

    @Mock
    private AssuranceRepository assuranceRepository;

    private HttpHeaders headers = new HttpHeaders();

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
    }

    @Test
    public void testFindAssuranceById1() {
        UUID id = UUID.randomUUID();
        Mockito.when(assuranceRepository.findById(id.toString())).thenReturn(null);
        Response result = assuranceServiceImpl.findAssuranceById(id, headers);
        Assert.assertEquals(new Response<>(0, "No Content by this id", null), result);
    }

    @Test
    public void testFindAssuranceById2() {
        UUID id = UUID.randomUUID();
        Assurance assurance = new Assurance(id.toString(), null, null);
        Mockito.when(assuranceRepository.findById(id.toString())).thenReturn(java.util.Optional.of(assurance));
        Response result = assuranceServiceImpl.findAssuranceById(id, headers);
        Assert.assertEquals(new Response<>(1, "Find Assurance Success", java.util.Optional.of(assurance)), result);
    }

    @Test
    public void testFindAssuranceByOrderId1() {
        UUID orderId = UUID.randomUUID();
        Mockito.when(assuranceRepository.findByOrderId(orderId.toString())).thenReturn(null);
        Response result = assuranceServiceImpl.findAssuranceByOrderId(orderId, headers);
        Assert.assertEquals(new Response<>(0, "No Content by this orderId", null), result);
    }

    @Test
    public void testFindAssuranceByOrderId2() {
        UUID orderId = UUID.randomUUID();
        Assurance assurance = new Assurance(null, orderId.toString(), null);
        Mockito.when(assuranceRepository.findByOrderId(orderId.toString())).thenReturn(assurance);
        Response result = assuranceServiceImpl.findAssuranceByOrderId(orderId, headers);
        Assert.assertEquals(new Response<>(1, "Find Assurance Success", assurance), result);
    }

    @Test
    public void testCreate1() {
        UUID orderId = UUID.randomUUID();
        Assurance assurance = new Assurance();
        Mockito.when(assuranceRepository.findByOrderId(orderId.toString())).thenReturn(assurance);
        Response result = assuranceServiceImpl.create(0, orderId.toString(), headers);
        Assert.assertEquals(new Response<>(0, "Fail.Assurance already exists", null), result);
    }

    @Test
    public void tesCreate2() {
        UUID orderId = UUID.randomUUID();
        Mockito.when(assuranceRepository.findByOrderId(orderId.toString())).thenReturn(null);
        Response result = assuranceServiceImpl.create(0, orderId.toString(), headers);
        Assert.assertEquals(new Response<>(0, "Fail.Assurance type doesn't exist", null), result);
    }

    @Test
    public void testCreate3() {
        UUID orderId = UUID.randomUUID();
        Mockito.when(assuranceRepository.findByOrderId(orderId.toString())).thenReturn(null);
        Mockito.when(assuranceRepository.save(Mockito.any(Assurance.class))).thenReturn(null);
        Response result = assuranceServiceImpl.create(1, orderId.toString(), headers);
        Assert.assertNotNull(result);
    }

    @Test
    public void testDeleteById1() {
        UUID assuranceId = UUID.randomUUID();
        Mockito.doNothing().doThrow(new RuntimeException()).when(assuranceRepository).deleteById(assuranceId.toString());
        Mockito.when(assuranceRepository.findById(assuranceId.toString())).thenReturn(null);
        Response result = assuranceServiceImpl.deleteById(assuranceId, headers);
        Assert.assertEquals(new Response<>(1, "Delete Success with Assurance id", null), result);
    }

    @Test
    public void testDeleteById2() {
        UUID assuranceId = UUID.randomUUID();
        Mockito.doNothing().doThrow(new RuntimeException()).when(assuranceRepository).deleteById(assuranceId.toString());
        Assurance assurance = new Assurance();
        Mockito.when(assuranceRepository.findById(assuranceId.toString())).thenReturn(java.util.Optional.of(assurance));
        Response result = assuranceServiceImpl.deleteById(assuranceId, headers);
        Assert.assertEquals(new Response<>(0, "Fail.Assurance not clear", assuranceId), result);
    }

    @Test
    public void testDeleteByOrderId1() {
        UUID orderId = UUID.randomUUID();
        Mockito.doNothing().doThrow(new RuntimeException()).when(assuranceRepository).removeAssuranceByOrderId(orderId.toString());
        Mockito.when(assuranceRepository.findByOrderId(orderId.toString())).thenReturn(null);
        Response result = assuranceServiceImpl.deleteByOrderId(orderId, headers);
        Assert.assertEquals(new Response<>(1, "Delete Success with Order Id", null), result);
    }

    @Test
    public void testDeleteByOrderId2() {
        UUID orderId = UUID.randomUUID();
        Mockito.doNothing().doThrow(new RuntimeException()).when(assuranceRepository).removeAssuranceByOrderId(orderId.toString());
        Assurance assurance = new Assurance();
        Mockito.when(assuranceRepository.findByOrderId(orderId.toString())).thenReturn(assurance);
        Response result = assuranceServiceImpl.deleteByOrderId(orderId, headers);
        Assert.assertEquals(new Response<>(0, "Fail.Assurance not clear", orderId), result);
    }

    @Test
    public void testModify2() {
        UUID assuranceId = UUID.randomUUID();
        Assurance assurance = new Assurance(null, null, null);
        Mockito.when(assuranceRepository.findById(assuranceId.toString())).thenReturn(java.util.Optional.of(assurance));
        Mockito.when(assuranceRepository.save(assurance)).thenReturn(null);
        Response result = assuranceServiceImpl.modify(assuranceId.toString(), "orderId", 1, headers);
        Assert.assertEquals(new Response<>(1, "Modify Success", new Assurance(null, null, AssuranceType.TRAFFIC_ACCIDENT)), result);
    }

    @Test
    public void testModify3() {
        UUID assuranceId = UUID.randomUUID();
        Assurance assurance = new Assurance(null, null, null);
        Mockito.when(assuranceRepository.findById(assuranceId.toString())).thenReturn(java.util.Optional.of(assurance));
        Mockito.when(assuranceRepository.save(assurance)).thenReturn(null);
        Response result = assuranceServiceImpl.modify(assuranceId.toString(), "orderId", 0, headers);
        Assert.assertEquals(new Response<>(0, "Assurance Type not exist", null), result);
    }

    @Test
    public void testGetAllAssurances1() {
        ArrayList<Assurance> assuranceList = new ArrayList<>();
        assuranceList.add(new Assurance(null, null, AssuranceType.TRAFFIC_ACCIDENT));
        ArrayList<PlainAssurance> plainAssuranceList = new ArrayList<>();
        plainAssuranceList.add(new PlainAssurance(null, null, 1, "Traffic Accident Assurance", 3.0));
        Mockito.when(assuranceRepository.findAll()).thenReturn(assuranceList);
        Response result = assuranceServiceImpl.getAllAssurances(headers);
        Assert.assertEquals(new Response<>(1, "Success", plainAssuranceList), result);
    }

    @Test
    public void testGetAllAssurances2() {
        Mockito.when(assuranceRepository.findAll()).thenReturn(null);
        Response result = assuranceServiceImpl.getAllAssurances(headers);
        Assert.assertEquals(new Response<>(0, "No Content, Assurance is empty", null), result);
    }

    @Test
    public void testGetAllAssuranceTypes() {
        List<AssuranceTypeBean> assuranceTypeBeanList = new ArrayList<>();
        AssuranceTypeBean assuranceTypeBean = new AssuranceTypeBean(1, "Traffic Accident Assurance", 3.0);
        assuranceTypeBeanList.add(assuranceTypeBean);
        Response result = assuranceServiceImpl.getAllAssuranceTypes(headers);
        Assert.assertEquals(new Response<>(1, "Find All Assurance", assuranceTypeBeanList), result);
    }

}


package adminorder;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;
import org.springframework.cloud.client.loadbalancer.LoadBalanced;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.EnableAspectJAutoProxy;
import org.springframework.integration.annotation.IntegrationComponentScan;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.web.client.RestTemplate;
import springfox.documentation.swagger2.annotations.EnableSwagger2;

/**
 * @author fdse
 */
@SpringBootApplication
@EnableAspectJAutoProxy(proxyTargetClass = true)
@EnableAsync
@IntegrationComponentScan
@EnableSwagger2
@EnableDiscoveryClient
public class AdminOrderApplication {
    public static void main(String[] args) {
        SpringApplication.run(AdminOrderApplication.class, args);
    }

    @LoadBalanced
    @Bean
    public RestTemplate restTemplate(RestTemplateBuilder builder) {
        return builder.build();
    }
}


package adminorder.controller;

import adminorder.service.AdminOrderService;
import com.alibaba.fastjson.JSONObject;
import edu.fudan.common.util.Response;
import edu.fudan.common.entity.*;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.springframework.http.*;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.request.MockMvcRequestBuilders;
import org.springframework.test.web.servlet.result.MockMvcResultMatchers;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

@RunWith(JUnit4.class)
public class AdminOrderControllerTest {

    @InjectMocks
    private AdminOrderController adminOrderController;

    @Mock
    private AdminOrderService adminOrderService;
    private MockMvc mockMvc;

    private Response response = new Response();

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
        mockMvc = MockMvcBuilders.standaloneSetup(adminOrderController).build();
    }

    @Test
    public void testHome() throws Exception {
        mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/adminorderservice/welcome"))
                .andExpect(MockMvcResultMatchers.status().isOk());
    }

    @Test
    public void testGetAllOrders() throws Exception {
        Mockito.when(adminOrderService.getAllOrders(Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/adminorderservice/adminorder"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testAddOrder() throws Exception {
        Order order = new Order(null, null, null, null, null, null, 0, null, "G", 0, 0, null, null, null, 0, null, null);
        Mockito.when(adminOrderService.addOrder(Mockito.any(Order.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(order);
        String result = mockMvc.perform(MockMvcRequestBuilders.post("/api/v1/adminorderservice/adminorder").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testUpdateOrder() throws Exception {
        Order order = new Order(null, null, null, null, null, null, 0, null, "G", 0, 0, null, null, null, 0, null, null);
        Mockito.when(adminOrderService.updateOrder(Mockito.any(Order.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(order);
        String result = mockMvc.perform(MockMvcRequestBuilders.put("/api/v1/adminorderservice/adminorder").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testDeleteOrder() throws Exception {
        Mockito.when(adminOrderService.deleteOrder(Mockito.anyString(), Mockito.anyString(), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.delete("/api/v1/adminorderservice/adminorder/orderId/trainNumber"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }
}


// Node: testGetAllOrders
// Node: testAddOrder
package adminorder.service;

import edu.fudan.common.util.Response;
import edu.fudan.common.entity.*;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.*;
import org.springframework.web.client.RestTemplate;

import java.util.ArrayList;

@RunWith(JUnit4.class)
public class AdminOrderServiceImplTest {

    @InjectMocks
    private AdminOrderServiceImpl adminOrderService;

    @Mock
    private RestTemplate restTemplate;

    private HttpHeaders headers = new HttpHeaders();
    private HttpEntity requestEntity = new HttpEntity(headers);

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
    }

    @Test
    public void testGetAllOrders1() {
        Response<ArrayList<Order>> response = new Response<>(0, null, null);
        ResponseEntity<Response<ArrayList<Order>>> re = new ResponseEntity<>(response, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                "http://ts-order-service:12031/api/v1/orderservice/order",
                HttpMethod.GET,
                requestEntity,
                new ParameterizedTypeReference<Response<ArrayList<Order>>>() {
                })).thenReturn(re);
        Mockito.when(restTemplate.exchange(
                "http://ts-order-other-service:12032/api/v1/orderOtherService/orderOther",
                HttpMethod.GET,
                requestEntity,
                new ParameterizedTypeReference<Response<ArrayList<Order>>>() {
                })).thenReturn(re);
        Response result = adminOrderService.getAllOrders(headers);
        Assert.assertEquals(new Response<>(1, "Get the orders successfully!", new ArrayList<>()), result);
    }

    @Test
    public void testGetAllOrders2() {
        ArrayList<Order> orders = new ArrayList<>();
        orders.add(new Order());
        Response<ArrayList<Order>> response = new Response<>(1, null, orders);
        ResponseEntity<Response<ArrayList<Order>>> re = new ResponseEntity<>(response, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                "http://ts-order-service:12031/api/v1/orderservice/order",
                HttpMethod.GET,
                requestEntity,
                new ParameterizedTypeReference<Response<ArrayList<Order>>>() {
                })).thenReturn(re);
        Mockito.when(restTemplate.exchange(
                "http://ts-order-other-service:12032/api/v1/orderOtherService/orderOther",
                HttpMethod.GET,
                requestEntity,
                new ParameterizedTypeReference<Response<ArrayList<Order>>>() {
                })).thenReturn(re);
        Response result = adminOrderService.getAllOrders(headers);
        Assert.assertNotNull(result);
    }

    @Test
    public void testDeleteOrder1() {
        Response response = new Response();
        ResponseEntity<Response> re = new ResponseEntity<>(response, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                "http://ts-order-service:12031/api/v1/orderservice/order/" + "orderId",
                HttpMethod.DELETE,
                requestEntity,
                Response.class)).thenReturn(re);
        Response result = adminOrderService.deleteOrder("orderId", "G", headers);
        Assert.assertEquals(new Response<>(null, null, null), result);
    }

    @Test
    public void testDeleteOrder2() {
        Response response = new Response();
        ResponseEntity<Response> re = new ResponseEntity<>(response, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                "http://ts-order-other-service:12032/api/v1/orderOtherService/orderOther/" + "orderId",
                HttpMethod.DELETE,
                requestEntity,
                Response.class)).thenReturn(re);
        Response result = adminOrderService.deleteOrder("orderId", "K", headers);
        Assert.assertEquals(new Response<>(null, null, null), result);
    }

    @Test
    public void testUpdateOrder1() {
        Order order = new Order(null, null, null, null, null, null, 0, null, "G", 0, 0, null, null, null, 0, null, null);
        HttpEntity<Order> requestEntity2 = new HttpEntity<>(order, headers);
        Response response = new Response();
        ResponseEntity<Response> re = new ResponseEntity<>(response, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                "http://ts-order-service:12031/api/v1/orderservice/order/admin",
                HttpMethod.PUT,
                requestEntity2,
                Response.class)).thenReturn(re);
        Response result = adminOrderService.updateOrder(order, headers);
        Assert.assertNotNull(result);
    }

    @Test
    public void testUpdateOrder2() {
        Order order = new Order(null, null, null, null, null, null, 0, null, "K", 0, 0, null, null, null, 0, null, null);
        HttpEntity<Order> requestEntity2 = new HttpEntity<>(order, headers);
        Response response = new Response();
        ResponseEntity<Response> re = new ResponseEntity<>(response, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                "http://ts-order-other-service:12032/api/v1/orderOtherService/orderOther/admin",
                HttpMethod.PUT,
                requestEntity2,
                Response.class)).thenReturn(re);
        Response result = adminOrderService.updateOrder(order, headers);
        Assert.assertNotNull(result);
    }

    @Test
    public void testAddOrder1() {
        Order order = new Order(null, null, null, null, null, null, 0, null, "G", 0, 0, null, null, null, 0, null,null);
        HttpEntity<Order> requestEntity2 = new HttpEntity<>(order, headers);
        Response response = new Response();
        ResponseEntity<Response> re = new ResponseEntity<>(response, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                "http://ts-order-service:12031/api/v1/orderservice/order/admin",
                HttpMethod.POST,
                requestEntity2,
                Response.class)).thenReturn(re);
        Response result = adminOrderService.addOrder(order, headers);
        Assert.assertNotNull(result);
    }

    @Test
    public void testAddOrder2() {
        Order order = new Order(null, null, null, null, null, null, 0, null, "K", 0, 0, null, null, null, 0, null, null);
        HttpEntity<Order> requestEntity2 = new HttpEntity<>(order, headers);
        Response response = new Response();
        ResponseEntity<Response> re = new ResponseEntity<>(response, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                "http://ts-order-other-service:12032/api/v1/orderOtherService/orderOther/admin",
                HttpMethod.POST,
                requestEntity2,
                Response.class)).thenReturn(re);
        Response result = adminOrderService.addOrder(order, headers);
        Assert.assertNotNull(result);
    }
}


package travel2;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;
import org.springframework.cloud.client.loadbalancer.LoadBalanced;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.EnableAspectJAutoProxy;
import org.springframework.integration.annotation.IntegrationComponentScan;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.web.client.RestTemplate;
import springfox.documentation.swagger2.annotations.EnableSwagger2;

/**
 * @author fdse
 */
@SpringBootApplication
@EnableAspectJAutoProxy(proxyTargetClass = true)
@EnableAsync
@IntegrationComponentScan
@EnableSwagger2
@EnableDiscoveryClient
public class Travel2Application {

    public static void main(String[] args) {
        SpringApplication.run(Travel2Application.class, args);
    }

    @LoadBalanced
    @Bean
    public RestTemplate restTemplate(RestTemplateBuilder builder) {
        return builder.build();
    }
}


// Node: getTrainTypeByTripId
// Node: getRouteByTripId
// Node: getTripByRoute
// Node: getTripAllDetailInfo
// Node: adminQueryAll
package travel2.service;

import edu.fudan.common.entity.TripInfo;
import edu.fudan.common.util.Response;
import org.springframework.http.HttpHeaders;

import java.util.ArrayList;

/**
 * @author  Chenjie Xu
 * @date  2017/6/7.
 */
public interface TravelService {
    Response create(edu.fudan.common.entity.TravelInfo info, HttpHeaders headers);

    Response retrieve(String tripId, HttpHeaders headers);

    Response update(edu.fudan.common.entity.TravelInfo info, HttpHeaders headers);

    Response delete(String tripId, HttpHeaders headers);

    Response query(TripInfo info, HttpHeaders headers);

    Response queryByBatch(TripInfo info, HttpHeaders headers);

    Response getTripAllDetailInfo(edu.fudan.common.entity.TripAllDetailInfo gtdi, HttpHeaders headers);

    Response getRouteByTripId(String tripId, HttpHeaders headers);

    Response getTrainTypeByTripId(String tripId, HttpHeaders headers);

    Response queryAll(HttpHeaders headers);

    Response getTripByRoute(ArrayList<String> routeIds, HttpHeaders headers);

    Response adminQueryAll(HttpHeaders headers);
}


// Node: repos/cloned_ms_repos/train-ticket/ts-travel2-service/src/main/java/travel2/service/TravelService.java:TravelService.<init>
package travel2.service;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import edu.fudan.common.entity.*;
import edu.fudan.common.util.JsonUtils;
import edu.fudan.common.util.Response;
import edu.fudan.common.util.StringUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.cloud.client.discovery.DiscoveryClient;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import travel2.entity.AdminTrip;
import travel2.entity.Trip;
import travel2.entity.Travel;
import travel2.entity.TripAllDetail;
import travel2.repository.TripRepository;

import javax.transaction.Transactional;
import java.util.*;

/**
 * @author fdse
 */
@Service
public class TravelServiceImpl implements TravelService {

    @Autowired
    TripRepository repository;

    @Autowired
    private RestTemplate restTemplate;

    @Autowired
    private DiscoveryClient discoveryClient;

    private static final Logger LOGGER = LoggerFactory.getLogger(TravelServiceImpl.class);

    private String getServiceUrl(String serviceName) {
        return "http://" + serviceName; }

    String success = "Success";
    String noCnontent = "No Content";

    @Override
    public Response getRouteByTripId(String tripId, HttpHeaders headers) {
        TripId tripId1 = new TripId(tripId);

        Trip trip = repository.findByTripId(tripId1);
        if (trip == null) {
            TravelServiceImpl.LOGGER.error("[getRouteByTripId][Get Route By Trip ID Fail][Trip Not Found][TripId: {}]", tripId);
            return new Response<>(0, "\"[Get Route By Trip ID] Trip Not Found:\" + tripId", null);
        } else {
            Route route = getRouteByRouteId(trip.getRouteId(), headers);
            if (route == null) {
                TravelServiceImpl.LOGGER.error("[getRouteByTripId][Get route by Trip id error][Route not found][RouteId: {}]",trip.getRouteId());
                return new Response<>(0, "\"[Get Route By Trip ID] Route Not Found:\" + trip.getRouteId()", null);
            } else {
                TravelServiceImpl.LOGGER.info("[getRouteByTripId][Get Route By Trip ID Success]");
                return new Response<>(1, "[Get Route By Trip ID] Success", route);
            }
        }
    }


    @Override
    public Response getTrainTypeByTripId(String tripId, HttpHeaders headers) {
        TripId tripId1 = new TripId(tripId);
        TrainType trainType = null;
        Trip trip = repository.findByTripId(tripId1);
        if (trip != null) {
            trainType = getTrainTypeByName(trip.getTrainTypeName(), headers);
        }
        else {
            TravelServiceImpl.LOGGER.error("[getTrainTypeByTripId[]Get Train Type by Trip id error][Trip not found][TripId: {}]",tripId);
        }
        if (trainType != null) {
            return new Response<>(1, "Success query Train by trip id", trainType);
        } else {
            TravelServiceImpl.LOGGER.error("[getTrainTypeByTripId][Get Train Type by Trip id error][Train Type not found][TripId: {}]",tripId);
            return new Response<>(0, noCnontent, null);
        }
    }

    @Override
    public Response getTripByRoute(ArrayList<String> routeIds, HttpHeaders headers) {
        ArrayList<ArrayList<Trip>> tripList = new ArrayList<>();
        for (String routeId : routeIds) {
            ArrayList<Trip> tempTripList = repository.findByRouteId(routeId);
            if (tempTripList == null) {
                tempTripList = new ArrayList<>();
            }
            tripList.add(tempTripList);
        }
        if (!tripList.isEmpty()) {
            return new Response<>(1, success, tripList);
        } else {
            TravelServiceImpl.LOGGER.warn("[getTripByRoute][Get Trips by Route ids warn][Trips not found][RouteIdNumber: {}]",routeIds.size());
            return new Response<>(0, noCnontent, null);
        }
    }

    @Override
    public Response create(edu.fudan.common.entity.TravelInfo info, HttpHeaders headers) {
        TripId ti = new TripId(info.getTripId());
        if (repository.findByTripId(ti) == null) {
            Trip trip = new Trip(ti, info.getTrainTypeName(), info.getStartStationName(),
                    info.getStationsName(), info.getTerminalStationName(), info.getStartTime(), info.getEndTime());
            trip.setRouteId(info.getRouteId());
            repository.save(trip);
            return new Response<>(1, "Create trip info:" + ti.toString() + ".", null);
        } else {
            TravelServiceImpl.LOGGER.error("[getTripByRoute][Create trip error][Trip already exists][TripId: {}]",info.getTripId());
            return new Response<>(1, "Trip " + info.getTripId() + " already exists", null);
        }
    }

    @Override
    public Response retrieve(String tripId, HttpHeaders headers) {
        TripId ti = new TripId(tripId);
        Trip trip = repository.findByTripId(ti);
        if (trip != null) {
            return new Response<>(1, "Search Trip Success by Trip Id " + tripId, trip);
        } else {
            TravelServiceImpl.LOGGER.error("[retrieve][Retrieve trip error][Trip not found][TripId: {}]",tripId);
            return new Response<>(0, "No Content according to tripId" + tripId, null);
        }
    }

    @Override
    public Response update(edu.fudan.common.entity.TravelInfo info, HttpHeaders headers) {
        TripId ti = new TripId(info.getTripId());
        Trip t = repository.findByTripId(ti);
        if (t != null) {
            t.setStartStationName(info.getTrainTypeName());
            t.setStartStationName( info.getStartStationName());
            t.setStationsName(info.getStationsName());
            t.setTerminalStationName(info.getTerminalStationName());
            t.setStartTime(info.getStartTime());
            t.setEndTime(info.getEndTime());
            t.setRouteId(info.getRouteId());
            repository.save(t);
            return new Response<>(1, "Update trip info:" + ti.toString(), t);
        } else {
            TravelServiceImpl.LOGGER.error("[update][Update trip error][Trip not found][TripId: {}]",info.getTripId());
            return new Response<>(1, "Trip" + info.getTripId() + "doesn 't exists", null);
        }
    }

    @Override
    @Transactional
    public Response delete(String tripId, HttpHeaders headers) {
        TripId ti = new TripId(tripId);
        if (repository.findByTripId(ti) != null) {
            repository.deleteByTripId(ti);
            return new Response<>(1, "Delete trip:" + tripId + ".", tripId);
        } else {
            TravelServiceImpl.LOGGER.error("[delete][Delete trip error][Trip not found][TripId: {}]",tripId);
            return new Response<>(0, "Trip " + tripId + " doesn't exist.", null);
        }
    }

    @Override
    public Response queryByBatch(TripInfo info, HttpHeaders headers) {

        //Gets the start and arrival stations of the train number to query. The originating and arriving stations received here are both station names, so two requests need to be sent to convert to station ids
        String startPlaceName = info.getStartPlace();
        String endPlaceName = info.getEndPlace();

        //This is the final result
        List<TripResponse> list = new ArrayList<>();

        //Check all train info
        List<Trip> allTripList = repository.findAll();
        list = getTicketsByBatch(allTripList, startPlaceName, endPlaceName, info.getDepartureTime(), headers);
        return new Response<>(1, success, list);
    }

    @Override
    public Response query(TripInfo info, HttpHeaders headers) {

        //Gets the start and arrival stations of the train number to query. The originating and arriving stations received here are both station names, so two requests need to be sent to convert to station ids
        String StartPlaceName = info.getStartPlace();
        String endPlaceName = info.getEndPlace();

        //This is the final result
        ArrayList<TripResponse> list = new ArrayList<>();

        //Check all train info
        ArrayList<Trip> allTripList = repository.findAll();
        if(allTripList != null){
            for (Trip tempTrip : allTripList) {
                //Get the detailed route list of this train
                TripResponse response = getTickets(tempTrip, null, StartPlaceName, endPlaceName, info.getDepartureTime(), headers);
                if (response == null) {
                    TravelServiceImpl.LOGGER.warn("[query][Query trip error][Tickets not found][start: {},end: {},time: {}]", StartPlaceName, endPlaceName, info.getDepartureTime());
                }else{
                    list.add(response);
                }
            }
        }
        return new Response<>(1, "Success Query", list);
    }

    @Override
    public Response getTripAllDetailInfo(TripAllDetailInfo gtdi, HttpHeaders headers) {
        TripAllDetail gtdr = new TripAllDetail();
        TravelServiceImpl.LOGGER.debug("[getTripAllDetailInfo][gtdi info: {}]", gtdi.toString());
        Trip trip = repository.findByTripId(new TripId(gtdi.getTripId()));
        if (trip == null) {
            gtdr.setTripResponse(null);
            gtdr.setTrip(null);
            TravelServiceImpl.LOGGER.error("[getTripAllDetailInfo][Get trip detail error][Trip not found][TripId: {}]",gtdi.getTripId());
            return new Response<>(0, "Trip not found", gtdr);
        } else {
            String endPlaceName = gtdi.getTo();
            String StartPlaceName = gtdi.getFrom();
            TripResponse tripResponse = getTickets(trip, null, gtdi.getFrom(), gtdi.getTo(), gtdi.getTravelDate(), headers);
            if (tripResponse == null) {
                gtdr.setTrip(null);
                gtdr.setTripResponse(null);
                TravelServiceImpl.LOGGER.warn("[getTripAllDetailInfo][Query trip error][Tickets not found][start: {},end: {}]", gtdi.getTo(), gtdi.getFrom());
                return new Response<>(0, "getTickets failed", gtdr);
            } else {
                gtdr.setTripResponse(tripResponse);
                gtdr.setTrip(repository.findByTripId(new TripId(gtdi.getTripId())));
            }
        }
        return new Response<>(1, success, gtdr);
    }

    private List<TripResponse> getTicketsByBatch(List<Trip> trips, String startPlaceName, String endPlaceName, String departureTime, HttpHeaders headers) {
        List<TripResponse> responses = new ArrayList<>();
        //Determine if the date checked is the same day and after
        if (!afterToday(departureTime)) {
            TravelServiceImpl.LOGGER.info("[getTickets][depaturetime not vailid][departuretime: {}]", departureTime);
            return responses;
        }

        List<Travel> infos = new ArrayList<>();
        Map<String, Trip> tripMap = new HashMap<>();
        for(Trip trip: trips){
            Travel query = new Travel();
            query.setTrip(trip);
            query.setStartPlace(startPlaceName);
            query.setEndPlace(endPlaceName);
            query.setDepartureTime(departureTime);

            infos.add(query);
            tripMap.put(trip.getTripId().toString(), trip);
        }

        TravelServiceImpl.LOGGER.info("[getTicketsByBatch][before get basic][trips: {}]", trips);

        HttpEntity requestEntity = new HttpEntity(infos, null);
        String basic_service_url = getServiceUrl("ts-basic-service");
        ResponseEntity<Response> re = restTemplate.exchange(
                basic_service_url + "/api/v1/basicservice/basic/travels",
                HttpMethod.POST,
                requestEntity,
                Response.class);

        Response r = re.getBody();
        if(r.getStatus() == 0){
            TravelServiceImpl.LOGGER.info("[getTicketsByBatch][Ts-basic-service response status is 0][response is: {}]", r);
            return responses;
        }
        Map<String, TravelResult> trMap;
        ObjectMapper mapper = new ObjectMapper();
        try{
            trMap = mapper.readValue(JsonUtils.object2Json(r.getData()), new TypeReference<Map<String, TravelResult>>(){});
        }catch(Exception e) {
            TravelServiceImpl.LOGGER.warn("[getTicketsByBatch][Ts-basic-service convert data failed][Fail msg: {}]", e.getMessage());
            return responses;
        }

        for(Map.Entry<String, TravelResult> trEntry: trMap.entrySet()){
            //Set the returned ticket information
            String tripNumber = trEntry.getKey();
            TravelResult tr = trEntry.getValue();
            Trip trip = tripMap.get(tripNumber);

            TripResponse response = setResponse(trip, tr, startPlaceName, endPlaceName, departureTime, headers);
            responses.add(response);
        }
        return responses;
    }


    private TripResponse getTickets(Trip trip, Route route1, String startPlaceName, String endPlaceName, String departureTime, HttpHeaders headers) {

        //Determine if the date checked is the same day and after
        if (!afterToday(departureTime)) {
            return null;
        }

        Travel query = new Travel();
        query.setTrip(trip);
        query.setStartPlace(startPlaceName);
        query.setEndPlace(endPlaceName);
        query.setDepartureTime(departureTime);

        HttpEntity requestEntity = new HttpEntity(query, null);
        String basic_service_url = getServiceUrl("ts-basic-service");
        ResponseEntity<Response<TravelResult>> re = restTemplate.exchange(
                basic_service_url + "/api/v1/basicservice/basic/travel",
                HttpMethod.POST,
                requestEntity,
                new ParameterizedTypeReference<Response<edu.fudan.common.entity.TravelResult>>() {
                });
        Response r = re.getBody();
        if(r.getStatus() == 0){
            TravelServiceImpl.LOGGER.info("[getTickets][Ts-basic-service response status is 0][response is: {}]", r);
            return null;
        }
        TravelResult resultForTravel =  re.getBody().getData();

        //Set the returned ticket information
        return setResponse(trip, resultForTravel, startPlaceName, endPlaceName, departureTime, headers);
    }

    private TripResponse setResponse(Trip trip, TravelResult tr, String startPlaceName, String endPlaceName, String departureTime, HttpHeaders headers){
        //Set the returned ticket information
        TripResponse response = new TripResponse();
        response.setConfortClass(50);
        response.setEconomyClass(50);

        Route route = tr.getRoute();
        List<String> stationList = route.getStations();

        int firstClassTotalNum = tr.getTrainType().getConfortClass();
        int secondClassTotalNum = tr.getTrainType().getEconomyClass();

        int first = getRestTicketNumber(departureTime, trip.getTripId().toString(),
                startPlaceName, endPlaceName, SeatClass.FIRSTCLASS.getCode(), firstClassTotalNum, stationList, headers);

        int second = getRestTicketNumber(departureTime, trip.getTripId().toString(),
                startPlaceName, endPlaceName, SeatClass.SECONDCLASS.getCode(), secondClassTotalNum, stationList, headers);
        response.setConfortClass(first);
        response.setEconomyClass(second);

        response.setStartStation(startPlaceName);
        response.setTerminalStation(endPlaceName);

        //Calculate the distance from the starting point
        int indexStart = route.getStations().indexOf(startPlaceName);
        int indexEnd = route.getStations().indexOf(endPlaceName);
        int distanceStart = route.getDistances().get(indexStart) - route.getDistances().get(0);
        int distanceEnd = route.getDistances().get(indexEnd) - route.getDistances().get(0);
        TrainType trainType = tr.getTrainType();
        //Train running time is calculated according to the average running speed of the train
        int minutesStart = 60 * distanceStart / trainType.getAverageSpeed();
        int minutesEnd = 60 * distanceEnd / trainType.getAverageSpeed();

        Calendar calendarStart = Calendar.getInstance();
        calendarStart.setTime(StringUtils.String2Date(trip.getStartTime()));
        calendarStart.add(Calendar.MINUTE, minutesStart);
        response.setStartTime(StringUtils.Date2String(calendarStart.getTime()));
        TravelServiceImpl.LOGGER.info("[getTickets][Calculate distance][calculate time：{}  time: {}]", minutesStart, calendarStart.getTime());

        Calendar calendarEnd = Calendar.getInstance();
        calendarEnd.setTime(StringUtils.String2Date(trip.getStartTime()));
        calendarEnd.add(Calendar.MINUTE, minutesEnd);
        response.setEndTime(StringUtils.Date2String(calendarEnd.getTime()));
        TravelServiceImpl.LOGGER.info("[getTickets][Calculate distance][calculate time：{}  time: {}]", minutesEnd, calendarEnd.getTime());

        response.setTripId(trip.getTripId());
        response.setTrainTypeName(trip.getTrainTypeName());
        response.setPriceForConfortClass(tr.getPrices().get("confortClass"));
        response.setPriceForEconomyClass(tr.getPrices().get("economyClass"));

        return response;
    }

    @Override
    public Response queryAll(HttpHeaders headers) {
        List<Trip> tripList = repository.findAll();
        if (tripList != null && !tripList.isEmpty()) {
            return new Response<>(1, success, tripList);
        }
        TravelServiceImpl.LOGGER.warn("[queryAll][Query all trips warn][{}]","No Content");
        return new Response<>(0, noCnontent, null);
    }

    private static boolean afterToday(String date) {
        Calendar calDateA = Calendar.getInstance();
        Date today = new Date();
        calDateA.setTime(today);

        Calendar calDateB = Calendar.getInstance();
        calDateB.setTime(StringUtils.String2Date(date));

        if (calDateA.get(Calendar.YEAR) > calDateB.get(Calendar.YEAR)) {
            return false;
        } else if (calDateA.get(Calendar.YEAR) == calDateB.get(Calendar.YEAR)) {
            if (calDateA.get(Calendar.MONTH) > calDateB.get(Calendar.MONTH)) {
                return false;
            } else if (calDateA.get(Calendar.MONTH) == calDateB.get(Calendar.MONTH)) {
                return calDateA.get(Calendar.DAY_OF_MONTH) <= calDateB.get(Calendar.DAY_OF_MONTH);
            } else {
                return true;
            }
        } else {
            return true;
        }
    }

    private TrainType getTrainTypeByName(String trainTypeName, HttpHeaders headers) {
        HttpEntity requestEntity = new HttpEntity(null);
        String train_service_url = getServiceUrl("ts-train-service");
        ResponseEntity<Response<TrainType>> re = restTemplate.exchange(
                train_service_url + "/api/v1/trainservice/trains/byName/" + trainTypeName,
                HttpMethod.GET,
                requestEntity,
                new ParameterizedTypeReference<Response<TrainType>>() {
                });

        return re.getBody().getData();
    }

    private Route getRouteByRouteId(String routeId, HttpHeaders headers) {
        TravelServiceImpl.LOGGER.debug("[getRouteByRouteId][Get Route By Id][Route ID：{}]", routeId);
        HttpEntity requestEntity = new HttpEntity(null);
        String route_service_url = getServiceUrl("ts-route-service");
        ResponseEntity<Response> re = restTemplate.exchange(
                route_service_url + "/api/v1/routeservice/routes/" + routeId,
                HttpMethod.GET,
                requestEntity,
                Response.class);
        Response result = re.getBody();

        if (result.getStatus() == 0 ) {
            TravelServiceImpl.LOGGER.error("[getRouteByRouteId][Get Route By Id Fail][Route not found][RouteId: {}]", routeId);
            return null;
        } else {
            TravelServiceImpl.LOGGER.info("[getRouteByRouteId][Get Route By Id Success]");
            return JsonUtils.conveterObject(result.getData(), Route.class);
        }
    }

    private int getRestTicketNumber(String travelDate, String trainNumber, String startStationName, String endStationName, int seatType, int totalNum, List<String> stationList, HttpHeaders headers) {
        Seat seatRequest = new Seat();

        seatRequest.setDestStation(endStationName);
        seatRequest.setStartStation(startStationName);
        seatRequest.setTrainNumber(trainNumber);
        seatRequest.setTravelDate(travelDate);
        seatRequest.setSeatType(seatType);
        seatRequest.setTotalNum(totalNum);
        seatRequest.setStations(stationList);

        TravelServiceImpl.LOGGER.info("[getRestTicketNumber][Seat request][request: {}]", seatRequest.toString());

        HttpEntity requestEntity = new HttpEntity(seatRequest, null);
        String seat_service_url = getServiceUrl("ts-seat-service");
        ResponseEntity<Response<Integer>> re = restTemplate.exchange(
                seat_service_url + "/api/v1/seatservice/seats/left_tickets",
                HttpMethod.POST,
                requestEntity,
                new ParameterizedTypeReference<Response<Integer>>() {
                });
        TravelServiceImpl.LOGGER.info("[getRestTicketNumber][Get Rest tickets num][num is: {}]", re.getBody().toString());

        return re.getBody().getData();
    }

    @Override
    public Response adminQueryAll(HttpHeaders headers) {
        List<Trip> trips = repository.findAll();
        ArrayList<AdminTrip> adminTrips = new ArrayList<>();
        if(trips != null){
            for (Trip trip : trips) {
                AdminTrip adminTrip = new AdminTrip();
                adminTrip.setRoute(getRouteByRouteId(trip.getRouteId(), headers));
                adminTrip.setTrainType(getTrainTypeByName(trip.getTrainTypeName(), headers));
                adminTrip.setTrip(trip);
                adminTrips.add(adminTrip);
            }
        }

        if (!adminTrips.isEmpty()) {
            return new Response<>(1, "Travel Service Admin Query All Travel Success", adminTrips);
        } else {
            TravelServiceImpl.LOGGER.warn("[adminQueryAll][Admin query all trips warn][{}]","No Content");
            return new Response<>(0, noCnontent, null);
        }
    }

}



package travel2.controller;

import com.alibaba.fastjson.JSONObject;
import edu.fudan.common.util.Response;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.springframework.http.*;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.request.MockMvcRequestBuilders;
import org.springframework.test.web.servlet.result.MockMvcResultMatchers;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import edu.fudan.common.entity.TravelInfo;
import edu.fudan.common.entity.TripAllDetailInfo;
import edu.fudan.common.entity.TripInfo;
import edu.fudan.common.entity.TripResponse;
import travel2.service.TravelService;

import java.util.ArrayList;
import java.util.Date;

@RunWith(JUnit4.class)
public class TravelControllerTest {

    @InjectMocks
    private Travel2Controller travel2Controller;

    @Mock
    private TravelService service;
    private MockMvc mockMvc;
    private Response response = new Response();

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
        mockMvc = MockMvcBuilders.standaloneSetup(travel2Controller).build();
    }

    @Test
    public void testHome() throws Exception {
        mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/travel2service/welcome"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andExpect(MockMvcResultMatchers.content().string("Welcome to [ Travle2 Service ] !"));
    }

    @Test
    public void testGetTrainTypeByTripId() throws Exception {
        Mockito.when(service.getTrainTypeByTripId(Mockito.anyString(), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/travel2service/train_types/trip_id"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testGetRouteByTripId() throws Exception {
        Mockito.when(service.getRouteByTripId(Mockito.anyString(), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/travel2service/routes/trip_id"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testGetTripsByRouteId() throws Exception {
        ArrayList<String> routeIds = new ArrayList<>();
        Mockito.when(service.getTripByRoute(Mockito.any(ArrayList.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(routeIds);
        String result = mockMvc.perform(MockMvcRequestBuilders.post("/api/v1/travel2service/trips/routes").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testCreateTrip() throws Exception {
        TravelInfo routeIds = new TravelInfo();
        Mockito.when(service.create(Mockito.any(TravelInfo.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(routeIds);
        String result = mockMvc.perform(MockMvcRequestBuilders.post("/api/v1/travel2service/trips").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isCreated())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testRetrieve() throws Exception {
        Mockito.when(service.retrieve(Mockito.anyString(), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/travel2service/trips/trip_id"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testUpdateTrip() throws Exception {
        TravelInfo info = new TravelInfo();
        Mockito.when(service.update(Mockito.any(TravelInfo.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(info);
        String result = mockMvc.perform(MockMvcRequestBuilders.put("/api/v1/travel2service/trips").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testDeleteTrip() throws Exception {
        Mockito.when(service.delete(Mockito.anyString(), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.delete("/api/v1/travel2service/trips/trip_id"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testQueryInfo1() throws Exception {
        TripInfo info = new TripInfo();
        ArrayList<TripResponse> errorList = new ArrayList<>();
        String requestJson = JSONObject.toJSONString(info);
        String result = mockMvc.perform(MockMvcRequestBuilders.post("/api/v1/travel2service/trips/left").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(errorList, JSONObject.parseObject(result, ArrayList.class));
    }

    @Test
    public void testQueryInfo2() throws Exception {
        TripInfo info = new TripInfo("startPlace", "endPlace", "");
        Mockito.when(service.query(Mockito.any(TripInfo.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(info);
        String result = mockMvc.perform(MockMvcRequestBuilders.post("/api/v1/travel2service/trips/left").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testGetTripAllDetailInfo() throws Exception {
        TripAllDetailInfo gtdi = new TripAllDetailInfo();
        Mockito.when(service.getTripAllDetailInfo(Mockito.any(TripAllDetailInfo.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(gtdi);
        String result = mockMvc.perform(MockMvcRequestBuilders.post("/api/v1/travel2service/trip_detail").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testQueryAll() throws Exception {
        Mockito.when(service.queryAll(Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/travel2service/trips"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testAdminQueryAll() throws Exception {
        Mockito.when(service.adminQueryAll(Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/travel2service/admin_trip"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

}


// Node: testGetTrainTypeByTripId
// Node: testGetRouteByTripId
// Node: testGetTripsByRouteId
// Node: testCreateTrip
// Node: testRetrieve
// Node: testUpdateTrip
// Node: testDeleteTrip
// Node: testQueryInfo1
// Node: testQueryInfo2
// Node: testGetTripAllDetailInfo
// Node: testAdminQueryAll
package travel2.service;

import edu.fudan.common.entity.TripId;
import edu.fudan.common.entity.TripAllDetailInfo;
import edu.fudan.common.entity.TripInfo;
import edu.fudan.common.util.Response;
import edu.fudan.common.util.StringUtils;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.*;
import org.springframework.web.client.RestTemplate;
import travel2.entity.Trip;
import travel2.repository.TripRepository;

import java.util.ArrayList;
import java.util.Date;

@RunWith(JUnit4.class)
public class TravelServiceImplTest {

    @InjectMocks
    private TravelServiceImpl travel2ServiceImpl;

    @Mock
    private TripRepository repository;

    @Mock
    private RestTemplate restTemplate;

    private HttpHeaders headers = new HttpHeaders();
    String success = "Success";
    String noCnontent = "No Content";

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
    }

    @Test
    public void testGetRouteByTripId1() {
        Mockito.when(repository.findByTripId(Mockito.any(TripId.class))).thenReturn(null);
        Response result = travel2ServiceImpl.getRouteByTripId("K1255", headers);
        Assert.assertEquals(new Response<>(0, "\"[Get Route By Trip ID] Trip Not Found:\" + tripId", null), result);
    }

    @Test
    public void testGetRouteByTripId2() {
        Trip trip = new Trip();
        Mockito.when(repository.findByTripId(Mockito.any(TripId.class))).thenReturn(trip);
        //mock getRouteByRouteId()
        edu.fudan.common.entity.Route route = new edu.fudan.common.entity.Route();
        Response response = new Response(1, null, route);
        ResponseEntity<Response> re = new ResponseEntity<>(response, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                Mockito.anyString(),
                Mockito.any(HttpMethod.class),
                Mockito.any(HttpEntity.class),
                Mockito.any(Class.class)))
                .thenReturn(re);
        Response result = travel2ServiceImpl.getRouteByTripId("K1255", headers);
        Assert.assertEquals("[Get Route By Trip ID] Success", result.getMsg());
    }

    @Test
    public void testGetTrainTypeByTripId() {
        Trip trip = new Trip();
        Mockito.when(repository.findByTripId(Mockito.any(TripId.class))).thenReturn(trip);
        //mock getTrainType()
        edu.fudan.common.entity.TrainType trainType = new edu.fudan.common.entity.TrainType();
        Response<edu.fudan.common.entity.TrainType> response = new Response<>(null, null, trainType);
        ResponseEntity<Response<edu.fudan.common.entity.TrainType>> re = new ResponseEntity<>(response, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                Mockito.anyString(),
                Mockito.any(HttpMethod.class),
                Mockito.any(HttpEntity.class),
                Mockito.any(ParameterizedTypeReference.class)))
                .thenReturn(re);
        Response result = travel2ServiceImpl.getTrainTypeByTripId("K1255", headers);
        Assert.assertEquals(new Response<>(1, "Success query Train by trip id", trainType), result);
    }

    @Test
    public void testGetTripByRoute1() {
        ArrayList<String> routeIds = new ArrayList<>();
        Response result = travel2ServiceImpl.getTripByRoute(routeIds, headers);
        Assert.assertEquals(new Response<>(0, noCnontent, null), result);
    }

    @Test
    public void testGetTripByRoute2() {
        ArrayList<String> routeIds = new ArrayList<>();
        routeIds.add("route_id_1");
        Mockito.when(repository.findByRouteId(Mockito.anyString())).thenReturn(null);
        Response result = travel2ServiceImpl.getTripByRoute(routeIds, headers);
        Assert.assertEquals(success, result.getMsg());
    }

    @Test
    public void testCreate1() {
        edu.fudan.common.entity.TravelInfo info = new edu.fudan.common.entity.TravelInfo();
        info.setTripId("Z");
        Mockito.when(repository.findByTripId(Mockito.any(TripId.class))).thenReturn(null);
        Mockito.when(repository.save(Mockito.any(Trip.class))).thenReturn(null);
        Response result = travel2ServiceImpl.create(info, headers);
        Assert.assertEquals(new Response<>(1, "Create trip info:Z.", null), result);
    }

    @Test
    public void testCreate2() {
        edu.fudan.common.entity.TravelInfo info = new edu.fudan.common.entity.TravelInfo();
        info.setTripId("Z");
        Trip trip = new Trip();
        Mockito.when(repository.findByTripId(Mockito.any(TripId.class))).thenReturn(trip);
        Response result = travel2ServiceImpl.create(info, headers);
        Assert.assertEquals(new Response<>(1, "Trip Z already exists", null), result);
    }

    @Test
    public void testRetrieve1() {
        Trip trip = new Trip();
        Mockito.when(repository.findByTripId(Mockito.any(TripId.class))).thenReturn(trip);
        Response result = travel2ServiceImpl.retrieve("trip_id_1", headers);
        Assert.assertEquals(new Response<>(1, "Search Trip Success by Trip Id trip_id_1", trip), result);
    }

    @Test
    public void testRetrieve2() {
        Trip trip = new Trip();
        Mockito.when(repository.findByTripId(Mockito.any(TripId.class))).thenReturn(trip);
        Response result = travel2ServiceImpl.retrieve("trip_id_1", headers);
        Assert.assertEquals(new Response<>(1, "Search Trip Success by Trip Id trip_id_1", trip), result);
    }

    @Test
    public void testUpdate1() {
        edu.fudan.common.entity.TravelInfo info = new edu.fudan.common.entity.TravelInfo();
        info.setTripId("Z");
        Trip trip = new Trip();
        Mockito.when(repository.findByTripId(Mockito.any(TripId.class))).thenReturn(trip);
        Mockito.when(repository.save(Mockito.any(Trip.class))).thenReturn(null);
        Response result = travel2ServiceImpl.update(info, headers);
        Assert.assertEquals("Update trip info:Z", result.getMsg());
    }

    @Test
    public void testUpdate2() {
        edu.fudan.common.entity.TravelInfo info = new edu.fudan.common.entity.TravelInfo();
        info.setTripId("Z");
        Mockito.when(repository.findByTripId(Mockito.any(TripId.class))).thenReturn(null);
        Response result = travel2ServiceImpl.update(info, headers);
        Assert.assertEquals(new Response<>(1, "TripZdoesn 't exists", null), result);
    }

    @Test
    public void testDelete1() {
        Trip trip = new Trip();
        Mockito.when(repository.findByTripId(Mockito.any(TripId.class))).thenReturn(trip);
        Mockito.doNothing().doThrow(new RuntimeException()).when(repository).deleteByTripId(Mockito.any(TripId.class));
        Response result = travel2ServiceImpl.delete("trip_id_1", headers);
        Assert.assertEquals(new Response<>(1, "Delete trip:trip_id_1.", "trip_id_1"), result);
    }

    @Test
    public void testDelete2() {
        Mockito.when(repository.findByTripId(Mockito.any(TripId.class))).thenReturn(null);
        Response result = travel2ServiceImpl.delete("trip_id_1", headers);
        Assert.assertEquals(new Response<>(0, "Trip trip_id_1 doesn't exist.", null), result);
    }

    @Test
    public void testQuery() {
        TripInfo info = new TripInfo();
        //mock queryForStationId()
        Response<String> response1 = new Response<>(null, null, "");
        ResponseEntity<Response<String>> re1 = new ResponseEntity<>(response1, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                Mockito.anyString(),
                Mockito.any(HttpMethod.class),
                Mockito.any(HttpEntity.class),
                Mockito.any(ParameterizedTypeReference.class)))
                .thenReturn(re1);

        ArrayList<Trip> tripList = new ArrayList<>();
        Trip trip = new Trip();
        trip.setRouteId("route_id");
        tripList.add(trip);
        Mockito.when(repository.findAll()).thenReturn(tripList);

        //mock getRouteByRouteId()
        edu.fudan.common.entity.Route route = new edu.fudan.common.entity.Route();
        route.setStations(new ArrayList<>());
        Response response2 = new Response(1, null, route);
        ResponseEntity<Response> re2 = new ResponseEntity<>(response2, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                Mockito.anyString(),
                Mockito.any(HttpMethod.class),
                Mockito.any(HttpEntity.class),
                Mockito.any(Class.class)))
                .thenReturn(re2);
        Response result = travel2ServiceImpl.query(info, headers);
        Assert.assertEquals(new Response<>(1, "Success Query", new ArrayList<>()), result);
    }

    @Test
    public void testGetTripAllDetailInfo() {
        TripAllDetailInfo gtdi = new TripAllDetailInfo();
        gtdi.setTripId("Z1255");
        gtdi.setFrom("from_station");
        gtdi.setTo("to_station");
        gtdi.setTravelDate(StringUtils.Date2String(new Date(System.currentTimeMillis() - 86400000)));

        Trip trip = new Trip();
        trip.setRouteId("route_id");
        Mockito.when(repository.findByTripId(Mockito.any(TripId.class))).thenReturn(trip);

        //mock queryForStationId()
        Response<String> response1 = new Response<>(null, null, "");
        ResponseEntity<Response<String>> re1 = new ResponseEntity<>(response1, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                Mockito.anyString(),
                Mockito.any(HttpMethod.class),
                Mockito.any(HttpEntity.class),
                Mockito.any(ParameterizedTypeReference.class)))
                .thenReturn(re1);

        //mock getRouteByRouteId()
        edu.fudan.common.entity.Route route = new edu.fudan.common.entity.Route();
        route.setStations(new ArrayList<>());
        Response response2 = new Response(1, null, route);
        ResponseEntity<Response> re2 = new ResponseEntity<>(response2, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                Mockito.anyString(),
                Mockito.any(HttpMethod.class),
                Mockito.any(HttpEntity.class),
                Mockito.any(Class.class)))
                .thenReturn(re2);
        Response result = travel2ServiceImpl.getTripAllDetailInfo(gtdi, headers);
        Assert.assertEquals("Success", result.getMsg());
    }

    @Test
    public void testQueryAll1() {
        ArrayList<Trip> tripList = new ArrayList<>();
        tripList.add(new Trip());
        Mockito.when(repository.findAll()).thenReturn(tripList);
        Response result = travel2ServiceImpl.queryAll(headers);
        Assert.assertEquals(new Response<>(1, success, tripList), result);
    }

    @Test
    public void testQueryAll2() {
        Mockito.when(repository.findAll()).thenReturn(null);
        Response result = travel2ServiceImpl.queryAll(headers);
        Assert.assertEquals(new Response<>(0, noCnontent, null), result);
    }

    @Test
    public void testAdminQueryAll1() {
        ArrayList<Trip> tripList = new ArrayList<>();
        Trip trip = new Trip();
        trip.setRouteId("route_id");
        tripList.add(trip);
        Mockito.when(repository.findAll()).thenReturn(tripList);

        //mock getRouteByRouteId()
        edu.fudan.common.entity.Route route = new edu.fudan.common.entity.Route();
        Response response2 = new Response(1, null, route);
        ResponseEntity<Response> re2 = new ResponseEntity<>(response2, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                Mockito.anyString(),
                Mockito.any(HttpMethod.class),
                Mockito.any(HttpEntity.class),
                Mockito.any(Class.class)))
                .thenReturn(re2);

        //mock getTrainType()
        edu.fudan.common.entity.TrainType trainType = new edu.fudan.common.entity.TrainType();
        Response<edu.fudan.common.entity.TrainType> response = new Response<>(null, null, trainType);
        ResponseEntity<Response<edu.fudan.common.entity.TrainType>> re = new ResponseEntity<>(response, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                Mockito.anyString(),
                Mockito.any(HttpMethod.class),
                Mockito.any(HttpEntity.class),
                Mockito.any(ParameterizedTypeReference.class)))
                .thenReturn(re);
        Response result = travel2ServiceImpl.adminQueryAll(headers);
        Assert.assertEquals("Travel Service Admin Query All Travel Success", result.getMsg());
    }
    @Test
    public void testAdminQueryAll2() {
        ArrayList<Trip> tripList = new ArrayList<>();
        Mockito.when(repository.findAll()).thenReturn(tripList);
        Response result = travel2ServiceImpl.adminQueryAll(headers);
        Assert.assertEquals(new Response<>(0, noCnontent, null), result);
    }

}


// Node: testGetTripByRoute1
package order;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;
import org.springframework.cloud.client.loadbalancer.LoadBalanced;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.EnableAspectJAutoProxy;
import org.springframework.integration.annotation.IntegrationComponentScan;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.web.client.RestTemplate;
import springfox.documentation.swagger2.annotations.EnableSwagger2;

/**
 * @author fdse
 */
@SpringBootApplication
@EnableAspectJAutoProxy(proxyTargetClass = true)
@EnableAsync
@IntegrationComponentScan
@EnableSwagger2
@EnableDiscoveryClient
public class OrderApplication {
    public static void main(String[] args) {
        SpringApplication.run(OrderApplication.class, args);
    }

    @LoadBalanced
    @Bean
    public RestTemplate restTemplate(RestTemplateBuilder builder) {
        return builder.build();
    }
}


package order.controller;

import com.alibaba.fastjson.JSONObject;
import edu.fudan.common.entity.Seat;
import edu.fudan.common.util.Response;
import order.entity.Order;
import order.entity.OrderInfo;
import order.service.OrderService;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.springframework.http.*;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.request.MockMvcRequestBuilders;
import org.springframework.test.web.servlet.result.MockMvcResultMatchers;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

import java.util.Date;

@RunWith(JUnit4.class)
public class OrderControllerTest {

    @InjectMocks
    private OrderController orderController;

    @Mock
    private OrderService orderService;
    private MockMvc mockMvc;
    private Response response = new Response();

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
        mockMvc = MockMvcBuilders.standaloneSetup(orderController).build();
    }

    @Test
    public void testHome() throws Exception {
        mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/orderservice/welcome"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andExpect(MockMvcResultMatchers.content().string("Welcome to [ Order Service ] !"));
    }

    @Test
    public void testGetTicketListByDateAndTripId() throws Exception {
        Seat seatRequest = new Seat();
        Mockito.when(orderService.getSoldTickets(Mockito.any(Seat.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(seatRequest);
        String result = mockMvc.perform(MockMvcRequestBuilders.post("/api/v1/orderservice/order/tickets").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testCreateNewOrder() throws Exception {
        Order createOrder = new Order();
        Mockito.when(orderService.create(Mockito.any(Order.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(createOrder);
        String result = mockMvc.perform(MockMvcRequestBuilders.post("/api/v1/orderservice/order").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testAddCreateNewOrder() throws Exception {
        Order order = new Order();
        Mockito.when(orderService.addNewOrder(Mockito.any(Order.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(order);
        String result = mockMvc.perform(MockMvcRequestBuilders.post("/api/v1/orderservice/order/admin").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testQueryOrders() throws Exception {
        OrderInfo qi = new OrderInfo();
        Mockito.when(orderService.queryOrders(Mockito.any(OrderInfo.class), Mockito.anyString(), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(qi);
        String result = mockMvc.perform(MockMvcRequestBuilders.post("/api/v1/orderservice/order/query").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testQueryOrdersForRefresh() throws Exception {
        OrderInfo qi = new OrderInfo();
        Mockito.when(orderService.queryOrdersForRefresh(Mockito.any(OrderInfo.class), Mockito.anyString(), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(qi);
        String result = mockMvc.perform(MockMvcRequestBuilders.post("/api/v1/orderservice/order/refresh").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testCalculateSoldTicket() throws Exception {
        Date travelDate = new Date();
        Mockito.when(orderService.queryAlreadySoldOrders(Mockito.any(Date.class), Mockito.anyString(), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/orderservice/order/" + travelDate.toString() + "/train_number"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testGetOrderPrice() throws Exception {
        Mockito.when(orderService.getOrderPrice(Mockito.anyString(), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/orderservice/order/price/order_id"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testPayOrder() throws Exception {
        Mockito.when(orderService.payOrder(Mockito.anyString(), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/orderservice/order/orderPay/order_id"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testGetOrderById() throws Exception {
        Mockito.when(orderService.getOrderById(Mockito.anyString(), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/orderservice/order/order_id"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testModifyOrder() throws Exception {
        Mockito.when(orderService.modifyOrder(Mockito.anyString(), Mockito.anyInt(), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/orderservice/order/status/order_id/1"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testSecurityInfoCheck() throws Exception {
        Date checkDate = new Date();
        Mockito.when(orderService.checkSecurityAboutOrder(Mockito.any(Date.class), Mockito.anyString(), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/orderservice/order/security/" + checkDate.toString() + "/account_id"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testSaveOrderInfo() throws Exception {
        Order orderInfo = new Order();
        Mockito.when(orderService.saveChanges(Mockito.any(Order.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(orderInfo);
        String result = mockMvc.perform(MockMvcRequestBuilders.put("/api/v1/orderservice/order").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testUpdateOrder() throws Exception {
        Order order = new Order();
        Mockito.when(orderService.updateOrder(Mockito.any(Order.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(order);
        String result = mockMvc.perform(MockMvcRequestBuilders.put("/api/v1/orderservice/order/admin").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testDeleteOrder() throws Exception {
        Mockito.when(orderService.deleteOrder(Mockito.anyString(), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.delete("/api/v1/orderservice/order/order_id"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testFindAllOrder() throws Exception {
        Mockito.when(orderService.getAllOrders(Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/orderservice/order"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

}


package order.service;


import edu.fudan.common.entity.OrderSecurity;
import edu.fudan.common.entity.Seat;
import edu.fudan.common.util.Response;
import order.entity.*;
import order.repository.OrderRepository;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.*;
import org.springframework.web.client.RestTemplate;

import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.UUID;

import static org.mockito.internal.verification.VerificationModeFactory.times;

@RunWith(JUnit4.class)
public class OrderServiceImplTest {

    @InjectMocks
    private OrderServiceImpl orderServiceImpl;

    @Mock
    private OrderRepository orderRepository;

    @Mock
    private RestTemplate restTemplate;

    private HttpHeaders headers = new HttpHeaders();

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
    }

    @Test
    public void testGetSoldTickets1() {
        Seat seatRequest = new Seat();
        ArrayList<Order> list = new ArrayList<>();
        list.add(new Order());
        Mockito.when(orderRepository.findByTravelDateAndTrainNumber(Mockito.any(String.class), Mockito.anyString())).thenReturn(list);
        Response result = orderServiceImpl.getSoldTickets(seatRequest, headers);
        Assert.assertEquals("Success", result.getMsg());
    }

    @Test
    public void testGetSoldTickets2() {
        Seat seatRequest = new Seat();
        Mockito.when(orderRepository.findByTravelDateAndTrainNumber(Mockito.any(String.class), Mockito.anyString())).thenReturn(null);
        Response result = orderServiceImpl.getSoldTickets(seatRequest, headers);
        Assert.assertEquals(new Response<>(0, "Order is Null.", null), result);
    }

    @Test
    public void testFindOrderById1() {
        String id = UUID.randomUUID().toString();
        Mockito.when(orderRepository.findById(Mockito.any(String.class))).thenReturn(null);
        Response result = orderServiceImpl.findOrderById(id, headers);
        Assert.assertEquals(new Response<>(0, "No Content by this id", null), result);
    }

    @Test
    public void testFindOrderById2() {
        String id = UUID.randomUUID().toString();
        Order order = new Order();
        Mockito.when(orderRepository.findById(Mockito.any(String.class)).get()).thenReturn(order);
        Response result = orderServiceImpl.findOrderById(id, headers);
        Assert.assertEquals(new Response<>(1, "Success", order), result);
    }

    @Test
    public void testCreate1() {
        Order order = new Order();
        ArrayList<Order> accountOrders = new ArrayList<>();
        accountOrders.add(order);
        Mockito.when(orderRepository.findByAccountId(Mockito.any(String.class))).thenReturn(accountOrders);
        Response result = orderServiceImpl.create(order, headers);
        Assert.assertEquals(new Response<>(0, "Order already exist", null), result);
    }

    @Test
    public void testCreate2() {
        Order order = new Order();
        ArrayList<Order> accountOrders = new ArrayList<>();
        Mockito.when(orderRepository.findByAccountId(Mockito.any(String.class))).thenReturn(accountOrders);
        Mockito.when(orderRepository.save(Mockito.any(Order.class))).thenReturn(null);
        Response result = orderServiceImpl.create(order, headers);
        Assert.assertEquals("Success", result.getMsg());
    }

    @Test
    public void testInitOrder1() {
        Order order = new Order();
        Mockito.when(orderRepository.findById(Mockito.any(String.class))).thenReturn(null);
        Mockito.when(orderRepository.save(Mockito.any(Order.class))).thenReturn(null);
        orderServiceImpl.initOrder(order, headers);
        Mockito.verify(orderRepository, times(1)).save(Mockito.any(Order.class));
    }

    @Test
    public void testInitOrder2() {
        Order order = new Order();
        Mockito.when(orderRepository.findById(Mockito.any(String.class)).get()).thenReturn(order);
        Mockito.when(orderRepository.save(Mockito.any(Order.class))).thenReturn(null);
        orderServiceImpl.initOrder(order, headers);
        Mockito.verify(orderRepository, times(0)).save(Mockito.any(Order.class));
    }

    @Test
    public void testAlterOrder1() {
        OrderAlterInfo oai = new OrderAlterInfo();
        Mockito.when(orderRepository.findById(Mockito.any(String.class))).thenReturn(null);
        Response result = orderServiceImpl.alterOrder(oai, headers);
        Assert.assertEquals(new Response<>(0, "Old Order Does Not Exists", null), result);
    }

    @Test
    public void testAlterOrder2() {
        OrderAlterInfo oai = new OrderAlterInfo(UUID.randomUUID().toString(), UUID.randomUUID().toString(), "login_token", new Order());
        Order order = new Order();
        Mockito.when(orderRepository.findById(Mockito.any(String.class)).get()).thenReturn(order);
        Mockito.when(orderRepository.save(Mockito.any(Order.class))).thenReturn(null);
        //mock create()
        ArrayList<Order> accountOrders = new ArrayList<>();
        Mockito.when(orderRepository.findByAccountId(Mockito.any(String.class))).thenReturn(accountOrders);
        Response result = orderServiceImpl.alterOrder(oai, headers);
        Assert.assertEquals("Success", result.getMsg());
    }

    @Test
    public void testQueryOrders() {
        ArrayList<Order> list = new ArrayList<>();
        Order order = new Order();
        order.setStatus(1);
        list.add(order);
        Mockito.when(orderRepository.findByAccountId(Mockito.any(String.class))).thenReturn(list);
        OrderInfo qi = new OrderInfo();
        qi.setEnableStateQuery(true);
        qi.setEnableBoughtDateQuery(false);
        qi.setEnableTravelDateQuery(false);
        qi.setState(1);
        Response result = orderServiceImpl.queryOrders(qi, UUID.randomUUID().toString(), headers);
        Assert.assertEquals(new Response<>(1, "Get order num", list), result);
    }

    @Test
    public void testQueryOrdersForRefresh() {
        ArrayList<Order> list = new ArrayList<>();
        Mockito.when(orderRepository.findByAccountId(Mockito.any(String.class))).thenReturn(list);
        //mock queryForStationId()
        Response<List<String>> response = new Response<>();
        ResponseEntity<Response<List<String>>> re = new ResponseEntity<>(response, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                Mockito.anyString(),
                Mockito.any(HttpMethod.class),
                Mockito.any(HttpEntity.class),
                Mockito.any(ParameterizedTypeReference.class)
        )).thenReturn(re);
        OrderInfo qi = new OrderInfo();
        qi.setEnableStateQuery(false);
        qi.setEnableBoughtDateQuery(false);
        qi.setEnableTravelDateQuery(false);
        Response result = orderServiceImpl.queryOrdersForRefresh(qi, UUID.randomUUID().toString(), headers);
        Assert.assertEquals("Query Orders For Refresh Success", result.getMsg());
    }

    @Test
    public void testQueryForStationId() {
        List<String> ids = new ArrayList<>();
        HttpEntity requestEntity = new HttpEntity<>(ids, headers);
        Response<List<String>> response = new Response<>();
        ResponseEntity<Response<List<String>>> re = new ResponseEntity<>(response, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                "http://ts-station-service:12345/api/v1/stationservice/stations/namelist",
                HttpMethod.POST,
                requestEntity,
                new ParameterizedTypeReference<Response<List<String>>>() {
                })).thenReturn(re);
        List<String> result = orderServiceImpl.queryForStationId(ids, headers);
        Assert.assertNull(result);
    }

    @Test
    public void testSaveChanges1() {
        Order order = new Order();
        Mockito.when(orderRepository.findById(Mockito.any(String.class))).thenReturn(null);
        Response result = orderServiceImpl.saveChanges(order, headers);
        Assert.assertEquals(new Response<>(0, "Order Not Found", null), result);
    }

    @Test
    public void testSaveChanges2() {
        Order order = new Order();
        Mockito.when(orderRepository.findById(Mockito.any(String.class)).get()).thenReturn(order);
        Mockito.when(orderRepository.save(Mockito.any(Order.class))).thenReturn(null);
        Response result = orderServiceImpl.saveChanges(order, headers);
        Assert.assertEquals(new Response<>(1, "Success", order), result);
    }

    @Test
    public void testCancelOrder1() {
        Mockito.when(orderRepository.findById(Mockito.any(String.class))).thenReturn(null);
        Response result = orderServiceImpl.cancelOrder(UUID.randomUUID().toString(), UUID.randomUUID().toString(), headers);
        Assert.assertEquals(new Response<>(0, "Order Not Found", null), result);
    }

    @Test
    public void testCancelOrder2() {
        Order oldOrder = new Order();
        Mockito.when(orderRepository.findById(Mockito.any(String.class)).get()).thenReturn(oldOrder);
        Mockito.when(orderRepository.save(Mockito.any(Order.class))).thenReturn(null);
        Response result = orderServiceImpl.cancelOrder(UUID.randomUUID().toString(), UUID.randomUUID().toString(), headers);
        Assert.assertEquals("Success", result.getMsg());
    }

    @Test
    public void testQueryAlreadySoldOrders() {
        ArrayList<Order> orders = new ArrayList<>();
        Mockito.when(orderRepository.findByTravelDateAndTrainNumber(Mockito.any(String.class), Mockito.anyString())).thenReturn(orders);
        Response result = orderServiceImpl.queryAlreadySoldOrders(new Date(), "G1234", headers);
        Assert.assertEquals("Success", result.getMsg());
    }

    @Test
    public void testGetAllOrders1() {
        Mockito.when(orderRepository.findAll()).thenReturn(null);
        Response result = orderServiceImpl.getAllOrders(headers);
        Assert.assertEquals(new Response<>(0, "No Content.", null), result);
    }

    @Test
    public void testGetAllOrders2() {
        ArrayList<Order> orders = new ArrayList<>();
        orders.add(new Order());
        Mockito.when(orderRepository.findAll()).thenReturn(orders);
        Response result = orderServiceImpl.getAllOrders(headers);
        Assert.assertEquals(new Response<>(1, "Success.", orders), result);
    }

    @Test
    public void testModifyOrder1() {
        Mockito.when(orderRepository.findById(Mockito.any(String.class))).thenReturn(null);
        Response result = orderServiceImpl.modifyOrder(UUID.randomUUID().toString(), 1, headers);
        Assert.assertEquals(new Response<>(0, "Order Not Found", null), result);
    }

    @Test
    public void testModifyOrder2() {
        Order order = new Order();
        Mockito.when(orderRepository.findById(Mockito.any(String.class)).get()).thenReturn(order);
        Mockito.when(orderRepository.save(Mockito.any(Order.class))).thenReturn(null);
        Response result = orderServiceImpl.modifyOrder(UUID.randomUUID().toString(), 1, headers);
        Assert.assertEquals("Modify Order Success", result.getMsg());
    }

    @Test
    public void testGetOrderPrice1() {
        Mockito.when(orderRepository.findById(Mockito.any(String.class))).thenReturn(null);
        Response result = orderServiceImpl.getOrderPrice(UUID.randomUUID().toString(), headers);
        Assert.assertEquals(new Response<>(0, "Order Not Found", "-1.0"), result);
    }

    @Test
    public void testGetOrderPrice2() {
        Order order = new Order();
        Mockito.when(orderRepository.findById(Mockito.any(String.class)).get()).thenReturn(order);
        Response result = orderServiceImpl.getOrderPrice(UUID.randomUUID().toString(), headers);
        Assert.assertEquals(new Response<>(1, "Success", order.getPrice()), result);
    }

    @Test
    public void testPayOrder1() {
        Mockito.when(orderRepository.findById(Mockito.any(String.class))).thenReturn(null);
        Response result = orderServiceImpl.payOrder(UUID.randomUUID().toString(), headers);
        Assert.assertEquals(new Response<>(0, "Order Not Found", null), result);
    }

    @Test
    public void testPayOrder2() {
        Order order = new Order();
        Mockito.when(orderRepository.findById(Mockito.any(String.class)).get()).thenReturn(order);
        Mockito.when(orderRepository.save(Mockito.any(Order.class))).thenReturn(null);
        Response result = orderServiceImpl.payOrder(UUID.randomUUID().toString(), headers);
        Assert.assertEquals("Pay Order Success.", result.getMsg());
    }

    @Test
    public void testGetOrderById1() {
        Mockito.when(orderRepository.findById(Mockito.any(String.class))).thenReturn(null);
        Response result = orderServiceImpl.getOrderById(UUID.randomUUID().toString(), headers);
        Assert.assertEquals(new Response<>(0, "Order Not Found", null), result);
    }

    @Test
    public void testGetOrderById2() {
        Order order = new Order();
        Mockito.when(orderRepository.findById(Mockito.any(String.class)).get()).thenReturn(order);
        Response result = orderServiceImpl.getOrderById(UUID.randomUUID().toString(), headers);
        Assert.assertEquals(new Response<>(1, "Success.", order), result);
    }

    @Test
    public void testCheckSecurityAboutOrder() {
        ArrayList<Order> orders = new ArrayList<>();
        Mockito.when(orderRepository.findByAccountId(Mockito.any(String.class))).thenReturn(orders);
        Response result = orderServiceImpl.checkSecurityAboutOrder(new Date(), UUID.randomUUID().toString(), headers);
        Assert.assertEquals(new Response<>(1, "Check Security Success . ", new OrderSecurity(0, 0)), result);
    }

    @Test
    public void testDeleteOrder1() {
        Mockito.when(orderRepository.findById(Mockito.any(String.class))).thenReturn(null);
        Response result = orderServiceImpl.deleteOrder(UUID.randomUUID().toString(), headers);
        Assert.assertEquals(new Response<>(0, "Order Not Exist.", null), result);
    }

    @Test
    public void testDeleteOrder2() {
        Order order = new Order();
        String orderUuid = UUID.randomUUID().toString();
        Mockito.when(orderRepository.findById(Mockito.any(String.class)).get()).thenReturn(order);
        Mockito.doNothing().doThrow(new RuntimeException()).when(orderRepository).deleteById(Mockito.any(String.class));
        Response result = orderServiceImpl.deleteOrder(orderUuid.toString(), headers);
        Assert.assertEquals(new Response<>(1, "Delete Order Success", order), result);
    }

    @Test
    public void testAddNewOrder1() {
        Order order = new Order();
        ArrayList<Order> accountOrders = new ArrayList<>();
        accountOrders.add(order);
        Mockito.when(orderRepository.findByAccountId(Mockito.any(String.class))).thenReturn(accountOrders);
        Response result = orderServiceImpl.addNewOrder(order, headers);
        Assert.assertEquals(new Response<>(0, "Order already exist", null), result);
    }

    @Test
    public void testAddNewOrder2() {
        Order order = new Order();
        ArrayList<Order> accountOrders = new ArrayList<>();
        Mockito.when(orderRepository.findByAccountId(Mockito.any(String.class))).thenReturn(accountOrders);
        Mockito.when(orderRepository.save(Mockito.any(Order.class))).thenReturn(null);
        Response result = orderServiceImpl.addNewOrder(order, headers);
        Assert.assertEquals("Add new Order Success", result.getMsg());
    }

    @Test
    public void testUpdateOrder1() {
        Order order = new Order();
        Mockito.when(orderRepository.findById(Mockito.any(String.class))).thenReturn(null);
        Response result = orderServiceImpl.updateOrder(order, headers);
        Assert.assertEquals(new Response<>(0, "Order Not Found, Can't update", null), result);
    }

    @Test
    public void testUpdateOrder2() {
        Order order = new Order();
        Mockito.when(orderRepository.findById(Mockito.any(String.class)).get()).thenReturn(order);
        Mockito.when(orderRepository.save(Mockito.any(Order.class))).thenReturn(null);
        Response result = orderServiceImpl.updateOrder(order, headers);
        Assert.assertEquals("Admin Update Order Success", result.getMsg());
    }

}


package gateway;

import com.alibaba.csp.sentinel.adapter.gateway.common.rule.GatewayFlowRule;
import com.alibaba.csp.sentinel.adapter.gateway.common.rule.GatewayRuleManager;
import com.alibaba.csp.sentinel.adapter.gateway.sc.SentinelGatewayFilter;
import com.alibaba.csp.sentinel.adapter.gateway.sc.callback.BlockRequestHandler;
import com.alibaba.csp.sentinel.adapter.gateway.sc.callback.GatewayCallbackManager;
import com.alibaba.csp.sentinel.adapter.gateway.sc.exception.SentinelGatewayBlockExceptionHandler;
import com.alibaba.csp.sentinel.slots.block.RuleConstant;
import org.springframework.beans.factory.ObjectProvider;
import org.springframework.cloud.gateway.filter.GlobalFilter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.Ordered;
import org.springframework.core.annotation.Order;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.codec.ServerCodecConfigurer;
import org.springframework.web.reactive.function.BodyInserters;
import org.springframework.web.reactive.function.server.ServerResponse;
import org.springframework.web.reactive.result.view.ViewResolver;

import javax.annotation.PostConstruct;
import java.util.*;

/**
 * 网关配置类
 *
 * <p>主要是<a href="https://sentinelguard.io/zh-cn/docs/api-gateway-flow-control.html">基于sentinel的网关限流策略配置</a></p>
 *
 * @author Akasaka Isami
 * @since 2022-06-30 15:13:58
 */

@Configuration
public class GatewayConfiguration {

    private final List<ViewResolver> viewResolvers;
    private final ServerCodecConfigurer serverCodecConfigurer;

    public GatewayConfiguration(ObjectProvider<List<ViewResolver>> viewResolversProvider,
                                ServerCodecConfigurer serverCodecConfigurer) {
        this.viewResolvers = viewResolversProvider.getIfAvailable(Collections::emptyList);
        this.serverCodecConfigurer = serverCodecConfigurer;
    }


    /**
     * 配置限流的异常处理器
     *
     * @return 限流的异常处理器
     */
    @Bean
    @Order(Ordered.HIGHEST_PRECEDENCE)
    public SentinelGatewayBlockExceptionHandler sentinelGatewayBlockExceptionHandler() {
        // Register the block exception handler for Spring Cloud Gateway.
        return new SentinelGatewayBlockExceptionHandler(viewResolvers, serverCodecConfigurer);
    }

    /**
     * 初始化一个限流的过滤器
     *
     * @return 限流过滤器
     */
    @Bean
    @Order(-1)
    public GlobalFilter sentinelGatewayFilter() {
        return new SentinelGatewayFilter();
    }

    /**
     * 配置初始化的限流参数
     */
    @PostConstruct
    public void doInit() {
        initGatewayRules();
//        initBlockHandlers();

        System.out.println("===== begin to do flow control");
        System.out.println("only 20 requests per second can pass");
    }

    /**
     * 注册函数用于实现自定义的逻辑处理被限流的请求
     *
     * <p>默认是返回错误信息： “Blocked by Sentinel: FlowException”。 这里自定义了异常处理，封装了自然语句。</p>
     */
    private void initBlockHandlers() {
        BlockRequestHandler blockRequestHandler = (serverWebExchange, throwable) -> {
            Map<Object, Object> map = new HashMap<>();
            map.put("code", 0);
            map.put("message", "接口被限流了");
            return ServerResponse.status(HttpStatus.OK).
                    contentType(MediaType.APPLICATION_JSON_UTF8).
                    body(BodyInserters.fromObject(map));
        };
        GatewayCallbackManager.setBlockHandler(blockRequestHandler);
    }


    /**
     * 初始化流量控制规则
     *
     * <p>Sentinal 的流量控制只能基于 route 或自定义 api 分组，这里的限流还是基于 application.yml 中定义的路由（即每个服务）采用 QPS 流量控制策略。
     * 当前是简单的对转发到 admin-basic-info-service 服务的流量做了QPS限制，每秒不超过20个请求。</p>
     */
    private void initGatewayRules() {
        Set<GatewayFlowRule> rules = new HashSet<>();

        // 对于转发到 admin-basic-info 的请求 set limit qps to 20
        // qps 超过 20 直接拒绝
        rules.add(new GatewayFlowRule("admin-basic-info") //资源名称，对应路由 id
                .setControlBehavior(RuleConstant.CONTROL_BEHAVIOR_DEFAULT)
                .setCount(20) // 限流qps阈值
                .setIntervalSec(1) // 统计时间窗口，单位是秒，默认是 1 秒
        );

        GatewayRuleManager.loadRules(rules);
    }
}


// Node: fromObject
// Node: setBlockHandler
package travel;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;
import org.springframework.cloud.client.loadbalancer.LoadBalanced;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.EnableAspectJAutoProxy;
import org.springframework.integration.annotation.IntegrationComponentScan;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.web.client.RestTemplate;
import springfox.documentation.swagger2.annotations.EnableSwagger2;

/**
 * @author fdse
 */
@SpringBootApplication
@EnableAspectJAutoProxy(proxyTargetClass = true)
@EnableAsync
@IntegrationComponentScan
@EnableSwagger2
@EnableDiscoveryClient
public class TravelApplication {

    public static void main(String[] args) {
        SpringApplication.run(TravelApplication.class, args);
    }

    @LoadBalanced
    @Bean
    public RestTemplate restTemplate(RestTemplateBuilder builder) {
        return builder.build();
    }
}


package travel.service;

import edu.fudan.common.entity.TravelInfo;
import edu.fudan.common.entity.TripAllDetailInfo;
import edu.fudan.common.entity.TripInfo;
import edu.fudan.common.util.Response;
import org.springframework.http.HttpHeaders;


import java.util.ArrayList;

/**
 * @author Chenjie Xu
 * @date 2017/5/9.
 */
public interface TravelService {

    Response create(TravelInfo info, HttpHeaders headers);

    Response retrieve(String tripId, HttpHeaders headers);

    Response update(TravelInfo info, HttpHeaders headers);

    Response delete(String tripId, HttpHeaders headers);

    Response query(TripInfo info, HttpHeaders headers);

    Response queryByBatch(TripInfo info, HttpHeaders headers);

    Response queryInParallel(TripInfo info, HttpHeaders headers);

    Response getTripAllDetailInfo(TripAllDetailInfo gtdi, HttpHeaders headers);

    Response getRouteByTripId(String tripId, HttpHeaders headers);

    Response getTrainTypeByTripId(String tripId, HttpHeaders headers);

    Response queryAll(HttpHeaders headers);

    Response getTripByRoute(ArrayList<String> routeIds, HttpHeaders headers);

    Response adminQueryAll(HttpHeaders headers);
}


// Node: repos/cloned_ms_repos/train-ticket/ts-travel-service/src/main/java/travel/service/TravelService.java:TravelService.<init>
package travel.service;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import edu.fudan.common.entity.*;
import edu.fudan.common.util.JsonUtils;
import edu.fudan.common.util.Response;
import edu.fudan.common.util.StringUtils;
import org.apache.skywalking.apm.toolkit.trace.TraceCrossThread;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.cloud.client.discovery.DiscoveryClient;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.ResponseEntity;
import org.springframework.scheduling.concurrent.CustomizableThreadFactory;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import travel.entity.AdminTrip;
import travel.entity.Travel;
import travel.entity.Trip;
import travel.entity.TripAllDetail;
import travel.repository.TripRepository;

import javax.transaction.Transactional;
import java.util.*;
import java.util.concurrent.*;

/**
 * @author fdse
 */
@Service
public class TravelServiceImpl implements TravelService {

    @Autowired
    private TripRepository repository;

    @Autowired
    private RestTemplate restTemplate;

    @Autowired
    private DiscoveryClient discoveryClient;

    private static final Logger LOGGER = LoggerFactory.getLogger(TravelServiceImpl.class);

    private static final ExecutorService executorService = Executors.newFixedThreadPool(20, new CustomizableThreadFactory("HttpClientThreadPool-"));

    private String getServiceUrl(String serviceName) {
        return "http://" + serviceName;
    }

    String success = "Success";
    String noContent = "No Content";

    @Override
    public Response create(TravelInfo info, HttpHeaders headers) {
        TripId ti = new TripId(info.getTripId());
        if (repository.findByTripId(ti) == null) {
            Trip trip = new Trip(ti, info.getTrainTypeName(), info.getStartStationName(),
                    info.getStationsName(), info.getTerminalStationName(), info.getStartTime(), info.getEndTime());
            trip.setRouteId(info.getRouteId());
            repository.save(trip);
            return new Response<>(1, "Create trip:" + ti.toString() + ".", null);
        } else {
            TravelServiceImpl.LOGGER.error("[create][Create trip error][Trip already exists][TripId: {}]", info.getTripId());
            return new Response<>(1, "Trip " + info.getTripId().toString() + " already exists", null);
        }
    }

    @Override
    public Response getRouteByTripId(String tripId, HttpHeaders headers) {
        Route route = null;
        if (null != tripId && tripId.length() >= 2) {
            TripId tripId1 = new TripId(tripId);
            Trip trip = repository.findByTripId(tripId1);
            if (trip != null) {
                route = getRouteByRouteId(trip.getRouteId(), headers);
            } else {
                TravelServiceImpl.LOGGER.error("[getRouteByTripId][Get route by Trip id error][Trip not found][TripId: {}]", tripId);
            }
        }
        if (route != null) {
            return new Response<>(1, success, route);
        } else {
            TravelServiceImpl.LOGGER.error("[getRouteByTripId][Get route by Trip id error][Route not found][TripId: {}]", tripId);
            return new Response<>(0, noContent, null);
        }
    }

    @Override
    public Response getTrainTypeByTripId(String tripId, HttpHeaders headers) {
        TripId tripId1 = new TripId(tripId);
        TrainType trainType = null;
        Trip trip = repository.findByTripId(tripId1);
        if (trip != null) {
            trainType = getTrainTypeByName(trip.getTrainTypeName(), headers);
        } else {
            TravelServiceImpl.LOGGER.error("[getTrainTypeByTripId][Get Train Type by Trip id error][Trip not found][TripId: {}]", tripId);
        }
        if (trainType != null) {
            return new Response<>(1, success, trainType);
        } else {
            TravelServiceImpl.LOGGER.error("[getTrainTypeByTripId][Get Train Type by Trip id error][Train Type not found][TripId: {}]", tripId);
            return new Response<>(0, noContent, null);
        }
    }

    @Override
    public Response getTripByRoute(ArrayList<String> routeIds, HttpHeaders headers) {
        ArrayList<ArrayList<Trip>> tripList = new ArrayList<>();
        for (String routeId : routeIds) {
            ArrayList<Trip> tempTripList = repository.findByRouteId(routeId);
            if (tempTripList == null) {
                tempTripList = new ArrayList<>();
            }
            tripList.add(tempTripList);
        }
        if (!tripList.isEmpty()) {
            return new Response<>(1, success, tripList);
        } else {
            TravelServiceImpl.LOGGER.warn("[getTripByRoute][Get trips by routes warn][Trip list][{}]", "No content");
            return new Response<>(0, noContent, null);
        }
    }


    @Override
    public Response retrieve(String tripId, HttpHeaders headers) {
        TripId ti = new TripId(tripId);
        Trip trip = repository.findByTripId(ti);
        if (trip != null) {
            return new Response<>(1, "Search Trip Success by Trip Id " + tripId, trip);
        } else {
            TravelServiceImpl.LOGGER.error("[retrieve][Retrieve trip error][Trip not found][TripId: {}]", tripId);
            return new Response<>(0, "No Content according to tripId" + tripId, null);
        }
    }

    @Override
    public Response update(TravelInfo info, HttpHeaders headers) {
        TripId ti = new TripId(info.getTripId());
        Trip t = repository.findByTripId(ti);
        if (t != null) {
            t.setStartStationName(info.getTrainTypeName());
            t.setStartStationName( info.getStartStationName());
            t.setStationsName(info.getStationsName());
            t.setTerminalStationName(info.getTerminalStationName());
            t.setStartTime(info.getStartTime());
            t.setEndTime(info.getEndTime());
            t.setRouteId(info.getRouteId());
            repository.save(t);
            return new Response<>(1, "Update trip:" + ti.toString(), t);
        } else {
            TravelServiceImpl.LOGGER.error("[update][Update trip error][Trip not found][TripId: {}]", info.getTripId());
            return new Response<>(1, "Trip" + info.getTripId().toString() + "doesn 't exists", null);
        }
    }

    @Override
    @Transactional
    public Response delete(String tripId, HttpHeaders headers) {
        TripId ti = new TripId(tripId);
        if (repository.findByTripId(ti) != null) {
            repository.deleteByTripId(ti);
            return new Response<>(1, "Delete trip:" + tripId + ".", tripId);
        } else {
            TravelServiceImpl.LOGGER.error("[delete][Delete trip error][Trip not found][TripId: {}]", tripId);
            return new Response<>(0, "Trip " + tripId + " doesn't exist.", null);
        }
    }

    @Override
    public Response query(TripInfo info, HttpHeaders headers) {

        //Gets the start and arrival stations of the train number to query. The originating and arriving stations received here are both station names, so two requests need to be sent to convert to station ids
        String startPlaceName = info.getStartPlace();
        String endPlaceName = info.getEndPlace();

        //This is the final result
        List<TripResponse> list = new ArrayList<>();

        //Check all train info
        List<Trip> allTripList = repository.findAll();
        if(allTripList != null) {
            for (Trip tempTrip : allTripList) {
                //Get the detailed route list of this train
                TripResponse response = getTickets(tempTrip, null, startPlaceName, endPlaceName, info.getDepartureTime(), headers);
                if (response == null) {
                    TravelServiceImpl.LOGGER.warn("[query][Query trip error][Tickets not found][start: {},end: {},time: {}]", startPlaceName, endPlaceName, info.getDepartureTime());
                }else{
                    list.add(response);
                }
            }
        }
        return new Response<>(1, success, list);
    }



    @Override
    public Response queryByBatch(TripInfo info, HttpHeaders headers) {

        //Gets the start and arrival stations of the train number to query. The originating and arriving stations received here are both station names, so two requests need to be sent to convert to station ids
        String startPlaceName = info.getStartPlace();
        String endPlaceName = info.getEndPlace();

        //This is the final result
        List<TripResponse> list = new ArrayList<>();

        //Check all train info
        List<Trip> allTripList = repository.findAll();
        list = getTicketsByBatch(allTripList, startPlaceName, endPlaceName, info.getDepartureTime(), headers);
        return new Response<>(1, success, list);
    }

    @TraceCrossThread
    class MyCallable implements Callable<TripResponse> {
        private TripInfo info;
        private Trip tempTrip;
        private HttpHeaders headers;
        private String startPlaceName;
        private String endPlaceName;

        MyCallable(TripInfo info, String startPlaceName, String endPlaceName, Trip tempTrip, HttpHeaders headers) {
            this.info = info;
            this.tempTrip = tempTrip;
            this.headers = headers;
            this.startPlaceName = startPlaceName;
            this.endPlaceName = endPlaceName;
        }

        @Override
        public TripResponse call() throws Exception {
            TravelServiceImpl.LOGGER.debug("[call][Start to query][tripId: {}, routeId: {}] ", tempTrip.getTripId().toString(), tempTrip.getRouteId());

            String startPlaceName = info.getStartPlace();
            String endPlaceName = info.getEndPlace();
            //Route tempRoute = getRouteByRouteId(tempTrip.getRouteId(), headers);

            TripResponse response = null;

            response = getTickets(tempTrip, null, startPlaceName, endPlaceName, info.getDepartureTime(), headers);

            if (response == null) {
                TravelServiceImpl.LOGGER.warn("[call][Query trip error][Tickets not found][tripId: {}, routeId: {}, start: {}, end: {},time: {}]", tempTrip.getTripId().toString(), tempTrip.getRouteId(), startPlaceName, endPlaceName, info.getDepartureTime());
            } else {
                TravelServiceImpl.LOGGER.info("[call][Query trip success][tripId: {}, routeId: {}] ", tempTrip.getTripId().toString(), tempTrip.getRouteId());
            }
            return response;
        }
    }

    @Override
    public Response queryInParallel(TripInfo info, HttpHeaders headers) {
        //Gets the start and arrival stations of the train number to query. The originating and arriving stations received here are both station names, so two requests need to be sent to convert to station ids
        String startPlaceName = info.getStartPlace();
        String endPlaceName = info.getEndPlace();

        //This is the final result
        List<TripResponse> list = new ArrayList<>();

        //Check all train info
        List<Trip> allTripList = repository.findAll();
        List<Future<TripResponse>> futureList = new ArrayList<>();

        if(allTripList != null ){
            for (Trip tempTrip : allTripList) {
                MyCallable callable = new MyCallable(info, startPlaceName, endPlaceName, tempTrip, headers);
                Future<TripResponse> future = executorService.submit(callable);
                futureList.add(future);
            }
        }

        for (Future<TripResponse> future : futureList) {
            try {
                TripResponse response = future.get();
                if (response != null) {
                    list.add(response);
                }
            } catch (Exception e) {
                TravelServiceImpl.LOGGER.error("[queryInParallel][Query error]"+e.toString());
            }
        }

        if (list.isEmpty()) {
            return new Response<>(0, "No Trip info content", null);
        } else {
            return new Response<>(1, success, list);
        }
    }

    @Override
    public Response getTripAllDetailInfo(TripAllDetailInfo gtdi, HttpHeaders headers) {
        TripAllDetail gtdr = new TripAllDetail();
        TravelServiceImpl.LOGGER.debug("[getTripAllDetailInfo][TripId: {}]", gtdi.getTripId());
        Trip trip = repository.findByTripId(new TripId(gtdi.getTripId()));
        if (trip == null) {
            gtdr.setTripResponse(null);
            gtdr.setTrip(null);
            TravelServiceImpl.LOGGER.error("[getTripAllDetailInfo][Get trip detail error][Trip not found][TripId: {}]", gtdi.getTripId());
            return new Response<>(0, "Trip not found", gtdr);
        } else {
            String startPlaceName = gtdi.getFrom();
            String endPlaceName = gtdi.getTo();
            TripResponse tripResponse = getTickets(trip, null, startPlaceName, endPlaceName, gtdi.getTravelDate(), headers);
            if (tripResponse == null) {
                gtdr.setTripResponse(null);
                gtdr.setTrip(null);
                TravelServiceImpl.LOGGER.warn("[getTripAllDetailInfo][Get trip detail error][Tickets not found][start: {},end: {},time: {}]", startPlaceName, endPlaceName, gtdi.getTravelDate());
                return new Response<>(0, "getTickets failed", gtdr);
            } else {
                gtdr.setTripResponse(tripResponse);
                gtdr.setTrip(repository.findByTripId(new TripId(gtdi.getTripId())));
            }
        }
        return new Response<>(1, success, gtdr);
    }

    private List<TripResponse> getTicketsByBatch(List<Trip> trips, String startPlaceName, String endPlaceName, String departureTime, HttpHeaders headers) {
        List<TripResponse> responses = new ArrayList<>();
        //Determine if the date checked is the same day and after
        if (!afterToday(departureTime)) {
            TravelServiceImpl.LOGGER.info("[getTickets][depaturetime not vailid][departuretime: {}]", departureTime);
            return responses;
        }

        List<Travel> infos = new ArrayList<>();
        Map<String, Trip> tripMap = new HashMap<>();
        for(Trip trip: trips){
            Travel query = new Travel();
            query.setTrip(trip);
            query.setStartPlace(startPlaceName);
            query.setEndPlace(endPlaceName);
            query.setDepartureTime(departureTime);

            infos.add(query);
            tripMap.put(trip.getTripId().toString(), trip);
        }

        TravelServiceImpl.LOGGER.info("[getTicketsByBatch][before get basic][trips: {}]", trips);

        HttpEntity requestEntity = new HttpEntity(infos, null);
        String basic_service_url = getServiceUrl("ts-basic-service");
        ResponseEntity<Response> re = restTemplate.exchange(
                basic_service_url + "/api/v1/basicservice/basic/travels",
                HttpMethod.POST,
                requestEntity,
                Response.class);

        Response r = re.getBody();
        if(r.getStatus() == 0){
            TravelServiceImpl.LOGGER.info("[getTicketsByBatch][Ts-basic-service response status is 0][response is: {}]", r);
            return responses;
        }
        Map<String, TravelResult> trMap;
        ObjectMapper mapper = new ObjectMapper();
        try{
            trMap = mapper.readValue(JsonUtils.object2Json(r.getData()), new TypeReference<Map<String, TravelResult>>(){});
        }catch(Exception e) {
            TravelServiceImpl.LOGGER.warn("[getTicketsByBatch][Ts-basic-service convert data failed][Fail msg: {}]", e.getMessage());
            return responses;
        }

        for(Map.Entry<String, TravelResult> trEntry: trMap.entrySet()){
            //Set the returned ticket information
            String tripNumber = trEntry.getKey();
            TravelResult tr = trEntry.getValue();
            Trip trip = tripMap.get(tripNumber);

            TripResponse response = setResponse(trip, tr, startPlaceName, endPlaceName, departureTime, headers);
            responses.add(response);
        }
        return responses;
    }

    private TripResponse getTickets(Trip trip, Route route1, String startPlaceName, String endPlaceName, String departureTime, HttpHeaders headers) {

        //Determine if the date checked is the same day and after
        if (!afterToday(departureTime)) {
            TravelServiceImpl.LOGGER.info("[getTickets][depaturetime not vailid][departuretime: {}]", departureTime);
            return null;
        }

        Travel query = new Travel();
        query.setTrip(trip);
        query.setStartPlace(startPlaceName);
        query.setEndPlace(endPlaceName);
        query.setDepartureTime(departureTime);
        TravelServiceImpl.LOGGER.info("[getTickets][before get basic][trip: {}]", trip);

        HttpEntity requestEntity = new HttpEntity(query, null);
        String basic_service_url = getServiceUrl("ts-basic-service");
        ResponseEntity<Response> re = restTemplate.exchange(
                basic_service_url + "/api/v1/basicservice/basic/travel",
                HttpMethod.POST,
                requestEntity,
                Response.class);

        Response r = re.getBody();
        if(r.getStatus() == 0){
            TravelServiceImpl.LOGGER.info("[getTickets][Ts-basic-service response status is 0][response is: {}]", r);
            return null;
        }

        TravelResult resultForTravel = JsonUtils.conveterObject(re.getBody().getData(), TravelResult.class);

        //Set the returned ticket information
        return setResponse(trip, resultForTravel, startPlaceName, endPlaceName, departureTime, headers);
    }

    private TripResponse setResponse(Trip trip, TravelResult tr, String startPlaceName, String endPlaceName, String departureTime, HttpHeaders headers){
        //Set the returned ticket information
        TripResponse response = new TripResponse();
        response.setConfortClass(50);
        response.setEconomyClass(50);

        Route route = tr.getRoute();
        List<String> stationList = route.getStations();

        int firstClassTotalNum = tr.getTrainType().getConfortClass();
        int secondClassTotalNum = tr.getTrainType().getEconomyClass();

        int first = getRestTicketNumber(departureTime, trip.getTripId().toString(),
                startPlaceName, endPlaceName, SeatClass.FIRSTCLASS.getCode(), firstClassTotalNum, stationList, headers);

        int second = getRestTicketNumber(departureTime, trip.getTripId().toString(),
                startPlaceName, endPlaceName, SeatClass.SECONDCLASS.getCode(), secondClassTotalNum, stationList, headers);
        response.setConfortClass(first);
        response.setEconomyClass(second);

        response.setStartStation(startPlaceName);
        response.setTerminalStation(endPlaceName);

        //Calculate the distance from the starting point
        int indexStart = route.getStations().indexOf(startPlaceName);
        int indexEnd = route.getStations().indexOf(endPlaceName);
        int distanceStart = route.getDistances().get(indexStart) - route.getDistances().get(0);
        int distanceEnd = route.getDistances().get(indexEnd) - route.getDistances().get(0);
        TrainType trainType = tr.getTrainType();
        //Train running time is calculated according to the average running speed of the train
        int minutesStart = 60 * distanceStart / trainType.getAverageSpeed();
        int minutesEnd = 60 * distanceEnd / trainType.getAverageSpeed();

        Calendar calendarStart = Calendar.getInstance();
        calendarStart.setTime(StringUtils.String2Date(trip.getStartTime()));
        calendarStart.add(Calendar.MINUTE, minutesStart);
        response.setStartTime(StringUtils.Date2String(calendarStart.getTime()));
        TravelServiceImpl.LOGGER.info("[getTickets][Calculate distance][calculate time：{}  time: {}]", minutesStart, calendarStart.getTime());

        Calendar calendarEnd = Calendar.getInstance();
        calendarEnd.setTime(StringUtils.String2Date(trip.getStartTime()));
        calendarEnd.add(Calendar.MINUTE, minutesEnd);
        response.setEndTime(StringUtils.Date2String(calendarEnd.getTime()));
        TravelServiceImpl.LOGGER.info("[getTickets][Calculate distance][calculate time：{}  time: {}]", minutesEnd, calendarEnd.getTime());

        response.setTripId(trip.getTripId());
        response.setTrainTypeName(trip.getTrainTypeName());
        response.setPriceForConfortClass(tr.getPrices().get("confortClass"));
        response.setPriceForEconomyClass(tr.getPrices().get("economyClass"));

        return response;
    }

    @Override
    public Response queryAll(HttpHeaders headers) {
        List<Trip> tripList = repository.findAll();
        if (tripList != null && !tripList.isEmpty()) {
            TravelServiceImpl.LOGGER.info("[queryAll][Query all trips:][{}]", "tripList");
            return new Response<>(1, success, tripList);
        }
        TravelServiceImpl.LOGGER.warn("[queryAll][Query all trips warn][{}]", "No Content");
        return new Response<>(0, noContent, null);
    }

    private static boolean afterToday(String date) {
        Calendar calDateA = Calendar.getInstance();
        Date today = new Date();
        calDateA.setTime(today);

        Calendar calDateB = Calendar.getInstance();
        calDateB.setTime(StringUtils.String2Date(date));

        TravelServiceImpl.LOGGER.info("[today date][y: {}][m:{}][d: {}]",calDateA.get(Calendar.YEAR), calDateA.get(Calendar.MONTH), calDateA.get(Calendar.DATE));
        TravelServiceImpl.LOGGER.info("[departrue date][y: {}][m:{}][d: {}]",calDateB.get(Calendar.YEAR), calDateB.get(Calendar.MONTH), calDateB.get(Calendar.DATE));

        if (calDateA.get(Calendar.YEAR) > calDateB.get(Calendar.YEAR)) {
            return false;
        } else if (calDateA.get(Calendar.YEAR) == calDateB.get(Calendar.YEAR)) {
            if (calDateA.get(Calendar.MONTH) > calDateB.get(Calendar.MONTH)) {
                return false;
            } else if (calDateA.get(Calendar.MONTH) == calDateB.get(Calendar.MONTH)) {
                return calDateA.get(Calendar.DAY_OF_MONTH) <= calDateB.get(Calendar.DAY_OF_MONTH);
            } else {
                return true;
            }
        } else {
            return true;
        }
    }

    private TrainType getTrainTypeByName(String trainTypeName, HttpHeaders headers) {
        HttpEntity requestEntity = new HttpEntity(null);
        String train_service_url = getServiceUrl("ts-train-service");
        ResponseEntity<Response<TrainType>> re = restTemplate.exchange(
                train_service_url + "/api/v1/trainservice/trains/byName/" + trainTypeName,
                HttpMethod.GET,
                requestEntity,
                new ParameterizedTypeReference<Response<TrainType>>() {
                });

        return re.getBody().getData();
    }

    private Route getRouteByRouteId(String routeId, HttpHeaders headers) {
        TravelServiceImpl.LOGGER.info("[getRouteByRouteId][Get Route By Id][Route ID：{}]", routeId);
        HttpEntity requestEntity = new HttpEntity(null);
        String route_service_url = getServiceUrl("ts-route-service");
        ResponseEntity<Response> re = restTemplate.exchange(
                route_service_url + "/api/v1/routeservice/routes/" + routeId,
                HttpMethod.GET,
                requestEntity,
                Response.class);
        Response routeRes = re.getBody();

        Route route1 = new Route();
        TravelServiceImpl.LOGGER.info("[getRouteByRouteId][Get Route By Id][Routes Response is : {}]", routeRes.toString());
        if (routeRes.getStatus() == 1) {
            route1 = JsonUtils.conveterObject(routeRes.getData(), Route.class);
            TravelServiceImpl.LOGGER.info("[getRouteByRouteId][Get Route By Id][Route is: {}]", route1.toString());
        }
        return route1;
    }

    private int getRestTicketNumber(String travelDate, String trainNumber, String startStationName, String endStationName, int seatType, int totalNum, List<String> stationList, HttpHeaders headers) {
        Seat seatRequest = new Seat();

        seatRequest.setDestStation(endStationName);
        seatRequest.setStartStation(startStationName);
        seatRequest.setTrainNumber(trainNumber);
        seatRequest.setTravelDate(travelDate);
        seatRequest.setSeatType(seatType);
        seatRequest.setTotalNum(totalNum);
        seatRequest.setStations(stationList);

        TravelServiceImpl.LOGGER.info("[getRestTicketNumber][Seat request][request: {}]", seatRequest.toString());

        HttpEntity requestEntity = new HttpEntity(seatRequest, null);
        String seat_service_url = getServiceUrl("ts-seat-service");
        ResponseEntity<Response<Integer>> re = restTemplate.exchange(
                seat_service_url + "/api/v1/seatservice/seats/left_tickets",
                HttpMethod.POST,
                requestEntity,
                new ParameterizedTypeReference<Response<Integer>>() {
                });
        TravelServiceImpl.LOGGER.info("[getRestTicketNumber][Get Rest tickets num][num is: {}]", re.getBody().toString());

        return re.getBody().getData();
    }

    @Override
    public Response adminQueryAll(HttpHeaders headers) {
        List<Trip> trips = repository.findAll();
        ArrayList<AdminTrip> adminTrips = new ArrayList<>();
        if(trips != null){
            for (Trip trip : trips) {
                AdminTrip adminTrip = new AdminTrip();
                adminTrip.setTrip(trip);
                adminTrip.setRoute(getRouteByRouteId(trip.getRouteId(), headers));
                adminTrip.setTrainType(getTrainTypeByName(trip.getTrainTypeName(), headers));
                adminTrips.add(adminTrip);
            }
        }

        if (!adminTrips.isEmpty()) {
            return new Response<>(1, success, adminTrips);
        } else {
            TravelServiceImpl.LOGGER.warn("[adminQueryAll][Admin query all trips warn][{}]", "No Content");
            return new Response<>(0, noContent, null);
        }
    }
}


package travel.controller;

import com.alibaba.fastjson.JSONObject;
import edu.fudan.common.entity.*;
import edu.fudan.common.entity.TravelInfo;
import edu.fudan.common.entity.TripAllDetailInfo;
import edu.fudan.common.entity.TripInfo;
import edu.fudan.common.entity.TripResponse;
import edu.fudan.common.util.Response;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.springframework.http.*;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.request.MockMvcRequestBuilders;
import org.springframework.test.web.servlet.result.MockMvcResultMatchers;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import travel.entity.Travel;
import travel.entity.AdminTrip;
import travel.service.TravelService;

import java.util.ArrayList;
import java.util.Date;

@RunWith(JUnit4.class)
public class TravelControllerTest {

    @InjectMocks
    private TravelController travelController;

    @Mock
    private TravelService service;
    private MockMvc mockMvc;
    private Response response = new Response();

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
        mockMvc = MockMvcBuilders.standaloneSetup(travelController).build();
    }

    @Test
    public void testHome() throws Exception {
        mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/travelservice/welcome"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andExpect(MockMvcResultMatchers.content().string("Welcome to [ Travel Service ] !"));
    }

    @Test
    public void testGetTrainTypeByTripId() throws Exception {
        Mockito.when(service.getTrainTypeByTripId(Mockito.anyString(), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/travelservice/train_types/trip_id"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testGetRouteByTripId() throws Exception {
        Mockito.when(service.getRouteByTripId(Mockito.anyString(), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/travelservice/routes/trip_id"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testGetTripsByRouteId() throws Exception {
        ArrayList<String> routeIds = new ArrayList<>();
        Mockito.when(service.getTripByRoute(Mockito.any(ArrayList.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(routeIds);
        String result = mockMvc.perform(MockMvcRequestBuilders.post("/api/v1/travelservice/trips/routes").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testCreateTrip() throws Exception {
        TravelInfo routeIds = new TravelInfo();
        Mockito.when(service.create(Mockito.any(TravelInfo.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(routeIds);
        String result = mockMvc.perform(MockMvcRequestBuilders.post("/api/v1/travelservice/trips").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isCreated())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testRetrieve() throws Exception {
        Mockito.when(service.retrieve(Mockito.anyString(), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/travelservice/trips/trip_id"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testUpdateTrip() throws Exception {
        TravelInfo info = new TravelInfo();
        Mockito.when(service.update(Mockito.any(TravelInfo.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(info);
        String result = mockMvc.perform(MockMvcRequestBuilders.put("/api/v1/travelservice/trips").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testDeleteTrip() throws Exception {
        Mockito.when(service.delete(Mockito.anyString(), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.delete("/api/v1/travelservice/trips/trip_id"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testQueryInfo1() throws Exception {
        TripInfo info = new TripInfo();
        ArrayList<TripResponse> errorList = new ArrayList<>();
        String requestJson = JSONObject.toJSONString(info);
        String result = mockMvc.perform(MockMvcRequestBuilders.post("/api/v1/travelservice/trips/left").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(errorList, JSONObject.parseObject(result, ArrayList.class));
    }

    @Test
    public void testQueryInfo2() throws Exception {
        TripInfo info = new TripInfo("startPlace", "endPlace", "");
        Mockito.when(service.query(Mockito.any(TripInfo.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(info);
        String result = mockMvc.perform(MockMvcRequestBuilders.post("/api/v1/travelservice/trips/left").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testGetTripAllDetailInfo() throws Exception {
        TripAllDetailInfo gtdi = new TripAllDetailInfo();
        Mockito.when(service.getTripAllDetailInfo(Mockito.any(TripAllDetailInfo.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(gtdi);
        String result = mockMvc.perform(MockMvcRequestBuilders.post("/api/v1/travelservice/trip_detail").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testQueryAll() throws Exception {
        Mockito.when(service.queryAll(Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/travelservice/trips"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testAdminQueryAll() throws Exception {
        Mockito.when(service.adminQueryAll(Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/travelservice/admin_trip"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

}


package travel.service;

import edu.fudan.common.entity.*;
import edu.fudan.common.util.Response;
import edu.fudan.common.util.StringUtils;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.*;
import org.springframework.web.client.RestTemplate;
import travel.entity.*;
import travel.entity.Trip;
import travel.repository.TripRepository;

import java.util.ArrayList;
import java.util.Date;

@RunWith(JUnit4.class)
public class TravelServiceImplTest {

    @InjectMocks
    private TravelServiceImpl travelServiceImpl;

    @Mock
    private TripRepository repository;

    @Mock
    private RestTemplate restTemplate;

    private HttpHeaders headers = new HttpHeaders();
    String success = "Success";
    String noCnontent = "No Content";

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
    }

    @Test
    public void testGetRouteByTripId1() {
        Mockito.when(repository.findByTripId(Mockito.any(TripId.class))).thenReturn(null);
        Response result = travelServiceImpl.getRouteByTripId("K1255", headers);
        Assert.assertEquals(new Response<>(0, "No Content", null), result);
    }

    @Test
    public void testGetRouteByTripId2() {
        Trip trip = new Trip();
        Mockito.when(repository.findByTripId(Mockito.any(TripId.class))).thenReturn(trip);
        //mock getRouteByRouteId()
        Route route = new Route();
        Response response = new Response(1, null, route);
        ResponseEntity<Response> re = new ResponseEntity<>(response, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                Mockito.anyString(),
                Mockito.any(HttpMethod.class),
                Mockito.any(HttpEntity.class),
                Mockito.any(Class.class)))
                .thenReturn(re);
        Response result = travelServiceImpl.getRouteByTripId("K1255", headers);
        Assert.assertEquals("Success", result.getMsg());
    }

    @Test
    public void testGetTrainTypeByTripId() {
        Trip trip = new Trip();
        Mockito.when(repository.findByTripId(Mockito.any(TripId.class))).thenReturn(trip);
        //mock getTrainType()
        TrainType trainType = new TrainType();
        Response<TrainType> response = new Response<>(null, null, trainType);
        ResponseEntity<Response<TrainType>> re = new ResponseEntity<>(response, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                Mockito.anyString(),
                Mockito.any(HttpMethod.class),
                Mockito.any(HttpEntity.class),
                Mockito.any(ParameterizedTypeReference.class)))
                .thenReturn(re);
        Response result = travelServiceImpl.getTrainTypeByTripId("K1255", headers);
        Assert.assertEquals(new Response<>(1, "Success", trainType), result);
    }

    @Test
    public void testGetTripByRoute1() {
        ArrayList<String> routeIds = new ArrayList<>();
        Response result = travelServiceImpl.getTripByRoute(routeIds, headers);
        Assert.assertEquals(new Response<>(0, noCnontent, null), result);
    }

    @Test
    public void testGetTripByRoute2() {
        ArrayList<String> routeIds = new ArrayList<>();
        routeIds.add("route_id_1");
        Mockito.when(repository.findByRouteId(Mockito.anyString())).thenReturn(null);
        Response result = travelServiceImpl.getTripByRoute(routeIds, headers);
        Assert.assertEquals(success, result.getMsg());
    }

    @Test
    public void testCreate1() {
        TravelInfo info = new TravelInfo();
        info.setTripId("G");
        Mockito.when(repository.findByTripId(Mockito.any(TripId.class))).thenReturn(null);
        Mockito.when(repository.save(Mockito.any(Trip.class))).thenReturn(null);
        Response result = travelServiceImpl.create(info, headers);
        Assert.assertEquals(new Response<>(1, "Create trip:G.", null), result);
    }

    @Test
    public void testCreate2() {
        TravelInfo info = new TravelInfo();
        info.setTripId("G");
        Trip trip = new Trip();
        Mockito.when(repository.findByTripId(Mockito.any(TripId.class))).thenReturn(trip);
        Response result = travelServiceImpl.create(info, headers);
        Assert.assertEquals(new Response<>(1, "Trip G already exists", null), result);
    }

    @Test
    public void testRetrieve1() {
        Trip trip = new Trip();
        Mockito.when(repository.findByTripId(Mockito.any(TripId.class))).thenReturn(trip);
        Response result = travelServiceImpl.retrieve("trip_id_1", headers);
        Assert.assertEquals(new Response<>(1, "Search Trip Success by Trip Id trip_id_1", trip), result);
    }

    @Test
    public void testRetrieve2() {
        Trip trip = new Trip();
        Mockito.when(repository.findByTripId(Mockito.any(TripId.class))).thenReturn(trip);
        Response result = travelServiceImpl.retrieve("trip_id_1", headers);
        Assert.assertEquals(new Response<>(1, "Search Trip Success by Trip Id trip_id_1", trip), result);
    }

    @Test
    public void testUpdate1() {
        TravelInfo info = new TravelInfo();
        info.setTripId("G");
        Trip trip = new Trip();
        Mockito.when(repository.findByTripId(Mockito.any(TripId.class))).thenReturn(trip);
        Mockito.when(repository.save(Mockito.any(Trip.class))).thenReturn(null);
        Response result = travelServiceImpl.update(info, headers);
        Assert.assertEquals("Update trip:G", result.getMsg());
    }

    @Test
    public void testUpdate2() {
        TravelInfo info = new TravelInfo();
        info.setTripId("G");
        Mockito.when(repository.findByTripId(Mockito.any(TripId.class))).thenReturn(null);
        Response result = travelServiceImpl.update(info, headers);
        Assert.assertEquals(new Response<>(1, "TripGdoesn 't exists", null), result);
    }

    @Test
    public void testDelete1() {
        Trip trip = new Trip();
        Mockito.when(repository.findByTripId(Mockito.any(TripId.class))).thenReturn(trip);
        Mockito.doNothing().doThrow(new RuntimeException()).when(repository).deleteByTripId(Mockito.any(TripId.class));
        Response result = travelServiceImpl.delete("trip_id_1", headers);
        Assert.assertEquals(new Response<>(1, "Delete trip:trip_id_1.", "trip_id_1"), result);
    }

    @Test
    public void testDelete2() {
        Mockito.when(repository.findByTripId(Mockito.any(TripId.class))).thenReturn(null);
        Response result = travelServiceImpl.delete("trip_id_1", headers);
        Assert.assertEquals(new Response<>(0, "Trip trip_id_1 doesn't exist.", null), result);
    }

    @Test
    public void testQuery() {
        TripInfo info = new TripInfo();
        //mock queryForStationId()
        Response<String> response1 = new Response<>(null, null, "");
        ResponseEntity<Response<String>> re1 = new ResponseEntity<>(response1, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                Mockito.anyString(),
                Mockito.any(HttpMethod.class),
                Mockito.any(HttpEntity.class),
                Mockito.any(ParameterizedTypeReference.class)))
                .thenReturn(re1);

        ArrayList<Trip> tripList = new ArrayList<>();
        Trip trip = new Trip();
        trip.setRouteId("route_id");
        tripList.add(trip);
        Mockito.when(repository.findAll()).thenReturn(tripList);

        //mock getRouteByRouteId()
        Route route = new Route();
        route.setStations(new ArrayList<>());
        Response response2 = new Response(1, null, route);
        ResponseEntity<Response> re2 = new ResponseEntity<>(response2, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                Mockito.anyString(),
                Mockito.any(HttpMethod.class),
                Mockito.any(HttpEntity.class),
                Mockito.any(Class.class)))
                .thenReturn(re2);
        Response result = travelServiceImpl.query(info, headers);
        Assert.assertEquals(new Response<>(1, "Success", new ArrayList<>()), result);
    }

    @Test
    public void testGetTripAllDetailInfo() {
        TripAllDetailInfo gtdi = new TripAllDetailInfo();
        gtdi.setTripId("Z1255");
        gtdi.setFrom("from_station");
        gtdi.setTo("to_station");
        gtdi.setTravelDate(StringUtils.Date2String(new Date(System.currentTimeMillis() - 86400000)));

        Trip trip = new Trip();
        trip.setRouteId("route_id");
        Mockito.when(repository.findByTripId(Mockito.any(TripId.class))).thenReturn(trip);

        //mock queryForStationId()
        Response<String> response1 = new Response<>(null, null, "");
        ResponseEntity<Response<String>> re1 = new ResponseEntity<>(response1, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                Mockito.anyString(),
                Mockito.any(HttpMethod.class),
                Mockito.any(HttpEntity.class),
                Mockito.any(ParameterizedTypeReference.class)))
                .thenReturn(re1);

        //mock getRouteByRouteId()
        Route route = new Route();
        route.setStations(new ArrayList<>());
        Response response2 = new Response(1, null, route);
        ResponseEntity<Response> re2 = new ResponseEntity<>(response2, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                Mockito.anyString(),
                Mockito.any(HttpMethod.class),
                Mockito.any(HttpEntity.class),
                Mockito.any(Class.class)))
                .thenReturn(re2);
        Response result = travelServiceImpl.getTripAllDetailInfo(gtdi, headers);
        Assert.assertEquals("Success", result.getMsg());
    }

    @Test
    public void testQueryAll1() {
        ArrayList<Trip> tripList = new ArrayList<>();
        tripList.add(new Trip());
        Mockito.when(repository.findAll()).thenReturn(tripList);
        Response result = travelServiceImpl.queryAll(headers);
        Assert.assertEquals(new Response<>(1, success, tripList), result);
    }

    @Test
    public void testQueryAll2() {
        Mockito.when(repository.findAll()).thenReturn(null);
        Response result = travelServiceImpl.queryAll(headers);
        Assert.assertEquals(new Response<>(0, noCnontent, null), result);
    }

    @Test
    public void testAdminQueryAll1() {
        ArrayList<Trip> tripList = new ArrayList<>();
        Trip trip = new Trip();
        trip.setRouteId("route_id");
        tripList.add(trip);
        Mockito.when(repository.findAll()).thenReturn(tripList);

        //mock getRouteByRouteId()
        Route route = new Route();
        Response response2 = new Response(1, null, route);
        ResponseEntity<Response> re2 = new ResponseEntity<>(response2, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                Mockito.anyString(),
                Mockito.any(HttpMethod.class),
                Mockito.any(HttpEntity.class),
                Mockito.any(Class.class)))
                .thenReturn(re2);

        //mock getTrainType()
        TrainType trainType = new TrainType();
        Response<TrainType> response = new Response<>(null, null, trainType);
        ResponseEntity<Response<TrainType>> re = new ResponseEntity<>(response, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                Mockito.anyString(),
                Mockito.any(HttpMethod.class),
                Mockito.any(HttpEntity.class),
                Mockito.any(ParameterizedTypeReference.class)))
                .thenReturn(re);
        Response result = travelServiceImpl.adminQueryAll(headers);
        Assert.assertEquals("Success", result.getMsg());
    }
    @Test
    public void testAdminQueryAll2() {
        ArrayList<Trip> tripList = new ArrayList<>();
        Mockito.when(repository.findAll()).thenReturn(tripList);
        Response result = travelServiceImpl.adminQueryAll(headers);
        Assert.assertEquals(new Response<>(0, noCnontent, null), result);
    }


}


package preserve;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;
import org.springframework.cloud.client.loadbalancer.LoadBalanced;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.EnableAspectJAutoProxy;
import org.springframework.integration.annotation.IntegrationComponentScan;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.web.client.RestTemplate;
import springfox.documentation.swagger2.annotations.EnableSwagger2;

/**
 * @author fdse
 */
@SpringBootApplication
@EnableAspectJAutoProxy(proxyTargetClass = true)
@EnableAsync
@IntegrationComponentScan
@EnableSwagger2
@EnableDiscoveryClient
public class PreserveApplication {

    public static void main(String[] args) {
        SpringApplication.run(PreserveApplication.class, args);
    }

    @LoadBalanced
    @Bean
    public RestTemplate restTemplate(RestTemplateBuilder builder) {
        return builder.build();
    }

}


// Node: preserve
package preserve.service;

import edu.fudan.common.util.Response;
import org.springframework.http.HttpHeaders;
import edu.fudan.common.entity.OrderTicketsInfo;

/**
 * @author fdse
 */
public interface PreserveService {

    Response preserve(OrderTicketsInfo oti, HttpHeaders headers);
}


// Node: repos/cloned_ms_repos/train-ticket/ts-preserve-service/src/main/java/preserve/service/PreserveService.java:PreserveService.<init>
package preserve.controller;

import com.alibaba.fastjson.JSONObject;
import edu.fudan.common.util.Response;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.springframework.http.*;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.request.MockMvcRequestBuilders;
import org.springframework.test.web.servlet.result.MockMvcResultMatchers;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import edu.fudan.common.entity.OrderTicketsInfo;
import preserve.service.PreserveService;

@RunWith(JUnit4.class)
public class PreserveControllerTest {

    @InjectMocks
    private PreserveController preserveController;

    @Mock
    private PreserveService preserveService;
    private MockMvc mockMvc;
    private Response response = new Response();

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
        mockMvc = MockMvcBuilders.standaloneSetup(preserveController).build();
    }

    @Test
    public void testHome() throws Exception {
        mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/preserveservice/welcome"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andExpect(MockMvcResultMatchers.content().string("Welcome to [ Preserve Service ] !"));
    }

    @Test
    public void testPreserve() throws Exception {
        OrderTicketsInfo oti = new OrderTicketsInfo();
        Mockito.when(preserveService.preserve(Mockito.any(OrderTicketsInfo.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(oti);
        String result = mockMvc.perform(MockMvcRequestBuilders.post("/api/v1/preserveservice/preserve").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

}


// Node: OrderTicketsInfo
package preserve.service;

import edu.fudan.common.util.Response;
import edu.fudan.common.util.StringUtils;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.*;
import org.springframework.web.client.RestTemplate;
import edu.fudan.common.entity.*;

import java.util.Date;
import java.util.HashMap;
import java.util.UUID;

@RunWith(JUnit4.class)
public class PreserveServiceImplTest {

    @InjectMocks
    private PreserveServiceImpl preserveServiceImpl;

    @Mock
    private RestTemplate restTemplate;

    private HttpHeaders headers = new HttpHeaders();
    private HttpEntity requestEntity = new HttpEntity(headers);

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
    }

    @Test
    public void testPreserve() {
        OrderTicketsInfo oti = OrderTicketsInfo.builder()
                .accountId(UUID.randomUUID().toString())
                .contactsId(UUID.randomUUID().toString())
                .from("from_station")
                .to("to_station")
                .date(StringUtils.Date2String(new Date()))
                .handleDate("handle_date")
                .tripId("G1255")
                .seatType(2)
                .assurance(1)
                .foodType(1)
                .foodName("food_name")
                .foodPrice(1.0)
                .stationName("station_name")
                .storeName("store_name")
                .consigneeName("consignee_name")
                .consigneePhone("123456789")
                .consigneeWeight(1.0)
                .isWithin(true)
                .build();

        //response for checkSecurity()、addAssuranceForOrder()、createFoodOrder()、createConsign()
        Response response1 = new Response<>(1, null, null);
        ResponseEntity<Response> re1 = new ResponseEntity<>(response1, HttpStatus.OK);

        //response for sendEmail()
        ResponseEntity<Boolean> re10 = new ResponseEntity<>(true, HttpStatus.OK);

        Mockito.when(restTemplate.exchange(
                Mockito.anyString(),
                Mockito.any(HttpMethod.class),
                Mockito.any(HttpEntity.class),
                Mockito.any(Class.class)))
                .thenReturn(re1).thenReturn(re1).thenReturn(re1).thenReturn(re1).thenReturn(re10);


        //response for getContactsById()
        Contacts contacts = new Contacts();
        contacts.setDocumentNumber("document_number");
        contacts.setName("name");
        contacts.setDocumentType(1);
        Response<Contacts> response2 = new Response<>(1, null, contacts);
        ResponseEntity<Response<Contacts>> re2 = new ResponseEntity<>(response2, HttpStatus.OK);

        //response for getTripAllDetailInformation()
        TripResponse tripResponse = new TripResponse();
        tripResponse.setConfortClass(1);
        tripResponse.setStartTime(StringUtils.Date2String(new Date()));
        TripAllDetail tripAllDetail = new TripAllDetail(true, "message", tripResponse, new Trip());
        Response<TripAllDetail> response3 = new Response<>(1, null, tripAllDetail);
        ResponseEntity<Response<TripAllDetail>> re3 = new ResponseEntity<>(response3, HttpStatus.OK);

        //response for queryForStationId()
        Response<String> response4 = new Response<>(null, null, "");
        ResponseEntity<Response<String>> re4 = new ResponseEntity<>(response4, HttpStatus.OK);

        //response for travel result
        TravelResult travelResult = new TravelResult();
        travelResult.setPrices( new HashMap<String, String>(){{ put("confortClass", "1.0"); }} );
        Response<TravelResult> response5 = new Response<>(null, null, travelResult);
        ResponseEntity<Response<TravelResult>> re5 = new ResponseEntity<>(response5, HttpStatus.OK);

        //response for dipatchSeat()
        Ticket ticket = new Ticket();
        ticket.setSeatNo(1);
        Response<Ticket> response6 = new Response<>(null, null, ticket);
        ResponseEntity<Response<Ticket>> re6 = new ResponseEntity<>(response6, HttpStatus.OK);

        //response for createOrder()
        Order order = new Order();
        order.setId(UUID.randomUUID().toString());
        order.setAccountId(UUID.randomUUID().toString());
        order.setTravelDate(StringUtils.Date2String(new Date()));
        order.setFrom("from_station");
        order.setTo("to_station");
        Response<Order> response7 = new Response<>(1, null, order);
        ResponseEntity<Response<Order>> re7 = new ResponseEntity<>(response7, HttpStatus.OK);

        //response for getAccount()
        User user = new User();
        user.setEmail("email");
        user.setUserName("user_name");
        Response<User> response9 = new Response<>(1, null, user);
        ResponseEntity<Response<User>> re9 = new ResponseEntity<>(response9, HttpStatus.OK);

        Mockito.when(restTemplate.exchange(
                Mockito.anyString(),
                Mockito.any(HttpMethod.class),
                Mockito.any(HttpEntity.class),
                Mockito.any(ParameterizedTypeReference.class)))
                .thenReturn(re2).thenReturn(re3).thenReturn(re4).thenReturn(re4).thenReturn(re5).thenReturn(re6).thenReturn(re7).thenReturn(re9);

        Response result = preserveServiceImpl.preserve(oti, headers);
        Assert.assertEquals(new Response<>(1, "Success.", null), result);
    }

    @Test
    public void testDipatchSeat() {
        long mills = System.currentTimeMillis();
        Seat seatRequest = new Seat(StringUtils.Date2String(new Date()), "G1234", "start_station", "dest_station", 2, 100, null);
        HttpEntity requestEntityTicket = new HttpEntity(seatRequest, headers);
        Response<Ticket> response = new Response<>();
        ResponseEntity<Response<Ticket>> reTicket = new ResponseEntity<>(response, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                "http://ts-seat-service:18898/api/v1/seatservice/seats",
                HttpMethod.POST,
                requestEntityTicket,
                new ParameterizedTypeReference<Response<Ticket>>() {
                })).thenReturn(reTicket);
        Ticket result = preserveServiceImpl.dipatchSeat(StringUtils.Date2String(new Date()), "G1234", "start_station", "dest_station", 2, 100, null, headers);
        Assert.assertNull(result);
    }

    @Test
    public void testSendEmail() {
        NotifyInfo notifyInfo = new NotifyInfo();
        HttpEntity requestEntitySendEmail = new HttpEntity(notifyInfo, headers);
        ResponseEntity<Boolean> reSendEmail = new ResponseEntity<>(true, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                "http://ts-notification-service:17853/api/v1/notifyservice/notification/preserve_success",
                HttpMethod.POST,
                requestEntitySendEmail,
                Boolean.class)).thenReturn(reSendEmail);
        boolean result = preserveServiceImpl.sendEmail(notifyInfo, headers);
        Assert.assertTrue(result);
    }

    @Test
    public void testGetAccount() {
        Response<User> response = new Response<>();
        ResponseEntity<Response<User>> re = new ResponseEntity<>(response, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                "http://ts-user-service:12342/api/v1/userservice/users/id/1",
                HttpMethod.GET,
                requestEntity,
                new ParameterizedTypeReference<Response<User>>() {
                })).thenReturn(re);
        User result = preserveServiceImpl.getAccount("1", headers);
        Assert.assertNull(result);
    }

}


package train;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;
import org.springframework.cloud.client.loadbalancer.LoadBalanced;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.EnableAspectJAutoProxy;
import org.springframework.integration.annotation.IntegrationComponentScan;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.web.client.RestTemplate;
import springfox.documentation.swagger2.annotations.EnableSwagger2;

@SpringBootApplication
@EnableAspectJAutoProxy(proxyTargetClass = true)
@EnableAsync
@IntegrationComponentScan
@EnableSwagger2
@EnableDiscoveryClient
public class TrainApplication {

    public static void main(String[] args) {
        SpringApplication.run(TrainApplication.class, args);
    }

    @LoadBalanced
    @Bean
    public RestTemplate restTemplate(RestTemplateBuilder builder) {
        return builder.build();
    }
}


package train.service;

import org.springframework.http.HttpHeaders;
import train.entity.TrainType;

import java.util.List;

public interface TrainService {
    //CRUD
    boolean create(TrainType trainType, HttpHeaders headers);

    TrainType retrieve(String id,HttpHeaders headers);

    TrainType retrieveByName(String name,HttpHeaders headers);

    List<TrainType> retrieveByNames(List<String> name,HttpHeaders headers);

    boolean update(TrainType trainType,HttpHeaders headers);

    boolean delete(String id,HttpHeaders headers);

    List<TrainType> query(HttpHeaders headers);
}


// Node: repos/cloned_ms_repos/train-ticket/ts-train-service/src/main/java/train/service/TrainService.java:TrainService.<init>
package train.service;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpHeaders;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import train.entity.TrainType;
import train.repository.TrainTypeRepository;

import java.util.List;

@Service
public class TrainServiceImpl implements TrainService {

    @Autowired
    private TrainTypeRepository repository;

    private static final Logger LOGGER = LoggerFactory.getLogger(TrainServiceImpl.class);

    @Override
    public boolean create(TrainType trainType, HttpHeaders headers) {
        boolean result = false;
        if(trainType.getName().isEmpty()){
            TrainServiceImpl.LOGGER.error("[create][Create train error][Train Type name not specified]");
            return result;
        }
        if (repository.findByName(trainType.getName()) == null) {
            TrainType type = new TrainType(trainType.getName(), trainType.getEconomyClass(), trainType.getConfortClass());
            type.setAverageSpeed(trainType.getAverageSpeed());
            repository.save(type);
            result = true;
        }
        else {
            TrainServiceImpl.LOGGER.error("[create][Create train error][Train already exists][TrainTypeId: {}]",trainType.getId());
        }
        return result;
    }

    @Override
    public TrainType retrieve(String id, HttpHeaders headers) {
        if (!repository.findById(id).isPresent()) {
            TrainServiceImpl.LOGGER.error("[retrieve][Retrieve train error][Train not found][TrainTypeId: {}]",id);
            return null;
        } else {
            return repository.findById(id).get();
        }
    }

    @Override
    public TrainType retrieveByName(String name, HttpHeaders headers) {
        TrainType tt = repository.findByName(name);
        if (tt == null) {
            TrainServiceImpl.LOGGER.error("[retrieveByName][RetrieveByName error][Train not found][TrainTypeName: {}]", name);
            return null;
        } else {
            return tt;
        }
    }

    @Override
    public List<TrainType> retrieveByNames(List<String> names, HttpHeaders headers) {
        List<TrainType> tt = repository.findByNames(names);
        if (tt == null || tt.isEmpty()) {
            TrainServiceImpl.LOGGER.error("[retrieveByNames][RetrieveByNames error][Train not found][TrainTypeNames: {}]", names);
            return null;
        } else {
            return tt;
        }
    }

    @Override
    @Transactional
    public boolean update(TrainType trainType, HttpHeaders headers) {
        boolean result = false;
        if (repository.findById(trainType.getId()).isPresent()) {
            TrainType type = new TrainType(trainType.getName(), trainType.getEconomyClass(), trainType.getConfortClass(), trainType.getAverageSpeed());
            type.setId(trainType.getId());
            repository.save(type);
            result = true;
        }
        else {
            TrainServiceImpl.LOGGER.error("[update][Update train error][Train not found][TrainTypeId: {}]",trainType.getId());
        }
        return result;
    }

    @Override
    public boolean delete(String id, HttpHeaders headers) {
        boolean result = false;
        if (repository.findById(id).isPresent()) {
            repository.deleteById(id);
            result = true;
        }
        else {
            TrainServiceImpl.LOGGER.error("[delete][Delete train error][Train not found][TrainTypeId: {}]",id);
        }
        return result;
    }

    @Override
    public List<TrainType> query(HttpHeaders headers) {
        return repository.findAll();
    }

}


package train.controller;

import com.alibaba.fastjson.JSONObject;
import edu.fudan.common.util.Response;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.springframework.http.*;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.request.MockMvcRequestBuilders;
import org.springframework.test.web.servlet.result.MockMvcResultMatchers;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import train.entity.TrainType;
import train.service.TrainService;

import java.util.ArrayList;
import java.util.List;

@RunWith(JUnit4.class)
public class TrainControllerTest {

    @InjectMocks
    private TrainController trainController;

    @Mock
    private TrainService trainService;
    private MockMvc mockMvc;

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
        mockMvc = MockMvcBuilders.standaloneSetup(trainController).build();
    }

    @Test
    public void testHome() throws Exception {
        mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/trainservice/trains/welcome"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andExpect(MockMvcResultMatchers.content().string("Welcome to [ Train Service ] !"));
    }

    @Test
    public void testCreate1() throws Exception {
        TrainType trainType = new TrainType();
        Mockito.when(trainService.create(Mockito.any(TrainType.class), Mockito.any(HttpHeaders.class))).thenReturn(true);
        String requestJson = JSONObject.toJSONString(trainType);
        String result = mockMvc.perform(MockMvcRequestBuilders.post("/api/v1/trainservice/trains").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(new Response(1, "create success", null), JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testCreate2() throws Exception {
        TrainType trainType = new TrainType();
        Mockito.when(trainService.create(Mockito.any(TrainType.class), Mockito.any(HttpHeaders.class))).thenReturn(false);
        String requestJson = JSONObject.toJSONString(trainType);
        String result = mockMvc.perform(MockMvcRequestBuilders.post("/api/v1/trainservice/trains").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals("train type already exist", JSONObject.parseObject(result, Response.class).getMsg());
    }

    @Test
    public void testRetrieve1() throws Exception {
        Mockito.when(trainService.retrieve(Mockito.anyString(), Mockito.any(HttpHeaders.class))).thenReturn(null);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/trainservice/trains/wrong_id"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(new Response(0, "here is no TrainType with the trainType id: wrong_id", null), JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testRetrieve2() throws Exception {
        TrainType trainType = new TrainType();
        Mockito.when(trainService.retrieve(Mockito.anyString(), Mockito.any(HttpHeaders.class))).thenReturn(trainType);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/trainservice/trains/id"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals("success", JSONObject.parseObject(result, Response.class).getMsg());
    }

    @Test
    public void testUpdate1() throws Exception {
        TrainType trainType = new TrainType();
        Mockito.when(trainService.update(Mockito.any(TrainType.class), Mockito.any(HttpHeaders.class))).thenReturn(true);
        String requestJson = JSONObject.toJSONString(trainType);
        String result = mockMvc.perform(MockMvcRequestBuilders.put("/api/v1/trainservice/trains").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(new Response(1, "update success", true), JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testUpdate2() throws Exception {
        TrainType trainType = new TrainType();
        Mockito.when(trainService.update(Mockito.any(TrainType.class), Mockito.any(HttpHeaders.class))).thenReturn(false);
        String requestJson = JSONObject.toJSONString(trainType);
        String result = mockMvc.perform(MockMvcRequestBuilders.put("/api/v1/trainservice/trains").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(new Response(0, "there is no trainType with the trainType id", false), JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testDelete1() throws Exception {
        Mockito.when(trainService.delete(Mockito.anyString(), Mockito.any(HttpHeaders.class))).thenReturn(true);
        String result = mockMvc.perform(MockMvcRequestBuilders.delete("/api/v1/trainservice/trains/id"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(new Response(1, "delete success", true), JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testDelete2() throws Exception {
        Mockito.when(trainService.delete(Mockito.anyString(), Mockito.any(HttpHeaders.class))).thenReturn(false);
        String result = mockMvc.perform(MockMvcRequestBuilders.delete("/api/v1/trainservice/trains/id"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(new Response(0, "there is no train according to id", null), JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testQuery1() throws Exception {
        List<TrainType> trainTypes = new ArrayList<>();
        trainTypes.add(new TrainType());
        Mockito.when(trainService.query(Mockito.any(HttpHeaders.class))).thenReturn(trainTypes);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/trainservice/trains"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals("success", JSONObject.parseObject(result, Response.class).getMsg());
    }

    @Test
    public void testQuery2() throws Exception {
        List<TrainType> trainTypes = new ArrayList<>();
        Mockito.when(trainService.query(Mockito.any(HttpHeaders.class))).thenReturn(trainTypes);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/trainservice/trains"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals("no content", JSONObject.parseObject(result, Response.class).getMsg());
    }

}


package train.service;

import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.springframework.http.HttpHeaders;
import train.entity.TrainType;
import train.repository.TrainTypeRepository;

@RunWith(JUnit4.class)
public class TrainServiceImplTest {

    @InjectMocks
    private TrainServiceImpl trainServiceImpl;

    @Mock
    private TrainTypeRepository repository;

    private HttpHeaders headers = new HttpHeaders();

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
    }

    @Test
    public void testCreate1() {
        TrainType trainType = new TrainType();
        Mockito.when(repository.findById(Mockito.anyString())).thenReturn(null);
        Mockito.when(repository.save(Mockito.any(TrainType.class))).thenReturn(null);
        boolean result = trainServiceImpl.create(trainType, headers);
        Assert.assertTrue(result);
    }

    @Test
    public void testCreate2() {
        TrainType trainType = new TrainType();
        Mockito.when(repository.findById(Mockito.anyString()).get()).thenReturn(trainType);
        boolean result = trainServiceImpl.create(trainType, headers);
        Assert.assertFalse(result);
    }

    @Test
    public void testRetrieve1() {
        Mockito.when(repository.findById(Mockito.anyString())).thenReturn(null);
        TrainType result = trainServiceImpl.retrieve("id", headers);
        Assert.assertNull(result);
    }

    @Test
    public void testRetrieve2() {
        TrainType trainType = new TrainType();
        Mockito.when(repository.findById(Mockito.anyString()).get()).thenReturn(trainType);
        TrainType result = trainServiceImpl.retrieve("id", headers);
        Assert.assertNotNull(result);
    }

    @Test
    public void testUpdate1() {
        TrainType trainType = new TrainType();
        Mockito.when(repository.findById(Mockito.anyString()).get()).thenReturn(trainType);
        Mockito.when(repository.save(Mockito.any(TrainType.class))).thenReturn(null);
        boolean result = trainServiceImpl.update(trainType, headers);
        Assert.assertTrue(result);
    }

    @Test
    public void testUpdate2() {
        TrainType trainType = new TrainType();
        Mockito.when(repository.findById(Mockito.anyString())).thenReturn(null);
        boolean result = trainServiceImpl.update(trainType, headers);
        Assert.assertFalse(result);
    }

    @Test
    public void testDelete1() {
        TrainType trainType = new TrainType();
        Mockito.when(repository.findById(Mockito.anyString()).get()).thenReturn(trainType);
        Mockito.doNothing().doThrow(new RuntimeException()).when(repository).deleteById(Mockito.anyString());
        boolean result = trainServiceImpl.delete("id", headers);
        Assert.assertTrue(result);
    }

    @Test
    public void testDelete2() {
        Mockito.when(repository.findById(Mockito.anyString())).thenReturn(null);
        boolean result = trainServiceImpl.delete("id", headers);
        Assert.assertFalse(result);
    }

    @Test
    public void testQuery() {
        Mockito.when(repository.findAll()).thenReturn(null);
        Assert.assertNull(trainServiceImpl.query(headers));
    }

}


package consignprice;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;
import org.springframework.cloud.client.loadbalancer.LoadBalanced;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.EnableAspectJAutoProxy;
import org.springframework.integration.annotation.IntegrationComponentScan;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.web.client.RestTemplate;
import springfox.documentation.swagger2.annotations.EnableSwagger2;

import java.util.Date;

/**
 * @author fdse
 */
@SpringBootApplication
@EnableAspectJAutoProxy(proxyTargetClass = true)
@EnableAsync
@IntegrationComponentScan
@EnableSwagger2
@EnableDiscoveryClient
public class ConsignPriceApplication {

    private static final Logger LOGGER = LoggerFactory.getLogger(ConsignPriceApplication.class);

    public static void main(String[] args) {
        ConsignPriceApplication.LOGGER.info("[ConsignPriceApplication.main][launch date: {}]", new Date());
        SpringApplication.run(ConsignPriceApplication.class, args);
    }

    @LoadBalanced
    @Bean
    public RestTemplate restTemplate(RestTemplateBuilder builder) {
        return builder.build();
    }
}


package consignprice.controller;

import com.alibaba.fastjson.JSONObject;
import consignprice.entity.ConsignPrice;
import consignprice.service.ConsignPriceService;
import edu.fudan.common.util.Response;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.springframework.http.*;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.request.MockMvcRequestBuilders;
import org.springframework.test.web.servlet.result.MockMvcResultMatchers;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

@RunWith(JUnit4.class)
public class ConsignPriceControllerTest {

    @InjectMocks
    private ConsignPriceController consignPriceController;

    @Mock
    private ConsignPriceService service;
    private MockMvc mockMvc;
    private Response response = new Response();

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
        mockMvc = MockMvcBuilders.standaloneSetup(consignPriceController).build();
    }

    @Test
    public void testHome() throws Exception {
        mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/consignpriceservice/welcome"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andExpect(MockMvcResultMatchers.content().string("Welcome to [ ConsignPrice Service ] !"));
    }

    @Test
    public void testGetPriceByWeightAndRegion() throws Exception {
        Mockito.when(service.getPriceByWeightAndRegion(Mockito.anyDouble(), Mockito.anyBoolean(), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/consignpriceservice/consignprice/1.0/true"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testGetPriceInfo() throws Exception {
        Mockito.when(service.queryPriceInformation(Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/consignpriceservice/consignprice/price"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testGetPriceConfig() throws Exception {
        Mockito.when(service.getPriceConfig(Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/consignpriceservice/consignprice/config"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testModifyPriceConfig() throws Exception {
        ConsignPrice priceConfig = new ConsignPrice();
        Mockito.when(service.createAndModifyPrice(Mockito.any(ConsignPrice.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(priceConfig);
        String result = mockMvc.perform(MockMvcRequestBuilders.post("/api/v1/consignpriceservice/consignprice").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

}


// Node: testGetPriceByWeightAndRegion
// Node: anyDouble
// Node: anyBoolean
// Node: testGetPriceInfo
// Node: testGetPriceConfig
// Node: testModifyPriceConfig
package consignprice.service;

import consignprice.entity.ConsignPrice;
import consignprice.repository.ConsignPriceConfigRepository;
import edu.fudan.common.util.Response;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.springframework.http.HttpHeaders;

import java.util.UUID;

@RunWith(JUnit4.class)
public class ConsignPriceServiceImplTest {

    @InjectMocks
    private ConsignPriceServiceImpl consignPriceServiceImpl;

    @Mock
    private ConsignPriceConfigRepository repository;

    private HttpHeaders headers = new HttpHeaders();

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
    }

    @Test
    public void testGetPriceByWeightAndRegion1() {
        ConsignPrice priceConfig = new ConsignPrice(UUID.randomUUID().toString(), 1, 2.0, 3.0, 3.5, 4.0);
        Mockito.when(repository.findByIndex(0)).thenReturn(priceConfig);
        Response result = consignPriceServiceImpl.getPriceByWeightAndRegion(1.0, true, headers);
        Assert.assertEquals(new Response<>(1, "Success", 3.0), result);
    }

    @Test
    public void testGetPriceByWeightAndRegion2() {
        ConsignPrice priceConfig = new ConsignPrice(UUID.randomUUID().toString(), 1, 2.0, 3.0, 3.5, 4.0);
        Mockito.when(repository.findByIndex(0)).thenReturn(priceConfig);
        Response result = consignPriceServiceImpl.getPriceByWeightAndRegion(3.0, true, headers);
        Assert.assertEquals(new Response<>(1, "Success", 6.5), result);
    }

    @Test
    public void testGetPriceByWeightAndRegion3() {
        ConsignPrice priceConfig = new ConsignPrice(UUID.randomUUID().toString(), 1, 2.0, 3.0, 3.5, 4.0);
        Mockito.when(repository.findByIndex(0)).thenReturn(priceConfig);
        Response result = consignPriceServiceImpl.getPriceByWeightAndRegion(3.0, false, headers);
        Assert.assertEquals(new Response<>(1, "Success", 7.0), result);
    }

    @Test
    public void testQueryPriceInformation() {
        ConsignPrice priceConfig = new ConsignPrice(UUID.randomUUID().toString(), 1, 2.0, 3.0, 3.5, 4.0);
        Mockito.when(repository.findByIndex(0)).thenReturn(priceConfig);
        Response result = consignPriceServiceImpl.queryPriceInformation(headers);
        String str = "The price of weight within 2.0 is 3.0. The price of extra weight within the region is 3.5 and beyond the region is 4.0\n";
        Assert.assertEquals(new Response<>(1, "Success", str), result);
    }

    @Test
    public void testCreateAndModifyPrice1() {
        ConsignPrice config = new ConsignPrice(UUID.randomUUID().toString(), 1, 2.0, 3.0, 3.5, 4.0);
        Mockito.when(repository.findByIndex(0)).thenReturn(config);
        Mockito.when(repository.save(Mockito.any(ConsignPrice.class))).thenReturn(null);
        Response result = consignPriceServiceImpl.createAndModifyPrice(config, headers);
        Assert.assertEquals(new Response<>(1, "Success", config), result);
    }

    @Test
    public void testCreateAndModifyPrice2() {
        ConsignPrice config = new ConsignPrice(UUID.randomUUID().toString(), 0, 2.0, 3.0, 3.5, 4.0);
        Mockito.when(repository.findByIndex(0)).thenReturn(null);
        Mockito.when(repository.save(Mockito.any(ConsignPrice.class))).thenReturn(null);
        Response result = consignPriceServiceImpl.createAndModifyPrice(config, headers);
        Assert.assertEquals(new Response<>(1, "Success", config), result);
    }

    @Test
    public void testGetPriceConfig() {
        ConsignPrice config = new ConsignPrice();
        Mockito.when(repository.findByIndex(0)).thenReturn(config);
        Response result = consignPriceServiceImpl.getPriceConfig(headers);
        Assert.assertEquals(new Response<>(1, "Success", config), result);
    }

}


package inside_payment;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;
import org.springframework.cloud.client.loadbalancer.LoadBalanced;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.EnableAspectJAutoProxy;
import org.springframework.integration.annotation.IntegrationComponentScan;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.web.client.RestTemplate;
import springfox.documentation.swagger2.annotations.EnableSwagger2;

/**
 * @author fdse
 */
@SpringBootApplication
@EnableAspectJAutoProxy(proxyTargetClass = true)
@EnableAsync
@IntegrationComponentScan
@EnableSwagger2
@EnableDiscoveryClient
public class InsidePaymentApplication {

    public static void main(String[] args) {
        SpringApplication.run(InsidePaymentApplication.class, args);
    }

    @LoadBalanced
    @Bean
    public RestTemplate restTemplate(RestTemplateBuilder builder) {
        return builder.build();
    }
}

package inside_payment.controller;

import com.alibaba.fastjson.JSONObject;
import edu.fudan.common.util.Response;
import inside_payment.entity.AccountInfo;
import inside_payment.entity.PaymentInfo;
import inside_payment.service.InsidePaymentService;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.springframework.http.*;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.request.MockMvcRequestBuilders;
import org.springframework.test.web.servlet.result.MockMvcResultMatchers;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

@RunWith(JUnit4.class)
public class InsidePaymentControllerTest {

    @InjectMocks
    private InsidePaymentController insidePaymentController;

    @Mock
    private InsidePaymentService service;
    private MockMvc mockMvc;
    private Response response = new Response();

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
        mockMvc = MockMvcBuilders.standaloneSetup(insidePaymentController).build();
    }

    @Test
    public void testHome() throws Exception {
        mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/inside_pay_service/welcome"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andExpect(MockMvcResultMatchers.content().string("Welcome to [ InsidePayment Service ] !"));
    }

    @Test
    public void testPay() throws Exception {
        PaymentInfo info = new PaymentInfo();
        Mockito.when(service.pay(Mockito.any(PaymentInfo.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(info);
        String result = mockMvc.perform(MockMvcRequestBuilders.post("/api/v1/inside_pay_service/inside_payment").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testCreateAccount() throws Exception {
        AccountInfo info = new AccountInfo();
        Mockito.when(service.createAccount(Mockito.any(AccountInfo.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(info);
        String result = mockMvc.perform(MockMvcRequestBuilders.post("/api/v1/inside_pay_service/inside_payment/account").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testAddMoney() throws Exception {
        Mockito.when(service.addMoney(Mockito.anyString(), Mockito.anyString(), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/inside_pay_service/inside_payment/user_id/money"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testQueryPayment() throws Exception {
        Mockito.when(service.queryPayment(Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/inside_pay_service/inside_payment/payment"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testQueryAccount() throws Exception {
        Mockito.when(service.queryAccount(Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/inside_pay_service/inside_payment/account"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testDrawBack() throws Exception {
        Mockito.when(service.drawBack(Mockito.anyString(), Mockito.anyString(), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/inside_pay_service/inside_payment/drawback/user_id/money"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testPayDifference() throws Exception {
        PaymentInfo info = new PaymentInfo();
        Mockito.when(service.payDifference(Mockito.any(PaymentInfo.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(info);
        String result = mockMvc.perform(MockMvcRequestBuilders.post("/api/v1/inside_pay_service/inside_payment/difference").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testQueryAddMoney() throws Exception {
        Mockito.when(service.queryAddMoney(Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/inside_pay_service/inside_payment/money"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

}


// Node: testCreateAccount
// Node: testQueryPayment
// Node: testQueryAccount
// Node: testDrawBack
// Node: testPayDifference
// Node: testQueryAddMoney
package inside_payment.service;

import edu.fudan.common.entity.Order;
import edu.fudan.common.util.Response;
import inside_payment.entity.*;
import inside_payment.repository.AddMoneyRepository;
import inside_payment.repository.PaymentRepository;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.*;
import org.springframework.web.client.RestTemplate;

import java.util.ArrayList;
import java.util.List;

import static org.mockito.internal.verification.VerificationModeFactory.times;

@RunWith(JUnit4.class)
public class InsidePaymentServiceImplTest {

    @InjectMocks
    private InsidePaymentServiceImpl insidePaymentServiceImpl;

    @Mock
    private AddMoneyRepository addMoneyRepository;

    @Mock
    private PaymentRepository paymentRepository;

    @Mock
    private RestTemplate restTemplate;

    private HttpHeaders headers = new HttpHeaders();
    HttpEntity httpEntity = new HttpEntity(headers);

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
    }

    @Test
    public void testPay() {
        PaymentInfo info = new PaymentInfo("user_id", "order_id", "G", "1.0");
        Order order = new Order();
        order.setStatus(0);
        order.setPrice("1.0");
        Response<Order> response = new Response<>(1, null, order);
        ResponseEntity<Response<Order>> re = new ResponseEntity<>(response, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                "http://ts-order-service:12031/api/v1/orderservice/order/order_id",
                HttpMethod.GET,
                httpEntity,
                new ParameterizedTypeReference<Response<Order>>() {
                })).thenReturn(re);

        List<Payment> payments = new ArrayList<>();
        List<Money> monies = new ArrayList<>();
        Money money = new Money();
        money.setMoney("2.0");
        monies.add(money);
        Mockito.when(paymentRepository.findByUserId(Mockito.anyString())).thenReturn(payments);
        Mockito.when(addMoneyRepository.findByUserId(Mockito.anyString())).thenReturn(monies);
        //mock setOrderStatus()
        Response response2 = new Response(1, "", null);
        ResponseEntity<Response> re2 = new ResponseEntity<>(response2, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                "http://ts-order-service:12031/api/v1/orderservice/order/status/" + "order_id" + "/" + 1,
                HttpMethod.GET,
                httpEntity,
                Response.class)).thenReturn(re2);
        Mockito.when(paymentRepository.save(Mockito.any(Payment.class))).thenReturn(null);
        Response result = insidePaymentServiceImpl.pay(info, headers);
        Assert.assertEquals(new Response<>(1, "Payment Success", null), result);
    }

    @Test
    public void testCreateAccount1() {
        AccountInfo info = new AccountInfo();
        List<Money> list = new ArrayList<>();
        Mockito.when(addMoneyRepository.findByUserId(Mockito.anyString())).thenReturn(list);
        Mockito.when(addMoneyRepository.save(Mockito.any(Money.class))).thenReturn(null);
        Response result = insidePaymentServiceImpl.createAccount(info, headers);
        Assert.assertEquals(new Response<>(1, "Create Account Success", null), result);
    }

    @Test
    public void testCreateAccount2() {
        AccountInfo info = new AccountInfo();
        List<Money> list = new ArrayList<>();
        list.add(new Money());
        Mockito.when(addMoneyRepository.findByUserId(Mockito.anyString())).thenReturn(list);
        Response result = insidePaymentServiceImpl.createAccount(info, headers);
        Assert.assertEquals(new Response<>(0, "Create Account Failed, Account already Exists", null), result);
    }

    @Test
    public void testAddMoney1() {
        List<Money> list = new ArrayList<>();
        Mockito.when(addMoneyRepository.findByUserId(Mockito.anyString())).thenReturn(list);
        Mockito.when(addMoneyRepository.save(Mockito.any(Money.class))).thenReturn(null);
        Response result = insidePaymentServiceImpl.addMoney("user_id", "money", headers);
        Assert.assertEquals(new Response<>(1, "Add Money Success", null), result);
    }

    @Test
    public void testAddMoney2() {
        Mockito.when(addMoneyRepository.findByUserId(Mockito.anyString())).thenReturn(null);
        Response result = insidePaymentServiceImpl.addMoney("user_id", "money", headers);
        Assert.assertEquals(new Response<>(0, "Add Money Failed", null), result);
    }

    @Test
    public void testQueryAccount() {
        List<Money> list = new ArrayList<>();
        Mockito.when(addMoneyRepository.findAll()).thenReturn(list);
        Response result = insidePaymentServiceImpl.queryAccount(headers);
        Assert.assertEquals("Success", result.getMsg());
    }

    @Test
    public void testQueryPayment1() {
        List<Payment> payments = new ArrayList<>();
        payments.add(new Payment());
        Mockito.when(paymentRepository.findAll()).thenReturn(payments);
        Response result = insidePaymentServiceImpl.queryPayment(headers);
        Assert.assertEquals(new Response<>(1, "Query Payment Success", payments), result);
    }

    @Test
    public void testQueryPayment2() {
        Mockito.when(paymentRepository.findAll()).thenReturn(null);
        Response result = insidePaymentServiceImpl.queryPayment(headers);
        Assert.assertEquals(new Response<>(0, "Query Payment Failed", null), result);
    }

    @Test
    public void testDrawBack1() {
        List<Money> list = new ArrayList<>();
        Mockito.when(addMoneyRepository.findByUserId(Mockito.anyString())).thenReturn(list);
        Mockito.when(addMoneyRepository.save(Mockito.any(Money.class))).thenReturn(null);
        Response result = insidePaymentServiceImpl.drawBack("user_id", "money", headers);
        Assert.assertEquals(new Response<>(1, "Draw Back Money Success", null), result);
    }

    @Test
    public void testDrawBack2() {
        Mockito.when(addMoneyRepository.findByUserId(Mockito.anyString())).thenReturn(null);
        Response result = insidePaymentServiceImpl.drawBack("user_id", "money", headers);
        Assert.assertEquals(new Response<>(0, "Draw Back Money Failed", null), result);
    }

    @Test
    public void testPayDifference() {
        PaymentInfo info = new PaymentInfo("user_id", "order_id", "G", "1.0");
        List<Payment> payments = new ArrayList<>();
        List<Money> monies = new ArrayList<>();
        Money money = new Money();
        money.setMoney("2.0");
        monies.add(money);
        Mockito.when(paymentRepository.findByUserId(Mockito.anyString())).thenReturn(payments);
        Mockito.when(addMoneyRepository.findByUserId(Mockito.anyString())).thenReturn(monies);
        Mockito.when(paymentRepository.save(Mockito.any(Payment.class))).thenReturn(null);
        Response result = insidePaymentServiceImpl.payDifference(info, headers);
        Assert.assertEquals(new Response<>(1, "Pay Difference Success", null), result);
    }

    @Test
    public void testQueryAddMoney1() {
        List<Money> monies = new ArrayList<>();
        monies.add(new Money());
        Mockito.when(addMoneyRepository.findAll()).thenReturn(monies);
        Response result = insidePaymentServiceImpl.queryAddMoney(headers);
        Assert.assertEquals(new Response<>(1, "Query Money Success", null), result);
    }

    @Test
    public void testQueryAddMoney2() {
        Mockito.when(addMoneyRepository.findAll()).thenReturn(null);
        Response result = insidePaymentServiceImpl.queryAddMoney(headers);
        Assert.assertEquals(new Response<>(0, "Query money failed", null), result);
    }

    @Test
    public void testInitPayment1() {
        Payment payment = new Payment();
        Mockito.when(paymentRepository.findById(Mockito.anyString())).thenReturn(null);
        Mockito.when(paymentRepository.save(Mockito.any(Payment.class))).thenReturn(null);
        insidePaymentServiceImpl.initPayment(payment, headers);
        Mockito.verify(paymentRepository, times(1)).save(Mockito.any(Payment.class));
    }

    @Test
    public void testInitPayment2() {
        Payment payment = new Payment();
        Mockito.when(paymentRepository.findById(Mockito.anyString()).get()).thenReturn(payment);
        Mockito.when(paymentRepository.save(Mockito.any(Payment.class))).thenReturn(null);
        insidePaymentServiceImpl.initPayment(payment, headers);
        Mockito.verify(paymentRepository, times(0)).save(Mockito.any(Payment.class));
    }

}


package foodsearch;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;
import org.springframework.cloud.client.loadbalancer.LoadBalanced;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.EnableAspectJAutoProxy;
import org.springframework.integration.annotation.IntegrationComponentScan;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.web.client.RestTemplate;
import springfox.documentation.swagger2.annotations.EnableSwagger2;

@SpringBootApplication
@EnableAspectJAutoProxy(proxyTargetClass = true)
@EnableAsync
@IntegrationComponentScan
@EnableSwagger2
@EnableDiscoveryClient
public class FoodApplication {

    public static void main(String[] args) {
        SpringApplication.run(FoodApplication.class, args);
    }

    @LoadBalanced
    @Bean
    public RestTemplate restTemplate(RestTemplateBuilder builder) {
        return builder.build();
    }

}


package adminorder.controller;

import com.alibaba.fastjson.JSONObject;
import edu.fudan.common.util.Response;
import foodsearch.controller.FoodController;
import foodsearch.entity.FoodOrder;
import foodsearch.service.FoodService;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.springframework.http.*;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.request.MockMvcRequestBuilders;
import org.springframework.test.web.servlet.result.MockMvcResultMatchers;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

@RunWith(JUnit4.class)
public class FoodControllerTest {

    @InjectMocks
    private FoodController foodController;

    @Mock
    private FoodService foodService;
    private MockMvc mockMvc;
    private Response response = new Response();

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
        mockMvc = MockMvcBuilders.standaloneSetup(foodController).build();
    }

    @Test
    public void testHome() throws Exception {
        mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/foodservice/welcome"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andExpect(MockMvcResultMatchers.content().string("Welcome to [ Food Service ] !"));
    }

    @Test
    public void testFindAllFoodOrder() throws Exception {
        Mockito.when(foodService.findAllFoodOrder(Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/foodservice/orders"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testCreateFoodOrder() throws Exception {
        FoodOrder addFoodOrder = new FoodOrder();
        Mockito.when(foodService.createFoodOrder(Mockito.any(FoodOrder.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(addFoodOrder);
        String result = mockMvc.perform(MockMvcRequestBuilders.post("/api/v1/foodservice/orders").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testUpdateFoodOrder() throws Exception {
        FoodOrder updateFoodOrder = new FoodOrder();
        Mockito.when(foodService.updateFoodOrder(Mockito.any(FoodOrder.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(updateFoodOrder);
        String result = mockMvc.perform(MockMvcRequestBuilders.put("/api/v1/foodservice/orders").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testDeleteFoodOrder() throws Exception {
        Mockito.when(foodService.deleteFoodOrder(Mockito.anyString(), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.delete("/api/v1/foodservice/orders/order_id"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testFindFoodOrderByOrderId() throws Exception {
        Mockito.when(foodService.findByOrderId(Mockito.anyString(), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/foodservice/orders/order_id"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testGetAllFood() throws Exception {
        Mockito.when(foodService.getAllFood(Mockito.anyString(), Mockito.anyString(), Mockito.anyString(), Mockito.anyString(), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/foodservice/foods/date/start_station/end_station/trip_id"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

}


// Node: testFindAllFoodOrder
// Node: testCreateFoodOrder
// Node: testUpdateFoodOrder
// Node: testDeleteFoodOrder
// Node: testFindFoodOrderByOrderId
// Node: testGetAllFood
package adminorder.service;

import edu.fudan.common.util.Response;
import foodsearch.entity.FoodOrder;
import foodsearch.repository.FoodOrderRepository;
import foodsearch.service.FoodServiceImpl;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.springframework.http.HttpHeaders;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

@RunWith(JUnit4.class)
public class FoodServiceImplTest {

    @InjectMocks
    private FoodServiceImpl foodServiceImpl;

    @Mock
    private FoodOrderRepository foodOrderRepository;

    private HttpHeaders headers = new HttpHeaders();

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
    }

    @Test
    public void testCreateFoodOrder1() {
        FoodOrder fo = new FoodOrder();
        Mockito.when(foodOrderRepository.findByOrderId(Mockito.any(UUID.class).toString())).thenReturn(fo);
        Response result = foodServiceImpl.createFoodOrder(fo, headers);
        Assert.assertEquals(new Response<>(0, "Order Id Has Existed.", null), result);
    }

    @Test
    public void testCreateFoodOrder2() {
        FoodOrder fo = new FoodOrder(UUID.randomUUID().toString(), UUID.randomUUID().toString(), 2, "station_name", "store_name", "food_name", 3.0);
        Mockito.when(foodOrderRepository.findByOrderId(Mockito.any(UUID.class).toString())).thenReturn(null);
        Mockito.when(foodOrderRepository.save(Mockito.any(FoodOrder.class))).thenReturn(null);
        Response result = foodServiceImpl.createFoodOrder(fo, headers);
        Assert.assertEquals("Success.", result.getMsg());
    }

    @Test
    public void testDeleteFoodOrder1() {
        UUID orderId = UUID.randomUUID();
        Mockito.when(foodOrderRepository.findByOrderId(Mockito.any(UUID.class).toString())).thenReturn(null);
        Response result = foodServiceImpl.deleteFoodOrder(orderId.toString(), headers);
        Assert.assertEquals(new Response<>(0, "Order Id Is Non-Existent.", null), result);
    }

    @Test
    public void testDeleteFoodOrder2() {
        UUID orderId = UUID.randomUUID();
        FoodOrder foodOrder = new FoodOrder();
        Mockito.when(foodOrderRepository.findByOrderId(Mockito.any(UUID.class).toString())).thenReturn(foodOrder);
        Mockito.doNothing().doThrow(new RuntimeException()).when(foodOrderRepository).deleteFoodOrderByOrderId(Mockito.any(UUID.class).toString());
        Response result = foodServiceImpl.deleteFoodOrder(orderId.toString(), headers);
        Assert.assertEquals(new Response<>(1, "Success.", null), result);
    }

    @Test
    public void testFindAllFoodOrder1() {
        List<FoodOrder> foodOrders = new ArrayList<>();
        foodOrders.add(new FoodOrder());
        Mockito.when(foodOrderRepository.findAll()).thenReturn(foodOrders);
        Response result = foodServiceImpl.findAllFoodOrder(headers);
        Assert.assertEquals(new Response<>(1, "Success.", foodOrders), result);
    }

    @Test
    public void testFindAllFoodOrder2() {
        Mockito.when(foodOrderRepository.findAll()).thenReturn(null);
        Response result = foodServiceImpl.findAllFoodOrder(headers);
        Assert.assertEquals(new Response<>(0, "No Content", null), result);
    }

    @Test
    public void testUpdateFoodOrder1() {
        FoodOrder updateFoodOrder = new FoodOrder();
        Mockito.when(foodOrderRepository.findById(Mockito.any(UUID.class).toString())).thenReturn(null);
        Response result = foodServiceImpl.updateFoodOrder(updateFoodOrder, headers);
        Assert.assertEquals(new Response<>(0, "Order Id Is Non-Existent.", null), result);
    }

    @Test
    public void testUpdateFoodOrder2() {
        FoodOrder updateFoodOrder = new FoodOrder(UUID.randomUUID().toString(), UUID.randomUUID().toString(), 1, "station_name", "store_name", "food_name", 3.0);
        Mockito.when(foodOrderRepository.findById(Mockito.any(UUID.class).toString())).thenReturn(Optional.of(updateFoodOrder));
        Mockito.when(foodOrderRepository.save(Mockito.any(FoodOrder.class))).thenReturn(null);
        Response result = foodServiceImpl.updateFoodOrder(updateFoodOrder, headers);
        Assert.assertEquals(new Response<>(1, "Success", updateFoodOrder), result);
    }

    @Test
    public void testFindByOrderId1() {
        UUID orderId = UUID.randomUUID();
        FoodOrder fo = new FoodOrder();
        Mockito.when(foodOrderRepository.findByOrderId(Mockito.any(UUID.class).toString())).thenReturn(fo);
        Response result = foodServiceImpl.findByOrderId(orderId.toString(), headers);
        Assert.assertEquals(new Response<>(1, "Success.", fo), result);
    }

    @Test
    public void testFindByOrderId2() {
        UUID orderId = UUID.randomUUID();
        Mockito.when(foodOrderRepository.findByOrderId(Mockito.any(UUID.class).toString())).thenReturn(null);
        Response result = foodServiceImpl.findByOrderId(orderId.toString(), headers);
        Assert.assertEquals(new Response<>(0, "Order Id Is Non-Existent.", null), result);
    }

    @Test
    public void testGetAllFood() {

    }

}


package route;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;
import org.springframework.cloud.client.loadbalancer.LoadBalanced;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.EnableAspectJAutoProxy;
import org.springframework.integration.annotation.IntegrationComponentScan;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.web.client.RestTemplate;
import springfox.documentation.swagger2.annotations.EnableSwagger2;

/**
 * @author fdse
 */
@SpringBootApplication
@EnableAspectJAutoProxy(proxyTargetClass = true)
@EnableAsync
@IntegrationComponentScan
@EnableSwagger2
@EnableDiscoveryClient
public class RouteApplication {

    public static void main(String[] args) {
        SpringApplication.run(RouteApplication.class, args);
    }

    @LoadBalanced
    @Bean
    public RestTemplate restTemplate(RestTemplateBuilder builder) {
        return builder.build();
    }
}


// Node: createAndModify
package route.controller;

import edu.fudan.common.util.Response;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import route.entity.RouteInfo;
import route.service.RouteService;

import java.util.List;

import static org.springframework.http.ResponseEntity.ok;

/**
 * @author fdse
 */
@RestController
@RequestMapping("/api/v1/routeservice")
public class RouteController {
    private static final Logger LOGGER = LoggerFactory.getLogger(RouteController.class);
    @Autowired
    private RouteService routeService;

    @GetMapping(path = "/welcome")
    public String home() {
        return "Welcome to [ Route Service ] !";
    }

    @PostMapping(path = "/routes")
    public ResponseEntity<Response> createAndModifyRoute(@RequestBody RouteInfo createAndModifyRouteInfo, @RequestHeader HttpHeaders headers) {
        RouteController.LOGGER.info("[createAndModify][Create route][start: {}, end: {}]", createAndModifyRouteInfo.getStartStation(),createAndModifyRouteInfo.getEndStation());
        return ok(routeService.createAndModify(createAndModifyRouteInfo, headers));
    }

    @DeleteMapping(path = "/routes/{routeId}")
    public HttpEntity deleteRoute(@PathVariable String routeId, @RequestHeader HttpHeaders headers) {
        RouteController.LOGGER.info("[deleteRoute][Delete route][RouteId: {}]", routeId);
        return ok(routeService.deleteRoute(routeId, headers));
    }

    @GetMapping(path = "/routes/{routeId}")
    public HttpEntity queryById(@PathVariable String routeId, @RequestHeader HttpHeaders headers) {
        RouteController.LOGGER.info("[getRouteById][Query route by id][RouteId: {}]", routeId);
        return ok(routeService.getRouteById(routeId, headers));
    }

    @PostMapping(path = "/routes/byIds")
    public HttpEntity queryByIds(@RequestBody List<String> routeIds, @RequestHeader HttpHeaders headers) {
        RouteController.LOGGER.info("[getRouteById][Query route by id][RouteId: {}]", routeIds);
        return ok(routeService.getRouteByIds(routeIds, headers));
    }

    @GetMapping(path = "/routes")
    public HttpEntity queryAll(@RequestHeader HttpHeaders headers) {
        RouteController.LOGGER.info("[getAllRoutes][Query all routes]");
        return ok(routeService.getAllRoutes(headers));
    }

    @GetMapping(path = "/routes/{start}/{end}")
    public HttpEntity queryByStartAndTerminal(@PathVariable String start,
                                              @PathVariable String end,
                                              @RequestHeader HttpHeaders headers) {
        RouteController.LOGGER.info("[getRouteByStartAndEnd][Query routes][start: {}, end: {}]", start, end);
        return ok(routeService.getRouteByStartAndEnd(start, end, headers));
    }

}

// Node: queryById
// Node: getRouteById
// Node: queryByStartAndTerminal
// Node: getRouteByStartAndEnd
package route.service;

import edu.fudan.common.util.Response;
import org.springframework.http.HttpHeaders;
import route.entity.*;

import java.util.List;


/**
 * @author fdse
 */
public interface RouteService {

    /**
     * get route with id
     *
     * @param startId start station id
     * @param terminalId terminal station id
     * @param headers headers
     * @return Response
     */
    Response getRouteByStartAndEnd(String startId, String terminalId, HttpHeaders headers);

    /**
     * get all routes
     *
     * @param headers headers
     * @return Response
     */
    Response getAllRoutes(HttpHeaders headers);

    /**
     * get route by id
     *
     * @param routeId route id
     * @param headers headers
     * @return Response
     */
    Response getRouteById(String routeId, HttpHeaders headers);

    /**
     * get route by ids
     *
     * @param routeIds route ids
     * @param headers headers
     * @return Response
     */
    Response getRouteByIds(List<String> routeIds, HttpHeaders headers);

    /**
     * delete route by id
     *
     * @param routeId route id
     * @param headers headers
     * @return Response
     */
    Response deleteRoute(String routeId, HttpHeaders headers);

    /**
     * create route and modify
     *
     * @param info info
     * @param headers headers
     * @return Response
     */
    Response createAndModify(RouteInfo info, HttpHeaders headers);

}


// Node: repos/cloned_ms_repos/train-ticket/ts-route-service/src/main/java/route/service/RouteService.java:RouteService.<init>
package route.service;

import edu.fudan.common.util.Response;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpHeaders;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import route.entity.Route;
import route.entity.RouteInfo;
import route.repository.RouteRepository;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

/**
 * @author fdse
 */
@Service
public class RouteServiceImpl implements RouteService {

    @Autowired
    private RouteRepository routeRepository;
    private static final Logger LOGGER = LoggerFactory.getLogger(RouteServiceImpl.class);

    String success = "Success";

    @Override
    public Response createAndModify(RouteInfo info, HttpHeaders headers) {
        RouteServiceImpl.LOGGER.info("[createAndModify][Create and modify start and end][Start: {} End: {}]", info.getStartStation(), info.getEndStation());

        String[] stations = info.getStationList().split(",");
        String[] distances = info.getDistanceList().split(",");
        List<String> stationList = new ArrayList<>();
        List<Integer> distanceList = new ArrayList<>();
        if (stations.length != distances.length) {
            RouteServiceImpl.LOGGER.error("[createAndModify][Create and modify error][Station number not equal to distance number][RouteId: {}]",info.getId());
            return new Response<>(0, "Station Number Not Equal To Distance Number", null);
        }
        for (int i = 0; i < stations.length; i++) {
            stationList.add(stations[i]);
            distanceList.add(Integer.parseInt(distances[i]));
        }
        int maxIdArrayLen = 32;
        Route route = new Route();
        if (info.getId() == null || info.getId().length() < maxIdArrayLen) {
            route.setId(UUID.randomUUID().toString());
        }else{
            Optional<Route> routeOld = routeRepository.findById(info.getId());
            if(routeOld.isPresent()) {
                route = routeOld.get();
            } else {
                route.setId(info.getId());
            }
        }
        route.setStartStation(info.getStartStation());
        route.setEndStation(info.getEndStation());
        route.setStations(stationList);
        route.setDistances(distanceList);
        routeRepository.save(route);
        return new Response<>(1, "Save and Modify success", route);
    }

    @Override
    @Transactional
    public Response deleteRoute(String routeId, HttpHeaders headers) {
        routeRepository.removeRouteById(routeId);
        Optional<Route> route = routeRepository.findById(routeId);
        if (!route.isPresent()) {
            return new Response<>(1, "Delete Success", routeId);
        } else {
            RouteServiceImpl.LOGGER.error("[deleteRoute][Delete error][Route not found][RouteId: {}]",routeId);
            return new Response<>(0, "Delete failed, Reason unKnown with this routeId", routeId);
        }
    }

    @Override
    public Response getRouteById(String routeId, HttpHeaders headers) {
        Optional<Route> route = routeRepository.findById(routeId);
        if (!route.isPresent()) {
            RouteServiceImpl.LOGGER.error("[getRouteById][Find route error][Route not found][RouteId: {}]",routeId);
            return new Response<>(0, "No content with the routeId", null);
        } else {
            return new Response<>(1, success, route);
        }

    }

    @Override
    public Response getRouteByIds(List<String> routeIds, HttpHeaders headers) {
        List<Route> routes = routeRepository.findByIds(routeIds);
        if (routes == null || routes.isEmpty()) {
            RouteServiceImpl.LOGGER.error("[getRouteById][Find route error][Route not found][RouteIds: {}]",routeIds);
            return new Response<>(0, "No content with the routeIds", null);
        } else {
            return new Response<>(1, success, routes);
        }
    }

    @Override
    public Response getRouteByStartAndEnd(String startId, String terminalId, HttpHeaders headers) {
        ArrayList<Route> routes = routeRepository.findAll();
        RouteServiceImpl.LOGGER.info("[getRouteByStartAndEnd][Find All][size:{}]", routes.size());
        List<Route> resultList = new ArrayList<>();
        for (Route route : routes) {
            if (route.getStations().contains(startId) &&
                    route.getStations().contains(terminalId) &&
                    route.getStations().indexOf(startId) < route.getStations().indexOf(terminalId)) {
                resultList.add(route);
            }
        }
        if (!resultList.isEmpty()) {
            return new Response<>(1, success, resultList);
        } else {
            RouteServiceImpl.LOGGER.warn("[getRouteByStartAndEnd][Find by start and terminal warn][Routes not found][startId: {},terminalId: {}]",startId,terminalId);
            return new Response<>(0, "No routes with the startId and terminalId", null);
        }
    }

    @Override
    public Response getAllRoutes(HttpHeaders headers) {
        ArrayList<Route> routes = routeRepository.findAll();
        if (routes != null && !routes.isEmpty()) {
            return new Response<>(1, success, routes);
        } else {
            RouteServiceImpl.LOGGER.warn("[getAllRoutes][Find all routes warn][{}]","No Content");
            return new Response<>(0, "No Content", null);
        }
    }

}

package route.controller;

import com.alibaba.fastjson.JSONObject;
import edu.fudan.common.util.Response;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.springframework.http.*;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.request.MockMvcRequestBuilders;
import org.springframework.test.web.servlet.result.MockMvcResultMatchers;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import route.entity.RouteInfo;
import route.service.RouteService;

@RunWith(JUnit4.class)
public class RouteControllerTest {

    @InjectMocks
    private RouteController routeController;

    @Mock
    private RouteService routeService;
    private MockMvc mockMvc;
    private Response response = new Response();

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
        mockMvc = MockMvcBuilders.standaloneSetup(routeController).build();
    }

    @Test
    public void testHome() throws Exception {
        mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/routeservice/welcome"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andExpect(MockMvcResultMatchers.content().string("Welcome to [ Route Service ] !"));
    }

    @Test
    public void testCreateAndModifyRoute() throws Exception {
        RouteInfo createAndModifyRouteInfo = new RouteInfo();
        Mockito.when(routeService.createAndModify(Mockito.any(RouteInfo.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(createAndModifyRouteInfo);
        String result = mockMvc.perform(MockMvcRequestBuilders.post("/api/v1/routeservice/routes").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testDeleteRoute() throws Exception {
        Mockito.when(routeService.deleteRoute(Mockito.anyString(), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.delete("/api/v1/routeservice/routes/route_id"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testQueryById() throws Exception {
        Mockito.when(routeService.getRouteById(Mockito.anyString(), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/routeservice/routes/route_id"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testQueryAll() throws Exception {
        Mockito.when(routeService.getAllRoutes(Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/routeservice/routes"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testQueryByStartAndTerminal() throws Exception {
        Mockito.when(routeService.getRouteByStartAndEnd(Mockito.anyString(), Mockito.anyString(), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/routeservice/routes/start_id/terminal_id"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

}


// Node: testQueryById
// Node: testQueryByStartAndTerminal
package route.service;

import edu.fudan.common.util.Response;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.springframework.http.HttpHeaders;
import route.entity.Route;
import route.entity.RouteInfo;
import route.repository.RouteRepository;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

@RunWith(JUnit4.class)
public class RouteServiceImplTest {

    @InjectMocks
    private RouteServiceImpl routeServiceImpl;

    @Mock
    private RouteRepository routeRepository;

    private HttpHeaders headers = new HttpHeaders();

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
    }

    @Test
    public void testCreateAndModify1() {
        RouteInfo info = new RouteInfo("id", "start_station", "end_station", "shanghai", "5,10");
        Response result = routeServiceImpl.createAndModify(info, headers);
        Assert.assertEquals(new Response<>(0, "Station Number Not Equal To Distance Number", null), result);
    }

    @Test
    public void testCreateAndModify2() {
        RouteInfo info = new RouteInfo("id", "start_station", "end_station", "shanghai", "5");
        Mockito.when(routeRepository.save(Mockito.any(Route.class))).thenReturn(null);
        Response result = routeServiceImpl.createAndModify(info, headers);
        Assert.assertEquals("Save Success", result.getMsg());
    }

    @Test
    public void testCreateAndModify3() {
        RouteInfo info = new RouteInfo("id123456789", "start_station", "end_station", "shanghai", "5");
        Mockito.when(routeRepository.findById(Mockito.anyString())).thenReturn(null);
        Mockito.when(routeRepository.save(Mockito.any(Route.class))).thenReturn(null);
        Response result = routeServiceImpl.createAndModify(info, headers);
        Assert.assertEquals("Modify success", result.getMsg());
    }

    @Test
    public void testDeleteRoute1() {
        Mockito.doNothing().doThrow(new RuntimeException()).when(routeRepository).removeRouteById(Mockito.anyString());
        Mockito.when(routeRepository.findById(Mockito.anyString())).thenReturn(null);
        Response result = routeServiceImpl.deleteRoute("route_id", headers);
        Assert.assertEquals(new Response<>(1, "Delete Success", "route_id"), result);
    }

    @Test
    public void testDeleteRoute2() {
        Route route = new Route();
        Mockito.doNothing().doThrow(new RuntimeException()).when(routeRepository).removeRouteById(Mockito.anyString());
        Mockito.when(routeRepository.findById(Mockito.anyString()).get()).thenReturn(route);
        Response result = routeServiceImpl.deleteRoute("route_id", headers);
        Assert.assertEquals(new Response<>(0, "Delete failed, Reason unKnown with this routeId", "route_id"), result);
    }

    @Test
    public void testGetRouteById1() {
        Mockito.when(routeRepository.findById(Mockito.anyString())).thenReturn(null);
        Response result = routeServiceImpl.getRouteById("route_id", headers);
        Assert.assertEquals(new Response<>(0, "No content with the routeId", null), result);
    }

    @Test
    public void testGetRouteById2() {
        Route route = new Route();
        Mockito.when(routeRepository.findById(Mockito.anyString()).get()).thenReturn(route);
        Response result = routeServiceImpl.getRouteById("route_id", headers);
        Assert.assertEquals(new Response<>(1, "Success", route), result);
    }

    @Test
    public void testGetRouteByStartAndTerminal1() {
        List<String> stations = new ArrayList<>();
        stations.add("shanghai");
        stations.add("nanjing");
        List<Integer> distances = new ArrayList<>();
        distances.add(5);
        distances.add(10);
        Route route = new Route(UUID.randomUUID().toString(), stations, distances, "shanghai", "nanjing");
        ArrayList<Route> routes = new ArrayList<>();
        routes.add(route);
        Mockito.when(routeRepository.findAll()).thenReturn(routes);
        Response result = routeServiceImpl.getRouteByStartAndEnd("shanghai", "nanjing", headers);
        Assert.assertEquals("Success", result.getMsg());
    }

    @Test
    public void testGetRouteByStartAndTerminal2() {
        ArrayList<Route> routes = new ArrayList<>();
        Mockito.when(routeRepository.findAll()).thenReturn(routes);
        Response result = routeServiceImpl.getRouteByStartAndEnd("shanghai", "nanjing", headers);
        Assert.assertEquals("No routes with the startId and terminalId", result.getMsg());
    }

    @Test
    public void testGetAllRoutes1() {
        ArrayList<Route> routes = new ArrayList<>();
        routes.add(new Route());
        Mockito.when(routeRepository.findAll()).thenReturn(routes);
        Response result = routeServiceImpl.getAllRoutes(headers);
        Assert.assertEquals("Success", result.getMsg());
    }

    @Test
    public void testGetAllRoutes2() {
        Mockito.when(routeRepository.findAll()).thenReturn(null);
        Response result = routeServiceImpl.getAllRoutes(headers);
        Assert.assertEquals("No Content", result.getMsg());
    }

}


// Node: testCreateAndModify1
package consign;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;
import org.springframework.cloud.client.loadbalancer.LoadBalanced;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.EnableAspectJAutoProxy;
import org.springframework.integration.annotation.IntegrationComponentScan;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.web.client.RestTemplate;
import springfox.documentation.swagger2.annotations.EnableSwagger2;

/**
 * @author fdse
 */
@SpringBootApplication
@EnableAspectJAutoProxy(proxyTargetClass = true)
@EnableAsync
@IntegrationComponentScan
@EnableSwagger2
@EnableDiscoveryClient
public class ConsignApplication {
    public static void main(String[] args) {
        SpringApplication.run(ConsignApplication.class, args);
    }

    @LoadBalanced
    @Bean
    public RestTemplate restTemplate(RestTemplateBuilder builder) {
        return builder.build();
    }
}


package consign.controller;

import com.alibaba.fastjson.JSONObject;
import consign.entity.Consign;
import consign.service.ConsignService;
import edu.fudan.common.util.Response;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.springframework.http.*;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.request.MockMvcRequestBuilders;
import org.springframework.test.web.servlet.result.MockMvcResultMatchers;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

import java.util.UUID;

@RunWith(JUnit4.class)
public class ConsignControllerTest {

    @InjectMocks
    private ConsignController consignController;

    @Mock
    private ConsignService service;
    private MockMvc mockMvc;
    private Response response = new Response();

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
        mockMvc = MockMvcBuilders.standaloneSetup(consignController).build();
    }

    @Test
    public void testHome() throws Exception {
        mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/consignservice/welcome"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andExpect(MockMvcResultMatchers.content().string("Welcome to [ Consign Service ] !"));
    }

    @Test
    public void testInsertConsign() throws Exception {
        Consign request = new Consign();
        Mockito.when(service.insertConsignRecord(Mockito.any(Consign.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(request);
        String result = mockMvc.perform(MockMvcRequestBuilders.post("/api/v1/consignservice/consigns").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testUpdateConsign() throws Exception {
        Consign request = new Consign();
        Mockito.when(service.updateConsignRecord(Mockito.any(Consign.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(request);
        String result = mockMvc.perform(MockMvcRequestBuilders.put("/api/v1/consignservice/consigns").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testFindByAccountId() throws Exception {
        UUID id = UUID.randomUUID();
        Mockito.when(service.queryByAccountId(Mockito.any(UUID.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/consignservice/consigns/account/" + id.toString()))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testFindByOrderId() throws Exception {
        UUID id = UUID.randomUUID();
        Mockito.when(service.queryByOrderId(Mockito.any(UUID.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/consignservice/consigns/order/" + id.toString()))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testFindByConsignee() throws Exception {
        Mockito.when(service.queryByConsignee(Mockito.anyString(), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/consignservice/consigns/consignee"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

}


// Node: testInsertConsign
// Node: testUpdateConsign
// Node: testFindByAccountId
// Node: testFindByOrderId
// Node: testFindByConsignee
package consign.service;

import consign.entity.Consign;
import consign.entity.ConsignRecord;
import consign.repository.ConsignRepository;
import edu.fudan.common.util.Response;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.*;
import org.springframework.web.client.RestTemplate;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

@RunWith(JUnit4.class)
public class ConsignServiceImplTest {

    @InjectMocks
    private ConsignServiceImpl consignServiceImpl;

    @Mock
    private ConsignRepository repository;

    @Mock
    private RestTemplate restTemplate;

    private HttpHeaders headers = new HttpHeaders();

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
    }

    @Test
    public void testInsertConsignRecord() {
        HttpEntity requestEntity = new HttpEntity(null, headers);
        Response<Double> response = new Response<>(1, null, 3.0);
        ResponseEntity<Response<Double>> re = new ResponseEntity<>(response, HttpStatus.OK);
        Consign consignRequest = new Consign(UUID.randomUUID().toString(), UUID.randomUUID().toString(), UUID.randomUUID().toString(), "handle_date", "target_date", "place_from", "place_to", "consignee", "10001", 1.0, true);
        ConsignRecord consignRecord = new ConsignRecord(UUID.randomUUID().toString(), UUID.randomUUID().toString(), UUID.randomUUID().toString(), "handle_date", "target_date", "place_from", "place_to", "consignee", "10001", 1.0, 3.0);
        Mockito.when(restTemplate.exchange(
                "http://ts-consign-price-service:16110/api/v1/consignpriceservice/consignprice/" + consignRequest.getWeight() + "/" + consignRequest.isWithin(),
                HttpMethod.GET,
                requestEntity,
                new ParameterizedTypeReference<Response<Double>>() {
                })).thenReturn(re);
        Mockito.when(repository.save(Mockito.any(ConsignRecord.class))).thenReturn(consignRecord);
        Response result = consignServiceImpl.insertConsignRecord(consignRequest, headers);
        Assert.assertEquals(new Response<>(1, "You have consigned successfully! The price is 3.0", consignRecord), result);
    }

    @Test
    public void testUpdateConsignRecord1() {
        HttpEntity requestEntity = new HttpEntity(null, headers);
        Response<Double> response = new Response<>(1, null, 3.0);
        ResponseEntity<Response<Double>> re = new ResponseEntity<>(response, HttpStatus.OK);
        Consign consignRequest = new Consign(UUID.randomUUID().toString(), UUID.randomUUID().toString(), UUID.randomUUID().toString(), "handle_date", "target_date", "place_from", "place_to", "consignee", "10001", 1.0, true);
        ConsignRecord consignRecord = new ConsignRecord(UUID.randomUUID().toString(), UUID.randomUUID().toString(), UUID.randomUUID().toString(), "handle_date", "target_date", "place_from", "place_to", "consignee", "10001", 2.0, 3.0);
        Mockito.when(repository.findById(Mockito.anyString())).thenReturn(java.util.Optional.of(consignRecord));
        Mockito.when(restTemplate.exchange(
                "http://ts-consign-price-service:16110/api/v1/consignpriceservice/consignprice/" + consignRequest.getWeight() + "/" + consignRequest.isWithin(),
                HttpMethod.GET,
                requestEntity,
                new ParameterizedTypeReference<Response<Double>>() {
                })).thenReturn(re);
        Mockito.when(repository.save(Mockito.any(ConsignRecord.class))).thenReturn(null);
        Response result = consignServiceImpl.updateConsignRecord(consignRequest, headers);
        consignRecord.setWeight(1.0);
        Assert.assertEquals(new Response<>(1, "Update consign success", consignRecord), result);
    }

    @Test
    public void testUpdateConsignRecord2() {
        Consign consignRequest = new Consign(UUID.randomUUID().toString(), UUID.randomUUID().toString(), UUID.randomUUID().toString(), "handle_date", "target_date", "place_from", "place_to", "consignee", "10001", 1.0, true);
        ConsignRecord consignRecord = new ConsignRecord(UUID.randomUUID().toString(), UUID.randomUUID().toString(), UUID.randomUUID().toString(), "handle_date", "target_date", "place_from", "place_to", "consignee", "10001", 1.0, 3.0);
        Mockito.when(repository.findById(Mockito.anyString())).thenReturn(java.util.Optional.of(consignRecord));
        Mockito.when(repository.save(Mockito.any(ConsignRecord.class))).thenReturn(null);
        Response result = consignServiceImpl.updateConsignRecord(consignRequest, headers);
        Assert.assertEquals(new Response<>(1, "Update consign success", consignRecord), result);
    }

    @Test
    public void testQueryByAccountId1() {
        UUID accountId = UUID.randomUUID();
        ArrayList<ConsignRecord> consignRecords = new ArrayList<>();
        consignRecords.add(new ConsignRecord());
        Mockito.when(repository.findByAccountId(Mockito.anyString())).thenReturn(consignRecords);
        Response result = consignServiceImpl.queryByAccountId(accountId, headers);
        Assert.assertEquals(new Response<>(1, "Find consign by account id success", consignRecords), result);
    }

    @Test
    public void testQueryByAccountId2() {
        UUID accountId = UUID.randomUUID();
        Mockito.when(repository.findByAccountId(Mockito.anyString())).thenReturn(null);
        Response result = consignServiceImpl.queryByAccountId(accountId, headers);
        Assert.assertEquals(new Response<>(0, "No Content according to accountId", null), result);
    }

    @Test
    public void testQueryByOrderId1() {
        UUID orderId = UUID.randomUUID();
        ConsignRecord consignRecords = new ConsignRecord();
        Mockito.when(repository.findByOrderId(Mockito.anyString())).thenReturn(consignRecords);
        Response result = consignServiceImpl.queryByOrderId(orderId, headers);
        Assert.assertEquals(new Response<>(1, "Find consign by order id success", consignRecords), result);
    }

    @Test
    public void testQueryByOrderId2() {
        UUID orderId = UUID.randomUUID();
        Mockito.when(repository.findByOrderId(Mockito.anyString())).thenReturn(null);
        Response result = consignServiceImpl.queryByOrderId(orderId, headers);
        Assert.assertEquals(new Response<>(0, "No Content according to order id", null), result);
    }

    @Test
    public void testQueryByConsignee1() {
        ArrayList<ConsignRecord> consignRecords = new ArrayList<>();
        consignRecords.add(new ConsignRecord());
        Mockito.when(repository.findByConsignee(Mockito.anyString())).thenReturn(consignRecords);
        Response result = consignServiceImpl.queryByConsignee("consignee", headers);
        Assert.assertEquals(new Response<>(1, "Find consign by consignee success", consignRecords), result);
    }

    @Test
    public void testQueryByConsignee2() {
        Mockito.when(repository.findByConsignee(Mockito.anyString())).thenReturn(null);
        Response result = consignServiceImpl.queryByConsignee("consignee", headers);
        Assert.assertEquals(new Response<>(0, "No Content according to consignee", null), result);
    }

}


package verifycode;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;
import org.springframework.cloud.client.loadbalancer.LoadBalanced;
import org.springframework.context.annotation.Bean;
import org.springframework.web.client.RestTemplate;

/**
 * @author fdse
 */
@SpringBootApplication
@EnableDiscoveryClient
public class VerifyCodeApplication {
    public static void main(String[] args) {
        SpringApplication.run(VerifyCodeApplication.class, args);
    }
    @LoadBalanced
    @Bean
    public RestTemplate restTemplate(RestTemplateBuilder builder) {
        return builder.build();
    }
}


// Node: getImageCode
// Node: verifyCode
package verifycode.service;

import org.springframework.http.HttpHeaders;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.io.OutputStream;
import java.util.Map;

/**
 * @author fdse
 */
public interface VerifyCodeService {

    Map<String, Object> getImageCode(int width, int height, OutputStream os, HttpServletRequest request, HttpServletResponse response, HttpHeaders headers);

    boolean verifyCode(HttpServletRequest request, HttpServletResponse response, String receivedCode, HttpHeaders headers);

}


// Node: repos/cloned_ms_repos/train-ticket/ts-verification-code-service/src/main/java/verifycode/service/VerifyCodeService.java:VerifyCodeService.<init>
package verifycode.controller;

import com.alibaba.fastjson.JSONObject;
import edu.fudan.common.util.Response;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.springframework.http.HttpHeaders;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.request.MockMvcRequestBuilders;
import org.springframework.test.web.servlet.result.MockMvcResultMatchers;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import verifycode.service.VerifyCodeService;

import javax.servlet.*;
import javax.servlet.http.*;
import java.awt.image.BufferedImage;
import java.io.*;
import java.rmi.MarshalledObject;
import java.security.Principal;
import java.util.*;

@RunWith(JUnit4.class)
public class VerifyCodeControllerTest {

    @InjectMocks
    private VerifyCodeController verifyCodeController;

    @Mock
    private VerifyCodeService verifyCodeService;
    private MockMvc mockMvc;

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
        mockMvc = MockMvcBuilders.standaloneSetup(verifyCodeController).build();
    }

    @Test
    public void testImageCode() throws Exception {
        Map<String, Object> map = new HashMap<>();
        BufferedImage image = new BufferedImage(60, 20, BufferedImage.TYPE_INT_RGB);
        map.put("strEnsure", "XYZ8");
        map.put("image", image);
        Mockito.when(verifyCodeService.getImageCode(Mockito.anyInt(), Mockito.anyInt(), Mockito.any(OutputStream.class), Mockito.any(HttpServletRequest.class), Mockito.any(HttpServletResponse.class), Mockito.any(HttpHeaders.class))).thenReturn(map);
        mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/verifycode/generate")).andReturn();
        Mockito.verify(verifyCodeService, Mockito.times(1)).getImageCode(Mockito.anyInt(), Mockito.anyInt(), Mockito.any(OutputStream.class), Mockito.any(HttpServletRequest.class), Mockito.any(HttpServletResponse.class), Mockito.any(HttpHeaders.class));
    }

    @Test
    public void testVerifyCode() throws Exception {
        Mockito.when(verifyCodeService.verifyCode(Mockito.any(HttpServletRequest.class), Mockito.any(HttpServletResponse.class), Mockito.anyString(), Mockito.any(HttpHeaders.class))).thenReturn(true);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/verifycode/verify/verifyCode"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertTrue(JSONObject.parseObject(result, Boolean.class));
    }

}


// Node: testImageCode
// Node: testVerifyCode
package verifycode.service;

import org.junit.Assert;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;
import org.springframework.http.HttpHeaders;
import verifycode.service.impl.VerifyCodeServiceImpl;

import javax.servlet.*;
import javax.servlet.http.*;
import java.io.*;
import java.security.Principal;
import java.util.Collection;
import java.util.Enumeration;
import java.util.Locale;
import java.util.Map;

@RunWith(JUnit4.class)
public class VerifyCodeServiceImplTest {

    private VerifyCodeServiceImpl verifyCodeServiceImpl = new VerifyCodeServiceImpl();
    private HttpHeaders headers = new HttpHeaders();

    private HttpServletRequest request = new HttpServletRequest() {
        @Override
        public String getAuthType() {
            return null;
        }

        @Override
        public Cookie[] getCookies() {
            return new Cookie[0];
        }

        @Override
        public long getDateHeader(String s) {
            return 0;
        }

        @Override
        public String getHeader(String s) {
            return null;
        }

        @Override
        public Enumeration<String> getHeaders(String s) {
            return null;
        }

        @Override
        public Enumeration<String> getHeaderNames() {
            return null;
        }

        @Override
        public int getIntHeader(String s) {
            return 0;
        }

        @Override
        public String getMethod() {
            return null;
        }

        @Override
        public String getPathInfo() {
            return null;
        }

        @Override
        public String getPathTranslated() {
            return null;
        }

        @Override
        public String getContextPath() {
            return null;
        }

        @Override
        public String getQueryString() {
            return null;
        }

        @Override
        public String getRemoteUser() {
            return null;
        }

        @Override
        public boolean isUserInRole(String s) {
            return false;
        }

        @Override
        public Principal getUserPrincipal() {
            return null;
        }

        @Override
        public String getRequestedSessionId() {
            return null;
        }

        @Override
        public String getRequestURI() {
            return null;
        }

        @Override
        public StringBuffer getRequestURL() {
            return null;
        }

        @Override
        public String getServletPath() {
            return null;
        }

        @Override
        public HttpSession getSession(boolean b) {
            return null;
        }

        @Override
        public HttpSession getSession() {
            return null;
        }

        @Override
        public String changeSessionId() {
            return null;
        }

        @Override
        public boolean isRequestedSessionIdValid() {
            return false;
        }

        @Override
        public boolean isRequestedSessionIdFromCookie() {
            return false;
        }

        @Override
        public boolean isRequestedSessionIdFromURL() {
            return false;
        }

        @Override
        public boolean isRequestedSessionIdFromUrl() {
            return false;
        }

        @Override
        public boolean authenticate(HttpServletResponse httpServletResponse) throws IOException, ServletException {
            return false;
        }

        @Override
        public void login(String s, String s1) throws ServletException {

        }

        @Override
        public void logout() throws ServletException {

        }

        @Override
        public Collection<Part> getParts() throws IOException, ServletException {
            return null;
        }

        @Override
        public Part getPart(String s) throws IOException, ServletException {
            return null;
        }

        @Override
        public <T extends HttpUpgradeHandler> T upgrade(Class<T> aClass) throws IOException, ServletException {
            return null;
        }

        @Override
        public Object getAttribute(String s) {
            return null;
        }

        @Override
        public Enumeration<String> getAttributeNames() {
            return null;
        }

        @Override
        public String getCharacterEncoding() {
            return null;
        }

        @Override
        public void setCharacterEncoding(String s) throws UnsupportedEncodingException {

        }

        @Override
        public int getContentLength() {
            return 0;
        }

        @Override
        public long getContentLengthLong() {
            return 0;
        }

        @Override
        public String getContentType() {
            return null;
        }

        @Override
        public ServletInputStream getInputStream() throws IOException {
            return null;
        }

        @Override
        public String getParameter(String s) {
            return null;
        }

        @Override
        public Enumeration<String> getParameterNames() {
            return null;
        }

        @Override
        public String[] getParameterValues(String s) {
            return new String[0];
        }

        @Override
        public Map<String, String[]> getParameterMap() {
            return null;
        }

        @Override
        public String getProtocol() {
            return null;
        }

        @Override
        public String getScheme() {
            return null;
        }

        @Override
        public String getServerName() {
            return null;
        }

        @Override
        public int getServerPort() {
            return 0;
        }

        @Override
        public BufferedReader getReader() throws IOException {
            return null;
        }

        @Override
        public String getRemoteAddr() {
            return null;
        }

        @Override
        public String getRemoteHost() {
            return null;
        }

        @Override
        public void setAttribute(String s, Object o) {

        }

        @Override
        public void removeAttribute(String s) {

        }

        @Override
        public Locale getLocale() {
            return null;
        }

        @Override
        public Enumeration<Locale> getLocales() {
            return null;
        }

        @Override
        public boolean isSecure() {
            return false;
        }

        @Override
        public RequestDispatcher getRequestDispatcher(String s) {
            return null;
        }

        @Override
        public String getRealPath(String s) {
            return null;
        }

        @Override
        public int getRemotePort() {
            return 0;
        }

        @Override
        public String getLocalName() {
            return null;
        }

        @Override
        public String getLocalAddr() {
            return null;
        }

        @Override
        public int getLocalPort() {
            return 0;
        }

        @Override
        public ServletContext getServletContext() {
            return null;
        }

        @Override
        public AsyncContext startAsync() throws IllegalStateException {
            return null;
        }

        @Override
        public AsyncContext startAsync(ServletRequest servletRequest, ServletResponse servletResponse) throws IllegalStateException {
            return null;
        }

        @Override
        public boolean isAsyncStarted() {
            return false;
        }

        @Override
        public boolean isAsyncSupported() {
            return false;
        }

        @Override
        public AsyncContext getAsyncContext() {
            return null;
        }

        @Override
        public DispatcherType getDispatcherType() {
            return null;
        }
    };
    private HttpServletResponse response = new HttpServletResponse() {
        @Override
        public void addCookie(Cookie cookie) {

        }

        @Override
        public boolean containsHeader(String s) {
            return false;
        }

        @Override
        public String encodeURL(String s) {
            return null;
        }

        @Override
        public String encodeRedirectURL(String s) {
            return null;
        }

        @Override
        public String encodeUrl(String s) {
            return null;
        }

        @Override
        public String encodeRedirectUrl(String s) {
            return null;
        }

        @Override
        public void sendError(int i, String s) throws IOException {

        }

        @Override
        public void sendError(int i) throws IOException {

        }

        @Override
        public void sendRedirect(String s) throws IOException {

        }

        @Override
        public void setDateHeader(String s, long l) {

        }

        @Override
        public void addDateHeader(String s, long l) {

        }

        @Override
        public void setHeader(String s, String s1) {

        }

        @Override
        public void addHeader(String s, String s1) {

        }

        @Override
        public void setIntHeader(String s, int i) {

        }

        @Override
        public void addIntHeader(String s, int i) {

        }

        @Override
        public void setStatus(int i) {

        }

        @Override
        public void setStatus(int i, String s) {

        }

        @Override
        public int getStatus() {
            return 0;
        }

        @Override
        public String getHeader(String s) {
            return null;
        }

        @Override
        public Collection<String> getHeaders(String s) {
            return null;
        }

        @Override
        public Collection<String> getHeaderNames() {
            return null;
        }

        @Override
        public String getCharacterEncoding() {
            return null;
        }

        @Override
        public String getContentType() {
            return null;
        }

        @Override
        public ServletOutputStream getOutputStream() throws IOException {
            return null;
        }

        @Override
        public PrintWriter getWriter() throws IOException {
            return null;
        }

        @Override
        public void setCharacterEncoding(String s) {

        }

        @Override
        public void setContentLength(int i) {

        }

        @Override
        public void setContentLengthLong(long l) {

        }

        @Override
        public void setContentType(String s) {

        }

        @Override
        public void setBufferSize(int i) {

        }

        @Override
        public int getBufferSize() {
            return 0;
        }

        @Override
        public void flushBuffer() throws IOException {

        }

        @Override
        public void resetBuffer() {

        }

        @Override
        public boolean isCommitted() {
            return false;
        }

        @Override
        public void reset() {

        }

        @Override
        public void setLocale(Locale locale) {

        }

        @Override
        public Locale getLocale() {
            return null;
        }
    };

    @Test
    public void testGetImageCode() {
        OutputStream os = System.out;
        Map<String, Object> returnMap = verifyCodeServiceImpl.getImageCode(60, 20, os, request, response, headers);
        Assert.assertNotNull(returnMap);
        Assert.assertNotNull(returnMap.get("strEnsure"));
    }

    @Test
    public void testVerifyCode() {
        boolean result = verifyCodeServiceImpl.verifyCode(request, response, "XYZ5", headers);
        Assert.assertFalse(result);
    }

}


// Node: testGetImageCode
package rebook;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;
import org.springframework.cloud.client.loadbalancer.LoadBalanced;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.EnableAspectJAutoProxy;
import org.springframework.integration.annotation.IntegrationComponentScan;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.web.client.RestTemplate;
import springfox.documentation.swagger2.annotations.EnableSwagger2;

/**
 * @author fdse
 */
@SpringBootApplication
@EnableAspectJAutoProxy(proxyTargetClass = true)
@EnableAsync
@IntegrationComponentScan
@EnableSwagger2
@EnableDiscoveryClient
public class RebookApplication {

    public static void main(String[] args) {
        SpringApplication.run(RebookApplication.class, args);
    }

    @LoadBalanced
    @Bean
    public RestTemplate restTemplate(RestTemplateBuilder builder) {
        return builder.build();
    }
}


package rebook.controller;

import com.alibaba.fastjson.JSONObject;
import edu.fudan.common.util.Response;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.springframework.http.*;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.request.MockMvcRequestBuilders;
import org.springframework.test.web.servlet.result.MockMvcResultMatchers;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import rebook.entity.RebookInfo;
import rebook.service.RebookService;

@RunWith(JUnit4.class)
public class RebookControllerTest {

    @InjectMocks
    private RebookController rebookController;

    @Mock
    private RebookService service;
    private MockMvc mockMvc;
    private Response response = new Response();

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
        mockMvc = MockMvcBuilders.standaloneSetup(rebookController).build();
    }

    @Test
    public void testHome() throws Exception {
        mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/rebookservice/welcome"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andExpect(MockMvcResultMatchers.content().string("Welcome to [ Rebook Service ] !"));
    }

    @Test
    public void testPayDifference() throws Exception {
        RebookInfo info = new RebookInfo();
        Mockito.when(service.payDifference(Mockito.any(RebookInfo.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(info);
        String result = mockMvc.perform(MockMvcRequestBuilders.post("/api/v1/rebookservice/rebook/difference").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testRebook() throws Exception {
        RebookInfo info = new RebookInfo();
        Mockito.when(service.rebook(Mockito.any(RebookInfo.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(info);
        String result = mockMvc.perform(MockMvcRequestBuilders.post("/api/v1/rebookservice/rebook").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

}


package rebook.service;

import edu.fudan.common.entity.Seat;
import edu.fudan.common.entity.Ticket;
import edu.fudan.common.entity.TripAllDetail;
import edu.fudan.common.entity.TripResponse;
import edu.fudan.common.util.Response;
import edu.fudan.common.util.StringUtils;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.*;
import org.springframework.web.client.RestTemplate;
import edu.fudan.common.entity.*;
import rebook.entity.RebookInfo;

import java.util.Date;

@RunWith(JUnit4.class)
public class RebookServiceImplTest {

    @InjectMocks
    private RebookServiceImpl rebookServiceImpl;

    @Mock
    private RestTemplate restTemplate;

    private HttpHeaders headers = new HttpHeaders();

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
    }

    @Test
    public void testRebook() {
        RebookInfo info = new RebookInfo();
        info.setOldTripId("G");
        info.setSeatType(2);

        //response for getOrderByRebookInfo()
        Order order = new Order();
        order.setStatus(1);
        order.setFrom("from_station");
        order.setTo("to_station");
        order.setPrice("1.0");
        String date = StringUtils.Date2String(new Date());
        order.setTravelDate(date);
        order.setTravelTime(date);
        Response<Order> response = new Response<>(1, null, order);
        ResponseEntity<Response<Order>> re = new ResponseEntity<>(response, HttpStatus.OK);

        //response for getTripAllDetailInformation()
        TripAllDetail tripAllDetail = new TripAllDetail();
        TripResponse tripResponse = new TripResponse();
        tripResponse.setConfortClass(1);
        tripResponse.setPriceForConfortClass("2.0");
        tripAllDetail.setTripResponse(tripResponse);
        Response<TripAllDetail> response2 = new Response<>(1, null, tripAllDetail);
        ResponseEntity<Response<TripAllDetail>> re2 = new ResponseEntity<>(response2, HttpStatus.OK);

        Mockito.when(restTemplate.exchange(
                Mockito.anyString(),
                Mockito.any(HttpMethod.class),
                Mockito.any(HttpEntity.class),
                Mockito.any(ParameterizedTypeReference.class)))
                .thenReturn(re).thenReturn(re2);

        //mock queryForStationName()
        Response<String> response3 = new Response(null, null, "");
        ResponseEntity<Response<String>> re3 = new ResponseEntity<>(response3, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                Mockito.anyString(),
                Mockito.any(HttpMethod.class),
                Mockito.any(HttpEntity.class),
                Mockito.any(Class.class)))
                .thenReturn(re3);

        Response result = rebookServiceImpl.rebook(info, headers);
        Assert.assertEquals("Please pay the different money!", result.getMsg());
    }

    @Test
    public void testPayDifference() {
        RebookInfo info = new RebookInfo();
        info.setTripId("G");
        info.setOldTripId("G");
        info.setLoginId("login_id");
        info.setDate("");
        info.setSeatType(0);

        //mock getOrderByRebookInfo() and getTripAllDetailInformation()
        Order order = new Order();
        order.setFrom("from_station");
        order.setTo("to_station");
        order.setPrice("0");
        Response<Order> response = new Response<>(1, null, order);
        ResponseEntity<Response<Order>> re = new ResponseEntity<>(response, HttpStatus.OK);

        TripAllDetail tripAllDetail = new TripAllDetail();
        Response<TripAllDetail> response2 = new Response<>(0, null, tripAllDetail);
        ResponseEntity<Response<TripAllDetail>> re2 = new ResponseEntity<>(response2, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                Mockito.anyString(),
                Mockito.any(HttpMethod.class),
                Mockito.any(HttpEntity.class),
                Mockito.any(ParameterizedTypeReference.class)))
                .thenReturn(re).thenReturn(re2);

        //mock queryForStationName() and updateOrder()
        Response response3 = new Response<>(0, null, "");
        ResponseEntity<Response> re3 = new ResponseEntity<>(response3, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                Mockito.anyString(),
                Mockito.any(HttpMethod.class),
                Mockito.any(HttpEntity.class),
                Mockito.any(Class.class)))
                .thenReturn(re3);
        Response result = rebookServiceImpl.payDifference(info, headers);
        Assert.assertEquals(new Response<>(0, "Can't pay the difference,please try again", null), result);
    }

    @Test
    public void testDipatchSeat() {
        Seat seatRequest = new Seat(StringUtils.Date2String(new Date()), "G1234", "start_station", "dest_station", 2, 100, null);
        HttpEntity requestEntityTicket = new HttpEntity<>(seatRequest, headers);
        Response<Ticket> response = new Response<>();
        ResponseEntity<Response<Ticket>> reTicket = new ResponseEntity<>(response, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                "http://ts-seat-service:18898/api/v1/seatservice/seats",
                HttpMethod.POST,
                requestEntityTicket,
                new ParameterizedTypeReference<Response<Ticket>>() {
                })).thenReturn(reTicket);
        Ticket result = rebookServiceImpl.dipatchSeat(StringUtils.Date2String(new Date()), "G1234", "start_station", "dest_station", 2, 100, null,headers);
        Assert.assertNull(result);
    }

}


package cancel;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;
import org.springframework.cloud.client.loadbalancer.LoadBalanced;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.EnableAspectJAutoProxy;
import org.springframework.integration.annotation.IntegrationComponentScan;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.web.client.RestTemplate;
import springfox.documentation.swagger2.annotations.EnableSwagger2;

/**
 * @author fdse
 */
@SpringBootApplication
@EnableAspectJAutoProxy(proxyTargetClass = true)
@EnableAsync
@IntegrationComponentScan
@EnableSwagger2
@EnableDiscoveryClient
public class CancelApplication {

    public static void main(String[] args) {
        SpringApplication.run(CancelApplication.class, args);
    }

    @LoadBalanced
    @Bean
    public RestTemplate restTemplate(RestTemplateBuilder builder) {
        return builder.build();
    }
}


package cancel.controller;

import cancel.service.CancelService;
import com.alibaba.fastjson.JSONObject;
import edu.fudan.common.util.Response;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.request.MockMvcRequestBuilders;
import org.springframework.test.web.servlet.result.MockMvcResultMatchers;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

@RunWith(JUnit4.class)
public class CancelControllerTest {

    @InjectMocks
    private CancelController cancelController;

    @Mock
    private CancelService cancelService;
    private MockMvc mockMvc;
    private Response response = new Response();

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
        mockMvc = MockMvcBuilders.standaloneSetup(cancelController).build();
    }

    @Test
    public void testHome() throws Exception {
        mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/cancelservice/welcome"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andExpect(MockMvcResultMatchers.content().string("Welcome to [ Cancel Service ] !"));
    }

    @Test
    public void testCalculate() throws Exception {
        Mockito.when(cancelService.calculateRefund(Mockito.anyString(), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/cancelservice/cancel/refound/order_id"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testCancelTicket() throws Exception {
        Mockito.when(cancelService.cancelOrder(Mockito.anyString(), Mockito.anyString(), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/cancelservice/cancel/order_id/login_id"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

}


// Node: testCalculate
// Node: testCancelTicket
package cancel.service;

import edu.fudan.common.entity.NotifyInfo;
import edu.fudan.common.entity.Order;
import edu.fudan.common.entity.User;
import edu.fudan.common.util.Response;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.*;
import org.springframework.web.client.RestTemplate;

@RunWith(JUnit4.class)
public class CancelServiceImplTest {

    @InjectMocks
    private CancelServiceImpl cancelServiceImpl;

    @Mock
    private RestTemplate restTemplate;

    private HttpHeaders headers = new HttpHeaders();
    private HttpEntity requestEntity = new HttpEntity(headers);

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
    }

    @Test
    public void testCancelOrder1() {
        //mock getOrderByIdFromOrder()
        Order order = new Order();
        order.setStatus(6);
        Response<Order> response = new Response<>(1, null, order);
        ResponseEntity<Response<Order>> re = new ResponseEntity<>(response, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                "http://ts-order-service:12031/api/v1/orderservice/order/" + "order_id",
                HttpMethod.GET,
                requestEntity,
                new ParameterizedTypeReference<Response<Order>>() {
                })).thenReturn(re);
        Response result = cancelServiceImpl.cancelOrder("order_id", "login_id", headers);
        Assert.assertEquals(new Response<>(0, "Order Status Cancel Not Permitted", null), result);
    }

    @Test
    public void testCancelOrder2() {
        //mock getOrderByIdFromOrder()
        Response<Order> response = new Response<>(0, null, null);
        ResponseEntity<Response<Order>> re = new ResponseEntity<>(response, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                "http://ts-order-service:12031/api/v1/orderservice/order/" + "order_id",
                HttpMethod.GET,
                requestEntity,
                new ParameterizedTypeReference<Response<Order>>() {
                })).thenReturn(re);
        //mock getOrderByIdFromOrderOther()
        Order order = new Order();
        order.setStatus(6);
        Response<Order> response2 = new Response<>(1, null, order);
        ResponseEntity<Response<Order>> re2 = new ResponseEntity<>(response2, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                "http://ts-order-other-service:12032/api/v1/orderOtherService/orderOther/" + "order_id",
                HttpMethod.GET,
                requestEntity,
                new ParameterizedTypeReference<Response<Order>>() {
                })).thenReturn(re2);
        Response result = cancelServiceImpl.cancelOrder("order_id", "login_id", headers);
        Assert.assertEquals(new Response<>(0, "Order Status Cancel Not Permitted", null), result);
    }

    @Test
    public void testSendEmail() {
        NotifyInfo notifyInfo = new NotifyInfo();
        HttpEntity requestEntity2 = new HttpEntity(notifyInfo, headers);
        ResponseEntity<Boolean> re = new ResponseEntity<>(true, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                "http://ts-notification-service:17853/api/v1/notifyservice/notification/order_cancel_success",
                HttpMethod.POST,
                requestEntity2,
                Boolean.class)).thenReturn(re);
        Boolean result = cancelServiceImpl.sendEmail(notifyInfo, headers);
        Assert.assertTrue(result);
    }

    @Test
    public void testCalculateRefund1() {
        //mock getOrderByIdFromOrder()
        Order order = new Order();
        order.setStatus(6);
        Response<Order> response = new Response<>(1, null, order);
        ResponseEntity<Response<Order>> re = new ResponseEntity<>(response, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                "http://ts-order-service:12031/api/v1/orderservice/order/" + "order_id",
                HttpMethod.GET,
                requestEntity,
                new ParameterizedTypeReference<Response<Order>>() {
                })).thenReturn(re);
        Response result = cancelServiceImpl.calculateRefund("order_id", headers);
        Assert.assertEquals(new Response<>(0, "Order Status Cancel Not Permitted, Refound error", null), result);
    }

    @Test
    public void testCalculateRefund2() {
        //mock getOrderByIdFromOrder()
        Response<Order> response = new Response<>(0, null, null);
        ResponseEntity<Response<Order>> re = new ResponseEntity<>(response, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                "http://ts-order-service:12031/api/v1/orderservice/order/" + "order_id",
                HttpMethod.GET,
                requestEntity,
                new ParameterizedTypeReference<Response<Order>>() {
                })).thenReturn(re);
        //mock getOrderByIdFromOrderOther()
        Order order = new Order();
        order.setStatus(6);
        Response<Order> response2 = new Response<>(1, null, order);
        ResponseEntity<Response<Order>> re2 = new ResponseEntity<>(response2, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                "http://ts-order-other-service:12032/api/v1/orderOtherService/orderOther/" + "order_id",
                HttpMethod.GET,
                requestEntity,
                new ParameterizedTypeReference<Response<Order>>() {
                })).thenReturn(re2);
        Response result = cancelServiceImpl.calculateRefund("order_id", headers);
        Assert.assertEquals(new Response<>(0, "Order Status Cancel Not Permitted", null), result);
    }

    @Test
    public void testDrawbackMoney() {
        Response response = new Response<>(1, null, null);
        ResponseEntity<Response> re = new ResponseEntity<>(response, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                "http://ts-inside-payment-service:18673/api/v1/inside_pay_service/inside_payment/drawback/" + "userId" + "/" + "money",
                HttpMethod.GET,
                requestEntity,
                Response.class)).thenReturn(re);
        Boolean result = cancelServiceImpl.drawbackMoney("money", "userId", headers);
        Assert.assertTrue(result);
    }

    @Test
    public void testGetAccount() {
        Response<User> response = new Response<>();
        ResponseEntity<Response<User>> re = new ResponseEntity<>(response, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                "http://ts-user-service:12342/api/v1/userservice/users/id/" + "orderId",
                HttpMethod.GET,
                requestEntity,
                new ParameterizedTypeReference<Response<User>>() {
                })).thenReturn(re);
        Response<User> result = cancelServiceImpl.getAccount("orderId", headers);
        Assert.assertEquals(new Response<User>(null, null, null), result);
    }

}


package adminbasic;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;
import org.springframework.cloud.client.loadbalancer.LoadBalanced;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.EnableAspectJAutoProxy;
import org.springframework.integration.annotation.IntegrationComponentScan;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.web.client.RestTemplate;
import springfox.documentation.swagger2.annotations.EnableSwagger2;

/**
 * @author fdse
 */
@SpringBootApplication
@EnableAspectJAutoProxy(proxyTargetClass = true)
@EnableAsync
@IntegrationComponentScan
@EnableSwagger2
@EnableDiscoveryClient
public class AdminBasicInfoApplication {

    public static void main(String[] args) {
        SpringApplication.run(AdminBasicInfoApplication.class, args);
    }

    @LoadBalanced
    @Bean
    public RestTemplate restTemplate(RestTemplateBuilder builder) {
        return builder.build();
    }
}


package adminbasic.controller;

import adminbasic.entity.*;
import adminbasic.service.AdminBasicInfoService;
import com.alibaba.fastjson.JSONObject;
import edu.fudan.common.entity.Config;
import edu.fudan.common.entity.Contacts;
import edu.fudan.common.entity.Station;
import edu.fudan.common.entity.TrainType;
import edu.fudan.common.util.Response;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.springframework.http.*;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.request.MockMvcRequestBuilders;
import org.springframework.test.web.servlet.result.MockMvcResultMatchers;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

@RunWith(JUnit4.class)
public class AdminBasicInfoControllerTest {

    @InjectMocks
    private AdminBasicInfoController adminBasicInfoController;

    @Mock
    private AdminBasicInfoService adminBasicInfoService;
    private MockMvc mockMvc;
    private Response response = new Response();

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
        mockMvc = MockMvcBuilders.standaloneSetup(adminBasicInfoController).build();
    }

    @Test
    public void testHome() throws Exception {
        mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/adminbasicservice/welcome"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andExpect(MockMvcResultMatchers.content().string("Welcome to [ AdminBasicInfo Service ] !"));
    }

    @Test
    public void testGetAllContacts() throws Exception {
        Mockito.when(adminBasicInfoService.getAllContacts(Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/adminbasicservice/adminbasic/contacts"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testDeleteContacts() throws Exception {
        Mockito.when(adminBasicInfoService.deleteContact(Mockito.anyString(), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.delete("/api/v1/adminbasicservice/adminbasic/contacts/contactsId"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testModifyContacts() throws Exception {
        Contacts mci = new Contacts();
        Mockito.when(adminBasicInfoService.modifyContact(Mockito.any(Contacts.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(mci);
        String result = mockMvc.perform(MockMvcRequestBuilders.put("/api/v1/adminbasicservice/adminbasic/contacts").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testAddContacts() throws Exception {
        Contacts c = new Contacts();
        Mockito.when(adminBasicInfoService.addContact(Mockito.any(Contacts.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(c);
        String result = mockMvc.perform(MockMvcRequestBuilders.post("/api/v1/adminbasicservice/adminbasic/contacts").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testGetAllStations() throws Exception {
        Mockito.when(adminBasicInfoService.getAllStations(Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/adminbasicservice/adminbasic/stations"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testDeleteStation() throws Exception {
        Station s = new Station();
        Mockito.when(adminBasicInfoService.deleteStation(Mockito.anyString(), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(s);
        String result = mockMvc.perform(MockMvcRequestBuilders.delete("/api/v1/adminbasicservice/adminbasic/stations").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testModifyStation() throws Exception {
        Station s = new Station();
        Mockito.when(adminBasicInfoService.modifyStation(Mockito.any(Station.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(s);
        String result = mockMvc.perform(MockMvcRequestBuilders.put("/api/v1/adminbasicservice/adminbasic/stations").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testAddStation() throws Exception {
        Station s = new Station();
        Mockito.when(adminBasicInfoService.addStation(Mockito.any(Station.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(s);
        String result = mockMvc.perform(MockMvcRequestBuilders.post("/api/v1/adminbasicservice/adminbasic/stations").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testGetAllTrains() throws Exception {
        Mockito.when(adminBasicInfoService.getAllTrains(Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/adminbasicservice/adminbasic/trains"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testDeleteTrain() throws Exception {
        Mockito.when(adminBasicInfoService.deleteTrain(Mockito.anyString(), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.delete("/api/v1/adminbasicservice/adminbasic/trains/id"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testModifyTrain() throws Exception {
        TrainType t = new TrainType();
        Mockito.when(adminBasicInfoService.modifyTrain(Mockito.any(TrainType.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(t);
        String result = mockMvc.perform(MockMvcRequestBuilders.put("/api/v1/adminbasicservice/adminbasic/trains").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testAddTrain() throws Exception {
        TrainType t = new TrainType();
        Mockito.when(adminBasicInfoService.addTrain(Mockito.any(TrainType.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(t);
        String result = mockMvc.perform(MockMvcRequestBuilders.post("/api/v1/adminbasicservice/adminbasic/trains").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testGetAllConfigs() throws Exception {
        Mockito.when(adminBasicInfoService.getAllConfigs(Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/adminbasicservice/adminbasic/configs"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testDeleteConfig() throws Exception {
        Mockito.when(adminBasicInfoService.deleteConfig(Mockito.anyString(), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.delete("/api/v1/adminbasicservice/adminbasic/configs/name"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testModifyConfig() throws Exception {
        Config c = new Config();
        Mockito.when(adminBasicInfoService.modifyConfig(Mockito.any(Config.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(c);
        String result = mockMvc.perform(MockMvcRequestBuilders.put("/api/v1/adminbasicservice/adminbasic/configs").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testAddConfig() throws Exception {
        Config c = new Config();
        Mockito.when(adminBasicInfoService.addConfig(Mockito.any(Config.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(c);
        String result = mockMvc.perform(MockMvcRequestBuilders.post("/api/v1/adminbasicservice/adminbasic/configs").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testGetAllPrices() throws Exception {
        Mockito.when(adminBasicInfoService.getAllPrices(Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/adminbasicservice/adminbasic/prices"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testDeletePrice() throws Exception {
        PriceInfo pi = new PriceInfo();
        Mockito.when(adminBasicInfoService.deletePrice(Mockito.anyString(), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(pi);
        String result = mockMvc.perform(MockMvcRequestBuilders.delete("/api/v1/adminbasicservice/adminbasic/prices").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testModifyPrice() throws Exception {
        PriceInfo pi = new PriceInfo();
        Mockito.when(adminBasicInfoService.modifyPrice(Mockito.any(PriceInfo.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(pi);
        String result = mockMvc.perform(MockMvcRequestBuilders.put("/api/v1/adminbasicservice/adminbasic/prices").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testAddPrice() throws Exception {
        PriceInfo pi = new PriceInfo();
        Mockito.when(adminBasicInfoService.addPrice(Mockito.any(PriceInfo.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(pi);
        String result = mockMvc.perform(MockMvcRequestBuilders.post("/api/v1/adminbasicservice/adminbasic/prices").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }
}


// Node: testGetAllContacts
// Node: testDeleteContacts
// Node: testModifyContacts
// Node: testAddContacts
// Node: testGetAllStations
// Node: testDeleteStation
// Node: testModifyStation
// Node: testAddStation
// Node: testGetAllTrains
// Node: testModifyTrain
// Node: testAddTrain
// Node: testGetAllConfigs
// Node: testDeleteConfig
// Node: testModifyConfig
// Node: testAddConfig
// Node: testGetAllPrices
// Node: testDeletePrice
// Node: testModifyPrice
// Node: testAddPrice
package adminbasic.service;

import adminbasic.entity.*;
import edu.fudan.common.entity.Config;
import edu.fudan.common.entity.Contacts;
import edu.fudan.common.entity.Station;
import edu.fudan.common.entity.TrainType;
import edu.fudan.common.util.Response;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;
import org.mockito.*;
import org.springframework.http.*;
import org.springframework.web.client.RestTemplate;

@RunWith(JUnit4.class)
public class AdminBasicInfoServiceImplTest {

    @InjectMocks
    private AdminBasicInfoServiceImpl adminBasicInfoService;

    @Mock
    private RestTemplate restTemplate;

    private HttpHeaders headers = new HttpHeaders();
    private HttpEntity requestEntity = new HttpEntity(headers);
    private Response response = new Response();
    private ResponseEntity<Response> re = new ResponseEntity<>(response, HttpStatus.OK);

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
    }

    @Test
    public void testGetAllContacts() {
        Mockito.when(restTemplate.exchange(
                "http://ts-contacts-service:12347/api/v1/contactservice/contacts",
                HttpMethod.GET,
                requestEntity,
                Response.class)).thenReturn(re);
        response = adminBasicInfoService.getAllContacts(headers);
        Assert.assertEquals(new Response<>(null, null, null), response);
    }

    @Test
    public void testDeleteContact() {
        Mockito.when(restTemplate.exchange(
                "http://ts-contacts-service:12347/api/v1/contactservice/contacts/" + "contactsId",
                HttpMethod.DELETE,
                requestEntity,
                Response.class)).thenReturn(re);
        response = adminBasicInfoService.deleteContact("contactsId", headers);
        Assert.assertEquals(new Response<>(null, null, null), response);
    }

    @Test
    public void testModifyContact() {
        Contacts mci = new Contacts();
        HttpEntity<Contacts> requestEntity = new HttpEntity<>(mci, headers);
        Mockito.when(restTemplate.exchange(
                "http://ts-contacts-service:12347/api/v1/contactservice/contacts",
                HttpMethod.PUT,
                requestEntity,
                Response.class)).thenReturn(re);
        response = adminBasicInfoService.modifyContact(mci, headers);
        Assert.assertEquals(new Response<>(null, null, null), response);
    }

    @Test
    public void testAddContact() {
        Contacts c = new Contacts();
        HttpEntity<Contacts> requestEntity = new HttpEntity<>(c, headers);
        Mockito.when(restTemplate.exchange(
                "http://ts-contacts-service:12347/api/v1/contactservice/contacts/admin",
                HttpMethod.POST,
                requestEntity,
                Response.class)).thenReturn(re);
        response = adminBasicInfoService.addContact(c, headers);
        Assert.assertEquals(new Response<>(null, null, null), response);
    }

    @Test
    public void testGetAllStations() {
        Mockito.when(restTemplate.exchange(
                "http://ts-station-service:12345/api/v1/stationservice/stations",
                HttpMethod.GET,
                requestEntity,
                Response.class)).thenReturn(re);
        response = adminBasicInfoService.getAllStations(headers);
        Assert.assertEquals(new Response<>(null, null, null), response);
    }

    @Test
    public void testAddStation() {
        Station s = new Station();
        HttpEntity<Station> requestEntity = new HttpEntity<>(s, headers);
        Mockito.when(restTemplate.exchange(
                "http://ts-station-service:12345/api/v1/stationservice/stations",
                HttpMethod.POST,
                requestEntity,
                Response.class)).thenReturn(re);
        response = adminBasicInfoService.addStation(s, headers);
        Assert.assertEquals(new Response<>(null, null, null), response);
    }

    @Test
    public void testDeleteStation() {
        Station s = new Station();
        HttpEntity<Station> requestEntity = new HttpEntity<>(s, headers);
        Mockito.when(restTemplate.exchange(
                "http://ts-station-service:12345/api/v1/stationservice/stations",
                HttpMethod.DELETE,
                requestEntity,
                Response.class)).thenReturn(re);
        response = adminBasicInfoService.deleteStation(s.getId(), headers);
        Assert.assertEquals(new Response<>(null, null, null), response);
    }

    @Test
    public void testModifyStation() {
        Station s = new Station();
        HttpEntity<Station> requestEntity = new HttpEntity<>(s, headers);
        Mockito.when(restTemplate.exchange(
                "http://ts-station-service:12345/api/v1/stationservice/stations",
                HttpMethod.PUT,
                requestEntity,
                Response.class)).thenReturn(re);
        response = adminBasicInfoService.modifyStation(s, headers);
        Assert.assertEquals(new Response<>(null, null, null), response);
    }

    @Test
    public void testGetAllTrains() {
        Mockito.when(restTemplate.exchange(
                "http://ts-train-service:14567/api/v1/trainservice/trains",
                HttpMethod.GET,
                requestEntity,
                Response.class)).thenReturn(re);
        response = adminBasicInfoService.getAllTrains(headers);
        Assert.assertEquals(new Response<>(null, null, null), response);
    }

    @Test
    public void testAddTrain() {
        TrainType t = new TrainType();
        HttpEntity<TrainType> requestEntity = new HttpEntity<>(t, headers);
        Mockito.when(restTemplate.exchange(
                "http://ts-train-service:14567/api/v1/trainservice/trains",
                HttpMethod.POST,
                requestEntity,
                Response.class)).thenReturn(re);
        response = adminBasicInfoService.addTrain(t, headers);
        Assert.assertEquals(new Response<>(null, null, null), response);
    }

    @Test
    public void testDeleteTrain() {
        Mockito.when(restTemplate.exchange(
                "http://ts-train-service:14567/api/v1/trainservice/trains/" + "id",
                HttpMethod.DELETE,
                requestEntity,
                Response.class)).thenReturn(re);
        response = adminBasicInfoService.deleteTrain("id", headers);
        Assert.assertEquals(new Response<>(null, null, null), response);
    }

    @Test
    public void testModifyTrain() {
        TrainType t = new TrainType();
        HttpEntity<TrainType> requestEntity = new HttpEntity<>(t, headers);
        Mockito.when(restTemplate.exchange(
                "http://ts-train-service:14567/api/v1/trainservice/trains",
                HttpMethod.PUT,
                requestEntity,
                Response.class)).thenReturn(re);
        response = adminBasicInfoService.modifyTrain(t, headers);
        Assert.assertEquals(new Response<>(null, null, null), response);
    }

    @Test
    public void testGetAllConfigs() {
        Mockito.when(restTemplate.exchange(
                "http://ts-config-service:15679/api/v1/configservice/configs",
                HttpMethod.GET,
                requestEntity,
                Response.class)).thenReturn(re);
        response = adminBasicInfoService.getAllConfigs(headers);
        Assert.assertEquals(new Response<>(null, null, null), response);
    }

    @Test
    public void testAddConfig() {
        Config c = new Config();
        HttpEntity<Config> requestEntity = new HttpEntity<>(c, headers);
        Mockito.when(restTemplate.exchange(
                "http://ts-config-service:15679/api/v1/configservice/configs",
                HttpMethod.POST,
                requestEntity,
                Response.class)).thenReturn(re);
        response = adminBasicInfoService.addConfig(c, headers);
        Assert.assertEquals(new Response<>(null, null, null), response);
    }

    @Test
    public void testDeleteConfig() {
        Mockito.when(restTemplate.exchange(
                "http://ts-config-service:15679/api/v1/configservice/configs/" + "name",
                HttpMethod.DELETE,
                requestEntity,
                Response.class)).thenReturn(re);
        response = adminBasicInfoService.deleteConfig("name", headers);
        Assert.assertEquals(new Response<>(null, null, null), response);
    }

    @Test
    public void testModifyConfig() {
        Config c = new Config();
        HttpEntity<Config> requestEntity = new HttpEntity<>(c, headers);
        Mockito.when(restTemplate.exchange(
                "http://ts-config-service:15679/api/v1/configservice/configs",
                HttpMethod.PUT,
                requestEntity,
                Response.class)).thenReturn(re);
        response = adminBasicInfoService.modifyConfig(c, headers);
        Assert.assertEquals(new Response<>(null, null, null), response);
    }

    @Test
    public void testGetAllPrices() {
        Mockito.when(restTemplate.exchange(
                "http://ts-price-service:16579/api/v1/priceservice/prices",
                HttpMethod.GET,
                requestEntity,
                Response.class)).thenReturn(re);
        response = adminBasicInfoService.getAllPrices(headers);
        Assert.assertEquals(new Response<>(null, null, null), response);
    }

    @Test
    public void testAddPrice() {
        PriceInfo pi = new PriceInfo();
        HttpEntity<PriceInfo> requestEntity = new HttpEntity<>(pi, headers);
        Mockito.when(restTemplate.exchange(
                "http://ts-price-service:16579/api/v1/priceservice/prices",
                HttpMethod.POST,
                requestEntity,
                Response.class)).thenReturn(re);
        response = adminBasicInfoService.addPrice(pi, headers);
        Assert.assertEquals(new Response<>(null, null, null), response);
    }

    @Test
    public void testDeletePrice() {
        PriceInfo pi = new PriceInfo();
        HttpEntity<PriceInfo> requestEntity = new HttpEntity<>(pi, headers);
        Mockito.when(restTemplate.exchange(
                "http://ts-price-service:16579/api/v1/priceservice/prices",
                HttpMethod.DELETE,
                requestEntity,
                Response.class)).thenReturn(re);
        response = adminBasicInfoService.deletePrice(pi.getId(), headers);
        Assert.assertEquals(new Response<>(null, null, null), response);
    }

    @Test
    public void testModifyPrice() {
        PriceInfo pi = new PriceInfo();
        HttpEntity<PriceInfo> requestEntity = new HttpEntity<>(pi, headers);
        Mockito.when(restTemplate.exchange(
                "http://ts-price-service:16579/api/v1/priceservice/prices",
                HttpMethod.PUT,
                requestEntity,
                Response.class)).thenReturn(re);
        response = adminBasicInfoService.modifyPrice(pi, headers);
        Assert.assertEquals(new Response<>(null, null, null), response);
    }

}




package org.myproject.ms.monitoring;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collection;
import java.util.Collections;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ConcurrentLinkedQueue;

import org.springframework.util.Assert;
import org.springframework.util.StringUtils;

import com.fasterxml.jackson.annotation.JsonAutoDetect;
import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonInclude;


@JsonAutoDetect(fieldVisibility = JsonAutoDetect.Visibility.ANY)
@JsonInclude(JsonInclude.Include.NON_DEFAULT)
public class Item implements ItemContext {

	public static final String SAMPLED_NAME = "X-B3-Sampled";
	public static final String PROCESS_ID_NAME = "X-Process-Id";
	public static final String PARENT_ID_NAME = "X-B3-ParentSpanId";
	public static final String TRACE_ID_NAME = "X-B3-TraceId";
	public static final String SPAN_NAME_NAME = "X-Span-Name";
	public static final String SPAN_ID_NAME = "X-B3-SpanId";
	public static final String SPAN_EXPORT_NAME = "X-Span-Export";
	public static final String SPAN_FLAGS = "X-B3-Flags";
	public static final String SPAN_BAGGAGE_HEADER_PREFIX = "baggage";
	public static final Set<String> SPAN_HEADERS = new HashSet<>(
			Arrays.asList(SAMPLED_NAME, PROCESS_ID_NAME, PARENT_ID_NAME, TRACE_ID_NAME,
					SPAN_ID_NAME, SPAN_NAME_NAME, SPAN_EXPORT_NAME));

	public static final String SPAN_SAMPLED = "1";
	public static final String SPAN_NOT_SAMPLED = "0";

	public static final String SPAN_LOCAL_COMPONENT_TAG_NAME = "lc";
	public static final String SPAN_ERROR_TAG_NAME = "error";

	
	public static final String CLIENT_RECV = "cr";

	
	// For an outbound RPC call, it should log a "cs" annotation.
	// If possible, it should log a binary annotation of "sa", indicating the
	// destination address.
	public static final String CLIENT_SEND = "cs";

	
	// If an inbound RPC call, it should log a "sr" annotation.
	// If possible, it should log a binary annotation of "ca", indicating the
	// caller's address (ex X-Forwarded-For header)
	public static final String SERVER_RECV = "sr";

	
	public static final String SERVER_SEND = "ss";

	
	public static final String SPAN_PEER_SERVICE_TAG_NAME = "peer.service";

	
	public static final String INSTANCEID = "spring.instance_id";

	private final long begin;
	private long end = 0;
	private final String name;
	private final long traceIdHigh;
	private final long traceId;
	private List<Long> parents = new ArrayList<>();
	private final long spanId;
	private boolean remote = false;
	private boolean exportable = true;
	private final Map<String, String> tags;
	private final String processId;
	private final Collection<Log> logs;
	private final Item savedSpan;
	@JsonIgnore
	private final Map<String,String> baggage;

	// Null means we don't know the start tick, so fallback to time
	@JsonIgnore
	private final Long startNanos;
	private Long durationMicros; // serialized in json so micros precision isn't lost

	@SuppressWarnings("unused")
	private Item() {
		this(-1, -1, "dummy", 0, Collections.<Long>emptyList(), 0, false, false, null);
	}

	
	public Item(Item current, Item savedSpan) {
		this.begin = current.getBegin();
		this.end = current.getEnd();
		this.name = current.getName();
		this.traceIdHigh = current.getTraceIdHigh();
		this.traceId = current.getTraceId();
		this.parents = current.getParents();
		this.spanId = current.getSpanId();
		this.remote = current.isRemote();
		this.exportable = current.isExportable();
		this.processId = current.getProcessId();
		this.tags = current.tags;
		this.logs = current.logs;
		this.startNanos = current.startNanos;
		this.durationMicros = current.durationMicros;
		this.baggage = current.baggage;
		this.savedSpan = savedSpan;
	}

	
	@Deprecated
	public Item(long begin, long end, String name, long traceId, List<Long> parents,
			long spanId, boolean remote, boolean exportable, String processId) {
		this(begin, end, name, traceId, parents, spanId, remote, exportable, processId,
				null);
	}

	
	@Deprecated
	public Item(long begin, long end, String name, long traceId, List<Long> parents,
			long spanId, boolean remote, boolean exportable, String processId,
			Item savedSpan) {
		this(new SpanBuilder()
				.begin(begin)
				.end(end)
				.name(name)
				.traceId(traceId)
				.parents(parents)
				.spanId(spanId)
				.remote(remote)
				.exportable(exportable)
				.processId(processId)
				.savedSpan(savedSpan));
	}

	Item(SpanBuilder builder) {
		if (builder.begin > 0) { // conventionally, 0 indicates unset
			this.startNanos = null; // don't know the start tick
			this.begin = builder.begin;
		} else {
			this.startNanos = nanoTime();
			this.begin = System.currentTimeMillis();
		}
		if (builder.end > 0) {
			this.end = builder.end;
			this.durationMicros = (this.end - this.begin) * 1000;
		}
		this.name = builder.name != null ? builder.name : "";
		this.traceIdHigh = builder.traceIdHigh;
		this.traceId = builder.traceId;
		this.parents.addAll(builder.parents);
		this.spanId = builder.spanId;
		this.remote = builder.remote;
		this.exportable = builder.exportable;
		this.processId = builder.processId;
		this.savedSpan = builder.savedSpan;
		this.tags = new ConcurrentHashMap<>();
		this.tags.putAll(builder.tags);
		this.logs = new ConcurrentLinkedQueue<>();
		this.logs.addAll(builder.logs);
		this.baggage = new ConcurrentHashMap<>();
		this.baggage.putAll(builder.baggage);
	}

	public static SpanBuilder builder() {
		return new SpanBuilder();
	}

	
	public synchronized void stop() {
		if (this.durationMicros == null) {
			if (this.begin == 0) {
				throw new IllegalStateException(
						"Span for " + this.name + " has not been started");
			}
			if (this.end == 0) {
				this.end = System.currentTimeMillis();
			}
			if (this.startNanos != null) { // set a precise duration
				this.durationMicros = Math.max(1, (nanoTime() - this.startNanos) / 1000);
			} else {
				this.durationMicros = (this.end - this.begin) * 1000;
			}
		}
	}

	
	@Deprecated
	@JsonIgnore
	public synchronized long getAccumulatedMillis() {
		return getAccumulatedMicros() / 1000;
	}

	
	@JsonIgnore
	public synchronized long getAccumulatedMicros() {
		if (this.durationMicros != null) {
			return this.durationMicros;
		} else { // stop() hasn't yet been called
			if (this.begin == 0) {
				return 0;
			}
			if (this.startNanos != null) {
				return Math.max(1, (nanoTime() - this.startNanos) / 1000);
			} else  {
				return (System.currentTimeMillis() - this.begin) * 1000;
			}
		}
	}

	// Visible for testing
	@JsonIgnore
	long nanoTime() {
		return System.nanoTime();
	}

	
	@JsonIgnore
	public synchronized boolean isRunning() {
		return this.begin != 0 && this.durationMicros == null;
	}

	
	public void tag(String key, String value) {
		if (StringUtils.hasText(value)) {
			this.tags.put(key, value);
		}
	}

	
	public void logEvent(String event) {
		logEvent(System.currentTimeMillis(), event);
	}

	
	public void logEvent(long timestampMilliseconds, String event) {
		this.logs.add(new Log(timestampMilliseconds, event));
	}

	
	public Item setBaggageItem(String key, String value) {
		this.baggage.put(key, value);
		return this;
	}

	
	public String getBaggageItem(String key) {
		return this.baggage.get(key);
	}

	@Override
	public final Iterable<Map.Entry<String,String>> baggageItems() {
		return this.baggage.entrySet();
	}

	public final Map<String,String> getBaggage() {
		return Collections.unmodifiableMap(this.baggage);
	}

	
	public Map<String, String> tags() {
		return Collections.unmodifiableMap(new LinkedHashMap<>(this.tags));
	}

	
	public List<Log> logs() {
		return Collections.unmodifiableList(new ArrayList<>(this.logs));
	}

	
	@JsonIgnore
	public Item getSavedSpan() {
		return this.savedSpan;
	}

	public boolean hasSavedSpan() {
		return this.savedSpan != null;
	}

	
	public String getName() {
		return this.name;
	}

	
	public long getSpanId() {
		return this.spanId;
	}

	
	public long getTraceIdHigh() {
		return this.traceIdHigh;
	}

	
	public long getTraceId() {
		return this.traceId;
	}

	
	public String getProcessId() {
		return this.processId;
	}

	
	public List<Long> getParents() {
		return this.parents;
	}

	
	public boolean isRemote() {
		return this.remote;
	}

	
	public long getBegin() {
		return this.begin;
	}

	
	public long getEnd() {
		return this.end;
	}

	
	public boolean isExportable() {
		return this.exportable;
	}

	
	public String traceIdString() {
		if (this.traceIdHigh != 0) {
			char[] result = new char[32];
			writeHexLong(result, 0, this.traceIdHigh);
			writeHexLong(result, 16, this.traceId);
			return new String(result);
		}
		char[] result = new char[16];
		writeHexLong(result, 0, this.traceId);
		return new String(result);
	}

	
	public SpanBuilder toBuilder() {
		return builder().from(this);
	}

	
	public static String idToHex(long id) {
		char[] data = new char[16];
		writeHexLong(data, 0, id);
		return new String(data);
	}

	
	static void writeHexLong(char[] data, int pos, long v) {
		writeHexByte(data, pos + 0,  (byte) ((v >>> 56L) & 0xff));
		writeHexByte(data, pos + 2,  (byte) ((v >>> 48L) & 0xff));
		writeHexByte(data, pos + 4,  (byte) ((v >>> 40L) & 0xff));
		writeHexByte(data, pos + 6,  (byte) ((v >>> 32L) & 0xff));
		writeHexByte(data, pos + 8,  (byte) ((v >>> 24L) & 0xff));
		writeHexByte(data, pos + 10, (byte) ((v >>> 16L) & 0xff));
		writeHexByte(data, pos + 12, (byte) ((v >>> 8L) & 0xff));
		writeHexByte(data, pos + 14, (byte)  (v & 0xff));
	}

	static void writeHexByte(char[] data, int pos, byte b) {
		data[pos + 0] = HEX_DIGITS[(b >> 4) & 0xf];
		data[pos + 1] = HEX_DIGITS[b & 0xf];
	}

	static final char[] HEX_DIGITS =
			{'0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd', 'e', 'f'};

	
	public static long hexToId(String hexString) {
		Assert.hasText(hexString, "Can't convert empty hex string to long");
		int length = hexString.length();
		if (length < 1 || length > 32) throw new IllegalArgumentException("Malformed id: " + hexString);

		// trim off any high bits
		int beginIndex = length > 16 ? length - 16 : 0;

		return hexToId(hexString, beginIndex);
	}

	
	public static long hexToId(String lowerHex, int index) {
		Assert.hasText(lowerHex, "Can't convert empty hex string to long");
		long result = 0;
		for (int endIndex = Math.min(index + 16, lowerHex.length()); index < endIndex; index++) {
			char c = lowerHex.charAt(index);
			result <<= 4;
			if (c >= '0' && c <= '9') {
				result |= c - '0';
			} else if (c >= 'a' && c <= 'f') {
				result |= c - 'a' + 10;
			} else {
				throw new IllegalArgumentException("Malformed id: " + lowerHex);
			}
		}
		return result;
	}

	@Override
	public String toString() {
		return "[Trace: " + traceIdString() + ", Span: " + idToHex(this.spanId)
				+ ", Parent: " + getParentIdIfPresent() + ", exportable:" + this.exportable + "]";
	}

	private String getParentIdIfPresent() {
		return this.getParents().isEmpty() ? "null" : idToHex(this.getParents().get(0));
	}

	@Override
	public int hashCode() {
		int h = 1;
		h *= 1000003;
		h ^= (this.traceIdHigh >>> 32) ^ this.traceIdHigh;
		h *= 1000003;
		h ^= (this.traceId >>> 32) ^ this.traceId;
		h *= 1000003;
		h ^= (this.spanId >>> 32) ^ this.spanId;
		h *= 1000003;
		return h;
	}

	@Override
	public boolean equals(Object o) {
		if (o == this) {
			return true;
		}
		if (o instanceof Item) {
			Item that = (Item) o;
			return (this.traceIdHigh == that.traceIdHigh)
					&& (this.traceId == that.traceId)
					&& (this.spanId == that.spanId);
		}
		return false;
	}

	public static class SpanBuilder {
		private long begin;
		private long end;
		private String name;
		private long traceIdHigh;
		private long traceId;
		private ArrayList<Long> parents = new ArrayList<>();
		private long spanId;
		private boolean remote;
		private boolean exportable = true;
		private String processId;
		private Item savedSpan;
		private List<Log> logs = new ArrayList<>();
		private Map<String, String> tags = new LinkedHashMap<>();
		private Map<String, String> baggage = new LinkedHashMap<>();

		SpanBuilder() {
		}

		
		public Item.SpanBuilder begin(long begin) {
			this.begin = begin;
			return this;
		}

		public Item.SpanBuilder end(long end) {
			this.end = end;
			return this;
		}

		public Item.SpanBuilder name(String name) {
			this.name = name;
			return this;
		}

		public Item.SpanBuilder traceIdHigh(long traceIdHigh) {
			this.traceIdHigh = traceIdHigh;
			return this;
		}

		public Item.SpanBuilder traceId(long traceId) {
			this.traceId = traceId;
			return this;
		}

		public Item.SpanBuilder parent(Long parent) {
			this.parents.add(parent);
			return this;
		}

		public Item.SpanBuilder parents(Collection<Long> parents) {
			this.parents.clear();
			this.parents.addAll(parents);
			return this;
		}

		public Item.SpanBuilder log(Log log) {
			this.logs.add(log);
			return this;
		}

		public Item.SpanBuilder logs(Collection<Log> logs) {
			this.logs.clear();
			this.logs.addAll(logs);
			return this;
		}

		public Item.SpanBuilder tag(String tagKey, String tagValue) {
			this.tags.put(tagKey, tagValue);
			return this;
		}

		public Item.SpanBuilder tags(Map<String, String> tags) {
			this.tags.clear();
			this.tags.putAll(tags);
			return this;
		}

		public Item.SpanBuilder baggage(String baggageKey, String baggageValue) {
			this.baggage.put(baggageKey, baggageValue);
			return this;
		}

		public Item.SpanBuilder baggage(Map<String, String> baggage) {
			this.baggage.putAll(baggage);
			return this;
		}

		public Item.SpanBuilder spanId(long spanId) {
			this.spanId = spanId;
			return this;
		}

		public Item.SpanBuilder remote(boolean remote) {
			this.remote = remote;
			return this;
		}

		public Item.SpanBuilder exportable(boolean exportable) {
			this.exportable = exportable;
			return this;
		}

		public Item.SpanBuilder processId(String processId) {
			this.processId = processId;
			return this;
		}

		public Item.SpanBuilder savedSpan(Item savedSpan) {
			this.savedSpan = savedSpan;
			return this;
		}

		public Item.SpanBuilder from(Item span) {
			return begin(span.begin).end(span.end).name(span.name)
					.traceIdHigh(span.traceIdHigh).traceId(span.traceId)
					.parents(span.getParents()).logs(span.logs).tags(span.tags)
					.spanId(span.spanId).remote(span.remote).exportable(span.exportable)
					.processId(span.processId).savedSpan(span.savedSpan);
		}

		public Item build() {
			return new Item(this);
		}

		@Override
		public String toString() {
			return new Item(this).toString();
		}
	}
}


// Node: getBaggageItem


package org.myproject.ms.monitoring.instrument.web.client;

import java.lang.invoke.MethodHandles;
import java.net.URI;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;

import org.apache.commons.logging.Log;
import org.apache.commons.logging.LogFactory;
import org.myproject.ms.monitoring.Item;
import org.myproject.ms.monitoring.Chainer;
import org.myproject.ms.monitoring.util.ExceptionUtils;
import org.springframework.core.task.AsyncListenableTaskExecutor;
import org.springframework.http.HttpMethod;
import org.springframework.http.client.AsyncClientHttpRequestFactory;
import org.springframework.http.client.ClientHttpRequestFactory;
import org.springframework.util.concurrent.FailureCallback;
import org.springframework.util.concurrent.ListenableFuture;
import org.springframework.util.concurrent.ListenableFutureCallback;
import org.springframework.util.concurrent.SuccessCallback;
import org.springframework.web.client.AsyncRequestCallback;
import org.springframework.web.client.AsyncRestTemplate;
import org.springframework.web.client.ResponseExtractor;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;


public class TARTemp extends AsyncRestTemplate {

	private final Chainer tracer;

	public TARTemp(Chainer tracer) {
		super();
		this.tracer = tracer;
	}

	public TARTemp(AsyncListenableTaskExecutor taskExecutor, Chainer tracer) {
		super(taskExecutor);
		this.tracer = tracer;
	}

	public TARTemp(AsyncClientHttpRequestFactory asyncRequestFactory,
			Chainer tracer) {
		super(asyncRequestFactory);
		this.tracer = tracer;
	}

	public TARTemp(AsyncClientHttpRequestFactory asyncRequestFactory,
			ClientHttpRequestFactory syncRequestFactory, Chainer tracer) {
		super(asyncRequestFactory, syncRequestFactory);
		this.tracer = tracer;
	}

	public TARTemp(AsyncClientHttpRequestFactory requestFactory,
			RestTemplate restTemplate, Chainer tracer) {
		super(requestFactory, restTemplate);
		this.tracer = tracer;
	}

	@Override
	protected <T> ListenableFuture<T> doExecute(URI url, HttpMethod method,
			AsyncRequestCallback requestCallback, ResponseExtractor<T> responseExtractor)
			throws RestClientException {
		final ListenableFuture<T> future = super.doExecute(url, method, requestCallback, responseExtractor);
		final Item span = this.tracer.getCurrentSpan();
		future.addCallback(new TraceListenableFutureCallback<>(this.tracer, span));
		// potential race can happen here
		if (span != null && span.equals(this.tracer.getCurrentSpan())) {
			this.tracer.detach(span);
		}
		return new ListenableFuture<T>() {

			@Override public boolean cancel(boolean mayInterruptIfRunning) {
				return future.cancel(mayInterruptIfRunning);
			}

			@Override public boolean isCancelled() {
				return future.isCancelled();
			}

			@Override public boolean isDone() {
				return future.isDone();
			}

			@Override public T get() throws InterruptedException, ExecutionException {
				return future.get();
			}

			@Override public T get(long timeout, TimeUnit unit)
					throws InterruptedException, ExecutionException, TimeoutException {
				return future.get(timeout, unit);
			}

			@Override
			public void addCallback(ListenableFutureCallback<? super T> callback) {
				future.addCallback(new TraceListenableFutureCallbackWrapper<>(TARTemp.this.tracer, span, callback));
			}

			@Override public void addCallback(SuccessCallback<? super T> successCallback,
					FailureCallback failureCallback) {
				future.addCallback(
						new TraceSuccessCallback<>(TARTemp.this.tracer, span, successCallback),
						new TraceFailureCallback(TARTemp.this.tracer, span, failureCallback));
			}
		};
	}

	private static class TraceSuccessCallback<T> implements SuccessCallback<T> {

		private static final Log log = LogFactory.getLog(MethodHandles.lookup().lookupClass());

		private final Chainer tracer;
		private final Item parent;
		private final SuccessCallback<T> delegate;

		private TraceSuccessCallback(Chainer tracer, Item parent,
				SuccessCallback<T> delegate) {
			this.tracer = tracer;
			this.parent = parent;
			this.delegate = delegate;
		}

		@Override public void onSuccess(T result) {
			continueSpan();
			if (log.isDebugEnabled()) {
				log.debug("Calling on success of the delegate");
			}
			this.delegate.onSuccess(result);
			finish();
		}

		private void continueSpan() {
			this.tracer.continueSpan(this.parent);
		}

		private void finish() {
			this.tracer.detach(currentSpan());
		}

		private Item currentSpan() {
			return this.tracer.getCurrentSpan();
		}
	}

	private static class TraceFailureCallback implements FailureCallback {

		private static final Log log = LogFactory.getLog(MethodHandles.lookup().lookupClass());

		private final Chainer tracer;
		private final Item parent;
		private final FailureCallback delegate;

		private TraceFailureCallback(Chainer tracer, Item parent,
				FailureCallback delegate) {
			this.tracer = tracer;
			this.parent = parent;
			this.delegate = delegate;
		}

		@Override public void onFailure(Throwable ex) {
			continueSpan();
			if (log.isDebugEnabled()) {
				log.debug("Calling on failure of the delegate");
			}
			this.delegate.onFailure(ex);
			finish();
		}

		private void continueSpan() {
			this.tracer.continueSpan(this.parent);
		}

		private void finish() {
			this.tracer.detach(currentSpan());
		}

		private Item currentSpan() {
			return this.tracer.getCurrentSpan();
		}
	}

	private static class TraceListenableFutureCallbackWrapper<T> implements ListenableFutureCallback<T> {

		private final Chainer tracer;
		private final Item parent;
		private final ListenableFutureCallback<T> delegate;

		private TraceListenableFutureCallbackWrapper(Chainer tracer, Item parent,
				ListenableFutureCallback<T> delegate) {
			this.tracer = tracer;
			this.parent = parent;
			this.delegate = delegate;
		}

		@Override public void onFailure(Throwable ex) {
			new TraceFailureCallback(this.tracer, this.parent, this.delegate).onFailure(ex);
		}

		@Override public void onSuccess(T result) {
			new TraceSuccessCallback<>(this.tracer, this.parent, this.delegate).onSuccess(result);
		}
	}

	private static class TraceListenableFutureCallback<T> implements ListenableFutureCallback<T> {

		private static final Log log = LogFactory.getLog(MethodHandles.lookup().lookupClass());

		private final Chainer tracer;
		private final Item parent;

		private TraceListenableFutureCallback(Chainer tracer, Item parent) {
			this.tracer = tracer;
			this.parent = parent;
		}

		@Override
		public void onFailure(Throwable ex) {
			continueSpan();
			if (log.isDebugEnabled()) {
				log.debug("The callback failed - will close the span");
			}
			this.tracer.addTag(Item.SPAN_ERROR_TAG_NAME, ExceptionUtils.getExceptionMessage(ex));
			finish();
		}

		@Override
		public void onSuccess(T result) {
			continueSpan();
			if (log.isDebugEnabled()) {
				log.debug("The callback succeeded - will close the span");
			}
			finish();
		}

		private void continueSpan() {
			this.tracer.continueSpan(this.parent);
		}

		private void finish() {
			if (!isTracing()) {
				return;
			}
			currentSpan().logEvent(Item.CLIENT_RECV);
			this.tracer.close(currentSpan());
		}

		private Item currentSpan() {
			return this.tracer.getCurrentSpan();
		}

		private boolean isTracing() {
			return this.tracer.isTracing();
		}
	}





}


// Node: isDone
package trainFood;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;
import org.springframework.cloud.client.loadbalancer.LoadBalanced;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.EnableAspectJAutoProxy;
import org.springframework.integration.annotation.IntegrationComponentScan;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.web.client.RestTemplate;
import springfox.documentation.swagger2.annotations.EnableSwagger2;

@SpringBootApplication
@EnableAspectJAutoProxy(proxyTargetClass = true)
@EnableAsync
@IntegrationComponentScan
@EnableSwagger2
@EnableDiscoveryClient
public class TrainFoodApplication {

    public static void main(String[] args) {
        SpringApplication.run(TrainFoodApplication.class, args);
    }
    @LoadBalanced
    @Bean
    public RestTemplate restTemplate(RestTemplateBuilder builder) {
        return builder.build();
    }
}


package execute;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;
import org.springframework.cloud.client.loadbalancer.LoadBalanced;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.EnableAspectJAutoProxy;
import org.springframework.integration.annotation.IntegrationComponentScan;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.web.client.RestTemplate;
import springfox.documentation.swagger2.annotations.EnableSwagger2;

/**
 * @author fdse
 */
@SpringBootApplication
@EnableAspectJAutoProxy(proxyTargetClass = true)
@EnableAsync
@IntegrationComponentScan
@EnableSwagger2
@EnableDiscoveryClient
public class ExecuteApplication {

    public static void main(String[] args) {
        SpringApplication.run(ExecuteApplication.class, args);
    }

    @LoadBalanced
    @Bean
    public RestTemplate restTemplate(RestTemplateBuilder builder) {
        return builder.build();
    }
}


package execute.controller;

import com.alibaba.fastjson.JSONObject;
import edu.fudan.common.util.Response;
import execute.serivce.ExecuteService;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.request.MockMvcRequestBuilders;
import org.springframework.test.web.servlet.result.MockMvcResultMatchers;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

@RunWith(JUnit4.class)
public class ExecuteControlllerTest {

    @InjectMocks
    private ExecuteControlller executeController;

    @Mock
    private ExecuteService executeService;
    private MockMvc mockMvc;
    private Response response = new Response();

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
        mockMvc = MockMvcBuilders.standaloneSetup(executeController).build();
    }

    @Test
    public void testHome() throws Exception {
        mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/executeservice/welcome"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andExpect(MockMvcResultMatchers.content().string("Welcome to [ Execute Service ] !"));
    }

    @Test
    public void testExecuteTicket() throws Exception {
        Mockito.when(executeService.ticketExecute(Mockito.anyString(), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/executeservice/execute/execute/order_id"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testCollectTicket() throws Exception {
        Mockito.when(executeService.ticketCollect(Mockito.anyString(), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/executeservice/execute/collected/order_id"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

}


// Node: testExecuteTicket
// Node: testCollectTicket
package execute.service;

import edu.fudan.common.util.Response;
import edu.fudan.common.entity.Order;
import execute.serivce.ExecuteServiceImpl;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.*;
import org.springframework.web.client.RestTemplate;

public class ExecuteServiceImplTest {

    @InjectMocks
    private ExecuteServiceImpl executeServiceImpl;

    @Mock
    private RestTemplate restTemplate;

    private HttpHeaders headers = new HttpHeaders();
    private HttpEntity requestEntity = new HttpEntity(headers);

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
    }

    @Test
    public void testTicketExecute1() {
        //mock getOrderByIdFromOrder()
        Order order = new Order();
        order.setStatus(2);
        Response<Order> response = new Response<>(1, null, order);
        ResponseEntity<Response<Order>> re = new ResponseEntity<>(response, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                "http://ts-order-service:12031/api/v1/orderservice/order/" + "order_id",
                HttpMethod.GET,
                requestEntity,
                new ParameterizedTypeReference<Response<Order>>() {
                })).thenReturn(re);
        //mock executeOrder()
        Response response2 = new Response(1, null, null);
        ResponseEntity<Response> re2 = new ResponseEntity<>(response2, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                "http://ts-order-service:12031/api/v1/orderservice/order/status/" + "order_id" + "/" + 6,
                HttpMethod.GET,
                requestEntity,
                Response.class)).thenReturn(re2);
        Response result = executeServiceImpl.ticketExecute("order_id", headers);
        Assert.assertEquals(new Response<>(1, "Success.", null), result);
    }

    @Test
    public void testTicketExecute2() {
        //mock getOrderByIdFromOrder(
        Response<Order> response = new Response<>(0, null, null);
        ResponseEntity<Response<Order>> re = new ResponseEntity<>(response, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                "http://ts-order-service:12031/api/v1/orderservice/order/" + "order_id",
                HttpMethod.GET,
                requestEntity,
                new ParameterizedTypeReference<Response<Order>>() {
                })).thenReturn(re);
        //mock getOrderByIdFromOrderOther()
        Order order = new Order();
        order.setStatus(2);
        Response<Order> response2 = new Response<>(1, null, order);
        ResponseEntity<Response<Order>> re2 = new ResponseEntity<>(response2, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                "http://ts-order-other-service:12032/api/v1/orderOtherService/orderOther/" + "order_id",
                HttpMethod.GET,
                requestEntity,
                new ParameterizedTypeReference<Response<Order>>() {
                })).thenReturn(re2);
        //mock executeOrderOther()
        Response response3 = new Response(1, null, null);
        ResponseEntity<Response> re3 = new ResponseEntity<>(response3, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                "http://ts-order-other-service:12032/api/v1/orderOtherService/orderOther/status/" + "order_id" + "/" + 6,
                HttpMethod.GET,
                requestEntity,
                Response.class)).thenReturn(re3);
        Response result = executeServiceImpl.ticketExecute("order_id", headers);
        Assert.assertEquals(new Response<>(1, "Success", null), result);
    }

    @Test
    public void testTicketCollect1() {
        //mock getOrderByIdFromOrder()
        Order order = new Order();
        order.setStatus(1);
        Response<Order> response = new Response<>(1, null, order);
        ResponseEntity<Response<Order>> re = new ResponseEntity<>(response, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                "http://ts-order-service:12031/api/v1/orderservice/order/" + "order_id",
                HttpMethod.GET,
                requestEntity,
                new ParameterizedTypeReference<Response<Order>>() {
                })).thenReturn(re);
        //mock executeOrder()
        Response response2 = new Response(1, null, null);
        ResponseEntity<Response> re2 = new ResponseEntity<>(response2, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                "http://ts-order-service:12031/api/v1/orderservice/order/status/" + "order_id" + "/" + 2,
                HttpMethod.GET,
                requestEntity,
                Response.class)).thenReturn(re2);
        Response result = executeServiceImpl.ticketCollect("order_id", headers);
        Assert.assertEquals(new Response<>(1, "Success", null), result);
    }

    @Test
    public void testTicketCollect2() {
        //mock getOrderByIdFromOrder(
        Response<Order> response = new Response<>(0, null, null);
        ResponseEntity<Response<Order>> re = new ResponseEntity<>(response, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                "http://ts-order-service:12031/api/v1/orderservice/order/" + "order_id",
                HttpMethod.GET,
                requestEntity,
                new ParameterizedTypeReference<Response<Order>>() {
                })).thenReturn(re);
        //mock getOrderByIdFromOrderOther()
        Order order = new Order();
        order.setStatus(1);
        Response<Order> response2 = new Response<>(1, null, order);
        ResponseEntity<Response<Order>> re2 = new ResponseEntity<>(response2, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                "http://ts-order-other-service:12032/api/v1/orderOtherService/orderOther/" + "order_id",
                HttpMethod.GET,
                requestEntity,
                new ParameterizedTypeReference<Response<Order>>() {
                })).thenReturn(re2);
        //mock executeOrderOther()
        Response response3 = new Response(1, null, null);
        ResponseEntity<Response> re3 = new ResponseEntity<>(response3, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                "http://ts-order-other-service:12032/api/v1/orderOtherService/orderOther/status/" + "order_id" + "/" + 2,
                HttpMethod.GET,
                requestEntity,
                Response.class)).thenReturn(re3);
        Response result = executeServiceImpl.ticketCollect("order_id", headers);
        Assert.assertEquals(new Response<>(1, "Success.", null), result);
    }

}


package fdse.microservice;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;
import org.springframework.cloud.client.loadbalancer.LoadBalanced;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.EnableAspectJAutoProxy;
import org.springframework.integration.annotation.IntegrationComponentScan;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.web.client.RestTemplate;
import springfox.documentation.swagger2.annotations.EnableSwagger2;

@SpringBootApplication
@EnableAspectJAutoProxy(proxyTargetClass = true)
@EnableAsync
@IntegrationComponentScan
@EnableSwagger2
@EnableDiscoveryClient
public class StationApplication {

	public static void main(String[] args) {
		SpringApplication.run(StationApplication.class, args);
	}

	@LoadBalanced
	@Bean
	public RestTemplate restTemplate(RestTemplateBuilder builder) {
		return builder.build();
	}
}


package fdse.microservice.controller;

import edu.fudan.common.util.Response;
import fdse.microservice.entity.*;
import fdse.microservice.service.StationService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

import static org.springframework.http.ResponseEntity.ok;

@RestController
@RequestMapping("/api/v1/stationservice")
public class StationController {

    @Autowired
    private StationService stationService;

    private static final Logger LOGGER = LoggerFactory.getLogger(StationController.class);

    @GetMapping(path = "/welcome")
    public String home(@RequestHeader HttpHeaders headers) {
        return "Welcome to [ Station Service ] !";
    }

    @GetMapping(value = "/stations")
    public HttpEntity query(@RequestHeader HttpHeaders headers) {
        return ok(stationService.query(headers));
    }

    @PostMapping(value = "/stations")
    public ResponseEntity<Response> create(@RequestBody Station station, @RequestHeader HttpHeaders headers) {
        StationController.LOGGER.info("[create][Create station][name: {}]",station.getName());
        return new ResponseEntity<>(stationService.create(station, headers), HttpStatus.CREATED);
    }

    @PutMapping(value = "/stations")
    public HttpEntity update(@RequestBody Station station, @RequestHeader HttpHeaders headers) {
        StationController.LOGGER.info("[update][Update station][StationId: {}]",station.getId());
        return ok(stationService.update(station, headers));
    }

    @DeleteMapping(value = "/stations/{stationsId}")
    public ResponseEntity<Response> delete(@PathVariable String stationsId, @RequestHeader HttpHeaders headers) {
        StationController.LOGGER.info("[delete][Delete station][StationId: {}]",stationsId);
        return ok(stationService.delete(stationsId, headers));
    }



    // according to station name ---> query station id
    @GetMapping(value = "/stations/id/{stationNameForId}")
    public HttpEntity queryForStationId(@PathVariable(value = "stationNameForId")
                                                String stationName, @RequestHeader HttpHeaders headers) {
        // string
        StationController.LOGGER.info("[queryForId][Query for station id][StationName: {}]",stationName);
        return ok(stationService.queryForId(stationName, headers));
    }

    // according to station name list --->  query all station ids
    @CrossOrigin(origins = "*")
    @PostMapping(value = "/stations/idlist")
    public HttpEntity queryForIdBatch(@RequestBody List<String> stationNameList, @RequestHeader HttpHeaders headers) {
        StationController.LOGGER.info("[queryForIdBatch][Query stations for id batch][StationNameNumbers: {}]",stationNameList.size());
        return ok(stationService.queryForIdBatch(stationNameList, headers));
    }

    // according to station id ---> query station name
    @CrossOrigin(origins = "*")
    @GetMapping(value = "/stations/name/{stationIdForName}")
    public HttpEntity queryById(@PathVariable(value = "stationIdForName")
                                        String stationId, @RequestHeader HttpHeaders headers) {
        StationController.LOGGER.info("[queryById][Query stations By Id][Id: {}]", stationId);
        // string
        return ok(stationService.queryById(stationId, headers));
    }

    // according to station id list  ---> query all station names
    @CrossOrigin(origins = "*")
    @PostMapping(value = "/stations/namelist")
    public HttpEntity queryForNameBatch(@RequestBody List<String> stationIdList, @RequestHeader HttpHeaders headers) {
        StationController.LOGGER.info("[queryByIdBatch][Query stations for name batch][StationIdNumbers: {}]",stationIdList.size());
        return ok(stationService.queryByIdBatch(stationIdList, headers));
    }

}


// Node: PathVariable
// Node: queryForId
// Node: queryForIdBatch
package fdse.microservice.service;

import edu.fudan.common.util.Response;
import fdse.microservice.entity.*;
import org.springframework.http.HttpHeaders;

import java.util.List;

public interface StationService {
    //CRUD
    Response create(Station info, HttpHeaders headers);

    boolean exist(String stationName, HttpHeaders headers);

    Response update(Station info, HttpHeaders headers);

    Response delete(String stationsId, HttpHeaders headers);

    Response query(HttpHeaders headers);

    Response queryForId(String stationName, HttpHeaders headers);

    Response queryForIdBatch(List<String> nameList, HttpHeaders headers);

    Response queryById(String stationId, HttpHeaders headers);

    Response queryByIdBatch(List<String> stationIdList, HttpHeaders headers);

}


// Node: repos/cloned_ms_repos/train-ticket/ts-station-service/src/main/java/fdse/microservice/service/StationService.java:StationService.<init>
package fdse.microservice.service;

import edu.fudan.common.util.Response;
import fdse.microservice.entity.*;
import fdse.microservice.repository.StationRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpHeaders;
import org.springframework.stereotype.Service;

import java.util.*;


@Service
public class StationServiceImpl implements StationService {

    @Autowired
    private StationRepository repository;

    String success = "Success";

    private static final Logger LOGGER = LoggerFactory.getLogger(StationServiceImpl.class);

    @Override
    public Response create(Station station, HttpHeaders headers) {
        if(station.getName().isEmpty()) {
            StationServiceImpl.LOGGER.error("[create][Create station error][Name not specify]");
            return new Response<>(0, "Name not specify", station);
        }
        if (repository.findByName(station.getName()) == null) {
            station.setStayTime(station.getStayTime());
            repository.save(station);
            return new Response<>(1, "Create success", station);
        }
        StationServiceImpl.LOGGER.error("[create][Create station error][Already exists][StationId: {}]",station.getId());
        return new Response<>(0, "Already exists", station);
    }


    @Override
    public boolean exist(String stationName, HttpHeaders headers) {
        boolean result = false;
        if (repository.findByName(stationName) != null) {
            result = true;
        }
        return result;
    }

    @Override
    public Response update(Station info, HttpHeaders headers) {

        Optional<Station> op = repository.findById(info.getId());
        if (!op.isPresent()) {
            StationServiceImpl.LOGGER.error("[update][Update station error][Station not found][StationId: {}]",info.getId());
            return new Response<>(0, "Station not exist", null);
        } else {
            Station station = op.get();
            station.setName(info.getName());
            station.setStayTime(info.getStayTime());
            repository.save(station);
            return new Response<>(1, "Update success", station);
        }
    }

    @Override
    public Response delete(String stationsId, HttpHeaders headers) {
        Optional<Station> op = repository.findById(stationsId);
        if (op.isPresent()) {
            Station station = op.get();
            repository.delete(station);
            return new Response<>(1, "Delete success", station);
        }
        StationServiceImpl.LOGGER.error("[delete][Delete station error][Station not found][StationId: {}]",stationsId);
        return new Response<>(0, "Station not exist", null);
    }

    @Override
    public Response query(HttpHeaders headers) {
        List<Station> stations = repository.findAll();
        if (stations != null && !stations.isEmpty()) {
            return new Response<>(1, "Find all content", stations);
        } else {
            StationServiceImpl.LOGGER.warn("[query][Query stations warn][Find all stations: {}]","No content");
            return new Response<>(0, "No content", null);
        }
    }

    @Override
    public Response queryForId(String stationName, HttpHeaders headers) {
        Station station = repository.findByName(stationName);

        if (station  != null) {
            return new Response<>(1, success, station.getId());
        } else {
            StationServiceImpl.LOGGER.warn("[queryForId][Find station id warn][Station not found][StationName: {}]",stationName);
            return new Response<>(0, "Not exists", stationName);
        }
    }


    @Override
    public Response queryForIdBatch(List<String> nameList, HttpHeaders headers) {
        Map<String, String> result = new HashMap<>();
        List<Station> stations = repository.findByNames(nameList);
        Map<String, String> stationMap = new HashMap<>();
        for(Station s: stations) {
            stationMap.put(s.getName(), s.getId());
        }

        for(String name: nameList){
            result.put(name, stationMap.get(name));
        }

        if (!result.isEmpty()) {
            return new Response<>(1, success, result);
        } else {
            StationServiceImpl.LOGGER.warn("[queryForIdBatch][Find station ids warn][Stations not found][StationNameNumber: {}]",nameList.size());
            return new Response<>(0, "No content according to name list", null);
        }

    }

    @Override
    public Response queryById(String stationId, HttpHeaders headers) {
        Optional<Station> station = repository.findById(stationId);
        if (station.isPresent()) {
            return new Response<>(1, success, station.get().getName());
        } else {
            StationServiceImpl.LOGGER.error("[queryById][Find station name error][Station not found][StationId: {}]",stationId);
            return new Response<>(0, "No that stationId", stationId);
        }
    }

    @Override
    public Response queryByIdBatch(List<String> idList, HttpHeaders headers) {
        ArrayList<String> result = new ArrayList<>();
        for (int i = 0; i < idList.size(); i++) {
            Optional<Station> stationOld = repository.findById(idList.get(i));
            if(stationOld.isPresent()){
                Station station=stationOld.get();
                result.add(station.getName());
            }
        }

        if (!result.isEmpty()) {
            return new Response<>(1, success, result);
        } else {
            StationServiceImpl.LOGGER.error("[queryByIdBatch][Find station names error][Stations not found][StationIdNumber: {}]",idList.size());
            return new Response<>(0, "No stationNamelist according to stationIdList", result);
        }

    }
}


package fdse.microservice.controller;

import com.alibaba.fastjson.JSONObject;
import edu.fudan.common.util.Response;
import fdse.microservice.entity.Station;
import fdse.microservice.service.StationService;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.springframework.http.*;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.request.MockMvcRequestBuilders;
import org.springframework.test.web.servlet.result.MockMvcResultMatchers;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

import java.util.ArrayList;
import java.util.List;

@RunWith(JUnit4.class)
public class StationControllerTest {

    @InjectMocks
    private StationController stationController;

    @Mock
    private StationService stationService;
    private MockMvc mockMvc;
    private Response response = new Response();

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
        mockMvc = MockMvcBuilders.standaloneSetup(stationController).build();
    }

    @Test
    public void testHome() throws Exception {
        mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/stationservice/welcome"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andExpect(MockMvcResultMatchers.content().string("Welcome to [ Station Service ] !"));
    }

    @Test
    public void testQuery() throws Exception {
        Mockito.when(stationService.query(Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/stationservice/stations"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testCreate() throws Exception {
        Station station = new Station();
        Mockito.when(stationService.create(Mockito.any(Station.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(station);
        String result = mockMvc.perform(MockMvcRequestBuilders.post("/api/v1/stationservice/stations").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isCreated())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testUpdate() throws Exception {
        Station station = new Station();
        Mockito.when(stationService.update(Mockito.any(Station.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(station);
        String result = mockMvc.perform(MockMvcRequestBuilders.put("/api/v1/stationservice/stations").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testDelete() throws Exception {
        Station station = new Station();
        Mockito.when(stationService.delete(Mockito.anyString(), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(station);
        String result = mockMvc.perform(MockMvcRequestBuilders.delete("/api/v1/stationservice/stations").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testQueryForStationId() throws Exception {
        Mockito.when(stationService.queryForId(Mockito.anyString(), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/stationservice/stations/id/station_name"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testQueryForIdBatch() throws Exception {
        List<String> stationNameList = new ArrayList<>();
        Mockito.when(stationService.queryForIdBatch(Mockito.anyList(), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(stationNameList);
        String result = mockMvc.perform(MockMvcRequestBuilders.post("/api/v1/stationservice/stations/idlist").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testQueryById() throws Exception {
        Mockito.when(stationService.queryById(Mockito.anyString(), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/stationservice/stations/name/station_id"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testQueryForNameBatch() throws Exception {
        List<String> stationIdList = new ArrayList<>();
        Mockito.when(stationService.queryByIdBatch(Mockito.anyList(), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(stationIdList);
        String result = mockMvc.perform(MockMvcRequestBuilders.post("/api/v1/stationservice/stations/namelist").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

}


// Node: testQueryForIdBatch
// Node: anyList
// Node: testQueryForNameBatch
package fdse.microservice.service;

import edu.fudan.common.util.Response;
import fdse.microservice.entity.Station;
import fdse.microservice.repository.StationRepository;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.springframework.http.HttpHeaders;

import java.util.ArrayList;
import java.util.List;

@RunWith(JUnit4.class)
public class StationServiceImplTest {

    @InjectMocks
    private StationServiceImpl stationServiceImpl;

    @Mock
    private StationRepository repository;

    private HttpHeaders headers = new HttpHeaders();

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
    }

    @Test
    public void testCreate1() {
        Station station = new Station();
        Mockito.when(repository.findById(Mockito.anyString()).get()).thenReturn(null);
        Mockito.when(repository.save(Mockito.any(Station.class))).thenReturn(null);
        Response result = stationServiceImpl.create(station, headers);
        Assert.assertEquals(new Response<>(1, "Create success", station), result);
    }

    @Test
    public void testCreate2() {
        Station station = new Station();
        Mockito.when(repository.findById(Mockito.anyString()).get()).thenReturn(station);
        Response result = stationServiceImpl.create(station, headers);
        Assert.assertEquals(new Response<>(0, "Already exists", station), result);
    }

    @Test
    public void testExist1() {
        Station station = new Station();
        Mockito.when(repository.findByName(Mockito.anyString())).thenReturn(station);
        Assert.assertTrue(stationServiceImpl.exist("station_name", headers));
    }

    @Test
    public void testExist2() {
        Mockito.when(repository.findByName(Mockito.anyString())).thenReturn(null);
        Assert.assertFalse(stationServiceImpl.exist("station_name", headers));
    }

    @Test
    public void testUpdate1() {
        Station info = new Station();
        Mockito.when(repository.findById(Mockito.anyString())).thenReturn(null);
        Response result = stationServiceImpl.update(info, headers);
        Assert.assertEquals(new Response<>(0, "Station not exist", null), result);
    }

    @Test
    public void testUpdate2() {
        Station info = new Station();
        Mockito.when(repository.findById(Mockito.anyString()).get()).thenReturn(info);
        Mockito.when(repository.save(Mockito.any(Station.class))).thenReturn(null);
        Response result = stationServiceImpl.update(info, headers);
        Assert.assertEquals("Update success", result.getMsg());
    }

    @Test
    public void testDelete1() {
        Station info = new Station();
        Mockito.when(repository.findById(Mockito.anyString()).get()).thenReturn(info);
        Mockito.doNothing().doThrow(new RuntimeException()).when(repository).delete(Mockito.any(Station.class));
        Response result = stationServiceImpl.delete(info.getId(), headers);
        Assert.assertEquals("Delete success", result.getMsg());
    }

    @Test
    public void testDelete2() {
        Station info = new Station();
        Mockito.when(repository.findById(Mockito.anyString())).thenReturn(null);
        Response result = stationServiceImpl.delete(info.getId(), headers);
        Assert.assertEquals(new Response<>(0, "Station not exist", null), result);
    }

    @Test
    public void testQuery1() {
        List<Station> stations = new ArrayList<>();
        stations.add(new Station());
        Mockito.when(repository.findAll()).thenReturn(stations);
        Response result = stationServiceImpl.query(headers);
        Assert.assertEquals(new Response<>(1, "Find all content", stations), result);
    }

    @Test
    public void testQuery2() {
        Mockito.when(repository.findAll()).thenReturn(null);
        Response result = stationServiceImpl.query(headers);
        Assert.assertEquals(new Response<>(0, "No content", null), result);
    }

    @Test
    public void testQueryForId1() {
        Station station = new Station();
        Mockito.when(repository.findByName(Mockito.anyString())).thenReturn(station);
        Response result = stationServiceImpl.queryForId("station_name", headers);
        Assert.assertEquals(new Response<>(1, "Success", station.getId()), result);
    }

    @Test
    public void testQueryForId2() {
        Mockito.when(repository.findByName(Mockito.anyString())).thenReturn(null);
        Response result = stationServiceImpl.queryForId("station_name", headers);
        Assert.assertEquals(new Response<>(0, "Not exists", "station_name"), result);
    }

    @Test
    public void testQueryForIdBatch1() {
        List<String> nameList = new ArrayList<>();
        Response result = stationServiceImpl.queryForIdBatch(nameList, headers);
        Assert.assertEquals(new Response<>(0, "No content according to name list", null), result);
    }

    @Test
    public void testQueryForIdBatch2() {
        List<String> nameList = new ArrayList<>();
        nameList.add("station_name");
        Mockito.when(repository.findByName(Mockito.anyString())).thenReturn(null);
        Response result = stationServiceImpl.queryForIdBatch(nameList, headers);
        Assert.assertEquals("Success", result.getMsg());
    }

    @Test
    public void testQueryById1() {
        Station station = new Station();
        Mockito.when(repository.findById(Mockito.anyString()).get()).thenReturn(station);
        Response result = stationServiceImpl.queryById("station_id", headers);
        Assert.assertEquals(new Response<>(1, "Success", ""), result);
    }

    @Test
    public void testQueryById2() {
        Mockito.when(repository.findById(Mockito.anyString())).thenReturn(null);
        Response result = stationServiceImpl.queryById("station_id", headers);
        Assert.assertEquals(new Response<>(0, "No that stationId", "station_id"), result);
    }

    @Test
    public void testQueryByIdBatch1() {
        List<String> idList = new ArrayList<>();
        Response result = stationServiceImpl.queryByIdBatch(idList, headers);
        Assert.assertEquals(new Response<>(0, "No stationNamelist according to stationIdList", new ArrayList<>()), result);
    }

    @Test
    public void testQueryByIdBatch2() {
        Station station = new Station();
        List<String> idList = new ArrayList<>();
        idList.add("station_id");
        Mockito.when(repository.findById(Mockito.anyString()).get()).thenReturn(station);
        Response result = stationServiceImpl.queryByIdBatch(idList, headers);
        Assert.assertEquals("Success", result.getMsg());
    }

}


// Node: testQueryForIdBatch1
package admintravel;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;
import org.springframework.cloud.client.loadbalancer.LoadBalanced;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.EnableAspectJAutoProxy;
import org.springframework.integration.annotation.IntegrationComponentScan;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.web.client.RestTemplate;
import springfox.documentation.swagger2.annotations.EnableSwagger2;

/**
 * @author fdse
 */
@SpringBootApplication
@EnableAspectJAutoProxy(proxyTargetClass = true)
@EnableAsync
@IntegrationComponentScan
@EnableSwagger2
@EnableDiscoveryClient
public class AdminTravelApplication {
    public static void main(String[] args) {
        SpringApplication.run(AdminTravelApplication.class, args);
    }

    @LoadBalanced
    @Bean
    public RestTemplate restTemplate(RestTemplateBuilder builder) {
        return builder.build();
    }
}


package admintravel.controller;

import admintravel.service.AdminTravelService;
import com.alibaba.fastjson.JSONObject;
import edu.fudan.common.entity.TravelInfo;
import edu.fudan.common.util.Response;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.springframework.http.*;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.request.MockMvcRequestBuilders;
import org.springframework.test.web.servlet.result.MockMvcResultMatchers;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

@RunWith(JUnit4.class)
public class AdminTravelControllerTest {

    @InjectMocks
    private AdminTravelController adminTravelController;

    @Mock
    private AdminTravelService adminTravelService;
    private MockMvc mockMvc;
    private Response response = new Response();

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
        mockMvc = MockMvcBuilders.standaloneSetup(adminTravelController).build();
    }

    @Test
    public void testHome() throws Exception {
        mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/admintravelservice/welcome"))
            .andExpect(MockMvcResultMatchers.status().isOk());
    }

    @Test
    public void testGetAllTravels() throws Exception {
        Mockito.when(adminTravelService.getAllTravels(Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/admintravelservice/admintravel"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testAddTravel() throws Exception {
        TravelInfo request = new TravelInfo();
        Mockito.when(adminTravelService.addTravel(Mockito.any(TravelInfo.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(request);
        String result = mockMvc.perform(MockMvcRequestBuilders.post("/api/v1/admintravelservice/admintravel").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testUpdateTravel() throws Exception {
        TravelInfo request = new TravelInfo();
        Mockito.when(adminTravelService.updateTravel(Mockito.any(TravelInfo.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(request);
        String result = mockMvc.perform(MockMvcRequestBuilders.put("/api/v1/admintravelservice/admintravel").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testDeleteTravel() throws Exception {
        Mockito.when(adminTravelService.deleteTravel(Mockito.anyString(), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.delete("/api/v1/admintravelservice/admintravel/trip_id"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

}


// Node: testGetAllTravels
// Node: testAddTravel
// Node: testUpdateTravel
// Node: testDeleteTravel
package admintravel.service;

import edu.fudan.common.entity.AdminTrip;
import edu.fudan.common.entity.TravelInfo;
import edu.fudan.common.util.Response;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.*;
import org.springframework.web.client.RestTemplate;

import java.util.ArrayList;

@RunWith(JUnit4.class)
public class AdminTravelServiceImplTest {

    @InjectMocks
    private AdminTravelServiceImpl adminTravelServiceImpl;

    @Mock
    private RestTemplate restTemplate;

    private HttpHeaders headers = new HttpHeaders();
    private HttpEntity requestEntity = new HttpEntity(headers);

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
    }

    @Test
    public void testGetAllTravels1() {
        Response<ArrayList<AdminTrip>> response = new Response<>(0, null, null);
        ResponseEntity<Response<ArrayList<AdminTrip>>> re = new ResponseEntity<>(response, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                "http://ts-travel-service:12346/api/v1/travelservice/admin_trip",
                HttpMethod.GET,
                requestEntity,
                new ParameterizedTypeReference<Response<ArrayList<AdminTrip>>>() {
                })).thenReturn(re);
        Mockito.when(restTemplate.exchange(
                "http://ts-travel2-service:16346/api/v1/travel2service/admin_trip",
                HttpMethod.GET,
                requestEntity,
                new ParameterizedTypeReference<Response<ArrayList<AdminTrip>>>() {
                })).thenReturn(re);
        Response result = adminTravelServiceImpl.getAllTravels(headers);
        Assert.assertEquals(new Response<>(0, null, new ArrayList<>()), result);
    }

    @Test
    public void testGetAllTravels2() {
        ArrayList<AdminTrip> adminTrips = new ArrayList<>();
        adminTrips.add(new AdminTrip());
        Response<ArrayList<AdminTrip>> response = new Response<>(1, null, adminTrips);
        ResponseEntity<Response<ArrayList<AdminTrip>>> re = new ResponseEntity<>(response, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                "http://ts-travel-service:12346/api/v1/travelservice/admin_trip",
                HttpMethod.GET,
                requestEntity,
                new ParameterizedTypeReference<Response<ArrayList<AdminTrip>>>() {
                })).thenReturn(re);
        Mockito.when(restTemplate.exchange(
                "http://ts-travel2-service:16346/api/v1/travel2service/admin_trip",
                HttpMethod.GET,
                requestEntity,
                new ParameterizedTypeReference<Response<ArrayList<AdminTrip>>>() {
                })).thenReturn(re);
        Response result = adminTravelServiceImpl.getAllTravels(headers);
        Assert.assertNotNull(result);
    }

    @Test
    public void testAddTravel1() {
        TravelInfo request = new TravelInfo();
        request.setTrainTypeName("G");
        HttpEntity requestEntity2 = new HttpEntity<>(request, headers);
        Response response = new Response<>(0, null, null);
        ResponseEntity<Response> re = new ResponseEntity<>(response, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                "http://ts-travel-service:12346/api/v1/travelservice/trips",
                HttpMethod.POST,
                requestEntity2,
                Response.class)).thenReturn(re);
        Response result = adminTravelServiceImpl.addTravel(request, headers);
        Assert.assertEquals(new Response<>(0, "Admin add new travel failed", null), result);
    }

    @Test
    public void testAddTravel2() {
        TravelInfo request = new TravelInfo();
        request.setTrainTypeName("G");
        HttpEntity<TravelInfo> requestEntity2 = new HttpEntity<>(request, headers);
        Response response = new Response<>(1, null, null);
        ResponseEntity<Response> re = new ResponseEntity<>(response, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                "http://ts-travel-service:12346/api/v1/travelservice/trips",
                HttpMethod.POST,
                requestEntity2,
                Response.class)).thenReturn(re);
        Response result = adminTravelServiceImpl.addTravel(request, headers);
        Assert.assertEquals(new Response<>(1, "[Admin add new travel]", null), result);
    }

    @Test
    public void testAddTravel3() {
        TravelInfo request = new TravelInfo();
        request.setTrainTypeName("K");
        HttpEntity<TravelInfo> requestEntity2 = new HttpEntity<>(request, headers);
        Response response = new Response<>(0, null, null);
        ResponseEntity<Response> re = new ResponseEntity<>(response, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                "http://ts-travel2-service:16346/api/v1/travel2service/trips",
                HttpMethod.POST,
                requestEntity2,
                Response.class)).thenReturn(re);
        Response result = adminTravelServiceImpl.addTravel(request, headers);
        Assert.assertEquals(new Response<>(0, "Admin add new travel failed", null), result);
    }

    @Test
    public void testAddTravel4() {
        TravelInfo request = new TravelInfo();
        request.setTrainTypeName("K");
        HttpEntity<TravelInfo> requestEntity2 = new HttpEntity<>(request, headers);
        Response response = new Response<>(1, null, null);
        ResponseEntity<Response> re = new ResponseEntity<>(response, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                "http://ts-travel2-service:16346/api/v1/travel2service/trips",
                HttpMethod.POST,
                requestEntity2,
                Response.class)).thenReturn(re);
        Response result = adminTravelServiceImpl.addTravel(request, headers);
        Assert.assertEquals(new Response<>(1, "[Admin add new travel]", null), result);
    }


    @Test
    public void testUpdateTravel1() {
        TravelInfo request = new TravelInfo();
        request.setTrainTypeName("G");
        HttpEntity<TravelInfo> requestEntity2 = new HttpEntity<>(request, headers);
        Response response = new Response(1, null, null);
        ResponseEntity<Response> re = new ResponseEntity<>(response, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                "http://ts-travel-service:12346/api/v1/travelservice/trips",
                HttpMethod.PUT,
                requestEntity2,
                Response.class)).thenReturn(re);
        Response result = adminTravelServiceImpl.updateTravel(request, headers);
        Assert.assertEquals(new Response<>(1, null, null), result);
    }

    @Test
    public void testUpdateTravel2() {
        TravelInfo request = new TravelInfo();
        request.setTrainTypeName("K");
        HttpEntity<TravelInfo> requestEntity2 = new HttpEntity<>(request, headers);
        Response response = new Response(1, null, null);
        ResponseEntity<Response> re = new ResponseEntity<>(response, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                "http://ts-travel2-service:16346/api/v1/travel2service/trips",
                HttpMethod.PUT,
                requestEntity2,
                Response.class)).thenReturn(re);
        Response result = adminTravelServiceImpl.updateTravel(request, headers);
        Assert.assertEquals(new Response<>(1, null, null), result);
    }

    @Test
    public void testDeleteTravel1() {
        Response response = new Response(1, null, null);
        ResponseEntity<Response> re = new ResponseEntity<>(response, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                "http://ts-travel-service:12346/api/v1/travelservice/trips/" + "GaoTie",
                HttpMethod.DELETE,
                requestEntity,
                Response.class)).thenReturn(re);
        Response result = adminTravelServiceImpl.deleteTravel("GaoTie", headers);
        Assert.assertEquals(new Response<>(1, null, null), result);
    }

    @Test
    public void testDeleteTravel2() {
        Response response = new Response(1, null, null);
        ResponseEntity<Response> re = new ResponseEntity<>(response, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                "http://ts-travel2-service:16346/api/v1/travel2service/trips/" + "K1024",
                HttpMethod.DELETE,
                requestEntity,
                Response.class)).thenReturn(re);
        Response result = adminTravelServiceImpl.deleteTravel("K1024", headers);
        Assert.assertEquals(new Response<>(1, null, null), result);
    }

}


package travelplan;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;
import org.springframework.cloud.client.loadbalancer.LoadBalanced;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.EnableAspectJAutoProxy;
import org.springframework.integration.annotation.IntegrationComponentScan;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.web.client.RestTemplate;
import springfox.documentation.swagger2.annotations.EnableSwagger2;

/**
 * @author fdse
 */
@SpringBootApplication
@EnableAspectJAutoProxy(proxyTargetClass = true)
@EnableAsync
@IntegrationComponentScan
@EnableSwagger2
@EnableDiscoveryClient
public class TravelPlanApplication {
    public static void main(String[] args) {
        SpringApplication.run(TravelPlanApplication.class, args);
    }

    @LoadBalanced
    @Bean
    public RestTemplate restTemplate(RestTemplateBuilder builder) {
        return builder.build();
    }
}


package travelplan.entity;

import edu.fudan.common.util.StringUtils;
import lombok.Data;

import java.util.Date;

/**
 * @author fdse
 */
@Data
public class TransferTravelInfo {

    private String startStation;

    private String viaStation;

    private String endStation;

    private String travelDate;

    private String trainType;

    public TransferTravelInfo() {
        //Empty Constructor
    }

    public TransferTravelInfo(String startStation, String viaStation, String endStation, String travelDate, String trainType) {
        this.startStation = startStation;
        this.viaStation = viaStation;
        this.endStation = endStation;
        this.travelDate = travelDate;
        this.trainType = trainType;
    }

    public Date getTravelDate() {
        return StringUtils.String2Date(travelDate);
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-travel-plan-service/src/main/java/travelplan/entity/TransferTravelInfo.java:TransferTravelInfo.<init>
// Node: TransferTravelInfo
package travelplan.controller;

import com.alibaba.fastjson.JSONObject;
import edu.fudan.common.util.Response;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.springframework.http.*;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.request.MockMvcRequestBuilders;
import org.springframework.test.web.servlet.result.MockMvcResultMatchers;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import travelplan.entity.TransferTravelInfo;
import edu.fudan.common.entity.TripInfo;
import travelplan.service.TravelPlanService;

@RunWith(JUnit4.class)
public class TravelPlanControllerTest {

    @InjectMocks
    private TravelPlanController travelPlanController;

    @Mock
    private TravelPlanService travelPlanService;
    private MockMvc mockMvc;
    private Response response = new Response();

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
        mockMvc = MockMvcBuilders.standaloneSetup(travelPlanController).build();
    }

    @Test
    public void testHome() throws Exception {
        mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/travelplanservice/welcome"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andExpect(MockMvcResultMatchers.content().string("Welcome to [ TravelPlan Service ] !"));
    }

    @Test
    public void testGetTransferResult() throws Exception {
        TransferTravelInfo info = new TransferTravelInfo();
        Mockito.when(travelPlanService.getTransferSearch(Mockito.any(TransferTravelInfo.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(info);
        String result = mockMvc.perform(MockMvcRequestBuilders.post("/api/v1/travelplanservice/travelPlan/transferResult").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testGetByCheapest() throws Exception {
        TripInfo queryInfo = new TripInfo();
        Mockito.when(travelPlanService.getCheapest(Mockito.any(TripInfo.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(queryInfo);
        String result = mockMvc.perform(MockMvcRequestBuilders.post("/api/v1/travelplanservice/travelPlan/cheapest").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testGetByQuickest() throws Exception {
        TripInfo queryInfo = new TripInfo();
        Mockito.when(travelPlanService.getQuickest(Mockito.any(TripInfo.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(queryInfo);
        String result = mockMvc.perform(MockMvcRequestBuilders.post("/api/v1/travelplanservice/travelPlan/quickest").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testGetByMinStation() throws Exception {
        TripInfo queryInfo = new TripInfo();
        Mockito.when(travelPlanService.getMinStation(Mockito.any(TripInfo.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(queryInfo);
        String result = mockMvc.perform(MockMvcRequestBuilders.post("/api/v1/travelplanservice/travelPlan/minStation").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

}


// Node: testGetTransferResult
// Node: testGetByCheapest
// Node: testGetByQuickest
// Node: testGetByMinStation
package travelplan.service;

import edu.fudan.common.util.Response;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.*;
import org.springframework.web.client.RestTemplate;
import edu.fudan.common.entity.*;
import travelplan.entity.TransferTravelInfo;

import java.util.ArrayList;
import java.util.Date;
import java.util.List;

@RunWith(JUnit4.class)
public class TravelPlanServiceImplTest {

    @InjectMocks
    private TravelPlanServiceImpl travelPlanServiceImpl;

    @Mock
    private RestTemplate restTemplate;

    private HttpHeaders headers = new HttpHeaders();

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
    }

    @Test
    public void testGetTransferSearch() {
        TransferTravelInfo info = new TransferTravelInfo("from_station", "", "to_station", "", "G");

        //mock tripsFromHighSpeed() and tripsFromNormal()
        List<TripResponse> tripResponseList = new ArrayList<>();
        Response<List<TripResponse>> response1 = new Response<>(null, null, tripResponseList);
        ResponseEntity<Response<List<TripResponse>>> re1 = new ResponseEntity<>(response1, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                Mockito.anyString(),
                Mockito.any(HttpMethod.class),
                Mockito.any(HttpEntity.class),
                Mockito.any(ParameterizedTypeReference.class)))
                .thenReturn(re1);
        Response result = travelPlanServiceImpl.getTransferSearch(info, headers);
        Assert.assertEquals("Success.", result.getMsg());
    }

    @Test
    public void testGetCheapest() {
        TripInfo info = new TripInfo("start_station", "end_station", "");

        //response for getRoutePlanResultCheapest()
        RoutePlanResultUnit rpru = new RoutePlanResultUnit("trip_id", "type_id", "from_station", "to_station", new ArrayList<>(), "1.0", "2.0", "", "");
        ArrayList<RoutePlanResultUnit> routePlanResultUnits = new ArrayList<RoutePlanResultUnit>(){{ add(rpru); }};
        Response<ArrayList<RoutePlanResultUnit>> response1 = new Response<>(null, null, routePlanResultUnits);
        ResponseEntity<Response<ArrayList<RoutePlanResultUnit>>> re1 = new ResponseEntity<>(response1, HttpStatus.OK);

        //response for transferStationIdToStationName()
        List<String> list = new ArrayList<>();
        Response<List<String>> response2 = new Response<>(null, null, list);
        ResponseEntity<Response<List<String>>> re2 = new ResponseEntity<>(response2, HttpStatus.OK);

        //response for queryForStationId()
        Response<String> response3 = new Response<>(null, null, "");
        ResponseEntity<Response<String>> re3 = new ResponseEntity<>(response3, HttpStatus.OK);

        //response for getRestTicketNumber()
        Response<Integer> response4 = new Response<>(null, null, 0);
        ResponseEntity<Response<Integer>> re4 = new ResponseEntity<>(response4, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                Mockito.anyString(),
                Mockito.any(HttpMethod.class),
                Mockito.any(HttpEntity.class),
                Mockito.any(ParameterizedTypeReference.class)))
                .thenReturn(re1)
                .thenReturn(re2)
                .thenReturn(re3).thenReturn(re3).thenReturn(re4)
                .thenReturn(re3).thenReturn(re3).thenReturn(re4);

        Response result = travelPlanServiceImpl.getCheapest(info, headers);
        Assert.assertEquals("Success", result.getMsg());
    }

    @Test
    public void testGetQuickest() {
        TripInfo info = new TripInfo("start_station", "end_station", "");

        //response for getRoutePlanResultQuickest()
        RoutePlanResultUnit rpru = new RoutePlanResultUnit("trip_id", "type_id", "from_station", "to_station", new ArrayList<>(), "1.0", "2.0", "", "");
        ArrayList<RoutePlanResultUnit> routePlanResultUnits = new ArrayList<RoutePlanResultUnit>(){{ add(rpru); }};
        Response<ArrayList<RoutePlanResultUnit>> response1 = new Response<>(null, null, routePlanResultUnits);
        ResponseEntity<Response<ArrayList<RoutePlanResultUnit>>> re1 = new ResponseEntity<>(response1, HttpStatus.OK);

        //response for transferStationIdToStationName()
        List<String> list = new ArrayList<>();
        Response<List<String>> response2 = new Response<>(null, null, list);
        ResponseEntity<Response<List<String>>> re2 = new ResponseEntity<>(response2, HttpStatus.OK);

        //response for queryForStationId()
        Response<String> response3 = new Response<>(null, null, "");
        ResponseEntity<Response<String>> re3 = new ResponseEntity<>(response3, HttpStatus.OK);

        //response for getRestTicketNumber()
        Response<Integer> response4 = new Response<>(null, null, 0);
        ResponseEntity<Response<Integer>> re4 = new ResponseEntity<>(response4, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                Mockito.anyString(),
                Mockito.any(HttpMethod.class),
                Mockito.any(HttpEntity.class),
                Mockito.any(ParameterizedTypeReference.class)))
                .thenReturn(re1)
                .thenReturn(re2)
                .thenReturn(re3).thenReturn(re3).thenReturn(re4)
                .thenReturn(re3).thenReturn(re3).thenReturn(re4);

        Response result = travelPlanServiceImpl.getQuickest(info, headers);
        Assert.assertEquals("Success", result.getMsg());
    }

    @Test
    public void testGetMinStation() {
        TripInfo info = new TripInfo("start_station", "end_station", "");

        //response for getRoutePlanResultMinStation()
        RoutePlanResultUnit rpru = new RoutePlanResultUnit("trip_id", "type_id", "from_station", "to_station", new ArrayList<>(), "1.0", "2.0", "", "");
        ArrayList<RoutePlanResultUnit> routePlanResultUnits = new ArrayList<RoutePlanResultUnit>(){{ add(rpru); }};
        Response<ArrayList<RoutePlanResultUnit>> response1 = new Response<>(null, null, routePlanResultUnits);
        ResponseEntity<Response<ArrayList<RoutePlanResultUnit>>> re1 = new ResponseEntity<>(response1, HttpStatus.OK);

        //response for transferStationIdToStationName()
        List<String> list = new ArrayList<>();
        Response<List<String>> response2 = new Response<>(null, null, list);
        ResponseEntity<Response<List<String>>> re2 = new ResponseEntity<>(response2, HttpStatus.OK);

        //response for queryForStationId()
        Response<String> response3 = new Response<>(null, null, "");
        ResponseEntity<Response<String>> re3 = new ResponseEntity<>(response3, HttpStatus.OK);

        //response for getRestTicketNumber()
        Response<Integer> response4 = new Response<>(null, null, 0);
        ResponseEntity<Response<Integer>> re4 = new ResponseEntity<>(response4, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                Mockito.anyString(),
                Mockito.any(HttpMethod.class),
                Mockito.any(HttpEntity.class),
                Mockito.any(ParameterizedTypeReference.class)))
                .thenReturn(re1)
                .thenReturn(re2)
                .thenReturn(re3).thenReturn(re3).thenReturn(re4)
                .thenReturn(re3).thenReturn(re3).thenReturn(re4);

        Response result = travelPlanServiceImpl.getMinStation(info, headers);
        Assert.assertEquals("Success", result.getMsg());
    }

}


package user;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;
import org.springframework.cloud.client.loadbalancer.LoadBalanced;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.EnableAspectJAutoProxy;
import org.springframework.integration.annotation.IntegrationComponentScan;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.web.client.RestTemplate;
import springfox.documentation.swagger2.annotations.EnableSwagger2;

/**
 * @author fdse
 */
@SpringBootApplication
@EnableAspectJAutoProxy(proxyTargetClass = true)
@EnableAsync
@IntegrationComponentScan
@EnableDiscoveryClient
@EnableSwagger2
public class UserApplication {
    public static void main(String[] args) {
        SpringApplication.run(UserApplication.class, args);
    }
    @LoadBalanced
    @Bean
    public RestTemplate restTemplate(RestTemplateBuilder builder) {
        return builder.build();
    }
}


package user.controller;

import edu.fudan.common.util.Response;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import user.dto.UserDto;
import user.service.UserService;

import java.util.UUID;

import static org.springframework.http.ResponseEntity.ok;

/**
 * @author fdse
 */
@RestController
@RequestMapping("/api/v1/userservice/users")
public class UserController {

    @Autowired
    private UserService userService;

    private static final Logger LOGGER = LoggerFactory.getLogger(UserController.class);

    @GetMapping("/hello")
    public String testHello() {
        return "Hello";
    }

    @GetMapping
    public ResponseEntity<Response> getAllUser(@RequestHeader HttpHeaders headers) {
        UserController.LOGGER.info("[getAllUser][Get all user]");
        return ok(userService.getAllUsers(headers));
    }

    @GetMapping("/{userName}")
    public ResponseEntity<Response> getUserByUserName(@PathVariable String userName, @RequestHeader HttpHeaders headers) {
        UserController.LOGGER.info("[getUserByUserName][Get user by user name][UserName: {}]",userName);
        return ok(userService.findByUserName(userName, headers));
    }
    @GetMapping("/id/{userId}")
    public ResponseEntity<Response> getUserByUserId(@PathVariable String userId, @RequestHeader HttpHeaders headers) {
        UserController.LOGGER.info("[getUserByUserId][Get user by user id][UserId: {}]",userId);
        return ok(userService.findByUserId(userId, headers));
    }

    @PostMapping("/register")
    public ResponseEntity<Response> registerUser(@RequestBody UserDto userDto, @RequestHeader HttpHeaders headers) {
        UserController.LOGGER.info("[registerUser][Register user][UserName: {}]",userDto.getUserName());
        return ResponseEntity.status(HttpStatus.CREATED).body(userService.saveUser(userDto, headers));
    }


    @DeleteMapping("/{userId}")
    public ResponseEntity<Response> deleteUserById(@PathVariable String userId,
                                                   @RequestHeader HttpHeaders headers) {
        // only admin token can delete
        UserController.LOGGER.info("[deleteUserById][Delete user][UserId: {}]",userId);
        return ok(userService.deleteUser(userId, headers));
    }

    @PutMapping
    public ResponseEntity<Response> updateUser(@RequestBody UserDto user,
                                               @RequestHeader HttpHeaders headers) {
        UserController.LOGGER.info("[updateUser][Update user][UserId: {}]",user.getUserId());
        return ok(userService.updateUser(user, headers));
    }

}


// Node: registerUser
package user.service;

import edu.fudan.common.util.Response;
import org.springframework.http.HttpHeaders;
import user.dto.UserDto;

import java.util.UUID;

/**
 * @author fdse
 */
public interface UserService {
    Response saveUser(UserDto user, HttpHeaders headers);

    Response getAllUsers(HttpHeaders headers);

    Response findByUserName(String userName, HttpHeaders headers);
    Response findByUserId(String userId, HttpHeaders headers);


    Response deleteUser(String userId, HttpHeaders headers);

    Response updateUser(UserDto user, HttpHeaders headers);
}


// Node: repos/cloned_ms_repos/train-ticket/ts-user-service/src/main/java/user/service/UserService.java:UserService.<init>
package user.controller;

import com.alibaba.fastjson.JSONObject;
import edu.fudan.common.util.Response;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.springframework.http.*;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.request.MockMvcRequestBuilders;
import org.springframework.test.web.servlet.result.MockMvcResultMatchers;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import user.dto.UserDto;
import user.service.UserService;

import java.util.UUID;

@RunWith(JUnit4.class)
public class UserControllerTest {

    @InjectMocks
    private UserController userController;

    @Mock
    private UserService userService;
    private MockMvc mockMvc;
    private Response response = new Response();

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
        mockMvc = MockMvcBuilders.standaloneSetup(userController).build();
    }

    @Test
    public void testHome() throws Exception {
        mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/userservice/users/hello"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andExpect(MockMvcResultMatchers.content().string("Hello"));
    }

    @Test
    public void testGetAllUser() throws Exception {
        Mockito.when(userService.getAllUsers(Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/userservice/users"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testGetUserByUserName() throws Exception {
        Mockito.when(userService.findByUserName(Mockito.anyString(), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/userservice/users/user_name"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testGetUserByUserId() throws Exception {
        Mockito.when(userService.findByUserId(Mockito.anyString(), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/userservice/users/id/user_id"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testRegisterUser() throws Exception {
        UserDto userDto = new UserDto();
        Mockito.when(userService.saveUser(Mockito.any(UserDto.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(userDto);
        String result = mockMvc.perform(MockMvcRequestBuilders.post("/api/v1/userservice/users/register").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isCreated())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testDeleteUserById() throws Exception {
        UUID userId = UUID.randomUUID();
        Mockito.when(userService.deleteUser(Mockito.any(UUID.class).toString(), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.delete("/api/v1/userservice/users/" + userId.toString()))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testUpdateUser() throws Exception {
        UserDto user = new UserDto();
        Mockito.when(userService.updateUser(Mockito.any(UserDto.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(user);
        String result = mockMvc.perform(MockMvcRequestBuilders.put("/api/v1/userservice/users").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

}


// Node: testGetUserByUserName
// Node: testGetUserByUserId
// Node: testRegisterUser
package user.service;

import edu.fudan.common.util.Response;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.*;
import org.springframework.web.client.RestTemplate;
import user.dto.AuthDto;
import user.dto.UserDto;
import user.entity.User;
import user.repository.UserRepository;
import user.service.impl.UserServiceImpl;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

@RunWith(JUnit4.class)
public class UserServiceImplTest {

    @InjectMocks
    private UserServiceImpl userServiceImpl;

    @Mock
    private UserRepository userRepository;

    @Mock
    private RestTemplate restTemplate;

    private HttpHeaders headers = new HttpHeaders();

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
    }

    @Test
    public void testSaveUser() {
        UserDto userDto = new UserDto(UUID.randomUUID().toString(), "user_name", "xxx", 0, 1, "", "");
        Mockito.when(userRepository.findByUserName(Mockito.anyString())).thenReturn(null);

        //mock createDefaultAuthUser()
        Response<ArrayList<AuthDto>> response1 = new Response<>();
        ResponseEntity<Response<ArrayList<AuthDto>>> re1 = new ResponseEntity<>(response1, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                Mockito.anyString(),
                Mockito.any(HttpMethod.class),
                Mockito.any(HttpEntity.class),
                Mockito.any(ParameterizedTypeReference.class)))
                .thenReturn(re1);

        User user = new User();
        Mockito.when(userRepository.save(Mockito.any(User.class))).thenReturn(user);
        Response result = userServiceImpl.saveUser(userDto, headers);
        Assert.assertEquals(new Response<>(1, "REGISTER USER SUCCESS", user), result);
    }

    @Test
    public void testGetAllUsers1() {
        List<User> users = new ArrayList<>();
        users.add(new User());
        Mockito.when(userRepository.findAll()).thenReturn(users);
        Response result = userServiceImpl.getAllUsers(headers);
        Assert.assertEquals(new Response<>(1, "Success", users), result);
    }

    @Test
    public void testGetAllUsers2() {
        Mockito.when(userRepository.findAll()).thenReturn(null);
        Response result = userServiceImpl.getAllUsers(headers);
        Assert.assertEquals(new Response<>(0, "NO User", null), result);
    }

    @Test
    public void testFindByUserName1() {
        User user = new User();
        Mockito.when(userRepository.findByUserName(Mockito.anyString())).thenReturn(user);
        Response result = userServiceImpl.findByUserName("user_name", headers);
        Assert.assertEquals(new Response<>(1, "Find User Success", user), result);
    }

    @Test
    public void testFindByUserName2() {
        Mockito.when(userRepository.findByUserName(Mockito.anyString())).thenReturn(null);
        Response result = userServiceImpl.findByUserName("user_name", headers);
        Assert.assertEquals(new Response<>(0, "No User", null), result);
    }

    @Test
    public void testFindByUserId1() {
        UUID userId = UUID.randomUUID();
        User user = new User();
        Mockito.when(userRepository.findByUserId(Mockito.any(UUID.class).toString())).thenReturn(user);
        Response result = userServiceImpl.findByUserId(userId.toString(), headers);
        Assert.assertEquals(new Response<>(1, "Find User Success", user), result);
    }

    @Test
    public void testFindByUserId2() {
        UUID userId = UUID.randomUUID();
        Mockito.when(userRepository.findByUserId(Mockito.any(UUID.class).toString())).thenReturn(null);
        Response result = userServiceImpl.findByUserId(userId.toString(), headers);
        Assert.assertEquals(new Response<>(0, "No User", null), result);
    }

    @Test
    public void testDeleteUser1() {
        String userId = UUID.randomUUID().toString();
        User user = new User();
        Mockito.when(userRepository.findByUserId(Mockito.any(UUID.class).toString())).thenReturn(user);
        HttpEntity<Response> httpEntity = new HttpEntity<>(headers);
        Mockito.when(restTemplate.exchange("http://ts-auth-service:12340/api/v1" + "/users/" + userId,
                HttpMethod.DELETE,
                httpEntity,
                Response.class)).thenReturn(null);
        Mockito.doNothing().doThrow(new RuntimeException()).when(userRepository).deleteByUserId(Mockito.any(UUID.class).toString());
        Response result = userServiceImpl.deleteUser(userId, headers);
        Assert.assertEquals(new Response<>(1, "DELETE SUCCESS", null), result);
    }

    @Test
    public void testDeleteUser2() {
        UUID userId = UUID.randomUUID();
        Mockito.when(userRepository.findByUserId(Mockito.any(UUID.class).toString())).thenReturn(null);
        Response result = userServiceImpl.deleteUser(userId.toString(), headers);
        Assert.assertEquals(new Response<>(0, "USER NOT EXISTS", null), result);
    }

    @Test
    public void testUpdateUser1() {
        UserDto userDto = new UserDto();
        User oldUser = new User();
        Mockito.when(userRepository.findByUserName(Mockito.anyString())).thenReturn(oldUser);
        Mockito.doNothing().doThrow(new RuntimeException()).when(userRepository).deleteByUserId(Mockito.any(UUID.class).toString());
        Mockito.when(userRepository.save(Mockito.any(User.class))).thenReturn(null);
        Response result = userServiceImpl.updateUser(userDto, headers);
        Assert.assertEquals("SAVE USER SUCCESS", result.getMsg());
    }

    @Test
    public void testUpdateUser2() {
        UserDto userDto = new UserDto();
        Mockito.when(userRepository.findByUserName(Mockito.anyString())).thenReturn(null);
        Response result = userServiceImpl.updateUser(userDto, headers);
        Assert.assertEquals(new Response(0, "USER NOT EXISTS", null), result);
    }

    @Test
    public void testDeleteUserAuth() {
        UUID userId = UUID.randomUUID();
        HttpEntity<Response> httpEntity = new HttpEntity<>(headers);
        Mockito.when(restTemplate.exchange("http://ts-auth-service:12340/api/v1" + "/users/" + userId,
                HttpMethod.DELETE,
                httpEntity,
                Response.class)).thenReturn(null);
        userServiceImpl.deleteUserAuth(userId.toString(), headers);
        Mockito.verify(restTemplate, Mockito.times(1))
                .exchange(Mockito.anyString(), Mockito.any(HttpMethod.class), Mockito.any(HttpEntity.class), Mockito.any(Class.class));
    }

}


package seat;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;
import org.springframework.cloud.client.loadbalancer.LoadBalanced;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.EnableAspectJAutoProxy;
import org.springframework.integration.annotation.IntegrationComponentScan;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.web.client.RestTemplate;
import springfox.documentation.swagger2.annotations.EnableSwagger2;

/**
 * @author fdse
 */
@SpringBootApplication
@EnableAspectJAutoProxy(proxyTargetClass = true)
@EnableAsync
@IntegrationComponentScan
@EnableSwagger2
@EnableDiscoveryClient
public class SeatApplication {

    public static void main(String[] args) {
        SpringApplication.run(SeatApplication.class, args);
    }

    @LoadBalanced
    @Bean
    public RestTemplate restTemplate(RestTemplateBuilder builder) {
        return builder.build();
    }
}


package seat.controller;

import com.alibaba.fastjson.JSONObject;
import edu.fudan.common.util.Response;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.springframework.http.*;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.request.MockMvcRequestBuilders;
import org.springframework.test.web.servlet.result.MockMvcResultMatchers;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import edu.fudan.common.entity.Seat;
import seat.service.SeatService;

@RunWith(JUnit4.class)
public class SeatControllerTest {

    @InjectMocks
    private SeatController seatController;

    @Mock
    private SeatService seatService;
    private MockMvc mockMvc;
    private Response response = new Response();

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
        mockMvc = MockMvcBuilders.standaloneSetup(seatController).build();
    }

    @Test
    public void testHome() throws Exception {
        mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/seatservice/welcome"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andExpect(MockMvcResultMatchers.content().string("Welcome to [ Seat Service ] !"));
    }

    @Test
    public void testCreate() throws Exception {
        Seat seatRequest = new Seat();
        Mockito.when(seatService.distributeSeat(Mockito.any(Seat.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(seatRequest);
        String result = mockMvc.perform(MockMvcRequestBuilders.post("/api/v1/seatservice/seats").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testGetLeftTicketOfInterval() throws Exception {
        Seat seatRequest = new Seat();
        Mockito.when(seatService.getLeftTicketOfInterval(Mockito.any(Seat.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(seatRequest);
        String result = mockMvc.perform(MockMvcRequestBuilders.post("/api/v1/seatservice/seats/left_tickets").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

}


// Node: testGetLeftTicketOfInterval
package seat.service;

import edu.fudan.common.util.Response;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.*;
import org.springframework.web.client.RestTemplate;
import edu.fudan.common.entity.*;

import java.util.ArrayList;

@RunWith(JUnit4.class)
public class SeatServiceImplTest {

    @InjectMocks
    private SeatServiceImpl seatServiceImpl;

    @Mock
    private RestTemplate restTemplate;

    private HttpHeaders headers = new HttpHeaders();

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
    }

    @Test
    public void testDistributeSeat1() {
        Seat seat = new Seat();
        seat.setTrainNumber("G");
        seat.setSeatType(2);
        seat.setStartStation("start_station");
        seat.setDestStation("dest_station");

        Route route = new Route();
        route.setStations(new ArrayList<>());
        Response<Route> response1 = new Response<>(null, null, route);
        ResponseEntity<Response<Route>> re1 = new ResponseEntity<>(response1, HttpStatus.OK);

        Response<LeftTicketInfo> response2 = new Response<>();
        ResponseEntity<Response<LeftTicketInfo>> re2 = new ResponseEntity<>(response2, HttpStatus.OK);

        TrainType trainType = new TrainType();
        trainType.setConfortClass(1);
        Response<TrainType> response3 = new Response<>(null, null, trainType);
        ResponseEntity<Response<TrainType>> re3 = new ResponseEntity<>(response3, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                Mockito.anyString(),
                Mockito.any(HttpMethod.class),
                Mockito.any(HttpEntity.class),
                Mockito.any(ParameterizedTypeReference.class)))
                .thenReturn(re1).thenReturn(re2).thenReturn(re3);
        Response result = seatServiceImpl.distributeSeat(seat, headers);
        Assert.assertEquals("Use a new seat number!", result.getMsg());
    }

    @Test
    public void testDistributeSeat2() {
        Seat seat = new Seat();
        seat.setTrainNumber("K");
        seat.setSeatType(3);
        seat.setStartStation("start_station");
        seat.setDestStation("dest_station");

        Route route = new Route();
        route.setStations(new ArrayList<>());
        Response<Route> response1 = new Response<>(null, null, route);
        ResponseEntity<Response<Route>> re1 = new ResponseEntity<>(response1, HttpStatus.OK);

        Response<LeftTicketInfo> response2 = new Response<>();
        ResponseEntity<Response<LeftTicketInfo>> re2 = new ResponseEntity<>(response2, HttpStatus.OK);

        TrainType trainType = new TrainType();
        trainType.setEconomyClass(1);
        Response<TrainType> response3 = new Response<>(null, null, trainType);
        ResponseEntity<Response<TrainType>> re3 = new ResponseEntity<>(response3, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                Mockito.anyString(),
                Mockito.any(HttpMethod.class),
                Mockito.any(HttpEntity.class),
                Mockito.any(ParameterizedTypeReference.class)))
                .thenReturn(re1).thenReturn(re2).thenReturn(re3);
        Response result = seatServiceImpl.distributeSeat(seat, headers);
        Assert.assertEquals("Use a new seat number!", result.getMsg());
    }

    @Test
    public void testGetLeftTicketOfInterval() {
        Seat seat = new Seat();
        seat.setTrainNumber("G");
        seat.setSeatType(2);
        seat.setStartStation("start_station");
        seat.setDestStation("dest_station");

        Route route = new Route();
        route.setStations( new ArrayList<String>(){{ add("start_place"); }} );
        Response<Route> response1 = new Response<>(null, null, route);
        ResponseEntity<Response<Route>> re1 = new ResponseEntity<>(response1, HttpStatus.OK);

        Response<LeftTicketInfo> response2 = new Response<>();
        ResponseEntity<Response<LeftTicketInfo>> re2 = new ResponseEntity<>(response2, HttpStatus.OK);

        TrainType trainType = new TrainType();
        trainType.setConfortClass(1);
        Response<TrainType> response3 = new Response<>(null, null, trainType);
        ResponseEntity<Response<TrainType>> re3 = new ResponseEntity<>(response3, HttpStatus.OK);

        Config config = new Config();
        config.setValue("0");
        Response<Config> response4 = new Response<>(null, null, config);
        ResponseEntity<Response<Config>> re4 = new ResponseEntity<>(response4, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                Mockito.anyString(),
                Mockito.any(HttpMethod.class),
                Mockito.any(HttpEntity.class),
                Mockito.any(ParameterizedTypeReference.class)))
                .thenReturn(re1).thenReturn(re2).thenReturn(re3).thenReturn(re4);
        Response result = seatServiceImpl.getLeftTicketOfInterval(seat, headers);
        Assert.assertEquals(new Response<>(1, "Get Left Ticket of Internal Success", 1), result);
    }

    @Test
    public void testGetLeftTicketOfInterva2() {
        Seat seat = new Seat();
        seat.setTrainNumber("K");
        seat.setSeatType(3);
        seat.setStartStation("start_station");
        seat.setDestStation("dest_station");

        Route route = new Route();
        route.setStations( new ArrayList<String>(){{ add("start_place"); }} );
        Response<Route> response1 = new Response<>(null, null, route);
        ResponseEntity<Response<Route>> re1 = new ResponseEntity<>(response1, HttpStatus.OK);

        Response<LeftTicketInfo> response2 = new Response<>();
        ResponseEntity<Response<LeftTicketInfo>> re2 = new ResponseEntity<>(response2, HttpStatus.OK);

        TrainType trainType = new TrainType();
        trainType.setEconomyClass(1);
        Response<TrainType> response3 = new Response<>(null, null, trainType);
        ResponseEntity<Response<TrainType>> re3 = new ResponseEntity<>(response3, HttpStatus.OK);

        Config config = new Config();
        config.setValue("0");
        Response<Config> response4 = new Response<>(null, null, config);
        ResponseEntity<Response<Config>> re4 = new ResponseEntity<>(response4, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                Mockito.anyString(),
                Mockito.any(HttpMethod.class),
                Mockito.any(HttpEntity.class),
                Mockito.any(ParameterizedTypeReference.class)))
                .thenReturn(re1).thenReturn(re2).thenReturn(re3).thenReturn(re4);
        Response result = seatServiceImpl.getLeftTicketOfInterval(seat, headers);
        Assert.assertEquals(new Response<>(1, "Get Left Ticket of Internal Success", 1), result);
    }

}


package security;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;
import org.springframework.cloud.client.loadbalancer.LoadBalanced;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.EnableAspectJAutoProxy;
import org.springframework.integration.annotation.IntegrationComponentScan;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.web.client.RestTemplate;
import springfox.documentation.swagger2.annotations.EnableSwagger2;

/**
 * @author fdse
 */
@SpringBootApplication
@EnableAspectJAutoProxy(proxyTargetClass = true)
@EnableAsync
@IntegrationComponentScan
@EnableSwagger2
@EnableDiscoveryClient
public class SecurityApplication {

    public static void main(String[] args) {
        SpringApplication.run(SecurityApplication.class, args);
    }

    @LoadBalanced
    @Bean
    public RestTemplate restTemplate(RestTemplateBuilder builder) {
        return builder.build();
    }

}


package security.controller;

import com.alibaba.fastjson.JSONObject;
import edu.fudan.common.util.Response;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.springframework.http.*;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.request.MockMvcRequestBuilders;
import org.springframework.test.web.servlet.result.MockMvcResultMatchers;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import security.entity.SecurityConfig;
import security.service.SecurityService;

@RunWith(JUnit4.class)
public class SecurityControllerTest {

    @InjectMocks
    private SecurityController securityController;

    @Mock
    private SecurityService securityService;
    private MockMvc mockMvc;
    private Response response = new Response();

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
        mockMvc = MockMvcBuilders.standaloneSetup(securityController).build();
    }

    @Test
    public void testHome() throws Exception {
        mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/securityservice/welcome"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andExpect(MockMvcResultMatchers.content().string("welcome to [Security Service]"));
    }

    @Test
    public void testFindAllSecurityConfig() throws Exception {
        Mockito.when(securityService.findAllSecurityConfig(Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/securityservice/securityConfigs"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testCreate() throws Exception {
        SecurityConfig info = new SecurityConfig();
        Mockito.when(securityService.addNewSecurityConfig(Mockito.any(SecurityConfig.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(info);
        String result = mockMvc.perform(MockMvcRequestBuilders.post("/api/v1/securityservice/securityConfigs").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testUpdate() throws Exception {
        SecurityConfig info = new SecurityConfig();
        Mockito.when(securityService.modifySecurityConfig(Mockito.any(SecurityConfig.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(info);
        String result = mockMvc.perform(MockMvcRequestBuilders.put("/api/v1/securityservice/securityConfigs").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testDelete() throws Exception {
        Mockito.when(securityService.deleteSecurityConfig(Mockito.anyString(), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.delete("/api/v1/securityservice/securityConfigs/id"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testCheck() throws Exception {
        Mockito.when(securityService.check(Mockito.anyString(), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/securityservice/securityConfigs/account_id"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

}


// Node: testFindAllSecurityConfig
// Node: testCheck
package security.service;

import edu.fudan.common.entity.OrderSecurity;
import edu.fudan.common.util.Response;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.*;
import org.springframework.web.client.RestTemplate;
import security.entity.SecurityConfig;
import security.repository.SecurityRepository;

import java.util.ArrayList;
import java.util.Optional;
import java.util.UUID;

@RunWith(JUnit4.class)
public class SecurityServiceImplTest {

    @InjectMocks
    private SecurityServiceImpl securityServiceImpl;

    @Mock
    private SecurityRepository securityRepository;

    @Mock
    private RestTemplate restTemplate;

    private HttpHeaders headers = new HttpHeaders();

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
    }

    @Test
    public void testFindAllSecurityConfig1() {
        ArrayList<SecurityConfig> securityConfigs = new ArrayList<>();
        securityConfigs.add(new SecurityConfig());
        Mockito.when(securityRepository.findAll()).thenReturn(securityConfigs);
        Response result = securityServiceImpl.findAllSecurityConfig(headers);
        Assert.assertEquals(new Response<>(1, "Success", securityConfigs), result);
    }

    @Test
    public void testFindAllSecurityConfig2() {
        Mockito.when(securityRepository.findAll()).thenReturn(null);
        Response result = securityServiceImpl.findAllSecurityConfig(headers);
        Assert.assertEquals(new Response<>(0, "No Content", null), result);
    }

    @Test
    public void testAddNewSecurityConfig1() {
        SecurityConfig sc = new SecurityConfig();
        Mockito.when(securityRepository.findByName(Mockito.anyString())).thenReturn(sc);
        Response result = securityServiceImpl.addNewSecurityConfig(sc, headers);
        Assert.assertEquals(new Response<>(0, "Security Config Already Exist", null), result);
    }

    @Test
    public void testAddNewSecurityConfig2() {
        SecurityConfig sc = new SecurityConfig();
        Mockito.when(securityRepository.findByName(Mockito.anyString())).thenReturn(null);
        Mockito.when(securityRepository.save(Mockito.any(SecurityConfig.class))).thenReturn(null);
        Response result = securityServiceImpl.addNewSecurityConfig(sc, headers);
        Assert.assertEquals("Success", result.getMsg());
    }

    @Test
    public void testModifySecurityConfig1() {
        SecurityConfig sc = new SecurityConfig();
        Mockito.when(securityRepository.findById(Mockito.any(UUID.class).toString())).thenReturn(null);
        Response result = securityServiceImpl.modifySecurityConfig(sc, headers);
        Assert.assertEquals(new Response<>(0, "Security Config Not Exist", null), result);
    }

    @Test
    public void testModifySecurityConfig2() {
        SecurityConfig sc = new SecurityConfig();
        Mockito.when(securityRepository.findById(Mockito.any(UUID.class).toString())).thenReturn(Optional.of(sc));
        Mockito.when(securityRepository.save(Mockito.any(SecurityConfig.class))).thenReturn(null);
        Response result = securityServiceImpl.modifySecurityConfig(sc, headers);
        Assert.assertEquals(new Response<>(1, "Success", sc), result);
    }

    @Test
    public void testDeleteSecurityConfig1() {
        UUID id = UUID.randomUUID();
        Mockito.doNothing().doThrow(new RuntimeException()).when(securityRepository).deleteById(Mockito.any(UUID.class).toString());
        Mockito.when(securityRepository.findById(Mockito.any(UUID.class).toString())).thenReturn(null);
        Response result = securityServiceImpl.deleteSecurityConfig(id.toString(), headers);
        Assert.assertEquals(new Response<>(1, "Success", id.toString()), result);
    }

    @Test
    public void testDeleteSecurityConfig2() {
        UUID id = UUID.randomUUID();
        SecurityConfig sc = new SecurityConfig();
        Mockito.doNothing().doThrow(new RuntimeException()).when(securityRepository).deleteById(Mockito.any(UUID.class).toString());
        Mockito.when(securityRepository.findById(Mockito.any(UUID.class).toString())).thenReturn(Optional.of(sc));
        Response result = securityServiceImpl.deleteSecurityConfig(id.toString(), headers);
        Assert.assertEquals("Reason Not clear", result.getMsg());
    }

    @Test
    public void testCheck() {
        //mock getSecurityOrderInfoFromOrder() and getSecurityOrderOtherInfoFromOrder()
        OrderSecurity orderSecurity = new OrderSecurity(1, 1);
        Response<OrderSecurity> response1 = new Response<>(null, null, orderSecurity);
        ResponseEntity<Response<OrderSecurity>> re1 = new ResponseEntity<>(response1, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                Mockito.anyString(),
                Mockito.any(HttpMethod.class),
                Mockito.any(HttpEntity.class),
                Mockito.any(ParameterizedTypeReference.class)))
                .thenReturn(re1);

        SecurityConfig securityConfig = new SecurityConfig();
        securityConfig.setValue("2");
        Mockito.when(securityRepository.findByName(Mockito.anyString())).thenReturn(securityConfig);
        Response result = securityServiceImpl.check("account_id", headers);
        Assert.assertEquals(new Response<>(1, "Success.r", "account_id"), result);
    }

}


package food_delivery;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;
import org.springframework.cloud.client.loadbalancer.LoadBalanced;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.EnableAspectJAutoProxy;
import org.springframework.integration.annotation.IntegrationComponentScan;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.web.client.RestTemplate;
import springfox.documentation.swagger2.annotations.EnableSwagger2;

@SpringBootApplication
@EnableAspectJAutoProxy(proxyTargetClass = true)
@EnableAsync
@IntegrationComponentScan
@EnableSwagger2
@EnableDiscoveryClient
public class FoodDeliveryApplication {

    public static void main(String[] args) {
        SpringApplication.run(FoodDeliveryApplication.class, args);
    }

    @LoadBalanced
    @Bean
    public RestTemplate restTemplate(RestTemplateBuilder builder) {
        return builder.build();
    }
}


package food_delivery.controller;

import com.alibaba.fastjson.JSONObject;
import edu.fudan.common.util.Response;
import food_delivery.entity.DeliveryInfo;
import food_delivery.entity.FoodDeliveryOrder;
import food_delivery.entity.SeatInfo;
import food_delivery.entity.TripOrderInfo;
import food_delivery.service.FoodDeliveryService;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.request.MockMvcRequestBuilders;
import org.springframework.test.web.servlet.result.MockMvcResultMatchers;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

@RunWith(JUnit4.class)
public class FoodDeliveryControllerTest {

    @InjectMocks
    private FoodDeliveryController foodDeliveryController;

    @Mock
    private FoodDeliveryService foodDeliveryService;
    private MockMvc mockMvc;
    private Response response = new Response();

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
        mockMvc = MockMvcBuilders.standaloneSetup(foodDeliveryController).build();
    }

    @Test
    public void testHome() throws Exception {
        mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/fooddeliveryservice/welcome"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andExpect(MockMvcResultMatchers.content().string("Welcome to [ food delivery service ] !"));
    }

    @Test
    public void testCreateFoodDeliveryOrder() throws Exception {
        FoodDeliveryOrder foodDeliveryOrder = new FoodDeliveryOrder();
        Mockito.when(foodDeliveryService.createFoodDeliveryOrder(Mockito.any(FoodDeliveryOrder.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(foodDeliveryOrder);
        String result = mockMvc.perform(MockMvcRequestBuilders.post("/api/v1/fooddeliveryservice/orders").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testDeleteFoodDeliveryOrder() throws Exception {
        Mockito.when(foodDeliveryService.deleteFoodDeliveryOrder(Mockito.anyString(), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.delete("/api/v1/fooddeliveryservice/orders/d/123"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testGetFoodDeliveryOrderById() throws Exception {
        Mockito.when(foodDeliveryService.getFoodDeliveryOrderById(Mockito.anyString(), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/fooddeliveryservice/orders/123"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testGetFoodDeliveryOrderByStoreId() throws Exception {
        Mockito.when(foodDeliveryService.getFoodDeliveryOrderByStoreId(Mockito.anyString(), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/fooddeliveryservice/orders/store/1234"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testGetAllFoodDeliveryOrders() throws Exception {
        Mockito.when(foodDeliveryService.getAllFoodDeliveryOrders(Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/fooddeliveryservice/orders/all"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testUpdateTripId() throws Exception {
        TripOrderInfo tripOrderInfo = new TripOrderInfo();
        Mockito.when(foodDeliveryService.updateTripId(Mockito.any(TripOrderInfo.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(tripOrderInfo);
        String result = mockMvc.perform(MockMvcRequestBuilders.put("/api/v1/fooddeliveryservice/orders/tripid").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testUpdateSeatNo() throws Exception {
        SeatInfo seatInfo = new SeatInfo();
        Mockito.when(foodDeliveryService.updateSeatNo(Mockito.any(SeatInfo.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(seatInfo);
        String result = mockMvc.perform(MockMvcRequestBuilders.put("/api/v1/fooddeliveryservice/orders/seatno").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testUpdateDeliveryTime() throws Exception {
        DeliveryInfo deliveryInfo = new DeliveryInfo();
        Mockito.when(foodDeliveryService.updateDeliveryTime(Mockito.any(DeliveryInfo.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(deliveryInfo);
        String result = mockMvc.perform(MockMvcRequestBuilders.put("/api/v1/fooddeliveryservice/orders/dtime").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

}


// Node: testCreateFoodDeliveryOrder
// Node: testDeleteFoodDeliveryOrder
// Node: testGetFoodDeliveryOrderById
// Node: testGetFoodDeliveryOrderByStoreId
// Node: testGetAllFoodDeliveryOrders
// Node: testUpdateTripId
// Node: TripOrderInfo
// Node: testUpdateSeatNo
// Node: SeatInfo
// Node: testUpdateDeliveryTime
// Node: DeliveryInfo
package food_delivery.service;

import org.junit.Before;
import org.junit.Test;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;
import org.springframework.http.*;
import org.springframework.web.client.RestTemplate;

public class FoodDeliveryServiceImplTest {
    @InjectMocks
    private FoodDeliveryServiceImpl foodDeliveryServiceImpl;

    @Mock
    private RestTemplate restTemplate;

    private HttpHeaders headers = new HttpHeaders();
    private HttpEntity requestEntity = new HttpEntity(headers);

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
    }

}


package contacts;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;
import org.springframework.cloud.client.loadbalancer.LoadBalanced;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.EnableAspectJAutoProxy;
import org.springframework.integration.annotation.IntegrationComponentScan;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.web.client.RestTemplate;
import springfox.documentation.swagger2.annotations.EnableSwagger2;

/**
 * @author fdse
 */
@SpringBootApplication
@EnableAspectJAutoProxy(proxyTargetClass = true)
@EnableAsync
@IntegrationComponentScan
@EnableSwagger2
@EnableDiscoveryClient
public class ContactsApplication {

    public static void main(String[] args) {
        SpringApplication.run(ContactsApplication.class, args);
    }

    @LoadBalanced
    @Bean
    public RestTemplate restTemplate(RestTemplateBuilder builder) {
        return builder.build();
    }
}


package contacts.controller;

import com.alibaba.fastjson.JSONObject;
import contacts.entity.Contacts;
import contacts.service.ContactsService;
import edu.fudan.common.util.Response;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.springframework.http.*;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.request.MockMvcRequestBuilders;
import org.springframework.test.web.servlet.result.MockMvcResultMatchers;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

import java.util.UUID;

@RunWith(JUnit4.class)
public class ContactsControllerTest {

    @InjectMocks
    private ContactsController contactsController;

    @Mock
    private ContactsService contactsService;
    private MockMvc mockMvc;
    private Response response = new Response();

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
        mockMvc = MockMvcBuilders.standaloneSetup(contactsController).build();
    }

    @Test
    public void testHome() throws Exception {
        mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/contactservice/contacts/welcome"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andExpect(MockMvcResultMatchers.content().string("Welcome to [ Contacts Service ] !"));
    }

    @Test
    public void testGetAllContacts() throws Exception {
        Mockito.when(contactsService.getAllContacts(Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/contactservice/contacts"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testCreateNewContacts() throws Exception {
        Contacts aci = new Contacts();
        Mockito.when(contactsService.create(Mockito.any(Contacts.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(aci);
        String result = mockMvc.perform(MockMvcRequestBuilders.post("/api/v1/contactservice/contacts").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isCreated())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testCreateNewContactsAdmin() throws Exception {
        Contacts aci = new Contacts();
        Mockito.when(contactsService.createContacts(Mockito.any(Contacts.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(aci);
        String result = mockMvc.perform(MockMvcRequestBuilders.post("/api/v1/contactservice/contacts/admin").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isCreated())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testDeleteContacts() throws Exception {
        UUID contactsId = UUID.randomUUID();
        Mockito.when(contactsService.delete(Mockito.any(UUID.class).toString(), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.delete("/api/v1/contactservice/contacts/" + contactsId.toString()))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testModifyContacts() throws Exception {
        Contacts info = new Contacts();
        Mockito.when(contactsService.modify(Mockito.any(Contacts.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(info);
        String result = mockMvc.perform(MockMvcRequestBuilders.put("/api/v1/contactservice/contacts").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testFindContactsByAccountId() throws Exception {
        UUID accountId = UUID.randomUUID();
        Mockito.when(contactsService.findContactsByAccountId(Mockito.any(UUID.class).toString(), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/contactservice/contacts/account/" + accountId.toString()))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testGetContactsByContactsId() throws Exception {
        UUID id = UUID.randomUUID();
        Mockito.when(contactsService.findContactsById(Mockito.any(UUID.class).toString(), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/contactservice/contacts/" + id.toString()))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

}


// Node: testCreateNewContacts
// Node: testCreateNewContactsAdmin
// Node: testFindContactsByAccountId
// Node: testGetContactsByContactsId
package contacts.service;

import contacts.entity.Contacts;
import contacts.repository.ContactsRepository;
import edu.fudan.common.util.Response;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.springframework.http.HttpHeaders;

import java.util.ArrayList;
import java.util.Optional;
import java.util.UUID;

@RunWith(JUnit4.class)
public class ContactsServiceImplTest {

    @InjectMocks
    private ContactsServiceImpl contactsServiceImpl;

    @Mock
    private ContactsRepository contactsRepository;

    private HttpHeaders headers = new HttpHeaders();

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
    }

    @Test
    public void testFindContactsById1() {
        UUID id = UUID.randomUUID();
        Contacts contacts = new Contacts();
        Mockito.when(contactsRepository.findById(Mockito.any(UUID.class).toString())).thenReturn(Optional.of(contacts));
        Response result = contactsServiceImpl.findContactsById(id.toString(), headers);
        Assert.assertEquals(new Response<>(1, "Success", contacts), result);
    }

    @Test
    public void testFindContactsById2() {
        UUID id = UUID.randomUUID();
        Mockito.when(contactsRepository.findById(Mockito.any(UUID.class).toString())).thenReturn(Optional.empty());
        Response result = contactsServiceImpl.findContactsById(id.toString(), headers);
        Assert.assertEquals(new Response<>(0, "No contacts according to contacts id", null), result);
    }

    @Test
    public void testFindContactsByAccountId() {
        UUID accountId = UUID.randomUUID();
        ArrayList<Contacts> arr = new ArrayList<>();
        Mockito.when(contactsRepository.findByAccountId(Mockito.any(UUID.class).toString())).thenReturn(arr);
        Response result = contactsServiceImpl.findContactsByAccountId(accountId.toString(), headers);
        Assert.assertEquals(new Response<>(1, "Success", arr), result);
    }

    @Test
    public void testCreateContacts1() {
        Contacts contacts = new Contacts();
        Mockito.when(contactsRepository.findById(Mockito.any(UUID.class).toString())).thenReturn(Optional.of(contacts));
        Response result = contactsServiceImpl.createContacts(contacts, headers);
        Assert.assertEquals(new Response<>(0, "Already Exists", contacts), result);
    }

    @Test
    public void testCreateContacts2() {
        Contacts contacts = new Contacts();
        Mockito.when(contactsRepository.findById(Mockito.any(UUID.class).toString())).thenReturn(Optional.empty());
        Mockito.when(contactsRepository.save(Mockito.any(Contacts.class))).thenReturn(null);
        Response result = contactsServiceImpl.createContacts(contacts, headers);
        Assert.assertEquals(new Response<>(1, "Create Success", null), result);
    }

    @Test
    public void testCreate1() {
        Contacts addContacts = new Contacts(UUID.randomUUID().toString(), UUID.randomUUID().toString(), "name", 1, "12", "10001");
        ArrayList<Contacts> accountContacts = new ArrayList<>();
        accountContacts.add(addContacts);
        Mockito.when(contactsRepository.findByAccountId(Mockito.any(UUID.class).toString())).thenReturn(accountContacts);
        Response result = contactsServiceImpl.create(addContacts, headers);
        Assert.assertEquals(new Response<>(0, "Contacts already exists", null), result);
    }

    @Test
    public void testCreate2() {
        Contacts addContacts = new Contacts(UUID.randomUUID().toString(), UUID.randomUUID().toString(), "name", 1, "12", "10001");
        ArrayList<Contacts> accountContacts = new ArrayList<>();
        Mockito.when(contactsRepository.findByAccountId(Mockito.any(UUID.class).toString())).thenReturn(accountContacts);
        Mockito.when(contactsRepository.save(Mockito.any(Contacts.class))).thenReturn(null);
        Response result = contactsServiceImpl.create(addContacts, headers);
        Assert.assertEquals(new Response<>(1, "Create contacts success", addContacts), result);
    }

    @Test
    public void testDelete1() {
        UUID contactsId = UUID.randomUUID();
        Mockito.doNothing().doThrow(new RuntimeException()).when(contactsRepository).deleteById(Mockito.any(UUID.class).toString());
        Mockito.when(contactsRepository.findById(Mockito.any(UUID.class).toString())).thenReturn(Optional.empty());
        Response result = contactsServiceImpl.delete(contactsId.toString(), headers);
        Assert.assertEquals(new Response<>(1, "Delete success", contactsId), result);
    }

    @Test
    public void testDelete2() {
        UUID contactsId = UUID.randomUUID();
        Contacts contacts = new Contacts();
        Mockito.doNothing().doThrow(new RuntimeException()).when(contactsRepository).deleteById(Mockito.any(UUID.class).toString());
        Mockito.when(contactsRepository.findById(Mockito.any(UUID.class).toString())).thenReturn(Optional.of(contacts));
        Response result = contactsServiceImpl.delete(contactsId.toString(), headers);
        Assert.assertEquals(new Response<>(0, "Delete failed", contactsId), result);
    }

    @Test
    public void testModify1() {
        Contacts contacts = new Contacts(UUID.randomUUID().toString(), UUID.randomUUID().toString(), "name", 1, "12", "10001");
        Mockito.when(contactsRepository.findById(Mockito.any(UUID.class).toString())).thenReturn(Optional.empty());
        Response result = contactsServiceImpl.modify(contacts, headers);
        Assert.assertEquals(new Response<>(0, "Contacts not found", null), result);
    }

    @Test
    public void testModify2() {
        Contacts contacts = new Contacts(UUID.randomUUID().toString(), UUID.randomUUID().toString(), "name", 1, "12", "10001");
        Mockito.when(contactsRepository.findById(Mockito.any(UUID.class).toString())).thenReturn(Optional.of(contacts));
        Mockito.when(contactsRepository.save(Mockito.any(Contacts.class))).thenReturn(null);
        Response result = contactsServiceImpl.modify(contacts, headers);
        Assert.assertEquals(new Response<>(1, "Modify success", contacts), result);
    }

    @Test
    public void testGetAllContacts1() {
        ArrayList<Contacts> contacts = new ArrayList<>();
        contacts.add(new Contacts());
        Mockito.when(contactsRepository.findAll()).thenReturn(contacts);
        Response result = contactsServiceImpl.getAllContacts(headers);
        Assert.assertEquals(new Response<>(1, "Success", contacts), result);
    }

    @Test
    public void testGetAllContacts2() {
        Mockito.when(contactsRepository.findAll()).thenReturn(null);
        Response result = contactsServiceImpl.getAllContacts(headers);
        Assert.assertEquals(new Response<>(0, "No content", null), result);
    }

}


package preserveOther;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;
import org.springframework.cloud.client.loadbalancer.LoadBalanced;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.EnableAspectJAutoProxy;
import org.springframework.integration.annotation.IntegrationComponentScan;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.web.client.RestTemplate;
import springfox.documentation.swagger2.annotations.EnableSwagger2;

/**
 * @author fdse
 */
@SpringBootApplication
@EnableAspectJAutoProxy(proxyTargetClass = true)
@EnableAsync
@IntegrationComponentScan
@EnableSwagger2
@EnableDiscoveryClient
public class PreserveOtherApplication {
    public static void main(String[] args) {

        SpringApplication.run(PreserveOtherApplication.class, args);
    }

    @LoadBalanced
    @Bean
    public RestTemplate restTemplate(RestTemplateBuilder builder) {
        return builder.build();
    }

}


package preserveOther.service;

import edu.fudan.common.entity.OrderTicketsInfo;
import edu.fudan.common.util.Response;
import org.springframework.http.HttpHeaders;


/**
 * @author fdse
 */
public interface PreserveOtherService {

    Response preserve(OrderTicketsInfo oti, HttpHeaders headers);
}


// Node: repos/cloned_ms_repos/train-ticket/ts-preserve-other-service/src/main/java/preserveOther/service/PreserveOtherService.java:PreserveOtherService.<init>
package preserveOther.controller;

import com.alibaba.fastjson.JSONObject;
import edu.fudan.common.util.Response;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.springframework.http.*;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.request.MockMvcRequestBuilders;
import org.springframework.test.web.servlet.result.MockMvcResultMatchers;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import edu.fudan.common.entity.OrderTicketsInfo;
import preserveOther.service.PreserveOtherService;

@RunWith(JUnit4.class)
public class PreserveOtherControllerTest {

    @InjectMocks
    private PreserveOtherController preserveOtherController;

    @Mock
    private PreserveOtherService preserveService;
    private MockMvc mockMvc;
    private Response response = new Response();

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
        mockMvc = MockMvcBuilders.standaloneSetup(preserveOtherController).build();
    }

    @Test
    public void testHome() throws Exception {
        mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/preserveotherservice/welcome"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andExpect(MockMvcResultMatchers.content().string("Welcome to [ PreserveOther Service ] !"));
    }

    @Test
    public void testPreserve() throws Exception {
        OrderTicketsInfo oti = new OrderTicketsInfo();
        Mockito.when(preserveService.preserve(Mockito.any(OrderTicketsInfo.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(oti);
        String result = mockMvc.perform(MockMvcRequestBuilders.post("/api/v1/preserveotherservice/preserveOther").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

}


package preserveOther.service;

import edu.fudan.common.util.Response;
import edu.fudan.common.util.StringUtils;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.*;
import org.springframework.web.client.RestTemplate;
import edu.fudan.common.entity.*;

import java.util.Date;
import java.util.HashMap;
import java.util.UUID;

@RunWith(JUnit4.class)
public class PreserveOtherServiceImplTest {

    @InjectMocks
    private PreserveOtherServiceImpl preserveOtherServiceImpl;

    @Mock
    private RestTemplate restTemplate;

    private HttpHeaders headers = new HttpHeaders();
    private HttpEntity requestEntity = new HttpEntity(headers);

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
    }

    @Test
    public void testPreserve() {
        OrderTicketsInfo oti = OrderTicketsInfo.builder()
                .accountId(UUID.randomUUID().toString())
                .contactsId(UUID.randomUUID().toString())
                .from("from_station")
                .to("to_station")
                .date(StringUtils.Date2String(new Date()))
                .handleDate("handle_date")
                .tripId("G1255")
                .seatType(2)
                .assurance(1)
                .foodType(1)
                .foodName("food_name")
                .foodPrice(1.0)
                .stationName("station_name")
                .storeName("store_name")
                .consigneeName("consignee_name")
                .consigneePhone("123456789")
                .consigneeWeight(1.0)
                .isWithin(true)
                .build();

        //response for checkSecurity()、createFoodOrder()、createConsign()
        Response response1 = new Response<>(1, null, null);
        ResponseEntity<Response> re1 = new ResponseEntity<>(response1, HttpStatus.OK);

        //response for sendEmail()
        ResponseEntity<Boolean> re10 = new ResponseEntity<>(true, HttpStatus.OK);

        Mockito.when(restTemplate.exchange(
                Mockito.anyString(),
                Mockito.any(HttpMethod.class),
                Mockito.any(HttpEntity.class),
                Mockito.any(Class.class)))
                .thenReturn(re1).thenReturn(re1).thenReturn(re1).thenReturn(re10);


        //response for getContactsById()
        Contacts contacts = new Contacts();
        contacts.setDocumentNumber("document_number");
        contacts.setName("name");
        contacts.setDocumentType(1);
        Response<Contacts> response2 = new Response<>(1, null, contacts);
        ResponseEntity<Response<Contacts>> re2 = new ResponseEntity<>(response2, HttpStatus.OK);

        //response for getTripAllDetailInformation()
        TripResponse tripResponse = new TripResponse();
        tripResponse.setConfortClass(1);
        tripResponse.setStartTime(StringUtils.Date2String(new Date()));
        TripAllDetail tripAllDetail = new TripAllDetail(true, "message", tripResponse, new Trip());
        Response<TripAllDetail> response3 = new Response<>(1, null, tripAllDetail);
        ResponseEntity<Response<TripAllDetail>> re3 = new ResponseEntity<>(response3, HttpStatus.OK);

        //response for queryForStationId()
        Response<String> response4 = new Response<>(null, null, "");
        ResponseEntity<Response<String>> re4 = new ResponseEntity<>(response4, HttpStatus.OK);

        //response for travel result
        TravelResult travelResult = new TravelResult();
        travelResult.setPrices( new HashMap<String, String>(){{ put("confortClass", "1.0"); }} );
        Response<TravelResult> response5 = new Response<>(null, null, travelResult);
        ResponseEntity<Response<TravelResult>> re5 = new ResponseEntity<>(response5, HttpStatus.OK);

        //response for dipatchSeat()
        Ticket ticket = new Ticket();
        ticket.setSeatNo(1);
        Response<Ticket> response6 = new Response<>(null, null, ticket);
        ResponseEntity<Response<Ticket>> re6 = new ResponseEntity<>(response6, HttpStatus.OK);

        //response for createOrder()
        Order order = new Order();
        order.setId(UUID.randomUUID().toString());
        order.setAccountId(UUID.randomUUID().toString());
        order.setTravelDate(StringUtils.Date2String(new Date()));
        order.setFrom("from_station");
        order.setTo("to_station");
        Response<Order> response7 = new Response<>(1, null, order);
        ResponseEntity<Response<Order>> re7 = new ResponseEntity<>(response7, HttpStatus.OK);

        //response for addAssuranceForOrder()
        Response<Assurance> response8 = new Response<>(1, null, null);
        ResponseEntity<Response<Assurance>> re8 = new ResponseEntity<>(response8, HttpStatus.OK);

        //response for getAccount()
        User user = new User();
        user.setEmail("email");
        user.setUserName("user_name");
        Response<User> response9 = new Response<>(1, null, user);
        ResponseEntity<Response<User>> re9 = new ResponseEntity<>(response9, HttpStatus.OK);

        Mockito.when(restTemplate.exchange(
                Mockito.anyString(),
                Mockito.any(HttpMethod.class),
                Mockito.any(HttpEntity.class),
                Mockito.any(ParameterizedTypeReference.class)))
                .thenReturn(re2).thenReturn(re3).thenReturn(re4).thenReturn(re4).thenReturn(re5).thenReturn(re6).thenReturn(re7).thenReturn(re8).thenReturn(re9);

        Response result = preserveOtherServiceImpl.preserve(oti, headers);
        Assert.assertEquals(new Response<>(1, "Success.", null), result);
    }

    @Test
    public void testDipatchSeat() {
        long mills = System.currentTimeMillis();
        Seat seatRequest = new Seat(StringUtils.Date2String(new Date()), "G1234", "start_station", "dest_station", 2, 100, null);
        HttpEntity requestEntityTicket = new HttpEntity<>(seatRequest, headers);
        Response<Ticket> response = new Response<>();
        ResponseEntity<Response<Ticket>> reTicket = new ResponseEntity<>(response, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                "http://ts-seat-service:18898/api/v1/seatservice/seats",
                HttpMethod.POST,
                requestEntityTicket,
                new ParameterizedTypeReference<Response<Ticket>>() {
                })).thenReturn(reTicket);
        Ticket result = preserveOtherServiceImpl.dipatchSeat(StringUtils.Date2String(new Date()), "G1234", "start_station", "dest_station", 2, 100, null, headers);
        Assert.assertNull(result);
    }

    @Test
    public void testSendEmail() {
        NotifyInfo notifyInfo = new NotifyInfo();
        HttpEntity requestEntitySendEmail = new HttpEntity<>(notifyInfo, headers);
        ResponseEntity<Boolean> reSendEmail = new ResponseEntity<>(true, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                "http://ts-notification-service:17853/api/v1/notifyservice/notification/preserve_success",
                HttpMethod.POST,
                requestEntitySendEmail,
                Boolean.class)).thenReturn(reSendEmail);
        boolean result = preserveOtherServiceImpl.sendEmail(notifyInfo, headers);
        Assert.assertTrue(result);
    }

    @Test
    public void testGetAccount() {
        Response<User> response = new Response<>();
        ResponseEntity<Response<User>> re = new ResponseEntity<>(response, HttpStatus.OK);
        Mockito.when(restTemplate.exchange(
                "http://ts-user-service:12342/api/v1/userservice/users/id/1",
                HttpMethod.GET,
                requestEntity,
                new ParameterizedTypeReference<Response<User>>() {
                })).thenReturn(re);
        User result = preserveOtherServiceImpl.getAccount("1", headers);
        Assert.assertNull(result);
    }

}


package food;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;
import org.springframework.cloud.client.loadbalancer.LoadBalanced;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.EnableAspectJAutoProxy;
import org.springframework.integration.annotation.IntegrationComponentScan;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.web.client.RestTemplate;
import springfox.documentation.swagger2.annotations.EnableSwagger2;

@SpringBootApplication
@EnableAspectJAutoProxy(proxyTargetClass = true)
@EnableAsync
@IntegrationComponentScan
@EnableSwagger2
@EnableDiscoveryClient
public class StationFoodApplication {

    public static void main(String[] args) {
        SpringApplication.run(StationFoodApplication.class, args);
    }

    @LoadBalanced
    @Bean
    public RestTemplate restTemplate(RestTemplateBuilder builder) {
        return builder.build();
    }
}


package food.controller;

import com.alibaba.fastjson.JSONObject;
import edu.fudan.common.util.Response;
import food.service.StationFoodService;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.springframework.http.*;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.request.MockMvcRequestBuilders;
import org.springframework.test.web.servlet.result.MockMvcResultMatchers;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

import java.util.ArrayList;
import java.util.List;

@RunWith(JUnit4.class)
public class StationFoodControllerTest {

    @InjectMocks
    private StationFoodController stationFoodController;

    @Mock
    private StationFoodService stationFoodService;
    private MockMvc mockMvc;
    private Response response = new Response();

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
        mockMvc = MockMvcBuilders.standaloneSetup(stationFoodController).build();
    }

    @Test
    public void testHome() throws Exception {
        mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/foodmapservice/stationfoodstores/welcome"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andExpect(MockMvcResultMatchers.content().string("Welcome to [ Food store Service ] !"));
    }

    @Test
    public void testGetAllFoodStores() throws Exception {
        Mockito.when(stationFoodService.listFoodStores(Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/foodmapservice/stationfoodstores"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testGetFoodStoresOfStation() throws Exception {
        Mockito.when(stationFoodService.listFoodStoresByStationName(Mockito.anyString(), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/foodmapservice/stationfoodstores/station_id"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testGetFoodStoresByStationNames() throws Exception {
        List<String> stationIdList = new ArrayList<>();
        Mockito.when(stationFoodService.getFoodStoresByStationNames(Mockito.anyList())).thenReturn(response);
        String requestJson = JSONObject.toJSONString(stationIdList);
        String result = mockMvc.perform(MockMvcRequestBuilders.post("/api/v1/foodmapservice/stationfoodstores").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

}


// Node: testGetAllFoodStores
// Node: testGetFoodStoresOfStation
// Node: testGetFoodStoresByStationNames
package food.service;

import edu.fudan.common.util.Response;
import food.entity.StationFoodStore;
import food.repository.StationFoodRepository;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.springframework.http.HttpHeaders;
import java.util.Optional;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

public class StationFoodServiceImplTest {

    @InjectMocks
    private StationFoodServiceImpl foodMapServiceImpl;

    @Mock
    private StationFoodRepository stationFoodRepository;

//    @Mock
//    private TrainFoodRepository trainFoodRepository;

    private HttpHeaders headers = new HttpHeaders();

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
    }

    @Test
    public void testCreateFoodStore1() {
        StationFoodStore fss=new StationFoodStore();
        Optional<StationFoodStore> fs = Optional.ofNullable(fss);
        Mockito.when(stationFoodRepository.findById(Mockito.any(String.class))).thenReturn(fs);
        Response result = foodMapServiceImpl.createFoodStore(fs.get(), headers);
        Assert.assertEquals(new Response<>(0, "Already Exists Id", null), result);
    }

    @Test
    public void testCreateFoodStore2() {
        StationFoodStore fs = new StationFoodStore();
        Mockito.when(stationFoodRepository.findById(Mockito.any(String.class))).thenReturn(null);
        Mockito.when(stationFoodRepository.save(Mockito.any(StationFoodStore.class))).thenReturn(null);
        Response result = foodMapServiceImpl.createFoodStore(fs, headers);
        Assert.assertEquals(new Response<>(1, "Save Success", fs), result);
    }

//    @Test
//    public void testCreateTrainFood1() {
//        TrainFood tf = new TrainFood();
//        Mockito.when(trainFoodRepository.findById(Mockito.any(UUID.class))).thenReturn(tf);
//        TrainFood result = foodMapServiceImpl.createTrainFood(tf, headers);
//        Assert.assertEquals(tf, result);
//    }
//
//    @Test
//    public void testCreateTrainFood2() {
//        TrainFood tf = new TrainFood();
//        Mockito.when(trainFoodRepository.findById(Mockito.any(UUID.class))).thenReturn(null);
//        Mockito.when(trainFoodRepository.save(Mockito.any(TrainFood.class))).thenReturn(null);
//        TrainFood result = foodMapServiceImpl.createTrainFood(tf, headers);
//        Assert.assertEquals(tf, result);
//    }

    @Test
    public void testListFoodStores1() {
        List<StationFoodStore> stationFoodStores = new ArrayList<>();
        stationFoodStores.add(new StationFoodStore());
        Mockito.when(stationFoodRepository.findAll()).thenReturn(stationFoodStores);
        Response result = foodMapServiceImpl.listFoodStores(headers);
        Assert.assertEquals(new Response<>(1, "Success", stationFoodStores), result);
    }

    @Test
    public void testListFoodStores2() {
        Mockito.when(stationFoodRepository.findAll()).thenReturn(null);
        Response result = foodMapServiceImpl.listFoodStores(headers);
        Assert.assertEquals(new Response<>(0, "Food store is empty", null), result);
    }

//    @Test
//    public void testListTrainFood1() {
//        List<TrainFood> trainFoodList = new ArrayList<>();
//        trainFoodList.add(new TrainFood());
//        Mockito.when(trainFoodRepository.findAll()).thenReturn(trainFoodList);
//        Response result = foodMapServiceImpl.listTrainFood(headers);
//        Assert.assertEquals(new Response<>(1, "Success", trainFoodList), result);
//    }
//
//    @Test
//    public void testListTrainFood2() {
//        Mockito.when(trainFoodRepository.findAll()).thenReturn(null);
//        Response result = foodMapServiceImpl.listTrainFood(headers);
//        Assert.assertEquals(new Response<>(0, "No content", null), result);
//    }

    @Test
    public void testListFoodStoresByStationName1() {
        List<StationFoodStore> stationFoodStoreList = new ArrayList<>();
        stationFoodStoreList.add(new StationFoodStore());
        Mockito.when(stationFoodRepository.findByStationName(Mockito.anyString())).thenReturn(stationFoodStoreList);
        Response result = foodMapServiceImpl.listFoodStoresByStationName("station_id", headers);
        Assert.assertEquals(new Response<>(1, "Success", stationFoodStoreList), result);
    }

    @Test
    public void testListFoodStoresByStationName2() {
        Mockito.when(stationFoodRepository.findByStationName(Mockito.anyString())).thenReturn(null);
        Response result = foodMapServiceImpl.listFoodStoresByStationName("station_id", headers);
        Assert.assertEquals(new Response<>(0, "Food store is empty", null), result);
    }

//    @Test
//    public void testListTrainFoodByTripId1() {
//        List<TrainFood> trainFoodList = new ArrayList<>();
//        trainFoodList.add(new TrainFood());
//        Mockito.when(trainFoodRepository.findByTripId(Mockito.anyString())).thenReturn(trainFoodList);
//        Response result = foodMapServiceImpl.listTrainFoodByTripId("trip_id", headers);
//        Assert.assertEquals(new Response<>(1, "Success", trainFoodList), result);
//    }
//
//    @Test
//    public void testListTrainFoodByTripId2() {
//        Mockito.when(trainFoodRepository.findByTripId(Mockito.anyString())).thenReturn(null);
//        Response result = foodMapServiceImpl.listTrainFoodByTripId("trip_id", headers);
//        Assert.assertEquals(new Response<>(0, "No content", null), result);
//    }

    @Test
    public void testGetFoodStoresByStationNames1() {
        List<String> stationIds = new ArrayList<>();
        List<StationFoodStore> stationFoodStoreList = new ArrayList<>();
        stationFoodStoreList.add(new StationFoodStore());
        Mockito.when(stationFoodRepository.findByStationNameIn(Mockito.anyList())).thenReturn(stationFoodStoreList);
        Response result = foodMapServiceImpl.getFoodStoresByStationNames(stationIds);
        Assert.assertEquals(new Response<>(1, "Success", stationFoodStoreList), result);
    }

    @Test
    public void testGetFoodStoresByStationNames2() {
        List<String> stationIds = new ArrayList<>();
        Mockito.when(stationFoodRepository.findByStationNameIn(Mockito.anyList())).thenReturn(null);
        Response result = foodMapServiceImpl.getFoodStoresByStationNames(stationIds);
        Assert.assertEquals(new Response<>(0, "No content", null), result);
    }

}


package config;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;
import org.springframework.cloud.client.loadbalancer.LoadBalanced;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.EnableAspectJAutoProxy;
import org.springframework.integration.annotation.IntegrationComponentScan;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.web.client.RestTemplate;
import springfox.documentation.swagger2.annotations.EnableSwagger2;

/**
 * @author fdse
 */
@SpringBootApplication
@EnableAspectJAutoProxy(proxyTargetClass = true)
@EnableAsync
@IntegrationComponentScan
@EnableSwagger2
@EnableDiscoveryClient
public class ConfigApplication {

    public static void main(String[] args) {
        SpringApplication.run(ConfigApplication.class, args);
    }

    @LoadBalanced
    @Bean
    public RestTemplate restTemplate(RestTemplateBuilder builder) {
        return builder.build();
    }
}


package config.service;

import config.entity.Config;
import edu.fudan.common.util.Response;
import org.springframework.http.HttpHeaders;


/**
 * @author fdse
 */
public interface ConfigService {

    /**
     * create by config information and headers
     *
     * @param info info
     * @param headers headers
     * @return Response
     */
    Response create(Config info, HttpHeaders headers);

    /**
     * update by config information and headers
     *
     * @param info info
     * @param headers headers
     * @return Response
     */
    Response update(Config info, HttpHeaders headers);

    /**
     * Config retrieve
     *
     * @param name name
     * @param headers headers
     * @return Response
     */
    Response query(String name, HttpHeaders headers);

    /**
     * delete by name and headers
     *
     * @param name name
     * @param headers headers
     * @return Response
     */
    Response delete(String name, HttpHeaders headers);

    /**
     * query all by headers
     *
     * @param headers headers
     * @return Response
     */
    Response queryAll(HttpHeaders headers);
}


// Node: repos/cloned_ms_repos/train-ticket/ts-config-service/src/main/java/config/service/ConfigService.java:ConfigService.<init>
package config.controller;

import com.alibaba.fastjson.JSONObject;
import config.entity.Config;
import config.service.ConfigService;
import edu.fudan.common.util.Response;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.springframework.http.*;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.request.MockMvcRequestBuilders;
import org.springframework.test.web.servlet.result.MockMvcResultMatchers;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

@RunWith(JUnit4.class)
public class ConfigControllerTest {

    @InjectMocks
    private ConfigController configController;

    @Mock
    private ConfigService configService;
    private MockMvc mockMvc;
    private Response response = new Response();

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
        mockMvc = MockMvcBuilders.standaloneSetup(configController).build();
    }

    @Test
    public void testHome() throws Exception {
        mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/configservice/welcome"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andExpect(MockMvcResultMatchers.content().string("Welcome to [ Config Service ] !"));
    }

    @Test
    public void testQueryAll() throws Exception {
        Mockito.when(configService.queryAll(Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/configservice/configs"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testCreateConfig() throws Exception {
        Config info = new Config();
        Mockito.when(configService.create(Mockito.any(Config.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(info);
        String result = mockMvc.perform(MockMvcRequestBuilders.post("/api/v1/configservice/configs").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isCreated())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testUpdateConfig() throws Exception {
        Config info = new Config();
        Mockito.when(configService.update(Mockito.any(Config.class), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String requestJson = JSONObject.toJSONString(info);
        String result = mockMvc.perform(MockMvcRequestBuilders.put("/api/v1/configservice/configs").contentType(MediaType.APPLICATION_JSON).content(requestJson))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testDeleteConfig() throws Exception {
        Mockito.when(configService.delete(Mockito.anyString(), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.delete("/api/v1/configservice/configs/config_name"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

    @Test
    public void testRetrieve() throws Exception {
        Mockito.when(configService.query(Mockito.anyString(), Mockito.any(HttpHeaders.class))).thenReturn(response);
        String result = mockMvc.perform(MockMvcRequestBuilders.get("/api/v1/configservice/configs/config_name"))
                .andExpect(MockMvcResultMatchers.status().isOk())
                .andReturn().getResponse().getContentAsString();
        Assert.assertEquals(response, JSONObject.parseObject(result, Response.class));
    }

}


// Node: testCreateConfig
// Node: testUpdateConfig
package config.service;

import config.entity.Config;
import config.repository.ConfigRepository;
import edu.fudan.common.util.Response;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.springframework.http.HttpHeaders;

import java.util.ArrayList;
import java.util.List;

@RunWith(JUnit4.class)
public class ConfigServiceImplTest {

    @InjectMocks
    private ConfigServiceImpl configServiceImpl;

    @Mock
    private ConfigRepository repository;

    private HttpHeaders headers = new HttpHeaders();

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
    }

    @Test
    public void testCreate1() {
        Config info = new Config();
        Mockito.when(repository.findByName(info.getName())).thenReturn(info);
        Response result = configServiceImpl.create(info, headers);
        Assert.assertEquals(new Response<>(0, "Config  already exists.", null), result);
    }

    @Test
    public void testCreate2() {
        Config info = new Config("", "", "");
        Mockito.when(repository.findByName(info.getName())).thenReturn(null);
        Mockito.when(repository.save(Mockito.any(Config.class))).thenReturn(null);
        Response result = configServiceImpl.create(info, headers);
        Assert.assertEquals(new Response<>(1, "Create success", new Config("", "", "")), result);
    }

    @Test
    public void testUpdate1() {
        Config info = new Config();
        Mockito.when(repository.findByName(info.getName())).thenReturn(null);
        Response result = configServiceImpl.update(info, headers);
        Assert.assertEquals(new Response<>(0, "Config  doesn't exist.", null), result);
    }

    @Test
    public void testUpdate2() {
        Config info = new Config("", "", "");
        Mockito.when(repository.findByName(info.getName())).thenReturn(info);
        Mockito.when(repository.save(Mockito.any(Config.class))).thenReturn(null);
        Response result = configServiceImpl.update(info, headers);
        Assert.assertEquals(new Response<>(1, "Update success", new Config("", "", "")), result);
    }

    @Test
    public void testQuery1() {
        Mockito.when(repository.findByName("name")).thenReturn(null);
        Response result = configServiceImpl.query("name", headers);
        Assert.assertEquals(new Response<>(0, "No content", null), result);
    }

    @Test
    public void testQuery2() {
        Config info = new Config();
        Mockito.when(repository.findByName("name")).thenReturn(info);
        Response result = configServiceImpl.query("name", headers);
        Assert.assertEquals(new Response<>(1, "Success", new Config()), result);
    }

    @Test
    public void testDelete1() {
        Mockito.when(repository.findByName("name")).thenReturn(null);
        Response result = configServiceImpl.delete("name", headers);
        Assert.assertEquals(new Response<>(0, "Config name doesn't exist.", null), result);
    }

    @Test
    public void testDelete2() {
        Config info = new Config();
        Mockito.when(repository.findByName("name")).thenReturn(info);
        Mockito.doNothing().doThrow(new RuntimeException()).when(repository).deleteByName("name");
        Response result = configServiceImpl.delete("name", headers);
        Assert.assertEquals(new Response<>(1, "Delete success", info), result);
    }

    @Test
    public void testQueryAll1() {
        List<Config> configList = new ArrayList<>();
        configList.add(new Config());
        Mockito.when(repository.findAll()).thenReturn(configList);
        Response result = configServiceImpl.queryAll(headers);
        Assert.assertEquals(new Response<>(1, "Find all  config success", configList), result);
    }

    @Test
    public void testQueryAll2() {
        Mockito.when(repository.findAll()).thenReturn(null);
        Response result = configServiceImpl.queryAll(headers);
        Assert.assertEquals(new Response<>(0, "No content", null), result);
    }

}


