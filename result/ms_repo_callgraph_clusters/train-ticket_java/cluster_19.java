// Cluster 19

package auth.constant;

/**
 * @author fdse
 */
public class AuthConstant {

    private AuthConstant() {
        throw new IllegalStateException("Utility class");
    }

    public static final String ROLE_USER = "ROLE_USER";
    public static final String ROLE_ADMIN = "ROLE_ADMIN";
}


// Node: repos/cloned_ms_repos/train-ticket/ts-auth-service/src/main/java/auth/constant/AuthConstant.java:AuthConstant.<init>
// Node: AuthConstant
// Node: IllegalStateException
package auth.constant;

/**
 * @author fdse
 */
public class InfoConstant {

    private InfoConstant() {
        throw new IllegalStateException("Utility class");
    }

    // User service information. If require params, the suffix number is the number of params

    public static final String DUPLICATE = "Duplicate";
    public static final String USER_HAS_ALREADY_EXIST = "User has already exist.";
    public static final String PROPERTIES_CANNOT_BE_EMPTY_1 = "{0} cannot be empty.";
    public static final String USER_IS_NOT_EXIST_2 = "User is not exist, {0}: {1}.";
    public static final String PASSWORD_LEAST_CHAR_1 = "Passwords must contain at least {0} characters."; //NOSONAR
    public static final String USER_NAME_NOT_FOUND_1 = "Username not found: {0}.";

    // User properties

    public static final String ID = "id";
    public static final String USERNAME = "username";
    public static final String PASSWORD = "password"; //NOSONAR
    public static final String ROLES = "roles";

}


// Node: repos/cloned_ms_repos/train-ticket/ts-auth-service/src/main/java/auth/constant/InfoConstant.java:InfoConstant.<init>
// Node: InfoConstant
package auth.security.jwt;

import auth.constant.InfoConstant;
import auth.entity.User;
import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.SignatureAlgorithm;
import org.springframework.stereotype.Component;

import javax.annotation.PostConstruct;
import java.util.Base64;
import java.util.Date;

/**
 * @author fdse
 */
@Component
public class JWTProvider {

    private String secretKey = "secret";

    private long validityInMilliseconds = 3600000;

    @PostConstruct
    protected void init() {
        secretKey = Base64.getEncoder().encodeToString(secretKey.getBytes());
    }

    public String createToken(User user) {

        Claims claims = Jwts.claims().setSubject(user.getUsername());
        claims.put(InfoConstant.ROLES, user.getRoles());
        claims.put(InfoConstant.ID, user.getUserId());

        Date now = new Date();
        Date validate = new Date(now.getTime() + validityInMilliseconds);

        return Jwts.builder()
                .setClaims(claims)
                .setIssuedAt(now)
                .setExpiration(validate)
                .signWith(SignatureAlgorithm.HS256, secretKey)
                .compact();
    }
}

// Node: init
// Node: getEncoder
// Node: encodeToString
// Node: getBytes
package edu.fudan.common.util;

import com.fasterxml.jackson.databind.ObjectMapper;

import java.io.IOException;
import java.util.Map;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
/**
 * @author fdse
 */
public class JsonUtils {

    private static final Logger LOGGER = LoggerFactory.getLogger(JsonUtils.class);

    private JsonUtils() {
        throw new IllegalStateException("Utility class");
    }

    /**
     * <p>
     * Object to JSON string
     * </p>
     */
    public static String object2Json(Object obj) {
        String result = null;
        try {
            ObjectMapper objectMapper = new ObjectMapper();
            result = objectMapper.writeValueAsString(obj);
        } catch (IOException e) {
            JsonUtils.LOGGER.error("[object2Json][writeValueAsString][IOException: {}]", e.getMessage());
        }
        return result;
    }


    public static Map object2Map(Object obj) {
        String object2Json = object2Json(obj);
        Map<?, ?> result = jsonToMap(object2Json);
        return result;
    }

    /**
     * <p>
     * JSON string to Map object
     * </p>
     */
    public static Map<?, ?> jsonToMap(String json) {
        return json2Object(json, Map.class);
    }

    /**
     * <p>
     * JSON to Object
     * </p>
     */
    public static <T> T json2Object(String json, Class<T> cls) {
        T result = null;
        try {
            ObjectMapper objectMapper = new ObjectMapper();
            result = objectMapper.readValue(json, cls);
        } catch (NullPointerException e) {
            JsonUtils.LOGGER.error("[json2Object][objectMapper.readValue][NullPointerException: {}]",e.getMessage());
        } catch (IOException e) {
            JsonUtils.LOGGER.error("[json2Object][objectMapper.readValue][IOException: {}]",e.getMessage());
        }

        return result;
    }


    public static <T> T conveterObject(Object srcObject, Class<T> destObjectType) {
        String jsonContent = object2Json(srcObject);
        return json2Object(jsonContent, destObjectType);
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-common/src/main/java/edu/fudan/common/util/JsonUtils.java:JsonUtils.<init>
// Node: JsonUtils
package edu.fudan.common.security.jwt;

import edu.fudan.common.exception.TokenException;
import io.jsonwebtoken.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.userdetails.UserDetails;

import javax.servlet.ServletRequest;
import javax.servlet.http.HttpServletRequest;
import java.util.Base64;
import java.util.Collection;
import java.util.Date;
import java.util.List;
import java.util.stream.Collectors;

/**
 * @author fdse
 */
public class JWTUtil {

    private JWTUtil() {
        throw new IllegalStateException("Utility class");
    }

    private static final Logger LOGGER = LoggerFactory.getLogger(JWTUtil.class);
    private static String secretKey = Base64.getEncoder().encodeToString("secret".getBytes());


    public static Authentication getJWTAuthentication(ServletRequest request) {
        String token = getTokenFromHeader((HttpServletRequest) request);
        if (token != null && validateToken(token)) {

            UserDetails userDetails = new UserDetails() {
                @Override
                public Collection<? extends GrantedAuthority> getAuthorities() {
                    return getRole(token).stream().map(SimpleGrantedAuthority::new).collect(Collectors.toList());
                }

                @Override
                public String getPassword() {
                    return "";
                }

                @Override
                public String getUsername() {
                    return getUserName(token);
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
            };
            // send to spring security
            return new UsernamePasswordAuthenticationToken(userDetails, "", userDetails.getAuthorities());
        }
        return null;
    }

    private static String getUserName(String token) {
        return getClaims(token).getBody().getSubject();
    }

    private static List<String> getRole(String token) {
        Jws<Claims> claimsJws = getClaims(token);
        return (List<String>) (claimsJws.getBody().get("roles", List.class));
    }

    private static String getTokenFromHeader(HttpServletRequest request) {
        String bearerToken = request.getHeader("Authorization");
        if (bearerToken != null && bearerToken.startsWith("Bearer ")) {
            return bearerToken.substring(7, bearerToken.length());
        }
        return null;
    }

    private static boolean validateToken(String token) {
        try {
            Jws<Claims> claimsJws = getClaims(token);
            return !claimsJws.getBody().getExpiration().before(new Date());
        } catch (ExpiredJwtException e) {
            LOGGER.error("[validateToken][getClaims][Token expired][ExpiredJwtException: {} ]" , e);
            throw new TokenException("Token expired");
        } catch (UnsupportedJwtException e) {
            LOGGER.error("[validateToken][getClaims][Token format error][UnsupportedJwtException: {}]", e);
            throw new TokenException("Token format error");
        } catch (MalformedJwtException e) {
            LOGGER.error("[validateToken][getClaims][Token is not properly constructed][MalformedJwtException: {}]", e);
            throw new TokenException("Token is not properly constructed");
        } catch (SignatureException e) {
            LOGGER.error("[validateToken][getClaims][Signature failure][SignatureException: {}]", e);
            throw new TokenException("Signature failure");
        } catch (IllegalArgumentException e) {
            LOGGER.error("[validateToken][getClaims][Illegal parameter exception][IllegalArgumentException: {}]", e);
            throw new TokenException("Illegal parameter exception");
        }
    }

    private static Jws<Claims> getClaims(String token) {
        return Jwts.parser().setSigningKey(secretKey).parseClaimsJws(token);
    }

}


// Node: repos/cloned_ms_repos/train-ticket/ts-common/src/main/java/edu/fudan/common/security/jwt/JWTUtil.java:JWTUtil.<init>
// Node: JWTUtil
package inside_payment.util;

import javax.servlet.http.Cookie;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.util.HashMap;
import java.util.Map;

/**
 * @author fdse
 */
public class CookieUtil {

    private CookieUtil() {
        throw new IllegalStateException("Utility class");
    }

    public static void addCookie(HttpServletResponse response, String name, String value, int maxAge){
        Cookie cookie = new Cookie(name,value);
        // against Cross-Site Scripting (XSS) attacks
        cookie.setHttpOnly(true);
        cookie.setPath("/");
        if(maxAge>0) {
            cookie.setMaxAge(maxAge);
        }
        response.addCookie(cookie);
    }

    public static Cookie getCookieByName(HttpServletRequest request, String name){
        Map<String,Cookie> cookieMap = readCookieMap(request);
        if(cookieMap.containsKey(name)){
            return cookieMap.get(name);
        }else{
            return null;
        }
    }

    private static Map<String,Cookie> readCookieMap(HttpServletRequest request){
        Map<String,Cookie> cookieMap = new HashMap<>();
        Cookie[] cookies = request.getCookies();
        if(null!=cookies){
            for(Cookie cookie : cookies){
                cookieMap.put(cookie.getName(), cookie);
            }
        }
        return cookieMap;
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-inside-payment-service/src/main/java/inside_payment/util/CookieUtil.java:CookieUtil.<init>
// Node: CookieUtil
package verifycode.util;

import javax.servlet.http.Cookie;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.util.HashMap;
import java.util.Map;

/**
 * @author fdse
 */
public class CookieUtil {

    private CookieUtil() {
        throw new IllegalStateException("Utility class");
    }

    public static void addCookie(HttpServletResponse response, String name, String value, int maxAge){
        Cookie cookie = new Cookie(name,value);
        // against Cross-Site Scripting (XSS) attacks.
        cookie.setHttpOnly(true);
        cookie.setPath("/");
        if(maxAge>0) {
            cookie.setMaxAge(maxAge);
        }
        response.addCookie(cookie);
    }

    public static Cookie getCookieByName(HttpServletRequest request, String name){
        Map<String,Cookie> cookieMap = readCookieMap(request);
        return cookieMap.getOrDefault(name, null);
    }

    private static Map<String,Cookie> readCookieMap(HttpServletRequest request){
        Map<String,Cookie> cookieMap = new HashMap<>();
        Cookie[] cookies = request.getCookies();
        if(null!=cookies){
            for(Cookie cookie : cookies){
                cookieMap.put(cookie.getName(), cookie);
            }
        }
        return cookieMap;
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-verification-code-service/src/main/java/verifycode/util/CookieUtil.java:CookieUtil.<init>


package org.myproject.ms.monitoring.util;

import org.apache.commons.logging.Log;


public final class ExceptionUtils {
	private static final Log log = org.apache.commons.logging.LogFactory
			.getLog(ExceptionUtils.class);
	private static boolean fail = false;
	private static Exception lastException = null;

	private ExceptionUtils() {
		throw new IllegalStateException("Utility class can't be instantiated");
	}

	public static void warn(String msg) {
		log.warn(msg);
		if (fail) {
			IllegalStateException exception = new IllegalStateException(msg);
			ExceptionUtils.lastException = exception;
			throw exception;
		}
	}

	public static Exception getLastException() {
		return ExceptionUtils.lastException;
	}

	public static void setFail(boolean fail) {
		ExceptionUtils.fail = fail;
		ExceptionUtils.lastException = null;
	}

	public static String getExceptionMessage(Throwable e) {
		return e.getMessage() != null ? e.getMessage() : e.toString();
	}
}


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/util/ExceptionUtils.java:ExceptionUtils.<init>
// Node: ExceptionUtils


package org.myproject.ms.monitoring.antn;

import java.lang.annotation.Annotation;
import java.lang.invoke.MethodHandles;
import java.lang.reflect.Method;
import java.util.concurrent.atomic.AtomicBoolean;
import javax.annotation.PostConstruct;

import org.aopalliance.aop.Advice;
import org.aopalliance.intercept.MethodInvocation;
import org.apache.commons.logging.Log;
import org.apache.commons.logging.LogFactory;
import org.springframework.aop.ClassFilter;
import org.springframework.aop.IntroductionAdvisor;
import org.springframework.aop.IntroductionInterceptor;
import org.springframework.aop.Pointcut;
import org.springframework.aop.support.AbstractPointcutAdvisor;
import org.springframework.aop.support.AopUtils;
import org.springframework.aop.support.DynamicMethodMatcherPointcut;
import org.springframework.aop.support.annotation.AnnotationClassFilter;
import org.springframework.beans.BeansException;
import org.springframework.beans.factory.BeanFactory;
import org.springframework.beans.factory.BeanFactoryAware;
import org.myproject.ms.monitoring.Item;
import org.myproject.ms.monitoring.Chainer;
import org.myproject.ms.monitoring.util.ExceptionUtils;
import org.springframework.core.annotation.AnnotationUtils;
import org.springframework.util.ObjectUtils;
import org.springframework.util.ReflectionUtils;
import org.springframework.util.StringUtils;


class SleuthAdvisorConfig  extends AbstractPointcutAdvisor implements
		IntroductionAdvisor, BeanFactoryAware {
	private static final Log log = LogFactory.getLog(MethodHandles.lookup().lookupClass());

	private Advice advice;

	private Pointcut pointcut;

	private BeanFactory beanFactory;

	@PostConstruct
	public void init() {
		this.pointcut = buildPointcut();
		this.advice = buildAdvice();
		if (this.advice instanceof BeanFactoryAware) {
			((BeanFactoryAware) this.advice).setBeanFactory(this.beanFactory);
		}
	}

	
	@Override
	public void setBeanFactory(BeanFactory beanFactory) {
		this.beanFactory = beanFactory;
	}

	@Override
	public ClassFilter getClassFilter() {
		return this.pointcut.getClassFilter();
	}

	@Override
	public Class<?>[] getInterfaces() {
		return new Class[] {};
	}

	@Override
	public void validateInterfaces() throws IllegalArgumentException {
	}

	@Override
	public Advice getAdvice() {
		return this.advice;
	}

	@Override
	public Pointcut getPointcut() {
		return this.pointcut;
	}

	private Advice buildAdvice() {
		return new SleuthInterceptor();
	}

	private Pointcut buildPointcut() {
		return new AnnotationClassOrMethodOrArgsPointcut();
	}

	
	private final class AnnotationClassOrMethodOrArgsPointcut extends
			DynamicMethodMatcherPointcut {

		private final DynamicMethodMatcherPointcut methodResolver;

		AnnotationClassOrMethodOrArgsPointcut() {
			this.methodResolver = new DynamicMethodMatcherPointcut() {
				@Override public boolean matches(Method method, Class<?> targetClass,
						Object... args) {
					if (SleuthAnnotationUtils.isMethodAnnotated(method)) {
						if (log.isDebugEnabled()) {
							log.debug("Found a method with Sleuth annotation");
						}
						return true;
					}
					if (SleuthAnnotationUtils.hasAnnotatedParams(method, args)) {
						if (log.isDebugEnabled()) {
							log.debug("Found annotated arguments of the method");
						}
						return true;
					}
					return false;
				}
			};
		}

		@Override
		public boolean matches(Method method, Class<?> targetClass, Object... args) {
			return getClassFilter().matches(targetClass) ||
					this.methodResolver.matches(method, targetClass, args);
		}

		@Override public ClassFilter getClassFilter() {
			return new ClassFilter() {
				@Override public boolean matches(Class<?> clazz) {
					return new AnnotationClassOrMethodFilter(NewSpan.class).matches(clazz) ||
							new AnnotationClassOrMethodFilter(ContinueSpan.class).matches(clazz);
				}
			};
		}

		@Override
		public boolean equals(Object other) {
			if (this == other) {
				return true;
			}
			if (!(other instanceof AnnotationClassOrMethodOrArgsPointcut)) {
				return false;
			}
			AnnotationClassOrMethodOrArgsPointcut otherAdvisor = (AnnotationClassOrMethodOrArgsPointcut) other;
			return ObjectUtils.nullSafeEquals(this.methodResolver, otherAdvisor.methodResolver);
		}

	}

	private final class AnnotationClassOrMethodFilter extends AnnotationClassFilter {

		private final AnnotationMethodsResolver methodResolver;

		AnnotationClassOrMethodFilter(Class<? extends Annotation> annotationType) {
			super(annotationType, true);
			this.methodResolver = new AnnotationMethodsResolver(annotationType);
		}

		@Override
		public boolean matches(Class<?> clazz) {
			return super.matches(clazz) || this.methodResolver.hasAnnotatedMethods(clazz);
		}

	}

	
	private static class AnnotationMethodsResolver {

		private Class<? extends Annotation> annotationType;

		public AnnotationMethodsResolver(Class<? extends Annotation> annotationType) {
			this.annotationType = annotationType;
		}

		public boolean hasAnnotatedMethods(Class<?> clazz) {
			final AtomicBoolean found = new AtomicBoolean(false);
			ReflectionUtils.doWithMethods(clazz,
					new ReflectionUtils.MethodCallback() {
						@Override
						public void doWith(Method method) throws IllegalArgumentException,
								IllegalAccessException {
							if (found.get()) {
								return;
							}
							Annotation annotation = AnnotationUtils.findAnnotation(method,
									AnnotationMethodsResolver.this.annotationType);
							if (annotation != null) { found.set(true); }
						}
					});
			return found.get();
		}

	}
}


class SleuthInterceptor  implements IntroductionInterceptor, BeanFactoryAware  {

	private static final Log logger = LogFactory.getLog(MethodHandles.lookup().lookupClass());

	private BeanFactory beanFactory;
	private SpanCreator spanCreator;
	private Chainer tracer;
	private SpanTagAnnotationHandler spanTagAnnotationHandler;

	@Override
	public Object invoke(MethodInvocation invocation) throws Throwable {
		Method method = invocation.getMethod();
		if (method == null) {
			return invocation.proceed();
		}
		Method mostSpecificMethod = AopUtils
				.getMostSpecificMethod(method, invocation.getThis().getClass());
		NewSpan newSpan = SleuthAnnotationUtils.findAnnotation(mostSpecificMethod, NewSpan.class);
		ContinueSpan continueSpan = SleuthAnnotationUtils.findAnnotation(mostSpecificMethod, ContinueSpan.class);
		if (newSpan == null && continueSpan == null) {
			return invocation.proceed();
		}
		Item span = tracer().getCurrentSpan();
		String log = log(continueSpan);
		boolean hasLog = StringUtils.hasText(log);
		try {
			if (newSpan != null) {
				span = spanCreator().createSpan(invocation, newSpan);
			}
			if (hasLog) {
				logEvent(span, log + ".before");
			}
			spanTagAnnotationHandler().addAnnotatedParameters(invocation);
			return invocation.proceed();
		} catch (Exception e) {
			if (logger.isDebugEnabled()) {
				logger.debug("Exception occurred while trying to continue the pointcut", e);
			}
			if (hasLog) {
				logEvent(span, log + ".afterFailure");
			}
			tracer().addTag(Item.SPAN_ERROR_TAG_NAME, ExceptionUtils.getExceptionMessage(e));
			throw e;
		} finally {
			if (span != null) {
				if (hasLog) {
					logEvent(span, log + ".after");
				}
				if (newSpan != null) {
					tracer().close(span);
				}
			}
		}
	}

	private void logEvent(Item span, String name) {
		if (span == null) {
			logger.warn("You were trying to continue a span which was null. Please "
					+ "remember that if two proxied methods are calling each other from "
					+ "the same class then the aspect will not be properly resolved");
			return;
		}
		span.logEvent(name);
	}

	private String log(ContinueSpan continueSpan) {
		if (continueSpan != null) {
			return continueSpan.log();
		}
		return "";
	}

	private Chainer tracer() {
		if (this.tracer == null) {
			this.tracer = this.beanFactory.getBean(Chainer.class);
		}
		return this.tracer;
	}

	private SpanCreator spanCreator() {
		if (this.spanCreator == null) {
			this.spanCreator = this.beanFactory.getBean(SpanCreator.class);
		}
		return this.spanCreator;
	}

	private SpanTagAnnotationHandler spanTagAnnotationHandler() {
		if (this.spanTagAnnotationHandler == null) {
			this.spanTagAnnotationHandler = new SpanTagAnnotationHandler(this.beanFactory);
		}
		return this.spanTagAnnotationHandler;
	}

	@Override public boolean implementsInterface(Class<?> intf) {
		return true;
	}

	@Override public void setBeanFactory(BeanFactory beanFactory) throws BeansException {
		this.beanFactory = beanFactory;
	}
}


// Node: buildPointcut
// Node: buildAdvice
// Node: setBeanFactory
// Node: SleuthInterceptor
// Node: AnnotationClassOrMethodOrArgsPointcut
// Node: implementsInterface


package org.myproject.ms.monitoring.instrument.msg;

import org.myproject.ms.monitoring.Log;
import org.myproject.ms.monitoring.Item;
import org.myproject.ms.monitoring.ChainKeys;
import org.myproject.ms.monitoring.Chainer;
import org.myproject.ms.monitoring.spl.NeverSampler;
import org.myproject.ms.monitoring.util.ExceptionUtils;
import org.springframework.messaging.Message;
import org.springframework.messaging.MessageChannel;
import org.springframework.messaging.MessageHandler;
import org.springframework.messaging.support.GenericMessage;
import org.springframework.messaging.support.MessageBuilder;
import org.springframework.messaging.support.MessageHeaderAccessor;


public class TCInter extends ATCInter {

	public TCInter(Chainer tracer, ChainKeys traceKeys,
			MSTMExtra spanExtractor,
			MSTMInject spanInjector) {
		super(tracer, traceKeys, spanExtractor, spanInjector);
	}

	@Override
	public void afterSendCompletion(Message<?> message, MessageChannel channel, boolean sent, Exception ex) {
		Item currentSpan = getTracer().getCurrentSpan();
		if (containsServerReceived(currentSpan)) {
			currentSpan.logEvent(Item.SERVER_SEND);
		} else if (currentSpan != null) {
			currentSpan.logEvent(Item.CLIENT_RECV);
		}
		addErrorTag(ex);
		getTracer().close(currentSpan);
	}

	private boolean containsServerReceived(Item span) {
		if (span == null) {
			return false;
		}
		for (Log log : span.logs()) {
			if (Item.SERVER_RECV.equals(log.getEvent())) {
				return true;
			}
		}
		return false;
	}

	@Override
	public Message<?> preSend(Message<?> message, MessageChannel channel) {
		MessageBuilder<?> messageBuilder = MessageBuilder.fromMessage(message);
		Item parentSpan = getTracer().isTracing() ? getTracer().getCurrentSpan()
				: buildSpan(new MTMap(messageBuilder));
		String name = getMessageChannelName(channel);
		Item span = startSpan(parentSpan, name, message);
		if (message.getHeaders().containsKey(TMHead.MESSAGE_SENT_FROM_CLIENT)) {
			span.logEvent(Item.SERVER_RECV);
		} else {
			span.logEvent(Item.CLIENT_SEND);
			messageBuilder.setHeader(TMHead.MESSAGE_SENT_FROM_CLIENT, true);
		}
		getSpanInjector().inject(span, new MTMap(messageBuilder));
		MessageHeaderAccessor headers = MessageHeaderAccessor.getMutableAccessor(message);
		headers.copyHeaders(messageBuilder.build().getHeaders());
		return new GenericMessage<Object>(message.getPayload(), headers.getMessageHeaders());
	}

	private Item startSpan(Item span, String name, Message<?> message) {
		if (span != null) {
			return getTracer().createSpan(name, span);
		}
		if (Item.SPAN_NOT_SAMPLED.equals(message.getHeaders().get(TMHead.SAMPLED_NAME))) {
			return getTracer().createSpan(name, NeverSampler.INSTANCE);
		}
		return getTracer().createSpan(name);
	}

	@Override
	public Message<?> beforeHandle(Message<?> message, MessageChannel channel,
			MessageHandler handler) {
		Item spanFromHeader = getTracer().getCurrentSpan();
		if (spanFromHeader!= null) {
			spanFromHeader.logEvent(Item.SERVER_RECV);
		}
		getTracer().continueSpan(spanFromHeader);
		return message;
	}

	@Override
	public void afterMessageHandled(Message<?> message, MessageChannel channel,
			MessageHandler handler, Exception ex) {
		Item spanFromHeader = getTracer().getCurrentSpan();
		if (spanFromHeader!= null) {
			spanFromHeader.logEvent(Item.SERVER_SEND);
			addErrorTag(ex);
		}
		// related to #447
		if (getTracer().isTracing()) {
			getTracer().detach(spanFromHeader);
		}
	}

	private void addErrorTag(Exception ex) {
		if (ex != null) {
			getTracer().addTag(Item.SPAN_ERROR_TAG_NAME, ExceptionUtils.getExceptionMessage(ex));
		}
	}

}


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/instrument/msg/TCInter.java:TCInter.<init>
// Node: TCInter


package org.myproject.ms.monitoring.instrument.web.client;

import javax.annotation.PostConstruct;
import java.util.ArrayList;
import java.util.Collection;
import java.util.List;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.autoconfigure.AutoConfigureAfter;
import org.springframework.boot.autoconfigure.condition.ConditionalOnBean;
import org.springframework.boot.autoconfigure.condition.ConditionalOnClass;
import org.springframework.boot.autoconfigure.condition.ConditionalOnMissingBean;
import org.myproject.ms.monitoring.instrument.web.HSInject;
import org.myproject.ms.monitoring.Chainer;
import org.myproject.ms.monitoring.instrument.web.HTKInject;
import org.myproject.ms.monitoring.instrument.web.TWAConf;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.client.ClientHttpRequestInterceptor;
import org.springframework.web.client.RestTemplate;


@Configuration
@SWCEnable
@ConditionalOnClass(RestTemplate.class)
@ConditionalOnBean(HTKInject.class)
@AutoConfigureAfter(TWAConf.class)
public class TWCAConf {

	@Bean
	@ConditionalOnMissingBean
	public TRTInter traceRestTemplateInterceptor(Chainer tracer,
			HSInject spanInjector,
			HTKInject httpTraceKeysInjector) {
		return new TRTInter(tracer, spanInjector, httpTraceKeysInjector);
	}

	@Configuration
	protected static class TraceInterceptorConfiguration {

		@Autowired(required = false)
		private Collection<RestTemplate> restTemplates;

		@Autowired
		private TRTInter traceRestTemplateInterceptor;

		@PostConstruct
		public void init() {
			if (this.restTemplates != null) {
				for (RestTemplate restTemplate : this.restTemplates) {
					List<ClientHttpRequestInterceptor> interceptors = new ArrayList<ClientHttpRequestInterceptor>(
							restTemplate.getInterceptors());
					interceptors.add(this.traceRestTemplateInterceptor);
					restTemplate.setInterceptors(interceptors);
				}
			}
		}
	}
}


// Node: getInterceptors
// Node: setInterceptors
package org.myproject.ms.monitoring.instrument.messaging.websocket;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.autoconfigure.AutoConfigureAfter;
import org.springframework.boot.autoconfigure.condition.ConditionalOnBean;
import org.springframework.boot.autoconfigure.condition.ConditionalOnClass;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.myproject.ms.monitoring.ChainKeys;
import org.myproject.ms.monitoring.Chainer;
import org.myproject.ms.monitoring.instrument.msg.MSTMExtra;
import org.myproject.ms.monitoring.instrument.msg.MSTMInject;
import org.myproject.ms.monitoring.instrument.msg.TCInter;
import org.myproject.ms.monitoring.instrument.msg.TSMAConf;
import org.springframework.context.annotation.Configuration;
import org.springframework.messaging.simp.config.ChannelRegistration;
import org.springframework.stereotype.Component;
import org.springframework.web.socket.config.annotation.AbstractWebSocketMessageBrokerConfigurer;
import org.springframework.web.socket.config.annotation.DelegatingWebSocketMessageBrokerConfiguration;
import org.springframework.web.socket.config.annotation.StompEndpointRegistry;


@Component
@Configuration
@AutoConfigureAfter(TSMAConf.class)
@ConditionalOnClass(DelegatingWebSocketMessageBrokerConfiguration.class)
@ConditionalOnBean(Chainer.class)
@ConditionalOnProperty(value = "spring.sleuth.integration.websockets.enabled", matchIfMissing = true)
public class TWSAConf
		extends AbstractWebSocketMessageBrokerConfigurer {

	@Autowired
	Chainer tracer;
	@Autowired
	ChainKeys traceKeys;
	@Autowired
	MSTMExtra spanExtractor;
	@Autowired
	MSTMInject spanInjector;

	@Override
	public void registerStompEndpoints(StompEndpointRegistry registry) {
		// The user must register their own endpoints
	}

	@Override
	public void configureClientOutboundChannel(ChannelRegistration registration) {
		registration.setInterceptors(new TCInter(this.tracer,
				this.traceKeys, this.spanExtractor, this.spanInjector));
	}

	@Override
	public void configureClientInboundChannel(ChannelRegistration registration) {
		registration.setInterceptors(new TCInter(this.tracer,
				this.traceKeys, this.spanExtractor, this.spanInjector));
	}
}

// Node: configureClientOutboundChannel
// Node: configureClientInboundChannel
