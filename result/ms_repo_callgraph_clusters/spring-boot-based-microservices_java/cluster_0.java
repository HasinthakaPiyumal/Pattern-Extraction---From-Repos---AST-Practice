// Cluster 0

package io.javatab.util.http;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.net.InetAddress;
import java.net.UnknownHostException;

@Component
public class NetworkUtility {

    private final String port;

    private String serviceAddress = null;

    public NetworkUtility(@Value("${server.port}") String port) {
        this.port = port;
    }

    public String getServiceAddress() {
        if (serviceAddress == null) {
            serviceAddress = findMyHostname() + "/" + findMyIpAddress() + ":" + port;
        }
        return serviceAddress;
    }

    private String findMyHostname() {
        try {
            return InetAddress.getLocalHost().getHostName();
        } catch (UnknownHostException e) {
            return "unknown host name";
        }
    }

    private String findMyIpAddress() {
        try {
            return InetAddress.getLocalHost().getHostAddress();
        } catch (UnknownHostException e) {
            return "unknown IP address";
        }
    }

}


// Node: repos/cloned_ms_repos/spring-boot-based-microservices/util/src/main/java/io/javatab/util/http/NetworkUtility.java:NetworkUtility.<init>
// Node: NetworkUtility
// Node: Value
package com.example.springcloud.gateway.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.convert.converter.Converter;
import org.springframework.security.authentication.AbstractAuthenticationToken;
import org.springframework.security.config.Customizer;
import org.springframework.security.config.annotation.web.reactive.EnableWebFluxSecurity;
import org.springframework.security.config.web.server.ServerHttpSecurity;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.security.oauth2.jwt.NimbusReactiveJwtDecoder;
import org.springframework.security.oauth2.jwt.ReactiveJwtDecoder;
import org.springframework.security.oauth2.server.resource.authentication.JwtAuthenticationToken;
import org.springframework.security.web.server.SecurityWebFilterChain;
import reactor.core.publisher.Mono;

import java.util.ArrayList;
import java.util.Collection;
import java.util.List;
import java.util.Map;

@Configuration
@EnableWebFluxSecurity
public class SecurityConfig {

    private String jwkSetUri;
    public SecurityConfig(@Value("${app.jwk-set-uri}") String jwkSetUri) {
        this.jwkSetUri = jwkSetUri;
    }

    @Bean
    public SecurityWebFilterChain securityWebFilterChain(ServerHttpSecurity http) {
        http
                .authorizeExchange(exchanges -> exchanges
                        .pathMatchers("/api/public", "/actuator/**").permitAll()
                        .anyExchange().authenticated()
                )
                .oauth2ResourceServer(oauth2 -> oauth2
                        .jwt(jwt -> jwt.jwtAuthenticationConverter(grantedAuthoritiesExtractor()))
                );

        return http.build();
    }

    @Bean
    public ReactiveJwtDecoder jwtDecoder() {
        System.out.println("======== " + jwkSetUri);
        return NimbusReactiveJwtDecoder.withJwkSetUri(jwkSetUri).build();
    }

    @Bean
    public Converter<Jwt, Mono<JwtAuthenticationToken>> grantedAuthoritiesExtractor() {
        return new Converter<Jwt, Mono<JwtAuthenticationToken>>() {
            @Override
            public Mono<JwtAuthenticationToken> convert(Jwt jwt) {
                Collection<GrantedAuthority> authorities = new ArrayList<>();

                // Extract realm roles
                Map<String, Object> realmAccess = jwt.getClaim("realm_access");
                if (realmAccess != null && realmAccess.containsKey("roles")) {
                    List<String> roles = (List<String>) realmAccess.get("roles");
                    authorities.addAll(roles.stream()
                            .map(role -> new SimpleGrantedAuthority("ROLE_" + role.toUpperCase()))
                            .toList());
                }

                Map<String, Object> resourceAccess = jwt.getClaim("resource_access");
                if (resourceAccess != null) {
                    resourceAccess.forEach((resource, access) -> {
                        if (access instanceof Map) {
                            Map<String, Object> clientRoles = (Map<String, Object>) access;
                            if (clientRoles.containsKey("roles")) {
                                List<String> roles = (List<String>) clientRoles.get("roles");
                                authorities.addAll(roles.stream()
                                        .map(role -> new SimpleGrantedAuthority("ROLE_" + role.toUpperCase()))
                                        .toList());
                            }
                        }
                    });
                }
                return Mono.just(new JwtAuthenticationToken(jwt, authorities));
            }
        };
    }
}

// Node: repos/cloned_ms_repos/spring-boot-based-microservices/spring-cloud/gateway-service/src/main/java/com/example/springcloud/gateway/config/SecurityConfig.java:SecurityConfig.<init>
// Node: SecurityConfig
package io.javatab.microservices.core.course;


import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.context.annotation.ComponentScan;


@SpringBootApplication
@ComponentScan({"io.javatab"})
public class CourseServiceApplication {

	private static final Logger LOG = LoggerFactory.getLogger(CourseServiceApplication.class);

	public static void main(String[] args) {
		ConfigurableApplicationContext ctx = SpringApplication.run(CourseServiceApplication.class, args);

		String postgresUri = ctx.getEnvironment().getProperty("spring.datasource.url");
		LOG.info("Connected to Postgres: " + postgresUri);
	}

}


// Node: repos/cloned_ms_repos/spring-boot-based-microservices/microservices/course-service/src/main/java/io/javatab/microservices/core/course/CourseServiceApplication.java:CourseServiceApplication.<init>
// Node: ComponentScan
// Node: getLogger
package io.javatab.microservices.core.course.web;

import io.javatab.microservices.core.course.domain.Course;
import io.javatab.microservices.core.course.domain.CourseService;
import io.javatab.util.http.NetworkUtility;
import jakarta.validation.Valid;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;

@RestController()
@RequestMapping("/api/courses")
public class CourseController {

    private final Logger logger = LoggerFactory.getLogger(CourseController.class);

    private final NetworkUtility utility;
    private CourseService courseService;

    public CourseController(NetworkUtility utility, CourseService courseService) {
        this.utility = utility;
        this.courseService = courseService;
    }

    @GetMapping
    public Iterable<Course> get() {
        logger.info("Fetching courses");
        return courseService.viewCourses();
    }

    /*
    * Make sure application is running in localhost mode to test and not in docker
    * http GET ':9001/api/courses/Microservices with Spring Boot'
    * */
    @GetMapping("/title/{title}")
    public Course getByTitle(@PathVariable String title) {
        return courseService.viewCourseDetails(title);
    }

    @GetMapping("/{id}")
    public Course getById(@PathVariable Long id) {
        return courseService.viewCourseDetailsById(id);
    }

    /*
    * http POST :9001/api/courses title="Microservices with Spring Boot" author="John Doe" price:=29.79 publisher="GitHub"
    * http POST :9001/api/courses title="Spring Boot in Action" author="John Doe" price:=69.45 publisher="GitHub"
    * */
    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public Course post(@Valid @RequestBody Course course) {
        logger.info("Received request to create course: {}", course.getTitle());
        Course savedCourse = courseService.addCourse(course);
        if (savedCourse.getId() == null) {
            logger.error("Course was not saved correctly! ID is null.");
            throw new IllegalStateException("Failed to save course, ID is null!");
        }
        logger.info("Course created successfully with ID: {}", savedCourse.getId());
        return savedCourse;
    }

    @DeleteMapping("/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void delete(@PathVariable Long id) {
        courseService.removeCourse(id);
    }

    @PutMapping("/{id}")
    public Course put(@PathVariable Long id, @Valid @RequestBody Course course) {
        return courseService.editCourseDetails(id, course);
    }

}


// Node: repos/cloned_ms_repos/spring-boot-based-microservices/microservices/course-service/src/main/java/io/javatab/microservices/core/course/web/CourseController.java:CourseController.<init>
// Node: RestController
// Node: RequestMapping
// Node: CourseController
package io.javatab.microservices.core.course.domain;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

@Service
public class CourseService {

    private final Logger logger = LoggerFactory.getLogger(CourseService.class);

    private final CourseRepository courseRepository;

    public CourseService(CourseRepository courseRepository) {
        this.courseRepository = courseRepository;
    }

    public Iterable<Course> viewCourses() {
        return courseRepository.findAll();
    }

    public Course viewCourseDetails(String title) {
        return courseRepository.findByTitle(title)
                .orElseThrow(() -> new CourseNotFoundException(title));
    }

    public Course viewCourseDetailsById(Long id) {
        return courseRepository.findById(id)
                .orElseThrow(() -> new CourseNotFoundException(String.valueOf(id)));
    }

    public Course addCourse(Course course) {

        logger.info("Checking if course '{}' already exists...", course.getTitle());

        if (courseRepository.existsByTitle(course.getTitle())) {
            logger.warn("Course '{}' already exists! Throwing exception.", course.getTitle());
            throw new CourseAlreadyExitsException(course.getTitle());
        }

        Course savedCourse = courseRepository.save(course);
        logger.info("Course '{}' saved successfully with ID: {}", savedCourse.getTitle(), savedCourse.getId());

        return savedCourse;
    }

    public void removeCourse(Long id) {
        courseRepository.deleteById(id);
    }

    public Course editCourseDetails(Long id, Course course) {
        return courseRepository.findById(id)
                .map(existingCourse -> {
                    existingCourse.setTitle(course.getTitle());
                    existingCourse.setAuthor(course.getAuthor());
                    existingCourse.setPrice(course.getPrice());
                    existingCourse.setPublisher(course.getPublisher());
                    return courseRepository.save(existingCourse);
                }).orElseGet(() -> addCourse(course));

    }
}


// Node: repos/cloned_ms_repos/spring-boot-based-microservices/microservices/course-service/src/main/java/io/javatab/microservices/core/course/domain/CourseService.java:CourseService.<init>
// Node: CourseService
package io.javatab.microservices.core.course.config;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.convert.converter.Converter;
import org.springframework.security.config.annotation.web.reactive.EnableWebFluxSecurity;
import org.springframework.security.config.web.server.SecurityWebFiltersOrder;
import org.springframework.security.config.web.server.ServerHttpSecurity;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.security.oauth2.jwt.NimbusReactiveJwtDecoder;
import org.springframework.security.oauth2.jwt.ReactiveJwtDecoder;
import org.springframework.security.oauth2.server.resource.authentication.JwtAuthenticationToken;
import org.springframework.security.web.server.SecurityWebFilterChain;
import org.springframework.web.server.ServerWebExchange;
import reactor.core.publisher.Mono;

import java.util.ArrayList;
import java.util.Collection;
import java.util.List;
import java.util.Map;

@Configuration
@EnableWebFluxSecurity
public class SecurityConfig {

    private static final Logger logger = LoggerFactory.getLogger(SecurityConfig.class);

    private String jwkSetUri;

    public SecurityConfig(@Value("${app.jwk-set-uri}") String jwkSetUri) {
        this.jwkSetUri = jwkSetUri;
    }

    @Bean
    public SecurityWebFilterChain securityFilterChain(ServerHttpSecurity http) {
        http
                .authorizeExchange(exchanges -> exchanges
                        .pathMatchers("/actuator/**").permitAll()
                        .pathMatchers("/api/courses/**").hasAnyRole("COURSE-READ", "COURSE-WRITE")
                        .anyExchange().authenticated()
                )
                .oauth2ResourceServer(oauth2 -> oauth2
                        .jwt(jwt -> jwt.jwtAuthenticationConverter(grantedAuthoritiesExtractor()))
                );

        // Add filter to log roles
        http.addFilterAt((exchange, chain) -> logRoles(exchange).then(chain.filter(exchange)),
                SecurityWebFiltersOrder.AUTHORIZATION);

        return http.build();
    }

    @Bean
    public ReactiveJwtDecoder jwtDecoder() {
        return NimbusReactiveJwtDecoder.withJwkSetUri(jwkSetUri).build();
    }

    @Bean
    public Converter<Jwt, Mono<JwtAuthenticationToken>> grantedAuthoritiesExtractor() {
        return new Converter<Jwt, Mono<JwtAuthenticationToken>>() {
            @Override
            public Mono<JwtAuthenticationToken> convert(Jwt jwt) {
                Collection<GrantedAuthority> authorities = new ArrayList<>();

                // Extract realm roles
                Map<String, Object> realmAccess = jwt.getClaim("realm_access");
                if (realmAccess != null && realmAccess.containsKey("roles")) {
                    List<String> roles = (List<String>) realmAccess.get("roles");
                    authorities.addAll(roles.stream()
                            .map(role -> new SimpleGrantedAuthority("ROLE_" + role.toUpperCase()))
                            .toList());
                }

                Map<String, Object> resourceAccess = jwt.getClaim("resource_access");
                if (resourceAccess != null) {
                    resourceAccess.forEach((resource, access) -> {
                        if (access instanceof Map) {
                            Map<String, Object> clientRoles = (Map<String, Object>) access;
                            if (clientRoles.containsKey("roles")) {
                                List<String> roles = (List<String>) clientRoles.get("roles");
                                authorities.addAll(roles.stream()
                                        .map(role -> new SimpleGrantedAuthority("ROLE_" + role.toUpperCase()))
                                        .toList());
                            }
                        }
                    });
                }

                return Mono.just(new JwtAuthenticationToken(jwt, authorities));
            }
        };
    }

    private Mono<Void> logRoles(ServerWebExchange exchange) {
        return exchange.getPrincipal()
                .cast(JwtAuthenticationToken.class)
                .doOnNext(jwtAuth -> {
                    Collection<? extends GrantedAuthority> authorities = jwtAuth.getAuthorities();
                    logger.info("Roles in Resource Server: {}", authorities);
                })
                .then();
    }
}

// Node: repos/cloned_ms_repos/spring-boot-based-microservices/microservices/course-service/src/main/java/io/javatab/microservices/core/course/config/SecurityConfig.java:SecurityConfig.<init>
package io.javatab.microservices.composite.course;

import io.micrometer.core.instrument.Counter;
import io.micrometer.core.instrument.MeterRegistry;
import io.micrometer.core.instrument.Timer;
import jakarta.annotation.PostConstruct;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;


import java.util.Random;


/*
* Just for manual test for metrics and errors which doesn't sit under security
* */
@RestController
@RequestMapping("/api/metrics")
public class MetricsController {
    private final Logger logger = LoggerFactory.getLogger(MetricsController.class);
    private final MeterRegistry meterRegistry;
    private Counter requestCounter;
    private Timer requestTimer;

    public MetricsController(MeterRegistry meterRegistry) {
        this.meterRegistry = meterRegistry;
    }

    @PostConstruct
    public void init() {
        // Initialize custom metrics
        requestCounter = Counter
                .builder("api.requests.total")
                .description("Total number of API requests")
                .tags("endpoint", "/hello")
                .register(meterRegistry);

        requestTimer = Timer
                .builder("api.request.duration")
                .description("Time taken to process requests")
                .tags("endpoint", "/hello")
                .register(meterRegistry);
    }

    @GetMapping("/hello")
    public String hello() {
        logger.info("Hello endpoint called");
        logger.warn("This is a warning log");
        // Record request count
        requestCounter.increment();

        // Record execution time
        return requestTimer.record(() -> {
            try {
                // Simulate some work
                int sleepTime = new Random().nextInt(1000);
                Thread.sleep(sleepTime);
                return "Hello, World!";
            } catch (InterruptedException e) {
                return "Error occurred";
            }
        });
    }

    @GetMapping("/runtime-error")
    public String error() {
        logger.error("An error occurred", new RuntimeException("Test exception"));
        return "Error logged";
    }

    @GetMapping("/error")
    public String triggerError() {
        throw new ResponseStatusException(HttpStatus.INTERNAL_SERVER_ERROR, "Something went wrong!");
    }
}

// Node: repos/cloned_ms_repos/spring-boot-based-microservices/microservices/course-composite-service/src/main/java/io/javatab/microservices/composite/course/MetricsController.java:MetricsController.<init>
// Node: MetricsController
package io.javatab.microservices.composite.course;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.web.client.RestTemplate;

@SpringBootApplication
@ComponentScan({"io.javatab"})
public class CourseCompositeServiceApplication {

	public static void main(String[] args) {
		SpringApplication.run(CourseCompositeServiceApplication.class, args);
	}

}


// Node: repos/cloned_ms_repos/spring-boot-based-microservices/microservices/course-composite-service/src/main/java/io/javatab/microservices/composite/course/CourseCompositeServiceApplication.java:CourseCompositeServiceApplication.<init>
package io.javatab.microservices.composite.course.web;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

import java.util.List;

@Service
public class CourseCompositeIntegration {

    private static final Logger logger = LoggerFactory.getLogger(CourseCompositeIntegration.class);

    private final String courseServiceUrl;
    private final String reviewServiceUrl;
    private final WebClient webClient;

    public CourseCompositeIntegration(
            @Value("${app.course-service.uri}") String courseServiceUrl,
            @Value("${app.review-service.uri}") String reviewServiceUrl,
            WebClient.Builder webClient
    ) {
        this.webClient = webClient.build();
        this.courseServiceUrl = courseServiceUrl;
        this.reviewServiceUrl = reviewServiceUrl;
    }

    public Mono<CourseAggregate> getCourseDetails(Long id, Jwt jwt) {
        logger.debug("JWT ===> {}", jwt.getTokenValue());
        String courseUrl = courseServiceUrl + "/api/courses/" + id;
        String reviewUrl = reviewServiceUrl + "/api/reviews?course=" + id;
        logger.debug("Course URL ===> {}", courseUrl);
        logger.debug("Review URL ===> {}", reviewUrl);
        Mono<Course> courseMono = webClient.get()
                .uri(courseUrl)
                .header("Authorization", "Bearer " + jwt.getTokenValue())
                .retrieve()
                .bodyToMono(Course.class);

        Mono<List<Review>> reviewsMono = webClient.get()
                .uri(reviewUrl)
                .header("Authorization", "Bearer " + jwt.getTokenValue())
                .retrieve()
                .bodyToFlux(Review.class)
                .collectList();

        return Mono.zip(courseMono, reviewsMono)
                .map(tuple -> CourseAggregate
                        .builder()
                        .course(tuple.getT1())
                        .reviews(tuple.getT2())
                        .build());
    }
}


// Node: repos/cloned_ms_repos/spring-boot-based-microservices/microservices/course-composite-service/src/main/java/io/javatab/microservices/composite/course/web/CourseCompositeIntegration.java:CourseCompositeIntegration.<init>
// Node: CourseCompositeIntegration
package io.javatab.microservices.composite.course.config;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.convert.converter.Converter;
import org.springframework.security.config.Customizer;
import org.springframework.security.config.annotation.web.reactive.EnableWebFluxSecurity;
import org.springframework.security.config.web.server.SecurityWebFiltersOrder;
import org.springframework.security.config.web.server.ServerHttpSecurity;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.security.oauth2.jwt.NimbusReactiveJwtDecoder;
import org.springframework.security.oauth2.jwt.ReactiveJwtDecoder;
import org.springframework.security.oauth2.server.resource.authentication.JwtAuthenticationToken;
import org.springframework.security.web.server.SecurityWebFilterChain;
import org.springframework.web.server.ServerWebExchange;
import reactor.core.publisher.Mono;

import java.util.ArrayList;
import java.util.Collection;
import java.util.List;
import java.util.Map;

@Configuration
@EnableWebFluxSecurity
public class SecurityConfig {

    private static final Logger logger = LoggerFactory.getLogger(SecurityConfig.class);

    private String jwkSetUri;

    public SecurityConfig(@Value("${app.jwk-set-uri}") String jwkSetUri) {
        this.jwkSetUri = jwkSetUri;
    }

    @Bean
    public SecurityWebFilterChain securityFilterChain(ServerHttpSecurity http) {
        http
                .authorizeExchange(exchanges -> exchanges
                        .pathMatchers("/actuator/**", "/api/metrics/**").permitAll()
                        .pathMatchers("/api/course-aggregate/**").hasAnyRole("COURSE-READ", "REVIEW-READ")
                        .anyExchange().authenticated()
                )
                .oauth2ResourceServer(oauth2 -> oauth2
                        .jwt(jwt -> jwt.jwtAuthenticationConverter(grantedAuthoritiesExtractor()))
                );

        // Add filter to log roles
        http.addFilterAt((exchange, chain) -> logRoles(exchange).then(chain.filter(exchange)),
                SecurityWebFiltersOrder.AUTHORIZATION);

        return http.build();
    }

    @Bean
    public ReactiveJwtDecoder jwtDecoder() {
        return NimbusReactiveJwtDecoder.withJwkSetUri(jwkSetUri).build();
    }

    @Bean
    public Converter<Jwt, Mono<JwtAuthenticationToken>> grantedAuthoritiesExtractor() {
        return new Converter<Jwt, Mono<JwtAuthenticationToken>>() {
            @Override
            public Mono<JwtAuthenticationToken> convert(Jwt jwt) {
                Collection<GrantedAuthority> authorities = new ArrayList<>();

                // Extract realm roles
                Map<String, Object> realmAccess = jwt.getClaim("realm_access");
                if (realmAccess != null && realmAccess.containsKey("roles")) {
                    List<String> roles = (List<String>) realmAccess.get("roles");
                    authorities.addAll(roles.stream()
                            .map(role -> new SimpleGrantedAuthority("ROLE_" + role.toUpperCase()))
                            .toList());
                }

                // Extract client roles (replace "my-resource-server" with your client ID)
                /*Map<String, Object> resourceAccess = jwt.getClaim("resource_access");
                if (resourceAccess != null) {
                    Map<String, Object> clientRoles = (Map<String, Object>) resourceAccess.get("my-resource-server");
                    if (clientRoles != null && clientRoles.containsKey("roles")) {
                        List<String> roles = (List<String>) clientRoles.get("roles");
                        authorities.addAll(roles.stream()
                                .map(role -> new SimpleGrantedAuthority("ROLE_" + role.toUpperCase()))
                                .toList());
                    }
                }*/
                Map<String, Object> resourceAccess = jwt.getClaim("resource_access");
                if (resourceAccess != null) {
                    resourceAccess.forEach((resource, access) -> {
                        if (access instanceof Map) {
                            Map<String, Object> clientRoles = (Map<String, Object>) access;
                            if (clientRoles.containsKey("roles")) {
                                List<String> roles = (List<String>) clientRoles.get("roles");
                                authorities.addAll(roles.stream()
                                        .map(role -> new SimpleGrantedAuthority("ROLE_" + role.toUpperCase()))
                                        .toList());
                            }
                        }
                    });
                }

                return Mono.just(new JwtAuthenticationToken(jwt, authorities));
            }
        };
    }

    private Mono<Void> logRoles(ServerWebExchange exchange) {
        return exchange.getPrincipal()
                .cast(JwtAuthenticationToken.class)
                .doOnNext(jwtAuth -> {
                    Collection<? extends GrantedAuthority> authorities = jwtAuth.getAuthorities();
                    logger.info("Roles in Resource Server: {}", authorities);
                })
                .then();
    }
}

// Node: repos/cloned_ms_repos/spring-boot-based-microservices/microservices/course-composite-service/src/main/java/io/javatab/microservices/composite/course/config/SecurityConfig.java:SecurityConfig.<init>
package io.javatab.microservices.core.review;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.context.annotation.ComponentScan;

@SpringBootApplication
@ComponentScan({"io.javatab"})
public class ReviewServiceApplication {

	private static final Logger logger = LoggerFactory.getLogger(ReviewServiceApplication.class);

	public static void main(String[] args) {
		ConfigurableApplicationContext ctx = SpringApplication.run(ReviewServiceApplication.class, args);

		String mongoDbUri = ctx.getEnvironment().getProperty("spring.data.mongodb.uri");
        logger.info("Connected to MongoDb ===> {}", mongoDbUri);
	}

}


// Node: repos/cloned_ms_repos/spring-boot-based-microservices/microservices/review-service/src/main/java/io/javatab/microservices/core/review/ReviewServiceApplication.java:ReviewServiceApplication.<init>
package io.javatab.microservices.core.review.web;

import io.javatab.microservices.core.review.domain.Review;
import io.javatab.microservices.core.review.domain.ReviewService;

import jakarta.validation.Valid;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController()
@RequestMapping("/api/reviews")
public class ReviewController {

    private static final Logger logger = LoggerFactory.getLogger(ReviewController.class);
    private final ReviewService reviewService;

    public ReviewController(ReviewService reviewService) {
        this.reviewService = reviewService;
    }


    /*
    * http POST :9002/api/reviews courseId:=1 author="John Doe" content="Amazing book"  email="abc@xyz.com"
    * */
    @PostMapping
    public ResponseEntity<Review> addReview(@Valid @RequestBody ReviewDTO review) {
        logger.info("Received request to add review to course id {} by email: {} and ", review.getCourseId(), review.getEmail());
        Review addedReview = reviewService.addReview(review);
        return new ResponseEntity<>(addedReview, HttpStatus.CREATED);
    }

    @GetMapping
    public ResponseEntity<List<Review>> getAllReviews() {
        logger.info("Received request to fetch all reviews");
        return ResponseEntity.ok(reviewService.getAllReviews());
    }

    @GetMapping("/{id}")
    public ResponseEntity<Review> getReviewById(@PathVariable String id) {
        logger.info("Received request to fetch review with id: {}", id);
        return ResponseEntity.ok(reviewService.getReviewId(id));
    }

    @GetMapping(params = {"course"})
    public ResponseEntity<List<Review>> getReviewByCourseId(@RequestParam("course") Long courseId) {
        logger.info("Received request to fetch review with course id: {}", courseId);
        return ResponseEntity.ok(reviewService.getReviewsByCourseId(courseId));
    }

    /*
    * http :9002/api/reviews courseId==1 email==abc@xyz.com
    * or
    * http GET "http://localhost:9002/api/reviews?courseId=1&email=abc@xyz.com"
     * */
    @GetMapping(params = {"courseId", "email"})
    public ResponseEntity<List<Review>> getReviewByCourseIdAndEmail(@RequestParam("courseId") Long courseId, @RequestParam("email") String email) {
        logger.info("Received request to fetch review with course id: {} and email : {}", courseId, email);
        return ResponseEntity.ok(reviewService.getReviewsByCourseIdAndEmail(courseId, email));
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteReview(@PathVariable String id) {
        logger.info("Received request to delete review with id: {}", id);
        reviewService.deleteReview(id);
        return ResponseEntity.noContent().build();
    }
}


// Node: repos/cloned_ms_repos/spring-boot-based-microservices/microservices/review-service/src/main/java/io/javatab/microservices/core/review/web/ReviewController.java:ReviewController.<init>
// Node: ReviewController
package io.javatab.microservices.core.review.domain;

import io.javatab.microservices.core.review.web.ReviewDTO;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
public class ReviewService {

    private static final Logger logger = LoggerFactory.getLogger(ReviewService.class);
    private final ReviewRepository reviewRepository;

    public ReviewService(ReviewRepository reviewRepository) {
        this.reviewRepository = reviewRepository;
    }

    @Transactional
    public Review addReview(ReviewDTO reviewDto) {
        logger.info("Adding new review with email: {}", reviewDto.getEmail());
        Review aReview = Review.builder()
                .courseId(reviewDto.getCourseId())
                .author(reviewDto.getAuthor())
                .content(reviewDto.getContent())
                .email(reviewDto.getEmail())
                .build();
        return reviewRepository.save(aReview);
    }

    @Transactional(readOnly = true)
    public List<Review> getAllReviews() {
        logger.info("Fetching all reviews");
        return reviewRepository.findAll();
    }

    @Transactional(readOnly = true)
    public List<Review> getReviewsByEmail(String email) {
        logger.info("Fetching review with email: {}", email);
        return reviewRepository.findByEmail(email);
    }

    @Transactional(readOnly = true)
    public List<Review> getReviewsByCourseIdAndEmail(Long courseId, String email) {
        logger.info("Fetching review with course Id: {} and by email {}", courseId, email);
        return reviewRepository.findByCourseIdAndEmail(courseId, email);
    }

    @Transactional(readOnly = true)
    public List<Review> getReviewsByCourseId(Long courseId) {
        logger.info("Fetching review with course Id : {}", courseId);
        return reviewRepository.findByCourseId(courseId);
    }

    @Transactional
    public void deleteReview(String id) {
        logger.info("Deleting review with id: {}", id);
        if (!reviewRepository.existsById(id)) {
            throw new ReviewNotFoundException("Review not found with id: " + id);
        }
        reviewRepository.deleteById(id);
    }

    @Transactional
    public Review getReviewId(String id) {
        logger.info("Fetching review with id: {}", id);
        return reviewRepository.findById(id)
                .orElseThrow(() -> new ReviewNotFoundException(id));
    }
}


// Node: repos/cloned_ms_repos/spring-boot-based-microservices/microservices/review-service/src/main/java/io/javatab/microservices/core/review/domain/ReviewService.java:ReviewService.<init>
// Node: ReviewService
package io.javatab.microservices.core.review.config;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.convert.converter.Converter;
import org.springframework.security.config.annotation.web.reactive.EnableWebFluxSecurity;
import org.springframework.security.config.web.server.SecurityWebFiltersOrder;
import org.springframework.security.config.web.server.ServerHttpSecurity;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.security.oauth2.jwt.NimbusReactiveJwtDecoder;
import org.springframework.security.oauth2.jwt.ReactiveJwtDecoder;
import org.springframework.security.oauth2.server.resource.authentication.JwtAuthenticationToken;
import org.springframework.security.web.server.SecurityWebFilterChain;
import org.springframework.web.server.ServerWebExchange;
import reactor.core.publisher.Mono;

import java.util.ArrayList;
import java.util.Collection;
import java.util.List;
import java.util.Map;

@Configuration
@EnableWebFluxSecurity
public class SecurityConfig {

    private static final Logger logger = LoggerFactory.getLogger(SecurityConfig.class);

    private String jwkSetUri;

    public SecurityConfig(@Value("${app.jwk-set-uri}") String jwkSetUri) {
        this.jwkSetUri = jwkSetUri;
    }

    @Bean
    public SecurityWebFilterChain securityFilterChain(ServerHttpSecurity http) {
        http
                .authorizeExchange(exchanges -> exchanges
                        .pathMatchers("/actuator/**").permitAll()
                        .pathMatchers("/api/reviews/**").hasAnyRole("REVIEW-READ", "REVIEW-WRITE")
                        .anyExchange().authenticated()
                )
                .oauth2ResourceServer(oauth2 -> oauth2
                        .jwt(jwt -> jwt.jwtAuthenticationConverter(grantedAuthoritiesExtractor()))
                );

        // Add filter to log roles
        http.addFilterAt((exchange, chain) -> logRoles(exchange).then(chain.filter(exchange)),
                SecurityWebFiltersOrder.AUTHORIZATION);

        return http.build();
    }

    @Bean
    public ReactiveJwtDecoder jwtDecoder() {
        return NimbusReactiveJwtDecoder.withJwkSetUri(jwkSetUri).build();
    }

    @Bean
    public Converter<Jwt, Mono<JwtAuthenticationToken>> grantedAuthoritiesExtractor() {
        return new Converter<Jwt, Mono<JwtAuthenticationToken>>() {
            @Override
            public Mono<JwtAuthenticationToken> convert(Jwt jwt) {
                Collection<GrantedAuthority> authorities = new ArrayList<>();

                // Extract realm roles
                Map<String, Object> realmAccess = jwt.getClaim("realm_access");
                if (realmAccess != null && realmAccess.containsKey("roles")) {
                    List<String> roles = (List<String>) realmAccess.get("roles");
                    authorities.addAll(roles.stream()
                            .map(role -> new SimpleGrantedAuthority("ROLE_" + role.toUpperCase()))
                            .toList());
                }

                Map<String, Object> resourceAccess = jwt.getClaim("resource_access");
                if (resourceAccess != null) {
                    resourceAccess.forEach((resource, access) -> {
                        if (access instanceof Map) {
                            Map<String, Object> clientRoles = (Map<String, Object>) access;
                            if (clientRoles.containsKey("roles")) {
                                List<String> roles = (List<String>) clientRoles.get("roles");
                                authorities.addAll(roles.stream()
                                        .map(role -> new SimpleGrantedAuthority("ROLE_" + role.toUpperCase()))
                                        .toList());
                            }
                        }
                    });
                }

                return Mono.just(new JwtAuthenticationToken(jwt, authorities));
            }
        };
    }

    private Mono<Void> logRoles(ServerWebExchange exchange) {
        return exchange.getPrincipal()
                .cast(JwtAuthenticationToken.class)
                .doOnNext(jwtAuth -> {
                    Collection<? extends GrantedAuthority> authorities = jwtAuth.getAuthorities();
                    logger.info("Roles in Resource Server: {}", authorities);
                })
                .then();
    }
}

// Node: repos/cloned_ms_repos/spring-boot-based-microservices/microservices/review-service/src/main/java/io/javatab/microservices/core/review/config/SecurityConfig.java:SecurityConfig.<init>
