// Cluster 8

package adminuser.config;

import edu.fudan.common.security.jwt.JWTFilter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.method.configuration.EnableGlobalMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configuration.WebSecurityConfigurerAdapter;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurerAdapter;

import static org.springframework.web.cors.CorsConfiguration.ALL;

/**
 * @author fdse
 */
@Configuration
@EnableWebSecurity
@EnableGlobalMethodSecurity(prePostEnabled = true)
public class SecurityConfig extends WebSecurityConfigurerAdapter {

    /**
     * load password encoder
     *
     * @return PasswordEncoder
     */
    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    /**
     * allow cors domain
     * header  By default, only six fields can be taken from the header, and the other fields can only be specified in the header.
     * credentials   Cookies are not sent by default and can only be true if a Cookie is needed
     * Validity of this request
     *
     * @return WebMvcConfigurer
     */
    @Bean
    public WebMvcConfigurer corsConfigurer() {
        return new WebMvcConfigurerAdapter() {
            @Override
            public void addCorsMappings(CorsRegistry registry) {
                registry.addMapping("/**")
                        .allowedOrigins(ALL)
                        .allowedMethods(ALL)
                        .allowedHeaders(ALL)
                        .allowCredentials(false)
                        .maxAge(3600);
            }
        };
    }


    @Override
    protected void configure(HttpSecurity httpSecurity) throws Exception {
        httpSecurity.httpBasic().disable()
                // close default csrf
                .csrf().disable()
                // close session
                .sessionManagement().sessionCreationPolicy(SessionCreationPolicy.STATELESS)
                .and()
                .authorizeRequests()
                .antMatchers("/swagger-ui.html", "/webjars/**", "/images/**",
                        "/configuration/**", "/swagger-resources/**", "/v2/**").permitAll()
                .antMatchers("/api/v1/adminuserservice/users/**").hasRole("ADMIN")
                .anyRequest().authenticated()
                .and()
                .addFilterBefore(new JWTFilter(), UsernamePasswordAuthenticationFilter.class);

        // close cache
        httpSecurity.headers().cacheControl();
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-admin-user-service/src/main/java/adminuser/config/SecurityConfig.java:SecurityConfig.<init>
// Node: EnableGlobalMethodSecurity
// Node: passwordEncoder
// Node: BCryptPasswordEncoder
package waitorder.config;

import edu.fudan.common.security.jwt.JWTFilter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpMethod;
import org.springframework.security.config.annotation.method.configuration.EnableGlobalMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configuration.WebSecurityConfigurerAdapter;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurerAdapter;

import static org.springframework.web.cors.CorsConfiguration.ALL;

/**
 * @author fdse
 */
@Configuration
@EnableWebSecurity
@EnableGlobalMethodSecurity(prePostEnabled = true)
public class SecurityConfig extends WebSecurityConfigurerAdapter {

    String admin = "ADMIN";
    String order = "/api/v1/orderservice/order";

    /**
     * load password encoder
     *
     * @return PasswordEncoder
     */
    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    /**
     * allow cors domain
     * header  By default, only six fields can be taken from the header, and the other fields can only be specified in the header.
     * credentials   Cookies are not sent by default and can only be true if a Cookie is needed
     * Validity of this request
     *
     * @return WebMvcConfigurer
     */
    @Bean
    public WebMvcConfigurer corsConfigurer() {
        return new WebMvcConfigurerAdapter() {
            @Override
            public void addCorsMappings(CorsRegistry registry) {
                registry.addMapping("/**")
                        .allowedOrigins(ALL)
                        .allowedMethods(ALL)
                        .allowedHeaders(ALL)
                        .allowCredentials(false)
                        .maxAge(3600);
            }
        };
    }


    @Override
    protected void configure(HttpSecurity httpSecurity) throws Exception {
        httpSecurity.httpBasic().disable()
                // close default csrf
                .csrf().disable()
                // close session
                .sessionManagement().sessionCreationPolicy(SessionCreationPolicy.STATELESS)
                .and()
                .authorizeRequests()
                .antMatchers(HttpMethod.POST, order).hasAnyRole(admin, "USER")
                .antMatchers(HttpMethod.PUT, order).hasAnyRole(admin, "USER")
                .antMatchers(HttpMethod.DELETE, order).hasAnyRole(admin, "USER")
                .antMatchers(HttpMethod.POST, "/api/v1/orderservice/order/admin").hasAnyRole(admin)
                .antMatchers(HttpMethod.PUT, "/api/v1/orderservice/order/admin").hasAnyRole(admin)
                .antMatchers("/api/v1/orderservice/order/**").permitAll()
                .antMatchers("/swagger-ui.html", "/webjars/**", "/images/**",
                        "/configuration/**", "/swagger-resources/**", "/v2/**").permitAll()
                .anyRequest().authenticated()
                .and()
                .addFilterBefore(new JWTFilter(), UsernamePasswordAuthenticationFilter.class);

        // close cache
        httpSecurity.headers().cacheControl();
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-wait-order-service/src/main/java/waitorder/config/SecurityConfig.java:SecurityConfig.<init>
// Node: getRoles
package auth.config;


import edu.fudan.common.security.jwt.JWTFilter;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpMethod;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.config.annotation.authentication.builders.AuthenticationManagerBuilder;
import org.springframework.security.config.annotation.method.configuration.EnableGlobalMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configuration.WebSecurityConfigurerAdapter;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurerAdapter;

import static org.springframework.web.cors.CorsConfiguration.ALL;

/**
 * @author fdse
 */
@Configuration
@EnableWebSecurity
@EnableGlobalMethodSecurity(prePostEnabled = true)
public class WebSecurityConfig extends WebSecurityConfigurerAdapter {


    @Autowired
    @Qualifier("userDetailServiceImpl")
    private UserDetailsService userDetailsService;

    @Bean
    @Override
    public AuthenticationManager authenticationManager() throws Exception {
        return super.authenticationManager();
    }

    @Autowired
    public void configureAuthentication(AuthenticationManagerBuilder authenticationManagerBuilder) throws Exception {
        authenticationManagerBuilder
                .userDetailsService(this.userDetailsService)
                .passwordEncoder(passwordEncoder());
    }

    @Bean
    public WebMvcConfigurer corsConfigurer() {
        return new WebMvcConfigurerAdapter() {
            @Override
            public void addCorsMappings(CorsRegistry registry) {
                registry.addMapping("/**")
                        .allowedOrigins(ALL)
                        .allowedMethods(ALL)
                        .allowedHeaders(ALL)
                        .allowCredentials(false)
                        .maxAge(3600);
            }
        };
    }

    /**
     * load password encoder
     *
     * @return PasswordEncoder
     */
    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    @Override
    protected void configure(HttpSecurity httpSecurity) throws Exception {
        httpSecurity
                .httpBasic().disable()
                .csrf().disable()
                .sessionManagement().sessionCreationPolicy(SessionCreationPolicy.STATELESS)
                .and()
                .authorizeRequests()
                .antMatchers("/api/v1/auth", "/api/v1/auth/hello", "/api/v1/user/hello").permitAll()
                .antMatchers("/api/v1/users/login").permitAll()
                .antMatchers(HttpMethod.GET, "/api/v1/users").hasRole("ADMIN")
                .antMatchers(HttpMethod.DELETE, "/api/v1/users/*").hasRole("ADMIN")
                // create user and role while user register
                .antMatchers("/user/**").permitAll()
                .antMatchers("/swagger-ui.html", "/webjars/**", "/images/**",
                        "/configuration/**", "/swagger-resources/**", "/v2/**").permitAll()
                .anyRequest().authenticated()
                .and()
                .addFilterBefore(new JWTFilter(), UsernamePasswordAuthenticationFilter.class);

        httpSecurity.headers().cacheControl();
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-auth-service/src/main/java/auth/config/WebSecurityConfig.java:WebSecurityConfig.<init>
// Node: Qualifier
// Node: authenticationManager
// Node: configureAuthentication
// Node: userDetailsService
package auth.security.jwt;

import auth.constant.InfoConstant;
import auth.entity.User;
import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.SignatureAlgorithm;
import org.springframework.stereotype.Component;

import javax.annotation.PostConstruct;
import java.util.Base64;
import java.util.Date;

/**
 * @author fdse
 */
@Component
public class JWTProvider {

    private String secretKey = "secret";

    private long validityInMilliseconds = 3600000;

    @PostConstruct
    protected void init() {
        secretKey = Base64.getEncoder().encodeToString(secretKey.getBytes());
    }

    public String createToken(User user) {

        Claims claims = Jwts.claims().setSubject(user.getUsername());
        claims.put(InfoConstant.ROLES, user.getRoles());
        claims.put(InfoConstant.ID, user.getUserId());

        Date now = new Date();
        Date validate = new Date(now.getTime() + validityInMilliseconds);

        return Jwts.builder()
                .setClaims(claims)
                .setIssuedAt(now)
                .setExpiration(validate)
                .signWith(SignatureAlgorithm.HS256, secretKey)
                .compact();
    }
}

// Node: claims
// Node: setSubject
// Node: setClaims
// Node: setIssuedAt
// Node: setExpiration
// Node: signWith
// Node: compact
package plan.config;

import edu.fudan.common.security.jwt.JWTFilter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.method.configuration.EnableGlobalMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configuration.WebSecurityConfigurerAdapter;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurerAdapter;

import static org.springframework.web.cors.CorsConfiguration.ALL;

/**
 * @author fdse
 */
@Configuration
@EnableWebSecurity
@EnableGlobalMethodSecurity(prePostEnabled = true)
public class SecurityConfig extends WebSecurityConfigurerAdapter {

    /**
     * load password encoder
     *
     * @return PasswordEncoder
     */
    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    /**
     * allow cors domain
     * header  By default, only six fields can be taken from the header, and the other fields can only be specified in the header.
     * credentials   Cookies are not sent by default and can only be true if a Cookie is needed
     * Validity of this request
     *
     * @return WebMvcConfigurer
     */
    @Bean
    public WebMvcConfigurer corsConfigurer() {
        return new WebMvcConfigurerAdapter() {
            @Override
            public void addCorsMappings(CorsRegistry registry) {
                registry.addMapping("/**")
                        .allowedOrigins(ALL)
                        .allowedMethods(ALL)
                        .allowedHeaders(ALL)
                        .allowCredentials(false)
                        .maxAge(3600);
            }
        };
    }


    @Override
    protected void configure(HttpSecurity httpSecurity) throws Exception {
        httpSecurity.httpBasic().disable()
                // close default csrf
                .csrf().disable()
                // close session
                .sessionManagement().sessionCreationPolicy(SessionCreationPolicy.STATELESS)
                .and()
                .authorizeRequests()
                .antMatchers("/api/v1/routeplanservice/**").permitAll()
                .antMatchers("/swagger-ui.html", "/webjars/**", "/images/**",
                        "/configuration/**", "/swagger-resources/**", "/v2/**").permitAll()
                .anyRequest().authenticated()
                .and()
                .addFilterBefore(new JWTFilter(), UsernamePasswordAuthenticationFilter.class);

        // close cache
        httpSecurity.headers().cacheControl();
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-route-plan-service/src/main/java/plan/config/SecurityConfig.java:SecurityConfig.<init>
package adminroute.config;

import edu.fudan.common.security.jwt.JWTFilter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.method.configuration.EnableGlobalMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configuration.WebSecurityConfigurerAdapter;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurerAdapter;

import static org.springframework.web.cors.CorsConfiguration.ALL;

/**
 * @author fdse
 */
@Configuration
@EnableWebSecurity
@EnableGlobalMethodSecurity(prePostEnabled = true)
public class SecurityConfig extends WebSecurityConfigurerAdapter {

    /**
     * load password encoder
     *
     * @return PasswordEncoder
     */
    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    /**
     * allow cors domain
     * header  By default, only six fields can be taken from the header, and the other fields can only be specified in the header.
     * credentials   Cookies are not sent by default and can only be true if a Cookie is needed
     * Validity of this request
     *
     * @return WebMvcConfigurer
     */
    @Bean
    public WebMvcConfigurer corsConfigurer() {
        return new WebMvcConfigurerAdapter() {
            @Override
            public void addCorsMappings(CorsRegistry registry) {
                registry.addMapping("/**")
                        .allowedOrigins(ALL)
                        .allowedMethods(ALL)
                        .allowedHeaders(ALL)
                        .allowCredentials(false)
                        .maxAge(3600);
            }
        };
    }


    @Override
    protected void configure(HttpSecurity httpSecurity) throws Exception {
        httpSecurity.httpBasic().disable()
                // close default csrf
                .csrf().disable()
                // close session
                .sessionManagement().sessionCreationPolicy(SessionCreationPolicy.STATELESS)
                .and()
                .authorizeRequests()
                .antMatchers("/api/v1/adminrouteservice/**").hasRole("ADMIN")
                .antMatchers("/swagger-ui.html", "/webjars/**", "/images/**",
                        "/configuration/**", "/swagger-resources/**", "/v2/**").permitAll()
                .anyRequest().authenticated()
                .and()
                .addFilterBefore(new JWTFilter(), UsernamePasswordAuthenticationFilter.class);

        // close cache
        httpSecurity.headers().cacheControl();
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-admin-route-service/src/main/java/adminroute/config/SecurityConfig.java:SecurityConfig.<init>
package com.trainticket.config;

import edu.fudan.common.security.jwt.JWTFilter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.method.configuration.EnableGlobalMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configuration.WebSecurityConfigurerAdapter;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurerAdapter;

import static org.springframework.web.cors.CorsConfiguration.ALL;

/**
 * @author fdse
 */
@Configuration
@EnableWebSecurity
@EnableGlobalMethodSecurity(prePostEnabled = true)
public class SecurityConfig extends WebSecurityConfigurerAdapter {

    /**
     * load password encoder
     *
     * @return PasswordEncoder
     */
    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    /**
     * allow cors domain
     * header  By default, only six fields can be taken from the header, and the other fields can only be specified in the header.
     * credentials   Cookies are not sent by default and can only be true if a Cookie is needed
     * Validity of this request
     *
     * @return WebMvcConfigurer
     */
    @Bean
    public WebMvcConfigurer corsConfigurer() {
        return new WebMvcConfigurerAdapter() {
            @Override
            public void addCorsMappings(CorsRegistry registry) {
                registry.addMapping("/**")
                        .allowedOrigins(ALL)
                        .allowedMethods(ALL)
                        .allowedHeaders(ALL)
                        .allowCredentials(false)
                        .maxAge(3600);
            }
        };
    }


    @Override
    protected void configure(HttpSecurity httpSecurity) throws Exception {
        httpSecurity.httpBasic().disable()
                // close default csrf
                .csrf().disable()
                // close session
                .sessionManagement().sessionCreationPolicy(SessionCreationPolicy.STATELESS)
                .and()
                .authorizeRequests()
                .antMatchers("/api/v1/paymentservice/**").hasAnyRole("ADMIN", "USER")
                .antMatchers("/swagger-ui.html", "/webjars/**", "/images/**",
                        "/configuration/**", "/swagger-resources/**", "/v2/**").permitAll()
                .anyRequest().authenticated()
                .and()
                .addFilterBefore(new JWTFilter(), UsernamePasswordAuthenticationFilter.class);

        // close cache
        httpSecurity.headers().cacheControl();
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-payment-service/src/main/java/com/trainticket/config/SecurityConfig.java:SecurityConfig.<init>
package price.config;

import edu.fudan.common.security.jwt.JWTFilter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpMethod;
import org.springframework.security.config.annotation.method.configuration.EnableGlobalMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configuration.WebSecurityConfigurerAdapter;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurerAdapter;

import static org.springframework.web.cors.CorsConfiguration.ALL;

/**
 * @author fdse
 */
@Configuration
@EnableWebSecurity
@EnableGlobalMethodSecurity(prePostEnabled = true)
public class SecurityConfig extends WebSecurityConfigurerAdapter {

    String admin = "ADMIN";
    String prices = "/api/v1/priceservice/prices";

    /**
     * load password encoder
     *
     * @return PasswordEncoder
     */
    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    /**
     * allow cors domain
     * header  By default, only six fields can be taken from the header, and the other fields can only be specified in the header.
     * credentials   Cookies are not sent by default and can only be true if a Cookie is needed
     * Validity of this request
     *
     * @return WebMvcConfigurer
     */
    @Bean
    public WebMvcConfigurer corsConfigurer() {
        return new WebMvcConfigurerAdapter() {
            @Override
            public void addCorsMappings(CorsRegistry registry) {
                registry.addMapping("/**")
                        .allowedOrigins(ALL)
                        .allowedMethods(ALL)
                        .allowedHeaders(ALL)
                        .allowCredentials(false)
                        .maxAge(3600);
            }
        };
    }


    @Override
    protected void configure(HttpSecurity httpSecurity) throws Exception {
        httpSecurity.httpBasic().disable()
                // close default csrf
                .csrf().disable()
                // close session
                .sessionManagement().sessionCreationPolicy(SessionCreationPolicy.STATELESS)
                .and()
                .authorizeRequests()
                .antMatchers("/api/v1/priceservice/**").permitAll()
                .antMatchers(HttpMethod.POST, prices).hasAnyRole(admin)
                .antMatchers(HttpMethod.DELETE, prices).hasAnyRole(admin)
                .antMatchers(HttpMethod.PUT, prices).hasAnyRole(admin)
                .antMatchers("/swagger-ui.html", "/webjars/**", "/images/**",
                        "/configuration/**", "/swagger-resources/**", "/v2/**").permitAll()
                .anyRequest().authenticated()
                .and()
                .addFilterBefore(new JWTFilter(), UsernamePasswordAuthenticationFilter.class);

        // close cache
        httpSecurity.headers().cacheControl();
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-price-service/src/main/java/price/config/SecurityConfig.java:SecurityConfig.<init>
package notification.service;

import javax.mail.internet.MimeMessage;

import notification.entity.Mail;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.mail.javamail.MimeMessageHelper;
import org.springframework.stereotype.Service;
import org.springframework.ui.freemarker.FreeMarkerTemplateUtils;

import freemarker.template.Configuration;
import freemarker.template.Template;

/**
 * @author fdse
 */
@Service
public class MailService {

    @Autowired
    private JavaMailSender sender;

    @Autowired
    @Qualifier("freeMarkerConfiguration")
    private Configuration freemarkerConfig;


    public void sendEmail(Mail mail,String template) throws Exception {
        MimeMessage message = sender.createMimeMessage();

        MimeMessageHelper helper = new MimeMessageHelper(message);

        // Using a subfolder such as /templates here
        freemarkerConfig.setClassForTemplateLoading(this.getClass(), "/templates");

        Template t = freemarkerConfig.getTemplate(template);
        String text = FreeMarkerTemplateUtils.processTemplateIntoString(t, mail.getModel());

        helper.setTo(mail.getMailTo());
        helper.setText(text, true);
        helper.setFrom(mail.getMailFrom());
        helper.setSubject(mail.getMailSubject());

        sender.send(message);
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-notification-service/src/main/java/notification/service/MailService.java:MailService.<init>
// Node: createMimeMessage
// Node: MimeMessageHelper
// Node: setClassForTemplateLoading
// Node: getTemplate
// Node: processTemplateIntoString
// Node: getModel
// Node: getMailTo
// Node: setText
// Node: getMailFrom
// Node: getMailSubject
package notification.config;

import edu.fudan.common.security.jwt.JWTFilter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.method.configuration.EnableGlobalMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configuration.WebSecurityConfigurerAdapter;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurerAdapter;

import static org.springframework.web.cors.CorsConfiguration.ALL;

/**
 * @author fdse
 */
@Configuration
@EnableWebSecurity
@EnableGlobalMethodSecurity(prePostEnabled = true)
public class SecurityConfig extends WebSecurityConfigurerAdapter {

    /**
     * load password encoder
     *
     * @return PasswordEncoder
     */
    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    /**
     * allow cors domain
     * header  By default, only six fields can be taken from the header, and the other fields can only be specified in the header.
     * credentials   Cookies are not sent by default and can only be true if a Cookie is needed
     * Validity of this request
     *
     * @return WebMvcConfigurer
     */
    @Bean
    public WebMvcConfigurer corsConfigurer() {
        return new WebMvcConfigurerAdapter() {
            @Override
            public void addCorsMappings(CorsRegistry registry) {
                registry.addMapping("/**")
                        .allowedOrigins(ALL)
                        .allowedMethods(ALL)
                        .allowedHeaders(ALL)
                        .allowCredentials(false)
                        .maxAge(3600);
            }
        };
    }


    @Override
    protected void configure(HttpSecurity httpSecurity) throws Exception {
        httpSecurity.httpBasic().disable()
                // close default csrf
                .csrf().disable()
                // close session
                .sessionManagement().sessionCreationPolicy(SessionCreationPolicy.STATELESS)
                .and()
                .authorizeRequests()
                .antMatchers("/api/v1/notifyservice/**").permitAll()
                //.antMatchers("/api/v1/notifyservice/**").hasAnyRole("ADMIN", "USER")
                .antMatchers("/swagger-ui.html", "/webjars/**", "/images/**",
                        "/configuration/**", "/swagger-resources/**", "/v2/**").permitAll()
                .anyRequest().authenticated()
                .and()
                .addFilterBefore(new JWTFilter(), UsernamePasswordAuthenticationFilter.class);

        // close cache
        httpSecurity.headers().cacheControl();
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-notification-service/src/main/java/notification/config/SecurityConfig.java:SecurityConfig.<init>
package fdse.microservice.config;

import edu.fudan.common.security.jwt.JWTFilter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.method.configuration.EnableGlobalMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configuration.WebSecurityConfigurerAdapter;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurerAdapter;

import static org.springframework.web.cors.CorsConfiguration.ALL;

/**
 * @author fdse
 */
@Configuration
@EnableWebSecurity
@EnableGlobalMethodSecurity(prePostEnabled = true)
public class SecurityConfig extends WebSecurityConfigurerAdapter {

    /**
     * load password encoder
     *
     * @return PasswordEncoder
     */
    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    /**
     * allow cors domain
     * header  By default, only six fields can be taken from the header, and the other fields can only be specified in the header.
     * credentials   Cookies are not sent by default and can only be true if a Cookie is needed
     * Validity of this request
     *
     * @return WebMvcConfigurer
     */
    @Bean
    public WebMvcConfigurer corsConfigurer() {
        return new WebMvcConfigurerAdapter() {
            @Override
            public void addCorsMappings(CorsRegistry registry) {
                registry.addMapping("/**")
                        .allowedOrigins(ALL)
                        .allowedMethods(ALL)
                        .allowedHeaders(ALL)
                        .allowCredentials(false)
                        .maxAge(3600);
            }
        };
    }


    @Override
    protected void configure(HttpSecurity httpSecurity) throws Exception {
        httpSecurity.httpBasic().disable()
                // close default csrf
                .csrf().disable()
                // close session
                .sessionManagement().sessionCreationPolicy(SessionCreationPolicy.STATELESS)
                .and()
                .authorizeRequests()
                .antMatchers("/api/v1/basicservice/**").permitAll()
                .antMatchers("/swagger-ui.html", "/webjars/**", "/images/**",
                        "/configuration/**", "/swagger-resources/**", "/v2/**").permitAll()
                .anyRequest().authenticated()
                .and()
                .addFilterBefore(new JWTFilter(), UsernamePasswordAuthenticationFilter.class);

        // close cache
        httpSecurity.headers().cacheControl();
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-basic-service/src/main/java/fdse/microservice/config/SecurityConfig.java:SecurityConfig.<init>
package other.config;

import edu.fudan.common.security.jwt.JWTFilter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpMethod;
import org.springframework.security.config.annotation.method.configuration.EnableGlobalMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configuration.WebSecurityConfigurerAdapter;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurerAdapter;

import static org.springframework.web.cors.CorsConfiguration.ALL;

/**
 * @author fdse
 */
@Configuration
@EnableWebSecurity
@EnableGlobalMethodSecurity(prePostEnabled = true)
public class SecurityConfig extends WebSecurityConfigurerAdapter {

    String admin = "ADMIN";
    String orderOther = "/api/v1/orderOtherService/orderOther";
    /**
     * load password encoder
     *
     * @return PasswordEncoder
     */
    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    /**
     * allow cors domain
     * header  By default, only six fields can be taken from the header, and the other fields can only be specified in the header.
     * credentials   Cookies are not sent by default and can only be true if a Cookie is needed
     * Validity of this request
     *
     * @return WebMvcConfigurer
     */
    @Bean
    public WebMvcConfigurer corsConfigurer() {
        return new WebMvcConfigurerAdapter() {
            @Override
            public void addCorsMappings(CorsRegistry registry) {
                registry.addMapping("/**")
                        .allowedOrigins(ALL)
                        .allowedMethods(ALL)
                        .allowedHeaders(ALL)
                        .allowCredentials(false)
                        .maxAge(3600);
            }
        };
    }


    @Override
    protected void configure(HttpSecurity httpSecurity) throws Exception {
        httpSecurity.httpBasic().disable()
                // close default csrf
                .csrf().disable()
                // close session
                .sessionManagement().sessionCreationPolicy(SessionCreationPolicy.STATELESS)
                .and()
                .authorizeRequests()
                .antMatchers("/api/v1/orderOtherService/orderOther/**").permitAll()
                .antMatchers(HttpMethod.POST, orderOther).hasAnyRole(admin, "USER")
                .antMatchers(HttpMethod.PUT, orderOther).hasAnyRole(admin, "USER")
                .antMatchers(HttpMethod.DELETE, orderOther).hasAnyRole(admin, "USER")
                .antMatchers(HttpMethod.POST, "/api/v1/orderOtherService/orderOther/admin").hasAnyRole(admin)
                .antMatchers(HttpMethod.PUT, "/api/v1/orderOtherService/orderOther/admin").hasAnyRole(admin)

                .antMatchers("/swagger-ui.html", "/webjars/**", "/images/**",
                        "/configuration/**", "/swagger-resources/**", "/v2/**").permitAll()
                .anyRequest().authenticated()
                .and()
                .addFilterBefore(new JWTFilter(), UsernamePasswordAuthenticationFilter.class);

        // close cache
        httpSecurity.headers().cacheControl();
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-order-other-service/src/main/java/other/config/SecurityConfig.java:SecurityConfig.<init>
package assurance.config;

import edu.fudan.common.security.jwt.JWTFilter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.method.configuration.EnableGlobalMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configuration.WebSecurityConfigurerAdapter;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurerAdapter;

import static org.springframework.web.cors.CorsConfiguration.ALL;

/**
 * @author fdse
 */
@Configuration
@EnableWebSecurity
@EnableGlobalMethodSecurity(prePostEnabled = true)
public class SecurityConfig extends WebSecurityConfigurerAdapter {

    /**
     * load password encoder
     *
     * @return PasswordEncoder
     */
    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    /**
     * allow cors domain
     * header  By default, only six fields can be taken from the header, and the other fields can only be specified in the header.
     * credentials   Cookies are not sent by default and can only be true if a Cookie is needed
     * Validity of this request
     *
     * @return WebMvcConfigurer
     */
    @Bean
    public WebMvcConfigurer corsConfigurer() {
        return new WebMvcConfigurerAdapter() {
            @Override
            public void addCorsMappings(CorsRegistry registry) {
                registry.addMapping("/**")
                        .allowedOrigins(ALL)
                        .allowedMethods(ALL)
                        .allowedHeaders(ALL)
                        .allowCredentials(false)
                        .maxAge(3600);
            }
        };
    }


    @Override
    protected void configure(HttpSecurity httpSecurity) throws Exception {
        httpSecurity.httpBasic().disable()
                // close default csrf
                .csrf().disable()
                // close session
                .sessionManagement().sessionCreationPolicy(SessionCreationPolicy.STATELESS)
                .and()
                .authorizeRequests()
                .antMatchers("/api/v1/assuranceservice/**").hasRole("USER")
                .antMatchers("/swagger-ui.html", "/webjars/**", "/images/**",
                        "/configuration/**", "/swagger-resources/**", "/v2/**").permitAll()
                .anyRequest().authenticated()
                .and()
                .addFilterBefore(new JWTFilter(), UsernamePasswordAuthenticationFilter.class);

        // close cache
        httpSecurity.headers().cacheControl();
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-assurance-service/src/main/java/assurance/config/SecurityConfig.java:SecurityConfig.<init>
package adminorder.config;

import edu.fudan.common.security.jwt.JWTFilter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.method.configuration.EnableGlobalMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configuration.WebSecurityConfigurerAdapter;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurerAdapter;

import static org.springframework.web.cors.CorsConfiguration.ALL;

/**
 * @author fdse
 */
@Configuration
@EnableWebSecurity
@EnableGlobalMethodSecurity(prePostEnabled = true)
public class SecurityConfig extends WebSecurityConfigurerAdapter {

    /**
     * load password encoder
     *
     * @return PasswordEncoder
     */
    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    /**
     * allow cors domain
     * header  By default, only six fields can be taken from the header, and the other fields can only be specified in the header.
     * credentials   Cookies are not sent by default and can only be true if a Cookie is needed
     * Validity of this request
     *
     * @return WebMvcConfigurer
     */
    @Bean
    public WebMvcConfigurer corsConfigurer() {
        return new WebMvcConfigurerAdapter() {
            @Override
            public void addCorsMappings(CorsRegistry registry) {
                registry.addMapping("/**")
                        .allowedOrigins(ALL)
                        .allowedMethods(ALL)
                        .allowedHeaders(ALL)
                        .allowCredentials(false)
                        .maxAge(3600);
            }
        };
    }


    @Override
    protected void configure(HttpSecurity httpSecurity) throws Exception {
        httpSecurity.httpBasic().disable()
                // close default csrf
                .csrf().disable()
                // close session
                .sessionManagement().sessionCreationPolicy(SessionCreationPolicy.STATELESS)
                .and()
                .authorizeRequests()
                .antMatchers("/api/v1/adminorderservice/**").hasRole("ADMIN")
                .antMatchers("/swagger-ui.html", "/webjars/**", "/images/**",
                        "/configuration/**", "/swagger-resources/**", "/v2/**").permitAll()
                .anyRequest().authenticated()
                .and()
                .addFilterBefore(new JWTFilter(), UsernamePasswordAuthenticationFilter.class);

        // close cache
        httpSecurity.headers().cacheControl();
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-admin-order-service/src/main/java/adminorder/config/SecurityConfig.java:SecurityConfig.<init>
package travel2.config;

import edu.fudan.common.security.jwt.JWTFilter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpMethod;
import org.springframework.security.config.annotation.method.configuration.EnableGlobalMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configuration.WebSecurityConfigurerAdapter;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurerAdapter;

import static org.springframework.web.cors.CorsConfiguration.ALL;

/**
 * @author fdse
 */
@Configuration
@EnableWebSecurity
@EnableGlobalMethodSecurity(prePostEnabled = true)
public class SecurityConfig extends WebSecurityConfigurerAdapter {

    String admin = "ADMIN";
    String trips = "/api/v1/travel2service/trips";

    /**
     * load password encoder
     *
     * @return PasswordEncoder
     */
    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    /**
     * allow cors domain
     * header  By default, only six fields can be taken from the header, and the other fields can only be specified in the header.
     * credentials   Cookies are not sent by default and can only be true if a Cookie is needed
     * Validity of this request
     *
     * @return WebMvcConfigurer
     */
    @Bean
    public WebMvcConfigurer corsConfigurer() {
        return new WebMvcConfigurerAdapter() {
            @Override
            public void addCorsMappings(CorsRegistry registry) {
                registry.addMapping("/**")
                        .allowedOrigins(ALL)
                        .allowedMethods(ALL)
                        .allowedHeaders(ALL)
                        .allowCredentials(false)
                        .maxAge(3600);
            }
        };
    }


    @Override
    protected void configure(HttpSecurity httpSecurity) throws Exception {
        httpSecurity.httpBasic().disable()
                // close default csrf
                .csrf().disable()
                // close session
                .sessionManagement().sessionCreationPolicy(SessionCreationPolicy.STATELESS)
                .and()
                .authorizeRequests()
                .antMatchers("/api/v1/travel2service/**").permitAll()
                .antMatchers(HttpMethod.PUT, trips).hasAnyRole(admin)
                .antMatchers(HttpMethod.POST, trips).hasAnyRole(admin)
                .antMatchers(HttpMethod.DELETE, trips).hasAnyRole(admin)
                .antMatchers("/swagger-ui.html", "/webjars/**", "/images/**",
                        "/configuration/**", "/swagger-resources/**", "/v2/**").permitAll()
                .anyRequest().authenticated()
                .and()
                .addFilterBefore(new JWTFilter(), UsernamePasswordAuthenticationFilter.class);

        // close cache
        httpSecurity.headers().cacheControl();
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-travel2-service/src/main/java/travel2/config/SecurityConfig.java:SecurityConfig.<init>
package order.config;

import edu.fudan.common.security.jwt.JWTFilter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpMethod;
import org.springframework.security.config.annotation.method.configuration.EnableGlobalMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configuration.WebSecurityConfigurerAdapter;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurerAdapter;

import static org.springframework.web.cors.CorsConfiguration.ALL;

/**
 * @author fdse
 */
@Configuration
@EnableWebSecurity
@EnableGlobalMethodSecurity(prePostEnabled = true)
public class SecurityConfig extends WebSecurityConfigurerAdapter {

    String admin = "ADMIN";
    String order = "/api/v1/orderservice/order";

    /**
     * load password encoder
     *
     * @return PasswordEncoder
     */
    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    /**
     * allow cors domain
     * header  By default, only six fields can be taken from the header, and the other fields can only be specified in the header.
     * credentials   Cookies are not sent by default and can only be true if a Cookie is needed
     * Validity of this request
     *
     * @return WebMvcConfigurer
     */
    @Bean
    public WebMvcConfigurer corsConfigurer() {
        return new WebMvcConfigurerAdapter() {
            @Override
            public void addCorsMappings(CorsRegistry registry) {
                registry.addMapping("/**")
                        .allowedOrigins(ALL)
                        .allowedMethods(ALL)
                        .allowedHeaders(ALL)
                        .allowCredentials(false)
                        .maxAge(3600);
            }
        };
    }


    @Override
    protected void configure(HttpSecurity httpSecurity) throws Exception {
        httpSecurity.httpBasic().disable()
                // close default csrf
                .csrf().disable()
                // close session
                .sessionManagement().sessionCreationPolicy(SessionCreationPolicy.STATELESS)
                .and()
                .authorizeRequests()
                .antMatchers(HttpMethod.POST, order).hasAnyRole(admin, "USER")
                .antMatchers(HttpMethod.PUT, order).hasAnyRole(admin, "USER")
                .antMatchers(HttpMethod.DELETE, order).hasAnyRole(admin, "USER")
                .antMatchers(HttpMethod.POST, "/api/v1/orderservice/order/admin").hasAnyRole(admin)
                .antMatchers(HttpMethod.PUT, "/api/v1/orderservice/order/admin").hasAnyRole(admin)
                .antMatchers("/api/v1/orderservice/order/**").permitAll()
                .antMatchers("/swagger-ui.html", "/webjars/**", "/images/**",
                        "/configuration/**", "/swagger-resources/**", "/v2/**").permitAll()
                .anyRequest().authenticated()
                .and()
                .addFilterBefore(new JWTFilter(), UsernamePasswordAuthenticationFilter.class);

        // close cache
        httpSecurity.headers().cacheControl();
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-order-service/src/main/java/order/config/SecurityConfig.java:SecurityConfig.<init>
package travel.config;

import edu.fudan.common.security.jwt.JWTFilter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpMethod;
import org.springframework.security.config.annotation.method.configuration.EnableGlobalMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configuration.WebSecurityConfigurerAdapter;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurerAdapter;

import static org.springframework.web.cors.CorsConfiguration.ALL;

/**
 * @author fdse
 */
@Configuration
@EnableWebSecurity
@EnableGlobalMethodSecurity(prePostEnabled = true)
public class SecurityConfig extends WebSecurityConfigurerAdapter {

    /**
     * load password encoder
     *
     * @return PasswordEncoder
     */
    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    /**
     * allow cors domain
     * header  By default, only six fields can be taken from the header, and the other fields can only be specified in the header.
     * credentials   Cookies are not sent by default and can only be true if a Cookie is needed
     * Validity of this request
     *
     * @return WebMvcConfigurer
     */
    @Bean
    public WebMvcConfigurer corsConfigurer() {
        return new WebMvcConfigurerAdapter() {
            @Override
            public void addCorsMappings(CorsRegistry registry) {
                registry.addMapping("/**")
                        .allowedOrigins(ALL)
                        .allowedMethods(ALL)
                        .allowedHeaders(ALL)
                        .allowCredentials(false)
                        .maxAge(3600);
            }
        };
    }


    @Override
    protected void configure(HttpSecurity httpSecurity) throws Exception {
        httpSecurity.httpBasic().disable()
                // close default csrf
                .csrf().disable()
                // close session
                .sessionManagement().sessionCreationPolicy(SessionCreationPolicy.STATELESS)
                .and()
                .authorizeRequests()

                .antMatchers(HttpMethod.PUT, "/api/v1/travelservice/trips").hasAnyRole("ADMIN")
                .antMatchers(HttpMethod.DELETE, "/api/v1/travelservice/trips/*").hasAnyRole("ADMIN")
                .antMatchers("/api/v1/travelservice/**").permitAll()
                .antMatchers("/swagger-ui.html", "/webjars/**", "/images/**",
                        "/configuration/**", "/swagger-resources/**", "/v2/**").permitAll()
                .anyRequest().authenticated()
                .and()
                .addFilterBefore(new JWTFilter(), UsernamePasswordAuthenticationFilter.class);

        // close cache
        httpSecurity.headers().cacheControl();
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-travel-service/src/main/java/travel/config/SecurityConfig.java:SecurityConfig.<init>
package preserve.config;

import edu.fudan.common.security.jwt.JWTFilter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.method.configuration.EnableGlobalMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configuration.WebSecurityConfigurerAdapter;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurerAdapter;

import static org.springframework.web.cors.CorsConfiguration.ALL;

/**
 * @author fdse
 */
@Configuration
@EnableWebSecurity
@EnableGlobalMethodSecurity(prePostEnabled = true)
public class SecurityConfig extends WebSecurityConfigurerAdapter {

    /**
     * load password encoder
     *
     * @return PasswordEncoder
     */
    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    /**
     * allow cors domain
     * header  By default, only six fields can be taken from the header, and the other fields can only be specified in the header.
     * credentials   Cookies are not sent by default and can only be true if a Cookie is needed
     * Validity of this request
     *
     * @return WebMvcConfigurer
     */
    @Bean
    public WebMvcConfigurer corsConfigurer() {
        return new WebMvcConfigurerAdapter() {
            @Override
            public void addCorsMappings(CorsRegistry registry) {
                registry.addMapping("/**")
                        .allowedOrigins(ALL)
                        .allowedMethods(ALL)
                        .allowedHeaders(ALL)
                        .allowCredentials(false)
                        .maxAge(3600);
            }
        };
    }


    @Override
    protected void configure(HttpSecurity httpSecurity) throws Exception {
        httpSecurity.httpBasic().disable()
                // close default csrf
                .csrf().disable()
                // close session
                .sessionManagement().sessionCreationPolicy(SessionCreationPolicy.STATELESS)
                .and()
                .authorizeRequests()
                .antMatchers("/api/v1/preserveservice/**").hasAnyRole("ADMIN", "USER")
                .antMatchers("/swagger-ui.html", "/webjars/**", "/images/**",
                        "/configuration/**", "/swagger-resources/**", "/v2/**").permitAll()
                .anyRequest().authenticated()
                .and()
                .addFilterBefore(new JWTFilter(), UsernamePasswordAuthenticationFilter.class);

        // close cache
        httpSecurity.headers().cacheControl();
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-preserve-service/src/main/java/preserve/config/SecurityConfig.java:SecurityConfig.<init>
package train.config;

import edu.fudan.common.security.jwt.JWTFilter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpMethod;
import org.springframework.security.config.annotation.method.configuration.EnableGlobalMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configuration.WebSecurityConfigurerAdapter;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurerAdapter;

import static org.springframework.web.cors.CorsConfiguration.ALL;

@Configuration
@EnableWebSecurity
@EnableGlobalMethodSecurity(prePostEnabled = true)
public class SecurityConfig extends WebSecurityConfigurerAdapter {

    String admin = "ADMIN";

    /**
     * load password encoder
     *
     * @return PasswordEncoder
     */
    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    /**
     * allow cors domain
     * header  By default, only six fields can be taken from the header, and the other fields can only be specified in the header.
     * credentials   Cookies are not sent by default and can only be true if a Cookie is needed
     * Validity of this request
     *
     * @return WebMvcConfigurer
     */
    @Bean
    public WebMvcConfigurer corsConfigurer() {
        return new WebMvcConfigurerAdapter() {
            @Override
            public void addCorsMappings(CorsRegistry registry) {
                registry.addMapping("/**")
                        .allowedOrigins(ALL)
                        .allowedMethods(ALL)
                        .allowedHeaders(ALL)
                        .allowCredentials(false)
                        .maxAge(3600);
            }
        };
    }


    @Override
    protected void configure(HttpSecurity httpSecurity) throws Exception {
        httpSecurity.httpBasic().disable()
                // close default csrf
                .csrf().disable()
                // close session
                .sessionManagement().sessionCreationPolicy(SessionCreationPolicy.STATELESS)
                .and()
                .authorizeRequests()
                .antMatchers("/api/v1/trainservice/**").permitAll()
                .antMatchers(HttpMethod.POST, "/api/v1/trainservice/trains").hasAnyRole(admin)
                .antMatchers(HttpMethod.PUT, "/api/v1/trainservice/trains").hasAnyRole(admin)
                .antMatchers(HttpMethod.DELETE, "/api/v1/trainservice/trains/*").hasAnyRole(admin)
                .antMatchers("/swagger-ui.html", "/webjars/**", "/images/**",
                        "/configuration/**", "/swagger-resources/**", "/v2/**").permitAll()
                .anyRequest().authenticated()
                .and()
                .addFilterBefore(new JWTFilter(), UsernamePasswordAuthenticationFilter.class);

        // close cache
        httpSecurity.headers().cacheControl();
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-train-service/src/main/java/train/config/SecurityConfig.java:SecurityConfig.<init>
package consignprice.config;

import edu.fudan.common.security.jwt.JWTFilter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.method.configuration.EnableGlobalMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configuration.WebSecurityConfigurerAdapter;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurerAdapter;

import static org.springframework.web.cors.CorsConfiguration.ALL;

/**
 * @author fdse
 */
@Configuration
@EnableWebSecurity
@EnableGlobalMethodSecurity(prePostEnabled = true)
public class SecurityConfig extends WebSecurityConfigurerAdapter {

    /**
     * load password encoder
     *
     * @return PasswordEncoder
     */
    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    /**
     * allow cors domain
     * header  By default, only six fields can be taken from the header, and the other fields can only be specified in the header.
     * credentials   Cookies are not sent by default and can only be true if a Cookie is needed
     * Validity of this request
     *
     * @return WebMvcConfigurer
     */
    @Bean
    public WebMvcConfigurer corsConfigurer() {
        return new WebMvcConfigurerAdapter() {
            @Override
            public void addCorsMappings(CorsRegistry registry) {
                registry.addMapping("/**")
                        .allowedOrigins(ALL)
                        .allowedMethods(ALL)
                        .allowedHeaders(ALL)
                        .allowCredentials(false)
                        .maxAge(3600);
            }
        };
    }


    @Override
    protected void configure(HttpSecurity httpSecurity) throws Exception {
        httpSecurity.httpBasic().disable()
                // close default csrf
                .csrf().disable()
                // close session
                .sessionManagement().sessionCreationPolicy(SessionCreationPolicy.STATELESS)
                .and()
                .authorizeRequests()
                .antMatchers("/api/v1/consignpriceservice/**").hasAnyRole("ADMIN", "USER")
                .antMatchers("/swagger-ui.html", "/webjars/**", "/images/**",
                        "/configuration/**", "/swagger-resources/**", "/v2/**").permitAll()
                .anyRequest().authenticated()
                .and()
                .addFilterBefore(new JWTFilter(), UsernamePasswordAuthenticationFilter.class);

        // close cache
        httpSecurity.headers().cacheControl();
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-consign-price-service/src/main/java/consignprice/config/SecurityConfig.java:SecurityConfig.<init>
package inside_payment.config;

import edu.fudan.common.security.jwt.JWTFilter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.method.configuration.EnableGlobalMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configuration.WebSecurityConfigurerAdapter;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurerAdapter;

import static org.springframework.web.cors.CorsConfiguration.ALL;

/**
 * @author fdse
 */
@Configuration
@EnableWebSecurity
@EnableGlobalMethodSecurity(prePostEnabled = true)
public class SecurityConfig extends WebSecurityConfigurerAdapter {

    /**
     * load password encoder
     *
     * @return PasswordEncoder
     */
    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    /**
     * allow cors domain
     * header  By default, only six fields can be taken from the header, and the other fields can only be specified in the header.
     * credentials   Cookies are not sent by default and can only be true if a Cookie is needed
     * Validity of this request
     *
     * @return WebMvcConfigurer
     */
    @Bean
    public WebMvcConfigurer corsConfigurer() {
        return new WebMvcConfigurerAdapter() {
            @Override
            public void addCorsMappings(CorsRegistry registry) {
                registry.addMapping("/**")
                        .allowedOrigins(ALL)
                        .allowedMethods(ALL)
                        .allowedHeaders(ALL)
                        .allowCredentials(false)
                        .maxAge(3600);
            }
        };
    }


    @Override
    protected void configure(HttpSecurity httpSecurity) throws Exception {
        httpSecurity.httpBasic().disable()
                // close default csrf
                .csrf().disable()
                // close session
                .sessionManagement().sessionCreationPolicy(SessionCreationPolicy.STATELESS)
                .and()
                .authorizeRequests()
                .antMatchers("/api/v1/inside_pay_service/**").hasAnyRole("ADMIN", "USER")
                .antMatchers("/swagger-ui.html", "/webjars/**", "/images/**",
                        "/configuration/**", "/swagger-resources/**", "/v2/**").permitAll()
                .anyRequest().authenticated()
                .and()
                .addFilterBefore(new JWTFilter(), UsernamePasswordAuthenticationFilter.class);

        // close cache
        httpSecurity.headers().cacheControl();
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-inside-payment-service/src/main/java/inside_payment/config/SecurityConfig.java:SecurityConfig.<init>
package foodsearch.config;

import edu.fudan.common.security.jwt.JWTFilter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpMethod;
import org.springframework.security.config.annotation.method.configuration.EnableGlobalMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configuration.WebSecurityConfigurerAdapter;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurerAdapter;

import static org.springframework.web.cors.CorsConfiguration.ALL;

@Configuration
@EnableWebSecurity
@EnableGlobalMethodSecurity(prePostEnabled = true)
public class SecurityConfig extends WebSecurityConfigurerAdapter {

    String admin = "ADMIN";

    /**
     * load password encoder
     *
     * @return PasswordEncoder
     */
    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    /**
     * allow cors domain
     * header  By default, only six fields can be taken from the header, and the other fields can only be specified in the header.
     * credentials   Cookies are not sent by default and can only be true if a Cookie is needed
     * Validity of this request
     *
     * @return WebMvcConfigurer
     */
    @Bean
    public WebMvcConfigurer corsConfigurer() {
        return new WebMvcConfigurerAdapter() {
            @Override
            public void addCorsMappings(CorsRegistry registry) {
                registry.addMapping("/**")
                        .allowedOrigins(ALL)
                        .allowedMethods(ALL)
                        .allowedHeaders(ALL)
                        .allowCredentials(false)
                        .maxAge(3600);
            }
        };
    }


    @Override
    protected void configure(HttpSecurity httpSecurity) throws Exception {
        httpSecurity.httpBasic().disable()
                // close default csrf
                .csrf().disable()
                // close session
                .sessionManagement().sessionCreationPolicy(SessionCreationPolicy.STATELESS)
                .and()
                .authorizeRequests()
                .antMatchers("/api/v1/foodservice/**").permitAll()
                .antMatchers(HttpMethod.DELETE, "/api/v1/foodservice/orders/*").hasAnyRole(admin)
                .antMatchers(HttpMethod.PUT, "/api/v1/foodservice/orders").hasAnyRole(admin)
                .antMatchers(HttpMethod.POST, "/api/v1/foodservice/orders").hasAnyRole(admin)
                .antMatchers("/swagger-ui.html", "/webjars/**", "/images/**",
                        "/configuration/**", "/swagger-resources/**", "/v2/**").permitAll()
                .anyRequest().authenticated()
                .and()
                .addFilterBefore(new JWTFilter(), UsernamePasswordAuthenticationFilter.class);

        // close cache
        httpSecurity.headers().cacheControl();
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-food-service/src/main/java/foodsearch/config/SecurityConfig.java:SecurityConfig.<init>
package route.config;

import edu.fudan.common.security.jwt.JWTFilter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpMethod;
import org.springframework.security.config.annotation.method.configuration.EnableGlobalMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configuration.WebSecurityConfigurerAdapter;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurerAdapter;

import static org.springframework.web.cors.CorsConfiguration.ALL;

/**
 * @author fdse
 */
@Configuration
@EnableWebSecurity
@EnableGlobalMethodSecurity(prePostEnabled = true)
public class SecurityConfig extends WebSecurityConfigurerAdapter {

    /**
     * load password encoder
     *
     * @return PasswordEncoder
     */
    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    /**
     * allow cors domain
     * header  By default, only six fields can be taken from the header, and the other fields can only be specified in the header.
     * credentials   Cookies are not sent by default and can only be true if a Cookie is needed
     * Validity of this request
     *
     * @return WebMvcConfigurer
     */
    @Bean
    public WebMvcConfigurer corsConfigurer() {
        return new WebMvcConfigurerAdapter() {
            @Override
            public void addCorsMappings(CorsRegistry registry) {
                registry.addMapping("/**")
                        .allowedOrigins(ALL)
                        .allowedMethods(ALL)
                        .allowedHeaders(ALL)
                        .allowCredentials(false)
                        .maxAge(3600);
            }
        };
    }


    @Override
    protected void configure(HttpSecurity httpSecurity) throws Exception {
        httpSecurity.httpBasic().disable()
                // close default csrf
                .csrf().disable()
                // close session
                .sessionManagement().sessionCreationPolicy(SessionCreationPolicy.STATELESS)
                .and()
                .authorizeRequests()
                .antMatchers("/api/v1/routeservice/**").permitAll()
                .antMatchers(HttpMethod.POST, "/api/v1/routeservice/routes").hasAnyRole("ADMIN")
                .antMatchers(HttpMethod.DELETE, "/api/v1/routeservice/routes/*").hasAnyRole("ADMIN")
                .antMatchers("/swagger-ui.html", "/webjars/**", "/images/**",
                        "/configuration/**", "/swagger-resources/**", "/v2/**").permitAll()
                .anyRequest().authenticated()
                .and()
                .addFilterBefore(new JWTFilter(), UsernamePasswordAuthenticationFilter.class);

        // close cache
        httpSecurity.headers().cacheControl();
    }
}

// Node: repos/cloned_ms_repos/train-ticket/ts-route-service/src/main/java/route/config/SecurityConfig.java:SecurityConfig.<init>
package consign.config;

import edu.fudan.common.security.jwt.JWTFilter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.method.configuration.EnableGlobalMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configuration.WebSecurityConfigurerAdapter;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurerAdapter;

import static org.springframework.web.cors.CorsConfiguration.ALL;

/**
 * @author fdse
 */
@Configuration
@EnableWebSecurity
@EnableGlobalMethodSecurity(prePostEnabled = true)
public class SecurityConfig extends WebSecurityConfigurerAdapter {

    /**
     * load password encoder
     *
     * @return PasswordEncoder
     */
    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    /**
     * allow cors domain
     * header  By default, only six fields can be taken from the header, and the other fields can only be specified in the header.
     * credentials   Cookies are not sent by default and can only be true if a Cookie is needed
     * Validity of this request
     *
     * @return WebMvcConfigurer
     */
    @Bean
    public WebMvcConfigurer corsConfigurer() {
        return new WebMvcConfigurerAdapter() {
            @Override
            public void addCorsMappings(CorsRegistry registry) {
                registry.addMapping("/**")
                        .allowedOrigins(ALL)
                        .allowedMethods(ALL)
                        .allowedHeaders(ALL)
                        .allowCredentials(false)
                        .maxAge(3600);
            }
        };
    }


    @Override
    protected void configure(HttpSecurity httpSecurity) throws Exception {
        httpSecurity.httpBasic().disable()
                // close default csrf
                .csrf().disable()
                // close session
                .sessionManagement().sessionCreationPolicy(SessionCreationPolicy.STATELESS)
                .and()
                .authorizeRequests()
                .antMatchers("/api/v1/consignservice/**").hasAnyRole("ADMIN", "USER")
                .antMatchers("/swagger-ui.html", "/webjars/**", "/images/**",
                        "/configuration/**", "/swagger-resources/**", "/v2/**").permitAll()
                .anyRequest().authenticated()
                .and()
                .addFilterBefore(new JWTFilter(), UsernamePasswordAuthenticationFilter.class);

        // close cache
        httpSecurity.headers().cacheControl();
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-consign-service/src/main/java/consign/config/SecurityConfig.java:SecurityConfig.<init>
package verifycode.config;

import edu.fudan.common.security.jwt.JWTFilter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.method.configuration.EnableGlobalMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configuration.WebSecurityConfigurerAdapter;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurerAdapter;

import static org.springframework.web.cors.CorsConfiguration.ALL;

/**
 * @author LeBW
 */
@Configuration
@EnableWebSecurity
@EnableGlobalMethodSecurity(prePostEnabled = true)
public class SecurityConfig extends WebSecurityConfigurerAdapter {

    /**
     * load password encoder
     *
     * @return PasswordEncoder
     */
    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    /**
     * allow cors domain
     * header  By default, only six fields can be taken from the header, and the other fields can only be specified in the header.
     * credentials   Cookies are not sent by default and can only be true if a Cookie is needed
     * Validity of this request
     *
     * @return WebMvcConfigurer
     */
    @Bean
    public WebMvcConfigurer corsConfigurer() {
        return new WebMvcConfigurerAdapter() {
            @Override
            public void addCorsMappings(CorsRegistry registry) {
                registry.addMapping("/**")
                        .allowedOrigins(ALL)
                        .allowedMethods(ALL)
                        .allowedHeaders(ALL)
                        .allowCredentials(false)
                        .maxAge(3600);
            }
        };
    }


    @Override
    protected void configure(HttpSecurity httpSecurity) throws Exception {
        httpSecurity.httpBasic().disable()
                // close default csrf
                .csrf().disable()
                // close session
                .sessionManagement().sessionCreationPolicy(SessionCreationPolicy.STATELESS)
                .and()
                .authorizeRequests()
                .antMatchers("/api/v1/verifycode/**").permitAll()
                .anyRequest().authenticated()
                .and()
                .addFilterBefore(new JWTFilter(), UsernamePasswordAuthenticationFilter.class);

        // close cache
        httpSecurity.headers().cacheControl();
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-verification-code-service/src/main/java/verifycode/config/SecurityConfig.java:SecurityConfig.<init>
package rebook.config;

import edu.fudan.common.security.jwt.JWTFilter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.method.configuration.EnableGlobalMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configuration.WebSecurityConfigurerAdapter;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurerAdapter;

import static org.springframework.web.cors.CorsConfiguration.ALL;

/**
 * @author fdse
 */
@Configuration
@EnableWebSecurity
@EnableGlobalMethodSecurity(prePostEnabled = true)
public class SecurityConfig extends WebSecurityConfigurerAdapter {

    /**
     * load password encoder
     *
     * @return PasswordEncoder
     */
    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    /**
     * allow cors domain
     * header  By default, only six fields can be taken from the header, and the other fields can only be specified in the header.
     * credentials   Cookies are not sent by default and can only be true if a Cookie is needed
     * Validity of this request
     *
     * @return WebMvcConfigurer
     */
    @Bean
    public WebMvcConfigurer corsConfigurer() {
        return new WebMvcConfigurerAdapter() {
            @Override
            public void addCorsMappings(CorsRegistry registry) {
                registry.addMapping("/**")
                        .allowedOrigins(ALL)
                        .allowedMethods(ALL)
                        .allowedHeaders(ALL)
                        .allowCredentials(false)
                        .maxAge(3600);
            }
        };
    }


    @Override
    protected void configure(HttpSecurity httpSecurity) throws Exception {
        httpSecurity.httpBasic().disable()
                // close default csrf
                .csrf().disable()
                // close session
                .sessionManagement().sessionCreationPolicy(SessionCreationPolicy.STATELESS)
                .and()
                .authorizeRequests()
                .antMatchers("/api/v1/rebookservice/**").hasAnyRole("ADMIN", "USER")
                .antMatchers("/swagger-ui.html", "/webjars/**", "/images/**",
                        "/configuration/**", "/swagger-resources/**", "/v2/**").permitAll()
                .anyRequest().authenticated()
                .and()
                .addFilterBefore(new JWTFilter(), UsernamePasswordAuthenticationFilter.class);

        // close cache
        httpSecurity.headers().cacheControl();
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-rebook-service/src/main/java/rebook/config/SecurityConfig.java:SecurityConfig.<init>
package cancel.config;

import edu.fudan.common.security.jwt.JWTFilter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.method.configuration.EnableGlobalMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configuration.WebSecurityConfigurerAdapter;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurerAdapter;

import static org.springframework.web.cors.CorsConfiguration.ALL;

/**
 * @author fdse
 */
@Configuration
@EnableWebSecurity
@EnableGlobalMethodSecurity(prePostEnabled = true)
public class SecurityConfig extends WebSecurityConfigurerAdapter {

    /**
     * load password encoder
     *
     * @return PasswordEncoder
     */
    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    /**
     * allow cors domain
     * header  By default, only six fields can be taken from the header, and the other fields can only be specified in the header.
     * credentials   Cookies are not sent by default and can only be true if a Cookie is needed
     * Validity of this request
     *
     * @return WebMvcConfigurer
     */
    @Bean
    public WebMvcConfigurer corsConfigurer() {
        return new WebMvcConfigurerAdapter() {
            @Override
            public void addCorsMappings(CorsRegistry registry) {
                registry.addMapping("/**")
                        .allowedOrigins(ALL)
                        .allowedMethods(ALL)
                        .allowedHeaders(ALL)
                        .allowCredentials(false)
                        .maxAge(3600);
            }
        };
    }


    @Override
    protected void configure(HttpSecurity httpSecurity) throws Exception {
        httpSecurity.httpBasic().disable()
                // close default csrf
                .csrf().disable()
                // close session
                .sessionManagement().sessionCreationPolicy(SessionCreationPolicy.STATELESS)
                .and()
                .authorizeRequests()
                .antMatchers("/api/v1/cancelservice/**").hasAnyRole("ADMIN", "USER")
                .antMatchers("/swagger-ui.html", "/webjars/**", "/images/**",
                        "/configuration/**", "/swagger-resources/**", "/v2/**").permitAll()
                .anyRequest().authenticated()
                .and()
                .addFilterBefore(new JWTFilter(), UsernamePasswordAuthenticationFilter.class);

        // close cache
        httpSecurity.headers().cacheControl();
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-cancel-service/src/main/java/cancel/config/SecurityConfig.java:SecurityConfig.<init>
package adminbasic.config;

import edu.fudan.common.security.jwt.JWTFilter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpMethod;
import org.springframework.security.config.annotation.method.configuration.EnableGlobalMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configuration.WebSecurityConfigurerAdapter;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurerAdapter;

import static org.springframework.web.cors.CorsConfiguration.ALL;

/**
 * @author fdse
 */
@Configuration
@EnableWebSecurity
@EnableGlobalMethodSecurity(prePostEnabled = true)
public class SecurityConfig extends WebSecurityConfigurerAdapter {

    /**
     * load password encoder
     *
     * @return PasswordEncoder
     */
    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    /**
     * allow cors domain
     * header  By default, only six fields can be taken from the header, and the other fields can only be specified in the header.
     * credentials   Cookies are not sent by default and can only be true if a Cookie is needed
     * Validity of this request
     *
     * @return WebMvcConfigurer
     */
    @Bean
    public WebMvcConfigurer corsConfigurer() {
        return new WebMvcConfigurerAdapter() {
            @Override
            public void addCorsMappings(CorsRegistry registry) {
                registry.addMapping("/**")
                        .allowedOrigins(ALL)
                        .allowedMethods(ALL)
                        .allowedHeaders(ALL)
                        .allowCredentials(false)
                        .maxAge(3600);
            }
        };
    }


    @Override
    protected void configure(HttpSecurity httpSecurity) throws Exception {
        httpSecurity.httpBasic().disable()
                // close default csrf
                .csrf().disable()
                // close session
                .sessionManagement().sessionCreationPolicy(SessionCreationPolicy.STATELESS)
                .and()
                .authorizeRequests()
                .antMatchers(HttpMethod.GET, "/api/v1/adminbasicservice/adminbasic/stations").permitAll()
                .antMatchers(HttpMethod.GET, "/api/v1/adminbasicservice/adminbasic/trains").permitAll()
                .antMatchers(HttpMethod.GET, "/api/v1/adminbasicservice/adminbasic/prices").permitAll()
                .antMatchers(HttpMethod.GET, "/api/v1/adminbasicservice/adminbasic/configs").permitAll()
                .antMatchers(HttpMethod.GET, "/api/v1/adminbasicservice/adminbasic/contacts").permitAll()
                .antMatchers("/api/v1/adminbasicservice/**").hasRole("ADMIN")
                .antMatchers("/swagger-ui.html", "/webjars/**", "/images/**",
                        "/configuration/**", "/swagger-resources/**", "/v2/**").permitAll()
                .anyRequest().authenticated()
                .and()
                .addFilterBefore(new JWTFilter(), UsernamePasswordAuthenticationFilter.class);


        // close cache
        httpSecurity.headers().cacheControl();
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-admin-basic-info-service/src/main/java/adminbasic/config/SecurityConfig.java:SecurityConfig.<init>
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


package trainFood.config;

import edu.fudan.common.security.jwt.JWTFilter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.method.configuration.EnableGlobalMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configuration.WebSecurityConfigurerAdapter;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurerAdapter;

import static org.springframework.web.cors.CorsConfiguration.ALL;

@Configuration
@EnableWebSecurity
@EnableGlobalMethodSecurity(prePostEnabled = true)
public class SecurityConfig extends WebSecurityConfigurerAdapter {

    // load password encoder
    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    /**
     *  allow cors domain
     * header 在默认的情况下只能从头部取出6个字段，想要其他字段只能自己在头里指定
     * credentials 默认不发送Cookie, 如果需要Cookie,这个值只能为true
     * 本次请求检查的有效期
     *
     * @return
     */
    @Bean
    public WebMvcConfigurer corsConfigurer() {
        return new WebMvcConfigurerAdapter() {
            @Override
            public void addCorsMappings(CorsRegistry registry) {
                registry.addMapping("/**")
                        .allowedOrigins(ALL)
                        .allowedMethods(ALL)
                        .allowedHeaders(ALL)
                        .allowCredentials(false)
                        .maxAge(3600);
            }
        };
    }


    @Override
    protected void configure(HttpSecurity httpSecurity) throws Exception {
        httpSecurity.httpBasic().disable()
                // close default csrf
                .csrf().disable()
                // close session
                .sessionManagement().sessionCreationPolicy(SessionCreationPolicy.STATELESS)
                .and()
                .authorizeRequests()
                .antMatchers("/api/v1/trainfoodservice/**").permitAll()
                .antMatchers("/swagger-ui.html", "/webjars/**", "/images/**",
                        "/configuration/**", "/swagger-resources/**", "/v2/**").permitAll()
                .anyRequest().authenticated()
                .and()
                .addFilterBefore(new JWTFilter(), UsernamePasswordAuthenticationFilter.class);

        // close cache
        httpSecurity.headers().cacheControl();
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-train-food-service/src/main/java/trainFood/config/SecurityConfig.java:SecurityConfig.<init>
package execute.config;

import edu.fudan.common.security.jwt.JWTFilter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.method.configuration.EnableGlobalMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configuration.WebSecurityConfigurerAdapter;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurerAdapter;

import static org.springframework.web.cors.CorsConfiguration.ALL;

/**
 * @author fdse
 */
@Configuration
@EnableWebSecurity
@EnableGlobalMethodSecurity(prePostEnabled = true)
public class SecurityConfig extends WebSecurityConfigurerAdapter {

    /**
     * load password encoder
     *
     * @return PasswordEncoder
     */
    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    /**
     * allow cors domain
     * header  By default, only six fields can be taken from the header, and the other fields can only be specified in the header.
     * credentials   Cookies are not sent by default and can only be true if a Cookie is needed
     * Validity of this request
     *
     * @return WebMvcConfigurer
     */
    @Bean
    public WebMvcConfigurer corsConfigurer() {
        return new WebMvcConfigurerAdapter() {
            @Override
            public void addCorsMappings(CorsRegistry registry) {
                registry.addMapping("/**")
                        .allowedOrigins(ALL)
                        .allowedMethods(ALL)
                        .allowedHeaders(ALL)
                        .allowCredentials(false)
                        .maxAge(3600);
            }
        };
    }


    @Override
    protected void configure(HttpSecurity httpSecurity) throws Exception {
        httpSecurity.httpBasic().disable()
                // close default csrf
                .csrf().disable()
                // close session
                .sessionManagement().sessionCreationPolicy(SessionCreationPolicy.STATELESS)
                .and()
                .authorizeRequests()
                .antMatchers("/api/v1/executeservice/**").hasAnyRole("ADMIN", "USER")
                .antMatchers("/swagger-ui.html", "/webjars/**", "/images/**",
                        "/configuration/**", "/swagger-resources/**", "/v2/**").permitAll()
                .anyRequest().authenticated()
                .and()
                .addFilterBefore(new JWTFilter(), UsernamePasswordAuthenticationFilter.class);

        // close cache
        httpSecurity.headers().cacheControl();
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-execute-service/src/main/java/execute/config/SecurityConfig.java:SecurityConfig.<init>
package fdse.microservice.config;

import edu.fudan.common.security.jwt.JWTFilter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpMethod;
import org.springframework.security.config.annotation.method.configuration.EnableGlobalMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configuration.WebSecurityConfigurerAdapter;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurerAdapter;

import static org.springframework.web.cors.CorsConfiguration.ALL;

@Configuration
@EnableWebSecurity
@EnableGlobalMethodSecurity(prePostEnabled = true)
public class SecurityConfig extends WebSecurityConfigurerAdapter {

    String admin = "ADMIN";
    String stations = "/api/v1/stationservice/stations";

    /**
     * load password encoder
     *
     * @return PasswordEncoder
     */
    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    /**
     * allow cors domain
     * header  By default, only six fields can be taken from the header, and the other fields can only be specified in the header.
     * credentials   Cookies are not sent by default and can only be true if a Cookie is needed
     * Validity of this request
     *
     * @return WebMvcConfigurer
     */
    @Bean
    public WebMvcConfigurer corsConfigurer() {
        return new WebMvcConfigurerAdapter() {
            @Override
            public void addCorsMappings(CorsRegistry registry) {
                registry.addMapping("/**")
                        .allowedOrigins(ALL)
                        .allowedMethods(ALL)
                        .allowedHeaders(ALL)
                        .allowCredentials(false)
                        .maxAge(3600);
            }
        };
    }


    @Override
    protected void configure(HttpSecurity httpSecurity) throws Exception {
        httpSecurity.httpBasic().disable()
                // close default csrf
                .csrf().disable()
                // close session
                .sessionManagement().sessionCreationPolicy(SessionCreationPolicy.STATELESS)
                .and()
                .authorizeRequests()
                .antMatchers(HttpMethod.POST, stations).hasAnyRole(admin)
                .antMatchers(HttpMethod.PUT, stations).hasAnyRole(admin)
                .antMatchers(HttpMethod.DELETE, stations).hasAnyRole(admin)
                .antMatchers("/api/v1/stationservice/**").permitAll()
                .antMatchers("/swagger-ui.html", "/webjars/**", "/images/**",
                        "/configuration/**", "/swagger-resources/**", "/v2/**").permitAll()
                .anyRequest().authenticated()
                .and()
                .addFilterBefore(new JWTFilter(), UsernamePasswordAuthenticationFilter.class);

        // close cache
        httpSecurity.headers().cacheControl();
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-station-service/src/main/java/fdse/microservice/config/SecurityConfig.java:SecurityConfig.<init>
package admintravel.config;

import edu.fudan.common.security.jwt.JWTFilter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.method.configuration.EnableGlobalMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configuration.WebSecurityConfigurerAdapter;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurerAdapter;

import static org.springframework.web.cors.CorsConfiguration.ALL;

/**
 * @author fdse
 */
@Configuration
@EnableWebSecurity
@EnableGlobalMethodSecurity(prePostEnabled = true)
public class SecurityConfig extends WebSecurityConfigurerAdapter {

    /**
     * load password encoder
     *
     * @return PasswordEncoder
     */
    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    /**
     * allow cors domain
     * header  By default, only six fields can be taken from the header, and the other fields can only be specified in the header.
     * credentials   Cookies are not sent by default and can only be true if a Cookie is needed
     * Validity of this request
     *
     * @return WebMvcConfigurer
     */
    @Bean
    public WebMvcConfigurer corsConfigurer() {
        return new WebMvcConfigurerAdapter() {
            @Override
            public void addCorsMappings(CorsRegistry registry) {
                registry.addMapping("/**")
                        .allowedOrigins(ALL)
                        .allowedMethods(ALL)
                        .allowedHeaders(ALL)
                        .allowCredentials(false)
                        .maxAge(3600);
            }
        };
    }


    @Override
    protected void configure(HttpSecurity httpSecurity) throws Exception {
        httpSecurity.httpBasic().disable()
                // close default csrf
                .csrf().disable()
                // close session
                .sessionManagement().sessionCreationPolicy(SessionCreationPolicy.STATELESS)
                .and()
                .authorizeRequests()
                .antMatchers("/api/v1/admintravelservice/**").hasRole("ADMIN")
                .antMatchers("/swagger-ui.html", "/webjars/**", "/images/**",
                        "/configuration/**", "/swagger-resources/**", "/v2/**").permitAll()
                .anyRequest().authenticated()
                .and()
                .addFilterBefore(new JWTFilter(), UsernamePasswordAuthenticationFilter.class);

        // close cache
        httpSecurity.headers().cacheControl();
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-admin-travel-service/src/main/java/admintravel/config/SecurityConfig.java:SecurityConfig.<init>
package travelplan.config;

import edu.fudan.common.security.jwt.JWTFilter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.method.configuration.EnableGlobalMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configuration.WebSecurityConfigurerAdapter;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurerAdapter;

import static org.springframework.web.cors.CorsConfiguration.ALL;

/**
 * @author fdse
 */
@Configuration
@EnableWebSecurity
@EnableGlobalMethodSecurity(prePostEnabled = true)
public class SecurityConfig extends WebSecurityConfigurerAdapter {

    /**
     * load password encoder
     *
     * @return PasswordEncoder
     */
    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    /**
     * allow cors domain
     * header  By default, only six fields can be taken from the header, and the other fields can only be specified in the header.
     * credentials   Cookies are not sent by default and can only be true if a Cookie is needed
     * Validity of this request
     *
     * @return WebMvcConfigurer
     */
    @Bean
    public WebMvcConfigurer corsConfigurer() {
        return new WebMvcConfigurerAdapter() {
            @Override
            public void addCorsMappings(CorsRegistry registry) {
                registry.addMapping("/**")
                        .allowedOrigins(ALL)
                        .allowedMethods(ALL)
                        .allowedHeaders(ALL)
                        .allowCredentials(false)
                        .maxAge(3600);
            }
        };
    }


    @Override
    protected void configure(HttpSecurity httpSecurity) throws Exception {
        httpSecurity.httpBasic().disable()
                // close default csrf
                .csrf().disable()
                // close session
                .sessionManagement().sessionCreationPolicy(SessionCreationPolicy.STATELESS)
                .and()
                .authorizeRequests()
                .antMatchers("/api/v1/travelplanservice/**").permitAll()
                .antMatchers("/swagger-ui.html", "/webjars/**", "/images/**",
                        "/configuration/**", "/swagger-resources/**", "/v2/**").permitAll()
                .anyRequest().authenticated()
                .and()
                .addFilterBefore(new JWTFilter(), UsernamePasswordAuthenticationFilter.class);

        // close cache
        httpSecurity.headers().cacheControl();
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-travel-plan-service/src/main/java/travelplan/config/SecurityConfig.java:SecurityConfig.<init>
package user.config;

import edu.fudan.common.security.jwt.JWTFilter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpMethod;
import org.springframework.security.config.annotation.method.configuration.EnableGlobalMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configuration.WebSecurityConfigurerAdapter;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurerAdapter;

import static org.springframework.web.cors.CorsConfiguration.ALL;

/**
 * @author fdse
 */
@Configuration
@EnableWebSecurity
@EnableGlobalMethodSecurity(prePostEnabled = true)
public class SecurityConfig extends WebSecurityConfigurerAdapter {

    /**
     * load password encoder
     *
     * @return PasswordEncoder
     */
    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    /**
     * allow cors domain
     * header  By default, only six fields can be taken from the header, and the other fields can only be specified in the header.
     * credentials   Cookies are not sent by default and can only be true if a Cookie is needed
     * Validity of this request
     *
     * @return WebMvcConfigurer
     */
    @Bean
    public WebMvcConfigurer corsConfigurer() {
        return new WebMvcConfigurerAdapter() {
            @Override
            public void addCorsMappings(CorsRegistry registry) {
                registry.addMapping("/**")
                        .allowedOrigins(ALL)
                        .allowedMethods(ALL)
                        .allowedHeaders(ALL)
                        .allowCredentials(false)
                        .maxAge(3600);
            }
        };
    }


    @Override
    protected void configure(HttpSecurity httpSecurity) throws Exception {
        httpSecurity.httpBasic().disable()
                // close default csrf
                .csrf().disable()
                // close session
                .sessionManagement().sessionCreationPolicy(SessionCreationPolicy.STATELESS)
                .and()
                .authorizeRequests()
                .antMatchers("/api/v1/userservice/users/**").permitAll()
                .antMatchers(HttpMethod.DELETE, "/api/v1/userservice/users/*").hasAnyRole("ADMIN", "USER")
                .antMatchers("/swagger-ui.html", "/webjars/**", "/images/**",
                        "/configuration/**", "/swagger-resources/**", "/v2/**").permitAll()
                .anyRequest().authenticated()
                .and()
                .addFilterBefore(new JWTFilter(), UsernamePasswordAuthenticationFilter.class);

        // close cache
        httpSecurity.headers().cacheControl();
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-user-service/src/main/java/user/config/SecurityConfig.java:SecurityConfig.<init>
package seat.config;

import edu.fudan.common.security.jwt.JWTFilter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpMethod;
import org.springframework.security.config.annotation.method.configuration.EnableGlobalMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configuration.WebSecurityConfigurerAdapter;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurerAdapter;

import static org.springframework.web.cors.CorsConfiguration.ALL;

/**
 * @author fdse
 */
@Configuration
@EnableWebSecurity
@EnableGlobalMethodSecurity(prePostEnabled = true)
public class SecurityConfig extends WebSecurityConfigurerAdapter {

    /**
     * load password encoder
     *
     * @return PasswordEncoder
     */
    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    /**
     * allow cors domain
     * header  By default, only six fields can be taken from the header, and the other fields can only be specified in the header.
     * credentials   Cookies are not sent by default and can only be true if a Cookie is needed
     * Validity of this request
     *
     * @return WebMvcConfigurer
     */
    @Bean
    public WebMvcConfigurer corsConfigurer() {
        return new WebMvcConfigurerAdapter() {
            @Override
            public void addCorsMappings(CorsRegistry registry) {
                registry.addMapping("/**")
                        .allowedOrigins(ALL)
                        .allowedMethods(ALL)
                        .allowedHeaders(ALL)
                        .allowCredentials(false)
                        .maxAge(3600);
            }
        };
    }


    @Override
    protected void configure(HttpSecurity httpSecurity) throws Exception {
        httpSecurity.httpBasic().disable()
                // close default csrf
                .csrf().disable()
                // close session
                .sessionManagement().sessionCreationPolicy(SessionCreationPolicy.STATELESS)
                .and()
                .authorizeRequests()
                .antMatchers("/api/v1/seatservice/**").permitAll()
                .antMatchers(HttpMethod.POST, "/api/v1/seatservice/seats").hasAnyRole("ADMIN")
                .antMatchers("/swagger-ui.html", "/webjars/**", "/images/**",
                        "/configuration/**", "/swagger-resources/**", "/v2/**").permitAll()
                .anyRequest().authenticated()
                .and()
                .addFilterBefore(new JWTFilter(), UsernamePasswordAuthenticationFilter.class);

        // close cache
        httpSecurity.headers().cacheControl();
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-seat-service/src/main/java/seat/config/SecurityConfig.java:SecurityConfig.<init>
package security.config;

import edu.fudan.common.security.jwt.JWTFilter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.method.configuration.EnableGlobalMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configuration.WebSecurityConfigurerAdapter;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurerAdapter;

import static org.springframework.web.cors.CorsConfiguration.ALL;

/**
 * @author fdse
 */
@Configuration
@EnableWebSecurity
@EnableGlobalMethodSecurity(prePostEnabled = true)
public class SecurityConfig extends WebSecurityConfigurerAdapter {

    /**
     * load password encoder
     *
     * @return PasswordEncoder
     */
    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    /**
     * allow cors domain
     * header  By default, only six fields can be taken from the header, and the other fields can only be specified in the header.
     * credentials   Cookies are not sent by default and can only be true if a Cookie is needed
     * Validity of this request
     *
     * @return WebMvcConfigurer
     */
    @Bean
    public WebMvcConfigurer corsConfigurer() {
        return new WebMvcConfigurerAdapter() {
            @Override
            public void addCorsMappings(CorsRegistry registry) {
                registry.addMapping("/**")
                        .allowedOrigins(ALL)
                        .allowedMethods(ALL)
                        .allowedHeaders(ALL)
                        .allowCredentials(false)
                        .maxAge(3600);
            }
        };
    }


    @Override
    protected void configure(HttpSecurity httpSecurity) throws Exception {
        httpSecurity.httpBasic().disable()
                // close default csrf
                .csrf().disable()
                // close session
                .sessionManagement().sessionCreationPolicy(SessionCreationPolicy.STATELESS)
                .and()
                .authorizeRequests()
                .antMatchers("/api/v1/securityservice/**").hasAnyRole("ADMIN", "USER")
                .antMatchers("/swagger-ui.html", "/webjars/**", "/images/**",
                        "/configuration/**", "/swagger-resources/**", "/v2/**").permitAll()
                .anyRequest().authenticated()
                .and()
                .addFilterBefore(new JWTFilter(), UsernamePasswordAuthenticationFilter.class);

        // close cache
        httpSecurity.headers().cacheControl();
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-security-service/src/main/java/security/config/SecurityConfig.java:SecurityConfig.<init>
package food_delivery.config;

import edu.fudan.common.security.jwt.JWTFilter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.method.configuration.EnableGlobalMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configuration.WebSecurityConfigurerAdapter;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurerAdapter;

import static org.springframework.web.cors.CorsConfiguration.ALL;

@Configuration
@EnableWebSecurity
@EnableGlobalMethodSecurity(prePostEnabled = true)
public class SecurityConfig extends WebSecurityConfigurerAdapter {

    // load password encoder
    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    /**
     *  allow cors domain
     * header 在默认的情况下只能从头部取出6个字段，想要其他字段只能自己在头里指定
     * credentials 默认不发送Cookie, 如果需要Cookie,这个值只能为true
     * 本次请求检查的有效期
     *
     * @return
     */
    @Bean
    public WebMvcConfigurer corsConfigurer() {
        return new WebMvcConfigurerAdapter() {
            @Override
            public void addCorsMappings(CorsRegistry registry) {
                registry.addMapping("/**")
                        .allowedOrigins(ALL)
                        .allowedMethods(ALL)
                        .allowedHeaders(ALL)
                        .allowCredentials(false)
                        .maxAge(3600);
            }
        };
    }


    @Override
    protected void configure(HttpSecurity httpSecurity) throws Exception {
        httpSecurity.httpBasic().disable()
                // close default csrf
                .csrf().disable()
                // close session
                .sessionManagement().sessionCreationPolicy(SessionCreationPolicy.STATELESS)
                .and()
                .authorizeRequests()
                .antMatchers("/api/v1/fooddeliveryservice/**").permitAll()
                .antMatchers("/swagger-ui.html", "/webjars/**", "/images/**",
                        "/configuration/**", "/swagger-resources/**", "/v2/**").permitAll()
                .anyRequest().authenticated()
                .and()
                .addFilterBefore(new JWTFilter(), UsernamePasswordAuthenticationFilter.class);

        // close cache
        httpSecurity.headers().cacheControl();
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-food-delivery-service/src/main/java/food_delivery/config/SecurityConfig.java:SecurityConfig.<init>
package contacts.config;

import edu.fudan.common.security.jwt.JWTFilter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.method.configuration.EnableGlobalMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configuration.WebSecurityConfigurerAdapter;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurerAdapter;

import static org.springframework.web.cors.CorsConfiguration.ALL;

/**
 * @author fdse
 */
@Configuration
@EnableWebSecurity
@EnableGlobalMethodSecurity(prePostEnabled = true)
public class SecurityConfig extends WebSecurityConfigurerAdapter {

    /**
     * load password encoder
     *
     * @return PasswordEncoder
     */
    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    /**
     * allow cors domain
     * header  By default, only six fields can be taken from the header, and the other fields can only be specified in the header.
     * credentials   Cookies are not sent by default and can only be true if a Cookie is needed
     * Validity of this request
     *
     * @return WebMvcConfigurer
     */
    @Bean
    public WebMvcConfigurer corsConfigurer() {
        return new WebMvcConfigurerAdapter() {
            @Override
            public void addCorsMappings(CorsRegistry registry) {
                registry.addMapping("/**")
                        .allowedOrigins(ALL)
                        .allowedMethods(ALL)
                        .allowedHeaders(ALL)
                        .allowCredentials(false)
                        .maxAge(3600);
            }
        };
    }


    @Override
    protected void configure(HttpSecurity httpSecurity) throws Exception {
        httpSecurity.httpBasic().disable()
                // close default csrf
                .csrf().disable()
                // close session
                .sessionManagement().sessionCreationPolicy(SessionCreationPolicy.STATELESS)
                .and()
                .authorizeRequests()
                .antMatchers("/api/v1/contactservice/**").hasAnyRole("ADMIN", "USER")
                .antMatchers("/swagger-ui.html", "/webjars/**", "/images/**",
                        "/configuration/**", "/swagger-resources/**", "/v2/**").permitAll()
                .anyRequest().authenticated()
                .and()
                .addFilterBefore(new JWTFilter(), UsernamePasswordAuthenticationFilter.class);

        // close cache
        httpSecurity.headers().cacheControl();
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-contacts-service/src/main/java/contacts/config/SecurityConfig.java:SecurityConfig.<init>
package preserveOther.config;

import edu.fudan.common.security.jwt.JWTFilter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.method.configuration.EnableGlobalMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configuration.WebSecurityConfigurerAdapter;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurerAdapter;

import static org.springframework.web.cors.CorsConfiguration.ALL;

/**
 * @author fdse
 */
@Configuration
@EnableWebSecurity
@EnableGlobalMethodSecurity(prePostEnabled = true)
public class SecurityConfig extends WebSecurityConfigurerAdapter {

    /**
     * load password encoder
     *
     * @return PasswordEncoder
     */
    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    /**
     * allow cors domain
     * header  By default, only six fields can be taken from the header, and the other fields can only be specified in the header.
     * credentials   Cookies are not sent by default and can only be true if a Cookie is needed
     * Validity of this request
     *
     * @return WebMvcConfigurer
     */
    @Bean
    public WebMvcConfigurer corsConfigurer() {
        return new WebMvcConfigurerAdapter() {
            @Override
            public void addCorsMappings(CorsRegistry registry) {
                registry.addMapping("/**")
                        .allowedOrigins(ALL)
                        .allowedMethods(ALL)
                        .allowedHeaders(ALL)
                        .allowCredentials(false)
                        .maxAge(3600);
            }
        };
    }


    @Override
    protected void configure(HttpSecurity httpSecurity) throws Exception {
        httpSecurity.httpBasic().disable()
                // close default csrf
                .csrf().disable()
                // close session
                .sessionManagement().sessionCreationPolicy(SessionCreationPolicy.STATELESS)
                .and()
                .authorizeRequests()
                .antMatchers("/api/v1/preserveotherservice/**").hasAnyRole("ADMIN", "USER")
                .antMatchers("/swagger-ui.html", "/webjars/**", "/images/**",
                        "/configuration/**", "/swagger-resources/**", "/v2/**").permitAll()
                .anyRequest().authenticated()
                .and()
                .addFilterBefore(new JWTFilter(), UsernamePasswordAuthenticationFilter.class);

        // close cache
        httpSecurity.headers().cacheControl();
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-preserve-other-service/src/main/java/preserveOther/config/SecurityConfig.java:SecurityConfig.<init>
package food.config;

import edu.fudan.common.security.jwt.JWTFilter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.method.configuration.EnableGlobalMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configuration.WebSecurityConfigurerAdapter;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurerAdapter;

import static org.springframework.web.cors.CorsConfiguration.ALL;

@Configuration
@EnableWebSecurity
@EnableGlobalMethodSecurity(prePostEnabled = true)
public class SecurityConfig extends WebSecurityConfigurerAdapter {

    // load password encoder
    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    /**
     *  allow cors domain
     * header 在默认的情况下只能从头部取出6个字段，想要其他字段只能自己在头里指定
     * credentials 默认不发送Cookie, 如果需要Cookie,这个值只能为true
     * 本次请求检查的有效期
     *
     * @return
     */
    @Bean
    public WebMvcConfigurer corsConfigurer() {
        return new WebMvcConfigurerAdapter() {
            @Override
            public void addCorsMappings(CorsRegistry registry) {
                registry.addMapping("/**")
                        .allowedOrigins(ALL)
                        .allowedMethods(ALL)
                        .allowedHeaders(ALL)
                        .allowCredentials(false)
                        .maxAge(3600);
            }
        };
    }


    @Override
    protected void configure(HttpSecurity httpSecurity) throws Exception {
        httpSecurity.httpBasic().disable()
                // close default csrf
                .csrf().disable()
                // close session
                .sessionManagement().sessionCreationPolicy(SessionCreationPolicy.STATELESS)
                .and()
                .authorizeRequests()
                .antMatchers("/api/v1/stationfoodservice/**").permitAll()
                .antMatchers("/swagger-ui.html", "/webjars/**", "/images/**",
                        "/configuration/**", "/swagger-resources/**", "/v2/**").permitAll()
                .anyRequest().authenticated()
                .and()
                .addFilterBefore(new JWTFilter(), UsernamePasswordAuthenticationFilter.class);

        // close cache
        httpSecurity.headers().cacheControl();
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-station-food-service/src/main/java/food/config/SecurityConfig.java:SecurityConfig.<init>
package config;

import edu.fudan.common.security.jwt.JWTFilter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpMethod;
import org.springframework.security.config.annotation.method.configuration.EnableGlobalMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configuration.WebSecurityConfigurerAdapter;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurerAdapter;

import static org.springframework.web.cors.CorsConfiguration.ALL;

/**
 * @author fdse
 */
@Configuration
@EnableWebSecurity
@EnableGlobalMethodSecurity(prePostEnabled = true)
public class SecurityConfig extends WebSecurityConfigurerAdapter {

    String admin = "ADMIN";

    /**
     * load password encoder
     *
     * @return PasswordEncoder
     */
    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    /**
     * allow cors domain
     * header  By default, only six fields can be taken from the header, and the other fields can only be specified in the header.
     * credentials   Cookies are not sent by default and can only be true if a Cookie is needed
     * Validity of this request
     *
     * @return WebMvcConfigurer
     */
    @Bean
    public WebMvcConfigurer corsConfigurer() {
        return new WebMvcConfigurerAdapter() {
            @Override
            public void addCorsMappings(CorsRegistry registry) {
                registry.addMapping("/**")
                        .allowedOrigins(ALL)
                        .allowedMethods(ALL)
                        .allowedHeaders(ALL)
                        .allowCredentials(false)
                        .maxAge(3600);
            }
        };
    }


    @Override
    protected void configure(HttpSecurity httpSecurity) throws Exception {
        httpSecurity.httpBasic().disable()
                // close default csrf
                .csrf().disable()
                // close session
                .sessionManagement().sessionCreationPolicy(SessionCreationPolicy.STATELESS)
                .and()
                .authorizeRequests()
                .antMatchers("/api/v1/configservice/**").permitAll()
                .antMatchers(HttpMethod.POST, "/api/v1/configservice/configs").hasAnyRole(admin)
                .antMatchers(HttpMethod.PUT, "/api/v1/configservice/configs").hasAnyRole(admin)
                .antMatchers(HttpMethod.DELETE, "/api/v1/configservice/configs/*").hasAnyRole(admin)
                .antMatchers("/swagger-ui.html", "/webjars/**", "/images/**",
                        "/configuration/**", "/swagger-resources/**", "/v2/**").permitAll()
                .anyRequest().authenticated()
                .and()
                .addFilterBefore(new JWTFilter(), UsernamePasswordAuthenticationFilter.class);

        // close cache
        httpSecurity.headers().cacheControl();
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-config-service/src/main/java/config/SecurityConfig.java:SecurityConfig.<init>
