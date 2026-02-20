// Cluster 7

// Node: toString
// Node: when
// Node: any
// Node: thenReturn
// Node: assertEquals
// Node: UserDto
// Node: anyString
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


// Node: create
// Node: getAllOrders
package waitorder.repository;


import org.springframework.data.repository.CrudRepository;
import org.springframework.stereotype.Repository;
import waitorder.entity.WaitListOrder;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

@Repository
public interface WaitListOrderRepository extends CrudRepository<WaitListOrder,String> {

    @Override
    Optional<WaitListOrder> findById(String id);

    @Override
    List<WaitListOrder> findAll();

    ArrayList<WaitListOrder> findByAccountId(String accountId);

    @Override
    void deleteById(String id);
}


// Node: repos/cloned_ms_repos/train-ticket/ts-wait-order-service/src/main/java/waitorder/repository/WaitListOrderRepository.java:WaitListOrderRepository.<init>
// Node: findById
// Node: findAll
// Node: findByAccountId
// Node: deleteById
package waitorder.service;

import edu.fudan.common.util.Response;
import org.springframework.http.HttpHeaders;
import waitorder.entity.WaitListOrder;
import waitorder.entity.WaitListOrderVO;

public interface WaitListOrderService {

    Response findOrderById(String id, HttpHeaders headers);

    Response create(WaitListOrderVO newOrder, HttpHeaders headers);

    /**
     * Get all orders, including completed and expired ones
     */
    Response getAllOrders(HttpHeaders headers);

    Response updateOrder(WaitListOrder order, HttpHeaders headers);

    /**
     * Use when modifying order status
     */
    Response modifyWaitListOrderStatus(int status, String orderId);

    /**
     * Get all orders in the wait list
     */
    Response getAllWaitListOrders(HttpHeaders headers);
}


// Node: repos/cloned_ms_repos/train-ticket/ts-wait-order-service/src/main/java/waitorder/service/WaitListOrderService.java:WaitListOrderService.<init>
// Node: findOrderById
// Node: add
// Node: save
// Node: randomUUID
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

// Node: ofNullable
// Node: createToken
// Node: User
// Node: BasicAuthDto
// Node: getMsg
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


// Node: testSaveUser
// Node: testCreateDefaultAuthUser
// Node: testDeleteByUserId
// Node: doNothing
// Node: doThrow
// Node: RuntimeException
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


// Node: testGetToken1
// Node: testGetToken2
// Node: of
package edu.fudan.common.entity;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;
import java.util.UUID;

/**
 * @author fdse
 */
@Data
@JsonIgnoreProperties(ignoreUnknown = true)
public class Route {
    private String id;

    private List<String> stations;

    private List<Integer> distances;

    private String startStation;

    private String endStation;

    public Route(){
        this.id = UUID.randomUUID().toString();
    }

    public Route(String id, List<String> stations, List<Integer> distances, String startStationName, String terminalStationName) {
        this.id = id;
        this.stations = stations;
        this.distances = distances;
        this.startStation = startStationName;
        this.endStation = terminalStationName;
    }

    public Route(List<String> stations, List<Integer> distances, String startStationName, String terminalStationName) {
        this.id = UUID.randomUUID().toString();
        this.stations = stations;
        this.distances = distances;
        this.startStation = startStationName;
        this.endStation = terminalStationName;
    }
}

// Node: repos/cloned_ms_repos/train-ticket/ts-common/src/main/java/edu/fudan/common/entity/Route.java:Route.<init>
// Node: Route
package edu.fudan.common.entity;

import lombok.Data;
import javax.validation.Valid;
import javax.validation.constraints.NotNull;

/**
 * @author fdse
 */
@Data
public class TrainType {
    private String id;

    private String name;

    private int economyClass;

    private int confortClass;

    private int averageSpeed;

    public TrainType(){
        //Default Constructor
    }

    public TrainType(String name, int economyClass, int confortClass) {
        this.name = name;
        this.economyClass = economyClass;
        this.confortClass = confortClass;
    }

    public TrainType(String name, int economyClass, int confortClass, int averageSpeed) {
        this.name = name;
        this.economyClass = economyClass;
        this.confortClass = confortClass;
        this.averageSpeed = averageSpeed;
    }
}

// Node: repos/cloned_ms_repos/train-ticket/ts-common/src/main/java/edu/fudan/common/entity/TrainType.java:TrainType.<init>
// Node: TrainType
package edu.fudan.common.entity;

import lombok.Data;

import java.util.Locale;

@Data
public class Station {
    private String id;

    private String name;

    private int stayTime;

    public Station(){
        this.name = "";
    }

    public void setName(String name) {
        this.name = name.replace(" ", "").toLowerCase(Locale.ROOT);
    }

    public Station(String name) {
        this.name = name.replace(" ", "").toLowerCase(Locale.ROOT);
    }


    public Station(String name, int stayTime) {
        this.name = name.replace(" ", "").toLowerCase(Locale.ROOT);;
        this.stayTime = stayTime;
    }
}



// Node: repos/cloned_ms_repos/train-ticket/ts-common/src/main/java/edu/fudan/common/entity/Station.java:Station.<init>
// Node: Station
package edu.fudan.common.entity;

import lombok.Data;

import java.io.Serializable;
import java.util.List;
import java.util.UUID;

@Data
public class StationFoodStore implements Serializable{

    private UUID id;

    private String stationName;

    private String storeName;

    private String telephone;

    private String businessTime;

    private double deliveryFee;

    private List<Food> foodList;

    public StationFoodStore(){
        //Default Constructor
    }

}


// Node: repos/cloned_ms_repos/train-ticket/ts-common/src/main/java/edu/fudan/common/entity/StationFoodStore.java:StationFoodStore.<init>
// Node: StationFoodStore
package edu.fudan.common.entity;

import lombok.AllArgsConstructor;
import lombok.Data;


/**
 * @author fdse
 */
@Data
@AllArgsConstructor
public class OrderAlterInfo {
    private String accountId;

    private String previousOrderId;

    private String loginToken;

    private Order newOrderInfo;

    public OrderAlterInfo(){
        newOrderInfo = new Order();
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-common/src/main/java/edu/fudan/common/entity/OrderAlterInfo.java:OrderAlterInfo.<init>
// Node: OrderAlterInfo
// Node: Order
// Node: Assurance
package edu.fudan.common.entity;

import lombok.Data;

import java.io.Serializable;
import java.util.List;
import java.util.UUID;

@Data
public class TrainFood implements Serializable{

    public TrainFood(){
        //Default Constructor
    }

    private UUID id;

    private String tripId;

    private List<Food> foodList;

}


// Node: repos/cloned_ms_repos/train-ticket/ts-common/src/main/java/edu/fudan/common/entity/TrainFood.java:TrainFood.<init>
// Node: TrainFood
package edu.fudan.common.entity;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.UUID;

/**
 * @author fdse
 */
@Data
@AllArgsConstructor
public class PriceConfig {

    private UUID id;

    private String trainType;

    private String routeId;

    private double basicPriceRate;

    private double firstClassPriceRate;

    public PriceConfig() {
        //Empty Constructor
    }

}


// Node: repos/cloned_ms_repos/train-ticket/ts-common/src/main/java/edu/fudan/common/entity/PriceConfig.java:PriceConfig.<init>
// Node: PriceConfig
// Node: Trip
package edu.fudan.common.entity;

import lombok.Data;

import javax.validation.Valid;
import javax.validation.constraints.NotNull;
import java.util.Set;

/**
 * @author fdse
 */
@Data
public class LeftTicketInfo {
    @Valid
    @NotNull
    private Set<Ticket> soldTickets;

    public LeftTicketInfo(){
        //Default Constructor
    }

    @Override
    public String toString() {
        return "LeftTicketInfo{" +
                "soldTickets=" + soldTickets +
                '}';
    }
}


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


// Node: testSearchCheapestResult
// Node: testSearchQuickestResult
// Node: testSearchMinStopStations
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


package com.trainticket.repository;

import com.trainticket.entity.Payment;
import org.springframework.data.repository.CrudRepository;

import java.util.List;
import java.util.Optional;

/**
 * @author fdse
 */
public interface PaymentRepository extends CrudRepository<Payment,String> {

    Optional<Payment> findById(String id);

    Payment findByOrderId(String orderId);

    @Override
    List<Payment> findAll();

    List<Payment> findByUserId(String userId);
}


// Node: repos/cloned_ms_repos/train-ticket/ts-payment-service/src/main/java/com/trainticket/repository/PaymentRepository.java:PaymentRepository.<init>
// Node: findByOrderId
// Node: findByUserId
// Node: Payment
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


// Node: testPay1
// Node: testPay2
// Node: testQuery1
// Node: testQuery2
// Node: testInitPayment1
// Node: verify
// Node: times
// Node: testInitPayment2
// Node: Query
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


// Node: fromString
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


// Node: testCreateNewPriceConfig1
// Node: assertNotNull
// Node: testCreateNewPriceConfig2
// Node: testFindById
// Node: testFindByRouteIdAndTrainType1
// Node: testFindByRouteIdAndTrainType2
// Node: testFindAllPriceConfig1
// Node: testFindAllPriceConfig2
// Node: testDeletePriceConfig1
// Node: testDeletePriceConfig2
// Node: testUpdatePriceConfig1
// Node: testUpdatePriceConfig2
package notification.repository;


import notification.entity.NotifyInfo;
import org.springframework.data.repository.CrudRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface NotifyRepository extends CrudRepository<NotifyInfo, String> {

    Optional<NotifyInfo> findById(String id);

    @Override
    List<NotifyInfo> findAll();

    void deleteById(String id);
}


// Node: repos/cloned_ms_repos/train-ticket/ts-notification-service/src/main/java/notification/repository/NotifyRepository.java:NotifyRepository.<init>
// Node: assertTrue
// Node: assertFalse
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


// Node: deleteOrder
package other.repository;

import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.CrudRepository;
import other.entity.Order;
import org.springframework.stereotype.Repository;
import java.util.ArrayList;
import java.util.Date;
import java.util.Optional;
import java.util.UUID;

/**
 * @author fdse
 */
@Repository
public interface OrderOtherRepository extends CrudRepository<Order, String> {

    /**
     * find order by id
     *
     * @param id id
     * @return Order
     */
//    @Query("{ 'id': ?0 }")
    @Override
    Optional<Order> findById(String id);

    /**
     * find all orders
     *
     * @return ArrayList<Order>
     */
    @Override
    ArrayList<Order> findAll();

    /**
     * find orders by account id
     *
     * @param accountId account id
     * @return ArrayList<Order>
     */
//    @Query("{ 'accountId' : ?0 }")
    ArrayList<Order> findByAccountId(String accountId);

    /**
     * find orders by travel date and train number
     *
     * @param travelDate travel date
     * @param trainNumber train number
     * @return ArrayList<Order>
     */
//    @Query("{ 'travelDate' : ?0 , trainNumber : ?1 }")
    ArrayList<Order> findByTravelDateAndTrainNumber(String travelDate, String trainNumber);

    /**
     * delete order by id
     *
     * @param id id
     * @return null
     */
    @Override
    void deleteById(String id);
}


// Node: repos/cloned_ms_repos/train-ticket/ts-order-other-service/src/main/java/other/repository/OrderOtherRepository.java:OrderOtherRepository.<init>
// Node: findByTravelDateAndTrainNumber
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



// Node: alterOrder
// Node: cancelOrder
package other.entity;

import edu.fudan.common.util.StringUtils;
import lombok.Data;

import java.util.Date;

/**
 * @author fdse
 */
@Data
public class QueryInfo {

    /**
     * account id
     */
    private String loginId;

    private String travelDateStart;

    private String travelDateEnd;

    private String boughtDateStart;

    private String boughtDateEnd;

    private int state;

    private boolean enableTravelDateQuery;

    private boolean enableBoughtDateQuery;

    private boolean enableStateQuery;

    public QueryInfo() {
        //Default Constructor
    }

    public void enableTravelDateQuery(String startTime, String endTime) {
        enableTravelDateQuery = true;
        travelDateStart = startTime;
        travelDateEnd = endTime;
    }

    public void disableTravelDateQuery() {
        enableTravelDateQuery = false;
        travelDateStart = null;
        travelDateEnd = null;
    }

    public void enableBoughtDateQuery(String startTime, String endTime) {
        enableBoughtDateQuery = true;
        boughtDateStart = startTime;
        boughtDateEnd = endTime;
    }

    public void disableBoughtDateQuery() {
        enableBoughtDateQuery = false;
        boughtDateStart = null;
        boughtDateEnd = null;
    }

    public void enableStateQuery(int targetStatus) {
        enableStateQuery = true;
        state = targetStatus;
    }

    public void disableStateQuery() {
        enableTravelDateQuery = false;
        state = -1;
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-order-other-service/src/main/java/other/entity/QueryInfo.java:QueryInfo.<init>
// Node: QueryInfo
// Node: testQueryOrders
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


// Node: testGetSoldTickets1
// Node: testGetSoldTickets2
// Node: testFindOrderById1
// Node: testFindOrderById2
// Node: testCreate1
// Node: testCreate2
// Node: testInitOrder1
// Node: testInitOrder2
// Node: testAlterOrder1
// Node: testAlterOrder2
// Node: setEnableStateQuery
// Node: setEnableBoughtDateQuery
// Node: setEnableTravelDateQuery
// Node: setState
// Node: testSaveChanges1
// Node: testSaveChanges2
// Node: testCancelOrder1
// Node: testCancelOrder2
// Node: testQueryAlreadySoldOrders
// Node: testGetAllOrders1
// Node: testGetAllOrders2
// Node: testModifyOrder1
// Node: testModifyOrder2
// Node: testGetOrderPrice1
// Node: testGetOrderPrice2
// Node: testPayOrder1
// Node: testPayOrder2
// Node: testGetOrderById1
// Node: testGetOrderById2
// Node: testCheckSecurityAboutOrder
// Node: testDeleteOrder1
// Node: testDeleteOrder2
// Node: testAddNewOrder1
// Node: testAddNewOrder2
// Node: testUpdateOrder1
// Node: testUpdateOrder2
package delivery.repository;

import delivery.entity.Delivery;
import org.springframework.data.repository.CrudRepository;

import org.springframework.scheduling.Trigger;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

@Repository
public interface DeliveryRepository extends CrudRepository<Delivery, String> {


    Optional<Delivery> findById(String id);

    Delivery findByOrderId(UUID orderId);

    @Override
    List<Delivery> findAll();

    void deleteById(String id);

    void deleteFoodOrderByOrderId(String id);

}


// Node: repos/cloned_ms_repos/train-ticket/ts-delivery-service/src/main/java/delivery/repository/DeliveryRepository.java:DeliveryRepository.<init>
// Node: deleteFoodOrderByOrderId
// Node: getAllAssurances
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


// Node: deleteAssurance
// Node: deleteByOrderId
// Node: modify
// Node: getAssuranceById
// Node: findAssuranceById
// Node: findAssuranceByOrderId
package assurance.repository;

import assurance.entity.Assurance;
import org.springframework.data.repository.CrudRepository;
import org.springframework.stereotype.Repository;

import javax.transaction.Transactional;
import java.util.ArrayList;
import java.util.Optional;

/**
 * @author fdse
 */
@Repository
public interface AssuranceRepository  extends CrudRepository<Assurance, String> {

    /**
     * find by id
     *
     * @param id id
     * @return Assurance
     */
    Optional<Assurance> findById(String id);

    /**
     * find by order id
     *
     * @param orderId order id
     * @return Assurance
     */
    Assurance findByOrderId(String orderId);

    /**
     * delete by id
     *
     * @param id id
     * @return null
     */
    @Transactional
    void deleteById(String id);

    /**
     * remove assurance by order id
     *
     * @param orderId order id
     * @return null
     */
    @Transactional
    void removeAssuranceByOrderId(String orderId);

    /**
     * find all
     *
     * @return ArrayList<Assurance>
     */
    @Override
    ArrayList<Assurance> findAll();
}


// Node: repos/cloned_ms_repos/train-ticket/ts-assurance-service/src/main/java/assurance/repository/AssuranceRepository.java:AssuranceRepository.<init>
// Node: removeAssuranceByOrderId
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


package assurance.service;

import edu.fudan.common.util.Response;
import org.springframework.http.HttpHeaders;

import javax.transaction.Transactional;
import java.util.UUID;

/**
 * @author fdse
 */
public interface AssuranceService {

    /**
     * find assurance by id
     *
     * @param id id
     * @param headers headers
     * @return Response
     */
    Response findAssuranceById(UUID id, HttpHeaders headers);

    /**
     * find assurance by order id
     *
     * @param orderId order id
     * @param headers headers
     * @return Response
     */
    Response findAssuranceByOrderId(UUID orderId, HttpHeaders headers);

    /**
     * find assurance by type index, order id
     *
     * @param typeIndex type index
     * @param orderId order id
     * @param headers headers
     * @return Response
     */
    Response create(int typeIndex,String orderId , HttpHeaders headers);

    /**
     * delete by order id
     *
     * @param assuranceId assurance id
     * @param headers headers
     * @return Response
     */
    @Transactional
    Response deleteById(UUID assuranceId, HttpHeaders headers);

    /**
     * delete by order id
     *
     * @param orderId order id
     * @param headers headers
     * @return Response
     */
    @Transactional
    Response deleteByOrderId(UUID orderId, HttpHeaders headers);

    /**
     * modify by assurance id, order id, type index
     *
     * @param assuranceId assurace id
     * @param orderId order id
     * @param typeIndex type index
     * @param headers headers
     * @return Response
     */
    Response modify(String assuranceId, String orderId, int typeIndex , HttpHeaders headers);

    /**
     * get all assurances
     *
     * @param headers headers
     * @return Response
     */
    Response getAllAssurances(HttpHeaders headers);

    /**
     * get all assurance types
     *
     * @param headers headers
     * @return Response
     */
    Response getAllAssuranceTypes(HttpHeaders headers);
}


// Node: repos/cloned_ms_repos/train-ticket/ts-assurance-service/src/main/java/assurance/service/AssuranceService.java:AssuranceService.<init>
package assurance.init;

import assurance.entity.Assurance;
import assurance.entity.AssuranceType;
import assurance.entity.AssuranceTypeBean;
import assurance.entity.PlainAssurance;
import assurance.repository.AssuranceRepository;
import assurance.service.AssuranceService;
import edu.fudan.common.util.Response;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.CommandLineRunner;
import org.springframework.stereotype.Component;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

/**
 * @author fdse
 */
@Component
public class InitData implements CommandLineRunner {
    @Autowired
    AssuranceService service;

    @Autowired
    AssuranceRepository repository;

    @Override
    public void run(String... args) throws Exception {
        //do nothing

       /* Assurance assurance1=new Assurance();
        String id="ff8080817b3e4c27017b3e4c3bee0000";
        assurance1.setId(id);
        assurance1.setType(AssuranceType.TRAFFIC_ACCIDENT);
        repository.save(assurance1);

        Assurance res1=repository.findById(id).get();
        System.out.println("ID: " + id + "  orderID: " + res1.getOrderId());  //根据ID查找 ， 打印orderID
        Assurance res2=repository.findByOrderId(res1.getOrderId());
        System.out.println("ID: " + res2.getId() + "  orderID: " + res1.getOrderId());  //根据orderID查找 ， 打印ID

        Assurance assurance2=new Assurance();
        String id2="ff8080817b3e4c27017b3e4c3bee1111";
        assurance2.setId(id2);
        assurance2.setType(AssuranceType.TRAFFIC_ACCIDENT);
        repository.save(assurance2);

        ArrayList<Assurance> res3 = repository.findAll();  //查找所有
        System.out.println("num: " + res3.size());

        repository.deleteById(res3.get(0).getId());  //用ID删除第一个
        System.out.println("delete successfully");
        repository.removeAssuranceByOrderId(res3.get(1).getOrderId());   //用orderID删除第二个
        System.out.println("delete successfully");

        //测试service
        String id_1 = UUID.randomUUID().toString();
        Response r_1 = service.create(1,id_1,null);  //create
        Assurance assurance_1 = (Assurance)r_1.getData();
        String id_2 = UUID.randomUUID().toString();
        Response r_2 = service.create(1,id_2,null);
        Assurance assurance_2 = (Assurance)r_2.getData();

        service.findAssuranceById(UUID.fromString(id_1),null);   //findAssuranceById
        service.findAssuranceByOrderId(UUID.fromString(assurance_2.getOrderId()),null); //findAssuranceByOrderId
        Response r_3 = service.getAllAssurances(null);
        ArrayList<PlainAssurance> data_1 = (ArrayList<PlainAssurance>)r_3.getData();
        System.out.println(data_1.size());
        Response r_4 = service.getAllAssuranceTypes(null);
        List<AssuranceTypeBean> data_2 = (List<AssuranceTypeBean>)r_4.getData();
        System.out.println(data_2.size());

        service.modify(assurance_2.getId(),assurance_2.getOrderId(),2,null);  //modify实际上2不存在日志中error

        service.deleteById(UUID.fromString(assurance_1.getId()),null);   //deleteById
        service.deleteByOrderId(UUID.fromString(assurance_2.getOrderId()),null);  //deleteByOrderId
*/
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-assurance-service/src/main/java/assurance/init/InitData.java:InitData.<init>
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


// Node: testFindAssuranceById1
// Node: testFindAssuranceById2
// Node: testFindAssuranceByOrderId1
// Node: testFindAssuranceByOrderId2
// Node: tesCreate2
// Node: testCreate3
// Node: testDeleteById1
// Node: testDeleteById2
// Node: testDeleteByOrderId1
// Node: testDeleteByOrderId2
// Node: testModify2
// Node: testModify3
// Node: testGetAllAssurances1
// Node: testGetAllAssurances2
// Node: addOrder
package adminorder.service;

import edu.fudan.common.entity.*;
import edu.fudan.common.util.Response;
import org.springframework.http.HttpHeaders;


/**
 * @author fdse
 */
public interface AdminOrderService {

    /**
     * get all orders
     *
     * @param headers headers
     * @return Response
     */
    Response getAllOrders(HttpHeaders headers);

    /**
     * delete order by order id, train number
     *
     * @param orderId order id
     * @param trainNumber train number
     * @param headers headers
     * @return Response
     */
    Response deleteOrder(  String orderId,String trainNumber, HttpHeaders headers);

    /**
     * update order by order
     *
     * @param request request
     * @param headers headers
     * @return Response
     */
    Response updateOrder(Order request, HttpHeaders headers);

    /**
     * add order by order
     *
     * @param request request
     * @param headers headers
     * @return Response
     */
    Response addOrder(Order request, HttpHeaders headers);
}


// Node: repos/cloned_ms_repos/train-ticket/ts-admin-order-service/src/main/java/adminorder/service/AdminOrderService.java:AdminOrderService.<init>
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


// Node: testAddOrder1
// Node: testAddOrder2
package travel2.repository;

import edu.fudan.common.entity.TripId;
import org.springframework.data.repository.CrudRepository;
import org.springframework.stereotype.Repository;

import travel2.entity.Trip;

import java.util.ArrayList;

/**
 * @author fdse
 */
@Repository
public interface TripRepository extends CrudRepository<Trip, TripId> {

    Trip findByTripId(TripId tripId);

    void deleteByTripId(TripId tripId);

    @Override
    ArrayList<Trip> findAll();

    ArrayList<Trip> findByRouteId(String routeId);
}

// Node: repos/cloned_ms_repos/train-ticket/ts-travel2-service/src/main/java/travel2/repository/TripRepository.java:TripRepository.<init>
// Node: findByTripId
// Node: deleteByTripId
// Node: findByRouteId
// Node: TravelInfo
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


// Node: testGetRouteByTripId1
// Node: testGetRouteByTripId2
// Node: testGetTripByRoute2
// Node: testRetrieve1
// Node: testRetrieve2
// Node: testUpdate1
// Node: testUpdate2
// Node: testDelete1
// Node: testDelete2
// Node: testQueryAll1
// Node: testQueryAll2
// Node: testAdminQueryAll1
// Node: testAdminQueryAll2
package order.repository;

import order.entity.Order;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.repository.CrudRepository;
import org.springframework.stereotype.Repository;
import java.util.ArrayList;
import java.util.Date;
import java.util.Optional;
import java.util.UUID;

/**
 * @author fdse
 */
@Repository
public interface OrderRepository extends JpaRepository<Order, String> {

    @Override
    Optional<Order> findById(String id);

    @Override
    ArrayList<Order> findAll();

    ArrayList<Order> findByAccountId(String accountId);

    ArrayList<Order> findByTravelDateAndTrainNumber(String travelDate,String trainNumber);

    @Override
    void deleteById(String id);
}


// Node: repos/cloned_ms_repos/train-ticket/ts-order-service/src/main/java/order/repository/OrderRepository.java:OrderRepository.<init>
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



package order.entity;

import edu.fudan.common.util.StringUtils;
import lombok.Data;

import java.util.Date;

/**
 * @author fdse
 */
@Data
public class OrderInfo {

    /**
     * account id
     */
    private String loginId;

    private String travelDateStart;

    private String travelDateEnd;

    private String boughtDateStart;

    private String boughtDateEnd;

    private int state;

    private boolean enableTravelDateQuery;

    private boolean enableBoughtDateQuery;

    private boolean enableStateQuery;

    public OrderInfo(){
        //Default Constructor
    }

    public String getLoginId() {
        return loginId;
    }

    public void setLoginId(String loginId) {
        this.loginId = loginId;
    }

    public int getState() {
        return state;
    }

    public void enableTravelDateQuery(String startTime, String endTime){
        enableTravelDateQuery = true;
        travelDateStart = startTime;
        travelDateEnd = endTime;
    }

    public void disableTravelDateQuery(){
        enableTravelDateQuery = false;
        travelDateStart = null;
        travelDateEnd = null;
    }

    public void enableBoughtDateQuery(String startTime, String endTime){
        enableBoughtDateQuery = true;
        boughtDateStart = startTime;
        boughtDateEnd = endTime;
    }

    public void disableBoughtDateQuery(){
        enableBoughtDateQuery = false;
        boughtDateStart = null;
        boughtDateEnd = null;
    }

    public void enableStateQuery(int targetStatus){
        enableStateQuery = true;
        state = targetStatus;
    }

    public void disableStateQuery(){
        enableTravelDateQuery = false;
        state = -1;
    }

    public boolean isEnableTravelDateQuery() {
        return enableTravelDateQuery;
    }

    public boolean isEnableBoughtDateQuery() {
        return enableBoughtDateQuery;
    }

    public boolean isEnableStateQuery() {
        return enableStateQuery;
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-order-service/src/main/java/order/entity/OrderInfo.java:OrderInfo.<init>
// Node: OrderInfo
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


package travel.repository;

import edu.fudan.common.entity.TripId;
import org.springframework.data.repository.CrudRepository;
import org.springframework.stereotype.Repository;
import travel.entity.Trip;

import java.util.ArrayList;

/**
 * @author fdse
 */
@Repository
public interface TripRepository extends CrudRepository<Trip, TripId> {

    Trip findByTripId(TripId tripId);

    void deleteByTripId(TripId tripId);

    @Override
    ArrayList<Trip> findAll();

    ArrayList<Trip> findByRouteId(String routeId);
}

// Node: repos/cloned_ms_repos/train-ticket/ts-travel-service/src/main/java/travel/repository/TripRepository.java:TripRepository.<init>
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


// Node: Contacts
package train.repository;

import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.CrudRepository;
import org.springframework.stereotype.Repository;
import train.entity.TrainType;

import java.util.List;
import java.util.Optional;

@Repository
public interface TrainTypeRepository extends CrudRepository<TrainType,String> {

    Optional<TrainType> findById(String id);
    @Override
    List<TrainType> findAll();
    void deleteById(String id);
    TrainType findByName(String name);

    @Query(value="SELECT * from train_type where name in ?1", nativeQuery = true)
    List<TrainType> findByNames(List<String> names);
}


// Node: repos/cloned_ms_repos/train-ticket/ts-train-service/src/main/java/train/repository/TrainTypeRepository.java:TrainTypeRepository.<init>
// Node: findByName
// Node: findByNames
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


// Node: getPriceByWeightAndRegion
package consignprice.repository;

import consignprice.entity.ConsignPrice;
import org.springframework.data.repository.CrudRepository;
import org.springframework.stereotype.Repository;

/**
 * @author fdse
 */
@Repository
public interface ConsignPriceConfigRepository extends CrudRepository<ConsignPrice, String> {

    /**
     * find by index
     *
     * @param index index
     * @return ConsignPrice
     */
//    @Query("{ 'index': ?0 }")
    ConsignPrice findByIndex(int index);

}


// Node: repos/cloned_ms_repos/train-ticket/ts-consign-price-service/src/main/java/consignprice/repository/ConsignPriceConfigRepository.java:ConsignPriceConfigRepository.<init>
// Node: findByIndex
// Node: ConsignPrice
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


// Node: testGetPriceByWeightAndRegion1
// Node: testGetPriceByWeightAndRegion2
// Node: testGetPriceByWeightAndRegion3
// Node: testQueryPriceInformation
// Node: testCreateAndModifyPrice1
// Node: testCreateAndModifyPrice2
package inside_payment.repository;

import inside_payment.entity.Money;
//import org.springframework.data.mongodb.repository.MongoRepository;
import org.springframework.data.repository.CrudRepository;

import java.util.List;

/**
 * @author fdse
 */
public interface AddMoneyRepository extends CrudRepository<Money,String> {

    /**
     * find by user id
     *
     * @param userId user id
     * @return List<Money>
     */
    List<Money> findByUserId(String userId);

    /**
     * find all
     *
     * @return List<Money>
     */
    @Override
    List<Money> findAll();
}


// Node: repos/cloned_ms_repos/train-ticket/ts-inside-payment-service/src/main/java/inside_payment/repository/AddMoneyRepository.java:AddMoneyRepository.<init>
package inside_payment.repository;

import inside_payment.entity.Payment;
//import org.springframework.data.mongodb.repository.MongoRepository;
import org.springframework.data.repository.CrudRepository;

import java.util.List;
import java.util.Optional;

/**
 * @author fdse
 */
public interface PaymentRepository extends CrudRepository<Payment,String> {

    /**
     * find by id
     *
     * @param id id
     * @return Payment
     */
    Optional<Payment> findById(String id);

    /**
     * find by order id
     *
     * @param orderId order id
     * @return List<Payment>
     */
    List<Payment> findByOrderId(String orderId);

    /**
     * find all
     *
     * @return List<Payment>
     */
    @Override
    List<Payment> findAll();

    /**
     * find by user id
     *
     * @param userId user id
     * @return List<Payment>
     */
    List<Payment> findByUserId(String userId);
}


// Node: repos/cloned_ms_repos/train-ticket/ts-inside-payment-service/src/main/java/inside_payment/repository/PaymentRepository.java:PaymentRepository.<init>
// Node: AccountInfo
package inside_payment.entity;

import lombok.Data;

/**
 * @author fdse
 */
@Data
public class AccountInfo {

    private String userId;

    private String money;

    public AccountInfo(){
        //Default Constructor
    }

}


// Node: repos/cloned_ms_repos/train-ticket/ts-inside-payment-service/src/main/java/inside_payment/entity/AccountInfo.java:AccountInfo.<init>
package inside_payment.entity;

import lombok.AllArgsConstructor;
import lombok.Data;

/**
 * @author fdse
 */
@Data
@AllArgsConstructor
public class PaymentInfo {
    public PaymentInfo(){
        //Default Constructor
    }

    private String userId;
    private String orderId;
    private String tripId;
    private String price;

//    public String getOrderId(){
//        return this.orderId;
//    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-inside-payment-service/src/main/java/inside_payment/entity/PaymentInfo.java:PaymentInfo.<init>
// Node: PaymentInfo
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


// Node: testCreateAccount1
// Node: testCreateAccount2
// Node: testAddMoney1
// Node: testAddMoney2
// Node: testQueryPayment1
// Node: testQueryPayment2
// Node: testDrawBack1
// Node: testDrawBack2
// Node: testQueryAddMoney1
// Node: testQueryAddMoney2
package foodsearch.repository;

import foodsearch.entity.FoodOrder;

import org.springframework.data.repository.CrudRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

@Repository
public interface FoodOrderRepository extends CrudRepository<FoodOrder, String> {

    Optional<FoodOrder> findById(String id);

    FoodOrder findByOrderId(String orderId);

    @Override
    List<FoodOrder> findAll();

    void deleteById(UUID id);

    void deleteFoodOrderByOrderId(String id);

}


// Node: repos/cloned_ms_repos/train-ticket/ts-food-service/src/main/java/foodsearch/repository/FoodOrderRepository.java:FoodOrderRepository.<init>
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


// Node: testCreateFoodOrder1
// Node: testCreateFoodOrder2
// Node: testDeleteFoodOrder1
// Node: testDeleteFoodOrder2
// Node: testFindAllFoodOrder1
// Node: testFindAllFoodOrder2
// Node: testUpdateFoodOrder1
// Node: testUpdateFoodOrder2
// Node: testFindByOrderId1
// Node: testFindByOrderId2
package route.repository;

import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.CrudRepository;
import org.springframework.stereotype.Repository;
import route.entity.Route;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

/**
 * @author fdse
 */
@Repository
public interface RouteRepository extends CrudRepository<Route, String> {

    /**
     * find route by id
     *
     * @param id id
     * @return Route
     */
    Optional<Route> findById(String id);

    /**
     * find route by ids
     *
     * @param ids ids
     * @return Route
     */
    @Query(value="SELECT * from route where id in ?1", nativeQuery = true)
    List<Route> findByIds(List<String> ids);

    /**
     * find all routes
     *
     * @return ArrayList<Route>
     */
    @Override
    ArrayList<Route> findAll();

    /**
     * remove route via id
     *
     * @param id id
     */
    void removeRouteById(String id);

    /**
     * return route with id from StartStationId to TerminalStationId
     *
     * @param startStation  Start Station Name
     * @param endStation  end Station Name
     * @return ArrayList<Route>
     */
    ArrayList<Route> findByStartStationAndEndStation(String startStation, String endStation);

}


// Node: repos/cloned_ms_repos/train-ticket/ts-route-service/src/main/java/route/repository/RouteRepository.java:RouteRepository.<init>
// Node: removeRouteById
// Node: findByStartStationAndEndStation
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


// Node: testCreateAndModify2
// Node: testCreateAndModify3
// Node: testDeleteRoute1
// Node: testDeleteRoute2
// Node: testGetRouteById1
// Node: testGetRouteById2
// Node: testGetRouteByStartAndTerminal1
// Node: testGetRouteByStartAndTerminal2
// Node: testGetAllRoutes1
// Node: testGetAllRoutes2
// Node: updateConsignRecord
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


// Node: queryByAccountId
// Node: queryByOrderId
// Node: findByConsignee
// Node: queryByConsignee
package consign.repository;

import consign.entity.ConsignRecord;
import org.springframework.data.repository.CrudRepository;
import org.springframework.stereotype.Repository;

import java.util.ArrayList;
import java.util.Optional;

/**
 * @author fdse
 */
@Repository
public interface ConsignRepository extends CrudRepository<ConsignRecord, String> {

    /**
     * find by account id
     *
     * @param accountId account id
     * @return ArrayList<ConsignRecord>
     */
    ArrayList<ConsignRecord> findByAccountId(String accountId);

    /**
     * find by order id
     *
     * @param accountId account id
     * @return ConsignRecord
     */
    ConsignRecord findByOrderId(String accountId);

    /**
     * find by consignee
     *
     * @param consignee consignee
     * @return ArrayList<ConsignRecord>
     */
    ArrayList<ConsignRecord> findByConsignee(String consignee);

    /**
     * find by id
     *
     * @param id id
     * @return ConsignRecord
     */
    Optional<ConsignRecord> findById(String id);
}


// Node: repos/cloned_ms_repos/train-ticket/ts-consign-service/src/main/java/consign/repository/ConsignRepository.java:ConsignRepository.<init>
package consign.service;

import consign.entity.Consign;
import org.springframework.http.HttpHeaders;

import edu.fudan.common.util.Response;

import java.util.UUID;

/**
 * @author fdse
 */
public interface ConsignService {

    /**
     * insert consign record
     *
     * @param consignRequest consign request
     * @param headers headers
     * @return Response
     */
    Response insertConsignRecord(Consign consignRequest, HttpHeaders headers);

    /**
     * update consign record
     *
     * @param consignRequest consign request
     * @param headers headers
     * @return Response
     */
    Response updateConsignRecord(Consign consignRequest, HttpHeaders headers);

    /**
     * query by account id
     *
     * @param accountId account id
     * @param headers headers
     * @return Response
     */
    Response queryByAccountId(UUID accountId, HttpHeaders headers);

    /**
     * query by order id
     *
     * @param orderId order id
     * @param headers headers
     * @return Response
     */
    Response queryByOrderId(UUID orderId, HttpHeaders headers);

    /**
     * query by consignee
     *
     * @param consignee consignee
     * @param headers headers
     * @return Response
     */
    Response queryByConsignee(String consignee, HttpHeaders headers);
}


// Node: repos/cloned_ms_repos/train-ticket/ts-consign-service/src/main/java/consign/service/ConsignService.java:ConsignService.<init>
// Node: ConsignRecord
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


// Node: testInsertConsignRecord
// Node: testUpdateConsignRecord1
// Node: testUpdateConsignRecord2
// Node: testQueryByAccountId1
// Node: testQueryByAccountId2
// Node: testQueryByOrderId1
// Node: testQueryByOrderId2
// Node: testQueryByConsignee1
// Node: testQueryByConsignee2
// Node: calculateRefund
package cancel.service;

import edu.fudan.common.util.Response;
import org.springframework.http.HttpHeaders;

/**
 * @author fdse
 */
public interface CancelService {

    /**
     * cancel order by order id, login id
     *
     * @param orderId order id
     * @param loginId login id
     * @param headers headers
     * @throws  Exception
     * @return Response
     */
    Response cancelOrder(String orderId, String loginId, HttpHeaders headers);

    /**
     * calculate refund by login id
     *
     * @param orderId order id
     * @param headers headers
     * @return Response
     */
    Response calculateRefund(String orderId, HttpHeaders headers);

}


// Node: repos/cloned_ms_repos/train-ticket/ts-cancel-service/src/main/java/cancel/service/CancelService.java:CancelService.<init>
// Node: getOrderByIdFromOrder
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


// Node: testCalculateRefund1
// Node: testCalculateRefund2
// Node: Config
// Node: PriceInfo
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


// Node: testDeleteContact
// Node: testModifyContact
// Node: testAddContact


package org.myproject.ms.monitoring;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;


public class Log {
	
	private final long timestamp;

	
	private final String event;

	@JsonCreator
	public Log(
			@JsonProperty(value = "timestamp", required = true) long timestamp,
			@JsonProperty(value = "event", required = true) String event
	) {
		if (event == null) throw new NullPointerException("event");
		this.timestamp = timestamp;
		this.event = event;
	}

	public long getTimestamp() {
		return this.timestamp;
	}

	public String getEvent() {
		return this.event;
	}

	@Override
	public boolean equals(Object o) {
		if (o == this) {
			return true;
		}
		if (o instanceof Log) {
			Log that = (Log) o;
			return (this.timestamp == that.timestamp)
					&& (this.event.equals(that.event));
		}
		return false;
	}

	@Override
	public int hashCode() {
		int h = 1;
		h *= 1000003;
		h ^= (this.timestamp >>> 32) ^ this.timestamp;
		h *= 1000003;
		h ^= this.event.hashCode();
		return h;
	}

	@Override public String toString() {
		return "Log{" +
				"timestamp=" + this.timestamp +
				", event='" + this.event + '\'' +
				'}';
	}
}


package org.services.analysis;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;

/**
 * Created by Administrator on 2017/7/22.
 */
public class Span {
    private String traceId;
    private String spanId;
    private String parentId;
    private String spanname;
    private List<String> childs;
    private List<HashMap<String,String>> logs;

    public Span(String traceId, String spanId, String parentId, String spanname) {
        this.traceId = traceId;
        this.spanId = spanId;
        this.parentId = parentId;
        this.spanname = spanname;
        logs = new ArrayList<HashMap<String,String>>();
    }

    public void addLog(HashMap<String,String> log){
        logs.add(log);
    }

    public List<HashMap<String,String>> getLogs(){
        return logs;
    }

    public String getTraceId() {
        return traceId;
    }

    public String getSpanId() {
        return spanId;
    }

    public String getParentId() {
        return parentId;
    }

    public List<String> getChilds() {
        return childs;
    }

    public void setChilds(List<String> childs) {
        this.childs = childs;
    }

    public void addChild(String childId){
        childs.add(childId);
    }

    public String getSpanname() {
        return spanname;
    }

    public void setSpanname(String spanname) {
        this.spanname = spanname;
    }
}


// Node: addChild
// Node: listTrainFood
// Node: listTrainFoodByTripId
package trainFood.repository;

import org.springframework.data.repository.CrudRepository;
import org.springframework.stereotype.Repository;
import trainFood.entity.TrainFood;

import java.util.List;
import java.util.UUID;

@Repository
public interface TrainFoodRepository extends CrudRepository<TrainFood, String> {

    TrainFood findById(UUID id);

    @Override
    List<TrainFood> findAll();


    TrainFood findByTripId(String tripId);

    void deleteById(UUID id);
}


// Node: repos/cloned_ms_repos/train-ticket/ts-train-food-service/src/main/java/trainFood/repository/TrainFoodRepository.java:TrainFoodRepository.<init>
package trainFood.service;

import edu.fudan.common.util.Response;
import org.springframework.http.HttpHeaders;
import trainFood.entity.*;

public interface TrainFoodService {
    TrainFood createTrainFood(TrainFood tf, HttpHeaders headers);

    Response listTrainFood(HttpHeaders headers);

    Response listTrainFoodByTripId(String tripId, HttpHeaders headers);
}


// Node: repos/cloned_ms_repos/train-ticket/ts-train-food-service/src/main/java/trainFood/service/TrainFoodService.java:TrainFoodService.<init>
// Node: createTrainFood
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


// Node: testTicketExecute1
// Node: testTicketExecute2
// Node: testTicketCollect1
// Node: testTicketCollect2
package fdse.microservice.repository;

import fdse.microservice.entity.Station;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.CrudRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface StationRepository extends CrudRepository<Station,String> {

    Station findByName(String name);

    @Query(value="SELECT * from station where name in ?1", nativeQuery = true)
    List<Station> findByNames(List<String> names);

    Optional<Station> findById(String id);

    @Override
    List<Station> findAll();
}


// Node: repos/cloned_ms_repos/train-ticket/ts-station-service/src/main/java/fdse/microservice/repository/StationRepository.java:StationRepository.<init>
// Node: exist
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


// Node: setStayTime
package fdse.microservice.init;

import fdse.microservice.entity.Station;
import fdse.microservice.service.StationService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.CommandLineRunner;
import org.springframework.stereotype.Component;

@Component
public class InitData implements CommandLineRunner {

    @Autowired
    StationService service;

    @Override
    public void run(String... args) throws Exception{
        Station info = new Station();
        info.setName("Shang Hai");
        info.setStayTime(10);
        service.create(info,null);

        info = new Station();
        info.setName("Shang Hai Hong Qiao");
        info.setStayTime(10);
        service.create(info,null);

        info = new Station();
        info.setName("Tai Yuan");
        info.setStayTime(5);
        service.create(info,null);

        info = new Station();
        info.setName("Bei Jing");
        info.setStayTime(10);
        service.create(info,null);

        info = new Station();
        info.setName("Nan Jing");
        info.setStayTime(8);
        service.create(info,null);

        info = new Station();
        info.setName("Shi Jia Zhuang");
        info.setStayTime(8);
        service.create(info,null);

        info = new Station();
        info.setName("Xu Zhou");
        info.setStayTime(7);
        service.create(info,null);

        info = new Station();
        info.setName("Ji Nan");
        info.setStayTime(5);
        service.create(info,null);

        info = new Station();
        info.setName("Hang Zhou");
        info.setStayTime(9);
        service.create(info,null);

        info = new Station();
        info.setName("Jia Xing Nan");
        info.setStayTime(2);
        service.create(info,null);

        info = new Station();
        info.setName("Zhen Jiang");
        info.setStayTime(2);
        service.create(info,null);

        info = new Station();
        info.setName("Wu Xi");
        info.setStayTime(3);
        service.create(info,null);

        info = new Station();
        info.setName("Su Zhou");
        info.setStayTime(3);
        service.create(info,null);

    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-station-service/src/main/java/fdse/microservice/init/InitData.java:InitData.<init>
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


// Node: testExist1
// Node: testExist2
// Node: testQueryForId1
// Node: testQueryForId2
// Node: testQueryForIdBatch2
// Node: testQueryById1
// Node: testQueryById2
// Node: testQueryByIdBatch2
// Node: addTravel
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


// Node: testGetAllTravels1
// Node: testGetAllTravels2
// Node: testAddTravel1
// Node: testAddTravel2
// Node: testAddTravel3
// Node: testAddTravel4
// Node: testUpdateTravel1
// Node: testUpdateTravel2
// Node: testDeleteTravel1
// Node: testDeleteTravel2
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


// Node: testGetTransferSearch
// Node: testGetCheapest
// Node: transferStationIdToStationName
// Node: testGetQuickest
// Node: testGetMinStation
// Node: findByUserName
package user.repository;

import org.springframework.data.repository.CrudRepository;
import org.springframework.stereotype.Repository;
import user.entity.User;

import java.util.List;
import java.util.UUID;

/**
 * @author fdse
 */
@Repository
public interface UserRepository extends CrudRepository<User, String> {

    User findByUserName(String userName);

    User findByUserId(String userId);

    void deleteByUserId(String userId);

    @Override
    List<User> findAll();
}


// Node: repos/cloned_ms_repos/train-ticket/ts-user-service/src/main/java/user/repository/UserRepository.java:UserRepository.<init>
package user.entity;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.hibernate.annotations.GenericGenerator;

import javax.persistence.Column;
import javax.persistence.Entity;
import javax.persistence.GeneratedValue;
import javax.persistence.Id;
import java.util.UUID;

/**
 * @author fdse
 */
@Data
@Builder
@AllArgsConstructor
@Entity
public class User {

    //    private UUID userId;
    @Id
    @Column(length = 36, name = "user_id")
    private String userId;
    @Column(name = "user_name")
    private String userName;
    private String password;

    private int gender;
    @Column(name = "document_type")
    private int documentType;
    @Column(name = "document_num")
    private String documentNum;

    private String email;

    public User() {
        this.userId = UUID.randomUUID().toString();
    }

}


// Node: repos/cloned_ms_repos/train-ticket/ts-user-service/src/main/java/user/entity/User.java:User.<init>
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


// Node: testGetAllUsers1
// Node: testGetAllUsers2
// Node: testFindByUserName1
// Node: testFindByUserName2
// Node: testFindByUserId1
// Node: testFindByUserId2
// Node: testDeleteUser1
// Node: testDeleteUser2
// Node: testUpdateUser1
// Node: testUpdateUser2
// Node: testDeleteUserAuth
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


// Node: setValue
// Node: testGetLeftTicketOfInterva2
// Node: addNewSecurityConfig
// Node: deleteSecurityConfig
package security.repository;


import org.springframework.data.repository.CrudRepository;
import org.springframework.stereotype.Repository;
import security.entity.SecurityConfig;
import java.util.ArrayList;
import java.util.Optional;

/**
 * @author fdse
 */
@Repository
public interface SecurityRepository extends CrudRepository<SecurityConfig,String> {


    SecurityConfig findByName(String name);


    Optional<SecurityConfig> findById(String id);

    @Override
    ArrayList<SecurityConfig> findAll();

    void deleteById(String id);
}


// Node: repos/cloned_ms_repos/train-ticket/ts-security-service/src/main/java/security/repository/SecurityRepository.java:SecurityRepository.<init>
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


// Node: SecurityConfig
// Node: setDescription
// Node: getDescription
package security.init;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.CommandLineRunner;
import org.springframework.stereotype.Component;
import security.entity.SecurityConfig;
import security.service.SecurityService;

/**
 * @author fdse
 */
@Component
public class InitData implements CommandLineRunner {

    @Autowired
    private SecurityService securityService;

    @Override
    public void run(String... args) throws Exception {

        // a man can not buy too many tickets in one hour
        SecurityConfig info1 = new SecurityConfig();
        info1.setName("max_order_1_hour");
        info1.setValue(Integer.MAX_VALUE + "");
        info1.setDescription("Max in 1 hour");
        securityService.addNewSecurityConfig(info1,null);
        SecurityConfig info2 = new SecurityConfig();
        info2.setName("max_order_not_use");
        info2.setValue(Integer.MAX_VALUE + "");
        info2.setDescription("Max not used");
        securityService.addNewSecurityConfig(info2,null);
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-security-service/src/main/java/security/init/InitData.java:InitData.<init>
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


// Node: testFindAllSecurityConfig1
// Node: testFindAllSecurityConfig2
// Node: testAddNewSecurityConfig1
// Node: testAddNewSecurityConfig2
// Node: testModifySecurityConfig1
// Node: testModifySecurityConfig2
// Node: testDeleteSecurityConfig1
// Node: testDeleteSecurityConfig2
package contacts.repository;

import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.CrudRepository;
import org.springframework.stereotype.Repository;
import contacts.entity.Contacts;

import java.util.*;

/**
 * @author fdse
 */
@Repository
public interface ContactsRepository extends CrudRepository<Contacts, String> {

    /**
     * find by id
     *
     * @param id id
     * @return Contacts
     */
    Optional<Contacts> findById(String id);

    /**
     * find by account id
     *
     * @param accountId account id
     * @return ArrayList<Contacts>
     */
//    @Query("{ 'accountId' : ?0 }")
    ArrayList<Contacts> findByAccountId(String accountId);

    /**
     * delete by id
     *
     * @param id id
     * @return null
     */
    void deleteById(String id);

    /**
     * find all
     *
     * @return ArrayList<Contacts>
     */
    @Override
    ArrayList<Contacts> findAll();

    @Query(value="SELECT * FROM contacts WHERE account_id = ?1 AND document_number = ?2 AND document_type = ?3", nativeQuery = true)
    Contacts findByAccountIdAndDocumentTypeAndDocumentType(String account_id, String document_number, int document_type);

}


// Node: repos/cloned_ms_repos/train-ticket/ts-contacts-service/src/main/java/contacts/repository/ContactsRepository.java:ContactsRepository.<init>
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


// Node: testFindContactsById1
// Node: testFindContactsById2
// Node: empty
// Node: testCreateContacts1
// Node: testCreateContacts2
// Node: testModify1
// Node: testGetAllContacts1
// Node: testGetAllContacts2
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


// Node: listFoodStores
// Node: getFoodStoresByStationNames
package food.repository;

import food.entity.StationFoodStore;
import org.springframework.data.repository.CrudRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

@Repository
public interface StationFoodRepository extends CrudRepository<StationFoodStore, String> {

    @Override
    Optional<StationFoodStore> findById(String id);

    List<StationFoodStore> findByStationName(String stationName);
    List<StationFoodStore> findByStationNameIn(List<String> stationNames);


    @Override
    List<StationFoodStore> findAll();

    @Override
    void deleteById(String id);
}


// Node: repos/cloned_ms_repos/train-ticket/ts-station-food-service/src/main/java/food/repository/StationFoodRepository.java:StationFoodRepository.<init>
// Node: findByStationName
// Node: findByStationNameIn
// Node: createFoodStore
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


package food.service;

import edu.fudan.common.util.Response;
import food.entity.*;
import org.springframework.http.HttpHeaders;

import java.util.List;

public interface StationFoodService {

    // create data
    Response createFoodStore(StationFoodStore fs, HttpHeaders headers);

//    TrainFood createTrainFood(TrainFood tf, HttpHeaders headers);

    // query all food
    Response listFoodStores(HttpHeaders headers);

//    Response listTrainFood(HttpHeaders headers);

    // query according id
    Response listFoodStoresByStationName(String stationName, HttpHeaders headers);

//    Response listTrainFoodByTripId(String tripId, HttpHeaders headers);

    Response getStaionFoodStoreById(String id);

    Response getFoodStoresByStationNames(List<String> stationNames);

}


// Node: repos/cloned_ms_repos/train-ticket/ts-station-food-service/src/main/java/food/service/StationFoodService.java:StationFoodService.<init>
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


// Node: testCreateFoodStore1
// Node: testCreateFoodStore2
// Node: testCreateTrainFood1
// Node: testCreateTrainFood2
// Node: testListFoodStores1
// Node: testListFoodStores2
// Node: testListTrainFood1
// Node: testListTrainFood2
// Node: testListFoodStoresByStationName1
// Node: testListFoodStoresByStationName2
// Node: testListTrainFoodByTripId1
// Node: testListTrainFoodByTripId2
// Node: testGetFoodStoresByStationNames1
// Node: testGetFoodStoresByStationNames2
package config.repository;

import config.entity.Config;
import org.springframework.data.repository.CrudRepository;

import java.util.List;

/**
 * @author fdse
 */
public interface ConfigRepository extends CrudRepository<Config, String> {

    /**
     * find by name
     *
     * @param name name
     * @return Config
     */
    Config findByName(String name);

    /**
     * find all
     *
     * @return List<Config>
     */
    @Override
    List<Config> findAll();

    /**
     * delete by name
     *
     * @param name name
     * @return null
     */
    void deleteByName(String name);
}


// Node: repos/cloned_ms_repos/train-ticket/ts-config-service/src/main/java/config/repository/ConfigRepository.java:ConfigRepository.<init>
// Node: deleteByName
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


package config.init;

import config.entity.Config;
import config.service.ConfigService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.CommandLineRunner;
import org.springframework.stereotype.Component;

/**
 * @author fdse
 */
@Component
public class InitData implements CommandLineRunner{

    @Autowired
    ConfigService service;

    @Override
    public void run(String... args) throws Exception {
        Config config = new Config();

        config.setName("DirectTicketAllocationProportion");
        config.setValue("0.5");
        config.setDescription("Allocation Proportion Of The Direct Ticket - From Start To End");
        service.create(config,null);

    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-config-service/src/main/java/config/init/InitData.java:InitData.<init>
package config.entity;

import lombok.Data;
import javax.persistence.Id;

import javax.persistence.Entity;
import javax.validation.Valid;
import javax.validation.constraints.NotNull;

/**
 * @author fdse
 */
@Data
@Entity
public class Config {
    @Valid
    @Id
    @NotNull
    private String name;

    @Valid
    @NotNull
    private String value;

    @Valid
    private String description;

    public Config() {
        this.name = "";
        this.value = "";
    }

    public Config(String name, String value, String description) {
        this.name = name;
        this.value = value;
        this.description = description;
    }

}


// Node: repos/cloned_ms_repos/train-ticket/ts-config-service/src/main/java/config/entity/Config.java:Config.<init>
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


