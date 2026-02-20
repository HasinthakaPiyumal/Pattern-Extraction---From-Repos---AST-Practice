// Cluster 9

// Node: value
package net.javaguides.identity_service.handler;

import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import net.javaguides.common_lib.dto.ApiResponse;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.security.web.access.AccessDeniedHandler;
import org.springframework.stereotype.Component;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.time.LocalDateTime;

@Component
public class CustomAccessDeniedHandler implements AccessDeniedHandler {

    private final ObjectMapper objectMapper;

    public CustomAccessDeniedHandler(ObjectMapper objectMapper) {
        this.objectMapper = objectMapper;
    }

    @Override
    public void handle(HttpServletRequest request, HttpServletResponse response,
                       org.springframework.security.access.AccessDeniedException accessDeniedException) throws IOException {
        ApiResponse<String> apiResponse = new ApiResponse<>("Access denied", HttpStatus.FORBIDDEN.value());
        apiResponse.setTimestamp(LocalDateTime.now());

        response.setStatus(HttpStatus.FORBIDDEN.value());
        response.setContentType(MediaType.APPLICATION_JSON_VALUE);
        response.setCharacterEncoding(StandardCharsets.UTF_8.name());

        response.getWriter().write(objectMapper.writeValueAsString(apiResponse));
    }
}


// Node: repos/cloned_ms_repos/springboot-kafka-microservices/identity-service/src/main/java/net/javaguides/identity_service/handler/CustomAccessDeniedHandler.java:CustomAccessDeniedHandler.<init>
// Node: CustomAccessDeniedHandler
// Node: handle
// Node: setTimestamp
// Node: now
// Node: setContentType
// Node: setCharacterEncoding
// Node: getWriter
// Node: write
// Node: writeValueAsString
package net.javaguides.identity_service.handler;

import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import net.javaguides.common_lib.dto.ApiResponse;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.security.core.AuthenticationException;
import org.springframework.security.web.AuthenticationEntryPoint;
import org.springframework.stereotype.Component;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.time.LocalDateTime;

@Component
public class CustomAuthenticationEntryPoint implements AuthenticationEntryPoint {

    private final ObjectMapper objectMapper;

    public CustomAuthenticationEntryPoint(ObjectMapper objectMapper) {
        this.objectMapper = objectMapper;
    }

    @Override
    public void commence(HttpServletRequest request, HttpServletResponse response,
                         AuthenticationException authException) throws IOException {
        ApiResponse<String> apiResponse = new ApiResponse<>("Unauthorized access", HttpStatus.UNAUTHORIZED.value());
        apiResponse.setTimestamp(LocalDateTime.now());

        response.setStatus(HttpStatus.UNAUTHORIZED.value());
        response.setContentType(MediaType.APPLICATION_JSON_VALUE);
        response.setCharacterEncoding(StandardCharsets.UTF_8.name());

        response.getWriter().write(objectMapper.writeValueAsString(apiResponse));
    }


}



// Node: repos/cloned_ms_repos/springboot-kafka-microservices/identity-service/src/main/java/net/javaguides/identity_service/handler/CustomAuthenticationEntryPoint.java:CustomAuthenticationEntryPoint.<init>
// Node: CustomAuthenticationEntryPoint
// Node: commence
// Node: getBytes
// Node: error
package net.javaguides.product_service.service;
import com.cloudinary.Cloudinary;
import com.cloudinary.utils.ObjectUtils;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.imgscalr.Scalr;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.awt.image.BufferedImage;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.util.Map;
import javax.imageio.ImageIO;

@Service
@RequiredArgsConstructor
@Slf4j
public class CloudinaryService {

    private final Cloudinary cloudinary;

    @Async
    public void uploadFile(MultipartFile file, String publicId) {
        try {
            // Đọc ảnh từ MultipartFile thành BufferedImage
            BufferedImage originalImage = ImageIO.read(file.getInputStream());

            // Resize ảnh, ví dụ resize width về 800px (giữ nguyên tỷ lệ)
            BufferedImage resizedImage = Scalr.resize(originalImage, Scalr.Method.QUALITY, Scalr.Mode.AUTOMATIC, 800);

            // Chuyển ảnh resized thành byte[]
            ByteArrayOutputStream outputStream = new ByteArrayOutputStream();
            ImageIO.write(resizedImage, "jpg", outputStream);
            byte[] resizedBytes = outputStream.toByteArray();

            // Upload ảnh đã resize lên Cloudinary
            Map uploadResult = cloudinary.uploader().upload(resizedBytes, ObjectUtils.asMap(
                    "public_id", publicId,
                    "quality", "auto:good" // Sử dụng nén tự động với chất lượng tốt
            ));

            // Tạo URL mà không chứa version để tiện lợi
            String url = cloudinary.url().generate(uploadResult.get("public_id").toString());

            log.info("Uploaded file URL: {}", url);

        } catch (IOException e) {
            log.error("IO Exception during file upload", e);
        } catch (Exception e) {
            log.error("Unexpected exception during file upload", e);
        }
    }
}


// Node: read
// Node: resize
// Node: ByteArrayOutputStream
// Node: toByteArray
// Node: uploader
// Node: upload
// Node: asMap
// Node: url
// Node: generate
// Node: Cloudinary
package net.javaguides.product_service.config;

import com.cloudinary.Cloudinary;
import com.cloudinary.utils.ObjectUtils;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class CloudinaryConfig {

    @Value("${cloudinary.cloud-name}")
    private String cloudName;

    @Value("${cloudinary.api-key}")
    private String apiKey;

    @Value("${cloudinary.api-secret}")
    private String apiSecret;

    @Bean
    public Cloudinary cloudinary() {
        return new Cloudinary(ObjectUtils.asMap(
                "cloud_name", cloudName,
                "api_key", apiKey,
                "api_secret", apiSecret,
                "secure", true
        ));
    }
}

// Node: cloudinary
package net.javaguides.common_lib.dto;

import lombok.*;

import java.time.LocalDateTime;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class ApiResponse<T> {
    // Getters và Setters
    private LocalDateTime timestamp;
    private T data;
    private int statusCode;

    public ApiResponse(T data, int statusCode) {
        this.timestamp = LocalDateTime.now();
        this.data = data;
        this.statusCode = statusCode;
    }

}


// Node: repos/cloned_ms_repos/springboot-kafka-microservices/common-lib/src/main/java/net/javaguides/common_lib/dto/ApiResponse.java:ApiResponse.<init>
// Node: ApiResponse
// Node: getHeaders
// Node: onError
package net.javaguides.api_gateway.filter;

import com.fasterxml.jackson.databind.ObjectMapper;
import net.javaguides.api_gateway.util.JwtUtil;
import net.javaguides.common_lib.dto.ApiResponse;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.cloud.gateway.filter.GatewayFilter;
import org.springframework.cloud.gateway.filter.factory.AbstractGatewayFilterFactory;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.server.reactive.ServerHttpRequest;
import org.springframework.stereotype.Component;
import org.springframework.web.server.ServerWebExchange;
import reactor.core.publisher.Mono;

import java.nio.charset.StandardCharsets;

@Component
public class AuthenticationFilter extends AbstractGatewayFilterFactory<AuthenticationFilter.Config> {

    @Autowired
    private RouteValidator routeValidator;

    @Autowired
    private JwtUtil jwtUtil;

    @Autowired
    private ObjectMapper objectMapper;  // Sử dụng để serialize ApiResponse

    public AuthenticationFilter() {
        super(Config.class);
    }

    @Override
    public GatewayFilter apply(Config config) {
        return (exchange, chain) -> {
            if (routeValidator.isSecured.test(exchange.getRequest())) {
                // Kiểm tra xem request có chứa cookie không
                HttpHeaders headers = exchange.getRequest().getHeaders();
                if (!headers.containsKey(HttpHeaders.COOKIE)) {
                    return this.onError(exchange, "Missing cookies", HttpStatus.UNAUTHORIZED);
                }

                // Lấy token từ cookie
                String token = extractTokenFromCookies(exchange.getRequest());
                if (token == null) {
                    return this.onError(exchange, "Missing or invalid token in cookies", HttpStatus.UNAUTHORIZED);
                }

                try {
                    // Kiểm tra tính hợp lệ của token
                    jwtUtil.validateToken(token);
                } catch (Exception e) {
                    return this.onError(exchange, "Unauthorized access", HttpStatus.UNAUTHORIZED);
                }
            }
            return chain.filter(exchange);
        };
    }


    private String extractTokenFromCookies(ServerHttpRequest request) {
        return request.getCookies().getFirst("token") != null ?
                request.getCookies().getFirst("token").getValue() : null;
    }

    // Hàm để trả về phản hồi lỗi tùy chỉnh
    private Mono<Void> onError(ServerWebExchange exchange, String errorMessage, HttpStatus httpStatus) {
        exchange.getResponse().setStatusCode(httpStatus);
        exchange.getResponse().getHeaders().setContentType(MediaType.APPLICATION_JSON);

        ApiResponse<String> apiResponse = new ApiResponse<>(errorMessage, httpStatus.value());
        try {
            // Chuyển ApiResponse thành JSON
            byte[] bytes = objectMapper.writeValueAsString(apiResponse).getBytes(StandardCharsets.UTF_8);

            return exchange.getResponse().writeWith(Mono.just(exchange.getResponse()
                    .bufferFactory().wrap(bytes)));
        } catch (Exception e) {
            // Xử lý nếu gặp lỗi trong quá trình serialize
            return Mono.error(e);
        }
    }

    public static class Config {
    }
}


// Node: getResponse
// Node: setStatusCode
// Node: writeWith
// Node: just
// Node: bufferFactory
// Node: wrap
package net.javaguides.api_gateway.filter;

import com.fasterxml.jackson.databind.ObjectMapper;
import net.javaguides.api_gateway.util.JwtUtil;
import net.javaguides.common_lib.dto.ApiResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.cloud.gateway.filter.GatewayFilter;
import org.springframework.cloud.gateway.filter.factory.AbstractGatewayFilterFactory;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.server.reactive.ServerHttpRequest;
import org.springframework.stereotype.Component;
import org.springframework.web.server.ServerWebExchange;
import reactor.core.publisher.Mono;

import java.nio.charset.StandardCharsets;
import java.util.Collection;
import java.util.Collections;
import java.util.List;

@Component
public class RoleBasedAccessFilter extends AbstractGatewayFilterFactory<RoleBasedAccessFilter.Config> {

    private static final Logger log = LoggerFactory.getLogger(RoleBasedAccessFilter.class);
    @Autowired
    private JwtUtil jwtUtil;

    @Autowired
    private ObjectMapper objectMapper;  // Inject ObjectMapper here

    public RoleBasedAccessFilter() {
        super(Config.class);
    }

    @Override
    public GatewayFilter apply(Config config) {
        return (exchange, chain) -> {
            ServerHttpRequest request = exchange.getRequest();

            // Kiểm tra xem phương thức HTTP có nằm trong danh sách được bảo vệ không
            // Trích xuất token từ cookie
            String token = extractTokenFromCookies(request);

            if (token == null) {
                return onError(exchange, "Missing or invalid token", HttpStatus.UNAUTHORIZED);
            }

            try {
                // Xác thực token
                jwtUtil.validateToken(token);

                // Trích xuất vai trò từ token
                List<String> roles = jwtUtil.extractRoles(token);
                List<String> permissions = jwtUtil.extractPermissions(token);
                // Kiểm tra vai trò của người dùng
                boolean hasRole = roles.stream().anyMatch(config.getRequiredRoles()::contains);
                // Kiểm tra vai trò của người dùng
                boolean hasPermission = permissions.stream().anyMatch(config.getRequiredPermissions()::contains);
                if (!hasRole) {
                    return onError(exchange, "Forbidden access", HttpStatus.FORBIDDEN);
                }

                if(config.getRequiredPermissions().size() == 0){
                    return chain.filter(exchange);
                }

                if(!hasPermission){
                    return onError(exchange, "You don't have permission to do this.", HttpStatus.UNAUTHORIZED);
                }

            } catch (Exception e) {
                log.error(e.getMessage());
                return onError(exchange, "Unauthorized access", HttpStatus.UNAUTHORIZED);
            }


            return chain.filter(exchange);
        };
    }

    private String extractTokenFromCookies(ServerHttpRequest request) {
        return request.getCookies().getFirst("token") != null ?
                request.getCookies().getFirst("token").getValue() : null; // Lấy giá trị của cookie "token"
    }

    private Mono<Void> onError(ServerWebExchange exchange, String errorMessage, HttpStatus httpStatus) {
        exchange.getResponse().setStatusCode(httpStatus);
        exchange.getResponse().getHeaders().setContentType(MediaType.APPLICATION_JSON);

        ApiResponse<String> apiResponse = new ApiResponse<>(errorMessage, httpStatus.value());
        try {
            byte[] bytes = objectMapper.writeValueAsString(apiResponse).getBytes(StandardCharsets.UTF_8);
            return exchange.getResponse().writeWith(Mono.just(exchange.getResponse()
                    .bufferFactory().wrap(bytes)));
        } catch (Exception e) {
            return Mono.error(e);
        }
    }

    public static class Config {
        private List<String> requiredPermissions;
        private List<String> requiredRoles;
        private List<String> methods;

        public List<String> getMethods() {
            return methods;
        }

        public void setMethods(List<String> methods) {
            this.methods = methods;
        }

        public List<String> getRequiredPermissions() {
            return requiredPermissions != null ? requiredPermissions : Collections.emptyList();
        }

        public void setRequiredPermissions(List<String> requiredPermissions) {
            this.requiredPermissions = requiredPermissions;
        }

        public List<String> getRequiredRoles() {
            return requiredRoles;
        }

        public void setRequiredRoles(List<String> requiredRoles) {
            this.requiredRoles = requiredRoles;
        }
    }
}


