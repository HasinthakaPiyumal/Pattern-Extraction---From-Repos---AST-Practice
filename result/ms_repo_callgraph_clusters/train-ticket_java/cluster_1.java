// Cluster 1

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


// Node: main
// Node: run
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


// Node: getUserName
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



// Node: createDefaultUser
// Node: createDefaultAuthUser
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


// Node: builder
// Node: userId
// Node: username
// Node: password
// Node: encode
// Node: getPassword
// Node: roles
// Node: checkUserCreateInfo
package auth.init;

import auth.entity.User;
import auth.repository.UserRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.CommandLineRunner;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Component;

import java.util.Arrays;
import java.util.HashSet;
import java.util.UUID;

/**
 * @author fdse
 */
@Component
public class InitUser implements CommandLineRunner {

    @Autowired
    private UserRepository userRepository;

    @Autowired
    protected PasswordEncoder passwordEncoder;


    @Override
    public void run(String... strings) throws Exception {
        User whetherExistUser = userRepository.findByUsername("fdse_microservice").orElse(new User());
        if (whetherExistUser.getUsername() == null) {
            User user = User.builder()
                    .userId("4d2a46c7-71cb-4cf1-b5bb-b68406d9da6f")
                    .username("fdse_microservice")
                    .password(passwordEncoder.encode("111111"))
                    .roles(new HashSet<>(Arrays.asList("ROLE_USER")))
                    .build();
            userRepository.save(user);
        }

        User whetherExistAdmin = userRepository.findByUsername("admin").orElse(new User());
        if (whetherExistAdmin.getUsername() == null) {
            User admin = User.builder()
                    .userId(UUID.randomUUID().toString())
                    .username("admin")
                    .password(passwordEncoder.encode("222222"))
                    .roles(new HashSet<>(Arrays.asList("ROLE_ADMIN")))
                    .build();
            userRepository.save(admin);
        }
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-auth-service/src/main/java/auth/init/InitUser.java:InitUser.<init>
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


package gateway;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;
import org.springframework.context.annotation.EnableAspectJAutoProxy;
import org.springframework.integration.annotation.IntegrationComponentScan;
import org.springframework.scheduling.annotation.EnableAsync;

@SpringBootApplication
@EnableAspectJAutoProxy(proxyTargetClass = true)
@EnableAsync
@IntegrationComponentScan
@EnableDiscoveryClient
public class GatewayApplication {
    public static void main(String[] args) {
        SpringApplication.run(GatewayApplication.class, args);
    }

}


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


// Node: SpanBuilder


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


/*
 * This Java source file was generated by the Gradle 'init' task.
 */

package org.services.analysis;


public class App {
    public String getGreeting() {
        return "Hello world.";
    }

//    public static void main(String[] args) {
//        System.out.println(new App().getGreeting());
//    }
}


// Node: getGreeting
// Node: App
/*
 * This Java source file was generated by the Gradle 'init' task.
 */

//package org.services.analysis;
//
//
//import org.junit.Test;
//import static org.junit.Assert.*;
//
//public class AppTest {
//    @Test public void testAppHasAGreeting() {
//        App classUnderTest = new App();
//        assertNotNull("app should have a greeting", classUnderTest.getGreeting());
//    }
//}


// Node: testAppHasAGreeting
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


// Node: userName
// Node: gender
// Node: getGender
// Node: documentType
// Node: documentNum
// Node: getDocumentNum
// Node: email
package user.init;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.CommandLineRunner;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Component;
import user.entity.User;
import user.repository.UserRepository;
import user.service.UserService;


import java.util.UUID;

/**
 * @author fdse
 */
@Component
public class InitUser implements CommandLineRunner {

    @Autowired
    private UserRepository userRepository;

    @Autowired
    protected PasswordEncoder passwordEncoder;

    @Autowired
    private UserService userService;

    @Override
    public void run(String... strings) throws Exception {
        User whetherExistUser = userRepository.findByUserName("fdse_microservice");
        User user = User.builder()
                .userId("4d2a46c7-71cb-4cf1-b5bb-b68406d9da6f")
                .userName("fdse_microservice")
                .password("111111")
                .gender(1)
                .documentType(1)
                .documentNum("2135488099312X")
                .email("trainticket_notify@163.com").build();
        user.setUserId("4d2a46c7-71cb-4cf1-b5bb-b68406d9da6f");
        if (whetherExistUser == null) {
            userRepository.save(user);
        }
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-user-service/src/main/java/user/init/InitUser.java:InitUser.<init>
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


