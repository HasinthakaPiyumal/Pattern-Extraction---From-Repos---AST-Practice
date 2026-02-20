// Cluster 40

package net.javaguides.identity_service.exception;

import org.springframework.http.HttpStatus;

public class AuthException extends RuntimeException {
    private HttpStatus status;

    public AuthException(String message, HttpStatus status) {
        super(message);
        this.status = status;
    }

    public HttpStatus getStatus() {
        return status;
    }
}



// Node: getStatus
// Node: setEmail
package net.javaguides.identity_service.service.impl;

import net.javaguides.identity_service.dto.UserDto;
import net.javaguides.identity_service.entity.UserCredential;
import net.javaguides.identity_service.repository.UserCredentialRepository;
import net.javaguides.identity_service.service.UserService;
import org.modelmapper.ModelMapper;
import org.springframework.stereotype.Service;

@Service
public class UserServiceImpl implements UserService {
    private final UserCredentialRepository userCredentialRepository;
    private final ModelMapper modelMapper;


    public UserServiceImpl(UserCredentialRepository userCredentialRepository, ModelMapper modelMapper) {
        this.userCredentialRepository = userCredentialRepository;
        this.modelMapper = modelMapper;
    }

    @Override
    public UserDto getUserByUsername(String username) {
        UserCredential userCredential = userCredentialRepository.findByName(username).orElse(null);
        if(userCredential != null){
            System.out.println("UserCredential: " + userCredential);
            return modelMapper.map(userCredential, UserDto.class);
        }
        return null;
    }
}


// Node: orElse
// Node: println
// Node: map
// Node: getBody
// Node: setStatus
package net.javaguides.identity_service.entity.converter;

import jakarta.persistence.AttributeConverter;
import jakarta.persistence.Converter;
import net.javaguides.identity_service.enums.ERole;

@Converter(autoApply = true)
public class RoleConverter implements AttributeConverter<ERole, String> {

    @Override
    public String convertToDatabaseColumn(ERole status) {
        if(status == null){
            return null;
        }
        return status.getLabel();
    }

    @Override
    public ERole convertToEntityAttribute(String label) {
        if(label == null){
            return null;
        }
        return switch(label) {
            case "Administrator" -> ERole.ADMINISTRATOR;
            case "Employee" -> ERole.EMPLOYEE;
            case "Customer" -> ERole.CUSTOMER;
            default -> throw new IllegalArgumentException("Unknown role: " + label);
        };
    }
}


// Node: convertToDatabaseColumn
// Node: getLabel
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



package net.javaguides.order_service.controller;

import jakarta.persistence.OptimisticLockException;
import jakarta.servlet.http.HttpServletRequest;
import net.javaguides.common_lib.dto.ApiResponse;
import net.javaguides.common_lib.dto.order.OrderDTO;
import net.javaguides.order_service.dto.OrderRequestDto;
import net.javaguides.order_service.dto.OrderResponseDto;
import net.javaguides.order_service.dto.UserDto;
import net.javaguides.order_service.exception.OrderException;
import net.javaguides.order_service.service.AuthenticationAPIClient;
import net.javaguides.order_service.service.OrderService;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Objects;

@RestController
@RequestMapping("api/v1/order")
public class OrderController {
    private final OrderService orderService;
    private final AuthenticationAPIClient authenticationAPIClient;

    public OrderController(OrderService orderService, AuthenticationAPIClient authenticationAPIClient) {
        this.orderService = orderService;
        this.authenticationAPIClient = authenticationAPIClient;
    }



    /**
     * Endpoint to place a new order
     * @param order: Order request DTO containing order details
     * @param request: The HTTP request to extract the cookie for user authentication
     * @return ResponseEntity<ApiResponse<?>>: Response with order details or error message
     */
    @PostMapping
    public ResponseEntity<ApiResponse<?>> placeOrder(@RequestBody OrderRequestDto order, HttpServletRequest request) {
        try {
            // Extract cookie from the request header
            String cookie = request.getHeader(HttpHeaders.COOKIE);

            // Send cookie in Feign request to authenticate user
            ApiResponse<UserDto> user = authenticationAPIClient.getCurrentUser(cookie).getBody();
            if (user != null && user.getData() != null) {
                // Place order with authenticated user's ID
                return new ResponseEntity<>(new ApiResponse<>(orderService.placeOrder(order, user.getData().getId(), user.getData().getEmail()), HttpStatus.CREATED.value()), HttpStatus.CREATED);
            }
            // Return if user not found
            return new ResponseEntity<>(new ApiResponse<>("User not found!", HttpStatus.NOT_FOUND.value()), HttpStatus.NOT_FOUND);
        } catch (OrderException e) {
            // Handle custom order exceptions
            return new ResponseEntity<>(new ApiResponse<>(e.getMessage(), e.getStatus().value()), e.getStatus());
        } catch (Exception e) {
            // Handle general exceptions
            return new ResponseEntity<>(new ApiResponse<>(e.getMessage(), HttpStatus.INTERNAL_SERVER_ERROR.value()), HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }

    /**
     * Endpoint to cancel an order
     * @param orderId: The ID of the order to cancel
     * @param request: The HTTP request to extract the cookie for user authentication
     * @return ResponseEntity<ApiResponse<?>>: Response with cancellation details or error message
     */
    @PostMapping("/cancel/{orderId}")
    public ResponseEntity<ApiResponse<?>> cancelOrder(@PathVariable("orderId") String orderId, HttpServletRequest request) {
        try {
            // Extract cookie for user authentication
            String cookie = request.getHeader(HttpHeaders.COOKIE);

            ApiResponse<UserDto> user = authenticationAPIClient.getCurrentUser(cookie).getBody();

            if (user != null && user.getData() != null) {
                // Cancel order using user's ID and orderId
                OrderDTO existingOrder = orderService.cancelOrder(orderId, user.getData().getId());

                if (existingOrder != null) {
                    return new ResponseEntity<>(new ApiResponse<>(existingOrder, HttpStatus.OK.value()), HttpStatus.OK);
                }
                // Return if order is not found
                return new ResponseEntity<>(new ApiResponse<>("Order not found!", HttpStatus.NOT_FOUND.value()), HttpStatus.NOT_FOUND);
            }
            // Return if unauthorized request
            return new ResponseEntity<>(new ApiResponse<>("Unauthorized request!", HttpStatus.NOT_FOUND.value()), HttpStatus.NOT_FOUND);
        } catch (Exception e) {
            // Handle general exceptions
            return new ResponseEntity<>(new ApiResponse<>(e.getMessage(), HttpStatus.INTERNAL_SERVER_ERROR.value()), HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }

    /**
     * Endpoint to get order status
     * @param orderId: The ID of the order to check
     * @return ResponseEntity<ApiResponse<?>>: Response with order status or error message
     */
    @GetMapping("{orderId}")
    public ResponseEntity<ApiResponse<?>> getOrderStatus(@PathVariable("orderId") String orderId) {
        try {
            // Fetch order status based on orderId
            OrderResponseDto existingOrder = orderService.checkOrderStatusByOrderId(orderId);

            if (existingOrder != null) {
                return new ResponseEntity<>(new ApiResponse<>(existingOrder, HttpStatus.OK.value()), HttpStatus.OK);
            }
            // Return if order not found
            return new ResponseEntity<>(new ApiResponse<>("Order not found!", HttpStatus.NOT_FOUND.value()), HttpStatus.NOT_FOUND);
        } catch (Exception e) {
            // Handle general exceptions
            return new ResponseEntity<>(new ApiResponse<>(e.getMessage(), HttpStatus.INTERNAL_SERVER_ERROR.value()), HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }

    @GetMapping
    public ResponseEntity<ApiResponse<?>> getOrders(HttpServletRequest request, @RequestParam(defaultValue = "0") int page,
                                                    @RequestParam(defaultValue = "10") int size) {
        try {
            // Extract cookie from the request header
            String cookie = request.getHeader(HttpHeaders.COOKIE);

            // Send cookie in Feign request to authenticate user
            ApiResponse<UserDto> user = authenticationAPIClient.getCurrentUser(cookie).getBody();

            return new ResponseEntity<>(new ApiResponse<>(orderService.getAllOrders(user.getData().getId(), page, size), HttpStatus.OK.value()), HttpStatus.OK);
        } catch (Exception e) {
            return new ResponseEntity<>(new ApiResponse<>(e.getMessage(), HttpStatus.INTERNAL_SERVER_ERROR.value()), HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }

    /**
     * Endpoint to update the order status
     * @param orderId: The ID of the order to update
     * @param version: Optimistic locking version for concurrency control
     * @return ResponseEntity<ApiResponse<?>>: Response with updated order status or error message
     */
    @PatchMapping("/update/status/{orderId}")
    public ResponseEntity<ApiResponse<?>> updateOrderStatus(@PathVariable("orderId") String orderId, @RequestHeader(HttpHeaders.IF_MATCH) int version) {
        try {
            // Update order status using orderId and version for concurrency control
            OrderResponseDto orderDTO = orderService.updateOrderStatus(orderId, version);
            return orderDTO != null ? new ResponseEntity<>(new ApiResponse<>(orderDTO, HttpStatus.OK.value()), HttpStatus.OK)
                    : new ResponseEntity<>(new ApiResponse<>("Not found order!", HttpStatus.NOT_FOUND.value()), HttpStatus.NOT_FOUND);
        } catch (IllegalStateException | OptimisticLockException e) {
            // Handle optimistic locking and state-related exceptions
            return new ResponseEntity<>(new ApiResponse<>(e.getMessage(), HttpStatus.BAD_REQUEST.value()), HttpStatus.BAD_REQUEST);
        } catch (Exception e) {
            // Handle general exceptions
            return new ResponseEntity<>(new ApiResponse<>(e.getMessage(), HttpStatus.INTERNAL_SERVER_ERROR.value()), HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }
}


// Node: repos/cloned_ms_repos/springboot-kafka-microservices/order-service/src/main/java/net/javaguides/order_service/controller/OrderController.java:OrderController.<init>
// Node: OrderController
// Node: placeOrder
// Node: getData
// Node: cancelOrder
// Node: getOrderStatus
// Node: checkOrderStatusByOrderId
// Node: getOrders
// Node: getAllOrders
// Node: PatchMapping
// Node: updateOrderStatus
// Node: getPaymentByOrderId
package net.javaguides.order_service.service;


import net.javaguides.common_lib.dto.order.OrderDTO;
import net.javaguides.order_service.dto.OrderRequestDto;
import net.javaguides.order_service.dto.OrderResponseDto;
import net.javaguides.order_service.dto.OrderResponseDtoWithOutOrderItems;

import java.awt.print.Pageable;
import java.util.List;

public interface OrderService {
    OrderDTO placeOrder(OrderRequestDto order, Long userId, String email);
    OrderResponseDto checkOrderStatusByOrderId(String orderId);
    OrderResponseDto updateOrderStatus(String orderId, int version);
    OrderDTO cancelOrder(String orderId, Long userId);
    List<OrderResponseDtoWithOutOrderItems> getAllOrders(Long userId, int page, int size);
}


// Node: repos/cloned_ms_repos/springboot-kafka-microservices/order-service/src/main/java/net/javaguides/order_service/service/OrderService.java:OrderService.<init>
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


// Node: OrderResponseDto
// Node: setOrderDTO
// Node: setPaymentDto
// Node: getVersion
// Node: OptimisticLockException
// Node: OrderContext
// Node: handleStateChange
// Node: sendRefundOrderEvent
// Node: OrderResponseDtoWithOutOrderItems
// Node: OrderEvent
// Node: setMessage
// Node: setPaymentMethod
// Node: createOrderResponseDto
package net.javaguides.order_service.service.state;

import net.javaguides.order_service.entity.Order;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class OrderContext {
    private static final Logger LOGGER = LoggerFactory.getLogger(OrderContext.class);
    private OrderState orderState;

    public OrderContext(Order order){
        switch(order.getStatus()){
            case "Pending":
                this.orderState = new NewOrderState();
                break;
            case "Processing":
                this.orderState = new ProcessingOrderState();
                break;
            case "Shipping":
                this.orderState = new ShippingOrderState();
                break;
            case "Delivered":
                this.orderState = new DeliveredOrderState();
                break;
            default:
                throw new IllegalStateException("Unknown order state: " + order.getStatus());
        }
    }

    public void handleStateChange(Order order){
        orderState.handleStateChange(order);
    }

    public void setOrderState(OrderState orderState){
        this.orderState = orderState;
    }
}


// Node: repos/cloned_ms_repos/springboot-kafka-microservices/order-service/src/main/java/net/javaguides/order_service/service/state/OrderContext.java:OrderContext.<init>
// Node: NewOrderState
// Node: ProcessingOrderState
// Node: ShippingOrderState
// Node: DeliveredOrderState
// Node: IllegalStateException
package net.javaguides.order_service.service.state;

import net.javaguides.order_service.entity.Order;
import net.javaguides.order_service.entity.OrderStatus;

public class ProcessingOrderState implements OrderState{

    @Override
    public void handleStateChange(Order order) {
        order.setStatus(OrderStatus.SHIPPING.getLabel());
    }
}


package net.javaguides.order_service.service.state;

import net.javaguides.order_service.entity.Order;

public class DeliveredOrderState implements OrderState {
    @Override
    public void handleStateChange(Order order) {
        throw new IllegalStateException("Order has already been delivered and cannot be updated.");
    }
}



package net.javaguides.order_service.service.state;

import net.javaguides.order_service.entity.Order;

public interface OrderState {
    void handleStateChange(Order order);
}


// Node: repos/cloned_ms_repos/springboot-kafka-microservices/order-service/src/main/java/net/javaguides/order_service/service/state/OrderState.java:OrderState.<init>
package net.javaguides.order_service.service.state;

import net.javaguides.order_service.entity.Order;
import net.javaguides.order_service.entity.OrderStatus;

public class NewOrderState implements OrderState{

    @Override
    public void handleStateChange(Order order) {
        order.setStatus(OrderStatus.PROCESSING.getLabel());
    }
}



package net.javaguides.order_service.service.state;

import net.javaguides.order_service.entity.Order;
import net.javaguides.order_service.entity.OrderStatus;

public class ShippingOrderState implements OrderState{

    @Override
    public void handleStateChange(Order order) {
        order.setStatus(OrderStatus.DELIVERED.getLabel());
    }
}


package net.javaguides.product_service.exception;

import org.springframework.http.HttpStatus;

public class ProductException extends  RuntimeException {
    private HttpStatus status;

    public ProductException(String message, HttpStatus status){
        super(message);
        this.status = status;
    }

    public HttpStatus getStatus() {
        return status;
    }


}


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


// Node: mapToEntity
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


package net.javaguides.payment_service.entity.converter;

import jakarta.persistence.AttributeConverter;
import jakarta.persistence.Converter;
import net.javaguides.payment_service.entity.PaymentStatus;

@Converter(autoApply = true)
public class PaymentStatusConverter implements AttributeConverter<PaymentStatus, String> {

    @Override
    public String convertToDatabaseColumn(PaymentStatus status) {
        if(status == null){
            return null;
        }
        return status.getLabel();
    }

    @Override
    public PaymentStatus convertToEntityAttribute(String label) {
        if(label == null){
            return null;
        }
        return switch(label) {
            case "Pending" -> PaymentStatus.PENDING;
            case "Success" -> PaymentStatus.SUCCESS;
            case "Failed" -> PaymentStatus.FAILED;
            default -> throw new IllegalArgumentException("Unknown payment status: " + label);
        };
    }
}


