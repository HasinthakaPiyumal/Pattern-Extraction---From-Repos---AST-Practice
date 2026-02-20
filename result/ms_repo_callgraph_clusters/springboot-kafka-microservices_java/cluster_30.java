// Cluster 30

// Node: getRoleNames
// Node: getPermissions
// Node: getEmail
// Node: getRoles
// Node: setRoles
package net.javaguides.identity_service.filter;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.Cookie;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import net.javaguides.identity_service.service.impl.UserDetailsServiceImpl;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.web.authentication.WebAuthenticationDetailsSource;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import javax.crypto.SecretKey;
import java.io.IOException;
import java.util.Arrays;
import java.util.Base64;

@Component
public class JwtAuthenticationFilter extends OncePerRequestFilter {

    @Autowired
    private UserDetailsServiceImpl userDetailsService;

    public static final String SECRET = "5367566B59703373367639792F423F4528482B4D6251655468576D5A71347437";

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain chain)
            throws IOException, ServletException {

        // Lấy JWT token từ cookie
        String jwtToken = extractTokenFromCookies(request);

        if (jwtToken != null) {
            Claims claims = Jwts.parser()
                    .setSigningKey(getSecretKey())
                    .build()
                    .parseClaimsJws(jwtToken)
                    .getBody();

            String username = claims.getSubject();
            UserDetails userDetails = userDetailsService.loadUserByUsername(username);

            if (username != null && SecurityContextHolder.getContext().getAuthentication() == null) {
                UsernamePasswordAuthenticationToken authToken = new UsernamePasswordAuthenticationToken(
                        userDetails, null, userDetails.getAuthorities());
                authToken.setDetails(new WebAuthenticationDetailsSource().buildDetails(request));
                SecurityContextHolder.getContext().setAuthentication(authToken);
            }
        }
        chain.doFilter(request, response);
    }

    // Phương thức lấy JWT từ cookie
    private String extractTokenFromCookies(HttpServletRequest request) {
        if (request.getCookies() != null) {
            return Arrays.stream(request.getCookies())
                    .filter(cookie -> "token".equals(cookie.getName()))  // Cookie với tên "token"
                    .map(Cookie::getValue)
                    .findFirst()
                    .orElse(null);
        }
        return null;
    }

    private SecretKey getSecretKey() {
        byte[] keyBytes = Base64.getDecoder().decode(SECRET);
        return Keys.hmacShaKeyFor(keyBytes);
    }
}


// Node: stream
// Node: filter
// Node: equals
// Node: findFirst
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


// Node: collect
// Node: toList
// Node: trò
// Node: SimpleGrantedAuthority
// Node: quyền
// Node: toSet
// Node: getId
package net.javaguides.identity_service.config;

import net.javaguides.identity_service.dto.RoleDto;
import net.javaguides.identity_service.dto.UserDto;
import net.javaguides.identity_service.entity.Role;
import net.javaguides.identity_service.entity.UserCredential;
import org.modelmapper.ModelMapper;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.util.Set;
import java.util.stream.Collectors;

@Configuration
public class ModelMapperConfig {
    @Bean
    public ModelMapper modelMapper() {
        ModelMapper modelMapper = new ModelMapper();

        // Mapping from Role to RoleDto
        modelMapper.typeMap(Role.class, RoleDto.class)
                .addMappings(mapper -> mapper.map(Role::getName, RoleDto::setAuthority));

        // Mapping from UserCredential to UserDto
        modelMapper.typeMap(UserCredential.class, UserDto.class)
                .addMappings(mapper -> mapper.skip(UserDto::setRoles))
                .setPostConverter(context -> {
                    UserCredential source = context.getSource();
                    UserDto destination = context.getDestination();

                    Set<RoleDto> roleDtos = source.getRoles().stream()
                            .map(role -> modelMapper.map(role, RoleDto.class))
                            .collect(Collectors.toSet());
                    destination.setRoles(roleDtos);
                    return destination;
                });

        return modelMapper;
    }
}


// Node: modelMapper
// Node: ModelMapper
// Node: typeMap
// Node: addMappings
// Node: skip
// Node: setPostConverter
// Node: getSource
// Node: getDestination
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


// Node: getVariants
package net.javaguides.order_service.config;

import org.modelmapper.ModelMapper;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class ModelMapperConfig {
    @Bean
    public ModelMapper modelMapper(){
        return new ModelMapper();
    }
}


package net.javaguides.product_service.controller;

import net.javaguides.common_lib.dto.ApiResponse;
import net.javaguides.product_service.dto.category.CategoryResponseDto;
import net.javaguides.product_service.dto.category.CreateCategoryRequestDto;
import net.javaguides.product_service.service.CategoryService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/v1/categories")
public class CategoryController {
    @Autowired
    private CategoryService categoryService;

    @PostMapping
    public ResponseEntity<ApiResponse<CategoryResponseDto>> createCategory(@RequestBody CreateCategoryRequestDto requestDto) {
        CategoryResponseDto category = categoryService.createCategory(requestDto);
        ApiResponse<CategoryResponseDto> response = new ApiResponse<>(category, HttpStatus.CREATED.value());
        return new ResponseEntity<>(response, HttpStatus.CREATED);
    }

    @PutMapping("/{id}")
    public ResponseEntity<ApiResponse<CategoryResponseDto>> updateCategory(@PathVariable String id, @RequestBody CreateCategoryRequestDto requestDto) {
        CategoryResponseDto category = categoryService.updateCategory(id, requestDto);
        ApiResponse<CategoryResponseDto> response = new ApiResponse<>(category, HttpStatus.OK.value());
        return ResponseEntity.ok(response);
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<ApiResponse<Void>> deleteCategory(@PathVariable String id) {
        categoryService.deleteCategory(id);
        ApiResponse<Void> response = new ApiResponse<>(null, HttpStatus.NO_CONTENT.value());
        return new ResponseEntity<>(response, HttpStatus.NO_CONTENT);
    }

    @GetMapping("/{id}")
    public ResponseEntity<ApiResponse<CategoryResponseDto>> getCategoryById(@PathVariable String id) {
        CategoryResponseDto category = categoryService.getCategoryById(id);
        ApiResponse<CategoryResponseDto> response = new ApiResponse<>(category, HttpStatus.OK.value());
        return ResponseEntity.ok(response);
    }

    @GetMapping
    public ResponseEntity<ApiResponse<List<CategoryResponseDto>>> getAllCategories() {
        List<CategoryResponseDto> categories = categoryService.getAllCategories();
        ApiResponse<List<CategoryResponseDto>> response = new ApiResponse<>(categories, HttpStatus.OK.value());
        return ResponseEntity.ok(response);
    }

    @GetMapping("/roots")
    public ResponseEntity<ApiResponse<List<CategoryResponseDto>>> getRootCategories() {
        List<CategoryResponseDto> rootCategories = categoryService.getRootCategories();
        ApiResponse<List<CategoryResponseDto>> response = new ApiResponse<>(rootCategories, HttpStatus.OK.value());
        return ResponseEntity.ok(response);
    }
}


// Node: getRootCategories
package net.javaguides.product_service.controller;

import lombok.RequiredArgsConstructor;
import net.javaguides.common_lib.dto.ApiResponse;
import net.javaguides.product_service.dto.product_variant.CreateProductVariantRequestDto;
import net.javaguides.product_service.dto.product_variant.ProductVariantResponseDto;
import net.javaguides.product_service.dto.product_variant.UpdateProductVariantRequestDto;
import net.javaguides.product_service.entity.ProductVariant;
import net.javaguides.product_service.service.ProductVariantService;
import org.modelmapper.ModelMapper;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Set;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/v1/products/variants")
@RequiredArgsConstructor
public class ProductVariantController {

    private final ProductVariantService productVariantService;

    private final ModelMapper modelMapper;

    /**
     * Thêm một biến thể mới cho sản phẩm
     */
    @PostMapping("{productId}")
    public ResponseEntity<ProductVariantResponseDto> createVariant(
            @PathVariable String productId,
            @RequestBody CreateProductVariantRequestDto requestDto) {
        ProductVariantResponseDto variant = productVariantService.createProductVariant(productId, requestDto.getAttributes(), requestDto.getPrice(), requestDto.getSku(), requestDto.getInitialStock(), requestDto.getReorderLevel());

        return ResponseEntity.ok(variant);
    }

    /**
     * Lấy tất cả biến thể của một sản phẩm
     */
    @GetMapping("{productId}")
    public ResponseEntity<List<ProductVariantResponseDto>> getVariants(@PathVariable String productId) {
        List<ProductVariantResponseDto> variants = productVariantService.getVariantsByProductId(productId);
        return ResponseEntity.ok(variants);
    }

    @GetMapping
    public ResponseEntity<List<ProductVariantResponseDto>> getVariantsByIds(@RequestParam("variantIds") Set<Long> variantIds) {
        List<ProductVariant> variants = productVariantService.getProductVariantByIds(variantIds);
        return ResponseEntity.ok(variants.stream().map(productVariant -> modelMapper.map(productVariant,ProductVariantResponseDto.class)).collect(Collectors.toList()));
    }



    @PutMapping("{variantId}")
    public ResponseEntity<ApiResponse<?>> updateVariant(@PathVariable Long variantId, @RequestBody UpdateProductVariantRequestDto requestDto){
        try {
            ProductVariantResponseDto responseDto = productVariantService.updateProductVariant(variantId, requestDto);
            return new ResponseEntity<>(new ApiResponse<>(responseDto, HttpStatus.OK.value()), HttpStatus.OK);
        }catch(Exception e){
            return new ResponseEntity<>(new ApiResponse<>(e.getMessage(), HttpStatus.INTERNAL_SERVER_ERROR.value()), HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }

    @DeleteMapping("{variantId}")
    public ResponseEntity<ApiResponse<?>> deleteVariant(@PathVariable Long variantId){
        try {
            productVariantService.deleteProductVariant(variantId);
            return new ResponseEntity<>(null, HttpStatus.NO_CONTENT);
        }catch(Exception e){
            return new ResponseEntity<>(new ApiResponse<>(e.getMessage(), HttpStatus.INTERNAL_SERVER_ERROR.value()), HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }


    // Các API khác như update, delete nếu cần
}


// Node: getVariantsByProductId
package net.javaguides.product_service.repository;

import net.javaguides.product_service.entity.Category;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface CategoryRepository extends JpaRepository<Category, String> {
    Category findByName(String name);
    List<Category> findByParentIsNull(); // Lấy danh mục gốc
}


// Node: repos/cloned_ms_repos/springboot-kafka-microservices/product-service/src/main/java/net/javaguides/product_service/repository/CategoryRepository.java:CategoryRepository.<init>
// Node: findByParentIsNull
package net.javaguides.product_service.repository;

import net.javaguides.product_service.entity.Product;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;

import java.util.List;
import java.util.Set;

public interface ProductRepository extends JpaRepository<Product, String>, JpaSpecificationExecutor<Product> {
    List<Product> findAllByIdIn(Set<String> productIds);

    @Override
    Page<Product> findAll(Pageable pageable);
}


// Node: repos/cloned_ms_repos/springboot-kafka-microservices/product-service/src/main/java/net/javaguides/product_service/repository/ProductRepository.java:ProductRepository.<init>
// Node: findAllByIdIn
// Node: findAll
package net.javaguides.product_service.repository;

import net.javaguides.product_service.entity.Product;
import net.javaguides.product_service.entity.ProductVariant;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Set;

public interface ProductVariantRepository extends JpaRepository<ProductVariant, Long> {
    List<ProductVariant> findAllByIdIn(Set<Long> variantIds);
    List<ProductVariant> findByProductId(String productId);
}

// Node: repos/cloned_ms_repos/springboot-kafka-microservices/product-service/src/main/java/net/javaguides/product_service/repository/ProductVariantRepository.java:ProductVariantRepository.<init>
// Node: setId
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


// Node: getContent
// Node: getTotalElements
// Node: insertProductToCache
package net.javaguides.product_service.service.impl;

import lombok.RequiredArgsConstructor;
import net.javaguides.product_service.dto.attribute_value.AttributeValueResponseDto;
import net.javaguides.product_service.dto.product_variant.ProductVariantResponseDto;
import net.javaguides.product_service.dto.product_variant.UpdateProductVariantRequestDto;
import net.javaguides.product_service.entity.Attribute;
import net.javaguides.product_service.entity.AttributeValue;
import net.javaguides.product_service.entity.Product;
import net.javaguides.product_service.entity.ProductVariant;
import net.javaguides.product_service.exception.ProductException;
import net.javaguides.product_service.redis.ProductRedis;
import net.javaguides.product_service.repository.AttributeRepository;
import net.javaguides.product_service.repository.ProductRepository;
import net.javaguides.product_service.repository.ProductVariantRepository;
import net.javaguides.product_service.service.ProductVariantService;
import org.hibernate.sql.Update;
import org.modelmapper.ModelMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class ProductVariantServiceImpl implements ProductVariantService {
    private final ProductVariantRepository productVariantRepository;

    private final AttributeRepository attributeRepository;

    private final ProductRepository productRepository;

    private final ModelMapper modelMapper;

    private final ProductRedis productRedis;

    @Transactional
    @Override
    public ProductVariantResponseDto createProductVariant(String productId, Map<String, String> attributes, BigDecimal price, String sku, Integer initialStock, Integer reorderLevel) {
        Product product = productRepository.findById(productId)
                .orElseThrow(() -> new RuntimeException("Product not found"));

        ProductVariant variant = new ProductVariant();
        variant.setProduct(product);
        variant.setPrice(price);
        variant.setSku(sku);
        variant.setStockQuantity(initialStock);
        variant.setReorderLevel(reorderLevel);

        // Liên kết các thuộc tính
        for (Map.Entry<String, String> entry : attributes.entrySet()) {
            Attribute attribute = attributeRepository.findByName(entry.getKey())
                    .orElseThrow(() -> new IllegalArgumentException("Attribute " + entry.getKey() + " not found."));
            AttributeValue attributeValue = new AttributeValue();
            attributeValue.setProductVariant(variant);
            attributeValue.setAttribute(attribute);
            attributeValue.setValue(entry.getValue());
            variant.getAttributeValues().add(attributeValue);
        }

        ProductVariant savedVariant = productVariantRepository.save(variant);

        product.getVariants().add(savedVariant);
        productRedis.save(product);

        return modelMapper.map(savedVariant, ProductVariantResponseDto.class);
    }

    @Override
    public List<ProductVariantResponseDto> getVariantsByProductId(String productId) {
        return productVariantRepository.findByProductId(productId)
                .stream()
                .map(productVariant -> modelMapper.map(productVariant, ProductVariantResponseDto.class))
                .collect(Collectors.toList());
    }

    @Transactional
    @Override
    public ProductVariantResponseDto updateProductVariant(Long variantId, UpdateProductVariantRequestDto updateDTO) {
        ProductVariant variant = productVariantRepository.findById(variantId)
                .orElseThrow(() -> new ProductException("ProductVariant not found", HttpStatus.NOT_FOUND));

        // Cập nhật các thuộc tính cơ bản
        if (updateDTO.getPrice() != null) {
            variant.setPrice(updateDTO.getPrice());
        }
        if (updateDTO.getSku() != null) {
            variant.setSku(updateDTO.getSku());
        }
        if (updateDTO.getStockQuantity() != null) {
            variant.setStockQuantity(updateDTO.getStockQuantity());
        }
        if (updateDTO.getReorderLevel() != null) {
            variant.setReorderLevel(updateDTO.getReorderLevel());
        }

        // Cập nhật AttributeValues
        if (updateDTO.getAttributeValues() != null && !updateDTO.getAttributeValues().isEmpty()) {
            // Xóa tất cả AttributeValues hiện tại
            variant.getAttributeValues().clear();

            // Thêm AttributeValues mới
            for(AttributeValueResponseDto attrDto : updateDTO.getAttributeValues()) {
                Attribute attribute = attributeRepository.findByName(attrDto.getAttribute().getName())
                        .orElseThrow(() -> new IllegalArgumentException("Attribute " + attrDto.getAttribute().getName() + " not found."));
                AttributeValue attributeValue = new AttributeValue();
                attributeValue.setProductVariant(variant);
                attributeValue.setAttribute(attribute);
                attributeValue.setValue(attrDto.getValue());
                variant.getAttributeValues().add(attributeValue);
            }
        }

        ProductVariant updatedVariant = productVariantRepository.save(variant);


        // Cập nhật cache cho sản phẩm
       Product productAfterUpdate = variant.getProduct();
        productRedis.save(productAfterUpdate);

        return modelMapper.map(updatedVariant, ProductVariantResponseDto.class);
    }

    /**
     * Xóa một ProductVariant
     */
    @Transactional
    public void deleteProductVariant(Long variantId) {
        ProductVariant variant = productVariantRepository.findById(variantId)
                .orElseThrow(() -> new ProductException("ProductVariant not found", HttpStatus.NOT_FOUND));

        Product product = variant.getProduct();

        // Xóa ProductVariant
        productVariantRepository.delete(variant);

        // Gọi Stock Service để xóa tồn kho
//        stockClient.deleteStock(variantId);

        // Cập nhật cache cho sản phẩm
        productRedis.save(product);
    }

    @Override
    public void saveProductVariant(ProductVariant productVariant) {
        productVariantRepository.save(productVariant);
    }

    @Override
    public List<ProductVariant> getProductVariantByIds(Set<Long> variantIds) {
        return productVariantRepository.findAllByIdIn(variantIds);
    }

    @Override
    public ProductVariant getVariantById(Long variantId) {
        ProductVariant variant = productVariantRepository.findById(variantId).orElseThrow(() -> new ProductException("Product variant not found with ID: " + variantId, HttpStatus.NOT_FOUND));
        return variant;
    }

    // Các phương thức CRUD khác như update, delete nếu cần
}


package net.javaguides.product_service.service.impl;

import net.javaguides.product_service.dto.category.CategoryResponseDto;
import net.javaguides.product_service.dto.category.CreateCategoryRequestDto;
import net.javaguides.product_service.entity.Category;
import net.javaguides.product_service.repository.CategoryRepository;
import net.javaguides.product_service.service.CategoryService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.*;
import java.util.stream.Collectors;

@Service
public class CategoryServiceImpl implements CategoryService {
    @Autowired
    private CategoryRepository categoryRepository;

    @Override
    public CategoryResponseDto createCategory(CreateCategoryRequestDto requestDto) {
        Category category = new Category();
        category.setId(UUID.randomUUID().toString());
        category.setName(requestDto.getName());

        if (requestDto.getParentId() != null) {
            Category parent = categoryRepository.findById(requestDto.getParentId())
                    .orElseThrow(() -> new RuntimeException("Parent category not found"));
            category.setParent(parent);
        }

        Category savedCategory = categoryRepository.save(category);
        return convertToDto(savedCategory);
    }

    @Override
    public CategoryResponseDto updateCategory(String id, CreateCategoryRequestDto requestDto) {
        Category category = categoryRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Category not found"));

        category.setName(requestDto.getName());

        if (requestDto.getParentId() != null) {
            Category parent = categoryRepository.findById(requestDto.getParentId())
                    .orElseThrow(() -> new RuntimeException("Parent category not found"));
            category.setParent(parent);
        } else {
            category.setParent(null);
        }

        Category updatedCategory = categoryRepository.save(category);
        return convertToDto(updatedCategory);
    }

    @Override
    public void deleteCategory(String id) {
        Category category = categoryRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Category not found"));
        categoryRepository.delete(category);
    }

    @Override
    public CategoryResponseDto getCategoryById(String id) {
        Category category = categoryRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Category not found"));
        return convertToDto(category);
    }

    @Override
    public List<CategoryResponseDto> getAllCategories() {
        List<Category> categories = categoryRepository.findAll();
        return categories.stream()
                .map(this::convertToDto)
                .collect(Collectors.toList());
    }

    @Override
    public List<CategoryResponseDto> getRootCategories() {
        List<Category> rootCategories = categoryRepository.findByParentIsNull();
        return rootCategories.stream()
                .map(this::convertToDto)
                .collect(Collectors.toList());
    }

    // Hàm chuyển đổi từ entity sang DTO
    private CategoryResponseDto convertToDto(Category category) {
        CategoryResponseDto dto = new CategoryResponseDto();
        dto.setId(category.getId());
        dto.setName(category.getName());
        dto.setParentId(category.getParent() != null ? category.getParent().getId() : null);

        // Đệ quy chuyển đổi danh mục con
        if (category.getChildren() != null && !category.getChildren().isEmpty()) {
            List<CategoryResponseDto> childDtos = category.getChildren().stream()
                    .map(this::convertToDto)
                    .collect(Collectors.toList());
            dto.setChildren(childDtos);
        }

        return dto;
    }
}


// Node: CategoryResponseDto
// Node: setParentId
// Node: getParent
// Node: getChildren
// Node: setChildren
package net.javaguides.product_service.config;

import org.modelmapper.ModelMapper;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class ModelMapperConfig {
    @Bean
    public ModelMapper modelMapper() {
        ModelMapper modelMapper = new ModelMapper();
        modelMapper.getConfiguration()
                .setSkipNullEnabled(true) // Skip null values during mapping
                .setFieldMatchingEnabled(true) ;
    return modelMapper;
    }
}


// Node: getConfiguration
// Node: setSkipNullEnabled
// Node: setFieldMatchingEnabled
package net.javaguides.payment_service.config;

import org.modelmapper.ModelMapper;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class ModelMapperConfig {
    @Bean
    public ModelMapper modelMapper(){
        return new ModelMapper();
    }
}


