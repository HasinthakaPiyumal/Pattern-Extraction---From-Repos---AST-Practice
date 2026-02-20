// Cluster 15

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


// Node: getClass
// Node: hashCode
package waitorder.entity;

import edu.fudan.common.entity.OrderStatus;

public enum WaitListOrderStatus {
    /**
     * not paid
     */
    NOTPAID   (0,"Not Paid"),
    /**
     * paid and not collected
     */
    PAID      (1,"Paid & Not Collected"),
    /**
     * collected
     */
    COLLECTED (2,"Collected"),
    /**
     * cancel
     */
    CANCEL    (3,"Cancel"),
    /**
     * refunded
     */
    REFUNDS   (4,"Refunded"),
    /**
     * expired
     */
    EXPIRED   (5, "Expired");



    private int code;
    private String name;

    WaitListOrderStatus(int code, String name){
        this.code = code;
        this.name = name;
    }

    public int getCode(){
        return code;
    }

    public String getName() {
        return name;
    }

    public static String getNameByCode(int code){
        OrderStatus[] orderStatusSet = OrderStatus.values();
        for(OrderStatus orderStatus : orderStatusSet){
            if(orderStatus.getCode() == code){
                return orderStatus.getName();
            }
        }
        return orderStatusSet[0].getName();
    }
}


// Node: getName
package edu.fudan.common.util;

import java.text.SimpleDateFormat;
import java.util.Locale;
import java.util.Date;

public class StringUtils {
    public static String String2Lower(String str){
        if(str == null || str.isEmpty()) {
            return str;
        }
        return str.replace(" ", "").toLowerCase(Locale.ROOT);
    }

    public static Date String2Date(String str){
        SimpleDateFormat formatter;
        if(str.length() > 10){
            formatter = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
        }else{
            formatter = new SimpleDateFormat("yyyy-MM-dd");
        }

        try{
            Date d = formatter.parse(str);
            return d;
        }catch(Exception e){
            return new Date(0);
        }
    }

    public static String Date2String(Date date){
        SimpleDateFormat formatter= new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
        return formatter.format(date);
    }
}


// Node: replace
// Node: toLowerCase
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


package edu.fudan.common.entity;

/**
 * @author fdse
 */
public enum DocumentType {

    /**
     * null
     */
    NONE      (0,"Null"),
    /**
     * id card
     */
    ID_CARD   (1,"ID Card"),
    /**
     * passport
     */
    PASSPORT  (2,"Passport"),
    /**
     * other
     */
    OTHER     (3,"Other");

    private int code;
    private String name;

    DocumentType(int code, String name){
        this.code = code;
        this.name = name;
    }

    public int getCode(){
        return code;
    }

    public String getName() {
        return name;
    }

    public static String getNameByCode(int code){
        DocumentType[] documentTypeSet = DocumentType.values();
        for(DocumentType documentType : documentTypeSet){
            if(documentType.getCode() == code){
                return documentType.getName();
            }
        }
        return documentTypeSet[0].getName();
    }
}


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


package edu.fudan.common.entity;

/**
 * @author fdse
 */
public enum Gender {

    /**
     * null
     */
    NONE   (0, "Null"),
    /**
     * male
     */
    MALE   (1, "Male"),
    /**
     * female
     */
    FEMALE (2, "Female"),
    /**
     * other
     */
    OTHER  (3, "Other");

    private int code;
    private String name;

    Gender(int code, String name){
        this.code = code;
        this.name = name;
    }

    public int getCode(){
        return code;
    }

    public String getName() {
        return name;
    }

    public static String getNameByCode(int code){
        Gender[] genderSet = Gender.values();
        for(Gender gender : genderSet){
            if(gender.getCode() == code){
                return gender.getName();
            }
        }
        return genderSet[0].getName();
    }

}


package edu.fudan.common.entity;

import java.io.Serializable;

/**
 * @author fdse
 */
public enum AssuranceType implements Serializable{

    /**
     * traffic accident assurance
     */
    TRAFFIC_ACCIDENT (1, "Traffic Accident Assurance", 3.0);

    /**
     * index of assurance type
     */
    private  int index;
    /**
     * the assurance type name
     */
    private String name;
    /**
     * the price of this type of assurence
     */
    private double price;

     AssuranceType(int index, String name, double price){
         this.index = index;
        this.name = name;
        this.price  = price;
    }

    public int getIndex() {
        return index;
    }

    void setIndex(int index) {
        this.index = index;
    }

    public String getName() {
        return name;
    }

    void setName(String name) {
        this.name = name;
    }

    public double getPrice() {
        return price;
    }

    void setPrice(double price) {
        this.price = price;
    }

    public static AssuranceType getTypeByIndex(int index){
         AssuranceType[] ats = AssuranceType.values();
         for(AssuranceType at : ats){
             if(at.getIndex() == index){
                 return at;
             }
         }
         return null;
    }


}


package edu.fudan.common.entity;

/**
 * @author fdse
 */
public enum SeatClass {

    /**
     * no seat
     */
    NONE        (0,"NoSeat"),
    /**
     * green seat
     */
    BUSINESS    (1,"GreenSeat"),
    /**
     * first class seat
     */
    FIRSTCLASS  (2,"FirstClassSeat"),
    /**
     * second class seat
     */
    SECONDCLASS (3,"SecondClassSeat"),
    /**
     * hard seat
     */
    HARDSEAT    (4,"HardSeat"),
    /**
     * soft seat
     */
    SOFTSEAT    (5,"SoftSeat"),
    /**
     * hard bed
     */
    HARDBED     (6,"HardBed"),
    /**
     * soft bed
     */
    SOFTBED     (7,"SoftBed"),
    /**
     * high soft seat
     */
    HIGHSOFTBED (8,"HighSoftSeat");

    private int code;
    private String name;

    SeatClass(int code, String name){
        this.code = code;
        this.name = name;
    }

    public int getCode(){
        return code;
    }

    public String getName() {
        return name;
    }

    public static String getNameByCode(int code){
        SeatClass[] seatClassSet = SeatClass.values();
        for(SeatClass seatClass : seatClassSet){
            if(seatClass.getCode() == code){
                return seatClass.getName();
            }
        }
        return seatClassSet[0].getName();
    }
}


package edu.fudan.common.entity;

/**
 * @author fdse
 */
public enum OrderStatus {

    /**
     * not paid
     */
    NOTPAID   (0,"Not Paid"),
    /**
     * paid and not collected
     */
    PAID      (1,"Paid & Not Collected"),
    /**
     * collected
     */
    COLLECTED (2,"Collected"),
    /**
     * cancel and rebook
     */
    CHANGE    (3,"Cancel & Rebook"),
    /**
     * cancel
     */
    CANCEL    (4,"Cancel"),
    /**
     * refunded
     */
    REFUNDS   (5,"Refunded"),
    /**
     * used
     */
    USED      (6,"Used");

    private int code;
    private String name;

    OrderStatus(int code, String name){
        this.code = code;
        this.name = name;
    }

    public int getCode(){
        return code;
    }

    public String getName() {
        return name;
    }

    public static String getNameByCode(int code){
        OrderStatus[] orderStatusSet = OrderStatus.values();
        for(OrderStatus orderStatus : orderStatusSet){
            if(orderStatus.getCode() == code){
                return orderStatus.getName();
            }
        }
        return orderStatusSet[0].getName();
    }

}


// Node: doFilter
// Node: getHeader
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


// Node: getHost
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


// Node: getType
package assurance.entity;

import java.io.Serializable;

/**
 * @author fdse
 */
public enum AssuranceType implements Serializable {

    /**
     * Traffic Accident Assurance
     */
    TRAFFIC_ACCIDENT(1, "Traffic Accident Assurance", 3.0);

    /**
     * index of assurance type
     */
    private int index;

    /**
     * the assurance type name
     */
    private String name;

    /**
     * the price of this type of assurence
     */
    private double price;

    AssuranceType(int index, String name, double price) {
        this.index = index;
        this.name = name;
        this.price = price;
    }

    public int getIndex() {
        return index;
    }

    void setIndex(int index) {
        this.index = index;
    }

    public String getName() {
        return name;
    }

    void setName(String name) {
        this.name = name;
    }

    public double getPrice() {
        return price;
    }

    void setPrice(double price) {
        this.price = price;
    }

    public static AssuranceType getTypeByIndex(int index) {
        AssuranceType[] ats = AssuranceType.values();
        for (AssuranceType at : ats) {
            if (at.getIndex() == index) {
                return at;
            }
        }
        return null;
    }
}


// Node: debug
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


// Node: call
// Node: getOutputStream
// Node: setAttribute
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


// Node: getHeaders
// Node: getMethod
// Node: getQueryString
// Node: getRequestURI
// Node: getRequestURL
// Node: getContentType
// Node: getInputStream
// Node: getWriter
// Node: getScheme
// Node: getServerName
// Node: removeAttribute
// Node: isAsyncStarted
// Node: getBufferSize
// Node: flushBuffer
// Node: reset


package org.myproject.ms.monitoring;


public class ChainRunnable implements Runnable {

	
	private static final String DEFAULT_SPAN_NAME = "async";

	private final Chainer tracer;
	private final ItemNamer spanNamer;
	private final Runnable delegate;
	private final String name;
	private final Item parent;

	public ChainRunnable(Chainer tracer, ItemNamer spanNamer, Runnable delegate) {
		this(tracer, spanNamer, delegate, null);
	}

	public ChainRunnable(Chainer tracer, ItemNamer spanNamer, Runnable delegate, String name) {
		this.tracer = tracer;
		this.spanNamer = spanNamer;
		this.delegate = delegate;
		this.name = name;
		this.parent = tracer.getCurrentSpan();
	}

	@Override
	public void run()  {
		Item span = startSpan();
		try {
			this.getDelegate().run();
		}
		finally {
			close(span);
		}
	}

	protected Item startSpan() {
		return this.tracer.createSpan(getSpanName(), this.parent);
	}

	protected String getSpanName() {
		if (this.name != null) {
			return this.name;
		}
		return this.spanNamer.name(this.delegate, DEFAULT_SPAN_NAME);
	}

	protected void close(Item span) {
		// race conditions - check #447
		if (!this.tracer.isTracing()) {
			this.tracer.continueSpan(span);
		}
		this.tracer.close(span);
	}

	protected Item continueSpan(Item span) {
		return this.tracer.continueSpan(span);
	}

	protected Item detachSpan(Item span) {
		if (this.tracer.isTracing()) {
			return this.tracer.detach(span);
		}
		return span;
	}

	public Chainer getTracer() {
		return this.tracer;
	}

	public Runnable getDelegate() {
		return this.delegate;
	}

	public String getName() {
		return this.name;
	}

	public Item getParent() {
		return this.parent;
	}
}


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/ChainRunnable.java:ChainRunnable.<init>
// Node: ChainRunnable
// Node: getCurrentSpan
// Node: startSpan
// Node: getDelegate
// Node: close
// Node: createSpan
// Node: getSpanName
// Node: isTracing
// Node: continueSpan
// Node: detachSpan
// Node: detach
// Node: getTracer
// Node: getParent


package org.myproject.ms.monitoring;


public class NOItemAdjuster implements ItemAdjuster {
	@Override public Item adjust(Item span) {
		return span;
	}
}


// Node: adjust


package org.myproject.ms.monitoring;


public interface ItemAdjuster {
	
	Item adjust(Item span);
}


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/ItemAdjuster.java:ItemAdjuster.<init>


package org.myproject.ms.monitoring;


public interface ItemInjector<T> {
	
	void inject(Item span, T carrier);
}


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/ItemInjector.java:ItemInjector.<init>
// Node: inject


package org.myproject.ms.monitoring;


public class StateItemAdjuster implements ItemAdjuster {
	
	@Override public Item adjust(Item span) {
		System.out.println("-------inside span adjuster-------:" + span.toString());
		return span.toBuilder()
				.tag("state", "mystate")
				.name(span.getName() + "--------------------")
				.build();
	}
}


// Node: toBuilder
// Node: tag
// Node: SuppressWarnings
// Node: emptyList


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


// Node: logEvent
// Node: tags
// Node: hasSavedSpan


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


// Node: getEvent


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


// Node: getHttp
// Node: getHystrix
// Node: getAsync
// Node: getMvc
// Node: getPayload
// Node: getPrefix
// Node: getSize
// Node: getPath
// Node: getUrl
// Node: getCommandKey
// Node: getCommandGroup
// Node: getThreadPoolKey
// Node: getThreadNameKey
// Node: getClassNameKey
// Node: getMethodNameKey
// Node: getControllerClass
// Node: getControllerMethod


package org.myproject.ms.monitoring;


public interface ItemExtractor<T> {
	
	Item joinTrace(T carrier);
}


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/ItemExtractor.java:ItemExtractor.<init>
// Node: joinTrace


package org.myproject.ms.monitoring;

import java.util.concurrent.Callable;


public class ChainCallable<V> implements Callable<V> {

	private final Chainer tracer;
	private final ItemNamer spanNamer;
	private final Callable<V> delegate;
	private final String name;
	private final Item parent;

	public ChainCallable(Chainer tracer,  ItemNamer spanNamer, Callable<V> delegate) {
		this(tracer, spanNamer, delegate, null);
	}

	public ChainCallable(Chainer tracer, ItemNamer spanNamer, Callable<V> delegate, String name) {
		this.tracer = tracer;
		this.spanNamer = spanNamer;
		this.delegate = delegate;
		this.name = name;
		this.parent = tracer.getCurrentSpan();
	}

	@Override
	public V call() throws Exception {
		Item span = startSpan();
		try {
			return this.getDelegate().call();
		}
		finally {
			close(span);
		}
	}

	protected Item startSpan() {
		return this.tracer.createSpan(getSpanName(), this.parent);
	}

	protected String getSpanName() {
		if (this.name != null) {
			return this.name;
		}
		return this.spanNamer.name(this.delegate, "async");
	}

	protected void close(Item span) {
		this.tracer.close(span);
	}

	protected Item continueSpan(Item span) {
		return this.tracer.continueSpan(span);
	}

	protected Item detachSpan(Item span) {
		return this.tracer.detach(span);
	}

	public Chainer getTracer() {
		return this.tracer;
	}

	public Callable<V> getDelegate() {
		return this.delegate;
	}

	public String getName() {
		return this.name;
	}

	public Item getParent() {
		return this.parent;
	}

}


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/ChainCallable.java:ChainCallable.<init>
// Node: ChainCallable


package org.myproject.ms.monitoring;


public interface ItemAccessor {

	
	Item getCurrentSpan();

	
	boolean isTracing();

}


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/ItemAccessor.java:ItemAccessor.<init>


package org.myproject.ms.monitoring;

import java.util.concurrent.Callable;


public interface Chainer extends ItemAccessor {

	
	Item createSpan(String name);

	
	Item createSpan(String name, Item parent);

	
	Item createSpan(String name, Sampler sampler);

	
	Item continueSpan(Item span);

	
	void addTag(String key, String value);

	
	Item detach(Item span);

	
	Item close(Item span);

	
	<V> Callable<V> wrap(Callable<V> callable);

	
	Runnable wrap(Runnable runnable);
}


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/Chainer.java:Chainer.<init>
// Node: addTag


package org.myproject.ms.monitoring;

import org.springframework.core.annotation.AnnotationUtils;


public class DefaultItemNamer implements ItemNamer {

	@Override
	public String name(Object object, String defaultValue) {
		ItemName annotation = AnnotationUtils
				.findAnnotation(object.getClass(), ItemName.class);
		String spanName = annotation != null ? annotation.value() : object.toString();
		// If there is no overridden toString method we'll put a constant value
		if (isDefaultToString(object, spanName)) {
			return defaultValue;
		}
		return spanName;
	}

	private static boolean isDefaultToString(Object delegate, String spanName) {
		return (delegate.getClass().getName() + "@" +
				Integer.toHexString(delegate.hashCode())).equals(spanName);
	}
}


// Node: findAnnotation
// Node: isDefaultToString
// Node: toHexString


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


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/trace/ICHolder.java:ICHolder.<init>
// Node: getLog


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


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/trace/DChainer.java:DChainer.<init>
// Node: lookup
// Node: lookupClass
// Node: matches
// Node: getExceptionMessage
// Node: toLowerHyphen


package org.myproject.ms.monitoring.mtc;

import java.lang.invoke.MethodHandles;

import org.apache.commons.logging.Log;
import org.apache.commons.logging.LogFactory;
import org.springframework.boot.actuate.metrics.CounterService;
import org.springframework.boot.autoconfigure.condition.ConditionOutcome;
import org.springframework.boot.autoconfigure.condition.ConditionalOnBean;
import org.springframework.boot.autoconfigure.condition.ConditionalOnClass;
import org.springframework.boot.autoconfigure.condition.ConditionalOnMissingBean;
import org.springframework.boot.autoconfigure.condition.ConditionalOnMissingClass;
import org.springframework.boot.autoconfigure.condition.SpringBootCondition;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.ConditionContext;
import org.springframework.context.annotation.Conditional;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.type.AnnotatedTypeMetadata;


@Configuration
@Conditional(ChainMetricsAtcfg.PickMetricIfMetricsIsMissing.class)
@EnableConfigurationProperties
public class ChainMetricsAtcfg {

	@Bean
	@ConditionalOnMissingBean
	public SMProp sleuthMetricProperties() {
		return new SMProp();
	}

	@Configuration
	@ConditionalOnClass(CounterService.class)
	@ConditionalOnMissingBean(ItemMetricReporter.class)
	protected static class CounterServiceSpanReporterConfig {
		@Bean
		@ConditionalOnBean(CounterService.class)
		public ItemMetricReporter spanReporterCounterService(CounterService counterService,
				SMProp sleuthMetricProperties) {
			return new CSBSMRep(sleuthMetricProperties.getSpan().getAcceptedName(),
					sleuthMetricProperties.getSpan().getDroppedName(), counterService);
		}

		@Bean
		@ConditionalOnMissingBean(CounterService.class)
		public ItemMetricReporter noOpSpanReporterCounterService() {
			return new NOIMRep();
		}
	}

	@Bean
	@ConditionalOnMissingClass("org.springframework.boot.actuate.metrics.CounterService")
	@ConditionalOnMissingBean(ItemMetricReporter.class)
	public ItemMetricReporter noOpSpanReporterCounterService() {
		return new NOIMRep();
	}

	static class PickMetricIfMetricsIsMissing extends SpringBootCondition {

		private static final Log log = LogFactory.getLog(MethodHandles.lookup().lookupClass());

		static final String DEPRECATED_SPRING_SLEUTH_METRICS_ENABLED = "spring.sleuth.metrics.enabled";
		static final String SPRING_SLEUTH_METRIC_ENABLED = "spring.sleuth.metric.enabled";

		@Override
		public ConditionOutcome getMatchOutcome(ConditionContext context, AnnotatedTypeMetadata metadata) {
			Boolean oldValue = context.getEnvironment().getProperty(DEPRECATED_SPRING_SLEUTH_METRICS_ENABLED, Boolean.class);
			Boolean newValue = context.getEnvironment().getProperty(SPRING_SLEUTH_METRIC_ENABLED, Boolean.class);
			if (oldValue != null) {
				log.warn("You're using an old version of the metrics property. Instead of using [" +
						DEPRECATED_SPRING_SLEUTH_METRICS_ENABLED + "] please use [" + SPRING_SLEUTH_METRIC_ENABLED + "]");
				return matchCondition(oldValue, DEPRECATED_SPRING_SLEUTH_METRICS_ENABLED);
			}
			if (newValue != null) {
				return matchCondition(newValue, SPRING_SLEUTH_METRIC_ENABLED);
			}
			return ConditionOutcome.match("No property was passed - assuming that metrics are enabled.");
		}

		private ConditionOutcome matchCondition(Boolean value, String property) {
			if (Boolean.TRUE.equals(value)) {
				return ConditionOutcome.match();
			}
			return ConditionOutcome.noMatch("Property [" + property + "] is set to false.");
		}
	}
}


// Node: noOpSpanReporterCounterService
// Node: NOIMRep

package org.myproject.ms.monitoring.antn;


class SleuthAnnotatedParameter {

	int parameterIndex;

	SpanTag annotation;

	Object argument;

	SleuthAnnotatedParameter(int parameterIndex, SpanTag annotation,
			Object argument) {
		this.parameterIndex = parameterIndex;
		this.annotation = annotation;
		this.argument = argument;
	}

}


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/antn/SleuthAnnotatedParameter.java:SleuthAnnotatedParameter.<init>
// Node: SleuthAnnotatedParameter


package org.myproject.ms.monitoring.antn;

import java.lang.annotation.Annotation;
import java.lang.invoke.MethodHandles;
import java.lang.reflect.Method;
import java.util.ArrayList;
import java.util.List;

import org.apache.commons.logging.Log;
import org.apache.commons.logging.LogFactory;
import org.springframework.core.annotation.AnnotationUtils;


class SleuthAnnotationUtils {

	private static final Log log = LogFactory.getLog(MethodHandles.lookup().lookupClass());

	static boolean isMethodAnnotated(Method method) {
		return findAnnotation(method, NewSpan.class) != null ||
				findAnnotation(method, ContinueSpan.class) != null;
	}

	static boolean hasAnnotatedParams(Method method, Object[] args) {
		return !findAnnotatedParameters(method, args).isEmpty();
	}

	static List<SleuthAnnotatedParameter> findAnnotatedParameters(Method method, Object[] args) {
		Annotation[][] parameters = method.getParameterAnnotations();
		List<SleuthAnnotatedParameter> result = new ArrayList<>();
		int i = 0;
		for (Annotation[] parameter : parameters) {
			for (Annotation parameter2 : parameter) {
				if (parameter2 instanceof SpanTag) {
					result.add(new SleuthAnnotatedParameter(i, (SpanTag) parameter2, args[i]));
				}
			}
			i++;
		}
		return result;
	}

	
	static <T extends Annotation> T findAnnotation(Method method, Class<T> clazz) {
		T annotation = AnnotationUtils.findAnnotation(method, clazz);
		if (annotation == null) {
			try {
				annotation = AnnotationUtils.findAnnotation(
						method.getDeclaringClass().getMethod(method.getName(),
								method.getParameterTypes()), clazz);
			} catch (NoSuchMethodException | SecurityException e) {
				if (log.isDebugEnabled()) {
					log.debug("Exception occurred while tyring to find the annotation", e);
				}
			}
		}
		return annotation;
	}
}


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/antn/SleuthAnnotationUtils.java:SleuthAnnotationUtils.<init>
// Node: isMethodAnnotated
// Node: hasAnnotatedParams
// Node: findAnnotatedParameters
// Node: getParameterAnnotations
// Node: getDeclaringClass
// Node: getParameterTypes
// Node: isDebugEnabled


package org.myproject.ms.monitoring.antn;

import java.lang.invoke.MethodHandles;
import java.lang.reflect.Method;
import java.util.Arrays;
import java.util.List;

import org.aopalliance.intercept.MethodInvocation;
import org.apache.commons.logging.Log;
import org.apache.commons.logging.LogFactory;
import org.springframework.aop.support.AopUtils;
import org.springframework.beans.factory.BeanFactory;
import org.myproject.ms.monitoring.Chainer;
import org.springframework.util.StringUtils;


class SpanTagAnnotationHandler {

	private static final Log log = LogFactory.getLog(MethodHandles.lookup().lookupClass());

	private final BeanFactory beanFactory;
	private Chainer tracer;
	
	SpanTagAnnotationHandler(BeanFactory beanFactory) {
		this.beanFactory = beanFactory;
	}

	void addAnnotatedParameters(MethodInvocation pjp) {
		try {
			Method method = pjp.getMethod();
			Method mostSpecificMethod = AopUtils.getMostSpecificMethod(method,
					pjp.getThis().getClass());
			List<SleuthAnnotatedParameter> annotatedParameters =
					SleuthAnnotationUtils.findAnnotatedParameters(mostSpecificMethod, pjp.getArguments());
			getAnnotationsFromInterfaces(pjp, mostSpecificMethod, annotatedParameters);
			mergeAnnotatedMethodsIfNecessary(pjp, method, mostSpecificMethod,
					annotatedParameters);
			addAnnotatedArguments(annotatedParameters);
		} catch (SecurityException e) {
			log.error("Exception occurred while trying to add annotated parameters", e);
		}
	}

	private void getAnnotationsFromInterfaces(MethodInvocation pjp,
			Method mostSpecificMethod,
			List<SleuthAnnotatedParameter> annotatedParameters) {
		Class<?>[] implementedInterfaces = pjp.getThis().getClass().getInterfaces();
		if (implementedInterfaces.length > 0) {
			for (Class<?> implementedInterface : implementedInterfaces) {
				for (Method methodFromInterface : implementedInterface.getMethods()) {
					if (methodsAreTheSame(mostSpecificMethod, methodFromInterface)) {
						List<SleuthAnnotatedParameter> annotatedParametersForActualMethod =
								SleuthAnnotationUtils.findAnnotatedParameters(methodFromInterface, pjp.getArguments());
						mergeAnnotatedParameters(annotatedParameters, annotatedParametersForActualMethod);
					}
				}
			}
		}
	}

	private boolean methodsAreTheSame(Method mostSpecificMethod, Method method1) {
		return method1.getName().equals(mostSpecificMethod.getName()) &&
				Arrays.equals(method1.getParameterTypes(), mostSpecificMethod.getParameterTypes());
	}

	private void mergeAnnotatedMethodsIfNecessary(MethodInvocation pjp, Method method,
			Method mostSpecificMethod, List<SleuthAnnotatedParameter> annotatedParameters) {
		// that can happen if we have an abstraction and a concrete class that is
		// annotated with @NewSpan annotation
		if (!method.equals(mostSpecificMethod)) {
			List<SleuthAnnotatedParameter> annotatedParametersForActualMethod = SleuthAnnotationUtils.findAnnotatedParameters(
					method, pjp.getArguments());
			mergeAnnotatedParameters(annotatedParameters, annotatedParametersForActualMethod);
		}
	}

	private void mergeAnnotatedParameters(List<SleuthAnnotatedParameter> annotatedParametersIndices,
			List<SleuthAnnotatedParameter> annotatedParametersIndicesForActualMethod) {
		for (SleuthAnnotatedParameter container : annotatedParametersIndicesForActualMethod) {
			final int index = container.parameterIndex;
			boolean parameterContained = false;
			for (SleuthAnnotatedParameter parameterContainer : annotatedParametersIndices) {
				if (parameterContainer.parameterIndex == index) {
					parameterContained = true;
					break;
				}
			}
			if (!parameterContained) {
				annotatedParametersIndices.add(container);
			}
		}
	}

	private void addAnnotatedArguments(List<SleuthAnnotatedParameter> toBeAdded) {
		for (SleuthAnnotatedParameter container : toBeAdded) {
			String tagValue = resolveTagValue(container.annotation, container.argument);
			tracer().addTag(container.annotation.value(), tagValue);
		}
	}

	String resolveTagValue(SpanTag annotation, Object argument) {
		if (argument == null) {
			return "";
		}
		if (annotation.resolver() != NoOpTagValueResolver.class) {
			TagValueResolver tagValueResolver = this.beanFactory.getBean(annotation.resolver());
			return tagValueResolver.resolve(argument);
		} else if (StringUtils.hasText(annotation.expression())) {
			return this.beanFactory.getBean(TagValueExpressionResolver.class)
					.resolve(annotation.expression(), argument);
		}
		return argument.toString();
	}

	private Chainer tracer() {
		if (this.tracer == null) {
			this.tracer = this.beanFactory.getBean(Chainer.class);
		}
		return this.tracer;
	}

}


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/antn/SpanTagAnnotationHandler.java:SpanTagAnnotationHandler.<init>
// Node: SpanTagAnnotationHandler
// Node: addAnnotatedParameters
// Node: getMostSpecificMethod
// Node: getThis
// Node: getArguments
// Node: getAnnotationsFromInterfaces
// Node: mergeAnnotatedMethodsIfNecessary
// Node: addAnnotatedArguments
// Node: getInterfaces
// Node: getMethods
// Node: methodsAreTheSame
// Node: mergeAnnotatedParameters


package org.myproject.ms.monitoring.antn;

import org.aopalliance.intercept.MethodInvocation;
import org.myproject.ms.monitoring.Item;


public interface SpanCreator {

	
	Item createSpan(MethodInvocation methodInvocation, NewSpan newSpan);
}


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/antn/SpanCreator.java:SpanCreator.<init>

package org.myproject.ms.monitoring.antn;

import java.lang.invoke.MethodHandles;

import org.aopalliance.intercept.MethodInvocation;
import org.apache.commons.logging.Log;
import org.apache.commons.logging.LogFactory;
import org.myproject.ms.monitoring.Item;
import org.myproject.ms.monitoring.Chainer;
import org.myproject.ms.monitoring.util.ItemNameUtil;
import org.springframework.util.StringUtils;


class DefaultSpanCreator implements SpanCreator {

	private static final Log log = LogFactory.getLog(MethodHandles.lookup().lookupClass());

	private final Chainer tracer;

	DefaultSpanCreator(Chainer tracer) {
		this.tracer = tracer;
	}

	@Override public Item createSpan(MethodInvocation pjp, NewSpan newSpanAnnotation) {
		String name = StringUtils.isEmpty(newSpanAnnotation.name()) ?
				pjp.getMethod().getName() : newSpanAnnotation.name();
		String changedName = ItemNameUtil.toLowerHyphen(name);
		if (log.isDebugEnabled()) {
			log.debug("For the class [" + pjp.getThis().getClass() + "] method "
					+ "[" + pjp.getMethod().getName() + "] will name the span [" + changedName + "]");
		}
		return createSpan(changedName);
	}

	private Item createSpan(String name) {
		if (this.tracer.isTracing()) {
			return this.tracer.createSpan(name, this.tracer.getCurrentSpan());
		}
		return this.tracer.createSpan(name);
	}

}


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/antn/DefaultSpanCreator.java:DefaultSpanCreator.<init>
// Node: DefaultSpanCreator


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


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/antn/SleuthAdvisorConfig.java:SleuthAdvisorConfig.<init>
// Node: getClassFilter
// Node: validateInterfaces
// Node: DynamicMethodMatcherPointcut
// Node: hasAnnotatedMethods
// Node: AtomicBoolean
// Node: doWithMethods
// Node: MethodCallback
// Node: doWith
// Node: invoke
// Node: proceed
// Node: spanCreator
// Node: spanTagAnnotationHandler

package org.myproject.ms.monitoring.antn;

import org.springframework.boot.autoconfigure.AutoConfigureAfter;
import org.springframework.boot.autoconfigure.condition.ConditionalOnBean;
import org.springframework.boot.autoconfigure.condition.ConditionalOnMissingBean;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.myproject.ms.monitoring.Chainer;
import org.myproject.ms.monitoring.atcfg.TraceAutoConfiguration;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;


@Configuration
@ConditionalOnBean(Chainer.class)
@ConditionalOnProperty(name = "spring.sleuth.annotation.enabled", matchIfMissing = true)
@AutoConfigureAfter(TraceAutoConfiguration.class)
@EnableConfigurationProperties(SleuthAnnotationProperties.class)
public class SleuthAnnotationAutoConfiguration {
	
	@Bean
	@ConditionalOnMissingBean
	SpanCreator spanCreator(Chainer tracer) {
		return new DefaultSpanCreator(tracer);
	}

	@Bean
	@ConditionalOnMissingBean
	TagValueExpressionResolver spelTagValueExpressionResolver() {
		return new SpelTagValueExpressionResolver();
	}

	@Bean
	@ConditionalOnMissingBean
	TagValueResolver noOpTagValueResolver() {
		return new NoOpTagValueResolver();
	}

	@Bean
	SleuthAdvisorConfig sleuthAdvisorConfig() {
		return new SleuthAdvisorConfig();
	}
	
}




package org.myproject.ms.monitoring.antn;

import java.lang.invoke.MethodHandles;

import org.apache.commons.logging.Log;
import org.apache.commons.logging.LogFactory;
import org.springframework.expression.Expression;
import org.springframework.expression.ExpressionParser;
import org.springframework.expression.spel.standard.SpelExpressionParser;


class SpelTagValueExpressionResolver implements TagValueExpressionResolver {
	private static final Log log = LogFactory.getLog(MethodHandles.lookup().lookupClass());

	@Override
	public String resolve(String expression, Object parameter) {
		try {
			ExpressionParser expressionParser = new SpelExpressionParser();
			Expression expressionToEvaluate = expressionParser.parseExpression(expression);
			return expressionToEvaluate.getValue(parameter, String.class);
		} catch (Exception e) {
			log.error("Exception occurred while tying to evaluate the SPEL expression [" + expression + "]", e);
		}
		return parameter.toString();
	}
}


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/antn/SpelTagValueExpressionResolver.java:SpelTagValueExpressionResolver.<init>


package org.myproject.ms.monitoring.instrument.msg;

import org.myproject.ms.monitoring.Log;
import org.myproject.ms.monitoring.Item;
import org.myproject.ms.monitoring.ChainKeys;
import org.myproject.ms.monitoring.Chainer;
import org.myproject.ms.monitoring.spl.NeverSampler;
import org.myproject.ms.monitoring.util.ExceptionUtils;
import org.springframework.messaging.Message;
import org.springframework.messaging.MessageChannel;
import org.springframework.messaging.MessageHandler;
import org.springframework.messaging.support.GenericMessage;
import org.springframework.messaging.support.MessageBuilder;
import org.springframework.messaging.support.MessageHeaderAccessor;


public class TCInter extends ATCInter {

	public TCInter(Chainer tracer, ChainKeys traceKeys,
			MSTMExtra spanExtractor,
			MSTMInject spanInjector) {
		super(tracer, traceKeys, spanExtractor, spanInjector);
	}

	@Override
	public void afterSendCompletion(Message<?> message, MessageChannel channel, boolean sent, Exception ex) {
		Item currentSpan = getTracer().getCurrentSpan();
		if (containsServerReceived(currentSpan)) {
			currentSpan.logEvent(Item.SERVER_SEND);
		} else if (currentSpan != null) {
			currentSpan.logEvent(Item.CLIENT_RECV);
		}
		addErrorTag(ex);
		getTracer().close(currentSpan);
	}

	private boolean containsServerReceived(Item span) {
		if (span == null) {
			return false;
		}
		for (Log log : span.logs()) {
			if (Item.SERVER_RECV.equals(log.getEvent())) {
				return true;
			}
		}
		return false;
	}

	@Override
	public Message<?> preSend(Message<?> message, MessageChannel channel) {
		MessageBuilder<?> messageBuilder = MessageBuilder.fromMessage(message);
		Item parentSpan = getTracer().isTracing() ? getTracer().getCurrentSpan()
				: buildSpan(new MTMap(messageBuilder));
		String name = getMessageChannelName(channel);
		Item span = startSpan(parentSpan, name, message);
		if (message.getHeaders().containsKey(TMHead.MESSAGE_SENT_FROM_CLIENT)) {
			span.logEvent(Item.SERVER_RECV);
		} else {
			span.logEvent(Item.CLIENT_SEND);
			messageBuilder.setHeader(TMHead.MESSAGE_SENT_FROM_CLIENT, true);
		}
		getSpanInjector().inject(span, new MTMap(messageBuilder));
		MessageHeaderAccessor headers = MessageHeaderAccessor.getMutableAccessor(message);
		headers.copyHeaders(messageBuilder.build().getHeaders());
		return new GenericMessage<Object>(message.getPayload(), headers.getMessageHeaders());
	}

	private Item startSpan(Item span, String name, Message<?> message) {
		if (span != null) {
			return getTracer().createSpan(name, span);
		}
		if (Item.SPAN_NOT_SAMPLED.equals(message.getHeaders().get(TMHead.SAMPLED_NAME))) {
			return getTracer().createSpan(name, NeverSampler.INSTANCE);
		}
		return getTracer().createSpan(name);
	}

	@Override
	public Message<?> beforeHandle(Message<?> message, MessageChannel channel,
			MessageHandler handler) {
		Item spanFromHeader = getTracer().getCurrentSpan();
		if (spanFromHeader!= null) {
			spanFromHeader.logEvent(Item.SERVER_RECV);
		}
		getTracer().continueSpan(spanFromHeader);
		return message;
	}

	@Override
	public void afterMessageHandled(Message<?> message, MessageChannel channel,
			MessageHandler handler, Exception ex) {
		Item spanFromHeader = getTracer().getCurrentSpan();
		if (spanFromHeader!= null) {
			spanFromHeader.logEvent(Item.SERVER_SEND);
			addErrorTag(ex);
		}
		// related to #447
		if (getTracer().isTracing()) {
			getTracer().detach(spanFromHeader);
		}
	}

	private void addErrorTag(Exception ex) {
		if (ex != null) {
			getTracer().addTag(Item.SPAN_ERROR_TAG_NAME, ExceptionUtils.getExceptionMessage(ex));
		}
	}

}


// Node: afterSendCompletion
// Node: containsServerReceived
// Node: addErrorTag
// Node: preSend
// Node: fromMessage
// Node: buildSpan
// Node: MTMap
// Node: getMessageChannelName
// Node: getSpanInjector
// Node: getMessageHeaders
// Node: beforeHandle
// Node: afterMessageHandled
package org.myproject.ms.monitoring.instrument.msg;

import java.lang.invoke.MethodHandles;

import org.apache.commons.logging.Log;
import org.apache.commons.logging.LogFactory;
import org.myproject.ms.monitoring.Item;
import org.myproject.ms.monitoring.ItemTextMap;
import org.myproject.ms.monitoring.ChainKeys;
import org.myproject.ms.monitoring.Chainer;
import org.myproject.ms.monitoring.util.ItemNameUtil;
import org.springframework.integration.channel.AbstractMessageChannel;
import org.springframework.integration.context.IntegrationObjectSupport;
import org.springframework.messaging.MessageChannel;
import org.springframework.messaging.support.ChannelInterceptorAdapter;
import org.springframework.messaging.support.ExecutorChannelInterceptor;
import org.springframework.util.ClassUtils;


abstract class ATCInter extends ChannelInterceptorAdapter
		implements ExecutorChannelInterceptor {

	private static final Log log = LogFactory.getLog(MethodHandles.lookup().lookupClass());

	
	protected static final String MESSAGE_COMPONENT = "message";

	private final Chainer tracer;
	private final ChainKeys traceKeys;
	private final MSTMExtra spanExtractor;
	private final MSTMInject spanInjector;

	protected ATCInter(Chainer tracer, ChainKeys traceKeys,
			MSTMExtra spanExtractor,
			MSTMInject spanInjector) {
		this.tracer = tracer;
		this.traceKeys = traceKeys;
		this.spanExtractor = spanExtractor;
		this.spanInjector = spanInjector;
	}

	protected Chainer getTracer() {
		return this.tracer;
	}

	protected ChainKeys getTraceKeys() {
		return this.traceKeys;
	}

	protected MSTMInject getSpanInjector() {
		return this.spanInjector;
	}

	
	protected Item buildSpan(ItemTextMap carrier) {
		try {
			return this.spanExtractor.joinTrace(carrier);
		} catch (Exception e) {
			log.error("Exception occurred while trying to extract span from carrier", e);
			return null;
		}
	}

	String getChannelName(MessageChannel channel) {
		String name = null;
		if (ClassUtils.isPresent(
				"org.springframework.integration.context.IntegrationObjectSupport",
				null)) {
			if (channel instanceof IntegrationObjectSupport) {
				name = ((IntegrationObjectSupport) channel).getComponentName();
			}
			if (name == null && channel instanceof AbstractMessageChannel) {
				name = ((AbstractMessageChannel) channel).getFullChannelName();
			}
		}
		if (name == null) {
			name = channel.toString();
		}
		return name;
	}

	String getMessageChannelName(MessageChannel channel) {
		return ItemNameUtil.shorten(MESSAGE_COMPONENT + ":" + getChannelName(channel));
	}

}


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/instrument/msg/ATCInter.java:ATCInter.<init>
// Node: ATCInter
// Node: getTraceKeys
// Node: getChannelName
// Node: getComponentName
// Node: getFullChannelName


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


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/instrument/msg/MTMap.java:MTMap.<init>
// Node: addAnnotations
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


// Node: tagIfEntryMissing
// Node: addPayloadAnnotations


package org.myproject.ms.monitoring.instrument.schedl;

import java.util.regex.Pattern;

import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.annotation.Around;
import org.aspectj.lang.annotation.Aspect;
import org.myproject.ms.monitoring.Item;
import org.myproject.ms.monitoring.ChainKeys;
import org.myproject.ms.monitoring.Chainer;
import org.myproject.ms.monitoring.util.ItemNameUtil;


@Aspect
public class TSAspect {

	private static final String SCHEDULED_COMPONENT = "scheduled";

	private final Chainer tracer;
	private final ChainKeys traceKeys;
	private final Pattern skipPattern;

	public TSAspect(Chainer tracer, ChainKeys traceKeys, Pattern skipPattern) {
		this.tracer = tracer;
		this.traceKeys = traceKeys;
		this.skipPattern = skipPattern;
	}

	@Around("execution (@org.springframework.scheduling.annotation.Scheduled  * *.*(..))")
	public Object traceBackgroundThread(final ProceedingJoinPoint pjp) throws Throwable {
		if (this.skipPattern.matcher(pjp.getTarget().getClass().getName()).matches()) {
			return pjp.proceed();
		}
		String spanName = ItemNameUtil.toLowerHyphen(pjp.getSignature().getName());
		Item span = this.tracer.createSpan(spanName);
		this.tracer.addTag(Item.SPAN_LOCAL_COMPONENT_TAG_NAME, SCHEDULED_COMPONENT);
		this.tracer.addTag(this.traceKeys.getAsync().getPrefix() +
				this.traceKeys.getAsync().getClassNameKey(), pjp.getTarget().getClass().getSimpleName());
		this.tracer.addTag(this.traceKeys.getAsync().getPrefix() +
				this.traceKeys.getAsync().getMethodNameKey(), pjp.getSignature().getName());
		try {
			return pjp.proceed();
		}
		finally {
			this.tracer.close(span);
		}
	}

}


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/instrument/schedl/TSAspect.java:TSAspect.<init>
// Node: Around
// Node: execution
// Node: traceBackgroundThread
// Node: getTarget
// Node: getSignature
// Node: getSimpleName


package org.myproject.ms.monitoring.instrument.async;

import org.myproject.ms.monitoring.Item;
import org.myproject.ms.monitoring.ItemNamer;
import org.myproject.ms.monitoring.ChainRunnable;
import org.myproject.ms.monitoring.Chainer;
import org.myproject.ms.monitoring.ChainKeys;


public class LCTRun extends ChainRunnable {

	protected static final String ASYNC_COMPONENT = "async";

	private final ChainKeys traceKeys;

	public LCTRun(Chainer tracer, ChainKeys traceKeys,
			ItemNamer spanNamer, Runnable delegate) {
		super(tracer, spanNamer, delegate);
		this.traceKeys = traceKeys;
	}

	public LCTRun(Chainer tracer, ChainKeys traceKeys,
			ItemNamer spanNamer, Runnable delegate, String name) {
		super(tracer, spanNamer, delegate, name);
		this.traceKeys = traceKeys;
	}

	@Override
	public void run() {
		Item span = startSpan();
		try {
			this.getDelegate().run();
		}
		finally {
			close(span);
		}
	}

	@Override
	protected Item startSpan() {
		Item span = getTracer().createSpan(getSpanName(), getParent());
		getTracer().addTag(Item.SPAN_LOCAL_COMPONENT_TAG_NAME, ASYNC_COMPONENT);
		getTracer().addTag(this.traceKeys.getAsync().getPrefix() +
				this.traceKeys.getAsync().getThreadNameKey(), Thread.currentThread().getName());
		return span;
	}
}


// Node: currentThread


package org.myproject.ms.monitoring.instrument.async;

import java.lang.invoke.MethodHandles;
import java.util.concurrent.Executor;

import org.apache.commons.logging.Log;
import org.apache.commons.logging.LogFactory;
import org.springframework.beans.factory.BeanFactory;
import org.springframework.beans.factory.NoSuchBeanDefinitionException;
import org.myproject.ms.monitoring.DefaultItemNamer;
import org.myproject.ms.monitoring.ItemNamer;
import org.myproject.ms.monitoring.ChainKeys;
import org.myproject.ms.monitoring.Chainer;


public class LTExec implements Executor {

	private static final Log log = LogFactory.getLog(MethodHandles.lookup().lookupClass());

	private Chainer tracer;
	private final BeanFactory beanFactory;
	private final Executor delegate;
	private ChainKeys traceKeys;
	private ItemNamer spanNamer;

	public LTExec(BeanFactory beanFactory, Executor delegate) {
		this.beanFactory = beanFactory;
		this.delegate = delegate;
	}

	@Override
	public void execute(Runnable command) {
		if (this.tracer == null) {
			try {
				this.tracer = this.beanFactory.getBean(Chainer.class);
			}
			catch (NoSuchBeanDefinitionException e) {
				this.delegate.execute(command);
				return;
			}
		}
		this.delegate.execute(new SCTRun(this.tracer, traceKeys(), spanNamer(), command));
	}

	// due to some race conditions trace keys might not be ready yet
	private ChainKeys traceKeys() {
		if (this.traceKeys == null) {
			try {
				this.traceKeys = this.beanFactory.getBean(ChainKeys.class);
			}
			catch (NoSuchBeanDefinitionException e) {
				log.warn("TraceKeys bean not found - will provide a manually created instance");
				return new ChainKeys();
			}
		}
		return this.traceKeys;
	}

	// due to some race conditions trace keys might not be ready yet
	private ItemNamer spanNamer() {
		if (this.spanNamer == null) {
			try {
				this.spanNamer = this.beanFactory.getBean(ItemNamer.class);
			}
			catch (NoSuchBeanDefinitionException e) {
				log.warn("SpanNamer bean not found - will provide a manually created instance");
				return new DefaultItemNamer();
			}
		}
		return this.spanNamer;
	}

}


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/instrument/async/LTExec.java:LTExec.<init>
// Node: LTExec


package org.myproject.ms.monitoring.instrument.async;

import java.lang.reflect.Method;
import java.lang.reflect.Modifier;
import java.util.concurrent.Executor;

import org.aopalliance.intercept.MethodInterceptor;
import org.aopalliance.intercept.MethodInvocation;
import org.springframework.aop.framework.ProxyFactoryBean;
import org.springframework.beans.BeansException;
import org.springframework.beans.factory.BeanFactory;
import org.springframework.beans.factory.config.BeanPostProcessor;
import org.springframework.scheduling.concurrent.ThreadPoolTaskExecutor;
import org.springframework.util.ReflectionUtils;


class EBPProc implements BeanPostProcessor {

	private final BeanFactory beanFactory;

	EBPProc(BeanFactory beanFactory) {
		this.beanFactory = beanFactory;
	}

	@Override
	public Object postProcessBeforeInitialization(Object bean, String beanName)
			throws BeansException {
		return bean;
	}

	@Override
	public Object postProcessAfterInitialization(Object bean, String beanName)
			throws BeansException {
		if (bean instanceof Executor && !(bean instanceof ThreadPoolTaskExecutor)) {
			Method execute = ReflectionUtils.findMethod(bean.getClass(), "execute", Runnable.class);
			boolean methodFinal = Modifier.isFinal(execute.getModifiers());
			boolean classFinal = Modifier.isFinal(bean.getClass().getModifiers());
			boolean cglibProxy = !methodFinal && !classFinal;
			Executor executor = (Executor) bean;
			ProxyFactoryBean factory = new ProxyFactoryBean();
			factory.setProxyTargetClass(cglibProxy);
			factory.addAdvice(new ExecutorMethodInterceptor(executor, this.beanFactory));
			factory.setTarget(bean);
			return factory.getObject();
		}
		return bean;
	}
}

class ExecutorMethodInterceptor implements MethodInterceptor {

	private final Executor delegate;
	private final BeanFactory beanFactory;

	ExecutorMethodInterceptor(Executor delegate, BeanFactory beanFactory) {
		this.delegate = delegate;
		this.beanFactory = beanFactory;
	}

	@Override public Object invoke(MethodInvocation invocation)
			throws Throwable {
		LTExec executor = new LTExec(this.beanFactory, this.delegate);
		Method methodOnTracedBean = getMethod(invocation, executor);
		if (methodOnTracedBean != null) {
			return methodOnTracedBean.invoke(executor, invocation.getArguments());
		}
		return invocation.proceed();
	}

	private Method getMethod(MethodInvocation invocation, Object object) {
		Method method = invocation.getMethod();
		return ReflectionUtils
				.findMethod(object.getClass(), method.getName(), method.getParameterTypes());
	}
}


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/instrument/async/EBPProc.java:EBPProc.<init>
// Node: EBPProc
// Node: findMethod
// Node: isFinal
// Node: getModifiers
// Node: ProxyFactoryBean
// Node: setProxyTargetClass
// Node: addAdvice
// Node: ExecutorMethodInterceptor
// Node: setTarget
// Node: getObject


package org.myproject.ms.monitoring.instrument.async;

import org.myproject.ms.monitoring.Item;
import org.myproject.ms.monitoring.ItemNamer;
import org.myproject.ms.monitoring.ChainKeys;
import org.myproject.ms.monitoring.ChainRunnable;
import org.myproject.ms.monitoring.Chainer;


public class SCTRun extends ChainRunnable {

	private final LCTRun traceRunnable;

	public SCTRun(Chainer tracer, ChainKeys traceKeys,
			ItemNamer spanNamer, Runnable delegate) {
		super(tracer, spanNamer, delegate);
		this.traceRunnable = new LCTRun(tracer, traceKeys, spanNamer, delegate);
	}

	public SCTRun(Chainer tracer, ChainKeys traceKeys,
			ItemNamer spanNamer, Runnable delegate, String name) {
		super(tracer, spanNamer, delegate, name);
		this.traceRunnable = new LCTRun(tracer, traceKeys, spanNamer, delegate, name);
	}

	@Override
	public void run() {
		Item span = startSpan();
		try {
			this.getDelegate().run();
		}
		finally {
			close(span);
		}
	}

	@Override
	protected Item startSpan() {
		Item span = this.getParent();
		if (span == null) {
			return this.traceRunnable.startSpan();
		}
		return continueSpan(span);
	}

	@Override protected void close(Item span) {
		if (this.getParent() == null) {
			super.close(span);
		} else {
			super.detachSpan(span);
		}
	}
}




package org.myproject.ms.monitoring.instrument.async;

import java.util.concurrent.Executor;

import org.springframework.beans.factory.BeanFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.autoconfigure.AutoConfigureAfter;
import org.springframework.boot.autoconfigure.condition.ConditionalOnBean;
import org.springframework.boot.autoconfigure.condition.ConditionalOnMissingBean;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.myproject.ms.monitoring.ChainKeys;
import org.myproject.ms.monitoring.Chainer;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.task.SimpleAsyncTaskExecutor;
import org.springframework.scheduling.annotation.AsyncConfigurer;
import org.springframework.scheduling.annotation.AsyncConfigurerSupport;
import org.springframework.scheduling.annotation.EnableAsync;


@EnableAsync
@Configuration
@ConditionalOnProperty(value = "spring.sleuth.async.enabled", matchIfMissing = true)
@ConditionalOnBean(Chainer.class)
@AutoConfigureAfter(ACAtcfg.class)
public class ADAtcfg {

	@Autowired private BeanFactory beanFactory;

	@Configuration
	@ConditionalOnMissingBean(AsyncConfigurer.class)
	@ConditionalOnProperty(value = "spring.sleuth.async.configurer.enabled", matchIfMissing = true)
	static class DefaultAsyncConfigurerSupport extends AsyncConfigurerSupport {

		@Autowired private BeanFactory beanFactory;

		@Override
		public Executor getAsyncExecutor() {
			return new LTExec(this.beanFactory, new SimpleAsyncTaskExecutor());
		}
	}

	@Bean
	public TAAsp traceAsyncAspect(Chainer tracer, ChainKeys traceKeys) {
		return new TAAsp(tracer, traceKeys, this.beanFactory);
	}

	@Bean
	public EBPProc executorBeanPostProcessor() {
		return new EBPProc(this.beanFactory);
	}

}

// Node: getAsyncExecutor
// Node: SimpleAsyncTaskExecutor
// Node: traceAsyncAspect
// Node: TAAsp
// Node: executorBeanPostProcessor


package org.myproject.ms.monitoring.instrument.async;

import java.util.concurrent.Callable;

import org.myproject.ms.monitoring.Item;
import org.myproject.ms.monitoring.ItemNamer;
import org.myproject.ms.monitoring.ChainCallable;
import org.myproject.ms.monitoring.ChainKeys;
import org.myproject.ms.monitoring.Chainer;


public class SCTCall<V> extends ChainCallable<V> {

	private final LCTCall<V> traceCallable;

	public SCTCall(Chainer tracer, ChainKeys traceKeys,
			ItemNamer spanNamer, Callable<V> delegate) {
		super(tracer, spanNamer, delegate);
		this.traceCallable = new LCTCall<>(tracer, traceKeys, spanNamer, delegate);
	}

	public SCTCall(Chainer tracer, ChainKeys traceKeys,
			ItemNamer spanNamer, String name, Callable<V> delegate) {
		super(tracer, spanNamer, delegate, name);
		this.traceCallable = new LCTCall<>(tracer, traceKeys, spanNamer, name, delegate);
	}

	@Override
	public V call() throws Exception {
		Item span = startSpan();
		try {
			return this.getDelegate().call();
		}
		finally {
			close(span);
		}
	}

	@Override
	protected Item startSpan() {
		Item span = this.getParent();
		if (span == null) {
			return this.traceCallable.startSpan();
		}
		return continueSpan(span);
	}

	@Override protected void close(Item span) {
		if (this.getParent() == null) {
			super.close(span);
		} else {
			super.detachSpan(span);
		}
	}
}


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/instrument/async/SCTCall.java:SCTCall.<init>
// Node: SCTCall


package org.myproject.ms.monitoring.instrument.async;

import java.util.concurrent.Executor;

import org.springframework.aop.interceptor.AsyncUncaughtExceptionHandler;
import org.springframework.beans.factory.BeanFactory;
import org.springframework.scheduling.annotation.AsyncConfigurer;
import org.springframework.scheduling.annotation.AsyncConfigurerSupport;


public class LTACus extends AsyncConfigurerSupport {

	private final BeanFactory beanFactory;
	private final AsyncConfigurer delegate;

	public LTACus(BeanFactory beanFactory, AsyncConfigurer delegate) {
		this.beanFactory = beanFactory;
		this.delegate = delegate;
	}

	@Override
	public Executor getAsyncExecutor() {
		return new LTExec(this.beanFactory, this.delegate.getAsyncExecutor());
	}

	@Override
	public AsyncUncaughtExceptionHandler getAsyncUncaughtExceptionHandler() {
		return this.delegate.getAsyncUncaughtExceptionHandler();
	}

}




package org.myproject.ms.monitoring.instrument.async;

import java.util.concurrent.Callable;

import org.myproject.ms.monitoring.Item;
import org.myproject.ms.monitoring.ItemNamer;
import org.myproject.ms.monitoring.ChainCallable;
import org.myproject.ms.monitoring.Chainer;


@Deprecated
public class TCCall<V> extends ChainCallable<V> implements Callable<V> {

	public TCCall(Chainer tracer, ItemNamer spanNamer, Callable<V> delegate) {
		super(tracer, spanNamer, delegate);
	}

	@Override
	protected Item startSpan() {
		return getTracer().continueSpan(getParent());
	}

	@Override
	protected void close(Item span) {
		if (getTracer().isTracing()) {
			getTracer().detach(span);
		}
	}
}




package org.myproject.ms.monitoring.instrument.async;

import java.lang.invoke.MethodHandles;
import java.util.concurrent.Callable;
import java.util.concurrent.Future;
import java.util.concurrent.ThreadPoolExecutor;

import org.apache.commons.logging.Log;
import org.apache.commons.logging.LogFactory;
import org.springframework.beans.factory.BeanFactory;
import org.springframework.beans.factory.NoSuchBeanDefinitionException;
import org.myproject.ms.monitoring.DefaultItemNamer;
import org.myproject.ms.monitoring.ItemNamer;
import org.myproject.ms.monitoring.ChainKeys;
import org.myproject.ms.monitoring.Chainer;
import org.springframework.scheduling.concurrent.ThreadPoolTaskExecutor;
import org.springframework.util.concurrent.ListenableFuture;


@SuppressWarnings("serial")
public class LTTPTExec extends ThreadPoolTaskExecutor {

	private static final Log log = LogFactory.getLog(MethodHandles.lookup().lookupClass());

	private Chainer tracer;
	private final BeanFactory beanFactory;
	private final ThreadPoolTaskExecutor delegate;
	private ChainKeys traceKeys;
	private ItemNamer spanNamer;

	public LTTPTExec(BeanFactory beanFactory,
			ThreadPoolTaskExecutor delegate) {
		this.beanFactory = beanFactory;
		this.delegate = delegate;
	}

	@Override
	public void execute(Runnable task) {
		this.delegate.execute(new SCTRun(tracer(), traceKeys(), spanNamer(), task));
	}

	@Override
	public void execute(Runnable task, long startTimeout) {
		this.delegate.execute(new SCTRun(tracer(), traceKeys(), spanNamer(), task), startTimeout);
	}

	@Override
	public Future<?> submit(Runnable task) {
		return this.delegate.submit(new SCTRun(tracer(), traceKeys(), spanNamer(), task));
	}

	@Override
	public <T> Future<T> submit(Callable<T> task) {
		return this.delegate.submit(new SCTCall<>(tracer(), traceKeys(), spanNamer(), task));
	}

	@Override
	public ListenableFuture<?> submitListenable(Runnable task) {
		return this.delegate.submitListenable(new SCTRun(tracer(), traceKeys(), spanNamer(), task));
	}

	@Override
	public <T> ListenableFuture<T> submitListenable(Callable<T> task) {
		return this.delegate.submitListenable(new SCTCall<>(tracer(), traceKeys(), spanNamer(), task));
	}

	@Override
	public ThreadPoolExecutor getThreadPoolExecutor() throws IllegalStateException {
		return this.delegate.getThreadPoolExecutor();
	}

	public void destroy() {
		this.delegate.destroy();
		super.destroy();
	}

	@Override
	public void afterPropertiesSet() {
		this.delegate.afterPropertiesSet();
		super.afterPropertiesSet();
	}

	private Chainer tracer() {
		if (this.tracer == null) {
			this.tracer = this.beanFactory.getBean(Chainer.class);
		}
		return this.tracer;
	}

	private ChainKeys traceKeys() {
		if (this.traceKeys == null) {
			try {
				this.traceKeys = this.beanFactory.getBean(ChainKeys.class);
			}
			catch (NoSuchBeanDefinitionException e) {
				log.warn("TraceKeys bean not found - will provide a manually created instance");
				return new ChainKeys();
			}
		}
		return this.traceKeys;
	}

	private ItemNamer spanNamer() {
		if (this.spanNamer == null) {
			try {
				this.spanNamer = this.beanFactory.getBean(ItemNamer.class);
			}
			catch (NoSuchBeanDefinitionException e) {
				log.warn("SpanNamer bean not found - will provide a manually created instance");
				return new DefaultItemNamer();
			}
		}
		return this.spanNamer;
	}
}


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/instrument/async/LTTPTExec.java:LTTPTExec.<init>
// Node: LTTPTExec


package org.myproject.ms.monitoring.instrument.async;

import java.lang.reflect.Method;

import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.annotation.Around;
import org.aspectj.lang.annotation.Aspect;
import org.aspectj.lang.reflect.MethodSignature;
import org.springframework.beans.factory.BeanFactory;
import org.myproject.ms.monitoring.Item;
import org.myproject.ms.monitoring.ChainKeys;
import org.myproject.ms.monitoring.Chainer;
import org.myproject.ms.monitoring.util.ItemNameUtil;
import org.springframework.scheduling.concurrent.ThreadPoolTaskExecutor;
import org.springframework.util.ReflectionUtils;


@Aspect
public class TAAsp {

	private static final String ASYNC_COMPONENT = "async";

	private final Chainer tracer;
	private final ChainKeys traceKeys;
	private final BeanFactory beanFactory;

	public TAAsp(Chainer tracer, ChainKeys traceKeys, BeanFactory beanFactory) {
		this.tracer = tracer;
		this.traceKeys = traceKeys;
		this.beanFactory = beanFactory;
	}

	@Around("execution (@org.springframework.scheduling.annotation.Async  * *.*(..))")
	public Object traceBackgroundThread(final ProceedingJoinPoint pjp) throws Throwable {
		Item span = this.tracer.createSpan(
				ItemNameUtil.toLowerHyphen(pjp.getSignature().getName()));
		this.tracer.addTag(Item.SPAN_LOCAL_COMPONENT_TAG_NAME, ASYNC_COMPONENT);
		this.tracer.addTag(this.traceKeys.getAsync().getPrefix() +
				this.traceKeys.getAsync().getClassNameKey(), pjp.getTarget().getClass().getSimpleName());
		this.tracer.addTag(this.traceKeys.getAsync().getPrefix() +
				this.traceKeys.getAsync().getMethodNameKey(), pjp.getSignature().getName());
		try {
			return pjp.proceed();
		} finally {
			this.tracer.close(span);
		}
	}

	@Around("execution (* org.springframework.scheduling.concurrent.ThreadPoolTaskExecutor.*(..))")
	public Object traceThreadPoolTaskExecutor(final ProceedingJoinPoint pjp) throws Throwable {
		LTTPTExec executor = new LTTPTExec(this.beanFactory,
				(ThreadPoolTaskExecutor) pjp.getTarget());
		Method methodOnTracedBean = getMethod(pjp, executor);
		if (methodOnTracedBean != null) {
			return methodOnTracedBean.invoke(executor, pjp.getArgs());
		}
		return pjp.proceed();
	}

	private Method getMethod(ProceedingJoinPoint pjp, Object object) {
		MethodSignature signature = (MethodSignature) pjp.getSignature();
		Method method = signature.getMethod();
		return ReflectionUtils
				.findMethod(object.getClass(), method.getName(), method.getParameterTypes());
	}

}


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/instrument/async/TAAsp.java:TAAsp.<init>
// Node: traceThreadPoolTaskExecutor
// Node: getArgs


package org.myproject.ms.monitoring.instrument.async;

import java.util.concurrent.Callable;

import org.myproject.ms.monitoring.Item;
import org.myproject.ms.monitoring.ItemNamer;
import org.myproject.ms.monitoring.ChainCallable;
import org.myproject.ms.monitoring.Chainer;
import org.myproject.ms.monitoring.ChainKeys;


public class LCTCall<V> extends ChainCallable<V> {

	protected static final String ASYNC_COMPONENT = "async";

	private final ChainKeys traceKeys;

	public LCTCall(Chainer tracer, ChainKeys traceKeys,
			ItemNamer spanNamer, Callable<V> delegate) {
		super(tracer, spanNamer, delegate);
		this.traceKeys = traceKeys;
	}

	public LCTCall(Chainer tracer, ChainKeys traceKeys,
			ItemNamer spanNamer, String name, Callable<V> delegate) {
		super(tracer, spanNamer, delegate, name);
		this.traceKeys = traceKeys;
	}

	@Override
	public V call() throws Exception {
		Item span = startSpan();
		try {
			return this.getDelegate().call();
		}
		finally {
			close(span);
		}
	}

	@Override
	protected Item startSpan() {
		Item span = getTracer().createSpan(getSpanName(), getParent());
		getTracer().addTag(Item.SPAN_LOCAL_COMPONENT_TAG_NAME, ASYNC_COMPONENT);
		getTracer().addTag(this.traceKeys.getAsync().getPrefix() +
				this.traceKeys.getAsync().getThreadNameKey(), Thread.currentThread().getName());
		return span;
	}
}


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/instrument/async/LCTCall.java:LCTCall.<init>
// Node: LCTCall


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


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/instrument/web/TPWriter.java:TPWriter.<init>
// Node: TPWriter


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


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/instrument/web/TSOStr.java:TSOStr.<init>
// Node: TSOStr

package org.myproject.ms.monitoring.instrument.web;

import java.io.IOException;
import java.lang.invoke.MethodHandles;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Enumeration;
import java.util.regex.Pattern;
import javax.servlet.FilterChain;
import javax.servlet.ServletException;
import javax.servlet.ServletRequest;
import javax.servlet.ServletResponse;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import org.apache.commons.logging.Log;
import org.apache.commons.logging.LogFactory;
import org.myproject.ms.monitoring.Item;
import org.myproject.ms.monitoring.ItemReporter;
import org.myproject.ms.monitoring.ChainKeys;
import org.myproject.ms.monitoring.Chainer;
import org.myproject.ms.monitoring.spl.AlwaysSampler;
import org.myproject.ms.monitoring.spl.NeverSampler;
import org.myproject.ms.monitoring.util.ExceptionUtils;
import org.springframework.core.Ordered;
import org.springframework.core.annotation.Order;
import org.springframework.http.HttpStatus;
import org.springframework.util.StringUtils;
import org.springframework.web.context.request.async.WebAsyncUtils;
import org.springframework.web.filter.GenericFilterBean;
import org.springframework.web.util.UrlPathHelper;


@Order(TFilter.ORDER)
public class TFilter extends GenericFilterBean {

	private static final Log log = LogFactory.getLog(MethodHandles.lookup().lookupClass());

	private static final String HTTP_COMPONENT = "http";

	
	public static final int ORDER = Ordered.HIGHEST_PRECEDENCE + 5;

	protected static final String TRACE_REQUEST_ATTR = TFilter.class.getName()
			+ ".TRACE";

	protected static final String TRACE_ERROR_HANDLED_REQUEST_ATTR = TFilter.class.getName()
			+ ".ERROR_HANDLED";

	protected static final String TRACE_CLOSE_SPAN_REQUEST_ATTR = TFilter.class.getName()
			+ ".CLOSE_SPAN";

	
	@Deprecated
	public static final String DEFAULT_SKIP_PATTERN = SWProp.DEFAULT_SKIP_PATTERN;

	private final Chainer tracer;
	private final ChainKeys traceKeys;
	private final Pattern skipPattern;
	private final ItemReporter spanReporter;
	private final HSExtra spanExtractor;
	private final HTKInject httpTraceKeysInjector;

	private UrlPathHelper urlPathHelper = new UrlPathHelper();

	public TFilter(Chainer tracer, ChainKeys traceKeys, ItemReporter spanReporter,
			HSExtra spanExtractor,
			HTKInject httpTraceKeysInjector) {
		this(tracer, traceKeys, Pattern.compile(SWProp.DEFAULT_SKIP_PATTERN), spanReporter,
				spanExtractor, httpTraceKeysInjector);
	}

	public TFilter(Chainer tracer, ChainKeys traceKeys, Pattern skipPattern,
			ItemReporter spanReporter, HSExtra spanExtractor,
			HTKInject httpTraceKeysInjector) {
		this.tracer = tracer;
		this.traceKeys = traceKeys;
		this.skipPattern = skipPattern;
		this.spanReporter = spanReporter;
		this.spanExtractor = spanExtractor;
		this.httpTraceKeysInjector = httpTraceKeysInjector;
	}

	@Override
	public void doFilter(ServletRequest servletRequest, ServletResponse servletResponse,
			FilterChain filterChain) throws IOException, ServletException {
		if (!(servletRequest instanceof HttpServletRequest) || !(servletResponse instanceof HttpServletResponse)) {
			throw new ServletException("Filter just supports HTTP requests");
		}
		HttpServletRequest request = (HttpServletRequest) servletRequest;
		HttpServletResponse response = (HttpServletResponse) servletResponse;
		String uri = this.urlPathHelper.getPathWithinApplication(request);
		boolean skip = this.skipPattern.matcher(uri).matches()
				|| Item.SPAN_NOT_SAMPLED.equals(ServletUtils.getHeader(request, response, Item.SAMPLED_NAME));
		Item spanFromRequest = getSpanFromAttribute(request);
		if (spanFromRequest != null) {
			continueSpan(request, spanFromRequest);
		}
		if (log.isDebugEnabled()) {
			log.debug("Received a request to uri [" + uri + "] that should not be sampled [" + skip + "]");
		}
		// in case of a response with exception status a exception controller will close the span
		if (!httpStatusSuccessful(response) && isSpanContinued(request)) {
			Item parentSpan = parentSpan(spanFromRequest);
			processErrorRequest(filterChain, request, new THSResp(response, parentSpan), spanFromRequest);
			return;
		}
		String name = HTTP_COMPONENT + ":" + uri;
		Throwable exception = null;
		try {
			spanFromRequest = createSpan(request, skip, spanFromRequest, name);
			filterChain.doFilter(request, new THSResp(response, spanFromRequest));
		} catch (Throwable e) {
			exception = e;
			this.tracer.addTag(Item.SPAN_ERROR_TAG_NAME, ExceptionUtils.getExceptionMessage(e));
			throw e;
		} finally {
			if (isAsyncStarted(request) || request.isAsyncStarted()) {
				if (log.isDebugEnabled()) {
					log.debug("The span " + spanFromRequest + " will get detached by a HandleInterceptor");
				}
				// TODO: how to deal with response annotations and async?
				return;
			}
			spanFromRequest = createSpanIfRequestNotHandled(request, spanFromRequest, name, skip);
			detachOrCloseSpans(request, response, spanFromRequest, exception);
		}
	}

	private Item parentSpan(Item span) {
		if (span == null) {
			return null;
		}
		if (span.hasSavedSpan()) {
			return span.getSavedSpan();
		}
		return span;
	}

	private void processErrorRequest(FilterChain filterChain, HttpServletRequest request,
			HttpServletResponse response, Item spanFromRequest)
			throws IOException, ServletException {
		if (log.isDebugEnabled()) {
			log.debug("The span " + spanFromRequest + " was already detached once and we're processing an error");
		}
		try {
			filterChain.doFilter(request, response);
		} finally {
			request.setAttribute(TRACE_ERROR_HANDLED_REQUEST_ATTR, true);
			addResponseTags(response, null);
			if (request.getAttribute(TRAttr.ERROR_HANDLED_SPAN_REQUEST_ATTR) == null) {
				this.tracer.close(spanFromRequest);
			}
		}
	}

	private void continueSpan(HttpServletRequest request, Item spanFromRequest) {
		this.tracer.continueSpan(spanFromRequest);
		request.setAttribute(TRAttr.SPAN_CONTINUED_REQUEST_ATTR, "true");
		if (log.isDebugEnabled()) {
			log.debug("There has already been a span in the request " + spanFromRequest);
		}
	}

	// This method is a fallback in case if handler interceptors didn't catch the request.
	// In that case we are creating an artificial span so that it can be visible in Zipkin.
	private Item createSpanIfRequestNotHandled(HttpServletRequest request,
			Item spanFromRequest, String name, boolean skip) {
		if (!requestHasAlreadyBeenHandled(request)) {
			spanFromRequest = this.tracer.createSpan(name);
			request.setAttribute(TRACE_REQUEST_ATTR, spanFromRequest);
			if (log.isDebugEnabled() && !skip) {
				log.debug("The request with uri [" + request.getRequestURI() + "] hasn't been handled by any of Sleuth's components. "
						+ "That means that most likely you're using custom HandlerMappings and didn't add Sleuth's TraceHandlerInterceptor. "
						+ "Sleuth will create a span to ensure that the graph of calls remains valid in Zipkin");
			}
		}
		return spanFromRequest;
	}

	private boolean requestHasAlreadyBeenHandled(HttpServletRequest request) {
		return request.getAttribute(TRAttr.HANDLED_SPAN_REQUEST_ATTR) != null;
	}

	private void detachOrCloseSpans(HttpServletRequest request,
			HttpServletResponse response, Item spanFromRequest, Throwable exception) {
		Item span = spanFromRequest;
		if (span != null) {
			addResponseTags(response, exception);
			if (span.hasSavedSpan() && requestHasAlreadyBeenHandled(request)) {
				recordParentSpan(span.getSavedSpan());
			} else if (!requestHasAlreadyBeenHandled(request)) {
				span = this.tracer.close(span);
			}
			recordParentSpan(span);
			// in case of a response with exception status will close the span when exception dispatch is handled
			// checking if tracing is in progress due to async / different order of view controller processing
			if (httpStatusSuccessful(response) && this.tracer.isTracing()) {
				if (log.isDebugEnabled()) {
					log.debug("Closing the span " + span + " since the response was successful");
				}
				this.tracer.close(span);
			} else if (errorAlreadyHandled(request) && this.tracer.isTracing()) {
				if (log.isDebugEnabled()) {
					log.debug(
							"Won't detach the span " + span + " since error has already been handled");
				}
			}  else if (shouldCloseSpan(request) && this.tracer.isTracing() && stillTracingCurrentSapn(span)) {
				if (log.isDebugEnabled()) {
					log.debug(
							"Will close span " + span + " since some component marked it for closure");
				}
				this.tracer.close(span);
			} else if (this.tracer.isTracing()) {
				if (log.isDebugEnabled()) {
					log.debug("Detaching the span " + span + " since the response was unsuccessful");
				}
				this.tracer.detach(span);
			}
		}
	}

	private boolean stillTracingCurrentSapn(Item span) {
		return this.tracer.getCurrentSpan().equals(span);
	}

	private void recordParentSpan(Item parent) {
		if (parent == null) {
			return;
		}
		if (parent.isRemote()) {
			if (log.isDebugEnabled()) {
				log.debug("Trying to send the parent span " + parent + " to Zipkin");
			}
			parent.stop();
			// should be already done by HttpServletResponse wrappers
			SsLogSetter.annotateWithServerSendIfLogIsNotAlreadyPresent(parent);
			this.spanReporter.report(parent);
		} else {
			// should be already done by HttpServletResponse wrappers
			SsLogSetter.annotateWithServerSendIfLogIsNotAlreadyPresent(parent);
		}
	}

	private boolean httpStatusSuccessful(HttpServletResponse response) {
		if (response.getStatus() == 0) {
			return false;
		}
		HttpStatus.Series httpStatusSeries = HttpStatus.Series.valueOf(response.getStatus());
		return httpStatusSeries == HttpStatus.Series.SUCCESSFUL || httpStatusSeries == HttpStatus.Series.REDIRECTION;
	}

	private Item getSpanFromAttribute(HttpServletRequest request) {
		return (Item) request.getAttribute(TRACE_REQUEST_ATTR);
	}

	private boolean errorAlreadyHandled(HttpServletRequest request) {
		return Boolean.valueOf(
				String.valueOf(request.getAttribute(TRACE_ERROR_HANDLED_REQUEST_ATTR)));
	}

	private boolean shouldCloseSpan(HttpServletRequest request) {
		return Boolean.valueOf(
				String.valueOf(request.getAttribute(TRACE_CLOSE_SPAN_REQUEST_ATTR)));
	}

	private boolean isSpanContinued(HttpServletRequest request) {
		return getSpanFromAttribute(request) != null;
	}

	
	private void addRequestTagsForParentSpan(HttpServletRequest request, Item spanFromRequest) {
		if (spanFromRequest.getName().contains("parent")) {
			addRequestTags(spanFromRequest, request);
		}
	}

	
	private Item createSpan(HttpServletRequest request,
			boolean skip, Item spanFromRequest, String name) {
		if (spanFromRequest != null) {
			if (log.isDebugEnabled()) {
				log.debug("Span has already been created - continuing with the previous one");
			}
			return spanFromRequest;
		}
		Item parent = this.spanExtractor.joinTrace(new HSRTMap(request));
		if (parent != null) {
			if (log.isDebugEnabled()) {
				log.debug("Found a parent span " + parent + " in the request");
			}
			addRequestTagsForParentSpan(request, parent);
			spanFromRequest = parent;
			this.tracer.continueSpan(spanFromRequest);
			if (parent.isRemote()) {
				parent.logEvent(Item.SERVER_RECV);
			}
			request.setAttribute(TRACE_REQUEST_ATTR, spanFromRequest);
			if (log.isDebugEnabled()) {
				log.debug("Parent span is " + parent + "");
			}
		} else {
			if (skip) {
				spanFromRequest = this.tracer.createSpan(name, NeverSampler.INSTANCE);
			}
			else {
				String header = request.getHeader(Item.SPAN_FLAGS);
				if (Item.SPAN_SAMPLED.equals(header)) {
					spanFromRequest = this.tracer.createSpan(name, new AlwaysSampler());
				} else {
					spanFromRequest = this.tracer.createSpan(name);
				}
			}
			spanFromRequest.logEvent(Item.SERVER_RECV);
			request.setAttribute(TRACE_REQUEST_ATTR, spanFromRequest);
			if (log.isDebugEnabled()) {
				log.debug("No parent span present - creating a new span");
			}
		}
		return spanFromRequest;
	}

	
	protected void addRequestTags(Item span, HttpServletRequest request) {
		String uri = this.urlPathHelper.getPathWithinApplication(request);
		this.httpTraceKeysInjector.addRequestTags(span, getFullUrl(request),
				request.getServerName(), uri, request.getMethod());
		for (String name : this.traceKeys.getHttp().getHeaders()) {
			Enumeration<String> values = request.getHeaders(name);
			if (values.hasMoreElements()) {
				String key = this.traceKeys.getHttp().getPrefix() + name.toLowerCase();
				ArrayList<String> list = Collections.list(values);
				String value = list.size() == 1 ? list.get(0)
						: StringUtils.collectionToDelimitedString(list, ",", "'", "'");
				this.httpTraceKeysInjector.tagSpan(span, key, value);
			}
		}
	}

	
	protected void addResponseTags(HttpServletResponse response, Throwable e) {
		int httpStatus = response.getStatus();
		if (httpStatus == HttpServletResponse.SC_OK && e != null) {
			// Filter chain threw exception but the response status may not have been set
			// yet, so we have to guess.
			this.tracer.addTag(this.traceKeys.getHttp().getStatusCode(),
					String.valueOf(HttpServletResponse.SC_INTERNAL_SERVER_ERROR));
		}
		// only tag valid http statuses
		else if (httpStatus >= 100 && (httpStatus < 200) || (httpStatus > 399)) {
			this.tracer.addTag(this.traceKeys.getHttp().getStatusCode(),
					String.valueOf(response.getStatus()));
		}
	}

	protected boolean isAsyncStarted(HttpServletRequest request) {
		return WebAsyncUtils.getAsyncManager(request).isConcurrentHandlingStarted();
	}

	private String getFullUrl(HttpServletRequest request) {
		StringBuffer requestURI = request.getRequestURL();
		String queryString = request.getQueryString();
		if (queryString == null) {
			return requestURI.toString();
		} else {
			return requestURI.append('?').append(queryString).toString();
		}
	}
}



// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/instrument/web/TFilter.java:TFilter.<init>
// Node: UrlPathHelper
// Node: ServletException
// Node: getPathWithinApplication
// Node: getSpanFromAttribute
// Node: httpStatusSuccessful
// Node: isSpanContinued
// Node: parentSpan
// Node: processErrorRequest
// Node: THSResp
// Node: createSpanIfRequestNotHandled
// Node: detachOrCloseSpans
// Node: addResponseTags
// Node: requestHasAlreadyBeenHandled
// Node: recordParentSpan
// Node: stillTracingCurrentSapn
// Node: addRequestTagsForParentSpan
// Node: addRequestTags
// Node: HSRTMap
// Node: AlwaysSampler
// Node: getFullUrl
// Node: hasMoreElements
// Node: list
// Node: collectionToDelimitedString
// Node: tagSpan
// Node: getAsyncManager
// Node: isConcurrentHandlingStarted


package org.myproject.ms.monitoring.instrument.web;

import java.lang.reflect.Field;
import java.util.concurrent.Callable;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import org.apache.commons.logging.Log;
import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.annotation.Around;
import org.aspectj.lang.annotation.Aspect;
import org.aspectj.lang.annotation.Pointcut;
import org.myproject.ms.monitoring.Item;
import org.myproject.ms.monitoring.ItemNamer;
import org.myproject.ms.monitoring.ChainKeys;
import org.myproject.ms.monitoring.Chainer;
import org.myproject.ms.monitoring.instrument.async.SCTCall;
import org.myproject.ms.monitoring.util.ExceptionUtils;
import org.springframework.web.context.request.async.WebAsyncTask;


@Aspect
public class TWAsp {

	private static final Log log = org.apache.commons.logging.LogFactory
			.getLog(TWAsp.class);

	private final Chainer tracer;
	private final ItemNamer spanNamer;
	private final ChainKeys traceKeys;

	public TWAsp(Chainer tracer, ItemNamer spanNamer, ChainKeys traceKeys) {
		this.tracer = tracer;
		this.spanNamer = spanNamer;
		this.traceKeys = traceKeys;
	}

	@Pointcut("@within(org.springframework.web.bind.annotation.RestController)")
	private void anyRestControllerAnnotated() { }// NOSONAR

	@Pointcut("@within(org.springframework.stereotype.Controller)")
	private void anyControllerAnnotated() { } // NOSONAR

	@Pointcut("execution(public java.util.concurrent.Callable *(..))")
	private void anyPublicMethodReturningCallable() { } // NOSONAR

	@Pointcut("(anyRestControllerAnnotated() || anyControllerAnnotated()) && anyPublicMethodReturningCallable()")
	private void anyControllerOrRestControllerWithPublicAsyncMethod() { } // NOSONAR

	@Pointcut("execution(public org.springframework.web.context.request.async.WebAsyncTask *(..))")
	private void anyPublicMethodReturningWebAsyncTask() { } // NOSONAR

	@Pointcut("execution(public * org.springframework.web.servlet.HandlerExceptionResolver.resolveException(..)) && args(request, response, handler, ex)")
	private void anyHandlerExceptionResolver(HttpServletRequest request, HttpServletResponse response, Object handler, Exception ex) { } // NOSONAR

	@Pointcut("(anyRestControllerAnnotated() || anyControllerAnnotated()) && anyPublicMethodReturningWebAsyncTask()")
	private void anyControllerOrRestControllerWithPublicWebAsyncTaskMethod() { } // NOSONAR

	@Around("anyControllerOrRestControllerWithPublicAsyncMethod()")
	@SuppressWarnings("unchecked")
	public Object wrapWithCorrelationId(ProceedingJoinPoint pjp) throws Throwable {
		Callable<Object> callable = (Callable<Object>) pjp.proceed();
		if (this.tracer.isTracing()) {
			if (log.isDebugEnabled()) {
				log.debug("Wrapping callable with span [" + this.tracer.getCurrentSpan() + "]");
			}
			return new SCTCall<>(this.tracer, this.traceKeys, this.spanNamer, callable);
		}
		else {
			return callable;
		}
	}

	@Around("anyControllerOrRestControllerWithPublicWebAsyncTaskMethod()")
	public Object wrapWebAsyncTaskWithCorrelationId(ProceedingJoinPoint pjp) throws Throwable {
		final WebAsyncTask<?> webAsyncTask = (WebAsyncTask<?>) pjp.proceed();
		if (this.tracer.isTracing()) {
			try {
				if (log.isDebugEnabled()) {
					log.debug("Wrapping callable with span [" + this.tracer.getCurrentSpan()
							+ "]");
				}
				Field callableField = WebAsyncTask.class.getDeclaredField("callable");
				callableField.setAccessible(true);
				callableField.set(webAsyncTask, new SCTCall<>(this.tracer,
						this.traceKeys, this.spanNamer, webAsyncTask.getCallable()));
			} catch (NoSuchFieldException ex) {
				log.warn("Cannot wrap webAsyncTask's callable with TraceCallable", ex);
			}
		}
		return webAsyncTask;
	}

	@Around("anyHandlerExceptionResolver(request, response, handler, ex)")
	public Object markRequestForSpanClosing(ProceedingJoinPoint pjp,
			HttpServletRequest request, HttpServletResponse response, Object handler, Exception ex) throws Throwable {
		Item currentSpan = this.tracer.getCurrentSpan();
		try {
			if (!currentSpan.tags().containsKey(Item.SPAN_ERROR_TAG_NAME)) {
				this.tracer.addTag(Item.SPAN_ERROR_TAG_NAME, ExceptionUtils.getExceptionMessage(ex));
			}
			return pjp.proceed();
		} finally {
			if (log.isDebugEnabled()) {
				log.debug("Marking span " + currentSpan + " for closure by Trace Filter");
			}
			request.setAttribute(TFilter.TRACE_CLOSE_SPAN_REQUEST_ATTR, true);
		}
	}

}


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/instrument/web/TWAsp.java:TWAsp.<init>
// Node: TWAsp
// Node: Pointcut
// Node: within
// Node: anyRestControllerAnnotated
// Node: anyControllerAnnotated
// Node: anyPublicMethodReturningCallable
// Node: anyControllerOrRestControllerWithPublicAsyncMethod
// Node: anyPublicMethodReturningWebAsyncTask
// Node: resolveException
// Node: args
// Node: anyHandlerExceptionResolver
// Node: anyControllerOrRestControllerWithPublicWebAsyncTaskMethod
// Node: wrapWithCorrelationId
// Node: wrapWebAsyncTaskWithCorrelationId
// Node: getDeclaredField
// Node: setAccessible
// Node: getCallable
// Node: markRequestForSpanClosing


package org.myproject.ms.monitoring.instrument.web;

import javax.servlet.http.HttpServletRequest;
import java.lang.invoke.MethodHandles;
import java.util.Collections;

import org.apache.commons.logging.Log;
import org.apache.commons.logging.LogFactory;
import org.springframework.beans.BeansException;
import org.springframework.beans.factory.BeanFactory;
import org.springframework.beans.factory.config.BeanPostProcessor;
import org.springframework.data.rest.webmvc.support.DelegatingHandlerMapping;
import org.springframework.web.servlet.HandlerExecutionChain;
import org.springframework.web.servlet.HandlerMapping;


class TSDBPProcess implements BeanPostProcessor {

	private static final Log log = LogFactory.getLog(MethodHandles.lookup().lookupClass());

	private final BeanFactory beanFactory;

	public TSDBPProcess(BeanFactory beanFactory) {
		this.beanFactory = beanFactory;
	}

	@Override
	public Object postProcessBeforeInitialization(Object bean, String beanName)
			throws BeansException {
		if (bean instanceof DelegatingHandlerMapping && !(bean instanceof TraceDelegatingHandlerMapping)) {
			if (log.isDebugEnabled()) {
				log.debug("Wrapping bean [" + beanName + "] of type [" + bean.getClass().getSimpleName() +
						"] in its trace representation");
			}
			return new TraceDelegatingHandlerMapping((DelegatingHandlerMapping) bean,
					this.beanFactory);
		}
		return bean;
	}

	@Override
	public Object postProcessAfterInitialization(Object bean, String beanName)
			throws BeansException {
		return bean;
	}

	private static class TraceDelegatingHandlerMapping extends DelegatingHandlerMapping {

		private final DelegatingHandlerMapping delegate;
		private final BeanFactory beanFactory;

		public TraceDelegatingHandlerMapping(DelegatingHandlerMapping delegate,
				BeanFactory beanFactory) {
			super(Collections.<HandlerMapping>emptyList());
			this.delegate = delegate;
			this.beanFactory = beanFactory;
		}

		@Override
		public int getOrder() {
			return this.delegate.getOrder();
		}

		@Override
		public HandlerExecutionChain getHandler(HttpServletRequest request)
				throws Exception {
			HandlerExecutionChain handlerExecutionChain = this.delegate.getHandler(request);
			if (handlerExecutionChain == null) {
				return null;
			}
			handlerExecutionChain.addInterceptor(new THInter(this.beanFactory));
			return handlerExecutionChain;
		}
	}
}


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/instrument/web/TSDBPProcess.java:TSDBPProcess.<init>
// Node: TraceDelegatingHandlerMapping


package org.myproject.ms.monitoring.instrument.web;

import java.io.IOException;
import java.io.PrintWriter;
import java.lang.invoke.MethodHandles;
import javax.servlet.ServletOutputStream;
import javax.servlet.http.HttpServletResponse;
import javax.servlet.http.HttpServletResponseWrapper;

import org.apache.commons.logging.Log;
import org.apache.commons.logging.LogFactory;
import org.myproject.ms.monitoring.Item;


class THSResp extends HttpServletResponseWrapper {

	private static final Log log = LogFactory.getLog(MethodHandles.lookup().lookupClass());

	private final Item span;

	THSResp(HttpServletResponse response, Item span) {
		super(response);
		this.span = span;
	}

	@Override public void flushBuffer() throws IOException {
		if (log.isTraceEnabled()) {
			log.trace("Will annotate SS once the response is flushed");
		}
		SsLogSetter.annotateWithServerSendIfLogIsNotAlreadyPresent(this.span);
		super.flushBuffer();
	}

	@Override public ServletOutputStream getOutputStream() throws IOException {
		return new TSOStr(super.getOutputStream(), this.span);
	}

	@Override public PrintWriter getWriter() throws IOException {
		return new TPWriter(super.getWriter(), this.span);
	}
}


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/instrument/web/THSResp.java:THSResp.<init>


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


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/instrument/web/SsLogSetter.java:SsLogSetter.<init>
package org.myproject.ms.monitoring.instrument.web;

import java.net.URI;
import java.util.Collection;
import java.util.Map;

import org.myproject.ms.monitoring.Item;
import org.myproject.ms.monitoring.ChainKeys;
import org.myproject.ms.monitoring.Chainer;
import org.springframework.util.StringUtils;


public class HTKInject {

	private final Chainer tracer;
	private final ChainKeys traceKeys;

	public HTKInject(Chainer tracer, ChainKeys traceKeys) {
		this.tracer = tracer;
		this.traceKeys = traceKeys;
	}

	
	public void addRequestTags(String url, String host, String path, String method) {
		this.tracer.addTag(this.traceKeys.getHttp().getUrl(), url);
		this.tracer.addTag(this.traceKeys.getHttp().getHost(), host);
		this.tracer.addTag(this.traceKeys.getHttp().getPath(), path);
		this.tracer.addTag(this.traceKeys.getHttp().getMethod(), method);
	}

	
	public void addRequestTags(Item span, String url, String host, String path, String method) {
		tagSpan(span, this.traceKeys.getHttp().getUrl(), url);
		tagSpan(span, this.traceKeys.getHttp().getHost(), host);
		tagSpan(span, this.traceKeys.getHttp().getPath(), path);
		tagSpan(span, this.traceKeys.getHttp().getMethod(), method);
	}

	
	public void addRequestTags(Item span, URI uri, String method) {
		addRequestTags(span, uri.toString(), uri.getHost(), uri.getPath(), method);
	}

	
	public void addRequestTags(String url, String host, String path, String method,
			Map<String, ? extends Collection<String>> headers) {
		addRequestTags(url, host, path, method);
		addRequestTagsFromHeaders(headers);
	}

	
	public void tagSpan(Item span, String key, String value) {
		if (span != null && span.isExportable()) {
			span.tag(key, value);
		}
	}

	private void addRequestTagsFromHeaders(Map<String, ? extends Collection<String>> headers) {
		for (String name : this.traceKeys.getHttp().getHeaders()) {
			for (Map.Entry<String, ? extends Collection<String>> entry : headers.entrySet()) {
				addTagForEntry(name, entry.getValue());
			}
		}
	}

	private void addTagForEntry(String name, Collection<String> list) {
		String key = this.traceKeys.getHttp().getPrefix() + name.toLowerCase();
		String value = list.size() == 1 ? list.iterator().next()
				: StringUtils.collectionToDelimitedString(list, ",", "'", "'");
		this.tracer.addTag(key, value);
	}

}


// Node: addRequestTagsFromHeaders
// Node: addTagForEntry


package org.myproject.ms.monitoring.instrument.web;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;


class ServletUtils {

	static String getHeader(HttpServletRequest request, HttpServletResponse response,
			String name) {
		String value = request.getHeader(name);
		return value != null ? value : response.getHeader(name);
	}

}


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/instrument/web/ServletUtils.java:ServletUtils.<init>


package org.myproject.ms.monitoring.instrument.web;


public final class TRAttr {

	
	public static final String HANDLED_SPAN_REQUEST_ATTR = TRAttr.class.getName()
			+ ".TRACE_HANDLED";

	
	public static final String ERROR_HANDLED_SPAN_REQUEST_ATTR = TRAttr.class.getName()
			+ ".ERROR_TRACE_HANDLED";

	
	public static final String NEW_SPAN_REQUEST_ATTR = TRAttr.class.getName()
			+ ".TRACE_HANDLED_NEW_SPAN";

	
	public static final String SPAN_CONTINUED_REQUEST_ATTR = TRAttr.class.getName()
					+ ".TRACE_CONTINUED";

	private TRAttr() {}
}


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/instrument/web/TRAttr.java:TRAttr.<init>
// Node: TRAttr


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


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/instrument/web/HSRTMap.java:HSRTMap.<init>
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


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/instrument/web/ZHSExtra.java:ZHSExtra.<init>


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


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/instrument/web/THInter.java:THInter.<init>
// Node: preHandle
// Node: spanName
// Node: getRootSpanFromAttribute
// Node: addClassMethodTag
// Node: addClassNameTag
// Node: setSpanInAttribute
// Node: setNewSpanCreatedAttribute
// Node: isErrorControllerRelated
// Node: getErrorController
// Node: getErrorPath
// Node: getBeanType
// Node: afterConcurrentHandlingStarted
// Node: afterCompletion
// Node: clearNewSpanCreatedAttribute
// Node: publishStartEvent


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


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/instrument/web/client/THResp.java:THResp.<init>
// Node: THResp
// Node: finish


package org.myproject.ms.monitoring.instrument.web.client;

import java.lang.invoke.MethodHandles;
import java.net.URI;

import org.apache.commons.logging.Log;
import org.apache.commons.logging.LogFactory;
import org.myproject.ms.monitoring.instrument.web.HSInject;
import org.myproject.ms.monitoring.Item;
import org.myproject.ms.monitoring.Chainer;
import org.myproject.ms.monitoring.instrument.web.HTKInject;
import org.myproject.ms.monitoring.util.ItemNameUtil;
import org.springframework.http.HttpRequest;

abstract class ATHRInter {

	protected static final Log log = LogFactory.getLog(MethodHandles.lookup().lookupClass());

	protected final Chainer tracer;
	protected final HSInject spanInjector;
	protected final HTKInject keysInjector;

	protected ATHRInter(Chainer tracer,
			HSInject spanInjector, HTKInject keysInjector) {
		this.tracer = tracer;
		this.spanInjector = spanInjector;
		this.keysInjector = keysInjector;
	}

	
	protected void publishStartEvent(HttpRequest request) {
		URI uri = request.getURI();
		String spanName = getName(uri);
		Item newSpan = this.tracer.createSpan(spanName);
		this.spanInjector.inject(newSpan, new HRTMap(request));
		addRequestTags(request);
		newSpan.logEvent(Item.CLIENT_SEND);
		if (log.isDebugEnabled()) {
			log.debug("Starting new client span [" + newSpan + "]");
		}
	}

	private String getName(URI uri) {
		return ItemNameUtil.shorten(uriScheme(uri) + ":" + uri.getPath());
	}

	private String uriScheme(URI uri) {
		return uri.getScheme() == null ? "http" : uri.getScheme();
	}

	
	protected void addRequestTags(HttpRequest request) {
		this.keysInjector.addRequestTags(request.getURI().toString(),
				request.getURI().getHost(),
				request.getURI().getPath(),
				request.getMethod().name(),
				request.getHeaders());
	}

	
	public void finish() {
		if (!isTracing()) {
			return;
		}
		currentSpan().logEvent(Item.CLIENT_RECV);
		this.tracer.close(this.currentSpan());
	}

	protected Item currentSpan() {
		return this.tracer.getCurrentSpan();
	}

	protected boolean isTracing() {
		return this.tracer.isTracing();
	}

}


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/instrument/web/client/ATHRInter.java:ATHRInter.<init>
// Node: ATHRInter
// Node: getURI
// Node: HRTMap
// Node: uriScheme
// Node: currentSpan


package org.myproject.ms.monitoring.instrument.web.client;

import java.io.IOException;

import org.myproject.ms.monitoring.instrument.web.HSInject;
import org.myproject.ms.monitoring.Item;
import org.myproject.ms.monitoring.Chainer;
import org.myproject.ms.monitoring.instrument.web.HTKInject;
import org.myproject.ms.monitoring.util.ExceptionUtils;
import org.springframework.http.HttpRequest;
import org.springframework.http.client.ClientHttpRequestExecution;
import org.springframework.http.client.ClientHttpRequestInterceptor;
import org.springframework.http.client.ClientHttpResponse;


public class TRTInter extends ATHRInter
		implements ClientHttpRequestInterceptor {

	public TRTInter(Chainer tracer, HSInject spanInjector,
			HTKInject httpTraceKeysInjector) {
		super(tracer, spanInjector, httpTraceKeysInjector);
	}

	@Override
	public ClientHttpResponse intercept(HttpRequest request, byte[] body,
			ClientHttpRequestExecution execution) throws IOException {
		publishStartEvent(request);
		return response(request, body, execution);
	}

	private ClientHttpResponse response(HttpRequest request, byte[] body,
			ClientHttpRequestExecution execution) throws IOException {
		try {
			return new THResp(this, execution.execute(request, body));
		} catch (Exception e) {
			if (log.isDebugEnabled()) {
				log.debug("Exception occurred while trying to execute the request. Will close the span [" + currentSpan() + "]", e);
			}
			this.tracer.addTag(Item.SPAN_ERROR_TAG_NAME, ExceptionUtils.getExceptionMessage(e));
			finish();
			throw e;
		}
	}

}


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/instrument/web/client/TRTInter.java:TRTInter.<init>
// Node: intercept
// Node: response


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


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/instrument/web/client/TARTemp.java:TARTemp.<init>
// Node: doExecute
// Node: addCallback
// Node: TraceFailureCallback
// Node: TraceSuccessCallback
// Node: onSuccess
// Node: TraceListenableFutureCallbackWrapper
// Node: onFailure


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


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/instrument/web/client/HRTMap.java:HRTMap.<init>


package org.myproject.ms.monitoring.instrument.rest;

import org.myproject.ms.monitoring.Item;
import org.myproject.ms.monitoring.Chainer;
import org.myproject.ms.monitoring.ChainKeys;

import com.netflix.hystrix.HystrixCommand;


public abstract class TComm<R> extends HystrixCommand<R> {

	private static final String HYSTRIX_COMPONENT = "hystrix";

	private final Chainer tracer;
	private final ChainKeys traceKeys;
	private final Item parentSpan;

	protected TComm(Chainer tracer, ChainKeys traceKeys, Setter setter) {
		super(setter);
		this.tracer = tracer;
		this.traceKeys = traceKeys;
		this.parentSpan = tracer.getCurrentSpan();
	}

	@Override
	protected R run() throws Exception {
		String commandKeyName = getCommandKey().name();
		Item span = startSpan(commandKeyName);
		this.tracer.addTag(Item.SPAN_LOCAL_COMPONENT_TAG_NAME, HYSTRIX_COMPONENT);
		this.tracer.addTag(this.traceKeys.getHystrix().getPrefix() +
				this.traceKeys.getHystrix().getCommandKey(), commandKeyName);
		this.tracer.addTag(this.traceKeys.getHystrix().getPrefix() +
				this.traceKeys.getHystrix().getCommandGroup(), getCommandGroup().name());
		this.tracer.addTag(this.traceKeys.getHystrix().getPrefix() +
				this.traceKeys.getHystrix().getThreadPoolKey(), getThreadPoolKey().name());
		try {
			return doRun();
		}
		finally {
			close(span);
		}
	}

	private Item startSpan(String commandKeyName) {
		Item span = this.parentSpan;
		if (span == null) {
			return this.tracer.createSpan(commandKeyName, this.parentSpan);
		}
		return this.tracer.continueSpan(span);
	}

	private void close(Item span) {
		if (this.parentSpan == null) {
			this.tracer.close(span);
		} else {
			this.tracer.detach(span);
		}
	}

	public abstract R doRun() throws Exception;
}


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/instrument/rest/TComm.java:TComm.<init>
// Node: TComm
// Node: doRun


package org.myproject.ms.monitoring.instrument.rest;

import java.lang.invoke.MethodHandles;
import java.util.concurrent.Callable;

import org.apache.commons.logging.Log;
import org.apache.commons.logging.LogFactory;
import org.myproject.ms.monitoring.Item;
import org.myproject.ms.monitoring.ChainKeys;
import org.myproject.ms.monitoring.Chainer;

import com.netflix.hystrix.strategy.HystrixPlugins;
import com.netflix.hystrix.strategy.concurrency.HystrixConcurrencyStrategy;
import com.netflix.hystrix.strategy.eventnotifier.HystrixEventNotifier;
import com.netflix.hystrix.strategy.executionhook.HystrixCommandExecutionHook;
import com.netflix.hystrix.strategy.metrics.HystrixMetricsPublisher;
import com.netflix.hystrix.strategy.properties.HystrixPropertiesStrategy;


public class SHCStra extends HystrixConcurrencyStrategy {

	private static final String HYSTRIX_COMPONENT = "hystrix";
	private static final Log log = LogFactory
			.getLog(SHCStra.class);

	private final Chainer tracer;
	private final ChainKeys traceKeys;
	private HystrixConcurrencyStrategy delegate;

	public SHCStra(Chainer tracer, ChainKeys traceKeys) {
		this.tracer = tracer;
		this.traceKeys = traceKeys;
		try {
			this.delegate = HystrixPlugins.getInstance().getConcurrencyStrategy();
			if (this.delegate instanceof SHCStra) {
				// Welcome to singleton hell...
				return;
			}
			HystrixCommandExecutionHook commandExecutionHook = HystrixPlugins
					.getInstance().getCommandExecutionHook();
			HystrixEventNotifier eventNotifier = HystrixPlugins.getInstance()
					.getEventNotifier();
			HystrixMetricsPublisher metricsPublisher = HystrixPlugins.getInstance()
					.getMetricsPublisher();
			HystrixPropertiesStrategy propertiesStrategy = HystrixPlugins.getInstance()
					.getPropertiesStrategy();
			logCurrentStateOfHysrixPlugins(eventNotifier, metricsPublisher,
					propertiesStrategy);
			HystrixPlugins.reset();
			HystrixPlugins.getInstance().registerConcurrencyStrategy(this);
			HystrixPlugins.getInstance()
					.registerCommandExecutionHook(commandExecutionHook);
			HystrixPlugins.getInstance().registerEventNotifier(eventNotifier);
			HystrixPlugins.getInstance().registerMetricsPublisher(metricsPublisher);
			HystrixPlugins.getInstance().registerPropertiesStrategy(propertiesStrategy);
		}
		catch (Exception e) {
			log.error("Failed to register Sleuth Hystrix Concurrency Strategy", e);
		}
	}

	private void logCurrentStateOfHysrixPlugins(HystrixEventNotifier eventNotifier,
			HystrixMetricsPublisher metricsPublisher,
			HystrixPropertiesStrategy propertiesStrategy) {
		if (log.isDebugEnabled()) {
			log.debug("Current Hystrix plugins configuration is [" + "concurrencyStrategy ["
					+ this.delegate + "]," + "eventNotifier [" + eventNotifier + "],"
					+ "metricPublisher [" + metricsPublisher + "]," + "propertiesStrategy ["
					+ propertiesStrategy + "]," + "]");
			log.debug("Registering Sleuth Hystrix Concurrency Strategy.");
		}
	}

	@Override
	public <T> Callable<T> wrapCallable(Callable<T> callable) {
		if (callable instanceof HystrixTraceCallable) {
			return callable;
		}
		Callable<T> wrappedCallable = this.delegate != null
				? this.delegate.wrapCallable(callable) : callable;
		if (wrappedCallable instanceof HystrixTraceCallable) {
			return wrappedCallable;
		}
		return new HystrixTraceCallable<>(this.tracer, this.traceKeys, wrappedCallable);
	}

	// Visible for testing
	static class HystrixTraceCallable<S> implements Callable<S> {

		private static final Log log = LogFactory.getLog(MethodHandles.lookup().lookupClass());

		private Chainer tracer;
		private ChainKeys traceKeys;
		private Callable<S> callable;
		private Item parent;

		public HystrixTraceCallable(Chainer tracer, ChainKeys traceKeys,
				Callable<S> callable) {
			this.tracer = tracer;
			this.traceKeys = traceKeys;
			this.callable = callable;
			this.parent = tracer.getCurrentSpan();
		}

		@Override
		public S call() throws Exception {
			Item span = this.parent;
			boolean created = false;
			if (span != null) {
				span = this.tracer.continueSpan(span);
				if (log.isDebugEnabled()) {
					log.debug("Continuing span " + span);
				}
			}
			else {
				span = this.tracer.createSpan(HYSTRIX_COMPONENT);
				created = true;
				if (log.isDebugEnabled()) {
					log.debug("Creating new span " + span);
				}
			}
			if (!span.tags().containsKey(Item.SPAN_LOCAL_COMPONENT_TAG_NAME)) {
				this.tracer.addTag(Item.SPAN_LOCAL_COMPONENT_TAG_NAME, HYSTRIX_COMPONENT);
			}
			String asyncKey = this.traceKeys.getAsync().getPrefix()
					+ this.traceKeys.getAsync().getThreadNameKey();
			if (!span.tags().containsKey(asyncKey)) {
				this.tracer.addTag(asyncKey, Thread.currentThread().getName());
			}
			try {
				return this.callable.call();
			}
			finally {
				if (created) {
					if (log.isDebugEnabled()) {
						log.debug("Closing span since it was created" + span);
					}
					this.tracer.close(span);
				}
				else if(this.tracer.isTracing()) {
					if (log.isDebugEnabled()) {
						log.debug("Detaching span since it was continued " + span);
					}
					this.tracer.detach(span);
				}
			}
		}

	}
}


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/instrument/rest/SHCStra.java:SHCStra.<init>
// Node: SHCStra
// Node: getConcurrencyStrategy
// Node: getCommandExecutionHook
// Node: getEventNotifier
// Node: getMetricsPublisher
// Node: getPropertiesStrategy
// Node: logCurrentStateOfHysrixPlugins
// Node: registerConcurrencyStrategy
// Node: registerCommandExecutionHook
// Node: registerEventNotifier
// Node: registerMetricsPublisher
// Node: registerPropertiesStrategy
// Node: wrapCallable
// Node: HystrixTraceCallable
package org.myproject.ms.monitoring.instrument.rest;

import org.springframework.boot.autoconfigure.AutoConfigureAfter;
import org.springframework.boot.autoconfigure.condition.ConditionalOnBean;
import org.springframework.boot.autoconfigure.condition.ConditionalOnClass;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.myproject.ms.monitoring.ChainKeys;
import org.myproject.ms.monitoring.Chainer;
import org.myproject.ms.monitoring.atcfg.TraceAutoConfiguration;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import com.netflix.hystrix.HystrixCommand;


@Configuration
@AutoConfigureAfter(TraceAutoConfiguration.class)
@ConditionalOnClass(HystrixCommand.class)
@ConditionalOnBean(Chainer.class)
@ConditionalOnProperty(value = "spring.sleuth.hystrix.strategy.enabled", matchIfMissing = true)
public class SHAConf {

	@Bean
	SHCStra sleuthHystrixConcurrencyStrategy(Chainer tracer, ChainKeys traceKeys) {
		return new SHCStra(tracer, traceKeys);
	}

}


// Node: sleuthHystrixConcurrencyStrategy
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


package user.dto;

/**
 * @author fdse
 */
public enum Gender {

    /**
     * null
     */
    NONE(0, "Null"),
    /**
     * male
     */
    MALE(1, "Male"),
    /**
     * female
     */
    FEMALE(2, "Female"),
    /**
     * other
     */
    OTHER(3, "Other");

    private int code;
    private String name;

    Gender(int code, String name) {
        this.code = code;
        this.name = name;
    }

    public int getCode() {
        return code;
    }

    public String getName() {
        return name;
    }

    public static String getNameByCode(int code) {
        Gender[] genderSet = Gender.values();
        for (Gender gender : genderSet) {
            if (gender.getCode() == code) {
                return gender.getName();
            }
        }
        return genderSet[0].getName();
    }

}


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


package contacts.entity;

/**
 * @author fdse
 */
public enum DocumentType {

    /**
     * null
     */
    NONE      (0,"Null"),
    /**
     * id card
     */
    ID_CARD   (1,"ID Card"),
    /**
     * passport
     */
    PASSPORT  (2,"Passport"),
    /**
     * other
     */
    OTHER     (3,"Other");

    private int code;
    private String name;

    DocumentType(int code, String name){
        this.code = code;
        this.name = name;
    }

    public int getCode(){
        return code;
    }

    public String getName() {
        return name;
    }

    public static String getNameByCode(int code){
        DocumentType[] documentTypeSet = DocumentType.values();
        for(DocumentType documentType : documentTypeSet){
            if(documentType.getCode() == code){
                return documentType.getName();
            }
        }
        return documentTypeSet[0].getName();
    }
}


