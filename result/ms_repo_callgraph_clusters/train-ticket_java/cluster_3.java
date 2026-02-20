// Cluster 3

package adminuser.controller;

import adminuser.dto.UserDto;
import adminuser.service.AdminUserService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.web.bind.annotation.*;

import static org.springframework.http.ResponseEntity.ok;

/**
 * @author fdse
 */
@RestController
@RequestMapping("/api/v1/adminuserservice/users")
public class AdminUserController {

    @Autowired
    AdminUserService adminUserService;
    private static final Logger logger = LoggerFactory.getLogger(AdminUserController.class);

    @GetMapping(path = "/welcome")
    public String home(@RequestHeader HttpHeaders headers) {
        return "Welcome to [ AdminUser Service ] !";
    }

    @CrossOrigin(origins = "*")
    @GetMapping
    public HttpEntity getAllUsers(@RequestHeader HttpHeaders headers) {
        logger.info("[getAllUsers][Get all users]");
        return ok(adminUserService.getAllUsers(headers));
    }

    @PutMapping
    public HttpEntity updateUser(@RequestBody UserDto userDto, @RequestHeader HttpHeaders headers) {
        logger.info("[updateUser][Update User][userName: {}]", userDto.getUserName());
        return ok(adminUserService.updateUser(userDto, headers));
    }


    @PostMapping
    public HttpEntity addUser(@RequestBody UserDto userDto, @RequestHeader HttpHeaders headers) {
        logger.info("[addUser][Add user][userName: {}]", userDto.getUserName());
        return ok(adminUserService.addUser(userDto, headers));
    }

    @DeleteMapping(value = "/{userId}")
    public HttpEntity deleteUser(@PathVariable String userId, @RequestHeader HttpHeaders headers) {
        logger.info("[deleteUser][Delete user][userId: {}]", userId);
        return ok(adminUserService.deleteUser(userId, headers));
    }

}


// Node: repos/cloned_ms_repos/train-ticket/ts-admin-user-service/src/main/java/adminuser/controller/AdminUserController.java:AdminUserController.<init>
// Node: RequestMapping
// Node: getLogger
// Node: GetMapping
// Node: home
// Node: CrossOrigin
// Node: ok
// Node: DeleteMapping
package adminuser.service;

import adminuser.dto.UserDto;
import edu.fudan.common.entity.User;
import edu.fudan.common.util.Response;
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


import java.util.List;

/**
 * @author fdse
 */
@Service
public class AdminUserServiceImpl implements AdminUserService {
    @Autowired
    private RestTemplate restTemplate;
    @Autowired
    private DiscoveryClient discoveryClient;

    private static final Logger LOGGER = LoggerFactory.getLogger(AdminUserServiceImpl.class);
//    @Value("${user-service.url}")
//    String user_service_url;
//    private final String USER_SERVICE_IP_URI = user_service_url + "/api/v1/userservice/users";

    private String getServiceUrl(String serviceName) {
        return "http://" + serviceName;
    }

    @Override
    public Response getAllUsers(HttpHeaders headers) {
        HttpEntity requestEntity = new HttpEntity(null);
        String user_service_url = getServiceUrl("ts-user-service");
        String USER_SERVICE_IP_URI = user_service_url + "/api/v1/userservice/users";
        ResponseEntity<Response<List<User>>> re = restTemplate.exchange(
                USER_SERVICE_IP_URI,
                HttpMethod.GET,
                requestEntity,
                new ParameterizedTypeReference<Response<List<User>>>() {
                });
        if (re.getBody() == null || re.getBody().getStatus() != 1) {
            AdminUserServiceImpl.LOGGER.error("[getAllUsers][receive response][Get All Users error]");
            return new Response<>(0, "get all users error", null);
        }
        AdminUserServiceImpl.LOGGER.info("[getAllUsers][Get All Users][success]");
        return re.getBody();
    }


    @Override
    public Response deleteUser(String userId, HttpHeaders headers) {
        HttpHeaders newHeaders = new HttpHeaders();
        String token = headers.getFirst(HttpHeaders.AUTHORIZATION);
        newHeaders.set(HttpHeaders.AUTHORIZATION, token);

        HttpEntity<Response> requestEntity = new HttpEntity<>(newHeaders);

        String user_service_url = getServiceUrl("ts-user-service");
        String USER_SERVICE_IP_URI = user_service_url + "/api/v1/userservice/users";
        ResponseEntity<Response> re = restTemplate.exchange(
                USER_SERVICE_IP_URI + "/" + userId,
                HttpMethod.DELETE,
                requestEntity,
                Response.class);
        if (re.getBody() == null || re.getBody().getStatus() != 1) {
            AdminUserServiceImpl.LOGGER.error("[deleteUser][receive response][Delete user error][userId: {}]", userId);
            return new Response<>(0, "delete user error", null);
        }
        AdminUserServiceImpl.LOGGER.info("[deleteUser][Delete user success][userId: {}]", userId);
        return re.getBody();
    }

    @Override
    public Response updateUser(UserDto userDto, HttpHeaders headers) {
        LOGGER.info("UPDATE USER: " + userDto.toString());

        HttpHeaders newHeaders = new HttpHeaders();
        String token = headers.getFirst(HttpHeaders.AUTHORIZATION);
        newHeaders.set(HttpHeaders.AUTHORIZATION, token);

        HttpEntity requestEntity = new HttpEntity(userDto, newHeaders);
        String user_service_url = getServiceUrl("ts-user-service");
        String USER_SERVICE_IP_URI = user_service_url + "/api/v1/userservice/users";
        ResponseEntity<Response> re = restTemplate.exchange(
                USER_SERVICE_IP_URI,
                HttpMethod.PUT,
                requestEntity,
                Response.class);

        String userName = userDto.getUserName();
        if (re.getBody() == null || re.getBody().getStatus() != 1) {
            AdminUserServiceImpl.LOGGER.error("[updateUser][receive response][Update user error][userName: {}]", userName);
            return new Response<>(0, "Update user error", null);
        }
        AdminUserServiceImpl.LOGGER.info("[updateUser][Update user success][userName: {}]", userName);
        return re.getBody();
    }

    @Override
    public Response addUser(UserDto userDto, HttpHeaders headers) {
        LOGGER.info("[addUser][ADD USER INFO][UserDto: {}]", userDto.toString());
        HttpEntity requestEntity = new HttpEntity(userDto, null);
        String user_service_url = getServiceUrl("ts-user-service");
        String USER_SERVICE_IP_URI = user_service_url + "/api/v1/userservice/users";
        ResponseEntity<Response<User>> re = restTemplate.exchange(
                USER_SERVICE_IP_URI + "/register",
                HttpMethod.POST,
                requestEntity,
                new ParameterizedTypeReference<Response<User>>() {
                });

        String userName = userDto.getUserName();
        if (re.getBody() == null || re.getBody().getStatus() != 1) {
            AdminUserServiceImpl.LOGGER.error("[addUser][receive response][Add user error][userName: {}]", userName);
            return new Response<>(0, "Add user error", null);
        }
        AdminUserServiceImpl.LOGGER.info("[addUser][Add user success][userName: {}]", userName);
        return re.getBody();
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-admin-user-service/src/main/java/adminuser/service/AdminUserServiceImpl.java:AdminUserServiceImpl.<init>
// Node: Value
package waitorder.controller;


import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.web.bind.annotation.*;
import waitorder.entity.WaitListOrderVO;
import waitorder.service.WaitListOrderService;


import static org.springframework.http.ResponseEntity.ok;

/**
 * @author fdse
 */
@RestController
@RequestMapping("/api/v1/waitorderservice")
public class WaitListOrderController {

    @Autowired
    private WaitListOrderService waitListOrderService;

    private static final Logger LOGGER = LoggerFactory.getLogger(WaitListOrderController.class);

    @GetMapping(path = "/welcome")
    public String home() {
        return "Welcome to [ Wait Order Service ] !";
    }

    @PostMapping(path = "/order")
    public HttpEntity createNewOrder(@RequestBody WaitListOrderVO createOrder, @RequestHeader HttpHeaders headers) {
        WaitListOrderController.LOGGER.info("[createWaitOrder][Create Wait Order][from {} to {} at {}]", createOrder.getFrom(), createOrder.getTo(), createOrder.getDate());
        return ok(waitListOrderService.create(createOrder, headers));
    }

    @GetMapping(path = "/orders")
    public HttpEntity getAllOrders(@RequestHeader HttpHeaders headers){
        LOGGER.info("[getAllOrders][Get All Orders]");
        return ok(waitListOrderService.getAllOrders(headers));
    }

    @GetMapping(path = "/waitlistorders")
    public HttpEntity getWaitListOrders(@RequestHeader HttpHeaders headers){
        LOGGER.info("[getWaitListOrders][Get All Wait List Orders]");
        return ok(waitListOrderService.getAllWaitListOrders(headers));
    }


}


// Node: repos/cloned_ms_repos/train-ticket/ts-wait-order-service/src/main/java/waitorder/controller/WaitListOrderController.java:WaitListOrderController.<init>
// Node: PostMapping
package waitorder.service.Impl;

import edu.fudan.common.util.Response;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.BeanUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.cloud.client.discovery.DiscoveryClient;
import org.springframework.http.HttpHeaders;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.client.RestTemplate;
import waitorder.entity.WaitListOrder;
import waitorder.entity.WaitListOrderStatus;
import waitorder.entity.WaitListOrderVO;
import waitorder.repository.WaitListOrderRepository;
import waitorder.service.WaitListOrderService;
import waitorder.utils.PollThread;

import java.util.*;
import java.util.stream.Collectors;

@Service
public class WaitListOrderServiceImpl implements WaitListOrderService {

    @Autowired
    private WaitListOrderRepository waitListOrderRepository;

    @Autowired
    private RestTemplate restTemplate;

    @Autowired
    private DiscoveryClient discoveryClient;

    private static final Logger LOGGER = LoggerFactory.getLogger(WaitListOrderServiceImpl.class);

    String success = "Success";

    @Override
    public Response findOrderById(String id, HttpHeaders headers) {
        Optional<WaitListOrder> op = waitListOrderRepository.findById(id);
        if(!op.isPresent()){
            LOGGER.warn("[findWaitOrderById][Find Order By Id Fail][No content][id: {}] ",id);
            return new Response<>(0, "No Content by this id", null);
        } else {
            WaitListOrder wo = op.get();
            LOGGER.info("[findWaitOrderById][Find Order By Id Success][id: {}] ",id);
            return new Response<>(1, success, wo);
        }
    }

    @Transactional
    @Override
    public Response create(WaitListOrderVO orderVO, HttpHeaders headers) {
        LOGGER.info("[create][Create Wait Order][Ready to Create Wait Order]");
        Response<WaitListOrder> response=saveNewOrder(orderVO,headers);
        if(response.getStatus()==0){
            //未能正常保存到数据库
            return response;
        } else {
            //已保存到数据库 开始轮询
            return triggerThread(response.getData(),orderVO,headers);
        }
    }

    @Override
    public Response getAllOrders(HttpHeaders headers) {
        List<WaitListOrder> orderList= waitListOrderRepository.findAll();
        if (orderList != null && !orderList.isEmpty()) {
            WaitListOrderServiceImpl.LOGGER.warn("[getAllOrders][Find all orders Success][size:{}]",orderList.size());
            return new Response<>(1, "Success.", orderList);
        } else {
            LOGGER.warn("[getAllOrders][Find All Wait List Orders Fail][{}]","No content");
            return new Response<>(0, "No Content.", null);
        }
    }

    @Override
    public Response getAllWaitListOrders(HttpHeaders headers) {
        List<WaitListOrder> orderList= waitListOrderRepository.findAll();
        if (orderList != null && !orderList.isEmpty()) {
            WaitListOrderServiceImpl.LOGGER.warn("[getAllWaitListOrders][Find all orders Success][size:{}]",orderList.size());
            List<Integer> filterList=new ArrayList<>();
            filterList.add(WaitListOrderStatus.NOTPAID.getCode());
            filterList.add(WaitListOrderStatus.PAID.getCode());
            //Only orders in the wait list will be selected
            orderList=orderList.stream()
                    .filter(WaitListOrder -> filterList.contains(WaitListOrder.getStatus()))
                    .collect(Collectors.toList());
            return new Response<>(1, "Success.", orderList);
        } else {
            LOGGER.warn("[getAllWaitListOrders][Find All Wait List Orders Fail][{}]","No content");
            return new Response<>(0, "No Content.", null);
        }
    }

    @Transactional
    @Override
    public Response updateOrder(WaitListOrder order, HttpHeaders headers) {
        LOGGER.info("[updateOrder][Update Wait List Order][Order Info:{}] ", order.toString());
        Optional<WaitListOrder> op = waitListOrderRepository.findById(order.getId());
        if(!op.isPresent()){
            LOGGER.error("[updateOrder][Update Order Info Fail][Order not found][OrderId: {}]",order.getId());
            return new Response<>(0, "Order Not Found, Can't update", null);
        } else {
            WaitListOrder old = op.get();
            BeanUtils.copyProperties(old,order);
            waitListOrderRepository.save(old);
            LOGGER.info("[updateOrder][Update Wait List Order Info Success][OrderId: {}]",order.getId());
            return new Response<>(1, "Update Wait List Order Success", old);
        }
    }

    @Transactional
    @Override
    public Response modifyWaitListOrderStatus(int status, String orderId) {
        LOGGER.info("[modifyWaitListOrderStatus][Modify Order Status][OrderId:{}] ", orderId);
        Optional<WaitListOrder> op = waitListOrderRepository.findById(orderId);
        if(!op.isPresent()){
            LOGGER.error("[modifyWaitListOrderStatus][Modify Order Status Fail][Order not found][OrderId: {}]",orderId);
            return new Response<>(0, "Order Not Found, Can't update", null);
        } else {
            WaitListOrder old = op.get();
            old.setStatus(status);
            waitListOrderRepository.save(old);
            LOGGER.info("[modifyWaitListOrderStatus][Modify Order Status Success][OrderId: {}]",orderId);
            return new Response<>(1, "Modify Wait List Order Status Success", old);
        }
    }

    private Response<WaitListOrder> saveNewOrder(WaitListOrderVO orderVO, HttpHeaders headers) {
        ArrayList<WaitListOrder> accountOrders= waitListOrderRepository.findByAccountId(orderVO.getAccountId());
        //if the order already exist
        if(WaitListOrderExist(accountOrders,orderVO)){
            WaitListOrderServiceImpl.LOGGER.error("[create][Create Wait Order Fail][Order already exists][AccountId: {} , TripId: {}]", orderVO.getAccountId(),orderVO.getTripId());
            return new Response<>(0, "Order already exist", null);
        } else {
            WaitListOrder newWaitListOrder=new WaitListOrder();
            newWaitListOrder.setId(UUID.randomUUID().toString());
            BeanUtils.copyProperties(newWaitListOrder,orderVO);
            newWaitListOrder.setTrainNumber(orderVO.getTripId());
            waitListOrderRepository.save(newWaitListOrder);
            WaitListOrderServiceImpl.LOGGER.info("[create][Create Wait Order Success][Order Price][AccountId: {} , TripId: {}]", orderVO.getAccountId(),orderVO.getTripId());
            return new Response<>(1,success,newWaitListOrder);
        }
    }

    private Boolean WaitListOrderExist(List<WaitListOrder> orderList,WaitListOrderVO newOrder){
        for(WaitListOrder order: orderList){
            if(Objects.equals(order.getAccountId(), newOrder.getAccountId())
                    && Objects.equals(order.getContactsId(), newOrder.getContactsId())
                    && Objects.equals(order.getTrainNumber(), newOrder.getTripId())
                    && Objects.equals(order.getTravelTime(),newOrder.getDate())
                    && Objects.equals(order.getFrom(),newOrder.getFrom())
                    && Objects.equals(order.getTo(),newOrder.getTo())){
                return true;
            }
        }
        return false;
    }

    private Response triggerThread(WaitListOrder orderPO,WaitListOrderVO orderVO,HttpHeaders headers){
        PollThread pollThread;
        try{
            pollThread =new PollThread(orderPO.getWaitUtilTime(),this,orderVO,restTemplate, headers);
            pollThread.start();
        } catch (Exception e){
            return new Response<>(0, "Fail To Run A New Thread", null);
        }
        return new Response<>(1,"Thread Start Success",null);
    }


}


// Node: repos/cloned_ms_repos/train-ticket/ts-wait-order-service/src/main/java/waitorder/service/Impl/WaitListOrderServiceImpl.java:WaitListOrderServiceImpl.<init>
package auth.controller;

import auth.dto.AuthDto;
import auth.service.UserService;
import edu.fudan.common.util.Response;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

/**
 * @author fdse
 */
@RestController
@RequestMapping("/api/v1/auth")
public class AuthController {

    @Autowired
    private UserService userService;

    private static final Logger logger = LoggerFactory.getLogger(AuthController.class);
    /**
     * only while  user register, this method will be called by ts-user-service
     * to create a default role use
     *
     * @return
     */
    @GetMapping("/hello")
    public String getHello() {
        return "hello";
    }

    @PostMapping
    public HttpEntity<Response> createDefaultUser(@RequestBody AuthDto authDto) {
        logger.info("[createDefaultUser][Create default auth user with authDto][AuthDto: {}]", authDto.toString());
        userService.createDefaultAuthUser(authDto);
        Response response = new Response(1, "SUCCESS", authDto);
        return new ResponseEntity<>(response, HttpStatus.CREATED);
    }
}



// Node: repos/cloned_ms_repos/train-ticket/ts-auth-service/src/main/java/auth/controller/AuthController.java:AuthController.<init>
// Node: getHello
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


// Node: repos/cloned_ms_repos/train-ticket/ts-auth-service/src/main/java/auth/controller/UserController.java:UserController.<init>
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


// Node: repos/cloned_ms_repos/train-ticket/ts-auth-service/src/main/java/auth/service/impl/UserServiceImpl.java:UserServiceImpl.<init>
package auth.service.impl;

import auth.constant.InfoConstant;
import auth.dto.BasicAuthDto;
import auth.dto.TokenDto;
import auth.entity.User;
import auth.exception.UserOperationException;
import auth.repository.UserRepository;
import auth.security.jwt.JWTProvider;
import auth.service.TokenService;
import edu.fudan.common.util.Response;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.cloud.client.ServiceInstance;
import org.springframework.cloud.client.discovery.DiscoveryClient;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.ResponseEntity;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.AuthenticationException;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;
import org.springframework.web.client.RestTemplate;

import java.text.MessageFormat;
import java.util.List;

/**
 * @author fdse
 */
@Service
public class TokenServiceImpl implements TokenService {
    private static final Logger LOGGER = LoggerFactory.getLogger(TokenServiceImpl.class);

    @Autowired
    private JWTProvider jwtProvider;

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private AuthenticationManager authenticationManager;

    @Autowired
    private RestTemplate restTemplate;

    @Autowired
    private DiscoveryClient discoveryClient;

    private String getServiceUrl(String serviceName) {
        return "http://" + serviceName;
    }

    @Override
    public Response getToken(BasicAuthDto dto, HttpHeaders headers) throws UserOperationException {
        String username = dto.getUsername();
        String password = dto.getPassword();
        String verifyCode = dto.getVerificationCode();
//        LOGGER.info("LOGIN USER :" + username + " __ " + password + " __ " + verifyCode);
        String verification_code_service_url = getServiceUrl("ts-verification-code-service");
        if (!StringUtils.isEmpty(verifyCode)) {
            HttpEntity requestEntity = new HttpEntity(headers);
            ResponseEntity<Boolean> re = restTemplate.exchange(
                     verification_code_service_url + "/api/v1/verifycode/verify/" + verifyCode,
                    HttpMethod.GET,
                    requestEntity,
                    Boolean.class);
            boolean id = re.getBody();

            // failed code
            if (!id) {
                LOGGER.info("[getToken][Verification failed][userName: {}]", username);
                return new Response<>(0, "Verification failed.", null);
            }
        }

        // verify username and password
        UsernamePasswordAuthenticationToken upat = new UsernamePasswordAuthenticationToken(username, password);
        try {
            authenticationManager.authenticate(upat);
        } catch (AuthenticationException e) {
            LOGGER.warn("[getToken][Incorrect username or password][username: {}, password: {}]", username, password);
            return new Response<>(0, "Incorrect username or password.", null);
        }

        User user = userRepository.findByUsername(username)
                .orElseThrow(() -> new UserOperationException(MessageFormat.format(
                        InfoConstant.USER_NAME_NOT_FOUND_1, username
                )));
        String token = jwtProvider.createToken(user);
        LOGGER.info("[getToken][success][USER TOKEN: {} USER ID: {}]", token, user.getUserId());
        return new Response<>(1, "login success", new TokenDto(user.getUserId(), username, token));
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-auth-service/src/main/java/auth/service/impl/TokenServiceImpl.java:TokenServiceImpl.<init>
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


// Node: repos/cloned_ms_repos/train-ticket/ts-common/src/main/java/edu/fudan/common/config/SwaggerConfig.java:SwaggerConfig.<init>
package plan.controller;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.web.bind.annotation.*;
import edu.fudan.common.entity.RoutePlanInfo;
import plan.service.RoutePlanService;

import static org.springframework.http.ResponseEntity.ok;

/**
 * @author fdse
 */
@RestController
@RequestMapping("/api/v1/routeplanservice")
public class RoutePlanController {

    @Autowired
    private RoutePlanService routePlanService;
    private static final Logger LOGGER = LoggerFactory.getLogger(RoutePlanController.class);

    @GetMapping(path = "/welcome")
    public String home() {
        return "Welcome to [ RoutePlan Service ] !";
    }

    @PostMapping(value = "/routePlan/cheapestRoute")
    public HttpEntity getCheapestRoutes(@RequestBody RoutePlanInfo info, @RequestHeader HttpHeaders headers) {
        RoutePlanController.LOGGER.info("[searchCheapestResult][Get Cheapest Routes][From: {}, To: {}, Num: {}, Date: {}]", info.getStartStation(), info.getEndStation(), + info.getNum(), info.getTravelDate());
        return ok(routePlanService.searchCheapestResult(info, headers));
    }

    @PostMapping(value = "/routePlan/quickestRoute")
    public HttpEntity getQuickestRoutes(@RequestBody RoutePlanInfo info, @RequestHeader HttpHeaders headers) {
        RoutePlanController.LOGGER.info("[searchQuickestResult][Get Quickest Routes][From: {}, To: {}, Num: {}, Date: {}]", info.getStartStation(), info.getEndStation(), info.getNum(), info.getTravelDate());
        return ok(routePlanService.searchQuickestResult(info, headers));
    }

    @PostMapping(value = "/routePlan/minStopStations")
    public HttpEntity getMinStopStations(@RequestBody RoutePlanInfo info, @RequestHeader HttpHeaders headers) {
        RoutePlanController.LOGGER.info("[searchMinStopStations][Get Min Stop Stations][From: {}, To: {}, Num: {}, Date: {}]", info.getStartStation(), info.getEndStation(), info.getNum(), info.getTravelDate());
        return ok(routePlanService.searchMinStopStations(info, headers));
    }

}


// Node: repos/cloned_ms_repos/train-ticket/ts-route-plan-service/src/main/java/plan/controller/RoutePlanController.java:RoutePlanController.<init>
package plan.service;

import edu.fudan.common.entity.*;
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

import java.util.ArrayList;
import java.util.Date;
import java.util.List;

/**
 * @author fdse
 */
@Service
public class RoutePlanServiceImpl implements RoutePlanService {

    @Autowired
    private RestTemplate restTemplate;
    @Autowired
    private DiscoveryClient discoveryClient;
    private static final Logger LOGGER = LoggerFactory.getLogger(RoutePlanServiceImpl.class);

    private String getServiceUrl(String serviceName) {
        return "http://" + serviceName;
    }

    @Override
    public Response searchCheapestResult(RoutePlanInfo info, HttpHeaders headers) {

        //1.Violence pulls out all the results of travel-service and travle2-service
        TripInfo queryInfo = new TripInfo();
        queryInfo.setStartPlace(info.getStartStation());
        queryInfo.setEndPlace(info.getEndStation());
        queryInfo.setDepartureTime(info.getTravelDate());

        ArrayList<TripResponse> highSpeed = getTripFromHighSpeedTravelServive(queryInfo, headers);
        ArrayList<TripResponse> normalTrain = getTripFromNormalTrainTravelService(queryInfo, headers);

        //2.Sort by second-class seats
        ArrayList<TripResponse> finalResult = new ArrayList<>();
        finalResult.addAll(highSpeed);
        finalResult.addAll(normalTrain);

        float minPrice;
        int minIndex = -1;
        int size = Math.min(5, finalResult.size());
        ArrayList<TripResponse> returnResult = new ArrayList<>();
        for (int i = 0; i < size; i++) {

            minPrice = Float.MAX_VALUE;
            for (int j = 0; j < finalResult.size(); j++) {
                TripResponse thisRes = finalResult.get(j);
                if (Float.parseFloat(thisRes.getPriceForEconomyClass()) < minPrice) {
                    minPrice = Float.parseFloat(finalResult.get(j).getPriceForEconomyClass());
                    minIndex = j;
                }
            }
            returnResult.add(finalResult.get(minIndex));
            finalResult.remove(minIndex);
        }


        ArrayList<RoutePlanResultUnit> units = new ArrayList<>();
        for (int i = 0; i < returnResult.size(); i++) {
            TripResponse tempResponse = returnResult.get(i);

            RoutePlanResultUnit tempUnit = new RoutePlanResultUnit();
            tempUnit.setTripId(tempResponse.getTripId().toString());
            tempUnit.setTrainTypeName(tempResponse.getTrainTypeName());
            tempUnit.setStartStation(tempResponse.getStartStation());
            tempUnit.setEndStation(tempResponse.getTerminalStation());
            tempUnit.setStopStations(getStationList(tempResponse.getTripId().toString(), headers));
            tempUnit.setPriceForSecondClassSeat(tempResponse.getPriceForEconomyClass());
            tempUnit.setPriceForFirstClassSeat(tempResponse.getPriceForConfortClass());
            tempUnit.setEndTime(tempResponse.getEndTime());
            tempUnit.setStartTime(tempResponse.getStartTime());

            units.add(tempUnit);
        }

        return new Response<>(1, "Success", units);
    }

    @Override
    public Response searchQuickestResult(RoutePlanInfo info, HttpHeaders headers) {

        //1.Violence pulls out all the results of travel-service and travle2-service
        TripInfo queryInfo = new TripInfo();
        queryInfo.setStartPlace(info.getStartStation());
        queryInfo.setEndPlace(info.getEndStation());
        queryInfo.setDepartureTime(info.getTravelDate());

        ArrayList<TripResponse> highSpeed = getTripFromHighSpeedTravelServive(queryInfo, headers);
        ArrayList<TripResponse> normalTrain = getTripFromNormalTrainTravelService(queryInfo, headers);

        //2.Sort by time
        ArrayList<TripResponse> finalResult = new ArrayList<>();

        for (TripResponse tr : highSpeed) {
            finalResult.add(tr);
        }
        for (TripResponse tr : normalTrain) {
            finalResult.add(tr);
        }

        long minTime;
        int minIndex = -1;
        int size = Math.min(finalResult.size(), 5);
        ArrayList<TripResponse> returnResult = new ArrayList<>();
        for (int i = 0; i < size; i++) {

            minTime = Long.MAX_VALUE;
            for (int j = 0; j < finalResult.size(); j++) {
                TripResponse thisRes = finalResult.get(j);
                Date endTime = StringUtils.String2Date(thisRes.getEndTime());
                Date startTime = StringUtils.String2Date(thisRes.getStartTime());
                if (endTime.getTime() - startTime.getTime() < minTime) {
                    minTime = endTime.getTime() - startTime.getTime();
                    minIndex = j;
                }
            }
            returnResult.add(finalResult.get(minIndex));
            finalResult.remove(minIndex);

        }


        ArrayList<RoutePlanResultUnit> units = new ArrayList<>();
        for (int i = 0; i < returnResult.size(); i++) {
            TripResponse tempResponse = returnResult.get(i);

            RoutePlanResultUnit tempUnit = new RoutePlanResultUnit();
            tempUnit.setTripId(tempResponse.getTripId().toString());
            tempUnit.setTrainTypeName(tempResponse.getTrainTypeName());
            tempUnit.setStartStation(tempResponse.getStartStation());
            tempUnit.setEndStation(tempResponse.getTerminalStation());

            tempUnit.setStopStations(getStationList(tempResponse.getTripId().toString(), headers));

            tempUnit.setPriceForSecondClassSeat(tempResponse.getPriceForEconomyClass());
            tempUnit.setPriceForFirstClassSeat(tempResponse.getPriceForConfortClass());
            tempUnit.setStartTime(tempResponse.getStartTime());
            tempUnit.setEndTime(tempResponse.getEndTime());
            units.add(tempUnit);
        }
        return new Response<>(1, "Success", units);
    }

    @Override
    public Response searchMinStopStations(RoutePlanInfo info, HttpHeaders headers) {
        String fromStationId = info.getStartStation();
        String toStationId = info.getEndStation();
        RoutePlanServiceImpl.LOGGER.info("[searchMinStopStations][Start and Finish][From Id: {} To: {}]", fromStationId , toStationId);
        //1.Get the route through the two stations

        HttpEntity requestEntity = new HttpEntity(null);
        String route_service_url = getServiceUrl("ts-route-service");
        ResponseEntity<Response<ArrayList<Route>>> re = restTemplate.exchange(
                route_service_url + "/api/v1/routeservice/routes/" + info.getStartStation() + "/" + info.getEndStation(),
                HttpMethod.GET,
                requestEntity,
                new ParameterizedTypeReference<Response<ArrayList<Route>>>() {
                });


        ArrayList<Route> routeList = re.getBody().getData();
        RoutePlanServiceImpl.LOGGER.info("[searchMinStopStations][Get the route][Candidate Route Number: {}]", routeList.size());
        //2.Calculate how many stops there are between the two stations
        ArrayList<Integer> gapList = new ArrayList<>();
        for (int i = 0; i < routeList.size(); i++) {
            int indexStart = routeList.get(i).getStations().indexOf(fromStationId);
            int indexEnd = routeList.get(i).getStations().indexOf(toStationId);
            gapList.add(indexEnd - indexStart);
        }
        //3.Pick the routes with the fewest stops
        ArrayList<String> resultRoutes = new ArrayList<>();
        int size = Math.min(5, routeList.size());
        for (int i = 0; i < size; i++) {
            int minIndex = 0;
            int tempMinGap = Integer.MAX_VALUE;
            for (int j = 0; j < gapList.size(); j++) {
                if (gapList.get(j) < tempMinGap) {
                    tempMinGap = gapList.get(j);
                    minIndex = j;
                }
            }
            resultRoutes.add(routeList.get(minIndex).getId());
            routeList.remove(minIndex);
            gapList.remove(minIndex);
        }
        //4.Depending on the route, go to travel-service or travel2service to get the train information
        requestEntity = new HttpEntity(resultRoutes, null);
        String travel_service_url=getServiceUrl("ts-travel-service");
        ResponseEntity<Response<ArrayList<ArrayList<Trip>>>> re2 = restTemplate.exchange(
                travel_service_url + "/api/v1/travelservice/trips/routes",
                HttpMethod.POST,
                requestEntity,
                new ParameterizedTypeReference<Response<ArrayList<ArrayList<Trip>>>>() {
                });

        ArrayList<ArrayList<Trip>> travelTrips = re2.getBody().getData();

        String travel2_service_url=getServiceUrl("ts-travel2-service");
        re2 = restTemplate.exchange(
                travel2_service_url + "/api/v1/travel2service/trips/routes",
                HttpMethod.POST,
                requestEntity,
                new ParameterizedTypeReference<Response<ArrayList<ArrayList<Trip>>>>() {
                });
        ArrayList<ArrayList<Trip>> travel2Trips = re2.getBody().getData();

        //Merge query results
        ArrayList<ArrayList<Trip>> finalTripResult = new ArrayList<>();
        for (int i = 0; i < travel2Trips.size(); i++) {
            ArrayList<Trip> tempList = travel2Trips.get(i);
            tempList.addAll(travelTrips.get(i));
            finalTripResult.add(tempList);
        }
        RoutePlanServiceImpl.LOGGER.info("[searchMinStopStations][Get train Information][Trips Num: {}]", finalTripResult.size());
        //5.Then, get the price and the station information according to the train information
        ArrayList<Trip> trips = new ArrayList<>();
        for (ArrayList<Trip> tempTrips : finalTripResult) {
            trips.addAll(tempTrips);
        }
        ArrayList<RoutePlanResultUnit> tripResponses = new ArrayList<>();

        ResponseEntity<Response<TripAllDetail>> re3;
        for (Trip trip : trips) {
            TripResponse tripResponse;
            TripAllDetailInfo allDetailInfo = new TripAllDetailInfo();
            allDetailInfo.setTripId(trip.getTripId().toString());
            allDetailInfo.setTravelDate(info.getTravelDate());
            allDetailInfo.setFrom(info.getStartStation());
            allDetailInfo.setTo(info.getEndStation());
            requestEntity = new HttpEntity(allDetailInfo, null);
            String requestUrl = "";
            if (trip.getTripId().toString().charAt(0) == 'D' || trip.getTripId().toString().charAt(0) == 'G') {
                requestUrl = travel_service_url + "/api/v1/travelservice/trip_detail";
            } else {
                requestUrl = travel2_service_url + "/api/v1/travel2service/trip_detail";
            }
            re3 = restTemplate.exchange(
                    requestUrl,
                    HttpMethod.POST,
                    requestEntity,
                    new ParameterizedTypeReference<Response<TripAllDetail>>() {
                    });

            TripAllDetail tripAllDetail = re3.getBody().getData();
            tripResponse = tripAllDetail.getTripResponse();


            RoutePlanResultUnit unit = new RoutePlanResultUnit();
            unit.setTripId(trip.getTripId().toString());
            unit.setTrainTypeName(tripResponse.getTrainTypeName());
            unit.setStartStation(tripResponse.getStartStation());
            unit.setEndStation(tripResponse.getTerminalStation());
            unit.setStartTime(tripResponse.getStartTime());
            unit.setEndTime(tripResponse.getEndTime());
            unit.setPriceForFirstClassSeat(tripResponse.getPriceForConfortClass());
            unit.setPriceForSecondClassSeat(tripResponse.getPriceForEconomyClass());
            //Go get the roadmap according to routeid
            String routeId = trip.getRouteId();
            Route tripRoute = getRouteByRouteId(routeId, headers);
            if (tripRoute != null) {
                unit.setStopStations(tripRoute.getStations());
            }

            tripResponses.add(unit);
        }
        RoutePlanServiceImpl.LOGGER.info("[searchMinStopStations][Trips Response Unit Num: {}]", tripResponses.size());
        return new Response<>(1, "Success.", tripResponses);
    }

    private Route getRouteByRouteId(String routeId, HttpHeaders headers) {
        HttpEntity requestEntity = new HttpEntity(null);
        String route_service_url = getServiceUrl("ts-route-service");
        ResponseEntity<Response<Route>> re = restTemplate.exchange(
                route_service_url + "/api/v1/routeservice/routes/" + routeId,
                HttpMethod.GET,
                requestEntity,
                new ParameterizedTypeReference<Response<Route>>() {
                });
        Response<Route> result = re.getBody();

        if (result.getStatus() == 0) {
            RoutePlanServiceImpl.LOGGER.error("[getRouteByRouteId][Get Route By Id Fail][RouteId: {}]", routeId);
            return null;
        } else {
            RoutePlanServiceImpl.LOGGER.info("[getRouteByRouteId][Get Route By Id Success]");
            return result.getData();
        }
    }

    private ArrayList<TripResponse> getTripFromHighSpeedTravelServive(TripInfo info, HttpHeaders headers) {
        RoutePlanServiceImpl.LOGGER.info("[getTripFromHighSpeedTravelServive][trip info: {}]", info);
        HttpEntity requestEntity = new HttpEntity(info, null);
        String travel_service_url=getServiceUrl("ts-travel-service");
        ResponseEntity<Response<ArrayList<TripResponse>>> re = restTemplate.exchange(
                travel_service_url + "/api/v1/travelservice/trips/left",
                HttpMethod.POST,
                requestEntity,
                new ParameterizedTypeReference<Response<ArrayList<TripResponse>>>() {
                });

        ArrayList<TripResponse> tripResponses = re.getBody().getData();
        RoutePlanServiceImpl.LOGGER.info("[getTripFromHighSpeedTravelServive][Route Plan Get Trip][Size:{}]", tripResponses.size());
        return tripResponses;
    }

    private ArrayList<TripResponse> getTripFromNormalTrainTravelService(TripInfo info, HttpHeaders headers) {
        HttpEntity requestEntity = new HttpEntity(info, null);
        String travel2_service_url=getServiceUrl("ts-travel2-service");
        ResponseEntity<Response<ArrayList<TripResponse>>> re = restTemplate.exchange(
                travel2_service_url + "/api/v1/travel2service/trips/left",
                HttpMethod.POST,
                requestEntity,
                new ParameterizedTypeReference<Response<ArrayList<TripResponse>>>() {
                });
        ArrayList<TripResponse> list = re.getBody().getData();
        RoutePlanServiceImpl.LOGGER.info("[getTripFromNormalTrainTravelService][Route Plan Get TripOther][Size:{}]", list.size());
        return list;
    }

    private List<String> getStationList(String tripId, HttpHeaders headers) {

        String path;
        String travel_service_url=getServiceUrl("ts-travel-service");
        String travel2_service_url=getServiceUrl("ts-travel2-service");
        if (tripId.charAt(0) == 'G' || tripId.charAt(0) == 'D') {
            path = travel_service_url + "/api/v1/travelservice/routes/" + tripId;
        } else {
            path = travel2_service_url + "/api/v1/travel2service/routes/" + tripId;
        }
        HttpEntity requestEntity = new HttpEntity(null);
        ResponseEntity<Response<Route>> re = restTemplate.exchange(
                path,
                HttpMethod.GET,
                requestEntity,
                new ParameterizedTypeReference<Response<Route>>() {
                });
        Route route = re.getBody().getData();
        return route.getStations();
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-route-plan-service/src/main/java/plan/service/RoutePlanServiceImpl.java:RoutePlanServiceImpl.<init>
package adminroute.controller;

import edu.fudan.common.entity.RouteInfo;
import adminroute.service.AdminRouteService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.web.bind.annotation.*;

import static org.springframework.http.ResponseEntity.ok;

/**
 * @author fdse
 */
@RestController
@RequestMapping("/api/v1/adminrouteservice")
public class AdminRouteController {

    @Autowired
    AdminRouteService adminRouteService;

    public static final Logger logger = LoggerFactory.getLogger(AdminRouteController.class);

    @GetMapping(path = "/welcome")
    public String home(@RequestHeader HttpHeaders headers) {
        return "Welcome to [ AdminRoute Service ] !";
    }

    @CrossOrigin(origins = "*")
    @GetMapping(path = "/adminroute")
    public HttpEntity getAllRoutes(@RequestHeader HttpHeaders headers) {
        logger.info("[getAllRoutes][Get all routes request]");
        return ok(adminRouteService.getAllRoutes(headers));
    }

    @PostMapping(value = "/adminroute")
    public HttpEntity addRoute(@RequestBody RouteInfo request, @RequestHeader HttpHeaders headers) {
        logger.info("[addRoute][Create and modify route][route id: {}, from station {} to station {}]",
                request.getId(), request.getStartStation(), request.getEndStation());
        return ok(adminRouteService.createAndModifyRoute(request, headers));
    }

    @DeleteMapping(value = "/adminroute/{routeId}")
    public HttpEntity deleteRoute(@PathVariable String routeId, @RequestHeader HttpHeaders headers) {
        logger.info("[deleteRoute][Delete route][route id: {}]", routeId);
        return ok(adminRouteService.deleteRoute(routeId, headers));
    }


}


// Node: repos/cloned_ms_repos/train-ticket/ts-admin-route-service/src/main/java/adminroute/controller/AdminRouteController.java:AdminRouteController.<init>
package adminroute.service;

import edu.fudan.common.entity.Route;
import edu.fudan.common.entity.RouteInfo;
import edu.fudan.common.util.Response;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.cloud.client.discovery.DiscoveryClient;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/**
 * @author fdse
 */
@Service
public class AdminRouteServiceImpl implements AdminRouteService {
    @Autowired
    private RestTemplate restTemplate;
    @Autowired
    private DiscoveryClient discoveryClient;

    public static final Logger logger = LoggerFactory.getLogger(AdminRouteServiceImpl.class);

    private String getServiceUrl(String serviceName) {
        return "http://" + serviceName;
    }

    @Override
    public Response getAllRoutes(HttpHeaders headers) {

        HttpEntity requestEntity = new HttpEntity(null);
        String route_service_url = getServiceUrl("ts-route-service");
        ResponseEntity<Response> re = restTemplate.exchange(
                 route_service_url + "/api/v1/routeservice/routes",
                HttpMethod.GET,
                requestEntity,
                Response.class);
        if (re.getStatusCode() != HttpStatus.ACCEPTED) {
            logger.error("[getAllRoutes][receive response][Get routes error][response code: {}]", re.getStatusCodeValue());
        }
        return re.getBody();

    }

    @Override
    public Response createAndModifyRoute(RouteInfo request, HttpHeaders headers) {
        // check stations
        String start = request.getStartStation();
        String end = request.getEndStation();
        List<String> stations = request.getStations();
        if(!stations.contains(start) || !stations.contains(end)){
            logger.error("[createAndModifyRoute][check stations][start or end not included in stationList][start: {}, end: {}]", start, end);
            return new Response(0, "start or end station not include in stationList.", null);
        }

        Response response = checkStationsExists(stations, headers);
        if(response.getStatus() ==0) {
            return response;
        }

        HttpEntity requestEntity = new HttpEntity(request, null);
        String route_service_url = getServiceUrl("ts-route-service");
        ResponseEntity<Response<Route>> re = restTemplate.exchange(
                route_service_url + "/api/v1/routeservice/routes",
                HttpMethod.POST,
                requestEntity,
                new ParameterizedTypeReference<Response<Route>>() {
                });
        if (re.getStatusCode() != HttpStatus.ACCEPTED) {
            logger.error("[createAndModifyRoute][receive response][Get status error][response code: {}]", re.getStatusCodeValue());
        }
        return re.getBody();
    }

    @Override
    public Response deleteRoute(String routeId, HttpHeaders headers) {

        HttpEntity requestEntity = new HttpEntity(null);
        String route_service_url = getServiceUrl("ts-route-service");
        ResponseEntity<Response> re = restTemplate.exchange(
                route_service_url + "/api/v1/routeservice/routes/" + routeId,
                HttpMethod.DELETE,
                requestEntity,
                Response.class);
        if (re.getStatusCode() != HttpStatus.ACCEPTED) {
            logger.error("[deleteRoute][response response][Delete error][response code: {}]", re.getStatusCodeValue());
        }
        return re.getBody();

    }

    public Response checkStationsExists(List<String> stationNames, HttpHeaders headers) {
        logger.info("[checkStationsExists][Check Stations Exists][stationNames: {}]", stationNames);
        HttpEntity requestEntity = new HttpEntity(stationNames, null);
        String station_service_url=getServiceUrl("ts-station-service");
        ResponseEntity<Response> re = restTemplate.exchange(
                station_service_url + "/api/v1/stationservice/stations/idlist",
                HttpMethod.POST,
                requestEntity,
                Response.class);
        Response<Map<String, String>> r = re.getBody();
        if(r.getStatus() == 0) {
            return r;
        }
        Map<String, String> stationMap = r.getData();
        List<String> notExists = new ArrayList<>();
        for(Map.Entry<String, String> s : stationMap.entrySet()){
            if(s.getValue() == null ){
                // station not exist
                notExists.add(s.getKey());
            }
        }
        if(notExists.size() > 0) {
            return new Response<>(0, "some station not exists", notExists);
        }
        return new Response<>(1, "check stations Exist succeed", null);
    }
}

// Node: repos/cloned_ms_repos/train-ticket/ts-admin-route-service/src/main/java/adminroute/service/AdminRouteServiceImpl.java:AdminRouteServiceImpl.<init>
package com.trainticket.controller;

import com.trainticket.entity.Payment;
import com.trainticket.service.PaymentService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.web.bind.annotation.*;

import static org.springframework.http.ResponseEntity.ok;

/**
 * @author Chenjie
 * @date 2017/4/7
 */
@RestController
@RequestMapping("/api/v1/paymentservice")
public class PaymentController {

    @Autowired
    PaymentService service;

    private static final Logger LOGGER = LoggerFactory.getLogger(PaymentController.class);

    @GetMapping(path = "/welcome")
    public String home() {
        return "Welcome to [ Payment Service ] !";
    }

    @PostMapping(path = "/payment")
    public HttpEntity pay(@RequestBody Payment info, @RequestHeader HttpHeaders headers) {
        PaymentController.LOGGER.info("[pay][Pay][PaymentId: {}]", info.getId());
        return ok(service.pay(info, headers));
    }

    @PostMapping(path = "/payment/money")
    public HttpEntity addMoney(@RequestBody Payment info, @RequestHeader HttpHeaders headers) {
        PaymentController.LOGGER.info("[addMoney][Add money][PaymentId: {}]", info.getId());
        return ok(service.addMoney(info, headers));
    }

    @GetMapping(path = "/payment")
    public HttpEntity query(@RequestHeader HttpHeaders headers) {
        PaymentController.LOGGER.info("[query][Query payment]");
        return ok(service.query(headers));
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-payment-service/src/main/java/com/trainticket/controller/PaymentController.java:PaymentController.<init>
package com.trainticket.service;

import com.trainticket.entity.Money;
import com.trainticket.entity.Payment;
import com.trainticket.repository.AddMoneyRepository;
import com.trainticket.repository.PaymentRepository;
import edu.fudan.common.util.Response;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpHeaders;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Optional;

/**
 * @author  Administrator
 * @date 2017/6/23.
 */
@Service
public class PaymentServiceImpl implements PaymentService{

    @Autowired
    PaymentRepository paymentRepository;

    @Autowired
    AddMoneyRepository addMoneyRepository;

    private static final Logger LOGGER = LoggerFactory.getLogger(PaymentServiceImpl.class);

    @Override
    public Response pay(Payment info, HttpHeaders headers){

        if(paymentRepository.findByOrderId(info.getOrderId()) == null){
            Payment payment = new Payment();
            payment.setOrderId(info.getOrderId());
            payment.setPrice(info.getPrice());
            payment.setUserId(info.getUserId());
            paymentRepository.save(payment);
            return new Response<>(1, "Pay Success", null);
        }else{
            PaymentServiceImpl.LOGGER.warn("[pay][Pay Failed][Order not found with order id][PaymentId: {}, OrderId: {}]",info.getId(),info.getOrderId());
            return new Response<>(0, "Pay Failed, order not found with order id" +info.getOrderId(), null);
        }
    }

    @Override
    public Response addMoney(Payment info, HttpHeaders headers){
        Money addMoney = new Money();
        addMoney.setUserId(info.getUserId());
        addMoney.setMoney(info.getPrice());
        addMoneyRepository.save(addMoney);
        return new Response<>(1,"Add Money Success", addMoney);
    }

    @Override
    public Response query(HttpHeaders headers){
        List<Payment> payments = paymentRepository.findAll();
        if(payments!= null && !payments.isEmpty()){
            PaymentServiceImpl.LOGGER.info("[query][Find all payment Success][size:{}]",payments.size());
            return new Response<>(1,"Query Success",  payments);
        }else {
            PaymentServiceImpl.LOGGER.warn("[query][Find all payment warn][{}]","No content");
            return new Response<>(0, "No Content", null);
        }
    }

    @Override
    public void initPayment(Payment payment, HttpHeaders headers){
        Optional<Payment> paymentTemp = paymentRepository.findById(payment.getId());
        if(!paymentTemp.isPresent()){
            paymentRepository.save(payment);
            PaymentServiceImpl.LOGGER.error("[initPayment][Init payment error][Payment not found][PaymentId: {}]",payment.getId());
        }else{
            PaymentServiceImpl.LOGGER.info("[initPayment][Init Payment Already Exists][PaymentId: {}]", payment.getId());
        }
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-payment-service/src/main/java/com/trainticket/service/PaymentServiceImpl.java:PaymentServiceImpl.<init>
package price.controller;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import price.entity.PriceConfig;
import price.service.PriceService;

import java.util.List;
import java.util.Map;

import static org.springframework.http.ResponseEntity.ok;

/**
 * @author fdse
 */
@RestController
@RequestMapping("/api/v1/priceservice")
public class PriceController {

    @Autowired
    PriceService service;

    private static final Logger LOGGER = LoggerFactory.getLogger(PriceController.class);

    @GetMapping(path = "/prices/welcome")
    public String home() {
        return "Welcome to [ Price Service ] !";
    }

    @GetMapping(value = "/prices/{routeId}/{trainType}")
    public HttpEntity query(@PathVariable String routeId, @PathVariable String trainType,
                            @RequestHeader HttpHeaders headers) {
        PriceController.LOGGER.info("[findByRouteIdAndTrainType][Query price][RouteId: {}, TrainType: {}]",routeId,trainType);
        return ok(service.findByRouteIdAndTrainType(routeId, trainType, headers));
    }

    @PostMapping(value = "/prices/byRouteIdsAndTrainTypes")
    public HttpEntity query(@RequestBody List<String> ridsAndTts,
                            @RequestHeader HttpHeaders headers) {
        PriceController.LOGGER.info("[findByRouteIdAndTrainType][Query price][routeId and Train Type: {}]", ridsAndTts);
        return ok(service.findByRouteIdsAndTrainTypes(ridsAndTts, headers));
    }

    @GetMapping(value = "/prices")
    public HttpEntity queryAll(@RequestHeader HttpHeaders headers) {
        PriceController.LOGGER.info("[findAllPriceConfig][Query all prices]");
        return ok(service.findAllPriceConfig(headers));
    }

    @PostMapping(value = "/prices")
    public HttpEntity<?> create(@RequestBody PriceConfig info,
                                @RequestHeader HttpHeaders headers) {
        PriceController.LOGGER.info("[createNewPriceConfig][Create price][RouteId: {}, TrainType: {}]",info.getRouteId(),info.getTrainType());
        return new ResponseEntity<>(service.createNewPriceConfig(info, headers), HttpStatus.CREATED);
    }

    @DeleteMapping(value = "/prices/{pricesId}")
    public HttpEntity delete(@PathVariable String pricesId, @RequestHeader HttpHeaders headers) {
        PriceController.LOGGER.info("[deletePriceConfig][Delete price][PriceConfigId: {}]",pricesId);
        return ok(service.deletePriceConfig(pricesId, headers));
    }

    @PutMapping(value = "/prices")
    public HttpEntity update(@RequestBody PriceConfig info, @RequestHeader HttpHeaders headers) {
        PriceController.LOGGER.info("[updatePriceConfig][Update price][PriceConfigId: {}]",info.getId());
        return ok(service.updatePriceConfig(info, headers));
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-price-service/src/main/java/price/controller/PriceController.java:PriceController.<init>
// Node: findByRouteIdAndTrainType
// Node: findByRouteIdsAndTrainTypes
// Node: findAllPriceConfig
// Node: PutMapping
// Node: updatePriceConfig
package price.repository;

import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.CrudRepository;
import org.springframework.stereotype.Repository;
import price.entity.PriceConfig;
import java.util.List;
import java.util.Optional;

/**
 * @author fdse
 */
@Repository
public interface PriceConfigRepository extends CrudRepository<PriceConfig, String> {

    @Override
    Optional<PriceConfig> findById(String id);

    PriceConfig findByRouteIdAndTrainType(String routeId,String trainType);

    @Query(value="SELECT * FROM price_config WHERE route_id IN ?1 AND train_type IN ?2", nativeQuery = true)
    List<PriceConfig> findByRouteIdsAndTrainTypes(List<String> routeIds, List<String> trainTypes);

    @Override
    List<PriceConfig> findAll();

}


// Node: repos/cloned_ms_repos/train-ticket/ts-price-service/src/main/java/price/repository/PriceConfigRepository.java:PriceConfigRepository.<init>
package price.service;

import edu.fudan.common.util.Response;
import org.springframework.http.HttpHeaders;

import price.entity.PriceConfig;

import java.util.List;
import java.util.Map;


/**
 * @author fdse
 */
public interface PriceService {

    Response createNewPriceConfig(PriceConfig priceConfig, HttpHeaders headers);

    PriceConfig findById(String id, HttpHeaders headers);

    Response findByRouteIdsAndTrainTypes(List<String> ridsAndTts, HttpHeaders headers);

    Response findByRouteIdAndTrainType(String routeId, String trainType, HttpHeaders headers);

    Response findAllPriceConfig(HttpHeaders headers);

    Response deletePriceConfig(String pcId, HttpHeaders headers);

    Response updatePriceConfig(PriceConfig c, HttpHeaders headers);

}


// Node: repos/cloned_ms_repos/train-ticket/ts-price-service/src/main/java/price/service/PriceService.java:PriceService.<init>
package notification.mq;

import edu.fudan.common.util.JsonUtils;
import edu.fudan.common.util.Response;
import notification.config.Queues;
import notification.entity.Mail;
import notification.entity.NotifyInfo;
import notification.repository.NotifyRepository;
import notification.service.MailService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.amqp.rabbit.annotation.RabbitHandler;
import org.springframework.amqp.rabbit.annotation.RabbitListener;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.HttpMethod;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

@Component
public class RabbitReceive {

    private static final Logger logger = LoggerFactory.getLogger(RabbitReceive.class);

    @Autowired
    MailService mailService;

    @Autowired
    private RestTemplate restTemplate;

    @Autowired
    private NotifyRepository notifyRepository;

    @Value("${email_address:trainticket_notify@163.com}")
    String email;
    String username = "username";
    String startPlace = "startPlace";
    String endPlace = "endPlace";
    String startTime = "startTime";
    String seatClass = "seatClass";
    String seatNumber = "seatNumber";
    String date = "date";
    String price = "price";

    @RabbitListener(queues = Queues.queueName)
    public void process(String payload) {
        NotifyInfo info = JsonUtils.json2Object(payload, NotifyInfo.class);

        if (info == null) {
            logger.error("[process][json2Object][Receive email object is null, error]");
            return;
        }

        logger.info("[process][Receive email object][info: {}]", info);

        Mail mail = new Mail();
        mail.setMailFrom(email);
        mail.setMailTo(info.getEmail());
        mail.setMailSubject("Preserve Success");

        Map<String, Object> model = new HashMap<>();
        model.put(username, info.getUsername());
        model.put(startPlace,info.getStartPlace());
        model.put(endPlace,info.getEndPlace());
        model.put(startTime,info.getStartTime());
        model.put(date,info.getDate());
        model.put(seatClass,info.getSeatClass());
        model.put(seatNumber,info.getSeatNumber());
        model.put(price,info.getPrice());
        mail.setModel(model);

        try {
            mailService.sendEmail(mail, "preserve_success.ftl");
            logger.info("[process][Send email to user {} success]", username);
            info.setSendStatus(true);
        } catch (Exception e) {
            logger.error("[process][mailService.sendEmail][Send email error][Exception: {}]", e.getMessage());
            info.setSendStatus(false);
        }


        info.setId(UUID.randomUUID().toString());
        logger.info("[process][Save notify info object [{}] into database]", info.getId());
        notifyRepository.save(info);
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-notification-service/src/main/java/notification/mq/RabbitReceive.java:RabbitReceive.<init>
// Node: RabbitListener
package notification.mq;

import notification.config.Queues;
import org.springframework.amqp.core.AmqpTemplate;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@Component
public class RabbitSend {

    @Autowired
    private AmqpTemplate rabbitTemplate;
    private static final Logger logger = LoggerFactory.getLogger(RabbitSend.class);

    public void send(String val) {
        logger.info("send val:" + val);
        this.rabbitTemplate.convertAndSend(Queues.queueName, val);
    }

}


// Node: repos/cloned_ms_repos/train-ticket/ts-notification-service/src/main/java/notification/mq/RabbitSend.java:RabbitSend.<init>
package notification.controller;

import notification.entity.NotifyInfo;
import notification.mq.RabbitSend;
import notification.service.NotificationService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpHeaders;
import org.springframework.web.bind.annotation.*;

/**
 * @author Wenvi
 * @date 2017/6/15
 */
@RestController
@RequestMapping("/api/v1/notifyservice")
public class NotificationController {

    @Autowired
    NotificationService service;

    @Autowired
    RabbitSend sender;

    @Value("${test_send_mail_user}")
    String test_mail_user;

    @GetMapping(path = "/welcome")
    public String home() {
        return "Welcome to [ Notification Service ] !";
    }

    @GetMapping("/test_send_mq")
    public boolean test_send() {
        sender.send("test");
        return true;
    }

    @GetMapping("/test_send_mail")
    public boolean test_send_mail() {
        NotifyInfo notifyInfo = new NotifyInfo();
        notifyInfo.setDate("Wed Jul 21 09:49:44 CST 2021");
        notifyInfo.setEmail(test_mail_user);
        notifyInfo.setEndPlace("Test");
        notifyInfo.setStartPlace("Test");
        notifyInfo.setOrderNumber("111-111-111");
        notifyInfo.setPrice("100");
        notifyInfo.setSeatClass("1");
        notifyInfo.setSeatNumber("1102");
        notifyInfo.setStartTime("Sat May 04 07:00:00 CST 2013");
        notifyInfo.setUsername("h10g");

        service.preserveSuccess(notifyInfo, null);
        return true;
    }

    @PostMapping(value = "/notification/preserve_success")
    public boolean preserve_success(@RequestBody NotifyInfo info, @RequestHeader HttpHeaders headers) {
        return service.preserveSuccess(info, headers);
    }

    @PostMapping(value = "/notification/order_create_success")
    public boolean order_create_success(@RequestBody NotifyInfo info, @RequestHeader HttpHeaders headers) {
        return service.orderCreateSuccess(info, headers);
    }

    @PostMapping(value = "/notification/order_changed_success")
    public boolean order_changed_success(@RequestBody NotifyInfo info, @RequestHeader HttpHeaders headers) {
        return service.orderChangedSuccess(info, headers);
    }

    @PostMapping(value = "/notification/order_cancel_success")
    public boolean order_cancel_success(@RequestBody NotifyInfo info, @RequestHeader HttpHeaders headers) {
        return service.orderCancelSuccess(info, headers);
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-notification-service/src/main/java/notification/controller/NotificationController.java:NotificationController.<init>
// Node: test_send
package notification.service;

import notification.entity.Mail;
import notification.entity.NotifyInfo;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpHeaders;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.stereotype.Service;
import java.util.HashMap;
import java.util.Map;

/**
 * @author fdse
 */
@Service
public class NotificationServiceImpl implements NotificationService{

    @Autowired
    private JavaMailSender mailSender;

    @Autowired
    MailService mailService;

    private static final Logger LOGGER = LoggerFactory.getLogger(NotificationServiceImpl.class);

    String email = "trainticket_notify@163.com";
    String username = "username";
    String startPlace = "startPlace";
    String endPlace = "endPlace";
    String startTime = "startTime";
    String seatClass = "seatClass";
    String seatNumber = "seatNumber";

    @Override
    public boolean preserveSuccess(NotifyInfo info, HttpHeaders headers){
        Mail mail = new Mail();
        mail.setMailFrom(email);
        mail.setMailTo(info.getEmail());
        mail.setMailSubject("Preserve Success");

        Map<String, Object> model = new HashMap<>();
        model.put(username, info.getUsername());
        model.put(startPlace,info.getStartPlace());
        model.put(endPlace,info.getEndPlace());
        model.put(startTime,info.getStartTime());
        model.put("date",info.getDate());
        model.put(seatClass,info.getSeatClass());
        model.put(seatNumber,info.getSeatNumber());
        model.put("price",info.getPrice());
        mail.setModel(model);

        try {
            mailService.sendEmail(mail,"preserve_success.ftl");
            return true;
        } catch (Exception e) {
            LOGGER.error("[preserveSuccess][mailService.sendEmai][Exception: {}]", e.getMessage());
            return false;
        }
    }

    @Override
    public boolean orderCreateSuccess(NotifyInfo info, HttpHeaders headers){
        Mail mail = new Mail();
        mail.setMailFrom(email);
        mail.setMailTo(info.getEmail());
        mail.setMailSubject("Order Create Success");

        Map<String, Object> model = new HashMap<>();
        model.put(username, info.getUsername());
        model.put(startPlace,info.getStartPlace());
        model.put(endPlace,info.getEndPlace());
        model.put(startTime,info.getStartTime());
        model.put("date",info.getDate());
        model.put(seatClass,info.getSeatClass());
        model.put(seatNumber,info.getSeatNumber());
        model.put("orderNumber", info.getOrderNumber());
        mail.setModel(model);

        try {
            mailService.sendEmail(mail,"order_create_success.ftl");
            return true;
        } catch (Exception e) {
            LOGGER.error("[orderCreateSuccess][mailService.sendEmai][Exception: {}]", e.getMessage());
            return false;
        }
    }

    @Override
    public boolean orderChangedSuccess(NotifyInfo info, HttpHeaders headers){
        Mail mail = new Mail();
        mail.setMailFrom(email);
        mail.setMailTo(info.getEmail());
        mail.setMailSubject("Order Changed Success");

        Map<String, Object> model = new HashMap<>();
        model.put(username, info.getUsername());
        model.put(startPlace,info.getStartPlace());
        model.put(endPlace,info.getEndPlace());
        model.put(startTime,info.getStartTime());
        model.put("date",info.getDate());
        model.put(seatClass,info.getSeatClass());
        model.put(seatNumber,info.getSeatNumber());
        model.put("orderNumber", info.getOrderNumber());
        mail.setModel(model);

        try {
            mailService.sendEmail(mail,"order_changed_success.ftl");
            return true;
        } catch (Exception e) {
            LOGGER.error("[orderChangedSuccess][mailService.sendEmai][Exception: {}]", e.getMessage());
            return false;
        }
    }

    @Override
    public boolean orderCancelSuccess(NotifyInfo info, HttpHeaders headers){
        Mail mail = new Mail();
        mail.setMailFrom(email);
        mail.setMailTo(info.getEmail());
        mail.setMailSubject("Order Cancel Success");

        Map<String, Object> model = new HashMap<>();
        model.put(username, info.getUsername());
        model.put("price",info.getPrice());
        mail.setModel(model);

        try {
            mailService.sendEmail(mail,"order_cancel_success.ftl");
            return true;
        } catch (Exception e) {
            LOGGER.error("[orderCancelSuccess][mailService.sendEmai][Exception: {}]", e.getMessage());
            return false;
        }
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-notification-service/src/main/java/notification/service/NotificationServiceImpl.java:NotificationServiceImpl.<init>
package fdse.microservice.controller;

import edu.fudan.common.entity.Travel;
import fdse.microservice.service.BasicService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.web.bind.annotation.*;

import java.util.List;

import static org.springframework.http.ResponseEntity.ok;

/**
 * @author Chenjie
 * @date 2017/6/6.
 */
@RestController
@RequestMapping("/api/v1/basicservice")

public class BasicController {

    @Autowired
    BasicService service;

    private static final Logger logger = LoggerFactory.getLogger(BasicController.class);

    @GetMapping(path = "/welcome")
    public String home(@RequestHeader HttpHeaders headers) {
        return "Welcome to [ Basic Service ] !";
    }

    @PostMapping(value = "/basic/travel")
    public HttpEntity queryForTravel(@RequestBody Travel info, @RequestHeader HttpHeaders headers) {
        // TravelResult
        logger.info("[queryForTravel][Query for travel][Travel: {}]", info.toString());
        return ok(service.queryForTravel(info, headers));
    }

    @PostMapping(value = "/basic/travels")
    public HttpEntity queryForTravels(@RequestBody List<Travel> infos, @RequestHeader HttpHeaders headers) {
        // TravelResult
        logger.info("[queryForTravels][Query for travels][Travels: {}]", infos);
        return ok(service.queryForTravels(infos, headers));
    }

    @GetMapping(value = "/basic/{stationName}")
    public HttpEntity queryForStationId(@PathVariable String stationName, @RequestHeader HttpHeaders headers) {
        // String id
        logger.info("[queryForStationId][Query for stationId by stationName][stationName: {}]", stationName);
        return ok(service.queryForStationId(stationName, headers));
    }

}


// Node: repos/cloned_ms_repos/train-ticket/ts-basic-service/src/main/java/fdse/microservice/controller/BasicController.java:BasicController.<init>
// Node: queryForTravel
// Node: queryForTravels
package fdse.microservice.service;

import edu.fudan.common.entity.Travel;
import edu.fudan.common.util.Response;
import edu.fudan.common.entity.*;
import org.springframework.http.HttpHeaders;

import java.util.List;

/**
 * @author Chenjie
 * @date 2017/6/6.
 */
public interface BasicService {

    /**
     * query for travel with travel information
     *
     * @param info information
     * @param  headers headers
     * @return Response
     */
    Response queryForTravel(Travel info, HttpHeaders headers);

    Response queryForTravels(List<Travel> infos, HttpHeaders headers);

    /**
     * query for station id with station name
     *
     * @param stationName station name
     * @param  headers headers
     * @return Response
     */
    Response queryForStationId(String stationName, HttpHeaders headers);
}


// Node: repos/cloned_ms_repos/train-ticket/ts-basic-service/src/main/java/fdse/microservice/service/BasicService.java:BasicService.<init>
package fdse.microservice.service;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import edu.fudan.common.entity.*;
import edu.fudan.common.util.JsonUtils;
import edu.fudan.common.util.Response;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.cloud.client.discovery.DiscoveryClient;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.util.*;

/**
 * @author fdse
 */
@Service
public class BasicServiceImpl implements BasicService {

    @Autowired
    private RestTemplate restTemplate;

    @Autowired
    private DiscoveryClient discoveryClient;

    private static final Logger LOGGER = LoggerFactory.getLogger(BasicServiceImpl.class);

    private String getServiceUrl(String serviceName) {
        return "http://" + serviceName;
    }

    @Override
    public Response queryForTravel(Travel info, HttpHeaders headers) {

        Response response = new Response<>();
        TravelResult result = new TravelResult();
        result.setStatus(true);
        response.setStatus(1);
        response.setMsg("Success");
        String start = info.getStartPlace();
        String end = info.getEndPlace();
        boolean startingPlaceExist = checkStationExists(start, headers);
        boolean endPlaceExist = checkStationExists(end, headers);
        if (!startingPlaceExist || !endPlaceExist) {
            result.setStatus(false);
            response.setStatus(0);
            response.setMsg("Start place or end place not exist!");
            if (!startingPlaceExist)
                BasicServiceImpl.LOGGER.warn("[queryForTravel][Start place not exist][start place: {}]", info.getStartPlace());
            if (!endPlaceExist)
                BasicServiceImpl.LOGGER.warn("[queryForTravel][End place not exist][end place: {}]", info.getEndPlace());
        }

        TrainType trainType = queryTrainTypeByName(info.getTrip().getTrainTypeName(), headers);
        if (trainType == null) {
            BasicServiceImpl.LOGGER.warn("[queryForTravel][traintype doesn't exist][trainTypeName: {}]", info.getTrip().getTrainTypeName());
            result.setStatus(false);
            response.setStatus(0);
            response.setMsg("Train type doesn't exist");
            return response;
        } else {
            result.setTrainType(trainType);
        }

        String routeId = info.getTrip().getRouteId();
        Route route = getRouteByRouteId(routeId, headers);
        if(route == null){
            result.setStatus(false);
            response.setStatus(0);
            response.setMsg("Route doesn't exist");
            return response;
        }

        //Check the route list for this train. Check that the required start and arrival stations are in the list of stops that are not on the route, and check that the location of the start station is before the stop
        //Trains that meet the above criteria are added to the return list
        int indexStart = 0;
        int indexEnd = 0;
        if (route.getStations().contains(start) &&
                route.getStations().contains(end) &&
                route.getStations().indexOf(start) < route.getStations().indexOf(end)){
            indexStart = route.getStations().indexOf(start);
            indexEnd = route.getStations().indexOf(end);
            LOGGER.info("[queryForTravel][query start index and end index][indexStart: {} indexEnd: {}]", indexStart, indexEnd);
            LOGGER.info("[queryForTravel][query stations and distances][stations: {} distances: {}]", route.getStations(), route.getDistances());
        }else {
            result.setStatus(false);
            response.setStatus(0);
            response.setMsg("Station not correct in Route");
            return response;
        }
        PriceConfig priceConfig = queryPriceConfigByRouteIdAndTrainType(routeId, trainType.getName(), headers);
        HashMap<String, String> prices = new HashMap<>();
        try {
            int distance = 0;
            distance = route.getDistances().get(indexEnd) - route.getDistances().get(indexStart);
            /**
             * We need the price Rate and distance (starting station).
             */
            double priceForEconomyClass = distance * priceConfig.getBasicPriceRate();
            double priceForConfortClass = distance * priceConfig.getFirstClassPriceRate();
            prices.put("economyClass", "" + priceForEconomyClass);
            prices.put("confortClass", "" + priceForConfortClass);
        }catch (Exception e){
                prices.put("economyClass", "95.0");
                prices.put("confortClass", "120.0");
        }
        result.setRoute(route);
        result.setPrices(prices);
        result.setPercent(1.0);
        response.setData(result);
        BasicServiceImpl.LOGGER.info("[queryForTravel][all done][result: {}]", result);

        return response;
    }

    @Override
    public Response queryForTravels(List<Travel> infos, HttpHeaders headers) {
        Response response = new Response<>();
        response.setStatus(1);
        response.setMsg("Success");

        HashMap<String, Travel> tripInfos = new HashMap<>();
        HashMap<String, List<String>> startTrips = new HashMap<>();
        HashMap<String, List<String>> endTrips = new HashMap<>();
        HashMap<String, List<String>> routeTrips = new HashMap<>();
        HashMap<String, List<String>> typeTrips = new HashMap<>();
        Set<String> stationNames = new HashSet<>();
        Set<String> trainTypeNames = new HashSet<>();
        Set<String> routeIds = new HashSet<>();
        Set<String> avaTrips = new HashSet<>();
        for(Travel info: infos){
            stationNames.add(info.getStartPlace());
            stationNames.add(info.getEndPlace());
            trainTypeNames.add(info.getTrip().getTrainTypeName());
            routeIds.add(info.getTrip().getRouteId());

            String tripNumber = info.getTrip().getTripId().toString();
            avaTrips.add(tripNumber);
            tripInfos.put(tripNumber, info);

            String start = info.getStartPlace();
            List<String> trips = startTrips.get(start);
            if(trips == null) {
               trips = new ArrayList<>();
            }
            trips.add(tripNumber);
            startTrips.put(start, trips);

            String end = info.getEndPlace();
            trips = endTrips.get(end);
            if(trips == null) {
                trips = new ArrayList<>();
            }
            trips.add(tripNumber);
            endTrips.put(end, trips);

            String routeId = info.getTrip().getRouteId();
            trips = routeTrips.get(routeId);
            if(trips == null) {
                trips = new ArrayList<>();
            }
            trips.add(tripNumber);
            routeTrips.put(routeId, trips);

            String trainTypeName = info.getTrip().getTrainTypeName();
            trips = typeTrips.get(trainTypeName);
            if(trips == null) {
                trips = new ArrayList<>();
            }
            trips.add(tripNumber);
            typeTrips.put(trainTypeName, trips);
        }

        //List<String> invalidTrips = new ArrayList<>();

        // check if station exist to exclude invalid travel info
        Map<String, String> stationMap = checkStationsExists(new ArrayList<>(stationNames), headers);
        if(stationMap == null) {
            response.setStatus(0);
            response.setMsg("all stations don't exist");
            return response;
        }
        for(Map.Entry<String, String> s : stationMap.entrySet()){
            if(s.getValue() == null ){
                // station not exist
                if(startTrips.get(s.getKey()) != null){
                    avaTrips.removeAll(startTrips.get(s.getKey()));
                }
                if(endTrips.get(s.getKey()) != null){
                    avaTrips.removeAll(endTrips.get(s.getKey()));
                }
            }
        }

        if(avaTrips.size() == 0){
            response.setStatus(0);
            response.setMsg("no travel info available");
            return response;
        }

        // check if train_type exist
        List<TrainType> tts = queryTrainTypeByNames(new ArrayList<>(trainTypeNames), headers);
        if(tts == null){
            response.setStatus(0);
            response.setMsg("all train_type don't exist");
            return response;
        }
        Map<String, TrainType> trainTypeMap = new HashMap<>();
        for(TrainType t: tts){
            trainTypeMap.put(t.getName(), t);
        }
        for(Map.Entry<String, List<String>> typeTrip: typeTrips.entrySet()){
            String ttype = typeTrip.getKey();
            if(trainTypeMap.get(ttype) == null){
                avaTrips.removeAll(typeTrip.getValue());
            }
        }
        if(avaTrips.size() ==0){
            response.setStatus(0);
            response.setMsg("no travel info available");
            return response;
        }

        // check if route exist to exclude invalid travel info
        List<Route> routes = getRoutesByRouteIds(new ArrayList<>(routeIds), headers);
        if(routes == null) {
            response.setStatus(0);
            response.setMsg("all routes don't exist");
            return response;
        }
        Map<String, Route> routeMap = new HashMap<>();
        for(Route r: routes){
            routeMap.put(r.getId(), r);
        }
        for(Map.Entry<String, List<String>> routeTrip: routeTrips.entrySet()){
            String routeId = routeTrip.getKey();
            if(routeMap.get(routeId) == null){
                avaTrips.removeAll(routeTrip.getValue());
            }else{
                Route route = routeMap.get(routeId);
                List<String> trips = routeTrip.getValue();
                for(String t: trips){
                    String start = tripInfos.get(t).getStartPlace();
                    String end = tripInfos.get(t).getEndPlace();
                    if (!route.getStations().contains(start) ||
                            !route.getStations().contains(end) ||
                            route.getStations().indexOf(start) >= route.getStations().indexOf(end)){
                        avaTrips.remove(t);
                    }
                }
            }
        }
        if(avaTrips.size() == 0){
            response.setStatus(0);
            response.setMsg("no travel info available");
            return response;
        }

        List<String> routeIdAndTypes = new ArrayList<>();
        for(String tripNumber: avaTrips){
            String routeId = tripInfos.get(tripNumber).getTrip().getRouteId();
            String trainType = tripInfos.get(tripNumber).getTrip().getTrainTypeName();
            routeIdAndTypes.add(routeId+":"+trainType);
        }
        Map<String, PriceConfig> pcMap = queryPriceConfigByRouteIdsAndTrainTypes(routeIdAndTypes, headers);

        Map<String, TravelResult> trMap = new HashMap<>();
        for(String tripNumber: avaTrips){
            Travel info = tripInfos.get(tripNumber);
            String trainType = info.getTrip().getTrainTypeName();
            String routeId = info.getTrip().getRouteId();
            Route route = routeMap.get(routeId);

            int indexStart = route.getStations().indexOf(info.getStartPlace());
            int indexEnd = route.getStations().indexOf(info.getEndPlace());

            double basicPriceRate = 0.75;
            double firstPriceRate = 1;
            PriceConfig priceConfig = pcMap.get(routeId+":"+trainType);
            if(priceConfig != null){
                basicPriceRate = priceConfig.getBasicPriceRate();
                firstPriceRate = priceConfig.getFirstClassPriceRate();
            }

            HashMap<String, String> prices = new HashMap<>();
            try {
                int distance = 0;
                distance = route.getDistances().get(indexEnd) - route.getDistances().get(indexStart);
                /**
                 * We need the price Rate and distance (starting station).
                 */
                double priceForEconomyClass = distance * basicPriceRate;
                double priceForConfortClass = distance * firstPriceRate;
                prices.put("economyClass", "" + priceForEconomyClass);
                prices.put("confortClass", "" + priceForConfortClass);
            }catch (Exception e){
                prices.put("economyClass", "95.0");
                prices.put("confortClass", "120.0");
            }


            TravelResult result = new TravelResult();
            result.setStatus(true);
            result.setTrainType(trainTypeMap.get(trainType));
            result.setRoute(route);
            result.setPrices(prices);
            result.setPercent(1.0);

            trMap.put(tripNumber, result);
        }
        response.setData(trMap);
        BasicServiceImpl.LOGGER.info("[queryForTravels][all done][result map: {}]", trMap);
        return response;
    }

    @Override
    public Response queryForStationId(String stationName, HttpHeaders headers) {
        BasicServiceImpl.LOGGER.info("[queryForStationId][Query For Station Id][stationName: {}]", stationName);
        HttpEntity requestEntity = new HttpEntity(null);
        String station_service_url=getServiceUrl("ts-station-service");
        ResponseEntity<Response> re = restTemplate.exchange(
                station_service_url + "/api/v1/stationservice/stations/id/" + stationName,
                HttpMethod.GET,
                requestEntity,
                Response.class);
        if (re.getBody().getStatus() != 1) {
            String msg = re.getBody().getMsg();
            BasicServiceImpl.LOGGER.warn("[queryForStationId][Query for stationId error][stationName: {}, message: {}]", stationName, msg);
            return new Response<>(0, msg, null);
        }
        return  re.getBody();
    }

    public Map<String,String> checkStationsExists(List<String> stationNames, HttpHeaders headers) {
        BasicServiceImpl.LOGGER.info("[checkStationsExists][Check Stations Exists][stationNames: {}]", stationNames);
        HttpEntity requestEntity = new HttpEntity(stationNames, null);
        String station_service_url=getServiceUrl("ts-station-service");
        ResponseEntity<Response> re = restTemplate.exchange(
                station_service_url + "/api/v1/stationservice/stations/idlist",
                HttpMethod.POST,
                requestEntity,
                Response.class);
        Response<Map<String, String>> r = re.getBody();
        if(r.getStatus() == 0) {
            return null;
        }
        Map<String, String> stationMap = r.getData();
        return stationMap;
    }

    public boolean checkStationExists(String stationName, HttpHeaders headers) {
        BasicServiceImpl.LOGGER.info("[checkStationExists][Check Station Exists][stationName: {}]", stationName);
        HttpEntity requestEntity = new HttpEntity(null);
        String station_service_url=getServiceUrl("ts-station-service");
        ResponseEntity<Response> re = restTemplate.exchange(
                station_service_url + "/api/v1/stationservice/stations/id/" + stationName,
                HttpMethod.GET,
                requestEntity,
                Response.class);
        Response exist = re.getBody();

        return exist.getStatus() == 1;
    }

    public List<TrainType> queryTrainTypeByNames(List<String> trainTypeNames, HttpHeaders headers) {
        BasicServiceImpl.LOGGER.info("[queryTrainTypeByNames][Query Train Type][Train Type names: {}]", trainTypeNames);
        HttpEntity requestEntity = new HttpEntity(trainTypeNames, null);
        String train_service_url=getServiceUrl("ts-train-service");
        ResponseEntity<Response> re = restTemplate.exchange(
                train_service_url + "/api/v1/trainservice/trains/byNames",
                HttpMethod.POST,
                requestEntity,
                Response.class);
        Response<List<TrainType>>  response = re.getBody();
        if(response.getStatus() == 0){
            return null;
        }
        List<TrainType> tts = Arrays.asList(JsonUtils.conveterObject(response.getData(), TrainType[].class));
        return tts;
    }

    public TrainType queryTrainTypeByName(String trainTypeName, HttpHeaders headers) {
        BasicServiceImpl.LOGGER.info("[queryTrainTypeByName][Query Train Type][Train Type name: {}]", trainTypeName);
        HttpEntity requestEntity = new HttpEntity(null);
        String train_service_url=getServiceUrl("ts-train-service");
        ResponseEntity<Response> re = restTemplate.exchange(
                train_service_url + "/api/v1/trainservice/trains/byName/" + trainTypeName,
                HttpMethod.GET,
                requestEntity,
                Response.class);
        Response  response = re.getBody();

        return JsonUtils.conveterObject(response.getData(), TrainType.class);
    }

    private List<Route> getRoutesByRouteIds(List<String> routeIds, HttpHeaders headers) {
        BasicServiceImpl.LOGGER.info("[getRoutesByRouteIds][Get Route By Ids][Route IDs：{}]", routeIds);
        HttpEntity requestEntity = new HttpEntity(routeIds, null);
        String route_service_url=getServiceUrl("ts-route-service");
        ResponseEntity<Response> re = restTemplate.exchange(
                route_service_url + "/api/v1/routeservice/routes/byIds/",
                HttpMethod.POST,
                requestEntity,
                Response.class);
        Response<List<Route>> result = re.getBody();
        if ( result.getStatus() == 0) {
            BasicServiceImpl.LOGGER.warn("[getRoutesByRouteIds][Get Route By Ids Failed][Fail msg: {}]", result.getMsg());
            return null;
        } else {
            BasicServiceImpl.LOGGER.info("[getRoutesByRouteIds][Get Route By Ids][Success]");
            List<Route> routes = Arrays.asList(JsonUtils.conveterObject(result.getData(), Route[].class));;
            return routes;
        }
    }

    private Route getRouteByRouteId(String routeId, HttpHeaders headers) {
        BasicServiceImpl.LOGGER.info("[getRouteByRouteId][Get Route By Id][Route ID：{}]", routeId);
        HttpEntity requestEntity = new HttpEntity(null);
        String route_service_url=getServiceUrl("ts-route-service");
        ResponseEntity<Response> re = restTemplate.exchange(
                route_service_url + "/api/v1/routeservice/routes/" + routeId,
                HttpMethod.GET,
                requestEntity,
                Response.class);
        Response result = re.getBody();
        if ( result.getStatus() == 0) {
            BasicServiceImpl.LOGGER.warn("[getRouteByRouteId][Get Route By Id Failed][Fail msg: {}]", result.getMsg());
            return null;
        } else {
            BasicServiceImpl.LOGGER.info("[getRouteByRouteId][Get Route By Id][Success]");
            return JsonUtils.conveterObject(result.getData(), Route.class);
        }
    }

    private PriceConfig queryPriceConfigByRouteIdAndTrainType(String routeId, String trainType, HttpHeaders headers) {
        BasicServiceImpl.LOGGER.info("[queryPriceConfigByRouteIdAndTrainType][Query For Price Config][RouteId: {} ,TrainType: {}]", routeId, trainType);
        HttpEntity requestEntity = new HttpEntity(null, null);
        String price_service_url=getServiceUrl("ts-price-service");
        ResponseEntity<Response> re = restTemplate.exchange(
                price_service_url + "/api/v1/priceservice/prices/" + routeId + "/" + trainType,
                HttpMethod.GET,
                requestEntity,
                Response.class);
        Response result = re.getBody();

        BasicServiceImpl.LOGGER.info("[queryPriceConfigByRouteIdAndTrainType][Response Resutl to String][result: {}]", result.toString());
        return  JsonUtils.conveterObject(result.getData(), PriceConfig.class);
    }

    private Map<String, PriceConfig> queryPriceConfigByRouteIdsAndTrainTypes(List<String> routeIdsTypes, HttpHeaders headers) {
        BasicServiceImpl.LOGGER.info("[queryPriceConfigByRouteIdsAndTrainTypes][Query For Price Config][RouteId and TrainType: {}]", routeIdsTypes);
        HttpEntity requestEntity = new HttpEntity(routeIdsTypes, null);
        String price_service_url=getServiceUrl("ts-price-service");
        ResponseEntity<Response> re = restTemplate.exchange(
                price_service_url + "/api/v1/priceservice/prices/byRouteIdsAndTrainTypes",
                HttpMethod.POST,
                requestEntity,
                Response.class);
        Response<Map<String, PriceConfig>> result = re.getBody();

        Map<String, PriceConfig> pcMap;
        if ( result.getStatus() == 0) {
            BasicServiceImpl.LOGGER.warn("[queryPriceConfigByRouteIdsAndTrainTypes][Get Price Config by routeId and trainType Failed][Fail msg: {}]", result.getMsg());
            return null;
        } else {
            ObjectMapper mapper = new ObjectMapper();
            try{
                pcMap = mapper.readValue(JsonUtils.object2Json(result.getData()), new TypeReference<Map<String, PriceConfig>>(){});
            }catch(Exception e) {
                BasicServiceImpl.LOGGER.warn("[queryPriceConfigByRouteIdsAndTrainTypes][Get Price Config by routeId and trainType Failed][Fail msg: {}]", e.getMessage());
                return null;
            }
            BasicServiceImpl.LOGGER.info("[queryPriceConfigByRouteIdsAndTrainTypes][Get Price Config by routeId and trainType][Success][priceConfigs: {}]", result.getData());
            return pcMap;
        }
    }

}


// Node: repos/cloned_ms_repos/train-ticket/ts-basic-service/src/main/java/fdse/microservice/service/BasicServiceImpl.java:BasicServiceImpl.<init>
package other.controller;

import edu.fudan.common.entity.Seat;
import edu.fudan.common.util.StringUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.web.bind.annotation.*;


import other.entity.Order;
import other.entity.QueryInfo;
import other.service.OrderOtherService;

import java.util.Date;

import static org.springframework.http.ResponseEntity.ok;

/**
 * @author fdse
 */
@RestController
@RequestMapping("/api/v1/orderOtherService")
public class OrderOtherController {

    @Autowired
    private OrderOtherService orderService;

    private static final Logger LOGGER = LoggerFactory.getLogger(OrderOtherController.class);

    @GetMapping(path = "/welcome")
    public String home() {
        return "Welcome to [ Order Other Service ] !";
    }

    /***************************For Normal Use***************************/

    @PostMapping(value = "/orderOther/tickets")
    public HttpEntity getTicketListByDateAndTripId(@RequestBody Seat seatRequest, @RequestHeader HttpHeaders headers) {
        OrderOtherController.LOGGER.info("[getSoldTickets][Get Sold Ticket][Travel Date: {}]", seatRequest.getTravelDate().toString());
        return ok(orderService.getSoldTickets(seatRequest, headers));
    }

    @CrossOrigin(origins = "*")
    @PostMapping(path = "/orderOther")
    public HttpEntity createNewOrder(@RequestBody Order createOrder, @RequestHeader HttpHeaders headers) {
        OrderOtherController.LOGGER.info("[create][Create Order][from {} to {} at {}]", createOrder.getFrom(), createOrder.getTo(), createOrder.getTravelDate());
        return ok(orderService.create(createOrder, headers));
    }

    @CrossOrigin(origins = "*")
    @PostMapping(path = "/orderOther/admin")
    public HttpEntity addcreateNewOrder(@RequestBody Order order, @RequestHeader HttpHeaders headers) {
        OrderOtherController.LOGGER.info("[addNewOrder][Add new order][OrderId: {}]", order.getId());
        return ok(orderService.addNewOrder(order, headers));
    }

    @CrossOrigin(origins = "*")
    @PostMapping(path = "/orderOther/query")
    public HttpEntity queryOrders(@RequestBody QueryInfo qi,
                                  @RequestHeader HttpHeaders headers) {
        OrderOtherController.LOGGER.info("[queryOrders][Query Orders][for LoginId :{}]", qi.getLoginId());
        return ok(orderService.queryOrders(qi, qi.getLoginId(), headers));

    }

    @CrossOrigin(origins = "*")
    @PostMapping(path = "/orderOther/refresh")
    public HttpEntity queryOrdersForRefresh(@RequestBody QueryInfo qi,
                                            @RequestHeader HttpHeaders headers) {
        OrderOtherController.LOGGER.info("[queryOrdersForRefresh][Query Orders][for LoginId:{}]", qi.getLoginId());
        return ok(orderService.queryOrdersForRefresh(qi, qi.getLoginId(), headers));
    }


    @CrossOrigin(origins = "*")
    @GetMapping(path = "/orderOther/{travelDate}/{trainNumber}")
    public HttpEntity calculateSoldTicket(@PathVariable String travelDate, @PathVariable String trainNumber,
                                          @RequestHeader HttpHeaders headers) {
        OrderOtherController.LOGGER.info("[queryAlreadySoldOrders][Calculate Sold Tickets][Date: {} TrainNumber: {}]", travelDate, trainNumber);
        return ok(orderService.queryAlreadySoldOrders(StringUtils.String2Date(travelDate), trainNumber, headers));
    }

    @CrossOrigin(origins = "*")
    @GetMapping(path = "/orderOther/price/{orderId}")
    public HttpEntity getOrderPrice(@PathVariable String orderId, @RequestHeader HttpHeaders headers) {
        OrderOtherController.LOGGER.info("[getOrderPrice][Get Order Price][Order Id: {}]", orderId);
        return ok(orderService.getOrderPrice(orderId, headers));
    }

    @CrossOrigin(origins = "*")
    @GetMapping(path = "/orderOther/orderPay/{orderId}")
    public HttpEntity payOrder(@PathVariable String orderId, @RequestHeader HttpHeaders headers) {
        OrderOtherController.LOGGER.info("[payOrder][Pay Order][Order Id: {}]", orderId);
        return ok(orderService.payOrder(orderId, headers));
    }

    @CrossOrigin(origins = "*")
    @GetMapping(path = "/orderOther/{orderId}")
    public HttpEntity getOrderById(@PathVariable String orderId, @RequestHeader HttpHeaders headers) {
        OrderOtherController.LOGGER.info("[getOrderById][Get Order By Id][Order Id: {}]", orderId);
        return ok(orderService.getOrderById(orderId, headers));
    }

    @CrossOrigin(origins = "*")
    @GetMapping(path = "/orderOther/status/{orderId}/{status}")
    public HttpEntity modifyOrder(@PathVariable String orderId, @PathVariable int status, @RequestHeader HttpHeaders headers) {
        OrderOtherController.LOGGER.info("[modifyOrder][Modify Order Status][Order Id: {}]", orderId);
        return ok(orderService.modifyOrder(orderId, status, headers));
    }

    @CrossOrigin(origins = "*")
    @GetMapping(path = "/orderOther/security/{checkDate}/{accountId}")
    public HttpEntity securityInfoCheck(@PathVariable String checkDate, @PathVariable String accountId,
                                        @RequestHeader HttpHeaders headers) {
        OrderOtherController.LOGGER.info("[checkSecurityAboutOrder][Security Info Get][CheckDate:{} , AccountId:{}]",checkDate,accountId);
        return ok(orderService.checkSecurityAboutOrder(StringUtils.String2Date(checkDate), accountId, headers));
    }

    @CrossOrigin(origins = "*")
    @PutMapping(path = "/orderOther")
    public HttpEntity saveOrderInfo(@RequestBody Order orderInfo,
                                    @RequestHeader HttpHeaders headers) {

        OrderOtherController.LOGGER.info("[saveChanges][Save Order Info][OrderId:{}]",orderInfo.getId());
        return ok(orderService.saveChanges(orderInfo, headers));
    }

    @CrossOrigin(origins = "*")
    @PutMapping(path = "/orderOther/admin")
    public HttpEntity updateOrder(@RequestBody Order order, @RequestHeader HttpHeaders headers) {
        OrderOtherController.LOGGER.info("[updateOrder][Update Order][OrderId: {}]", order.getId());
        return ok(orderService.updateOrder(order, headers));
    }

    @CrossOrigin(origins = "*")
    @DeleteMapping(path = "/orderOther/{orderId}")
    public HttpEntity deleteOrder(@PathVariable String orderId, @RequestHeader HttpHeaders headers) {
        OrderOtherController.LOGGER.info("[deleteOrder][Delete Order][OrderId: {}]", orderId);
        return ok(orderService.deleteOrder(orderId, headers));
    }

    /***************For super admin(Single Service Test*******************/

    @CrossOrigin(origins = "*")
    @GetMapping(path = "/orderOther")
    public HttpEntity findAllOrder(@RequestHeader HttpHeaders headers) {
        OrderOtherController.LOGGER.info("[getAllOrders][Find All Order]");
        return ok(orderService.getAllOrders(headers));
    }

}


// Node: repos/cloned_ms_repos/train-ticket/ts-order-other-service/src/main/java/other/controller/OrderOtherController.java:OrderOtherController.<init>
// Node: getTicketListByDateAndTripId
// Node: getSoldTickets
// Node: addcreateNewOrder
// Node: addNewOrder
// Node: queryOrders
// Node: queryOrdersForRefresh
// Node: calculateSoldTicket
// Node: queryAlreadySoldOrders
// Node: getOrderPrice
// Node: payOrder
// Node: getOrderById
// Node: modifyOrder
// Node: securityInfoCheck
// Node: saveOrderInfo
// Node: admin
// Node: repos/cloned_ms_repos/train-ticket/ts-order-other-service/src/main/java/other/controller/OrderOtherController.java:OrderOtherController.findAllOrder
// Node: findAllOrder
package other.service;

import edu.fudan.common.entity.*;
import edu.fudan.common.util.Response;
import edu.fudan.common.util.StringUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.cloud.client.discovery.DiscoveryClient;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.ResponseEntity;
import org.springframework.web.client.RestTemplate;
import other.entity.*;
import other.entity.Order;
import other.entity.OrderAlterInfo;
import other.repository.OrderOtherRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.*;

/**
 * @author fdse
 */
@Service
public class OrderOtherServiceImpl implements OrderOtherService {

    @Autowired
    private OrderOtherRepository orderOtherRepository;

    @Autowired
    private RestTemplate restTemplate;

    private static final Logger LOGGER = LoggerFactory.getLogger(OrderOtherServiceImpl.class);

    @Autowired
    private DiscoveryClient discoveryClient;

    private String getServiceUrl(String serviceName) {
        return "http://" + serviceName;
    }

//    @Value("${station-service.url}")
//    String station_service_url;

    String success = "Success";
    String orderNotFound = "Order Not Found";

    @Override
    public Response getSoldTickets(Seat seatRequest, HttpHeaders headers) {
        ArrayList<Order> list = orderOtherRepository.findByTravelDateAndTrainNumber(seatRequest.getTravelDate(),
                seatRequest.getTrainNumber());
        if (list != null && !list.isEmpty()) {
            Set ticketSet = new HashSet();
            for (Order tempOrder : list) {
                Ticket ticket = new Ticket();
                ticket.setSeatNo(Integer.parseInt(tempOrder.getSeatNumber()));
                ticket.setStartStation(tempOrder.getFrom());
                ticket.setDestStation(tempOrder.getTo());
                ticketSet.add(ticket);
            }

            LeftTicketInfo leftTicketInfo = new LeftTicketInfo();
            leftTicketInfo.setSoldTickets(ticketSet);
            OrderOtherServiceImpl.LOGGER.info("[getSoldTickets][Left ticket info][info is: {}]", leftTicketInfo.toString());

            return new Response<>(1, success, leftTicketInfo);
        } else {

            OrderOtherServiceImpl.LOGGER.warn("[getSoldTickets][Seat][No content][seat from date: {}, train number: {}",seatRequest.getTravelDate(),seatRequest.getTrainNumber());
            return new Response<>(0, "Seat is Null.", null);
        }
    }

    @Override
    public Response findOrderById(String id, HttpHeaders headers) {
        Optional<Order> op = orderOtherRepository.findById(id);
        if (!op.isPresent()) {
            OrderOtherServiceImpl.LOGGER.warn("[findOrderById][Find Order By Id Fail][No content][id: {}]",id);
            return new Response<>(0, "No Content by this id", null);
        } else {
            Order order = op.get();
            OrderOtherServiceImpl.LOGGER.info("[findOrderById][Find Order By Id Success][id: {}]",id);
            return new Response<>(1, success, order);
        }
    }

    @Override
    public Response create(Order order, HttpHeaders headers) {
        OrderOtherServiceImpl.LOGGER.info("[create][Create Order][Ready Create Order]");
        ArrayList<Order> accountOrders = orderOtherRepository.findByAccountId(order.getAccountId());
        if (accountOrders.contains(order)) {
            OrderOtherServiceImpl.LOGGER.error("[create][Order Create Fail][Order already exists][OrderId: {}]", order.getId());
            return new Response<>(0, "Order already exist", order);
        } else {
            order.setId(UUID.randomUUID().toString());
            order=orderOtherRepository.save(order);
            OrderOtherServiceImpl.LOGGER.info("[create][Order Create Success][OrderId:{},Price: {}]",order.getId(),order.getPrice());
            return new Response<>(1, success, order);
        }
    }

    @Override
    public void initOrder(Order order, HttpHeaders headers) {
        Optional<Order> op = orderOtherRepository.findById(order.getId());
        if (!op.isPresent()) {
            orderOtherRepository.save(order);
            OrderOtherServiceImpl.LOGGER.info("[initOrder][Init Order Success][OrderId: {}]", order.getId());
        } else {
            Order orderTemp = op.get();
            OrderOtherServiceImpl.LOGGER.error("[initOrder][Init Order Fail][Order Already Exists][OrderId: {}]", order.getId());
        }
    }


    @Override
    public Response alterOrder(OrderAlterInfo oai, HttpHeaders headers) {

        String oldOrderId = oai.getPreviousOrderId();

        if (!orderOtherRepository.findById(oldOrderId).isPresent()) {
            OrderOtherServiceImpl.LOGGER.error("[alterOrder][Alter Order Fail][Order do not exist][OrderId: {}]", oldOrderId);
            return new Response<>(0, "Old Order Does Not Exists", null);
        }
        Order oldOrder = orderOtherRepository.findById(oldOrderId).get();
        oldOrder.setStatus(OrderStatus.CANCEL.getCode());
        saveChanges(oldOrder, headers);
        Order newOrder = oai.getNewOrderInfo();
        newOrder.setId(UUID.randomUUID().toString());
        Response cor = create(oai.getNewOrderInfo(), headers);
        if (cor.getStatus() == 1) {
            OrderOtherServiceImpl.LOGGER.info("[alterOrder][Alter Order Success][newOrderId:{}]",newOrder.getId());
            return new Response<>(1, "Alter Order Success", newOrder);
        } else {
            OrderOtherServiceImpl.LOGGER.error("[alterOrder][Alter Order Fail][Create new order fail][newOrderId: {}]", newOrder.getId());
            return new Response<>(0, cor.getMsg(), null);
        }
    }

    @Override
    public Response<ArrayList<Order>> queryOrders(QueryInfo qi, String accountId, HttpHeaders headers) {
        //1.Get all orders of the user
        ArrayList<Order> list = orderOtherRepository.findByAccountId(accountId);
        OrderOtherServiceImpl.LOGGER.info("[queryOrders][Step 1][Get Orders Number of Account][size: {}]", list.size());
        //2.Check is these orders fit the requirement/
        if (qi.isEnableStateQuery() || qi.isEnableBoughtDateQuery() || qi.isEnableTravelDateQuery()) {
            ArrayList<Order> finalList = new ArrayList<>();
            for (Order tempOrder : list) {
                boolean statePassFlag = false;
                boolean boughtDatePassFlag = false;
                boolean travelDatePassFlag = false;
                //3.Check order state requirement.
                if (qi.isEnableStateQuery()) {
                    if (tempOrder.getStatus() != qi.getState()) {
                        statePassFlag = false;
                    } else {
                        statePassFlag = true;
                    }
                } else {
                    statePassFlag = true;
                }
                OrderOtherServiceImpl.LOGGER.info("[queryOrders][Step 2][Check Status Fits End]");
                //4.Check order travel date requirement.
                Date boughtDate = StringUtils.String2Date(tempOrder.getBoughtDate());
                Date travelDate = StringUtils.String2Date(tempOrder.getTravelDate());
                Date travelDateEnd = StringUtils.String2Date(qi.getTravelDateEnd());
                Date boughtDateStart = StringUtils.String2Date(qi.getBoughtDateStart());
                Date boughtDateEnd = StringUtils.String2Date(qi.getBoughtDateEnd());
                if (qi.isEnableTravelDateQuery()) {
                    if (travelDate.before(travelDateEnd) &&
                            travelDate.after(boughtDateStart)) {
                        travelDatePassFlag = true;
                    } else {
                        travelDatePassFlag = false;
                    }
                } else {
                    travelDatePassFlag = true;
                }
                OrderOtherServiceImpl.LOGGER.info("[queryOrders][Step 2][Check Travel Date End]");
                //5.Check order bought date requirement.
                if (qi.isEnableBoughtDateQuery()) {
                    if (boughtDate.before(boughtDateEnd) &&
                            boughtDate.after(boughtDateStart)) {
                        boughtDatePassFlag = true;
                    } else {
                        boughtDatePassFlag = false;
                    }
                } else {
                    boughtDatePassFlag = true;
                }
                OrderOtherServiceImpl.LOGGER.info("[queryOrders][Step 2][Check Bought Date End]");
                //6.check if all requirement fits.
                if (statePassFlag && boughtDatePassFlag && travelDatePassFlag) {
                    finalList.add(tempOrder);
                }
                OrderOtherServiceImpl.LOGGER.info("[queryOrders][Step 2][Check All Requirement End]");
            }
            OrderOtherServiceImpl.LOGGER.info("[queryOrders][Get order num][size:{}]", finalList.size());
            return new Response<>(1, "Get order num", finalList);
        } else {
            OrderOtherServiceImpl.LOGGER.warn("[queryOrders][Orders don't fit the requirement][loginId: {}]", qi.getLoginId());
            return new Response<>(1, "Get order num", list);
        }
    }

    @Override
    public Response queryOrdersForRefresh(QueryInfo qi, String accountId, HttpHeaders headers) {
        ArrayList<Order> orders = queryOrders(qi, accountId, headers).getData();
        ArrayList<String> stationIds = new ArrayList<>();
        for (Order order : orders) {
            stationIds.add(order.getFrom());
            stationIds.add(order.getTo());
        }
        for (int i = 0; i < orders.size(); i++) {
            orders.get(i).setFrom(stationIds.get(i * 2));
            orders.get(i).setTo(stationIds.get(i * 2 + 1));
        }
        return new Response<>(1, success, orders);
    }

    public List<String> queryForStationId(List<String> ids, HttpHeaders headers) {

        HttpEntity requestEntity = new HttpEntity(ids, null);
        String station_service_url=getServiceUrl("ts-station-service");
        ResponseEntity<Response<List<String>>> re = restTemplate.exchange(
                station_service_url + "/api/v1/stationservice/stations/namelist",
                HttpMethod.POST,
                requestEntity,
                new ParameterizedTypeReference<Response<List<String>>>() {
                });
        OrderOtherServiceImpl.LOGGER.info("[queryForStationId][Stations name list][Name List is : {}]", re.getBody().toString());
        return re.getBody().getData();
    }

    @Override
    public Response saveChanges(Order order, HttpHeaders headers) {
        Optional<Order> op = orderOtherRepository.findById(order.getId());
        if (!op.isPresent() ) {
            OrderOtherServiceImpl.LOGGER.error("[saveChanges][Modify Order Fail][Order not found][OrderId: {}]", order.getId());
            return new Response<>(0, orderNotFound, null);
        } else {
            Order oldOrder = op.get();
            oldOrder.setAccountId(order.getAccountId());
            oldOrder.setBoughtDate(order.getBoughtDate());
            oldOrder.setTravelDate(order.getTravelDate());
            oldOrder.setTravelTime(order.getTravelTime());
            oldOrder.setSeatClass(order.getSeatClass());
            oldOrder.setCoachNumber(order.getCoachNumber());

            oldOrder.setSeatNumber(order.getSeatNumber());
            oldOrder.setTo(order.getTo());
            oldOrder.setFrom(order.getFrom());
            oldOrder.setStatus(order.getStatus());
            oldOrder.setTrainNumber(order.getTrainNumber());
            oldOrder.setPrice(order.getPrice());
            oldOrder.setContactsName(order.getContactsName());
            oldOrder.setDocumentType(order.getDocumentType());
            oldOrder.setContactsDocumentNumber(order.getContactsDocumentNumber());

            orderOtherRepository.save(oldOrder);
            OrderOtherServiceImpl.LOGGER.info("[saveChanges][Modify Order Success][OrderId: {}]",order.getId());
            return new Response<>(1, success, oldOrder);
        }
    }

    @Override
    public Response cancelOrder(String accountId, String orderId, HttpHeaders headers) {

        Optional<Order> op = orderOtherRepository.findById(orderId);
        if (!op.isPresent()) {
            OrderOtherServiceImpl.LOGGER.error("[cancelOrder][Cancel Order Fail][Order not found][OrderId: {}]", orderId);
            return new Response<>(0, orderNotFound, null);
        } else {
            Order oldOrder = op.get();
            oldOrder.setStatus(OrderStatus.CANCEL.getCode());
            orderOtherRepository.save(oldOrder);
            OrderOtherServiceImpl.LOGGER.info("[cancelOrder][Cancel Order Success][OrderId: {}]",oldOrder.getId());
            return new Response<>(1, success, oldOrder);
        }
    }

    @Override
    public Response queryAlreadySoldOrders(Date travelDate, String trainNumber, HttpHeaders headers) {
        ArrayList<Order> orders = orderOtherRepository.findByTravelDateAndTrainNumber(StringUtils.Date2String(travelDate), trainNumber);
        SoldTicket cstr = new SoldTicket();
        cstr.setTravelDate(travelDate);
        cstr.setTrainNumber(trainNumber);
        OrderOtherServiceImpl.LOGGER.info("[queryAlreadySoldOrders][Calculate Sold Ticket][Get Orders Number: {}]", orders.size());
        for (Order order : orders) {
            if (order.getStatus() >= OrderStatus.CHANGE.getCode()) {
                continue;
            }
            if (order.getSeatClass() == SeatClass.NONE.getCode()) {
                cstr.setNoSeat(cstr.getNoSeat() + 1);
            } else if (order.getSeatClass() == SeatClass.BUSINESS.getCode()) {
                cstr.setBusinessSeat(cstr.getBusinessSeat() + 1);
            } else if (order.getSeatClass() == SeatClass.FIRSTCLASS.getCode()) {
                cstr.setFirstClassSeat(cstr.getFirstClassSeat() + 1);
            } else if (order.getSeatClass() == SeatClass.SECONDCLASS.getCode()) {
                cstr.setSecondClassSeat(cstr.getSecondClassSeat() + 1);
            } else if (order.getSeatClass() == SeatClass.HARDSEAT.getCode()) {
                cstr.setHardSeat(cstr.getHardSeat() + 1);
            } else if (order.getSeatClass() == SeatClass.SOFTSEAT.getCode()) {
                cstr.setSoftSeat(cstr.getSoftSeat() + 1);
            } else if (order.getSeatClass() == SeatClass.HARDBED.getCode()) {
                cstr.setHardBed(cstr.getHardBed() + 1);
            } else if (order.getSeatClass() == SeatClass.SOFTBED.getCode()) {
                cstr.setSoftBed(cstr.getSoftBed() + 1);
            } else if (order.getSeatClass() == SeatClass.HIGHSOFTBED.getCode()) {
                cstr.setHighSoftBed(cstr.getHighSoftBed() + 1);
            } else {
                OrderOtherServiceImpl.LOGGER.info("[queryAlreadySoldOrders][Calculate Sold Tickets][Seat class not exists][Order ID: {}]", order.getId());
            }
        }
        return new Response<>(1, success, cstr);
    }

    @Override
    public Response getAllOrders(HttpHeaders headers) {
        ArrayList<Order> orders = orderOtherRepository.findAll();
        if (orders == null) {
            OrderOtherServiceImpl.LOGGER.warn("[getAllOrders][Find all orders warn][{}]","No content");
            return new Response<>(0, "No Content", null);
        } else {
            OrderOtherServiceImpl.LOGGER.info("[getAllOrders][Find all orders Success][size:{}]",orders.size());
            return new Response<>(1, success, orders);
        }
    }

    @Override
    public Response modifyOrder(String orderId, int status, HttpHeaders headers) {
        Optional<Order> op = orderOtherRepository.findById(orderId);
        if (!op.isPresent()) {
            OrderOtherServiceImpl.LOGGER.error("[modifyOrder][Modify order Fail][Order not found][OrderId: {}]",orderId);
            return new Response<>(0, orderNotFound, null);
        } else {
            Order order = op.get();
            order.setStatus(status);
            orderOtherRepository.save(order);
            OrderOtherServiceImpl.LOGGER.info("[modifyOrder][Modify order Success][OrderId: {}]",orderId);
            return new Response<>(1, success, order);
        }
    }

    @Override
    public Response getOrderPrice(String orderId, HttpHeaders headers) {
        Optional<Order> op = orderOtherRepository.findById(orderId);
        if (!op.isPresent()) {
            OrderOtherServiceImpl.LOGGER.error("[getOrderPrice][Get order price Fail][Order not found][OrderId: {}]",orderId);
            return new Response<>(0, orderNotFound, "-1.0");
        } else {
            Order order = op.get();
            OrderOtherServiceImpl.LOGGER.info("[getOrderPrice][Get Order Price Success][OrderId:{} , Price: {}]", orderId,order.getPrice());
            return new Response<>(1, success, order.getPrice());
        }
    }

    @Override
    public Response payOrder(String orderId, HttpHeaders headers) {
        Optional<Order> op = orderOtherRepository.findById(orderId);
        if (!op.isPresent()) {
            OrderOtherServiceImpl.LOGGER.error("[payOrder][Pay order Fail][Order not found][OrderId: {}]",orderId);
            return new Response<>(0, orderNotFound, null);
        } else {
            Order order = op.get();
            order.setStatus(OrderStatus.PAID.getCode());
            orderOtherRepository.save(order);
            OrderOtherServiceImpl.LOGGER.info("[payOrder][Pay order Success][OrderId: {}]",orderId);
            return new Response<>(1, success, order);
        }
    }

    @Override
    public Response getOrderById(String orderId, HttpHeaders headers) {
        Optional<Order> op = orderOtherRepository.findById(orderId);

        if(!op.isPresent()) {
            OrderOtherServiceImpl.LOGGER.error("[getOrderById][Get Order By ID Fail][Order not found][OrderId: {}]",orderId);
            return new Response<>(0, orderNotFound, null);
        } else {
            Order order = op.get();
            OrderOtherServiceImpl.LOGGER.info("[getOrderById][Get Order By ID Success][OrderId: {}]",orderId);
            return new Response<>(1, success, order);
        }
    }

    @Override
    public Response checkSecurityAboutOrder(Date dateFrom, String accountId, HttpHeaders headers) {
        OrderSecurity result = new OrderSecurity();
        ArrayList<Order> orders = orderOtherRepository.findByAccountId(accountId);
        int countOrderInOneHour = 0;
        int countTotalValidOrder = 0;
        Calendar ca = Calendar.getInstance();
        ca.setTime(dateFrom);
        ca.add(Calendar.HOUR_OF_DAY, -1);
        dateFrom = ca.getTime();
        for (Order order : orders) {
            if (order.getStatus() == OrderStatus.NOTPAID.getCode() ||
                    order.getStatus() == OrderStatus.PAID.getCode() ||
                    order.getStatus() == OrderStatus.COLLECTED.getCode()) {
                countTotalValidOrder += 1;
            }
            Date boughtDate = StringUtils.String2Date(order.getBoughtDate());
            if (boughtDate.after(dateFrom)) {
                countOrderInOneHour += 1;
            }
        }
        result.setOrderNumInLastOneHour(countOrderInOneHour);
        result.setOrderNumOfValidOrder(countTotalValidOrder);
        return new Response<>(1, success, result);
    }

    @Override
    public Response deleteOrder(String orderId, HttpHeaders headers) {
        String orderUuid = UUID.fromString(orderId).toString();
        Optional<Order> op = orderOtherRepository.findById(orderUuid);
        if(!op.isPresent()) {
            OrderOtherServiceImpl.LOGGER.error("[deleteOrder][Delete order Fail][Order not found][OrderId: {}]",orderId);
            return new Response<>(0, "Order Not Exist.", null);
        } else {
            Order order = op.get();
            orderOtherRepository.deleteById(orderUuid);
            OrderOtherServiceImpl.LOGGER.info("[deleteOrder][Delete order Success][OrderId: {}]",orderId);
            return new Response<>(1, success, orderUuid);
        }
    }

    @Override
    public Response addNewOrder(Order order, HttpHeaders headers) {
        OrderOtherServiceImpl.LOGGER.info("[addNewOrder][Admin Add Order][Ready to Add Order]");
        ArrayList<Order> accountOrders = orderOtherRepository.findByAccountId(order.getAccountId());
        if (accountOrders.contains(order)) {
            OrderOtherServiceImpl.LOGGER.error("[addNewOrder][Admin Add Order Fail][Order already exists][OrderId: {}]",order.getId());
            return new Response<>(0, "Order already exist", null);
        } else {
            order.setId(UUID.randomUUID().toString());
            orderOtherRepository.save(order);
            OrderOtherServiceImpl.LOGGER.info("[addNewOrder][Admin Add Order Success][OrderId:{} , Price:{}]",order.getId(),order.getPrice());
            return new Response<>(1, success, order);
        }
    }

    @Override
    public Response updateOrder(Order order, HttpHeaders headers) {
        LOGGER.info("[updateOrder][Admin Update Order][Order Info:{}]",order.toString());

        Optional<Order> op = orderOtherRepository.findById(order.getId());
        if(!op.isPresent()) {
            OrderOtherServiceImpl.LOGGER.error("[updateOrder][Admin Update Order Fail][Order not found][OrderId: {}]",order.getId());
            return new Response<>(0, orderNotFound, null);
        } else {
            Order oldOrder = op.get();
            //OrderOtherServiceImpl.LOGGER.info("{}", oldOrder.toString());
            oldOrder.setAccountId(order.getAccountId());
            oldOrder.setBoughtDate(order.getBoughtDate());
            oldOrder.setTravelDate(order.getTravelDate());
            oldOrder.setTravelTime(order.getTravelTime());
            oldOrder.setCoachNumber(order.getCoachNumber());
            oldOrder.setSeatClass(order.getSeatClass());
            oldOrder.setSeatNumber(order.getSeatNumber());
            oldOrder.setFrom(order.getFrom());
            oldOrder.setTo(order.getTo());
            oldOrder.setStatus(order.getStatus());
            oldOrder.setTrainNumber(order.getTrainNumber());
            oldOrder.setPrice(order.getPrice());
            oldOrder.setContactsName(order.getContactsName());
            oldOrder.setContactsDocumentNumber(order.getContactsDocumentNumber());
            oldOrder.setDocumentType(order.getDocumentType());
            orderOtherRepository.save(oldOrder);
            OrderOtherServiceImpl.LOGGER.info("[updateOrder][Admin Update Order Success][OrderId:{}]",oldOrder.getId());
            return new Response<>(1, success, oldOrder);
        }
    }
}



// Node: repos/cloned_ms_repos/train-ticket/ts-order-other-service/src/main/java/other/service/OrderOtherServiceImpl.java:OrderOtherServiceImpl.<init>
package other.service;


import edu.fudan.common.entity.Seat;
import edu.fudan.common.util.Response;
import org.springframework.http.HttpHeaders;
import other.entity.Order;
import other.entity.QueryInfo;
import other.entity.OrderAlterInfo;

import java.util.Date;

/**
 * @author fdse
 */
public interface OrderOtherService {

    Response findOrderById(String id, HttpHeaders headers);

    Response create(Order newOrder, HttpHeaders headers);

    Response updateOrder(Order order, HttpHeaders headers);

    Response saveChanges(Order order, HttpHeaders headers);

    Response cancelOrder(String accountId, String orderId, HttpHeaders headers);

    Response addNewOrder(Order order, HttpHeaders headers);

    Response deleteOrder(String orderId, HttpHeaders headers);

    Response getOrderById(String orderId, HttpHeaders headers);

    Response payOrder(String orderId, HttpHeaders headers);

    Response getOrderPrice(String orderId, HttpHeaders headers);

    Response modifyOrder(String orderId, int status, HttpHeaders headers);

    Response getAllOrders(HttpHeaders headers);

    Response getSoldTickets(Seat seatRequest, HttpHeaders headers);

    Response queryOrders(QueryInfo qi, String accountId, HttpHeaders headers);

    Response queryOrdersForRefresh(QueryInfo qi, String accountId, HttpHeaders headers);

    Response alterOrder(OrderAlterInfo oai, HttpHeaders headers);

    Response queryAlreadySoldOrders(Date travelDate, String trainNumber, HttpHeaders headers);

    Response checkSecurityAboutOrder(Date checkDate, String accountId, HttpHeaders headers);

    void initOrder(Order order, HttpHeaders headers);
}


// Node: repos/cloned_ms_repos/train-ticket/ts-order-other-service/src/main/java/other/service/OrderOtherService.java:OrderOtherService.<init>
package delivery.mq;

import delivery.config.Queues;
import delivery.entity.Delivery;
import delivery.repository.DeliveryRepository;
import edu.fudan.common.util.JsonUtils;
import edu.fudan.common.util.Response;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.amqp.rabbit.annotation.RabbitListener;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;

import java.util.UUID;


@Component
public class RabbitReceive {

    private static final Logger logger = LoggerFactory.getLogger(RabbitReceive.class);

    @Autowired
    private RestTemplate restTemplate;

    @Autowired
    private DeliveryRepository deliveryRepository;


    @RabbitListener(queues = Queues.queueName)
    public void process(String payload) {
        Delivery delivery = JsonUtils.json2Object(payload, Delivery.class);

        if (delivery == null) {
            logger.error("[process][json2Object][Receive delivery object is null error]");
            return;
        }
        logger.info("[process][Receive delivery object][delivery object: {}]" + delivery);

        if (delivery.getId() == null) {
            delivery.setId(UUID.randomUUID().toString());
        }

        try {
            deliveryRepository.save(delivery);
            logger.info("[process][Save delivery object into database success]");
        } catch (Exception e) {
            logger.error("[process][deliveryRepository.save][Save delivery object into database failed][exception: {}]", e.toString());
        }
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-delivery-service/src/main/java/delivery/mq/RabbitReceive.java:RabbitReceive.<init>
package assurance.controller;

import assurance.service.AssuranceService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.web.bind.annotation.*;

import java.util.UUID;

import static org.springframework.http.ResponseEntity.ok;

/**
 * @author fdse
 */
@RestController
@RequestMapping("/api/v1/assuranceservice")
public class AssuranceController {

    @Autowired
    private AssuranceService assuranceService;

    private static final Logger LOGGER = LoggerFactory.getLogger(AssuranceController.class);

    @GetMapping(path = "/welcome")
    public String home(@RequestHeader HttpHeaders headers) {
        return "Welcome to [ Assurance Service ] !";
    }

    @CrossOrigin(origins = "*")
    @GetMapping(path = "/assurances")
    public HttpEntity getAllAssurances(@RequestHeader HttpHeaders headers) {
        AssuranceController.LOGGER.info("[getAllAssurances][Get All Assurances]");
        return ok(assuranceService.getAllAssurances(headers));
    }

    @CrossOrigin(origins = "*")
    @GetMapping(path = "/assurances/types")
    public HttpEntity getAllAssuranceType(@RequestHeader HttpHeaders headers) {
        AssuranceController.LOGGER.info("[getAllAssuranceType][Get Assurance Type]");
        return ok(assuranceService.getAllAssuranceTypes(headers));
    }

    @CrossOrigin(origins = "*")
    @DeleteMapping(path = "/assurances/assuranceid/{assuranceId}")
    public HttpEntity deleteAssurance(@PathVariable String assuranceId, @RequestHeader HttpHeaders headers) {
        AssuranceController.LOGGER.info("[deleteAssurance][Delete Assurance][assuranceId: {}]", assuranceId);
        return ok(assuranceService.deleteById(UUID.fromString(assuranceId), headers));
    }

    @CrossOrigin(origins = "*")
    @DeleteMapping(path = "/assurances/orderid/{orderId}")
    public HttpEntity deleteAssuranceByOrderId(@PathVariable String orderId, @RequestHeader HttpHeaders headers) {
        AssuranceController.LOGGER.info("[deleteAssuranceByOrderId][Delete Assurance by orderId][orderId: {}]", orderId);
        return ok(assuranceService.deleteByOrderId(UUID.fromString(orderId), headers));
    }

    @CrossOrigin(origins = "*")
    @PatchMapping(path = "/assurances/{assuranceId}/{orderId}/{typeIndex}")
    public HttpEntity modifyAssurance(@PathVariable String assuranceId,
                                      @PathVariable String orderId,
                                      @PathVariable int typeIndex, @RequestHeader HttpHeaders headers) {
        AssuranceController.LOGGER.info("[modifyAssurance][Modify Assurance][assuranceId: {}, orderId: {}, typeIndex: {}]",
                assuranceId, orderId, typeIndex);
        return ok(assuranceService.modify(assuranceId, orderId, typeIndex, headers));
    }


    @CrossOrigin(origins = "*")
    @GetMapping(path = "/assurances/{typeIndex}/{orderId}")
    public HttpEntity createNewAssurance(@PathVariable int typeIndex, @PathVariable String orderId, @RequestHeader HttpHeaders headers) {
        //Assurance
        AssuranceController.LOGGER.info("[createNewAssurance][Create new assurance][typeIndex: {}, orderId: {}]", typeIndex, orderId);
        return ok(assuranceService.create(typeIndex, orderId, headers));
    }

    @CrossOrigin(origins = "*")
    @GetMapping(path = "/assurances/assuranceid/{assuranceId}")
    public HttpEntity getAssuranceById(@PathVariable String assuranceId, @RequestHeader HttpHeaders headers) {
        AssuranceController.LOGGER.info("[getAssuranceById][Find assurance by assuranceId][assureId: {}]", assuranceId);
        return ok(assuranceService.findAssuranceById(UUID.fromString(assuranceId), headers));
    }

    @CrossOrigin(origins = "*")
    @GetMapping(path = "/assurance/orderid/{orderId}")
    public HttpEntity findAssuranceByOrderId(@PathVariable String orderId, @RequestHeader HttpHeaders headers) {
        AssuranceController.LOGGER.info("[findAssuranceByOrderId][Find assurance by orderId][orderId: {}]", orderId);
        return ok(assuranceService.findAssuranceByOrderId(UUID.fromString(orderId), headers));
    }

}


// Node: repos/cloned_ms_repos/train-ticket/ts-assurance-service/src/main/java/assurance/controller/AssuranceController.java:AssuranceController.<init>
// Node: getAllAssuranceType
// Node: deleteAssuranceByOrderId
// Node: PatchMapping
// Node: modifyAssurance
// Node: createNewAssurance
package assurance.service;

import assurance.entity.*;
import assurance.repository.AssuranceRepository;
import edu.fudan.common.util.Response;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpHeaders;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

/**
 * @author fdse
 */
@Service
public class AssuranceServiceImpl implements AssuranceService {

    @Autowired
    private AssuranceRepository assuranceRepository;

    private static final Logger LOGGER = LoggerFactory.getLogger(AssuranceServiceImpl.class);

    @Override
    public Response findAssuranceById(UUID id, HttpHeaders headers) {
        Optional<Assurance> assurance = assuranceRepository.findById(id.toString());
        if (assurance == null) {
            AssuranceServiceImpl.LOGGER.warn("[findAssuranceById][find assurance][No content][assurance id: {}]", id);
            return new Response<>(0, "No Content by this id", null);
        } else {
            AssuranceServiceImpl.LOGGER.info("[findAssuranceById][Find Assurance][assurance id: {}]", id);
            return new Response<>(1, "Find Assurance Success", assurance);
        }
    }

    @Override
    public Response findAssuranceByOrderId(UUID orderId, HttpHeaders headers) {
        Assurance assurance = assuranceRepository.findByOrderId(orderId.toString());
        if (assurance == null) {
            AssuranceServiceImpl.LOGGER.warn("[findAssuranceByOrderId][find assurance][No content][orderId: {}]", orderId);
            return new Response<>(0, "No Content by this orderId", null);
        } else {
            AssuranceServiceImpl.LOGGER.info("[findAssuranceByOrderId][find assurance success][orderId: {}]", orderId);
            return new Response<>(1, "Find Assurance Success", assurance);
        }
    }

    @Override
    public Response create(int typeIndex, String orderId, HttpHeaders headers) {
        Assurance a = assuranceRepository.findByOrderId(orderId);
        AssuranceType at = AssuranceType.getTypeByIndex(typeIndex);
        if (a != null) {
            AssuranceServiceImpl.LOGGER.error("[create][AddAssurance Fail][Assurance already exists][typeIndex: {}, orderId: {}]", typeIndex, orderId);
            return new Response<>(0, "Fail.Assurance already exists", null);
        } else if (at == null) {
            AssuranceServiceImpl.LOGGER.warn("[create][AddAssurance Fail][Assurance type doesn't exist][typeIndex: {}, orderId: {}]", typeIndex, orderId);
            return new Response<>(0, "Fail.Assurance type doesn't exist", null);
        } else {
            Assurance assurance = new Assurance(UUID.randomUUID().toString(), UUID.fromString(orderId).toString(), at);
            assuranceRepository.save(assurance);
            AssuranceServiceImpl.LOGGER.info("[create][AddAssurance][Success]");
            return new Response<>(1, "Success", assurance);
        }
    }

    @Override
    public Response deleteById(UUID assuranceId, HttpHeaders headers) {
        assuranceRepository.deleteById(assuranceId.toString());
        Optional<Assurance> a = assuranceRepository.findById(assuranceId.toString());
        if (a == null) {
            AssuranceServiceImpl.LOGGER.info("[deleteById][DeleteAssurance success][assuranceId: {}]", assuranceId);
            return new Response<>(1, "Delete Success with Assurance id", null);
        } else {
            AssuranceServiceImpl.LOGGER.error("[deleteById][DeleteAssurance Fail][Assurance not clear][assuranceId: {}]", assuranceId);
            return new Response<>(0, "Fail.Assurance not clear", assuranceId);
        }
    }

    @Override
    public Response deleteByOrderId(UUID orderId, HttpHeaders headers) {
        assuranceRepository.removeAssuranceByOrderId(orderId.toString());
        Assurance isExistAssurace = assuranceRepository.findByOrderId(orderId.toString());
        if (isExistAssurace == null) {
            AssuranceServiceImpl.LOGGER.info("[deleteByOrderId][DeleteAssurance Success][orderId: {}]", orderId);
            return new Response<>(1, "Delete Success with Order Id", null);
        } else {
            AssuranceServiceImpl.LOGGER.error("[deleteByOrderId][DeleteAssurance Fail][Assurance not clear][orderId: {}]", orderId);
            return new Response<>(0, "Fail.Assurance not clear", orderId);
        }
    }

    @Override
    public Response modify(String assuranceId, String orderId, int typeIndex, HttpHeaders headers) {
        Response oldAssuranceResponse = findAssuranceById(UUID.fromString(assuranceId), headers);
        Assurance oldAssurance =  ((Optional<Assurance>)oldAssuranceResponse.getData()).get();
        if (oldAssurance == null) {
            AssuranceServiceImpl.LOGGER.error("[modify][ModifyAssurance Fail][Assurance not found][assuranceId: {}, orderId: {}, typeIndex: {}]", assuranceId, orderId, typeIndex);
            return new Response<>(0, "Fail.Assurance not found.", null);
        } else {
            AssuranceType at = AssuranceType.getTypeByIndex(typeIndex);
            if (at != null) {
                oldAssurance.setType(at);
                assuranceRepository.save(oldAssurance);
                AssuranceServiceImpl.LOGGER.info("[modify][ModifyAssurance Success][assuranceId: {}, orderId: {}, typeIndex: {}]", assuranceId, orderId, typeIndex);
                return new Response<>(1, "Modify Success", oldAssurance);
            } else {
                AssuranceServiceImpl.LOGGER.error("[modify][ModifyAssurance Fail][Assurance Type not exist][assuranceId: {}, orderId: {}, typeIndex: {}]", assuranceId, orderId, typeIndex);
                return new Response<>(0, "Assurance Type not exist", null);
            }
        }
    }

    @Override
    public Response getAllAssurances(HttpHeaders headers) {
        List<Assurance> as = assuranceRepository.findAll();
        if (as != null && !as.isEmpty()) {
            ArrayList<PlainAssurance> result = new ArrayList<>();
            for (Assurance a : as) {
                PlainAssurance pa = new PlainAssurance();
                pa.setId(a.getId());
                pa.setOrderId(a.getOrderId());
                pa.setTypeIndex(a.getType().getIndex());
                pa.setTypeName(a.getType().getName());
                pa.setTypePrice(a.getType().getPrice());
                result.add(pa);
            }
            AssuranceServiceImpl.LOGGER.info("[getAllAssurances][find all assurance success][list size: {}]", as.size());
            return new Response<>(1, "Success", result);
        } else {
            AssuranceServiceImpl.LOGGER.warn("[getAllAssurances][find all assurance][No content]");
            return new Response<>(0, "No Content, Assurance is empty", null);
        }
    }

    @Override
    public Response getAllAssuranceTypes(HttpHeaders headers) {

        List<AssuranceTypeBean> atlist = new ArrayList<>();
        for (AssuranceType at : AssuranceType.values()) {
            AssuranceTypeBean atb = new AssuranceTypeBean();
            atb.setIndex(at.getIndex());
            atb.setName(at.getName());
            atb.setPrice(at.getPrice());
            atlist.add(atb);
        }
        if (!atlist.isEmpty()) {
            AssuranceServiceImpl.LOGGER.info("[getAllAssuranceTypes][find all assurance type success][list size: {}]", atlist.size());
            return new Response<>(1, "Find All Assurance", atlist);
        } else {
            AssuranceServiceImpl.LOGGER.warn("[getAllAssuranceTypes][find all assurance type][No content]");
            return new Response<>(0, "Assurance is Empty", null);
        }
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-assurance-service/src/main/java/assurance/service/AssuranceServiceImpl.java:AssuranceServiceImpl.<init>
package adminorder.controller;

import edu.fudan.common.entity.*;
import adminorder.service.AdminOrderService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.web.bind.annotation.*;

import static org.springframework.http.ResponseEntity.ok;

/**
 * @author fdse
 */
@RestController
@RequestMapping("/api/v1/adminorderservice")
public class AdminOrderController {

    @Autowired
    AdminOrderService adminOrderService;

    private static final Logger logger = LoggerFactory.getLogger(AdminOrderController.class);

    @GetMapping(path = "/welcome")
    public String home(@RequestHeader HttpHeaders headers) {
        return "Welcome to [Admin Order Service] !";
    }

    @CrossOrigin(origins = "*")
    @GetMapping(path = "/adminorder")
    public HttpEntity getAllOrders(@RequestHeader HttpHeaders headers) {
        logger.info("[getAllOrders][Get all orders][getAllOrders]");
        return ok(adminOrderService.getAllOrders(headers));
    }

    @PostMapping(value = "/adminorder")
    public HttpEntity addOrder(@RequestBody Order request, @RequestHeader HttpHeaders headers) {
        logger.info("[addOrder][Add new order][AccountID: {}]", request.getAccountId());
        return ok(adminOrderService.addOrder(request, headers));
    }

    @PutMapping(value = "/adminorder")
    public HttpEntity updateOrder(@RequestBody Order request, @RequestHeader HttpHeaders headers) {
        logger.info("[updateOrder][Update order][AccountID: {}, OrderId: {}]", request.getAccountId(), request.getId());
        return ok(adminOrderService.updateOrder(request, headers));
    }

    @DeleteMapping(value = "/adminorder/{orderId}/{trainNumber}")
    public HttpEntity deleteOrder(@PathVariable String orderId, @PathVariable String trainNumber, @RequestHeader HttpHeaders headers) {
        logger.info("[deleteOrder][Delete order][OrderId: {}, TrainNumber: {}]", orderId, trainNumber);
        return ok(adminOrderService.deleteOrder(orderId, trainNumber, headers));
    }

}


// Node: repos/cloned_ms_repos/train-ticket/ts-admin-order-service/src/main/java/adminorder/controller/AdminOrderController.java:AdminOrderController.<init>
package adminorder.service;

import edu.fudan.common.entity.*;
import edu.fudan.common.util.Response;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.cloud.client.ServiceInstance;
import org.springframework.cloud.client.discovery.DiscoveryClient;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.util.ArrayList;
import java.util.List;

/**
 * @author fdse
 */
@Service
public class AdminOrderServiceImpl implements AdminOrderService {
    @Autowired
    private RestTemplate restTemplate;
    @Autowired
    private DiscoveryClient discoveryClient;

    private static final Logger LOGGER = LoggerFactory.getLogger(AdminOrderServiceImpl.class);

    private String getServiceUrl(String serviceName) {
        return "http://" + serviceName;
    }

    @Override
    public Response getAllOrders(HttpHeaders headers) {

        AdminOrderServiceImpl.LOGGER.info("[getAllOrders][Get All Orders: Generate Reponse Begin]");
        //Get all of the orders
        ArrayList<Order> orders = new ArrayList<>();
        //From ts-order-service
        HttpEntity requestEntity = new HttpEntity(null);

        String order_service_url = getServiceUrl("ts-order-service");
        ResponseEntity<Response<ArrayList<Order>>> re = restTemplate.exchange(
                order_service_url + "/api/v1/orderservice/order",
                HttpMethod.GET,
                requestEntity,
                new ParameterizedTypeReference<Response<ArrayList<Order>>>() {
                });
        Response<ArrayList<Order>> result = re.getBody();

        if (result.getStatus() == 1) {
            AdminOrderServiceImpl.LOGGER.info("[getAllOrders][Get Orders From ts-order-service successfully!]");
            ArrayList<Order> orders1 = result.getData();
            orders.addAll(orders1);
        } else {
            AdminOrderServiceImpl.LOGGER.error("[getAllOrders][receive response][Get Orders From ts-order-service fail!]");
        }
        //From ts-order-other-service
        HttpEntity requestEntity2 = new HttpEntity(null);
        String order_other_service_url = getServiceUrl("ts-order-other-service");
        ResponseEntity<Response<ArrayList<Order>>> re2 = restTemplate.exchange(
                order_other_service_url + "/api/v1/orderOtherService/orderOther",
                HttpMethod.GET,
                requestEntity2,
                new ParameterizedTypeReference<Response<ArrayList<Order>>>() {
                });
        result = re2.getBody();

        if (result.getStatus() == 1) {
            AdminOrderServiceImpl.LOGGER.info("[getAllOrders][Get Orders From ts-order-other-service successfully!]");
            ArrayList<Order> orders1 = (ArrayList<Order>) result.getData();
            orders.addAll(orders1);
        } else {
            AdminOrderServiceImpl.LOGGER.error("[getAllOrders][receive response][Get Orders From ts-order-other-service fail!]");
        }
        //Return orders
        return new Response<>(1, "Get the orders successfully!", orders);

    }

    @Override
    public Response deleteOrder(String orderId, String trainNumber, HttpHeaders headers) {
        Response deleteOrderResult;
        if (trainNumber.startsWith("G") || trainNumber.startsWith("D")) {
            AdminOrderServiceImpl.LOGGER.info("[deleteOrder][Delete Order][orderId: {}, trainNumber: {}]", orderId, trainNumber);
            HttpEntity requestEntity = new HttpEntity(null);
            String order_service_url = getServiceUrl("ts-order-service");
            ResponseEntity<Response> re = restTemplate.exchange(
                     order_service_url + "/api/v1/orderservice/order/" + orderId,
                    HttpMethod.DELETE,
                    requestEntity,
                    Response.class);
            deleteOrderResult = re.getBody();

        } else {
            AdminOrderServiceImpl.LOGGER.info("[deleteOrder][Delete Order Other][trainNumber doesn't starts With G or D]");
            HttpEntity requestEntity = new HttpEntity(null);
            String order_other_service_url = getServiceUrl("ts-order-other-service");
            ResponseEntity<Response> re = restTemplate.exchange(
                    order_other_service_url + "/api/v1/orderOtherService/orderOther/" + orderId,
                    HttpMethod.DELETE,
                    requestEntity,
                    Response.class);
            deleteOrderResult = re.getBody();

        }
        return deleteOrderResult;

    }

    @Override
    public Response updateOrder(Order request, HttpHeaders headers) {

        Response updateOrderResult;
        LOGGER.info("[updateOrder][UPDATE ORDER INFO][request info: {}]", request.toString());
        if (request.getTrainNumber().startsWith("G") || request.getTrainNumber().startsWith("D")) {

            AdminOrderServiceImpl.LOGGER.info("[updateOrder][Update Order][trainNumber starts With G or D]");
            HttpEntity requestEntity = new HttpEntity(request, headers);
            String order_service_url = getServiceUrl("ts-order-service");
            ResponseEntity<Response> re = restTemplate.exchange(
                    order_service_url + "/api/v1/orderservice/order/admin",
                    HttpMethod.PUT,
                    requestEntity,
                    Response.class);
            updateOrderResult = re.getBody();

        } else {
            AdminOrderServiceImpl.LOGGER.info("[updateOrder][Add New Order Other][trainNumber doesn't starts With G or D]");
            HttpEntity requestEntity = new HttpEntity(request, headers);
            String order_other_service_url = getServiceUrl("ts-order-other-service");
            ResponseEntity<Response> re = restTemplate.exchange(
                    order_other_service_url + "/api/v1/orderOtherService/orderOther/admin",
                    HttpMethod.PUT,
                    requestEntity,
                    Response.class);
            updateOrderResult = re.getBody();

        }
        return updateOrderResult;
    }

    @Override
    public Response addOrder(Order request, HttpHeaders headers) {

        Response addOrderResult;
        LOGGER.info("[addOrder][ADD ORDER][request info: {}]", request.toString());
        if (request.getTrainNumber().startsWith("G") || request.getTrainNumber().startsWith("D")) {
            AdminOrderServiceImpl.LOGGER.info("[addOrder][Add New Order][trainNumber starts With G or D]");
            HttpEntity requestEntity = new HttpEntity(request, headers);
            String order_service_url = getServiceUrl("ts-order-service");
            ResponseEntity<Response> re = restTemplate.exchange(
                    order_service_url + "/api/v1/orderservice/order/admin",
                    HttpMethod.POST,
                    requestEntity,
                    Response.class);
            addOrderResult = re.getBody();

        } else {
            AdminOrderServiceImpl.LOGGER.info("[addOrder][Add New Order Other][trainNumber doesn't starts With G or D]");
            HttpEntity requestEntity = new HttpEntity(request, headers);
            String order_other_service_url = getServiceUrl("ts-order-other-service");
            ResponseEntity<Response> re = restTemplate.exchange(
                     order_other_service_url + "/api/v1/orderOtherService/orderOther/admin",
                    HttpMethod.POST,
                    requestEntity,
                    Response.class);
            addOrderResult = re.getBody();

        }
        return addOrderResult;

    }


}


// Node: repos/cloned_ms_repos/train-ticket/ts-admin-order-service/src/main/java/adminorder/service/AdminOrderServiceImpl.java:AdminOrderServiceImpl.<init>
package travel2.controller;

import edu.fudan.common.entity.TripResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import travel2.service.TravelService;

import java.util.ArrayList;

import static org.springframework.http.ResponseEntity.ok;

/**
 * @author fdse
 */
@RestController
@RequestMapping("/api/v1/travel2service")
public class Travel2Controller {

    @Autowired
    private TravelService service;

    private static final Logger LOGGER = LoggerFactory.getLogger(Travel2Controller.class);

    @GetMapping(path = "/welcome")
    public String home(@RequestHeader HttpHeaders headers) {
        return "Welcome to [ Travle2 Service ] !";
    }

    @GetMapping(value = "/train_types/{tripId}")
    public HttpEntity getTrainTypeByTripId(@PathVariable String tripId,
                                           @RequestHeader HttpHeaders headers) {
        // TrainType
        Travel2Controller.LOGGER.info("[getTrainTypeByTripId][Get train by Trip id][TripId: {}]",tripId);
        return ok(service.getTrainTypeByTripId(tripId, headers));
    }

    @GetMapping(value = "/routes/{tripId}")
    public HttpEntity getRouteByTripId(@PathVariable String tripId,
                                       @RequestHeader HttpHeaders headers) {
        Travel2Controller.LOGGER.info("[getRouteByTripId][Get Route By Trip ID][TripId: {}]", tripId);
        //Route
        return ok(service.getRouteByTripId(tripId, headers));
    }

    @PostMapping(value = "/trips/routes")
    public HttpEntity getTripsByRouteId(@RequestBody ArrayList<String> routeIds,
                                        @RequestHeader HttpHeaders headers) {
        // ArrayList<ArrayList<Trip>>
        Travel2Controller.LOGGER.info("[getTripByRoute][Get trips by Route id][RouteIdNumber: {}]",routeIds.size());
        return ok(service.getTripByRoute(routeIds, headers));
    }

    @CrossOrigin(origins = "*")
    @PostMapping(value = "/trips")
    public HttpEntity<?> createTrip(@RequestBody edu.fudan.common.entity.TravelInfo routeIds, @RequestHeader HttpHeaders headers) {
        // null
        Travel2Controller.LOGGER.info("[create][Create trip][TripId: {}]", routeIds.getTripId());
        return new ResponseEntity<>(service.create(routeIds, headers), HttpStatus.CREATED);
    }

    /**
     *Return Trip only, no left ticket information
     *
     * @param tripId trip id
     * @param headers headers
     * @return HttpEntity
     */
    @CrossOrigin(origins = "*")
    @GetMapping(value = "/trips/{tripId}")
    public HttpEntity retrieve(@PathVariable String tripId, @RequestHeader HttpHeaders headers) {
        // Trip
        Travel2Controller.LOGGER.info("[retrieve][Retrieve trip][TripId: {}]",tripId);
        return ok(service.retrieve(tripId, headers));
    }

    @CrossOrigin(origins = "*")
    @PutMapping(value = "/trips")
    public HttpEntity updateTrip(@RequestBody edu.fudan.common.entity.TravelInfo info, @RequestHeader HttpHeaders headers) {
        // Trip
        Travel2Controller.LOGGER.info("[update][Update trip][TripId: {}]",info.getTripId());
        return ok(service.update(info, headers));
    }

    @CrossOrigin(origins = "*")
    @DeleteMapping(value = "/trips/{tripId}")
    public HttpEntity deleteTrip(@PathVariable String tripId, @RequestHeader HttpHeaders headers) {
        // string
        Travel2Controller.LOGGER.info("[delete][Delete trip][TripId: {}]",tripId);
        return ok(service.delete(tripId, headers));
    }

    /**
     * Return Trip and the remaining tickets
     *
     * @param info trip info
     * @param headers headers
     * @return HttpEntity
     */
    @CrossOrigin(origins = "*")
    @PostMapping(value = "/trips/left")
    public HttpEntity queryInfo(@RequestBody edu.fudan.common.entity.TripInfo info, @RequestHeader HttpHeaders headers) {
        if (info.getStartPlace() == null || info.getStartPlace().length() == 0 ||
                info.getEndPlace() == null || info.getEndPlace().length() == 0 ||
                info.getDepartureTime() == null) {
            Travel2Controller.LOGGER.info("[query][Travel Query Fail][Something null]");
            ArrayList<TripResponse> errorList = new ArrayList<>();
            return ok(errorList);
        }
        Travel2Controller.LOGGER.info("[query][Query TripResponse]");
        return ok(service.queryByBatch(info, headers));
    }

    /**
     * Return a Trip and the remaining tickets
     *
     * @param gtdi trip all datail info
     * @param headers headers
     * @return HttpEntity
     */
    @CrossOrigin(origins = "*")
    @PostMapping(value = "/trip_detail")
    public HttpEntity getTripAllDetailInfo(@RequestBody edu.fudan.common.entity.TripAllDetailInfo gtdi, @RequestHeader HttpHeaders headers) {
        Travel2Controller.LOGGER.info("[getTripAllDetailInfo][Get trip detail][TripId: {}]",gtdi.getTripId());
        return ok(service.getTripAllDetailInfo(gtdi, headers));
    }

    @CrossOrigin(origins = "*")
    @GetMapping(value = "/trips")
    public HttpEntity queryAll(@RequestHeader HttpHeaders headers) {
        // List<Trip>
        Travel2Controller.LOGGER.info("[queryAll][Query all trips]");
        return ok(service.queryAll(headers));
    }

    @CrossOrigin(origins = "*")
    @GetMapping(value = "/admin_trip")
    public HttpEntity adminQueryAll(@RequestHeader HttpHeaders headers) {
        // ArrayList<AdminTrip>
        Travel2Controller.LOGGER.info("[adminQueryAll][Admin query all trips]");
        return ok(service.adminQueryAll(headers));
    }

}


// Node: repos/cloned_ms_repos/train-ticket/ts-travel2-service/src/main/java/travel2/controller/Travel2Controller.java:Travel2Controller.<init>
// Node: getTripsByRouteId
// Node: createTrip
// Node: retrieve
// Node: updateTrip
// Node: deleteTrip
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



// Node: repos/cloned_ms_repos/train-ticket/ts-travel2-service/src/main/java/travel2/service/TravelServiceImpl.java:TravelServiceImpl.<init>
package order.controller;

import edu.fudan.common.entity.Seat;
import edu.fudan.common.util.StringUtils;
import order.entity.*;
import order.service.OrderService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.web.bind.annotation.*;

import java.util.Date;

import static org.springframework.http.ResponseEntity.ok;

/**
 * @author fdse
 */
@RestController
@RequestMapping("/api/v1/orderservice")
public class OrderController {

    @Autowired
    private OrderService orderService;

    private static final Logger LOGGER = LoggerFactory.getLogger(OrderController.class);

    @GetMapping(path = "/welcome")
    public String home() {
        return "Welcome to [ Order Service ] !";
    }

    /***************************For Normal Use***************************/

    @PostMapping(value = "/order/tickets")
    public HttpEntity getTicketListByDateAndTripId(@RequestBody Seat seatRequest, @RequestHeader HttpHeaders headers) {
        OrderController.LOGGER.info("[getSoldTickets][Get Sold Ticket][Travel Date: {}]", seatRequest.getTravelDate().toString());
        return ok(orderService.getSoldTickets(seatRequest, headers));
    }

    @CrossOrigin(origins = "*")
    @PostMapping(path = "/order")
    public HttpEntity createNewOrder(@RequestBody Order createOrder, @RequestHeader HttpHeaders headers) {
        OrderController.LOGGER.info("[createNewOrder][Create Order][from {} to {} at {}]", createOrder.getFrom(), createOrder.getTo(), createOrder.getTravelDate());
        return ok(orderService.create(createOrder, headers));
    }

    @CrossOrigin(origins = "*")
    @PostMapping(path = "/order/admin")
    public HttpEntity addcreateNewOrder(@RequestBody Order order, @RequestHeader HttpHeaders headers) {
        return ok(orderService.addNewOrder(order, headers));
    }

    @CrossOrigin(origins = "*")
    @PostMapping(path = "/order/query")
    public HttpEntity queryOrders(@RequestBody OrderInfo qi,
                                  @RequestHeader HttpHeaders headers) {
        OrderController.LOGGER.info("[queryOrders][Query Orders][for LoginId :{}]", qi.getLoginId());
        return ok(orderService.queryOrders(qi, qi.getLoginId(), headers));
    }

    @CrossOrigin(origins = "*")
    @PostMapping(path = "/order/refresh")
    public HttpEntity queryOrdersForRefresh(@RequestBody OrderInfo qi,
                                            @RequestHeader HttpHeaders headers) {
        OrderController.LOGGER.info("[queryOrdersForRefresh][Query Orders][for LoginId:{}]", qi.getLoginId());
        return ok(orderService.queryOrdersForRefresh(qi, qi.getLoginId(), headers));
    }

    @CrossOrigin(origins = "*")
    @GetMapping(path = "/order/{travelDate}/{trainNumber}")
    public HttpEntity calculateSoldTicket(@PathVariable String travelDate, @PathVariable String trainNumber,
                                          @RequestHeader HttpHeaders headers) {
        OrderController.LOGGER.info("[queryAlreadySoldOrders][Calculate Sold Tickets][Date: {} TrainNumber: {}]", travelDate, trainNumber);
        return ok(orderService.queryAlreadySoldOrders(StringUtils.String2Date(travelDate), trainNumber, headers));
    }

    @CrossOrigin(origins = "*")
    @GetMapping(path = "/order/price/{orderId}")
    public HttpEntity getOrderPrice(@PathVariable String orderId, @RequestHeader HttpHeaders headers) {
        OrderController.LOGGER.info("[getOrderPrice][Get Order Price][OrderId: {}]", orderId);
        // String
        return ok(orderService.getOrderPrice(orderId, headers));
    }


    @CrossOrigin(origins = "*")
    @GetMapping(path = "/order/orderPay/{orderId}")
    public HttpEntity payOrder(@PathVariable String orderId, @RequestHeader HttpHeaders headers) {
        OrderController.LOGGER.info("[payOrder][Pay Order][OrderId: {}]", orderId);
        // Order
        return ok(orderService.payOrder(orderId, headers));
    }

    @CrossOrigin(origins = "*")
    @GetMapping(path = "/order/{orderId}")
    public HttpEntity getOrderById(@PathVariable String orderId, @RequestHeader HttpHeaders headers) {
        OrderController.LOGGER.info("[getOrderById][Get Order By Id][OrderId: {}]", orderId);
        // Order
        return ok(orderService.getOrderById(orderId, headers));
    }

    @CrossOrigin(origins = "*")
    @GetMapping(path = "/order/status/{orderId}/{status}")
    public HttpEntity modifyOrder(@PathVariable String orderId, @PathVariable int status, @RequestHeader HttpHeaders headers) {
        OrderController.LOGGER.info("[modifyOrder][Modify Order Status][OrderId: {}]", orderId);
        // Order
        return ok(orderService.modifyOrder(orderId, status, headers));
    }


    @CrossOrigin(origins = "*")
    @GetMapping(path = "/order/security/{checkDate}/{accountId}")
    public HttpEntity securityInfoCheck(@PathVariable String checkDate, @PathVariable String accountId,
                                        @RequestHeader HttpHeaders headers) {
        OrderController.LOGGER.info("[checkSecurityAboutOrder][Security Info Get][AccountId:{}]", accountId);
        return ok(orderService.checkSecurityAboutOrder(StringUtils.String2Date(checkDate), accountId, headers));
    }


    @CrossOrigin(origins = "*")
    @PutMapping(path = "/order")
    public HttpEntity saveOrderInfo(@RequestBody Order orderInfo,
                                    @RequestHeader HttpHeaders headers) {

        OrderController.LOGGER.info("[saveChanges][Save Order Info][OrderId:{}]",orderInfo.getId());
        return ok(orderService.saveChanges(orderInfo, headers));
    }

    @CrossOrigin(origins = "*")
    @PutMapping(path = "/order/admin")
    public HttpEntity updateOrder(@RequestBody Order order, @RequestHeader HttpHeaders headers) {
        // Order
        OrderController.LOGGER.info("[updateOrder][Update Order][OrderId: {}]", order.getId());
        return ok(orderService.updateOrder(order, headers));
    }


    @CrossOrigin(origins = "*")
    @DeleteMapping(path = "/order/{orderId}")
    public HttpEntity deleteOrder(@PathVariable String orderId, @RequestHeader HttpHeaders headers) {
        OrderController.LOGGER.info("[deleteOrder][Delete Order][OrderId: {}]", orderId);
        // Order
        return ok(orderService.deleteOrder(orderId, headers));
    }

    /***************For super admin(Single Service Test*******************/

    @CrossOrigin(origins = "*")
    @GetMapping(path = "/order")
    public HttpEntity findAllOrder(@RequestHeader HttpHeaders headers) {
        OrderController.LOGGER.info("[getAllOrders][Find All Order]");
        // ArrayList<Order>
        return ok(orderService.getAllOrders(headers));
    }

}


// Node: repos/cloned_ms_repos/train-ticket/ts-order-service/src/main/java/order/controller/OrderController.java:OrderController.<init>
// Node: repos/cloned_ms_repos/train-ticket/ts-order-service/src/main/java/order/controller/OrderController.java:OrderController.findAllOrder
package order.service;

import edu.fudan.common.entity.*;
import edu.fudan.common.util.Response;
import edu.fudan.common.util.StringUtils;
import order.entity.OrderAlterInfo;
import order.entity.Order;
import order.entity.OrderInfo;
import order.repository.OrderRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.cloud.client.ServiceInstance;
import org.springframework.cloud.client.discovery.DiscoveryClient;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.util.*;

/**
 * @author fdse
 */
@Service
public class OrderServiceImpl implements OrderService {

    @Autowired
    private OrderRepository orderRepository;

    @Autowired
    private RestTemplate restTemplate;

    private static final Logger LOGGER = LoggerFactory.getLogger(OrderServiceImpl.class);

    @Autowired
    private DiscoveryClient discoveryClient;

    private String getServiceUrl(String serviceName) {
        return "http://" + serviceName; }

//    @Value("${station-service.url}")
//    String station_service_url;

    String success = "Success";
    String orderNotFound = "Order Not Found";


    @Override
    public Response getSoldTickets(Seat seatRequest, HttpHeaders headers) {
        ArrayList<Order> list = orderRepository.findByTravelDateAndTrainNumber(seatRequest.getTravelDate(),
                seatRequest.getTrainNumber());
        if (list != null && !list.isEmpty()) {
            Set ticketSet = new HashSet();
            for (Order tempOrder : list) {
                ticketSet.add(new Ticket(Integer.parseInt(tempOrder.getSeatNumber()),
                        tempOrder.getFrom(), tempOrder.getTo()));
            }
            LeftTicketInfo leftTicketInfo = new LeftTicketInfo();
            leftTicketInfo.setSoldTickets(ticketSet);
            OrderServiceImpl.LOGGER.info("[getSoldTickets][Left ticket info][info is: {}]", leftTicketInfo.toString());
            return new Response<>(1, success, leftTicketInfo);
        } else {
            OrderServiceImpl.LOGGER.warn("[getSoldTickets][Seat][Left ticket info is empty][seat from date: {}, train number: {}]",seatRequest.getTravelDate(),seatRequest.getTrainNumber()); //warn级别，获取资源但资源为空
            return new Response<>(0, "Order is Null.", null);
        }
    }

    @Override
    public Response findOrderById(String id, HttpHeaders headers) {
        Optional<Order> op = orderRepository.findById(id);
        if (!op.isPresent()) {
            OrderServiceImpl.LOGGER.warn("[findOrderById][Find Order By Id Fail][No content][id: {}] ",id);  //获取资源但资源为空
            return new Response<>(0, "No Content by this id", null);
        } else {
            Order order = op.get();
            OrderServiceImpl.LOGGER.warn("[findOrderById][Find Order By Id Success][id: {}] ",id);  //获取资源但资源为空
            return new Response<>(1, success, order);
        }
    }

    @Override
    public Response create(Order order, HttpHeaders headers) {
        OrderServiceImpl.LOGGER.info("[create][Create Order][Ready to Create Order]");
        ArrayList<Order> accountOrders = orderRepository.findByAccountId(order.getAccountId());
        if (accountOrders.contains(order)) {
            OrderServiceImpl.LOGGER.error("[create][Order Create Fail][Order already exists][OrderId: {}]", order.getId());
            return new Response<>(0, "Order already exist", null);
        } else {
            order.setId(UUID.randomUUID().toString());
            order=orderRepository.save(order);
            OrderServiceImpl.LOGGER.info("[create][Order Create Success][Order Price][OrderId:{} , Price: {}]",order.getId(),order.getPrice());
            return new Response<>(1, success, order);
        }
    }

    @Override
    public Response alterOrder(OrderAlterInfo oai, HttpHeaders headers) {

        String oldOrderId = oai.getPreviousOrderId();
        Optional<Order> op = orderRepository.findById(oldOrderId);
        if (!op.isPresent()) {
            OrderServiceImpl.LOGGER.error("[alterOrder][Alter Order Fail][Order do not exist][OrderId: {}]", oldOrderId);
            return new Response<>(0, "Old Order Does Not Exists", null);
        }
        Order oldOrder = op.get();
        oldOrder.setStatus(OrderStatus.CANCEL.getCode());
        saveChanges(oldOrder, headers);
        Order newOrder = oai.getNewOrderInfo();
        newOrder.setId(UUID.randomUUID().toString());
        Response cor = create(oai.getNewOrderInfo(), headers);
        if (cor.getStatus() == 1) {
            OrderServiceImpl.LOGGER.info("[alterOrder][Alter Order Success][newOrderId: {}]",newOrder.getId());
            return new Response<>(1, success, newOrder);
        } else {
            OrderServiceImpl.LOGGER.error("[alterOrder][Alter Order Fail][Create new order fail][newOrderId: {}]", newOrder.getId());
            return new Response<>(0, cor.getMsg(), null);
        }
    }

    @Override
    public Response<ArrayList<Order>> queryOrders(OrderInfo qi, String accountId, HttpHeaders headers) {
        //1.Get all orders of the user
        ArrayList<Order> list = orderRepository.findByAccountId(accountId);
        OrderServiceImpl.LOGGER.info("[queryOrders][Step 1][Get Orders Number of Account][size: {}]", list.size());
        //2.Check is these orders fit the requirement/
        if (qi.isEnableStateQuery() || qi.isEnableBoughtDateQuery() || qi.isEnableTravelDateQuery()) {
            ArrayList<Order> finalList = new ArrayList<>();
            for (Order tempOrder : list) {
                boolean statePassFlag = false;
                boolean boughtDatePassFlag = false;
                boolean travelDatePassFlag = false;
                //3.Check order state requirement.
                if (qi.isEnableStateQuery()) {
                    if (tempOrder.getStatus() != qi.getState()) {
                        statePassFlag = false;
                    } else {
                        statePassFlag = true;
                    }
                } else {
                    statePassFlag = true;
                }
                OrderServiceImpl.LOGGER.info("[queryOrders][Step 2][Check Status Fits End]");
                //4.Check order travel date requirement.
                Date boughtDate = StringUtils.String2Date(tempOrder.getBoughtDate());
                Date travelDate = StringUtils.String2Date(tempOrder.getTravelDate());
                Date travelDateEnd = StringUtils.String2Date(qi.getTravelDateEnd());
                Date boughtDateStart = StringUtils.String2Date(qi.getBoughtDateStart());
                Date boughtDateEnd = StringUtils.String2Date(qi.getBoughtDateEnd());
                if (qi.isEnableTravelDateQuery()) {
                    if (travelDate.before(travelDateEnd) &&
                            travelDate.after(boughtDateStart)) {
                        travelDatePassFlag = true;
                    } else {
                        travelDatePassFlag = false;
                    }
                } else {
                    travelDatePassFlag = true;
                }
                OrderServiceImpl.LOGGER.info("[queryOrders][Step 2][Check Travel Date End]");
                //5.Check order bought date requirement.
                if (qi.isEnableBoughtDateQuery()) {
                    if (boughtDate.before(boughtDateEnd) &&
                            boughtDate.after(boughtDateStart)) {
                        boughtDatePassFlag = true;
                    } else {
                        boughtDatePassFlag = false;
                    }
                } else {
                    boughtDatePassFlag = true;
                }
                OrderServiceImpl.LOGGER.info("[queryOrders][Step 2][Check Bought Date End]");
                //6.check if all requirement fits.
                if (statePassFlag && boughtDatePassFlag && travelDatePassFlag) {
                    finalList.add(tempOrder);
                }
                OrderServiceImpl.LOGGER.info("[queryOrders][Step 2][Check All Requirement End]");
            }
            OrderServiceImpl.LOGGER.info("[queryOrders][Get order num][size:{}]", finalList.size());
            return new Response<>(1, "Get order num", finalList);
        } else {
            OrderServiceImpl.LOGGER.warn("[queryOrders][Orders don't fit the requirement][loginId: {}]", qi.getLoginId());
            return new Response<>(1, "Get order num", list);
        }
    }

    @Override
    public Response queryOrdersForRefresh(OrderInfo qi, String accountId, HttpHeaders headers) {
        ArrayList<Order> orders =   queryOrders(qi, accountId, headers).getData();
        ArrayList<String> stationIds = new ArrayList<>();
        for (Order order : orders) {
            stationIds.add(order.getFrom());
            stationIds.add(order.getTo());
        }

        // List<String> names = queryForStationId(stationIds, headers);
        for (int i = 0; i < orders.size(); i++) {
            orders.get(i).setFrom(stationIds.get(i * 2));
            orders.get(i).setTo(stationIds.get(i * 2 + 1));
        }
        return new Response<>(1, "Query Orders For Refresh Success", orders);
    }

    public List<String> queryForStationId(List<String> ids, HttpHeaders headers) {

        HttpEntity requestEntity = new HttpEntity(ids, null);
        String station_service_url=getServiceUrl("ts-station-service");
        ResponseEntity<Response<List<String>>> re = restTemplate.exchange(
                station_service_url + "/api/v1/stationservice/stations/namelist",
                HttpMethod.POST,
                requestEntity,
                new ParameterizedTypeReference<Response<List<String>>>() {
                });
        OrderServiceImpl.LOGGER.info("[queryForStationId][Station Name List][Name List is: {}]", re.getBody().toString());
        return re.getBody().getData();
    }

    @Override
    public Response saveChanges(Order order, HttpHeaders headers) {
        Optional<Order> op = orderRepository.findById(order.getId());
        if (!op.isPresent()) {
            OrderServiceImpl.LOGGER.error("[saveChanges][Modify Order Fail][Order not found][OrderId: {}]", order.getId());
            return new Response<>(0, orderNotFound, null);
        } else {
            Order oldOrder = op.get();
            oldOrder.setAccountId(order.getAccountId());
            oldOrder.setBoughtDate(order.getBoughtDate());
            oldOrder.setTravelDate(order.getTravelDate());
            oldOrder.setTravelTime(order.getTravelTime());
            oldOrder.setCoachNumber(order.getCoachNumber());
            oldOrder.setSeatClass(order.getSeatClass());
            oldOrder.setSeatNumber(order.getSeatNumber());
            oldOrder.setFrom(order.getFrom());
            oldOrder.setTo(order.getTo());
            oldOrder.setStatus(order.getStatus());
            oldOrder.setTrainNumber(order.getTrainNumber());
            oldOrder.setPrice(order.getPrice());
            oldOrder.setContactsName(order.getContactsName());
            oldOrder.setContactsDocumentNumber(order.getContactsDocumentNumber());
            oldOrder.setDocumentType(order.getDocumentType());
            orderRepository.save(oldOrder);
            OrderServiceImpl.LOGGER.info("[saveChanges][Modify Order Success][OrderId: {}]", order.getId());
            return new Response<>(1, success, oldOrder);
        }
    }

    @Override
    public Response cancelOrder(String accountId, String orderId, HttpHeaders headers) {
        Optional<Order> op = orderRepository.findById(orderId);
        if (!op.isPresent()) {
            OrderServiceImpl.LOGGER.error("[cancelOrder][Cancel Order Fail][Order not found][OrderId: {}]", orderId);
            return new Response<>(0, orderNotFound, null);
        } else {
            Order oldOrder = op.get();
            oldOrder.setStatus(OrderStatus.CANCEL.getCode());
            orderRepository.save(oldOrder);
            OrderServiceImpl.LOGGER.info("[cancelOrder][Cancel Order Success][OrderId: {}]", orderId);
            return new Response<>(1, success, oldOrder);
        }
    }

    @Override
    public Response queryAlreadySoldOrders(Date travelDate, String trainNumber, HttpHeaders headers) {
        ArrayList<Order> orders = orderRepository.findByTravelDateAndTrainNumber(StringUtils.Date2String(travelDate), trainNumber);
        SoldTicket cstr = new SoldTicket();
        cstr.setTravelDate(travelDate);
        cstr.setTrainNumber(trainNumber);
        OrderServiceImpl.LOGGER.info("[queryAlreadySoldOrders][Calculate Sold Ticket][Get Orders Number: {}]", orders.size());
        for (Order order : orders) {
            if (order.getStatus() >= OrderStatus.CHANGE.getCode()) {
                continue;
            }
            if (order.getSeatClass() == SeatClass.NONE.getCode()) {
                cstr.setNoSeat(cstr.getNoSeat() + 1);
            } else if (order.getSeatClass() == SeatClass.BUSINESS.getCode()) {
                cstr.setBusinessSeat(cstr.getBusinessSeat() + 1);
            } else if (order.getSeatClass() == SeatClass.FIRSTCLASS.getCode()) {
                cstr.setFirstClassSeat(cstr.getFirstClassSeat() + 1);
            } else if (order.getSeatClass() == SeatClass.SECONDCLASS.getCode()) {
                cstr.setSecondClassSeat(cstr.getSecondClassSeat() + 1);
            } else if (order.getSeatClass() == SeatClass.HARDSEAT.getCode()) {
                cstr.setHardSeat(cstr.getHardSeat() + 1);
            } else if (order.getSeatClass() == SeatClass.SOFTSEAT.getCode()) {
                cstr.setSoftSeat(cstr.getSoftSeat() + 1);
            } else if (order.getSeatClass() == SeatClass.HARDBED.getCode()) {
                cstr.setHardBed(cstr.getHardBed() + 1);
            } else if (order.getSeatClass() == SeatClass.SOFTBED.getCode()) {
                cstr.setSoftBed(cstr.getSoftBed() + 1);
            } else if (order.getSeatClass() == SeatClass.HIGHSOFTBED.getCode()) {
                cstr.setHighSoftBed(cstr.getHighSoftBed() + 1);
            } else {
                OrderServiceImpl.LOGGER.info("[queryAlreadySoldOrders][Calculate Sold Tickets][Seat class not exists][Order ID: {}]", order.getId());
            }
        }
        return new Response<>(1, success, cstr);
    }

    @Override
    public Response getAllOrders(HttpHeaders headers) {
        ArrayList<Order> orders = orderRepository.findAll();
        if (orders != null && !orders.isEmpty()) {
            OrderServiceImpl.LOGGER.warn("[getAllOrders][Find all orders Success][size:{}]",orders.size());
            return new Response<>(1, "Success.", orders);
        } else {
            OrderServiceImpl.LOGGER.warn("[getAllOrders][Find all orders Fail][{}]","No content");
            return new Response<>(0, "No Content.", null);
        }
    }

    @Override
    public Response modifyOrder(String orderId, int status, HttpHeaders headers) {
        Optional<Order> op = orderRepository.findById(orderId);
        if (!op.isPresent()) {
            OrderServiceImpl.LOGGER.error("[modifyOrder][Modify order Fail][Order not found][OrderId: {}]",orderId);
            return new Response<>(0, orderNotFound, null);
        } else {
            Order order = op.get();
            order.setStatus(status);
            orderRepository.save(order);
            OrderServiceImpl.LOGGER.info("[modifyOrder][Modify order Success][OrderId: {}]",orderId);
            return new Response<>(1, "Modify Order Success", order);
        }
    }

    @Override
    public Response getOrderPrice(String orderId, HttpHeaders headers) {
        Optional<Order> op = orderRepository.findById(orderId);
        if (!op.isPresent()) {
            OrderServiceImpl.LOGGER.error("[getOrderPrice][Get order price Fail][Order not found][OrderId: {}]",orderId);
            return new Response<>(0, orderNotFound, "-1.0");
        } else {
            Order order = op.get();
            OrderServiceImpl.LOGGER.info("[getOrderPrice][Get Order Price Success][OrderId: {} , Price: {}]",orderId ,order.getPrice());
            return new Response<>(1, success, order.getPrice());
        }
    }

    @Override
    public Response payOrder(String orderId, HttpHeaders headers) {
        Optional<Order> op = orderRepository.findById(orderId);
        if (!op.isPresent()) {
            OrderServiceImpl.LOGGER.error("[payOrder][Pay order Fail][Order not found][OrderId: {}]",orderId);
            return new Response<>(0, orderNotFound, null);
        } else {
            Order order = op.get();
            order.setStatus(OrderStatus.PAID.getCode());
            orderRepository.save(order);
            OrderServiceImpl.LOGGER.info("[payOrder][Pay order Success][OrderId: {}]",orderId);
            return new Response<>(1, "Pay Order Success.", order);
        }
    }

    @Override
    public Response getOrderById(String orderId, HttpHeaders headers) {
        Optional<Order> op = orderRepository.findById(orderId);
        if (!op.isPresent()) {
            OrderServiceImpl.LOGGER.warn("[getOrderById][Get Order By ID Fail][Order not found][OrderId: {}]",orderId);
            return new Response<>(0, orderNotFound, null);
        } else {
            Order order = op.get();
            OrderServiceImpl.LOGGER.info("[getOrderById][Get Order By ID Success][OrderId: {}]",orderId);
            return new Response<>(1, "Success.", order);
        }
    }

    @Override
    public void initOrder(Order order, HttpHeaders headers) {
        Optional<Order> op = orderRepository.findById(order.getId());
        if (!op.isPresent()) {
            orderRepository.save(order);
            OrderServiceImpl.LOGGER.info("[initOrder][Init Order Success][OrderId: {}]", order.getId());
        } else {
            Order orderTemp = op.get();
            OrderServiceImpl.LOGGER.error("[initOrder][Init Order Fail][Order Already Exists][OrderId: {}]", order.getId());
        }
    }

    @Override
    public Response checkSecurityAboutOrder(Date dateFrom, String accountId, HttpHeaders headers) {
        OrderSecurity result = new OrderSecurity();
        ArrayList<Order> orders = orderRepository.findByAccountId(accountId);
        int countOrderInOneHour = 0;
        int countTotalValidOrder = 0;
        Calendar ca = Calendar.getInstance();
        ca.setTime(dateFrom);
        ca.add(Calendar.HOUR_OF_DAY, -1);
        dateFrom = ca.getTime();
        for (Order order : orders) {
            if (order.getStatus() == OrderStatus.NOTPAID.getCode() ||
                    order.getStatus() == OrderStatus.PAID.getCode() ||
                    order.getStatus() == OrderStatus.COLLECTED.getCode()) {
                countTotalValidOrder += 1;
            }
            Date boughtDate = StringUtils.String2Date(order.getBoughtDate());
            if (boughtDate.after(dateFrom)) {
                countOrderInOneHour += 1;
            }
        }
        result.setOrderNumInLastOneHour(countOrderInOneHour);
        result.setOrderNumOfValidOrder(countTotalValidOrder);
        return new Response<>(1, "Check Security Success . ", result);
    }

    @Override
    public Response deleteOrder(String orderId, HttpHeaders headers) {
        String orderUuid = UUID.fromString(orderId).toString();

        Optional<Order> op = orderRepository.findById(orderUuid);
        if (!op.isPresent()) {
            OrderServiceImpl.LOGGER.error("[deleteOrder][Delete order Fail][Order not found][OrderId: {}]",orderId);
            return new Response<>(0, "Order Not Exist.", null);
        } else {
            Order order = op.get();
            orderRepository.deleteById(orderUuid);
            OrderServiceImpl.LOGGER.info("[deleteOrder][Delete order Success][OrderId: {}]",orderId);
            return new Response<>(1, "Delete Order Success", order);
        }
    }

    @Override
    public Response addNewOrder(Order order, HttpHeaders headers) {
        OrderServiceImpl.LOGGER.info("[addNewOrder][Admin Add Order][Ready to Add Order]");
        ArrayList<Order> accountOrders = orderRepository.findByAccountId(order.getAccountId());
        if (accountOrders.contains(order)) {
            OrderServiceImpl.LOGGER.error("[addNewOrder][Admin Add Order Fail][Order already exists][OrderId: {}]",order.getId());
            return new Response<>(0, "Order already exist", null);
        } else {
            order.setId(UUID.randomUUID().toString());
            orderRepository.save(order);
            OrderServiceImpl.LOGGER.info("[addNewOrder][Admin Add Order Success][OrderId: {} , Price: {}]",order.getId() ,order.getPrice());
            return new Response<>(1, "Add new Order Success", order);
        }
    }

    @Override
    public Response updateOrder(Order order, HttpHeaders headers) {
        LOGGER.info("[updateOrder][Admin Update Order][Order Info:{}] ", order.toString());
        Optional<Order> op = orderRepository.findById(order.getId());
        if (!op.isPresent()) {
            OrderServiceImpl.LOGGER.error("[updateOrder][Admin Update Order Fail][Order not found][OrderId: {}]",order.getId());
            return new Response<>(0, "Order Not Found, Can't update", null);
        } else {
            Order oldOrder = op.get();
            //OrderServiceImpl.LOGGER.info("{}", oldOrder.toString());
            oldOrder.setAccountId(order.getAccountId());
            oldOrder.setBoughtDate(order.getBoughtDate());
            oldOrder.setTravelDate(order.getTravelDate());
            oldOrder.setTravelTime(order.getTravelTime());
            oldOrder.setCoachNumber(order.getCoachNumber());
            oldOrder.setSeatClass(order.getSeatClass());
            oldOrder.setSeatNumber(order.getSeatNumber());
            oldOrder.setFrom(order.getFrom());
            oldOrder.setTo(order.getTo());
            oldOrder.setStatus(order.getStatus());
            oldOrder.setTrainNumber(order.getTrainNumber());
            oldOrder.setPrice(order.getPrice());
            oldOrder.setContactsName(order.getContactsName());
            oldOrder.setContactsDocumentNumber(order.getContactsDocumentNumber());
            oldOrder.setDocumentType(order.getDocumentType());
            orderRepository.save(oldOrder);
            OrderServiceImpl.LOGGER.info("[updateOrder][Admin Update Order Success][OrderId: {}]",order.getId());
            return new Response<>(1, "Admin Update Order Success", oldOrder);
        }
    }
}



// Node: repos/cloned_ms_repos/train-ticket/ts-order-service/src/main/java/order/service/OrderServiceImpl.java:OrderServiceImpl.<init>
package order.service;

import edu.fudan.common.entity.Seat;
import edu.fudan.common.util.Response;
import order.entity.*;
import org.springframework.http.HttpHeaders;

import java.util.Date;
import java.util.UUID;

/**
 * @author fdse
 */
public interface OrderService {

    Response findOrderById(String id, HttpHeaders headers);

    Response create(Order newOrder, HttpHeaders headers);

    Response saveChanges(Order order, HttpHeaders headers);

    Response cancelOrder(String accountId, String orderId, HttpHeaders headers);

    Response queryOrders(OrderInfo qi, String accountId, HttpHeaders headers);

    Response queryOrdersForRefresh(OrderInfo qi, String accountId, HttpHeaders headers);

    Response alterOrder(OrderAlterInfo oai, HttpHeaders headers);

    Response queryAlreadySoldOrders(Date travelDate, String trainNumber, HttpHeaders headers);

    Response getAllOrders(HttpHeaders headers);

    Response modifyOrder(String orderId, int status, HttpHeaders headers);

    Response getOrderPrice(String orderId, HttpHeaders headers);

    Response payOrder(String orderId, HttpHeaders headers);

    Response getOrderById(String orderId , HttpHeaders headers);

    Response checkSecurityAboutOrder(Date checkDate, String accountId, HttpHeaders headers);

    void initOrder(Order order, HttpHeaders headers);

    Response deleteOrder(String orderId, HttpHeaders headers);

    Response getSoldTickets(Seat seatRequest, HttpHeaders headers);

    Response addNewOrder(Order order, HttpHeaders headers);

    Response updateOrder(Order order, HttpHeaders headers);
}


// Node: repos/cloned_ms_repos/train-ticket/ts-order-service/src/main/java/order/service/OrderService.java:OrderService.<init>
package travel.controller;

import edu.fudan.common.entity.TravelInfo;
import edu.fudan.common.entity.TripAllDetailInfo;
import edu.fudan.common.entity.TripInfo;
import edu.fudan.common.entity.TripResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import edu.fudan.common.entity.TravelInfo;
import travel.entity.*;
import travel.service.TravelService;

import java.util.ArrayList;

import static org.springframework.http.ResponseEntity.ok;

/**
 * @author fdse
 */
@RestController
@RequestMapping("/api/v1/travelservice")

public class TravelController {

    @Autowired
    private TravelService travelService;

    private static final Logger LOGGER = LoggerFactory.getLogger(TravelController.class);

    @GetMapping(path = "/welcome")
    public String home(@RequestHeader HttpHeaders headers) {
        return "Welcome to [ Travel Service ] !";
    }

    @GetMapping(value = "/train_types/{tripId}")
    public HttpEntity getTrainTypeByTripId(@PathVariable String tripId,
                                           @RequestHeader HttpHeaders headers) {
        // TrainType
        TravelController.LOGGER.info("[getTrainTypeByTripId][Get train Type by Trip id][TripId: {}]", tripId);
        return ok(travelService.getTrainTypeByTripId(tripId, headers));
    }

    @GetMapping(value = "/routes/{tripId}")
    public HttpEntity getRouteByTripId(@PathVariable String tripId,
                                       @RequestHeader HttpHeaders headers) {
        TravelController.LOGGER.info("[getRouteByTripId][Get Route By Trip ID][TripId: {}]", tripId);
        //Route
        return ok(travelService.getRouteByTripId(tripId, headers));
    }

    @PostMapping(value = "/trips/routes")
    public HttpEntity getTripsByRouteId(@RequestBody ArrayList<String> routeIds,
                                        @RequestHeader HttpHeaders headers) {
        // ArrayList<ArrayList<Trip>>
        TravelController.LOGGER.info("[getTripByRoute][Get Trips by Route ids][RouteIds: {}]", routeIds.size());
        return ok(travelService.getTripByRoute(routeIds, headers));
    }

    @CrossOrigin(origins = "*")
    @PostMapping(value = "/trips")
    public HttpEntity<?> createTrip(@RequestBody TravelInfo routeIds, @RequestHeader HttpHeaders headers) {
        // null
        TravelController.LOGGER.info("[create][Create trip][TripId: {}]", routeIds.getTripId());
        return new ResponseEntity<>(travelService.create(routeIds, headers), HttpStatus.CREATED);
    }

    /**
     * Return Trip only, no left ticket information
     *
     * @param tripId  trip id
     * @param headers headers
     * @return HttpEntity
     */
    @CrossOrigin(origins = "*")
    @GetMapping(value = "/trips/{tripId}")
    public HttpEntity retrieve(@PathVariable String tripId, @RequestHeader HttpHeaders headers) {
        // Trip
        TravelController.LOGGER.info("[retrieve][Retrieve trip][TripId: {}]", tripId);
        return ok(travelService.retrieve(tripId, headers));
    }

    @CrossOrigin(origins = "*")
    @PutMapping(value = "/trips")
    public HttpEntity updateTrip(@RequestBody TravelInfo info, @RequestHeader HttpHeaders headers) {
        // Trip
        TravelController.LOGGER.info("[update][Update trip][TripId: {}]", info.getTripId());
        return ok(travelService.update(info, headers));
    }

    @CrossOrigin(origins = "*")
    @DeleteMapping(value = "/trips/{tripId}")
    public HttpEntity deleteTrip(@PathVariable String tripId, @RequestHeader HttpHeaders headers) {
        // string
        TravelController.LOGGER.info("[delete][Delete trip][TripId: {}]", tripId);
        return ok(travelService.delete(tripId, headers));
    }

    /**
     * Return Trips and the remaining tickets
     *
     * @param info    trip info
     * @param headers headers
     * @return HttpEntity
     */
    @CrossOrigin(origins = "*")
    @PostMapping(value = "/trips/left")
    public HttpEntity queryInfo(@RequestBody TripInfo info, @RequestHeader HttpHeaders headers) {
        if (info.getStartPlace() == null || info.getStartPlace().length() == 0 ||
                info.getEndPlace() == null || info.getEndPlace().length() == 0 ||
                info.getDepartureTime() == null) {
            TravelController.LOGGER.info("[query][Travel Query Fail][Something null]");
            ArrayList<TripResponse> errorList = new ArrayList<>();
            return ok(errorList);
        }
        TravelController.LOGGER.info("[query][Query TripResponse]");
        return ok(travelService.queryByBatch(info, headers));
    }

    /**
     * Return Trips and the remaining tickets
     *
     * @param info    trip info
     * @param headers headers
     * @return HttpEntity
     */
    @CrossOrigin(origins = "*")
    @PostMapping(value = "/trips/left_parallel")
    public HttpEntity queryInfoInparallel(@RequestBody TripInfo info, @RequestHeader HttpHeaders headers) {
        if (info.getStartPlace() == null || info.getStartPlace().length() == 0 ||
                info.getEndPlace() == null || info.getEndPlace().length() == 0 ||
                info.getDepartureTime() == null) {
            TravelController.LOGGER.info("[queryInParallel][Travel Query Fail][Something null]");
            ArrayList<TripResponse> errorList = new ArrayList<>();
            return ok(errorList);
        }
        TravelController.LOGGER.info("[queryInParallel][Query TripResponse]");
        return ok(travelService.queryInParallel(info, headers));
    }

    /**
     * Return a Trip and the remaining
     *
     * @param gtdi    trip all detail info
     * @param headers headers
     * @return HttpEntity
     */
    @CrossOrigin(origins = "*")
    @PostMapping(value = "/trip_detail")
    public HttpEntity getTripAllDetailInfo(@RequestBody TripAllDetailInfo gtdi, @RequestHeader HttpHeaders headers) {
        // TripAllDetailInfo
        // TripAllDetail tripAllDetail
        TravelController.LOGGER.info("[getTripAllDetailInfo][Get trip detail][TripId: {}]", gtdi.getTripId());
        return ok(travelService.getTripAllDetailInfo(gtdi, headers));
    }

    @CrossOrigin(origins = "*")
    @GetMapping(value = "/trips")
    public HttpEntity queryAll(@RequestHeader HttpHeaders headers) {
        // List<Trip>
        TravelController.LOGGER.info("[queryAll][Query all trips]");
        return ok(travelService.queryAll(headers));
    }

    @CrossOrigin(origins = "*")
    @GetMapping(value = "/admin_trip")
    public HttpEntity adminQueryAll(@RequestHeader HttpHeaders headers) {
        // ArrayList<AdminTrip>
        TravelController.LOGGER.info("[adminQueryAll][Admin query all trips]");
        return ok(travelService.adminQueryAll(headers));
    }

}


// Node: repos/cloned_ms_repos/train-ticket/ts-travel-service/src/main/java/travel/controller/TravelController.java:TravelController.<init>
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


// Node: repos/cloned_ms_repos/train-ticket/ts-travel-service/src/main/java/travel/service/TravelServiceImpl.java:TravelServiceImpl.<init>
// Node: newFixedThreadPool
// Node: CustomizableThreadFactory
package preserve.mq;


import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.amqp.core.AmqpTemplate;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;
import preserve.config.Queues;

@Component
public class RabbitSend {

    @Autowired
    private AmqpTemplate rabbitTemplate;
    private static final Logger logger = LoggerFactory.getLogger(RabbitSend.class);

    public void send(String val) {
        logger.info("send info to mq:" + val);
        this.rabbitTemplate.convertAndSend(Queues.queueName, val);
    }

}


// Node: repos/cloned_ms_repos/train-ticket/ts-preserve-service/src/main/java/preserve/mq/RabbitSend.java:RabbitSend.<init>
package preserve.controller;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.web.bind.annotation.*;
import edu.fudan.common.entity.*;
import preserve.service.PreserveService;

import static org.springframework.http.ResponseEntity.ok;

/**
 * @author fdse
 */
@RestController
@RequestMapping("/api/v1/preserveservice")
public class PreserveController {

    @Autowired
    private PreserveService preserveService;

    private static final Logger LOGGER = LoggerFactory.getLogger(PreserveController.class);

    @GetMapping(path = "/welcome")
    public String home() {
        return "Welcome to [ Preserve Service ] !";
    }

    @CrossOrigin(origins = "*")
    @PostMapping(value = "/preserve")
    public HttpEntity preserve(@RequestBody OrderTicketsInfo oti,
                               @RequestHeader HttpHeaders headers) {
        PreserveController.LOGGER.info("[preserve][Preserve Account order][from {} to {} at {}]", oti.getFrom(), oti.getTo(), oti.getDate());
        return ok(preserveService.preserve(oti, headers));
    }

}


// Node: repos/cloned_ms_repos/train-ticket/ts-preserve-service/src/main/java/preserve/controller/PreserveController.java:PreserveController.<init>
package preserve.service;

import edu.fudan.common.util.JsonUtils;
import edu.fudan.common.util.Response;
import edu.fudan.common.util.StringUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.cloud.client.ServiceInstance;
import org.springframework.cloud.client.discovery.DiscoveryClient;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import edu.fudan.common.entity.*;
import preserve.mq.RabbitSend;

import java.util.Date;
import java.util.List;
import java.util.UUID;

/**
 * @author fdse
 */
@Service
public class PreserveServiceImpl implements PreserveService {

    @Autowired
    private RestTemplate restTemplate;

    @Autowired
    private RabbitSend sendService;

    @Autowired
    private DiscoveryClient discoveryClient;


    private static final Logger LOGGER = LoggerFactory.getLogger(PreserveServiceImpl.class);

    private String getServiceUrl(String serviceName) {
        return "http://" + serviceName; }

    @Override
    public Response preserve(OrderTicketsInfo oti, HttpHeaders headers) {
        //1.detect ticket scalper
        //PreserveServiceImpl.LOGGER.info("[Step 1] Check Security");

        Response result = checkSecurity(oti.getAccountId(), headers);
        if (result.getStatus() == 0) {
            PreserveServiceImpl.LOGGER.error("[preserve][Step 1][Check Security Fail][AccountId: {}]",oti.getAccountId());
            return new Response<>(0, result.getMsg(), null);
        }
        PreserveServiceImpl.LOGGER.info("[preserve][Step 1][Check Security Complete][AccountId: {}]",oti.getAccountId());
        //2.Querying contact information -- modification, mediated by the underlying information micro service
        //PreserveServiceImpl.LOGGER.info("[Step 2] Find contacts");
        //PreserveServiceImpl.LOGGER.info("[Step 2] Contacts Id: {}", oti.getContactsId());

        Response<Contacts> gcr = getContactsById(oti.getContactsId(), headers);
        if (gcr.getStatus() == 0) {
            PreserveServiceImpl.LOGGER.error("[preserve][Step 2][Find Contacts Fail][ContactsId: {},message: {}]",oti.getContactsId(),gcr.getMsg());
            return new Response<>(0, gcr.getMsg(), null);
        }
        PreserveServiceImpl.LOGGER.info("[preserve][Step 2][Find contacts Complete][ContactsId: {}]",oti.getContactsId());
        //3.Check the info of train and the number of remaining tickets
        //PreserveServiceImpl.LOGGER.info("[Step 3] Check tickets num");
        TripAllDetailInfo gtdi = new TripAllDetailInfo();

        gtdi.setFrom(oti.getFrom());
        gtdi.setTo(oti.getTo());

        gtdi.setTravelDate(oti.getDate());
        gtdi.setTripId(oti.getTripId());
        PreserveServiceImpl.LOGGER.info("[preserve][Step 3][Check tickets num][TripId: {}]", oti.getTripId());
        Response<TripAllDetail> response = getTripAllDetailInformation(gtdi, headers);
        TripAllDetail gtdr = response.getData();
        //LOGGER.info("TripAllDetail:" + gtdr.toString());
        if (response.getStatus() == 0) {
            PreserveServiceImpl.LOGGER.error("[preserve][Step 3][Check tickets num][Search For Trip Detail Information error][TripId: {}, message: {}]", gtdi.getTripId(), response.getMsg());
            return new Response<>(0, response.getMsg(), null);
        } else {
            TripResponse tripResponse = gtdr.getTripResponse();
            //LOGGER.info("TripResponse:" + tripResponse.toString());
            if (oti.getSeatType() == SeatClass.FIRSTCLASS.getCode()) {
                if (tripResponse.getConfortClass() == 0) {
                    PreserveServiceImpl.LOGGER.warn("[preserve][Step 3][Check seat][Check seat is enough][TripId: {}]",oti.getTripId());
                    return new Response<>(0, "Seat Not Enough", null);
                }
            } else {
                if (tripResponse.getEconomyClass() == SeatClass.SECONDCLASS.getCode() && tripResponse.getConfortClass() == 0) {
                    PreserveServiceImpl.LOGGER.warn("[preserve][Step 3][Check seat][Check seat is Not enough][TripId: {}]",oti.getTripId());
                    return new Response<>(0, "Seat Not Enough", null);
                }
            }
        }
        Trip trip = gtdr.getTrip();
        PreserveServiceImpl.LOGGER.info("[preserve][Step 3][Check tickets num][Tickets Enough]");
        //4.send the order request and set the order information
        //PreserveServiceImpl.LOGGER.info("[Step 4] Do Order");
        Contacts contacts = gcr.getData();
        Order order = new Order();
        UUID orderId = UUID.randomUUID();
        order.setId(orderId.toString());
        order.setTrainNumber(oti.getTripId());
        order.setAccountId(oti.getAccountId());

        String fromStationName = oti.getFrom();
        String toStationName = oti.getTo();

        order.setFrom(fromStationName);
        order.setTo(toStationName);
        order.setBoughtDate(StringUtils.Date2String(new Date()));
        order.setStatus(OrderStatus.NOTPAID.getCode());
        order.setContactsDocumentNumber(contacts.getDocumentNumber());
        order.setContactsName(contacts.getName());
        order.setDocumentType(contacts.getDocumentType());

        Travel query = new Travel();
        query.setTrip(trip);
        query.setStartPlace(oti.getFrom());
        query.setEndPlace(oti.getTo());
        query.setDepartureTime(StringUtils.Date2String(new Date()));

        HttpEntity requestEntity = new HttpEntity(query, headers);
        String basic_service_url = getServiceUrl("ts-basic-service");
        ResponseEntity<Response<TravelResult>> re = restTemplate.exchange(
                basic_service_url + "/api/v1/basicservice/basic/travel",
                HttpMethod.POST,
                requestEntity,
                new ParameterizedTypeReference<Response<TravelResult>>() {
                });
        if(re.getBody().getStatus() == 0){
            PreserveServiceImpl.LOGGER.info("[Preserve 3][Get basic travel response status is 0][response is: {}]", re.getBody());
            return new Response<>(0, re.getBody().getMsg(), null);
        }
        TravelResult resultForTravel = re.getBody().getData();

        order.setSeatClass(oti.getSeatType());
        PreserveServiceImpl.LOGGER.info("[preserve][Step 4][Do Order][Travel Date][Date is: {}]", oti.getDate().toString());
        order.setTravelDate(oti.getDate());
        order.setTravelTime(gtdr.getTripResponse().getStartTime());

        //Dispatch the seat
        List<String> stationList = resultForTravel.getRoute().getStations();
        if (oti.getSeatType() == SeatClass.FIRSTCLASS.getCode()) {
            int firstClassTotalNum = resultForTravel.getTrainType().getConfortClass();
            Ticket ticket =
                    dipatchSeat(oti.getDate(),
                            order.getTrainNumber(), fromStationName, toStationName,
                            SeatClass.FIRSTCLASS.getCode(), firstClassTotalNum, stationList, headers);
            order.setSeatNumber("" + ticket.getSeatNo());
            order.setSeatClass(SeatClass.FIRSTCLASS.getCode());
            order.setPrice(resultForTravel.getPrices().get("confortClass"));
        } else {
            int secondClassTotalNum = resultForTravel.getTrainType().getEconomyClass();
            Ticket ticket =
                    dipatchSeat(oti.getDate(),
                            order.getTrainNumber(), fromStationName, toStationName,
                            SeatClass.SECONDCLASS.getCode(), secondClassTotalNum, stationList, headers);
            order.setSeatClass(SeatClass.SECONDCLASS.getCode());
            order.setSeatNumber("" + ticket.getSeatNo());
            order.setPrice(resultForTravel.getPrices().get("economyClass"));
        }

        PreserveServiceImpl.LOGGER.info("[preserve][Step 4][Do Order][Order Price][Price is: {}]", order.getPrice());

        Response<Order> cor = createOrder(order, headers);
        if (cor.getStatus() == 0) {
            PreserveServiceImpl.LOGGER.error("[preserve][Step 4][Do Order][Create Order Fail][OrderId: {},  Reason: {}]", order.getId(), cor.getMsg());
            return new Response<>(0, cor.getMsg(), null);
        }
        PreserveServiceImpl.LOGGER.info("[preserve][Step 4][Do Order][Do Order Complete]");

        Response returnResponse = new Response<>(1, "Success.", cor.getMsg());
        //5.Check insurance options
        if (oti.getAssurance() == 0) {
            PreserveServiceImpl.LOGGER.info("[preserve][Step 5][Buy Assurance][Do not need to buy assurance]");
        } else {
            Response addAssuranceResult = addAssuranceForOrder(
                    oti.getAssurance(), cor.getData().getId().toString(), headers);
            if (addAssuranceResult.getStatus() == 1) {
                PreserveServiceImpl.LOGGER.info("[preserve][Step 5][Buy Assurance][Preserve Buy Assurance Success]");
            } else {
                PreserveServiceImpl.LOGGER.warn("[preserve][Step 5][Buy Assurance][Buy Assurance Fail][assurance: {}, OrderId: {}]", oti.getAssurance(),cor.getData().getId());
                returnResponse.setMsg("Success.But Buy Assurance Fail.");
            }
        }

        //6.Increase the food order
        if (oti.getFoodType() != 0) {

            FoodOrder foodOrder = new FoodOrder();
            foodOrder.setOrderId(cor.getData().getId());
            foodOrder.setFoodType(oti.getFoodType());
            foodOrder.setFoodName(oti.getFoodName());
            foodOrder.setPrice(oti.getFoodPrice());

            if (oti.getFoodType() == 2) {
                foodOrder.setStationName(oti.getStationName());
                foodOrder.setStoreName(oti.getStoreName());
                //PreserveServiceImpl.LOGGER.info("foodstore= {}   {}   {}", foodOrder.getFoodType(), foodOrder.getStationName(), foodOrder.getStoreName());
            }
            Response afor = createFoodOrder(foodOrder, headers);
            if (afor.getStatus() == 1) {
                PreserveServiceImpl.LOGGER.info("[preserve][Step 6][Buy Food][Buy Food Success]");
            } else {
                PreserveServiceImpl.LOGGER.error("[preserve][Step 6][Buy Food][Buy Food Fail][OrderId: {}]",cor.getData().getId());
                returnResponse.setMsg("Success.But Buy Food Fail.");
            }
        } else {
            PreserveServiceImpl.LOGGER.info("[preserve][Step 6][Buy Food][Do not need to buy food]");
        }

        //7.add consign
        if (null != oti.getConsigneeName() && !"".equals(oti.getConsigneeName())) {

            Consign consignRequest = new Consign();
            consignRequest.setOrderId(cor.getData().getId());
            consignRequest.setAccountId(cor.getData().getAccountId());
            consignRequest.setHandleDate(oti.getHandleDate());
            consignRequest.setTargetDate(cor.getData().getTravelDate().toString());
            consignRequest.setFrom(cor.getData().getFrom());
            consignRequest.setTo(cor.getData().getTo());
            consignRequest.setConsignee(oti.getConsigneeName());
            consignRequest.setPhone(oti.getConsigneePhone());
            consignRequest.setWeight(oti.getConsigneeWeight());
            consignRequest.setWithin(oti.isWithin());
            LOGGER.info("CONSIGN INFO : " +consignRequest.toString());
            Response icresult = createConsign(consignRequest, headers);
            if (icresult.getStatus() == 1) {
                PreserveServiceImpl.LOGGER.info("[preserve][Step 7][Add Consign][Consign Success]");
            } else {
                PreserveServiceImpl.LOGGER.error("[preserve][Step 7][Add Consign][Preserve Consign Fail][OrderId: {}]", cor.getData().getId());
                returnResponse.setMsg("Consign Fail.");
            }
        } else {
            PreserveServiceImpl.LOGGER.info("[preserve][Step 7][Add Consign][Do not need to consign]");
        }

        //8.send notification

        User getUser = getAccount(order.getAccountId().toString(), headers);

        NotifyInfo notifyInfo = new NotifyInfo();
        notifyInfo.setDate(new Date().toString());

        notifyInfo.setEmail(getUser.getEmail());
        notifyInfo.setStartPlace(order.getFrom());
        notifyInfo.setEndPlace(order.getTo());
        notifyInfo.setUsername(getUser.getUserName());
        notifyInfo.setSeatNumber(order.getSeatNumber());
        notifyInfo.setOrderNumber(order.getId().toString());
        notifyInfo.setPrice(order.getPrice());
        notifyInfo.setSeatClass(SeatClass.getNameByCode(order.getSeatClass()));
        notifyInfo.setStartTime(order.getTravelTime().toString());

        // TODO: change to async message serivce
        // sendEmail(notifyInfo, headers);

        return returnResponse;
    }

    public Ticket dipatchSeat(String date, String tripId, String startStation, String endStataion, int seatType, int totalNum, List<String> stationList, HttpHeaders httpHeaders) {
        Seat seatRequest = new Seat();
        seatRequest.setTravelDate(date);
        seatRequest.setTrainNumber(tripId);
        seatRequest.setStartStation(startStation);
        seatRequest.setDestStation(endStataion);
        seatRequest.setSeatType(seatType);
        seatRequest.setTotalNum(totalNum);
        seatRequest.setStations(stationList);

        HttpEntity requestEntityTicket = new HttpEntity(seatRequest, httpHeaders);
        String seat_service_url = getServiceUrl("ts-seat-service");
        ResponseEntity<Response<Ticket>> reTicket = restTemplate.exchange(
                seat_service_url + "/api/v1/seatservice/seats",
                HttpMethod.POST,
                requestEntityTicket,
                new ParameterizedTypeReference<Response<Ticket>>() {
                });

        return reTicket.getBody().getData();
    }

    public boolean sendEmail(NotifyInfo notifyInfo, HttpHeaders httpHeaders) {
        try {
            String infoJson = JsonUtils.object2Json(notifyInfo);
            sendService.send(infoJson);
            PreserveServiceImpl.LOGGER.info("[sendEmail][Send email to mq success]");
        } catch (Exception e) {
            PreserveServiceImpl.LOGGER.error("[sendEmail][Send email to mq error] exception is:" + e);
            return false;
        }

        return true;
    }

    public User getAccount(String accountId, HttpHeaders httpHeaders) {
        PreserveServiceImpl.LOGGER.info("[getAccount][Cancel Order Service][Get Order By Id]");

        HttpEntity requestEntitySendEmail = new HttpEntity(httpHeaders);
        String user_service_url = getServiceUrl("ts-user-service");
        ResponseEntity<Response<User>> getAccount = restTemplate.exchange(
                user_service_url + "/api/v1/userservice/users/id/" + accountId,
                HttpMethod.GET,
                requestEntitySendEmail,
                new ParameterizedTypeReference<Response<User>>() {
                });
        Response<User> result = getAccount.getBody();
        return result.getData();
    }

    private Response addAssuranceForOrder(int assuranceType, String orderId, HttpHeaders httpHeaders) {
        PreserveServiceImpl.LOGGER.info("[addAssuranceForOrder][Preserve Service][Add Assurance Type For Order]");
        HttpEntity requestAddAssuranceResult = new HttpEntity(httpHeaders);
        String assurance_service_url = getServiceUrl("ts-assurance-service");
        ResponseEntity<Response> reAddAssuranceResult = restTemplate.exchange(
                assurance_service_url + "/api/v1/assuranceservice/assurances/" + assuranceType + "/" + orderId,
                HttpMethod.GET,
                requestAddAssuranceResult,
                Response.class);

        return reAddAssuranceResult.getBody();
    }

    private String queryForStationId(String stationName, HttpHeaders httpHeaders) {
        PreserveServiceImpl.LOGGER.info("[queryForStationId][Preserve Other Service][Get Station By  Name]");


        HttpEntity requestQueryForStationId = new HttpEntity(httpHeaders);
        String station_service_url = getServiceUrl("ts-station-service");
        ResponseEntity<Response<String>> reQueryForStationId = restTemplate.exchange(
                station_service_url + "/api/v1/stationservice/stations/id/" + stationName,
                HttpMethod.GET,
                requestQueryForStationId,
                new ParameterizedTypeReference<Response<String>>() {
                });

        return reQueryForStationId.getBody().getData();
    }

    private Response checkSecurity(String accountId, HttpHeaders httpHeaders) {
        PreserveServiceImpl.LOGGER.info("[checkSecurity][Preserve Other Service][Check Account Security]");

        HttpEntity requestCheckResult = new HttpEntity(httpHeaders);
        String security_service_url = getServiceUrl("ts-security-service");
        ResponseEntity<Response> reCheckResult = restTemplate.exchange(
                security_service_url + "/api/v1/securityservice/securityConfigs/" + accountId,
                HttpMethod.GET,
                requestCheckResult,
                Response.class);

        return reCheckResult.getBody();
    }


    private Response<TripAllDetail> getTripAllDetailInformation(TripAllDetailInfo gtdi, HttpHeaders httpHeaders) {
        PreserveServiceImpl.LOGGER.info("[getTripAllDetailInformation][Preserve Other Service][Get Trip All Detail Information]");

        HttpEntity requestGetTripAllDetailResult = new HttpEntity(gtdi, httpHeaders);
        String travel_service_url = getServiceUrl("ts-travel-service");
        ResponseEntity<Response<TripAllDetail>> reGetTripAllDetailResult = restTemplate.exchange(
                travel_service_url + "/api/v1/travelservice/trip_detail",
                HttpMethod.POST,
                requestGetTripAllDetailResult,
                new ParameterizedTypeReference<Response<TripAllDetail>>() {
                });

        return reGetTripAllDetailResult.getBody();
    }


    private Response<Contacts> getContactsById(String contactsId, HttpHeaders httpHeaders) {
        PreserveServiceImpl.LOGGER.info("[getContactsById][Preserve Other Service][Get Contacts By Id is]");

        HttpEntity requestGetContactsResult = new HttpEntity(httpHeaders);
        String contacts_service_url = getServiceUrl("ts-contacts-service");
        ResponseEntity<Response<Contacts>> reGetContactsResult = restTemplate.exchange(
                contacts_service_url + "/api/v1/contactservice/contacts/" + contactsId,
                HttpMethod.GET,
                requestGetContactsResult,
                new ParameterizedTypeReference<Response<Contacts>>() {
                });

        return reGetContactsResult.getBody();
    }

    private Response createOrder(Order coi, HttpHeaders httpHeaders) {
        PreserveServiceImpl.LOGGER.info("[createOrder][Preserve Service][create order]");

        HttpEntity requestEntityCreateOrderResult = new HttpEntity(coi, httpHeaders);
        String order_service_url = getServiceUrl("ts-order-service");
        ResponseEntity<Response<Order>> reCreateOrderResult = restTemplate.exchange(
                order_service_url + "/api/v1/orderservice/order",
                HttpMethod.POST,
                requestEntityCreateOrderResult,
                new ParameterizedTypeReference<Response<Order>>() {
                });

        return reCreateOrderResult.getBody();
    }

    private Response createFoodOrder(FoodOrder afi, HttpHeaders httpHeaders) {
        PreserveServiceImpl.LOGGER.info("[createFoodOrder][Preserve Service][Add Preserve food Order]");

        HttpEntity requestEntityAddFoodOrderResult = new HttpEntity(afi, httpHeaders);
        String food_service_url = getServiceUrl("ts-food-service");
        ResponseEntity<Response> reAddFoodOrderResult = restTemplate.exchange(
                food_service_url + "/api/v1/foodservice/orders",
                HttpMethod.POST,
                requestEntityAddFoodOrderResult,
                Response.class);

        return reAddFoodOrderResult.getBody();
    }

    private Response createConsign(Consign cr, HttpHeaders httpHeaders) {
        PreserveServiceImpl.LOGGER.info("[createConsign][Preserve Service][Add Condign");

        HttpEntity requestEntityResultForTravel = new HttpEntity(cr, httpHeaders);
        String consign_service_url = getServiceUrl("ts-consign-service");
        ResponseEntity<Response> reResultForTravel = restTemplate.exchange(
                consign_service_url + "/api/v1/consignservice/consigns",
                HttpMethod.POST,
                requestEntityResultForTravel,
                Response.class);
        return reResultForTravel.getBody();
    }

}


// Node: repos/cloned_ms_repos/train-ticket/ts-preserve-service/src/main/java/preserve/service/PreserveServiceImpl.java:PreserveServiceImpl.<init>
package train.controller;

import edu.fudan.common.util.Response;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.web.bind.annotation.*;
import train.entity.TrainType;
import train.service.TrainService;

import java.util.List;

import static org.springframework.http.ResponseEntity.ok;


@RestController
@RequestMapping("/api/v1/trainservice")
public class TrainController {


    @Autowired
    private TrainService trainService;

    private static final Logger LOGGER = LoggerFactory.getLogger(TrainController.class);

    @GetMapping(path = "/trains/welcome")
    public String home(@RequestHeader HttpHeaders headers) {
        return "Welcome to [ Train Service ] !";
    }

    @CrossOrigin(origins = "*")
    @PostMapping(value = "/trains")
    public HttpEntity create(@RequestBody TrainType trainType, @RequestHeader HttpHeaders headers) {
        TrainController.LOGGER.info("[create][Create train][TrainTypeId: {}]",trainType.getId());
        boolean isCreateSuccess = trainService.create(trainType, headers);
        if (isCreateSuccess) {
            return ok(new Response(1, "create success", null));
        } else {
            return ok(new Response(0, "train type already exist", trainType));
        }
    }

    @CrossOrigin(origins = "*")
    @GetMapping(value = "/trains/{id}")
    public HttpEntity retrieve(@PathVariable String id, @RequestHeader HttpHeaders headers) {
        TrainController.LOGGER.info("[retrieve][Retrieve train][TrainTypeId: {}]",id);
        TrainType trainType = trainService.retrieve(id, headers);
        if (trainType == null) {
            return ok(new Response(0, "here is no TrainType with the trainType id: " + id, null));
        } else {
            return ok(new Response(1, "success", trainType));
        }
    }

    @CrossOrigin(origins = "*")
    @GetMapping(value = "/trains/byName/{name}")
    public HttpEntity retrieveByName(@PathVariable String name, @RequestHeader HttpHeaders headers) {
        TrainController.LOGGER.info("[retrieveByName][Retrieve train][TrainTypeName: {}]", name);
        TrainType trainType = trainService.retrieveByName(name, headers);
        if (trainType == null) {
            return ok(new Response(0, "here is no TrainType with the trainType name: " + name, null));
        } else {
            return ok(new Response(1, "success", trainType));
        }
    }

    @CrossOrigin(origins = "*")
    @PostMapping(value = "/trains/byNames")
    public HttpEntity retrieveByName(@RequestBody List<String> names, @RequestHeader HttpHeaders headers) {
        TrainController.LOGGER.info("[retrieveByNames][Retrieve train][TrainTypeNames: {}]", names);
        List<TrainType> trainTypes = trainService.retrieveByNames(names, headers);
        if (trainTypes == null) {
            return ok(new Response(0, "here is no TrainTypes with the trainType names: " + names, null));
        } else {
            return ok(new Response(1, "success", trainTypes));
        }
    }

    @CrossOrigin(origins = "*")
    @PutMapping(value = "/trains")
    public HttpEntity update(@RequestBody TrainType trainType, @RequestHeader HttpHeaders headers) {
        TrainController.LOGGER.info("[update][Update train][TrainTypeId: {}]",trainType.getId());
        boolean isUpdateSuccess = trainService.update(trainType, headers);
        if (isUpdateSuccess) {
            return ok(new Response(1, "update success", isUpdateSuccess));
        } else {
            return ok(new Response(0, "there is no trainType with the trainType id", isUpdateSuccess));
        }
    }

    @CrossOrigin(origins = "*")
    @DeleteMapping(value = "/trains/{id}")
    public HttpEntity delete(@PathVariable String id, @RequestHeader HttpHeaders headers) {
        TrainController.LOGGER.info("[delete][Delete train][TrainTypeId: {}]",id);
        boolean isDeleteSuccess = trainService.delete(id, headers);
        if (isDeleteSuccess) {
            return ok(new Response(1, "delete success", isDeleteSuccess));
        } else {
            return ok(new Response(0, "there is no train according to id", null));
        }
    }

    @CrossOrigin(origins = "*")
    @GetMapping(value = "/trains")
    public HttpEntity query(@RequestHeader HttpHeaders headers) {
        TrainController.LOGGER.info("[query][Query train]");
        List<TrainType> trainTypes = trainService.query(headers);
        if (trainTypes != null && !trainTypes.isEmpty()) {
            return ok(new Response(1, "success", trainTypes));
        } else {
            return ok(new Response(0, "no content", trainTypes));
        }
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-train-service/src/main/java/train/controller/TrainController.java:TrainController.<init>
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


// Node: repos/cloned_ms_repos/train-ticket/ts-train-service/src/main/java/train/service/TrainServiceImpl.java:TrainServiceImpl.<init>
package consignprice.controller;

import consignprice.entity.ConsignPrice;
import consignprice.service.ConsignPriceService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.web.bind.annotation.*;

import static org.springframework.http.ResponseEntity.ok;

/**
 * @author fdse
 */
@RestController
@RequestMapping("/api/v1/consignpriceservice")
public class ConsignPriceController {

    @Autowired
    ConsignPriceService service;

    private static final Logger logger = LoggerFactory.getLogger(ConsignPriceController.class);

    @GetMapping(path = "/welcome")
    public String home(@RequestHeader HttpHeaders headers) {
        return "Welcome to [ ConsignPrice Service ] !";
    }

    @GetMapping(value = "/consignprice/{weight}/{isWithinRegion}")
    public HttpEntity getPriceByWeightAndRegion(@PathVariable String weight, @PathVariable String isWithinRegion,
                                                @RequestHeader HttpHeaders headers) {
        logger.info("[getPriceByWeightAndRegion][Get price by weight and region][weight: {}, region: {}]", weight, isWithinRegion);
        return ok(service.getPriceByWeightAndRegion(Double.parseDouble(weight),
                Boolean.parseBoolean(isWithinRegion), headers));
    }

    @GetMapping(value = "/consignprice/price")
    public HttpEntity getPriceInfo(@RequestHeader HttpHeaders headers) {
        logger.info("[getPriceInfo][Get price info]");
        return ok(service.queryPriceInformation(headers));
    }

    @GetMapping(value = "/consignprice/config")
    public HttpEntity getPriceConfig(@RequestHeader HttpHeaders headers) {
        logger.info("[getPriceConfig][Get price config]");
        return ok(service.getPriceConfig(headers));
    }

    @PostMapping(value = "/consignprice")
    public HttpEntity modifyPriceConfig(@RequestBody ConsignPrice priceConfig,
                                        @RequestHeader HttpHeaders headers) {
        logger.info("[modifyPriceConfig][Create and modify price][config: {}]", priceConfig);
        return ok(service.createAndModifyPrice(priceConfig, headers));
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-consign-price-service/src/main/java/consignprice/controller/ConsignPriceController.java:ConsignPriceController.<init>
// Node: parseBoolean
// Node: getPriceInfo
package consignprice.service;

import consignprice.entity.ConsignPrice;
import consignprice.repository.ConsignPriceConfigRepository;
import edu.fudan.common.util.Response;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpHeaders;
import org.springframework.stereotype.Service;

/**
 * @author fdse
 */
@Service
public class ConsignPriceServiceImpl implements ConsignPriceService {

    @Autowired
    private ConsignPriceConfigRepository repository;

    String success = "Success";

    private static final Logger LOGGER = LoggerFactory.getLogger(ConsignPriceServiceImpl.class);

    @Override
    public Response getPriceByWeightAndRegion(double weight, boolean isWithinRegion, HttpHeaders headers) {
        ConsignPrice priceConfig = repository.findByIndex(0);
        double price = 0;
        double initialPrice = priceConfig.getInitialPrice();
        if (weight <= priceConfig.getInitialWeight()) {
            price = initialPrice;
        } else {
            double extraWeight = weight - priceConfig.getInitialWeight();
            if (isWithinRegion) {
                price = initialPrice + extraWeight * priceConfig.getWithinPrice();
            }else {
                price = initialPrice + extraWeight * priceConfig.getBeyondPrice();
            }
        }
        return new Response<>(1, success, price);
    }

    @Override
    public Response queryPriceInformation(HttpHeaders headers) {
        StringBuilder sb = new StringBuilder();
        ConsignPrice price = repository.findByIndex(0);
        sb.append("The price of weight within ");
        sb.append(price.getInitialWeight());
        sb.append(" is ");
        sb.append(price.getInitialPrice());
        sb.append(". The price of extra weight within the region is ");
        sb.append(price.getWithinPrice());
        sb.append(" and beyond the region is ");
        sb.append(price.getBeyondPrice());
        sb.append("\n");
        return new Response<>(1, success, sb.toString());
    }

    @Override
    public Response createAndModifyPrice(ConsignPrice config, HttpHeaders headers) {
        ConsignPriceServiceImpl.LOGGER.info("[createAndModifyPrice][Create New Price Config]");
        //update price
        ConsignPrice originalConfig;
        if (repository.findByIndex(0) != null) {
            originalConfig = repository.findByIndex(0);
        } else {
            originalConfig = new ConsignPrice();
        }
        originalConfig.setId(config.getId());
        originalConfig.setIndex(0);
        originalConfig.setInitialPrice(config.getInitialPrice());
        originalConfig.setInitialWeight(config.getInitialWeight());
        originalConfig.setWithinPrice(config.getWithinPrice());
        originalConfig.setBeyondPrice(config.getBeyondPrice());
        repository.save(originalConfig);
        return new Response<>(1, success, originalConfig);
    }

    @Override
    public Response getPriceConfig(HttpHeaders headers) {
        return new Response<>(1, success, repository.findByIndex(0));
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-consign-price-service/src/main/java/consignprice/service/ConsignPriceServiceImpl.java:ConsignPriceServiceImpl.<init>
package inside_payment.controller;

import inside_payment.entity.*;
import inside_payment.service.InsidePaymentService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.web.bind.annotation.*;

import static org.springframework.http.ResponseEntity.ok;

/**
 * @author fdse
 */
@RestController
@RequestMapping("/api/v1/inside_pay_service")
public class InsidePaymentController {

    @Autowired
    public InsidePaymentService service;

    private static final Logger LOGGER = LoggerFactory.getLogger(InsidePaymentController.class);

    @GetMapping(path = "/welcome")
    public String home() {
        return "Welcome to [ InsidePayment Service ] !";
    }

    @PostMapping(value = "/inside_payment")
    public HttpEntity pay(@RequestBody PaymentInfo info, @RequestHeader HttpHeaders headers) {
        InsidePaymentController.LOGGER.info("[pay][Inside Payment Service.Pay][Pay for: {}]", info.getOrderId());
        return ok(service.pay(info, headers));
    }

    @PostMapping(value = "/inside_payment/account")
    public HttpEntity createAccount(@RequestBody AccountInfo info, @RequestHeader HttpHeaders headers) {
        LOGGER.info("[createAccount][Create account][accountInfo: {}]", info);
        return ok(service.createAccount(info, headers));
    }

    @GetMapping(value = "/inside_payment/{userId}/{money}")
    public HttpEntity addMoney(@PathVariable String userId, @PathVariable
            String money, @RequestHeader HttpHeaders headers) {
        LOGGER.info("[addMoney][add money][userId: {}, money: {}]", userId, money);
        return ok(service.addMoney(userId, money, headers));
    }

    @GetMapping(value = "/inside_payment/payment")
    public HttpEntity queryPayment(@RequestHeader HttpHeaders headers) {
        LOGGER.info("[queryPayment][query payment]");
        return ok(service.queryPayment(headers));
    }

    @GetMapping(value = "/inside_payment/account")
    public HttpEntity queryAccount(@RequestHeader HttpHeaders headers) {
        LOGGER.info("[queryAccount][query account]");
        return ok(service.queryAccount(headers));
    }

    @GetMapping(value = "/inside_payment/drawback/{userId}/{money}")
    public HttpEntity drawBack(@PathVariable String userId, @PathVariable String money, @RequestHeader HttpHeaders headers) {
        LOGGER.info("[drawBack][draw back payment][userId: {}, money: {}]", userId, money);
        return ok(service.drawBack(userId, money, headers));
    }

    @PostMapping(value = "/inside_payment/difference")
    public HttpEntity payDifference(@RequestBody PaymentInfo info, @RequestHeader HttpHeaders headers) {
        LOGGER.info("[payDifference][pay difference]");
        return ok(service.payDifference(info, headers));
    }

    @GetMapping(value = "/inside_payment/money")
    public HttpEntity queryAddMoney(@RequestHeader HttpHeaders headers) {
        LOGGER.info("[queryAddMoney][query add money]");
        return ok(service.queryAddMoney(headers));
    }

}


// Node: repos/cloned_ms_repos/train-ticket/ts-inside-payment-service/src/main/java/inside_payment/controller/InsidePaymentController.java:InsidePaymentController.<init>
// Node: queryPayment
// Node: queryAccount
package inside_payment.service;

import edu.fudan.common.entity.OrderStatus;
import edu.fudan.common.entity.Order;
import edu.fudan.common.util.Response;
import inside_payment.entity.*;
import inside_payment.repository.AddMoneyRepository;
import inside_payment.repository.PaymentRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.math.BigDecimal;
import java.util.*;

/**
 * @author fdse
 */
@Service
public class InsidePaymentServiceImpl implements InsidePaymentService {

    @Autowired
    public AddMoneyRepository addMoneyRepository;

    @Autowired
    public PaymentRepository paymentRepository;

    @Autowired
    public RestTemplate restTemplate;

    private static final Logger LOGGER = LoggerFactory.getLogger(InsidePaymentServiceImpl.class);

    private String getServiceUrl(String serviceName) {
        return "http://" + serviceName;
    }

    @Override
    public Response pay(PaymentInfo info, HttpHeaders headers) {

        String userId = info.getUserId();

        String requestOrderURL = "";
        String order_service_url = getServiceUrl("ts-order-service");
        String order_other_service_url = getServiceUrl("ts-order-other-service");
        if (info.getTripId().startsWith("G") || info.getTripId().startsWith("D")) {
            requestOrderURL =  order_service_url + "/api/v1/orderservice/order/" + info.getOrderId();
        } else {
            requestOrderURL = order_other_service_url + "/api/v1/orderOtherService/orderOther/" + info.getOrderId();
        }
        HttpEntity requestGetOrderResults = new HttpEntity(headers);
        ResponseEntity<Response<Order>> reGetOrderResults = restTemplate.exchange(
                requestOrderURL,
                HttpMethod.GET,
                requestGetOrderResults,
                new ParameterizedTypeReference<Response<Order>>() {
                });
        Response<Order> result = reGetOrderResults.getBody();


        if (result.getStatus() == 1) {
            Order order = result.getData();
            if (order.getStatus() != OrderStatus.NOTPAID.getCode()) {
                InsidePaymentServiceImpl.LOGGER.warn("[Inside Payment Service.pay][Order status Not allowed to Pay]");
                return new Response<>(0, "Error. Order status Not allowed to Pay.", null);
            }

            Payment payment = new Payment();
            payment.setOrderId(info.getOrderId());
            payment.setPrice(order.getPrice());
            payment.setUserId(userId);

            //判断一下账户余额够不够，不够要去站外支付
            List<Payment> payments = paymentRepository.findByUserId(userId);
            List<Money> addMonies = addMoneyRepository.findByUserId(userId);
            Iterator<Payment> paymentsIterator = payments.iterator();
            Iterator<Money> addMoniesIterator = addMonies.iterator();

            BigDecimal totalExpand = new BigDecimal("0");
            while (paymentsIterator.hasNext()) {
                Payment p = paymentsIterator.next();
                totalExpand = totalExpand.add(new BigDecimal(p.getPrice()));
            }
            totalExpand = totalExpand.add(new BigDecimal(order.getPrice()));

            BigDecimal money = new BigDecimal("0");
            while (addMoniesIterator.hasNext()) {
                Money addMoney = addMoniesIterator.next();
                money = money.add(new BigDecimal(addMoney.getMoney()));
            }

            if (totalExpand.compareTo(money) > 0) {
                //站外支付
                Payment outsidePaymentInfo = new Payment();
                outsidePaymentInfo.setOrderId(info.getOrderId());
                outsidePaymentInfo.setUserId(userId);
                outsidePaymentInfo.setPrice(order.getPrice());

                /****这里调用第三方支付***/

                HttpEntity requestEntityOutsidePaySuccess = new HttpEntity(outsidePaymentInfo, headers);
                String payment_service_url = getServiceUrl("ts-payment-service");
                ResponseEntity<Response> reOutsidePaySuccess = restTemplate.exchange(
                        payment_service_url + "/api/v1/paymentservice/payment",
                        HttpMethod.POST,
                        requestEntityOutsidePaySuccess,
                        Response.class);
                Response outsidePaySuccess = reOutsidePaySuccess.getBody();

                InsidePaymentServiceImpl.LOGGER.info("[Inside Payment Service.pay][outside Pay][Out pay result: {}]", outsidePaySuccess.toString());
                if (outsidePaySuccess.getStatus() == 1) {
                    payment.setType(PaymentType.O);
                    paymentRepository.save(payment);
                    setOrderStatus(info.getTripId(), info.getOrderId(), headers);
                    return new Response<>(1, "Payment Success " +    outsidePaySuccess.getMsg(), null);
                } else {
                    LOGGER.error("Payment failed: {}", outsidePaySuccess.getMsg());
                    return new Response<>(0, "Payment Failed:  " +  outsidePaySuccess.getMsg(), null);
                }
            } else {
                setOrderStatus(info.getTripId(), info.getOrderId(), headers);
                payment.setType(PaymentType.P);
                paymentRepository.save(payment);
            }
            LOGGER.info("[Inside Payment Service.pay][Payment success][orderId: {}]", info.getOrderId());
            return new Response<>(1, "Payment Success", null);

        } else {
            LOGGER.error("[Inside Payment Service.pay][Payment failed][Order not exists][orderId: {}]", info.getOrderId());
            return new Response<>(0, "Payment Failed, Order Not Exists", null);
        }
    }

    @Override
    public Response createAccount(AccountInfo info, HttpHeaders headers) {
        List<Money> list = addMoneyRepository.findByUserId(info.getUserId());
        if (list.isEmpty()) {
            Money addMoney = new Money();
            addMoney.setMoney(info.getMoney());
            addMoney.setUserId(info.getUserId());
            addMoney.setType(MoneyType.A);
            addMoneyRepository.save(addMoney);
            return new Response<>(1, "Create Account Success", null);
        } else {
            LOGGER.error("[createAccount][Create Account Failed][Account already Exists][userId: {}]", info.getUserId());
            return new Response<>(0, "Create Account Failed, Account already Exists", null);
        }
    }

    @Override
    public Response addMoney(String userId, String money, HttpHeaders headers) {
        if (addMoneyRepository.findByUserId(userId) != null) {
            Money addMoney = new Money();
            addMoney.setUserId(userId);
            addMoney.setMoney(money);
            addMoney.setType(MoneyType.A);
            addMoneyRepository.save(addMoney);
            return new Response<>(1, "Add Money Success", null);
        } else {
            LOGGER.error("Add Money Failed, userId: {}", userId);
            return new Response<>(0, "Add Money Failed", null);
        }
    }

    @Override
    public Response queryAccount(HttpHeaders headers) {
        List<Balance> result = new ArrayList<>();
        List<Money> list = addMoneyRepository.findAll();
        Iterator<Money> ite = list.iterator();
        HashMap<String, String> map = new HashMap<>();
        while (ite.hasNext()) {
            Money addMoney = ite.next();
            if (map.containsKey(addMoney.getUserId())) {
                BigDecimal money = new BigDecimal(map.get(addMoney.getUserId()));
                map.put(addMoney.getUserId(), money.add(new BigDecimal(addMoney.getMoney())).toString());
            } else {
                map.put(addMoney.getUserId(), addMoney.getMoney());
            }
        }

        Iterator ite1 = map.entrySet().iterator();
        while (ite1.hasNext()) {
            Map.Entry entry = (Map.Entry) ite1.next();
            String userId = (String) entry.getKey();
            String money = (String) entry.getValue();

            List<Payment> payments = paymentRepository.findByUserId(userId);
            Iterator<Payment> iterator = payments.iterator();
            String totalExpand = "0";
            while (iterator.hasNext()) {
                Payment p = iterator.next();
                BigDecimal expand = new BigDecimal(totalExpand);
                totalExpand = expand.add(new BigDecimal(p.getPrice())).toString();
            }
            String balanceMoney = new BigDecimal(money).subtract(new BigDecimal(totalExpand)).toString();
            Balance balance = new Balance();
            balance.setUserId(userId);
            balance.setBalance(balanceMoney);
            result.add(balance);
        }

        return new Response<>(1, "Success", result);
    }

    public String queryAccount(String userId, HttpHeaders headers) {
        List<Payment> payments = paymentRepository.findByUserId(userId);
        List<Money> addMonies = addMoneyRepository.findByUserId(userId);
        Iterator<Payment> paymentsIterator = payments.iterator();
        Iterator<Money> addMoniesIterator = addMonies.iterator();

        BigDecimal totalExpand = new BigDecimal("0");
        while (paymentsIterator.hasNext()) {
            Payment p = paymentsIterator.next();
            totalExpand.add(new BigDecimal(p.getPrice()));
        }

        BigDecimal money = new BigDecimal("0");
        while (addMoniesIterator.hasNext()) {
            Money addMoney = addMoniesIterator.next();
            money.add(new BigDecimal(addMoney.getMoney()));
        }

        return money.subtract(totalExpand).toString();
    }

    @Override
    public Response queryPayment(HttpHeaders headers) {
        List<Payment> payments = paymentRepository.findAll();
        if (payments != null && !payments.isEmpty()) {
            return new Response<>(1, "Query Payment Success", payments);
        }else {
            LOGGER.error("[queryPayment][Query payment failed][payment is null]");
            return new Response<>(0, "Query Payment Failed", null);
        }
    }

    @Override
    public Response drawBack(String userId, String money, HttpHeaders headers) {
        if (addMoneyRepository.findByUserId(userId) != null) {
            Money addMoney = new Money();
            addMoney.setUserId(userId);
            addMoney.setMoney(money);
            addMoney.setType(MoneyType.D);
            addMoneyRepository.save(addMoney);
            return new Response<>(1, "Draw Back Money Success", null);
        } else {
            LOGGER.error("[drawBack][Draw Back Money Failed][addMoneyRepository.findByUserId null][userId: {}]", userId);
            return new Response<>(0, "Draw Back Money Failed", null);
        }
    }

    @Override
    public Response payDifference(PaymentInfo info, HttpHeaders headers) {

        String userId = info.getUserId();

        Payment payment = new Payment();
        payment.setOrderId(info.getOrderId());
        payment.setPrice(info.getPrice());
        payment.setUserId(info.getUserId());


        List<Payment> payments = paymentRepository.findByUserId(userId);
        List<Money> addMonies = addMoneyRepository.findByUserId(userId);
        Iterator<Payment> paymentsIterator = payments.iterator();
        Iterator<Money> addMoniesIterator = addMonies.iterator();

        BigDecimal totalExpand = new BigDecimal("0");
        while (paymentsIterator.hasNext()) {
            Payment p = paymentsIterator.next();
            totalExpand.add(new BigDecimal(p.getPrice()));
        }
        totalExpand.add(new BigDecimal(info.getPrice()));

        BigDecimal money = new BigDecimal("0");
        while (addMoniesIterator.hasNext()) {
            Money addMoney = addMoniesIterator.next();
            money.add(new BigDecimal(addMoney.getMoney()));
        }

        if (totalExpand.compareTo(money) > 0) {
            //站外支付
            Payment outsidePaymentInfo = new Payment();
            outsidePaymentInfo.setOrderId(info.getOrderId());
            outsidePaymentInfo.setUserId(userId);
            outsidePaymentInfo.setPrice(info.getPrice());

            HttpEntity requestEntityOutsidePaySuccess = new HttpEntity(outsidePaymentInfo, headers);
            String payment_service_url = getServiceUrl("ts-payment-service");
            ResponseEntity<Response> reOutsidePaySuccess = restTemplate.exchange(
                    payment_service_url + "/api/v1/paymentservice/payment",
                    HttpMethod.POST,
                    requestEntityOutsidePaySuccess,
                    Response.class);
            Response outsidePaySuccess = reOutsidePaySuccess.getBody();

            if (outsidePaySuccess.getStatus() == 1) {
                payment.setType(PaymentType.E);
                paymentRepository.save(payment);
                return new Response<>(1, "Pay Difference Success", null);
            } else {
                LOGGER.error("[payDifference][Pay Difference Failed][outsidePaySuccess status not 1][orderId: {}]", info.getOrderId());
                return new Response<>(0, "Pay Difference Failed", null);
            }
        } else {
            payment.setType(PaymentType.E);
            paymentRepository.save(payment);
        }
        return new Response<>(1, "Pay Difference Success", null);
    }

    @Override
    public Response queryAddMoney(HttpHeaders headers) {
        List<Money> monies = addMoneyRepository.findAll();
        if (monies != null && !monies.isEmpty()) {
            return new Response<>(1, "Query Money Success", null);
        } else {
            LOGGER.error("[queryAddMoney][Query money failed][addMoneyRepository.findAll null]");
            return new Response<>(0, "Query money failed", null);
        }
    }

    private Response setOrderStatus(String tripId, String orderId, HttpHeaders headers) {

        //order paid and not collected
        int orderStatus = 1;
        Response result;
        if (tripId.startsWith("G") || tripId.startsWith("D")) {

            HttpEntity requestEntityModifyOrderStatusResult = new HttpEntity(headers);
            String order_service_url = getServiceUrl("ts-order-service");
            ResponseEntity<Response> reModifyOrderStatusResult = restTemplate.exchange(
                    order_service_url + "/api/v1/orderservice/order/status/" + orderId + "/" + orderStatus,
                    HttpMethod.GET,
                    requestEntityModifyOrderStatusResult,
                    Response.class);
            result = reModifyOrderStatusResult.getBody();

        } else {
            HttpEntity requestEntityModifyOrderStatusResult = new HttpEntity(headers);
            String order_other_service_url = getServiceUrl("ts-order-other-service");
            ResponseEntity<Response> reModifyOrderStatusResult = restTemplate.exchange(
                    order_other_service_url + "/api/v1/orderOtherService/orderOther/status/" + orderId + "/" + orderStatus,
                    HttpMethod.GET,
                    requestEntityModifyOrderStatusResult,
                    Response.class);
            result = reModifyOrderStatusResult.getBody();

        }
        return result;
    }

    @Override
    public void initPayment(Payment payment, HttpHeaders headers) {
        Optional<Payment> paymentTemp = paymentRepository.findById(payment.getId());
        if (paymentTemp == null) {
            paymentRepository.save(payment);
        } else {
            InsidePaymentServiceImpl.LOGGER.error("[initPayment][paymentTemp Already Exists][paymentId: {}, orderId: {}]", payment.getId(), payment.getOrderId());
        }
    }

}


// Node: repos/cloned_ms_repos/train-ticket/ts-inside-payment-service/src/main/java/inside_payment/service/InsidePaymentServiceImpl.java:InsidePaymentServiceImpl.<init>
package foodsearch.mq;


import foodsearch.config.Queues;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.amqp.core.AmqpTemplate;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;


@Component
public class RabbitSend {

    @Autowired
    private AmqpTemplate rabbitTemplate;
    private static final Logger logger = LoggerFactory.getLogger(RabbitSend.class);

    public void send(String val) {
        logger.info("Send info to mq:" + val);
        this.rabbitTemplate.convertAndSend(Queues.queueName, val);
    }

}


// Node: repos/cloned_ms_repos/train-ticket/ts-food-service/src/main/java/foodsearch/mq/RabbitSend.java:RabbitSend.<init>
package foodsearch.controller;

import edu.fudan.common.util.JsonUtils;
import foodsearch.entity.*;
import foodsearch.mq.RabbitSend;
import foodsearch.service.FoodService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.UUID;

import static org.springframework.http.ResponseEntity.ok;

@RestController
@RequestMapping("/api/v1/foodservice")
public class FoodController {

    @Autowired
    FoodService foodService;

    @Autowired
    RabbitSend sender;

    private static final Logger LOGGER = LoggerFactory.getLogger(FoodController.class);

    @GetMapping(path = "/welcome")
    public String home() {
        return "Welcome to [ Food Service ] !";
    }

    @GetMapping(path = "/test_send_delivery")
    public boolean test_send_delivery() {
        Delivery delivery = new Delivery();
        delivery.setFoodName("HotPot");
        delivery.setOrderId(UUID.randomUUID());
        delivery.setStationName("Shang Hai");
        delivery.setStoreName("MiaoTing Instant-Boiled Mutton");

        String deliveryJson = JsonUtils.object2Json(delivery);
        sender.send(deliveryJson);
        return true;
    }

    @GetMapping(path = "/orders")
    public HttpEntity findAllFoodOrder(@RequestHeader HttpHeaders headers) {
        FoodController.LOGGER.info("[Food Service]Try to Find all FoodOrder!");
        return ok(foodService.findAllFoodOrder(headers));
    }

    @PostMapping(path = "/orders")
    public HttpEntity createFoodOrder(@RequestBody FoodOrder addFoodOrder, @RequestHeader HttpHeaders headers) {
        FoodController.LOGGER.info("[createFoodOrder][Try to Create a FoodOrder!]");
        return ok(foodService.createFoodOrder(addFoodOrder, headers));
    }

    @PostMapping(path = "/createOrderBatch")
    public HttpEntity createFoodBatches(@RequestBody List<FoodOrder> foodOrderList, @RequestHeader HttpHeaders headers) {
        FoodController.LOGGER.info("[createFoodBatches][Try to Create Food Batches!]");
        return ok(foodService.createFoodOrdersInBatch(foodOrderList, headers));
    }


    @PutMapping(path = "/orders")
    public HttpEntity updateFoodOrder(@RequestBody FoodOrder updateFoodOrder, @RequestHeader HttpHeaders headers) {
        FoodController.LOGGER.info("[updateFoodOrder][Try to Update a FoodOrder!]");
        return ok(foodService.updateFoodOrder(updateFoodOrder, headers));
    }

    @ResponseStatus(HttpStatus.ACCEPTED)
    @DeleteMapping(path = "/orders/{orderId}")
    public HttpEntity deleteFoodOrder(@PathVariable String orderId, @RequestHeader HttpHeaders headers) {
        FoodController.LOGGER.info("[deleteFoodOrder][Try to Cancel a FoodOrder!]");
        return ok(foodService.deleteFoodOrder(orderId, headers));
    }

    @GetMapping(path = "/orders/{orderId}")
    public HttpEntity findFoodOrderByOrderId(@PathVariable String orderId, @RequestHeader HttpHeaders headers) {
        FoodController.LOGGER.info("[findFoodOrderByOrderId][Try to Find FoodOrder By orderId!][orderId: {}]", orderId);
        return ok(foodService.findByOrderId(orderId, headers));
    }

    // This relies on a lot of other services, not completely modified
    @GetMapping(path = "/foods/{date}/{startStation}/{endStation}/{tripId}")
    public HttpEntity getAllFood(@PathVariable String date, @PathVariable String startStation,
                                 @PathVariable String endStation, @PathVariable String tripId,
                                 @RequestHeader HttpHeaders headers) {
        FoodController.LOGGER.info("[getAllFood][Get Food Request!]");
        return ok(foodService.getAllFood(date, startStation, endStation, tripId, headers));
    }

}


// Node: repos/cloned_ms_repos/train-ticket/ts-food-service/src/main/java/foodsearch/controller/FoodController.java:FoodController.<init>
// Node: findAllFoodOrder
// Node: createFoodBatches
// Node: createFoodOrdersInBatch
// Node: updateFoodOrder
// Node: ResponseStatus
// Node: deleteFoodOrder
// Node: findFoodOrderByOrderId
// Node: getAllFood
package foodsearch.service;

import edu.fudan.common.util.Response;
import foodsearch.entity.*;
import org.springframework.http.HttpHeaders;

import java.util.List;


public interface FoodService {

    Response createFoodOrder(FoodOrder afoi, HttpHeaders headers);

    Response createFoodOrdersInBatch(List<FoodOrder> orders, HttpHeaders headers);
    
    Response deleteFoodOrder(String orderId, HttpHeaders headers);

    Response findByOrderId(String orderId, HttpHeaders headers);

    Response updateFoodOrder(FoodOrder updateFoodOrder, HttpHeaders headers);

    Response findAllFoodOrder(HttpHeaders headers);

    Response getAllFood(String date, String startStation, String endStation, String tripId, HttpHeaders headers);

}


// Node: repos/cloned_ms_repos/train-ticket/ts-food-service/src/main/java/foodsearch/service/FoodService.java:FoodService.<init>
package foodsearch.service;

import edu.fudan.common.entity.Food;
import edu.fudan.common.entity.StationFoodStore;
import edu.fudan.common.entity.TrainFood;
import edu.fudan.common.util.JsonUtils;
import edu.fudan.common.util.Response;
import edu.fudan.common.entity.Route;
import foodsearch.entity.*;
import foodsearch.mq.RabbitSend;
import foodsearch.repository.FoodOrderRepository;
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
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.client.RestTemplate;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.stream.Collectors;

@Service
public class FoodServiceImpl implements FoodService {

    @Autowired
    private RestTemplate restTemplate;

    @Autowired
    private FoodOrderRepository foodOrderRepository;

    @Autowired
    private RabbitSend sender;

    @Autowired
    private DiscoveryClient discoveryClient;

    private static final Logger LOGGER = LoggerFactory.getLogger(FoodServiceImpl.class);

    private String getServiceUrl(String serviceName) {
        return "http://" + serviceName;
    }

    String success = "Success.";
    String orderIdNotExist = "Order Id Is Non-Existent.";

    @Override
    public Response createFoodOrdersInBatch(List<FoodOrder> orders, HttpHeaders headers) {
        boolean error = false;
        String errorOrderId = "";

        // Check if foodOrder exists
        for (FoodOrder addFoodOrder : orders) {
            FoodOrder fo = foodOrderRepository.findByOrderId(addFoodOrder.getOrderId());
            if (fo != null) {
                LOGGER.error("[createFoodOrdersInBatch][AddFoodOrder][Order Id Has Existed][OrderId: {}]", addFoodOrder.getOrderId());
                error = true;
                errorOrderId = addFoodOrder.getOrderId().toString();
                break;
            }
        }
        if (error) {
            return new Response<>(0, "Order Id " + errorOrderId + "Existed", null);
        }

        List<String> deliveryJsons = new ArrayList<>();
        for (FoodOrder addFoodOrder : orders) {
            FoodOrder fo = new FoodOrder();
            fo.setId(UUID.randomUUID().toString());
            fo.setOrderId(addFoodOrder.getOrderId());
            fo.setFoodType(addFoodOrder.getFoodType());
            if (addFoodOrder.getFoodType() == 2) {
                fo.setStationName(addFoodOrder.getStationName());
                fo.setStoreName(addFoodOrder.getStoreName());
            }
            fo.setFoodName(addFoodOrder.getFoodName());
            fo.setPrice(addFoodOrder.getPrice());
            foodOrderRepository.save(fo);
            LOGGER.info("[createFoodOrdersInBatch][AddFoodOrderBatch][Success Save One Order][FoodOrderId: {}]", fo.getOrderId());

            Delivery delivery = new Delivery();
            delivery.setFoodName(addFoodOrder.getFoodName());
            delivery.setOrderId(UUID.fromString(addFoodOrder.getOrderId()));
            delivery.setStationName(addFoodOrder.getStationName());
            delivery.setStoreName(addFoodOrder.getStoreName());

            String deliveryJson = JsonUtils.object2Json(delivery);
            deliveryJsons.add(deliveryJson);
        }

        // 批量发送消息
        for(String deliveryJson: deliveryJsons) {
            LOGGER.info("[createFoodOrdersInBatch][AddFoodOrder][delivery info send to mq][delivery info: {}]", deliveryJson);
            try {
                sender.send(deliveryJson);
            } catch (Exception e) {
                LOGGER.error("[createFoodOrdersInBatch][AddFoodOrder][send delivery info to mq error][exception: {}]", e.toString());
            }
        }

        return new Response<>(1, success, null);
    }

    @Override
    public Response createFoodOrder(FoodOrder addFoodOrder, HttpHeaders headers) {

        FoodOrder fo = foodOrderRepository.findByOrderId(addFoodOrder.getOrderId());
        if (fo != null) {
            FoodServiceImpl.LOGGER.error("[createFoodOrder][AddFoodOrder][Order Id Has Existed][OrderId: {}]", addFoodOrder.getOrderId());
            return new Response<>(0, "Order Id Has Existed.", null);
        } else {
            fo = new FoodOrder();
            fo.setId(UUID.randomUUID().toString());
            fo.setOrderId(addFoodOrder.getOrderId());
            fo.setFoodType(addFoodOrder.getFoodType());
            if (addFoodOrder.getFoodType() == 2) {
                fo.setStationName(addFoodOrder.getStationName());
                fo.setStoreName(addFoodOrder.getStoreName());
            }
            fo.setFoodName(addFoodOrder.getFoodName());
            fo.setPrice(addFoodOrder.getPrice());
            foodOrderRepository.save(fo);
            FoodServiceImpl.LOGGER.info("[createFoodOrder][AddFoodOrder Success]");

            Delivery delivery = new Delivery();
            delivery.setFoodName(addFoodOrder.getFoodName());
            delivery.setOrderId(UUID.fromString(addFoodOrder.getOrderId()));
            delivery.setStationName(addFoodOrder.getStationName());
            delivery.setStoreName(addFoodOrder.getStoreName());

            String deliveryJson = JsonUtils.object2Json(delivery);
            LOGGER.info("[createFoodOrder][AddFoodOrder, delivery info send to mq][delivery info: {}]", deliveryJson);
            try {
                sender.send(deliveryJson);
            } catch (Exception e) {
                LOGGER.error("[createFoodOrder][AddFoodOrder][send delivery info to mq error][exception: {}]", e.toString());
            }

            return new Response<>(1, success, fo);
        }
    }

    @Transactional
    @Override
    public Response deleteFoodOrder(String orderId, HttpHeaders headers) {
        FoodOrder foodOrder = foodOrderRepository.findByOrderId(UUID.fromString(orderId).toString());
        if (foodOrder == null) {
            FoodServiceImpl.LOGGER.error("[deleteFoodOrder][Cancel FoodOrder][Order Id Is Non-Existent][orderId: {}]", orderId);
            return new Response<>(0, orderIdNotExist, null);
        } else {
//            foodOrderRepository.deleteFoodOrderByOrderId(UUID.fromString(orderId));
            foodOrderRepository.deleteFoodOrderByOrderId(orderId);
            FoodServiceImpl.LOGGER.info("[deleteFoodOrder][Cancel FoodOrder Success]");
            return new Response<>(1, success, null);
        }
    }

    @Override
    public Response findAllFoodOrder(HttpHeaders headers) {
        List<FoodOrder> foodOrders = foodOrderRepository.findAll();
        if (foodOrders != null && !foodOrders.isEmpty()) {
            return new Response<>(1, success, foodOrders);
        } else {
            FoodServiceImpl.LOGGER.error("[findAllFoodOrder][Find all food order error: {}]", "No Content");
            return new Response<>(0, "No Content", null);
        }
    }


    @Override
    public Response updateFoodOrder(FoodOrder updateFoodOrder, HttpHeaders headers) {
        FoodOrder fo = foodOrderRepository.findById(updateFoodOrder.getId()).orElse(null);
        if (fo == null) {
            FoodServiceImpl.LOGGER.info("[updateFoodOrder][Update FoodOrder][Order Id Is Non-Existent][orderId: {}]", updateFoodOrder.getOrderId());
            return new Response<>(0, orderIdNotExist, null);
        } else {
            fo.setFoodType(updateFoodOrder.getFoodType());
            if (updateFoodOrder.getFoodType() == 1) {
                fo.setStationName(updateFoodOrder.getStationName());
                fo.setStoreName(updateFoodOrder.getStoreName());
            }
            fo.setFoodName(updateFoodOrder.getFoodName());
            fo.setPrice(updateFoodOrder.getPrice());
            foodOrderRepository.save(fo);
            FoodServiceImpl.LOGGER.info("[updateFoodOrder][Update FoodOrder Success]");
            return new Response<>(1, "Success", fo);
        }
    }

    @Override
    public Response findByOrderId(String orderId, HttpHeaders headers) {
        FoodOrder fo = foodOrderRepository.findByOrderId(UUID.fromString(orderId).toString());
        if (fo != null) {
            FoodServiceImpl.LOGGER.info("[findByOrderId][Find Order by id Success][orderId: {}]", orderId);
            return new Response<>(1, success, fo);
        } else {
            FoodServiceImpl.LOGGER.warn("[findByOrderId][Find Order by id][Order Id Is Non-Existent][orderId: {}]", orderId);
            return new Response<>(0, orderIdNotExist, null);
        }
    }


    @Override
    public Response getAllFood(String date, String startStation, String endStation, String tripId, HttpHeaders headers) {
        FoodServiceImpl.LOGGER.info("[getAllFood][get All Food with info][data:{} start:{} end:{} tripid:{}]", date, startStation, endStation, tripId);
        AllTripFood allTripFood = new AllTripFood();

        if (null == tripId || tripId.length() <= 2) {
            FoodServiceImpl.LOGGER.error("[getAllFood][Get the Get Food Request Failed][Trip id is not suitable][date: {}, tripId: {}]", date, tripId);
            return new Response<>(0, "Trip id is not suitable", null);
        }

        // need return this tow element
        List<Food> trainFoodList = null;
        Map<String, List<StationFoodStore>> foodStoreListMap = new HashMap<>();

        /**--------------------------------------------------------------------------------------*/
        HttpEntity requestEntityGetTrainFoodListResult = new HttpEntity(null);
        String train_food_service_url = getServiceUrl("ts-train-food-service");
        ResponseEntity<Response<List<Food>>> reGetTrainFoodListResult = restTemplate.exchange(
                train_food_service_url + "/api/v1/trainfoodservice/trainfoods/" + tripId,
                HttpMethod.GET,
                requestEntityGetTrainFoodListResult,
                new ParameterizedTypeReference<Response<List<Food>>>() {
                });



        List<Food> trainFoodListResult = reGetTrainFoodListResult.getBody().getData();

        if (trainFoodListResult != null) {
            trainFoodList = trainFoodListResult;
            FoodServiceImpl.LOGGER.info("[getAllFood][Get Train Food List!]");
        } else {
            FoodServiceImpl.LOGGER.error("[getAllFood][reGetTrainFoodListResult][Get the Get Food Request Failed!][date: {}, tripId: {}]", date, tripId);
            return new Response<>(0, "Get the Get Food Request Failed!", null);
        }
        //车次途经的车站
        /**--------------------------------------------------------------------------------------*/
        HttpEntity requestEntityGetRouteResult = new HttpEntity(null, null);
        String travel_service_url = getServiceUrl("ts-travel-service");
        ResponseEntity<Response<Route>> reGetRouteResult = restTemplate.exchange(
                travel_service_url + "/api/v1/travelservice/routes/" + tripId,
                HttpMethod.GET,
                requestEntityGetRouteResult,
                new ParameterizedTypeReference<Response<Route>>() {
                });
        Response<Route> stationResult = reGetRouteResult.getBody();

        if (stationResult.getStatus() == 1) {
            Route route = stationResult.getData();
            List<String> stations = route.getStations();
            //去除不经过的站，如果起点终点有的话
            if (null != startStation && !"".equals(startStation)) {
                /**--------------------------------------------------------------------------------------*/
                for (int i = 0; i < stations.size(); i++) {
                    if (stations.get(i).equals(startStation)) {
                        break;
                    } else {
                        stations.remove(i);
                    }
                }
            }
            if (null != endStation && !"".equals(endStation)) {
                /**--------------------------------------------------------------------------------------*/
                for (int i = stations.size() - 1; i >= 0; i--) {
                    if (stations.get(i).equals(endStation)) {
                        break;
                    } else {
                        stations.remove(i);
                    }
                }
            }

            HttpEntity requestEntityFoodStoresListResult = new HttpEntity(stations, null);
            String station_food_service_url = getServiceUrl("ts-station-food-service");
            ResponseEntity<Response<List<StationFoodStore>>> reFoodStoresListResult = restTemplate.exchange(
                     station_food_service_url + "/api/v1/stationfoodservice/stationfoodstores",
                    HttpMethod.POST,
                    requestEntityFoodStoresListResult,
                    new ParameterizedTypeReference<Response<List<StationFoodStore>>>() {
                    });
            List<StationFoodStore> stationFoodStoresListResult = reFoodStoresListResult.getBody().getData();
            if (stationFoodStoresListResult != null && !stationFoodStoresListResult.isEmpty()) {
                for (String station : stations) {
                    List<StationFoodStore> res = stationFoodStoresListResult.stream()
                            .filter(stationFoodStore -> (stationFoodStore.getStationName().equals(station)))
                            .collect(Collectors.toList());
                    foodStoreListMap.put(station, res);
                }
            } else {
                FoodServiceImpl.LOGGER.error("[getAllFood][Get the Get Food Request Failed!][foodStoresListResult is null][date: {}, tripId: {}]", date, tripId);
                return new Response<>(0, "Get All Food Failed", allTripFood);
            }
        } else {
            FoodServiceImpl.LOGGER.error("[getAllFood][Get the Get Food Request Failed!][station status error][date: {}, tripId: {}]", date, tripId);
            return new Response<>(0, "Get All Food Failed", allTripFood);
        }
        allTripFood.setTrainFoodList(trainFoodList);
        allTripFood.setFoodStoreListMap(foodStoreListMap);
        return new Response<>(1, "Get All Food Success", allTripFood);
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-food-service/src/main/java/foodsearch/service/FoodServiceImpl.java:FoodServiceImpl.<init>
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

// Node: repos/cloned_ms_repos/train-ticket/ts-route-service/src/main/java/route/controller/RouteController.java:RouteController.<init>
// Node: queryByIds
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

// Node: repos/cloned_ms_repos/train-ticket/ts-route-service/src/main/java/route/service/RouteServiceImpl.java:RouteServiceImpl.<init>
package consign.controller;

import consign.entity.Consign;
import consign.service.ConsignService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.web.bind.annotation.*;

import java.util.UUID;

import static org.springframework.http.ResponseEntity.ok;

/**
 * @author fdse
 */
@RestController
@RequestMapping("/api/v1/consignservice")
public class ConsignController {

    @Autowired
    ConsignService service;

    private static final Logger logger = LoggerFactory.getLogger(ConsignController.class);

    @GetMapping(path = "/welcome")
    public String home(@RequestHeader HttpHeaders headers) {
        return "Welcome to [ Consign Service ] !";
    }

    @PostMapping(value = "/consigns")
    public HttpEntity insertConsign(@RequestBody Consign request,
                                    @RequestHeader HttpHeaders headers) {
        logger.info("[insertConsign][Insert consign record][id:{}]", request.getId());
        return ok(service.insertConsignRecord(request, headers));
    }

    @PutMapping(value = "/consigns")
    public HttpEntity updateConsign(@RequestBody Consign request, @RequestHeader HttpHeaders headers) {
        logger.info("[updateConsign][Update consign record][id: {}]", request.getId());
        return ok(service.updateConsignRecord(request, headers));
    }

    @GetMapping(value = "/consigns/account/{id}")
    public HttpEntity findByAccountId(@PathVariable String id, @RequestHeader HttpHeaders headers) {
        logger.info("[findByAccountId][Find consign by account id][id: {}]", id);
        UUID newid = UUID.fromString(id);
        return ok(service.queryByAccountId(newid, headers));
    }

    @GetMapping(value = "/consigns/order/{id}")
    public HttpEntity findByOrderId(@PathVariable String id, @RequestHeader HttpHeaders headers) {
        logger.info("[findByOrderId][Find consign by order id][id: {}]", id);
        UUID newid = UUID.fromString(id);
        return ok(service.queryByOrderId(newid, headers));
    }

    @GetMapping(value = "/consigns/{consignee}")
    public HttpEntity findByConsignee(@PathVariable String consignee, @RequestHeader HttpHeaders headers) {
        logger.info("[findByConsignee][Find consign by consignee][consignee: {}]", consignee);
        return ok(service.queryByConsignee(consignee, headers));
    }

}


// Node: repos/cloned_ms_repos/train-ticket/ts-consign-service/src/main/java/consign/controller/ConsignController.java:ConsignController.<init>
// Node: insertConsign
// Node: updateConsign
package consign.service;

import consign.entity.ConsignRecord;
import consign.entity.Consign;
import consign.repository.ConsignRepository;
import edu.fudan.common.util.Response;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.cloud.client.ServiceInstance;
import org.springframework.cloud.client.discovery.DiscoveryClient;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

/**
 * @author fdse
 */
@Service
public class ConsignServiceImpl implements ConsignService {
    @Autowired
    ConsignRepository repository;

    @Autowired
    RestTemplate restTemplate;

    @Autowired
    private DiscoveryClient discoveryClient;

    private static final Logger LOGGER = LoggerFactory.getLogger(ConsignServiceImpl.class);

    private String getServiceUrl(String serviceName) {
        return "http://" + serviceName;
    }


    @Override
    public Response insertConsignRecord(Consign consignRequest, HttpHeaders headers) {
        ConsignServiceImpl.LOGGER.info("[insertConsignRecord][Insert Start][consignRequest.getOrderId: {}]", consignRequest.getOrderId());

        ConsignRecord consignRecord = new ConsignRecord();
        //Set the record attribute
        consignRecord.setId(UUID.randomUUID().toString());
        consignRecord.setOrderId(consignRequest.getOrderId().toString());
        consignRecord.setAccountId(consignRequest.getAccountId().toString());
        ConsignServiceImpl.LOGGER.info("[insertConsignRecord][Insert Info][handle date: {}, target date: {}]", consignRequest.getHandleDate(), consignRequest.getTargetDate());
        consignRecord.setHandleDate(consignRequest.getHandleDate());
        consignRecord.setTargetDate(consignRequest.getTargetDate());
        consignRecord.setFrom(consignRequest.getFrom());
        consignRecord.setTo(consignRequest.getTo());
        consignRecord.setConsignee(consignRequest.getConsignee());
        consignRecord.setPhone(consignRequest.getPhone());
        consignRecord.setWeight(consignRequest.getWeight());

        //get the price
        HttpEntity requestEntity = new HttpEntity(null, headers);
        String consign_price_service_url = getServiceUrl("ts-consign-price-service");
        ResponseEntity<Response<Double>> re = restTemplate.exchange(
                consign_price_service_url + "/api/v1/consignpriceservice/consignprice/" + consignRequest.getWeight() + "/" + consignRequest.isWithin(),
                HttpMethod.GET,
                requestEntity,
                new ParameterizedTypeReference<Response<Double>>() {
                });
        consignRecord.setPrice(re.getBody().getData());

        LOGGER.info("[insertConsignRecord][SAVE consign info][consignRecord : {}]", consignRecord.toString());
        ConsignRecord result = repository.save(consignRecord);
        LOGGER.info("[insertConsignRecord][SAVE consign result][result: {}]", result.toString());
        return new Response<>(1, "You have consigned successfully! The price is " + result.getPrice(), result);
    }

    @Override
    public Response updateConsignRecord(Consign consignRequest, HttpHeaders headers) {
        ConsignServiceImpl.LOGGER.info("[updateConsignRecord][Update Start]");

        if (!repository.findById(consignRequest.getId()).isPresent()) {
            return insertConsignRecord(consignRequest, headers);
        }
        ConsignRecord originalRecord = repository.findById(consignRequest.getId()).get();
        originalRecord.setAccountId(consignRequest.getAccountId().toString());
        originalRecord.setHandleDate(consignRequest.getHandleDate());
        originalRecord.setTargetDate(consignRequest.getTargetDate());
        originalRecord.setFrom(consignRequest.getFrom());
        originalRecord.setTo(consignRequest.getTo());
        originalRecord.setConsignee(consignRequest.getConsignee());
        originalRecord.setPhone(consignRequest.getPhone());
        //Recalculate price
        if (originalRecord.getWeight() != consignRequest.getWeight()) {
            HttpEntity requestEntity = new HttpEntity<>(null, headers);
            String consign_price_service_url = getServiceUrl("ts-consign-price-service");
            ResponseEntity<Response<Double>> re = restTemplate.exchange(
                    consign_price_service_url + "/api/v1/consignpriceservice/consignprice/" + consignRequest.getWeight() + "/" + consignRequest.isWithin(),
                    HttpMethod.GET,
                    requestEntity,
                    new ParameterizedTypeReference<Response<Double>>() {
                    });

            originalRecord.setPrice(re.getBody().getData());
        } else {
            originalRecord.setPrice(originalRecord.getPrice());
        }
        originalRecord.setConsignee(consignRequest.getConsignee());
        originalRecord.setPhone(consignRequest.getPhone());
        originalRecord.setWeight(consignRequest.getWeight());
        repository.save(originalRecord);
        return new Response<>(1, "Update consign success", originalRecord);
    }

    @Override
    public Response queryByAccountId(UUID accountId, HttpHeaders headers) {
        List<ConsignRecord> consignRecords = repository.findByAccountId(accountId.toString());
        if (consignRecords != null && !consignRecords.isEmpty()) {
            return new Response<>(1, "Find consign by account id success", consignRecords);
        }else {
            LOGGER.warn("[queryByAccountId][No Content according to accountId][accountId: {}]", accountId);
            return new Response<>(0, "No Content according to accountId", null);
        }
    }

    @Override
    public Response queryByOrderId(UUID orderId, HttpHeaders headers) {
        ConsignRecord consignRecords = repository.findByOrderId(orderId.toString());
        if (consignRecords != null ) {
            return new Response<>(1, "Find consign by order id success", consignRecords);
        }else {
            LOGGER.warn("[queryByOrderId][No Content according to orderId][orderId: {}]", orderId);
            return new Response<>(0, "No Content according to order id", null);
        }
    }

    @Override
    public Response queryByConsignee(String consignee, HttpHeaders headers) {
        List<ConsignRecord> consignRecords = repository.findByConsignee(consignee);
        if (consignRecords != null && !consignRecords.isEmpty()) {
            return new Response<>(1, "Find consign by consignee success", consignRecords);
        }else {
            LOGGER.warn("[queryByConsignee][No Content according to consignee][consignee: {}]", consignee);
            return new Response<>(0, "No Content according to consignee", null);
        }
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-consign-service/src/main/java/consign/service/ConsignServiceImpl.java:ConsignServiceImpl.<init>
package verifycode.controller;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpHeaders;
import org.springframework.web.bind.annotation.*;
import verifycode.service.VerifyCodeService;

import javax.imageio.ImageIO;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.awt.image.BufferedImage;
import java.io.IOException;
import java.io.OutputStream;
import java.util.Map;

/**
 * @author fdse
 */
@RestController
@RequestMapping("/api/v1/verifycode")
public class VerifyCodeController {
    private static final Logger LOGGER = LoggerFactory.getLogger(VerifyCodeController.class);

    @Autowired
    private VerifyCodeService verifyCodeService;

    @GetMapping("/generate")
    public void imageCode(@RequestHeader HttpHeaders headers,
                          HttpServletRequest request,
                          HttpServletResponse response) throws IOException {
        VerifyCodeController.LOGGER.info("[imageCode][Image code]");
        OutputStream os = response.getOutputStream();
        Map<String, Object> map = verifyCodeService.getImageCode(60, 20, os, request, response, headers);
        String simpleCaptcha = "simpleCaptcha";
        request.getSession().setAttribute(simpleCaptcha, map.get("strEnsure").toString().toLowerCase());
        request.getSession().setAttribute("codeTime", System.currentTimeMillis());
        try {
            ImageIO.write((BufferedImage) map.get("image"), "JPEG", os);
        } catch (IOException e) {
            //error
            String error = "Can't generate verification code";
            os.write(error.getBytes());
        }
    }

    @GetMapping(value = "/verify/{verifyCode}")
    public boolean verifyCode(@PathVariable String verifyCode, HttpServletRequest request,
                              HttpServletResponse response, @RequestHeader HttpHeaders headers) {
        LOGGER.info("[verifyCode][receivedCode: {}]", verifyCode);

        boolean result = verifyCodeService.verifyCode(request, response, verifyCode, headers);
        LOGGER.info("[verifyCode][verify result: {}]", result);
        return true;
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-verification-code-service/src/main/java/verifycode/controller/VerifyCodeController.java:VerifyCodeController.<init>
// Node: imageCode
// Node: getSession
package verifycode.service.impl;

import com.google.common.cache.Cache;
import com.google.common.cache.CacheBuilder;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpHeaders;
import org.springframework.stereotype.Service;
import verifycode.service.VerifyCodeService;
import verifycode.util.CookieUtil;

import javax.servlet.http.Cookie;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.awt.*;
import java.awt.image.BufferedImage;
import java.io.OutputStream;
import java.util.HashMap;
import java.util.Map;
import java.util.Random;
import java.util.UUID;
import java.util.concurrent.TimeUnit;

/**
 * @author fdse
 */
@Service
public class VerifyCodeServiceImpl implements VerifyCodeService {

    public static final int CAPTCHA_EXPIRED = 1000;
    private static final Logger LOGGER = LoggerFactory.getLogger(VerifyCodeServiceImpl.class);

    String ysbCaptcha = "YsbCaptcha";

    /**
     * build local cache
     */
    public Cache<String, String> cacheCode = CacheBuilder.newBuilder()
            // max  size
            .maximumSize(CAPTCHA_EXPIRED)
            .expireAfterAccess(CAPTCHA_EXPIRED, TimeUnit.SECONDS)
            .build();

    private static char mapTable[] = {
            'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J',
            'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W',
            'X', 'Y', 'Z', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9'};

    @Override
    public Map<String, Object> getImageCode(int width, int height, OutputStream os, HttpServletRequest request, HttpServletResponse response, HttpHeaders headers) {
        Map<String, Object> returnMap = new HashMap<>();
        if (width <= 0) {
            width = 60;
        }
        if (height <= 0) {
            height = 20;
        }
        BufferedImage image = new BufferedImage(width, height, BufferedImage.TYPE_INT_RGB);

        Graphics g = image.getGraphics();

        Random random = new Random(); //NOSONAR

        g.setColor(getRandColor(200, 250));
        g.fillRect(0, 0, width, height);

        g.setFont(new Font("Times New Roman", Font.PLAIN, 18));

        g.setColor(getRandColor(160, 200));
        for (int i = 0; i < 168; i++) {
            int x = random.nextInt(width);
            int y = random.nextInt(height);
            int xl = random.nextInt(12);
            int yl = random.nextInt(12);
            g.drawLine(x, y, x + xl, y + yl);
        }

        String strEnsure = "";

        for (int i = 0; i < 4; ++i) {
            strEnsure += mapTable[(int) (mapTable.length * Math.random())];

            g.setColor(new Color(20 + random.nextInt(110), 20 + random.nextInt(110), 20 + random.nextInt(110)));

            String str = strEnsure.substring(i, i + 1);
            g.drawString(str, 13 * i + 6, 16);
        }

        g.dispose();
        returnMap.put("image", image);
        returnMap.put("strEnsure", strEnsure);

        Cookie cookie = CookieUtil.getCookieByName(request, ysbCaptcha);
        String cookieId;
        if (cookie == null) {
            VerifyCodeServiceImpl.LOGGER.warn("[getImageCode][Get image code warn.Cookie not found][Path Info: {}]",request.getPathInfo());
            cookieId = UUID.randomUUID().toString().replace("-", "").toUpperCase();
            CookieUtil.addCookie(response, ysbCaptcha, cookieId, CAPTCHA_EXPIRED);
        } else {
            if (cookie.getValue() != null) {
                cookieId = UUID.randomUUID().toString().replace("-", "").toUpperCase();
                CookieUtil.addCookie(response, ysbCaptcha, cookieId, CAPTCHA_EXPIRED);
            } else {
                cookieId = cookie.getValue();
            }
        }
        VerifyCodeServiceImpl.LOGGER.info("[getImageCode][strEnsure: {}]", strEnsure);
        cacheCode.put(cookieId, strEnsure);
        return returnMap;
    }

    @Override
    public boolean verifyCode(HttpServletRequest request, HttpServletResponse response, String receivedCode, HttpHeaders headers) {
        boolean result = false;
        Cookie cookie = CookieUtil.getCookieByName(request, ysbCaptcha);
        String cookieId;
        if (cookie == null) {
            VerifyCodeServiceImpl.LOGGER.warn("[verifyCode][Verify code warn][Cookie not found][Path Info: {}]",request.getPathInfo());
            cookieId = UUID.randomUUID().toString().replace("-", "").toUpperCase();
            CookieUtil.addCookie(response, ysbCaptcha, cookieId, CAPTCHA_EXPIRED);
        } else {
            cookieId = cookie.getValue();
        }

        String code = cacheCode.getIfPresent(cookieId);
        LOGGER.info("GET Code By cookieId " + cookieId + "   is :" + code);
        if (code == null) {
            VerifyCodeServiceImpl.LOGGER.warn("[verifyCode][Get image code warn][Code not found][CookieId: {}]",cookieId);
            return false;
        }
        if (code.equalsIgnoreCase(receivedCode)) {
            result = true;
        }
        return result;
    }


    static Color getRandColor(int fc, int bc) {
        Random random = new Random(); //NOSONAR
        if (fc > 255) {
            fc = 255;
        }
        if (bc > 255) {
            bc = 255;
        }
        int r = fc + random.nextInt(bc - fc);
        int g = fc + random.nextInt(bc - fc);
        int b = fc + random.nextInt(bc - fc);
        return new Color(r, g, b);
    }

}


// Node: repos/cloned_ms_repos/train-ticket/ts-verification-code-service/src/main/java/verifycode/service/impl/VerifyCodeServiceImpl.java:VerifyCodeServiceImpl.<init>
// Node: newBuilder
// Node: maximumSize
// Node: expireAfterAccess
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


package rebook.controller;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.web.bind.annotation.*;
import rebook.entity.RebookInfo;
import rebook.service.RebookService;

import static org.springframework.http.ResponseEntity.ok;

/**
 * @author fdse
 */
@RestController
@RequestMapping("/api/v1/rebookservice")
public class RebookController {

    @Autowired
    RebookService service;

    private static final Logger LOGGER = LoggerFactory.getLogger(RebookController.class);

    @GetMapping(path = "/welcome")
    public String home() {
        return "Welcome to [ Rebook Service ] !";
    }

    @PostMapping(value = "/rebook/difference")
    public HttpEntity payDifference(@RequestBody RebookInfo info,
                                    @RequestHeader HttpHeaders headers) {
        RebookController.LOGGER.info("[payDifference][Pay difference][OrderId: {}]",info.getOrderId());
        return ok(service.payDifference(info, headers));
    }

    @PostMapping(value = "/rebook")
    public HttpEntity rebook(@RequestBody RebookInfo info, @RequestHeader HttpHeaders headers) {
        RebookController.LOGGER.info("[rebook][Rebook][OrderId: {}, Old Trip Id: {}, New Trip Id: {}, Date: {}, Seat Type: {}]", info.getOrderId(), info.getOldTripId(), info.getTripId(), info.getDate(), info.getSeatType());
        return ok(service.rebook(info, headers));
    }

}


// Node: repos/cloned_ms_repos/train-ticket/ts-rebook-service/src/main/java/rebook/controller/RebookController.java:RebookController.<init>
package rebook.service;

import edu.fudan.common.entity.Trip;
import edu.fudan.common.entity.TripAllDetail;
import edu.fudan.common.entity.TripAllDetailInfo;
import edu.fudan.common.entity.TripResponse;
import edu.fudan.common.util.JsonUtils;
import edu.fudan.common.util.Response;
import edu.fudan.common.util.StringUtils;
import org.apache.tomcat.jni.Time;
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
import edu.fudan.common.entity.*;
import rebook.entity.*;

import java.math.BigDecimal;
import java.util.Calendar;
import java.util.Date;
import java.util.List;

/**
 * @author fdse
 */
@Service
public class RebookServiceImpl implements RebookService {

    @Autowired
    private RestTemplate restTemplate;
    @Autowired
    private DiscoveryClient discoveryClient;

    private static final Logger LOGGER = LoggerFactory.getLogger(RebookServiceImpl.class);

    private String getServiceUrl(String serviceName) {
        return "http://" + serviceName;
    }

    @Override
    public Response rebook(RebookInfo info, HttpHeaders httpHeaders) {

        Response<Order> queryOrderResult = getOrderByRebookInfo(info, httpHeaders);

        if (queryOrderResult.getStatus() == 1) {
            if (queryOrderResult.getData().getStatus() != 1) {
                RebookServiceImpl.LOGGER.warn("[rebook][Rebook warn][Order not suitable to rebook][OrderId: {}]",info.getOrderId());
                return new Response<>(0, "you order not suitable to rebook!", null);
            }
        } else {
            RebookServiceImpl.LOGGER.warn("[rebook][Rebook warn][Order not found][OrderId: {}]",info.getOrderId());
            return new Response(0, "order not found", null);
        }

        Order order = queryOrderResult.getData();
        int status = order.getStatus();
        if (status == OrderStatus.NOTPAID.getCode()) {
            RebookServiceImpl.LOGGER.warn("[rebook][Rebook warn][Order not paid][OrderId: {}]",info.getOrderId());
            return new Response<>(0, "You haven't paid the original ticket!", null);
        } else if (status == OrderStatus.PAID.getCode()) {
            // do nothing
        } else if (status == OrderStatus.CHANGE.getCode()) {
            RebookServiceImpl.LOGGER.warn("[rebook][Rebook warn][Order can't change twice][OrderId: {}]",info.getOrderId());
            return new Response<>(0, "You have already changed your ticket and you can only change one time.", null);
        } else if (status == OrderStatus.COLLECTED.getCode()) {
            RebookServiceImpl.LOGGER.warn("[rebook][Rebook warn][Order already collected][OrderId: {}]",info.getOrderId());
            return new Response<>(0, "You have already collected your ticket and you can change it now.", null);
        } else {
            RebookServiceImpl.LOGGER.warn("[rebook][Rebook warn][Order can't change][OrderId: {}]",info.getOrderId());
            return new Response<>(0, "You can't change your ticket.", null);
        }

        //Check the current time and the bus time of the old order, and judge whether the ticket can be changed according to the time. The ticket cannot be changed after two hours.
        if (!checkTime(order.getTravelDate(), order.getTravelTime())) {
            RebookServiceImpl.LOGGER.warn("[rebook][Rebook warn][Order beyond change time][OrderId: {}]",info.getOrderId());
            return new Response<>(0, "You can only change the ticket before the train start or within 2 hours after the train start.", null);
        }

        //The departure and destination cannot be changed, only the train number, seat and time can be changed
        //Check the info of seat availability and trains
        TripAllDetailInfo gtdi = new TripAllDetailInfo();
        gtdi.setFrom(order.getFrom());
        gtdi.setTo(order.getTo());
        gtdi.setTravelDate(info.getDate());
        gtdi.setTripId(info.getTripId());
        Response<TripAllDetail> gtdr = getTripAllDetailInformation(gtdi, info.getTripId(), httpHeaders);
        if (gtdr.getStatus() == 0) {
            RebookServiceImpl.LOGGER.warn("[rebook][Rebook warn][Trip detail not found][OrderId: {}]",info.getOrderId());
            return new Response<>(0, gtdr.getMsg(), null);
        } else {
            TripResponse tripResponse = gtdr.getData().getTripResponse();
            if (info.getSeatType() == SeatClass.FIRSTCLASS.getCode()) {
                if (tripResponse.getConfortClass() <= 0) {
                    RebookServiceImpl.LOGGER.warn("[rebook][Rebook warn][Seat Not Enough][OrderId: {},SeatType: {}]",info.getOrderId(),info.getSeatType());
                    return new Response<>(0, "Seat Not Enough", null);
                }
            } else {
                if (tripResponse.getEconomyClass() == SeatClass.SECONDCLASS.getCode() && tripResponse.getConfortClass() <= 0) {
                    RebookServiceImpl.LOGGER.warn("[rebook][Rebook warn][Seat Not Enough][OrderId: {},SeatType: {}]",info.getOrderId(),info.getSeatType());
                    return new Response<>(0, "Seat Not Enough", null);
                }
            }
        }

        //Deal with the difference, more refund less compensation
        //Return the original ticket so that someone else can book the corresponding seat

        String ticketPrice = "0";
        if (info.getSeatType() == SeatClass.FIRSTCLASS.getCode()) {
            ticketPrice = ((TripAllDetail) gtdr.getData()).getTripResponse().getPriceForConfortClass();
        } else if (info.getSeatType() == SeatClass.SECONDCLASS.getCode()) {
            ticketPrice = ((TripAllDetail) gtdr.getData()).getTripResponse().getPriceForEconomyClass();
        }
        String oldPrice = order.getPrice();
        BigDecimal priceOld = new BigDecimal(oldPrice);
        BigDecimal priceNew = new BigDecimal(ticketPrice);
        if (priceOld.compareTo(priceNew) > 0) {
            //Refund the difference
            String difference = priceOld.subtract(priceNew).toString();
            if (!drawBackMoney(info.getLoginId(), difference, httpHeaders)) {
                RebookServiceImpl.LOGGER.warn("[rebook][Rebook warn][Can't draw back the difference money][OrderId: {},LoginId: {},difference: {}]",info.getOrderId(),info.getLoginId(),difference);
                return new Response<>(0, "Can't draw back the difference money, please try again!", null);
            }
            return updateOrder(order, info, (TripAllDetail) gtdr.getData(), ticketPrice, httpHeaders);

        } else if (priceOld.compareTo(priceNew) == 0) {
            //do nothing
            return updateOrder(order, info, (TripAllDetail) gtdr.getData(), ticketPrice, httpHeaders);
        } else {
            //make up the difference
            String difference = priceNew.subtract(priceOld).toString();
            Order orderMoneyDifference = new Order();
            orderMoneyDifference.setDifferenceMoney(difference);
            return new Response<>(2, "Please pay the different money!", orderMoneyDifference);
        }
    }

    @Override
    public Response payDifference(RebookInfo info, HttpHeaders httpHeaders) {

        Response queryOrderResult = getOrderByRebookInfo(info, httpHeaders);
        if (queryOrderResult.getStatus() == 0) {
            return new Response<>(0, queryOrderResult.getMsg(), null);
        }
        Order order = (Order) queryOrderResult.getData();

        TripAllDetailInfo gtdi = new TripAllDetailInfo();
        gtdi.setFrom(order.getFrom());
        gtdi.setTo(order.getTo());
        gtdi.setTravelDate(info.getDate());
        gtdi.setTripId(info.getTripId());
        // TripAllDetail
        Response gtdrResposne = getTripAllDetailInformation(gtdi, info.getTripId(), httpHeaders);


        TripAllDetail gtdr = (TripAllDetail) gtdrResposne.getData();


        String ticketPrice = "0";
        if (info.getSeatType() == SeatClass.FIRSTCLASS.getCode()) {
            ticketPrice = gtdr.getTripResponse().getPriceForConfortClass();
        } else if (info.getSeatType() == SeatClass.SECONDCLASS.getCode()) {
            ticketPrice = gtdr.getTripResponse().getPriceForEconomyClass();
        }
        String oldPrice = order.getPrice();
        BigDecimal priceOld = new BigDecimal(oldPrice);
        BigDecimal priceNew = new BigDecimal(ticketPrice);

        if (payDifferentMoney(info.getOrderId(), info.getTripId(), info.getLoginId(), priceNew.subtract(priceOld).toString(), httpHeaders)) {
            return updateOrder(order, info, gtdr, ticketPrice, httpHeaders);
        } else {
            RebookServiceImpl.LOGGER.warn("[payDifference][Pay difference warn][Can't pay the difference money][OrderId: {},LoginId: {},TripId: {}]",info.getOrderId(),info.getLoginId(),info.getTripId());
            return new Response<>(0, "Can't pay the difference,please try again", null);
        }
    }

    private Response updateOrder(Order order, RebookInfo info, TripAllDetail gtdr, String ticketPrice, HttpHeaders httpHeaders) {

        //4.Modify the original order and set the information of the order
        Trip trip = gtdr.getTrip();
        String oldTripId = order.getTrainNumber();
        order.setTrainNumber(info.getTripId());
        order.setBoughtDate(StringUtils.Date2String(new Date()));
        order.setStatus(OrderStatus.CHANGE.getCode());
        order.setPrice(ticketPrice);//Set ticket price
        order.setSeatClass(info.getSeatType());
        order.setTravelDate(info.getDate());
        order.setTravelTime(trip.getStartTime());

        Route route = getRouteByRouteId(trip.getRouteId(), httpHeaders);
        TrainType trainType = queryTrainTypeByName(trip.getTrainTypeName(), httpHeaders);
        List<String> stations = route.getStations();
        int firstClassTotalNum = trainType.getConfortClass();
        int secondClassTotalNum = trainType.getEconomyClass();
        if (info.getSeatType() == SeatClass.FIRSTCLASS.getCode()) {//Dispatch the seat
            Ticket ticket =
                    dipatchSeat(info.getDate(),
                            order.getTrainNumber(), order.getFrom(), order.getTo(),
                            SeatClass.FIRSTCLASS.getCode(), firstClassTotalNum, stations, httpHeaders);
            order.setSeatClass(SeatClass.FIRSTCLASS.getCode());
            order.setSeatNumber("" + ticket.getSeatNo());
        } else {
            Ticket ticket =
                    dipatchSeat(info.getDate(),
                            order.getTrainNumber(), order.getFrom(), order.getTo(),
                            SeatClass.SECONDCLASS.getCode(), secondClassTotalNum, stations, httpHeaders);
            order.setSeatClass(SeatClass.SECONDCLASS.getCode());
            order.setSeatNumber("" + ticket.getSeatNo());
        }

        //Update order information
        //If the original order and the new order are located in the high-speed train and other orders respectively, the original order should be deleted and created on the other side with a new id.
        if ((tripGD(oldTripId) && tripGD(info.getTripId())) || (!tripGD(oldTripId) && !tripGD(info.getTripId()))) {

            Response changeOrderResult = updateOrder(order, info.getTripId(), httpHeaders);
            if (changeOrderResult.getStatus() == 1) {
                return new Response<>(1, "Success!", order);
            } else {
                RebookServiceImpl.LOGGER.error("[updateOrder][Update order error][OrderId: {},TripId: {}]",info.getOrderId(),info.getTripId());
                return new Response<>(0, "Can't update Order!", null);
            }
        } else {
            //Delete the original order
            deleteOrder(order.getId().toString(), oldTripId, httpHeaders);
            //Create a new order on the other side
            createOrder(order, order.getTrainNumber(), httpHeaders);
            return new Response<>(1, "Success", order);
        }
    }

    public Ticket dipatchSeat(String date, String tripId, String startStationId, String endStataionId, int seatType, int tatalNum, List<String> stations, HttpHeaders httpHeaders) {
        Seat seatRequest = new Seat();
        seatRequest.setTravelDate(date);
        seatRequest.setTrainNumber(tripId);
        seatRequest.setSeatType(seatType);
        seatRequest.setStartStation(startStationId);
        seatRequest.setDestStation(endStataionId);
        seatRequest.setTotalNum(tatalNum);
        seatRequest.setStations(stations);

        HttpHeaders newHeaders = getAuthorizationHeadersFrom(httpHeaders);
        HttpEntity requestEntityTicket = new HttpEntity(seatRequest, newHeaders);
        String seat_service_url = getServiceUrl("ts-seat-service");
        ResponseEntity<Response<Ticket>> reTicket = restTemplate.exchange(
                seat_service_url + "/api/v1/seatservice/seats",
                HttpMethod.POST,
                requestEntityTicket,
                new ParameterizedTypeReference<Response<Ticket>>() {
                });
        return reTicket.getBody().getData();
    }


    private boolean tripGD(String tripId) {
        return tripId.startsWith("G") || tripId.startsWith("D");
    }

    private boolean checkTime(String travelDate, String travelTime) {
        boolean result = true;
        Calendar calDateA = Calendar.getInstance();
        Date today = new Date();
        calDateA.setTime(today);
        Calendar calDateB = Calendar.getInstance();
        calDateB.setTime(StringUtils.String2Date(travelDate));
        Calendar calDateC = Calendar.getInstance();
        calDateC.setTime(StringUtils.String2Date(travelTime));
        if (calDateA.get(Calendar.YEAR) > calDateB.get(Calendar.YEAR)) {
            result = false;
        } else if (calDateA.get(Calendar.YEAR) == calDateB.get(Calendar.YEAR)) {
            if (calDateA.get(Calendar.MONTH) > calDateB.get(Calendar.MONTH)) {
                result = false;
            } else if (calDateA.get(Calendar.MONTH) == calDateB.get(Calendar.MONTH)) {
                if (calDateA.get(Calendar.DAY_OF_MONTH) > calDateB.get(Calendar.DAY_OF_MONTH)) {
                    result = false;
                } else if (calDateA.get(Calendar.DAY_OF_MONTH) == calDateB.get(Calendar.DAY_OF_MONTH)) {
                    if (calDateA.get(Calendar.HOUR_OF_DAY) > calDateC.get(Calendar.HOUR_OF_DAY) + 2) {
                        result = false;
                    } else if (calDateA.get(Calendar.HOUR_OF_DAY) == (calDateC.get(Calendar.HOUR_OF_DAY) + 2) && calDateA.get(Calendar.MINUTE) > calDateC.get(Calendar.MINUTE)) {
                        result = false;
                    }
                }
            }
        }
        return result;
    }


    private Response<TripAllDetail> getTripAllDetailInformation(TripAllDetailInfo gtdi, String tripId, HttpHeaders httpHeaders) {
        Response<TripAllDetail> gtdr;
        String requestUrl = "";
        String travel_service_url = getServiceUrl("ts-travel-service");
        String travel2_service_url = getServiceUrl("ts-travel2-service");
        if (tripId.startsWith("G") || tripId.startsWith("D")) {
            requestUrl = travel_service_url + "/api/v1/travelservice/trip_detail";
            // ts-travel-service:12346/travel/getTripAllDetailInfo
        } else {
            requestUrl = travel2_service_url + "/api/v1/travel2service/trip_detail";
            //ts-travel2-service:16346/travel2/getTripAllDetailInfo
        }
        HttpHeaders newHeaders = getAuthorizationHeadersFrom(httpHeaders);
        HttpEntity requestGetTripAllDetailResult = new HttpEntity(gtdi, newHeaders);
        ResponseEntity<Response<TripAllDetail>> reGetTripAllDetailResult = restTemplate.exchange(
                requestUrl,
                HttpMethod.POST,
                requestGetTripAllDetailResult,
                new ParameterizedTypeReference<Response<TripAllDetail>>() {
                });
        gtdr = reGetTripAllDetailResult.getBody();
        return gtdr;
    }

    private Response createOrder(Order order, String tripId, HttpHeaders httpHeaders) {
        String requestUrl = "";
        String order_service_url = getServiceUrl("ts-order-service");
        String order_other_service_url = getServiceUrl("ts-order-other-service");
        if (tripId.startsWith("G") || tripId.startsWith("D")) {
            // ts-order-service:12031/order/create
            requestUrl = order_service_url + "/api/v1/orderservice/order";
        } else {
            //ts-order-other-service:12032/orderOther/create
            requestUrl = order_other_service_url + "/api/v1/orderOtherService/orderOther";
        }
        HttpHeaders newHeaders = getAuthorizationHeadersFrom(httpHeaders);
        HttpEntity requestCreateOrder = new HttpEntity(order, newHeaders);
        ResponseEntity<Response> reCreateOrder = restTemplate.exchange(
                requestUrl,
                HttpMethod.POST,
                requestCreateOrder,
                Response.class);
        return reCreateOrder.getBody();
    }

    private Response updateOrder(Order info, String tripId, HttpHeaders httpHeaders) {
        String requestOrderUtl = "";
        String order_service_url = getServiceUrl("ts-order-service");
        String order_other_service_url = getServiceUrl("ts-order-other-service");
        if (tripGD(tripId)) {
            requestOrderUtl = order_service_url + "/api/v1/orderservice/order";
        } else {
            requestOrderUtl = order_other_service_url + "/api/v1/orderOtherService/orderOther";
        }
        HttpHeaders newHeaders = getAuthorizationHeadersFrom(httpHeaders);
        HttpEntity requestUpdateOrder = new HttpEntity(info, newHeaders);
        ResponseEntity<Response> reUpdateOrder = restTemplate.exchange(
                requestOrderUtl,
                HttpMethod.PUT,
                requestUpdateOrder,
                Response.class);
        return reUpdateOrder.getBody();
    }

    private Response deleteOrder(String orderId, String tripId, HttpHeaders httpHeaders) {

        String requestUrl = "";
        String order_service_url = getServiceUrl("ts-order-service");
        String order_other_service_url = getServiceUrl("ts-order-other-service");
        if (tripGD(tripId)) {
            requestUrl = order_service_url + "/api/v1/orderservice/order/" + orderId;
        } else {
            requestUrl = order_other_service_url + "/api/v1/orderOtherService/orderOther/" + orderId;
        }
        HttpHeaders newHeaders = getAuthorizationHeadersFrom(httpHeaders);
        HttpEntity requestDeleteOrder = new HttpEntity(newHeaders);
        ResponseEntity<Response> reDeleteOrder = restTemplate.exchange(
                requestUrl,
                HttpMethod.POST,
                requestDeleteOrder,
                Response.class);

        return reDeleteOrder.getBody();
    }

    private Response<Order> getOrderByRebookInfo(RebookInfo info, HttpHeaders httpHeaders) {
        Response<Order> queryOrderResult;
        //Change can only be changed once, check the status of the order to determine whether it has been changed
        String requestUrl = "";
        String order_service_url = getServiceUrl("ts-order-service");
        String order_other_service_url = getServiceUrl("ts-order-other-service");
        if (info.getOldTripId().startsWith("G") || info.getOldTripId().startsWith("D")) {
            requestUrl = order_service_url + "/api/v1/orderservice/order/" + info.getOrderId();
        } else {
            requestUrl = order_other_service_url + "/api/v1/orderOtherService/orderOther/" + info.getOrderId();
        }
        HttpHeaders newHeaders = getAuthorizationHeadersFrom(httpHeaders);
        HttpEntity requestEntityGetOrderByRebookInfo = new HttpEntity(newHeaders);
        ResponseEntity<Response<Order>> reGetOrderByRebookInfo = restTemplate.exchange(
                requestUrl,
                HttpMethod.GET,
                requestEntityGetOrderByRebookInfo,
                new ParameterizedTypeReference<Response<Order>>() {
                });

        queryOrderResult = reGetOrderByRebookInfo.getBody();
        return queryOrderResult;
    }

    public TrainType queryTrainTypeByName(String trainTypeName, HttpHeaders headers) {
        HttpEntity requestEntity = new HttpEntity(null);
        String train_service_url=getServiceUrl("ts-train-service");
        ResponseEntity<Response> re = restTemplate.exchange(
                train_service_url + "/api/v1/trainservice/trains/byName/" + trainTypeName,
                HttpMethod.GET,
                requestEntity,
                Response.class);
        Response  response = re.getBody();

        return JsonUtils.conveterObject(response.getData(), TrainType.class);
    }

    private Route getRouteByRouteId(String routeId, HttpHeaders headers) {
        HttpEntity requestEntity = new HttpEntity(null);
        String route_service_url=getServiceUrl("ts-route-service");
        ResponseEntity<Response> re = restTemplate.exchange(
                route_service_url + "/api/v1/routeservice/routes/" + routeId,
                HttpMethod.GET,
                requestEntity,
                Response.class);
        Response result = re.getBody();
        if ( result.getStatus() == 0) {
            LOGGER.warn("[getRouteByRouteId][Get Route By Id Failed][Fail msg: {}]", result.getMsg());
            return null;
        } else {
            LOGGER.info("[getRouteByRouteId][Get Route By Id][Success]");
            return JsonUtils.conveterObject(result.getData(), Route.class);
        }
    }

    private boolean payDifferentMoney(String orderId, String tripId, String userId, String money, HttpHeaders httpHeaders) {
        PaymentDifferenceInfo info = new PaymentDifferenceInfo();
        info.setOrderId(orderId);
        info.setTripId(tripId);
        info.setUserId(userId);
        info.setPrice(money);

        HttpHeaders newHeaders = getAuthorizationHeadersFrom(httpHeaders);
        HttpEntity requestEntityPayDifferentMoney = new HttpEntity(info, newHeaders);
        String inside_payment_service_url = getServiceUrl("ts-inside-payment-service");
        ResponseEntity<Response> rePayDifferentMoney = restTemplate.exchange(
                inside_payment_service_url + "/api/v1/inside_pay_service/inside_payment/difference",
                HttpMethod.POST,
                requestEntityPayDifferentMoney,
                Response.class);
        Response result = rePayDifferentMoney.getBody();
        return result.getStatus() == 1;
    }

    private boolean drawBackMoney(String userId, String money, HttpHeaders httpHeaders) {

        HttpHeaders newHeaders = getAuthorizationHeadersFrom(httpHeaders);
        HttpEntity requestEntityDrawBackMoney = new HttpEntity(newHeaders);
        String inside_payment_service_url = getServiceUrl("ts-inside-payment-service");
        ResponseEntity<Response> reDrawBackMoney = restTemplate.exchange(
                inside_payment_service_url + "/api/v1/inside_pay_service/inside_payment/drawback/" + userId + "/" + money,
                HttpMethod.GET,
                requestEntityDrawBackMoney,
                Response.class);
        Response result = reDrawBackMoney.getBody();
        return result.getStatus() == 1;
    }

    public static HttpHeaders getAuthorizationHeadersFrom(HttpHeaders oldHeaders) {
        HttpHeaders newHeaders = new HttpHeaders();
        if (oldHeaders.containsKey(HttpHeaders.AUTHORIZATION)) {
            newHeaders.add(HttpHeaders.AUTHORIZATION, oldHeaders.getFirst(HttpHeaders.AUTHORIZATION));
        }
        return newHeaders;
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-rebook-service/src/main/java/rebook/service/RebookServiceImpl.java:RebookServiceImpl.<init>
package cancel.controller;

import cancel.service.CancelService;
import edu.fudan.common.util.Response;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import static org.springframework.http.ResponseEntity.ok;

/**
 * @author fdse
 */
@RestController
@RequestMapping("/api/v1/cancelservice")
public class CancelController {

    @Autowired
    CancelService cancelService;

    private static final Logger LOGGER = LoggerFactory.getLogger(CancelController.class);

    @GetMapping(path = "/welcome")
    public String home(@RequestHeader HttpHeaders headers) {
        return "Welcome to [ Cancel Service ] !";
    }

    @CrossOrigin(origins = "*")
    @GetMapping(path = "/cancel/refound/{orderId}")
    public HttpEntity calculate(@PathVariable String orderId, @RequestHeader HttpHeaders headers) {
        CancelController.LOGGER.info("[calculate][Calculate Cancel Refund][OrderId: {}]", orderId);
        return ok(cancelService.calculateRefund(orderId, headers));
    }

    @CrossOrigin(origins = "*")
    @GetMapping(path = "/cancel/{orderId}/{loginId}")
    public HttpEntity cancelTicket(@PathVariable String orderId, @PathVariable String loginId,
                                   @RequestHeader HttpHeaders headers) {

        CancelController.LOGGER.info("[cancelTicket][Cancel Ticket][info: {}]", orderId);
        try {
            CancelController.LOGGER.info("[cancelTicket][Cancel Ticket, Verify Success]");
            return ok(cancelService.cancelOrder(orderId, loginId, headers));
        } catch (Exception e) {
            CancelController.LOGGER.error(e.getMessage());
            return ok(new Response<>(1, "error", null));
        }
    }

}


// Node: repos/cloned_ms_repos/train-ticket/ts-cancel-service/src/main/java/cancel/controller/CancelController.java:CancelController.<init>
// Node: calculate
// Node: cancelTicket
package cancel.service;

import edu.fudan.common.entity.NotifyInfo;
import edu.fudan.common.entity.OrderStatus;
import edu.fudan.common.entity.Order;
import edu.fudan.common.entity.SeatClass;
import edu.fudan.common.entity.User;
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

import java.text.DecimalFormat;
import java.util.Calendar;
import java.util.Date;

/**
 * @author fdse
 */
@Service
public class CancelServiceImpl implements CancelService {

    @Autowired
    private RestTemplate restTemplate;
    @Autowired
    private DiscoveryClient discoveryClient;

    private static final Logger LOGGER = LoggerFactory.getLogger(CancelServiceImpl.class);

    String orderStatusCancelNotPermitted = "Order Status Cancel Not Permitted";

    private String getServiceUrl(String serviceName) {
        return "http://" + serviceName;
    }

    @Override
    public Response cancelOrder(String orderId, String loginId, HttpHeaders headers) {

        Response<Order> orderResult = getOrderByIdFromOrder(orderId, headers);
        if (orderResult.getStatus() == 1) {
            CancelServiceImpl.LOGGER.info("[cancelOrder][Cancel Order, Order found G|H]");
            Order order =  orderResult.getData();
            if (order.getStatus() == OrderStatus.NOTPAID.getCode()
                    || order.getStatus() == OrderStatus.PAID.getCode() || order.getStatus() == OrderStatus.CHANGE.getCode()) {

                // order.setStatus(OrderStatus.CANCEL.getCode());

                Response changeOrderResult = cancelFromOrder(order, headers);
                // 0 -- not find order   1 - cancel success
                if (changeOrderResult.getStatus() == 1) {

                    CancelServiceImpl.LOGGER.info("[cancelOrder][Cancel Order Success]");
                    //Draw back money
                    String money = calculateRefund(order);
                    boolean status = drawbackMoney(money, loginId, headers);
                    if (status) {
                        CancelServiceImpl.LOGGER.info("[cancelOrder][Draw Back Money Success]");



                        Response<User> result = getAccount(order.getAccountId().toString(), headers);
                        if (result.getStatus() == 0) {
                            return new Response<>(0, "Cann't find userinfo by user id.", null);
                        }
                        NotifyInfo notifyInfo = new NotifyInfo();
                        notifyInfo.setDate(new Date().toString());
                        notifyInfo.setEmail(result.getData().getEmail());
                        notifyInfo.setStartPlace(order.getFrom());
                        notifyInfo.setEndPlace(order.getTo());
                        notifyInfo.setUsername(result.getData().getUserName());
                        notifyInfo.setSeatNumber(order.getSeatNumber());
                        notifyInfo.setOrderNumber(order.getId().toString());
                        notifyInfo.setPrice(order.getPrice());
                        notifyInfo.setSeatClass(SeatClass.getNameByCode(order.getSeatClass()));
                        notifyInfo.setStartTime(order.getTravelTime().toString());

                        // TODO: change to async message serivce
                        // sendEmail(notifyInfo, headers);

                    } else {
                        CancelServiceImpl.LOGGER.error("[cancelOrder][Draw Back Money Failed][loginId: {}, orderId: {}]", loginId, orderId);
                    }
                    return new Response<>(1, "Success.", "test not null");
                } else {
                    CancelServiceImpl.LOGGER.error("[cancelOrder][Cancel Order Failed][orderId: {}, Reason: {}]", orderId, changeOrderResult.getMsg());
                    return new Response<>(0, changeOrderResult.getMsg(), null);
                }

            } else {
                CancelServiceImpl.LOGGER.info("[cancelOrder][Cancel Order, Order Status Not Permitted][loginId: {}, orderId: {}]", loginId, orderId);
                return new Response<>(0, orderStatusCancelNotPermitted, null);
            }
        } else {

            Response<Order> orderOtherResult = getOrderByIdFromOrderOther(orderId, headers);
            if (orderOtherResult.getStatus() == 1) {
                CancelServiceImpl.LOGGER.info("[cancelOrder][Cancel Order, Order found Z|K|Other]");

                Order order =   orderOtherResult.getData();
                if (order.getStatus() == OrderStatus.NOTPAID.getCode()
                        || order.getStatus() == OrderStatus.PAID.getCode() || order.getStatus() == OrderStatus.CHANGE.getCode()) {

                    CancelServiceImpl.LOGGER.info("[cancelOrder][Cancel Order, Order status ok]");

//                    order.setStatus(OrderStatus.CANCEL.getCode());
                    Response changeOrderResult = cancelFromOtherOrder(order, headers);

                    if (changeOrderResult.getStatus() == 1) {
                        CancelServiceImpl.LOGGER.info("[cancelOrder][Cancel Order Success]");
                        //Draw back money
                        String money = calculateRefund(order);
                        boolean status = drawbackMoney(money, loginId, headers);
                        if (status) {
                            CancelServiceImpl.LOGGER.info("[cancelOrder][Draw Back Money Success]");
                        } else {
                            CancelServiceImpl.LOGGER.error("[cancelOrder][Draw Back Money Failed][loginId: {}, orderId: {}]", loginId, orderId);
                        }
                        return new Response<>(1, "Success.", null);
                    } else {
                        CancelServiceImpl.LOGGER.error("[cancelOrder][Cancel Order Failed][orderId: {}, Reason: {}]", orderId, changeOrderResult.getMsg());
                        return new Response<>(0, "Fail.Reason:" + changeOrderResult.getMsg(), null);
                    }
                } else {
                    CancelServiceImpl.LOGGER.warn("[cancelOrder][Cancel Order, Order Status Not Permitted][loginId: {}, orderId: {}]", loginId, orderId);
                    return new Response<>(0, orderStatusCancelNotPermitted, null);
                }
            } else {
                CancelServiceImpl.LOGGER.warn("[cancelOrder][Cancel Order, Order Not Found][loginId: {}, orderId: {}]", loginId, orderId);
                return new Response<>(0, "Order Not Found.", null);
            }
        }
    }

    public boolean sendEmail(NotifyInfo notifyInfo, HttpHeaders headers) {
        CancelServiceImpl.LOGGER.info("[sendEmail][Send Email]");
        HttpHeaders newHeaders = getAuthorizationHeadersFrom(headers);
        HttpEntity requestEntity = new HttpEntity(notifyInfo, newHeaders);
        String notification_service_url = getServiceUrl("ts-notification-service");
        ResponseEntity<Boolean> re = restTemplate.exchange(
                notification_service_url + "/api/v1/notifyservice/notification/order_cancel_success",
                HttpMethod.POST,
                requestEntity,
                Boolean.class);
        return re.getBody();
    }

    @Override
    public Response calculateRefund(String orderId, HttpHeaders headers) {

        Response<Order> orderResult = getOrderByIdFromOrder(orderId, headers);
        if (orderResult.getStatus() == 1) {
            Order order =   orderResult.getData();
            if (order.getStatus() == OrderStatus.NOTPAID.getCode()
                    || order.getStatus() == OrderStatus.PAID.getCode()) {
                if (order.getStatus() == OrderStatus.NOTPAID.getCode()) {
                    CancelServiceImpl.LOGGER.info("[calculateRefund][Cancel Order, Refund Price From Order Service.Not Paid][orderId: {}]", orderId);
                    return new Response<>(1, "Success. Refoud 0", "0");
                } else {
                    CancelServiceImpl.LOGGER.info("[calculateRefund][Cancel Order, Refund Price From Order Service.Paid][orderId: {}]", orderId);
                    return new Response<>(1, "Success. ", calculateRefund(order));
                }
            } else {
                CancelServiceImpl.LOGGER.info("[calculateRefund][Cancel Order Refund Price Order.Cancel Not Permitted][orderId: {}]", orderId);
                return new Response<>(0, "Order Status Cancel Not Permitted, Refound error", null);
            }
        } else {

            Response<Order> orderOtherResult = getOrderByIdFromOrderOther(orderId, headers);
            if (orderOtherResult.getStatus() == 1) {
                Order order =   orderOtherResult.getData();
                if (order.getStatus() == OrderStatus.NOTPAID.getCode()
                        || order.getStatus() == OrderStatus.PAID.getCode()) {
                    if (order.getStatus() == OrderStatus.NOTPAID.getCode()) {
                        CancelServiceImpl.LOGGER.info("[calculateRefund][Cancel Order, Refund Price From Order Other Service.Not Paid][orderId: {}]", orderId);
                        return new Response<>(1, "Success, Refound 0", "0");
                    } else {
                        CancelServiceImpl.LOGGER.info("[Cancel Order][Refund Price From Order Other Service.Paid][orderId: {}]", orderId);
                        return new Response<>(1, "Success", calculateRefund(order));
                    }
                } else {
                    CancelServiceImpl.LOGGER.warn("[Cancel Order][Refund Price, Order Other. Cancel Not Permitted][orderId: {}]", orderId);
                    return new Response<>(0, orderStatusCancelNotPermitted, null);
                }
            } else {
                CancelServiceImpl.LOGGER.error("[Cancel Order][Refund Price][Order not found][orderId: {}]", orderId);
                return new Response<>(0, "Order Not Found", null);
            }
        }
    }

    private String calculateRefund(Order order) {
        if (order.getStatus() == OrderStatus.NOTPAID.getCode()) {
            return "0.00";
        }
        CancelServiceImpl.LOGGER.info("[calculateRefund][Cancel Order][Order Travel Date: {}]", order.getTravelDate().toString());
        Date nowDate = new Date();
        Calendar cal = Calendar.getInstance();
        cal.setTime(StringUtils.String2Date(order.getTravelDate()));
        int year = cal.get(Calendar.YEAR);
        int month = cal.get(Calendar.MONTH);
        int day = cal.get(Calendar.DAY_OF_MONTH);
        Calendar cal2 = Calendar.getInstance();
        cal2.setTime(StringUtils.String2Date(order.getTravelTime()));
        int hour = cal2.get(Calendar.HOUR);
        int minute = cal2.get(Calendar.MINUTE);
        int second = cal2.get(Calendar.SECOND);
        Date startTime = new Date(year,  //NOSONAR
                month,
                day,
                hour,
                minute,
                second);
        CancelServiceImpl.LOGGER.info("[calculateRefund][Cancel Order][nowDate  : {}]", nowDate);
        CancelServiceImpl.LOGGER.info("[calculateRefund][Cancel Order][startTime: {}]", startTime);
        if (nowDate.after(startTime)) {
            CancelServiceImpl.LOGGER.warn("[calculateRefund][Cancel Order, Ticket expire refund 0]");
            return "0";
        } else {
            double totalPrice = Double.parseDouble(order.getPrice());
            double price = totalPrice * 0.8;
            DecimalFormat priceFormat = new java.text.DecimalFormat("0.00");
            String str = priceFormat.format(price);
            CancelServiceImpl.LOGGER.info("[calculateRefund][calculate refund][refund: {}]", str);
            return str;
        }
    }


    private Response cancelFromOrder(Order order, HttpHeaders headers) {
        CancelServiceImpl.LOGGER.info("[cancelFromOrder][Change Order Status]");
        order.setStatus(OrderStatus.CANCEL.getCode());
        // add authorization header
        HttpHeaders newHeaders = getAuthorizationHeadersFrom(headers);
        HttpEntity requestEntity = new HttpEntity(order, newHeaders);
        String order_service_url = getServiceUrl("ts-order-service");
        ResponseEntity<Response> re = restTemplate.exchange(
                order_service_url + "/api/v1/orderservice/order",
                HttpMethod.PUT,
                requestEntity,
                Response.class);

        return re.getBody();
    }

    public static HttpHeaders getAuthorizationHeadersFrom(HttpHeaders oldHeaders) {
        HttpHeaders newHeaders = new HttpHeaders();
        if (oldHeaders.containsKey(HttpHeaders.AUTHORIZATION)) {
            newHeaders.add(HttpHeaders.AUTHORIZATION, oldHeaders.getFirst(HttpHeaders.AUTHORIZATION));
        }
        return newHeaders;
    }


    private Response cancelFromOtherOrder(Order order, HttpHeaders headers) {
        CancelServiceImpl.LOGGER.info("[cancelFromOtherOrder][Change Order Status]");
        order.setStatus(OrderStatus.CANCEL.getCode());
        HttpHeaders newHeaders = getAuthorizationHeadersFrom(headers);
        HttpEntity requestEntity = new HttpEntity(order, newHeaders);
        String order_other_service_url = getServiceUrl("ts-order-other-service");
        ResponseEntity<Response> re = restTemplate.exchange(
                order_other_service_url + "/api/v1/orderOtherService/orderOther",
                HttpMethod.PUT,
                requestEntity,
                Response.class);

        return re.getBody();
    }

    public boolean drawbackMoney(String money, String userId, HttpHeaders headers) {
        CancelServiceImpl.LOGGER.info("[drawbackMoney][Draw Back Money]");

        HttpHeaders newHeaders = getAuthorizationHeadersFrom(headers);
        HttpEntity requestEntity = new HttpEntity(newHeaders);
        String inside_payment_service_url = getServiceUrl("ts-inside-payment-service");
        ResponseEntity<Response> re = restTemplate.exchange(
                inside_payment_service_url + "/api/v1/inside_pay_service/inside_payment/drawback/" + userId + "/" + money,
                HttpMethod.GET,
                requestEntity,
                Response.class);
        Response result = re.getBody();

        return result.getStatus() == 1;
    }

    public Response<User> getAccount(String orderId, HttpHeaders headers) {
        CancelServiceImpl.LOGGER.info("[getAccount][Get By Id][orderId: {}]", orderId);
        HttpHeaders newHeaders = getAuthorizationHeadersFrom(headers);
        HttpEntity requestEntity = new HttpEntity(newHeaders);
        String user_service_url = getServiceUrl("ts-user-service");
        ResponseEntity<Response<User>> re = restTemplate.exchange(
                user_service_url + "/api/v1/userservice/users/id/" + orderId,
                HttpMethod.GET,
                requestEntity,
                new ParameterizedTypeReference<Response<User>>() {
                });
        return re.getBody();
    }

    private Response<Order> getOrderByIdFromOrder(String orderId, HttpHeaders headers) {
        CancelServiceImpl.LOGGER.info("[getOrderByIdFromOrder][Get Order][orderId: {}]", orderId);
        HttpHeaders newHeaders = getAuthorizationHeadersFrom(headers);
        HttpEntity requestEntity = new HttpEntity(newHeaders);
        String order_service_url = getServiceUrl("ts-order-service");
        ResponseEntity<Response<Order>> re = restTemplate.exchange(
                order_service_url + "/api/v1/orderservice/order/" + orderId,
                HttpMethod.GET,
                requestEntity,
                new ParameterizedTypeReference<Response<Order>>() {
                });
        return re.getBody();
    }

    private Response<Order> getOrderByIdFromOrderOther(String orderId, HttpHeaders headers) {
        CancelServiceImpl.LOGGER.info("[getOrderByIdFromOrderOther][Get Order][orderId: {}]", orderId);
        HttpHeaders newHeaders = getAuthorizationHeadersFrom(headers);
        HttpEntity requestEntity = new HttpEntity(newHeaders);
        String order_other_service_url = getServiceUrl("ts-order-other-service");
        ResponseEntity<Response<Order>> re = restTemplate.exchange(
                order_other_service_url + "/api/v1/orderOtherService/orderOther/" + orderId,
                HttpMethod.GET,
                requestEntity,
                new ParameterizedTypeReference<Response<Order>>() {
                });
        return re.getBody();
    }

}


// Node: repos/cloned_ms_repos/train-ticket/ts-cancel-service/src/main/java/cancel/service/CancelServiceImpl.java:CancelServiceImpl.<init>
package adminbasic.controller;

import adminbasic.entity.*;
import adminbasic.service.AdminBasicInfoService;
import edu.fudan.common.entity.Config;
import edu.fudan.common.entity.Contacts;
import edu.fudan.common.entity.Station;
import edu.fudan.common.entity.TrainType;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.web.bind.annotation.*;

import static org.springframework.http.ResponseEntity.ok;

/**
 * @author fdse
 */
@RestController
@RequestMapping("/api/v1/adminbasicservice")
public class AdminBasicInfoController {

    @Autowired
    AdminBasicInfoService adminBasicInfoService;
    private static final Logger LOGGER = LoggerFactory.getLogger(AdminBasicInfoController.class);

    @GetMapping(path = "/welcome")
    public String home(@RequestHeader HttpHeaders headers) {
        return "Welcome to [ AdminBasicInfo Service ] !";
    }

    @CrossOrigin(origins = "*")
    @GetMapping(path = "/adminbasic/contacts")
    public HttpEntity getAllContacts(@RequestHeader HttpHeaders headers) {
        AdminBasicInfoController.LOGGER.info("[getAllContacts][Find All Contacts by admin][getAllContacts] ");
        return ok(adminBasicInfoService.getAllContacts(headers));
    }

    @CrossOrigin(origins = "*")
    @DeleteMapping(path = "/adminbasic/contacts/{contactsId}")
    public HttpEntity deleteContacts(@PathVariable String contactsId, @RequestHeader HttpHeaders headers) {
        AdminBasicInfoController.LOGGER.info("[deleteContacts][Delete Contacts by admin][contactsId: {}]", contactsId);
        return ok(adminBasicInfoService.deleteContact(contactsId, headers));
    }

    @CrossOrigin(origins = "*")
    @PutMapping(path = "/adminbasic/contacts")
    public HttpEntity modifyContacts(@RequestBody Contacts mci, @RequestHeader HttpHeaders headers) {
        AdminBasicInfoController.LOGGER.info("[modifyContacts][Modify Contacts by admin][Contacts name:{}]", mci.getName());
        return ok(adminBasicInfoService.modifyContact(mci, headers));
    }

    @CrossOrigin(origins = "*")
    @PostMapping(path = "/adminbasic/contacts")
    public HttpEntity addContacts(@RequestBody Contacts c, @RequestHeader HttpHeaders headers) {
        AdminBasicInfoController.LOGGER.info("[addContacts][Modify Contacts by admin][Contacts name: {}]", c.getName());
        return ok(adminBasicInfoService.addContact(c, headers));
    }

    @CrossOrigin(origins = "*")
    @GetMapping(path = "/adminbasic/stations")
    public HttpEntity getAllStations(@RequestHeader HttpHeaders headers) {
        AdminBasicInfoController.LOGGER.info("[getAllStations][Find All Station by admin][getAllStations]");
        return ok(adminBasicInfoService.getAllStations(headers));
    }

    @CrossOrigin(origins = "*")
    @DeleteMapping(path = "/adminbasic/stations/{id}")
    public HttpEntity deleteStation(@PathVariable String id, @RequestHeader HttpHeaders headers) {
        AdminBasicInfoController.LOGGER.info("[deleteStation][Delete Station by admin][Station id: {}]", id);
        return ok(adminBasicInfoService.deleteStation(id, headers));
    }

    @CrossOrigin(origins = "*")
    @PutMapping(path = "/adminbasic/stations")
    public HttpEntity modifyStation(@RequestBody Station s, @RequestHeader HttpHeaders headers) {
        AdminBasicInfoController.LOGGER.info("[modifyStation][Modify Station by admin][Station id: {}]", s.getId());
        return ok(adminBasicInfoService.modifyStation(s, headers));
    }

    @CrossOrigin(origins = "*")
    @PostMapping(path = "/adminbasic/stations")
    public HttpEntity addStation(@RequestBody Station s, @RequestHeader HttpHeaders headers) {
        AdminBasicInfoController.LOGGER.info("[addStation][Add Station by admin][Station id: {}]", s.getId());
        return ok(adminBasicInfoService.addStation(s, headers));
    }

    @CrossOrigin(origins = "*")
    @GetMapping(path = "/adminbasic/trains")
    public HttpEntity getAllTrains(@RequestHeader HttpHeaders headers) {
        AdminBasicInfoController.LOGGER.info("[getAllTrains][Find All Train by admin][getAllStations]");
        return ok(adminBasicInfoService.getAllTrains(headers));
    }

    @CrossOrigin(origins = "*")
    @DeleteMapping(path = "/adminbasic/trains/{id}")
    public HttpEntity deleteTrain(@PathVariable String id, @RequestHeader HttpHeaders headers) {
        AdminBasicInfoController.LOGGER.info("[deleteTrain][Delete Train by admin][train id: {}]", id);
        return ok(adminBasicInfoService.deleteTrain(id, headers));
    }

    @CrossOrigin(origins = "*")
    @PutMapping(path = "/adminbasic/trains")
    public HttpEntity modifyTrain(@RequestBody TrainType t, @RequestHeader HttpHeaders headers) {
        AdminBasicInfoController.LOGGER.info("[modifyTrain][Modify Train by admin][TrainType id: {}]", t.getId());
        return ok(adminBasicInfoService.modifyTrain(t, headers));
    }

    @CrossOrigin(origins = "*")
    @PostMapping(path = "/adminbasic/trains")
    public HttpEntity addTrain(@RequestBody TrainType t, @RequestHeader HttpHeaders headers) {
        AdminBasicInfoController.LOGGER.info("[addTrain][Add Train by admin][TrainType id: {}]", t.getId());
        return ok(adminBasicInfoService.addTrain(t, headers));
    }

    @CrossOrigin(origins = "*")
    @GetMapping(path = "/adminbasic/configs")
    public HttpEntity getAllConfigs(@RequestHeader HttpHeaders headers) {
        AdminBasicInfoController.LOGGER.info("[getAllConfigs][Find All Config by admin][getAllConfigs]");
        return ok(adminBasicInfoService.getAllConfigs(headers));
    }

    @CrossOrigin(origins = "*")
    @DeleteMapping(path = "/adminbasic/configs/{name}")
    public HttpEntity deleteConfig(@PathVariable String name, @RequestHeader HttpHeaders headers) {
        AdminBasicInfoController.LOGGER.info("[deleteConfig][Delete Config by admin][Config name: {}]", name);
        return ok(adminBasicInfoService.deleteConfig(name, headers));
    }

    @CrossOrigin(origins = "*")
    @PutMapping(path = "/adminbasic/configs")
    public HttpEntity modifyConfig(@RequestBody Config c, @RequestHeader HttpHeaders headers) {
        AdminBasicInfoController.LOGGER.info("[modifyConfig][Modify Config by admin][Config name: {}]", c.getName());
        return ok(adminBasicInfoService.modifyConfig(c, headers));
    }

    @CrossOrigin(origins = "*")
    @PostMapping(path = "/adminbasic/configs")
    public HttpEntity addConfig(@RequestBody Config c, @RequestHeader HttpHeaders headers) {
        AdminBasicInfoController.LOGGER.info("[addConfig][Add Config by admin][Config name: {}]", c.getName());
        return ok(adminBasicInfoService.addConfig(c, headers));
    }

    @CrossOrigin(origins = "*")
    @GetMapping(path = "/adminbasic/prices")
    public HttpEntity getAllPrices(@RequestHeader HttpHeaders headers) {
        AdminBasicInfoController.LOGGER.info("[getAllPrices][Find All Price by admin][getAllPrices]");
        return ok(adminBasicInfoService.getAllPrices(headers));
    }

    @CrossOrigin(origins = "*")
    @DeleteMapping(path = "/adminbasic/prices/{pricesId}")
    public HttpEntity deletePrice(@PathVariable String pricesId, @RequestHeader HttpHeaders headers) {
        AdminBasicInfoController.LOGGER.info("[deletePrice][Delete Price by admin][PriceInfo id: {}]", pricesId);
        return ok(adminBasicInfoService.deletePrice(pricesId, headers));
    }

    @CrossOrigin(origins = "*")
    @PutMapping(path = "/adminbasic/prices")
    public HttpEntity modifyPrice(@RequestBody PriceInfo pi, @RequestHeader HttpHeaders headers) {
        AdminBasicInfoController.LOGGER.info("[modifyPrice][Modify Price by admin][PriceInfo id: {}]", pi.getId());
        return ok(adminBasicInfoService.modifyPrice(pi, headers));
    }

    @CrossOrigin(origins = "*")
    @PostMapping(path = "/adminbasic/prices")
    public HttpEntity addPrice(@RequestBody PriceInfo pi, @RequestHeader HttpHeaders headers) {
        AdminBasicInfoController.LOGGER.info("[addPrice][Add Price by admin[PriceInfo id: {}]", pi.getId());
        return ok(adminBasicInfoService.addPrice(pi, headers));
    }

}


// Node: repos/cloned_ms_repos/train-ticket/ts-admin-basic-info-service/src/main/java/adminbasic/controller/AdminBasicInfoController.java:AdminBasicInfoController.<init>
// Node: getAllContacts
// Node: deleteContacts
// Node: deleteContact
// Node: modifyContacts
// Node: modifyContact
// Node: addContacts
// Node: addContact
// Node: getAllStations
// Node: deleteStation
// Node: modifyStation
// Node: addStation
// Node: getAllTrains
// Node: deleteTrain
// Node: modifyTrain
// Node: addTrain
// Node: getAllConfigs
// Node: deleteConfig
// Node: modifyConfig
// Node: addConfig
// Node: getAllPrices
// Node: deletePrice
// Node: modifyPrice
// Node: addPrice
package adminbasic.service;

import adminbasic.entity.*;
import edu.fudan.common.entity.Config;
import edu.fudan.common.entity.Contacts;
import edu.fudan.common.entity.Station;
import edu.fudan.common.entity.TrainType;
import edu.fudan.common.util.Response;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.cloud.client.discovery.DiscoveryClient;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;


/**
 * @author fdse
 */
@Service
public class AdminBasicInfoServiceImpl implements AdminBasicInfoService {

    @Autowired
    private RestTemplate restTemplate;

    @Autowired
    private DiscoveryClient discoveryClient;

    private static final Logger LOGGER = LoggerFactory.getLogger(AdminBasicInfoServiceImpl.class);

    private String getServiceUrl(String serviceName) {
        return "http://" + serviceName;
    }

    @Override
    public Response getAllContacts(HttpHeaders headers) {
        Response result;
        HttpEntity requestEntity = new HttpEntity(headers);
        String contacts_service_url = getServiceUrl("ts-contacts-service");
        ResponseEntity<Response> re = restTemplate.exchange(
                contacts_service_url + "/api/v1/contactservice/contacts",
                HttpMethod.GET,
                requestEntity,
                Response.class);
        result = re.getBody();

        return result;
    }

    @Override
    public Response deleteContact(String contactsId, HttpHeaders headers) {
        Response result;
        HttpEntity requestEntity = new HttpEntity(headers);
        String contacts_service_url = getServiceUrl("ts-contacts-service");
        ResponseEntity<Response> re = restTemplate.exchange(
                contacts_service_url + "/api/v1/contactservice/contacts/" + contactsId,
                HttpMethod.DELETE,
                requestEntity,
                Response.class);
        result = re.getBody();

        return result;
    }

    @Override
    public Response modifyContact(Contacts mci, HttpHeaders headers) {
        Response result;
        HttpEntity requestEntity = new HttpEntity(mci, headers);
        String contacts_service_url = getServiceUrl("ts-contacts-service");
        ResponseEntity<Response> re = restTemplate.exchange(
                contacts_service_url + "/api/v1/contactservice/contacts",
                HttpMethod.PUT,
                requestEntity,
                Response.class);
        result = re.getBody();

        return result;
    }


    @Override
    public Response addContact(Contacts c, HttpHeaders headers) {
        Response result;
        HttpEntity requestEntity = new HttpEntity(c, headers);
        String contacts_service_url = getServiceUrl("ts-contacts-service");
        ResponseEntity<Response> re = restTemplate.exchange(
                contacts_service_url + "/api/v1/contactservice/contacts/admin",
                HttpMethod.POST,
                requestEntity,
                Response.class);
        result = re.getBody();

        return result;
    }

    @Override
    public Response getAllStations(HttpHeaders headers) {
        HttpEntity requestEntity = new HttpEntity(headers);
        String station_service_url = getServiceUrl("ts-station-service");
        String stations = station_service_url + "/api/v1/stationservice/stations";
        ResponseEntity<Response> re = restTemplate.exchange(
                stations,
                HttpMethod.GET,
                requestEntity,
                Response.class);

        return re.getBody();


    }

    @Override
    public Response addStation(Station s, HttpHeaders headers) {
        Response result;
        HttpEntity requestEntity = new HttpEntity(s, headers);
        String station_service_url = getServiceUrl("ts-station-service");
        String stations = station_service_url + "/api/v1/stationservice/stations";
        ResponseEntity<Response> re = restTemplate.exchange(
                stations,
                HttpMethod.POST,
                requestEntity,
                Response.class);
        result = re.getBody();
        return result;
    }

    @Override
    public Response deleteStation(String id, HttpHeaders headers) {
        Response result;
        HttpEntity requestEntity = new HttpEntity(headers);
        String station_service_url = getServiceUrl("ts-station-service");
        String path = station_service_url + "/api/v1/stationservice/stations/" + id;
        ResponseEntity<Response> re = restTemplate.exchange(
                path,
                HttpMethod.DELETE,
                requestEntity,
                Response.class);
        result = re.getBody();
        return result;
    }

    @Override
    public Response modifyStation(Station s, HttpHeaders headers) {
        Response result;
        HttpEntity requestEntity = new HttpEntity(s, headers);
        String station_service_url = getServiceUrl("ts-station-service");
        String stations = station_service_url + "/api/v1/stationservice/stations";
        ResponseEntity<Response> re = restTemplate.exchange(
                stations,
                HttpMethod.PUT,
                requestEntity,
                Response.class);
        result = re.getBody();

        return result;

    }

    @Override
    public Response getAllTrains(HttpHeaders headers) {
        HttpEntity requestEntity = new HttpEntity(headers);
        String train_service_url = getServiceUrl("ts-train-service");
        String trains = train_service_url + "/api/v1/trainservice/trains";
        ResponseEntity<Response> re = restTemplate.exchange(
                trains,
                HttpMethod.GET,
                requestEntity,
                Response.class);

        return re.getBody();

    }

    @Override
    public Response addTrain(TrainType t, HttpHeaders headers) {
        Response result;
        HttpEntity requestEntity = new HttpEntity(t, headers);
        String train_service_url = getServiceUrl("ts-train-service");
        String trains = train_service_url + "/api/v1/trainservice/trains";
        ResponseEntity<Response> re = restTemplate.exchange(
                trains,
                HttpMethod.POST,
                requestEntity,
                Response.class);
        result = re.getBody();
        return result;

    }

    @Override
    public Response deleteTrain(String id, HttpHeaders headers) {
        Response result;
        HttpEntity requestEntity = new HttpEntity(headers);
        String train_service_url = getServiceUrl("ts-train-service");
        ResponseEntity<Response> re = restTemplate.exchange(
                train_service_url + "/api/v1/trainservice/trains/" + id,
                HttpMethod.DELETE,
                requestEntity,
                Response.class);
        result = re.getBody();
        return result;
    }

    @Override
    public Response modifyTrain(TrainType t, HttpHeaders headers) {
        Response result;
        HttpEntity requestEntity = new HttpEntity(t, headers);
        String train_service_url = getServiceUrl("ts-train-service");
        String trains = train_service_url + "/api/v1/trainservice/trains";
        ResponseEntity<Response> re = restTemplate.exchange(
                trains,
                HttpMethod.PUT,
                requestEntity,
                Response.class);
        result = re.getBody();
        return result;
    }

    @Override
    public Response getAllConfigs(HttpHeaders headers) {
        HttpEntity requestEntity = new HttpEntity(headers);
        String config_service_url = getServiceUrl("ts-config-service");
        String configs = config_service_url + "/api/v1/configservice/configs";
        ResponseEntity<Response> re = restTemplate.exchange(
                configs,
                HttpMethod.GET,
                requestEntity,
                Response.class);

        return re.getBody();
    }

    @Override
    public Response addConfig(Config c, HttpHeaders headers) {
        HttpEntity requestEntity = new HttpEntity(c, headers);
        String config_service_url = getServiceUrl("ts-config-service");
        String configs = config_service_url + "/api/v1/configservice/configs";
        ResponseEntity<Response> re = restTemplate.exchange(
                configs,
                HttpMethod.POST,
                requestEntity,
                Response.class);
        return re.getBody();
    }

    @Override
    public Response deleteConfig(String name, HttpHeaders headers) {
        HttpEntity requestEntity = new HttpEntity(headers);
        String config_service_url = getServiceUrl("ts-config-service");
        ResponseEntity<Response> re = restTemplate.exchange(
                config_service_url + "/api/v1/configservice/configs/" + name,
                HttpMethod.DELETE,
                requestEntity,
                Response.class);
        return re.getBody();
    }

    @Override
    public Response modifyConfig(Config c, HttpHeaders headers) {
        HttpEntity requestEntity = new HttpEntity(c, headers);
        String config_service_url = getServiceUrl("ts-config-service");
        String configs = config_service_url + "/api/v1/configservice/configs";
        ResponseEntity<Response> re = restTemplate.exchange(
                configs,
                HttpMethod.PUT,
                requestEntity,
                Response.class);
        return re.getBody();
    }

    @Override
    public Response getAllPrices(HttpHeaders headers) {
        HttpEntity requestEntity = new HttpEntity(headers);
        String price_service_url = getServiceUrl("ts-price-service");
        String prices = price_service_url + "/api/v1/priceservice/prices";
        ResponseEntity<Response> re = restTemplate.exchange(
                prices,
                HttpMethod.GET,
                requestEntity,
                Response.class);
        return re.getBody();
    }

    @Override
    public Response addPrice(PriceInfo pi, HttpHeaders headers) {
        HttpEntity requestEntity = new HttpEntity(pi, headers);
        String price_service_url = getServiceUrl("ts-price-service");
        String prices = price_service_url + "/api/v1/priceservice/prices";
        ResponseEntity<Response> re = restTemplate.exchange(
                prices,
                HttpMethod.POST,
                requestEntity,
                Response.class);
        return re.getBody();

    }

    @Override
    public Response deletePrice(String pricesId, HttpHeaders headers) {
        HttpEntity requestEntity = new HttpEntity(headers);
        String price_service_url = getServiceUrl("ts-price-service");
        String path = price_service_url + "/api/v1/priceservice/prices/" + pricesId;
        ResponseEntity<Response> re = restTemplate.exchange(
                path,
                HttpMethod.DELETE,
                requestEntity,
                Response.class);

        return re.getBody();
    }

    @Override
    public Response modifyPrice(PriceInfo pi, HttpHeaders headers) {
        HttpEntity requestEntity = new HttpEntity(pi, headers);
        String price_service_url = getServiceUrl("ts-price-service");
        String prices = price_service_url + "/api/v1/priceservice/prices";
        ResponseEntity<Response> re = restTemplate.exchange(
                prices,
                HttpMethod.PUT,
                requestEntity,
                Response.class);
        return re.getBody();
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-admin-basic-info-service/src/main/java/adminbasic/service/AdminBasicInfoServiceImpl.java:AdminBasicInfoServiceImpl.<init>
package adminbasic.service;

import adminbasic.entity.*;
import edu.fudan.common.entity.Config;
import edu.fudan.common.entity.Contacts;
import edu.fudan.common.entity.Station;
import edu.fudan.common.entity.TrainType;
import edu.fudan.common.util.Response;
import org.springframework.http.HttpHeaders;


/**
 * @author fdse
 */
public interface AdminBasicInfoService {

    /**
     * get all contacts
     *
     * @param headers headers
     * @return Response
     */
    Response getAllContacts(  HttpHeaders headers);

    /**
     * add contact with contact information
     *
     * @param c contact information
     * @param headers headers
     * @return Response
     */
    Response addContact(Contacts c, HttpHeaders headers);

    /**
     * delete contact with contact id
     *
     * @param contactsId contact id
     * @param headers headers
     * @return Response
     */
    Response deleteContact( String contactsId, HttpHeaders headers);

    /**
     * modify contact with contact information
     *
     * @param mci contact information
     * @param headers headers
     * @return Response
     */
    Response modifyContact(Contacts mci, HttpHeaders headers);



    /**
     * get all stations
     *
     * @param headers headers
     * @return Response
     */
    Response getAllStations(  HttpHeaders headers);

    /**
     * add station with station information
     *
     * @param s station information
     * @param headers headers
     * @return Response
     */
    Response addStation(Station s, HttpHeaders headers);

    /**
     * delete station with station information
     *
     * @param id station id
     * @param headers headers
     * @return Response
     */
    Response deleteStation(String id, HttpHeaders headers);

    /**
     * modify station with station information
     *
     * @param s station information
     * @param headers headers
     * @return Response
     */
    Response modifyStation(Station s, HttpHeaders headers);



    /**
     * get all trains
     *
     * @param headers headers
     * @return Response
     */
    Response getAllTrains(  HttpHeaders headers);

    /**
     * add train with train type
     *
     * @param t train type
     * @param headers headers
     * @return Response
     */
    Response addTrain(TrainType t, HttpHeaders headers);

    /**
     * delete train with id
     *
     * @param id id
     * @param headers headers
     * @return Response
     */
    Response deleteTrain(String id,   HttpHeaders headers);

    /**
     * modify train with train type
     *
     * @param t train type
     * @param headers headers
     * @return Response
     */
    Response modifyTrain(TrainType t, HttpHeaders headers);



    /**
     * get all configs
     *
     * @param headers headers
     * @return Response
     */
    Response getAllConfigs(  HttpHeaders headers);

    /**
     * add config with config info
     *
     * @param c config info
     * @param headers headers
     * @return Response
     */
    Response addConfig(Config c, HttpHeaders headers);

    /**
     * delete config with name
     *
     * @param name name
     * @param headers headers
     * @return Response
     */
    Response deleteConfig(String name, HttpHeaders headers);

    /**
     * modify config with config info
     *
     * @param c config info
     * @param headers headers
     * @return Response
     */
    Response modifyConfig(Config c, HttpHeaders headers);



    /**
     * get all prices
     *
     * @param headers headers
     * @return Response
     */
    Response getAllPrices(  HttpHeaders headers);

    /**
     * add price with price info
     *
     * @param pi price info
     * @param headers headers
     * @return Response
     */
    Response addPrice(PriceInfo pi, HttpHeaders headers);

    /**
     * delete price with price info
     *
     * @param pricesId price config id
     * @param headers headers
     * @return Response
     */
    Response deletePrice(String pricesId, HttpHeaders headers);

    /**
     * modify price with price info
     *
     * @param pi price info
     * @param headers headers
     * @return Response
     */
    Response modifyPrice(PriceInfo pi, HttpHeaders headers);


}


// Node: repos/cloned_ms_repos/train-ticket/ts-admin-basic-info-service/src/main/java/adminbasic/service/AdminBasicInfoService.java:AdminBasicInfoService.<init>
// Node: testDeleteTrain
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


package trainFood.controller;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.web.bind.annotation.*;
import trainFood.service.TrainFoodService;

import static org.springframework.http.ResponseEntity.ok;

@RestController
@RequestMapping("/api/v1/trainfoodservice")
public class TrainFoodController {

    @Autowired
    TrainFoodService trainFoodService;

    private static final Logger LOGGER = LoggerFactory.getLogger(TrainFoodController.class);

    @GetMapping(path = "/trainfoods/welcome")
    public String home() {
        return "Welcome to [ Train Food Service ] !";
    }

    @CrossOrigin(origins = "*")
    @GetMapping("/trainfoods")
    public HttpEntity getAllTrainFood(@RequestHeader HttpHeaders headers) {
        TrainFoodController.LOGGER.info("[Food Map Service][Get All TrainFoods]");
        return ok(trainFoodService.listTrainFood(headers));
    }

    @CrossOrigin(origins = "*")
    @GetMapping("/trainfoods/{tripId}")
    public HttpEntity getTrainFoodOfTrip(@PathVariable String tripId, @RequestHeader HttpHeaders headers) {
        TrainFoodController.LOGGER.info("[Food Map Service][Get TrainFoods By TripId]");
        return ok(trainFoodService.listTrainFoodByTripId(tripId, headers));
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-train-food-service/src/main/java/trainFood/controller/TrainFoodController.java:TrainFoodController.<init>
// Node: getAllTrainFood
// Node: getTrainFoodOfTrip
package trainFood.service;

import edu.fudan.common.util.Response;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpHeaders;
import org.springframework.stereotype.Service;
import trainFood.entity.*;
import trainFood.repository.TrainFoodRepository;

import java.util.List;

@Service
public class TrainFoodServiceImpl implements TrainFoodService{

    @Autowired
    TrainFoodRepository trainFoodRepository;

    private static final Logger LOGGER = LoggerFactory.getLogger(TrainFoodServiceImpl.class);

    String success = "Success";
    String noContent = "No content";

    @Override
    public TrainFood createTrainFood(TrainFood tf, HttpHeaders headers) {
        TrainFood tfTemp = trainFoodRepository.findByTripId(tf.getTripId());
        if (tfTemp != null) {
            if(tfTemp.getFoodList().equals(tf.getFoodList())){
                TrainFoodServiceImpl.LOGGER.error("[Init TrainFood] Already Exists TripId: {}", tf.getTripId());
            }else{
                tfTemp.setFoodList(tf.getFoodList());
                trainFoodRepository.save(tfTemp);
            }
        } else {
            trainFoodRepository.save(tf);
        }
        return tf;
    }

    @Override
    public Response listTrainFood(HttpHeaders headers) {
        List<TrainFood> trainFoodList = trainFoodRepository.findAll();
        if (trainFoodList != null && !trainFoodList.isEmpty()) {
            return new Response<>(1, success, trainFoodList);
        } else {
            TrainFoodServiceImpl.LOGGER.error("List train food error: {}", noContent);
            return new Response<>(0, noContent, null);
        }
    }

    @Override
    public Response listTrainFoodByTripId(String tripId, HttpHeaders headers) {
        TrainFood tf = trainFoodRepository.findByTripId(tripId);
        if(tf == null){
            return new Response<>(0, noContent, null);
        }else{
            return new Response<>(1, success, tf.getFoodList());
        }
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-train-food-service/src/main/java/trainFood/service/TrainFoodServiceImpl.java:TrainFoodServiceImpl.<init>
package execute.controller;

import execute.serivce.ExecuteService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.web.bind.annotation.*;

import static org.springframework.http.ResponseEntity.ok;

/**
 * @author fdse
 */
@RestController
@RequestMapping("/api/v1/executeservice")
public class ExecuteControlller {

    @Autowired
    private ExecuteService executeService;

    private static final Logger LOGGER = LoggerFactory.getLogger(ExecuteControlller.class);

    @GetMapping(path = "/welcome")
    public String home(@RequestHeader HttpHeaders headers) {
        return "Welcome to [ Execute Service ] !";
    }

    @CrossOrigin(origins = "*")
    @GetMapping(path = "/execute/execute/{orderId}")
    public HttpEntity executeTicket(@PathVariable String orderId, @RequestHeader HttpHeaders headers) {
        ExecuteControlller.LOGGER.info("[executeTicket][Execute][Id: {}]", orderId);
        // null
        return ok(executeService.ticketExecute(orderId, headers));
    }

    @CrossOrigin(origins = "*")
    @GetMapping(path = "/execute/collected/{orderId}")
    public HttpEntity collectTicket(@PathVariable String orderId, @RequestHeader HttpHeaders headers) {
        ExecuteControlller.LOGGER.info("[collectTicket][Collect][Id: {}]", orderId);
        // null
        return ok(executeService.ticketCollect(orderId, headers));
    }

}


// Node: repos/cloned_ms_repos/train-ticket/ts-execute-service/src/main/java/execute/controller/ExecuteControlller.java:ExecuteControlller.<init>
// Node: executeTicket
package execute.serivce;

import edu.fudan.common.util.Response;
import edu.fudan.common.entity.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.cloud.client.ServiceInstance;
import org.springframework.cloud.client.discovery.DiscoveryClient;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.util.List;

/**
 * @author fdse
 */
@Service
public class ExecuteServiceImpl implements ExecuteService {

    @Autowired
    private RestTemplate restTemplate;
    @Autowired
    private DiscoveryClient discoveryClient;

    String orderStatusWrong = "Order Status Wrong";

    private static final Logger LOGGER = LoggerFactory.getLogger(ExecuteServiceImpl.class);
    private String getServiceUrl(String serviceName) {
        return "http://" + serviceName;
    }


    @Override
    public Response ticketExecute(String orderId, HttpHeaders headers) {
        //1.Get order information

        headers = null;
        Response<Order> resultFromOrder = getOrderByIdFromOrder(orderId, headers);
        Order order;
        if (resultFromOrder.getStatus() == 1) {
            order =  resultFromOrder.getData();
            //2.Check if the order can come in
            if (order.getStatus() != OrderStatus.COLLECTED.getCode()) {
                LOGGER.error("[ticketExecute][getOrderByIdFromOrder][ticket execute error: {}][orderId: {}]", orderStatusWrong, orderId);
                return new Response<>(0, orderStatusWrong, null);
            }
            //3.Confirm inbound, request change order information

            Response resultExecute = executeOrder(orderId, OrderStatus.USED.getCode(), headers);
            if (resultExecute.getStatus() == 1) {
                return new Response<>(1, "Success.", null);
            } else {
                LOGGER.error("[ticketExecute][executeOrder][executeOrder error: {}][orderId: {}]", resultExecute.getMsg(), orderId);
                return new Response<>(0, resultExecute.getMsg(), null);
            }
        } else {
            resultFromOrder = getOrderByIdFromOrderOther(orderId, headers);
            if (resultFromOrder.getStatus() == 1) {
                order =   resultFromOrder.getData();
                //2.Check if the order can come in
                if (order.getStatus() != OrderStatus.COLLECTED.getCode()) {
                    LOGGER.error("[ticketExecute][getOrderByIdFromOrderOther][ticket execute error: {}][orderId: {}]", orderStatusWrong, orderId);
                    return new Response<>(0, orderStatusWrong, null);
                }
                //3.Confirm inbound, request change order information

                Response resultExecute = executeOrderOther(orderId, OrderStatus.USED.getCode(), headers);
                if (resultExecute.getStatus() == 1) {
                    return new Response<>(1, "Success", null);
                } else {
                    LOGGER.error("[ticketExecute][executeOrderOther][executeOrderOther error: {}][orderId: {}]", resultExecute.getMsg(), orderId);
                    return new Response<>(0, resultExecute.getMsg(), null);
                }
            } else {
                LOGGER.error("[ticketExecute][getOrderByIdFromOrderOther][ticker execute error: {}][orderId: {}]", "Order Not Found", orderId);
                return new Response<>(0, "Order Not Found", null);
            }
        }
    }

    @Override
    public Response ticketCollect(String orderId, HttpHeaders headers) {
        //1.Get order information

        headers = null;
        Response<Order> resultFromOrder = getOrderByIdFromOrder(orderId, headers);
        Order order;
        if (resultFromOrder.getStatus() == 1) {
            order =  resultFromOrder.getData();
            //2.Check if the order can come in
            if (order.getStatus() != OrderStatus.PAID.getCode() && order.getStatus() != OrderStatus.CHANGE.getCode()) {
                LOGGER.error("[ticketCollect][getOrderByIdFromOrder][ticket collect error: {}][orderId: {}]", orderStatusWrong, orderId);
                return new Response<>(0, orderStatusWrong, null);
            }
            //3.Confirm inbound, request change order information

            Response resultExecute = executeOrder(orderId, OrderStatus.COLLECTED.getCode(), headers);
            if (resultExecute.getStatus() == 1) {
                return new Response<>(1, "Success", null);
            } else {
                LOGGER.error("[ticketCollect][executeOrder][ticket collect error: {}][orderId: {}]", resultExecute.getMsg(), orderId);
                return new Response<>(0, resultExecute.getMsg(), null);
            }
        } else {
            resultFromOrder = getOrderByIdFromOrderOther(orderId, headers);
            if (resultFromOrder.getStatus() == 1) {
                order = (Order) resultFromOrder.getData();
                //2.Check if the order can come in
                if (order.getStatus() != OrderStatus.PAID.getCode() && order.getStatus() != OrderStatus.CHANGE.getCode()) {
                    LOGGER.error("[ticketCollect][getOrderByIdFromOrderOther][ticket collect error: {}][orderId: {}]", orderStatusWrong, orderId);
                    return new Response<>(0, orderStatusWrong, null);
                }
                //3.Confirm inbound, request change order information
                Response resultExecute = executeOrderOther(orderId, OrderStatus.COLLECTED.getCode(), headers);
                if (resultExecute.getStatus() == 1) {
                    return new Response<>(1, "Success.", null);
                } else {
                    LOGGER.error("[ticketCollect][executeOrderOther][ticket collect error: {}][orderId: {}]", resultExecute.getMsg(), orderId);
                    return new Response<>(0, resultExecute.getMsg(), null);
                }
            } else {
                LOGGER.error("[ticketCollect][getOrderByIdFromOrderOther][ticket collect error: {}][orderId: {}]", "Order Not Found", orderId);
                return new Response<>(0, "Order Not Found", null);
            }
        }
    }


    private Response executeOrder(String orderId, int status, HttpHeaders headers) {
        ExecuteServiceImpl.LOGGER.info("[Execute Service][Execute Order] Executing....");
        headers = null;
        HttpEntity requestEntity = new HttpEntity(headers);
        String order_service_url=getServiceUrl("ts-order-service");
        ResponseEntity<Response> re = restTemplate.exchange(
                order_service_url + "/api/v1/orderservice/order/status/" + orderId + "/" + status,
                HttpMethod.GET,
                requestEntity,
                Response.class);
        return re.getBody();
    }


    private Response executeOrderOther(String orderId, int status, HttpHeaders headers) {
        ExecuteServiceImpl.LOGGER.info("[Execute Service][Execute Order] Executing....");
        headers = null;
        HttpEntity requestEntity = new HttpEntity(headers);
        String order_other_service_url=getServiceUrl("ts-order-other-service");
        ResponseEntity<Response> re = restTemplate.exchange(
                order_other_service_url + "/api/v1/orderOtherService/orderOther/status/" + orderId + "/" + status,
                HttpMethod.GET,
                requestEntity,
                Response.class);
        return re.getBody();
    }

    private Response<Order> getOrderByIdFromOrder(String orderId, HttpHeaders headers) {
        ExecuteServiceImpl.LOGGER.info("[Execute Service][Get Order] Getting....");
        headers = null;
        HttpEntity requestEntity = new HttpEntity(headers);
        String order_service_url=getServiceUrl("ts-order-service");
        ResponseEntity<Response<Order>> re = restTemplate.exchange(
                order_service_url + "/api/v1/orderservice/order/" + orderId,
                HttpMethod.GET,
                requestEntity,
                new ParameterizedTypeReference<Response<Order>>() {
                });
        return re.getBody();
    }

    private Response<Order> getOrderByIdFromOrderOther(String orderId, HttpHeaders headers) {
        ExecuteServiceImpl.LOGGER.info("[getOrderByIdFromOrderOther][Execute Service, Get Order]");
        headers = null;
        HttpEntity requestEntity = new HttpEntity(headers);
        String order_other_service_url=getServiceUrl("ts-order-other-service");
        ResponseEntity<Response<Order>> re = restTemplate.exchange(
                order_other_service_url + "/api/v1/orderOtherService/orderOther/" + orderId,
                HttpMethod.GET,
                requestEntity,
                new ParameterizedTypeReference<Response<Order>>() {
                });
        return re.getBody();
    }

}


// Node: repos/cloned_ms_repos/train-ticket/ts-execute-service/src/main/java/execute/serivce/ExecuteServiceImpl.java:ExecuteServiceImpl.<init>
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


// Node: repos/cloned_ms_repos/train-ticket/ts-station-service/src/main/java/fdse/microservice/controller/StationController.java:StationController.<init>
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


// Node: repos/cloned_ms_repos/train-ticket/ts-station-service/src/main/java/fdse/microservice/service/StationServiceImpl.java:StationServiceImpl.<init>
package admintravel.controller;

import admintravel.service.AdminTravelService;
import edu.fudan.common.entity.TravelInfo;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.web.bind.annotation.*;

import static org.springframework.http.ResponseEntity.*;

/**
 * @author fdse
 */
@RestController
@RequestMapping("/api/v1/admintravelservice")
public class AdminTravelController {
    @Autowired
    AdminTravelService adminTravelService;

    private static final Logger logger = LoggerFactory.getLogger(AdminTravelController.class);

    @GetMapping(path = "/welcome")
    public String home(@RequestHeader HttpHeaders headers) {
        return "Welcome to [ AdminTravel Service ] !";
    }

    @CrossOrigin(origins = "*")
    @GetMapping(path = "/admintravel")
    public HttpEntity getAllTravels(@RequestHeader HttpHeaders headers) {
        logger.info("[getAllTravels][Get all travels]");
        return ok(adminTravelService.getAllTravels(headers));
    }

    @PostMapping(value = "/admintravel")
    public HttpEntity addTravel(@RequestBody TravelInfo request, @RequestHeader HttpHeaders headers) {
        logger.info("[addTravel][Add travel][trip id: {}, train type name: {}, form station {} to station {}, login id: {}]",
                request.getTripId(), request.getTrainTypeName(), request.getStartStationName(), request.getStationsName(), request.getLoginId());
        return ok(adminTravelService.addTravel(request, headers));
    }

    @PutMapping(value = "/admintravel")
    public HttpEntity updateTravel(@RequestBody TravelInfo request, @RequestHeader HttpHeaders headers) {
        logger.info("[updateTravel][Update travel][trip id: {}, train type id: {}, form station {} to station {}, login id: {}]",
                request.getTripId(), request.getTrainTypeName(), request.getStartStationName(), request.getStationsName(), request.getLoginId());
        return ok(adminTravelService.updateTravel(request, headers));
    }

    @DeleteMapping(value = "/admintravel/{tripId}")
    public HttpEntity deleteTravel(@PathVariable String tripId, @RequestHeader HttpHeaders headers) {
        logger.info("[deleteTravel][Delete travel][trip id: {}]", tripId);
        return ok(adminTravelService.deleteTravel(tripId, headers));
    }

}


// Node: repos/cloned_ms_repos/train-ticket/ts-admin-travel-service/src/main/java/admintravel/controller/AdminTravelController.java:AdminTravelController.<init>
package admintravel.service;

import edu.fudan.common.entity.AdminTrip;
import edu.fudan.common.entity.Route;
import edu.fudan.common.entity.TrainType;
import edu.fudan.common.entity.TravelInfo;
import edu.fudan.common.util.JsonUtils;
import edu.fudan.common.util.Response;
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

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/**
 * @author fdse
 */
@Service
public class AdminTravelServiceImpl implements AdminTravelService {

    @Autowired
    private RestTemplate restTemplate;
    @Autowired
    private DiscoveryClient discoveryClient;
    private static final Logger LOGGER = LoggerFactory.getLogger(AdminTravelServiceImpl.class);

    private String getServiceUrl(String serviceName) {
        return "http://" + serviceName;
    }

    @Override
    public Response getAllTravels(HttpHeaders headers) {
        Response<ArrayList<AdminTrip>> result;
        ArrayList<AdminTrip> trips = new ArrayList<>();

        AdminTravelServiceImpl.LOGGER.info("[getAllTravels][Get All Travels]");
        HttpEntity requestEntity = new HttpEntity(headers);
        String travel_service_url = getServiceUrl("ts-travel-service");
        ResponseEntity<Response<ArrayList<AdminTrip>>> re = restTemplate.exchange(
                travel_service_url + "/api/v1/travelservice/admin_trip",
                HttpMethod.GET,
                requestEntity,
                new ParameterizedTypeReference<Response<ArrayList<AdminTrip>>>() {
                });
        result = re.getBody();

        if (result.getStatus() == 1) {
            ArrayList<AdminTrip> adminTrips = result.getData();
            AdminTravelServiceImpl.LOGGER.info("[getAllTravels][Get Travel From ts-travel-service successfully!]");
            trips.addAll(adminTrips);
        } else {
            AdminTravelServiceImpl.LOGGER.error("[getAllTravels][receive response][Get Travel From ts-travel-service fail!]");
        }

        HttpEntity requestEntity2 = new HttpEntity(headers);
        String travel2_service_url = getServiceUrl("ts-travel2-service");
        ResponseEntity<Response<ArrayList<AdminTrip>>> re2 = restTemplate.exchange(
                travel2_service_url + "/api/v1/travel2service/admin_trip",
                HttpMethod.GET,
                requestEntity2,
                new ParameterizedTypeReference<Response<ArrayList<AdminTrip>>>() {
                });
        result = re2.getBody();

        if (result.getStatus() == 1) {
            AdminTravelServiceImpl.LOGGER.info("[getAllTravels][Get Travel From ts-travel2-service successfully!]");
            ArrayList<AdminTrip> adminTrips = result.getData();
            trips.addAll(adminTrips);
        } else {
            AdminTravelServiceImpl.LOGGER.error("[getAllTravels][receive response][Get Travel From ts-travel2-service fail!]");
        }
        result.setData(trips);

        return result;
    }

    @Override
    public Response addTravel(TravelInfo request, HttpHeaders headers) {
        // check for travel info
        Response response = checkTravelInfo(request, headers);
        if(response.getStatus() == 0){
            return response;
        }

        Response result;
        String requestUrl;

        String travel_service_url = getServiceUrl("ts-travel-service");
        String travel2_service_url = getServiceUrl("ts-travel2-service");
        String tripId = request.getTripId();
        if (tripId.charAt(0) == 'G' || tripId.charAt(0) == 'D'){
            requestUrl = travel_service_url + "/api/v1/travelservice/trips";
        } else {
            requestUrl = travel2_service_url + "/api/v1/travel2service/trips";
        }
        HttpEntity requestEntity = new HttpEntity(request, headers);
        ResponseEntity<Response> re = restTemplate.exchange(
                requestUrl,
                HttpMethod.POST,
                requestEntity,
                Response.class);
        result = re.getBody();

        if (result.getStatus() == 1) {
            AdminTravelServiceImpl.LOGGER.info("[addTravel][Admin add new travel][success]");
            return new Response<>(1, "[Admin add new travel]", null);
        } else {
            AdminTravelServiceImpl.LOGGER.error("[addTravel][receive response][Admin add new travel failed][trip id: {}]", request.getTripId());
            return new Response<>(0, "Admin add new travel failed", null);
        }
    }

    @Override
    public Response updateTravel(TravelInfo request, HttpHeaders headers) {
        // check for travel info
        Response response = checkTravelInfo(request, headers);
        if(response.getStatus() == 0){
            return response;
        }

        Response result;
        String requestUrl = "";
        String travel_service_url = getServiceUrl("ts-travel-service");
        String travel2_service_url = getServiceUrl("ts-travel2-service");
        String tripId = request.getTripId();
        if (tripId.charAt(0) == 'G' || tripId.charAt(0) == 'D'){
            requestUrl = travel_service_url + "/api/v1/travelservice/trips";
        } else {
            requestUrl = travel2_service_url + "/api/v1/travel2service/trips";
        }
        HttpEntity requestEntity = new HttpEntity(request, headers);
        ResponseEntity<Response> re = restTemplate.exchange(
                requestUrl,
                HttpMethod.PUT,
                requestEntity,
                Response.class);

        result = re.getBody();
        if (result.getStatus() != 1)  {
            AdminTravelServiceImpl.LOGGER.info("[updateTravel][Admin update travel failed]");
            return new Response<>(0, "Admin update travel failed", null);
        }

        AdminTravelServiceImpl.LOGGER.info("[updateTravel][Admin update travel][success]");
        return result;
    }

    @Override
    public Response deleteTravel(String tripId, HttpHeaders headers) {

        Response result;
        String requestUtl = "";
        String travel_service_url = getServiceUrl("ts-travel-service");
        String travel2_service_url = getServiceUrl("ts-travel2-service");
        if (tripId.charAt(0) == 'G' || tripId.charAt(0) == 'D') {
            requestUtl = travel_service_url + "/api/v1/travelservice/trips/" + tripId;
        } else {
            requestUtl = travel2_service_url + "/api/v1/travel2service/trips/" + tripId;
        }
        HttpEntity requestEntity = new HttpEntity(headers);
        ResponseEntity<Response> re = restTemplate.exchange(
                requestUtl,
                HttpMethod.DELETE,
                requestEntity,
                Response.class);

        result = re.getBody();
        if (result.getStatus() != 1) {
            AdminTravelServiceImpl.LOGGER.error("[deleteTravel][receive response][Admin delete travel failed][trip id: {}]", tripId);
            return new Response<>(0, "Admin delete travel failed", null);
        }

        AdminTravelServiceImpl.LOGGER.info("[deleteTravel][Admin delete travel success][trip id: {}]", tripId);
        return result;
    }

    public Response checkTravelInfo(TravelInfo info, HttpHeaders headers) {
        String start = info.getStartStationName();
        String end = info.getTerminalStationName();
        List<String> stations = new ArrayList<>();
        stations.add(start);
        stations.add(end);
        Response response = checkStationsExists(stations, headers);
        if(response.getStatus() ==0) {
            return response;
        }

        TrainType trainType = queryTrainTypeByName(info.getTrainTypeName(), headers);
        if (trainType == null) {
            AdminTravelServiceImpl.LOGGER.warn(
                    "[queryForTravel][traintype doesn't exist][trainTypeName: {}]",
                    info.getTrainTypeName());
            response.setStatus(0);
            response.setMsg("Train type doesn't exist");
            return response;
        }
        String routeId = info.getRouteId();
        Route route = getRouteByRouteId(routeId, headers);
        if (route == null) {
            response.setStatus(0);
            response.setMsg("Route doesn't exist");
            return response;
        }

        // Check the route list for this train. Check that the required start and arrival stations are
        // in the list of stops that are not on the route, and check that the location of the start
        // station is before the stop
        if (!route.getStations().contains(start)
                || !route.getStations().contains(end)
                || (route.getStations().indexOf(start) >= route.getStations().indexOf(end))) {
            response.setStatus(0);
            response.setMsg("Station not correct in Route");
            return response;
        }
        response.setStatus(1);
        return response;
    }

    public Response checkStationsExists(List<String> stationNames, HttpHeaders headers) {
        AdminTravelServiceImpl.LOGGER.info("[checkStationsExists][Check Stations Exists][stationNames: {}]", stationNames);
        HttpEntity requestEntity = new HttpEntity(stationNames, null);
        String station_service_url=getServiceUrl("ts-station-service");
        ResponseEntity<Response> re = restTemplate.exchange(
                station_service_url + "/api/v1/stationservice/stations/idlist",
                HttpMethod.POST,
                requestEntity,
                Response.class);
        Response<Map<String, String>> r = re.getBody();
        if(r.getStatus() == 0) {
            return r;
        }
        Map<String, String> stationMap = r.getData();
        List<String> notExists = new ArrayList<>();
        for(Map.Entry<String, String> s : stationMap.entrySet()){
            if(s.getValue() == null ){
                // station not exist
                notExists.add(s.getKey());
            }
        }
        if(notExists.size() > 0) {
            return new Response<>(0, "some station not exists", notExists);
        }
        return new Response<>(1, "check stations Exist succeed", null);
    }

    public TrainType queryTrainTypeByName(String trainTypeName, HttpHeaders headers) {
        AdminTravelServiceImpl.LOGGER.info("[queryTrainTypeByName][Query Train Type][Train Type name: {}]", trainTypeName);
        HttpEntity requestEntity = new HttpEntity(null);
        String train_service_url=getServiceUrl("ts-train-service");
        ResponseEntity<Response> re = restTemplate.exchange(
                train_service_url + "/api/v1/trainservice/trains/byName/" + trainTypeName,
                HttpMethod.GET,
                requestEntity,
                Response.class);
        Response  response = re.getBody();

        return JsonUtils.conveterObject(response.getData(), TrainType.class);
    }

    private Route getRouteByRouteId(String routeId, HttpHeaders headers) {
        AdminTravelServiceImpl.LOGGER.info("[getRouteByRouteId][Get Route By Id][Route ID：{}]", routeId);
        HttpEntity requestEntity = new HttpEntity(null);
        String route_service_url=getServiceUrl("ts-route-service");
        ResponseEntity<Response> re = restTemplate.exchange(
                route_service_url + "/api/v1/routeservice/routes/" + routeId,
                HttpMethod.GET,
                requestEntity,
                Response.class);
        Response result = re.getBody();
        if ( result.getStatus() == 0) {
            AdminTravelServiceImpl.LOGGER.warn("[getRouteByRouteId][Get Route By Id Failed][Fail msg: {}]", result.getMsg());
            return null;
        } else {
            AdminTravelServiceImpl.LOGGER.info("[getRouteByRouteId][Get Route By Id][Success]");
            return JsonUtils.conveterObject(result.getData(), Route.class);
        }
    }

}


// Node: repos/cloned_ms_repos/train-ticket/ts-admin-travel-service/src/main/java/admintravel/service/AdminTravelServiceImpl.java:AdminTravelServiceImpl.<init>
package travelplan.controller;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.web.bind.annotation.*;
import edu.fudan.common.entity.TripInfo;
import travelplan.entity.TransferTravelInfo;
import travelplan.service.TravelPlanService;

import static org.springframework.http.ResponseEntity.ok;

/**
 * @author fdse
 */
@RestController
@RequestMapping("api/v1/travelplanservice")
public class TravelPlanController {

    @Autowired
    TravelPlanService travelPlanService;

    private static final Logger LOGGER = LoggerFactory.getLogger(TravelPlanController.class);

    @GetMapping(path = "/welcome" )
    public String home() {
        return "Welcome to [ TravelPlan Service ] !";
    }

    @PostMapping(value="/travelPlan/transferResult" )
    public HttpEntity getTransferResult(@RequestBody TransferTravelInfo info, @RequestHeader HttpHeaders headers) {
        TravelPlanController.LOGGER.info("[getTransferSearch][Search Transit][start: {},end: {}]",info.getStartStation(),info.getEndStation());
        return ok(travelPlanService.getTransferSearch(info, headers));
    }

    @PostMapping(value="/travelPlan/cheapest")
    public HttpEntity getByCheapest(@RequestBody TripInfo queryInfo, @RequestHeader HttpHeaders headers) {
        TravelPlanController.LOGGER.info("[getCheapest][Search Cheapest][start: {},end: {},time: {}]",queryInfo.getStartPlace(),queryInfo.getEndPlace(),queryInfo.getDepartureTime());
        return ok(travelPlanService.getCheapest(queryInfo, headers));
    }

    @PostMapping(value="/travelPlan/quickest")
    public HttpEntity getByQuickest(@RequestBody TripInfo queryInfo, @RequestHeader HttpHeaders headers) {
        TravelPlanController.LOGGER.info("[getQuickest][Search Quickest][start: {},end: {},time: {}]",queryInfo.getStartPlace(),queryInfo.getEndPlace(),queryInfo.getDepartureTime());
        return ok(travelPlanService.getQuickest(queryInfo, headers));
    }

    @PostMapping(value="/travelPlan/minStation")
    public HttpEntity getByMinStation(@RequestBody TripInfo queryInfo, @RequestHeader HttpHeaders headers) {
        TravelPlanController.LOGGER.info("[getMinStation][Search Min Station][start: {},end: {},time: {}]",queryInfo.getStartPlace(),queryInfo.getEndPlace(),queryInfo.getDepartureTime());
        return ok(travelPlanService.getMinStation(queryInfo, headers));
    }

}


// Node: repos/cloned_ms_repos/train-ticket/ts-travel-plan-service/src/main/java/travelplan/controller/TravelPlanController.java:TravelPlanController.<init>
package travelplan.service;

import edu.fudan.common.util.JsonUtils;
import edu.fudan.common.util.Response;
import edu.fudan.common.util.StringUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.cloud.client.ServiceInstance;
import org.springframework.cloud.client.discovery.DiscoveryClient;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import edu.fudan.common.entity.*;
import travelplan.entity.TransferTravelInfo;
import travelplan.entity.TransferTravelResult;
import travelplan.entity.TravelAdvanceResultUnit;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Date;
import java.util.List;

/**
 * @author fdse
 */
@Service
public class TravelPlanServiceImpl implements TravelPlanService {

    @Autowired
    private RestTemplate restTemplate;
    @Autowired
    private DiscoveryClient discoveryClient;

    private static final Logger LOGGER = LoggerFactory.getLogger(TravelPlanServiceImpl.class);

    String success = "Success";
    String cannotFind = "Cannot Find";

    private String getServiceUrl(String serviceName) {
        return "http://" + serviceName;
    }

    @Override
    public Response getTransferSearch(TransferTravelInfo info, HttpHeaders headers) {

        TripInfo queryInfoFirstSection = new TripInfo();
        queryInfoFirstSection.setDepartureTime(StringUtils.Date2String(info.getTravelDate()));
        queryInfoFirstSection.setStartPlace(info.getStartStation());
        queryInfoFirstSection.setEndPlace(info.getViaStation());

        List<TripResponse> firstSectionFromHighSpeed;
        List<TripResponse> firstSectionFromNormal;
        firstSectionFromHighSpeed = tripsFromHighSpeed(queryInfoFirstSection, headers);
        firstSectionFromNormal = tripsFromNormal(queryInfoFirstSection, headers);

        TripInfo queryInfoSecondSectoin = new TripInfo();
        queryInfoSecondSectoin.setDepartureTime(StringUtils.Date2String(info.getTravelDate()));
        queryInfoSecondSectoin.setStartPlace(info.getViaStation());
        queryInfoSecondSectoin.setEndPlace(info.getEndStation());

        List<TripResponse> secondSectionFromHighSpeed;
        List<TripResponse> secondSectionFromNormal;
        secondSectionFromHighSpeed = tripsFromHighSpeed(queryInfoSecondSectoin, headers);
        secondSectionFromNormal = tripsFromNormal(queryInfoSecondSectoin, headers);

        List<TripResponse> firstSection = new ArrayList<>();
        firstSection.addAll(firstSectionFromHighSpeed);
        firstSection.addAll(firstSectionFromNormal);

        List<TripResponse> secondSection = new ArrayList<>();
        secondSection.addAll(secondSectionFromHighSpeed);
        secondSection.addAll(secondSectionFromNormal);

        TransferTravelResult result = new TransferTravelResult();
        result.setFirstSectionResult(firstSection);
        result.setSecondSectionResult(secondSection);

        return new Response<>(1, "Success.", result);
    }

    @Override
    public Response getCheapest(TripInfo info, HttpHeaders headers) {
        RoutePlanInfo routePlanInfo = new RoutePlanInfo();
        routePlanInfo.setNum(5);
        routePlanInfo.setStartStation(info.getStartPlace());
        routePlanInfo.setEndStation(info.getEndPlace());
        routePlanInfo.setTravelDate(info.getDepartureTime());
        ArrayList<RoutePlanResultUnit> routePlanResultUnits = getRoutePlanResultCheapest(routePlanInfo, headers);

        if (!routePlanResultUnits.isEmpty()) {
            ArrayList<TravelAdvanceResultUnit> lists = new ArrayList<>();
            for (int i = 0; i < routePlanResultUnits.size(); i++) {
                RoutePlanResultUnit tempUnit = routePlanResultUnits.get(i);
                TravelAdvanceResultUnit newUnit = new TravelAdvanceResultUnit();
                newUnit.setTripId(tempUnit.getTripId());
                newUnit.setEndStation(tempUnit.getEndStation());
                newUnit.setTrainTypeId(tempUnit.getTrainTypeName());
                newUnit.setStartStation(tempUnit.getStartStation());

                List<String> stops = tempUnit.getStopStations();
                newUnit.setStopStations(stops);
                newUnit.setPriceForFirstClassSeat(tempUnit.getPriceForFirstClassSeat());
                newUnit.setPriceForSecondClassSeat(tempUnit.getPriceForSecondClassSeat());
                newUnit.setStartTime(tempUnit.getStartTime());
                newUnit.setEndTime(tempUnit.getEndTime());

                TrainType trainType = queryTrainTypeByName(tempUnit.getTrainTypeName(), headers);
                int firstClassTotalNum = trainType.getConfortClass();
                int secondClassTotalNum = trainType.getEconomyClass();

                int first = getRestTicketNumber(info.getDepartureTime(), tempUnit.getTripId(),
                        tempUnit.getStartStation(), tempUnit.getEndStation(), SeatClass.FIRSTCLASS.getCode(), firstClassTotalNum, tempUnit.getStopStations(), headers);

                int second = getRestTicketNumber(info.getDepartureTime(), tempUnit.getTripId(),
                        tempUnit.getStartStation(), tempUnit.getEndStation(), SeatClass.SECONDCLASS.getCode(), secondClassTotalNum, tempUnit.getStopStations(), headers);
                newUnit.setNumberOfRestTicketFirstClass(first);
                newUnit.setNumberOfRestTicketSecondClass(second);
                lists.add(newUnit);
            }

            return new Response<>(1, success, lists);
        } else {
            TravelPlanServiceImpl.LOGGER.warn("[getCheapest][Get cheapest trip warn][Route Plan Result Units: {}]","No Content");
            return new Response<>(0, cannotFind, null);
        }
    }

    @Override
    public Response getQuickest(TripInfo info, HttpHeaders headers) {
        RoutePlanInfo routePlanInfo = new RoutePlanInfo();
        routePlanInfo.setNum(5);
        routePlanInfo.setStartStation(info.getStartPlace());
        routePlanInfo.setEndStation(info.getEndPlace());
        routePlanInfo.setTravelDate(info.getDepartureTime());
        ArrayList<RoutePlanResultUnit> routePlanResultUnits = getRoutePlanResultQuickest(routePlanInfo, headers);


        if (!routePlanResultUnits.isEmpty()) {

            ArrayList<TravelAdvanceResultUnit> lists = new ArrayList<>();
            for (int i = 0; i < routePlanResultUnits.size(); i++) {
                RoutePlanResultUnit tempUnit = routePlanResultUnits.get(i);
                TravelAdvanceResultUnit newUnit = new TravelAdvanceResultUnit();
                newUnit.setTripId(tempUnit.getTripId());
                newUnit.setTrainTypeId(tempUnit.getTrainTypeName());
                newUnit.setEndStation(tempUnit.getEndStation());
                newUnit.setStartStation(tempUnit.getStartStation());

                List<String> stops = tempUnit.getStopStations();
                newUnit.setStopStations(stops);

                newUnit.setPriceForFirstClassSeat(tempUnit.getPriceForFirstClassSeat());
                newUnit.setPriceForSecondClassSeat(tempUnit.getPriceForSecondClassSeat());
                newUnit.setStartTime(tempUnit.getStartTime());
                newUnit.setEndTime(tempUnit.getEndTime());

                TrainType trainType = queryTrainTypeByName(tempUnit.getTrainTypeName(), headers);
                int firstClassTotalNum = trainType.getConfortClass();
                int secondClassTotalNum = trainType.getEconomyClass();
                int first = getRestTicketNumber(info.getDepartureTime(), tempUnit.getTripId(),
                        tempUnit.getStartStation(), tempUnit.getEndStation(), SeatClass.FIRSTCLASS.getCode(), firstClassTotalNum, tempUnit.getStopStations(), headers);

                int second = getRestTicketNumber(info.getDepartureTime(), tempUnit.getTripId(),
                        tempUnit.getStartStation(), tempUnit.getEndStation(), SeatClass.SECONDCLASS.getCode(), secondClassTotalNum, tempUnit.getStopStations(),headers);
                newUnit.setNumberOfRestTicketFirstClass(first);
                newUnit.setNumberOfRestTicketSecondClass(second);
                lists.add(newUnit);
            }
            return new Response<>(1, success, lists);
        } else {
            TravelPlanServiceImpl.LOGGER.warn("[getQuickest][Get quickest trip warn][Route Plan Result Units: {}]","No Content");
            return new Response<>(0, cannotFind, null);
        }
    }

    @Override
    public Response getMinStation(TripInfo info, HttpHeaders headers) {
        RoutePlanInfo routePlanInfo = new RoutePlanInfo();
        routePlanInfo.setNum(5);
        routePlanInfo.setStartStation(info.getStartPlace());
        routePlanInfo.setEndStation(info.getEndPlace());
        routePlanInfo.setTravelDate(info.getDepartureTime());
        ArrayList<RoutePlanResultUnit> routePlanResultUnits = getRoutePlanResultMinStation(routePlanInfo, headers);

        if (!routePlanResultUnits.isEmpty()) {

            ArrayList<TravelAdvanceResultUnit> lists = new ArrayList<>();
            for (int i = 0; i < routePlanResultUnits.size(); i++) {
                RoutePlanResultUnit tempUnit = routePlanResultUnits.get(i);
                TravelAdvanceResultUnit newUnit = new TravelAdvanceResultUnit();
                newUnit.setTripId(tempUnit.getTripId());
                newUnit.setTrainTypeId(tempUnit.getTrainTypeName());
                newUnit.setStartStation(tempUnit.getStartStation());
                newUnit.setEndStation(tempUnit.getEndStation());

                List<String> stops = tempUnit.getStopStations();
                newUnit.setStopStations(stops);

                newUnit.setPriceForFirstClassSeat(tempUnit.getPriceForFirstClassSeat());
                newUnit.setPriceForSecondClassSeat(tempUnit.getPriceForSecondClassSeat());
                newUnit.setEndTime(tempUnit.getEndTime());
                newUnit.setStartTime(tempUnit.getStartTime());

                TrainType trainType = queryTrainTypeByName(tempUnit.getTrainTypeName(), headers);
                int firstClassTotalNum = trainType.getConfortClass();
                int secondClassTotalNum = trainType.getEconomyClass();

                int first = getRestTicketNumber(info.getDepartureTime(), tempUnit.getTripId(),
                        tempUnit.getStartStation(), tempUnit.getEndStation(), SeatClass.FIRSTCLASS.getCode(), firstClassTotalNum, tempUnit.getStopStations(), headers);

                int second = getRestTicketNumber(info.getDepartureTime(), tempUnit.getTripId(),
                        tempUnit.getStartStation(), tempUnit.getEndStation(), SeatClass.SECONDCLASS.getCode(), secondClassTotalNum, tempUnit.getStopStations(), headers);
                newUnit.setNumberOfRestTicketFirstClass(first);
                newUnit.setNumberOfRestTicketSecondClass(second);
                lists.add(newUnit);
            }
            return new Response<>(1, success, lists);
        } else {
            TravelPlanServiceImpl.LOGGER.warn("[getMinStation][Get min stations trip warn][Route Plan Result Units: {}]","No Content");
            return new Response<>(0, cannotFind, null);
        }
    }

    private int getRestTicketNumber(String travelDate, String trainNumber, String startStationName, String endStationName, int seatType, int totalNum, List<String> stations, HttpHeaders headers) {
        Seat seatRequest = new Seat();

        seatRequest.setDestStation(startStationName);
        seatRequest.setStartStation(endStationName);
        seatRequest.setTrainNumber(trainNumber);
        seatRequest.setTravelDate(travelDate);
        seatRequest.setSeatType(seatType);
        seatRequest.setStations(stations);
        seatRequest.setTotalNum(totalNum);

        TravelPlanServiceImpl.LOGGER.info("[getRestTicketNumber][Seat Request][Seat Request is: {}]", seatRequest.toString());
        HttpEntity requestEntity = new HttpEntity(seatRequest, null);
        String seat_service_url = getServiceUrl("ts-seat-service");
        ResponseEntity<Response<Integer>> re = restTemplate.exchange(
                seat_service_url + "/api/v1/seatservice/seats/left_tickets",
                HttpMethod.POST,
                requestEntity,
                new ParameterizedTypeReference<Response<Integer>>() {
                });

        return re.getBody().getData();
    }

    private ArrayList<RoutePlanResultUnit> getRoutePlanResultCheapest(RoutePlanInfo info, HttpHeaders headers) {
        HttpEntity requestEntity = new HttpEntity(info, null);
        String route_plan_service_url = getServiceUrl("ts-route-plan-service");
        ResponseEntity<Response<ArrayList<RoutePlanResultUnit>>> re = restTemplate.exchange(
                route_plan_service_url + "/api/v1/routeplanservice/routePlan/cheapestRoute",
                HttpMethod.POST,
                requestEntity,
                new ParameterizedTypeReference<Response<ArrayList<RoutePlanResultUnit>>>() {
                });
        return re.getBody().getData();
    }

    private ArrayList<RoutePlanResultUnit> getRoutePlanResultQuickest(RoutePlanInfo info, HttpHeaders headers) {
        HttpEntity requestEntity = new HttpEntity(info, null);
        String route_plan_service_url = getServiceUrl("ts-route-plan-service");
        ResponseEntity<Response<ArrayList<RoutePlanResultUnit>>> re = restTemplate.exchange(
                route_plan_service_url + "/api/v1/routeplanservice/routePlan/quickestRoute",
                HttpMethod.POST,
                requestEntity,
                new ParameterizedTypeReference<Response<ArrayList<RoutePlanResultUnit>>>() {
                });

        return re.getBody().getData();
    }

    private ArrayList<RoutePlanResultUnit> getRoutePlanResultMinStation(RoutePlanInfo info, HttpHeaders headers) {
        HttpEntity requestEntity = new HttpEntity(info, null);
        String route_plan_service_url = getServiceUrl("ts-route-plan-service");
        ResponseEntity<Response<ArrayList<RoutePlanResultUnit>>> re = restTemplate.exchange(
                route_plan_service_url + "/api/v1/routeplanservice/routePlan/minStopStations",
                HttpMethod.POST,
                requestEntity,
                new ParameterizedTypeReference<Response<ArrayList<RoutePlanResultUnit>>>() {
                });
        return re.getBody().getData();
    }

    private List<TripResponse> tripsFromHighSpeed(TripInfo info, HttpHeaders headers) {
        HttpEntity requestEntity = new HttpEntity(info, null);
        String travel_service_url=getServiceUrl("ts-travel-service");
        ResponseEntity<Response<List<TripResponse>>> re = restTemplate.exchange(
                travel_service_url + "/api/v1/travelservice/trips/left",
                HttpMethod.POST,
                requestEntity,
                new ParameterizedTypeReference<Response<List<TripResponse>>>() {
                });
        return re.getBody().getData();
    }

    private ArrayList<TripResponse> tripsFromNormal(TripInfo info, HttpHeaders headers) {

        HttpEntity requestEntity = new HttpEntity(info, null);
        String travel2_service_url=getServiceUrl("ts-travel2-service");
        ResponseEntity<Response<ArrayList<TripResponse>>> re = restTemplate.exchange(
                travel2_service_url + "/api/v1/travel2service/trips/left",
                HttpMethod.POST,
                requestEntity,
                new ParameterizedTypeReference<Response<ArrayList<TripResponse>>>() {
                });

        return re.getBody().getData();
    }

    public TrainType queryTrainTypeByName(String trainTypeName, HttpHeaders headers) {
        HttpEntity requestEntity = new HttpEntity(null);
        String train_service_url=getServiceUrl("ts-train-service");
        ResponseEntity<Response> re = restTemplate.exchange(
                train_service_url + "/api/v1/trainservice/trains/byName/" + trainTypeName,
                HttpMethod.GET,
                requestEntity,
                Response.class);
        Response  response = re.getBody();

        return JsonUtils.conveterObject(response.getData(), TrainType.class);
    }

}


// Node: repos/cloned_ms_repos/train-ticket/ts-travel-plan-service/src/main/java/travelplan/service/TravelPlanServiceImpl.java:TravelPlanServiceImpl.<init>
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


// Node: repos/cloned_ms_repos/train-ticket/ts-user-service/src/main/java/user/controller/UserController.java:UserController.<init>
// Node: getUserByUserName
// Node: getUserByUserId
package user.service.impl;

import edu.fudan.common.util.Response;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.cloud.client.ServiceInstance;
import org.springframework.cloud.client.discovery.DiscoveryClient;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.client.RestTemplate;
import user.dto.AuthDto;
import user.dto.UserDto;
import user.entity.User;
import user.repository.UserRepository;
import user.service.UserService;


import java.util.List;
import java.util.UUID;

/**
 * @author fdse
 */
@Service
public class UserServiceImpl implements UserService {
    private static final Logger LOGGER = LoggerFactory.getLogger(UserServiceImpl.class);

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private DiscoveryClient discoveryClient;

    @Autowired
    private RestTemplate restTemplate;

    private String getServiceUrl(String serviceName) {
        return "http://" + serviceName;
    }

    @Override
    public Response saveUser(UserDto userDto, HttpHeaders headers) {
        LOGGER.info("[saveUser][Save User Name][user name: {}]", userDto.getUserName());
        String userId = userDto.getUserId();
        if (userDto.getUserId() == null) {
            userId = UUID.randomUUID().toString();
        }

        User user = User.builder()
                .userId(userId)
                .userName(userDto.getUserName())
                .password(userDto.getPassword())
                .gender(userDto.getGender())
                .documentType(userDto.getDocumentType())
                .documentNum(userDto.getDocumentNum())
                .email(userDto.getEmail()).build();

        // avoid same user name
        User user1 = userRepository.findByUserName(userDto.getUserName());
        if (user1 == null) {

            createDefaultAuthUser(AuthDto.builder().userId(userId + "")
                    .userName(user.getUserName())
                    .password(user.getPassword()).build());

            User userSaveResult = userRepository.save(user);
            LOGGER.info("[saveUser][Send authorization message to ts-auth-service....]");

            return new Response<>(1, "REGISTER USER SUCCESS", userSaveResult);
        } else {
            UserServiceImpl.LOGGER.error("[saveUser][Save user error][User already exists][UserId: {}]",userDto.getUserId());
            return new Response<>(0, "USER HAS ALREADY EXISTS", null);
        }
    }

    private Response createDefaultAuthUser(AuthDto dto) {
        LOGGER.info("[createDefaultAuthUser][CALL TO AUTH][AuthDto: {}]", dto.toString());
        HttpHeaders headers = new HttpHeaders();
        HttpEntity<AuthDto> entity = new HttpEntity<>(dto, null);
        String auth_service_url = getServiceUrl("ts-auth-service");

        List<ServiceInstance> auth_svcs = discoveryClient.getInstances("ts-auth-service");
        if(auth_svcs.size() >0 ){
            ServiceInstance auth_svc = auth_svcs.get(0);
            LOGGER.info("[createDefaultAuthUser][CALL TO AUTH][auth_svc host: {}][auth_svc port: {}]", auth_svc.getHost(), auth_svc.getPort());
        }else{
            LOGGER.info("[createDefaultAuthUser][CALL TO AUTH][can not get auth url]");
        }

        ResponseEntity<Response<AuthDto>> res  = restTemplate.exchange(auth_service_url + "/api/v1/auth",
                HttpMethod.POST,
                entity,
                new ParameterizedTypeReference<Response<AuthDto>>() {
                });
        return res.getBody();
    }

    @Override
    public Response getAllUsers(HttpHeaders headers) {
        List<User> users = userRepository.findAll();
        if (users != null && !users.isEmpty()) {
            return new Response<>(1, "Success", users);
        }
        UserServiceImpl.LOGGER.warn("[getAllUsers][Get all users warn: {}]","No Content");
        return new Response<>(0, "NO User", null);
    }

    @Override
    public Response findByUserName(String userName, HttpHeaders headers) {
        User user = userRepository.findByUserName(userName);
        if (user != null) {
            return new Response<>(1, "Find User Success", user);
        }
        UserServiceImpl.LOGGER.warn("[findByUserName][Get user by name warn,user is null][UserName: {}]",userName);
        return new Response<>(0, "No User", null);
    }

    @Override
    public Response findByUserId(String userId, HttpHeaders headers) {
        User user = userRepository.findByUserId(userId);
        if (user != null) {
            return new Response<>(1, "Find User Success", user);
        }
        UserServiceImpl.LOGGER.error("[findByUserId][Get user by id error,user is null][UserId: {}]",userId);
        return new Response<>(0, "No User", null);
    }

    @Override
    @Transactional
    public Response deleteUser(String userId, HttpHeaders headers) {
        LOGGER.info("[deleteUser][DELETE USER BY ID][userId: {}]", userId);
        User user = userRepository.findByUserId(userId);
        if (user != null) {
            // first  only admin token can delete success
            deleteUserAuth(userId, headers);
            // second
            userRepository.deleteByUserId(userId);
            LOGGER.info("[deleteUser][DELETE SUCCESS][userId: {}]", userId);
            return new Response<>(1, "DELETE SUCCESS", null);
        } else {
            UserServiceImpl.LOGGER.error("[deleteUser][Delete user error][User not found][UserId: {}]",userId);
            return new Response<>(0, "USER NOT EXISTS", null);
        }
    }

    @Override
    @Transactional
    public Response updateUser(UserDto userDto, HttpHeaders headers) {
        LOGGER.info("[updateUser][UPDATE USER: {}]", userDto.toString());
        User oldUser = userRepository.findByUserId(userDto.getUserId());
        if (oldUser != null) {
            User newUser = User.builder().email(userDto.getEmail())
                    .password(userDto.getPassword())
                    .userId(oldUser.getUserId())
                    .userName(userDto.getUserName())
                    .gender(userDto.getGender())
                    .documentNum(userDto.getDocumentNum())
                    .documentType(userDto.getDocumentType()).build();
            userRepository.deleteByUserId(oldUser.getUserId());
            userRepository.save(newUser);
            return new Response<>(1, "SAVE USER SUCCESS", newUser);
        } else {
            UserServiceImpl.LOGGER.error("[updateUser][Update user error][User not found][UserId: {}]",userDto.getUserId());
            return new Response(0, "USER NOT EXISTS", null);
        }
    }

    public void deleteUserAuth(String userId, HttpHeaders headers) {
        LOGGER.info("[deleteUserAuth][DELETE USER BY ID][userId: {}]", userId);

        HttpHeaders newHeaders = new HttpHeaders();
        String token = headers.getFirst(HttpHeaders.AUTHORIZATION);
        newHeaders.set(HttpHeaders.AUTHORIZATION, token);

        HttpEntity<Response> httpEntity = new HttpEntity<>(newHeaders);

        String auth_service_url = getServiceUrl("ts-auth-service");
        String AUTH_SERVICE_URI = auth_service_url + "/api/v1";
        restTemplate.exchange(AUTH_SERVICE_URI + "/users/" + userId,
                HttpMethod.DELETE,
                httpEntity,
                Response.class);
        LOGGER.info("[deleteUserAuth][DELETE USER AUTH SUCCESS][userId: {}]", userId);
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-user-service/src/main/java/user/service/impl/UserServiceImpl.java:UserServiceImpl.<init>
package seat.controller;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.web.bind.annotation.*;
import edu.fudan.common.entity.Seat;
import seat.service.SeatService;

import static org.springframework.http.ResponseEntity.ok;

/**
 * @author fdse
 */
@RestController
@RequestMapping("/api/v1/seatservice")
public class SeatController {

    @Autowired
    private SeatService seatService;

    private static final Logger LOGGER = LoggerFactory.getLogger(SeatController.class);

    @GetMapping(path = "/welcome")
    public String home() {
        return "Welcome to [ Seat Service ] !";
    }

    /**
     * Assign seats by seat request
     *
     * @param seatRequest seat request
     * @param headers headers
     * @return HttpEntity
     */
    @CrossOrigin(origins = "*")
    @PostMapping(value = "/seats")
    public HttpEntity create(@RequestBody Seat seatRequest, @RequestHeader HttpHeaders headers) {
        SeatController.LOGGER.info("[distributeSeat][Create seat][TravelDate: {},TrainNumber: {},SeatType: {}]",seatRequest.getTravelDate(),seatRequest.getTrainNumber(),seatRequest.getSeatType());
        return ok(seatService.distributeSeat(seatRequest, headers));
    }

    /**
     * get left ticket of interval
     * query specific interval residual
     *
     * @param seatRequest seat request
     * @param headers headers
     * @return HttpEntity
     */
    @CrossOrigin(origins = "*")
    @PostMapping(value = "/seats/left_tickets")
    public HttpEntity getLeftTicketOfInterval(@RequestBody Seat seatRequest, @RequestHeader HttpHeaders headers) {
        // int
        SeatController.LOGGER.info("[getLeftTicketOfInterval][Get left ticket of interval][TravelDate: {},TrainNumber: {},SeatType: {}]",seatRequest.getTravelDate(),seatRequest.getTrainNumber(),seatRequest.getSeatType());
        return ok(seatService.getLeftTicketOfInterval(seatRequest, headers));
    }

}


// Node: repos/cloned_ms_repos/train-ticket/ts-seat-service/src/main/java/seat/controller/SeatController.java:SeatController.<init>
package seat.service;

import edu.fudan.common.util.Response;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.cloud.client.ServiceInstance;
import org.springframework.cloud.client.discovery.DiscoveryClient;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import edu.fudan.common.entity.*;

import java.util.List;
import java.util.Random;
import java.util.Set;

/**
 * @author fdse
 */
@Service
public class SeatServiceImpl implements SeatService {
    @Autowired
    RestTemplate restTemplate;

    @Autowired
    private DiscoveryClient discoveryClient;

    private static final Logger LOGGER = LoggerFactory.getLogger(SeatServiceImpl.class);

    private String getServiceUrl(String serviceName) {
        return "http://" + serviceName;
    }

    @Override
    public Response distributeSeat(Seat seatRequest, HttpHeaders headers) {
        Response<Route> routeResult;

        LeftTicketInfo leftTicketInfo;
        TrainType trainTypeResult = null;
        ResponseEntity<Response<Route>> re;
        ResponseEntity<Response<TrainType>> re2;
        ResponseEntity<Response<LeftTicketInfo>> re3;

        //Distinguish G\D from other trains
        String trainNumber = seatRequest.getTrainNumber();

        if (trainNumber.startsWith("G") || trainNumber.startsWith("D")) {
            SeatServiceImpl.LOGGER.info("[distributeSeat][TrainNumber start][G or D]");

            HttpEntity requestEntity = new HttpEntity(null);
            //Call the microservice to query for residual Ticket information: the set of the Ticket sold for the specified seat type
            requestEntity = new HttpEntity(seatRequest, null);
            String order_service_url=getServiceUrl("ts-order-service");
            re3 = restTemplate.exchange(
                    order_service_url + "/api/v1/orderservice/order/tickets",
                    HttpMethod.POST,
                    requestEntity,
                    new ParameterizedTypeReference<Response<LeftTicketInfo>>() {
                    });
            SeatServiceImpl.LOGGER.info("[distributeSeat][Left ticket info][info is : {}]", re3.getBody().toString());
            leftTicketInfo = re3.getBody().getData();
        } else {
            SeatServiceImpl.LOGGER.info("[distributeSeat][TrainNumber start][Other Capital Except D and G]");
            //Call the microservice to query for residual Ticket information: the set of the Ticket sold for the specified seat type
            HttpEntity requestEntity = new HttpEntity(seatRequest, null);
            String order_other_service_url=getServiceUrl("ts-order-other-service");
            re3 = restTemplate.exchange(
                    order_other_service_url + "/api/v1/orderOtherService/orderOther/tickets",
                    HttpMethod.POST,
                    requestEntity,
                    new ParameterizedTypeReference<Response<LeftTicketInfo>>() {
                    });
            SeatServiceImpl.LOGGER.info("[distributeSeat][Left ticket info][info is : {}]", re3.getBody().toString());
            leftTicketInfo = re3.getBody().getData();
        }

        //Assign seats
        List<String> stationList = seatRequest.getStations();

        int seatTotalNum = seatRequest.getTotalNum();
        String startStation = seatRequest.getStartStation();
        Ticket ticket = new Ticket();
        ticket.setStartStation(startStation);
        ticket.setDestStation(seatRequest.getDestStation());

        //Assign new tickets
        Random rand = new Random();
        int range = seatTotalNum;
        int seat = rand.nextInt(range) + 1;

        if(leftTicketInfo != null) {
            Set<Ticket> soldTickets = leftTicketInfo.getSoldTickets();
            //Give priority to tickets already sold
            for (Ticket soldTicket : soldTickets) {
                String soldTicketDestStation = soldTicket.getDestStation();
                //Tickets can be allocated if the sold ticket's end station before the start station of the request
                if (stationList.indexOf(soldTicketDestStation) < stationList.indexOf(startStation)) {
                    ticket.setSeatNo(soldTicket.getSeatNo());
                    SeatServiceImpl.LOGGER.info("[distributeSeat][Assign new tickets][Use the previous distributed seat number][seat number:{}]", soldTicket.getSeatNo());
                    return new Response<>(1, "Use the previous distributed seat number!", ticket);
                }
            }
            while (isContained(soldTickets, seat)) {
                seat = rand.nextInt(range) + 1;
            }
        }
        ticket.setSeatNo(seat);
        SeatServiceImpl.LOGGER.info("[distributeSeat][Assign new tickets][Use a new seat number][seat number:{}]", seat);
        return new Response<>(1, "Use a new seat number!", ticket);
    }

    private boolean isContained(Set<Ticket> soldTickets, int seat) {
        //Check that the seat number has been used
        boolean result = false;
        for (Ticket soldTicket : soldTickets) {
            if (soldTicket.getSeatNo() == seat) {
                return true;
            }
        }
        return result;
    }

    @Override
    public Response getLeftTicketOfInterval(Seat seatRequest, HttpHeaders headers) {
        int numOfLeftTicket = 0;
        LeftTicketInfo leftTicketInfo;
        ResponseEntity<Response<LeftTicketInfo>> re3;

        //Distinguish G\D from other trains
        String trainNumber = seatRequest.getTrainNumber();
        SeatServiceImpl.LOGGER.info("[getLeftTicketOfInterval][Seat request][request:{}]", seatRequest.toString());
        if (trainNumber.startsWith("G") || trainNumber.startsWith("D")) {
            SeatServiceImpl.LOGGER.info("[getLeftTicketOfInterval][TrainNumber start with G|D][trainNumber:{}]", trainNumber);

            //Call the micro service to query all the station information for the trains
            HttpEntity requestEntity = new HttpEntity(seatRequest, null);
            String order_service_url=getServiceUrl("ts-order-service");
            re3 = restTemplate.exchange(
                    order_service_url + "/api/v1/orderservice/order/tickets",
                    HttpMethod.POST,
                    requestEntity,
                    new ParameterizedTypeReference<Response<LeftTicketInfo>>() {
                    });

            SeatServiceImpl.LOGGER.info("[getLeftTicketOfInterval][Get Order tickets result][result is {}]", re3);
            leftTicketInfo = re3.getBody().getData();
        } else {
            SeatServiceImpl.LOGGER.info("[getLeftTicketOfInterval][TrainNumber start with other capital][trainNumber:{}]", trainNumber);
            //Call the micro service to query all the station information for the trains
            HttpEntity requestEntity = new HttpEntity(null);
            //Call the micro service to query for residual Ticket information: the set of the Ticket sold for the specified seat type
            requestEntity = new HttpEntity(seatRequest, null);
            String order_other_service_url=getServiceUrl("ts-order-other-service");
            re3 = restTemplate.exchange(
                    order_other_service_url + "/api/v1/orderOtherService/orderOther/tickets",
                    HttpMethod.POST,
                    requestEntity,
                    new ParameterizedTypeReference<Response<LeftTicketInfo>>() {
                    });
            SeatServiceImpl.LOGGER.info("[getLeftTicketOfInterval][Get Order tickets result][result is {}]", re3);
            leftTicketInfo = re3.getBody().getData();
        }

        //Counting the seats remaining in certain sections
        List<String> stationList = seatRequest.getStations();
        int seatTotalNum = seatRequest.getTotalNum();
        int solidTicketSize = 0;
        if (leftTicketInfo != null) {
            String startStation = seatRequest.getStartStation();
            Set<Ticket> soldTickets = leftTicketInfo.getSoldTickets();
            solidTicketSize = soldTickets.size();
            //To find out if tickets already sold are available
            for (Ticket soldTicket : soldTickets) {
                String soldTicketDestStation = soldTicket.getDestStation();
                //Tickets can be allocated if the sold ticket's end station before the start station of the request
                if (stationList.indexOf(soldTicketDestStation) < stationList.indexOf(startStation)) {
                    SeatServiceImpl.LOGGER.info("[getLeftTicketOfInterval][Ticket available or sold][The previous distributed seat number is usable][{}]", soldTicket.getSeatNo());
                    numOfLeftTicket++;
                }
            }
        }
        //Count the unsold tickets

        double direstPart = getDirectProportion(headers);

        if (stationList.get(0).equals(seatRequest.getStartStation()) &&
                stationList.get(stationList.size() - 1).equals(seatRequest.getDestStation())) {
            //do nothing
        } else {
            direstPart = 1.0 - direstPart;
        }

        int unusedNum = (int) (seatTotalNum * direstPart) - solidTicketSize;
        numOfLeftTicket += unusedNum;

        return new Response<>(1, "Get Left Ticket of Internal Success", numOfLeftTicket);
    }

    private double getDirectProportion(HttpHeaders headers) {

        String configName = "DirectTicketAllocationProportion";
        HttpEntity requestEntity = new HttpEntity(null);
        String config_service_url = getServiceUrl("ts-config-service");
        ResponseEntity<Response<Config>> re = restTemplate.exchange(
                config_service_url + "/api/v1/configservice/configs/" + configName,
                HttpMethod.GET,
                requestEntity,
                new ParameterizedTypeReference<Response<Config>>() {
                });
        Response<Config> configValue = re.getBody();
        SeatServiceImpl.LOGGER.info("[getDirectProportion][Configs is : {}]", configValue.getData().toString());
        return Double.parseDouble(configValue.getData().getValue());
    }
}

// Node: repos/cloned_ms_repos/train-ticket/ts-seat-service/src/main/java/seat/service/SeatServiceImpl.java:SeatServiceImpl.<init>
package security.controller;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.web.bind.annotation.*;
import security.entity.*;
import security.service.SecurityService;

import static org.springframework.http.ResponseEntity.ok;

/**
 * @author fdse
 */
@RestController
@RequestMapping("/api/v1/securityservice")
public class SecurityController {

    @Autowired
    private SecurityService securityService;

    private static final Logger LOGGER = LoggerFactory.getLogger(SecurityController.class);

    @GetMapping(value = "/welcome")
    public String home(@RequestHeader HttpHeaders headers) {
        return "welcome to [Security Service]";
    }

    @CrossOrigin(origins = "*")
    @GetMapping(path = "/securityConfigs")
    public HttpEntity findAllSecurityConfig(@RequestHeader HttpHeaders headers) {
        SecurityController.LOGGER.info("[findAllSecurityConfig][Find All]");
        return ok(securityService.findAllSecurityConfig(headers));
    }

    @CrossOrigin(origins = "*")
    @PostMapping(path = "/securityConfigs")
    public HttpEntity create(@RequestBody SecurityConfig info, @RequestHeader HttpHeaders headers) {
        SecurityController.LOGGER.info("[addNewSecurityConfig][Create][SecurityConfig Name: {}]", info.getName());
        return ok(securityService.addNewSecurityConfig(info, headers));
    }

    @CrossOrigin(origins = "*")
    @PutMapping(path = "/securityConfigs")
    public HttpEntity update(@RequestBody SecurityConfig info, @RequestHeader HttpHeaders headers) {
        SecurityController.LOGGER.info("[modifySecurityConfig][Update][SecurityConfig Name: {}]", info.getName());
        return ok(securityService.modifySecurityConfig(info, headers));
    }

    @CrossOrigin(origins = "*")
    @DeleteMapping(path = "/securityConfigs/{id}")
    public HttpEntity delete(@PathVariable String id, @RequestHeader HttpHeaders headers) {
        SecurityController.LOGGER.info("[deleteSecurityConfig][Delete][SecurityConfig Id: {}]", id);
        return ok(securityService.deleteSecurityConfig(id, headers));
    }

    @CrossOrigin(origins = "*")
    @GetMapping(path = "/securityConfigs/{accountId}")
    public HttpEntity check(@PathVariable String accountId, @RequestHeader HttpHeaders headers) {
        SecurityController.LOGGER.info("[check][Check Security][Check Account Id: {}]", accountId);
        return ok(securityService.check(accountId, headers));
    }

}


// Node: repos/cloned_ms_repos/train-ticket/ts-security-service/src/main/java/security/controller/SecurityController.java:SecurityController.<init>
// Node: findAllSecurityConfig
// Node: modifySecurityConfig
// Node: check
package security.service;

import edu.fudan.common.util.Response;
import org.springframework.http.HttpHeaders;
import security.entity.*;

/**
 * @author fdse
 */
public interface SecurityService {

    Response findAllSecurityConfig(HttpHeaders headers);

    Response addNewSecurityConfig(SecurityConfig info, HttpHeaders headers);

    Response modifySecurityConfig(SecurityConfig info, HttpHeaders headers);

    Response deleteSecurityConfig(String id, HttpHeaders headers);

    Response check(String accountId, HttpHeaders headers);

}


// Node: repos/cloned_ms_repos/train-ticket/ts-security-service/src/main/java/security/service/SecurityService.java:SecurityService.<init>
package security.service;

import edu.fudan.common.entity.OrderSecurity;
import edu.fudan.common.util.Response;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.cloud.client.ServiceInstance;
import org.springframework.cloud.client.discovery.DiscoveryClient;
import org.springframework.cloud.client.ServiceInstance;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.client.RestTemplate;
import security.entity.SecurityConfig;
import security.repository.SecurityRepository;


import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.UUID;

/**
 * @author fdse
 */
@Service
public class SecurityServiceImpl implements SecurityService {

    @Autowired
    private SecurityRepository securityRepository;

    @Autowired
    RestTemplate restTemplate;

    @Autowired
    private DiscoveryClient discoveryClient;

    private static final Logger LOGGER = LoggerFactory.getLogger(SecurityServiceImpl.class);

    private String getServiceUrl(String serviceName) {
        return "http://" + serviceName;
    }

    String success = "Success";

    @Override
    public Response findAllSecurityConfig(HttpHeaders headers) {
        ArrayList<SecurityConfig> securityConfigs = securityRepository.findAll();
        if (securityConfigs != null && !securityConfigs.isEmpty()) {
            return new Response<>(1, success, securityConfigs);
        }
        SecurityServiceImpl.LOGGER.warn("[findAllSecurityConfig][Find all security config warn][{}]","No content");
        return new Response<>(0, "No Content", null);
    }

    @Override
    public Response addNewSecurityConfig(SecurityConfig info, HttpHeaders headers) {
        SecurityConfig sc = securityRepository.findByName(info.getName());
        if (sc != null) {
            SecurityServiceImpl.LOGGER.warn("[addNewSecurityConfig][Add new Security config warn][Security config already exist][SecurityConfigId: {},Name: {}]",sc.getId(),info.getName());
            return new Response<>(0, "Security Config Already Exist", null);
        } else {
            SecurityConfig config = new SecurityConfig();
            config.setId(UUID.randomUUID().toString());
            config.setName(info.getName());
            config.setValue(info.getValue());
            config.setDescription(info.getDescription());
            securityRepository.save(config);
            return new Response<>(1, success, config);
        }
    }

    @Override
    public Response modifySecurityConfig(SecurityConfig info, HttpHeaders headers) {
        SecurityConfig sc = securityRepository.findById(info.getId()).orElse(null);
        if (sc == null) {
            SecurityServiceImpl.LOGGER.error("[modifySecurityConfig][Modify Security config error][Security config not found][SecurityConfigId: {},Name: {}]",info.getId(),info.getName());
            return new Response<>(0, "Security Config Not Exist", null);
        } else {
            sc.setName(info.getName());
            sc.setValue(info.getValue());
            sc.setDescription(info.getDescription());
            securityRepository.save(sc);
            return new Response<>(1, success, sc);
        }
    }

    @Transactional
    @Override
    public Response deleteSecurityConfig(String id, HttpHeaders headers) {
        securityRepository.deleteById(id);
        SecurityConfig sc = securityRepository.findById(id).orElse(null);
        if (sc == null) {
            return new Response<>(1, success, id);
        } else {
            SecurityServiceImpl.LOGGER.error("[deleteSecurityConfig][Delete Security config error][Reason not clear][SecurityConfigId: {}]",id);
            return new Response<>(0, "Reason Not clear", id);
        }
    }

    @Override
    public Response check(String accountId, HttpHeaders headers) {
        //1.Get the orders in the past one hour and the total effective votes
        SecurityServiceImpl.LOGGER.debug("[check][Get Order Num Info]");
        OrderSecurity orderResult = getSecurityOrderInfoFromOrder(new Date(), accountId, headers);
        OrderSecurity orderOtherResult = getSecurityOrderOtherInfoFromOrder(new Date(), accountId, headers);
        int orderInOneHour = orderOtherResult.getOrderNumInLastOneHour() + orderResult.getOrderNumInLastOneHour();
        int totalValidOrder = orderOtherResult.getOrderNumOfValidOrder() + orderResult.getOrderNumOfValidOrder();
        //2. get critical configuration information
        SecurityServiceImpl.LOGGER.debug("[check][Get Security Config Info]");
        SecurityConfig configMaxInHour = securityRepository.findByName("max_order_1_hour");
        SecurityConfig configMaxNotUse = securityRepository.findByName("max_order_not_use");
        SecurityServiceImpl.LOGGER.info("[check][Max][Max In One Hour: {}  Max Not Use: {}]", configMaxInHour.getValue(), configMaxNotUse.getValue());
        int oneHourLine = Integer.parseInt(configMaxInHour.getValue());
        int totalValidLine = Integer.parseInt(configMaxNotUse.getValue());
        if (orderInOneHour > oneHourLine || totalValidOrder > totalValidLine) {
            SecurityServiceImpl.LOGGER.warn("[check][Check Security config warn][Too much order in last one hour or too much valid order][AccountId: {}]",accountId);
            return new Response<>(0, "Too much order in last one hour or too much valid order", accountId);
        } else {
            return new Response<>(1, "Success.r", accountId);
        }
    }

    private OrderSecurity getSecurityOrderInfoFromOrder(Date checkDate, String accountId, HttpHeaders headers) {
        HttpEntity requestEntity = new HttpEntity(null);
        String order_service_url = getServiceUrl("ts-order-service");
        ResponseEntity<Response<OrderSecurity>> re = restTemplate.exchange(
                order_service_url + "/api/v1/orderservice/order/security/" + checkDate + "/" + accountId,
                HttpMethod.GET,
                requestEntity,
                new ParameterizedTypeReference<Response<OrderSecurity>>() {
                });
        Response<OrderSecurity> response = re.getBody();
        OrderSecurity result =  response.getData();
        SecurityServiceImpl.LOGGER.info("[getSecurityOrderInfoFromOrder][Get Order Info For Security][Last One Hour: {}  Total Valid Order: {}]", result.getOrderNumInLastOneHour(), result.getOrderNumOfValidOrder());
        return result;
    }

    private OrderSecurity getSecurityOrderOtherInfoFromOrder(Date checkDate, String accountId, HttpHeaders headers) {
        HttpEntity requestEntity = new HttpEntity(null);
        String order_other_service_url = getServiceUrl("ts-order-other-service");
        ResponseEntity<Response<OrderSecurity>> re = restTemplate.exchange(
                order_other_service_url + "/api/v1/orderOtherService/orderOther/security/" + checkDate + "/" + accountId,
                HttpMethod.GET,
                requestEntity,
                new ParameterizedTypeReference<Response<OrderSecurity>>() {
                });
        Response<OrderSecurity> response = re.getBody();
        OrderSecurity result =  response.getData();
        SecurityServiceImpl.LOGGER.info("[getSecurityOrderOtherInfoFromOrder][Get Order Other Info For Security][Last One Hour: {}  Total Valid Order: {}]", result.getOrderNumInLastOneHour(), result.getOrderNumOfValidOrder());
        return result;
    }

}


// Node: repos/cloned_ms_repos/train-ticket/ts-security-service/src/main/java/security/service/SecurityServiceImpl.java:SecurityServiceImpl.<init>
package food_delivery.controller;


import edu.fudan.common.util.Response;
import food_delivery.entity.DeliveryInfo;
import food_delivery.entity.FoodDeliveryOrder;
import food_delivery.entity.SeatInfo;
import food_delivery.entity.TripOrderInfo;
import food_delivery.service.FoodDeliveryService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.web.bind.annotation.*;

import static org.springframework.http.ResponseEntity.ok;

@RestController
@RequestMapping("/api/v1/fooddeliveryservice")
public class FoodDeliveryController {

    @Autowired
    private FoodDeliveryService foodDeliveryService;

    private static final Logger LOGGER = LoggerFactory.getLogger(FoodDeliveryController.class);

    @GetMapping(path = "/welcome")
    public String home() {
        return "Welcome to [ food delivery service ] !";
    }


    @PostMapping("/orders")
    public HttpEntity createFoodDeliveryOrder(@RequestBody FoodDeliveryOrder fd, @RequestHeader HttpHeaders headers) {
        LOGGER.info("[Food Delivery Service][Create Food Delivery Order]");
        return ok(foodDeliveryService.createFoodDeliveryOrder(fd, headers));
    }

    @DeleteMapping("/orders/d/{orderId}")
    public HttpEntity deleteFoodDeliveryOrder(@PathVariable String orderId, @RequestHeader HttpHeaders headers) {
        LOGGER.info("[Food Delivery Service][Delete Food Delivery Order]");
        return ok(foodDeliveryService.deleteFoodDeliveryOrder(orderId, headers));
    }

    @GetMapping("/orders/{orderId}")
    public HttpEntity getFoodDeliveryOrderById(@PathVariable String orderId, @RequestHeader HttpHeaders headers) {
        LOGGER.info("[Food Delivery Service][Get Food Delivery Order By Id]");
        return ok(foodDeliveryService.getFoodDeliveryOrderById(orderId, headers));
    }

    @GetMapping("/orders/all")
    public HttpEntity getAllFoodDeliveryOrders(@RequestHeader HttpHeaders headers) {
        LOGGER.info("[Food Delivery Service][Get All Food Delivery Orders]");
        return ok(foodDeliveryService.getAllFoodDeliveryOrders(headers));
    }

    @GetMapping("/orders/store/{storeId}")
    public HttpEntity getFoodDeliveryOrderByStoreId(@PathVariable String storeId, @RequestHeader HttpHeaders headers) {
        LOGGER.info("[Food Delivery Service][Get Food Delivery Order By StoreId]");
        return ok(foodDeliveryService.getFoodDeliveryOrderByStoreId(storeId, headers));
    }

    @PutMapping("/orders/tripid")
    public HttpEntity updateTripId(@RequestBody TripOrderInfo tripOrderInfo, @RequestHeader HttpHeaders headers) {
        LOGGER.info("[Food Delivery Service][Update Trip Id]");
        return ok(foodDeliveryService.updateTripId(tripOrderInfo, headers));
    }

    @PutMapping("/orders/seatno")
    public HttpEntity updateSeatNo(@RequestBody SeatInfo seatInfo, @RequestHeader HttpHeaders headers) {
        LOGGER.info("[Food Delivery Service][Update Seat No]");
        return ok(foodDeliveryService.updateSeatNo(seatInfo, headers));
    }

    @PutMapping("/orders/dtime")
    public HttpEntity updateDeliveryTime(@RequestBody DeliveryInfo deliveryInfo, @RequestHeader HttpHeaders headers) {
        LOGGER.info("[Food Delivery Service][Update Delivery Time]");
        return ok(foodDeliveryService.updateDeliveryTime(deliveryInfo, headers));
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-food-delivery-service/src/main/java/food_delivery/controller/FoodDeliveryController.java:FoodDeliveryController.<init>
// Node: createFoodDeliveryOrder
// Node: deleteFoodDeliveryOrder
// Node: getFoodDeliveryOrderById
// Node: getAllFoodDeliveryOrders
// Node: getFoodDeliveryOrderByStoreId
// Node: updateTripId
// Node: updateSeatNo
// Node: updateDeliveryTime
package food_delivery.repository;

import food_delivery.entity.FoodDeliveryOrder;
import org.springframework.data.repository.CrudRepository;

import java.util.List;

public interface FoodDeliveryOrderRepository extends CrudRepository<FoodDeliveryOrder, String> {

    List<FoodDeliveryOrder> findByStationFoodStoreId(String stationFoodStoreId);

    @Override
    List<FoodDeliveryOrder> findAll();

}


// Node: repos/cloned_ms_repos/train-ticket/ts-food-delivery-service/src/main/java/food_delivery/repository/FoodDeliveryOrderRepository.java:FoodDeliveryOrderRepository.<init>
// Node: findByStationFoodStoreId
package food_delivery.service;


import edu.fudan.common.util.Response;
import food_delivery.entity.*;
import edu.fudan.common.entity.*;
import food_delivery.repository.FoodDeliveryOrderRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.cloud.client.ServiceInstance;
import org.springframework.cloud.client.discovery.DiscoveryClient;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Service
public class FoodDeliveryServiceImpl implements FoodDeliveryService {

    @Autowired
    FoodDeliveryOrderRepository foodDeliveryOrderRepository;

    private static final Logger LOGGER = LoggerFactory.getLogger(FoodDeliveryServiceImpl.class);

    @Autowired
    private RestTemplate restTemplate;

    @Autowired
    private DiscoveryClient discoveryClient;

    private String getServiceUrl(String serviceName) {
        return "http://" + serviceName;
    }

    @Override
    public Response createFoodDeliveryOrder(FoodDeliveryOrder fd, HttpHeaders headers) {
        String stationFoodStoreId = fd.getStationFoodStoreId();

        String staion_food_service_url = getServiceUrl("ts-station-food-service");
//        staion_food_service_url = "http://ts-station-food-service"; // 测试
        ResponseEntity<Response<StationFoodStoreInfo>> getStationFoodStore = restTemplate.exchange(
                staion_food_service_url + "/api/v1/stationfoodservice/stationfoodstores/bystoreid/" + stationFoodStoreId,
                HttpMethod.GET,
                new HttpEntity(headers),
                new ParameterizedTypeReference<Response<StationFoodStoreInfo>>() {
                });
        Response<StationFoodStoreInfo> result = getStationFoodStore.getBody();
        StationFoodStoreInfo stationFoodStoreInfo = result.getData();
        List<Food> storeFoodList = stationFoodStoreInfo.getFoodList();
        Map<String, Double> foodPrice = storeFoodList.stream()
                                                     .collect(Collectors.toMap(Food::getFoodName, Food::getPrice));
        List<Food> orderFoodList = fd.getFoodList();
        double deliveryFee = 0;
        for (Food food : orderFoodList) {
            Double fee = foodPrice.get(food.getFoodName());
            if (fee == null) {
                LOGGER.error("{}:{} have no such food: {}", stationFoodStoreId, stationFoodStoreInfo.getStoreName(), food.getFoodName());
                return new Response<>(0, "Food not in store", null);
            }
            deliveryFee += fee;
        }
        deliveryFee += stationFoodStoreInfo.getDeliveryFee();
        fd.setDeliveryFee(deliveryFee);
        FoodDeliveryOrder res = foodDeliveryOrderRepository.save(fd);
        return new Response<>(1, "Save success", res);
    }

    @Override
    public Response deleteFoodDeliveryOrder(String id, HttpHeaders headers) {
        FoodDeliveryOrder t = foodDeliveryOrderRepository.findById(id).orElse(null);
        if (t == null) {
            LOGGER.error("[deleteFoodDeliveryOrder] No such food delivery order id: {}", id);
            return new Response<>(0, "No such food delivery order id", id);
        } else {
            foodDeliveryOrderRepository.deleteById(id);
            LOGGER.info("[deleteFoodDeliveryOrder] Delete success, food delivery order id: {}", id);
            return new Response<>(1, "Delete success", null);
        }
    }

    @Override
    public Response getFoodDeliveryOrderById(String id, HttpHeaders headers) {
        FoodDeliveryOrder t = foodDeliveryOrderRepository.findById(id).orElse(null);
        if (t == null) {
            LOGGER.error("[deleteFoodDeliveryOrder] No such food delivery order id: {}", id);
            return new Response<>(0, "No such food delivery order id", id);
        } else {
            LOGGER.info("[getFoodDeliveryOrderById] Get success, food delivery order id: {}", id);
            return new Response<>(1, "Get success", t);
        }
    }

    @Override
    public Response getAllFoodDeliveryOrders(HttpHeaders headers) {
        List<FoodDeliveryOrder> foodDeliveryOrders = foodDeliveryOrderRepository.findAll();
        if (foodDeliveryOrders == null) {
            LOGGER.error("[getAllFoodDeliveryOrders] Food delivery orders query error");
            return new Response<>(0, "food delivery orders query error", null);
        } else {
            LOGGER.info("[getAllFoodDeliveryOrders] Get all food delivery orders success");
            return new Response<>(1, "Get success", foodDeliveryOrders);
        }
    }

    @Override
    public Response getFoodDeliveryOrderByStoreId(String storeId, HttpHeaders headers) {
        List<FoodDeliveryOrder> foodDeliveryOrders = foodDeliveryOrderRepository.findByStationFoodStoreId(storeId);
        if (foodDeliveryOrders == null) {
            LOGGER.error("[getAllFoodDeliveryOrders] Food delivery orders query error");
            return new Response<>(0, "food delivery orders query error", storeId);
        } else {
            LOGGER.info("[getAllFoodDeliveryOrders] Get food delivery orders by storeId {} success", storeId);
            return new Response<>(1, "Get success", foodDeliveryOrders);
        }
    }

    @Override
    public Response updateTripId(TripOrderInfo tripInfo, HttpHeaders headers) {
        String id = tripInfo.getOrderId();
        String tripId = tripInfo.getTripId();
        FoodDeliveryOrder t = foodDeliveryOrderRepository.findById(id).orElse(null);
        if (t == null) {
            LOGGER.error("[updateTripId] No such delivery order id: {}", id);
            return new Response<>(0, "No such delivery order id", id);
        } else {
            t.setTripId(tripId);
            foodDeliveryOrderRepository.save(t);
            LOGGER.info("[updateTripId] update tripId success. id:{}, tripId:{}", id, tripId);
            return new Response<>(1, "update tripId success", t);
        }
    }

    @Override
    public Response updateSeatNo(SeatInfo seatInfo, HttpHeaders headers) {
        String id = seatInfo.getOrderId();
        int seatNo = seatInfo.getSeatNo();
        FoodDeliveryOrder t = foodDeliveryOrderRepository.findById(id).orElse(null);
        if (t == null) {
            LOGGER.error("[updateSeatNo] No such delivery order id: {}", id);
            return new Response<>(0, "No such delivery order id", id);
        } else {
            t.setSeatNo(seatNo);
            foodDeliveryOrderRepository.save(t);
            LOGGER.info("[updateSeatNo] update seatNo success. id:{}, seatNo:{}", id, seatNo);
            return new Response<>(1, "update seatNo success", t);
        }
    }

    @Override
    public Response updateDeliveryTime(DeliveryInfo deliveryInfo, HttpHeaders headers) {
        String id = deliveryInfo.getOrderId();
        String deliveryTime = deliveryInfo.getDeliveryTime();
        FoodDeliveryOrder t = foodDeliveryOrderRepository.findById(id).orElse(null);
        if (t == null) {
            LOGGER.error("[updateDeliveryTime] No such delivery order id: {}", id);
            return new Response<>(0, "No such delivery order id", id);
        } else {
            t.setDeliveryTime(deliveryTime);
            foodDeliveryOrderRepository.save(t);
            LOGGER.info("[updateDeliveryTime] update deliveryTime success. id:{}, deliveryTime:{}", id, deliveryTime);
            return new Response<>(1, "update deliveryTime success", t);
        }
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-food-delivery-service/src/main/java/food_delivery/service/FoodDeliveryServiceImpl.java:FoodDeliveryServiceImpl.<init>
package food_delivery.service;

import edu.fudan.common.util.Response;
import food_delivery.entity.DeliveryInfo;
import food_delivery.entity.FoodDeliveryOrder;
import food_delivery.entity.SeatInfo;
import food_delivery.entity.TripOrderInfo;
import org.springframework.http.HttpHeaders;

public interface FoodDeliveryService {

    Response createFoodDeliveryOrder(FoodDeliveryOrder fd, HttpHeaders headers);

    Response deleteFoodDeliveryOrder(String id, HttpHeaders headers);

    Response getFoodDeliveryOrderById(String id, HttpHeaders headers);

    Response getAllFoodDeliveryOrders(HttpHeaders headers);

    Response getFoodDeliveryOrderByStoreId(String storeId, HttpHeaders headers);

    Response updateTripId(TripOrderInfo tripOrderInfo, HttpHeaders headers);

    Response updateSeatNo(SeatInfo seatInfo, HttpHeaders headers);

    Response updateDeliveryTime(DeliveryInfo deliveryInfo, HttpHeaders headers);
}


// Node: repos/cloned_ms_repos/train-ticket/ts-food-delivery-service/src/main/java/food_delivery/service/FoodDeliveryService.java:FoodDeliveryService.<init>
package food_delivery.init;

import food_delivery.service.FoodDeliveryService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.CommandLineRunner;
import org.springframework.stereotype.Component;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import edu.fudan.common.entity.Food;

@Component
public class InitData implements CommandLineRunner {

    @Autowired
    FoodDeliveryService foodDeliveryService;

    private static final Logger LOGGER = LoggerFactory.getLogger(InitData.class);


    @Override
    public void run(String... args) {
        BufferedReader br = new BufferedReader(new InputStreamReader(this.getClass().getResourceAsStream("/food_delivery_orders.txt")));
        try {  // 有限制，不能随意init初始化数据，因此先注释掉。
//            String line;
//            while ((line = br.readLine()) != null) {
//                String[] strs = line.trim().split("\\|");
//                String[] foods = strs[1].trim().split(",");
//                List<Food> foodList = new ArrayList<>();
//                for (String food : foods) {
//                    String[] food_info = food.trim().split("_");
//                    foodList.add(new Food(food_info[0], Double.parseDouble(food_info[1])));
//                }
//                FoodDeliveryOrder foodDeliveryOrder = new FoodDeliveryOrder(
//                        UUID.randomUUID().toString(),       // id
//                        strs[0],                            // stationFoodStoreId
//                        foodList,                           // foodList
//                        strs[2],                            // tripId
//                        Integer.parseInt(strs[3]),          // seatNo
//                        strs[4],                            // createdTime
//                        strs[5],                            // deliveryTime
//                        Double.parseDouble(strs[6])         // deliveryFee
//                );
//                foodDeliveryService.createFoodDeliveryOrder(foodDeliveryOrder, null);
//            }
        } catch(Exception e) {
            InitData.LOGGER.info("food_delivery_orders.txt has format error!");
            InitData.LOGGER.error(e.getMessage());
            System.exit(1);
        }
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-food-delivery-service/src/main/java/food_delivery/init/InitData.java:InitData.<init>
package contacts.controller;

import contacts.entity.*;
import edu.fudan.common.util.Response;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;
import contacts.service.ContactsService;

import java.util.UUID;

import static org.springframework.http.ResponseEntity.ok;

/**
 * @author fdse
 */
@RestController
@RequestMapping("api/v1/contactservice")
public class ContactsController {


    @Autowired
    private ContactsService contactsService;

    private static final Logger LOGGER = LoggerFactory.getLogger(ContactsController.class);

    @GetMapping(path = "/contacts/welcome")
    public String home() {
        return "Welcome to [ Contacts Service ] !";
    }

    @CrossOrigin(origins = "*")
    @GetMapping(path = "/contacts")
    public HttpEntity getAllContacts(@RequestHeader HttpHeaders headers) {
        ContactsController.LOGGER.info("[getAllContacts][Get All Contacts]");
        return ok(contactsService.getAllContacts(headers));
    }

    @CrossOrigin(origins = "*")
    @PostMapping(path = "/contacts")
    public ResponseEntity<Response> createNewContacts(@RequestBody Contacts aci,
                                                      @RequestHeader HttpHeaders headers) {
        ContactsController.LOGGER.info("[createNewContacts][VerifyLogin Success]");
        return new ResponseEntity<>(contactsService.create(aci, headers), HttpStatus.CREATED);
    }

    @CrossOrigin(origins = "*")
    @PostMapping(path = "/contacts/admin")
    public HttpEntity<?> createNewContactsAdmin(@RequestBody Contacts aci, @RequestHeader HttpHeaders headers) {
        aci.setId(UUID.randomUUID().toString());
        ContactsController.LOGGER.info("[createNewContactsAdmin][Create Contacts In Admin]");
        return new ResponseEntity<>(contactsService.createContacts(aci, headers), HttpStatus.CREATED);
    }


    @CrossOrigin(origins = "*")
    @DeleteMapping(path = "/contacts/{contactsId}")
    public HttpEntity deleteContacts(@PathVariable String contactsId, @RequestHeader HttpHeaders headers) {
        return ok(contactsService.delete(contactsId, headers));
    }


    @CrossOrigin(origins = "*")
    @PutMapping(path = "/contacts")
    public HttpEntity modifyContacts(@RequestBody Contacts info, @RequestHeader HttpHeaders headers) {
        ContactsController.LOGGER.info("[Contacts modifyContacts][Modify Contacts] ContactsId: {}", info.getId());
        return ok(contactsService.modify(info, headers));
    }

    @CrossOrigin(origins = "*")
    @GetMapping(path = "/contacts/account/{accountId}")
    public HttpEntity findContactsByAccountId(@PathVariable String accountId, @RequestHeader HttpHeaders headers) {
        ContactsController.LOGGER.info("[findContactsByAccountId][Find Contacts By Account Id][accountId: {}]", accountId);
        ContactsController.LOGGER.info("[ContactsService][VerifyLogin Success]");
        return ok(contactsService.findContactsByAccountId(accountId, headers));
    }

    @CrossOrigin(origins = "*")
    @GetMapping(path = "/contacts/{id}")
    public HttpEntity getContactsByContactsId(@PathVariable String id, @RequestHeader HttpHeaders headers) {
        ContactsController.LOGGER.info("[ContactsService][Contacts Id Print][id: {}]", id);
        ContactsController.LOGGER.info("[ContactsService][VerifyLogin Success]");
        return ok(contactsService.findContactsById(id, headers));
    }



}


// Node: repos/cloned_ms_repos/train-ticket/ts-contacts-service/src/main/java/contacts/controller/ContactsController.java:ContactsController.<init>
// Node: createNewContacts
// Node: createNewContactsAdmin
// Node: createContacts
// Node: findContactsByAccountId
// Node: getContactsByContactsId
// Node: findContactsById
package contacts.service;

import contacts.entity.*;
import edu.fudan.common.util.Response;
import org.springframework.http.HttpHeaders;

import java.util.UUID;

/**
 * @author fdse
 */
public interface ContactsService {

    /**
     * create contacts
     *
     * @param contacts contacts
     * @param headers headers
     * @return Reaponse
     */
    Response createContacts(Contacts contacts, HttpHeaders headers);

    /**
     * create
     *
     * @param addContacts add contacts
     * @param headers headers
     * @return Reaponse
     */
    Response create(Contacts addContacts, HttpHeaders headers);

    /**
     * delete
     *
     * @param contactsId contacts id
     * @param headers headers
     * @return Reaponse
     */
    Response delete(String contactsId, HttpHeaders headers);

    /**
     * modify
     *
     * @param contacts contacts
     * @param headers headers
     * @return Reaponse
     */
    Response modify(Contacts contacts, HttpHeaders headers);

    /**
     * get all contacts
     *
     * @param headers headers
     * @return Reaponse
     */
    Response getAllContacts(HttpHeaders headers);

    /**
     * find contacts by id
     *
     * @param id id
     * @param headers headers
     * @return Reaponse
     */
    Response findContactsById(String id, HttpHeaders headers);

    /**
     * find contacts by account id
     *
     * @param accountId account id
     * @param headers headers
     * @return Reaponse
     */
    Response findContactsByAccountId(String accountId, HttpHeaders headers);

}


// Node: repos/cloned_ms_repos/train-ticket/ts-contacts-service/src/main/java/contacts/service/ContactsService.java:ContactsService.<init>
package contacts.service;

import contacts.entity.*;
import edu.fudan.common.util.Response;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpHeaders;
import org.springframework.stereotype.Service;
import contacts.repository.ContactsRepository;

import java.util.ArrayList;
import java.util.UUID;


/**
 * @author fdse
 */
@Service
public class ContactsServiceImpl implements ContactsService {

    @Autowired
    private ContactsRepository contactsRepository;

    String success = "Success";

    private static final Logger LOGGER = LoggerFactory.getLogger(ContactsServiceImpl.class);

    @Override
    public Response findContactsById(String id, HttpHeaders headers) {
        LOGGER.info("FIND CONTACTS BY ID: " + id);
        Contacts contacts = contactsRepository.findById(id).orElse(null);
        if (contacts != null) {
            return new Response<>(1, success, contacts);
        } else {
            LOGGER.error("[findContactsById][contactsRepository.findById][No contacts according to contactsId][contactsId: {}]", id);
            return new Response<>(0, "No contacts according to contacts id", null);
        }
    }

    @Override
    public Response findContactsByAccountId(String accountId, HttpHeaders headers) {
        ArrayList<Contacts> arr = contactsRepository.findByAccountId(accountId);
        ContactsServiceImpl.LOGGER.info("[findContactsByAccountId][Query Contacts][Result Size: {}]", arr.size());
        return new Response<>(1, success, arr);
    }

    @Override
    public Response createContacts(Contacts contacts, HttpHeaders headers) {
        Contacts contactsTemp = contactsRepository.findByAccountIdAndDocumentTypeAndDocumentType(contacts.getAccountId(), contacts.getDocumentNumber(), contacts.getDocumentType());
        if (contactsTemp != null) {
            ContactsServiceImpl.LOGGER.warn("[createContacts][Init Contacts, Already Exists][Id: {}]", contacts.getId());
            return new Response<>(0, "Already Exists", contactsTemp);
        } else {
            contactsRepository.save(contacts);
            return new Response<>(1, "Create Success", null);
        }
    }

    @Override
    public Response create(Contacts addContacts, HttpHeaders headers) {

        Contacts c = contactsRepository.findByAccountIdAndDocumentTypeAndDocumentType(addContacts.getAccountId(), addContacts.getDocumentNumber(), addContacts.getDocumentType());

        if (c != null) {
            ContactsServiceImpl.LOGGER.warn("[Contacts-Add&Delete-Service.create][AddContacts][Fail.Contacts already exists][contactId: {}]", addContacts.getId());
            return new Response<>(0, "Contacts already exists", null);
        } else {
            Contacts contacts = contactsRepository.save(addContacts);
            ContactsServiceImpl.LOGGER.info("[Contacts-Add&Delete-Service.create][AddContacts Success]");
            return new Response<>(1, "Create contacts success", contacts);
        }
    }

    @Override
    public Response delete(String contactsId, HttpHeaders headers) {
        contactsRepository.deleteById(contactsId);
        Contacts contacts = contactsRepository.findById(contactsId).orElse(null);
        if (contacts == null) {
            ContactsServiceImpl.LOGGER.info("[Contacts-Add&Delete-Service][DeleteContacts Success]");
            return new Response<>(1, "Delete success", contactsId);
        } else {
            ContactsServiceImpl.LOGGER.error("[Contacts-Add&Delete-Service][DeleteContacts][Fail.Reason not clear][contactsId: {}]", contactsId);
            return new Response<>(0, "Delete failed", contactsId);
        }
    }

    @Override
    public Response modify(Contacts contacts, HttpHeaders headers) {
        headers = null;
        Response oldContactResponse = findContactsById(contacts.getId(), headers);
        LOGGER.info(oldContactResponse.toString());
        Contacts oldContacts = (Contacts) oldContactResponse.getData();
        if (oldContacts == null) {
            ContactsServiceImpl.LOGGER.error("[Contacts-Modify-Service.modify][ModifyContacts][Fail.Contacts not found][contactId: {}]", contacts.getId());
            return new Response<>(0, "Contacts not found", null);
        } else {
            oldContacts.setName(contacts.getName());
            oldContacts.setDocumentType(contacts.getDocumentType());
            oldContacts.setDocumentNumber(contacts.getDocumentNumber());
            oldContacts.setPhoneNumber(contacts.getPhoneNumber());
            contactsRepository.save(oldContacts);
            ContactsServiceImpl.LOGGER.info("[Contacts-Modify-Service.modify][ModifyContacts Success]");
            return new Response<>(1, "Modify success", oldContacts);
        }
    }

    @Override
    public Response getAllContacts(HttpHeaders headers) {
        ArrayList<Contacts> contacts = contactsRepository.findAll();
        if (contacts != null && !contacts.isEmpty()) {
            return new Response<>(1, success, contacts);
        } else {
            LOGGER.error("[getAllContacts][contactsRepository.findAll][Get all contacts error][message: {}]", "No content");
            return new Response<>(0, "No content", null);
        }
    }

}




// Node: repos/cloned_ms_repos/train-ticket/ts-contacts-service/src/main/java/contacts/service/ContactsServiceImpl.java:ContactsServiceImpl.<init>
package preserveOther.mq;


import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.amqp.core.AmqpTemplate;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;
import preserveOther.config.Queues;


@Component
public class RabbitSend {

    @Autowired
    private AmqpTemplate rabbitTemplate;

    private static final Logger logger = LoggerFactory.getLogger(RabbitSend.class);

    public void send(String val) {
        logger.info("send info to mq:" + val);
        this.rabbitTemplate.convertAndSend(Queues.queueName, val);
    }

}


// Node: repos/cloned_ms_repos/train-ticket/ts-preserve-other-service/src/main/java/preserveOther/mq/RabbitSend.java:RabbitSend.<init>
package preserveOther.controller;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.web.bind.annotation.*;
import edu.fudan.common.entity.OrderTicketsInfo;
import preserveOther.service.PreserveOtherService;

import static org.springframework.http.ResponseEntity.ok;

/**
 * @author fdse
 */
@RestController
@RequestMapping("/api/v1/preserveotherservice")
public class PreserveOtherController {

    @Autowired
    private PreserveOtherService preserveService;

    private static final Logger LOGGER = LoggerFactory.getLogger(PreserveOtherController.class);

    @GetMapping(path = "/welcome")
    public String home() {
        return "Welcome to [ PreserveOther Service ] !";
    }

    @CrossOrigin(origins = "*")
    @PostMapping(value = "/preserveOther")
    public HttpEntity preserve(@RequestBody OrderTicketsInfo oti,
                               @RequestHeader HttpHeaders headers) {
        PreserveOtherController.LOGGER.info("[preserve][Preserve Account order][from {} to {} at {}]", oti.getFrom(), oti.getTo(), oti.getDate());
        return ok(preserveService.preserve(oti, headers));
    }

}


// Node: repos/cloned_ms_repos/train-ticket/ts-preserve-other-service/src/main/java/preserveOther/controller/PreserveOtherController.java:PreserveOtherController.<init>
package preserveOther.service;

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
import preserveOther.mq.RabbitSend;

import java.util.Date;
import java.util.List;
import java.util.UUID;

/**
 * @author fdse
 */
@Service
public class PreserveOtherServiceImpl implements PreserveOtherService {

    @Autowired
    private RestTemplate restTemplate;

    @Autowired
    private RabbitSend sendService;

    @Autowired
    private DiscoveryClient discoveryClient;

    private static final Logger LOGGER = LoggerFactory.getLogger(PreserveOtherServiceImpl.class);

    private String getServiceUrl(String serviceName) {
        return "http://" + serviceName;
    }

    @Override
    public Response preserve(OrderTicketsInfo oti, HttpHeaders httpHeaders) {

        PreserveOtherServiceImpl.LOGGER.info("[preserve][Verify Login] Success");
        //1.detect ticket scalper
        //PreserveOtherServiceImpl.LOGGER.info("[preserve][Step 1][Check Security]");

        Response result = checkSecurity(oti.getAccountId(), httpHeaders);

        if (result.getStatus() == 0) {
            PreserveOtherServiceImpl.LOGGER.error("[preserve][Step 1][Check Security Fail][AccountId: {}]",oti.getAccountId());
            return new Response<>(0, result.getMsg(), null);
        }
        PreserveOtherServiceImpl.LOGGER.info("[preserve][Step 1][Check Security Complete][AccountId: {}]",oti.getAccountId());
        //2.Querying contact information -- modification, mediated by the underlying information micro service
        //PreserveOtherServiceImpl.LOGGER.info("[preserve][Step 2][Find contacts][Contacts Id: {}]", oti.getContactsId());

        Response<Contacts> gcr = getContactsById(oti.getContactsId(), httpHeaders);
        if (gcr.getStatus() == 0) {
            PreserveOtherServiceImpl.LOGGER.error("[preserve][Step 2][Find Contacts Fail][ContactsId: {},message: {}]",oti.getContactsId(),gcr.getMsg());
            return new Response<>(0, gcr.getMsg(), null);
        }

        PreserveOtherServiceImpl.LOGGER.info("[preserve][Step 2][Find contacts Complete][ContactsId: {}]",oti.getContactsId());
        //3.Check the info of train and the number of remaining tickets
        //PreserveOtherServiceImpl.LOGGER.info("[Step 3] Check tickets num");
        TripAllDetailInfo gtdi = new TripAllDetailInfo();

        gtdi.setFrom(oti.getFrom());
        gtdi.setTo(oti.getTo());

        gtdi.setTravelDate(oti.getDate());
        gtdi.setTripId(oti.getTripId());
        PreserveOtherServiceImpl.LOGGER.info("[preserve][Step 3][Check tickets num][TripId: {}]", oti.getTripId());
        Response<TripAllDetail> response = getTripAllDetailInformation(gtdi, httpHeaders);
        TripAllDetail gtdr = response.getData();
        //LOGGER.info("TripAllDetail : " + gtdr.toString());
        if (response.getStatus() == 0) {
            PreserveOtherServiceImpl.LOGGER.error("[preserve][Step 3][Check tickets num][Search For Trip Detail Information error][TripId: {}, message: {}]", gtdi.getTripId(), response.getMsg());
            return new Response<>(0, response.getMsg(), null);
        } else {
            TripResponse tripResponse = gtdr.getTripResponse();
            //LOGGER.info("TripResponse : " + tripResponse.toString());
            if (oti.getSeatType() == SeatClass.FIRSTCLASS.getCode()) {
                if (tripResponse.getConfortClass() == 0) {
                    PreserveOtherServiceImpl.LOGGER.warn("[preserve][Step 3][Check seat][Check seat is enough][TripId: {}]",oti.getTripId());
                    return new Response<>(0, "Seat Not Enough", null);
                }
            } else {
                if (tripResponse.getEconomyClass() == SeatClass.SECONDCLASS.getCode() && tripResponse.getConfortClass() == 0) {
                    PreserveOtherServiceImpl.LOGGER.warn("[preserve][Step 3][Check seat][Check seat is Not enough][TripId: {}]",oti.getTripId());
                    return new Response<>(0, "Check Seat Not Enough", null);
                }
            }
        }
        Trip trip = gtdr.getTrip();
        PreserveOtherServiceImpl.LOGGER.info("[preserve][Step 3][Check tickets num][Tickets Enough]");
        //4.send the order request and set the order information
        //PreserveOtherServiceImpl.LOGGER.info("[preserve][Step 4][Do Order]");
        Contacts contacts = gcr.getData();
        Order order = new Order();
        String orderId = UUID.randomUUID().toString();
        order.setId(orderId);
        order.setTrainNumber(oti.getTripId());
        order.setAccountId(oti.getAccountId());

        String fromStationName = oti.getFrom();
        String toStationName = oti.getTo();

        order.setFrom(fromStationName);
        order.setTo(toStationName);
        order.setBoughtDate(StringUtils.Date2String(new Date()));
        order.setStatus(OrderStatus.NOTPAID.getCode());
        order.setContactsDocumentNumber(contacts.getDocumentNumber());
        order.setContactsName(contacts.getName());
        order.setDocumentType(contacts.getDocumentType());


        Travel query = new Travel();
        query.setTrip(trip);
        query.setStartPlace(oti.getFrom());
        query.setEndPlace(oti.getTo());
        query.setDepartureTime(StringUtils.Date2String(new Date()));


        HttpEntity requestEntity = new HttpEntity(query, httpHeaders);
        String basic_service_url = getServiceUrl("ts-basic-service");
        ResponseEntity<Response<TravelResult>> re = restTemplate.exchange(
                basic_service_url + "/api/v1/basicservice/basic/travel",
                HttpMethod.POST,
                requestEntity,
                new ParameterizedTypeReference<Response<TravelResult>>() {
                });
        if(re.getBody().getStatus() == 0){
            PreserveOtherServiceImpl.LOGGER.info("[Preserve 3][Get basic travel response status is 0][response is: {}]", re.getBody());
            return new Response<>(0, re.getBody().getMsg(), null);
        }
        TravelResult resultForTravel = re.getBody().getData();

        order.setSeatClass(oti.getSeatType());
        PreserveOtherServiceImpl.LOGGER.info("[preserve][Step 4][Do Order][Travel Date][Date is: {}]", oti.getDate().toString());
        order.setTravelDate(oti.getDate());
        order.setTravelTime(gtdr.getTripResponse().getStartTime());

        //Dispatch the seat
        List<String> stationList = resultForTravel.getRoute().getStations();
        if (oti.getSeatType() == SeatClass.FIRSTCLASS.getCode()) {
            int firstClassTotalNum = resultForTravel.getTrainType().getConfortClass();
            Ticket ticket =
                    dipatchSeat(oti.getDate(),
                            order.getTrainNumber(), fromStationName, toStationName,
                            SeatClass.FIRSTCLASS.getCode(), firstClassTotalNum, stationList, httpHeaders);
            order.setSeatClass(SeatClass.FIRSTCLASS.getCode());
            order.setSeatNumber("" + ticket.getSeatNo());
            order.setPrice(resultForTravel.getPrices().get("confortClass"));
        } else {
            int secondClassTotalNum = resultForTravel.getTrainType().getEconomyClass();
            Ticket ticket =
                    dipatchSeat(oti.getDate(),
                            order.getTrainNumber(), fromStationName, toStationName,
                            SeatClass.SECONDCLASS.getCode(), secondClassTotalNum, stationList, httpHeaders);
            order.setSeatClass(SeatClass.SECONDCLASS.getCode());
            order.setSeatNumber("" + ticket.getSeatNo());

            order.setPrice(resultForTravel.getPrices().get("economyClass"));
        }
        PreserveOtherServiceImpl.LOGGER.info("[preserve][Step 4][Do Order][Order Price][Price is: {}]", order.getPrice());

        Response<Order> cor = createOrder(order, httpHeaders);
        if (cor.getStatus() == 0) {
            PreserveOtherServiceImpl.LOGGER.error("[preserve][Step 4][Do Order][Create Order Fail][OrderId: {},  Reason: {}]", order.getId(), cor.getMsg());
            return new Response<>(0, cor.getMsg(), null);
        }

        PreserveOtherServiceImpl.LOGGER.info("[preserve][Step 4][Do Order][Do Order Complete]");
        Response returnResponse = new Response<>(1, "Success.", cor.getMsg());
        //5.Check insurance options
        if (oti.getAssurance() == 0) {
            PreserveOtherServiceImpl.LOGGER.info("[preserve][Step 5][Buy Assurance][Do not need to buy assurance]");
        } else {
            Response<Assurance> addAssuranceResult = addAssuranceForOrder(
                    oti.getAssurance(), cor.getData().getId().toString(), httpHeaders);
            if (addAssuranceResult.getStatus() == 1) {
                PreserveOtherServiceImpl.LOGGER.info("[preserve][Step 5][Buy Assurance][Preserve Buy Assurance Success]");
            } else {
                PreserveOtherServiceImpl.LOGGER.warn("[preserve][Step 5][Buy Assurance][Buy Assurance Fail][assurance: {}, OrderId: {}]", oti.getAssurance(),cor.getData().getId());
                returnResponse.setMsg("Success.But Buy Assurance Fail.");
            }
        }

        //6.Increase the food order
        if (oti.getFoodType() != 0) {
            FoodOrder foodOrder = new FoodOrder();
            foodOrder.setOrderId(cor.getData().getId());
            foodOrder.setFoodType(oti.getFoodType());
            foodOrder.setFoodName(oti.getFoodName());
            foodOrder.setPrice(oti.getFoodPrice());
            if (oti.getFoodType() == 2) {
                foodOrder.setStationName(oti.getStationName());
                foodOrder.setStoreName(oti.getStoreName());
            }
            Response afor = createFoodOrder(foodOrder, httpHeaders);
            if (afor.getStatus() == 1) {
                PreserveOtherServiceImpl.LOGGER.info("[preserve][Step 6][Buy Food][Buy Food Success]");
            } else {
                PreserveOtherServiceImpl.LOGGER.error("[preserve][Step 6][Buy Food][Buy Food Fail][OrderId: {}]",cor.getData().getId());
                returnResponse.setMsg("Success.But Buy Food Fail.");
            }
        } else {
            PreserveOtherServiceImpl.LOGGER.info("[preserve][Step 6][Buy Food][Do not need to buy food]");
        }

        //7.add consign
        if (null != oti.getConsigneeName() && !"".equals(oti.getConsigneeName())) {
            Consign consignRequest = new Consign();
            consignRequest.setOrderId(cor.getData().getId());
            consignRequest.setAccountId(cor.getData().getAccountId());
            consignRequest.setHandleDate(oti.getHandleDate());
            consignRequest.setTargetDate(cor.getData().getTravelDate().toString());
            consignRequest.setFrom(cor.getData().getFrom());
            consignRequest.setTo(cor.getData().getTo());
            consignRequest.setConsignee(oti.getConsigneeName());
            consignRequest.setPhone(oti.getConsigneePhone());
            consignRequest.setWeight(oti.getConsigneeWeight());
            consignRequest.setWithin(oti.isWithin());
            //LOGGER.info("CONSIGN INFO : " + consignRequest.toString());
            Response icresult = createConsign(consignRequest, httpHeaders);
            if (icresult.getStatus() == 1) {
                PreserveOtherServiceImpl.LOGGER.info("[preserve][Step 7][Add Consign][Consign Success]");
            } else {
                PreserveOtherServiceImpl.LOGGER.error("[preserve][Step 7][Add Consign][Preserve Consign Fail][OrderId: {}]", cor.getData().getId());
                returnResponse.setMsg("Consign Fail.");
            }
        } else {
            PreserveOtherServiceImpl.LOGGER.info("[preserve][Step 7][Add Consign][Do not need to consign]");
        }

        //8.send notification

        User getUser = getAccount(order.getAccountId().toString(), httpHeaders);

        NotifyInfo notifyInfo = new NotifyInfo();
        notifyInfo.setDate(new Date().toString());

        notifyInfo.setEmail(getUser.getEmail());
        notifyInfo.setStartPlace(order.getFrom());
        notifyInfo.setEndPlace(order.getTo());
        notifyInfo.setUsername(getUser.getUserName());
        notifyInfo.setSeatNumber(order.getSeatNumber());
        notifyInfo.setOrderNumber(order.getId().toString());
        notifyInfo.setPrice(order.getPrice());
        notifyInfo.setSeatClass(SeatClass.getNameByCode(order.getSeatClass()));
        notifyInfo.setStartTime(order.getTravelTime().toString());

        // TODO: change to async message serivce
        // sendEmail(notifyInfo, httpHeaders);

        return returnResponse;
    }

    public Ticket dipatchSeat(String date, String tripId, String startStationId, String endStataionId, int seatType, int totalNum, List<String> stationList, HttpHeaders httpHeaders) {
        Seat seatRequest = new Seat();
        seatRequest.setTravelDate(date);
        seatRequest.setTrainNumber(tripId);
        seatRequest.setStartStation(startStationId);
        seatRequest.setSeatType(seatType);
        seatRequest.setDestStation(endStataionId);
        seatRequest.setTotalNum(totalNum);
        seatRequest.setStations(stationList);

        HttpEntity requestEntityTicket = new HttpEntity(seatRequest, httpHeaders);
        String seat_service_url = getServiceUrl("ts-seat-service");
        ResponseEntity<Response<Ticket>> reTicket = restTemplate.exchange(
                seat_service_url + "/api/v1/seatservice/seats",
                HttpMethod.POST,
                requestEntityTicket,
                new ParameterizedTypeReference<Response<Ticket>>() {
                });

        return reTicket.getBody().getData();
    }

    public boolean sendEmail(NotifyInfo notifyInfo, HttpHeaders httpHeaders) {
        try {
            String infoJson = JsonUtils.object2Json(notifyInfo);
            sendService.send(infoJson);
            PreserveOtherServiceImpl.LOGGER.info("[sendEmail][Send email to mq success]");
        } catch (Exception e) {
            PreserveOtherServiceImpl.LOGGER.error("[sendEmail][Send email to mq error] exception is:" + e);
            return false;
        }

        return true;
    }

    public User getAccount(String accountId, HttpHeaders httpHeaders) {
        PreserveOtherServiceImpl.LOGGER.info("[getAccount][Cancel Order Service][Get Order By Id]");

        HttpEntity requestEntitySendEmail = new HttpEntity(httpHeaders);
        String user_service_url = getServiceUrl("ts-user-service");
        ResponseEntity<Response<User>> getAccount = restTemplate.exchange(
                user_service_url + "/api/v1/userservice/users/id/" + accountId,
                HttpMethod.GET,
                requestEntitySendEmail,
                new ParameterizedTypeReference<Response<User>>() {
                });
        Response<User> result = getAccount.getBody();
        return result.getData();


    }

    private Response<Assurance> addAssuranceForOrder(int assuranceType, String orderId, HttpHeaders httpHeaders) {
        PreserveOtherServiceImpl.LOGGER.info("[addAssuranceForOrder][Preserve Service][Add Assurance Type For Order]");
        HttpEntity requestAddAssuranceResult = new HttpEntity(httpHeaders);
        String assurance_service_url = getServiceUrl("ts-assurance-service");
        ResponseEntity<Response<Assurance>> reAddAssuranceResult = restTemplate.exchange(
                assurance_service_url + "/api/v1/assuranceservice/assurances/" + assuranceType + "/" + orderId,
                HttpMethod.GET,
                requestAddAssuranceResult,
                new ParameterizedTypeReference<Response<Assurance>>() {
                });

        return reAddAssuranceResult.getBody();
    }


    private String queryForStationId(String stationName, HttpHeaders httpHeaders) {
        PreserveOtherServiceImpl.LOGGER.info("[queryForStationId][Preserve Other Service][Get Station By  Name]");


        HttpEntity requestQueryForStationId = new HttpEntity(httpHeaders);
        String station_service_url = getServiceUrl("ts-station-service");
        ResponseEntity<Response<String>> reQueryForStationId = restTemplate.exchange(
                station_service_url + "/api/v1/stationservice/stations/id/" + stationName,
                HttpMethod.GET,
                requestQueryForStationId,
                new ParameterizedTypeReference<Response<String>>() {
                });
        return reQueryForStationId.getBody().getData();
    }

    private Response checkSecurity(String accountId, HttpHeaders httpHeaders) {
        PreserveOtherServiceImpl.LOGGER.info("[checkSecurity][Preserve Other Service][Check Account Security]");

        HttpEntity requestCheckResult = new HttpEntity(httpHeaders);
        String security_service_url = getServiceUrl("ts-security-service");
        ResponseEntity<Response> reCheckResult = restTemplate.exchange(
                security_service_url + "/api/v1/securityservice/securityConfigs/" + accountId,
                HttpMethod.GET,
                requestCheckResult,
                Response.class);

        return reCheckResult.getBody();
    }


    private Response<TripAllDetail> getTripAllDetailInformation(TripAllDetailInfo gtdi, HttpHeaders httpHeaders) {
        PreserveOtherServiceImpl.LOGGER.info("[getTripAllDetailInformation][Preserve Other Service][Get Trip All Detail Information]");

        HttpEntity requestGetTripAllDetailResult = new HttpEntity(gtdi, httpHeaders);
        String travel2_service_url = getServiceUrl("ts-travel2-service");
        ResponseEntity<Response<TripAllDetail>> reGetTripAllDetailResult = restTemplate.exchange(
                travel2_service_url + "/api/v1/travel2service/trip_detail",
                HttpMethod.POST,
                requestGetTripAllDetailResult,
                new ParameterizedTypeReference<Response<TripAllDetail>>() {
                });

        return reGetTripAllDetailResult.getBody();
    }

    private Response<Contacts> getContactsById(String contactsId, HttpHeaders httpHeaders) {
        PreserveOtherServiceImpl.LOGGER.info("[getContactsById][Preserve Other Service][Get Contacts By Id is]");

        HttpEntity requestGetContactsResult = new HttpEntity(httpHeaders);
        String contacts_service_url = getServiceUrl("ts-contacts-service");
        ResponseEntity<Response<Contacts>> reGetContactsResult = restTemplate.exchange(
                contacts_service_url + "/api/v1/contactservice/contacts/" + contactsId,
                HttpMethod.GET,
                requestGetContactsResult,
                new ParameterizedTypeReference<Response<Contacts>>() {
                });

        return reGetContactsResult.getBody();
    }

    private Response<Order> createOrder(Order coi, HttpHeaders httpHeaders) {
        PreserveOtherServiceImpl.LOGGER.info("[createOrder][Preserve Other Service][Get Contacts By Id]");

        HttpEntity requestEntityCreateOrderResult = new HttpEntity(coi, httpHeaders);
        String order_other_service_url = getServiceUrl("ts-order-other-service");
        ResponseEntity<Response<Order>> reCreateOrderResult = restTemplate.exchange(
                order_other_service_url + "/api/v1/orderOtherService/orderOther",
                HttpMethod.POST,
                requestEntityCreateOrderResult,
                new ParameterizedTypeReference<Response<Order>>() {
                });


        return reCreateOrderResult.getBody();
    }

    private Response createFoodOrder(FoodOrder afi, HttpHeaders httpHeaders) {
        PreserveOtherServiceImpl.LOGGER.info("[createFoodOrder][Preserve Service][Add Preserve food Order]");

        HttpEntity requestEntityAddFoodOrderResult = new HttpEntity(afi, httpHeaders);
        String food_service_url = getServiceUrl("ts-food-service");
        ResponseEntity<Response> reAddFoodOrderResult = restTemplate.exchange(
                food_service_url + "/api/v1/foodservice/orders",
                HttpMethod.POST,
                requestEntityAddFoodOrderResult,
                Response.class);

        return reAddFoodOrderResult.getBody();
    }

    private Response createConsign(Consign cr, HttpHeaders httpHeaders) {
        PreserveOtherServiceImpl.LOGGER.info("[createConsign][Preserve Service][Add Condign]");

        HttpEntity requestEntityResultForTravel = new HttpEntity(cr, httpHeaders);
        String consign_service_url = getServiceUrl("ts-consign-service");
        ResponseEntity<Response> reResultForTravel = restTemplate.exchange(
                consign_service_url + "/api/v1/consignservice/consigns",
                HttpMethod.POST,
                requestEntityResultForTravel,
                Response.class);


        return reResultForTravel.getBody();
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-preserve-other-service/src/main/java/preserveOther/service/PreserveOtherServiceImpl.java:PreserveOtherServiceImpl.<init>
package food.controller;

import food.service.StationFoodService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.web.bind.annotation.*;

import java.util.List;

import static org.springframework.http.ResponseEntity.ok;

@RestController
@RequestMapping("/api/v1/stationfoodservice")
public class StationFoodController {

    @Autowired
    StationFoodService stationFoodService;

    private static final Logger LOGGER = LoggerFactory.getLogger(StationFoodController.class);

    @GetMapping(path = "/stationfoodstores/welcome")
    public String home() {
        return "Welcome to [ Food store Service ] !";
    }

    @CrossOrigin(origins = "*")
    @GetMapping("/stationfoodstores")
    public HttpEntity getAllFoodStores(@RequestHeader HttpHeaders headers) {
        StationFoodController.LOGGER.info("[Food Map Service][Get All FoodStores]");
        return ok(stationFoodService.listFoodStores(headers));
    }

    @CrossOrigin(origins = "*")
    @GetMapping("/stationfoodstores/{stationId}")
    public HttpEntity getFoodStoresOfStation(@PathVariable String stationName, @RequestHeader HttpHeaders headers) {
        StationFoodController.LOGGER.info("[Food Map Service][Get FoodStores By StationName]");
        return ok(stationFoodService.listFoodStoresByStationName(stationName, headers));
    }

    @CrossOrigin(origins = "*")
    @PostMapping("/stationfoodstores")
    public HttpEntity getFoodStoresByStationNames(@RequestBody List<String> stationNameList) {
        StationFoodController.LOGGER.info("[Food Map Service][Get FoodStores By StationNames]");
        return ok(stationFoodService.getFoodStoresByStationNames(stationNameList));
    }
    @GetMapping("/stationfoodstores/bystoreid/{stationFoodStoreId}")
    public HttpEntity getFoodListByStationFoodStoreId(@PathVariable String stationFoodStoreId, @RequestHeader HttpHeaders headers) {
        StationFoodController.LOGGER.info("[Food Map Service][Get Foodlist By stationFoodStoreId]");
        return ok(stationFoodService.getStaionFoodStoreById(stationFoodStoreId));
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-station-food-service/src/main/java/food/controller/StationFoodController.java:StationFoodController.<init>
// Node: getAllFoodStores
// Node: getFoodStoresOfStation
// Node: listFoodStoresByStationName
package food.service;

import edu.fudan.common.util.Response;
import food.entity.StationFoodStore;
import food.repository.StationFoodRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpHeaders;
import org.springframework.stereotype.Service;

import java.util.List;


@Service
public class StationFoodServiceImpl implements StationFoodService {

    @Autowired
    StationFoodRepository stationFoodRepository;

//    @Autowired
//    TrainFoodRepository trainFoodRepository;

    private static final Logger LOGGER = LoggerFactory.getLogger(StationFoodServiceImpl.class);

    String success = "Success";
    String noContent = "No content";

    @Override
    public Response createFoodStore(StationFoodStore fs, HttpHeaders headers) {
        StationFoodStore fsTemp = stationFoodRepository.findById(fs.getId()).orElse(null);
        if (fsTemp != null) {
            StationFoodServiceImpl.LOGGER.error("[Init FoodStore] Already Exists Id: {}", fs.getId());
            return new Response<>(0, "Already Exists Id", null);
        } else {
            try{
                stationFoodRepository.save(fs);
                return new Response<>(1, "Save Success", fs);
            }catch(Exception e){
                return new Response<>(0, "Save failed", e.getMessage());
            }
        }
    }

//    @Override
//    public TrainFood createTrainFood(TrainFood tf, HttpHeaders headers) {
//        TrainFood tfTemp = trainFoodRepository.findById(tf.getId());
//        if (tfTemp != null) {
//            StationFoodServiceImpl.LOGGER.error("[Init TrainFood] Already Exists Id: {}", tf.getId());
//        } else {
//            trainFoodRepository.save(tf);
//        }
//        return tf;
//    }

    @Override
    public Response listFoodStores(HttpHeaders headers) {
        List<StationFoodStore> stationFoodStores = stationFoodRepository.findAll();
        if (stationFoodStores != null && !stationFoodStores.isEmpty()) {
            return new Response<>(1, success, stationFoodStores);
        } else {
            StationFoodServiceImpl.LOGGER.error("List food stores error: {}", "Food store is empty");
            return new Response<>(0, "Food store is empty", null);
        }
    }

//    @Override
//    public Response listTrainFood(HttpHeaders headers) {
//        List<TrainFood> trainFoodList = trainFoodRepository.findAll();
//        if (trainFoodList != null && !trainFoodList.isEmpty()) {
//            return new Response<>(1, success, trainFoodList);
//        } else {
//            StationFoodServiceImpl.LOGGER.error("List train food error: {}", noContent);
//            return new Response<>(0, noContent, null);
//        }
//    }

    @Override
    public Response listFoodStoresByStationName(String stationName, HttpHeaders headers) {
        List<StationFoodStore> stationFoodStoreList = stationFoodRepository.findByStationName(stationName);
        if (stationFoodStoreList != null && !stationFoodStoreList.isEmpty()) {
            return new Response<>(1, success, stationFoodStoreList);
        } else {
            StationFoodServiceImpl.LOGGER.error("List food stores by station id error: {}, stationName: {}", "Food store is empty", stationName);
            return new Response<>(0, "Food store is empty", null);
        }
    }

//    @Override
//    public Response listTrainFoodByTripId(String tripId, HttpHeaders headers) {
//        List<TrainFood> trainFoodList = trainFoodRepository.findByTripId(tripId);
//        if (trainFoodList != null) {
//            return new Response<>(1, success, trainFoodList);
//        } else {
//            StationFoodServiceImpl.LOGGER.error("List train food by trip id error: {}, tripId: {}", noContent, tripId);
//            return new Response<>(0, noContent, null);
//        }
//    }

    @Override
    public Response getFoodStoresByStationNames(List<String> stationNames) {
        List<StationFoodStore> stationFoodStoreList = stationFoodRepository.findByStationNameIn(stationNames);
        if (stationFoodStoreList != null) {
            return new Response<>(1, success, stationFoodStoreList);
        } else {
            StationFoodServiceImpl.LOGGER.error("List food stores by station ids error: {}, stationName list: {}", "Food store is empty", stationNames);
            return new Response<>(0, noContent, null);
        }
    }

    @Override
    public Response getStaionFoodStoreById(String id) {
        StationFoodStore stationFoodStore = stationFoodRepository.findById(id).orElse(null);
        if (stationFoodStore == null) {
            LOGGER.error("no such staionFoodStoreId: {}", id);
            return new Response<>(0, noContent, null);
        } else {
            return new Response<>(1, success, stationFoodStore);
        }
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-station-food-service/src/main/java/food/service/StationFoodServiceImpl.java:StationFoodServiceImpl.<init>
package config.controller;

import config.entity.Config;
import config.service.ConfigService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;


import static org.springframework.http.ResponseEntity.ok;

/**
 * @author  Chenjie Xu
 * @date 2017/5/11.
 */
@RestController
@RequestMapping("api/v1/configservice")
public class ConfigController {

    @Autowired
    private ConfigService configService;

    private static final Logger logger = LoggerFactory.getLogger(ConfigController.class);

    @GetMapping(path = "/welcome")
    public String home(@RequestHeader HttpHeaders headers) {
        return "Welcome to [ Config Service ] !";
    }

    @CrossOrigin(origins = "*")
    @GetMapping(value = "/configs")
    public HttpEntity queryAll(@RequestHeader HttpHeaders headers) {
        logger.info("[queryAll][Query all configs]");
        return ok(configService.queryAll(headers));
    }

    @CrossOrigin(origins = "*")
    @PostMapping(value = "/configs")
    public HttpEntity<?> createConfig(@RequestBody Config info, @RequestHeader HttpHeaders headers) {
        logger.info("[createConfig][Create config][Config name: {}]", info.getName());
        return new ResponseEntity<>(configService.create(info, headers), HttpStatus.CREATED);
    }

    @CrossOrigin(origins = "*")
    @PutMapping(value = "/configs")
    public HttpEntity updateConfig(@RequestBody Config info, @RequestHeader HttpHeaders headers) {
        logger.info("[updateConfig][Update config][Config name: {}]", info.getName());
        return ok(configService.update(info, headers));
    }


    @CrossOrigin(origins = "*")
    @DeleteMapping(value = "/configs/{configName}")
    public HttpEntity deleteConfig(@PathVariable String configName, @RequestHeader HttpHeaders headers) {
        logger.info("[deleteConfig][Delete config][configName: {}]", configName);
        return ok(configService.delete(configName, headers));
    }

    @CrossOrigin(origins = "*")
    @GetMapping(value = "/configs/{configName}")
    public HttpEntity retrieve(@PathVariable String configName, @RequestHeader HttpHeaders headers) {
        logger.info("[retrieve][Retrieve config][configName: {}]", configName);
        return ok(configService.query(configName, headers));
    }



}


// Node: repos/cloned_ms_repos/train-ticket/ts-config-service/src/main/java/config/controller/ConfigController.java:ConfigController.<init>
// Node: createConfig
// Node: updateConfig
package config.service;

import config.entity.Config;
import config.repository.ConfigRepository;
import edu.fudan.common.util.Response;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpHeaders;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;


/**
 * @author fdse
 */
@Service
public class ConfigServiceImpl implements ConfigService {

    @Autowired
    ConfigRepository repository;

    private static final Logger logger = LoggerFactory.getLogger(ConfigServiceImpl.class);

    String config0 = "Config ";

    @Override
    public Response create(Config info, HttpHeaders headers) {
        if (repository.findByName(info.getName()) != null) {
            String result = config0 + info.getName() + " already exists.";
            logger.warn("[create][{} already exists][config info: {}]", config0, info.getName());
            return new Response<>(0, result, null);
        } else {
            Config config = new Config(info.getName(), info.getValue(), info.getDescription());
            repository.save(config);
            logger.info("[create][create success][Config: {}]", info);
            return new Response<>(1, "Create success", config);
        }
    }

    @Override
    public Response update(Config info, HttpHeaders headers) {
        if (repository.findByName(info.getName()) == null) {
            String result = config0 + info.getName() + " doesn't exist.";
            logger.warn(result);
            return new Response<>(0, result, null);
        } else {
            Config config = new Config(info.getName(), info.getValue(), info.getDescription());
            repository.save(config);
            logger.info("[update][update success][Config: {}]", config);
            return new Response<>(1, "Update success", config);
        }
    }


    @Override
    public Response query(String name, HttpHeaders headers) {
        Config config = repository.findByName(name);
        if (config == null) {
            logger.warn("[query][Config does not exist][name: {}, message: {}]", name, "No content");
            return new Response<>(0, "No content", null);
        } else {
            logger.info("[query][Query config success][config name: {}]", name);
            return new Response<>(1, "Success", config);
        }
    }

    @Override
    @Transactional
    public Response delete(String name, HttpHeaders headers) {
        Config config = repository.findByName(name);
        if (config == null) {
            String result = config0 + name + " doesn't exist.";
            logger.warn("[delete][config doesn't exist][config name: {}]", name);
            return new Response<>(0, result, null);
        } else {
            repository.deleteByName(name);
            logger.info("[delete][Config delete success][config name: {}]", name);
            return new Response<>(1, "Delete success", config);
        }
    }

    @Override
    public Response queryAll(HttpHeaders headers) {
        List<Config> configList = repository.findAll();

        if (configList != null && !configList.isEmpty()) {
            logger.info("[queryAll][Query all config success]");
            return new Response<>(1, "Find all  config success", configList);
        } else {
            logger.warn("[queryAll][Query config, No content]");
            return new Response<>(0, "No content", null);
        }
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-config-service/src/main/java/config/service/ConfigServiceImpl.java:ConfigServiceImpl.<init>
