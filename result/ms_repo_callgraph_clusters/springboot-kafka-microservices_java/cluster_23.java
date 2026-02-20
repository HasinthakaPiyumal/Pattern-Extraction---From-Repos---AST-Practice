// Cluster 23

// Node: extractTokenFromCookies
// Node: getCookies
package net.javaguides.order_service.interceptor;

import feign.RequestInterceptor;
import feign.RequestTemplate;
import org.springframework.stereotype.Component;
import org.springframework.web.context.request.RequestContextHolder;
import org.springframework.web.context.request.ServletRequestAttributes;

@Component
public class FeignClientInterceptor implements RequestInterceptor {

    private static final String AUTHORIZATION_HEADER = "Authorization";

    public static String getBearerTokenHeader() {
        return ((ServletRequestAttributes) RequestContextHolder.getRequestAttributes()).getRequest().getHeader("Authorization");
    }

    @Override
    public void apply(RequestTemplate requestTemplate) {

        requestTemplate.header(AUTHORIZATION_HEADER, getBearerTokenHeader());

    }
}

// Node: getBearerTokenHeader
// Node: getRequestAttributes
// Node: getRequest
// Node: getHeader
// Node: apply
// Node: header
// Node: size
package net.javaguides.order_service.config;

import feign.RequestInterceptor;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.context.request.RequestContextHolder;
import org.springframework.web.context.request.ServletRequestAttributes;

@Configuration
public class FeignConfig {
    @Bean
    public RequestInterceptor requestInterceptor() {
        return requestTemplate -> {
            // Add the JWT token from cookie to the request headers
            HttpServletRequest request = ((ServletRequestAttributes) RequestContextHolder.getRequestAttributes()).getRequest();
            String cookie = request.getHeader("Cookie");
            if (cookie != null) {
                requestTemplate.header("Cookie", cookie);
            }
        };
    }
}


// Node: requestInterceptor
// Node: replacePlaceholders
package net.javaguides.email_service.service;

import jakarta.mail.MessagingException;
import jakarta.mail.internet.MimeMessage;
import net.javaguides.common_lib.dto.ApiResponse;
import net.javaguides.common_lib.dto.order.OrderEvent;
import net.javaguides.common_lib.dto.order.OrderItemDTO;
import net.javaguides.email_service.dto.ProductStockResponse;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.core.io.ClassPathResource;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.mail.javamail.MimeMessageHelper;
import org.springframework.stereotype.Service;
import org.springframework.scheduling.annotation.Async;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.math.BigDecimal;
import java.nio.charset.StandardCharsets;
import java.text.NumberFormat;
import java.util.Date;
import java.util.List;
import java.util.Locale;
import java.util.Map;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@Service
public class EmailService {

    @Autowired
    private JavaMailSender mailSender;

    @Autowired
    private ProductAPIClient productClient;
    private static final Logger logger = LoggerFactory.getLogger(EmailService.class);



    /**
     * Sends an order confirmation email by loading the HTML template and replacing placeholders.
     *
     * @param order The order details
     * @throws MessagingException if sending fails
     * @throws IOException if template reading fails
     */
    public void sendOrderConfirmationEmail(OrderEvent order)
            throws MessagingException, IOException {
        try {
            // Load the HTML template from resources
            String template = loadTemplate("templates/email-template.html");

            // Fetch detailed product information for each OrderItem
            List<OrderItemDTO> items = order.getOrderDTO().getOrderItems();
            StringBuilder orderItemsHtmlBuilder = new StringBuilder();
            BigDecimal amount = BigDecimal.valueOf(0);

            NumberFormat currencyFormatter = NumberFormat.getCurrencyInstance(Locale.US);

            for(OrderItemDTO item : items){
                try {
                    ApiResponse<ProductStockResponse> productResponse = productClient.getProductById(item.getProductId()).getBody();


                    if(productResponse != null && productResponse.getStatusCode() != 200){
                        logger.warn("Product with ID {} not found.", item.getProductId());
                        return;
                    }


                    BigDecimal totalPrice = productResponse.getData().getProduct().getPrice().multiply(BigDecimal.valueOf(item.getQuantity()));

                    amount = amount.add(totalPrice);

                    String formattedUnitPrice = currencyFormatter.format(productResponse.getData().getProduct().getPrice());
                    String formattedTotalPrice = currencyFormatter.format(totalPrice);

                    orderItemsHtmlBuilder.append("<tr>")
                            .append("<td><img width='100' height='100' src='").append(productResponse.getData().getProduct().getImageUrl()).append("' alt='Product Image'/></td>")
                            .append("<td>").append(productResponse.getData().getProduct().getName()).append("</td>")
                            .append("<td>").append(item.getQuantity()).append("</td>")
                            .append("<td>").append(formattedUnitPrice).append("</td>")
                            .append("<td>").append(formattedTotalPrice).append("</td>")
                            .append("</tr>");

                } catch (Exception e) {
                    logger.error("Error fetching product with ID {}: {}", item.getProductId(), e.getMessage());
                    // Optionally, you can continue or rethrow the exception based on requirements
                    continue;
                }
            }

            String orderItemsHtml = orderItemsHtmlBuilder.toString();
            String formattedGrandTotal = currencyFormatter.format(amount);

            // Prepare variables for template replacement
            Map<String, String> variables = Map.of(
                    "customerName", order.getEmail(),
                    "orderId", order.getOrderDTO().getOrderId(),
                    "orderDate", order.getOrderDTO().getCreatedAt().toString(),
                    "orderItems", orderItemsHtml,
                    "grandTotal", formattedGrandTotal,
                    "actionUrl", "https://yourapp.com/orders/" + order.getOrderDTO().getOrderId()
            );

            // Replace placeholders with actual values
            String htmlContent = replacePlaceholders(template, variables);

            // Create a MimeMessage
            MimeMessage message = mailSender.createMimeMessage();

            // Use MimeMessageHelper to set email properties
            MimeMessageHelper helper = new MimeMessageHelper(message, true, "UTF-8");
            helper.setTo(order.getEmail());
            helper.setSubject("Your Order Confirmation - " + order.getOrderDTO().getOrderId());
            helper.setText(htmlContent, true); // true indicates HTML

            // (Optional) Set the sender's email address
            // helper.setFrom("your_email@gmail.com");

            // Send the email
            mailSender.send(message);
            logger.info("Order confirmation email sent to {}", order.getEmail());

        } catch (Exception e) {
            logger.error("Failed to send order confirmation email for Order ID {}: {}", order.getOrderDTO().getOrderId(), e.getMessage());
            throw e;
        }
    }

    /**
     * Loads an HTML template from the classpath.
     *
     * @param path Path to the template file
     * @return Template content as a String
     * @throws IOException if reading fails
     */
    private String loadTemplate(String path) throws IOException {
        ClassPathResource resource = new ClassPathResource(path);
        StringBuilder contentBuilder = new StringBuilder();

        try (BufferedReader reader = new BufferedReader(
                new InputStreamReader(resource.getInputStream(), StandardCharsets.UTF_8))) {
            String line;
            while((line = reader.readLine()) != null){
                contentBuilder.append(line).append("\n");
            }
        }

        return contentBuilder.toString();
    }

    /**
     * Replaces placeholders in the template with actual values.
     *
     * @param template The email template with placeholders
     * @param variables Map of placeholders and their corresponding values
     * @return The final email content
     */
    private String replacePlaceholders(String template, Map<String, String> variables){
        String result = template;
        for(Map.Entry<String, String> entry : variables.entrySet()){
            String placeholder = "{" + entry.getKey() + "}";
            result = result.replace(placeholder, entry.getValue());
        }
        return result;
    }
}


// Node: entrySet
// Node: getKey
// Node: replace
// Node: getValue
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


// Node: test
// Node: containsKey
// Node: getFirst
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


// Node: anyMatch
// Node: getRequiredRoles
// Node: getRequiredPermissions
// Node: emptyList
