// Cluster 12

// Node: put
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


// Node: repos/cloned_ms_repos/train-ticket/ts-wait-order-service/src/main/java/waitorder/utils/PollThread.java:PollThread.<init>
// Node: PollThread
// Node: printStackTrace
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


// Node: getWaitListOrders
// Node: getAllWaitListOrders
// Node: triggerThread
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


// Node: stream
// Node: filter
// Node: contains
// Node: collect
// Node: toList
// Node: getWaitUtilTime
// Node: start
package waitorder.entity;

import edu.fudan.common.util.StringUtils;
import lombok.AllArgsConstructor;
import lombok.Data;
import org.hibernate.annotations.GenericGenerator;

import javax.persistence.*;
import java.util.Calendar;
import java.util.Date;


@Data
@AllArgsConstructor
@Entity
@GenericGenerator(name = "jpa-uuid", strategy ="uuid")
public class WaitListOrder {
    @Id
    @GeneratedValue(generator = "jpa-uuid")
    @Column(length = 36)
    private String id;

//    private String travelDate;
    private String travelTime;

    @Column(length = 36)
    private String accountId;
    private String contactsId;
    private String contactsName;
    private int contactsDocumentType;
    private String contactsDocumentNumber;
    private String trainNumber;
    private int seatType;

    @Column(name = "from_station")
    private String from;
    @Column(name = "to_station")
    private String to;

    private String price;
    private String waitUtilTime;
    private String createdTime;
    private int status;


    public WaitListOrder(){
        createdTime = StringUtils.Date2String(new Date(System.currentTimeMillis()));
//        trainNumber = "G1235";
//        seatType = SeatClass.FIRSTCLASS.getCode();
//        from = "shanghai";
//        to = "taiyuan";
//        price = "0.0";

        //wait until 24 hours later
        Calendar c = Calendar.getInstance();
        c.setTime(new Date(System.currentTimeMillis()));
        c.add(Calendar.DAY_OF_MONTH,1);
        waitUtilTime = StringUtils.Date2String(c.getTime());
        travelTime=StringUtils.Date2String(c.getTime());
        status= WaitListOrderStatus.NOTPAID.getCode();
    }

//    @Override
//    public boolean equals(Object o) {
//        if (this == o) return true;
//        if (o == null || getClass() != o.getClass()) return false;
//        WaitListOrder that = (WaitListOrder) o;
//        return contactsDocumentType == that.contactsDocumentType
//                && coachNumber == that.coachNumber
//                && seatClass == that.seatClass
//                && id.equals(that.id)
//                && Objects.equals(travelTime, that.travelTime)
//                && Objects.equals(accountId, that.accountId)
//                && Objects.equals(contactsName, that.contactsName)
//                && Objects.equals(contactsDocumentNumber, that.contactsDocumentNumber)
//                && Objects.equals(trainNumber, that.trainNumber)
//                && Objects.equals(seatNumber, that.seatNumber)
//                && Objects.equals(fromStation, that.fromStation)
//                && Objects.equals(toStation, that.toStation)
//                && Objects.equals(price, that.price);
//    }

    @Override
    public int hashCode() {
        int result = 17;
        result = 31 * result + (id == null ? 0 : id.hashCode());
        return result;
    }

    public Date getCreatedTime(){ return StringUtils.String2Date(createdTime); }

    public Date getTravelTime(){ return StringUtils.String2Date(createdTime); }

    public Date getWaitUtilTime(){ return StringUtils.String2Date(waitUtilTime); }

    public void setCreatedTime(Date createdTime){
        this.createdTime = StringUtils.Date2String(createdTime);
    }

    public void setTravelTime(Date travelTime){ this.createdTime = StringUtils.Date2String(travelTime); }

    public void setWaitUntilTime(Date waitUntilTime){ this.waitUtilTime=StringUtils.Date2String(waitUntilTime);}



}


package auth.entity;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.userdetails.UserDetails;

import org.hibernate.annotations.GenericGenerator;

import javax.persistence.*;
import java.util.*;
import java.util.stream.Collectors;

/**
 * @author fdse
 */
@Data
@GenericGenerator(name = "jpa-uuid", strategy = "org.hibernate.id.UUIDGenerator")
@Builder
@AllArgsConstructor
@NoArgsConstructor
@Entity
@Table(name = "auth_user")
public class User implements UserDetails {
    @Id
    @Column(length=36, name = "user_id")
    private String userId;

    @Column(length=36, name = "user_name")
    private String username;

    private String password;

    @ElementCollection
    @CollectionTable(joinColumns = @JoinColumn(name = "user_id"))
    private Set<String> roles = new HashSet<>();

    @Override
    public Collection<? extends GrantedAuthority> getAuthorities() {
        return this.roles.stream().map(SimpleGrantedAuthority::new).collect(Collectors.toList());
    }

    @Override
    public String getPassword() {
        return this.password;
    }

    @Override
    public String getUsername() {
        return this.username;
    }

    @Override
    public boolean isAccountNonExpired() {
        return true;
    }

    @Override
    public boolean isAccountNonLocked() {
        return true;
    }

    @Override
    public boolean isCredentialsNonExpired() {
        return true;
    }

    @Override
    public boolean isEnabled() {
        return true;
    }
}


// Node: getAuthorities
// Node: map
package edu.fudan.common.entity;

import lombok.Data;

import java.io.Serializable;

/**
 * @author fdse
 */
@Data
public class TripId implements Serializable{
    private Type type;
    private String number;


    public TripId(){
        //Default Constructor
    }

    public TripId(String trainNumber){
        char type0 = trainNumber.charAt(0);
        switch(type0){
            case 'Z': this.type = Type.Z;
                break;
            case 'T': this.type = Type.T;
                break;
            case 'K': this.type = Type.K;
                break;
            case 'G':
                this.type = Type.G;
                break;
            case 'D':
                this.type = Type.D;
                break;
            default:break;
        }

        this.number = trainNumber.substring(1);
    }

    @Override
    public String toString(){
        return type.getName() + number;
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-common/src/main/java/edu/fudan/common/entity/TripId.java:TripId.<init>
// Node: substring
package edu.fudan.common.security.jwt;

import edu.fudan.common.exception.TokenException;
import io.jsonwebtoken.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.userdetails.UserDetails;

import javax.servlet.ServletRequest;
import javax.servlet.http.HttpServletRequest;
import java.util.Base64;
import java.util.Collection;
import java.util.Date;
import java.util.List;
import java.util.stream.Collectors;

/**
 * @author fdse
 */
public class JWTUtil {

    private JWTUtil() {
        throw new IllegalStateException("Utility class");
    }

    private static final Logger LOGGER = LoggerFactory.getLogger(JWTUtil.class);
    private static String secretKey = Base64.getEncoder().encodeToString("secret".getBytes());


    public static Authentication getJWTAuthentication(ServletRequest request) {
        String token = getTokenFromHeader((HttpServletRequest) request);
        if (token != null && validateToken(token)) {

            UserDetails userDetails = new UserDetails() {
                @Override
                public Collection<? extends GrantedAuthority> getAuthorities() {
                    return getRole(token).stream().map(SimpleGrantedAuthority::new).collect(Collectors.toList());
                }

                @Override
                public String getPassword() {
                    return "";
                }

                @Override
                public String getUsername() {
                    return getUserName(token);
                }

                @Override
                public boolean isAccountNonExpired() {
                    return true;
                }

                @Override
                public boolean isAccountNonLocked() {
                    return true;
                }

                @Override
                public boolean isCredentialsNonExpired() {
                    return true;
                }

                @Override
                public boolean isEnabled() {
                    return true;
                }
            };
            // send to spring security
            return new UsernamePasswordAuthenticationToken(userDetails, "", userDetails.getAuthorities());
        }
        return null;
    }

    private static String getUserName(String token) {
        return getClaims(token).getBody().getSubject();
    }

    private static List<String> getRole(String token) {
        Jws<Claims> claimsJws = getClaims(token);
        return (List<String>) (claimsJws.getBody().get("roles", List.class));
    }

    private static String getTokenFromHeader(HttpServletRequest request) {
        String bearerToken = request.getHeader("Authorization");
        if (bearerToken != null && bearerToken.startsWith("Bearer ")) {
            return bearerToken.substring(7, bearerToken.length());
        }
        return null;
    }

    private static boolean validateToken(String token) {
        try {
            Jws<Claims> claimsJws = getClaims(token);
            return !claimsJws.getBody().getExpiration().before(new Date());
        } catch (ExpiredJwtException e) {
            LOGGER.error("[validateToken][getClaims][Token expired][ExpiredJwtException: {} ]" , e);
            throw new TokenException("Token expired");
        } catch (UnsupportedJwtException e) {
            LOGGER.error("[validateToken][getClaims][Token format error][UnsupportedJwtException: {}]", e);
            throw new TokenException("Token format error");
        } catch (MalformedJwtException e) {
            LOGGER.error("[validateToken][getClaims][Token is not properly constructed][MalformedJwtException: {}]", e);
            throw new TokenException("Token is not properly constructed");
        } catch (SignatureException e) {
            LOGGER.error("[validateToken][getClaims][Signature failure][SignatureException: {}]", e);
            throw new TokenException("Signature failure");
        } catch (IllegalArgumentException e) {
            LOGGER.error("[validateToken][getClaims][Illegal parameter exception][IllegalArgumentException: {}]", e);
            throw new TokenException("Illegal parameter exception");
        }
    }

    private static Jws<Claims> getClaims(String token) {
        return Jwts.parser().setSigningKey(secretKey).parseClaimsJws(token);
    }

}


// Node: addAll
// Node: entrySet
// Node: getValue
// Node: getKey
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


// Node: StringBuilder
// Node: append
// Node: iterator
// Node: hasNext
// Node: next
// Node: compareTo
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


// Node: containsKey
// Node: Balance
// Node: setBalance
package inside_payment.entity;

import lombok.Data;

import javax.validation.Valid;
import javax.validation.constraints.NotNull;

/**
 * @author fdse
 */
@Data
public class Balance {
    @Valid
    @NotNull
    private String userId;

    @Valid
    @NotNull
    private String balance; //NOSONAR

    public Balance(){
        //Default Constructor
        this.userId = "";
        this.balance = "";
    }

}


// Node: repos/cloned_ms_repos/train-ticket/ts-inside-payment-service/src/main/java/inside_payment/entity/Balance.java:Balance.<init>
// Node: write
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


// Node: getHeaderNames
// Node: getContextPath
// Node: setHeader
// Node: addHeader
// Node: name


package org.myproject.ms.monitoring;


public interface ItemNamer {

	
	String name(Object object, String defaultValue);
}


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/ItemNamer.java:ItemNamer.<init>
package org.myproject.ms.monitoring;

import java.util.Map;


public interface ItemContext {
	
	
	Iterable<Map.Entry<String, String>> baggageItems();
}

// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/ItemContext.java:ItemContext.<init>
// Node: baggageItems
package org.myproject.ms.monitoring;

import java.util.Iterator;
import java.util.Map;


public interface ItemTextMap extends Iterable<Map.Entry<String, String>> {
	
	Iterator<Map.Entry<String,String>> iterator();

	
	void put(String key, String value);
}

// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/ItemTextMap.java:ItemTextMap.<init>


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


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/Item.java:Item.<init>
// Node: JsonAutoDetect
// Node: JsonInclude
// Node: address
// Node: Item
// Node: getBegin
// Node: getEnd
// Node: getTraceIdHigh
// Node: getTraceId
// Node: getParents
// Node: getSpanId
// Node: isRemote
// Node: isExportable
// Node: getProcessId
// Node: begin
// Node: end
// Node: traceId
// Node: parents
// Node: spanId
// Node: remote
// Node: exportable
// Node: processId
// Node: savedSpan
// Node: putAll
// Node: hasText
// Node: setBaggageItem
// Node: getBaggage
// Node: unmodifiableMap
// Node: logs
// Node: unmodifiableList
// Node: getSavedSpan
// Node: traceIdString
// Node: writeHexLong
// Node: String
// Node: idToHex
// Node: writeHexByte
// Node: hexToId
// Node: IllegalArgumentException
// Node: getParentIdIfPresent
// Node: traceIdHigh
// Node: parent
// Node: log
// Node: baggage


package org.myproject.ms.monitoring.trace;

import org.apache.commons.logging.Log;
import org.myproject.ms.monitoring.Item;
import org.springframework.core.NamedThreadLocal;


class ICHolder {

	private static final Log log = org.apache.commons.logging.LogFactory
			.getLog(ICHolder.class);
	private static final ThreadLocal<SpanContext> CURRENT_SPAN = new NamedThreadLocal<>(
			"Trace Context");

	
	static Item getCurrentSpan() {
		return isTracing() ? CURRENT_SPAN.get().span : null;
	}

	
	static void setCurrentSpan(Item span) {
		if (log.isTraceEnabled()) {
			log.trace("Setting current span " + span);
		}
		push(span, false);
	}

	
	static void removeCurrentSpan() {
		CURRENT_SPAN.remove();
	}

	
	static boolean isTracing() {
		return CURRENT_SPAN.get() != null;
	}

	
	static void close(SpanFunction spanFunction) {
		SpanContext current = CURRENT_SPAN.get();
		CURRENT_SPAN.remove();
		while (current != null) {
			current = current.parent;
			spanFunction.apply(current != null ? current.span : null);
			if (current != null) {
				if (!current.autoClose) {
					CURRENT_SPAN.set(current);
					current = null;
				}
			}
		}
	}

	
	static void close() {
		close(new NoOpFunction());
	}

	
	static void push(Item span, boolean autoClose) {
		if (isCurrent(span)) {
			return;
		}
		CURRENT_SPAN.set(new SpanContext(span, autoClose));
	}

	private static boolean isCurrent(Item span) {
		if (span == null || CURRENT_SPAN.get() == null) {
			return false;
		}
		return span.equals(CURRENT_SPAN.get().span);
	}

	private static class SpanContext {
		Item span;
		boolean autoClose;
		SpanContext parent;

		public SpanContext(Item span, boolean autoClose) {
			this.span = span;
			this.autoClose = autoClose;
			this.parent = CURRENT_SPAN.get();
		}
	}

	interface SpanFunction {
		void apply(Item span);
	}

	private static class NoOpFunction implements SpanFunction {
		@Override public void apply(Item span) { }
	}
}


// Node: setCurrentSpan
// Node: isTraceEnabled
// Node: trace
// Node: push
// Node: apply
// Node: NoOpFunction
// Node: isCurrent
// Node: SpanContext


package org.myproject.ms.monitoring.trace;

import java.lang.invoke.MethodHandles;
import java.util.Random;
import java.util.concurrent.Callable;

import org.apache.commons.logging.Log;
import org.apache.commons.logging.LogFactory;
import org.myproject.ms.monitoring.Sampler;
import org.myproject.ms.monitoring.Item;
import org.myproject.ms.monitoring.ItemNamer;
import org.myproject.ms.monitoring.ItemReporter;
import org.myproject.ms.monitoring.ChainKeys;
import org.myproject.ms.monitoring.Chainer;
import org.myproject.ms.monitoring.instrument.async.SCTCall;
import org.myproject.ms.monitoring.instrument.async.SCTRun;
import org.myproject.ms.monitoring.lgger.ItemLogger;
import org.myproject.ms.monitoring.util.ExceptionUtils;
import org.myproject.ms.monitoring.util.ItemNameUtil;


public class DChainer implements Chainer {

	private static final Log log = LogFactory.getLog(MethodHandles.lookup().lookupClass());

	private static final int MAX_CHARS_IN_SPAN_NAME = 50;

	private final Sampler defaultSampler;

	private final Random random;

	private final ItemNamer spanNamer;

	private final ItemLogger spanLogger;

	private final ItemReporter spanReporter;

	private final ChainKeys traceKeys;

	private final boolean traceId128;

	@Deprecated
	public DChainer(Sampler defaultSampler, Random random, ItemNamer spanNamer,
			ItemLogger spanLogger, ItemReporter spanReporter) {
		this(defaultSampler, random, spanNamer, spanLogger, spanReporter, false);
	}

	@Deprecated
	public DChainer(Sampler defaultSampler, Random random, ItemNamer spanNamer,
				ItemLogger spanLogger, ItemReporter spanReporter, boolean traceId128) {
		this(defaultSampler, random, spanNamer, spanLogger, spanReporter, traceId128, null);
	}

	public DChainer(Sampler defaultSampler, Random random, ItemNamer spanNamer,
				ItemLogger spanLogger, ItemReporter spanReporter, ChainKeys traceKeys) {
		this(defaultSampler, random, spanNamer, spanLogger, spanReporter, false, traceKeys);
	}

	public DChainer(Sampler defaultSampler, Random random, ItemNamer spanNamer,
				ItemLogger spanLogger, ItemReporter spanReporter, boolean traceId128,
			ChainKeys traceKeys) {
		this.defaultSampler = defaultSampler;
		this.random = random;
		this.spanNamer = spanNamer;
		this.spanLogger = spanLogger;
		this.spanReporter = spanReporter;
		this.traceId128 = traceId128;
		this.traceKeys = traceKeys != null ? traceKeys : new ChainKeys();
	}

	@Override
	public Item createSpan(String name, Item parent) {
		if (parent == null) {
			return createSpan(name);
		}
		return continueSpan(createChild(parent, name));
	}

	@Override
	public Item createSpan(String name) {
		return this.createSpan(name, this.defaultSampler);
	}

	@Override
	public Item createSpan(String name, Sampler sampler) {
		String shortenedName = ItemNameUtil.shorten(name);
		Item span;
		if (isTracing()) {
			span = createChild(getCurrentSpan(), shortenedName);
		}
		else {
			long id = createId();
			span = Item.builder().name(shortenedName)
					.traceIdHigh(this.traceId128 ? createId() : 0L)
					.traceId(id)
					.spanId(id).build();
			if (sampler == null) {
				sampler = this.defaultSampler;
			}
			span = sampledSpan(span, sampler);
			this.spanLogger.logStartedSpan(null, span);
		}
		return continueSpan(span);
	}

	@Override
	public Item detach(Item span) {
		if (span == null) {
			return null;
		}
		Item cur = ICHolder.getCurrentSpan();
		if (cur == null) {
			if (log.isTraceEnabled()) {
				log.trace("Span in the context is null so something has already detached the span. Won't do anything about it");
			}
			return null;
		}
		if (!span.equals(cur)) {
			ExceptionUtils.warn("Tried to detach trace span but "
					+ "it is not the current span: " + span
					+ ". You may have forgotten to close or detach " + cur);
		}
		else {
			ICHolder.removeCurrentSpan();
		}
		return span.getSavedSpan();
	}

	@Override
	public Item close(Item span) {
		if (span == null) {
			return null;
		}
		Item cur = ICHolder.getCurrentSpan();
		final Item savedSpan = span.getSavedSpan();
		if (!span.equals(cur)) {
			ExceptionUtils.warn(
					"Tried to close span but it is not the current span: " + span
							+ ".  You may have forgotten to close or detach " + cur);
		}
		else {
			span.stop();
			if (savedSpan != null && span.getParents().contains(savedSpan.getSpanId())) {
				this.spanReporter.report(span);
				this.spanLogger.logStoppedSpan(savedSpan, span);
			}
			else {
				if (!span.isRemote()) {
					this.spanReporter.report(span);
					this.spanLogger.logStoppedSpan(null, span);
				}
			}
			ICHolder.close(new ICHolder.SpanFunction() {
				@Override public void apply(Item span) {
					DChainer.this.spanLogger.logStoppedSpan(savedSpan, span);
				}
			});
		}
		return savedSpan;
	}

	Item createChild(Item parent, String name) {
		String shortenedName = ItemNameUtil.shorten(name);
		long id = createId();
		if (parent == null) {
			Item span = Item.builder().name(shortenedName)
					.traceIdHigh(this.traceId128 ? createId() : 0L)
					.traceId(id)
					.spanId(id).build();
			span = sampledSpan(span, this.defaultSampler);
			this.spanLogger.logStartedSpan(null, span);
			return span;
		}
		else {
			if (!isTracing()) {
				ICHolder.push(parent, true);
			}
			Item span = Item.builder().name(shortenedName)
					.traceIdHigh(parent.getTraceIdHigh())
					.traceId(parent.getTraceId()).parent(parent.getSpanId()).spanId(id)
					.processId(parent.getProcessId()).savedSpan(parent)
					.exportable(parent.isExportable())
					.baggage(parent.getBaggage())
					.build();
			this.spanLogger.logStartedSpan(parent, span);
			return span;
		}
	}

	private Item sampledSpan(Item span, Sampler sampler) {
		if (!sampler.isSampled(span)) {
			// Copy everything, except set exportable to false
			return Item.builder()
					.begin(span.getBegin())
					.traceIdHigh(span.getTraceIdHigh())
					.traceId(span.getTraceId())
					.spanId(span.getSpanId())
					.name(span.getName())
					.exportable(false).build();
		}
		return span;
	}

	private long createId() {
		return this.random.nextLong();
	}

	@Override
	public Item continueSpan(Item span) {
		if (span != null) {
			this.spanLogger.logContinuedSpan(span);
		} else {
			return null;
		}
		Item newSpan = createContinuedSpan(span, ICHolder.getCurrentSpan());
		ICHolder.setCurrentSpan(newSpan);
		return newSpan;
	}

	private Item createContinuedSpan(Item span, Item saved) {
		if (saved == null && span.getSavedSpan() != null) {
			saved = span.getSavedSpan();
		}
		return new Item(span, saved);
	}

	@Override
	public Item getCurrentSpan() {
		return ICHolder.getCurrentSpan();
	}

	@Override
	public boolean isTracing() {
		return ICHolder.isTracing();
	}

	@Override
	public void addTag(String key, String value) {
		Item s = getCurrentSpan();
		if (s != null && s.isExportable()) {
			s.tag(key, value);
		}
	}

	
	@Override
	public <V> Callable<V> wrap(Callable<V> callable) {
		if (isTracing()) {
			return new SCTCall<>(this, this.traceKeys, this.spanNamer, callable);
		}
		return callable;
	}

	
	@Override
	public Runnable wrap(Runnable runnable) {
		if (isTracing()) {
			return new SCTRun(this, this.traceKeys, this.spanNamer, runnable);
		}
		return runnable;
	}
}


// Node: createChild
// Node: shorten
// Node: createId
// Node: sampledSpan
// Node: logStartedSpan
// Node: logStoppedSpan
// Node: SpanFunction
// Node: nextLong
// Node: logContinuedSpan
// Node: createContinuedSpan


package org.myproject.ms.monitoring.lgger;

import org.myproject.ms.monitoring.Item;


public interface ItemLogger {

	
	void logStartedSpan(Item parent, Item span);

	
	void logContinuedSpan(Item span);

	
	void logStoppedSpan(Item parent, Item span);
}


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/lgger/ItemLogger.java:ItemLogger.<init>


package org.myproject.ms.monitoring.lgger;

import org.myproject.ms.monitoring.Item;


public class NoItemLogger implements ItemLogger {
	@Override
	public void logStartedSpan(Item parent, Item span) {

	}

	@Override
	public void logContinuedSpan(Item span) {

	}

	@Override
	public void logStoppedSpan(Item parent, Item span) {

	}
}


// Node: compile


package org.myproject.ms.monitoring.lgger;

import java.util.regex.Pattern;

import org.slf4j.Logger;
import org.slf4j.MDC;
import org.myproject.ms.monitoring.Item;


public class Slf4jItemLogger implements ItemLogger {

	private final Logger log;
	private final Pattern nameSkipPattern;

	public Slf4jItemLogger(String nameSkipPattern) {
		this.nameSkipPattern = Pattern.compile(nameSkipPattern);
		this.log = org.slf4j.LoggerFactory.getLogger(Slf4jItemLogger.class);
	}

	Slf4jItemLogger(String nameSkipPattern, Logger log) {
		this.nameSkipPattern = Pattern.compile(nameSkipPattern);
		this.log = log;
	}

	@Override
	public void logStartedSpan(Item parent, Item span) {
		MDC.put(Item.SPAN_ID_NAME, Item.idToHex(span.getSpanId()));
		MDC.put(Item.SPAN_EXPORT_NAME, String.valueOf(span.isExportable()));
		MDC.put(Item.TRACE_ID_NAME, span.traceIdString());
		log("Starting span: {}", span);
		if (parent != null) {
			log("With parent: {}", parent);
			MDC.put(Item.PARENT_ID_NAME, Item.idToHex(parent.getSpanId()));
		}
	}

	@Override
	public void logContinuedSpan(Item span) {
		MDC.put(Item.SPAN_ID_NAME, Item.idToHex(span.getSpanId()));
		MDC.put(Item.TRACE_ID_NAME, span.traceIdString());
		MDC.put(Item.SPAN_EXPORT_NAME, String.valueOf(span.isExportable()));
		setParentIdIfPresent(span);
		log("Continued span: {}", span);
	}

	private void setParentIdIfPresent(Item span) {
		if (!span.getParents().isEmpty()) {
			MDC.put(Item.PARENT_ID_NAME, Item.idToHex(span.getParents().get(0)));
		}
	}

	@Override
	public void logStoppedSpan(Item parent, Item span) {
		if (span != null) {
			log("Stopped span: {}", span);
		}
		if (span != null && parent != null) {
			log("With parent: {}", parent);
			MDC.put(Item.SPAN_ID_NAME, Item.idToHex(parent.getSpanId()));
			MDC.put(Item.SPAN_EXPORT_NAME, String.valueOf(parent.isExportable()));
			setParentIdIfPresent(parent);
		}
		else {
			MDC.remove(Item.SPAN_ID_NAME);
			MDC.remove(Item.SPAN_EXPORT_NAME);
			MDC.remove(Item.TRACE_ID_NAME);
			MDC.remove(Item.PARENT_ID_NAME);
		}
	}

	private void log(String text, Item span) {
		if (span != null && this.nameSkipPattern.matcher(span.getName()).matches()) {
			return;
		}
		if (this.log.isTraceEnabled()) {
			this.log.trace(text, span);
		}
	}

}


// Node: valueOf
// Node: setParentIdIfPresent
// Node: matcher
package org.myproject.ms.monitoring.util;

import java.util.Comparator;
import java.util.Map;
import java.util.TreeMap;


public final class TextMapUtil {

	private TextMapUtil() {}

	public static Map<String, String> asMap(Iterable<Map.Entry<String, String>> iterable) {
		Map<String, String> map = new TreeMap<>(new Comparator<String>() {
			@Override public int compare(String o1, String o2) {
				return o1.toLowerCase().compareTo(o2.toLowerCase());
			}
		});
		for (Map.Entry<String, String> entry : iterable) {
			map.put(entry.getKey(), entry.getValue());
		}
		return map;
	}
}


// Node: asMap
// Node: compare


package org.myproject.ms.monitoring.util;

import org.springframework.util.StringUtils;


public final class ItemNameUtil {

	static final int MAX_NAME_LENGTH = 50;

	public static String shorten(String name) {
		if (StringUtils.isEmpty(name)) {
			return name;
		}
		int maxLength = name.length() > MAX_NAME_LENGTH ? MAX_NAME_LENGTH : name.length();
		return name.substring(0, maxLength);
	}

	public static String toLowerHyphen(String name) {
		StringBuilder result = new StringBuilder();
		for (int i = 0; i < name.length(); i++) {
			char c = name.charAt(i);
			if (Character.isUpperCase(c)) {
				if (i != 0) result.append('-');
				result.append(Character.toLowerCase(c));
			} else {
				result.append(c);
			}
		}
		return ItemNameUtil.shorten(result.toString());
	}
}


// Node: isUpperCase
package org.myproject.ms.monitoring.mtc;

import org.springframework.boot.context.properties.ConfigurationProperties;


@ConfigurationProperties("spring.sleuth.metric")
public class SMProp {

	
	private boolean enabled = true;

	private Span span = new Span();

	public boolean isEnabled() {
		return this.enabled;
	}

	public void setEnabled(boolean enabled) {
		this.enabled = enabled;
	}

	public Span getSpan() {
		return this.span;
	}

	public void setSpan(Span span) {
		this.span = span;
	}

	public static class Span {

		private String acceptedName = "counter.span.accepted";

		private String droppedName = "counter.span.dropped";

		public String getAcceptedName() {
			return this.acceptedName;
		}

		public void setAcceptedName(String acceptedName) {
			this.acceptedName = acceptedName;
		}

		public String getDroppedName() {
			return this.droppedName;
		}

		public void setDroppedName(String droppedName) {
			this.droppedName = droppedName;
		}
	}
}


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/mtc/SMProp.java:SMProp.<init>
// Node: Span


package org.myproject.ms.monitoring.antn;

import java.lang.annotation.Annotation;
import java.lang.invoke.MethodHandles;
import java.lang.reflect.Method;
import java.util.concurrent.atomic.AtomicBoolean;
import javax.annotation.PostConstruct;

import org.aopalliance.aop.Advice;
import org.aopalliance.intercept.MethodInvocation;
import org.apache.commons.logging.Log;
import org.apache.commons.logging.LogFactory;
import org.springframework.aop.ClassFilter;
import org.springframework.aop.IntroductionAdvisor;
import org.springframework.aop.IntroductionInterceptor;
import org.springframework.aop.Pointcut;
import org.springframework.aop.support.AbstractPointcutAdvisor;
import org.springframework.aop.support.AopUtils;
import org.springframework.aop.support.DynamicMethodMatcherPointcut;
import org.springframework.aop.support.annotation.AnnotationClassFilter;
import org.springframework.beans.BeansException;
import org.springframework.beans.factory.BeanFactory;
import org.springframework.beans.factory.BeanFactoryAware;
import org.myproject.ms.monitoring.Item;
import org.myproject.ms.monitoring.Chainer;
import org.myproject.ms.monitoring.util.ExceptionUtils;
import org.springframework.core.annotation.AnnotationUtils;
import org.springframework.util.ObjectUtils;
import org.springframework.util.ReflectionUtils;
import org.springframework.util.StringUtils;


class SleuthAdvisorConfig  extends AbstractPointcutAdvisor implements
		IntroductionAdvisor, BeanFactoryAware {
	private static final Log log = LogFactory.getLog(MethodHandles.lookup().lookupClass());

	private Advice advice;

	private Pointcut pointcut;

	private BeanFactory beanFactory;

	@PostConstruct
	public void init() {
		this.pointcut = buildPointcut();
		this.advice = buildAdvice();
		if (this.advice instanceof BeanFactoryAware) {
			((BeanFactoryAware) this.advice).setBeanFactory(this.beanFactory);
		}
	}

	
	@Override
	public void setBeanFactory(BeanFactory beanFactory) {
		this.beanFactory = beanFactory;
	}

	@Override
	public ClassFilter getClassFilter() {
		return this.pointcut.getClassFilter();
	}

	@Override
	public Class<?>[] getInterfaces() {
		return new Class[] {};
	}

	@Override
	public void validateInterfaces() throws IllegalArgumentException {
	}

	@Override
	public Advice getAdvice() {
		return this.advice;
	}

	@Override
	public Pointcut getPointcut() {
		return this.pointcut;
	}

	private Advice buildAdvice() {
		return new SleuthInterceptor();
	}

	private Pointcut buildPointcut() {
		return new AnnotationClassOrMethodOrArgsPointcut();
	}

	
	private final class AnnotationClassOrMethodOrArgsPointcut extends
			DynamicMethodMatcherPointcut {

		private final DynamicMethodMatcherPointcut methodResolver;

		AnnotationClassOrMethodOrArgsPointcut() {
			this.methodResolver = new DynamicMethodMatcherPointcut() {
				@Override public boolean matches(Method method, Class<?> targetClass,
						Object... args) {
					if (SleuthAnnotationUtils.isMethodAnnotated(method)) {
						if (log.isDebugEnabled()) {
							log.debug("Found a method with Sleuth annotation");
						}
						return true;
					}
					if (SleuthAnnotationUtils.hasAnnotatedParams(method, args)) {
						if (log.isDebugEnabled()) {
							log.debug("Found annotated arguments of the method");
						}
						return true;
					}
					return false;
				}
			};
		}

		@Override
		public boolean matches(Method method, Class<?> targetClass, Object... args) {
			return getClassFilter().matches(targetClass) ||
					this.methodResolver.matches(method, targetClass, args);
		}

		@Override public ClassFilter getClassFilter() {
			return new ClassFilter() {
				@Override public boolean matches(Class<?> clazz) {
					return new AnnotationClassOrMethodFilter(NewSpan.class).matches(clazz) ||
							new AnnotationClassOrMethodFilter(ContinueSpan.class).matches(clazz);
				}
			};
		}

		@Override
		public boolean equals(Object other) {
			if (this == other) {
				return true;
			}
			if (!(other instanceof AnnotationClassOrMethodOrArgsPointcut)) {
				return false;
			}
			AnnotationClassOrMethodOrArgsPointcut otherAdvisor = (AnnotationClassOrMethodOrArgsPointcut) other;
			return ObjectUtils.nullSafeEquals(this.methodResolver, otherAdvisor.methodResolver);
		}

	}

	private final class AnnotationClassOrMethodFilter extends AnnotationClassFilter {

		private final AnnotationMethodsResolver methodResolver;

		AnnotationClassOrMethodFilter(Class<? extends Annotation> annotationType) {
			super(annotationType, true);
			this.methodResolver = new AnnotationMethodsResolver(annotationType);
		}

		@Override
		public boolean matches(Class<?> clazz) {
			return super.matches(clazz) || this.methodResolver.hasAnnotatedMethods(clazz);
		}

	}

	
	private static class AnnotationMethodsResolver {

		private Class<? extends Annotation> annotationType;

		public AnnotationMethodsResolver(Class<? extends Annotation> annotationType) {
			this.annotationType = annotationType;
		}

		public boolean hasAnnotatedMethods(Class<?> clazz) {
			final AtomicBoolean found = new AtomicBoolean(false);
			ReflectionUtils.doWithMethods(clazz,
					new ReflectionUtils.MethodCallback() {
						@Override
						public void doWith(Method method) throws IllegalArgumentException,
								IllegalAccessException {
							if (found.get()) {
								return;
							}
							Annotation annotation = AnnotationUtils.findAnnotation(method,
									AnnotationMethodsResolver.this.annotationType);
							if (annotation != null) { found.set(true); }
						}
					});
			return found.get();
		}

	}
}


class SleuthInterceptor  implements IntroductionInterceptor, BeanFactoryAware  {

	private static final Log logger = LogFactory.getLog(MethodHandles.lookup().lookupClass());

	private BeanFactory beanFactory;
	private SpanCreator spanCreator;
	private Chainer tracer;
	private SpanTagAnnotationHandler spanTagAnnotationHandler;

	@Override
	public Object invoke(MethodInvocation invocation) throws Throwable {
		Method method = invocation.getMethod();
		if (method == null) {
			return invocation.proceed();
		}
		Method mostSpecificMethod = AopUtils
				.getMostSpecificMethod(method, invocation.getThis().getClass());
		NewSpan newSpan = SleuthAnnotationUtils.findAnnotation(mostSpecificMethod, NewSpan.class);
		ContinueSpan continueSpan = SleuthAnnotationUtils.findAnnotation(mostSpecificMethod, ContinueSpan.class);
		if (newSpan == null && continueSpan == null) {
			return invocation.proceed();
		}
		Item span = tracer().getCurrentSpan();
		String log = log(continueSpan);
		boolean hasLog = StringUtils.hasText(log);
		try {
			if (newSpan != null) {
				span = spanCreator().createSpan(invocation, newSpan);
			}
			if (hasLog) {
				logEvent(span, log + ".before");
			}
			spanTagAnnotationHandler().addAnnotatedParameters(invocation);
			return invocation.proceed();
		} catch (Exception e) {
			if (logger.isDebugEnabled()) {
				logger.debug("Exception occurred while trying to continue the pointcut", e);
			}
			if (hasLog) {
				logEvent(span, log + ".afterFailure");
			}
			tracer().addTag(Item.SPAN_ERROR_TAG_NAME, ExceptionUtils.getExceptionMessage(e));
			throw e;
		} finally {
			if (span != null) {
				if (hasLog) {
					logEvent(span, log + ".after");
				}
				if (newSpan != null) {
					tracer().close(span);
				}
			}
		}
	}

	private void logEvent(Item span, String name) {
		if (span == null) {
			logger.warn("You were trying to continue a span which was null. Please "
					+ "remember that if two proxied methods are calling each other from "
					+ "the same class then the aspect will not be properly resolved");
			return;
		}
		span.logEvent(name);
	}

	private String log(ContinueSpan continueSpan) {
		if (continueSpan != null) {
			return continueSpan.log();
		}
		return "";
	}

	private Chainer tracer() {
		if (this.tracer == null) {
			this.tracer = this.beanFactory.getBean(Chainer.class);
		}
		return this.tracer;
	}

	private SpanCreator spanCreator() {
		if (this.spanCreator == null) {
			this.spanCreator = this.beanFactory.getBean(SpanCreator.class);
		}
		return this.spanCreator;
	}

	private SpanTagAnnotationHandler spanTagAnnotationHandler() {
		if (this.spanTagAnnotationHandler == null) {
			this.spanTagAnnotationHandler = new SpanTagAnnotationHandler(this.beanFactory);
		}
		return this.spanTagAnnotationHandler;
	}

	@Override public boolean implementsInterface(Class<?> intf) {
		return true;
	}

	@Override public void setBeanFactory(BeanFactory beanFactory) throws BeansException {
		this.beanFactory = beanFactory;
	}
}


// Node: getMutableAccessor
// Node: copyHeaders


package org.myproject.ms.monitoring.instrument.msg;

import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;

import org.myproject.ms.monitoring.ItemTextMap;
import org.springframework.messaging.Message;
import org.springframework.messaging.support.MessageBuilder;
import org.springframework.messaging.support.MessageHeaderAccessor;
import org.springframework.messaging.support.NativeMessageHeaderAccessor;
import org.springframework.util.StringUtils;


class MTMap implements ItemTextMap {

	private final MessageBuilder delegate;

	public MTMap(MessageBuilder delegate) {
		this.delegate = delegate;
	}

	@Override
	public Iterator<Map.Entry<String, String>> iterator() {
		Map<String, String> map = new HashMap<>();
		for (Map.Entry<String, Object> entry : this.delegate.build().getHeaders()
				.entrySet()) {
			map.put(entry.getKey(), String.valueOf(entry.getValue()));
		}
		return map.entrySet().iterator();
	}

	@Override
	@SuppressWarnings("unchecked")
	public void put(String key, String value) {
		if (!StringUtils.hasText(value)) {
			return;
		}
		Message<?> initialMessage = this.delegate.build();
		MessageHeaderAccessor accessor = MessageHeaderAccessor
				.getMutableAccessor(initialMessage);
		accessor.setHeader(key, value);
		if (accessor instanceof NativeMessageHeaderAccessor) {
			NativeMessageHeaderAccessor nativeAccessor = (NativeMessageHeaderAccessor) accessor;
			nativeAccessor.setNativeHeader(key, value);
		}
		this.delegate.copyHeaders(accessor.toMessageHeaders());
	}
}


// Node: setNativeHeader
// Node: toMessageHeaders
package org.myproject.ms.monitoring.instrument.msg;

import java.util.Map;
import java.util.Random;

import org.myproject.ms.monitoring.Item;
import org.myproject.ms.monitoring.ItemTextMap;
import org.myproject.ms.monitoring.util.TextMapUtil;


public class HBMExtra implements MSTMExtra {

	@Override
	public Item joinTrace(ItemTextMap textMap) {
		Map<String, String> carrier = TextMapUtil.asMap(textMap);
		if (Item.SPAN_SAMPLED.equals(carrier.get(TMHead.SPAN_FLAGS_NAME))) {
			String traceId = generateTraceIdIfMissing(carrier);
			if (!carrier.containsKey(TMHead.SPAN_ID_NAME)) {
				carrier.put(TMHead.SPAN_ID_NAME, traceId);
			}
		} else if (!hasHeader(carrier, TMHead.SPAN_ID_NAME)
				|| !hasHeader(carrier, TMHead.TRACE_ID_NAME)) {
			return null;
			// TODO: Consider throwing IllegalArgumentException;
		}
		return extractSpanFromHeaders(carrier, Item.builder());
	}

	private String generateTraceIdIfMissing(Map<String, String> carrier) {
		if (!hasHeader(carrier, TMHead.TRACE_ID_NAME)) {
			carrier.put(TMHead.TRACE_ID_NAME, Item.idToHex(new Random().nextLong()));
		}
		return carrier.get(TMHead.TRACE_ID_NAME);
	}

	private Item extractSpanFromHeaders(Map<String, String> carrier, Item.SpanBuilder spanBuilder) {
		String traceId = carrier.get(TMHead.TRACE_ID_NAME);
		spanBuilder = spanBuilder
				.traceIdHigh(traceId.length() == 32 ? Item.hexToId(traceId, 0) : 0)
				.traceId(Item.hexToId(traceId))
				.spanId(Item.hexToId(carrier.get(TMHead.SPAN_ID_NAME)));
		String flags = carrier.get(TMHead.SPAN_FLAGS_NAME);
		if (Item.SPAN_SAMPLED.equals(flags)) {
			spanBuilder.exportable(true);
		} else {
			spanBuilder.exportable(
				Item.SPAN_SAMPLED.equals(carrier.get(TMHead.SAMPLED_NAME)));
		}
		String processId = carrier.get(TMHead.PROCESS_ID_NAME);
		String spanName = carrier.get(TMHead.SPAN_NAME_NAME);
		if (spanName != null) {
			spanBuilder.name(spanName);
		}
		if (processId != null) {
			spanBuilder.processId(processId);
		}
		setParentIdIfApplicable(carrier, spanBuilder, TMHead.PARENT_ID_NAME);
		spanBuilder.remote(true);
		for (Map.Entry<String, String> entry : carrier.entrySet()) {
			if (entry.getKey().startsWith(Item.SPAN_BAGGAGE_HEADER_PREFIX + TMHead.HEADER_DELIMITER)) {
				spanBuilder.baggage(unprefixedKey(entry.getKey()), entry.getValue());
			}
		}
		return spanBuilder.build();
	}

	boolean hasHeader(Map<String, String> message, String name) {
		return message.containsKey(name);
	}

	private void setParentIdIfApplicable(Map<String, String> carrier, Item.SpanBuilder spanBuilder,
			String spanParentIdHeader) {
		String parentId = carrier.get(spanParentIdHeader);
		if (parentId != null) {
			spanBuilder.parent(Item.hexToId(parentId));
		}
	}

	private String unprefixedKey(String key) {
		return key.substring(key.indexOf(TMHead.HEADER_DELIMITER) + 1);
	}

}


// Node: generateTraceIdIfMissing
// Node: hasHeader
// Node: extractSpanFromHeaders
// Node: setParentIdIfApplicable
// Node: unprefixedKey
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


// Node: addHeaders


package org.myproject.ms.monitoring.instrument.web;

import java.io.PrintWriter;
import java.lang.invoke.MethodHandles;
import java.util.Locale;

import org.apache.commons.logging.Log;
import org.apache.commons.logging.LogFactory;
import org.myproject.ms.monitoring.Item;


class TPWriter extends PrintWriter {

	private static final Log log = LogFactory.getLog(MethodHandles.lookup().lookupClass());

	private final PrintWriter delegate;
	private final Item span;

	TPWriter(PrintWriter delegate, Item span) {
		super(delegate);
		this.delegate = delegate;
		this.span = span;
	}

	@Override public void flush() {
		if (log.isTraceEnabled()) {
			log.trace("Will annotate SS once the response is flushed");
		}
		SsLogSetter.annotateWithServerSendIfLogIsNotAlreadyPresent(this.span);
		this.delegate.flush();
	}

	@Override public void close() {
		if (log.isTraceEnabled()) {
			log.trace("Will annotate SS once the stream is closed");
		}
		SsLogSetter.annotateWithServerSendIfLogIsNotAlreadyPresent(this.span);
		this.delegate.close();
	}

	@Override public boolean checkError() {
		return this.delegate.checkError();
	}

	@Override public void write(int c) {
		this.delegate.write(c);
	}

	@Override public void write(char[] buf, int off, int len) {
		this.delegate.write(buf, off, len);
	}

	@Override public void write(char[] buf) {
		this.delegate.write(buf);
	}

	@Override public void write(String s, int off, int len) {
		this.delegate.write(s, off, len);
	}

	@Override public void write(String s) {
		this.delegate.write(s);
	}

	@Override public void print(boolean b) {
		this.delegate.print(b);
	}

	@Override public void print(char c) {
		this.delegate.print(c);
	}

	@Override public void print(int i) {
		this.delegate.print(i);
	}

	@Override public void print(long l) {
		this.delegate.print(l);
	}

	@Override public void print(float f) {
		this.delegate.print(f);
	}

	@Override public void print(double d) {
		this.delegate.print(d);
	}

	@Override public void print(char[] s) {
		this.delegate.print(s);
	}

	@Override public void print(String s) {
		this.delegate.print(s);
	}

	@Override public void print(Object obj) {
		this.delegate.print(obj);
	}

	@Override public void println() {
		this.delegate.println();
	}

	@Override public void println(boolean x) {
		this.delegate.println(x);
	}

	@Override public void println(char x) {
		this.delegate.println(x);
	}

	@Override public void println(int x) {
		this.delegate.println(x);
	}

	@Override public void println(long x) {
		this.delegate.println(x);
	}

	@Override public void println(float x) {
		this.delegate.println(x);
	}

	@Override public void println(double x) {
		this.delegate.println(x);
	}

	@Override public void println(char[] x) {
		this.delegate.println(x);
	}

	@Override public void println(String x) {
		this.delegate.println(x);
	}

	@Override public void println(Object x) {
		this.delegate.println(x);
	}

	@Override public PrintWriter printf(String format, Object... args) {
		return this.delegate.printf(format, args);
	}

	@Override public PrintWriter printf(Locale l, String format, Object... args) {
		return this.delegate.printf(l, format, args);
	}

	@Override public PrintWriter format(String format, Object... args) {
		return this.delegate.format(format, args);
	}

	@Override public PrintWriter format(Locale l, String format, Object... args) {
		return this.delegate.format(l, format, args);
	}

	@Override public PrintWriter append(CharSequence csq) {
		return this.delegate.append(csq);
	}

	@Override public PrintWriter append(CharSequence csq, int start, int end) {
		return this.delegate.append(csq, start, end);
	}

	@Override public PrintWriter append(char c) {
		return this.delegate.append(c);
	}
}


// Node: flush
// Node: annotateWithServerSendIfLogIsNotAlreadyPresent
// Node: print


package org.myproject.ms.monitoring.instrument.web;

import java.io.IOException;
import java.lang.invoke.MethodHandles;
import javax.servlet.ServletOutputStream;
import javax.servlet.WriteListener;

import org.apache.commons.logging.Log;
import org.apache.commons.logging.LogFactory;
import org.myproject.ms.monitoring.Item;


class TSOStr extends ServletOutputStream {

	private static final Log log = LogFactory.getLog(MethodHandles.lookup().lookupClass());

	private final ServletOutputStream delegate;
	private final Item span;

	TSOStr(ServletOutputStream delegate, Item span) {
		this.delegate = delegate;
		this.span = span;
	}

	@Override public boolean isReady() {
		return this.delegate.isReady();
	}

	@Override public void setWriteListener(WriteListener listener) {
		this.delegate.setWriteListener(listener);
	}

	@Override public void write(int b) throws IOException {
		this.delegate.write(b);
	}

	@Override public void print(String s) throws IOException {
		this.delegate.print(s);
	}

	@Override public void print(boolean b) throws IOException {
		this.delegate.print(b);
	}

	@Override public void print(char c) throws IOException {
		this.delegate.print(c);
	}

	@Override public void print(int i) throws IOException {
		this.delegate.print(i);
	}

	@Override public void print(long l) throws IOException {
		this.delegate.print(l);
	}

	@Override public void print(float f) throws IOException {
		this.delegate.print(f);
	}

	@Override public void print(double d) throws IOException {
		this.delegate.print(d);
	}

	@Override public void println() throws IOException {
		this.delegate.println();
	}

	@Override public void println(String s) throws IOException {
		this.delegate.println(s);
	}

	@Override public void println(boolean b) throws IOException {
		this.delegate.println(b);
	}

	@Override public void println(char c) throws IOException {
		this.delegate.println(c);
	}

	@Override public void println(int i) throws IOException {
		this.delegate.println(i);
	}

	@Override public void println(long l) throws IOException {
		this.delegate.println(l);
	}

	@Override public void println(float f) throws IOException {
		this.delegate.println(f);
	}

	@Override public void println(double d) throws IOException {
		this.delegate.println(d);
	}

	@Override public void write(byte[] b) throws IOException {
		this.delegate.write(b);
	}

	@Override public void write(byte[] b, int off, int len) throws IOException {
		this.delegate.write(b, off, len);
	}

	@Override public void flush() throws IOException {
		if (log.isTraceEnabled()) {
			log.trace("Will annotate SS once the stream is flushed");
		}
		SsLogSetter.annotateWithServerSendIfLogIsNotAlreadyPresent(this.span);
		this.delegate.flush();
	}

	@Override public void close() throws IOException {
		if (log.isTraceEnabled()) {
			log.trace("Will annotate SS once the stream is closed");
		}
		SsLogSetter.annotateWithServerSendIfLogIsNotAlreadyPresent(this.span);
		this.delegate.close();
	}
}


// Node: setWriteListener


package org.myproject.ms.monitoring.instrument.web;

import java.lang.invoke.MethodHandles;

import org.apache.commons.logging.Log;
import org.apache.commons.logging.LogFactory;
import org.myproject.ms.monitoring.Item;


class SsLogSetter {

	private static final Log log = LogFactory.getLog(MethodHandles.lookup().lookupClass());

	static void annotateWithServerSendIfLogIsNotAlreadyPresent(Item span) {
		if (span == null) {
			return;
		}
		for (org.myproject.ms.monitoring.Log log1 : span.logs()) {
			if (Item.SERVER_SEND.equals(log1.getEvent())) {
				if (log.isTraceEnabled()) {
					log.trace("Span was already annotated with SS, will not do it again");
				}
				return;
			}
		}
		if (log.isTraceEnabled()) {
			log.trace("Will set SS on the span");
		}
		span.logEvent(Item.SERVER_SEND);
	}
}


// Node: skipPattern

package org.myproject.ms.monitoring.instrument.web;

import java.util.regex.Pattern;

import org.springframework.beans.factory.BeanFactory;
import org.springframework.boot.actuate.autoconfigure.ManagementServerProperties;
import org.springframework.boot.autoconfigure.AutoConfigureAfter;
import org.springframework.boot.autoconfigure.condition.ConditionalOnBean;
import org.springframework.boot.autoconfigure.condition.ConditionalOnClass;
import org.springframework.boot.autoconfigure.condition.ConditionalOnMissingBean;
import org.springframework.boot.autoconfigure.condition.ConditionalOnMissingClass;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.boot.autoconfigure.condition.ConditionalOnWebApplication;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.boot.web.servlet.FilterRegistrationBean;
import org.myproject.ms.monitoring.ItemNamer;
import org.myproject.ms.monitoring.ItemReporter;
import org.myproject.ms.monitoring.ChainKeys;
import org.myproject.ms.monitoring.Chainer;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;
import org.springframework.util.StringUtils;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurerAdapter;

import static javax.servlet.DispatcherType.ASYNC;
import static javax.servlet.DispatcherType.ERROR;
import static javax.servlet.DispatcherType.FORWARD;
import static javax.servlet.DispatcherType.INCLUDE;
import static javax.servlet.DispatcherType.REQUEST;


@Configuration
@ConditionalOnProperty(value = "spring.sleuth.web.enabled", matchIfMissing = true)
@ConditionalOnWebApplication
@ConditionalOnBean(Chainer.class)
@AutoConfigureAfter(THAConf.class)
public class TWAConf {

	
	@Configuration
	@ConditionalOnClass(WebMvcConfigurerAdapter.class)
	@Import(TWMConf.class)
	protected static class TraceWebMvcAutoConfiguration {
	}

	@Bean
	public TWAsp traceWebAspect(Chainer tracer, ChainKeys traceKeys,
			ItemNamer spanNamer) {
		return new TWAsp(tracer, spanNamer, traceKeys);
	}

	@Bean
	@ConditionalOnClass(name = "org.springframework.data.rest.webmvc.support.DelegatingHandlerMapping")
	public TSDBPProcess traceSpringDataBeanPostProcessor(
			BeanFactory beanFactory) {
		return new TSDBPProcess(beanFactory);
	}

	@Bean
	public FilterRegistrationBean traceWebFilter(TFilter traceFilter) {
		FilterRegistrationBean filterRegistrationBean = new FilterRegistrationBean(
				traceFilter);
		filterRegistrationBean.setDispatcherTypes(ASYNC, ERROR, FORWARD, INCLUDE,
				REQUEST);
		filterRegistrationBean.setOrder(TFilter.ORDER);
		return filterRegistrationBean;
	}

	@Bean
	public TFilter traceFilter(Chainer tracer, ChainKeys traceKeys,
			SkipPatternProvider skipPatternProvider, ItemReporter spanReporter,
			HSExtra spanExtractor,
			HTKInject httpTraceKeysInjector) {
		return new TFilter(tracer, traceKeys, skipPatternProvider.skipPattern(),
				spanReporter, spanExtractor, httpTraceKeysInjector);
	}

	@Configuration
	@ConditionalOnClass(ManagementServerProperties.class)
	@ConditionalOnMissingBean(SkipPatternProvider.class)
	@EnableConfigurationProperties(SWProp.class)
	protected static class SkipPatternProviderConfig {

		@Bean
		@ConditionalOnBean(ManagementServerProperties.class)
		public SkipPatternProvider skipPatternForManagementServerProperties(
				final ManagementServerProperties managementServerProperties,
				final SWProp sleuthWebProperties) {
			return new SkipPatternProvider() {
				@Override
				public Pattern skipPattern() {
					return getPatternForManagementServerProperties(
							managementServerProperties,
							sleuthWebProperties);
				}
			};
		}

		
		static Pattern getPatternForManagementServerProperties(
				ManagementServerProperties managementServerProperties,
				SWProp sleuthWebProperties) {
			String skipPattern = sleuthWebProperties.getSkipPattern();
			if (StringUtils.hasText(skipPattern)
					&& StringUtils.hasText(managementServerProperties.getContextPath())) {
				return Pattern.compile(skipPattern + "|"
						+ managementServerProperties.getContextPath() + ".*");
			}
			else if (StringUtils.hasText(managementServerProperties.getContextPath())) {
				return Pattern
						.compile(managementServerProperties.getContextPath() + ".*");
			}
			return defaultSkipPattern(skipPattern);
		}

		@Bean
		@ConditionalOnMissingBean(ManagementServerProperties.class)
		public SkipPatternProvider defaultSkipPatternBeanIfManagementServerPropsArePresent(SWProp sleuthWebProperties) {
			return defaultSkipPatternProvider(sleuthWebProperties.getSkipPattern());
		}
	}

	@Bean
	@ConditionalOnMissingClass("org.springframework.boot.actuate.autoconfigure.ManagementServerProperties")
	@ConditionalOnMissingBean(SkipPatternProvider.class)
	public SkipPatternProvider defaultSkipPatternBean(SWProp sleuthWebProperties) {
		return defaultSkipPatternProvider(sleuthWebProperties.getSkipPattern());
	}

	private static SkipPatternProvider defaultSkipPatternProvider(
			final String skipPattern) {
		return new SkipPatternProvider() {
			@Override
			public Pattern skipPattern() {
				return defaultSkipPattern(skipPattern);
			}
		};
	}

	private static Pattern defaultSkipPattern(String skipPattern) {
		return StringUtils.hasText(skipPattern) ? Pattern.compile(skipPattern)
				: Pattern.compile(SWProp.DEFAULT_SKIP_PATTERN);
	}

	interface SkipPatternProvider {
		Pattern skipPattern();
	}
}


// Node: getPatternForManagementServerProperties
// Node: defaultSkipPattern


package org.myproject.ms.monitoring.instrument.web;

import javax.servlet.http.HttpServletRequest;
import java.util.Enumeration;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;

import org.myproject.ms.monitoring.ItemTextMap;
import org.springframework.web.util.UrlPathHelper;


class HSRTMap implements ItemTextMap {

	private final HttpServletRequest delegate;
	private final Map<String, String> additionalHeaders = new HashMap<>();

	HSRTMap(HttpServletRequest delegate) {
		this.delegate = delegate;
		UrlPathHelper urlPathHelper = new UrlPathHelper();
		this.additionalHeaders.put(ZHSExtra.URI_HEADER,
				urlPathHelper.getPathWithinApplication(delegate));
	}

	@Override
	public Iterator<Map.Entry<String, String>> iterator() {
		Map<String, String> map = new HashMap<>();
		Enumeration<String> headerNames = this.delegate.getHeaderNames();
		while (headerNames != null && headerNames.hasMoreElements()) {
			String name = headerNames.nextElement();
			map.put(name, this.delegate.getHeader(name));
		}
		map.putAll(this.additionalHeaders);
		return map.entrySet().iterator();
	}

	@Override
	public void put(String key, String value) {
		this.additionalHeaders.put(key, value);
	}
}


// Node: nextElement
package org.myproject.ms.monitoring.instrument.web;

import java.lang.invoke.MethodHandles;
import java.util.Map;
import java.util.Random;
import java.util.regex.Pattern;

import org.apache.commons.logging.LogFactory;
import org.myproject.ms.monitoring.Item;
import org.myproject.ms.monitoring.ItemTextMap;
import org.myproject.ms.monitoring.util.TextMapUtil;
import org.springframework.util.StringUtils;


public class ZHSExtra implements HSExtra {

	private static final org.apache.commons.logging.Log log = LogFactory.getLog(
			MethodHandles.lookup().lookupClass());
	private static final String HEADER_DELIMITER = "-";
	static final String URI_HEADER = "X-Span-Uri";
	private static final String HTTP_COMPONENT = "http";

	private final Pattern skipPattern;

	public ZHSExtra(Pattern skipPattern) {
		this.skipPattern = skipPattern;
	}

	@Override
	public Item joinTrace(ItemTextMap textMap) {
		Map<String, String> carrier = TextMapUtil.asMap(textMap);
		boolean debug = Item.SPAN_SAMPLED.equals(carrier.get(Item.SPAN_FLAGS));
		if (debug) {
			// we're only generating Trace ID since if there's no Span ID will assume
			// that it's equal to Trace ID
			generateIdIfMissing(carrier, Item.TRACE_ID_NAME);
		} else if (carrier.get(Item.TRACE_ID_NAME) == null) {
			// can't build a Span without trace id
			return null;
		}
		try {
			String uri = carrier.get(URI_HEADER);
			boolean skip = this.skipPattern.matcher(uri).matches()
					|| Item.SPAN_NOT_SAMPLED.equals(carrier.get(Item.SAMPLED_NAME));
			long spanId = spanId(carrier);
			return buildParentSpan(carrier, uri, skip, spanId);
		} catch (Exception e) {
			log.error("Exception occurred while trying to extract span from carrier", e);
			return null;
		}
	}

	private void generateIdIfMissing(Map<String, String> carrier, String key) {
		if (!carrier.containsKey(key)) {
			carrier.put(key, Item.idToHex(new Random().nextLong()));
		}
	}

	private long spanId(Map<String, String> carrier) {
		String spanId = carrier.get(Item.SPAN_ID_NAME);
		if (spanId == null) {
			if (log.isDebugEnabled()) {
				log.debug("Request is missing a span id but it has a trace id. We'll assume that this is "
						+ "a root span with span id equal to the lower 64-bits of the trace id");
			}
			return Item.hexToId(carrier.get(Item.TRACE_ID_NAME));
		} else {
			return Item.hexToId(spanId);
		}
	}

	private Item buildParentSpan(Map<String, String> carrier, String uri, boolean skip, long spanId) {
		String traceId = carrier.get(Item.TRACE_ID_NAME);
		Item.SpanBuilder span = Item.builder()
				.traceIdHigh(traceId.length() == 32 ? Item.hexToId(traceId, 0) : 0)
				.traceId(Item.hexToId(traceId))
				.spanId(spanId);
		String processId = carrier.get(Item.PROCESS_ID_NAME);
		String parentName = carrier.get(Item.SPAN_NAME_NAME);
		if (StringUtils.hasText(parentName)) {
			span.name(parentName);
		}  else {
			span.name(HTTP_COMPONENT + ":/parent" + uri);
		}
		if (StringUtils.hasText(processId)) {
			span.processId(processId);
		}
		if (carrier.containsKey(Item.PARENT_ID_NAME)) {
			span.parent(Item.hexToId(carrier.get(Item.PARENT_ID_NAME)));
		}
		span.remote(true);
		boolean debug = Item.SPAN_SAMPLED.equals(carrier.get(Item.SPAN_FLAGS));
		if (debug) {
			span.exportable(true);
		} else if (skip) {
			span.exportable(false);
		}
		for (Map.Entry<String, String> entry : carrier.entrySet()) {
			if (entry.getKey().startsWith(Item.SPAN_BAGGAGE_HEADER_PREFIX + HEADER_DELIMITER)) {
				span.baggage(unprefixedKey(entry.getKey()), entry.getValue());
			}
		}
		return span.build();
	}

	private String unprefixedKey(String key) {
		return key.substring(key.indexOf(HEADER_DELIMITER) + 1);
	}

}


// Node: generateIdIfMissing
// Node: buildParentSpan
package org.myproject.ms.monitoring.instrument.web;

import java.util.Map;

import org.myproject.ms.monitoring.Item;
import org.myproject.ms.monitoring.ItemTextMap;
import org.springframework.util.StringUtils;


public class ZHSInject implements HSInject {

	private static final String HEADER_DELIMITER = "-";

	@Override
	public void inject(Item span, ItemTextMap carrier) {
		setHeader(carrier, Item.TRACE_ID_NAME, span.traceIdString());
		setIdHeader(carrier, Item.SPAN_ID_NAME, span.getSpanId());
		setHeader(carrier, Item.SAMPLED_NAME, span.isExportable() ? Item.SPAN_SAMPLED : Item.SPAN_NOT_SAMPLED);
		setHeader(carrier, Item.SPAN_NAME_NAME, span.getName());
		setIdHeader(carrier, Item.PARENT_ID_NAME, getParentId(span));
		setHeader(carrier, Item.PROCESS_ID_NAME, span.getProcessId());
		for (Map.Entry<String, String> entry : span.baggageItems()) {
			carrier.put(prefixedKey(entry.getKey()), entry.getValue());
		}
	}

	private String prefixedKey(String key) {
		if (key.startsWith(Item.SPAN_BAGGAGE_HEADER_PREFIX + HEADER_DELIMITER)) {
			return key;
		}
		return Item.SPAN_BAGGAGE_HEADER_PREFIX + HEADER_DELIMITER + key;
	}

	private Long getParentId(Item span) {
		return !span.getParents().isEmpty() ? span.getParents().get(0) : null;
	}

	private void setIdHeader(ItemTextMap carrier, String name, Long value) {
		if (value != null) {
			setHeader(carrier, name, Item.idToHex(value));
		}
	}

	private void setHeader(ItemTextMap carrier, String name, String value) {
		if (StringUtils.hasText(value)) {
			carrier.put(name, value);
		}
	}

}


// Node: setIdHeader
// Node: getParentId


package org.myproject.ms.monitoring.instrument.web;

import java.lang.invoke.MethodHandles;
import java.util.concurrent.atomic.AtomicReference;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import org.apache.commons.logging.Log;
import org.apache.commons.logging.LogFactory;
import org.springframework.beans.factory.BeanFactory;
import org.springframework.beans.factory.NoSuchBeanDefinitionException;
import org.springframework.boot.autoconfigure.web.ErrorController;
import org.myproject.ms.monitoring.Item;
import org.myproject.ms.monitoring.ChainKeys;
import org.myproject.ms.monitoring.Chainer;
import org.myproject.ms.monitoring.util.ExceptionUtils;
import org.myproject.ms.monitoring.util.ItemNameUtil;
import org.springframework.web.method.HandlerMethod;
import org.springframework.web.servlet.handler.HandlerInterceptorAdapter;


public class THInter extends HandlerInterceptorAdapter {

	private static final Log log = LogFactory.getLog(MethodHandles.lookup().lookupClass());

	private final BeanFactory beanFactory;

	private Chainer tracer;
	private ChainKeys traceKeys;
	private AtomicReference<ErrorController> errorController;

	public THInter(BeanFactory beanFactory) {
		this.beanFactory = beanFactory;
	}

	@Override
	public boolean preHandle(HttpServletRequest request, HttpServletResponse response,
			Object handler) throws Exception {
		String spanName = spanName(handler);
		boolean continueSpan = getRootSpanFromAttribute(request) != null;
		Item span = continueSpan ? getRootSpanFromAttribute(request) : getTracer().createSpan(spanName);
		if (log.isDebugEnabled()) {
			log.debug("Handling span " + span);
		}
		addClassMethodTag(handler, span);
		addClassNameTag(handler, span);
		setSpanInAttribute(request, span);
		if (!continueSpan) {
			setNewSpanCreatedAttribute(request, span);
		}
		return true;
	}

	private boolean isErrorControllerRelated(HttpServletRequest request) {
		return getErrorController() != null && getErrorController().getErrorPath()
				.equals(request.getRequestURI());
	}

	private void addClassMethodTag(Object handler, Item span) {
		if (handler instanceof HandlerMethod) {
			String methodName = ((HandlerMethod) handler).getMethod().getName();
			getTracer().addTag(getTraceKeys().getMvc().getControllerMethod(), methodName);
			if (log.isDebugEnabled()) {
				log.debug("Adding a method tag with value [" + methodName + "] to a span " + span);
			}
		}
	}

	private void addClassNameTag(Object handler, Item span) {
		String className;
		if (handler instanceof HandlerMethod) {
			className = ((HandlerMethod) handler).getBeanType().getSimpleName();
		} else {
			className = handler.getClass().getSimpleName();
		}
		if (log.isDebugEnabled()) {
			log.debug("Adding a class tag with value [" + className + "] to a span " + span);
		}
		getTracer().addTag(getTraceKeys().getMvc().getControllerClass(), className);
	}

	private String spanName(Object handler) {
		if (handler instanceof HandlerMethod) {
			return ItemNameUtil.toLowerHyphen(((HandlerMethod) handler).getMethod().getName());
		}
		return ItemNameUtil.toLowerHyphen(handler.getClass().getSimpleName());
	}

	@Override
	public void afterConcurrentHandlingStarted(HttpServletRequest request,
			HttpServletResponse response, Object handler) throws Exception {
		Item spanFromRequest = getNewSpanFromAttribute(request);
		Item rootSpanFromRequest = getRootSpanFromAttribute(request);
		if (log.isDebugEnabled()) {
			log.debug("Closing the span " + spanFromRequest + " and detaching its parent " + rootSpanFromRequest + " since the request is asynchronous");
		}
		getTracer().close(spanFromRequest);
		getTracer().detach(rootSpanFromRequest);
	}

	@Override
	public void afterCompletion(HttpServletRequest request, HttpServletResponse response,
			Object handler, Exception ex) throws Exception {
		if (isErrorControllerRelated(request)) {
			if (log.isDebugEnabled()) {
				log.debug("Skipping closing of a span for error controller processing");
			}
			return;
		}
		Item span = getRootSpanFromAttribute(request);
		if (ex != null) {
			String errorMsg = ExceptionUtils.getExceptionMessage(ex);
			if (log.isDebugEnabled()) {
				log.debug("Adding an error tag [" + errorMsg + "] to span " + span + "");
			}
			getTracer().addTag(Item.SPAN_ERROR_TAG_NAME, errorMsg);
		}
		if (getNewSpanFromAttribute(request) != null) {
			if (log.isDebugEnabled()) {
				log.debug("Closing span " + span);
			}
			Item newSpan = getNewSpanFromAttribute(request);
			getTracer().continueSpan(newSpan);
			getTracer().close(newSpan);
			clearNewSpanCreatedAttribute(request);
		}
	}

	private Item getNewSpanFromAttribute(HttpServletRequest request) {
		return (Item) request.getAttribute(TRAttr.NEW_SPAN_REQUEST_ATTR);
	}

	private Item getRootSpanFromAttribute(HttpServletRequest request) {
		return (Item) request.getAttribute(TFilter.TRACE_REQUEST_ATTR);
	}

	private void setSpanInAttribute(HttpServletRequest request, Item span) {
		request.setAttribute(TRAttr.HANDLED_SPAN_REQUEST_ATTR, span);
	}

	private void setNewSpanCreatedAttribute(HttpServletRequest request, Item span) {
		request.setAttribute(TRAttr.NEW_SPAN_REQUEST_ATTR, span);
	}

	private void clearNewSpanCreatedAttribute(HttpServletRequest request) {
		request.removeAttribute(TRAttr.NEW_SPAN_REQUEST_ATTR);
	}

	private Chainer getTracer() {
		if (this.tracer == null) {
			this.tracer = this.beanFactory.getBean(Chainer.class);
		}
		return this.tracer;
	}

	private ChainKeys getTraceKeys() {
		if (this.traceKeys == null) {
			this.traceKeys = this.beanFactory.getBean(ChainKeys.class);
		}
		return this.traceKeys;
	}

	ErrorController getErrorController() {
		if (this.errorController == null) {
			try {
				ErrorController errorController = this.beanFactory.getBean(ErrorController.class);
				this.errorController = new AtomicReference<>(errorController);
			} catch (NoSuchBeanDefinitionException e) {
				if (log.isTraceEnabled()) {
					log.trace("ErrorController bean not found");
				}
				this.errorController = new AtomicReference<>();
			}
		}
		return this.errorController.get();
	}

}




package org.myproject.ms.monitoring.instrument.web.client;

import java.util.AbstractMap;
import java.util.Collections;
import java.util.Iterator;
import java.util.List;
import java.util.Map;

import org.myproject.ms.monitoring.ItemTextMap;
import org.springframework.http.HttpRequest;
import org.springframework.util.StringUtils;


class HRTMap implements ItemTextMap {

	private final HttpRequest delegate;

	HRTMap(HttpRequest delegate) {
		this.delegate = delegate;
	}

	@Override
	public Iterator<Map.Entry<String, String>> iterator() {
		final Iterator<Map.Entry<String, List<String>>> iterator = this.delegate.getHeaders()
				.entrySet().iterator();
		return new Iterator<Map.Entry<String, String>>() {
			@Override public boolean hasNext() {
				return iterator.hasNext();
			}

			@Override public Map.Entry<String, String> next() {
				Map.Entry<String, List<String>> next = iterator.next();
				List<String> value = next.getValue();
				return new AbstractMap.SimpleEntry<>(next.getKey(), value.isEmpty() ? "" : value.get(0));
			}
		};
	}

	@Override
	public void put(String key, String value) {
		if (!StringUtils.hasText(value)) {
			return;
		}
		this.delegate.getHeaders().put(key, Collections.singletonList(value));
	}
}


// Node: singletonList


package org.myproject.ms.monitoring.atcfg;

import java.util.HashMap;
import java.util.Map;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.env.EnvironmentPostProcessor;
import org.springframework.core.env.ConfigurableEnvironment;
import org.springframework.core.env.MapPropertySource;
import org.springframework.core.env.MutablePropertySources;
import org.springframework.core.env.PropertySource;


public class TraceEnvironmentPostProcessor implements EnvironmentPostProcessor {

	private static final String PROPERTY_SOURCE_NAME = "defaultProperties";

	@Override
	public void postProcessEnvironment(ConfigurableEnvironment environment,
			SpringApplication application) {
		Map<String, Object> map = new HashMap<String, Object>();
		// This doesn't work with all logging systems but it's a useful default so you see
		// traces in logs without having to configure it.
		map.put("logging.pattern.level",
				"%5p [${spring.zipkin.service.name:${spring.application.name:-}},%X{X-B3-TraceId:-},%X{X-B3-SpanId:-},%X{X-Span-Export:-}]");
		map.put("spring.aop.proxyTargetClass", "true");
		addOrReplace(environment.getPropertySources(), map);
	}

	private void addOrReplace(MutablePropertySources propertySources,
			Map<String, Object> map) {
		MapPropertySource target = null;
		if (propertySources.contains(PROPERTY_SOURCE_NAME)) {
			PropertySource<?> source = propertySources.get(PROPERTY_SOURCE_NAME);
			if (source instanceof MapPropertySource) {
				target = (MapPropertySource) source;
				for (String key : map.keySet()) {
					if (!target.containsProperty(key)) {
						target.getSource().put(key, map.get(key));
					}
				}
			}
		}
		if (target == null) {
			target = new MapPropertySource(PROPERTY_SOURCE_NAME, map);
		}
		if (!propertySources.contains(PROPERTY_SOURCE_NAME)) {
			propertySources.addLast(target);
		}
	}

}


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/atcfg/TraceEnvironmentPostProcessor.java:TraceEnvironmentPostProcessor.<init>
// Node: postProcessEnvironment
// Node: addOrReplace
// Node: getPropertySources
// Node: keySet
// Node: containsProperty
// Node: getSource
// Node: MapPropertySource
// Node: addLast
package org.services.analysis;

import java.io.File;
import java.util.ArrayList;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class Test {
    private static String SRC_DIR = "D:\\workspace\\microservice\\faults\\F1\\step2_fault_origin_traces";

    public static void  main(String[] args){
        String mircroServiceName = "{traceId=1b114102c6306ef8, spanId=1b114102c6306ef8, hostName=ts-order-service, destName=null, host=ts-order-service, clock={\"ts-order-service\":4,\"ts-sso-service\":2}, dest=null, event=ts-order-service.OrderController.queryOrders, type=ss, parentId=, timestamp=1516255241135800, }";
        Pattern patternNode = Pattern.compile("host=(\\S*),");
        Matcher matcherCase = patternNode.matcher(mircroServiceName);
        if(matcherCase.find()){
            System.out.println(matcherCase.group(1));
        }
    }

    //Get all the test case directory
    private static ArrayList<File> getTestCaseDirList(String path){
        ArrayList<File> testDirs = new ArrayList<File>();
        File rootDir = new File(path);
        File[] dirList = rootDir.listFiles();
        for (int i = 0; i < dirList.length; i++) {
            File file = dirList[i];
            if(file.isDirectory())
                testDirs.add(file);
        }
        return testDirs;
    }
}


// Node: find
// Node: group
// Node: getTestCaseDirList
// Node: File
// Node: listFiles
// Node: isDirectory
package org.services.analysis;

import java.util.HashMap;

/**
 * Created by Administrator on 2017/7/18.
 */
public class Clock {

    private String type;
    private String host;
    private String src;
    private String traceId;
    private String spanId;
    private String parentId;

    private HashMap<String,Integer> clock;

    public Clock(String type, String host, String src, String traceId, String spanId, String parentId, HashMap<String,Integer> clock) {
        this.type = type;
        this.host = host;
        this.src = src;
        this.traceId = traceId;
        this.spanId = spanId;
        this.parentId = parentId;
        this.clock = clock;
    }

    public HashMap<String,Integer> getClock() {
        return clock;
    }

    public boolean isSrc(String traceId, String spanId, String type, String queue, String parentId){
        boolean result = false;

        if("queue".equals(queue)){
            if(traceId.equals(this.traceId) && parentId.equals(this.spanId)){
                if(type.equals("sr") && this.type.equals("cs")){
                    result = true;
                }
            }
        }else{
            if(traceId.equals(this.traceId) && spanId.equals(this.spanId)){
                if(type.equals("sr") && this.type.equals("cs")){
                    result = true;
                }else if(type.equals("cr") && this.type.equals("ss")){
                    result = true;
                }
            }
        }


        return result;
    }
}


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Json2Shiviz/src/main/java/org/services/analysis/Clock.java:Clock.<init>
// Node: Clock
// Node: getClock
// Node: isSrc
package org.services.analysis;

import java.io.*;
import java.util.ArrayList;
import java.util.List;

public class AggregateAllCases {
    private static String ROOT_DIR = "C:\\Users\\dingding\\Desktop\\faults\\F13\\step3_fault_shiviz_traces";
    private static String SINGLEAGGREGATEFILENAME = "all.txt";
    private static String ALLAGGREGATEFILENAME = "AllCasesResult.txt";

    public static void main(String[] args){
        String destFilePath = String.format("%s\\%s",ROOT_DIR,ALLAGGREGATEFILENAME);
        File destFile = new File(destFilePath);
        try {
            destFile.createNewFile();
            FileOutputStream fileOutputStream = new FileOutputStream(destFile);
            List<File> dirList = getTestCaseDirList(ROOT_DIR);//Get case1, case2... directory
            for (int index1 = 0; index1 < dirList.size(); index1++) {
                File file = new File(String.format("%s\\%s\\%s",ROOT_DIR,dirList.get(index1).getName(),SINGLEAGGREGATEFILENAME));
                StringBuilder sb = new StringBuilder();
                InputStreamReader reader = new InputStreamReader(new FileInputStream(file));
                BufferedReader br = new BufferedReader(reader);
                String line = null;
                while((line = br.readLine())!=null){
                    sb.append(line);
                    sb.append("\r\n");
                }
                reader.close();
                fileOutputStream.write(sb.toString().getBytes());
            }
            fileOutputStream.close();
        }
        catch (Exception e){
            e.printStackTrace();
        }
    }

    //Get all the test case directory
    private static ArrayList<File> getTestCaseDirList(String path) {
        ArrayList<File> testDirs = new ArrayList<File>();
        File rootDir = new File(path);
        File[] dirList = rootDir.listFiles();
        for (int i = 0; i < dirList.length; i++) {
            File file = dirList[i];
            if (file.isDirectory())
                testDirs.add(file);
        }
        return testDirs;
    }

    //Get all the shiviz txt file
    private static ArrayList<File> getListFiles(Object obj) {
        File directory = null;
        if (obj instanceof File) {
            directory = (File) obj;
        } else {
            directory = new File(obj.toString());
        }
        ArrayList<File> files = new ArrayList<File>();
        if (directory.isFile()) {
            files.add(directory);
            return files;
        } else if (directory.isDirectory()) {
            File[] fileArr = directory.listFiles();
            for (int i = 0; i < fileArr.length; i++) {
                File fileOne = fileArr[i];
                if (fileOne.getName().endsWith(".txt")) {
                    files.addAll(getListFiles(fileOne));
                }
            }
        }
        return files;
    }
}


// Node: createNewFile
// Node: FileOutputStream
// Node: InputStreamReader
// Node: FileInputStream
// Node: BufferedReader
// Node: readLine
// Node: getListFiles
// Node: isFile
// Node: endsWith
package org.services.analysis;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileInputStream;
import java.io.InputStreamReader;
import java.util.HashSet;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class CalculateEventAndNode {

    private static String ROOT_DIR = "C:\\Users\\dingding\\Desktop\\tse debug exp\\F20\\shiviz\\4 scope failure elements\\shiviz_trace";
    private static String caseDirectory = "case1";
    private static String fileName = "all.txt";
    private static Pattern patternEvent = Pattern.compile("\\{traceId=.*spanId=.*event=.*\\}");
    private static Pattern patternNode = Pattern.compile("host=(\\S*),");
    private static HashSet<String> nodes = new HashSet<String>();

    public static void main(String[] args){
        try {
            int count = 0;
            File file = new File(String.format("%s\\%s\\%s",ROOT_DIR,caseDirectory,fileName));
            InputStreamReader reader = new InputStreamReader(new FileInputStream(file));
            BufferedReader br = new BufferedReader(reader);
            String line = null;
            while((line = br.readLine())!=null){
                Matcher matcherEvent = patternEvent.matcher(line);
                if(matcherEvent.find()) {
                    System.out.println(line);
                    count ++;
                    Matcher matcherNode = patternNode.matcher(line);
                    if(matcherNode.find()){
                        nodes.add(matcherNode.group(1));
                    }
                }
            }
            System.out.println(nodes);
            System.out.println(String.format("The number of event is [%d]", count));
            System.out.println(String.format("The number of node is [%d]", nodes.size()));
            reader.close();
        }
        catch (Exception e){
            e.printStackTrace();
        }

    }

}


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Json2Shiviz/src/main/java/org/services/analysis/CalculateEventAndNode.java:CalculateEventAndNode.<init>
/*
 * This Java source file was generated by the Gradle 'init' task.
 */

package org.services.analysis;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

import org.json.JSONArray;
import org.json.JSONObject;

public class CallAnalysis {

	public static void main(String[] args) {

		HashMap<String, HashMap<String, Object>> traces = new HashMap<String, HashMap<String, Object>>();
		List<String> pListAll = new ArrayList<String>();

		String traceStr = readFile("./sample/traces-error-normal.json");
		JSONArray tracelist = new JSONArray(traceStr);

		for (int k = 0; k < tracelist.length(); k++) {
			JSONArray traceobj = (JSONArray) tracelist.get(k);

			// String call = readFile("./sample/call1x.json");
			// JSONArray spanlist = new JSONArray(call);

			List<HashMap<String, String>> serviceList = new ArrayList<HashMap<String, String>>();
			String traceId = ((JSONObject) traceobj.get(0)).getString("traceId");
			for (int j = 0; j < traceobj.length(); j++) {
				JSONObject spanobj = (JSONObject) traceobj.get(j);

				// String traceId = spanobj.getString("traceId");
				String id = spanobj.getString("id");
				String pid = "";
				if (spanobj.has("parentId")) {
					pid = spanobj.getString("parentId");
				}
				String name = spanobj.getString("name");

				HashMap<String, String> content = new HashMap<String, String>();
				content.put("spanid", id);
				content.put("parentid", pid);
				content.put("spanname", name);
				if(spanobj.has("annotations")){
					JSONArray annotations = spanobj.getJSONArray("annotations");
					for (int i = 0; i < annotations.length(); i++) {
						JSONObject anno = annotations.getJSONObject(i);
						if ("sr".equals(anno.getString("value"))) {
							JSONObject endpoint = anno.getJSONObject("endpoint");
							String service = endpoint.getString("serviceName");
							content.put("service", service);
						}
					}
					
					if (name.contains("message:")) {
						if ("message:input".equals(name)) {
							content.put("api", content.get("service") + "." + "message_received");
						}
					} else {
						JSONArray binaryAnnotations = spanobj.getJSONArray("binaryAnnotations");
						for (int i = 0; i < binaryAnnotations.length(); i++) {
							JSONObject anno = binaryAnnotations.getJSONObject(i);
							if ("error".equals(anno.getString("key"))) {
								content.put("error", anno.getString("value"));
							}
							if ("mvc.controller.class".equals(anno.getString("key"))
									&& !"BasicErrorController".equals(anno.getString("value"))) {
								String classname = anno.getString("value");
								content.put("classname", classname);
							}
							if ("mvc.controller.method".equals(anno.getString("key"))
									&& !"errorHtml".equals(anno.getString("value"))) {
								String methodname = anno.getString("value");
								content.put("methodname", methodname);
							}
						}
						content.put("api",
								content.get("service") + "." + content.get("classname") + "." + content.get("methodname"));
					}
					
					serviceList.add(content);
				}
			}

			// filter validate service api
			List<HashMap<String, String>> processList = serviceList.stream()
					.filter(elem -> !"message:output".equals(elem.get("spanname"))).collect(Collectors.toList());
			// processList.stream().forEach(n -> System.out.println(n));
			boolean failed = processList.stream().anyMatch(pl -> pl.containsKey("error"));

			// final info
			List<String> pList = processList.stream().map(pl -> {
				return pl.get("api");
			}).collect(Collectors.toList());
			pList.stream().forEach(n -> System.out.println(n));
			pListAll.addAll(pList);

			HashMap<String, Object> traceContent = new HashMap<String, Object>();
			traceContent.put("failed", failed);
			traceContent.put("list", pList);
			traces.put(traceId, traceContent);

		}
		
//		traces.forEach((key, val) -> System.out.println(val));
		
		System.out.println("---------------result-------------------");
		//all 
		double N = traces.keySet().size();
		//failed
		double NF = traces.values().stream().filter(trace->{
			return (Boolean)trace.get("failed");
		}).collect(Collectors.toList()).size();
		double NS = N - NF;
		System.out.println("Failed cases: " + NF);
		System.out.println("Success cases: " + NS);
		//method/spectrum list
		pListAll = pListAll.stream().distinct().collect(Collectors.toList());
//		methods.stream().forEach(n -> System.out.println(n));
		
		HashMap<String, Double> pListNCF = new HashMap<String, Double>();
		pListAll.stream().forEach(pl -> pListNCF.put(pl, 0.0));
		HashMap<String, Double> pListNCS = new HashMap<String, Double>();
		pListAll.stream().forEach(pl -> pListNCS.put(pl, 0.0));
		
		traces.values().stream().forEach(trace->{
			List<String> pList = (List<String>)trace.get("list");
			if((Boolean)trace.get("failed")){
				pList.stream().forEach(pl -> pListNCF.put(pl, pListNCF.get(pl)+1));
			}else{
				pList.stream().forEach(pl -> pListNCS.put(pl, pListNCS.get(pl)+1));
			}
		});
		
//		System.out.println(pListNCF);
//		System.out.println(pListNCS);
		
		//calculate Suspiciousness
		//NCF/NF // NCF/NF + NCS/NS
		//NCF // sqrt(NF*(NCF + NCS))
		HashMap<String, Double> pListSuspicious = new HashMap<String, Double>();
		pListAll.stream().forEach(pl -> {
//			double susp = (pListNCF.get(pl)/NF)  /  (pListNCF.get(pl)/NF + pListNCS.get(pl)/NS);
			double susp = (pListNCF.get(pl))  / Math.sqrt(NF*(pListNCF.get(pl) + pListNCS.get(pl)));
			pListSuspicious.put(pl, susp);
		});
//		System.out.println(pListSuspicious);
		
		Map<String, Double> result = pListSuspicious.entrySet().stream()
                .sorted(Map.Entry.comparingByValue(Comparator.reverseOrder()))
                .collect(Collectors.toMap(Map.Entry::getKey, Map.Entry::getValue,
                        (oldValue, newValue) -> oldValue, LinkedHashMap::new));
		result.entrySet().stream().forEach(System.out::println);
//		System.out.println(result);
		
		
		
		
	}

	public static String readFile(String path) {
		File file = new File(path);
		BufferedReader reader = null;
		String laststr = "";
		try {
			reader = new BufferedReader(new FileReader(file));
			String tempString = null;
			while ((tempString = reader.readLine()) != null) {
				laststr = laststr + tempString;
			}
			reader.close();
		} catch (IOException e) {
			e.printStackTrace();
		} finally {
			if (reader != null) {
				try {
					reader.close();
				} catch (IOException e1) {
				}
			}
		}
		return laststr;
	}
}


// Node: readFile
// Node: JSONArray
// Node: getString
// Node: has
// Node: getJSONArray
// Node: getJSONObject
// Node: forEach
// Node: anyMatch
// Node: distinct
// Node: sqrt
// Node: sorted
// Node: comparingByValue
// Node: reverseOrder
// Node: FileReader
package org.services.analysis;

import java.io.*;
import java.util.ArrayList;
import java.util.List;

public class AggregateEachCase {
    private static String ROOT_DIR = "C:\\Users\\dingding\\Desktop\\tse debug exp\\F20\\shiviz\\4 scope failure elements\\shiviz_trace";
    private static String AGGREGATEFILENAME = "all.txt";

    public static void main(String[] args){
        List<File> dirList = getTestCaseDirList(ROOT_DIR);//Get case1, case2... directory
        for (int index1 = 0; index1 < dirList.size(); index1++) {

            String dirName = dirList.get(index1).getName();//case1, for example
            String destDir = String.format("%s\\%s", ROOT_DIR, dirName);
            String destFilePath = String.format("%s\\%s",destDir,AGGREGATEFILENAME);

            File destFile = new File(destFilePath);
            try {
                destFile.createNewFile();
                FileOutputStream fileOutputStream = new FileOutputStream(destFile);

                List<File> subDirList = getTestCaseDirList(destDir);//Get fail1,fail2... directory
                System.out.println(subDirList);
                for (int index2 = 0; index2 < subDirList.size(); index2++) {
                    List<File> fileLists = getListFiles(subDirList.get(index2));
                    //Aggreate all of the txt file
                    for (int x = 0; x < fileLists.size(); x++) {
                        File file = fileLists.get(x);
                        StringBuilder sb = new StringBuilder();
                        InputStreamReader reader = new InputStreamReader(new FileInputStream(file));
                        BufferedReader br = new BufferedReader(reader);
                        String line = null;
                        while((line = br.readLine())!=null){
                            sb.append(line);
                            sb.append("\r\n");
                        }
                        reader.close();
                        fileOutputStream.write(sb.toString().getBytes());
                    }
                }
                fileOutputStream.close();
            }
            catch(Exception e){
                e.printStackTrace();
            }
        }
    }

    //Get all the test case directory
    private static ArrayList<File> getTestCaseDirList(String path) {
        ArrayList<File> testDirs = new ArrayList<File>();
        File rootDir = new File(path);
        File[] dirList = rootDir.listFiles();
        for (int i = 0; i < dirList.length; i++) {
            File file = dirList[i];
            if (file.isDirectory())
                testDirs.add(file);
        }
        return testDirs;
    }

    //Get all the shiviz txt file
    private static ArrayList<File> getListFiles(Object obj) {
        File directory = null;
        if (obj instanceof File) {
            directory = (File) obj;
        } else {
            directory = new File(obj.toString());
        }
        ArrayList<File> files = new ArrayList<File>();
        if (directory.isFile()) {
            files.add(directory);
            return files;
        } else if (directory.isDirectory()) {
            File[] fileArr = directory.listFiles();
            for (int i = 0; i < fileArr.length; i++) {
                File fileOne = fileArr[i];
                if (fileOne.getName().endsWith(".txt")) {
                    files.addAll(getListFiles(fileOne));
                }
            }
        }
        return files;
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


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Json2Shiviz/src/main/java/org/services/analysis/Span.java:Span.<init>
// Node: addLog
// Node: getLogs
// Node: getChilds
// Node: setChilds
// Node: getSpanname
package org.services.analysis;

///**
// * Created by hh on 2017-07-08.
// */
///**
// * Created by Administrator on 2017/7/11.
// */

import java.io.*;
import java.sql.Timestamp;
import java.util.*;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.stream.Collectors;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

/**
 * Created by hh on 2017-07-08.
 */
public class TraceTranslator {

//    private static String SRC_DIR = "F:\\gitwork\\fault_replicate\\faults-dingding\\F2\\step2_fault_origin_traces";
    private static String SRC_DIR = "./example/zipkin_log";
    private static String DEST_DIR = "./example/shiviz_log";

//    private static String DEST_DIR = "F:\\gitwork\\fault_replicate\\faults-dingding\\F2\\step3_fault_shiviz_traces";

    public static void main(String[] args) throws JSONException {
        List<File> dirList = getTestCaseDirList(SRC_DIR);//Get case1, case2... directory
        for (int index1 = 0; index1 < dirList.size(); index1++) {
            String dirName = dirList.get(index1).getName();//case1, for example

            //Get the test case number
            Pattern patternCaseNumber = Pattern.compile("case([0-9]+)");
            Matcher matcherCaseNumber = patternCaseNumber.matcher(dirName);
            int testCaseNumber = 0;
            if(matcherCaseNumber.find())
                testCaseNumber = Integer.parseInt(matcherCaseNumber.group(1));

            List<File> subDirList = getTestCaseDirList(String.format("%s\\%s", SRC_DIR, dirName));//Get fail1,fail2... directory
            System.out.println(subDirList);
            for (int index2 = 0; index2 < subDirList.size(); index2++) {
                /**
                 * Begin
                 */
                String subDirName = subDirList.get(index2).getName();
                List<File> fileLists = getListFiles(subDirList.get(index2));
                String destDir = String.format("%s\\%s\\%s",DEST_DIR,dirName,subDirName);

                //Create the output directory
                File outputDir = new File(destDir);
                if(!outputDir.exists())
                    outputDir.mkdirs();

                for (int x = 0; x < fileLists.size(); x++) {
                    File file = fileLists.get(x);
                    String path = file.getPath();

                    String microserviceName = path.substring(path.lastIndexOf("/") + 1, path.lastIndexOf("."));

                    String traceStr = readFile(path);

                    JSONArray tracelist = new JSONArray(traceStr);

                    List<HashMap<String, String>> logs = new ArrayList<HashMap<String, String>>();

                    HashMap<String, String> states = new HashMap<String, String>();


                    JSONArray traceobj = tracelist;

                    List<HashMap<String, String>> serviceList = new ArrayList<HashMap<String, String>>();
                    String traceId = ((JSONObject) traceobj.get(0)).getString("traceId");

                    for (int j = 0; j < traceobj.length(); j++) {
                        JSONObject spanobj = (JSONObject) traceobj.get(j);

                        String id = spanobj.getString("id");
                        String pid = "";
                        if (spanobj.has("parentId")) {
                            pid = spanobj.getString("parentId");
                        }
                        String name = spanobj.getString("name");
                        String time = String.valueOf(spanobj.getLong("timestamp"));

                        HashMap<String, String> content = new HashMap<String, String>();
                        content.put("traceId", traceId);
                        content.put("spanid", id);
                        content.put("parentid", pid);
                        content.put("spanname", name);

                        //annotation
                        if (spanobj.has("annotations")) {
                            JSONArray annotations = spanobj.getJSONArray("annotations");
                            for (int i = 0; i < annotations.length(); i++) {
                                JSONObject anno = annotations.getJSONObject(i);
                                if ("cs".equals(anno.getString("value"))) {
                                    JSONObject endpoint = anno.getJSONObject("endpoint");
                                    String service = endpoint.getString("serviceName");
                                    content.put("clientName", service);
                                    String csTime = String.valueOf(anno.getLong("timestamp"));
                                    content.put("csTime", csTime);
                                }
                                if ("sr".equals(anno.getString("value"))) {
                                    JSONObject endpoint = anno.getJSONObject("endpoint");
                                    String service = endpoint.getString("serviceName");
                                    content.put("serverName", service);
                                    String srTime = String.valueOf(anno.getLong("timestamp"));
                                    content.put("srTime", srTime);
                                }
                                if ("ss".equals(anno.getString("value"))) {
                                    JSONObject endpoint = anno.getJSONObject("endpoint");
                                    String service = endpoint.getString("serviceName");
                                    content.put("serverName", service);
                                    String ssTime = String.valueOf(anno.getLong("timestamp"));
                                    content.put("ssTime", ssTime);
                                }
                                if ("cr".equals(anno.getString("value"))) {
                                    JSONObject endpoint = anno.getJSONObject("endpoint");
                                    String service = endpoint.getString("serviceName");
                                    content.put("clientName", service);
                                    String crTime = String.valueOf(anno.getLong("timestamp"));
                                    content.put("crTime", crTime);
                                }
                            }
                        }

                        //if annotation doesn't exist
                        if (!spanobj.has("annotations")) {
                            content.put("time", time);
                        }

                        JSONArray binaryAnnotations = spanobj.getJSONArray("binaryAnnotations");
                        for (int i = 0; i < binaryAnnotations.length(); i++) {
                            JSONObject anno = binaryAnnotations.getJSONObject(i);
                            if ("error".equals(anno.getString("key"))) {
                                content.put("error", anno.getString("value"));
                            }
                            if ("mvc.controller.class".equals(anno.getString("key"))
                                    && !"BasicErrorController".equals(anno.getString("value"))) {
                                String classname = anno.getString("value");
                                content.put("classname", classname);
                            }
                            if ("mvc.controller.method".equals(anno.getString("key"))
                                    && !"errorHtml".equals(anno.getString("value"))) {
                                String methodname = anno.getString("value");
                                content.put("methodname", methodname);
                            }
                            if ("spring.instance_id".equals(anno.getString("key"))) {
                                String instance_id = anno.getString("value");
                                JSONObject endpoint = anno.getJSONObject("endpoint");
                                String ipv4 = endpoint.getString("ipv4");

                                if (content.get("serverName") != null && instance_id.indexOf(content.get("serverName")) != -1) {
                                    String key = content.get("serverName") + ":" + ipv4;
                                    String new_instance_id;
                                    if (states.containsKey(key)) {
                                        new_instance_id = content.get("serverName") + ":" + states.get(key);
                                    } else {
                                        new_instance_id = content.get("serverName");
                                    }

                                    content.put("server_instance_id", new_instance_id);
                                }
                                if (content.get("clientName") != null && instance_id.indexOf(content.get("clientName")) != -1) {
                                    String key = content.get("clientName") + ":" + ipv4;
                                    String new_instance_id;
                                    if (states.containsKey(key)) {
                                        new_instance_id = content.get("clientName") + ":" + states.get(key);
                                    } else {
                                        new_instance_id = content.get("clientName");
                                    }
                                    content.put("client_instance_id", new_instance_id);
                                }
                            }
                            if ("http.method".equals(anno.getString("key"))) {
                                String httpMethod = anno.getString("value");
                                content.put("httpMethod", httpMethod);
                            }
                            if ("class".equals(anno.getString("key"))) {
                                String c = anno.getString("value");
                                content.put("class", c);
                                JSONObject endpoint = anno.getJSONObject("endpoint");
                                String ipv4 = endpoint.getString("ipv4");
                                String port = String.valueOf(endpoint.get("port"));
                                String serviceName = String.valueOf(endpoint.get("serviceName"));

                                String hostId = serviceName;
                                content.put("hostId", hostId);
                                content.put("serviceName", serviceName);

                            }
                            if ("method".equals(anno.getString("key"))) {
                                String method = anno.getString("value");
                                content.put("method", method);
                                JSONObject endpoint = anno.getJSONObject("endpoint");
                                String ipv4 = endpoint.getString("ipv4");
                                String port = String.valueOf(endpoint.get("port"));
                                String serviceName = String.valueOf(endpoint.get("serviceName"));

                                String hostId = serviceName;
                                content.put("hostId", hostId);
                                content.put("serviceName", serviceName);
                            }
                            if ("controller_state".equals(anno.getString("key"))) {
                                String state = anno.getString("value");
                                JSONObject endpoint = anno.getJSONObject("endpoint");
                                String ipv4 = endpoint.getString("ipv4");
                                String serviceName = String.valueOf(endpoint.get("serviceName"));
                                content.put("state", state);
                                content.put("ipv4State", ipv4);
                                content.put("serviceNameState", serviceName);
                                states.put(serviceName + ":" + ipv4, state);
                            }
                        }

                        if (content.get("serverName") != null && (content.get("classname") != null || content.get("methodname") != null)) {
                            content.put("api",
                                    content.get("serverName") + "." + content.get("classname") + "." + content.get("methodname"));
                        } else if (content.get("hostId") != null && (content.get("class") != null || content.get("method") != null)) {
                            content.put("api",
                                    content.get("hostId") + "." + content.get("class") + "." + content.get("method"));
                        }
                        if (name.contains("message:")) {
                            if (content.get("serverName") != null) {
                                if ("message:input".equals(name)) {
                                    content.put("api", content.get("serverName") + "." + "message_received");
                                } else if ("message:output".equals(name)) {
                                    content.put("api", content.get("serverName") + "." + "message_send");
                                }
                            } else if (content.get("clientName") != null) {
                                if ("message:input".equals(name)) {
                                    content.put("api", content.get("clientName") + "." + "message_received");
                                } else if ("message:output".equals(name)) {
                                    content.put("api", content.get("clientName") + "." + "message_send");
                                }
                            }
                        }

                        serviceList.add(content);
                    }

                    serviceList.forEach(n -> {

                        if (n.get("csTime") != null) {
                            HashMap<String, String> log = new HashMap<String, String>();
                            log.put("traceId", n.get("traceId"));
                            log.put("spanId", n.get("spanid"));
                            log.put("parentId", n.get("parentid"));
                            log.put("timestamp", n.get("csTime"));
                            log.put("hostName", n.get("clientName"));
                            log.put("host", n.get("client_instance_id"));
                            log.put("destName", n.get("serverName"));
                            log.put("dest", n.get("server_instance_id"));
                            log.put("api", n.get("api"));
                            log.put("spanname", n.get("spanname"));

                            if (n.get("spanname").contains("message:")) {
                                log.put("event", n.get("api"));
                                log.put("queue", "queue");
                            } else {
                                log.put("event", "");
                            }

                            log.put("type", "cs");
                            if (null != n.get("api")) {
                                log.put("api", n.get("api"));
                            }
                            if (n.containsKey("error")) {
                                log.put("error", n.get("error"));
                            }
                            logs.add(log);
                        }
                        if (n.get("srTime") != null) {
                            HashMap<String, String> log = new HashMap<String, String>();
                            log.put("traceId", n.get("traceId"));
                            log.put("spanId", n.get("spanid"));
                            log.put("parentId", n.get("parentid"));
                            log.put("timestamp", n.get("srTime"));
                            log.put("hostName", n.get("serverName"));
                            log.put("host", n.get("server_instance_id"));
                            log.put("srcName", n.get("clientName"));
                            log.put("src", n.get("client_instance_id"));
                            log.put("api", n.get("api"));
                            log.put("spanname", n.get("spanname"));
                            log.put("event", n.get("api"));
                            log.put("type", "sr");
                            if (n.containsKey("error")) {
                                log.put("error", n.get("error"));
                            }
                            if (n.get("spanname").contains("message:")) {
                                log.put("queue", "queue");
                            }
                            logs.add(log);
                        }
                        if (n.get("ssTime") != null) {
                            HashMap<String, String> log = new HashMap<String, String>();
                            log.put("traceId", n.get("traceId"));
                            log.put("spanId", n.get("spanid"));
                            log.put("parentId", n.get("parentid"));
                            log.put("timestamp", n.get("ssTime"));
                            log.put("hostName", n.get("serverName"));
                            log.put("host", n.get("server_instance_id"));
                            log.put("destName", n.get("clientName"));
                            log.put("dest", n.get("client_instance_id"));
                            log.put("api", n.get("api"));
                            log.put("spanname", n.get("spanname"));

                            log.put("event", n.get("api"));
                            log.put("type", "ss");
                            if (n.containsKey("error")) {
                                log.put("error", n.get("error"));
                            }
                            if (n.get("spanname").contains("message:")) {
                                log.put("queue", "queue");
                            }
                            logs.add(log);
                        }
                        if (n.get("crTime") != null) {
                            HashMap<String, String> log = new HashMap<String, String>();
                            log.put("traceId", n.get("traceId"));
                            log.put("spanId", n.get("spanid"));
                            log.put("parentId", n.get("parentid"));
                            log.put("timestamp", n.get("crTime"));
                            log.put("hostName", n.get("clientName"));
                            log.put("host", n.get("client_instance_id"));
                            log.put("srcName", n.get("serverName"));
                            log.put("src", n.get("server_instance_id"));
                            log.put("api", n.get("api"));
                            log.put("spanname", n.get("spanname"));

                            if (n.get("spanname").contains("message:")) {
                                log.put("event", n.get("api"));
                                log.put("queue", "queue");

                            } else {
                                log.put("event", "");
                            }

                            log.put("type", "cr");
                            if (n.containsKey("error")) {
                                log.put("error", n.get("error"));
                            }
                            logs.add(log);
                        }
                        if (n.get("time") != null) {
                            HashMap<String, String> log = new HashMap<String, String>();
                            log.put("traceId", n.get("traceId"));
                            log.put("spanId", n.get("spanid"));
                            log.put("parentId", n.get("parentid"));
                            log.put("timestamp", n.get("time"));
                            log.put("hostName", n.get("serviceName"));
                            log.put("host", n.get("hostId"));
                            log.put("api", n.get("api"));
                            log.put("spanname", n.get("spanname"));
                            log.put("event", n.get("api"));
                            log.put("type", "async");
                            if (n.containsKey("error")) {
                                log.put("error", n.get("error"));
                            }
                            if (n.get("spanname").contains("message:")) {
                                log.put("queue", "queue");
                            }
                            logs.add(log);
                        }

                    });

                    HashMap<String, String> traceIds = new HashMap<String, String>();
                    logs.forEach(n -> {
                        if (!traceIds.containsKey(n.get("traceId"))) {
                            traceIds.put(n.get("traceId"), "");
                        }
                    });

                    List<List<HashMap<String, String>>> list = new ArrayList<List<HashMap<String, String>>>();
                    HashMap<List<HashMap<String, String>>, Boolean> failures = new HashMap<List<HashMap<String, String>>, Boolean>();
                    traceIds.forEach((n, s) -> {
                        List l = logs.stream().filter(elem -> {
                            return n.equals(elem.get("traceId"));
                        }).collect(Collectors.toList());
                        List<HashMap<String, String>> listWithClock = clock2(l);

                        boolean failed = listWithClock.stream().anyMatch(pl -> pl.containsKey("error"));
                        failures.put(listWithClock, failed);
                        list.add(listWithClock);
                    });

                    List<List<HashMap<String, String>>> listSorted = sortListByTime(list);
                    listSorted.forEach(n -> {
                        System.out.println("event number:" + n.size());
                    });

                    String fileName = getFileName(file.getName());

                    writeFile(String.format("%s\\shiviz-%s.txt",destDir,fileName), listSorted, subDirName, microserviceName, testCaseNumber);
                }

                /**
                 * End
                 */

            }
        }

    }

    private static String getFileName(String origin) {
        String name;
        String prefix = origin.substring(origin.lastIndexOf("."));
        int num = prefix.length();//得到后缀名长度
        name = origin.substring(0, origin.length() - num);
        return name;
    }

    //Get all the test case directory
    private static ArrayList<File> getTestCaseDirList(String path) {
        ArrayList<File> testDirs = new ArrayList<File>();
        File rootDir = new File(path);
        File[] dirList = rootDir.listFiles();
        for (int i = 0; i < dirList.length; i++) {
            File file = dirList[i];
            if (file.isDirectory())
                testDirs.add(file);
        }
        return testDirs;
    }

    private static ArrayList<File> getListFiles(Object obj) {
        File directory = null;
        if (obj instanceof File) {
            directory = (File) obj;
        } else {
            directory = new File(obj.toString());
        }
        ArrayList<File> files = new ArrayList<File>();
        if (directory.isFile()) {
            files.add(directory);
            return files;
        } else if (directory.isDirectory()) {
            File[] fileArr = directory.listFiles();
            for (int i = 0; i < fileArr.length; i++) {
                File fileOne = fileArr[i];
                if (fileOne.getName().endsWith(".json")) {
                    files.addAll(getListFiles(fileOne));
                }
            }
        }
        return files;
    }

    private static List<List<HashMap<String, String>>> sortListByTime(List<List<HashMap<String, String>>> list) {
        List<List<HashMap<String, String>>> result = new ArrayList<List<HashMap<String, String>>>();
        Iterator<List<HashMap<String, String>>> iterator = list.iterator();
        List<HashMap<String, String>> logs;
        HashMap<String, String> log;
        HashMap<String, String> times = new HashMap<String, String>();
        HashMap<String, List<HashMap<String, String>>> traceIdAndList = new HashMap<String, List<HashMap<String, String>>>();

        while (iterator.hasNext()) {
            logs = iterator.next();

            log = logs.get(0);
            String traceId = log.get("traceId");
            traceIdAndList.put(traceId, logs);
            for (HashMap<String, String> stringStringHashMap : logs) {
                if (stringStringHashMap.get("spanId").equals(traceId)) {
                    times.put(stringStringHashMap.get("timestamp"), traceId);
                    break;
                }
            }

//            if(!times.containsKey(traceId)){
//                for (HashMap<String, String> stringStringHashMap : logs) {
//                    if(stringStringHashMap.get("parentId").equals(traceId)){
//                        times.put(stringStringHashMap.get("timestamp"), traceId);
//                        break;
//                    }
//                }
//            }
        }

        Long[] timestamps = new Long[times.size()];
        Iterator<String> iterator1 = times.keySet().iterator();
        for (int i = 0; i < timestamps.length; i++) {
            timestamps[i] = Long.valueOf(iterator1.next());
        }
        Arrays.sort(timestamps);

        for (int i = 0; i < timestamps.length; i++) {
            String traceId1 = times.get(String.valueOf(timestamps[i]));
            result.add(traceIdAndList.get(traceId1));
        }

        return result;
    }


    public static HashMap<String, Integer> findSrcClock(List<Clock> allClocks, String traceId, String spanId, String type, String queue, String parentId) {
        HashMap<String, Integer> clock = null;
        Clock item;

        for (int i = allClocks.size() - 1; i >= 0; i--) {
            item = allClocks.get(i);
            if (item.isSrc(traceId, spanId, type, queue, parentId)) {
                clock = item.getClock();
                break;
            }
        }

        if (clock == null) {
            System.out.println();
        }

        return (HashMap<String, Integer>) clock.clone();
    }


    //sort the log for one trace according to the calling sequences
    public static List<HashMap<String, String>> sortLog(List<HashMap<String, String>> logs) {
//        List<HashMap<String,String>> list = logs.stream().sorted((log1,log2) -> {
//            Long time1 = Long.valueOf(log1.get("timestamp"));
//            Long time2 = Long.valueOf(log2.get("timestamp"));
//            return time1.compareTo(time2);
//        }).collect(Collectors.toList());
        List<HashMap<String, String>> list = null;

        HashMap<String, String> log = logs.get(0);
        String traceId = log.get("traceId");

        HashMap<String, Span> spans = new HashMap<String, Span>();
        HashMap<String, List<String>> spanRelation = new HashMap<String, List<String>>();
        logs.forEach(n -> {
            String spanId = n.get("spanId");
            if (spans.containsKey(spanId)) {
                Span span = spans.get(spanId);
                span.addLog(n);
            } else {
                Span span = new Span(n.get("traceId"), n.get("spanId"), n.get("parentId"), n.get("spanname"));
                span.addLog(n);
                spans.put(spanId, span);
            }

            if (spanRelation.containsKey(n.get("parentId"))) {
                List<String> childs = spanRelation.get(n.get("parentId"));
                if (!childs.contains(spanId)) {
                    childs.add(spanId);
                }
            } else {
                List<String> childs = new ArrayList<String>();
                childs.add(spanId);
                spanRelation.put(n.get("parentId"), childs);
            }
        });

        //add the event for cs & cr
        HashMap<String, String> apis = new HashMap<String, String>();
        logs.forEach(n -> {
            String api = n.get("api");
            apis.put(n.get("spanId"), n.get("api"));
        });
        logs.forEach(n -> {
            if ("cs".equals(n.get("type")) || "cr".equals(n.get("type"))) {
                if ("".equals(n.get("event"))) {
                    n.put("event", apis.get(n.get("parentId")));
                }
            } else if ("sr".equals(n.get("type")) || "ss".equals(n.get("type"))) {
                n.put("event", n.get("api"));
            } else if ("async".equals(n.get("type"))) {
                n.put("event", n.get("api"));
            }
            n.remove("api");
        });

        List<HashMap<String, String>> forwardLogs = new ArrayList<HashMap<String, String>>();
        List<HashMap<String, String>> backwardLogs = new ArrayList<HashMap<String, String>>();
        List<Span> sortedSpan = new ArrayList<Span>();

        Span entrance = spans.get(traceId);

        if (entrance == null) {
            Iterator<Map.Entry<String, Span>> entries = spans.entrySet().iterator();
            while (entries.hasNext()) {
                Map.Entry<String, Span> entry = entries.next();
                Span span = entry.getValue();
                if (traceId.equals(span.getParentId())) {
                    entrance = span;
                    break;
                }
            }
        }

        setChilds(spanRelation, entrance, spans);

        traverse(entrance, forwardLogs, backwardLogs, spans);

        forwardLogs = mergeForwardAndBackwardLogs(forwardLogs, backwardLogs);

        forwardLogs.forEach(n -> {
            n.remove("spanname");
        });

        return forwardLogs;
    }

    public static void setChilds(HashMap<String, List<String>> spanRelation, Span entrance, HashMap<String, Span> spans) {
        Span s = entrance;

        //Queue,add the src and srcName for queue receive(sr),dest& destName for queue send(cs)
        if ("message:input".equals(s.getSpanname())) {
            Span parent = spans.get(s.getParentId());
            HashMap<String, String> parentCs = null;
            HashMap<String, String> sr = null;

            Iterator<HashMap<String, String>> parentIterator = parent.getLogs().iterator();
            while (parentIterator.hasNext()) {
                HashMap<String, String> log = parentIterator.next();
                if ("cs".equals(log.get("type"))) {
                    parentCs = log;
                    break;
                }
            }

            Iterator<HashMap<String, String>> sIterator = s.getLogs().iterator();
            while (sIterator.hasNext()) {
                HashMap<String, String> log = sIterator.next();
                if ("sr".equals(log.get("type"))) {
                    sr = log;
                    break;
                }
            }

            if (sr != null && parentCs != null) {
                sr.put("src", parentCs.get("host"));
                sr.put("srcName", parentCs.get("hostName"));
                parentCs.put("dest", sr.get("host"));
                parentCs.put("destName", sr.get("hostName"));
            } else {
                System.out.println(sr);
                System.out.println(parentCs);
            }

        }

        if (spanRelation.containsKey(s.getSpanId())) {
            s.setChilds(spanRelation.get(s.getSpanId()));

            Iterator<String> iterator = s.getChilds().iterator();
            while (iterator.hasNext()) {
                String childId = iterator.next();
                s = spans.get(childId);
                setChilds(spanRelation, s, spans);
            }
        }
    }

    public static void traverse(Span entrance, List<HashMap<String, String>> forwardLogs, List<HashMap<String, String>> backwardLogs, HashMap<String, Span> spans) {
        //from the entrance to end
        Span s = entrance;

        HashMap<String, String> cs = null;
        HashMap<String, String> sr = null;
        HashMap<String, String> ss = null;
        HashMap<String, String> cr = null;
        HashMap<String, String> async = null;

        Iterator<HashMap<String, String>> iterator = s.getLogs().iterator();
        while (iterator.hasNext()) {
            HashMap<String, String> log1 = iterator.next();
            if ("cs".equals(log1.get("type"))) {
                cs = log1;
            }
            if ("sr".equals(log1.get("type"))) {
                sr = log1;
            }
            if ("ss".equals(log1.get("type"))) {
                ss = log1;
            }
            if ("cr".equals(log1.get("type"))) {
                cr = log1;
            }
            if ("async".equals(log1.get("type"))) {
                async = log1;
            }
        }

        if (cs != null) {
            forwardLogs.add(cs);
        }
        if (sr != null) {
            forwardLogs.add(sr);
        }
        if (async != null) {
            forwardLogs.add(async);
        }
        if (cr != null) {
            backwardLogs.add(cr);
        }
        if (ss != null) {
            backwardLogs.add(ss);
        }


        if (s.getChilds() != null) {
            List<String> sortedChilds = s.getChilds().stream().sorted((spanId1, spanId2) -> {
                Span span1 = spans.get(spanId1);
                Span span2 = spans.get(spanId2);

                HashMap<String, String> sr1 = null;
                HashMap<String, String> sr2 = null;

                Iterator<HashMap<String, String>> ite1 = span1.getLogs().iterator();
                while (ite1.hasNext()) {
                    HashMap<String, String> log1 = ite1.next();
                    if ("cs".equals(log1.get("type"))) {
                        sr1 = log1;
                    } else if ("sr".equals(log1.get("type"))) {
                        sr1 = log1;
                    } else if ("async".equals(log1.get("type"))) {
                        sr1 = log1;
                    }
                }

                Iterator<HashMap<String, String>> ite2 = span2.getLogs().iterator();
                while (ite2.hasNext()) {
                    HashMap<String, String> log2 = ite2.next();
                    if ("cs".equals(log2.get("type"))) {
                        sr2 = log2;
                    } else if ("sr".equals(log2.get("type"))) {
                        sr2 = log2;
                    } else if ("async".equals(log2.get("type"))) {
                        sr2 = log2;
                    }
                }

//                System.out.println("sr1:"+sr1.get("timestamp"));
//                System.out.println("sr2:"+sr2.get("timestamp"));
                Long time1 = Long.valueOf(sr1.get("timestamp"));
                Long time2 = Long.valueOf(sr2.get("timestamp"));
                return time1.compareTo(time2);
            }).collect(Collectors.toList());

//            Iterator<String> iterator1 = sortedChilds.iterator();
//            List<HashMap<String,String>> childsLogs = new ArrayList<HashMap<String,String>>();
//
//            while(iterator1.hasNext()){
//                List<HashMap<String,String>> childForwardLogs = new ArrayList<HashMap<String,String>>();
//                List<HashMap<String,String>> childBackwardLogs = new ArrayList<HashMap<String,String>>();
//                String childId = iterator1.next();
//                traverse(spans.get(childId), childForwardLogs, childBackwardLogs, spans);
//                childsLogs.addAll(mergeForwardAndBackwardLogs(childForwardLogs,childBackwardLogs));
//            }
//            forwardLogs.addAll(childsLogs);
            Iterator<String> iterator1 = sortedChilds.iterator();
            List<List<HashMap<String, String>>> childLogLists = new ArrayList<List<HashMap<String, String>>>();

            while (iterator1.hasNext()) {
                List<HashMap<String, String>> childForwardLogs = new ArrayList<HashMap<String, String>>();
                List<HashMap<String, String>> childBackwardLogs = new ArrayList<HashMap<String, String>>();
                String childId = iterator1.next();
                traverse(spans.get(childId), childForwardLogs, childBackwardLogs, spans);
                childLogLists.add(mergeForwardAndBackwardLogs(childForwardLogs, childBackwardLogs));
            }

            List<HashMap<String, String>> childsLogs = mergeChildLogLists(childLogLists);

            forwardLogs.addAll(childsLogs);
        }


    }

    private static List<HashMap<String, String>> mergeChildLogLists(List<List<HashMap<String, String>>> childLogLists) {
        List<HashMap<String, String>> childsLogs = new ArrayList<HashMap<String, String>>();
        List<HashMap<String, String>> logs;
        List<HashMap<String, String>> childLogList;
        HashMap<String, String> earlist;

        while (!childLogLists.isEmpty()) {
            logs = new ArrayList<HashMap<String, String>>();

            for (int i = 0, size = childLogLists.size(); i < size; i++) {
                childLogList = childLogLists.get(i);
                if (!childLogList.isEmpty()) {
                    logs.add(childLogList.get(0));
                }
            }

            earlist = findEarliest(logs, childLogLists);
            childsLogs.add(earlist);

            for (int i = 0, length = logs.size(); i < length; i++) {
                if (earlist == logs.get(i)) {
                    childLogList = childLogLists.get(i);
                    childLogList.remove(0);
                    if (childLogList.isEmpty()) {
                        childLogLists.remove(childLogList);
                    }
                }
            }
        }

        return childsLogs;
    }

    private static HashMap<String, String> findEarliest(List<HashMap<String, String>> logs, List<List<HashMap<String, String>>> logLists) {

        HashMap<String, String> earlist = logs.get(0);
        List<HashMap<String, String>> logListEarlist = logLists.get(0);

        Iterator<HashMap<String, String>> iterator1 = logs.iterator();
        Iterator<List<HashMap<String, String>>> iterator2 = logLists.iterator();
        while (iterator1.hasNext() && iterator2.hasNext()) {
            HashMap<String, String> log = iterator1.next();
            List<HashMap<String, String>> logList = iterator2.next();
            if (compareLog(log, earlist, logList, logListEarlist)) {
                earlist = log;
                logListEarlist = logList;
            }
        }

        return earlist;
    }

    /*   log1 happens before log2 return true;
         log2 happens before log1 return false;
     */
    private static boolean compareLog(HashMap<String, String> log1, HashMap<String, String> log2, List<HashMap<String, String>> logs1, List<HashMap<String, String>> logs2) {
        long timestamp1 = Long.valueOf(log1.get("timestamp"));
        long timestamp2 = Long.valueOf(log2.get("timestamp"));
        String host1 = log1.get("host");
        String host2 = log2.get("host");

        if (host1.equals(host2)) {
            if (timestamp1 <= timestamp2) {
                return true;
            } else {
                return false;
            }
        } else {
            Iterator<HashMap<String, String>> iterator1 = logs1.iterator();
            Iterator<HashMap<String, String>> iterator2 = logs2.iterator();
            HashMap<String, String> log3 = null;
            HashMap<String, String> log4 = null;

            //log1 before log3, log3 before log2, then log1 before log2
            while (iterator1.hasNext()) {
                log3 = iterator1.next();
                if (host2.equals(log3.get("host"))) {
                    break;
                }
            }

            if (log3 != null) {
                long timestamp = Long.valueOf(log3.get("timestamp"));
                if (timestamp <= timestamp2) {
                    return true;
                }
            }

            //log2 before log4, log4 before log1, then log2 before log1
            while (iterator2.hasNext()) {
                log4 = iterator2.next();
                if (host1.equals(log4.get("host"))) {
                    break;
                }
            }

            if (log4 != null) {
                long timestamp = Long.valueOf(log4.get("timestamp"));
                if (timestamp <= timestamp1) {
                    return false;
                }
            }

            //still can't compare, then just compare timestamp, maybe wrong
            //but 1->2 or 2->1 both are meaningful
            if (timestamp1 <= timestamp2) {
                return true;
            } else {
                return false;
            }
        }
    }


    public static List<HashMap<String, String>> mergeForwardAndBackwardLogs(List<HashMap<String, String>> forwardLogs, List<HashMap<String, String>> backwardLogs) {
        Stack<HashMap<String, String>> stack = new Stack<HashMap<String, String>>();
        backwardLogs.forEach(n -> {
            stack.push(n);
        });

        while (!stack.isEmpty()) {
            forwardLogs.add(stack.pop());
        }

        return forwardLogs;
    }

    public static List<HashMap<String, String>> clock2(List<HashMap<String, String>> logs) {
        HashMap<String, HashMap<String, Integer>> clocks = new HashMap<String, HashMap<String, Integer>>();
        List<Clock> allClocks = new ArrayList<Clock>();

        List<HashMap<String, String>> list = sortLog(logs);

        list.forEach(n -> {
            if (clocks.containsKey(n.get("host"))) {
                HashMap<String, Integer> clock = clocks.get(n.get("host"));

                if (n.get("src") != null) {
                    HashMap<String, Integer> srcClock = findSrcClock(allClocks, n.get("traceId"), n.get("spanId"), n.get("type"), n.get("queue"), n.get("parentId"));

                    Iterator<Map.Entry<String, Integer>> iterator = srcClock.entrySet().iterator();
                    while (iterator.hasNext()) {
                        Map.Entry<String, Integer> entry = iterator.next();
                        if (clock.get(entry.getKey()) != null) {
                            if (entry.getValue() <= clock.get(entry.getKey())) {
                                //don't change clock
                            } else {  //update clock
                                clock.put(entry.getKey(), entry.getValue());
                            }
                        } else {   //update clock
                            clock.put(entry.getKey(), entry.getValue());
                        }
                    }

                    clock.put(n.get("host"), clock.get(n.get("host")) + 1);

                } else {
                    clock.put(n.get("host"), clock.get(n.get("host")) + 1);
                }
                n.put("clock", clock.toString());

                clocks.put(n.get("host"), clock);
                allClocks.add(new Clock(n.get("type"), n.get("host"), n.get("src"), n.get("traceId"), n.get("spanId"), n.get("parentId"), (HashMap<String, Integer>) clock.clone()));
            } else {
                HashMap<String, Integer> clock = new HashMap<String, Integer>();

                if (n.get("src") != null) {
                    HashMap<String, Integer> srcClock = findSrcClock(allClocks, n.get("traceId"), n.get("spanId"), n.get("type"), n.get("queue"), n.get("parentId"));

                    Iterator<Map.Entry<String, Integer>> iterator = srcClock.entrySet().iterator();
                    while (iterator.hasNext()) {
                        Map.Entry<String, Integer> entry = iterator.next();
                        if (clock.get(entry.getKey()) != null) {
                            if (entry.getValue() <= clock.get(entry.getKey())) {
                                //don't change clock
                            } else {  //update clock
                                clock.put(entry.getKey(), entry.getValue());
                            }
                        } else {   //update clock
                            clock.put(entry.getKey(), entry.getValue());
                        }
                    }
                    clock.put(n.get("host"), 1);
                } else {
                    clock.put(n.get("host"), 1);
                }
                n.put("clock", clock.toString());

                clocks.put(n.get("host"), clock);
                allClocks.add(new Clock(n.get("type"), n.get("host"), n.get("src"), n.get("traceId"), n.get("spanId"), n.get("parentId"), (HashMap<String, Integer>) clock.clone()));
            }
        });

        list.forEach(n -> {
            if (n.containsKey("queue")) {
                n.remove("queue");
            }
        });

        return list;
    }

    public static List<HashMap<String, String>> clock(List<HashMap<String, String>> logs) {
        HashMap<String, HashMap<String, Integer>> clocks = new HashMap<String, HashMap<String, Integer>>();

        List<HashMap<String, String>> list = logs.stream().sorted((log1, log2) -> {
            Long time1 = Long.valueOf(log1.get("timestamp"));
            Long time2 = Long.valueOf(log2.get("timestamp"));
            return time1.compareTo(time2);
        }).collect(Collectors.toList());

        list.forEach(n -> {
            if (clocks.containsKey(n.get("host"))) {
                HashMap<String, Integer> clock = clocks.get(n.get("host"));

                if (n.get("src") != null) {
                    HashMap<String, Integer> srcClock = (HashMap<String, Integer>) clocks.get(n.get("src")).clone();

                    Iterator<Map.Entry<String, Integer>> iterator = srcClock.entrySet().iterator();
                    while (iterator.hasNext()) {
                        Map.Entry<String, Integer> entry = iterator.next();
                        if (clock.get(entry.getKey()) != null) {
                            if (entry.getValue() <= clock.get(entry.getKey())) {
                                //don't change clock
                            } else {  //update clock
                                clock.put(entry.getKey(), entry.getValue());
                            }
                        } else {   //update clock
                            clock.put(entry.getKey(), entry.getValue());
                        }
                    }

                    clock.put(n.get("host"), clock.get(n.get("host")) + 1);

                } else {
                    clock.put(n.get("host"), clock.get(n.get("host")) + 1);
                }
                n.put("clock", clock.toString());
                clocks.put(n.get("host"), clock);
            } else {
                HashMap<String, Integer> clock = new HashMap<String, Integer>();

                if (n.get("src") != null) {
                    HashMap<String, Integer> srcClock = (HashMap<String, Integer>) clocks.get(n.get("src")).clone();

                    Iterator<Map.Entry<String, Integer>> iterator = srcClock.entrySet().iterator();
                    while (iterator.hasNext()) {
                        Map.Entry<String, Integer> entry = iterator.next();
                        if (clock.get(entry.getKey()) != null) {
                            if (entry.getValue() <= clock.get(entry.getKey())) {
                                //don't change clock
                            } else {  //update clock
                                clock.put(entry.getKey(), entry.getValue());
                            }
                        } else {   //update clock
                            clock.put(entry.getKey(), entry.getValue());
                        }
                    }
                    clock.put(n.get("host"), 1);
                } else {
                    clock.put(n.get("host"), 1);
                }
                n.put("clock", clock.toString());
                clocks.put(n.get("host"), clock);
            }
        });

        return list;
    }


    public static String readFile(String path) {
        File file = new File(path);
        BufferedReader reader = null;
        String laststr = "";
        try {
            reader = new BufferedReader(new FileReader(file));
            String tempString = null;
            while ((tempString = reader.readLine()) != null) {
                laststr = laststr + tempString;
//                System.out.println("reading");
            }
            reader.close();
        } catch (IOException e) {
            e.printStackTrace();
        } finally {
            if (reader != null) {
                try {
                    reader.close();
                } catch (IOException e1) {
                }
            }
        }
        return laststr;
    }

    public static boolean write(String path, List<HashMap<String, String>> logs) {
        File writer = new File(path);
        BufferedWriter out = null;
        try {
            writer.createNewFile(); // 鍒涘缓鏂版枃浠?
            out = new BufferedWriter(new FileWriter(writer));
            Iterator<HashMap<String, String>> iterator = logs.iterator();
            while (iterator.hasNext()) {
                HashMap<String, String> map = iterator.next();
                out.write(map.toString() + "\r\n");
            }
        } catch (IOException e) {
            e.printStackTrace();
            return false;
        } finally {
            if (out != null) {
                try {
                    out.flush();
                    out.close();
                } catch (IOException e1) {
                }
            }
        }

        return true;
    }

    public static boolean writeFile(String path, List<List<HashMap<String, String>>> logs, String dirName, String microserviceName, int testCaseNumber) {
        File writer = new File(path);
        System.out.println(dirName);
        BufferedWriter out = null;
        try {
            writer.createNewFile();
            out = new BufferedWriter(new FileWriter(writer));

            boolean failed = true;

            Pattern patternFail = Pattern.compile("fail([0-9]+)");
            Matcher matcherFail = patternFail.matcher(dirName);
            int failExecutionNumber = 0;
            if(matcherFail.find()) {
                failExecutionNumber = Integer.parseInt(matcherFail.group(1));
                failed = true;
            }
            Pattern patternSuccess = Pattern.compile("success");
            Matcher matcherSuccess = patternSuccess.matcher(dirName);
            int successExecutionNumber = 1;
            if(matcherSuccess.find())
                failed = false;

            //截取microserviceName
            Pattern patternCase = Pattern.compile("case");
            Matcher matcherCase = patternCase.matcher(microserviceName);
            if(matcherCase.find()){
                int begin = matcherCase.start();
                microserviceName = microserviceName.substring(begin);
            }
            Iterator<List<HashMap<String, String>>> iterator1 = logs.iterator();
            while (iterator1.hasNext()) {
                List<HashMap<String, String>> list = iterator1.next();

                if (failed) {
                    out.write("\r\n=== " + "TestCase" + testCaseNumber + " " + microserviceName + " Fail execution " + failExecutionNumber + " ===\r\n");
                } else {
                    out.write("\r\n=== " + "TestCase" + testCaseNumber + " " + microserviceName + " Success execution " + successExecutionNumber + " ===\r\n");
                }

                Iterator<HashMap<String, String>> iterator = list.iterator();
                while (iterator.hasNext()) {
                    HashMap<String, String> map = iterator.next();
                    out.write("{");


                    if (map.containsKey("traceId")) {
                        out.write("traceId=" + map.get("traceId") + ", ");
                    }
                    if (map.containsKey("spanId")) {
                        out.write("spanId=" + map.get("spanId") + ", ");
                    }
                    if (map.containsKey("hostName")) {
                        out.write("hostName=" + map.get("hostName") + ", ");
                    }
                    if (map.containsKey("srcName")) {
                        out.write("srcName=" + map.get("srcName") + ", ");
                    }
                    if (map.containsKey("destName")) {
                        out.write("destName=" + map.get("destName") + ", ");
                    }
                    if (map.containsKey("src")) {
                        out.write("src=" + map.get("src") + ", ");
                    }
                    if (map.containsKey("host")) {
                        out.write("host=" + map.get("host") + ", ");
                    }
                    if (map.containsKey("api")) {
                        out.write("api=" + map.get("api") + ", ");
                    }
                    if (map.containsKey("clock")) {
                        String clocks = map.get("clock");
                        String[] c = clocks.split(",");
                        out.write("clock={");
                        for (int i = 0, length = c.length; i < length; i++) {
                            c[i] = "\"" + c[i].substring(1, c[i].lastIndexOf("=")) + "\":"
                                    + c[i].substring(c[i].lastIndexOf("=") + 1);
                            if (i < length - 1) {
                                out.write(c[i] + ",");
                            } else {
                                out.write(c[i]);
                            }

                        }
                        out.write(", ");
                    }
                    if (map.containsKey("dest")) {
                        out.write("dest=" + map.get("dest") + ", ");
                    }
                    if (map.containsKey("event")) {
                        out.write("event=" + map.get("event") + ", ");
                    }
                    if (map.containsKey("type")) {
                        out.write("type=" + map.get("type") + ", ");
                    }
                    if (map.containsKey("error")) {
                        out.write("error=" + map.get("error") + ", ");
                    }
                    if (map.containsKey("parentId")) {
                        out.write("parentId=" + map.get("parentId") + ", ");
                    }
                    if (map.containsKey("timestamp")) {
                        out.write("timestamp=" + map.get("timestamp") + ", ");
                    }


                    out.write("}\r\n");
                }
            }


        } catch (IOException e) {
            e.printStackTrace();
            return false;
        } finally {
            if (out != null) {
                try {
                    out.flush();
                    out.close();
                } catch (IOException e1) {
                }
            }
        }

        return true;
    }
}


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Json2Shiviz/src/main/java/org/services/analysis/TraceTranslator.java:TraceTranslator.<init>
// Node: case
// Node: exists
// Node: mkdirs
// Node: lastIndexOf
// Node: getLong
// Node: clock2
// Node: sortListByTime
// Node: getFileName
// Node: writeFile
// Node: traverse
// Node: mergeForwardAndBackwardLogs
// Node: mergeChildLogLists
// Node: sort
// Node: findSrcClock
// Node: clone
// Node: sortLog
// Node: receive
// Node: findEarliest
// Node: compareLog
// Node: pop
// Node: clock
// Node: BufferedWriter
// Node: FileWriter
// Node: fail
///**
// * Created by hh on 2017-07-08.
// */
///**
// * Created by Administrator on 2017/7/11.
// */
//package org.services.analysis;
//
//import java.io.*;
//import java.util.*;
//import java.util.stream.Collectors;
//import org.json.JSONArray;
//import org.json.JSONException;
//import org.json.JSONObject;
//import org.services.analysis.Clock;
//import org.services.analysis.Span;
//
///**
// * Created by hh on 2017-07-08.
// */
//public class TraceTranslatorQueue {
//    public static void main(String[] args) throws JSONException {
//
////
//
////        String path = "./sample/trace-error-queue-seq-multi.json";
////        String destPath = "./output/shiviz-error-queue-seq-multi.txt";
//
////        String path = "./ts-sample/ts-error-queue/success.json";
////        String destPath = "./ts-output/error-queue/shiviz-error-queue-success.txt";
//
//        String path = "./ts-sample/ts-external-normal/ts-external-normal.json";
//        String destPath = "./ts-output/ts-external-normal/shiviz-external-normal.txt";
//
//        String traceStr = readFile(path);
//        JSONArray tracelist = new JSONArray(traceStr);
//        List<HashMap<String,String>> logs = new ArrayList<HashMap<String, String>>();
//        HashMap<String,String> states = new HashMap<String,String>();
//
//        for (int k = 0; k < tracelist.length(); k++) {
//
//            JSONArray traceobj = tracelist.getJSONArray(k);
//
//            List<HashMap<String, String>> serviceList = new ArrayList<HashMap<String, String>>();
//            String traceId = ((JSONObject) traceobj.get(0)).getString("traceId");
//
//            for (int j = 0; j < traceobj.length(); j++) {
//                JSONObject spanobj = (JSONObject) traceobj.get(j);
//
//                // String traceId = spanobj.getString("traceId");
//                String id = spanobj.getString("id");
//                String pid = "";
//                if (spanobj.has("parentId")) {
//                    pid = spanobj.getString("parentId");
//                }
//                String name = spanobj.getString("name");
//                String time = String.valueOf(spanobj.getLong("timestamp"));
//
//                HashMap<String, String> content = new HashMap<String, String>();
//                content.put("traceId" , traceId);
//                content.put("spanid", id);
//                content.put("parentid", pid);
//                content.put("spanname", name);
//
//
//
//                //annotation
//                if(spanobj.has("annotations")) {
//                    JSONArray annotations = spanobj.getJSONArray("annotations");
//                    for (int i = 0; i < annotations.length(); i++) {
//                        JSONObject anno = annotations.getJSONObject(i);
//                        if ("cs".equals(anno.getString("value"))) {
//                            JSONObject endpoint = anno.getJSONObject("endpoint");
//                            String service = endpoint.getString("serviceName");
//                            content.put("clientName", service);
//                            String csTime = String.valueOf(anno.getLong("timestamp"));
//                            content.put("csTime", csTime);
//                        }
//                        if ("sr".equals(anno.getString("value"))) {
//                            JSONObject endpoint = anno.getJSONObject("endpoint");
//                            String service = endpoint.getString("serviceName");
//                            content.put("serverName", service);
//                            String srTime = String.valueOf(anno.getLong("timestamp"));
//                            content.put("srTime", srTime);
//                        }
//                        if ("ss".equals(anno.getString("value"))) {
//                            JSONObject endpoint = anno.getJSONObject("endpoint");
//                            String service = endpoint.getString("serviceName");
//                            content.put("serverName", service);
//                            String ssTime = String.valueOf(anno.getLong("timestamp"));
//                            content.put("ssTime", ssTime);
//                        }
//                        if ("cr".equals(anno.getString("value"))) {
//                            JSONObject endpoint = anno.getJSONObject("endpoint");
//                            String service = endpoint.getString("serviceName");
//                            content.put("clientName", service);
//                            String crTime = String.valueOf(anno.getLong("timestamp"));
//                            content.put("crTime", crTime);
//                        }
//                    }
//                }
//
//
//
//                //if annotation doesn't exist
//                if(!spanobj.has("annotations")){
//                    content.put("time",time);
//                }
//
//
//                //binaryAnnotation
////                if (name.contains("message:")) {
////                    if ("message:input".equals(name)) {
////                        content.put("api", content.get("service") + "." + "message_received");
////                    }
////                } else {
//                JSONArray binaryAnnotations = spanobj.getJSONArray("binaryAnnotations");
//                for (int i = 0; i < binaryAnnotations.length(); i++) {
//                    JSONObject anno = binaryAnnotations.getJSONObject(i);
//                    if ("error".equals(anno.getString("key"))) {
//                        content.put("error", anno.getString("value"));
//                    }
//                    if ("mvc.controller.class".equals(anno.getString("key"))
//                            && !"BasicErrorController".equals(anno.getString("value"))) {
//                        String classname = anno.getString("value");
//                        content.put("classname", classname);
//                    }
//                    if ("mvc.controller.method".equals(anno.getString("key"))
//                            && !"errorHtml".equals(anno.getString("value"))) {
//                        String methodname = anno.getString("value");
//                        content.put("methodname", methodname);
//                    }
//                    if ("spring.instance_id".equals(anno.getString("key"))) {
//                        String instance_id = anno.getString("value");
//                        JSONObject endpoint = anno.getJSONObject("endpoint");
//                        String ipv4 = endpoint.getString("ipv4");
////                            String port = String.valueOf(endpoint.get("port"));
//
//                        if(content.get("serverName")!=null && instance_id.indexOf(content.get("serverName")) != -1){
//                            String key = content.get("serverName") + ":" + ipv4;
//                            String new_instance_id;
//                            if(states.containsKey(key)){
//                                new_instance_id = content.get("serverName") + ":" + states.get(key) + ":" + ipv4;
//                            }else{
//                                new_instance_id = content.get("serverName") + ":" + ipv4;
//                            }
//
//                            content.put("server_instance_id", new_instance_id);
//                        }
//                        if(content.get("clientName")!=null  && instance_id.indexOf(content.get("clientName")) != -1){
//                            String key = content.get("clientName") + ":" + ipv4;
//                            String new_instance_id;
//                            if(states.containsKey(key)){
//                                new_instance_id = content.get("clientName") + ":" + states.get(key) + ":" + ipv4;
//                            }else{
////                                    new_instance_id = ipv4 + ":" + content.get("clientName") + ":" + port;
//                                new_instance_id = content.get("clientName") + ":" + ipv4 ;
//                            }
//                            content.put("client_instance_id", new_instance_id);
//                        }
//                    }
//                    if ("http.method".equals(anno.getString("key"))) {
//                        String httpMethod = anno.getString("value");
//                        content.put("httpMethod", httpMethod);
//                    }
//                    if ("class".equals(anno.getString("key"))) {
//                        String c = anno.getString("value");
//                        content.put("class", c);
//                        JSONObject endpoint = anno.getJSONObject("endpoint");
//                        String ipv4 = endpoint.getString("ipv4");
//                        String port = String.valueOf(endpoint.get("port"));
//                        String serviceName = String.valueOf(endpoint.get("serviceName"));
//
//                        String hostId = serviceName + ":" + ipv4 ;
//                        content.put("hostId", hostId);
//                        content.put("serviceName", serviceName);
//
//                    }
//                    if ("method".equals(anno.getString("key"))) {
//                        String method = anno.getString("value");
//                        content.put("method", method);
//                        JSONObject endpoint = anno.getJSONObject("endpoint");
//                        String ipv4 = endpoint.getString("ipv4");
//                        String port = String.valueOf(endpoint.get("port"));
//                        String serviceName = String.valueOf(endpoint.get("serviceName"));
//
//                        String hostId = serviceName + ":" + ipv4 ;
//                        content.put("hostId", hostId);
//                        content.put("serviceName", serviceName);
//                    }
//                    if ("controller_state".equals(anno.getString("key"))) {
//                        String state = anno.getString("value");
//                        JSONObject endpoint = anno.getJSONObject("endpoint");
//                        String ipv4 = endpoint.getString("ipv4");
//                        String serviceName = String.valueOf(endpoint.get("serviceName"));
//                        content.put("state",state);
//                        content.put("ipv4State",ipv4);
//                        content.put("serviceNameState",serviceName);
//                        states.put(serviceName +":" + ipv4, state);
//                    }
//
//
//                }
//
//
//
//                if(content.get("serverName") != null && (content.get("classname") != null || content.get("methodname") != null)){
//                    content.put("api",
//                            content.get("serverName") + "." + content.get("classname") + "." + content.get("methodname"));
//                }else if(content.get("hostId") != null && (content.get("class") != null || content.get("method") != null)){
//                    content.put("api",
//                            content.get("hostId") + "." + content.get("class") + "." + content.get("method"));
//                }
//                if (name.contains("message:")) {
//                    if(content.get("serverName") != null){
//                        if ("message:input".equals(name)) {
//                            content.put("api", content.get("serverName") + "." + "message_received");
//                        }else if("message:output".equals(name)){
//                            content.put("api", content.get("serverName") + "." + "message_received");
//                        }
//                    }else if(content.get("clientName") != null){
//                        if ("message:input".equals(name)) {
//                            content.put("api", content.get("clientName") + "." + "message_send");
//                        }else if("message:output".equals(name)){
//                            content.put("api", content.get("clientName") + "." + "message_send");
//                        }
//                    }
//                }
//
//
//                serviceList.add(content);
//            }
//
//
//            serviceList.forEach(n -> {
//
//                if(n.get("csTime") != null){
//                    HashMap<String,String> log = new HashMap<String,String>();
//                    log.put("traceId" , n.get("traceId"));
//                    log.put("spanId" , n.get("spanid"));
//                    log.put("parentId" , n.get("parentid"));
//                    log.put("timestamp",n.get("csTime"));
//                    log.put("hostName" , n.get("clientName"));
//                    log.put("host" , n.get("client_instance_id"));
//                    log.put("destName" , n.get("serverName"));
//                    log.put("dest" , n.get("server_instance_id"));
//
//                    if(n.get("spanname").contains("message:")){
//                        log.put("event" , n.get("api"));
//                    }else{
//                        log.put("event" , "");
//                    }
//                    if(n.get("spanname").contains("message:")){
//                        log.put("spanname", n.get("spanname"));
//                    }
//
//                    log.put("type", "cs");
//                    if(null != n.get("api")){
//                        log.put("api", n.get("api"));
//                    }
//                    if(n.containsKey("error")){
//                        log.put("error", n.get("error"));
//                    }
//                    logs.add(log);
//                }
//                if(n.get("srTime") != null){
//                    HashMap<String,String> log = new HashMap<String,String>();
//                    log.put("traceId" , n.get("traceId"));
//                    log.put("spanId" , n.get("spanid"));
//                    log.put("parentId" , n.get("parentid"));
//                    log.put("timestamp",n.get("srTime"));
//                    log.put("hostName" , n.get("serverName"));
//                    log.put("host" , n.get("server_instance_id"));
//                    log.put("srcName" , n.get("clientName"));
//                    log.put("src" , n.get("client_instance_id"));
//                    log.put("event", n.get("api"));
//                    log.put("type", "sr");
//                    if(n.containsKey("error")){
//                        log.put("error", n.get("error"));
//                    }
//                    if(n.get("spanname").contains("message:")){
//                        log.put("spanname", n.get("spanname"));
//                    }
//                    logs.add(log);
//                }
//                if(n.get("ssTime") != null){
//                    HashMap<String,String> log = new HashMap<String,String>();
//                    log.put("traceId" , n.get("traceId"));
//                    log.put("spanId" , n.get("spanid"));
//                    log.put("parentId" , n.get("parentid"));
//                    log.put("timestamp",n.get("ssTime"));
//                    log.put("hostName" , n.get("serverName"));
//                    log.put("host" , n.get("server_instance_id"));
//                    log.put("destName" , n.get("clientName"));
//                    log.put("dest" , n.get("client_instance_id"));
//
//                    log.put("event", n.get("api"));
//                    log.put("type", "ss");
//                    if(n.containsKey("error")){
//                        log.put("error", n.get("error"));
//                    }
//                    if(n.get("spanname").contains("message:")){
//                        log.put("spanname", n.get("spanname"));
//                    }
//                    logs.add(log);
//                }
//                if(n.get("crTime") != null){
//                    HashMap<String,String> log = new HashMap<String,String>();
//                    log.put("traceId" , n.get("traceId"));
//                    log.put("spanId" , n.get("spanid"));
//                    log.put("parentId" , n.get("parentid"));
//                    log.put("timestamp",n.get("crTime"));
//                    log.put("hostName" , n.get("clientName"));
//                    log.put("host" , n.get("client_instance_id"));
//                    log.put("srcName" , n.get("serverName"));
//                    log.put("src" , n.get("server_instance_id"));
//
//                    if(n.get("spanname").contains("message:")){
//                        log.put("event" , n.get("api"));
//                    }else{
//                        log.put("event" , "");
//                    }
//                    if(n.get("spanname").contains("message:")){
//                        log.put("spanname", n.get("spanname"));
//                    }
//
//                    log.put("type", "cr");
//                    if(n.containsKey("error")){
//                        log.put("error", n.get("error"));
//                    }
//                    logs.add(log);
//                }
//                if(n.get("time") != null){
//                    HashMap<String,String> log = new HashMap<String,String>();
//                    log.put("traceId" , n.get("traceId"));
//                    log.put("spanId" , n.get("spanid"));
//                    log.put("parentId" , n.get("parentid"));
//                    log.put("timestamp",n.get("time"));
//                    log.put("hostName" , n.get("serviceName"));
//                    log.put("host" , n.get("hostId"));
//                    log.put("event", n.get("api"));
//                    log.put("type", "inside_payment.async");
//                    if(n.containsKey("error")){
//                        log.put("error", n.get("error"));
//                    }
//                    if(n.get("spanname").contains("message:")){
//                        log.put("spanname", n.get("spanname"));
//                    }
//                    logs.add(log);
//                }
//
//
//            });
//
//        }
//
//
//
//        HashMap<String,String> traceIds = new HashMap<String,String>();
//        logs.forEach(n -> {
//            if(!traceIds.containsKey(n.get("traceId"))){
//                traceIds.put(n.get("traceId"),"");
//            }
//        });
//
//        List<List<HashMap<String,String>>> list = new ArrayList<List<HashMap<String,String>>>();
//        HashMap<List<HashMap<String,String>>, Boolean> failures = new HashMap<List<HashMap<String,String>>, Boolean>();
//        traceIds.forEach((n,s) -> {
//            List l = logs.stream().filter(elem -> {
//                return n.equals(elem.get("traceId"));
//            }).collect(Collectors.toList());
//            List<HashMap<String,String>> listWithClock = clock2(l);
//            boolean failed = listWithClock.stream().anyMatch(pl -> pl.containsKey("error"));
//            failures.put(listWithClock,failed);
//            list.add(listWithClock);
//        });
//
//
//        writeFile(destPath, list, failures);
//
//
//
//    }
//
//    public static HashMap<String,Integer> findSrcClock(List<Clock> allClocks, String traceId, String spanId, String type){
//        HashMap<String,Integer> clock = null;
//        Clock item;
//
//        for(int i= allClocks.size() - 1; i >= 0 ; i--){
//            item = allClocks.get(i);
//            if(item.isSrc(traceId, spanId, type)){
//                clock = item.getClock();
//                break;
//            }
//        }
//        return (HashMap<String,Integer>)clock.clone();
//    }
//
//
//
//    //sort the log for one trace according to the calling sequences
//    public static List<HashMap<String,String>> sortLog(List<HashMap<String,String>> logs){
//        List<HashMap<String,String>> list = null ;
//
//        HashMap<String,String> log = logs.get(0);
//        String traceId = log.get("traceId");
//
//        HashMap<String, Span> spans = new HashMap<String, Span>();
//        HashMap<String,List<String>> spanRelation = new HashMap<String, List<String>>();
//        logs.forEach(n -> {
//            String spanId = n.get("spanId");
//            if(spans.containsKey(spanId)){
//                Span span = spans.get(spanId);
//                span.addLog(n);
//            }else{
//                Span span = new Span(n.get("traceId"), n.get("spanId"), n.get("parentId"));
//                span.addLog(n);
//                spans.put(spanId,span);
//            }
//
//            if(spanRelation.containsKey(n.get("parentId"))){
//                List<String> childs = spanRelation.get(n.get("parentId"));
//                if(!childs.contains(spanId)){
//                    childs.add(spanId);
//                }
//            }else{
//                List<String> childs = new ArrayList<String>();
//                childs.add(spanId);
//                spanRelation.put(n.get("parentId"),childs);
//            }
//        });
//
//        List<HashMap<String,String>> forwardLogs = new ArrayList<HashMap<String,String>>();
//        List<HashMap<String,String>> backwardLogs = new ArrayList<HashMap<String,String>>();
//        List<Span> sortedSpan = new ArrayList<Span>();
//
//        Span entrance = spans.get(traceId);
//
//        if(entrance == null){
//            Iterator<Map.Entry<String, Span>> entries = spans.entrySet().iterator();
//            while(entries.hasNext()){
//                Map.Entry<String, Span> entry = entries.next();
//                Span span = entry.getValue();
//                if(traceId.equals(span.getParentId())){
//                    entrance = span;
//                    break;
//                }
//            }
//        }
//
//        setChilds(spanRelation,entrance,spans);
//
//        traverse(entrance, forwardLogs, backwardLogs, spans);
//
//        Stack<HashMap<String,String>> stack = new Stack<HashMap<String,String>>();
//        backwardLogs.forEach(n ->{
//            stack.push(n);
//        });
//
//        while(!stack.isEmpty()){
//            forwardLogs.add(stack.pop());
//        }
//
//        return forwardLogs;
//    }
//
//    public static void setChilds(HashMap<String,List<String>> spanRelation, Span entrance, HashMap<String, Span> spans){
//        Span s = entrance;
//
//        if(spanRelation.containsKey(s.getSpanId())){
//            s.setChilds(spanRelation.get(s.getSpanId()));
//            Iterator<String> iterator = s.getChilds().iterator();
//            while(iterator.hasNext()){
//                String childId = iterator.next();
//                s = spans.get(childId);
//                setChilds(spanRelation,s,spans);
//            }
//        }
//    }
//
//    public static void traverse(Span entrance, List<HashMap<String,String>> forwardLogs, List<HashMap<String,String>> backwardLogs, HashMap<String, Span> spans){
//        //from the entrance to end
//        Span s = entrance;
//
//        HashMap<String,String> cs = null;
//        HashMap<String,String> sr = null;
//        HashMap<String,String> ss = null;
//        HashMap<String,String> cr = null;
//        HashMap<String,String> async = null;
//
//        Iterator<HashMap<String,String>> iterator = s.getLogs().iterator();
//        while(iterator.hasNext()){
//            HashMap<String,String> log1 = iterator.next();
//            if("cs".equals(log1.get("type"))){
//                cs = log1;
//            }
//            if("sr".equals(log1.get("type"))){
//                sr = log1;
//            }
//            if("ss".equals(log1.get("type"))){
//                ss = log1;
//            }
//            if("cr".equals(log1.get("type"))){
//                cr = log1;
//            }
//            if("inside_payment.async".equals(log1.get("type"))){
//                async = log1;
//            }
//        }
//
//        if(cs != null){
//            forwardLogs.add(cs);
//        }
//        if(sr != null){
//            forwardLogs.add(sr);
//        }
//        if(async != null){
//            forwardLogs.add(async);
//        }
//        if(cr != null){
//            backwardLogs.add(cr);
//        }
//        if(ss != null){
//            backwardLogs.add(ss);
//        }
//
//
//
//        if(s.getChilds() != null){
//            List<String> sortedChilds = s.getChilds().stream().sorted((spanId1,spanId2) -> {
//                Span span1 = spans.get(spanId1);
//                Span span2 = spans.get(spanId2);
//
//                HashMap<String,String> sr1 = null;
//                HashMap<String,String> sr2 = null;
//
//                Iterator<HashMap<String,String>> ite1 = span1.getLogs().iterator();
//                while(ite1.hasNext()){
//                    HashMap<String,String> log1 = ite1.next();
//                    if("cs".equals(log1.get("type"))){
//                        sr1 = log1;
//                    }else if("sr".equals(log1.get("type"))){
//                        sr1 = log1;
//                    }else if("inside_payment.async".equals(log1.get("type"))){
//                        sr1 = log1;
//                    }
//                }
//
//                Iterator<HashMap<String,String>> ite2 = span2.getLogs().iterator();
//                while(ite2.hasNext()){
//                    HashMap<String,String> log2 = ite2.next();
//                    if("cs".equals(log2.get("type"))){
//                        sr2 = log2;
//                    }else if("sr".equals(log2.get("type"))){
//                        sr2 = log2;
//                    }else if("inside_payment.async".equals(log2.get("type"))){
//                        sr2 = log2;
//                    }
//                }
//
//                System.out.println("sr1:"+sr1.get("timestamp"));
//                System.out.println("sr2:"+sr2.get("timestamp"));
//                Long time1 = Long.valueOf(sr1.get("timestamp"));
//                Long time2 = Long.valueOf(sr2.get("timestamp"));
//                return time1.compareTo(time2);
//            }).collect(Collectors.toList());
//
//            Iterator<String> iterator1 = sortedChilds.iterator();
//            List<HashMap<String,String>> childsLogs = new ArrayList<HashMap<String,String>>();
//
//            while(iterator1.hasNext()){
//                List<HashMap<String,String>> childForwardLogs = new ArrayList<HashMap<String,String>>();
//                List<HashMap<String,String>> childBackwardLogs = new ArrayList<HashMap<String,String>>();
//                String childId = iterator1.next();
//                traverse(spans.get(childId), childForwardLogs, childBackwardLogs, spans);
//                childsLogs.addAll(mergeForwardAndBackwardLogs(childForwardLogs,childBackwardLogs));
//            }
//
//            forwardLogs.addAll(childsLogs);
//        }
//
//
//    }
//
//    public static List<HashMap<String,String>> mergeForwardAndBackwardLogs(List<HashMap<String,String>> forwardLogs, List<HashMap<String,String>> backwardLogs){
//        Stack<HashMap<String,String>> stack = new Stack<HashMap<String,String>>();
//        backwardLogs.forEach(n ->{
//            stack.push(n);
//        });
//
//        while(!stack.isEmpty()){
//            forwardLogs.add(stack.pop());
//        }
//
//        return forwardLogs;
//    }
//
//    public static List<HashMap<String,String>> clock2(List<HashMap<String,String>> logs){
//        HashMap<String,HashMap<String,Integer>> clocks = new HashMap<String,HashMap<String,Integer>>();
//        List<Clock> allClocks = new ArrayList<Clock>();
//
//        List<HashMap<String,String>> list = sortLog(logs);
//
//        list.forEach(n -> {
//            if(clocks.containsKey(n.get("host"))){
//                HashMap<String,Integer> clock = clocks.get(n.get("host"));
//
//                if(n.get("src") != null){
//                    HashMap<String,Integer> srcClock = findSrcClock(allClocks, n.get("traceId"), n.get("spanId"), n.get("type"));
//
//                    Iterator<Map.Entry<String,Integer>> iterator = srcClock.entrySet().iterator();
//                    while (iterator.hasNext()) {
//                        Map.Entry<String, Integer> entry = iterator.next();
//                        if(clock.get(entry.getKey()) != null){
//                            if(entry.getValue() <= clock.get(entry.getKey())){
//                                //don't change clock
//                            }else{  //update clock
//                                clock.put(entry.getKey(),entry.getValue());
//                            }
//                        }else{   //update clock
//                            clock.put(entry.getKey(),entry.getValue());
//                        }
//                    }
//
//                    clock.put(n.get("host"),clock.get(n.get("host")) +1);
//
//                }else{
//                    clock.put(n.get("host"),clock.get(n.get("host")) +1);
//                }
//                n.put("clock",clock.toString());
//
//                clocks.put(n.get("host"), clock);
//                allClocks.add(new Clock(n.get("type"), n.get("host"), n.get("src"), n.get("traceId"), n.get("spanId"), (HashMap<String,Integer>)clock.clone()));
//            }else{
//                HashMap<String,Integer> clock = new HashMap<String,Integer>();
//
//                if(n.get("src") != null){
//                    HashMap<String,Integer> srcClock = findSrcClock(allClocks, n.get("traceId"), n.get("spanId"), n.get("type"));
//
//                    Iterator<Map.Entry<String,Integer>> iterator = srcClock.entrySet().iterator();
//                    while (iterator.hasNext()) {
//                        Map.Entry<String, Integer> entry = iterator.next();
//                        if(clock.get(entry.getKey()) != null){
//                            if(entry.getValue() <= clock.get(entry.getKey())){
//                                //don't change clock
//                            }else{  //update clock
//                                clock.put(entry.getKey(),entry.getValue());
//                            }
//                        }else{   //update clock
//                            clock.put(entry.getKey(),entry.getValue());
//                        }
//                    }
//                    clock.put(n.get("host"),1);
//                }else{
//                    clock.put(n.get("host"),1);
//                }
//                n.put("clock",clock.toString());
//
//                clocks.put(n.get("host"), clock);
//                allClocks.add(new Clock(n.get("type"), n.get("host"), n.get("src"), n.get("traceId"), n.get("spanId"), (HashMap<String,Integer>)clock.clone()));
//            }
//        });
//
//        return list;
//    }
//
//    public static List<HashMap<String,String>> clock(List<HashMap<String,String>> logs){
//        HashMap<String,HashMap<String,Integer>> clocks = new HashMap<String,HashMap<String,Integer>>();
//
//        List<HashMap<String,String>> list = logs.stream().sorted((log1,log2) -> {
//            Long time1 = Long.valueOf(log1.get("timestamp"));
//            Long time2 = Long.valueOf(log2.get("timestamp"));
//            return time1.compareTo(time2);
//        }).collect(Collectors.toList());
//
//        list.forEach(n -> {
//            if(clocks.containsKey(n.get("host"))){
//                HashMap<String,Integer> clock = clocks.get(n.get("host"));
//
//                if(n.get("src") != null){
//                    HashMap<String,Integer> srcClock = (HashMap<String,Integer>)clocks.get(n.get("src")).clone();
//
//                    Iterator<Map.Entry<String,Integer>> iterator = srcClock.entrySet().iterator();
//                    while (iterator.hasNext()) {
//                        Map.Entry<String, Integer> entry = iterator.next();
//                        if(clock.get(entry.getKey()) != null){
//                            if(entry.getValue() <= clock.get(entry.getKey())){
//                                //don't change clock
//                            }else{  //update clock
//                                clock.put(entry.getKey(),entry.getValue());
//                            }
//                        }else{   //update clock
//                            clock.put(entry.getKey(),entry.getValue());
//                        }
//                    }
//
//                    clock.put(n.get("host"),clock.get(n.get("host")) +1);
//
//                }else{
//                    clock.put(n.get("host"),clock.get(n.get("host")) +1);
//                }
//                n.put("clock",clock.toString());
//                clocks.put(n.get("host"), clock);
//            }else{
//                HashMap<String,Integer> clock = new HashMap<String,Integer>();
//
//                if(n.get("src") != null){
//                    HashMap<String,Integer> srcClock = (HashMap<String,Integer>)clocks.get(n.get("src")).clone();
//
//                    Iterator<Map.Entry<String,Integer>> iterator = srcClock.entrySet().iterator();
//                    while (iterator.hasNext()) {
//                        Map.Entry<String, Integer> entry = iterator.next();
//                        if(clock.get(entry.getKey()) != null){
//                            if(entry.getValue() <= clock.get(entry.getKey())){
//                                //don't change clock
//                            }else{  //update clock
//                                clock.put(entry.getKey(),entry.getValue());
//                            }
//                        }else{   //update clock
//                            clock.put(entry.getKey(),entry.getValue());
//                        }
//                    }
//                    clock.put(n.get("host"),1);
//                }else{
//                    clock.put(n.get("host"),1);
//                }
//                n.put("clock",clock.toString());
//                clocks.put(n.get("host"), clock);
//            }
//        });
//
//        return list;
//    }
//
//
//    public static String readFile(String path) {
//        File file = new File(path);
//        BufferedReader reader = null;
//        String laststr = "";
//        try {
//            reader = new BufferedReader(new FileReader(file));
//            String tempString = null;
//            while ((tempString = reader.readLine()) != null) {
//                laststr = laststr + tempString;
//                System.out.println("reading");
//            }
//            reader.close();
//        } catch (IOException e) {
//            e.printStackTrace();
//        } finally {
//            if (reader != null) {
//                try {
//                    reader.close();
//                } catch (IOException e1) {
//                }
//            }
//        }
//        return laststr;
//    }
//
//    public static boolean write(String path, List<HashMap<String,String>> logs){
//        File writer = new File(path);
//        BufferedWriter out = null;
//        try{
//            writer.createNewFile(); // 鍒涘缓鏂版枃浠?
//            out = new BufferedWriter(new FileWriter(writer));
//            Iterator<HashMap<String,String>> iterator = logs.iterator();
//            while(iterator.hasNext()){
//                HashMap<String,String> map = iterator.next();
//                out.write(map.toString() + "\r\n");
//            }
//        }catch(IOException e){
//            e.printStackTrace();
//            return false;
//        }finally{
//            if (out != null) {
//                try {
//                    out.flush();
//                    out.close();
//                } catch (IOException e1) {
//                }
//            }
//        }
//
//        return true;
//    }
//
//
////    public static boolean writeFile(String path, List<HashMap<String,String>> logs){
////        File writer = new File(path);
////        BufferedWriter out = null;
////        try{
////            writer.createNewFile(); // 鍒涘缓鏂版枃浠?
////            out = new BufferedWriter(new FileWriter(writer));
////            Iterator<HashMap<String,String>> iterator = logs.iterator();
////            while(iterator.hasNext()){
////                HashMap<String,String> map = iterator.next();
////                Iterator<Map.Entry<String, String>> entries = map.entrySet().iterator();
////                out.write("{");
////                while (entries.hasNext()) {
////                    Map.Entry<String, String> entry = entries.next();
////                    if(entry.getKey().equals("clock")){
////                        String clocks = entry.getValue();
////                        String[] c = clocks.split(",");
////                        out.write("clock={");
////                        for(int i=0,length=c.length; i<length; i++){
////                            c[i] = "\"" + c[i].substring(1,c[i].indexOf("=")) + "\":"
////                                    + c[i].substring(c[i].indexOf("=")+1);
////                            if(i < length-1){
////                                out.write(c[i] + ",");
////                            }else{
////                                out.write(c[i]);
////                            }
////
////                        }
////                        out.write(", ");
////
////                    }else{
////                        out.write(entry.toString() + ", ");
////                    }
////                }
////
////                out.write("}\r\n");
////            }
////        }catch(IOException e){
////            e.printStackTrace();
////            return false;
////        }finally{
////            if (out != null) {
////                try {
////                    out.flush();
////                    out.close();
////                } catch (IOException e1) {
////                }
////            }
////        }
////
////        return true;
////    }
//
////    public static boolean writeFile(String path, List<List<HashMap<String,String>>> logs, HashMap<List<HashMap<String,String>>, Boolean> failures){
////        File writer = new File(path);
////        BufferedWriter out = null;
////        try{
////            writer.createNewFile(); // 鍒涘缓鏂版枃浠?
////            out = new BufferedWriter(new FileWriter(writer));
////            int fail = 0;
////            int success = 0;
////
////            Iterator<List<HashMap<String,String>>> iterator1 = logs.iterator();
////            while(iterator1.hasNext()){
////                List<HashMap<String,String>> list = iterator1.next();
////
////                boolean failed = failures.get(list);
////                if(failed){
////                    out.write("\r\n=== Fail execution " + (fail++) + " ===\r\n");
////                }else{
////                    out.write("\r\n=== Success execution " + (success++) + " ===\r\n");
////                }
////
////                Iterator<HashMap<String,String>> iterator = list.iterator();
////                while(iterator.hasNext()){
////                    HashMap<String,String> map = iterator.next();
////                    Iterator<Map.Entry<String, String>> entries = map.entrySet().iterator();
////                    out.write("{");
////                    while (entries.hasNext()) {
////                        Map.Entry<String, String> entry = entries.next();
////                        if(entry.getKey().equals("clock")){
////                            String clocks = entry.getValue();
////                            String[] c = clocks.split(",");
////                            out.write("clock={");
////                            for(int i=0,length=c.length; i<length; i++){
////                                c[i] = "\"" + c[i].substring(1,c[i].lastIndexOf("=")) + "\":"
////                                        + c[i].substring(c[i].lastIndexOf("=")+1);
////                                if(i < length-1){
////                                    out.write(c[i] + ",");
////                                }else{
////                                    out.write(c[i]);
////                                }
////
////                            }
////                            out.write(", ");
////
////                        }else{
////                            out.write(entry.toString() + ", ");
////                        }
////                    }
////
////                    out.write("}\r\n");
////                }
////            }
////
////
////
////        }catch(IOException e){
////            e.printStackTrace();
////            return false;
////        }finally{
////            if (out != null) {
////                try {
////                    out.flush();
////                    out.close();
////                } catch (IOException e1) {
////                }
////            }
////        }
////
////        return true;
////    }
//
//    public static boolean writeFile(String path, List<List<HashMap<String,String>>> logs, HashMap<List<HashMap<String,String>>, Boolean> failures){
//        File writer = new File(path);
//        BufferedWriter out = null;
//        try{
//            writer.createNewFile(); // 鍒涘缓鏂版枃浠?
//            out = new BufferedWriter(new FileWriter(writer));
//            int fail = 0;
//            int success = 0;
//
//            Iterator<List<HashMap<String,String>>> iterator1 = logs.iterator();
//            while(iterator1.hasNext()){
//                List<HashMap<String,String>> list = iterator1.next();
//
//                boolean failed = failures.get(list);
//                if(failed){
//                    out.write("\r\n=== Fail execution " + (fail++) + " ===\r\n");
//                }else{
//                    out.write("\r\n=== Success execution " + (success++) + " ===\r\n");
//                }
//
//                Iterator<HashMap<String,String>> iterator = list.iterator();
//                while(iterator.hasNext()){
//                    HashMap<String,String> map = iterator.next();
//                    out.write("{");
//
//
//                    if(map.containsKey("traceId")){
//                        out.write("traceId="+ map.get("traceId") + ", ");
//                    }
//                    if(map.containsKey("spanId")){
//                        out.write("spanId="+ map.get("spanId") + ", ");
//                    }
//                    if(map.containsKey("hostName")){
//                        out.write("hostName="+ map.get("hostName") + ", ");
//                    }
//                    if(map.containsKey("srcName")){
//                        out.write("srcName="+ map.get("srcName") + ", ");
//                    }
//                    if(map.containsKey("destName")){
//                        out.write("destName="+ map.get("destName") + ", ");
//                    }
//                    if(map.containsKey("src")){
//                        out.write("src="+ map.get("src") + ", ");
//                    }
//                    if(map.containsKey("host")){
//                        out.write("host="+ map.get("host") + ", ");
//                    }
//                    if(map.containsKey("api")){
//                        out.write("api="+ map.get("api") + ", ");
//                    }
//                    if(map.containsKey("clock")){
//                        String clocks = map.get("clock");
//                        String[] c = clocks.split(",");
//                        out.write("clock={");
//                        for(int i=0,length=c.length; i<length; i++){
//                            c[i] = "\"" + c[i].substring(1,c[i].lastIndexOf("=")) + "\":"
//                                    + c[i].substring(c[i].lastIndexOf("=")+1);
//                            if(i < length-1){
//                                out.write(c[i] + ",");
//                            }else{
//                                out.write(c[i]);
//                            }
//
//                        }
//                        out.write(", ");
//                    }
//                    if(map.containsKey("dest")){
//                        out.write("dest="+ map.get("dest") + ", ");
//                    }
//                    if(map.containsKey("event")){
//                        out.write("event="+ map.get("event") + ", ");
//                    }
//                    if(map.containsKey("type")){
//                        out.write("type="+ map.get("type") + ", ");
//                    }
//                    if(map.containsKey("error")){
//                        out.write("error="+ map.get("error") + ", ");
//                    }
//                    if(map.containsKey("parentId")){
//                        out.write("parentId="+ map.get("parentId") + ", ");
//                    }
//                    if(map.containsKey("timestamp")){
//                        out.write("timestamp="+ map.get("timestamp") + ", ");
//                    }
//
//
//                    out.write("}\r\n");
//                }
//            }
//
//
//
//        }catch(IOException e){
//            e.printStackTrace();
//            return false;
//        }finally{
//            if (out != null) {
//                try {
//                    out.flush();
//                    out.close();
//                } catch (IOException e1) {
//                }
//            }
//        }
//
//        return true;
//    }
//}


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Json2Shiviz/src/main/java/org/services/analysis/TraceTranslatorQueue.java:TraceTranslatorQueue.<init>
