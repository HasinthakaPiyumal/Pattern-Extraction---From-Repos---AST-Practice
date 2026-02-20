// Cluster 13

// Node: currentTimeMillis
// Node: WaitListOrder
package waitorder.entity;

import edu.fudan.common.util.StringUtils;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.Date;

/**
 * @author fdse
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class WaitListOrderVO {
    private String accountId;

    private String contactsId;

    private String tripId;

    private int seatType;

    private String date;

    private String from;

    private String to;

    private String price;


    public Date getDate(){
        return StringUtils.String2Date(date);
    }

    public void setDate(Date date){
        this.date = StringUtils.Date2String(date);
    }


}



// Node: Date2String
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


// Node: repos/cloned_ms_repos/train-ticket/ts-wait-order-service/src/main/java/waitorder/entity/WaitListOrder.java:WaitListOrder.<init>
// Node: GenericGenerator
// Node: GeneratedValue
// Node: Column
// Node: Date
// Node: setTime
// Node: setCreatedTime
// Node: setWaitUntilTime
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


// Node: repos/cloned_ms_repos/train-ticket/ts-auth-service/src/main/java/auth/entity/User.java:User.<init>
// Node: Table
// Node: CollectionTable
// Node: JoinColumn
package edu.fudan.common.exception;

/**
 * @author fdse
 */
public class TokenException extends BaseException{

    public TokenException(String message) {
        super(message);
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-common/src/main/java/edu/fudan/common/exception/TokenException.java:TokenException.<init>
// Node: TokenException
// Node: JsonIgnoreProperties
package edu.fudan.common.entity;

import edu.fudan.common.util.StringUtils;
import lombok.Data;

import javax.validation.Valid;
import javax.validation.constraints.NotNull;
import java.util.Date;

/**
 * @author fdse
 */
@Data
public class TripResponse {
    @Valid
    private TripId tripId;

    @Valid
    @NotNull
    private String trainTypeName;

    @Valid
    @NotNull
    private String startStation;

    @Valid
    @NotNull
    private String terminalStation;

    @Valid
    @NotNull
    private String startTime;

    @Valid
    @NotNull
    private String endTime;

    /**
     * the number of economy seats
     */
    @Valid
    @NotNull
    private int economyClass;

    /**
     * the number of confort seats
     */
    @Valid
    @NotNull
    private int confortClass;

    @Valid
    @NotNull
    private String priceForEconomyClass;

    @Valid
    @NotNull
    private String priceForConfortClass;

    public TripResponse(){
        //Default Constructor
        this.trainTypeName = "";
        this.startStation = "";
        this.terminalStation = "";
        this.startTime = "";
        this.endTime = "";
        this.economyClass = 0;
        this.confortClass = 0;
        this.priceForEconomyClass = "";
        this.priceForConfortClass = "";
    }

//    public Date getStartTime(){
//        return StringUtils.String2Date(startTime);
//    }
//    public Date getEndTime(){
//        return StringUtils.String2Date(endTime);
//    }
//
//    public void setStartTime(Date startTime){
//        this.startTime = StringUtils.Date2String(startTime);
//    }
//    public void setEndTime(Date endTime){
//        this.endTime = StringUtils.Date2String(endTime);
//    }

}


package edu.fudan.common.entity;

import lombok.AllArgsConstructor;
import lombok.Data;

/**
 * @author fdse
 */
@Data
@AllArgsConstructor
public class OrderSecurity {

    private int orderNumInLastOneHour;

    private int orderNumOfValidOrder;

    public OrderSecurity() {
        //Default Constructor
    }

}


// Node: repos/cloned_ms_repos/train-ticket/ts-common/src/main/java/edu/fudan/common/entity/OrderSecurity.java:OrderSecurity.<init>
// Node: OrderSecurity
package edu.fudan.common.entity;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.UUID;

/**
 * @author fdse
 */
@Data
@JsonIgnoreProperties(ignoreUnknown = true)
@NoArgsConstructor
@AllArgsConstructor
public class Contacts {

    private UUID id;

    private UUID accountId;

    private String name;

    private int documentType;

    private String documentNumber;

    private String phoneNumber;

    @Override
    public boolean equals(Object obj) {
        if (this == obj) {
            return true;
        }
        if (obj == null) {
            return false;
        }
        if (getClass() != obj.getClass()) {
            return false;
        }
        Contacts other = (Contacts) obj;
        return name.equals(other.getName())
                && accountId .equals( other.getAccountId() )
                && documentNumber.equals(other.getDocumentNumber())
                && phoneNumber.equals(other.getPhoneNumber())
                && documentType == other.getDocumentType();
    }

    @Override
    public int hashCode() {
        int result = 17;
        result = 31 * result + (id == null ? 0 : id.hashCode());
        return result;
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-common/src/main/java/edu/fudan/common/entity/Contacts.java:Contacts.<init>
package edu.fudan.common.entity;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import lombok.Data;

import javax.validation.constraints.NotNull;
import java.util.UUID;

/**
 * @author fdse
 */
@Data
@JsonIgnoreProperties(ignoreUnknown = true)
public class Assurance {

    private UUID id;

    /**
     * which order the assurance is related to
     */
    @NotNull
    private UUID orderId;

    /**
     * the type of assurance
     */
    private AssuranceType type;

    public Assurance(){
        this.orderId = UUID.randomUUID();
    }

    public Assurance(UUID id, UUID orderId, AssuranceType type){
        this.id = id;
        this.orderId = orderId;
        this.type = type;
    }

}


// Node: repos/cloned_ms_repos/train-ticket/ts-common/src/main/java/edu/fudan/common/entity/Assurance.java:Assurance.<init>
package edu.fudan.common.entity;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import edu.fudan.common.entity.SeatClass;
import edu.fudan.common.util.StringUtils;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.Date;
import java.util.UUID;

/**
 * @author fdse
 */
@Data
@JsonIgnoreProperties(ignoreUnknown = true)
@AllArgsConstructor
public class Order {

    private String id;

    private String boughtDate;

    private String travelDate;

    private String travelTime;

    /**
     * Which Account Bought it
     */
    private String accountId;

    /**
     * Tickets bought for whom....
     */
    private String contactsName;

    private int documentType;

    private String contactsDocumentNumber;

    private String trainNumber;

    private int coachNumber;

    private int seatClass;

    private String seatNumber;

    private String from;

    private String to;

    private int status;

    private String price;

    private String differenceMoney;

    public Order(){
        boughtDate = StringUtils.Date2String(new Date(System.currentTimeMillis()));
        travelDate = StringUtils.Date2String(new Date(123456789));
        trainNumber = "G1235";
        coachNumber = 5;
        seatClass = SeatClass.FIRSTCLASS.getCode();
        seatNumber = "5A";
        from = "shanghai";
        to = "taiyuan";
        status = OrderStatus.PAID.getCode();
        price = "0.0";
        differenceMoney ="0.0";
    }

    public boolean equals(Object obj) {
        if (this == obj) {
            return true;
        }
        if (obj == null) {
            return false;
        }
        if (getClass() != obj.getClass()) {
            return false;
        }
        Order other = (Order) obj;
        return getBoughtDate().equals(other.getBoughtDate())
                && getBoughtDate().equals(other.getTravelDate())
                && getTravelTime().equals(other.getTravelTime())
                && accountId .equals( other.getAccountId() )
                && contactsName.equals(other.getContactsName())
                && contactsDocumentNumber.equals(other.getContactsDocumentNumber())
                && documentType == other.getDocumentType()
                && trainNumber.equals(other.getTrainNumber())
                && coachNumber == other.getCoachNumber()
                && seatClass == other.getSeatClass()
                && seatNumber .equals(other.getSeatNumber())
                && from.equals(other.getFrom())
                && to.equals(other.getTo())
                && status == other.getStatus()
                && price.equals(other.price);
    }

    @Override
    public int hashCode() {
        int result = 17;
        result = 31 * result + (id == null ? 0 : id.hashCode());
        return result;
    }

}


// Node: repos/cloned_ms_repos/train-ticket/ts-common/src/main/java/edu/fudan/common/entity/Order.java:Order.<init>
package edu.fudan.common.entity;

import edu.fudan.common.util.StringUtils;
import lombok.Data;
import lombok.ToString;

import java.util.Date;

/**
 * @author fdse
 */
@Data
@ToString
public class TripAllDetailInfo {

    private String tripId;

    private String travelDate;

    private String from;

    private String to;

    public TripAllDetailInfo() {
        //Default Constructor
    }

    public String getFrom() {
        return StringUtils.String2Lower(this.from);
    }

    public String getTo() {
        return StringUtils.String2Lower(this.to);
    }

//    public Date getTravelDate() {
//        return StringUtils.String2Date(travelDate);
//    }
//
//    public void setTravelDate(Date travelDate) {
//        this.travelDate = StringUtils.Date2String(travelDate);
//    }
}


package edu.fudan.common.entity;

import edu.fudan.common.util.StringUtils;

import lombok.Data;

import javax.validation.Valid;
import javax.validation.constraints.NotNull;
import java.util.Date;
import java.util.UUID;

/**
 * @author fdse
 */
@Data
public class Trip {
    private String id;

    private TripId tripId;

    private String trainTypeName;

    private String routeId;
    private String startStationName;

    private String stationsName;

    private String terminalStationName;

    private String startTime;

    private String endTime;

    public Trip(edu.fudan.common.entity.TripId tripId, String trainTypeName, String startStationName, String stationsName, String terminalStationName, String startTime, String endTime) {
        this.tripId = tripId;
        this.trainTypeName = trainTypeName;
        this.startStationName = StringUtils.String2Lower(startStationName);
        this.stationsName = StringUtils.String2Lower(stationsName);
        this.terminalStationName = StringUtils.String2Lower(terminalStationName);
        this.startTime = startTime;
        this.endTime = endTime;
    }

    public Trip(TripId tripId, String trainTypeName, String routeId) {
        this.tripId = tripId;
        this.trainTypeName = trainTypeName;
        this.routeId = routeId;
        this.startStationName = "";
        this.terminalStationName = "";
        this.startTime = "";
        this.endTime = "";
    }

    public Trip(){
        //Default Constructor
        this.trainTypeName = "";
        this.startStationName = "";
        this.terminalStationName = "";
        this.startTime = "";
        this.endTime = "";
    }

//    public Date getStartTime(){
//        return StringUtils.String2Date(this.startTime);
//    }
//
//    public Date getEndTime(){
//        return StringUtils.String2Date(this.endTime);
//    }
//
//    public void setStartTime(Date startTime){
//        this.startTime = StringUtils.Date2String(startTime);
//    }
//
//    public void setEndTime(Date endTime){
//        this.endTime = StringUtils.Date2String(endTime);
//    }

}

package edu.fudan.common.security.jwt;

import io.jsonwebtoken.JwtException;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.filter.OncePerRequestFilter;

import javax.servlet.FilterChain;
import javax.servlet.ServletException;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.io.IOException;

/**
 * @author fdse
 */
public class JWTFilter extends OncePerRequestFilter {

    @Override
    protected void doFilterInternal(HttpServletRequest httpServletRequest, HttpServletResponse httpServletResponse, FilterChain filterChain) throws ServletException, IOException {

        try {
            Authentication authentication =
                    JWTUtil.
                            getJWTAuthentication(httpServletRequest);
            SecurityContextHolder.getContext().setAuthentication(authentication);
            filterChain.doFilter(httpServletRequest, httpServletResponse);
        } catch (JwtException e) {
            httpServletResponse.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
        }
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-common/src/main/java/edu/fudan/common/security/jwt/JWTFilter.java:JWTFilter.<init>
// Node: doFilterInternal
// Node: getJWTAuthentication
// Node: getContext
// Node: setAuthentication
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


// Node: getTokenFromHeader
// Node: validateToken
// Node: getRole
// Node: getClaims
// Node: getSubject
// Node: getExpiration
// Node: before
// Node: parser
// Node: setSigningKey
// Node: parseClaimsJws
package com.trainticket.entity;

import lombok.Data;
import org.hibernate.annotations.GenericGenerator;

import javax.persistence.Column;
import javax.persistence.Entity;
import javax.persistence.GeneratedValue;
import javax.persistence.Id;
import javax.validation.Valid;
import javax.validation.constraints.NotNull;
import java.util.UUID;

/**
 * @author fdse
 */
@Data
@Entity
@GenericGenerator(name = "jpa-uuid", strategy = "org.hibernate.id.UUIDGenerator")
public class Payment {
    @Id
    @NotNull
    @Column(length = 36)
    @GeneratedValue(generator = "jpa-uuid")
    private String id;

    @NotNull
    @Valid
    @Column(length = 36)
    private String orderId;

    @NotNull
    @Valid
    @Column(length = 36)
    private String userId;

    @NotNull
    @Valid
    @Column(name = "payment_price")
    private String price;

    public Payment(){
        this.id = UUID.randomUUID().toString();
        this.orderId = "";
        this.userId = "";
        this.price = "";
    }

}


// Node: repos/cloned_ms_repos/train-ticket/ts-payment-service/src/main/java/com/trainticket/entity/Payment.java:Payment.<init>
package com.trainticket.entity;

import lombok.AllArgsConstructor;
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
@AllArgsConstructor
@NoArgsConstructor
@GenericGenerator(name = "jpa-uuid", strategy = "org.hibernate.id.UUIDGenerator")
@Entity
public class Money {
    @Id
    @Column(length = 36)
    @GeneratedValue(generator = "jpa-uuid")
    private String id;

    @Column(length = 36)
    private String userId;
    private String money; //NOSONAR

}


// Node: repos/cloned_ms_repos/train-ticket/ts-payment-service/src/main/java/com/trainticket/entity/Money.java:Money.<init>
package price.entity;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import lombok.AllArgsConstructor;
import lombok.Data;

import javax.persistence.*;

import java.util.UUID;

/**
 * @author fdse
 */
@Data
@AllArgsConstructor
@Entity
@JsonIgnoreProperties(ignoreUnknown = true)
@Table(indexes = {@Index(name = "route_type_idx", columnList = "train_type, route_id", unique = true)})
public class PriceConfig {

    @Id
    @Column(length = 36)
    private String id;

    @Column(name="train_type")
    private String trainType;

    @Column(name="route_id", length = 36)
    private String routeId;

    private double basicPriceRate;

    private double firstClassPriceRate;

    public PriceConfig() {
        //Empty Constructor
        this.id = UUID.randomUUID().toString();
    }

}


// Node: repos/cloned_ms_repos/train-ticket/ts-price-service/src/main/java/price/entity/PriceConfig.java:PriceConfig.<init>
// Node: Index
package notification.entity;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import lombok.AllArgsConstructor;
import lombok.Data;

import javax.persistence.Column;
import javax.persistence.Id;


import javax.persistence.Entity;
import org.hibernate.annotations.GenericGenerator;
import java.util.UUID;

import lombok.Data;

import javax.persistence.Entity;

/**
 * @author fdse
 */
@Data
@AllArgsConstructor
@Entity
@GenericGenerator(name = "jpa-uuid", strategy = "org.hibernate.id.UUIDGenerator")
@JsonIgnoreProperties(ignoreUnknown = true)
public class NotifyInfo {

    public NotifyInfo(){
        //Default Constructor
    }

    @Id
    @JsonIgnoreProperties(ignoreUnknown = true)
    @Column(length = 36)
    private String id;

    private Boolean sendStatus;

    private String email;
    private String orderNumber;
    private String username;
    private String startPlace;
    private String endPlace;
    private String startTime;
    private String date;
    private String seatClass;
    private String seatNumber;
    private String price;

}


// Node: repos/cloned_ms_repos/train-ticket/ts-notification-service/src/main/java/notification/entity/NotifyInfo.java:NotifyInfo.<init>
// Node: getLoginId
// Node: checkSecurityAboutOrder
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



// Node: isEnableStateQuery
// Node: isEnableBoughtDateQuery
// Node: isEnableTravelDateQuery
// Node: getState
// Node: getTravelDateEnd
// Node: getBoughtDateStart
// Node: getBoughtDateEnd
// Node: after
// Node: setOrderNumInLastOneHour
// Node: setOrderNumOfValidOrder
package other.entity;

import lombok.AllArgsConstructor;
import lombok.Data;
import org.hibernate.annotations.GenericGenerator;

import javax.persistence.Column;
import javax.persistence.GeneratedValue;
import java.util.UUID;

/**
 * @author fdse
 */
@Data
@AllArgsConstructor
@GenericGenerator(name = "jpa-uuid", strategy = "org.hibernate.id.UUIDGenerator")
public class OrderAlterInfo {

    @GeneratedValue(generator = "jpa-uuid")
    @Column(length = 36)
    private String accountId;

    @GeneratedValue(generator = "jpa-uuid")
    @Column(length = 36)
    private String previousOrderId;

    private String loginToken;

    private Order newOrderInfo;

    public OrderAlterInfo(){
        newOrderInfo = new Order();
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-order-other-service/src/main/java/other/entity/OrderAlterInfo.java:OrderAlterInfo.<init>
package other.entity;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import edu.fudan.common.entity.OrderStatus;
import edu.fudan.common.entity.SeatClass;
import edu.fudan.common.util.StringUtils;
import lombok.Data;
import lombok.ToString;
import org.hibernate.annotations.GenericGenerator;

import javax.persistence.*;
import java.util.Date;

/**
 * @author fdse
 */
@Data
@Table(name = "orders_other")
@Entity
@GenericGenerator(name = "jpa-uuid", strategy = "org.hibernate.id.UUIDGenerator")
@ToString
@JsonIgnoreProperties(ignoreUnknown = true)
public class Order {
    @Id
    @Column(length = 36)
    @GeneratedValue(generator = "jpa-uuid")
    private String id;

    private String boughtDate;


    private String travelDate;


    private String travelTime;

    /**
     * Which Account Bought it
     */
    @Column(length = 36)
    private String accountId;

    /**
     * Tickets bought for whom....
     */
    private String contactsName;

    private int documentType;

    private String contactsDocumentNumber;

    private String trainNumber;

    private int coachNumber;

    private int seatClass;

    private String seatNumber;

    @Column(name = "from_station")
    private String from;

    @Column(name = "to_station")
    private String to;

    private int status;

    private String price;

    public Order(){
        boughtDate = StringUtils.Date2String(new Date(System.currentTimeMillis()));
        travelDate = StringUtils.Date2String(new Date(123456789));
        trainNumber = "G1235";
        coachNumber = 5;
        seatClass = SeatClass.FIRSTCLASS.getCode();
        seatNumber = "1";
        from = "shanghai";
        to = "taiyuan";
        status = OrderStatus.PAID.getCode();
        price = "0.0";
    }

    @Override
    public boolean equals(Object obj) {
        if (this == obj) {
            return true;
        }
        if (obj == null) {
            return false;
        }
        if (getClass() != obj.getClass()) {
            return false;
        }
        Order other = (Order) obj;
        return getBoughtDate().equals(other.getBoughtDate())
                && getBoughtDate().equals(other.getTravelDate())
                && getTravelTime().equals(other.getTravelTime())
                && accountId .equals( other.getAccountId() )
                && contactsName.equals(other.getContactsName())
                && contactsDocumentNumber.equals(other.getContactsDocumentNumber())
                && documentType == other.getDocumentType()
                && trainNumber.equals(other.getTrainNumber())
                && coachNumber == other.getCoachNumber()
                && seatClass == other.getSeatClass()
                && seatNumber .equals(other.getSeatNumber())
                && from.equals(other.getFrom())
                && to.equals(other.getTo())
                && status == other.getStatus()
                && price.equals(other.price);
    }

    @Override
    public int hashCode() {
        int result = 17;
        result = 31 * result + (id == null ? 0 : id.hashCode());
        return result;
    }

}


// Node: repos/cloned_ms_repos/train-ticket/ts-order-other-service/src/main/java/other/entity/Order.java:Order.<init>
package delivery.entity;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import lombok.AllArgsConstructor;
import lombok.Data;
import org.hibernate.annotations.GeneratorType;
import org.hibernate.annotations.GenericGenerator;
import org.hibernate.annotations.GenericGenerators;

import javax.persistence.Column;
import javax.persistence.GeneratedValue;
import javax.persistence.Id;
import javax.persistence.Entity;
import java.util.UUID;

@Data
@AllArgsConstructor
@Entity
@GenericGenerator(name = "jpa-uuid", strategy = "org.hibernate.id.UUIDGenerator")
@JsonIgnoreProperties(ignoreUnknown = true)
public class Delivery {
    public Delivery() {
        //Default Constructor
    }

    @Id
    @GeneratedValue(generator = "jpa-uuid")
    @Column(length = 36)
    private String id;

    private UUID orderId;
    private String foodName;
    private String storeName;
    private String stationName;
}


// Node: repos/cloned_ms_repos/train-ticket/ts-delivery-service/src/main/java/delivery/entity/Delivery.java:Delivery.<init>
package assurance.entity;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import lombok.Data;
import org.hibernate.annotations.GenericGenerator;

import javax.persistence.*;
import javax.validation.constraints.NotNull;
import java.util.UUID;

/**
 * @author fdse
 */
@Data
@Entity
@JsonIgnoreProperties(ignoreUnknown = true)
public class Assurance {

    @Id
    @Column(name = "assurance_id")
    private String id;  //主键

    /**
     * which order the assurance is related to
     */
    @NotNull
    private String orderId;  //这个保险关联的订单

    /**
     * the type of assurance
     */
    @Enumerated(EnumType.STRING)
    @Column(name = "assurance_type")
    private AssuranceType type;

    public Assurance(){
        this.orderId = UUID.randomUUID().toString();
    }

    public Assurance(String id, String orderId, AssuranceType type){
        this.id = id;
        this.orderId = orderId;
        this.type = type;
    }

}


// Node: repos/cloned_ms_repos/train-ticket/ts-assurance-service/src/main/java/assurance/entity/Assurance.java:Assurance.<init>
// Node: Enumerated
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



package travel2.entity;

import edu.fudan.common.entity.TripId;
import edu.fudan.common.util.StringUtils;
import lombok.Data;
import org.hibernate.annotations.GenericGenerator;

import javax.persistence.*;
import javax.validation.Valid;
import javax.validation.constraints.NotNull;
import java.util.Date;

/**
 * @author fdse
 */
@Data
@Entity
@Table(name = "trip2")
@GenericGenerator(name = "jpa-uuid", strategy = "org.hibernate.id.UUIDGenerator")
public class
Trip {
    @Valid
    @Id
    @GeneratedValue(generator = "jpa-uuid")
    @Column(length = 36)
    private String id;

    @Embedded
    private TripId tripId;

    @Valid
    @NotNull
    private String trainTypeName;

    private String routeId;


    @Valid
    @NotNull
    private String startStationName;

    @Valid
    private String stationsName;

    @Valid
    @NotNull
    private String terminalStationName;

    @Valid
    @NotNull
    private String startTime;

    @Valid
    @NotNull
    private String endTime;

    public Trip(edu.fudan.common.entity.TripId tripId, String trainTypeName, String startStationName, String stationsName, String terminalStationName, String startTime, String endTime) {
        this.tripId = tripId;
        this.trainTypeName = trainTypeName;
        this.startStationName = StringUtils.String2Lower(startStationName);
        this.stationsName = StringUtils.String2Lower(stationsName);
        this.terminalStationName = StringUtils.String2Lower(terminalStationName);
        this.startTime = startTime;
        this.endTime = endTime;
    }

    public Trip(TripId tripId, String trainTypeName, String routeId) {
        this.tripId = tripId;
        this.trainTypeName = trainTypeName;
        this.routeId = routeId;
        this.startStationName = "";
        this.terminalStationName = "";
        this.startTime = "";
        this.endTime = "";
    }

    public Trip(){
        //Default Constructor
        this.trainTypeName = "";
        this.startStationName = "";
        this.terminalStationName = "";
        this.startTime = "";
        this.endTime = "";
    }

}

// Node: repos/cloned_ms_repos/train-ticket/ts-travel2-service/src/main/java/travel2/entity/Trip.java:Trip.<init>
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


package order.entity;

import lombok.AllArgsConstructor;
import lombok.Data;
import org.hibernate.annotations.GenericGenerator;

import javax.persistence.Column;
import javax.persistence.GeneratedValue;
import java.util.UUID;

/**
 * @author fdse
 */
@Data
@AllArgsConstructor
@GenericGenerator(name = "jpa-uuid", strategy = "org.hibernate.id.UUIDGenerator")
public class OrderAlterInfo {

    @GeneratedValue(generator = "jpa-uuid")
    @Column(length = 36)
    private String accountId;

    @GeneratedValue(generator = "jpa-uuid")
    @Column(length = 36)
    private String previousOrderId;

    private String loginToken;

    private Order newOrderInfo;

    public OrderAlterInfo(){
        newOrderInfo = new Order();
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-order-service/src/main/java/order/entity/OrderAlterInfo.java:OrderAlterInfo.<init>
package order.entity;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import edu.fudan.common.entity.OrderStatus;
import edu.fudan.common.entity.SeatClass;
import edu.fudan.common.util.StringUtils;
import lombok.Data;
import lombok.ToString;
import org.hibernate.annotations.GenericGenerator;

import javax.persistence.*;
import java.util.Date;

import edu.fudan.common.entity.SeatClass;

/**
 * @author fdse
 */
@Data
@Table(name = "orders")
@Entity
@GenericGenerator(name = "jpa-uuid", strategy = "org.hibernate.id.UUIDGenerator")
@ToString
@JsonIgnoreProperties(ignoreUnknown = true)
public class Order {

    @Id
    @Column(length = 36)
    @GeneratedValue(generator = "jpa-uuid")
    private String id;

    private String boughtDate;


    private String travelDate;


    private String travelTime;

    /**
     * Which Account Bought it
     */
    @Column(length = 36)
    private String accountId;

    /**
     * Tickets bought for whom....
     */
    private String contactsName;

    private int documentType;

    private String contactsDocumentNumber;

    private String trainNumber;

    private int coachNumber;

    private int seatClass;

    private String seatNumber;

    @Column(name = "from_station")
    private String from;

    @Column(name = "to_station")
    private String to;

    private int status;

    private String price;



    public Order(){
        boughtDate = StringUtils.Date2String(new Date(System.currentTimeMillis()));
        travelDate = StringUtils.Date2String(new Date(123456789));
        trainNumber = "G1235";
        coachNumber = 5;
        seatClass = SeatClass.FIRSTCLASS.getCode();
        seatNumber = "1";
        from = "shanghai";
        to = "taiyuan";
        status = OrderStatus.PAID.getCode();
        price = "0.0";
    }

    @Override
    public boolean equals(Object obj) {
        if (this == obj) {
            return true;
        }
        if (obj == null) {
            return false;
        }
        if (getClass() != obj.getClass()) {
            return false;
        }
        Order other = (Order) obj;
        return getBoughtDate().equals(other.getBoughtDate())
                && getBoughtDate().equals(other.getTravelDate())
                && getTravelTime().equals(other.getTravelTime())
                && accountId .equals( other.getAccountId() )
                && contactsName.equals(other.getContactsName())
                && contactsDocumentNumber.equals(other.getContactsDocumentNumber())
                && documentType == other.getDocumentType()
                && trainNumber.equals(other.getTrainNumber())
                && coachNumber == other.getCoachNumber()
                && seatClass == other.getSeatClass()
                && seatNumber .equals(other.getSeatNumber())
                && from.equals(other.getFrom())
                && to.equals(other.getTo())
                && status == other.getStatus()
                && price.equals(other.price);
    }

    @Override
    public int hashCode() {
        int result = 17;
        result = 31 * result + (id == null ? 0 : id.hashCode());
        return result;
    }

}


// Node: repos/cloned_ms_repos/train-ticket/ts-order-service/src/main/java/order/entity/Order.java:Order.<init>
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

import edu.fudan.common.entity.TripId;
import edu.fudan.common.util.StringUtils;
import lombok.Data;
import org.hibernate.annotations.GenericGenerator;


import javax.persistence.*;
import javax.validation.Valid;
import javax.validation.constraints.NotNull;
import java.util.Date;
import java.util.UUID;

/**
 * @author fdse
 */
@Data
@Entity
@GenericGenerator(name = "jpa-uuid", strategy = "org.hibernate.id.UUIDGenerator")
public class Trip {
    @Valid
    @Id
    @GeneratedValue(generator = "jpa-uuid")
    @Column(length = 36)
    private String id;

    @Embedded
    private TripId tripId;

    @Valid
    @NotNull
    private String trainTypeName;

    private String routeId;


    @Valid
    @NotNull
    private String startStationName;

    @Valid
    private String stationsName;

    @Valid
    @NotNull
    private String terminalStationName;

    @Valid
    @NotNull
    private String startTime;

    @Valid
    @NotNull
    private String endTime;

    public Trip(edu.fudan.common.entity.TripId tripId, String trainTypeName, String startStationName, String stationsName, String terminalStationName, String startTime, String endTime) {
        this.tripId = tripId;
        this.trainTypeName = trainTypeName;
        this.startStationName = StringUtils.String2Lower(startStationName);
        this.stationsName = StringUtils.String2Lower(stationsName);
        this.terminalStationName = StringUtils.String2Lower(terminalStationName);
        this.startTime = startTime;
        this.endTime = endTime;
    }

    public Trip(TripId tripId, String trainTypeName, String routeId) {
        this.tripId = tripId;
        this.trainTypeName = trainTypeName;
        this.routeId = routeId;
        this.startStationName = "";
        this.terminalStationName = "";
        this.startTime = "";
        this.endTime = "";
    }

    public Trip(){
        //Default Constructor
        this.trainTypeName = "";
        this.startStationName = "";
        this.terminalStationName = "";
        this.startTime = "";
        this.endTime = "";
    }

}

// Node: repos/cloned_ms_repos/train-ticket/ts-travel-service/src/main/java/travel/entity/Trip.java:Trip.<init>
package train.entity;

import lombok.Data;
import lombok.NonNull;
import org.hibernate.annotations.GenericGenerator;

import javax.persistence.Column;
import javax.persistence.GeneratedValue;
import javax.persistence.Id;

import javax.persistence.Entity;

import javax.validation.Valid;
import javax.validation.constraints.NotNull;

@Data
@Entity
@GenericGenerator(name = "jpa-uuid", strategy = "org.hibernate.id.UUIDGenerator")
public class TrainType {
    @Id
    @GeneratedValue(generator = "jpa-uuid")
    @Column(length = 36)
    private String id;

    @NotNull
    @Column(name="name", unique = true)
    private String name;

    @Valid
    @Column(name = "economy_class")
    private int economyClass;
    @Valid
    @Column(name = "confort_class")
    private int confortClass;
    @Column(name = "average_speed")
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


// Node: repos/cloned_ms_repos/train-ticket/ts-train-service/src/main/java/train/entity/TrainType.java:TrainType.<init>
package consignprice.entity;

import lombok.AllArgsConstructor;
import lombok.Data;
import org.hibernate.annotations.GenericGenerator;

import javax.persistence.*;

import java.util.UUID;

/**
 * @author fdse
 */
@Data
@AllArgsConstructor
@Entity
@GenericGenerator(name = "jpa-uuid", strategy = "org.hibernate.id.UUIDGenerator")
@Table(name="consign_price")
public class ConsignPrice {
    @Id
    @GeneratedValue(generator = "jpa-uuid")
    @Column(length = 36)
    private String id;
    @Column(name = "idx",unique = true)
    private int index;
    @Column(name = "initial_weight")
    private double initialWeight;
    @Column(name = "initial_price")
    private double initialPrice;
    @Column(name = "within_price")
    private double withinPrice;
    @Column(name = "beyond_price")
    private double beyondPrice;

    public ConsignPrice(){
        //Default Constructor
    }

}


// Node: repos/cloned_ms_repos/train-ticket/ts-consign-price-service/src/main/java/consignprice/entity/ConsignPrice.java:ConsignPrice.<init>
package inside_payment.entity;

import lombok.Data;
import org.hibernate.annotations.GenericGenerator;

import javax.persistence.*;
//import org.springframework.data.mongodb.core.mapping.Document;

import javax.validation.Valid;
import javax.validation.constraints.NotNull;
import java.util.UUID;

/**
 * @author fdse
 */
@Data
@Entity
@GenericGenerator(name = "jpa-uuid", strategy = "org.hibernate.id.UUIDGenerator")
@Table(name="inside_payment")
public class Payment {
    @Id
    @NotNull
    @Column(length = 36)
    @GeneratedValue(generator = "jpa-uuid")
    private String id;

    @NotNull
    @Valid
    @Column(length = 36)
    private String orderId;

    @NotNull
    @Valid
    @Column(length = 36)
    private String userId;

    @NotNull
    @Valid
    private String price;

    @NotNull
    @Valid
    @Enumerated(EnumType.STRING)
    private PaymentType type;

    public Payment(){
        this.orderId = "";
        this.userId = "";
        this.price = "";
    }

}


// Node: repos/cloned_ms_repos/train-ticket/ts-inside-payment-service/src/main/java/inside_payment/entity/Payment.java:Payment.<init>
package inside_payment.entity;

import lombok.Data;
import org.hibernate.annotations.GenericGenerator;

import javax.persistence.*;
//import org.springframework.data.mongodb.core.mapping.Document;

import javax.validation.Valid;
import javax.validation.constraints.NotNull;
import java.util.UUID;

/**
 * @author fdse
 */
@Data
@Entity
@GenericGenerator(name = "jpa-uuid", strategy = "org.hibernate.id.UUIDGenerator")
@Table(name = "inside_money")
public class Money {

    @Valid
    @NotNull
    @Id
    @Column(length = 36)
    @GeneratedValue(generator = "jpa-uuid")
    private String id;

    @Valid
    @NotNull
    @Column(length = 36)
    private String userId;

    @Valid
    @NotNull
    private String money; //NOSONAR

    @Valid
    @NotNull
    @Enumerated(EnumType.STRING)
    private MoneyType type;

    public Money(){
        this.userId = "";
        this.money = "";

    }

}


// Node: repos/cloned_ms_repos/train-ticket/ts-inside-payment-service/src/main/java/inside_payment/entity/Money.java:Money.<init>
package foodsearch.entity;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import lombok.AllArgsConstructor;
import lombok.Data;
import org.hibernate.annotations.GenericGenerator;

import javax.persistence.Column;
import javax.persistence.GeneratedValue;
import javax.persistence.Id;
import javax.persistence.Entity;
import java.util.UUID;

@Data
@AllArgsConstructor
@Entity
@JsonIgnoreProperties(ignoreUnknown = true)
@GenericGenerator(name = "jpa-uuid", strategy = "org.hibernate.id.UUIDGenerator")
public class FoodOrder {

    @Id
    @GeneratedValue(generator = "jpa-uuid")
    @Column(length = 36)
    private String id;

    private String orderId;

    //1:train food;2:food store
    private int foodType;

    private String stationName;

    private String storeName;

    private String foodName;

    private double price;

    public FoodOrder(){
        //Default Constructor
    }

}


// Node: repos/cloned_ms_repos/train-ticket/ts-food-service/src/main/java/foodsearch/entity/FoodOrder.java:FoodOrder.<init>
package route.entity;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import io.swagger.models.auth.In;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.hibernate.annotations.GenericGenerator;

import javax.persistence.*;

import java.util.List;
import java.util.UUID;

/**
 * @author fdse
 */
@Data
@Entity
@JsonIgnoreProperties(ignoreUnknown = true)
@GenericGenerator(name = "jpa-uuid", strategy = "org.hibernate.id.UUIDGenerator")
public class Route {

    @Id
    @Column(length = 36)
    private String id;

    @ElementCollection(targetClass = String.class)
    @OrderColumn
    private List<String> stations;

    @ElementCollection(targetClass = Integer.class)
    @OrderColumn
    private List<Integer> distances;

    private String startStation;

    private String endStation;

    public Route(){
        this.id = UUID.randomUUID().toString();
    }

    public Route(String id, List<String> stations, List<Integer> distances, String startStation, String endStation) {
        this.id = id;
        this.stations = stations;
        this.distances = distances;
        this.startStation = startStation;
        this.endStation = endStation;
    }

    public Route(List<String> stations, List<Integer> distances, String startStation, String endStation) {
        this.id = UUID.randomUUID().toString();
        this.stations = stations;
        this.distances = distances;
        this.startStation = startStation;
        this.endStation = endStation;
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-route-service/src/main/java/route/entity/Route.java:Route.<init>
// Node: ElementCollection
package consign.entity;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.hibernate.annotations.GenericGenerator;

import javax.persistence.*;


/**
 * @author fdse
 */
@Data
@AllArgsConstructor
@NoArgsConstructor
@GenericGenerator(name="jpa-uuid",strategy ="uuid")
public class Consign {
    @Id
    @GeneratedValue(generator = "jpa-uuid")
    @Column(length = 36)
    private String id;        //id主键改成String类型的 自定义生成策略
    private String orderId;   //这次托运关联订单
    private String accountId;  //这次托运关联的账户

    private String handleDate;
    private String targetDate;
    private String from;
    private String to;
    private String consignee;
    private String phone;
    private double weight;
    private boolean isWithin;


}


// Node: repos/cloned_ms_repos/train-ticket/ts-consign-service/src/main/java/consign/entity/Consign.java:Consign.<init>
package consign.entity;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import javax.persistence.*;

/**
 * @author fdse
 */
@Data
@AllArgsConstructor
@NoArgsConstructor
@Entity
@JsonIgnoreProperties(ignoreUnknown = true)
@Table(schema = "ts-consign-mysql")
public class ConsignRecord {

    @Id
    @Column(name = "consign_record_id")
    private String id;
    private String orderId;
    @Column(name = "user_id")
    private String accountId;
    private String handleDate;
    private String targetDate;
    @Column(name = "from_place")
    private String from;
    @Column(name = "to_place")
    private String to;
    private String consignee;
    @Column(name = "consign_record_phone")
    private String phone;
    private double weight;
    @Column(name = "consign_record_price")
    private double price;

}


// Node: repos/cloned_ms_repos/train-ticket/ts-consign-service/src/main/java/consign/entity/ConsignRecord.java:ConsignRecord.<init>
// Node: checkTime
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


package rebook.entity;

import edu.fudan.common.util.StringUtils;
import lombok.Data;

import javax.validation.Valid;
import javax.validation.constraints.NotNull;
import java.util.Date;

/**
 * @author fdse
 */
@Data
public class RebookInfo {

    @Valid
    @NotNull
    private String loginId;

    @Valid
    @NotNull
    private String orderId;

    @Valid
    @NotNull
    private String oldTripId;

    @Valid
    @NotNull
    private String tripId;

    @Valid
    @NotNull
    private int seatType;

    @Valid
    @NotNull
    private String date;

    public RebookInfo(){
        //Default Constructor
        this.loginId = "";
        this.orderId = "";
        this.oldTripId = "";
        this.tripId = "";
        this.seatType = 0;
        this.date = StringUtils.Date2String(new Date());
    }

}


// Node: repos/cloned_ms_repos/train-ticket/ts-rebook-service/src/main/java/rebook/entity/RebookInfo.java:RebookInfo.<init>
// Node: nanoTime


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


// Node: stop
// Node: max
// Node: getAccumulatedMillis
// Node: getAccumulatedMicros
// Node: Log


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


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/Log.java:Log.<init>
// Node: JsonProperty
// Node: NullPointerException
package trainFood.entity;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import edu.fudan.common.entity.Food;
import lombok.Data;
import org.hibernate.annotations.GenericGenerator;

import javax.persistence.*;
import javax.validation.Valid;
import javax.validation.constraints.NotNull;
import java.util.List;
import java.util.UUID;

@Data
@Entity
@GenericGenerator(name = "jpa-uuid", strategy = "org.hibernate.id.UUIDGenerator")
@JsonIgnoreProperties(ignoreUnknown = true)
public class TrainFood {

    @Id
    @GeneratedValue(generator = "jpa-uuid")
    @Column(length = 36)
    private String id;

    @NotNull
    @Column(unique = true)
    private String tripId;

    @ElementCollection(targetClass = Food.class)
    @CollectionTable(name = "train_food_list", joinColumns = @JoinColumn(name = "trip_id"))
    private List<Food> foodList;

    public TrainFood(){
        //Default Constructor
        this.tripId = "";
    }

}


// Node: repos/cloned_ms_repos/train-ticket/ts-train-food-service/src/main/java/trainFood/entity/TrainFood.java:TrainFood.<init>
package fdse.microservice.entity;

import lombok.Data;
import org.hibernate.annotations.GenericGenerator;

import javax.persistence.Column;
import javax.persistence.Entity;
import javax.persistence.GeneratedValue;
import javax.persistence.Id;
import javax.validation.Valid;
import javax.validation.constraints.NotNull;
import java.util.Locale;
import java.util.UUID;

@Data
@Entity
@GenericGenerator(name = "jpa-uuid", strategy = "org.hibernate.id.UUIDGenerator")
public class Station {
    @Id
    @GeneratedValue(generator = "jpa-uuid")
    @Column(length = 36)
    private String id;

    @Valid
    @NotNull
    @Column(unique = true)
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


// Node: repos/cloned_ms_repos/train-ticket/ts-station-service/src/main/java/fdse/microservice/entity/Station.java:Station.<init>
package security.entity;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import lombok.Data;
import org.hibernate.annotations.GenericGenerator;

import javax.persistence.Column;
import javax.persistence.GeneratedValue;
import javax.persistence.Id;
import javax.persistence.Entity;

import java.util.UUID;

/**
 * @author fdse
 */
@Data
@Entity
@GenericGenerator(name = "jpa-uuid", strategy = "org.hibernate.id.UUIDGenerator")
@JsonIgnoreProperties(ignoreUnknown = true)
public class SecurityConfig {

    @Id
    @GeneratedValue(generator = "jpa-uuid")
    @Column(length = 36)
    private String id;

    private String name;

    private String value;

    private String description;

    public SecurityConfig() {
        //Default Constructor
    }

}


// Node: repos/cloned_ms_repos/train-ticket/ts-security-service/src/main/java/security/entity/SecurityConfig.java:SecurityConfig.<init>
package food_delivery.entity;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.hibernate.annotations.GenericGenerator;

import javax.persistence.*;
import java.util.List;
import edu.fudan.common.entity.Food;

@Data
@Entity
@GenericGenerator(name = "jpa-uuid", strategy = "uuid")
@JsonIgnoreProperties(ignoreUnknown = true)
@AllArgsConstructor
@NoArgsConstructor
public class FoodDeliveryOrder {

    @Id
    @GeneratedValue(generator = "jpa-uuid")
    @Column(length = 36)
    private String id;

    private String stationFoodStoreId;

    @ElementCollection(targetClass = Food.class)
    private List<Food> foodList;

    private String tripId;

    private int seatNo;

    private String createdTime;

    private String deliveryTime;

    private double deliveryFee;
}


// Node: repos/cloned_ms_repos/train-ticket/ts-food-delivery-service/src/main/java/food_delivery/entity/FoodDeliveryOrder.java:FoodDeliveryOrder.<init>
package food_delivery.entity;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;
import edu.fudan.common.entity.Food;

@Data
@NoArgsConstructor
@AllArgsConstructor
@JsonIgnoreProperties(ignoreUnknown = true)
public class StationFoodStoreInfo {

    private String id;

    private String stationId;

    private String storeName;

    private String telephone;

    private String businessTime;

    private double deliveryFee;

    private List<Food> foodList;

}


// Node: repos/cloned_ms_repos/train-ticket/ts-food-delivery-service/src/main/java/food_delivery/entity/StationFoodStoreInfo.java:StationFoodStoreInfo.<init>
package contacts.entity;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import lombok.AllArgsConstructor;
import lombok.Data;

import javax.persistence.*;

import org.hibernate.annotations.GenericGenerator;

import java.util.UUID;

/**
 * @author fdse
 */
@Data
@AllArgsConstructor
@Entity
@GenericGenerator(name = "jpa-uuid", strategy = "org.hibernate.id.UUIDGenerator")
@JsonIgnoreProperties(ignoreUnknown = true)
@Table(indexes = {@Index(name = "account_document_idx", columnList = "account_id, document_number, document_type", unique = true)})
public class Contacts {

    @Id
//    private UUID id;
    @GeneratedValue(generator = "jpa-uuid")
    @Column(length = 36)
    private String id;
    @Column(name = "account_id")
    private String accountId;

    private String name;
    @Column(name = "document_type")
    private int documentType;
    @Column(name = "document_number")
    private String documentNumber;
    @Column(name = "phone_number")
    private String phoneNumber;

    public Contacts() {
        //Default Constructor
    }

    @Override
    public boolean equals(Object obj) {
        if (this == obj) {
            return true;
        }
        if (obj == null) {
            return false;
        }
        if (getClass() != obj.getClass()) {
            return false;
        }
        Contacts other = (Contacts) obj;
        return name.equals(other.getName())
                && accountId .equals( other.getAccountId() )
                && documentNumber.equals(other.getDocumentNumber())
                && phoneNumber.equals(other.getPhoneNumber())
                && documentType == other.getDocumentType();
    }

    @Override
    public int hashCode() {
        int result = 17;
        result = 31 * result + (id == null ? 0 : id.hashCode());
        return result;
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-contacts-service/src/main/java/contacts/entity/Contacts.java:Contacts.<init>
package food.entity;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import edu.fudan.common.entity.Food;
import lombok.Data;
import lombok.ToString;
import org.hibernate.annotations.GenericGenerator;

import javax.persistence.*;
import javax.validation.constraints.NotNull;
import java.util.List;

@Data
@Entity
@GenericGenerator(name = "jpa-uuid", strategy = "org.hibernate.id.UUIDGenerator")
@ToString
@JsonIgnoreProperties(ignoreUnknown = true)
@Table(indexes = {@Index(name = "station_store_idx", columnList = "station_name, store_name", unique = true)})
public class StationFoodStore {

    @Id
    @Column(name = "store_id")
    private String id;

    @NotNull
    @Column(name = "station_name")
    private String stationName;

    @Column(name = "store_name")
    private String storeName;

    private String telephone;

    private String businessTime;

    private double deliveryFee;

    @ElementCollection(targetClass = Food.class, fetch = FetchType.EAGER)
    @CollectionTable(name = "station_food_list", joinColumns = @JoinColumn(name = "store_id"))
    private List<Food> foodList;

    public StationFoodStore(){
        //Default Constructor
        this.stationName = "";
    }

}


// Node: repos/cloned_ms_repos/train-ticket/ts-station-food-service/src/main/java/food/entity/StationFoodStore.java:StationFoodStore.<init>
