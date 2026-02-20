// Cluster 38

package net.javaguides.identity_service.config;

import lombok.Getter;
import net.javaguides.identity_service.entity.Permission;
import net.javaguides.identity_service.entity.UserCredential;
import net.javaguides.identity_service.enums.EPermission;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.userdetails.UserDetails;

import java.util.Collection;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import java.util.stream.Collectors;

@Getter
public class CustomUserDetails implements UserDetails {
    private Long id;
    private String username;
    private String password;
    private String email;
    private Collection<? extends GrantedAuthority> authorities;
    private Set<String> permissions;

    public CustomUserDetails(Long id, String username, String password, String email, Collection<? extends GrantedAuthority> authorities, Set<String> permissions) {
        this.id = id;
        this.email = email;
        this.username = username;
        this.password = password;
        this.authorities = authorities;
        this.permissions = permissions;
    }

    public CustomUserDetails(UserCredential userCredential) {
        this.username = userCredential.getName();
        this.password = userCredential.getPassword();
    }

    @Override
    public Collection<? extends GrantedAuthority> getAuthorities() {
        return authorities;
    }

    // Phương thức để trả về danh sách các authority dưới dạng mảng String
    public List<String> getRoleNames() {
        return authorities.stream()
                .map(GrantedAuthority::getAuthority)  // Lấy tên của mỗi authority
                .collect(Collectors.toList());
    }


    @Override
    public String getPassword() {
        return password;
    }

    @Override
    public String getUsername() {
        return username;
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

    // Phương thức build để tạo CustomUserDetails từ UserCredential
    public static CustomUserDetails build(UserCredential user) {
        // Lấy danh sách vai trò (roles) và chuyển thành danh sách SimpleGrantedAuthority
        List<GrantedAuthority> authorities = user.getRoles().stream()
                .map(role -> new SimpleGrantedAuthority(role.getName().name()))
                .collect(Collectors.toList());

        // Lấy danh sách các quyền (permissions) và chuyển thành danh sách String
        Set<String> permissions = user.getPermissions().stream()
                .map(permission -> permission.getName().name())  // Lấy tên của quyền
                .collect(Collectors.toSet());

        return new CustomUserDetails(
                user.getId(),
                user.getName(),
                user.getPassword(),
                user.getEmail(),
                authorities,
                permissions // Có thể tùy chỉnh nếu muốn lưu trữ permissions dạng khác
        );
    }

    @Override
    public boolean equals(Object o) {
        if (this == o)
            return true;
        if (o == null || getClass() != o.getClass())
            return false;
        CustomUserDetails user = (CustomUserDetails) o;
        return Objects.equals(id, user.id);
    }

    @Override
    public int hashCode() {
        return Objects.hash(id);
    }
}


// Node: getClass
package net.javaguides.order_service.paypal;

import lombok.RequiredArgsConstructor;
import org.json.JSONArray;
import org.json.JSONObject;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.Base64;

@Service
@RequiredArgsConstructor
public class PayPalService {

    @Value("${paypal.client-id}")
    public static String CLIENT_ID;

    @Value("${paypal.client-secret}")
    public static String CLIENT_SECRET;

    private static final String PAYPAL_API = "https://api.sandbox.paypal.com/v2/checkout/orders/";
    //*
    public void refundPayment(String captureId) {
       try {
           URL url = new URL("https://api.sandbox.paypal.com/v2/payments/captures/" + captureId + "/refund");
           int responseCode = getResponseCode(url);
           if (responseCode != HttpURLConnection.HTTP_CREATED) {
               throw new RuntimeException("Refund failed with response code: " + responseCode);
           }
       }catch(Exception e){
           throw new RuntimeException("Refund failed: " + e.getMessage());
       }
    }

    public String getCaptureIdFromOrder(String orderId) throws Exception {
        URL url = new URL(PAYPAL_API + orderId);
        HttpURLConnection connection = (HttpURLConnection) url.openConnection();
        connection.setRequestMethod("GET");
        connection.setRequestProperty("Authorization", "Bearer " + getAccessToken());
        connection.setRequestProperty("Content-Type", "application/json");

        int responseCode = connection.getResponseCode();
        if (responseCode == HttpURLConnection.HTTP_OK) {
            try (BufferedReader br = new BufferedReader(new InputStreamReader(connection.getInputStream(), "utf-8"))) {
                StringBuilder response = new StringBuilder();
                String responseLine;
                while ((responseLine = br.readLine()) != null) {
                    response.append(responseLine.trim());
                }

                JSONObject jsonResponse = new JSONObject(response.toString());

                JSONArray purchaseUnits = jsonResponse.getJSONArray("purchase_units");
                JSONObject payments = purchaseUnits.getJSONObject(0).getJSONObject("payments");
                if (payments.has("captures")) {
                    JSONArray captures = payments.getJSONArray("captures");
                    for (int i = 0; i < captures.length(); i++) {
                        JSONObject capture = captures.getJSONObject(i);
                        String status = capture.getString("status");
                        if ("COMPLETED".equals(status)) {
                            return capture.getString("id");
                        }
                    }
                }
            }
        } else {
            throw new RuntimeException("Failed to retrieve order details from PayPal.");
        }
        return null;
    }

    private int getResponseCode(URL url) throws Exception {
        HttpURLConnection connection = (HttpURLConnection) url.openConnection();
        connection.setRequestMethod("POST");
        connection.setRequestProperty("Content-Type", "application/json");
        connection.setRequestProperty("Authorization", "Bearer " + getAccessToken());
        connection.setDoOutput(true);

        try (OutputStream os = connection.getOutputStream()) {
            byte[] input = "{}".getBytes("utf-8");
            os.write(input, 0, input.length);
        }

        return connection.getResponseCode();
    }

    // Lấy access token
    private String getAccessToken() throws Exception {
        URL url = new URL("https://api-m.sandbox.paypal.com/v1/oauth2/token");
        String credentials = CLIENT_ID + ":" + CLIENT_SECRET;
        String authHeader = "Basic " + Base64.getEncoder().encodeToString(credentials.getBytes());

        HttpURLConnection connection = (HttpURLConnection) url.openConnection();
        connection.setRequestMethod("POST");
        connection.setRequestProperty("Authorization", authHeader);
        connection.setRequestProperty("Content-Type", "application/x-www-form-urlencoded");
        connection.setDoOutput(true);

        try (OutputStream os = connection.getOutputStream()) {
            String params = "grant_type=client_credentials";
            os.write(params.getBytes("utf-8"));
        }

        int responseCode = connection.getResponseCode();
        if (responseCode == HttpURLConnection.HTTP_OK) {
            try (BufferedReader br = new BufferedReader(new InputStreamReader(connection.getInputStream(), "utf-8"))) {
                StringBuilder response = new StringBuilder();
                String responseLine;
                while ((responseLine = br.readLine()) != null) {
                    response.append(responseLine.trim());
                }
                JSONObject jsonResponse = new JSONObject(response.toString());
                return jsonResponse.getString("access_token");
            }
        } else {
            throw new RuntimeException("Failed to get access token.");
        }
    }
}


// Node: repos/cloned_ms_repos/springboot-kafka-microservices/order-service/src/main/java/net/javaguides/order_service/paypal/PayPalService.java:PayPalService.<init>
// Node: Value
package net.javaguides.order_service.kafka;

import net.javaguides.common_lib.dto.order.OrderEvent;
import org.apache.kafka.clients.admin.NewTopic;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.kafka.support.KafkaHeaders;
import org.springframework.messaging.Message;
import org.springframework.messaging.support.MessageBuilder;
import org.springframework.stereotype.Service;

@Service
public class OrderProducer {
    private static final Logger LOGGER = LoggerFactory.getLogger(OrderProducer.class);
    private NewTopic topic;
    private KafkaTemplate<String, OrderEvent> kafkaTemplate;

    public OrderProducer(NewTopic topic, KafkaTemplate<String, OrderEvent> kafkaTemplate) {
        this.topic = topic;
        this.kafkaTemplate = kafkaTemplate;
    }

    public void sendMessage(OrderEvent orderEvent){
        LOGGER.info(String.format("OrderDTO event => %s", orderEvent.toString()));


        //create message
        Message<OrderEvent> message = MessageBuilder.withPayload(orderEvent)
                .setHeader(KafkaHeaders.TOPIC, topic.name())
                .build();
        kafkaTemplate.send(message);
    }
}


// Node: repos/cloned_ms_repos/springboot-kafka-microservices/order-service/src/main/java/net/javaguides/order_service/kafka/OrderProducer.java:OrderProducer.<init>
// Node: getLogger
// Node: OrderProducer
package net.javaguides.order_service.service.impl;


import jakarta.persistence.OptimisticLockException;
import lombok.RequiredArgsConstructor;
import net.javaguides.common_lib.dto.ApiResponse;
import net.javaguides.common_lib.dto.order.OrderDTO;
import net.javaguides.common_lib.dto.order.OrderEvent;
import net.javaguides.common_lib.dto.order.OrderItemDTO;
import net.javaguides.common_lib.dto.product.ProductDTO;
import net.javaguides.order_service.dto.*;
import net.javaguides.order_service.dto.attribute_value.AttributeValueResponseDto;
import net.javaguides.order_service.dto.product.ProductResponseDto;
import net.javaguides.order_service.dto.product_variant.ProductVariantResponseDto;
import net.javaguides.order_service.entity.Order;
import net.javaguides.order_service.entity.OrderItem;
import net.javaguides.order_service.entity.OrderStatus;
import net.javaguides.order_service.exception.OrderException;
import net.javaguides.order_service.kafka.OrderProducer;
import net.javaguides.order_service.paypal.PayPalService;
import net.javaguides.order_service.redis.OrderRedis;
import net.javaguides.order_service.repository.OrderRepository;
import net.javaguides.order_service.service.OrderService;
import net.javaguides.order_service.service.PaymentAPIClient;
import net.javaguides.order_service.service.ProductAPIClient;

import net.javaguides.order_service.service.state.OrderContext;
import org.modelmapper.ModelMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import java.util.function.Function;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class OrderServiceImpl implements OrderService {
    private static final Logger LOGGER = LoggerFactory.getLogger(OrderServiceImpl.class);

    private final OrderProducer orderProducer;
    private final OrderRepository orderRepository;
    private final ModelMapper modelMapper;
    private final ProductAPIClient productAPIClient;
    private final PaymentAPIClient paymentAPIClient;
    private final PayPalService payPalService;
    private final OrderRedis orderRedis;

    @Override
    @Transactional
    public OrderDTO placeOrder(OrderRequestDto orderRequestDto, Long userId, String email) {
        try {
            if(orderRequestDto.getPaymentMethod().equals("Paypal") && orderRequestDto.getOrderId() == null){
                throw new OrderException("Please provide Paypal's ID", HttpStatus.BAD_REQUEST);
            }

            OrderDTO newOrder = createOrderDTO(orderRequestDto, userId);
            validateStockAndPrice(orderRequestDto, newOrder);

            Order createdOrder = saveOrder(newOrder, orderRequestDto);
            orderRedis.save(modelMapper.map(createdOrder, OrderDTO.class));


            sendOrderEvent(createdOrder, orderRequestDto.getPaymentMethod(), email);

            return modelMapper.map(createdOrder, OrderDTO.class);
        } catch (OrderException e) {
            throw e;
        } catch (Exception e) {
            LOGGER.error("Failed to create order: {}", e.getMessage(), e);
            throw new OrderException("Failed to create order: " + e.getMessage(), HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }

    @Override
    public OrderResponseDto checkOrderStatusByOrderId(String orderId) {
        // Kiểm tra từ Redis cache
        OrderDTO cachedOrder = orderRedis.findByOrderId(orderId);
        OrderDTO order;

        if (cachedOrder != null) {
            order = cachedOrder;
            LOGGER.info("Order retrieved from Redis cache.");
        } else {
            // Nếu không tìm thấy trong cache, truy vấn cơ sở dữ liệu và lưu vào cache
            order = modelMapper.map(orderRepository.findById(orderId).orElse(null), OrderDTO.class);
            if (order != null) {
                orderRedis.save(order);
                LOGGER.info("Order retrieved from DB and saved to Redis cache.");
            }
        }

        if (order != null) {
            OrderDTO orderDTO = modelMapper.map(order, OrderDTO.class);
            PaymentDto paymentDto = paymentAPIClient.getPaymentByOrderId(orderId).getBody().getData();

            OrderResponseDto orderResponseDto = new OrderResponseDto();
            orderResponseDto.setOrderDTO(orderDTO);
            orderResponseDto.setPaymentDto(paymentDto);

            return orderResponseDto;
        }
        return null;
    }


    @Override
    public OrderResponseDto updateOrderStatus(String orderId, int version) {
        Order order = orderRepository.findById(orderId).orElse(null);
        if (order != null) {
            if (order.getVersion() != version) {
                throw new OptimisticLockException("Version conflict!");
            }

            OrderContext context = new OrderContext(order);
            context.handleStateChange(order);

            Order savedOrder = orderRepository.save(order);
            OrderDTO orderDTO = modelMapper.map(savedOrder, OrderDTO.class);

            // Cập nhật cache Redis
            orderRedis.save(orderDTO);

            PaymentDto paymentDto = paymentAPIClient.getPaymentByOrderId(orderId).getBody().getData();

            OrderResponseDto orderResponseDto = new OrderResponseDto();
            orderResponseDto.setOrderDTO(orderDTO);
            orderResponseDto.setPaymentDto(paymentDto);
            return orderResponseDto;
        }
        return null;
    }


    //* Pre Authorized: ADMINISTRATOR, EMPLOYEE
    @Override
    public OrderDTO cancelOrder(String orderId, Long userId) {
        Order order = orderRepository.findById(orderId).orElse(null);
        if (order != null) {
            order.setStatus(OrderStatus.CANCELED.getLabel());
            ApiResponse<PaymentDto> paymentDto = paymentAPIClient.getPaymentByOrderId(orderId).getBody();
            if(paymentDto != null && paymentDto.getData() != null && paymentDto.getData().getStatus().equals("Paypal")){
                try {
                    String captureId = payPalService.getCaptureIdFromOrder(orderId);
                    if(captureId != null){
                        sendRefundOrderEvent(order);
                        payPalService.refundPayment(captureId);
                    }
                }catch(Exception e){
                    throw new OrderException("No captures found for this order. Refund cannot be processed.", HttpStatus.BAD_REQUEST);
                }
            }
            OrderDTO savedOrderDTO = modelMapper.map(orderRepository.save(order), OrderDTO.class);
            orderRedis.save(savedOrderDTO);
            return savedOrderDTO;
        }
        return null;
    }

    @Override
    public List<OrderResponseDtoWithOutOrderItems> getAllOrders(Long userId, int page, int size) {
        Page<Order> orderPage = orderRepository.findByUserId(userId, PageRequest.of(page, size));
        return orderPage.stream().map(order -> {
            // Lấy đơn hàng từ cache nếu có
            OrderDTO cachedOrder = orderRedis.findByOrderId(order.getOrderId());
            OrderWithOutOrderItems orderDTO = modelMapper.map(order, OrderWithOutOrderItems.class);
            if (cachedOrder == null) {
                // Nếu không có trong cache, lưu vào cache
                orderRedis.save(modelMapper.map(order, OrderDTO.class));
            }
            PaymentDto paymentDto = paymentAPIClient.getPaymentByOrderId(order.getOrderId()).getBody().getData();
            return new OrderResponseDtoWithOutOrderItems(orderDTO, paymentDto);
        }).collect(Collectors.toList());
    }


    private OrderEvent createOrderEvent(Order createdOrder, String paymentMethod, String email) {
        OrderDTO createdOrderDto = modelMapper.map(createdOrder, OrderDTO.class);
        OrderEvent orderEvent = new OrderEvent();
        orderEvent.setOrderDTO(createdOrderDto);
        orderEvent.setStatus("PENDING");
        orderEvent.setMessage("Order status is in pending state");
        orderEvent.setPaymentMethod(paymentMethod);
        orderEvent.setEmail(email);
        return orderEvent;
    }

    private OrderDTO createOrderDTO(OrderRequestDto orderRequestDto, Long userId) {
        OrderDTO newOrder = modelMapper.map(orderRequestDto, OrderDTO.class);
        newOrder.setUserId(userId);
        return newOrder;
    }


    private void validateStockAndPrice(OrderRequestDto orderRequestDTO, OrderDTO newOrder) {
        Set<String> productIds = extractProductIds(orderRequestDTO.getOrderItems());
        List<ProductResponseDto> products = fetchProducts(productIds);

        if (products.size() != productIds.size()) {
            throw new OrderException("Variants not found for ids: " + productIds, HttpStatus.BAD_REQUEST);
        }

        Map<String, ProductResponseDto> productsMap = products.stream()
                .collect(Collectors.toMap(ProductResponseDto::getId, Function.identity()));

        for (OrderItemDTO orderItem : orderRequestDTO.getOrderItems()) {
            ProductResponseDto product = productsMap.get(orderItem.getProductId());
            if (product == null) {
                throw new OrderException("Not found product!", HttpStatus.NOT_FOUND);
            }

            //* UPDATE PRICE AND VALIDATE STOCK
            updatePriceAndValidateStock(orderItem, product);
        }
    }

    private Set<String> extractProductIds(List<OrderItemDTO> orderItems) {
        return orderItems.stream()
                .map(OrderItemDTO::getProductId)
                .collect(Collectors.toSet());
    }

    private List<ProductResponseDto> fetchProducts(Set<String> productIds) {
        return productAPIClient.getProductsByIds(productIds).getBody().getData();
    }

    private void updatePriceAndValidateStock(OrderItemDTO orderItem, ProductResponseDto product) {
        ProductVariantResponseDto selectedVariant = findMatchingVariant(product.getVariants(), orderItem.getVariantId());
        if (selectedVariant != null) {
            if (selectedVariant.getStockQuantity() < orderItem.getQuantity()) {
                throw new OrderException("Insufficient stock for variantId: " + selectedVariant.getId(), HttpStatus.BAD_REQUEST);
            }
            if(selectedVariant.getPrice() != null){
                orderItem.setPrice(selectedVariant.getPrice());
                return;
            }
            orderItem.setPrice(product.getPrice());
        }
    }

    private ProductVariantResponseDto findMatchingVariant(List<ProductVariantResponseDto> variants, Long variantId) {
        if (variants == null) return null;
        return variants.stream()
                .filter(v -> v.getId().equals(variantId))
                .findFirst()
                .orElse(null);
    }

    private Order saveOrder(OrderDTO newOrder, OrderRequestDto orderRequestDto) {
        Order order = modelMapper.map(newOrder, Order.class);
        if ("Paypal".equalsIgnoreCase(orderRequestDto.getPaymentMethod())) {
            BigDecimal amount = BigDecimal.valueOf(0);

            for (OrderItemDTO orderItemDTO : orderRequestDto.getOrderItems()) {
                BigDecimal itemTotal = orderItemDTO.getPrice().multiply(BigDecimal.valueOf(orderItemDTO.getQuantity()));
                amount = amount.add(itemTotal);
            }
            order.setOrderId(orderRequestDto.getOrderId());
        } else {
            order.setOrderId(UUID.randomUUID().toString());
        }
        order.setStatus(OrderStatus.PENDING.getLabel());
        for (OrderItem orderItem : order.getOrderItems()) {
            orderItem.setOrder(order);
        }
        return orderRepository.save(order);
    }

    private void sendOrderEvent(Order createdOrder, String paymentMethod, String email) {
        OrderEvent orderEvent = createOrderEvent(createdOrder, paymentMethod, email);
        orderProducer.sendMessage(orderEvent);
    }

    // ! This method is deprecated.
//    private OrderResponseDto createOrderResponseDto(Order createdOrder, OrderRequestDto orderRequestDto) {
//        OrderResponseDto orderResponseDto = new OrderResponseDto();
//        PaymentDto paymentDto = paymentAPIClient.getPaymentByOrderId(createdOrder.getOrderId()).getBody().getData();
//        OrderDTO createdOrderDto = modelMapper.map(createdOrder, OrderDTO.class);
//        orderResponseDto.setPaymentDto(paymentDto);
//        orderResponseDto.setOrderDTO(createdOrderDto);
//        LOGGER.info("Order created successfully with ID: {}", createdOrder.getOrderId());
//        return orderResponseDto;
//    }

    private void sendRefundOrderEvent(Order order){
        OrderEvent orderEvent = new OrderEvent();
        OrderDTO orderDTO = modelMapper.map(order, OrderDTO.class);
        orderEvent.setOrderDTO(orderDTO);
        orderEvent.setMessage("REFUND");
    }

}


// Node: repos/cloned_ms_repos/springboot-kafka-microservices/order-service/src/main/java/net/javaguides/order_service/service/impl/OrderServiceImpl.java:OrderServiceImpl.<init>
package net.javaguides.order_service.config;

import org.apache.kafka.clients.admin.NewTopic;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.kafka.config.TopicBuilder;

@Configuration
public class KafkaTopicConfig {

    @Value("${spring.kafka.topic.name}")
    private String orderTopic;

    @Value("${spring.kafka.create-order-topic.name}")
    private String createOrderTopic;

    //spring bean for kafka topic
    @Bean
    public NewTopic createOrderTopic(){
        return TopicBuilder.name(createOrderTopic).build();
    }
}


// Node: repos/cloned_ms_repos/springboot-kafka-microservices/order-service/src/main/java/net/javaguides/order_service/config/KafkaTopicConfig.java:KafkaTopicConfig.<init>
package net.javaguides.order_service.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.redis.connection.RedisStandaloneConfiguration;
import org.springframework.data.redis.connection.jedis.JedisConnectionFactory;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.data.redis.repository.configuration.EnableRedisRepositories;
import org.springframework.data.redis.serializer.GenericJackson2JsonRedisSerializer;
import org.springframework.data.redis.serializer.StringRedisSerializer;

import java.time.Duration;

@Configuration
@EnableRedisRepositories
public class RedisConfig {
    @Value("${spring.redis.host}")
    private String redisHost;

    @Value("${spring.redis.port}")
    private int redisPort;

    @Bean
    public JedisConnectionFactory connectionFactory(){
        RedisStandaloneConfiguration configuration = new RedisStandaloneConfiguration();
        configuration.setPort(redisPort);
        configuration.setHostName(redisHost);
        return new JedisConnectionFactory(configuration);
    }

    @Bean
    public RedisTemplate<String, Object> redisTemplate() {
        RedisTemplate<String, Object> template = new RedisTemplate<>();
        template.setConnectionFactory(connectionFactory());
        template.setKeySerializer(new StringRedisSerializer());
        template.setValueSerializer(new GenericJackson2JsonRedisSerializer()); // Using JSON serialization
        template.setHashKeySerializer(new StringRedisSerializer());
        template.setHashValueSerializer(new GenericJackson2JsonRedisSerializer()); // Using JSON serialization
        template.setEnableTransactionSupport(true);
        template.afterPropertiesSet();
        return template;
    }

}

// Node: repos/cloned_ms_repos/springboot-kafka-microservices/order-service/src/main/java/net/javaguides/order_service/config/RedisConfig.java:RedisConfig.<init>
package net.javaguides.email_service.kafka;


import net.javaguides.common_lib.dto.order.OrderEvent;
import net.javaguides.email_service.service.EmailService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Service;

@Service
public class OrderConsumer {
    private static final Logger LOGGER = LoggerFactory.getLogger(OrderConsumer.class);

    @Autowired
    private EmailService emailService;


    @KafkaListener(topics = "${spring.kafka.order-topic.name}",
            groupId = "${spring.kafka.consumer.group-id}")
    public void consume(OrderEvent orderEvent){
        try {
            LOGGER.info(String.format("OrderDTO event received in payment service -> %s", orderEvent.toString()));

            emailService.sendOrderConfirmationEmail(orderEvent);

        }catch(Exception e){
            LOGGER.warn(String.format("Error message -> %s", e.getMessage()));
        }
    }
}


// Node: repos/cloned_ms_repos/springboot-kafka-microservices/email-service/src/main/java/net/javaguides/email_service/kafka/OrderConsumer.java:OrderConsumer.<init>
// Node: KafkaListener
package net.javaguides.email_service.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.mail.javamail.JavaMailSenderImpl;

import java.util.Properties;

@Configuration
public class MailConfig {
    @Value("${spring.mail.host}")
    private String SMTP_HOST;

    @Value("${spring.mail.port}")
    private int SMTP_PORT;

    @Value("${spring.mail.username}")
    private String SMTP_USERNAME;

    @Value("${spring.mail.password}")
    private String SMTP_PASSWORD;


    @Bean
    public JavaMailSender javaMailSender() {
        JavaMailSenderImpl mailSender = new JavaMailSenderImpl();
        mailSender.setHost(SMTP_HOST);
        mailSender.setPort(SMTP_PORT);

        mailSender.setUsername(SMTP_USERNAME);
        mailSender.setPassword(SMTP_PASSWORD);

        Properties props = mailSender.getJavaMailProperties();
        props.put("mail.transport.protocol", "smtp");
        props.put("mail.smtp.auth", "true");
        props.put("mail.smtp.starttls.enable", "true");
        props.put("mail.debug", "true"); // If you want to see the debug output

        return mailSender;
    }
}


// Node: repos/cloned_ms_repos/springboot-kafka-microservices/email-service/src/main/java/net/javaguides/email_service/config/MailConfig.java:MailConfig.<init>
package net.javaguides.product_service.kafka.producer;

import net.javaguides.common_lib.dto.product.ProductEvent;

import org.apache.kafka.clients.admin.NewTopic;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.kafka.support.KafkaHeaders;
import org.springframework.messaging.Message;
import org.springframework.messaging.support.MessageBuilder;
import org.springframework.stereotype.Service;

@Service
public class ProductProducer {
    private static final Logger LOGGER = LoggerFactory.getLogger(ProductProducer.class);
    private NewTopic topic;
    private KafkaTemplate<String, ProductEvent> kafkaTemplate;

    public ProductProducer(NewTopic topic, KafkaTemplate<String, ProductEvent> kafkaTemplate) {
        this.topic = topic;
        this.kafkaTemplate = kafkaTemplate;
    }

    public void sendMessage(ProductEvent productEvent){
        LOGGER.info(String.format("ProductDTO event => %s", productEvent.toString()));


        //create message
        Message<ProductEvent> message = MessageBuilder.withPayload(productEvent)
                .setHeader(KafkaHeaders.TOPIC, topic.name())
                .build();
        kafkaTemplate.send(message);
    }

    public void sendDeleteProductMessage(ProductEvent productEvent){
        Message<ProductEvent> message = MessageBuilder.withPayload(productEvent)
                        .setHeader(KafkaHeaders.TOPIC, topic.name())
                                .build();
        kafkaTemplate.send(message);
    }
}


// Node: repos/cloned_ms_repos/springboot-kafka-microservices/product-service/src/main/java/net/javaguides/product_service/kafka/producer/ProductProducer.java:ProductProducer.<init>
// Node: ProductProducer
package net.javaguides.product_service.kafka.consumer;

import lombok.RequiredArgsConstructor;
import net.javaguides.common_lib.dto.order.OrderDTO;
import net.javaguides.common_lib.dto.order.OrderEvent;
import net.javaguides.common_lib.dto.order.OrderItemDTO;
import net.javaguides.product_service.entity.ProductVariant;
import net.javaguides.product_service.exception.InsufficientStockException;
import net.javaguides.product_service.service.ProductVariantService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;

@Component
@RequiredArgsConstructor
public class OrderConsumer {

    private static final Logger LOGGER = LoggerFactory.getLogger(OrderConsumer.class);

    private final ProductVariantService productVariantService;

    @KafkaListener(topics = "${spring.kafka.create-order-topic.name}", groupId = "${spring.kafka.consumer.group-id}")
    @Transactional
    public void consume(OrderEvent orderEvent) {
        LOGGER.info("Received OrderEvent: {}", orderEvent);

        OrderDTO orderDTO = orderEvent.getOrderDTO();
        Set<Long> variantIds = orderDTO.getOrderItems().stream()
                .map(OrderItemDTO::getVariantId)
                .collect(Collectors.toSet());

        // Lấy danh sách các ProductVariant theo variantIds
        Map<Long, ProductVariant> variantMap = productVariantService.getProductVariantByIds(variantIds).stream()
                .collect(Collectors.toMap(ProductVariant::getId, variant -> variant));

        // Cập nhật tồn kho sản phẩm
        for (OrderItemDTO orderItem : orderDTO.getOrderItems()) {
            updateStockForVariant(orderItem, variantMap);
        }

        LOGGER.info("Successfully processed OrderEvent for orderId: {}", orderDTO.getOrderId());
    }

    private void updateStockForVariant(OrderItemDTO orderItem, Map<Long, ProductVariant> variantMap) {
        Long variantId = orderItem.getVariantId();
        ProductVariant productVariant = variantMap.get(variantId);

        if (productVariant == null) {
            LOGGER.error("ProductVariant with id {} not found.", variantId);
            throw new RuntimeException("ProductVariant with id " + variantId + " not found.");
        }

        int requiredQuantity = orderItem.getQuantity();
        int currentStock = productVariant.getStockQuantity();
        int updatedStock = currentStock - requiredQuantity;

        if (updatedStock < 0) {
            LOGGER.error("Insufficient stock for variant {}. Required: {}, Available: {}", variantId, requiredQuantity, currentStock);
            throw new InsufficientStockException("Insufficient stock for variant " + variantId);
        }

        productVariant.setStockQuantity(updatedStock);
        productVariantService.saveProductVariant(productVariant);

        LOGGER.info("Updated stock for variant {}. New stock: {}", variantId, updatedStock);
    }
}


// Node: repos/cloned_ms_repos/springboot-kafka-microservices/product-service/src/main/java/net/javaguides/product_service/kafka/consumer/OrderConsumer.java:OrderConsumer.<init>
package net.javaguides.product_service.service.impl;

import lombok.RequiredArgsConstructor;
import net.javaguides.common_lib.dto.product.ProductDTO;
import net.javaguides.common_lib.dto.product.ProductEvent;
import net.javaguides.common_lib.dto.product.ProductMethod;
import net.javaguides.product_service.dto.*;
import net.javaguides.product_service.dto.product.CreateProductRequestDto;
import net.javaguides.product_service.dto.product.ProductCacheDto;
import net.javaguides.product_service.dto.product.ProductResponseDto;
import net.javaguides.product_service.dto.product.UpdateProductRequestDto;
import net.javaguides.product_service.redis.ProductRedis;
import net.javaguides.product_service.entity.Product;
import net.javaguides.product_service.exception.ProductException;
import net.javaguides.product_service.kafka.producer.ProductProducer;
import net.javaguides.product_service.repository.ProductRepository;
import net.javaguides.product_service.service.CloudinaryService;
import net.javaguides.product_service.service.ProductService;
import net.javaguides.product_service.specification.ProductSpecification;
import org.modelmapper.ModelMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

import java.math.BigDecimal;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.UUID;

import java.util.stream.Collector;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class ProductServiceImpl implements ProductService {
    private static final Logger LOGGER = LoggerFactory.getLogger(ProductServiceImpl.class);
    private final ProductProducer productProducer;
    private final ProductRepository productRepository;
    private final ModelMapper modelMapper;
    private final ProductRedis productDAO;
    private final CloudinaryService cloudinaryService;

    @Value("${cloudinary.cloud_name}")
    private String cloudName;

    public String getFileExtension(MultipartFile file) {
        String originalFilename = file.getOriginalFilename();
        if (originalFilename != null && originalFilename.contains(".")) {
            return originalFilename.substring(originalFilename.lastIndexOf(".") + 1);
        } else {
            return "";
        }
    }
    @Override
    @Transactional
    public ProductResponseDto saveProduct(CreateProductRequestDto createProductRequestDto) {
        try {
            String publicId = System.currentTimeMillis() + "_" + createProductRequestDto.getMultipartFile().getOriginalFilename().replace(".jpg", "");
            String preUrl = "https://res.cloudinary.com/" + cloudName + "/image/upload/" + publicId + "." + getFileExtension(createProductRequestDto.getMultipartFile());

            // Map DTO sang Product entity
            Product product = modelMapper.map(createProductRequestDto, Product.class);
            product.setId(UUID.randomUUID().toString());
            product.setImageUrl(preUrl);
            Product savedProduct = productRepository.save(product);

            // Lưu sản phẩm vào cache
            productDAO.save(savedProduct);

            // Upload ảnh lên Cloudinary (nên thực hiện sau khi lưu sản phẩm thành công)
            cloudinaryService.uploadFile(createProductRequestDto.getMultipartFile(), publicId);

            return modelMapper.map(savedProduct, ProductResponseDto.class);
        } catch (Exception e) {
            throw new ProductException("Failed to create product: " + e.getMessage(), HttpStatus.BAD_REQUEST);
        }
    }



    @Override
    public ProductResponseDto getProductById(String id) {
        ProductCacheDto cachedProduct = productDAO.findByProductId(id);

        if (cachedProduct != null) {
            LOGGER.info("Cache hit for product id: {}", id);
            return modelMapper.map(cachedProduct, ProductResponseDto.class);
        } else {
            LOGGER.info("Cache miss for product id: {}", id);
            Product product = productRepository.findById(id)
                    .orElseThrow(() -> new ProductException("Product not found with id: " + id, HttpStatus.NOT_FOUND));

            productDAO.save(product);

            return modelMapper.map(product, ProductResponseDto.class);
        }
    }




    @Override
    public Page<ProductResponseDto> getProductList(int page, int size) {
        Page<Product> productPage = productRepository.findAll(PageRequest.of(page, size));

        List<ProductResponseDto> productDtos = productPage.getContent()
                .stream()
                .map(product -> {
                    ProductCacheDto cachedProduct = productDAO.findByProductId(product.getId());

                    if(cachedProduct == null){
                       productDAO.save(product);
                    }
                    return modelMapper.map(product, ProductResponseDto.class);
                })
                .collect(Collectors.toList());

        return new PageImpl<>(productDtos, PageRequest.of(page, size), productPage.getTotalElements());

    }

    @Override
    public ProductResponseDto updateProduct(String id, UpdateProductRequestDto productUpdateDto, int version) {
        return productRepository.findById(id)
                .map(existingProduct -> {
                    if (existingProduct.getVersion() != version) {
                        throw new ProductException("Version conflict! Current version: "
                                + existingProduct.getVersion(), HttpStatus.CONFLICT);
                    }

                    modelMapper.map(productUpdateDto, existingProduct);

                    Product savedProduct = productRepository.save(existingProduct);

                    // Cập nhật sản phẩm trong cache
                    productDAO.save(savedProduct);

                    return modelMapper.map(savedProduct, ProductResponseDto.class);
                })
                .orElseThrow(() -> new ProductException("Product not found with id: " + id, HttpStatus.NOT_FOUND));
    }



    @Override
    public void deleteProduct(String id) {
        Product existingProduct = productRepository.findById(id)
                .orElseThrow(() -> new ProductException("Product not found with ID: " + id, HttpStatus.NOT_FOUND));

        productRepository.delete(existingProduct);

        // Xóa sản phẩm khỏi cache
        productDAO.deleteByProductId(id);
    }


    @Override
    public List<ProductResponseDto> getProductsByIds(Set<String> productIds) {
        return productRepository.findAllByIdIn(productIds)
                .stream()
                .map(product -> modelMapper.map(product, ProductResponseDto.class))
                .collect(Collectors.toList());
    }

    @Override
    public Page<ProductResponseDto> searchProducts(String name, String categoryId, BigDecimal minPrice, BigDecimal maxPrice, Pageable pageable) {
        Specification<Product> spec = Specification.where(null);

        if (name != null && !name.isEmpty()) {
            spec = spec.and(ProductSpecification.hasName(name));
        }

        if (categoryId != null && !categoryId.isEmpty()) {
            spec = spec.and(ProductSpecification.inCategory(categoryId));
        }

        if (minPrice != null && maxPrice != null) {
            spec = spec.and(ProductSpecification.hasPriceBetween(minPrice, maxPrice));
        }

        Page<Product> products = productRepository.findAll(spec, pageable);

        // Sử dụng map() của Page để chuyển đổi từng Product thành ProductResponseDto
        return products.map(product -> modelMapper.map(product, ProductResponseDto.class));
    }



    // Private Helper Methods
    private Product mapToEntity(ProductDTO productDTO) {
        return modelMapper.map(productDTO, Product.class);
    }

    private ProductEvent createProductEvent(Product product, int stockQuantity, ProductMethod method) {
        ProductDTO productDTO = modelMapper.map(product, ProductDTO.class);
        productDTO.setStockQuantity(stockQuantity);

        ProductEvent productEvent = new ProductEvent();
        productEvent.setProductDTO(productDTO);
        productEvent.setMethod(method);
        return productEvent;
    }

    private ProductEvent createProductEvent(ProductDTO productDTO, ProductMethod method) {
        ProductEvent productEvent = new ProductEvent();
        productEvent.setProductDTO(productDTO);
        productEvent.setMethod(method);
        return productEvent;
    }


    private ProductStockResponse buildProductStockResponse(ProductResponseDto productDto) {
        ProductStockResponse response = new ProductStockResponse();
        response.setProduct(productDto);
        return response;
    }

    private ProductResponseDto updateAndSaveProduct(Product existingProduct, UpdateProductRequestDto productUpdateDto) {
        modelMapper.map(productUpdateDto, existingProduct);

        Product savedProduct = productRepository.save(existingProduct);
        ProductEvent productEvent = createProductEvent(savedProduct, productUpdateDto.getStockQuantity(), ProductMethod.UPDATE);
        productProducer.sendMessage(productEvent);

        return modelMapper.map(savedProduct, ProductResponseDto.class);
    }


    private void insertProductToCache(Product product) {
        productDAO.save(product);
        LOGGER.info("ProductServiceImpl.getProductById(): cache insert >> " + product.getId());
    }

}


// Node: repos/cloned_ms_repos/springboot-kafka-microservices/product-service/src/main/java/net/javaguides/product_service/service/impl/ProductServiceImpl.java:ProductServiceImpl.<init>
package net.javaguides.product_service.aspect;

import org.aspectj.lang.annotation.Aspect;
import org.aspectj.lang.annotation.Before;
import org.aspectj.lang.JoinPoint;
import org.aspectj.lang.annotation.AfterReturning;
import org.aspectj.lang.annotation.AfterThrowing;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

@Aspect
@Component
public class LoggingAspect {

    private final Logger log = LoggerFactory.getLogger(this.getClass());

    // Ghi log trước khi các method trong các service được thực thi
    @Before("execution(* net.javaguides.product_service.service.impl.*.*(..))")
    public void logBeforeMethod(JoinPoint joinPoint) {
        log.info("Starting method: " + joinPoint.getSignature().getName());
    }

    // Ghi log sau khi các method hoàn thành
    @AfterReturning(pointcut = "execution(* net.javaguides.product_service.service.impl.*.*(..))", returning = "result")
    public void logAfterReturning(JoinPoint joinPoint, Object result) {
        log.info("Completed method: " + joinPoint.getSignature().getName() + " with result: " + result);
    }

    // Ghi log khi có exception
    @AfterThrowing(pointcut = "execution(* net.javaguides.product_service.service.impl.*.*(..))", throwing = "error")
    public void logAfterThrowing(JoinPoint joinPoint, Throwable error) {
        log.error("Exception in method: " + joinPoint.getSignature().getName() + " with cause: " + error.getMessage());
    }
}


// Node: repos/cloned_ms_repos/springboot-kafka-microservices/product-service/src/main/java/net/javaguides/product_service/aspect/LoggingAspect.java:LoggingAspect.<init>
// Node: Before
// Node: execution
// Node: logBeforeMethod
// Node: getSignature
// Node: AfterReturning
// Node: logAfterReturning
// Node: AfterThrowing
// Node: logAfterThrowing
package net.javaguides.product_service.config;

import org.apache.kafka.clients.admin.NewTopic;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.kafka.config.TopicBuilder;

@Configuration
public class KafkaTopicConfig {
    @Value("${spring.kafka.topic.name}")
    private String topicName;

    @Bean
    public NewTopic topic(){
        return TopicBuilder.name(topicName).build();
    }
}


// Node: repos/cloned_ms_repos/springboot-kafka-microservices/product-service/src/main/java/net/javaguides/product_service/config/KafkaTopicConfig.java:KafkaTopicConfig.<init>
package net.javaguides.product_service.config;

import net.javaguides.product_service.dto.product.ProductCacheDto;
import net.javaguides.product_service.entity.Product;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.redis.connection.RedisStandaloneConfiguration;
import org.springframework.data.redis.connection.jedis.JedisConnectionFactory;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.data.redis.repository.configuration.EnableRedisRepositories;
import org.springframework.data.redis.serializer.GenericJackson2JsonRedisSerializer;
import org.springframework.data.redis.serializer.JdkSerializationRedisSerializer;
import org.springframework.data.redis.serializer.StringRedisSerializer;
import redis.clients.jedis.JedisPool;
import redis.clients.jedis.JedisPoolConfig;

import java.time.Duration;

@Configuration
@EnableRedisRepositories
public class RedisConfig {
    @Value("${spring.redis.host}")
    private String redisHost;

    @Value("${spring.redis.port}")
    private int redisPort;

    @Bean
    public JedisConnectionFactory connectionFactory(){
        RedisStandaloneConfiguration configuration = new RedisStandaloneConfiguration();
        configuration.setPort(redisPort);
        configuration.setHostName(redisHost);
        return new JedisConnectionFactory(configuration);
    }

    @Bean
    public RedisTemplate<String, ProductCacheDto> redisTemplate() {
        RedisTemplate<String, ProductCacheDto> template = new RedisTemplate<>();
        template.setConnectionFactory(connectionFactory());
        // Thiết lập serializer cho key và value
        template.setKeySerializer(new StringRedisSerializer());
        template.setValueSerializer(new GenericJackson2JsonRedisSerializer()); // Using JSON serialization
        template.setHashKeySerializer(new StringRedisSerializer());
        template.setHashValueSerializer(new GenericJackson2JsonRedisSerializer()); // Using JSON serialization

        template.setEnableTransactionSupport(true);
        template.afterPropertiesSet();
        return template;
    }

}

// Node: repos/cloned_ms_repos/springboot-kafka-microservices/product-service/src/main/java/net/javaguides/product_service/config/RedisConfig.java:RedisConfig.<init>
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

// Node: repos/cloned_ms_repos/springboot-kafka-microservices/product-service/src/main/java/net/javaguides/product_service/config/CloudinaryConfig.java:CloudinaryConfig.<init>
package net.javaguides.payment_service.kafka;


import net.javaguides.common_lib.dto.order.OrderEvent;
import net.javaguides.payment_service.entity.PaymentStatus;
import net.javaguides.payment_service.service.PaymentService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Service;

@Service
public class OrderConsumer {
    private static final Logger LOGGER = LoggerFactory.getLogger(OrderConsumer.class);
    private final PaymentService paymentService;

    public OrderConsumer(PaymentService paymentService) {
        this.paymentService = paymentService;
    }


    @KafkaListener(topics = "${spring.kafka.order-topic.name}",
            groupId = "${spring.kafka.consumer.group-id}")
    public void consume(OrderEvent orderEvent){
        try {
            LOGGER.info(String.format("OrderDTO event received in payment service -> %s", orderEvent.toString()));

            if(orderEvent.getMessage().equals("REFUND")){
                paymentService.refundPayment(orderEvent.getOrderDTO().getOrderId());
                return;
            }

            if(orderEvent.getMessage().equals("PAID")){
                paymentService.updateStatusPayment(orderEvent.getOrderDTO().getOrderId(), PaymentStatus.SUCCESS);
                return;
            }

            paymentService.createPayment(orderEvent);

        }catch(Exception e){
           LOGGER.warn(String.format("Error message -> %s", e.getMessage()));
        }
    }
}


// Node: repos/cloned_ms_repos/springboot-kafka-microservices/payment-service/src/main/java/net/javaguides/payment_service/kafka/OrderConsumer.java:OrderConsumer.<init>
// Node: OrderConsumer
package net.javaguides.payment_service.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.redis.connection.RedisStandaloneConfiguration;
import org.springframework.data.redis.connection.jedis.JedisConnectionFactory;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.data.redis.repository.configuration.EnableRedisRepositories;
import org.springframework.data.redis.serializer.GenericJackson2JsonRedisSerializer;
import org.springframework.data.redis.serializer.StringRedisSerializer;

@Configuration
@EnableRedisRepositories
public class RedisConfig {
    @Value("${spring.redis.host}")
    private String redisHost;

    @Value("${spring.redis.port}")
    private int redisPort;

    @Bean
    public JedisConnectionFactory connectionFactory(){
        RedisStandaloneConfiguration configuration = new RedisStandaloneConfiguration();
        configuration.setPort(redisPort);
        configuration.setHostName(redisHost);
        return new JedisConnectionFactory(configuration);
    }

    @Bean
    public RedisTemplate<String, Object> redisTemplate() {
        RedisTemplate<String, Object> template = new RedisTemplate<>();
        template.setConnectionFactory(connectionFactory());
        template.setKeySerializer(new StringRedisSerializer());
        template.setValueSerializer(new GenericJackson2JsonRedisSerializer()); // Using JSON serialization
        template.setHashKeySerializer(new StringRedisSerializer());
        template.setHashValueSerializer(new GenericJackson2JsonRedisSerializer()); // Using JSON serialization
        template.setEnableTransactionSupport(true);
        template.afterPropertiesSet();
        return template;
    }

}

// Node: repos/cloned_ms_repos/springboot-kafka-microservices/payment-service/src/main/java/net/javaguides/payment_service/config/RedisConfig.java:RedisConfig.<init>
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


// Node: repos/cloned_ms_repos/springboot-kafka-microservices/api-gateway/src/main/java/net/javaguides/api_gateway/filter/RoleBasedAccessFilter.java:RoleBasedAccessFilter.<init>
// Node: RoleBasedAccessFilter
