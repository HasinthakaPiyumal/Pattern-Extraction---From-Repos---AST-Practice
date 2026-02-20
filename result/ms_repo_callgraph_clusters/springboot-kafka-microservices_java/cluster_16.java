// Cluster 16

// Node: currentTimeMillis
// Node: of
// Node: findByProductId
// Node: uploadFile
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


// Node: getFileExtension
// Node: getOriginalFilename
// Node: contains
// Node: substring
// Node: lastIndexOf
// Node: getMultipartFile
// Node: setImageUrl
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


package net.javaguides.product_service;

import net.javaguides.product_service.dto.product.CreateProductRequestDto;
import net.javaguides.product_service.dto.product.ProductResponseDto;
import net.javaguides.product_service.dto.product.ProductCacheDto;
import net.javaguides.product_service.entity.Product;
import net.javaguides.product_service.exception.ProductException;
import net.javaguides.product_service.repository.ProductRepository;
import net.javaguides.product_service.service.CloudinaryService;
import net.javaguides.product_service.redis.ProductRedis;
import net.javaguides.product_service.service.impl.ProductServiceImpl;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.modelmapper.ModelMapper;
import org.springframework.web.multipart.MultipartFile;

import java.math.BigDecimal;
import java.util.Optional;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class ProductServiceImplTest {

    @Mock
    private ProductRepository productRepository;

    @Mock
    private ModelMapper modelMapper;

    @Mock
    private ProductRedis productDAO;

    @Mock
    private CloudinaryService cloudinaryService;

    @InjectMocks
    private ProductServiceImpl productService;

    private CreateProductRequestDto createProductRequestDto;
    private Product product;
    private ProductCacheDto productCacheDto;
    private ProductResponseDto productResponseDto;

    @BeforeEach
    void setUp() {
        // Khởi tạo đối tượng CreateProductRequestDto
        createProductRequestDto = new CreateProductRequestDto();
        createProductRequestDto.setName("Test Product");
        createProductRequestDto.setDescription("Test Description");
        createProductRequestDto.setPrice(new BigDecimal("100.00"));
        createProductRequestDto.setMultipartFile(mock(MultipartFile.class));

        // Khởi tạo đối tượng Product
        product = new Product();
        product.setId(UUID.randomUUID().toString());
        product.setName(createProductRequestDto.getName());
        product.setDescription(createProductRequestDto.getDescription());
        product.setPrice(createProductRequestDto.getPrice());
        product.setImageUrl("http://test.com/image.jpg");

        // Khởi tạo đối tượng ProductCacheDto
        productCacheDto = new ProductCacheDto();
        productCacheDto.setId(product.getId());
        productCacheDto.setName(product.getName());
        productCacheDto.setDescription(product.getDescription());
        productCacheDto.setPrice(product.getPrice());
        productCacheDto.setImageUrl(product.getImageUrl());

        // Khởi tạo đối tượng ProductResponseDto
        productResponseDto = new ProductResponseDto();
        productResponseDto.setId(product.getId());
        productResponseDto.setName(product.getName());
        productResponseDto.setDescription(product.getDescription());
        productResponseDto.setPrice(product.getPrice());
        productResponseDto.setImageUrl(product.getImageUrl());
    }

    @Test
    void testSaveProduct_Success() throws Exception {
        // Mock behavior
        when(modelMapper.map(any(CreateProductRequestDto.class), eq(Product.class))).thenReturn(product);
        when(modelMapper.map(any(Product.class), eq(ProductResponseDto.class))).thenReturn(productResponseDto);
        when(productRepository.save(any(Product.class))).thenReturn(product);
        doNothing().when(productDAO).save(any(Product.class));
        doNothing().when(cloudinaryService).uploadFile(any(MultipartFile.class), anyString());
        when(createProductRequestDto.getMultipartFile().getOriginalFilename()).thenReturn("image.jpg");

        // Thực thi phương thức cần test
        ProductResponseDto responseDto = productService.saveProduct(createProductRequestDto);

        // Kiểm tra kết quả
        assertNotNull(responseDto);
        assertEquals(product.getName(), responseDto.getName());

        verify(productRepository, times(1)).save(any(Product.class));
        verify(productDAO, times(1)).save(any(Product.class));
        verify(cloudinaryService, times(1)).uploadFile(any(MultipartFile.class), anyString());
    }

    @Test
    void testSaveProduct_Exception() throws Exception {
        // Mock behavior để ném ra ngoại lệ khi mapping
        when(modelMapper.map(any(CreateProductRequestDto.class), eq(Product.class))).thenThrow(new RuntimeException("Mapping error"));

        // Thực thi và kiểm tra ngoại lệ
        ProductException exception = assertThrows(ProductException.class, () -> {
            productService.saveProduct(createProductRequestDto);
        });

        assertTrue(exception.getMessage().contains("Failed to create product"));

        verify(productRepository, never()).save(any(Product.class));
    }

    @Test
    void testGetProductById_ProductExistsInCache() {
        // Mock behavior
        when(productDAO.findByProductId(anyString())).thenReturn(productCacheDto);
        when(modelMapper.map(any(ProductCacheDto.class), eq(ProductResponseDto.class))).thenReturn(productResponseDto);

        // Thực thi
        ProductResponseDto responseDto = productService.getProductById(product.getId());

        // Kiểm tra kết quả
        assertNotNull(responseDto);
        verify(productDAO, times(1)).findByProductId(product.getId());
        verify(productRepository, never()).findById(anyString());
    }

    @Test
    void testGetProductById_ProductNotInCacheButExistsInDB() {
        // Mock behavior
        when(productDAO.findByProductId(anyString())).thenReturn(null);
        when(productRepository.findById(anyString())).thenReturn(Optional.of(product));
        when(modelMapper.map(any(Product.class), eq(ProductResponseDto.class))).thenReturn(productResponseDto);
        doNothing().when(productDAO).save(any(Product.class));

        // Thực thi
        ProductResponseDto responseDto = productService.getProductById(product.getId());

        // Kiểm tra kết quả
        assertNotNull(responseDto);
        verify(productDAO, times(1)).findByProductId(product.getId());
        verify(productRepository, times(1)).findById(product.getId());
    }

    @Test
    void testGetProductById_ProductNotFound() {
        // Mock behavior
        when(productDAO.findByProductId(anyString())).thenReturn(null);
        when(productRepository.findById(anyString())).thenReturn(Optional.empty());

        // Thực thi và kiểm tra ngoại lệ
        ProductException exception = assertThrows(ProductException.class, () -> {
            productService.getProductById("non-existing-id");
        });

        assertTrue(exception.getMessage().contains("Product not found with id"));

        verify(productDAO, times(1)).findByProductId("non-existing-id");
        verify(productRepository, times(1)).findById("non-existing-id");
    }
}


// Node: setUp
// Node: CreateProductRequestDto
// Node: setDescription
// Node: BigDecimal
// Node: setMultipartFile
// Node: mock
// Node: Product
// Node: getDescription
// Node: ProductCacheDto
// Node: ProductResponseDto
// Node: testSaveProduct_Success
// Node: when
// Node: any
// Node: eq
// Node: thenReturn
// Node: doNothing
// Node: anyString
// Node: assertNotNull
// Node: assertEquals
// Node: verify
// Node: times
// Node: testSaveProduct_Exception
// Node: thenThrow
// Node: assertThrows
// Node: assertTrue
// Node: never
// Node: testGetProductById_ProductExistsInCache
// Node: testGetProductById_ProductNotInCacheButExistsInDB
// Node: testGetProductById_ProductNotFound
// Node: empty
package net.javaguides.api_gateway.filter;

import org.springframework.http.server.reactive.ServerHttpRequest;
import org.springframework.stereotype.Component;

import java.util.List;
import java.util.function.Predicate;

@Component
public class RouteValidator {
    public static final List<String> openApiEndpoints = List.of(
            "/api/v1/auth/register",
            "/api/v1/auth/token",
            "/eureka"
    );

    public Predicate<ServerHttpRequest> isSecured =
            request -> openApiEndpoints
                    .stream()
                    .noneMatch(uri -> request.getURI().getPath().contains(uri));
}


// Node: repos/cloned_ms_repos/springboot-kafka-microservices/api-gateway/src/main/java/net/javaguides/api_gateway/filter/RouteValidator.java:RouteValidator.<init>
// Node: noneMatch
// Node: getURI
// Node: getPath
