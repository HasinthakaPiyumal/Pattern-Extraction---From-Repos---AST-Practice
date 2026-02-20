// Cluster 13

// Node: build
// Node: valueOf
// Node: name
// Node: refundPayment
// Node: toString
package net.javaguides.order_service.exception;

import org.springframework.http.HttpStatus;

public class OrderException extends RuntimeException {
    private HttpStatus status;

    public OrderException(String message, HttpStatus status) {
        super(message);
        this.status = status;
    }

    public HttpStatus getStatus() {
        return status;
    }
}



// Node: repos/cloned_ms_repos/springboot-kafka-microservices/order-service/src/main/java/net/javaguides/order_service/exception/OrderException.java:OrderException.<init>
// Node: OrderException
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


// Node: sendMessage
// Node: info
// Node: format
// Node: withPayload
// Node: setHeader
// Node: send
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


// Node: getPaymentMethod
// Node: createOrderDTO
// Node: validateStockAndPrice
// Node: saveOrder
// Node: sendOrderEvent
// Node: createOrderEvent
// Node: setUserId
// Node: extractProductIds
// Node: getOrderItems
// Node: fetchProducts
// Node: toMap
// Node: identity
// Node: getProductId
// Node: updatePriceAndValidateStock
// Node: findMatchingVariant
// Node: getVariantId
// Node: getStockQuantity
// Node: getQuantity
// Node: getPrice
// Node: equalsIgnoreCase
// Node: multiply
// Node: setOrderId
// Node: randomUUID
// Node: setOrder
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


// Node: createOrderTopic
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


// Node: consume
// Node: sendOrderConfirmationEmail
// Node: warn
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


// Node: repos/cloned_ms_repos/springboot-kafka-microservices/email-service/src/main/java/net/javaguides/email_service/service/EmailService.java:EmailService.<init>
// Node: loadTemplate
// Node: getOrderDTO
// Node: getCurrencyInstance
// Node: getStatusCode
// Node: getImageUrl
// Node: getCreatedAt
// Node: createMimeMessage
// Node: MimeMessageHelper
// Node: setTo
// Node: setText
// Node: setFrom
// Node: ClassPathResource
package net.javaguides.product_service.exception;

public class InsufficientStockException extends RuntimeException {
    public InsufficientStockException(String message) {
        super(message);
    }
}


// Node: repos/cloned_ms_repos/springboot-kafka-microservices/product-service/src/main/java/net/javaguides/product_service/exception/InsufficientStockException.java:InsufficientStockException.<init>
// Node: InsufficientStockException
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


// Node: sendDeleteProductMessage
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


// Node: updateStockForVariant
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


// Node: createProductEvent
// Node: ProductEvent
// Node: setProductDTO
// Node: setMethod
// Node: updateAndSaveProduct
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


// Node: topic
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


// Node: updateStatusPayment
// Node: createPayment
package net.javaguides.payment_service.service;


import net.javaguides.common_lib.dto.order.OrderEvent;
import net.javaguides.payment_service.dto.PaymentDto;
import net.javaguides.payment_service.entity.Payment;
import net.javaguides.payment_service.entity.PaymentStatus;

public interface PaymentService {
    void createPayment(OrderEvent orderEvent);
    PaymentDto getPaymentByOrderId(String orderId);
    void updateStatusPayment(String orderId, PaymentStatus status);
    void refundPayment(String orderId);
}


// Node: repos/cloned_ms_repos/springboot-kafka-microservices/payment-service/src/main/java/net/javaguides/payment_service/service/PaymentService.java:PaymentService.<init>
package net.javaguides.payment_service.service.impl;

import lombok.RequiredArgsConstructor;
import net.javaguides.common_lib.dto.order.OrderEvent;
import net.javaguides.common_lib.dto.order.OrderItemDTO;
import net.javaguides.payment_service.dto.PaymentDto;
import net.javaguides.payment_service.entity.Payment;
import net.javaguides.payment_service.entity.PaymentStatus;
import net.javaguides.payment_service.redis.PaymentRedis;
import net.javaguides.payment_service.repository.PaymentRepository;
import net.javaguides.payment_service.service.PaymentService;
import org.modelmapper.ModelMapper;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class PaymentServiceImpl implements PaymentService {
    private final PaymentRepository paymentRepository;
    private final ModelMapper modelMapper;
    private final PaymentRedis paymentRedis;


    @Override
    public void createPayment(OrderEvent orderEvent) {
        Payment newPayment = new Payment();
        newPayment.setId(UUID.randomUUID().toString());

        BigDecimal amount = BigDecimal.valueOf(0);

        for (OrderItemDTO orderItemDTO : orderEvent.getOrderDTO().getOrderItems()) {
            BigDecimal itemTotal = orderItemDTO.getPrice().multiply(BigDecimal.valueOf(orderItemDTO.getQuantity()));
            amount = amount.add(itemTotal);
        }

        newPayment.setAmount(amount);
        newPayment.setPaymentMethod(orderEvent.getPaymentMethod());
        newPayment.setOrderId(orderEvent.getOrderDTO().getOrderId());
        newPayment.setStatus(PaymentStatus.PENDING);
        paymentRedis.save(newPayment);
        paymentRepository.save(newPayment);
    }

    @Override
    public PaymentDto getPaymentByOrderId(String orderId) {
        Payment cachePayment = paymentRedis.findByOrderId(orderId);

        if(cachePayment != null){
            return modelMapper.map(cachePayment, PaymentDto.class);
        }

        Payment existingPayment = paymentRepository.findByOrderId(orderId);
        if(existingPayment != null){
            paymentRedis.save(existingPayment);
            return modelMapper.map(existingPayment, PaymentDto.class);
        }
        return null;
    }



    @Override
    public void updateStatusPayment(String orderId, PaymentStatus status) {
        Payment existingPayment = paymentRepository.findByOrderId(orderId);
        if(existingPayment != null){
            existingPayment.setStatus(status);
            paymentRedis.save(existingPayment);
            paymentRepository.save(existingPayment);
        }
        System.out.println("Khong tim thay payment!");
    }

    @Override
    public void refundPayment(String orderId) {
        Payment existingPayment = paymentRepository.findByOrderId(orderId);
        if(existingPayment != null){
            existingPayment.setStatus(PaymentStatus.REFUND);
            paymentRepository.save(existingPayment);
        }
        System.out.println("Khong tim thay payment!");
    }
}


// Node: Payment
// Node: setAmount
