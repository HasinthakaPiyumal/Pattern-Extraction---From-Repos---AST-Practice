// Cluster 116

// Node: getTime
// Node: sleep
// Node: size
// Node: equals
// Node: getInstance
package auth.exception;

/**
 * @author fdse
 */
public class UserOperationException extends RuntimeException {
    private static final long serialVersionUID = 8468616518092020748L;

    public UserOperationException(String msg) {
        super(msg);
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-auth-service/src/main/java/auth/exception/UserOperationException.java:UserOperationException.<init>
// Node: UserOperationException
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


// Node: format
// Node: length
// Node: UsernamePasswordAuthenticationToken
// Node: authenticate
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


// Node: isEnabled
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


// Node: SimpleDateFormat
// Node: parse
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


// Node: startsWith
// Node: println
// Node: Random
// Node: nextInt
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


// Node: isRequestedSessionIdFromUrl
// Node: login
// Node: logout
// Node: getParts
// Node: getPart
// Node: upgrade
// Node: getAttribute
// Node: tripGD
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




package org.myproject.ms.monitoring;


public interface Sampler {
	
	boolean isSampled(Item span);
}


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/Sampler.java:Sampler.<init>
// Node: isSampled
// Node: clear


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




package org.myproject.ms.monitoring;


public class NOItemReporter implements ItemReporter {
	@Override
	public void report(Item span) {

	}
}


// Node: report


package org.myproject.ms.monitoring;


public interface ItemReporter {
	
	void report(Item span);
}


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/ItemReporter.java:ItemReporter.<init>
package org.myproject.ms.monitoring.lgger;

import org.springframework.boot.context.properties.ConfigurationProperties;


@ConfigurationProperties("spring.sleuth.log.slf4j")
public class Slf4jProps {

	
	private boolean enabled = true;

	
	private String nameSkipPattern = "";

	public boolean isEnabled() {
		return this.enabled;
	}

	public void setEnabled(boolean enabled) {
		this.enabled = enabled;
	}

	public String getNameSkipPattern() {
		return this.nameSkipPattern;
	}

	public void setNameSkipPattern(String nameSkipPattern) {
		this.nameSkipPattern = nameSkipPattern;
	}
}




package org.myproject.ms.monitoring.util;

import java.util.ArrayList;
import java.util.List;

import org.myproject.ms.monitoring.Item;
import org.myproject.ms.monitoring.ItemReporter;


public class ArrayListItemAccum implements ItemReporter {
	private final List<Item> spans = new ArrayList<>();

	public List<Item> getSpans() {
		synchronized (this.spans) {
			return this.spans;
		}
	}

	@Override
	public String toString() {
		return "ArrayListSpanAccumulator{" +
				"spans=" + getSpans() +
				'}';
	}

	@Override
	public void report(Item span) {
		synchronized (this.spans) {
			this.spans.add(span);
		}
	}

	public void clear() {
		synchronized (this.spans) {
			this.spans.clear();
		}
	}
}


// Node: getSpans
// Node: synchronized
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


// Node: getMatchOutcome
// Node: getEnvironment
// Node: getProperty
// Node: matchCondition
// Node: match
// Node: noMatch


package org.myproject.ms.monitoring.spl;

import org.myproject.ms.monitoring.Sampler;
import org.myproject.ms.monitoring.Item;
import org.myproject.ms.monitoring.ItemAccessor;


public class IsChainingSampler implements Sampler {

	private ItemAccessor accessor;

	public IsChainingSampler(ItemAccessor accessor) {
		this.accessor = accessor;
	}

	@Override
	public boolean isSampled(Item span) {
		return this.accessor.isTracing();
	}
}




package org.myproject.ms.monitoring.spl;

import org.myproject.ms.monitoring.Sampler;
import org.myproject.ms.monitoring.Item;


public class NeverSampler implements Sampler {

	public static final NeverSampler INSTANCE = new NeverSampler();

	@Override
	public boolean isSampled(Item span) {
		return false;
	}
}




package org.myproject.ms.monitoring.spl;

import org.myproject.ms.monitoring.Sampler;
import org.myproject.ms.monitoring.Item;


public class AlwaysSampler implements Sampler {
	@Override
	public boolean isSampled(Item span) {
		return true;
	}
}


package org.myproject.ms.monitoring.spl;

import org.springframework.boot.context.properties.ConfigurationProperties;


@ConfigurationProperties("spring.sleuth.sampler")
public class SProps {

	
	private float percentage = 0.1f;

	public float getPercentage() {
		return this.percentage;
	}

	public void setPercentage(float percentage) {
		this.percentage = percentage;
	}
}


// Node: getPercentage
package org.myproject.ms.monitoring.spl;

import java.util.BitSet;
import java.util.Random;
import java.util.concurrent.atomic.AtomicInteger;

import org.myproject.ms.monitoring.Sampler;
import org.myproject.ms.monitoring.Item;


public class PBSamp implements Sampler {

	private final AtomicInteger counter = new AtomicInteger(0);
	private final BitSet sampleDecisions;
	private final SProps configuration;

	public PBSamp(SProps configuration) {
		int outOf100 = (int) (configuration.getPercentage() * 100.0f);
		this.sampleDecisions = randomBitSet(100, outOf100, new Random());
		this.configuration = configuration;
	}

	@Override
	public boolean isSampled(Item currentSpan) {
		if (this.configuration.getPercentage() == 0 || currentSpan == null) {
			return false;
		} else if (this.configuration.getPercentage() == 100) {
			return true;
		}
		synchronized (this) {
			final int i = this.counter.getAndIncrement();
			boolean result = this.sampleDecisions.get(i);
			if (i == 99) {
				this.counter.set(0);
			}
			return result;
		}
	}

	
	static BitSet randomBitSet(int size, int cardinality, Random rnd) {
		BitSet result = new BitSet(size);
		int[] chosen = new int[cardinality];
		int i;
		for (i = 0; i < cardinality; ++i) {
			chosen[i] = i;
			result.set(i);
		}
		for (; i < size; ++i) {
			int j = rnd.nextInt(i + 1);
			if (j < cardinality) {
				result.clear(chosen[j]);
				result.set(i);
				chosen[j] = i;
			}
		}
		return result;
	}
}


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/spl/PBSamp.java:PBSamp.<init>
// Node: AtomicInteger
// Node: PBSamp
// Node: randomBitSet
// Node: getAndIncrement
// Node: BitSet


package org.myproject.ms.monitoring.antn;

import org.springframework.boot.context.properties.ConfigurationProperties;


@ConfigurationProperties("spring.sleuth.annotation")
public class SleuthAnnotationProperties {

	private boolean enabled = true;

	public boolean isEnabled() {
		return this.enabled;
	}

	public void setEnabled(boolean enabled) {
		this.enabled = enabled;
	}
}


// Node: AnnotationClassOrMethodFilter


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


// Node: nullSafeEquals
// Node: AnnotationMethodsResolver
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


// Node: prefixedKey
package org.myproject.ms.monitoring.instrument.schedl;

import org.springframework.boot.context.properties.ConfigurationProperties;


@ConfigurationProperties("spring.sleuth.scheduled")
public class SSProp {

	
	private boolean enabled = true;

	
	private String skipPattern = "";

	public boolean isEnabled() {
		return this.enabled;
	}

	public void setEnabled(boolean enabled) {
		this.enabled = enabled;
	}

	public String getSkipPattern() {
		return this.skipPattern;
	}

	public void setSkipPattern(String skipPattern) {
		this.skipPattern = skipPattern;
	}
}




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


// Node: printf
package org.myproject.ms.monitoring.instrument.web;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.boot.context.properties.NestedConfigurationProperty;


@ConfigurationProperties("spring.sleuth.web")
public class SWProp {

	public static final String DEFAULT_SKIP_PATTERN =
			"/api-docs.*|/autoconfig|/configprops|/dump|/health|/info|/metrics.*|/mappings|/trace|/swagger.*|.*\\.png|.*\\.css|.*\\.js|.*\\.html|/favicon.ico|/hystrix.stream";

	
	private boolean enabled = true;

	
	private String skipPattern = DEFAULT_SKIP_PATTERN;

	private Client client;

	public boolean isEnabled() {
		return this.enabled;
	}

	public void setEnabled(boolean enabled) {
		this.enabled = enabled;
	}

	public String getSkipPattern() {
		return this.skipPattern;
	}

	public void setSkipPattern(String skipPattern) {
		this.skipPattern = skipPattern;
	}

	public Client getClient() {
		return this.client;
	}

	public void setClient(Client client) {
		this.client = client;
	}

	public static class Client {

		
		private boolean enabled = true;

		public boolean isEnabled() {
			return this.enabled;
		}

		public void setEnabled(boolean enabled) {
			this.enabled = enabled;
		}
	}

	public static class Async {

		@NestedConfigurationProperty
		private AsyncClient client;

		public AsyncClient getClient() {
			return this.client;
		}

		public void setClient(AsyncClient client) {
			this.client = client;
		}
	}

	public static class AsyncClient {

		
		private boolean enabled;

		@NestedConfigurationProperty
		private Template template;

		public boolean isEnabled() {
			return this.enabled;
		}

		public void setEnabled(boolean enabled) {
			this.enabled = enabled;
		}

		public Template getTemplate() {
			return this.template;
		}

		public void setTemplate(Template template) {
			this.template = template;
		}
	}

	public static class Template {

		
		private boolean enabled;

		public boolean isEnabled() {
			return this.enabled;
		}

		public void setEnabled(boolean enabled) {
			this.enabled = enabled;
		}
	}
}


// Node: errorAlreadyHandled
// Node: shouldCloseSpan

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


// Node: getNewSpanFromAttribute


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




package org.myproject.ms.monitoring.atcfg;

import java.util.Random;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.autoconfigure.condition.ConditionalOnMissingBean;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.myproject.ms.monitoring.DefaultItemNamer;
import org.myproject.ms.monitoring.NOItemAdjuster;
import org.myproject.ms.monitoring.NOItemReporter;
import org.myproject.ms.monitoring.Sampler;
import org.myproject.ms.monitoring.ItemAdjuster;
import org.myproject.ms.monitoring.ItemNamer;
import org.myproject.ms.monitoring.ItemReporter;
//import org.myproject.ms.monitoring.StateSpanAdjuster;
import org.myproject.ms.monitoring.ChainKeys;
import org.myproject.ms.monitoring.Chainer;
import org.myproject.ms.monitoring.lgger.ItemLogger;
import org.myproject.ms.monitoring.spl.NeverSampler;
import org.myproject.ms.monitoring.trace.DChainer;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;


@Configuration
@ConditionalOnProperty(value="spring.sleuth.enabled", matchIfMissing=true)
@EnableConfigurationProperties({ChainKeys.class, SleuthProperties.class})
public class TraceAutoConfiguration {
	@Autowired
	SleuthProperties properties;

	@Bean
	@ConditionalOnMissingBean
	public Random randomForSpanIds() {
		return new Random();
	}

	@Bean
	@ConditionalOnMissingBean
	public Sampler defaultTraceSampler() {
		return NeverSampler.INSTANCE;
	}

	@Bean
	@ConditionalOnMissingBean(Chainer.class)
	public DChainer sleuthTracer(Sampler sampler, Random random,
			ItemNamer spanNamer, ItemLogger spanLogger,
			ItemReporter spanReporter, ChainKeys traceKeys) {
		return new DChainer(sampler, random, spanNamer, spanLogger,
				spanReporter, this.properties.isTraceId128(), traceKeys);
	}

	@Bean
	@ConditionalOnMissingBean
	public ItemNamer spanNamer() {
		return new DefaultItemNamer();
	}

	@Bean
	@ConditionalOnMissingBean
	public ItemReporter defaultSpanReporter() {
		return new NOItemReporter();
	}

	@Bean
	@ConditionalOnMissingBean
	public ItemAdjuster defaultSpanAdjuster() {
		return new NOItemAdjuster();
//		return new StateSpanAdjuster();
	}

}


// Node: randomForSpanIds


package org.myproject.ms.monitoring.atcfg;

import org.springframework.boot.context.properties.ConfigurationProperties;


@ConfigurationProperties("spring.sleuth")
public class SleuthProperties {

	private boolean enabled = true;
	
	private boolean traceId128 = false;

	public boolean isEnabled() {
		return this.enabled;
	}

	public void setEnabled(boolean enabled) {
		this.enabled = enabled;
	}

	public boolean isTraceId128() {
		return this.traceId128;
	}

	public void setTraceId128(boolean traceId128) {
		this.traceId128 = traceId128;
	}
}


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



import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.chrome.ChromeDriver;
import org.testng.annotations.AfterClass;
import org.testng.annotations.BeforeClass;
import org.testng.annotations.Test;

import java.util.concurrent.TimeUnit;

import static org.junit.Assert.assertEquals;


public class TestServiceSSO {
    private WebDriver driver;
    private String baseUrl;
    @BeforeClass
    public void setUp() throws Exception {
        System.setProperty("webdriver.chrome.driver", "D:/Program/chromedriver_win32/chromedriver.exe");
        driver = new ChromeDriver();
        baseUrl = "http://10.141.212.24/";
        driver.manage().timeouts().implicitlyWait(30, TimeUnit.SECONDS);
    }
    @Test
    public void testSSOAccount() throws Exception {
        driver.get(baseUrl + "/");
        driver.findElement(By.id("refresh_account_button")).click();
        driver.findElement(By.id("refresh_login_account_button")).click();
    }
    @AfterClass
    public void tearDown() throws Exception {
        driver.quit();
    }
}



// Node: repos/cloned_ms_repos/train-ticket/old-docs/ts-ui-test/src/test/java/TestServiceSSO.java:TestServiceSSO.<init>
// Node: setProperty
// Node: ChromeDriver
// Node: manage
// Node: timeouts
// Node: implicitlyWait
// Node: testSSOAccount
// Node: findElement
// Node: id
// Node: click
// Node: tearDown
// Node: quit
import org.openqa.selenium.By;
import org.openqa.selenium.JavascriptExecutor;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.support.ui.Select;
import org.testng.Assert;
import org.testng.annotations.AfterClass;
import org.testng.annotations.BeforeClass;
import org.testng.annotations.Test;

import java.util.concurrent.TimeUnit;

public class TestServiceNotification {
    private WebDriver driver;
    private String baseUrl;
    @BeforeClass
    public void setUp() throws Exception {
        System.setProperty("webdriver.chrome.driver", "D:/Program/chromedriver_win32/chromedriver.exe");
        driver = new ChromeDriver();
        baseUrl = "http://10.141.212.24/";
        driver.manage().timeouts().implicitlyWait(30, TimeUnit.SECONDS);
    }
    @Test
    public void testNotification() throws Exception{
        driver.get(baseUrl + "/");
        JavascriptExecutor js = (JavascriptExecutor) driver;
        js.executeScript("document.getElementById('notification_email').value='daihongok@163.com'");
        js.executeScript("document.getElementById('notification_orderNumber').value='123456789'");
        js.executeScript("document.getElementById('notification_username').value='fdse_microservices'");
        js.executeScript("document.getElementById('notification_startingPlace').value='Shang Hai'");
        js.executeScript("document.getElementById('notification_endPlace').value='Tai Yuan'");

        String jsstartingTime = "document.getElementById('notification_startingTime').value='11:55'";
        js.executeScript(jsstartingTime);
        String jssendTime = "document.getElementById('notification_date').value='2017-8-8'";
        js.executeScript(jssendTime);

        js.executeScript("document.getElementById('ticketinfo_startingPlace').value='Shang Hai'");
        js.executeScript("document.getElementById('ticketinfo_endPlace').value='Tai Yuan'");

        js.executeScript("document.getElementById('notification_seatClass').value='economyClass'");
        js.executeScript("document.getElementById('notification_seatNumber').value='2'");
        js.executeScript("document.getElementById('notification_price').value='1000'");

        WebElement elementNotificationtype = driver.findElement(By.id("notification_type"));
        Select selNotifType = new Select(elementNotificationtype);
        selNotifType.selectByValue("0"); //Preserve Success
        driver.findElement(By.id("notification_send_email_button")).click();
        Thread.sleep(1000);

        //get Notification status
        String statusSendemail = driver.findElement(By.id("notification_result")).getText();
        if("".equals(statusSendemail))
            System.out.println("Failed to Send email! Send email status is NULL");
        else if(statusSendemail.startsWith("true"))
            System.out.println("Send email status:"+statusSendemail);
        else
            System.out.println("Failed to Send email! Send email status："+statusSendemail);
        Assert.assertEquals(statusSendemail.startsWith("true"),true);
    }
    @AfterClass
    public void tearDown() throws Exception {
        driver.quit();
    }
}


// Node: repos/cloned_ms_repos/train-ticket/old-docs/ts-ui-test/src/test/java/TestServiceNotification.java:TestServiceNotification.<init>
// Node: testNotification
// Node: executeScript
// Node: getElementById
// Node: Select
// Node: selectByValue
// Node: getText
import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.chrome.ChromeDriver;
import org.testng.Assert;
import org.testng.annotations.AfterClass;
import org.testng.annotations.BeforeClass;
import org.testng.annotations.Test;

import java.util.List;
import java.util.concurrent.TimeUnit;


public class TestServiceExecute {
    private WebDriver driver;
    private String baseUrl;
    @BeforeClass
    public void setUp() throws Exception {
        System.setProperty("webdriver.chrome.driver", "D:/Program/chromedriver_win32/chromedriver.exe");
        driver = new ChromeDriver();
        baseUrl = "http://10.141.212.24/";
        driver.manage().timeouts().implicitlyWait(30, TimeUnit.SECONDS);
    }
    @Test
    public void testExecute() throws Exception {
        driver.get(baseUrl + "/");
        driver.findElement(By.id("execute_order_id")).clear();
        driver.findElement(By.id("execute_order_id")).sendKeys("5ad7750b-a68b-49c0-a8c0-32776b067703");
        driver.findElement(By.id("execute_order_button")).click();
        Thread.sleep(1000);
        String statusExecute = driver.findElement(By.id("execute_order_message")).getText();
        if (!"".equals(statusExecute))
            System.out.println("Success: "+statusExecute);
        else
            System.out.println("False, status security check is null!");
        Assert.assertEquals(statusExecute.equals(""),false);
    }
    @AfterClass
    public void tearDown() throws Exception {
        driver.quit();
    }
}


// Node: repos/cloned_ms_repos/train-ticket/old-docs/ts-ui-test/src/test/java/TestServiceExecute.java:TestServiceExecute.<init>
// Node: testExecute
// Node: sendKeys
import org.openqa.selenium.*;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.support.ui.Select;
import org.testng.Assert;
import org.testng.annotations.AfterClass;
import org.testng.annotations.BeforeClass;
import org.testng.annotations.Test;

import java.text.SimpleDateFormat;
import java.util.Calendar;
import java.util.List;
import java.util.Random;
import java.util.concurrent.TimeUnit;


public class TestServiceRebook {
    private WebDriver driver;
    private String baseUrl;
    private String orderId = "";
    public static void login(WebDriver driver,String username,String password){
        driver.findElement(By.id("flow_one_page")).click();
        driver.findElement(By.id("flow_preserve_login_email")).clear();
        driver.findElement(By.id("flow_preserve_login_email")).sendKeys(username);
        driver.findElement(By.id("flow_preserve_login_password")).clear();
        driver.findElement(By.id("flow_preserve_login_password")).sendKeys(password);
        driver.findElement(By.id("flow_preserve_login_button")).click();
    }
    @BeforeClass
    public void setUp() throws Exception {
        System.setProperty("webdriver.chrome.driver", "D:/Program/chromedriver_win32/chromedriver.exe");
        driver = new ChromeDriver();
        baseUrl = "http://10.141.212.24/";
        driver.manage().timeouts().implicitlyWait(30, TimeUnit.SECONDS);
    }
    @Test
    public void login()throws Exception{
        driver.get(baseUrl + "/");
        //Go to flow_one_page

        //define username and password
        String username = "fdse_microservices@163.com";
        String password = "DefaultPassword";

        //call function login
        login(driver,username,password);
        Thread.sleep(1000);

        //get login status
        String statusLogin = driver.findElement(By.id("flow_preserve_login_msg")).getText();
        if("".equals(statusLogin))
            System.out.println("Failed to Login! Status is Null!");
        else if(statusLogin.startsWith("Success"))
            System.out.println("Success to Login! Status:"+statusLogin);
        else
            System.out.println("Failed to Login! Status:"+statusLogin);

        Assert.assertEquals(statusLogin.startsWith("Success"),true);
        driver.findElement(By.id("microservice_page")).click();
    }
    @Test (dependsOnMethods = {"login"})
    public void getOrders()throws Exception{

        WebElement elementRefreshOrdersBtn = driver.findElement(By.id("refresh_order_button"));
        WebElement elementOrdertypeGTCJ = driver.findElement(By.xpath("//*[@id='microservices']/div[4]/div[1]/h3/input[1]"));
        WebElement elementOrdertypePT = driver.findElement(By.xpath("//*[@id='microservices']/div[4]/div[1]/h3/input[2]"));
        elementOrdertypeGTCJ.click();
        elementOrdertypePT.click();
        if(elementOrdertypeGTCJ.isEnabled() || elementOrdertypePT.isEnabled()){
            elementRefreshOrdersBtn.click();
            System.out.println("Show Orders according database!");
        }
        else {
            elementRefreshOrdersBtn.click();
            Alert javascriptConfirm = driver.switchTo().alert();
            javascriptConfirm.accept();
            elementOrdertypeGTCJ.click();
            elementOrdertypePT.click();
            elementRefreshOrdersBtn.click();
        }
        //gain oeders
        List<WebElement> ordersList = driver.findElements(By.xpath("//table[@id='all_order_table']/tbody/tr"));
        //Confirm ticket selection
        if (ordersList.size() > 0) {
            Random rand = new Random();
            int i = rand.nextInt(100) % ordersList.size(); //int范围类的随机数
            orderId =  ordersList.get(i).findElement(By.xpath("td[3]")).getText();
            WebElement elementOrderStatus = ordersList.get(i).findElement(By.xpath("td[8]/select"));
            Select selSeat = new Select(elementOrderStatus);
            selSeat.selectByValue("1"); //2st
            ordersList.get(i).findElement(By.xpath("td[9]/button")).click();
            System.out.println("Success get orderId and update order status! orderId:"+orderId);
        }
        else
            System.out.println("Cant't get orders information1");
        Assert.assertEquals(ordersList.size() > 0,true);
        Assert.assertEquals(orderId.equals(""),false);
    }
    @Test (dependsOnMethods = {"getOrders"})
    public void testTicketRebook()throws Exception{
        JavascriptExecutor js = (JavascriptExecutor) driver;
//        if(orderId ==null || orderId.length() <= 0) {
//            System.out.println("Failed,orderId is NULL!");
//            driver.quit();
//        }
//        if (!"".equals(orderId))
//            System.out.println("Sign Up btn status: "+statusSignIn);
//        else
//            System.out.println("False，Status of Sign In btn is NULL!");
        driver.findElement(By.id("single_rebook_order_id")).clear();

        driver.findElement(By.id("single_rebook_order_id")).sendKeys(orderId);
        //driver.findElement(By.id("single_rebook_order_id")).sendKeys("8177ac5a-61ac-42f4-83f4-bd7b394d0531");
        //js.executeScript("document.getElementById('single_rebook_order_id').value=orderId");
        js.executeScript("document.getElementById('single_rebook_old_trip_id').value='G1234'");
        js.executeScript("document.getElementById('single_rebook_trip_id').value='G1235'");
        WebElement elementRebookSeatType = driver.findElement(By.id("single_rebook_seat_type"));
        Select selSeat = new Select(elementRebookSeatType);
        selSeat.selectByValue("2"); //2st

        String bookDate = "";
        SimpleDateFormat sdf=new SimpleDateFormat("yyyy-MM-dd");
        Calendar newDate = Calendar.getInstance();
        Random randDate = new Random();
        int randomDate = randDate.nextInt(25); //int范围类的随机数
        newDate.add(Calendar.DATE, randomDate+5);//随机定5-30天后的票
        bookDate=sdf.format(newDate.getTime());

        js.executeScript("document.getElementById('single_rebook_date').value='"+bookDate+"'");

        driver.findElement(By.id("single_rebook_button")).click();
        Thread.sleep(1000);
        //get rebook status
        String statusRebook = driver.findElement(By.id("single_rebook_result")).getText();
        if("".equals(statusRebook)){
            System.out.println("Failed,Status of Rebook btn is NULL!");
            Assert.assertEquals(!"".equals(statusRebook), true);
        }
        else if(statusRebook.startsWith("You haven't paid")){
            System.out.println("Failed,You haven't paid the original ticket!");
        }
        else if(statusRebook.startsWith("Please")) {
            System.out.println(statusRebook);
            driver.findElement(By.id("rebook_pay_button")).click();
            Thread.sleep(1000);
            String statusRebookPayment = driver.findElement(By.id("rebook_payment_result")).getText();
            System.out.println("Rebook payment status:"+statusRebookPayment);
            Assert.assertEquals(statusRebookPayment.startsWith("true"), true);
        }
        else {
            System.out.println("Rebook status:" + statusRebook);
            Assert.assertEquals(statusRebook.startsWith("true"), true);
        }
    }

    @AfterClass
    public void tearDown() throws Exception {
        driver.quit();
    }
}


// Node: Test
// Node: getOrders
// Node: xpath
// Node: switchTo
// Node: alert
// Node: accept
// Node: findElements
// Node: testTicketRebook
import org.openqa.selenium.By;
import org.openqa.selenium.JavascriptExecutor;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.chrome.ChromeDriver;
import org.testng.Assert;
import org.testng.annotations.AfterClass;
import org.testng.annotations.BeforeClass;
import org.testng.annotations.Test;

import java.text.SimpleDateFormat;
import java.util.Calendar;
import java.util.List;
import java.util.Random;
import java.util.concurrent.TimeUnit;

public class TestServiceTicketInfo {
    private WebDriver driver;
    private String baseUrl;
    @BeforeClass
    public void setUp() throws Exception {
        System.setProperty("webdriver.chrome.driver", "D:/Program/chromedriver_win32/chromedriver.exe");
        driver = new ChromeDriver();
        baseUrl = "http://10.141.212.24/";
        driver.manage().timeouts().implicitlyWait(30, TimeUnit.SECONDS);
    }
    @Test
    public void testTicketInfo() throws Exception{
        driver.get(baseUrl + "/");
        JavascriptExecutor js = (JavascriptExecutor) driver;
        js.executeScript("document.getElementById('ticketinfo_tripId').value='G1234'");
        js.executeScript("document.getElementById('ticketinfo_trainTypeId').value='GaoTieOne'");
        js.executeScript("document.getElementById('ticketinfo_startingStation').value='shanghai'");
        js.executeScript("document.getElementById('ticketinfo_stations').value='beijing'");
        js.executeScript("document.getElementById('ticketinfo_terminalStation').value='taiyuan'");

        String jsstartingTime = "document.getElementById('ticketinfo_startingTime').value='09:51'";
        js.executeScript(jsstartingTime);
        String jssendTime = "document.getElementById('ticketinfo_endTime').value='15:51'";
        js.executeScript(jssendTime);

        js.executeScript("document.getElementById('ticketinfo_startingPlace').value='Shang Hai'");
        js.executeScript("document.getElementById('ticketinfo_endPlace').value='Tai Yuan'");

        String bookDate = "";
        SimpleDateFormat sdf=new SimpleDateFormat("yyyy-MM-dd");
        Calendar newDate = Calendar.getInstance();
        Random randDate = new Random();
        int randomDate = randDate.nextInt(25); //int范围类的随机数
        newDate.add(Calendar.DATE, randomDate+5);//随机定5-30天后的票
        bookDate=sdf.format(newDate.getTime());

        js.executeScript("document.getElementById('ticketinfo_departureTime').value='"+bookDate+"'");

        driver.findElement(By.id("ticketinfo_button")).click();
        Thread.sleep(1000);

        //gain TicketInfo list
        List<WebElement> ticketInfoList = driver.findElements(By.xpath("//table[@id='query_ticketinfo_list_table']/tbody/tr"));
        if (ticketInfoList.size() > 0)
            System.out.printf("Success to Query TicketInfo and TicketInfo list size is %d.%n",ticketInfoList.size());
        else
            System.out.println("Failed to Query TicketInfo or TicketInfo list size is 0");
        Assert.assertEquals(ticketInfoList.size() > 0,true);
    }
    @AfterClass
    public void tearDown() throws Exception {
        driver.quit();
    }
}


// Node: repos/cloned_ms_repos/train-ticket/old-docs/ts-ui-test/src/test/java/TestServiceTicketInfo.java:TestServiceTicketInfo.<init>
// Node: testTicketInfo
import org.openqa.selenium.Alert;
import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.chrome.ChromeDriver;
import org.testng.Assert;
import org.testng.annotations.AfterClass;
import org.testng.annotations.BeforeClass;
import org.testng.annotations.Test;

import java.util.List;
import java.util.concurrent.TimeUnit;


public class TestServiceOrders {
    private WebDriver driver;
    private String baseUrl;

    @BeforeClass
    public void setUp() throws Exception {
        System.setProperty("webdriver.chrome.driver", "D:/Program/chromedriver_win32/chromedriver.exe");
        driver = new ChromeDriver();
        baseUrl = "http://10.141.212.24/";
        driver.manage().timeouts().implicitlyWait(30, TimeUnit.SECONDS);
    }
    @Test
    public void testOrders()throws Exception{
        driver.get(baseUrl + "/");
        WebElement elementRefreshOrdersBtn = driver.findElement(By.id("refresh_order_button"));
        WebElement elementOrdertypeGTCJ = driver.findElement(By.xpath("//*[@id='microservices']/div[4]/div[1]/h3/input[1]"));
        WebElement elementOrdertypePT = driver.findElement(By.xpath("//*[@id='microservices']/div[4]/div[1]/h3/input[2]"));
        elementOrdertypeGTCJ.click();
        elementOrdertypePT.click();
        if(elementOrdertypeGTCJ.isEnabled() || elementOrdertypePT.isEnabled()){
            elementRefreshOrdersBtn.click();
            System.out.println("Show Orders according database!");
        }
        else {
            elementRefreshOrdersBtn.click();
            Alert javascriptConfirm = driver.switchTo().alert();
            javascriptConfirm.accept();
            elementOrdertypeGTCJ.click();
            elementOrdertypePT.click();
            elementRefreshOrdersBtn.click();
        }
        List<WebElement> ordersList = driver.findElements(By.xpath("//table[@id='all_order_table']/tbody/tr"));
        if (ordersList.size() > 0) {
            System.out.printf("Success,Orders List's size is %d.%n", ordersList.size());
        } else
            System.out.println("False,Security Config List's size is 0 or Failed");
        Assert.assertEquals(ordersList.size() > 0, true);

    }
    @AfterClass
    public void tearDown() throws Exception {
        driver.quit();
    }
}


// Node: repos/cloned_ms_repos/train-ticket/old-docs/ts-ui-test/src/test/java/TestServiceOrders.java:TestServiceOrders.<init>
// Node: testOrders
import org.openqa.selenium.By;
import org.openqa.selenium.JavascriptExecutor;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.chrome.ChromeDriver;
import org.testng.Assert;
import org.testng.annotations.AfterClass;
import org.testng.annotations.BeforeClass;
import org.testng.annotations.Test;

import java.util.concurrent.TimeUnit;


public class TestServiceCellect {
    private WebDriver driver;
    private String baseUrl;
    @BeforeClass
    public void setUp() throws Exception {
        System.setProperty("webdriver.chrome.driver", "D:/Program/chromedriver_win32/chromedriver.exe");
        driver = new ChromeDriver();
        baseUrl = "http://10.141.212.24/";
        driver.manage().timeouts().implicitlyWait(30, TimeUnit.SECONDS);
    }
    @Test
    public void testTicketCollect() throws Exception{
        driver.get(baseUrl + "/");
        JavascriptExecutor js = (JavascriptExecutor) driver;
        js.executeScript("document.getElementById('single_collect_order_id').value='5ad7750b-a68b-49c0-a8c0-32776b067703'");
        driver.findElement(By.id("single_collect_button")).click();
        String statusTicketCollect = driver.findElement(By.id("single_collect_order_result")).getText();
        if ("".equals(statusTicketCollect))
            System.out.println("False,status security check is null!");
        else
            System.out.println("Ticket Collect status:"+statusTicketCollect);
        Assert.assertEquals(!"".equals(statusTicketCollect),true);
    }
    @AfterClass
    public void tearDown() throws Exception {
        driver.quit();
    }
}


// Node: repos/cloned_ms_repos/train-ticket/old-docs/ts-ui-test/src/test/java/TestServiceCellect.java:TestServiceCellect.<init>
// Node: testTicketCollect
import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.chrome.ChromeDriver;
import org.testng.Assert;
import org.testng.annotations.AfterClass;
import org.testng.annotations.BeforeClass;
import org.testng.annotations.Test;

import java.util.List;
import java.util.concurrent.TimeUnit;


public class TestServiceContacts {
    private WebDriver driver;
    private String baseUrl;
    @BeforeClass
    public void setUp() throws Exception {
        System.setProperty("webdriver.chrome.driver", "D:/Program/chromedriver_win32/chromedriver.exe");
        driver = new ChromeDriver();
        baseUrl = "http://10.141.212.24/";
        driver.manage().timeouts().implicitlyWait(30, TimeUnit.SECONDS);
    }
    @Test
    public void testContacts()throws Exception{
        driver.get(baseUrl + "/");
        driver.findElement(By.id("refresh_contacts_button")).click();
        Thread.sleep(1000);
        List<WebElement> contactsList = driver.findElements(By.xpath("//table[@id='contacts_list_table']/tbody/tr"));
        //List<WebElement> contactsList = driver.findElements(By.xpath("//table[@id='contacts_booking_list_table']/tbody/tr"));
        if(contactsList.size() > 0) {
            System.out.printf("Success,Contacts List's size is %d.%n", contactsList.size());
        }
        else
            System.out.println("False,Contacts List's size is 0 or Failed");
        Assert.assertEquals(contactsList.size() > 0,true);
    }
    @AfterClass
    public void tearDown() throws Exception {
        driver.quit();
    }
}


// Node: repos/cloned_ms_repos/train-ticket/old-docs/ts-ui-test/src/test/java/TestServiceContacts.java:TestServiceContacts.<init>
// Node: testContacts
import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.chrome.ChromeDriver;
import org.testng.Assert;
import org.testng.annotations.AfterClass;
import org.testng.annotations.BeforeClass;
import org.testng.annotations.Test;

import java.util.List;
import java.util.concurrent.TimeUnit;

public class TestServicePayment {
    private WebDriver driver;
    private String baseUrl;
    public static void login(WebDriver driver,String username,String password){
        driver.findElement(By.id("flow_one_page")).click();
        driver.findElement(By.id("flow_preserve_login_email")).clear();
        driver.findElement(By.id("flow_preserve_login_email")).sendKeys(username);
        driver.findElement(By.id("flow_preserve_login_password")).clear();
        driver.findElement(By.id("flow_preserve_login_password")).sendKeys(password);
        driver.findElement(By.id("flow_preserve_login_button")).click();
    }
    @BeforeClass
    public void setUp() throws Exception {
        System.setProperty("webdriver.chrome.driver", "D:/Program/chromedriver_win32/chromedriver.exe");
        driver = new ChromeDriver();
        baseUrl = "http://10.141.212.24/";
        driver.manage().timeouts().implicitlyWait(30, TimeUnit.SECONDS);
    }
    @Test
    public void login()throws Exception{
        driver.get(baseUrl + "/");

        //define username and password
        String username = "fdse_microservices@163.com";
        String password = "DefaultPassword";

        //call function login
        login(driver,username,password);
        Thread.sleep(1000);

        //get login status
        String statusLogin = driver.findElement(By.id("flow_preserve_login_msg")).getText();
        if("".equals(statusLogin))
            System.out.println("Failed to Login! Status is Null!");
        else if(statusLogin.startsWith("Success"))
            System.out.println("Success to Login! Status:"+statusLogin);
        else
            System.out.println("Failed to Login! Status:"+statusLogin);

        Assert.assertEquals(statusLogin.startsWith("Success"),true);
        driver.findElement(By.id("microservice_page")).click();
    }
    @Test (dependsOnMethods = {"login"})
    public void testPayment() throws Exception {
        driver.get(baseUrl + "/");
        driver.findElement(By.id("payment_orderId")).clear();
        driver.findElement(By.id("payment_orderId")).sendKeys("5ad7750b-a68b-49c0-a8c0-32776b067703");
        driver.findElement(By.id("payment_price")).clear();
        driver.findElement(By.id("payment_price")).sendKeys("100.0");
        driver.findElement(By.id("payment_userId")).clear();
        driver.findElement(By.id("payment_userId")).sendKeys("4d2a46c7-71cb-4cf1-b5bb-b68406d9da6f");
        driver.findElement(By.id("payment_pay_button")).click();
        Thread.sleep(1000);

        String statusPayment = driver.findElement(By.id("payment_result")).getText();
        if (!"".equals(statusPayment))
            System.out.println("Status of payment: "+statusPayment);
        else
            System.out.println("False, status of  payment result is null!");
        Assert.assertEquals(!"".equals(statusPayment),true);
    }
    @Test (dependsOnMethods = {"testPayment"})
    public void testPaymentList() throws Exception {
        driver.findElement(By.id("payment_query_button")).click();
        Thread.sleep(1000);

        List<WebElement> paymentList = driver.findElements(By.xpath("//table[@id='query_payment_list_table']/tbody/tr"));
        if (paymentList.size() > 0)
            System.out.printf("Success to Query PaymentList and Payment list size is %d.%n",paymentList.size());
        else
            System.out.println("Failed to Query PaymentList or Payment list size is 0");
        Assert.assertEquals(paymentList.size() > 0,true);
    }
    @AfterClass
    public void tearDown() throws Exception {
        driver.quit();
    }
}


// Node: testPayment
// Node: testPaymentList
import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.chrome.ChromeDriver;
import org.testng.Assert;
import org.testng.annotations.AfterClass;
import org.testng.annotations.BeforeClass;
import org.testng.annotations.Test;

import java.util.List;
import java.util.concurrent.TimeUnit;


public class TestServiceSecurity {
    private WebDriver driver;
    private String baseUrl;
    @BeforeClass
    public void setUp() throws Exception {
        System.setProperty("webdriver.chrome.driver", "D:/Program/chromedriver_win32/chromedriver.exe");
        driver = new ChromeDriver();
        baseUrl = "http://10.141.212.24/";
        driver.manage().timeouts().implicitlyWait(30, TimeUnit.SECONDS);
    }
    @Test
    public void testSecurity() throws Exception {
        driver.get(baseUrl + "/");
        driver.findElement(By.id("refresh_security_config_button")).click();
        Thread.sleep(1000);
        List<WebElement> securityList = driver.findElements(By.xpath("//table[@id='security_config_list_table']/tbody/tr"));
        if(securityList.size() > 0) {
            System.out.printf("Success,Security Config List's size is %d.%n", securityList.size());
            testSecurityCheck();
        }
        else
            System.out.println("False,Security Config List's size is 0 or Failed");
        Assert.assertEquals(securityList.size() > 0,true);
    }
    public void testSecurityCheck() throws Exception{
        driver.findElement(By.id("security_check_account_id")).clear();
        driver.findElement(By.id("security_check_account_id")).sendKeys("4d2a46c7-71cb-4cf1-b5bb-b68406d9da6f");
        driver.findElement(By.id("security_check_button")).click();
        Thread.sleep(1000);
        String statusSecurityCheck = driver.findElement(By.id("security_check_message")).getText();
        if (!"".equals(statusSecurityCheck))
            System.out.println("Success: "+statusSecurityCheck);
        else
            System.out.println("False, status security check is null!");
        Assert.assertEquals(statusSecurityCheck.startsWith("Success"),true);
    }
    @AfterClass
    public void tearDown() throws Exception {
        driver.quit();
    }
}


// Node: repos/cloned_ms_repos/train-ticket/old-docs/ts-ui-test/src/test/java/TestServiceSecurity.java:TestServiceSecurity.<init>
// Node: testSecurity
// Node: testSecurityCheck
import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.chrome.ChromeDriver;
import org.testng.Assert;
import org.testng.annotations.AfterClass;
import org.testng.annotations.BeforeClass;
import org.testng.annotations.DataProvider;
import org.testng.annotations.Test;

import java.util.concurrent.TimeUnit;

/**
 * Created by ZDH on 2017/7/21.
 */
public class TestServiceRegister {
    private WebDriver driver;
    private String baseUrl;
    public static void login(WebDriver driver,String username,String password){
        driver.findElement(By.id("flow_one_page")).click();
        driver.findElement(By.id("flow_preserve_login_email")).clear();
        driver.findElement(By.id("flow_preserve_login_email")).sendKeys(username);
        driver.findElement(By.id("flow_preserve_login_password")).clear();
        driver.findElement(By.id("flow_preserve_login_password")).sendKeys(password);
        driver.findElement(By.id("flow_preserve_login_button")).click();
    }
    @BeforeClass
    public void setUp() throws Exception {
        System.setProperty("webdriver.chrome.driver", "D:/Program/chromedriver_win32/chromedriver.exe");
        driver = new ChromeDriver();
        baseUrl = "http://10.141.212.24/";
        driver.manage().timeouts().implicitlyWait(30, TimeUnit.SECONDS);
    }
    @DataProvider(name="user")
    public Object[][] Users(){
        return new Object[][]{
                {"2daihongok@163.com","DefaultPassword"},
        };
    }
    @Test (dataProvider="user")
    public void testRegister(String username,String password) throws Exception{
        driver.get(baseUrl + "/");

        driver.findElement(By.id("register_email")).clear();
        driver.findElement(By.id("register_email")).sendKeys(username);
        driver.findElement(By.id("register_password")).clear();
        driver.findElement(By.id("register_password")).sendKeys(password);

        driver.findElement(By.id("register_button")).click();
        Thread.sleep(1000);

        String statusSignUp = driver.findElement(By.id("register_result_msg")).getText();
        if ("".equals(statusSignUp))
            System.out.println("Failed,Status of Sign Up btn is NULL!");
        else
            System.out.println("Sign Up btn status:"+statusSignUp);
        Assert.assertEquals(statusSignUp.startsWith("Success"),true);
    }
    @Test (dependsOnMethods = {"testRegister"},dataProvider="user")
    public void testRegisterLogin(String username,String password) throws Exception{
        //call function login
        login(driver,username,password);
        Thread.sleep(1000);

        //get login status
        String statusLogin = driver.findElement(By.id("flow_preserve_login_msg")).getText();
        if(statusLogin.startsWith("Success")) {
            System.out.println("Login status:"+statusLogin);
            driver.findElement(By.id("microservice_page")).click();
        }
        else if("".equals(statusLogin))
            System.out.println("False,Failed to login! StatusLogin is NULL");
        else
            System.out.println("Failed to login!" + "Wrong login Id or password!");

        Assert.assertEquals(statusLogin.startsWith("Success"),true);
    }
    @AfterClass
    public void tearDown() throws Exception {
        driver.quit();
    }
}


// Node: DataProvider
// Node: Users
// Node: testRegister
// Node: testRegisterLogin
import org.openqa.selenium.By;
import org.openqa.selenium.JavascriptExecutor;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.chrome.ChromeDriver;
import org.testng.Assert;
import org.testng.annotations.AfterClass;
import org.testng.annotations.BeforeClass;
import org.testng.annotations.Test;

import java.text.SimpleDateFormat;
import java.util.Calendar;
import java.util.List;
import java.util.Random;
import java.util.concurrent.TimeUnit;

public class TestServiceBasicInfo {
    private WebDriver driver;
    private String baseUrl;
    @BeforeClass
    public void setUp() throws Exception {
        System.setProperty("webdriver.chrome.driver", "D:/Program/chromedriver_win32/chromedriver.exe");
        driver = new ChromeDriver();
        baseUrl = "http://10.141.212.24/";
        driver.manage().timeouts().implicitlyWait(30, TimeUnit.SECONDS);
    }
    @Test
    public void testBasicInfo() throws Exception{
        driver.get(baseUrl + "/");
        JavascriptExecutor js = (JavascriptExecutor) driver;
        js.executeScript("document.getElementById('basic_information_tripId').value='G1234'");
        js.executeScript("document.getElementById('basic_information_trainTypeId').value='GaoTieOne'");
        js.executeScript("document.getElementById('basic_information_startingStation').value='shanghai'");
        js.executeScript("document.getElementById('basic_information_stations').value='beijing'");
        js.executeScript("document.getElementById('basic_information_terminalStation').value='taiyuan'");

        String jsstartingTime = "document.getElementById('basic_information_startingTime').value='09:51'";
        js.executeScript(jsstartingTime);
        String jssendTime = "document.getElementById('basic_information_endTime').value='15:51'";
        js.executeScript(jssendTime);

        js.executeScript("document.getElementById('basic_information_startingPlace').value='Shang Hai'");
        js.executeScript("document.getElementById('basic_information_endPlace').value='Tai Yuan'");

        String bookDate = "";
        SimpleDateFormat sdf=new SimpleDateFormat("yyyy-MM-dd");
        Calendar newDate = Calendar.getInstance();
        Random randDate = new Random();
        int randomDate = randDate.nextInt(25); //int范围类的随机数
        newDate.add(Calendar.DATE, randomDate+5);//随机定5-30天后的票
        bookDate=sdf.format(newDate.getTime());

        js.executeScript("document.getElementById('basic_information_departureTime').value='"+bookDate+"'");

        driver.findElement(By.id("basic_information_button")).click();
        Thread.sleep(1000);

        //gain BasicInfo list
        List<WebElement> basicInfoList = driver.findElements(By.xpath("//table[@id='query_basic_information_list_table']/tbody/tr"));
        if (basicInfoList.size() > 0)
            System.out.printf("Success to Query BasicInfo and BasicInfo list size is %d.%n",basicInfoList.size());
        else
            System.out.println("Failed to Query BasicInfo or BasicInfo list size is 0");
        Assert.assertEquals(basicInfoList.size() > 0,true);
    }
    @AfterClass
    public void tearDown() throws Exception {
        driver.quit();
    }
}


// Node: repos/cloned_ms_repos/train-ticket/old-docs/ts-ui-test/src/test/java/TestServiceBasicInfo.java:TestServiceBasicInfo.<init>
// Node: testBasicInfo
import org.openqa.selenium.*;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.support.ui.Select;
import org.testng.Assert;
import org.testng.annotations.AfterClass;
import org.testng.annotations.BeforeClass;
import org.testng.annotations.Test;

import java.util.List;
import java.util.concurrent.TimeUnit;

public class TestFlowTwoPay {
    private WebDriver driver;
    private String baseUrl;
    private List<WebElement> myOrdersList;
    public static void login(WebDriver driver,String username,String password){
        driver.findElement(By.id("flow_one_page")).click();
        driver.findElement(By.id("flow_preserve_login_email")).clear();
        driver.findElement(By.id("flow_preserve_login_email")).sendKeys(username);
        driver.findElement(By.id("flow_preserve_login_password")).clear();
        driver.findElement(By.id("flow_preserve_login_password")).sendKeys(password);
        driver.findElement(By.id("flow_preserve_login_button")).click();
    }
    @BeforeClass
    public void setUp() throws Exception {
        System.setProperty("webdriver.chrome.driver", "D:/Program/chromedriver_win32/chromedriver.exe");
        driver = new ChromeDriver();
        baseUrl = "http://10.141.212.24/";
        driver.manage().timeouts().implicitlyWait(30, TimeUnit.SECONDS);
    }
    @Test
    //Test Flow Preserve Step 1: - Login
    public void testLogin()throws Exception{
        driver.get(baseUrl + "/");

        //define username and password
        String username = "fdse_microservices@163.com";
        String password = "DefaultPassword";

        //call function login
        login(driver,username,password);
        Thread.sleep(1000);

        //get login status
        String statusLogin = driver.findElement(By.id("flow_preserve_login_msg")).getText();
        if("".equals(statusLogin))
            System.out.println("Failed to Login! Status is Null!");
        else if(statusLogin.startsWith("Success"))
            System.out.println("Success to Login! Status:"+statusLogin);
        else
            System.out.println("Failed to Login! Status:"+statusLogin);
        Assert.assertEquals(statusLogin.startsWith("Success"),true);
        driver.findElement(By.id("flow_two_page")).click();
    }
    @Test (dependsOnMethods = {"testLogin"})
    public void testViewOrders() throws Exception{
        driver.findElement(By.id("flow_two_page")).click();
        driver.findElement(By.id("refresh_my_order_list_button")).click();
        Thread.sleep(1000);
        //gain my oeders
        myOrdersList = driver.findElements(By.xpath("//div[@id='my_orders_result']/div"));
        if (myOrdersList.size() > 0) {
            System.out.printf("Success to show my orders list，the list size is:%d%n",myOrdersList.size());
        }
        else
            System.out.println("Failed to show my orders list，the list size is 0 or No orders in this user!");
        Assert.assertEquals(myOrdersList.size() > 0,true);
    }
    @Test (dependsOnMethods = {"testViewOrders"})
    public void testPayOrder() throws Exception{
        System.out.printf("The orders list size is:%d%n",myOrdersList.size());
        String statusOrder  = "";
        int i;
        //Find the first not paid order .
        for(i = 0;i < myOrdersList.size();i++) {
        //while(!(statusOrder.startsWith("Not")) && i < myOrdersList.size()) {
            //statusOrder = myOrdersList.get(i).findElement(By.xpath("/div[2]/div/div/form/div[7]/div/label[2]")).getText();
            statusOrder = myOrdersList.get(i).findElement(By.xpath("div[2]//form[@role='form']/div[7]/div/label[2]")).getText();
            if(statusOrder.startsWith("Not"))
                break;
        }
        if(i == myOrdersList.size() || i > myOrdersList.size())
            System.out.printf("Failed,there is no not paid order!");
        Assert.assertEquals(i < myOrdersList.size(),true);

        myOrdersList.get(i).findElement(By.xpath("div[2]//form[@role='form']/div[7]/div/button")).click();
        Thread.sleep(1000);
        String inputNotPaidOrderId = driver.findElement(By.id("pay_for_not_paid_orderId")).getAttribute("value");
        String inputNotPaidPrice = driver.findElement(By.id("pay_for_not_paid_price")).getAttribute("value");
        String inputNotPaidTripId = driver.findElement(By.id("pay_for_not_paid_tripId")).getAttribute("value");
        boolean bNotPaidOrderId = !"".equals(inputNotPaidOrderId);
        boolean bNotPaidPrice = !"".equals(inputNotPaidPrice);
        boolean bNotPaidTripId = !"".equals(inputNotPaidTripId);
        boolean bNotPaidStatus = bNotPaidOrderId && bNotPaidPrice && bNotPaidTripId;
        if(bNotPaidStatus == false)
            System.out.println("Step-Pay for Your Order,The input is null!!");
        Assert.assertEquals(bNotPaidStatus,true);

        driver.findElement(By.id("pay_for_not_paid_pay_button")).click();
        Thread.sleep(1000);

        Alert javascriptConfirm = driver.switchTo().alert();
        String statusAlert = driver.switchTo().alert().getText();
        System.out.println("The Alert information of Payment："+statusAlert);
        Assert.assertEquals(statusAlert.startsWith("Success"),true);
        javascriptConfirm.accept();
    }
    @AfterClass
    public void tearDown() throws Exception {
        driver.quit();
    }
}


// Node: testLogin
// Node: testViewOrders
import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.chrome.ChromeDriver;
import org.testng.Assert;
import org.testng.annotations.AfterClass;
import org.testng.annotations.BeforeClass;
import org.testng.annotations.DataProvider;
import org.testng.annotations.Test;

import java.util.concurrent.TimeUnit;


public class TestServiceLogin {
    private WebDriver driver;
    private String baseUrl;
    public static void ServiceLogin(WebDriver driver,String username,String password){
        driver.findElement(By.id("login_email")).clear();
        driver.findElement(By.id("login_email")).sendKeys(username);
        driver.findElement(By.id("login_password")).clear();
        driver.findElement(By.id("login_password")).sendKeys(password);
        driver.findElement(By.id("login_button")).click();
    }
    @BeforeClass
    public void setUp() throws Exception {
        System.setProperty("webdriver.chrome.driver", "D:/Program/chromedriver_win32/chromedriver.exe");
        driver = new ChromeDriver();
        baseUrl = "http://10.141.212.24/";
        driver.manage().timeouts().implicitlyWait(30, TimeUnit.SECONDS);
    }
    @DataProvider(name="user")
    public Object[][] Users(){
        return new Object[][]{
                {"fdse_microservices@163","DefaultPassword",false},
                {"fdse_microservices@163.com","DefaultPass",false},
                {"fdse_microservices@163.com","DefaultPassword",true},
                {"error","error",false},
                //{"","","请先输入您的邮箱帐号"},
                //{"fdse_microservices@163.com"," ","帐号或密码错误"},
                //{" ","DefaultPassword","请先输入您的邮箱帐号"},
                //{"error","error","帐号或密码错误"},
        };
    }
    @Test (dataProvider="user")
    public void testSignIn(String username,String password,boolean expectText)throws Exception{
        driver.get(baseUrl + "/");

        //call function login
        ServiceLogin(driver,username,password);
        Thread.sleep(1000);

        //get login status
        String statusSignIn = driver.findElement(By.id("login_result_msg")).getText();
        if (!"".equals(statusSignIn))
            System.out.println("Sign Up btn status: "+statusSignIn);
        else
            System.out.println("False，Status of Sign In btn is NULL!");
        System.out.println(expectText);
        Assert.assertEquals(statusSignIn.startsWith("Success"),expectText);
    }
    @AfterClass
    public void tearDown() throws Exception {
        driver.quit();
    }
}


// Node: ServiceLogin
// Node: testSignIn
import org.openqa.selenium.By;
import org.openqa.selenium.JavascriptExecutor;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.chrome.ChromeDriver;
import org.testng.Assert;
import org.testng.annotations.AfterClass;
import org.testng.annotations.BeforeClass;
import org.testng.annotations.Test;

import java.util.List;
import java.util.concurrent.TimeUnit;


public class TestServiceStation {
    private WebDriver driver;
    private String baseUrl;
    @BeforeClass
    public void setUp() throws Exception {
        System.setProperty("webdriver.chrome.driver", "D:/Program/chromedriver_win32/chromedriver.exe");
        driver = new ChromeDriver();
        baseUrl = "http://10.141.212.24/";
        driver.manage().timeouts().implicitlyWait(30, TimeUnit.SECONDS);
    }
    @Test
    public void testStation() throws Exception{
        driver.get(baseUrl + "/");
        JavascriptExecutor js = (JavascriptExecutor) driver;
        js.executeScript("document.getElementById('station_update_id').value='shanghai'");
        js.executeScript("document.getElementById('station_update_name').value='shang hai'");

        driver.findElement(By.id("station_update_button")).click();
        Thread.sleep(1000);
 //       String statusStation = driver.findElement(By.id("login_result_msg")).getText();
//        if(statusSignIn ==null || statusSignIn.length() <= 0) {
//            System.out.println("Failed,Status of Sign In btn is NULL!");
//            driver.quit();
//        }else
//            System.out.println("Sign Up btn status:"+statusSignIn);
    }
    @Test (dependsOnMethods = {"testStation"})
    public void testQueryStation() throws Exception{
        driver.findElement(By.id("station_query_button")).click();
        Thread.sleep(1000);
        //gain Travel list
        List<WebElement> stationList = driver.findElements(By.xpath("//table[@id='query_station_list_table']/tbody/tr"));

        if (stationList.size() > 0)
            System.out.printf("Success to Query Station and Station list size is %d.%n",stationList.size());
        else
            System.out.println("Failed to Query Station or Station list size is 0");
        Assert.assertEquals(stationList.size() > 0,true);
    }
    @AfterClass
    public void tearDown() throws Exception {
        driver.quit();
    }
}


// Node: repos/cloned_ms_repos/train-ticket/old-docs/ts-ui-test/src/test/java/TestServiceStation.java:TestServiceStation.<init>
// Node: testStation
// Node: testQueryStation
import org.openqa.selenium.By;
import org.openqa.selenium.JavascriptExecutor;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.chrome.ChromeDriver;
import org.testng.Assert;
import org.testng.annotations.AfterClass;
import org.testng.annotations.BeforeClass;
import org.testng.annotations.Test;

import java.util.List;
import java.util.Random;
import java.util.concurrent.TimeUnit;


public class TestServiceTravel2 {
    private WebDriver driver;
    private String baseUrl;
    @BeforeClass
    public void setUp() throws Exception {
        System.setProperty("webdriver.chrome.driver", "D:/Program/chromedriver_win32/chromedriver.exe");
        driver = new ChromeDriver();
        baseUrl = "http://10.141.212.24/";
        driver.manage().timeouts().implicitlyWait(30, TimeUnit.SECONDS);
    }
    @Test
    public void testTravel2() throws Exception{
        driver.get(baseUrl + "/");
        JavascriptExecutor js = (JavascriptExecutor) driver;
        js.executeScript("document.getElementById('travel2_update_tripId').value='Z1234'");
        js.executeScript("document.getElementById('travel2_update_trainTypeId').value='ZhiDa'");
        js.executeScript("document.getElementById('travel2_update_startingStationId').value='shanghai'");
        js.executeScript("document.getElementById('travel2_update_stationsId').value='beijing'");
        js.executeScript("document.getElementById('travel2_update_terminalStationId').value='taiyuan'");
        js.executeScript("document.getElementById('travel2_update_startingTime').value='11:17'");
        js.executeScript("document.getElementById('travel2_update_endTime').value='15:19'");

        driver.findElement(By.id("travel2_update_button")).click();
        Thread.sleep(1000);
//        String statusSignIn = driver.findElement(By.id("login_result_msg")).getText();
//        if(statusSignIn ==null || statusSignIn.length() <= 0) {
//            System.out.println("Failed,Status of Sign In btn is NULL!");
//            driver.quit();
//        }else
//            System.out.println("Sign Up btn status:"+statusSignIn);
    }
    @Test (dependsOnMethods = {"testTravel2"})
    public void testQueryTravel2() throws Exception{
        driver.findElement(By.id("travel2_queryAll_button")).click();
        Thread.sleep(1000);
        //gain Travel list
        List<WebElement> travel2List = driver.findElements(By.xpath("//table[@id='query_travel2_list_table']/tbody/tr"));

        if (travel2List.size() > 0)
            System.out.printf("Success to Query Travel2 and Travel2 list size is %d.%n",travel2List.size());
        else
            System.out.println("Failed to Query Travel2 or Travel2 list size is 0");
        Assert.assertEquals(travel2List.size() > 0,true);
    }
    @AfterClass
    public void tearDown() throws Exception {
        driver.quit();
    }
}


// Node: repos/cloned_ms_repos/train-ticket/old-docs/ts-ui-test/src/test/java/TestServiceTravel2.java:TestServiceTravel2.<init>
// Node: testTravel2
// Node: testQueryTravel2
import org.openqa.selenium.By;
import org.openqa.selenium.JavascriptExecutor;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.chrome.ChromeDriver;
import org.testng.Assert;
import org.testng.annotations.AfterClass;
import org.testng.annotations.BeforeClass;
import org.testng.annotations.Test;

import java.util.List;
import java.util.concurrent.TimeUnit;

public class TestServiceConfig {
    private WebDriver driver;
    private String baseUrl;
    @BeforeClass
    public void setUp() throws Exception {
        System.setProperty("webdriver.chrome.driver", "D:/Program/chromedriver_win32/chromedriver.exe");
        driver = new ChromeDriver();
        baseUrl = "http://10.141.212.24/";
        driver.manage().timeouts().implicitlyWait(30, TimeUnit.SECONDS);
    }
    @Test
    public void testConfig() throws Exception{
        driver.get(baseUrl + "/");
        JavascriptExecutor js = (JavascriptExecutor) driver;
        js.executeScript("document.getElementById('config_update_name').value='DirectTicketAllocationProportion'");
        js.executeScript("document.getElementById('config_update_value').value='50%'");
        js.executeScript("document.getElementById('config_update_description').value='configtest'");

        driver.findElement(By.id("config_update_button")).click();
        Thread.sleep(1000);
//        String statusSignIn = driver.findElement(By.id("login_result_msg")).getText();
//        if(statusSignIn ==null || statusSignIn.length() <= 0) {
//            System.out.println("Failed,Status of Sign In btn is NULL!");
//            driver.quit();
//        }else
//            System.out.println("Sign Up btn status:"+statusSignIn);
    }
    @Test (dependsOnMethods = {"testConfig"})
    public void testQueryConfig() throws Exception{
        driver.findElement(By.id("config_query_button")).click();
        Thread.sleep(1000);
        //gain Travel list
        List<WebElement> configList = driver.findElements(By.xpath("//table[@id='query_config_list_table']/tbody/tr"));
        if (configList.size() > 0)
            System.out.printf("Success to Query Config and Config list size is %d.%n",configList.size());
        else
            System.out.println("Failed to Query Config or Config list size is 0");
        Assert.assertEquals(configList.size() > 0,true);
    }
    @AfterClass
    public void tearDown() throws Exception {
        driver.quit();
    }
}


// Node: repos/cloned_ms_repos/train-ticket/old-docs/ts-ui-test/src/test/java/TestServiceConfig.java:TestServiceConfig.<init>
// Node: testConfig
// Node: testQueryConfig
import org.openqa.selenium.*;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.Select;
import org.openqa.selenium.support.ui.WebDriverWait;
import org.testng.Assert;
import org.testng.annotations.AfterClass;
import org.testng.annotations.BeforeClass;
import org.testng.annotations.Test;

import java.text.SimpleDateFormat;
import java.util.Calendar;
import java.util.List;
import java.util.Random;
import java.util.concurrent.TimeUnit;

public class TestFlowTwoRebook {
    private WebDriver driver;
    private String baseUrl;
    private String trainType;//0--all,1--GaoTie,2--others
    private List<WebElement> myOrdersList;
    private List<WebElement> changeTicketsSearchList;
    public static void login(WebDriver driver,String username,String password){
        driver.findElement(By.id("flow_one_page")).click();
        driver.findElement(By.id("flow_preserve_login_email")).clear();
        driver.findElement(By.id("flow_preserve_login_email")).sendKeys(username);
        driver.findElement(By.id("flow_preserve_login_password")).clear();
        driver.findElement(By.id("flow_preserve_login_password")).sendKeys(password);
        driver.findElement(By.id("flow_preserve_login_button")).click();
    }
    @BeforeClass
    public void setUp() throws Exception {
        System.setProperty("webdriver.chrome.driver", "D:/Program/chromedriver_win32/chromedriver.exe");
        driver = new ChromeDriver();
        baseUrl = "http://10.141.212.24/";
        trainType = "1";
        driver.manage().timeouts().implicitlyWait(30, TimeUnit.SECONDS);
    }
    @Test
    //Test Flow Preserve Step 1: - Login
    public void testLogin()throws Exception{
        driver.get(baseUrl + "/");

        //define username and password
        String username = "fdse_microservices@163.com";
        String password = "DefaultPassword";

        //call function login
        login(driver,username,password);
        Thread.sleep(1000);

        //get login status
        String statusLogin = driver.findElement(By.id("flow_preserve_login_msg")).getText();
        if("".equals(statusLogin))
            System.out.println("Failed to Login! Status is Null!");
        else if(statusLogin.startsWith("Success"))
            System.out.println("Success to Login! Status:"+statusLogin);
        else
            System.out.println("Failed to Login! Status:"+statusLogin);
        Assert.assertEquals(statusLogin.startsWith("Success"),true);
        driver.findElement(By.id("flow_two_page")).click();
    }
    @Test (dependsOnMethods = {"testLogin"})
    public void testViewOrders() throws Exception{
        driver.findElement(By.id("flow_two_page")).click();
        driver.findElement(By.id("refresh_my_order_list_button")).click();
        Thread.sleep(1000);
        //gain my oeders
        myOrdersList = driver.findElements(By.xpath("//div[@id='my_orders_result']/div"));
        if (myOrdersList.size() > 0) {
            System.out.printf("Success to show my orders list，the list size is:%d%n",myOrdersList.size());
        }
        else
            System.out.println("Failed to show my orders list，the list size is 0 or No orders in this user!");
        Assert.assertEquals(myOrdersList.size() > 0,true);
    }
    @Test (dependsOnMethods = {"testViewOrders"})
    public void testChangeOrder() throws Exception{
        System.out.printf("The orders list size is:%d%n",myOrdersList.size());
        String statusOrder  = "";
        int i;
        //Find the first paid order .
        for(i = 0;i < myOrdersList.size();i++) {
            statusOrder = myOrdersList.get(i).findElement(By.xpath("div[2]//form[@role='form']/div[7]/div/label[2]")).getText();
            if(statusOrder.startsWith("Paid"))
                break;
        }
        if(i == myOrdersList.size() || i > myOrdersList.size())
            System.out.printf("Failed,there is no paid order!");
        Assert.assertEquals(i < myOrdersList.size(),true);

        //click change btn
        myOrdersList.get(i).findElement(By.xpath("div[2]//form[@role='form']/div[12]/div/button[1]")).click();
        Thread.sleep(1000);
        String inputStartingPlace = driver.findElement(By.id("travel_rebook_startingPlace")).getAttribute("value");
        String inputTerminalPlace = driver.findElement(By.id("travel_rebook_terminalPlace")).getAttribute("value");
        boolean bStartingPlace = !"".equals(inputStartingPlace);
        boolean bTerminalPlace = !"".equals(inputTerminalPlace);
        boolean bchangeStatus = bStartingPlace && bTerminalPlace;
        if(bchangeStatus == false)
            System.out.println("Step-Change Your Order,The input is null!!");
        Assert.assertEquals(bchangeStatus,true);

        String bookDate = "";
        SimpleDateFormat sdf=new SimpleDateFormat("yyyy-MM-dd");
        Calendar newDate = Calendar.getInstance();
        Random randDate = new Random();
        int randomDate = randDate.nextInt(25); //int范围类的随机数
        newDate.add(Calendar.DATE, randomDate+5);//随机定5-30天后的票
        bookDate=sdf.format(newDate.getTime());

        JavascriptExecutor js = (JavascriptExecutor) driver;
        js.executeScript("document.getElementById('travel_rebook_date').value='"+bookDate+"'");

        WebElement elementRebookTraintype = driver.findElement(By.id("search_rebook_train_type"));
        Select selTraintype = new Select(elementRebookTraintype);
        selTraintype.selectByValue("trainType"); //All

        driver.findElement(By.id("travel_rebook_button")).click();
        Thread.sleep(1000);

        changeTicketsSearchList = driver.findElements(By.xpath("//table[@id='tickets_change_list_table']/tbody/tr"));
        if (changeTicketsSearchList.size() > 0) {
            System.out.printf("Success to search tickets，the tickets list size is:%d%n",changeTicketsSearchList.size());
        }
        else
            System.out.println("Failed to search tickets，the tickets list size is 0 or No tickets available!");
        Assert.assertEquals(changeTicketsSearchList.size() > 0,true);


    }
    @Test (dependsOnMethods = {"testChangeOrder"})
    public void testTicketRebook ()throws Exception{
        //Pick up a train (the first one!)and rebook tickets
        WebElement elementBookingSeat = changeTicketsSearchList.get(0).findElement(By.xpath("td[10]/select"));
        Select selSeat = new Select(elementBookingSeat);
        selSeat.selectByValue("2"); //1st
        changeTicketsSearchList.get(0).findElement(By.xpath("td[11]/button")).click();
        Thread.sleep(1000);

        String itemTripId = driver.findElement(By.id("ticket_rebook_confirm_old_tripId")).getText();
        String itemNewTripId = driver.findElement(By.id("ticket_rebook_confirm_new_tripId")).getText();
        String itemDate = driver.findElement(By.id("ticket_rebook_confirm_travel_date")).getText();
        String itemSeatType = driver.findElement(By.id("ticket_rebook_confirm_seatType_String")).getText();

        boolean bTripId = !"".equals(itemTripId);
        boolean bNewTripId = !"".equals(itemNewTripId);
        boolean bDate = !"".equals(itemDate);
        boolean bSeatType = !"".equals(itemSeatType);

        boolean bStatusConfirm = bTripId && bNewTripId && bDate &&  bSeatType;
        if(bStatusConfirm == false){
            driver.findElement(By.id("ticket_rebook_confirm_cancel_btn")).click();
            System.out.println("Confirming Ticket Canceled!");
        }
        Assert.assertEquals(bStatusConfirm,true);

        driver.findElement(By.id("ticket_rebook_confirm_confirm_btn")).click();
        Thread.sleep(1000);
        System.out.println("Confirm Ticket!");
        Alert javascriptConfirm = driver.switchTo().alert();
        String statusAlert = driver.switchTo().alert().getText();
        //System.out.println("The Alert information of Confirming Ticket："+statusAlert);

        if("".equals(statusAlert)){
            System.out.println("Failed,Status of tickets confirm alert is NULL!");
            Assert.assertEquals(!"".equals(statusAlert), true);
        }
        else if(statusAlert.startsWith("Success")){
            System.out.println("Rebook status:" + statusAlert);
            javascriptConfirm.accept();
        }
        else if(statusAlert.startsWith("Please")) {
            System.out.println(statusAlert);
            javascriptConfirm.accept();

            String itemPrice = driver.findElement(By.id("rebook_money_pay")).getAttribute("value");
            boolean bPrice = !"".equals(itemPrice);
            if(bPrice == false)
                System.out.println("Confirming Ticket failed!");
            Assert.assertEquals(bPrice,true);

            driver.findElement(By.id("ticket_rebook_pay_panel_confirm")).click();
            Thread.sleep(1000);

            Alert javascriptPay = null;
            String statusPayAlert;

            try {
                new WebDriverWait(driver, 30).until(ExpectedConditions
                        .alertIsPresent());
                javascriptPay = driver.switchTo().alert();
                statusPayAlert = driver.switchTo().alert().getText();
                System.out.println("Rebook payment status:"+statusPayAlert);
                javascriptPay.accept();
                Thread.sleep(1000);
                Assert.assertEquals(statusPayAlert.startsWith("Success"),true);
            } catch (NoAlertPresentException NofindAlert) {
                NofindAlert.printStackTrace();
            }
        }
        else
            System.out.println("Failed,Rebook status:" + statusAlert);
    }
    @AfterClass
    public void tearDown() throws Exception {
        driver.quit();
    }
}


// Node: testChangeOrder
// Node: train
// Node: WebDriverWait
// Node: until
// Node: alertIsPresent
import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.chrome.ChromeDriver;
import org.testng.Assert;
import org.testng.annotations.AfterClass;
import org.testng.annotations.BeforeClass;
import org.testng.annotations.Test;

import java.util.List;
import java.util.concurrent.TimeUnit;

public class TestServiceInsidePay {
    private WebDriver driver;
    private String baseUrl;
    public static void login(WebDriver driver,String username,String password){
        driver.findElement(By.id("flow_one_page")).click();
        driver.findElement(By.id("flow_preserve_login_email")).clear();
        driver.findElement(By.id("flow_preserve_login_email")).sendKeys(username);
        driver.findElement(By.id("flow_preserve_login_password")).clear();
        driver.findElement(By.id("flow_preserve_login_password")).sendKeys(password);
        driver.findElement(By.id("flow_preserve_login_button")).click();
    }
    @BeforeClass
    public void setUp() throws Exception {
        System.setProperty("webdriver.chrome.driver", "D:/Program/chromedriver_win32/chromedriver.exe");
        driver = new ChromeDriver();
        baseUrl = "http://10.141.212.24/";
        driver.manage().timeouts().implicitlyWait(30, TimeUnit.SECONDS);
    }
    @Test
    public void login()throws Exception{
        driver.get(baseUrl + "/");

        //define username and password
        String username = "fdse_microservices@163.com";
        String password = "DefaultPassword";

        //call function login
        login(driver,username,password);
        Thread.sleep(1000);

        //get login status
        String statusLogin = driver.findElement(By.id("flow_preserve_login_msg")).getText();
        if("".equals(statusLogin))
            System.out.println("Failed to Login! Status is Null!");
        else if(statusLogin.startsWith("Success"))
            System.out.println("Success to Login! Status:"+statusLogin);
        else
            System.out.println("Failed to Login! Status:"+statusLogin);
        Assert.assertEquals(statusLogin.startsWith("Success"),true);
        driver.findElement(By.id("microservice_page")).click();
    }
    @Test (dependsOnMethods = {"login"})
    public void testInsidePay() throws Exception {
        driver.get(baseUrl + "/");
        driver.findElement(By.id("inside_payment_orderId")).clear();
        driver.findElement(By.id("inside_payment_orderId")).sendKeys("5ad7750b-a68b-49c0-a8c0-32776b067703");
        driver.findElement(By.id("inside_payment_tripId")).clear();
        driver.findElement(By.id("inside_payment_tripId")).sendKeys("G1234");
        driver.findElement(By.id("inside_payment_pay_button")).click();
        Thread.sleep(1000);

        String statusInsidePay = driver.findElement(By.id("inside_payment_result")).getText();
        if (!"".equals(statusInsidePay))
            System.out.println("Status of inside payment: "+statusInsidePay);
        else
            System.out.println("False, status of inside payment result is null!");
        Assert.assertEquals(!"".equals(statusInsidePay),true);
    }
    @Test (dependsOnMethods = {"testInsidePay"})
    public void testInsidePayList() throws Exception {
        driver.findElement(By.id("inside_payment_query_payment_button")).click();
        Thread.sleep(1000);

        List<WebElement> insidePayList = driver.findElements(By.xpath("//table[@id='query_inside_payment_payment_list_table']/tbody/tr"));
        if (insidePayList.size() > 0)
            System.out.printf("Success to Query InsidePayList and InsidePay list size is %d.%n",insidePayList.size());
        else
            System.out.println("Failed to Query InsidePayList or InsidePay list size is 0");
        Assert.assertEquals(insidePayList.size() > 0,true);
    }
    @Test (dependsOnMethods = {"testInsidePayList"})
    public void testUserBalance() throws Exception {
        driver.findElement(By.id("inside_payment_query_account_button")).click();
        Thread.sleep(1000);

        List<WebElement> userBalanceList = driver.findElements(By.xpath("//table[@id='query_inside_payment_account_list_table']/tbody/tr"));
        if (userBalanceList.size() > 0)
            System.out.printf("Success to Query UserBalanceList and UserBalanceList list size is %d.%n",userBalanceList.size());
        else
            System.out.println("Failed to Query UserBalanceList or UserBalanceList list size is 0");
        Assert.assertEquals(userBalanceList.size() > 0,true);
    }
    @Test (dependsOnMethods = {"testUserBalance"})
    public void testAddMoney() throws Exception {
        driver.findElement(By.id("inside_payment_query_add_money_button")).click();
        Thread.sleep(1000);

        List<WebElement> addMoneyList = driver.findElements(By.xpath("//table[@id='query_inside_payment_add_money_list_table']/tbody/tr"));
        if (addMoneyList.size() > 0)
            System.out.printf("Success to Query Add Money List and Add Money List list size is %d.%n",addMoneyList.size());
        else
            System.out.println("Failed to Query Add Money List or Add Money List list size is 0");
        Assert.assertEquals(addMoneyList.size() > 0,true);
    }

    @AfterClass
    public void tearDown() throws Exception {
        driver.quit();
    }
}


// Node: testInsidePay
// Node: testInsidePayList
// Node: testUserBalance
import org.openqa.selenium.By;
import org.openqa.selenium.JavascriptExecutor;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.chrome.ChromeDriver;
import org.testng.Assert;
import org.testng.annotations.AfterClass;
import org.testng.annotations.BeforeClass;
import org.testng.annotations.Test;

import java.util.List;
import java.util.concurrent.TimeUnit;

/**
 * Created by ZDH on 2017/7/21.
 */
public class TestServiceTrain {
    private WebDriver driver;
    private String baseUrl;
    @BeforeClass
    public void setUp() throws Exception {
        System.setProperty("webdriver.chrome.driver", "D:/Program/chromedriver_win32/chromedriver.exe");
        driver = new ChromeDriver();
        baseUrl = "http://10.141.212.24/";
        driver.manage().timeouts().implicitlyWait(30, TimeUnit.SECONDS);
    }
    @Test
    public void testTrain() throws Exception{
        driver.get(baseUrl + "/");
        JavascriptExecutor js = (JavascriptExecutor) driver;
        js.executeScript("document.getElementById('train_update_id').value='GaoTieOne'");
        js.executeScript("document.getElementById('train_update_economyClass').value='120'");
        js.executeScript("document.getElementById('train_update_confortClass').value='60'");

        driver.findElement(By.id("train_update_button")).click();
        Thread.sleep(1000);
//        String statusSignIn = driver.findElement(By.id("login_result_msg")).getText();
//        if(statusSignIn ==null || statusSignIn.length() <= 0) {
//            System.out.println("Failed,Status of Sign In btn is NULL!");
//            driver.quit();
//        }else
//            System.out.println("Sign Up btn status:"+statusSignIn);
    }
    @Test (dependsOnMethods = {"testTrain"})
    public void testQueryTrain() throws Exception{
        driver.findElement(By.id("train_query_button")).click();
        Thread.sleep(1000);
        //gain Travel list
        List<WebElement> trainList = driver.findElements(By.xpath("//table[@id='query_train_list_table']/tbody/tr"));

        if (trainList.size() > 0)
            System.out.printf("Success to Query Train and Train list size is %d.%n",trainList.size());
        else
            System.out.println("Failed to Query Train or Train list size is 0");
        Assert.assertEquals(trainList.size() > 0,true);
    }
    @AfterClass
    public void tearDown() throws Exception {
        driver.quit();
    }
}


// Node: repos/cloned_ms_repos/train-ticket/old-docs/ts-ui-test/src/test/java/TestServiceTrain.java:TestServiceTrain.<init>
// Node: testTrain
// Node: testQueryTrain
import org.openqa.selenium.By;
import org.openqa.selenium.JavascriptExecutor;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.chrome.ChromeDriver;
import org.testng.Assert;
import org.testng.annotations.AfterClass;
import org.testng.annotations.BeforeClass;
import org.testng.annotations.DataProvider;
import org.testng.annotations.Test;

import java.util.List;
import java.util.Random;
import java.util.concurrent.TimeUnit;


public class TestServiceTravel {
    private WebDriver driver;
    private String baseUrl;
    public class TravelInfo{
        String tripId;
        String trainTypeId;
        String startStationName;
        String stationsId;
        String terminalStationId;
        String startingTime;
        String endTime;
        TravelInfo (
                String tripId,
                String trainTypeId,
                String startStationName,
                String stationsId,
                String terminalStationId,
                String startingTime,
                String endTime
        ){
            this.tripId = tripId;
            this.trainTypeId = trainTypeId;
            this.startStationName = startingStationId;
            this.stationsId = stationsId;
            this.terminalStationId = terminalStationId;
            this.startingTime = startingTime;
            this.endTime = endTime;
        }
    }
    @BeforeClass
    public void setUp() throws Exception {
        System.setProperty("webdriver.chrome.driver", "D:/Program/chromedriver_win32/chromedriver.exe");
        driver = new ChromeDriver();
        baseUrl = "http://10.141.212.24/";
        driver.manage().timeouts().implicitlyWait(30, TimeUnit.SECONDS);
    }
    @DataProvider(name="travel")
    public Object[][] Travel(){
        return new Object[][]{
                {new TravelInfo("G1234","GaoTieOne","shanghai","beijing","taiyuan","11:17","15:29")},
        };
    }
    @Test (dataProvider="travel")
    public void testTravel(TravelInfo travelinfo) throws Exception{
        driver.get(baseUrl + "/");

        driver.findElement(By.id("travel_update_tripId")).clear();
        driver.findElement(By.id("travel_update_tripId")).sendKeys(travelinfo.tripId);

        driver.findElement(By.id("travel_update_trainTypeId")).clear();
        driver.findElement(By.id("travel_update_trainTypeId")).sendKeys(travelinfo.trainTypeId);

        driver.findElement(By.id("travel_update_startingStationId")).clear();
        driver.findElement(By.id("travel_update_startingStationId")).sendKeys(travelinfo.startStationName);

        driver.findElement(By.id("travel_update_stationsId")).clear();
        driver.findElement(By.id("travel_update_stationsId")).sendKeys(travelinfo.stationsId);

        driver.findElement(By.id("travel_update_terminalStationId")).clear();
        driver.findElement(By.id("travel_update_terminalStationId")).sendKeys(travelinfo.terminalStationId);

        JavascriptExecutor js = (JavascriptExecutor) driver;
        String jsStartingTime = "document.getElementById('travel_update_startingTime').value='"+travelinfo.startingTime+"'";
        js.executeScript(jsStartingTime);
        //driver.findElement(By.id("travel_update_startingTime")).clear();
        //driver.findElement(By.id("travel_update_startingTime")).sendKeys(travelinfo.startingTime);

        String jsEndTime = "document.getElementById('travel_update_endTime').value='"+travelinfo.endTime+"'";
        js.executeScript(jsEndTime);
        //driver.findElement(By.id("travel_update_endTime")).clear();
        //driver.findElement(By.id("travel_update_endTime")).sendKeys(travelinfo.endTime);

        driver.findElement(By.id("travel_update_button")).click();
        Thread.sleep(1000);

//        String statusUpdateTrip = driver.findElement(By.id("login_result_msg")).getText();
//        if(!"".equals(statusUpdateTrip))
//            System.out.println("Failed,Status of Update Trip btn is NULL!");
//        else
//            System.out.println("Update Trip btn status:"+statusUpdateTrip);
//
//        Assert.assertEquals(statusUpdateTrip.startsWith("Success"),true);
    }
    @Test (dependsOnMethods = {"testTravel"})
    public void testQueryTravel() throws Exception{
        driver.findElement(By.id("travel_queryAll_button")).click();
        Thread.sleep(1000);
        //gain Travel list
        List<WebElement> travelList = driver.findElements(By.xpath("//table[@id='query_travel_list_table']/tbody/tr"));

        if (travelList.size() > 0)
            System.out.printf("Success to Query Travel and Travel list size is %d.%n",travelList.size());
        else
            System.out.println("Failed to Query Travel or Travel list size is 0");
        Assert.assertEquals(travelList.size() > 0,true);
    }
    @AfterClass
    public void tearDown() throws Exception {
        driver.quit();
    }
}


// Node: repos/cloned_ms_repos/train-ticket/old-docs/ts-ui-test/src/test/java/TestServiceTravel.java:TestServiceTravel.<init>
// Node: testTravel
// Node: testQueryTravel
import org.openqa.selenium.By;
import org.openqa.selenium.JavascriptExecutor;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.chrome.ChromeDriver;
import org.testng.Assert;
import org.testng.annotations.AfterClass;
import org.testng.annotations.BeforeClass;
import org.testng.annotations.Test;

import java.util.List;
import java.util.concurrent.TimeUnit;

public class TestServicePrice {
    private WebDriver driver;
    private String baseUrl;
    @BeforeClass
    public void setUp() throws Exception {
        System.setProperty("webdriver.chrome.driver", "D:/Program/chromedriver_win32/chromedriver.exe");
        driver = new ChromeDriver();
        baseUrl = "http://10.141.212.24/";
        driver.manage().timeouts().implicitlyWait(30, TimeUnit.SECONDS);
    }
    @Test
    public void testPrice() throws Exception{
        driver.get(baseUrl + "/");
        JavascriptExecutor js = (JavascriptExecutor) driver;
        js.executeScript("document.getElementById('price_update_startingPlace').value='shanghai'");
        js.executeScript("document.getElementById('price_update_endPlace').value='beijing'");
        js.executeScript("document.getElementById('price_update_distance').value='300'");

        driver.findElement(By.id("price_update_button")).click();
        Thread.sleep(1000);
//        String statusSignIn = driver.findElement(By.id("login_result_msg")).getText();
//        if(statusSignIn ==null || statusSignIn.length() <= 0) {
//            System.out.println("Failed,Status of Sign In btn is NULL!");
//            driver.quit();
//        }else
//            System.out.println("Sign Up btn status:"+statusSignIn);
    }
    @Test (dependsOnMethods = {"testPrice"})
    public void testQueryPrice() throws Exception{
        driver.findElement(By.id("price_queryAll_button")).click();
        Thread.sleep(1000);
        //gain Travel list
        List<WebElement> priceList = driver.findElements(By.xpath("//table[@id='query_price_list_table']/tbody/tr"));
        if (priceList.size() > 0)
            System.out.printf("Success to Query Price and Price list size is %d.%n",priceList.size());
        else
            System.out.println("Failed to Query Price or Price list size is 0");
        Assert.assertEquals(priceList.size() > 0,true);
    }
    @AfterClass
    public void tearDown() throws Exception {
        driver.quit();
    }
}


// Node: repos/cloned_ms_repos/train-ticket/old-docs/ts-ui-test/src/test/java/TestServicePrice.java:TestServicePrice.<init>
// Node: testPrice
// Node: testQueryPrice
import org.openqa.selenium.*;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.support.ui.Select;
import org.testng.Assert;
import org.testng.annotations.AfterClass;
import org.testng.annotations.BeforeClass;
import org.testng.annotations.DataProvider;
import org.testng.annotations.Test;

import java.text.SimpleDateFormat;
import java.util.Calendar;
import java.util.List;
import java.util.Random;
import java.util.concurrent.TimeUnit;


public class TestFlowOne {
    private WebDriver driver;
    private String trainType;//0--all,1--GaoTie,2--others
    private String baseUrl;
    public static void login(WebDriver driver,String username,String password){
        driver.findElement(By.id("flow_one_page")).click();
        driver.findElement(By.id("flow_preserve_login_email")).clear();
        driver.findElement(By.id("flow_preserve_login_email")).sendKeys(username);
        driver.findElement(By.id("flow_preserve_login_password")).clear();
        driver.findElement(By.id("flow_preserve_login_password")).sendKeys(password);
        driver.findElement(By.id("flow_preserve_login_button")).click();
    }
    //获取指定位数的随机字符串(包含数字,0<length)
    public static String getRandomString(int length) {
        //随机字符串的随机字符库
        String KeyString = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
        StringBuffer sb = new StringBuffer();
        int len = KeyString.length();
        for (int i = 0; i < length; i++) {
            sb.append(KeyString.charAt((int) Math.round(Math.random() * (len - 1))));
        }
        return sb.toString();
    }
    @BeforeClass
    public void setUp() throws Exception {
        System.setProperty("webdriver.chrome.driver", "D:/Program/chromedriver_win32/chromedriver.exe");
        baseUrl = "http://10.141.212.24/";
        driver = new ChromeDriver();
        trainType = "1";//all
        driver.manage().timeouts().implicitlyWait(30, TimeUnit.SECONDS);
    }
    @Test
    //Test Flow Preserve Step 1: - Login
    public void testLogin()throws Exception{
        driver.get(baseUrl + "/");

        //define username and password
        String username = "fdse_microservices@163.com";
        String password = "DefaultPassword";

        //call function login
        login(driver,username,password);
        Thread.sleep(1000);

        //get login status
        String statusLogin = driver.findElement(By.id("flow_preserve_login_msg")).getText();
        if("".equals(statusLogin))
            System.out.println("Failed to Login! Status is Null!");
        else if(statusLogin.startsWith("Success"))
            System.out.println("Success to Login! Status:"+statusLogin);
        else
            System.out.println("Failed to Login! Status:"+statusLogin);
        Assert.assertEquals(statusLogin.startsWith("Success"),true);
    }
    @Test (dependsOnMethods = {"testLogin"})
    //test Flow Preserve Step 2: - Ticket Booking
    public void testBooking() throws Exception{
        //locate booking startingPlace input
        WebElement elementBookingStartingPlace = driver.findElement(By.id("travel_booking_startingPlace"));
        elementBookingStartingPlace.clear();
        elementBookingStartingPlace.sendKeys("Shang Hai");

        //locate booking terminalPlace input
        WebElement elementBookingTerminalPlace = driver.findElement(By.id("travel_booking_terminalPlace"));
        elementBookingTerminalPlace.clear();
        elementBookingTerminalPlace.sendKeys("Tai Yuan");

        //locate booking Date input
        String bookDate = "";
        SimpleDateFormat sdf=new SimpleDateFormat("yyyy-MM-dd");
        Calendar newDate = Calendar.getInstance();
        Random randDate = new Random();
        int randomDate = randDate.nextInt(26); //int范围类的随机数
        newDate.add(Calendar.DATE, randomDate+5);//随机定5-30天后的票
        bookDate=sdf.format(newDate.getTime());

        JavascriptExecutor js = (JavascriptExecutor) driver;
        js.executeScript("document.getElementById('travel_booking_date').value='"+bookDate+"'");


        //locate Train Type input
        WebElement elementBookingTraintype = driver.findElement(By.id("search_select_train_type"));
        Select selTraintype = new Select(elementBookingTraintype);
        selTraintype.selectByValue("trainType"); //ALL

        //locate Train search button
        WebElement elementBookingSearchBtn = driver.findElement(By.id("travel_booking_button"));
        elementBookingSearchBtn.click();
        Thread.sleep(1000);

        List<WebElement> ticketsList = driver.findElements(By.xpath("//table[@id='tickets_booking_list_table']/tbody/tr"));
        //Confirm ticket selection
        if (ticketsList.size() == 0) {
            elementBookingSearchBtn.click();
            ticketsList = driver.findElements(By.xpath("//table[@id='tickets_booking_list_table']/tbody/tr"));
        }
        if(ticketsList.size() > 0) {
            //Pick up a train at random and book tickets
            System.out.printf("Success to search tickets，the tickets list size is:%d%n",ticketsList.size());
            Random rand = new Random();
            int i = rand.nextInt(1000) % ticketsList.size(); //int范围类的随机数
            WebElement elementBookingSeat = ticketsList.get(i).findElement(By.xpath("td[10]/select"));
            Select selSeat = new Select(elementBookingSeat);
            selSeat.selectByValue("3"); //2st
            ticketsList.get(i).findElement(By.xpath("td[13]/button")).click();
            Thread.sleep(1000);
        }
        else
            System.out.println("Tickets search failed!!!");
        Assert.assertEquals(ticketsList.size() > 0,true);
    }
   // @Test(enabled = false)
    @Test (dependsOnMethods = {"testBooking"})
    public void testSelectContacts()throws Exception{
        List<WebElement> contactsList = driver.findElements(By.xpath("//table[@id='contacts_booking_list_table']/tbody/tr"));
        //Confirm ticket selection
        if (contactsList.size() == 0) {
            driver.findElement(By.id("refresh_booking_contacts_button")).click();
            Thread.sleep(1000);
            contactsList = driver.findElements(By.xpath("//table[@id='contacts_booking_list_table']/tbody/tr"));
        }
        if(contactsList.size() == 0)
            System.out.println("Show Contacts failed!");
        Assert.assertEquals(contactsList.size() > 0,true);

        if (contactsList.size() == 1){
            String contactName = getRandomString(5);
            String documentType = "1";//ID Card
            String idNumber = getRandomString(8);
            String phoneNumber = getRandomString(11);
            contactsList.get(0).findElement(By.xpath("td[2]/input")).sendKeys(contactName);

            WebElement elementContactstype = contactsList.get(0).findElement(By.xpath("td[3]/select"));
            Select selTraintype = new Select(elementContactstype);
            selTraintype.selectByValue(documentType); //ID type

            contactsList.get(0).findElement(By.xpath("td[4]/input")).sendKeys(idNumber);
            contactsList.get(0).findElement(By.xpath("td[5]/input")).sendKeys(phoneNumber);
            contactsList.get(0).findElement(By.xpath("td[6]/label/input")).click();
        }

        if (contactsList.size() > 1) {
            Random rand = new Random();
            int i = rand.nextInt(100) % (contactsList.size() - 1); //int范围类的随机数
            contactsList.get(i).findElement(By.xpath("td[6]/label/input")).click();
        }
        driver.findElement(By.id("ticket_select_contacts_confirm_btn")).click();
        System.out.println("Ticket contacts selected btn is clicked");
        Thread.sleep(1000);
    }
    @Test (dependsOnMethods = {"testBooking"})
    public void testTicketConfirm ()throws Exception{
        String itemFrom = driver.findElement(By.id("ticket_confirm_from")).getText();
        String itemTo = driver.findElement(By.id("ticket_confirm_to")).getText();
        String itemTripId = driver.findElement(By.id("ticket_confirm_tripId")).getText();
        String itemPrice = driver.findElement(By.id("ticket_confirm_price")).getText();
        String itemDate = driver.findElement(By.id("ticket_confirm_travel_date")).getText();
        String itemName = driver.findElement(By.id("ticket_confirm_contactsName")).getText();
        String itemSeatType = driver.findElement(By.id("ticket_confirm_seatType_String")).getText();
        String itemDocumentType = driver.findElement(By.id("ticket_confirm_documentType")).getText();
        String itemDocumentNum = driver.findElement(By.id("ticket_confirm_documentNumber")).getText();
        boolean bFrom = !"".equals(itemFrom);
        boolean bTo = !"".equals(itemTo);
        boolean bTripId = !"".equals(itemTripId);
        boolean bPrice = !"".equals(itemPrice);
        boolean bDate = !"".equals(itemDate);
        boolean bName = !"".equals(itemName);
        boolean bSeatType = !"".equals(itemSeatType);
        boolean bDocumentType = !"".equals(itemDocumentType);
        boolean bDocumentNum = !"".equals(itemDocumentNum);
        boolean bStatusConfirm = bFrom && bTo && bTripId && bPrice && bDate && bName && bSeatType && bDocumentType && bDocumentNum;
        if(bStatusConfirm == false){
            driver.findElement(By.id("ticket_confirm_cancel_btn")).click();
            System.out.println("Confirming Ticket Canceled!");
        }
        Assert.assertEquals(bStatusConfirm,true);

        driver.findElement(By.id("ticket_confirm_confirm_btn")).click();
        Thread.sleep(1000);
        System.out.println("Confirm Ticket!");
        Alert javascriptConfirm = driver.switchTo().alert();
        String statusAlert = driver.switchTo().alert().getText();
        System.out.println("The Alert information of Confirming Ticket："+statusAlert);
        Assert.assertEquals(statusAlert.startsWith("Success"),true);
        javascriptConfirm.accept();
    }
    @Test (dependsOnMethods = {"testTicketConfirm"})
    public void testTicketPay ()throws Exception {
        String itemOrderId = driver.findElement(By.id("preserve_pay_orderId")).getAttribute("value");
        String itemPrice = driver.findElement(By.id("preserve_pay_price")).getAttribute("value");
        String itemTripId = driver.findElement(By.id("preserve_pay_tripId")).getAttribute("value");
        boolean bOrderId = !"".equals(itemOrderId);
        boolean bPrice = !"".equals(itemPrice);
        boolean bTripId = !"".equals(itemTripId);
        boolean bStatusPay = bOrderId && bPrice && bTripId;
        if(bStatusPay == false)
            System.out.println("Confirming Ticket failed!");
        Assert.assertEquals(bStatusPay,true);

        driver.findElement(By.id("preserve_pay_button")).click();
        Thread.sleep(1000);
        String itemCollectOrderId = driver.findElement(By.id("preserve_collect_order_id")).getAttribute("value");
        Assert.assertEquals(!"".equals(itemCollectOrderId),true);
        System.out.println("Success to pay and book ticket!");
    }
    @Test (dependsOnMethods = {"testTicketPay"})
    public void testTicketCollect ()throws Exception {
        String itemCollectOrderId = driver.findElement(By.id("preserve_collect_order_id")).getAttribute("value");
        boolean bCollectOrderId = !"".equals(itemCollectOrderId);
        if(bCollectOrderId == false)
            System.out.println("Ticket payment failed!");
        Assert.assertEquals(bCollectOrderId,true);

        driver.findElement(By.id("preserve_collect_button")).click();
        Thread.sleep(1000);
        String statusCollectOrderId = driver.findElement(By.id("preserve_collect_order_status")).getText();

        if("".equals(statusCollectOrderId))
            System.out.println("Failed to Collect Ticket! Status is Null!");
        else if(statusCollectOrderId.startsWith("Success"))
            System.out.println("Success to Collect Ticket! Status:"+statusCollectOrderId);
        else
            System.out.println("Failed to Collect Ticket! Status is:"+statusCollectOrderId);
        Assert.assertEquals(statusCollectOrderId.startsWith("Success"),true);
    }
    @Test (dependsOnMethods = {"testTicketCollect"})
    public void testEnterStation ()throws Exception {
        String itemEnterOrderId = driver.findElement(By.id("preserve_execute_order_id")).getAttribute("value");
        if("".equals(itemEnterOrderId))
            System.out.println("Enter Station,No Order Id,failed");
        Assert.assertEquals(!"".equals(itemEnterOrderId),true);

        driver.findElement(By.id("preserve_order_button")).click();
        Thread.sleep(1000);
        String statusEnterStation = driver.findElement(By.id("preserve_order_status")).getText();
        if("".equals(statusEnterStation))
            System.out.println("Failed to Enter Station! Status is Null!");
        else if(statusEnterStation.startsWith("Success"))
            System.out.println("Success to Enter Station! Status:"+statusEnterStation);
        else
            System.out.println("Failed to Enter Station! Status is:"+statusEnterStation);
        Assert.assertEquals(statusEnterStation.startsWith("Success"),true);
    }
    @AfterClass
    public void tearDown() throws Exception {
        driver.quit();
    }
}


// Node: getRandomString
// Node: StringBuffer
// Node: round
// Node: testBooking
// Node: testSelectContacts
// Node: testTicketConfirm
// Node: testTicketPay
// Node: testEnterStation
import org.openqa.selenium.By;
import org.openqa.selenium.JavascriptExecutor;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.chrome.ChromeDriver;
import org.testng.Assert;
import org.testng.annotations.AfterClass;
import org.testng.annotations.BeforeClass;
import org.testng.annotations.Test;

import java.util.concurrent.TimeUnit;


public class TestServiceCancel {
    private WebDriver driver;
    private String baseUrl;
    public static void login(WebDriver driver,String username,String password){
        driver.findElement(By.id("flow_one_page")).click();
        driver.findElement(By.id("flow_preserve_login_email")).clear();
        driver.findElement(By.id("flow_preserve_login_email")).sendKeys(username);
        driver.findElement(By.id("flow_preserve_login_password")).clear();
        driver.findElement(By.id("flow_preserve_login_password")).sendKeys(password);
        driver.findElement(By.id("flow_preserve_login_button")).click();
    }
    @BeforeClass
    public void setUp() throws Exception {
        System.setProperty("webdriver.chrome.driver", "D:/Program/chromedriver_win32/chromedriver.exe");
        driver = new ChromeDriver();
        baseUrl = "http://10.141.212.24/";
        driver.manage().timeouts().implicitlyWait(30, TimeUnit.SECONDS);
    }
    @Test
    public void login()throws Exception{
        driver.get(baseUrl + "/");

        //define username and password
        String username = "fdse_microservices@163.com";
        String password = "DefaultPassword";

        //call function login
        login(driver,username,password);
        Thread.sleep(1000);

        //get login status
        String statusLogin = driver.findElement(By.id("flow_preserve_login_msg")).getText();
        if("".equals(statusLogin))
            System.out.println("Failed to Login! Status is Null!");
        else if(statusLogin.startsWith("Success"))
            System.out.println("Success to Login! Status:"+statusLogin);
        else
            System.out.println("Failed to Login! Status:"+statusLogin);

        Assert.assertEquals(statusLogin.startsWith("Success"),true);
        driver.findElement(By.id("microservice_page")).click();
    }
    @Test (dependsOnMethods = {"login"})
    public void testCheckRefund() throws Exception{
        JavascriptExecutor js = (JavascriptExecutor) driver;
        js.executeScript("document.getElementById('single_cancel_order_id').value='5ad7750b-a68b-49c0-a8c0-32776b067703'");

        driver.findElement(By.id("single_cancel_refund_button")).click();
        Thread.sleep(500);
        String statusCancelRefundBtn = driver.findElement(By.id("single_cancel_refund_result")).getText();
        System.out.println("Cancel Refund Btn status:"+statusCancelRefundBtn);
        Assert.assertEquals(!"".equals(statusCancelRefundBtn), true);
    }
    @Test (dependsOnMethods = {"testCheckRefund"})
    public void testTicketCancel() throws Exception {
        driver.findElement(By.id("single_cancel_button")).click();
        Thread.sleep(1000);
        String statusCancelOrderResult = driver.findElement(By.id("single_cancel_order_result")).getText();
        System.out.println("Do Cancel Btn status:"+statusCancelOrderResult);
        Assert.assertEquals(statusCancelOrderResult.startsWith("Success"), true);
    }
    @AfterClass
    public void tearDown() throws Exception {
        driver.quit();
    }
}


// Node: testCheckRefund
// Node: testTicketCancel
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


// Node: queryForNameBatch
// Node: queryByIdBatch
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


// Node: testQueryByIdBatch1
