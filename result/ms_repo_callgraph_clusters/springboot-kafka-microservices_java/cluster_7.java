// Cluster 7

// Node: getMessage
// Node: getOrderId
package net.javaguides.order_service.redis;

import net.javaguides.common_lib.dto.order.OrderDTO;
import net.javaguides.order_service.entity.Order;
import org.apache.kafka.common.errors.ResourceNotFoundException;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Repository;

import java.time.Duration;

@Repository
public class OrderRedis {
    private static final String HASH_KEY = "Order";
    @Autowired
    private RedisTemplate redisTemplate;

    public void save(OrderDTO order) {
        try {
            redisTemplate.opsForHash().put(HASH_KEY, order.getOrderId(), order);
            redisTemplate.expire(HASH_KEY, Duration.ofHours(1));

        } catch (Exception e) {
            throw new RuntimeException("Error saving order in Redis: " + e.getMessage(), e);
        }
    }

    public OrderDTO findByOrderId(String id) {
        try {
            return (OrderDTO) redisTemplate.opsForHash().get(HASH_KEY, id);
        } catch (Exception e) {
            return null;
        }
    }

    public void deleteByOrderId(String id) {
        try {
            redisTemplate.opsForHash().delete(HASH_KEY, id);
        } catch (Exception e) {
            throw new ResourceNotFoundException("Not Found", e);
        }
    }
}


// Node: opsForHash
// Node: put
// Node: expire
// Node: ofHours
// Node: deleteByOrderId
// Node: ResourceNotFoundException
package net.javaguides.product_service.exception;

import net.javaguides.common_lib.dto.ApiResponse;
import org.apache.kafka.common.errors.ResourceNotFoundException;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ControllerAdvice;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.multipart.MultipartException;

@ControllerAdvice
public class GlobalException {

    @ExceptionHandler(MultipartException.class)
    public ResponseEntity<ApiResponse<String>> handleMultipartException(MultipartException e) {
        return new ResponseEntity<>(new ApiResponse<>(e.getMessage(), HttpStatus.BAD_REQUEST.value()), HttpStatus.BAD_REQUEST);
    }

    @ExceptionHandler(ResourceNotFoundException.class)
    public ResponseEntity<ApiResponse<String>> handleResourceNotFoundException(ResourceNotFoundException ex) {
        ApiResponse<String> response = new ApiResponse<>(ex.getMessage(), HttpStatus.NOT_FOUND.value());
        return new ResponseEntity<>(response, HttpStatus.NOT_FOUND);
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<ApiResponse<String>> handleException(Exception ex) {
        ApiResponse<String> response = new ApiResponse<>(ex.getMessage(), HttpStatus.INTERNAL_SERVER_ERROR.value());
        return new ResponseEntity<>(response, HttpStatus.INTERNAL_SERVER_ERROR);
    }
}


// Node: repos/cloned_ms_repos/springboot-kafka-microservices/product-service/src/main/java/net/javaguides/product_service/exception/GlobalException.java:GlobalException.<init>
// Node: ExceptionHandler
// Node: handleMultipartException
// Node: handleResourceNotFoundException
// Node: handleException
// Node: deleteByProductId
package net.javaguides.product_service.redis;

import net.javaguides.product_service.dto.product.ProductCacheDto;
import net.javaguides.product_service.entity.Product;
import org.apache.kafka.common.errors.ResourceNotFoundException;
import org.modelmapper.ModelMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Repository;

import java.time.Duration;

@Repository
public class ProductRedis {
    private static final String HASH_KEY = "Product";

    @Autowired
    private RedisTemplate<String, ProductCacheDto> redisTemplate;

    @Autowired
    private ModelMapper modelMapper;

    public void save(Product product){
        try {
            if(product.getImageUrl() != null){
                ProductCacheDto productCacheDto = modelMapper.map(product, ProductCacheDto.class);

                redisTemplate.opsForHash().put(HASH_KEY, product.getId(), productCacheDto);
                redisTemplate.expire(HASH_KEY, Duration.ofHours(1));
            }
        }catch(Exception e){
            throw new RuntimeException("Error to save product in redis: " + e.getMessage());
        }
    }

    public ProductCacheDto findByProductId(String id){
        try {
            return (ProductCacheDto) redisTemplate.opsForHash().get(HASH_KEY, id);
        }catch(Exception e){
            return null;
        }
    }

    public void deleteByProductId(String id){
        try {
            redisTemplate.opsForHash().delete(HASH_KEY, id);
        }catch(Exception e){
            throw new ResourceNotFoundException("Not Found", e);
        }
    }

}


package net.javaguides.product_service.handler;

import net.javaguides.common_lib.dto.ApiResponse;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import java.util.HashMap;
import java.util.Map;

@RestControllerAdvice
public class ValidationExceptionHandler {

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ApiResponse<?>> handleValidationExceptions(MethodArgumentNotValidException ex) {
        Map<String, String> errors = new HashMap<>();
        ex.getBindingResult().getFieldErrors().forEach(error ->
                errors.put(error.getField(), error.getDefaultMessage())
        );

        // Tạo ApiResponse với lỗi
        ApiResponse<Map<String, String>> apiResponse = new ApiResponse<>(errors, HttpStatus.BAD_REQUEST.value());

        return new ResponseEntity<>(apiResponse, HttpStatus.BAD_REQUEST);
    }
}

// Node: repos/cloned_ms_repos/springboot-kafka-microservices/product-service/src/main/java/net/javaguides/product_service/handler/ValidationExceptionHandler.java:ValidationExceptionHandler.<init>
// Node: handleValidationExceptions
// Node: getBindingResult
// Node: getFieldErrors
// Node: forEach
// Node: getField
// Node: getDefaultMessage
package net.javaguides.payment_service.redis;

import net.javaguides.payment_service.entity.Payment;
import org.apache.kafka.common.errors.ResourceNotFoundException;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Repository;

import java.time.Duration;

@Repository
public class PaymentRedis {
    private static final String HASH_KEY = "Payment";
    @Autowired
    private RedisTemplate redisTemplate;

    public void save(Payment payment) {
        try {
            redisTemplate.opsForHash().put(HASH_KEY, payment.getOrderId(), payment);
            redisTemplate.expire(HASH_KEY, Duration.ofHours(1));

        } catch (Exception e) {
            throw new RuntimeException("Error saving payment in Redis: " + e.getMessage(), e);
        }
    }

    public Payment findByOrderId(String orderId) {
        try {
            return (Payment) redisTemplate.opsForHash().get(HASH_KEY, orderId);
        } catch (Exception e) {
            return null;
        }
    }

    public void deleteByOrderId(String id) {
        try {
            redisTemplate.opsForHash().delete(HASH_KEY, id);
        } catch (Exception e) {
            throw new ResourceNotFoundException("Not Found", e);
        }
    }
}


