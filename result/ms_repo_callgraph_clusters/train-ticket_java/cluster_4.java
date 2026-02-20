// Cluster 4

// Node: info
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


// Node: getServiceUrl
// Node: HttpEntity
// Node: exchange
// Node: getBody
// Node: getStatus
// Node: getFirst
// Node: set
package waitorder.utils;

import edu.fudan.common.entity.Contacts;
import edu.fudan.common.util.Response;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.ResponseEntity;
import org.springframework.web.client.RestTemplate;
import waitorder.entity.WaitListOrderStatus;
import waitorder.entity.WaitListOrderVO;
import waitorder.service.WaitListOrderService;

import java.util.Date;
import java.util.concurrent.TimeUnit;

public class PollThread extends Thread{

    private Date waitUntil;

    private WaitListOrderVO waitListOrderVO;

    private HttpHeaders httpHeaders;

    private RestTemplate restTemplate;

    private WaitListOrderService waitListOrderService;

    final static Integer INTERVAL_MINUTES=5;

    public PollThread(Date waitUntilTime,WaitListOrderService service, WaitListOrderVO order, RestTemplate template, HttpHeaders headers){
        restTemplate=template;
        httpHeaders=headers;
        waitListOrderVO=order;
        waitListOrderService =service;
        waitUntil=waitUntilTime;
    }


    @Override
    public void run() {
        String service_url=getServiceUrl("ts-preserve-service");
        HttpEntity requestEntityPreserve = new HttpEntity(waitListOrderVO,httpHeaders);

        //TODO compare with waitUntilTime
        while(true){
            long currentTime=System.currentTimeMillis();
            if(waitUntil.getTime()>currentTime){
                // expired
                waitListOrderService.modifyWaitListOrderStatus(WaitListOrderStatus.EXPIRED.getCode(), waitListOrderVO.getAccountId());
                break;
            }
            Response postResult=doPreserve(service_url,requestEntityPreserve);
            if(postResult.getStatus()==0){
                //预定失败
                try {
                    TimeUnit.MINUTES.sleep(INTERVAL_MINUTES);
                } catch (InterruptedException e) {
                    e.printStackTrace();
                }
            } else{
                // preserve success
                waitListOrderService.modifyWaitListOrderStatus(WaitListOrderStatus.COLLECTED.getCode(),waitListOrderVO.getAccountId());
                break;
            }
        }
    }

    private String getServiceUrl(String serviceName) {
        return "http://" + serviceName;
    }

    private Response doPreserve(String url, HttpEntity requestParam){
        ResponseEntity<Response<Contacts>> rePostPreserveResult = restTemplate.exchange(
                url + "/api/v1/contactservice/preserve",
                HttpMethod.POST,
                requestParam,
                new ParameterizedTypeReference<Response<Contacts>>() {
                });
        return rePostPreserveResult.getBody();
    }

}


// Node: doPreserve
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


// Node: warn
// Node: getData
// Node: isEmpty
// Node: setTrainNumber
package auth.repository;

import auth.entity.User;
import org.springframework.data.repository.CrudRepository;

import java.util.Optional;
import java.util.UUID;

/**
 * @author fdse
 */
public interface UserRepository extends CrudRepository<User, String> {

    /**
     * find by username
     *
     * @param username username
     * @return Optional<User>
     */
    Optional<User> findByUsername(String username);

    /**
     * delete by user id
     *
     * @param userId user id
     * @return null
     */
    void deleteByUserId(String userId);
}


// Node: repos/cloned_ms_repos/train-ticket/ts-auth-service/src/main/java/auth/repository/UserRepository.java:UserRepository.<init>
// Node: findByUsername
// Node: asList
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


// Node: getVerificationCode
// Node: orElseThrow
// Node: TokenDto
package auth.security;

import auth.constant.InfoConstant;
import auth.repository.UserRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.stereotype.Component;

import java.text.MessageFormat;

/**
 * @author fdse
 */
@Component("userDetailServiceImpl")
public class UserDetailsServiceImpl implements UserDetailsService {

    @Autowired
    private UserRepository userRepository;

    private static final Logger LOGGER = LoggerFactory.getLogger(UserDetailsServiceImpl.class);

    @Override
    public UserDetails loadUserByUsername(String s) throws UsernameNotFoundException {
        LOGGER.info("[loadUserByUsername][load UsernamePasswordAuthenticationToken][username: {}]", s);
        return userRepository.findByUsername(s)
                .orElseThrow(() -> new UsernameNotFoundException(
                        MessageFormat.format(InfoConstant.USER_NAME_NOT_FOUND_1, s)
                ));
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-auth-service/src/main/java/auth/security/UserDetailsServiceImpl.java:UserDetailsServiceImpl.<init>
// Node: Component
// Node: loadUserByUsername
// Node: UsernameNotFoundException
// Node: conveterObject
package edu.fudan.common.entity;

import edu.fudan.common.util.StringUtils;
import lombok.AllArgsConstructor;
import lombok.Data;

import javax.validation.Valid;
import javax.validation.constraints.NotNull;
import java.util.Date;
import java.util.List;

/**
 * @author fdse
 */
@Data
@AllArgsConstructor
public class Seat {
    @Valid
    @NotNull
    private String travelDate;

    @Valid
    @NotNull
    private String trainNumber;


    @Valid
    @NotNull
    private String startStation;

    @Valid
    @NotNull
    private String destStation;

    @Valid
    @NotNull
    private int seatType;

    private int totalNum;

    private List<String> stations;

    public Seat(){
        //Default Constructor
        this.travelDate = "";
        this.trainNumber = "";
        this.startStation = "";
        this.destStation = "";
        this.seatType = 0;
        this.totalNum = 0;
        this.stations = null;
    }


}


// Node: repos/cloned_ms_repos/train-ticket/ts-common/src/main/java/edu/fudan/common/entity/Seat.java:Seat.<init>
// Node: Seat
// Node: charAt
package edu.fudan.common.entity;

import lombok.Data;

/**
 * @author fdse
 */
@Data
public class AdminTrip {
    private Trip trip;
    private TrainType trainType;
    private Route route;

    public AdminTrip(){
        //Default Constructor
    }

}


// Node: repos/cloned_ms_repos/train-ticket/ts-common/src/main/java/edu/fudan/common/entity/AdminTrip.java:AdminTrip.<init>
// Node: AdminTrip
package edu.fudan.common.entity;

import lombok.Data;

import java.util.Date;

/**
 * @author fdse
 */
@Data
public class SoldTicket {

    private Date travelDate;

    private String trainNumber;

    private int noSeat;

    private int businessSeat;

    private int firstClassSeat;

    private int secondClassSeat;

    private int hardSeat;

    private int softSeat;

    private int hardBed;

    private int softBed;

    private int highSoftBed;

    public SoldTicket(){
        noSeat = 0;
        businessSeat = 0;
        firstClassSeat = 0;
        secondClassSeat = 0;
        hardSeat = 0;
        softSeat = 0;
        hardBed = 0;
        softBed = 0;
        highSoftBed = 0;
    }

}


// Node: repos/cloned_ms_repos/train-ticket/ts-common/src/main/java/edu/fudan/common/entity/SoldTicket.java:SoldTicket.<init>
// Node: SoldTicket
package edu.fudan.common.entity;

import lombok.Data;

/**
 * @author fdse
 */
@Data
public class PaymentDifferenceInfo {

    private String orderId;

    private String tripId;

    private String userId;

    private String price;

    public PaymentDifferenceInfo(){
        //Default Constructor
    }

}


// Node: repos/cloned_ms_repos/train-ticket/ts-common/src/main/java/edu/fudan/common/entity/PaymentDifferenceInfo.java:PaymentDifferenceInfo.<init>
// Node: PaymentDifferenceInfo
package edu.fudan.common.entity;

import edu.fudan.common.util.Response;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

/**
 * @author fdse
 */
@Data
@NoArgsConstructor
public class RouteInfo {
    private String loginId;

    private String startStation;

    private String endStation;

    private String stationList;

    private String distanceList;

    private String id;

    public List<String> getStations(){
        String[] stations = stationList.split(",");
        return Arrays.asList(stations);
    }

    public List<String> getDistances(){
        String[] distances = distanceList.split(",");
        return Arrays.asList(distances);
    }

}


// Node: getStations
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


// Node: indexOf
// Node: getRouteByRouteId
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

// Node: getStatusCode
// Node: getStatusCodeValue
// Node: checkStationsExists
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


// Node: assertNull
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


// Node: send
// Node: convertAndSend
package notification.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

/**
 * @author fdse
 */
@Component
@ConfigurationProperties("email")
public class EmailProperties {

    private String host;
    private String port;
    private String username;
    private String password;

    public void setHost(String host) {
        this.host = host;
    }

    public String getHost() {
        return host;
    }

    public void setPort(String port) {
        this.port = port;
    }

    public String getPort() {
        return port;
    }

    public void setUsername(String username) {
        this.username = username;
    }

    public String getUsername() {
        return username;
    }

    public void setPassword(String password) {
        this.password = password;
    }

    public String getPassword() {
        return password;
    }

}


// Node: getPort
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


// Node: queryForStationId
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


// Node: checkStationExists
// Node: queryTrainTypeByName
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


// Node: testCheckStationExists
// Node: testQueryTrainType
// Node: setDestStation
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



// Node: setNoSeat
// Node: getNoSeat
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



// Node: getTrainTypeByName
// Node: setSeatType
// Node: setTotalNum
// Node: setStations
package travel2.entity;

import edu.fudan.common.entity.Route;
import edu.fudan.common.entity.TrainType;
import lombok.Data;

/**
 * @author fdse
 */
@Data
public class AdminTrip {
    private Trip trip;
    private TrainType trainType;
    private Route route;

    public AdminTrip(){
        //Default Constructor
    }

}


// Node: repos/cloned_ms_repos/train-ticket/ts-travel2-service/src/main/java/travel2/entity/AdminTrip.java:AdminTrip.<init>
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


package travel.entity;

import edu.fudan.common.entity.TrainType;
import edu.fudan.common.entity.Route;
import lombok.Data;


/**
 * @author fdse
 */
@Data
public class AdminTrip {
    private Trip trip;
    private TrainType trainType;
    private Route route;

    public AdminTrip(){
        //Default Constructor
    }

}


// Node: repos/cloned_ms_repos/train-ticket/ts-travel-service/src/main/java/travel/entity/AdminTrip.java:AdminTrip.<init>
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


// Node: dipatchSeat
// Node: createOrder
// Node: getAccount
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


// Node: testDipatchSeat
// Node: testSendEmail
// Node: testGetAccount
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


// Node: queryAddMoney
package inside_payment.async;

import java.util.concurrent.Future;
import inside_payment.entity.OutsidePaymentInfo;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.scheduling.annotation.Async;
import org.springframework.scheduling.annotation.AsyncResult;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;

/**
 * @author fdse
 */
@Component  
public class AsyncTask {
    
    @Autowired
	private RestTemplate restTemplate;

    private static final Logger LOGGER = LoggerFactory.getLogger(AsyncTask.class);

    @Async("mySimpleAsync")
    public Future<Boolean> sendAsyncCallToPaymentService(OutsidePaymentInfo outsidePaymentInfo) {
        AsyncTask.LOGGER.info("[sendAsyncCallToPaymentService][Inside Payment Service, Async Task,Begin]");
        Boolean value = restTemplate.getForObject("http://rest-service-external:16100/greet", Boolean.class);
        AsyncTask.LOGGER.info("[sendAsyncCallToPaymentService][Inside Payment Service, Async Task][Receive call Value directly back: {}]", value);
        return new AsyncResult<>(value);
    }
    
}  


// Node: sendAsyncCallToPaymentService
// Node: getForObject
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


// Node: AllTripFood
// Node: setTrainFoodList
// Node: setFoodStoreListMap
package foodsearch.entity;

import edu.fudan.common.entity.Food;
import edu.fudan.common.entity.StationFoodStore;
import edu.fudan.common.entity.TrainFood;
import lombok.Data;

import java.util.List;
import java.util.Map;

@Data
public class AllTripFood {

    private List<Food> trainFoodList;

    private Map<String, List<StationFoodStore>>  foodStoreListMap;

    public AllTripFood(){
        //Default Constructor
    }

}


// Node: repos/cloned_ms_repos/train-ticket/ts-food-service/src/main/java/foodsearch/entity/AllTripFood.java:AllTripFood.<init>
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


// Node: getAuthorizationHeadersFrom
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


// Node: drawbackMoney
// Node: getOrderByIdFromOrderOther
// Node: DecimalFormat
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


// Node: testDrawbackMoney
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




package org.myproject.ms.monitoring;

import java.util.Collection;
import java.util.LinkedHashSet;

import org.springframework.boot.context.properties.ConfigurationProperties;


@ConfigurationProperties("spring.sleuth.keys")
public class ChainKeys {

	private Http http = new Http();

	private Message message = new Message();

	private Hystrix hystrix = new Hystrix();

	private Async async = new Async();

	private Mvc mvc = new Mvc();

	public Http getHttp() {
		return this.http;
	}

	public Message getMessage() {
		return this.message;
	}

	public Hystrix getHystrix() {
		return this.hystrix;
	}

	public Async getAsync() {
		return this.async;
	}

	public Mvc getMvc() {
		return this.mvc;
	}

	public void setHttp(Http http) {
		this.http = http;
	}

	public void setMessage(Message message) {
		this.message = message;
	}

	public void setHystrix(Hystrix hystrix) {
		this.hystrix = hystrix;
	}

	public void setAsync(Async async) {
		this.async = async;
	}

	public void setMvc(Mvc mvc) {
		this.mvc = mvc;
	}

	public static class Message {

		private Payload payload = new Payload();

		public Payload getPayload() {
			return this.payload;
		}

		public String getPrefix() {
			return this.prefix;
		}

		public Collection<String> getHeaders() {
			return this.headers;
		}

		public void setPayload(Payload payload) {
			this.payload = payload;
		}

		public void setPrefix(String prefix) {
			this.prefix = prefix;
		}

		public void setHeaders(Collection<String> headers) {
			this.headers = headers;
		}

		public static class Payload {
			
			private String size = "message/payload-size";
			
			private String type = "message/payload-type";

			public String getSize() {
				return this.size;
			}

			public String getType() {
				return this.type;
			}

			public void setSize(String size) {
				this.size = size;
			}

			public void setType(String type) {
				this.type = type;
			}
		}

		
		private String prefix = "message/";

		
		private Collection<String> headers = new LinkedHashSet<String>();

	}

	public static class Http {

		
		private String host = "http.host";

		
		private String method = "http.method";

		
		private String path = "http.path";

		
		private String url = "http.url";

		
		private String statusCode = "http.status_code";

		
		private String requestSize = "http.request.size";

		
		private String responseSize = "http.response.size";

		
		private String prefix = "http.";

		
		private Collection<String> headers = new LinkedHashSet<String>();

		public String getHost() {
			return this.host;
		}

		public String getMethod() {
			return this.method;
		}

		public String getPath() {
			return this.path;
		}

		public String getUrl() {
			return this.url;
		}

		public String getStatusCode() {
			return this.statusCode;
		}

		public String getRequestSize() {
			return this.requestSize;
		}

		public String getResponseSize() {
			return this.responseSize;
		}

		public String getPrefix() {
			return this.prefix;
		}

		public Collection<String> getHeaders() {
			return this.headers;
		}

		public void setHost(String host) {
			this.host = host;
		}

		public void setMethod(String method) {
			this.method = method;
		}

		public void setPath(String path) {
			this.path = path;
		}

		public void setUrl(String url) {
			this.url = url;
		}

		public void setStatusCode(String statusCode) {
			this.statusCode = statusCode;
		}

		public void setRequestSize(String requestSize) {
			this.requestSize = requestSize;
		}

		public void setResponseSize(String responseSize) {
			this.responseSize = responseSize;
		}

		public void setPrefix(String prefix) {
			this.prefix = prefix;
		}

		public void setHeaders(Collection<String> headers) {
			this.headers = headers;
		}
	}

	
	public static class Hystrix {

		
		private String prefix = "";

		
		private String commandKey = "commandKey";

		
		private String commandGroup = "commandGroup";

		
		private String threadPoolKey = "threadPoolKey";

		public String getPrefix() {
			return this.prefix;
		}

		public String getCommandKey() {
			return this.commandKey;
		}

		public String getCommandGroup() {
			return this.commandGroup;
		}

		public String getThreadPoolKey() {
			return this.threadPoolKey;
		}

		public void setPrefix(String prefix) {
			this.prefix = prefix;
		}

		public void setCommandKey(String commandKey) {
			this.commandKey = commandKey;
		}

		public void setCommandGroup(String commandGroup) {
			this.commandGroup = commandGroup;
		}

		public void setThreadPoolKey(String threadPoolKey) {
			this.threadPoolKey = threadPoolKey;
		}
	}

	
	public static class Async {

		
		private String prefix = "";

		
		private String threadNameKey = "thread";

		
		private String classNameKey = "class";

		
		private String methodNameKey = "method";

		public String getPrefix() {
			return this.prefix;
		}

		public String getThreadNameKey() {
			return this.threadNameKey;
		}

		public String getClassNameKey() {
			return this.classNameKey;
		}

		public String getMethodNameKey() {
			return this.methodNameKey;
		}

		public void setPrefix(String prefix) {
			this.prefix = prefix;
		}

		public void setThreadNameKey(String threadNameKey) {
			this.threadNameKey = threadNameKey;
		}

		public void setClassNameKey(String classNameKey) {
			this.classNameKey = classNameKey;
		}

		public void setMethodNameKey(String methodNameKey) {
			this.methodNameKey = methodNameKey;
		}
	}

	
	public static class Mvc {

		
		private String controllerClass = "mvc.controller.class";

		
		private String controllerMethod = "mvc.controller.method";

		public String getControllerClass() {
			return this.controllerClass;
		}

		public void setControllerClass(String controllerClass) {
			this.controllerClass = controllerClass;
		}

		public String getControllerMethod() {
			return this.controllerMethod;
		}

		public void setControllerMethod(String controllerMethod) {
			this.controllerMethod = controllerMethod;
		}
	}

}


package org.myproject.ms.monitoring.instrument.msg;

import java.util.List;
import java.util.Map;

import org.myproject.ms.monitoring.Item;
import org.myproject.ms.monitoring.ItemTextMap;
import org.myproject.ms.monitoring.ChainKeys;
import org.myproject.ms.monitoring.util.TextMapUtil;
import org.springframework.util.StringUtils;


public class HBMInject implements MSTMInject {

	private final ChainKeys traceKeys;

	public HBMInject(ChainKeys traceKeys) {
		this.traceKeys = traceKeys;
	}

	@Override
	public void inject(Item span, ItemTextMap carrier) {
		Map<String, String> map = TextMapUtil.asMap(carrier);
		if (span == null) {
			if (!isSampled(map, TMHead.SAMPLED_NAME)) {
				carrier.put(TMHead.SAMPLED_NAME, Item.SPAN_NOT_SAMPLED);
				return;
			}
			return;
		}
		addHeaders(span, carrier);
	}

	private boolean isSampled(Map<String, String> initialMessage, String sampledHeaderName) {
		return Item.SPAN_SAMPLED.equals(initialMessage.get(sampledHeaderName));
	}

	private void addHeaders(Item span, ItemTextMap textMap) {
		addHeader(textMap, TMHead.TRACE_ID_NAME, span.traceIdString());
		addHeader(textMap, TMHead.SPAN_ID_NAME, Item.idToHex(span.getSpanId()));
		if (span.isExportable()) {
			addAnnotations(this.traceKeys, textMap, span);
			Long parentId = getFirst(span.getParents());
			if (parentId != null) {
				addHeader(textMap, TMHead.PARENT_ID_NAME, Item.idToHex(parentId));
			}
			addHeader(textMap, TMHead.SPAN_NAME_NAME, span.getName());
			addHeader(textMap, TMHead.PROCESS_ID_NAME, span.getProcessId());
			addHeader(textMap, TMHead.SAMPLED_NAME, Item.SPAN_SAMPLED);
		}
		else {
			addHeader(textMap, TMHead.SAMPLED_NAME, Item.SPAN_NOT_SAMPLED);
		}
		for (Map.Entry<String, String> entry : span.baggageItems()) {
			textMap.put(prefixedKey(entry.getKey()), entry.getValue());
		}
	}

	private void addAnnotations(ChainKeys traceKeys, ItemTextMap spanTextMap, Item span) {
		Map<String, String> map = TextMapUtil.asMap(spanTextMap);
		for (String name : traceKeys.getMessage().getHeaders()) {
			if (map.containsKey(name)) {
				String key = traceKeys.getMessage().getPrefix() + name.toLowerCase();
				Object value = map.get(name);
				if (value == null) {
					value = "null";
				}
				// TODO: better way to serialize?
				tagIfEntryMissing(span, key, value.toString());
			}
		}
		addPayloadAnnotations(traceKeys, map, span);
	}

	private void addPayloadAnnotations(ChainKeys traceKeys, Map<String, String> map, Item span) {
		if (map.containsKey(traceKeys.getMessage().getPayload().getType())) {
			tagIfEntryMissing(span, traceKeys.getMessage().getPayload().getType(),
					map.get(traceKeys.getMessage().getPayload().getType()));
			tagIfEntryMissing(span, traceKeys.getMessage().getPayload().getSize(),
					map.get(traceKeys.getMessage().getPayload().getSize()));
		}
	}

	private void tagIfEntryMissing(Item span, String key, String value) {
		if (!span.tags().containsKey(key)) {
			span.tag(key, value);
		}
	}

	private void addHeader(ItemTextMap textMap, String name, String value) {
		if (StringUtils.hasText(value)) {
			textMap.put(name, value);
		}
	}

	private Long getFirst(List<Long> parents) {
		return parents.isEmpty() ? null : parents.get(0);
	}

	private String prefixedKey(String key) {
		if (key.startsWith(Item.SPAN_BAGGAGE_HEADER_PREFIX + TMHead.HEADER_DELIMITER )) {
			return key;
		}
		return Item.SPAN_BAGGAGE_HEADER_PREFIX + TMHead.HEADER_DELIMITER + key;
	}

}




package org.myproject.ms.monitoring.instrument.web.client;

import java.io.IOException;
import java.io.InputStream;

import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.client.ClientHttpResponse;


public class THResp implements ClientHttpResponse {

	private final ClientHttpResponse delegate;
	private final TRTInter interceptor;

	public THResp(TRTInter interceptor,
			ClientHttpResponse delegate) {
		this.interceptor = interceptor;
		this.delegate = delegate;
	}

	@Override
	public HttpHeaders getHeaders() {
		return this.delegate.getHeaders();
	}

	@Override
	public InputStream getBody() throws IOException {
		return this.delegate.getBody();
	}

	@Override
	public HttpStatus getStatusCode() throws IOException {
		return this.delegate.getStatusCode();
	}

	@Override
	public int getRawStatusCode() throws IOException {
		return this.delegate.getRawStatusCode();
	}

	@Override
	public String getStatusText() throws IOException {
		return this.delegate.getStatusText();
	}

	@Override
	public void close() {
		try {
			this.delegate.close();
		}
		finally {
			this.interceptor.finish();
		}
	}
}


// Node: getRawStatusCode
// Node: getStatusText
// Node: toMap
// Node: ticketExecute
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


// Node: collectTicket
// Node: ticketCollect
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


// Node: executeOrder
// Node: executeOrderOther
package execute.serivce;

import edu.fudan.common.util.Response;
import org.springframework.http.HttpHeaders;

/**
 * @author fdse
 */
public interface ExecuteService {

    /**
     * ticket execute by order id
     *
     * @param orderId order id
     * @param headers headers
     * @return Response
     */
    Response ticketExecute(String orderId, HttpHeaders headers);

    /**
     * ticker collect
     *
     * @param orderId order id
     * @param headers headers
     * @return Response
     */
    Response ticketCollect(String orderId, HttpHeaders headers);

}


// Node: repos/cloned_ms_repos/train-ticket/ts-execute-service/src/main/java/execute/serivce/ExecuteService.java:ExecuteService.<init>
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


// Node: getAllTravels
// Node: updateTravel
// Node: deleteTravel
package admintravel.service;

import edu.fudan.common.entity.TravelInfo;
import edu.fudan.common.util.Response;
import org.springframework.http.HttpHeaders;

/**
 * @author fdse
 */
public interface AdminTravelService {

    /**
     * get all travels
     *
     * @param headers headers
     * @return Response
     */
    Response getAllTravels(  HttpHeaders headers);

    /**
     * add travel by traver information
     *
     * @param request request
     * @param headers headers
     * @return Response
     */
    Response addTravel(TravelInfo request, HttpHeaders headers);

    /**
     * update travel by traver information
     *
     * @param request request
     * @param headers headers
     * @return Response
     */
    Response updateTravel(TravelInfo request, HttpHeaders headers);

    /**
     * add travel by trip id
     *
     * @param tripId trip id
     * @param headers headers
     * @return Response
     */
    Response deleteTravel(String tripId, HttpHeaders headers);
}


// Node: repos/cloned_ms_repos/train-ticket/ts-admin-travel-service/src/main/java/admintravel/service/AdminTravelService.java:AdminTravelService.<init>
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


// Node: checkTravelInfo
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


// Node: getInstances
// Node: deleteUserAuth
// Node: distributeSeat
// Node: getLeftTicketOfInterval
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

// Node: getTotalNum
// Node: getDestStation
// Node: isContained
// Node: getDirectProportion
package seat.service;

import edu.fudan.common.util.Response;
import org.springframework.http.HttpHeaders;
import edu.fudan.common.entity.Seat;

/**
 * @author fdse
 */
public interface SeatService {

    Response distributeSeat(Seat seatRequest, HttpHeaders headers);
    Response getLeftTicketOfInterval(Seat seatRequest, HttpHeaders headers);
}


// Node: repos/cloned_ms_repos/train-ticket/ts-seat-service/src/main/java/seat/service/SeatService.java:SeatService.<init>
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


// Node: testDistributeSeat1
// Node: testDistributeSeat2
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


// Node: getSecurityOrderInfoFromOrder
// Node: getSecurityOrderOtherInfoFromOrder
// Node: getOrderNumInLastOneHour
// Node: getOrderNumOfValidOrder
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


// Node: getStationFoodStoreId
// Node: getDeliveryFee
// Node: setDeliveryFee
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


