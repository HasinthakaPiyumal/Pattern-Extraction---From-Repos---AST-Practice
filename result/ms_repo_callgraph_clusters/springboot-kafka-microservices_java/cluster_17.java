// Cluster 17

package net.javaguides.identity_service.repository;

import net.javaguides.identity_service.entity.UserCredential;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface UserCredentialRepository extends JpaRepository<UserCredential, Long> {
    Optional<UserCredential> findByName(String username);
}


// Node: repos/cloned_ms_repos/springboot-kafka-microservices/identity-service/src/main/java/net/javaguides/identity_service/repository/UserCredentialRepository.java:UserCredentialRepository.<init>
// Node: findByName
package net.javaguides.identity_service.repository;

import net.javaguides.identity_service.entity.Role;
import net.javaguides.identity_service.enums.ERole;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface RoleRepository extends JpaRepository<Role, Long> {
    Optional<Role> findByName(ERole name);
}

// Node: repos/cloned_ms_repos/springboot-kafka-microservices/identity-service/src/main/java/net/javaguides/identity_service/repository/RoleRepository.java:RoleRepository.<init>
package net.javaguides.identity_service.service.impl;

import net.javaguides.identity_service.config.CustomUserDetails;
import net.javaguides.identity_service.entity.UserCredential;
import net.javaguides.identity_service.repository.UserCredentialRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.core.userdetails.User;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class UserDetailsServiceImpl implements UserDetailsService {
    @Autowired
    private UserCredentialRepository userRepository;

    @Override
    @Transactional
    public UserDetails loadUserByUsername(String username) throws UsernameNotFoundException {
        UserCredential user = userRepository.findByName(username)
                .orElseThrow(() -> new UsernameNotFoundException("User Not Found with username: " + username));

        return CustomUserDetails.build(user);
    }

}

// Node: repos/cloned_ms_repos/springboot-kafka-microservices/identity-service/src/main/java/net/javaguides/identity_service/service/impl/UserDetailsServiceImpl.java:UserDetailsServiceImpl.<init>
// Node: loadUserByUsername
// Node: orElseThrow
// Node: UsernameNotFoundException
package net.javaguides.identity_service.service.impl;

import jakarta.servlet.http.Cookie;
import jakarta.servlet.http.HttpServletResponse;
import jakarta.ws.rs.core.SecurityContext;
import lombok.RequiredArgsConstructor;
import net.javaguides.identity_service.config.CustomUserDetails;
import net.javaguides.identity_service.dto.AuthRequest;
import net.javaguides.identity_service.dto.SignUpRequest;
import net.javaguides.identity_service.entity.Role;
import net.javaguides.identity_service.entity.UserCredential;
import net.javaguides.identity_service.enums.ERole;
import net.javaguides.identity_service.exception.AuthException;
import net.javaguides.identity_service.repository.RoleRepository;
import net.javaguides.identity_service.repository.UserCredentialRepository;
import net.javaguides.identity_service.service.AuthService;
import net.javaguides.identity_service.service.JwtService;
import org.springframework.http.HttpStatus;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

import java.util.HashSet;
import java.util.Optional;
import java.util.Set;

@Service
@RequiredArgsConstructor
public class AuthServiceImpl implements AuthService {
    private final UserCredentialRepository userCredentialRepository;
    private final PasswordEncoder passwordEncoder;
    private final JwtService jwtService;
    private final RoleRepository roleRepository;
    private final AuthenticationManager authenticationManager;

    @Override
    public String saveUser(SignUpRequest signUpRequest) {
        try {
            boolean existingUsername = checkExistingUsername(signUpRequest.getName());
            if(existingUsername){
                throw new AuthException("Username already exists in the database!", HttpStatus.BAD_REQUEST);
            }
            UserCredential userCredential = new UserCredential();
            userCredential.setName(signUpRequest.getName());
            userCredential.setEmail(signUpRequest.getEmail());
            userCredential.setPassword(passwordEncoder.encode(signUpRequest.getPassword()));
            Set<Role> roles = new HashSet<>();
            if(signUpRequest.getRoles() == null){
                Role role = roleRepository.findByName(ERole.CUSTOMER)
                        .orElseThrow(() -> new RuntimeException("Role not found"));
                roles.add(role);
            }else{
                for (String roleName : signUpRequest.getRoles()) {
                    ERole eRole;
                    try {
                        eRole = ERole.valueOf(roleName.toUpperCase());  // Chuyển vai trò sang chữ in hoa
                    } catch (IllegalArgumentException e) {
                        throw new RuntimeException("Invalid role name: " + roleName);
                    }

                    Role role = roleRepository.findByName(eRole)
                            .orElseThrow(() -> new RuntimeException("Role not found"));
                    roles.add(role);
                }
            }
            userCredential.setRoles(roles);
            userCredentialRepository.save(userCredential);
            return "User added to the system!";
        }catch(Exception e){
            throw new RuntimeException("Error registering user: " + e.getMessage());
        }
    }

    @Override
    public String generateToken(AuthRequest authRequest, HttpServletResponse response) {
        Authentication authentication = authenticationManager.authenticate(new UsernamePasswordAuthenticationToken(authRequest.getUsername(), authRequest.getPassword()));

        Optional<UserCredential> optionalUser = userCredentialRepository.findByName(authRequest.getUsername());
        if(!optionalUser.isPresent()){
            throw new AuthException("Invalid credentials! Please try again!",HttpStatus.UNAUTHORIZED);
        }

        UserCredential userCredential = optionalUser.get();
        SecurityContextHolder.getContext().setAuthentication(authentication);



        CustomUserDetails userDetails = (CustomUserDetails) authentication.getPrincipal();
        String jwtToken = jwtService.generateToken(authentication);

        Cookie cookie = new Cookie("token", jwtToken);
        cookie.setHttpOnly(true);
        cookie.setPath("/");
        cookie.setMaxAge(30 * 60);
        response.addCookie(cookie);
        return jwtToken;
    }

    @Override
    public void validateToken(String token) {
        jwtService.validateToken(token);
    }

    private boolean checkExistingUsername(String username){
        return userCredentialRepository.findByName(username).isPresent();
    }
}


// Node: checkExistingUsername
// Node: getName
// Node: UserCredential
// Node: setName
// Node: encode
// Node: RuntimeException
// Node: add
// Node: toUpperCase
// Node: save
// Node: isPresent
package net.javaguides.identity_service.config;
import net.javaguides.identity_service.entity.UserCredential;
import net.javaguides.identity_service.repository.UserCredentialRepository;
import net.javaguides.identity_service.service.impl.UserDetailsServiceImpl;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.stereotype.Component;

import java.util.Optional;

@Component
public class CustomUserDetailsService implements UserDetailsService {

    @Autowired
    private UserCredentialRepository repository;

    @Override
    public UserDetails loadUserByUsername(String username) throws UsernameNotFoundException {
        UserCredential credential = repository.findByName(username).orElseThrow(() -> new UsernameNotFoundException("User not found with username: " + username));
        return CustomUserDetails.build(credential);
    }
}

// Node: repos/cloned_ms_repos/springboot-kafka-microservices/identity-service/src/main/java/net/javaguides/identity_service/config/CustomUserDetailsService.java:CustomUserDetailsService.<init>
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


// Node: IllegalArgumentException
// Node: findById
// Node: setPrice
// Node: delete
// Node: getProduct
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


// Node: repos/cloned_ms_repos/springboot-kafka-microservices/product-service/src/main/java/net/javaguides/product_service/exception/ProductException.java:ProductException.<init>
// Node: ProductException
package net.javaguides.product_service.repository;

import net.javaguides.product_service.entity.Attribute;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.Optional;

public interface AttributeRepository extends JpaRepository<Attribute, Long> {
    Optional<Attribute> findByName(String name);
}


// Node: repos/cloned_ms_repos/springboot-kafka-microservices/product-service/src/main/java/net/javaguides/product_service/repository/AttributeRepository.java:AttributeRepository.<init>
// Node: setStockQuantity
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


// Node: buildProductStockResponse
// Node: ProductStockResponse
// Node: setProduct
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


// Node: ProductVariant
// Node: setSku
// Node: setReorderLevel
// Node: AttributeValue
// Node: setProductVariant
// Node: setAttribute
// Node: setValue
// Node: getAttributeValues
// Node: clear
// Node: getAttribute
// Node: deleteStock
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


// Node: Attribute
// Node: setDataType
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


// Node: Category
// Node: getParentId
// Node: setParent
// Node: convertToDto
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


