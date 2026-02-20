// Cluster 37

package net.javaguides.identity_service.controller;



import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import net.javaguides.common_lib.dto.ApiResponse;
import net.javaguides.identity_service.dto.AuthRequest;
import net.javaguides.identity_service.dto.SignUpRequest;
import net.javaguides.identity_service.dto.UserDto;
import net.javaguides.identity_service.exception.AuthException;
import net.javaguides.identity_service.service.AuthService;
import net.javaguides.identity_service.service.UserService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("api/v1/auth")
@RequiredArgsConstructor
public class AuthController {
    private final AuthService authService;
    private final AuthenticationManager authenticationManager;
    private final UserService userService;

    @PostMapping("/register")
    public ResponseEntity<ApiResponse<String>> addNewUser(@RequestBody SignUpRequest signUpRequest) {
        try {
            String message = authService.saveUser(signUpRequest);
            ApiResponse<String> apiResponse = new ApiResponse<>(message, HttpStatus.CREATED.value());
            return new ResponseEntity<>(apiResponse, HttpStatus.CREATED);
        }
        catch(AuthException e){
            ApiResponse<String> apiResponse = new ApiResponse<>(e.getMessage(), e.getStatus().value());
            return new ResponseEntity<>(apiResponse, e.getStatus());
        }
        catch(Exception e){
            ApiResponse<String> apiResponse = new ApiResponse<>(e.getMessage(), HttpStatus.INTERNAL_SERVER_ERROR.value());
            return new ResponseEntity<>(apiResponse, HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }

    @PostMapping("/token")
    public ResponseEntity<ApiResponse<String>> getToken(@RequestBody AuthRequest authRequest, HttpServletResponse response) {
        try {
            Authentication authenticate = authenticationManager.authenticate(new UsernamePasswordAuthenticationToken(authRequest.getUsername(), authRequest.getPassword()));
            if (authenticate.isAuthenticated()) {
                String generateToken = authService.generateToken(authRequest, response);

                ApiResponse<String> apiResponse = new ApiResponse<>(generateToken, HttpStatus.OK.value());
                return new ResponseEntity<>(apiResponse, HttpStatus.OK);
            } else {
                ApiResponse<String> apiResponse = new ApiResponse<>("Invalid access!", HttpStatus.BAD_REQUEST.value());
                return new ResponseEntity<>(apiResponse, HttpStatus.OK);            }
        }catch(Exception e){
            ApiResponse<String> apiResponse = new ApiResponse<>(e.getMessage(), HttpStatus.INTERNAL_SERVER_ERROR.value());
            return new ResponseEntity<>(apiResponse, HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }

    @GetMapping("/validate")
    public ResponseEntity<ApiResponse<String>> validateToken(@RequestParam("token") String token) {
        try {
            authService.validateToken(token);
            ApiResponse<String> apiResponse = new ApiResponse<>("Token is valid", HttpStatus.OK.value());
            return new ResponseEntity<>(apiResponse, HttpStatus.OK);
        }catch(Exception e){
            ApiResponse<String> apiResponse = new ApiResponse<>(e.getMessage(), HttpStatus.INTERNAL_SERVER_ERROR.value());
            return new ResponseEntity<>(apiResponse, HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }

    @GetMapping("/me")
    public ResponseEntity<ApiResponse<?>> getCurrentUser(@AuthenticationPrincipal UserDetails currentUser) {
        try {
            UserDto userDto = userService.getUserByUsername(currentUser.getUsername());
            ApiResponse<UserDto> apiResponse = new ApiResponse<>(userDto, HttpStatus.OK.value());
            return new ResponseEntity<>(apiResponse, HttpStatus.OK);
        } catch (Exception e) {
            ApiResponse<String> apiResponse = new ApiResponse<>(e.getMessage(), HttpStatus.INTERNAL_SERVER_ERROR.value());
            return new ResponseEntity<>(apiResponse, HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }

}


// Node: repos/cloned_ms_repos/springboot-kafka-microservices/identity-service/src/main/java/net/javaguides/identity_service/controller/AuthController.java:AuthController.<init>
// Node: RequestMapping
// Node: PostMapping
// Node: GetMapping
// Node: RequestParam
// Node: getCurrentUser
// Node: getUserByUsername
package net.javaguides.identity_service.service;

import net.javaguides.identity_service.dto.UserDto;

public interface UserService {
    UserDto getUserByUsername(String username);
}


// Node: repos/cloned_ms_repos/springboot-kafka-microservices/identity-service/src/main/java/net/javaguides/identity_service/service/UserService.java:UserService.<init>
// Node: PathVariable
// Node: RequestHeader
package net.javaguides.order_service.repository;

import net.javaguides.order_service.entity.Order;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.web.bind.annotation.PathVariable;



public interface OrderRepository extends JpaRepository<Order, String> {
    Page<Order> findByUserId(@PathVariable("userId") Long userId, Pageable pageable);
}


// Node: repos/cloned_ms_repos/springboot-kafka-microservices/order-service/src/main/java/net/javaguides/order_service/repository/OrderRepository.java:OrderRepository.<init>
// Node: findByUserId
package net.javaguides.order_service.service;

import net.javaguides.common_lib.dto.ApiResponse;
import net.javaguides.order_service.dto.PaymentDto;
import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;

@FeignClient(name = "PAYMENT-SERVICE")
public interface PaymentAPIClient {
    @GetMapping("api/v1/payment/{orderId}")
    ResponseEntity<ApiResponse<PaymentDto>> getPaymentByOrderId(@PathVariable("orderId") String orderId);
}


// Node: repos/cloned_ms_repos/springboot-kafka-microservices/order-service/src/main/java/net/javaguides/order_service/service/PaymentAPIClient.java:PaymentAPIClient.<init>
// Node: FeignClient
package net.javaguides.order_service.service;

import net.javaguides.order_service.dto.StockDto;
import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;

import java.util.List;
import java.util.Set;

@FeignClient(name = "STOCK-SERVICE")
public interface StockAPIClient {
    @GetMapping("api/v1/stock")
    ResponseEntity<List<StockDto>> getProductsStock(@RequestParam("productIds") Set<String> productIds);
}


// Node: repos/cloned_ms_repos/springboot-kafka-microservices/order-service/src/main/java/net/javaguides/order_service/service/StockAPIClient.java:StockAPIClient.<init>
// Node: getProductsStock
package net.javaguides.order_service.service;
import net.javaguides.common_lib.dto.ApiResponse;
import net.javaguides.order_service.dto.UserDto;
import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.http.HttpHeaders;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestHeader;

@FeignClient(name = "IDENTITY-SERVICE")
public interface AuthenticationAPIClient {
    @GetMapping("api/v1/auth/me")
    ResponseEntity<ApiResponse<UserDto>> getCurrentUser(@RequestHeader(HttpHeaders.COOKIE) String cookie);
}


// Node: repos/cloned_ms_repos/springboot-kafka-microservices/order-service/src/main/java/net/javaguides/order_service/service/AuthenticationAPIClient.java:AuthenticationAPIClient.<init>
package net.javaguides.order_service.service;

import net.javaguides.common_lib.dto.ApiResponse;

import net.javaguides.order_service.dto.product.ProductResponseDto;
import net.javaguides.order_service.dto.product_variant.ProductVariantResponseDto;
import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;

import java.util.List;
import java.util.Set;

@FeignClient(name = "PRODUCT-SERVICE")
public interface ProductAPIClient {
    @GetMapping("/api/v1/products/products")
    ResponseEntity<ApiResponse<List<ProductResponseDto>>> getProductsByIds(@RequestParam("ids") Set<String> productIds);

    @GetMapping("/api/v1/products/variants")
    ResponseEntity<List<ProductVariantResponseDto>> getProductsByVariantIds(@RequestParam("variantIds") Set<Long> variantIds);
}


// Node: repos/cloned_ms_repos/springboot-kafka-microservices/order-service/src/main/java/net/javaguides/order_service/service/ProductAPIClient.java:ProductAPIClient.<init>
// Node: getProductsByIds
// Node: getProductsByVariantIds
// Node: getProductById
package net.javaguides.email_service.service;

import net.javaguides.common_lib.dto.ApiResponse;
import net.javaguides.common_lib.dto.product.ProductDTO;
import net.javaguides.email_service.dto.ProductStockResponse;
import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestParam;

@FeignClient(name = "PRODUCT-SERVICE")
public interface ProductAPIClient {
    @GetMapping("api/v1/products/{id}")
    ResponseEntity<ApiResponse<ProductStockResponse>> getProductById(@RequestParam("id") String id);
}


// Node: repos/cloned_ms_repos/springboot-kafka-microservices/email-service/src/main/java/net/javaguides/email_service/service/ProductAPIClient.java:ProductAPIClient.<init>
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


// Node: repos/cloned_ms_repos/springboot-kafka-microservices/product-service/src/main/java/net/javaguides/product_service/controller/CategoryController.java:CategoryController.<init>
// Node: createCategory
// Node: PutMapping
// Node: updateCategory
// Node: ok
// Node: DeleteMapping
// Node: deleteCategory
// Node: getCategoryById
// Node: getAllCategories
package net.javaguides.product_service.controller;


import jakarta.persistence.OptimisticLockException;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import net.javaguides.common_lib.dto.ApiResponse;
import net.javaguides.common_lib.dto.product.ProductDTO;
import net.javaguides.product_service.dto.product.CreateProductRequestDto;
import net.javaguides.product_service.dto.ProductStockResponse;
import net.javaguides.product_service.dto.product.ProductResponseDto;
import net.javaguides.product_service.dto.product.UpdateProductRequestDto;
import net.javaguides.product_service.exception.ProductException;
import net.javaguides.product_service.service.ProductService;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.math.BigDecimal;
import java.util.List;
import java.util.Set;

@RestController
@RequestMapping("api/v1/products")
@RequiredArgsConstructor
public class ProductController {
    private final ProductService productService;
    @PostMapping
    public ResponseEntity<ApiResponse<?>> saveProduct(@ModelAttribute @Valid CreateProductRequestDto createProductRequestDto) {
        try {
            ProductResponseDto createdProductDto = productService.saveProduct(createProductRequestDto);
            ApiResponse<ProductResponseDto> apiResponse = new ApiResponse<>(createdProductDto, HttpStatus.CREATED.value());
            return new ResponseEntity<>(apiResponse, HttpStatus.CREATED);
        } catch (Exception e) {
            ApiResponse<String> response = new ApiResponse<>(e.getMessage(), HttpStatus.INTERNAL_SERVER_ERROR.value());
            return new ResponseEntity<>(response, HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }

    @GetMapping
    public ResponseEntity<ApiResponse<?>> getProductList(@RequestParam(defaultValue = "0") int page,
                                                            @RequestParam(defaultValue = "10") int size
    ) {
        try {
            Page<ProductResponseDto> productList = productService.getProductList(page, size);
            ApiResponse<Page<ProductResponseDto>> apiResponse = new ApiResponse<>(productList, HttpStatus.OK.value());
            return new ResponseEntity<>(apiResponse, HttpStatus.OK);
        } catch (Exception e) {
            ApiResponse<String> response = new ApiResponse<>(e.getMessage(), HttpStatus.INTERNAL_SERVER_ERROR.value());
            return new ResponseEntity<>(response, HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }

    @GetMapping("{id}")
    public ResponseEntity<ApiResponse<?>> getProductById(@PathVariable("id") String id) {
        try {
            ProductResponseDto productStockResponse = productService.getProductById(id);
            ApiResponse<ProductResponseDto> apiResponse = new ApiResponse<>(productStockResponse, HttpStatus.OK.value());
            return new ResponseEntity<>(apiResponse, HttpStatus.OK);
        } catch (ProductException e) {
            ApiResponse<String> response = new ApiResponse<>(e.getMessage(), e.getStatus().value());
            return new ResponseEntity<>(response, e.getStatus());
        } catch (Exception e) {
            ApiResponse<String> response = new ApiResponse<>(e.getMessage(), HttpStatus.INTERNAL_SERVER_ERROR.value());
            return new ResponseEntity<>(response, HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }

    @PutMapping("/update/{id}")
    public ResponseEntity<ApiResponse<?>> updateProduct(@PathVariable("id") String id, @RequestBody UpdateProductRequestDto productDTO, @RequestHeader(HttpHeaders.IF_MATCH) int version) {
        try {
            ProductResponseDto productStockResponse = productService.updateProduct(id, productDTO, version);
            ApiResponse<ProductResponseDto> apiResponse = new ApiResponse<>(productStockResponse, HttpStatus.OK.value());
            return new ResponseEntity<>(apiResponse, HttpStatus.OK);
        }
        catch(OptimisticLockException e){
            ApiResponse<String> response = new ApiResponse<>(e.getMessage(), HttpStatus.CONFLICT.value());
            return new ResponseEntity<>(response, HttpStatus.CONFLICT);
        }
        catch (Exception e) {
            ApiResponse<String> response = new ApiResponse<>(e.getMessage(), HttpStatus.INTERNAL_SERVER_ERROR.value());
            return new ResponseEntity<>(response, HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }

    @DeleteMapping("{id}")
    public ResponseEntity<ApiResponse<?>> deleteProduct(@PathVariable("id") String id) {
        try {
            productService.deleteProduct(id);
            return new ResponseEntity<>(HttpStatus.NOT_FOUND);
        }
        catch (ProductException e) {
            ApiResponse<String> response = new ApiResponse<>(e.getMessage(), e.getStatus().value());
            return new ResponseEntity<>(response, e.getStatus());
        }
        catch (Exception e) {
            ApiResponse<String> response = new ApiResponse<>(e.getMessage(), HttpStatus.INTERNAL_SERVER_ERROR.value());
            return new ResponseEntity<>(response, HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }

    @GetMapping("/search")
    public ResponseEntity<ApiResponse<Page<ProductResponseDto>>> searchProducts(
            @RequestParam(required = false) String name,
            @RequestParam(required = false) String categoryId,
            @RequestParam(required = false) BigDecimal minPrice,
            @RequestParam(required = false) BigDecimal maxPrice,
            Pageable pageable) {

        Page<ProductResponseDto> products = productService.searchProducts(name, categoryId, minPrice, maxPrice, pageable);
        ApiResponse<Page<ProductResponseDto>> response = new ApiResponse<>(products, HttpStatus.OK.value());
        return ResponseEntity.ok(response);
    }



    @GetMapping("/products")
    public ResponseEntity<ApiResponse<?>> getProductsByIds(@RequestParam("ids") Set<String> productIds) {
        try {
            List<ProductResponseDto> productDTOs = productService.getProductsByIds(productIds);
            ApiResponse<List<ProductResponseDto>> apiResponse = new ApiResponse<>(productDTOs, HttpStatus.OK.value());
            return new ResponseEntity<>(apiResponse, HttpStatus.OK);
        } catch (Exception e) {
            ApiResponse<String> response = new ApiResponse<>(e.getMessage(), HttpStatus.INTERNAL_SERVER_ERROR.value());
            return new ResponseEntity<>(response, HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }


}


// Node: repos/cloned_ms_repos/springboot-kafka-microservices/product-service/src/main/java/net/javaguides/product_service/controller/ProductController.java:ProductController.<init>
// Node: saveProduct
// Node: getProductList
// Node: updateProduct
// Node: deleteProduct
// Node: searchProducts
package net.javaguides.product_service.controller;

import lombok.RequiredArgsConstructor;
import net.javaguides.common_lib.dto.ApiResponse;
import net.javaguides.product_service.dto.attribute.UpdateAttributeRequestDto;
import net.javaguides.product_service.entity.Attribute;
import net.javaguides.product_service.service.AttributeService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.List;

@RestController
@RequestMapping("/api/v1/attributes")
@RequiredArgsConstructor
public class AttributeController {


    private final AttributeService attributeService;

    // --- Attribute APIs ---

    /**
     * Thêm Attribute mới
     */
    @PostMapping
    public ResponseEntity<ApiResponse<?>> createAttribute(
            @RequestBody UpdateAttributeRequestDto requestDto) {
        Attribute createdAttribute = attributeService.createAttribute(requestDto.getName(), requestDto.getDataType());
        return new ResponseEntity<>(new ApiResponse<>(createdAttribute, HttpStatus.CREATED.value()), HttpStatus.CREATED);
    }

    /**
     * Cập nhật Attribute hiện có
     */
    @PutMapping("/{id}")
    public ResponseEntity<ApiResponse<?>> updateAttribute(
            @PathVariable Long id,
            @RequestBody UpdateAttributeRequestDto requestDto) {
        Attribute updatedAttribute = attributeService.updateAttribute(id, requestDto.getName(), requestDto.getDataType());
        return new ResponseEntity<>(new ApiResponse<>(updatedAttribute, HttpStatus.OK.value()), HttpStatus.OK);
    }

    /**
     * Xóa Attribute
     */
    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteAttribute(@PathVariable Long id) {
        attributeService.deleteAttribute(id);
        return ResponseEntity.noContent().build();
    }

    /**
     * Lấy tất cả Attributes
     */
    @GetMapping
    public ResponseEntity<ApiResponse<?>> getAllAttributes() {
        List<Attribute> attributes = attributeService.getAllAttributes();
        return new ResponseEntity<>(new ApiResponse<>(attributes, HttpStatus.OK.value()), HttpStatus.OK);
    }
}


// Node: repos/cloned_ms_repos/springboot-kafka-microservices/product-service/src/main/java/net/javaguides/product_service/controller/AttributeController.java:AttributeController.<init>
// Node: createAttribute
// Node: getDataType
// Node: updateAttribute
// Node: deleteAttribute
// Node: noContent
// Node: getAllAttributes
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


// Node: repos/cloned_ms_repos/springboot-kafka-microservices/product-service/src/main/java/net/javaguides/product_service/controller/ProductVariantController.java:ProductVariantController.<init>
// Node: createVariant
// Node: createProductVariant
// Node: getAttributes
// Node: getSku
// Node: getInitialStock
// Node: getReorderLevel
// Node: getVariantsByIds
// Node: getProductVariantByIds
// Node: updateVariant
// Node: updateProductVariant
// Node: deleteVariant
// Node: deleteProductVariant
// Node: saveProductVariant
package net.javaguides.product_service.service;



import net.javaguides.common_lib.dto.product.ProductDTO;
import net.javaguides.product_service.dto.product.CreateProductRequestDto;
import net.javaguides.product_service.dto.ProductStockResponse;
import net.javaguides.product_service.dto.product.ProductResponseDto;
import net.javaguides.product_service.dto.product.UpdateProductRequestDto;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;

import java.math.BigDecimal;
import java.util.List;
import java.util.Set;

public interface ProductService {
    ProductResponseDto saveProduct(CreateProductRequestDto createProductRequestDto);
    ProductResponseDto getProductById(String id);
    Page<ProductResponseDto> getProductList(int page, int size);
    ProductResponseDto updateProduct(String id, UpdateProductRequestDto productUpdateDto, int version);
    void deleteProduct(String id);
    List<ProductResponseDto> getProductsByIds(Set<String> productIds);
    Page<ProductResponseDto> searchProducts(String name, String categoryId, BigDecimal minPrice, BigDecimal maxPrice, Pageable pageable);
}


// Node: repos/cloned_ms_repos/springboot-kafka-microservices/product-service/src/main/java/net/javaguides/product_service/service/ProductService.java:ProductService.<init>
package net.javaguides.product_service.service;

import net.javaguides.product_service.entity.Attribute;

import java.util.List;

public interface AttributeService {
    Attribute createAttribute(String name, String dataType);
    Attribute updateAttribute(Long id, String newName, String newDataType);
    List<Attribute> getAllAttributes();
    Attribute getAttributeByName(String name);
    void deleteAttribute(Long id);
}


// Node: repos/cloned_ms_repos/springboot-kafka-microservices/product-service/src/main/java/net/javaguides/product_service/service/AttributeService.java:AttributeService.<init>
// Node: getAttributeByName
package net.javaguides.product_service.service;



import net.javaguides.product_service.dto.category.CategoryResponseDto;
import net.javaguides.product_service.dto.category.CreateCategoryRequestDto;

import java.util.List;

public interface CategoryService {
    CategoryResponseDto createCategory(CreateCategoryRequestDto requestDto);
    CategoryResponseDto updateCategory(String id, CreateCategoryRequestDto requestDto);
    void deleteCategory(String id);
    CategoryResponseDto getCategoryById(String id);
    List<CategoryResponseDto> getAllCategories();
    List<CategoryResponseDto> getRootCategories(); // Danh mục gốc cho mega menu
}


// Node: repos/cloned_ms_repos/springboot-kafka-microservices/product-service/src/main/java/net/javaguides/product_service/service/CategoryService.java:CategoryService.<init>
package net.javaguides.product_service.service;

import net.javaguides.product_service.dto.product.ProductResponseDto;
import net.javaguides.product_service.dto.product_variant.ProductVariantResponseDto;
import net.javaguides.product_service.dto.product_variant.UpdateProductVariantRequestDto;
import net.javaguides.product_service.entity.ProductVariant;

import java.math.BigDecimal;
import java.util.List;
import java.util.Map;
import java.util.Set;

public interface ProductVariantService {
    ProductVariantResponseDto createProductVariant(String productId, Map<String, String> attributes, BigDecimal price, String sku, Integer initialStock, Integer reorderLevel);
    List<ProductVariantResponseDto> getVariantsByProductId(String productId);
    ProductVariantResponseDto updateProductVariant(Long variantId, UpdateProductVariantRequestDto updateDTO);
    void deleteProductVariant(Long variantId);
    List<ProductVariant> getProductVariantByIds(Set<Long> variantIds);
    ProductVariant getVariantById(Long variantId);
    void saveProductVariant(ProductVariant productVariant);
}


// Node: repos/cloned_ms_repos/springboot-kafka-microservices/product-service/src/main/java/net/javaguides/product_service/service/ProductVariantService.java:ProductVariantService.<init>
// Node: getVariantById
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

import lombok.RequiredArgsConstructor;
import net.javaguides.product_service.entity.Attribute;
import net.javaguides.product_service.repository.AttributeRepository;
import net.javaguides.product_service.service.AttributeService;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Optional;

@Service
@RequiredArgsConstructor
public class AttributeServiceImpl implements AttributeService {

    private final AttributeRepository attributeRepository;

    @Transactional
    public Attribute createAttribute(String name, String dataType) {
        Optional<Attribute> existingAttribute = attributeRepository.findByName(name);
        if (existingAttribute.isPresent()) {
            throw new IllegalArgumentException("Attribute with name " + name + " already exists.");
        }
        Attribute attribute = new Attribute();
        attribute.setName(name);
        attribute.setDataType(dataType);
        return attributeRepository.save(attribute);
    }

    @Transactional
    public Attribute updateAttribute(Long id, String newName, String newDataType) {
        Attribute attribute = attributeRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Attribute not found."));
        attribute.setName(newName);
        attribute.setDataType(newDataType);
        return attributeRepository.save(attribute);
    }

    @Transactional
    public void deleteAttribute(Long id) {
        attributeRepository.deleteById(id);
    }

    public List<Attribute> getAllAttributes() {
        return attributeRepository.findAll();
    }

    public Attribute getAttributeByName(String name) {
        return attributeRepository.findByName(name)
                .orElseThrow(() -> new RuntimeException("Attribute not found."));
    }
}


// Node: deleteById
package net.javaguides.payment_service.controller;

import lombok.RequiredArgsConstructor;
import net.javaguides.common_lib.dto.ApiResponse;
import net.javaguides.payment_service.dto.PaymentDto;
import net.javaguides.payment_service.entity.Payment;
import net.javaguides.payment_service.service.PaymentService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("api/v1/payment")
@RequiredArgsConstructor
public class PaymentController {
    private final PaymentService paymentService;

    @GetMapping("{orderId}")
    public ResponseEntity<ApiResponse<?>> getPaymentByOrderId(@PathVariable("orderId") String orderId) {
        try {
            PaymentDto payment = paymentService.getPaymentByOrderId(orderId);
            return payment != null
                    ? ResponseEntity.ok(new ApiResponse<>(payment, HttpStatus.OK.value()))
                    : ResponseEntity.status(HttpStatus.NOT_FOUND)
                    .body(new ApiResponse<>("Unknown order ID: " + orderId, HttpStatus.NOT_FOUND.value()));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(new ApiResponse<>(
                                    e.getMessage(),
                                    HttpStatus.INTERNAL_SERVER_ERROR.value()
                            )
                    );
        }
    }

}


// Node: repos/cloned_ms_repos/springboot-kafka-microservices/payment-service/src/main/java/net/javaguides/payment_service/controller/PaymentController.java:PaymentController.<init>
// Node: status
// Node: body
