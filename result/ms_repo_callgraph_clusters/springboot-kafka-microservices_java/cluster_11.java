// Cluster 11

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



// Node: repos/cloned_ms_repos/springboot-kafka-microservices/identity-service/src/main/java/net/javaguides/identity_service/exception/AuthException.java:AuthException.<init>
// Node: AuthException
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


// Node: addNewUser
// Node: saveUser
// Node: getToken
// Node: authenticate
// Node: UsernamePasswordAuthenticationToken
// Node: getUsername
// Node: getPassword
// Node: isAuthenticated
// Node: generateToken
// Node: validateToken
package net.javaguides.identity_service.service;

import jakarta.servlet.http.HttpServletResponse;
import net.javaguides.identity_service.dto.AuthRequest;
import net.javaguides.identity_service.dto.SignUpRequest;
import net.javaguides.identity_service.entity.UserCredential;

public interface AuthService {
    String saveUser(SignUpRequest userCredential);
    String generateToken(AuthRequest authRequest, HttpServletResponse response);
    void validateToken(String token);
}


// Node: repos/cloned_ms_repos/springboot-kafka-microservices/identity-service/src/main/java/net/javaguides/identity_service/service/AuthService.java:AuthService.<init>
package net.javaguides.identity_service.service;

import org.springframework.security.core.Authentication;

import java.util.Set;

public interface JwtService {
    void validateToken(final String token);
    String generateToken(Authentication authentication);
}


// Node: repos/cloned_ms_repos/springboot-kafka-microservices/identity-service/src/main/java/net/javaguides/identity_service/service/JwtService.java:JwtService.<init>
package net.javaguides.identity_service.service.impl;

import io.jsonwebtoken.*;
import io.jsonwebtoken.io.Decoders;
import io.jsonwebtoken.security.Keys;
import net.javaguides.identity_service.config.CustomUserDetails;
import net.javaguides.identity_service.enums.ERole;
import net.javaguides.identity_service.service.JwtService;
import org.springframework.security.authentication.AuthenticationCredentialsNotFoundException;
import org.springframework.security.core.Authentication;
import org.springframework.stereotype.Component;

import javax.crypto.SecretKey;
import java.security.Key;
import java.util.*;

@Component
public class JwtServiceImpl implements JwtService {
    public static final String SECRET = "5367566B59703373367639792F423F4528482B4D6251655468576D5A71347437";

    @Override
    public void validateToken(String token) {
        try {
            Jwts.parser().verifyWith(getSecretKey()).build().parseSignedClaims(token);
        } catch(SecurityException | MalformedJwtException e) {
            throw new AuthenticationCredentialsNotFoundException("JWT was expired or incorrect");
        } catch (ExpiredJwtException e) {
            throw new AuthenticationCredentialsNotFoundException("Expired JWT token.");
        } catch (UnsupportedJwtException e) {
            throw new AuthenticationCredentialsNotFoundException("Unsupported JWT token.");
        } catch (IllegalArgumentException e) {
            throw new AuthenticationCredentialsNotFoundException("JWT token compact of handler are invalid.");
        }
    }

    @Override
    public String generateToken(Authentication authentication) {
        CustomUserDetails userPrincipal = (CustomUserDetails) authentication.getPrincipal();
        List<String> roles = userPrincipal.getRoleNames();

        return Jwts.builder()
                .setSubject(userPrincipal.getUsername())
                .claim("roles", roles)
                .claim("permissions", userPrincipal.getPermissions())
                .claim("email", userPrincipal.getEmail())
                .setIssuedAt(new Date())
                .setExpiration(new Date(System.currentTimeMillis() + 1000 * 60 * 30))
                .signWith(getSignKey(), SignatureAlgorithm.HS256).compact();
    }


    private Key getSignKey() {
        byte[] keyBytes = Decoders.BASE64.decode(SECRET);
        return Keys.hmacShaKeyFor(keyBytes);
    }
    private SecretKey getSecretKey() {
        byte[] keyBytes = Base64.getDecoder().decode(SECRET);
        return Keys.hmacShaKeyFor(keyBytes);
    }

}


// Node: parser
// Node: verifyWith
// Node: getSecretKey
// Node: parseSignedClaims
// Node: AuthenticationCredentialsNotFoundException
// Node: getPrincipal
// Node: builder
// Node: setSubject
// Node: claim
// Node: setIssuedAt
// Node: Date
// Node: setExpiration
// Node: signWith
// Node: getSignKey
// Node: compact
// Node: decode
// Node: hmacShaKeyFor
// Node: getDecoder
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


// Node: getContext
// Node: setAuthentication
// Node: Cookie
// Node: setHttpOnly
// Node: setPath
// Node: setMaxAge
// Node: addCookie
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


// Node: repos/cloned_ms_repos/springboot-kafka-microservices/identity-service/src/main/java/net/javaguides/identity_service/filter/JwtAuthenticationFilter.java:JwtAuthenticationFilter.<init>
// Node: doFilterInternal
// Node: setSigningKey
// Node: parseClaimsJws
// Node: getSubject
// Node: getAuthentication
// Node: getAuthorities
// Node: setDetails
// Node: WebAuthenticationDetailsSource
// Node: buildDetails
// Node: doFilter
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


// Node: repos/cloned_ms_repos/springboot-kafka-microservices/identity-service/src/main/java/net/javaguides/identity_service/config/CustomUserDetails.java:CustomUserDetails.<init>
// Node: CustomUserDetails
package net.javaguides.common_lib.entity;

import jakarta.persistence.*;
import lombok.*;

import java.util.Date;

@MappedSuperclass
@Getter
@Setter
@NoArgsConstructor
public abstract class AbstractEntity {

    @Temporal(TemporalType.TIMESTAMP)
    protected Date createdAt;

    @Temporal(TemporalType.TIMESTAMP)
    protected Date updatedAt;

    @Version
    protected int version;

    @PrePersist
    protected void onCreate() {
        createdAt = new Date();
        updatedAt = new Date();
    }

    @PreUpdate
    protected void onUpdate() {
        updatedAt = new Date();
    }
}


// Node: onCreate
// Node: onUpdate
package net.javaguides.api_gateway.util;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import org.springframework.stereotype.Component;

import javax.crypto.SecretKey;
import java.security.Key;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

@Component
public class JwtUtil {

    private static final String SECRET = "5367566B59703373367639792F423F4528482B4D6251655468576D5A71347437";

    // Validate the token
    public void validateToken(String token) {
        Jwts.parser().setSigningKey(getSignKey()).build().parseClaimsJws(token);
    }

    // Extract roles from the token
    public List<String> extractRoles(String token) {
        Claims claims = getClaims(token);
        List<String> rolesClaim = claims.get("roles", List.class);

        List<String> roles = new ArrayList<>();
        if (rolesClaim != null) {
            for (String role : rolesClaim) {
                if (role != null) {
                    roles.add(role);
                }
            }
        }
        return roles;
    }

    public List<String> extractPermissions(String token) {
        Claims claims = getClaims(token);
        List<String> permissionClaim = claims.get("permissions", List.class);

        List<String> permissions = new ArrayList<>();
        if (permissionClaim != null) {
            for (String permission : permissionClaim) {
                if (permission != null) {
                    permissions.add(permission);
                }
            }
        }
        return permissions;
    }


    private Claims getClaims(String token) {
        return Jwts.parser()
                .setSigningKey(getSignKey())
                .build()
                .parseClaimsJws(token)
                .getBody();
    }

    private Key getSignKey() {
        byte[] keyBytes = io.jsonwebtoken.io.Decoders.BASE64.decode(SECRET);
        return Keys.hmacShaKeyFor(keyBytes);
    }
}


