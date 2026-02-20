// Cluster 50

// Node: submit
package inside_payment.async;

import java.util.concurrent.Executor;
import java.util.concurrent.ThreadPoolExecutor;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.scheduling.concurrent.ThreadPoolTaskExecutor;

/**
 * @author fdse
 */
@Configuration  
@EnableAsync  
public class ExecutorConfig {  
  

    private int corePoolSize = 10;  

    private int maxPoolSize = 200;  

    private int queueCapacity = 10;  
  
    @Bean  
    public Executor mySimpleAsync() {  
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();  
        executor.setCorePoolSize(corePoolSize);  
        executor.setMaxPoolSize(maxPoolSize);  
        executor.setQueueCapacity(queueCapacity);  
        executor.setThreadNamePrefix("MySimpleExecutor-");  
        executor.initialize();  
        return executor;  
    }  
      
    @Bean  
    public Executor myAsync() {  
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();  
        executor.setCorePoolSize(corePoolSize);  
        executor.setMaxPoolSize(maxPoolSize);  
        executor.setQueueCapacity(queueCapacity);  
        executor.setThreadNamePrefix("MyExecutor-");  
  
        // rejection-policy：当pool已经达到max size的时候，如何处理新任务  
        // CALLER_RUNS：不在新线程中执行任务，而是有调用者所在的线程来执行  
        executor.setRejectedExecutionHandler(new ThreadPoolExecutor.CallerRunsPolicy());  
        executor.initialize();  
        return executor;  
    }
}


// Node: mySimpleAsync
// Node: ThreadPoolTaskExecutor
// Node: setCorePoolSize
// Node: setMaxPoolSize
// Node: setQueueCapacity
// Node: setThreadNamePrefix
// Node: initialize
// Node: myAsync
// Node: setRejectedExecutionHandler
// Node: CallerRunsPolicy


package org.myproject.ms.monitoring;

import java.lang.annotation.Documented;
import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;


@Target(ElementType.TYPE)
@Retention(RetentionPolicy.RUNTIME)
@Documented
public @interface ItemName {
	
	String value();
}


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/ItemName.java:ItemName.<init>
// Node: Target
// Node: Retention
// Node: value
// Node: wrap
// Node: ChainKeys


package org.myproject.ms.monitoring.trace;

import java.lang.invoke.MethodHandles;
import java.util.Random;
import java.util.concurrent.Callable;

import org.apache.commons.logging.Log;
import org.apache.commons.logging.LogFactory;
import org.myproject.ms.monitoring.Sampler;
import org.myproject.ms.monitoring.Item;
import org.myproject.ms.monitoring.ItemNamer;
import org.myproject.ms.monitoring.ItemReporter;
import org.myproject.ms.monitoring.ChainKeys;
import org.myproject.ms.monitoring.Chainer;
import org.myproject.ms.monitoring.instrument.async.SCTCall;
import org.myproject.ms.monitoring.instrument.async.SCTRun;
import org.myproject.ms.monitoring.lgger.ItemLogger;
import org.myproject.ms.monitoring.util.ExceptionUtils;
import org.myproject.ms.monitoring.util.ItemNameUtil;


public class DChainer implements Chainer {

	private static final Log log = LogFactory.getLog(MethodHandles.lookup().lookupClass());

	private static final int MAX_CHARS_IN_SPAN_NAME = 50;

	private final Sampler defaultSampler;

	private final Random random;

	private final ItemNamer spanNamer;

	private final ItemLogger spanLogger;

	private final ItemReporter spanReporter;

	private final ChainKeys traceKeys;

	private final boolean traceId128;

	@Deprecated
	public DChainer(Sampler defaultSampler, Random random, ItemNamer spanNamer,
			ItemLogger spanLogger, ItemReporter spanReporter) {
		this(defaultSampler, random, spanNamer, spanLogger, spanReporter, false);
	}

	@Deprecated
	public DChainer(Sampler defaultSampler, Random random, ItemNamer spanNamer,
				ItemLogger spanLogger, ItemReporter spanReporter, boolean traceId128) {
		this(defaultSampler, random, spanNamer, spanLogger, spanReporter, traceId128, null);
	}

	public DChainer(Sampler defaultSampler, Random random, ItemNamer spanNamer,
				ItemLogger spanLogger, ItemReporter spanReporter, ChainKeys traceKeys) {
		this(defaultSampler, random, spanNamer, spanLogger, spanReporter, false, traceKeys);
	}

	public DChainer(Sampler defaultSampler, Random random, ItemNamer spanNamer,
				ItemLogger spanLogger, ItemReporter spanReporter, boolean traceId128,
			ChainKeys traceKeys) {
		this.defaultSampler = defaultSampler;
		this.random = random;
		this.spanNamer = spanNamer;
		this.spanLogger = spanLogger;
		this.spanReporter = spanReporter;
		this.traceId128 = traceId128;
		this.traceKeys = traceKeys != null ? traceKeys : new ChainKeys();
	}

	@Override
	public Item createSpan(String name, Item parent) {
		if (parent == null) {
			return createSpan(name);
		}
		return continueSpan(createChild(parent, name));
	}

	@Override
	public Item createSpan(String name) {
		return this.createSpan(name, this.defaultSampler);
	}

	@Override
	public Item createSpan(String name, Sampler sampler) {
		String shortenedName = ItemNameUtil.shorten(name);
		Item span;
		if (isTracing()) {
			span = createChild(getCurrentSpan(), shortenedName);
		}
		else {
			long id = createId();
			span = Item.builder().name(shortenedName)
					.traceIdHigh(this.traceId128 ? createId() : 0L)
					.traceId(id)
					.spanId(id).build();
			if (sampler == null) {
				sampler = this.defaultSampler;
			}
			span = sampledSpan(span, sampler);
			this.spanLogger.logStartedSpan(null, span);
		}
		return continueSpan(span);
	}

	@Override
	public Item detach(Item span) {
		if (span == null) {
			return null;
		}
		Item cur = ICHolder.getCurrentSpan();
		if (cur == null) {
			if (log.isTraceEnabled()) {
				log.trace("Span in the context is null so something has already detached the span. Won't do anything about it");
			}
			return null;
		}
		if (!span.equals(cur)) {
			ExceptionUtils.warn("Tried to detach trace span but "
					+ "it is not the current span: " + span
					+ ". You may have forgotten to close or detach " + cur);
		}
		else {
			ICHolder.removeCurrentSpan();
		}
		return span.getSavedSpan();
	}

	@Override
	public Item close(Item span) {
		if (span == null) {
			return null;
		}
		Item cur = ICHolder.getCurrentSpan();
		final Item savedSpan = span.getSavedSpan();
		if (!span.equals(cur)) {
			ExceptionUtils.warn(
					"Tried to close span but it is not the current span: " + span
							+ ".  You may have forgotten to close or detach " + cur);
		}
		else {
			span.stop();
			if (savedSpan != null && span.getParents().contains(savedSpan.getSpanId())) {
				this.spanReporter.report(span);
				this.spanLogger.logStoppedSpan(savedSpan, span);
			}
			else {
				if (!span.isRemote()) {
					this.spanReporter.report(span);
					this.spanLogger.logStoppedSpan(null, span);
				}
			}
			ICHolder.close(new ICHolder.SpanFunction() {
				@Override public void apply(Item span) {
					DChainer.this.spanLogger.logStoppedSpan(savedSpan, span);
				}
			});
		}
		return savedSpan;
	}

	Item createChild(Item parent, String name) {
		String shortenedName = ItemNameUtil.shorten(name);
		long id = createId();
		if (parent == null) {
			Item span = Item.builder().name(shortenedName)
					.traceIdHigh(this.traceId128 ? createId() : 0L)
					.traceId(id)
					.spanId(id).build();
			span = sampledSpan(span, this.defaultSampler);
			this.spanLogger.logStartedSpan(null, span);
			return span;
		}
		else {
			if (!isTracing()) {
				ICHolder.push(parent, true);
			}
			Item span = Item.builder().name(shortenedName)
					.traceIdHigh(parent.getTraceIdHigh())
					.traceId(parent.getTraceId()).parent(parent.getSpanId()).spanId(id)
					.processId(parent.getProcessId()).savedSpan(parent)
					.exportable(parent.isExportable())
					.baggage(parent.getBaggage())
					.build();
			this.spanLogger.logStartedSpan(parent, span);
			return span;
		}
	}

	private Item sampledSpan(Item span, Sampler sampler) {
		if (!sampler.isSampled(span)) {
			// Copy everything, except set exportable to false
			return Item.builder()
					.begin(span.getBegin())
					.traceIdHigh(span.getTraceIdHigh())
					.traceId(span.getTraceId())
					.spanId(span.getSpanId())
					.name(span.getName())
					.exportable(false).build();
		}
		return span;
	}

	private long createId() {
		return this.random.nextLong();
	}

	@Override
	public Item continueSpan(Item span) {
		if (span != null) {
			this.spanLogger.logContinuedSpan(span);
		} else {
			return null;
		}
		Item newSpan = createContinuedSpan(span, ICHolder.getCurrentSpan());
		ICHolder.setCurrentSpan(newSpan);
		return newSpan;
	}

	private Item createContinuedSpan(Item span, Item saved) {
		if (saved == null && span.getSavedSpan() != null) {
			saved = span.getSavedSpan();
		}
		return new Item(span, saved);
	}

	@Override
	public Item getCurrentSpan() {
		return ICHolder.getCurrentSpan();
	}

	@Override
	public boolean isTracing() {
		return ICHolder.isTracing();
	}

	@Override
	public void addTag(String key, String value) {
		Item s = getCurrentSpan();
		if (s != null && s.isExportable()) {
			s.tag(key, value);
		}
	}

	
	@Override
	public <V> Callable<V> wrap(Callable<V> callable) {
		if (isTracing()) {
			return new SCTCall<>(this, this.traceKeys, this.spanNamer, callable);
		}
		return callable;
	}

	
	@Override
	public Runnable wrap(Runnable runnable) {
		if (isTracing()) {
			return new SCTRun(this, this.traceKeys, this.spanNamer, runnable);
		}
		return runnable;
	}
}


// Node: SCTRun


package org.myproject.ms.monitoring.antn;


class NoOpTagValueResolver implements TagValueResolver {
	@Override public String resolve(Object parameter) {
		return null;
	}
}


// Node: resolve
// Node: resolveTagValue
// Node: tracer


package org.myproject.ms.monitoring.antn;

import java.lang.invoke.MethodHandles;
import java.lang.reflect.Method;
import java.util.Arrays;
import java.util.List;

import org.aopalliance.intercept.MethodInvocation;
import org.apache.commons.logging.Log;
import org.apache.commons.logging.LogFactory;
import org.springframework.aop.support.AopUtils;
import org.springframework.beans.factory.BeanFactory;
import org.myproject.ms.monitoring.Chainer;
import org.springframework.util.StringUtils;


class SpanTagAnnotationHandler {

	private static final Log log = LogFactory.getLog(MethodHandles.lookup().lookupClass());

	private final BeanFactory beanFactory;
	private Chainer tracer;
	
	SpanTagAnnotationHandler(BeanFactory beanFactory) {
		this.beanFactory = beanFactory;
	}

	void addAnnotatedParameters(MethodInvocation pjp) {
		try {
			Method method = pjp.getMethod();
			Method mostSpecificMethod = AopUtils.getMostSpecificMethod(method,
					pjp.getThis().getClass());
			List<SleuthAnnotatedParameter> annotatedParameters =
					SleuthAnnotationUtils.findAnnotatedParameters(mostSpecificMethod, pjp.getArguments());
			getAnnotationsFromInterfaces(pjp, mostSpecificMethod, annotatedParameters);
			mergeAnnotatedMethodsIfNecessary(pjp, method, mostSpecificMethod,
					annotatedParameters);
			addAnnotatedArguments(annotatedParameters);
		} catch (SecurityException e) {
			log.error("Exception occurred while trying to add annotated parameters", e);
		}
	}

	private void getAnnotationsFromInterfaces(MethodInvocation pjp,
			Method mostSpecificMethod,
			List<SleuthAnnotatedParameter> annotatedParameters) {
		Class<?>[] implementedInterfaces = pjp.getThis().getClass().getInterfaces();
		if (implementedInterfaces.length > 0) {
			for (Class<?> implementedInterface : implementedInterfaces) {
				for (Method methodFromInterface : implementedInterface.getMethods()) {
					if (methodsAreTheSame(mostSpecificMethod, methodFromInterface)) {
						List<SleuthAnnotatedParameter> annotatedParametersForActualMethod =
								SleuthAnnotationUtils.findAnnotatedParameters(methodFromInterface, pjp.getArguments());
						mergeAnnotatedParameters(annotatedParameters, annotatedParametersForActualMethod);
					}
				}
			}
		}
	}

	private boolean methodsAreTheSame(Method mostSpecificMethod, Method method1) {
		return method1.getName().equals(mostSpecificMethod.getName()) &&
				Arrays.equals(method1.getParameterTypes(), mostSpecificMethod.getParameterTypes());
	}

	private void mergeAnnotatedMethodsIfNecessary(MethodInvocation pjp, Method method,
			Method mostSpecificMethod, List<SleuthAnnotatedParameter> annotatedParameters) {
		// that can happen if we have an abstraction and a concrete class that is
		// annotated with @NewSpan annotation
		if (!method.equals(mostSpecificMethod)) {
			List<SleuthAnnotatedParameter> annotatedParametersForActualMethod = SleuthAnnotationUtils.findAnnotatedParameters(
					method, pjp.getArguments());
			mergeAnnotatedParameters(annotatedParameters, annotatedParametersForActualMethod);
		}
	}

	private void mergeAnnotatedParameters(List<SleuthAnnotatedParameter> annotatedParametersIndices,
			List<SleuthAnnotatedParameter> annotatedParametersIndicesForActualMethod) {
		for (SleuthAnnotatedParameter container : annotatedParametersIndicesForActualMethod) {
			final int index = container.parameterIndex;
			boolean parameterContained = false;
			for (SleuthAnnotatedParameter parameterContainer : annotatedParametersIndices) {
				if (parameterContainer.parameterIndex == index) {
					parameterContained = true;
					break;
				}
			}
			if (!parameterContained) {
				annotatedParametersIndices.add(container);
			}
		}
	}

	private void addAnnotatedArguments(List<SleuthAnnotatedParameter> toBeAdded) {
		for (SleuthAnnotatedParameter container : toBeAdded) {
			String tagValue = resolveTagValue(container.annotation, container.argument);
			tracer().addTag(container.annotation.value(), tagValue);
		}
	}

	String resolveTagValue(SpanTag annotation, Object argument) {
		if (argument == null) {
			return "";
		}
		if (annotation.resolver() != NoOpTagValueResolver.class) {
			TagValueResolver tagValueResolver = this.beanFactory.getBean(annotation.resolver());
			return tagValueResolver.resolve(argument);
		} else if (StringUtils.hasText(annotation.expression())) {
			return this.beanFactory.getBean(TagValueExpressionResolver.class)
					.resolve(annotation.expression(), argument);
		}
		return argument.toString();
	}

	private Chainer tracer() {
		if (this.tracer == null) {
			this.tracer = this.beanFactory.getBean(Chainer.class);
		}
		return this.tracer;
	}

}


// Node: resolver
// Node: getBean
// Node: expression

package org.myproject.ms.monitoring.antn;

import java.lang.annotation.ElementType;
import java.lang.annotation.Inherited;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

import org.springframework.core.annotation.AliasFor;


@Retention(RetentionPolicy.RUNTIME)
@Inherited
@Target(value = { ElementType.METHOD, ElementType.TYPE })
public @interface NewSpan {

	
	@AliasFor("value")
	String name() default "";

	
	@AliasFor("name")
	String value() default "";

}


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/antn/NewSpan.java:NewSpan.<init>
// Node: AliasFor


package org.myproject.ms.monitoring.antn;


public interface TagValueExpressionResolver {

	
	String resolve(String expression, Object parameter);
	
}


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/antn/TagValueExpressionResolver.java:TagValueExpressionResolver.<init>


package org.myproject.ms.monitoring.antn;

import java.lang.annotation.ElementType;
import java.lang.annotation.Inherited;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;


@Retention(RetentionPolicy.RUNTIME)
@Inherited
@Target(value = { ElementType.METHOD, ElementType.TYPE })
public @interface ContinueSpan {

	
	String log() default "";
}


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/antn/ContinueSpan.java:ContinueSpan.<init>


package org.myproject.ms.monitoring.antn;

import java.lang.annotation.ElementType;
import java.lang.annotation.Inherited;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

import org.springframework.core.annotation.AliasFor;


@Retention(RetentionPolicy.RUNTIME)
@Inherited
@Target(value = { ElementType.PARAMETER })
public @interface SpanTag {

	
	@AliasFor("key")
	String value() default "";

	
	@AliasFor("value")
	String key() default "";

	
	String expression() default "";

	
	Class<? extends TagValueResolver> resolver() default NoOpTagValueResolver.class;

}


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/antn/SpanTag.java:SpanTag.<init>
// Node: key
package org.myproject.ms.monitoring.antn;


public interface TagValueResolver {

	
	String resolve(Object parameter);
	
}


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/antn/TagValueResolver.java:TagValueResolver.<init>


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




package org.myproject.ms.monitoring.antn;

import java.lang.invoke.MethodHandles;

import org.apache.commons.logging.Log;
import org.apache.commons.logging.LogFactory;
import org.springframework.expression.Expression;
import org.springframework.expression.ExpressionParser;
import org.springframework.expression.spel.standard.SpelExpressionParser;


class SpelTagValueExpressionResolver implements TagValueExpressionResolver {
	private static final Log log = LogFactory.getLog(MethodHandles.lookup().lookupClass());

	@Override
	public String resolve(String expression, Object parameter) {
		try {
			ExpressionParser expressionParser = new SpelExpressionParser();
			Expression expressionToEvaluate = expressionParser.parseExpression(expression);
			return expressionToEvaluate.getValue(parameter, String.class);
		} catch (Exception e) {
			log.error("Exception occurred while tying to evaluate the SPEL expression [" + expression + "]", e);
		}
		return parameter.toString();
	}
}


// Node: SpelExpressionParser
// Node: parseExpression


package org.myproject.ms.monitoring.instrument.async;

import org.myproject.ms.monitoring.Item;
import org.myproject.ms.monitoring.ItemNamer;
import org.myproject.ms.monitoring.ChainRunnable;
import org.myproject.ms.monitoring.Chainer;
import org.myproject.ms.monitoring.ChainKeys;


public class LCTRun extends ChainRunnable {

	protected static final String ASYNC_COMPONENT = "async";

	private final ChainKeys traceKeys;

	public LCTRun(Chainer tracer, ChainKeys traceKeys,
			ItemNamer spanNamer, Runnable delegate) {
		super(tracer, spanNamer, delegate);
		this.traceKeys = traceKeys;
	}

	public LCTRun(Chainer tracer, ChainKeys traceKeys,
			ItemNamer spanNamer, Runnable delegate, String name) {
		super(tracer, spanNamer, delegate, name);
		this.traceKeys = traceKeys;
	}

	@Override
	public void run() {
		Item span = startSpan();
		try {
			this.getDelegate().run();
		}
		finally {
			close(span);
		}
	}

	@Override
	protected Item startSpan() {
		Item span = getTracer().createSpan(getSpanName(), getParent());
		getTracer().addTag(Item.SPAN_LOCAL_COMPONENT_TAG_NAME, ASYNC_COMPONENT);
		getTracer().addTag(this.traceKeys.getAsync().getPrefix() +
				this.traceKeys.getAsync().getThreadNameKey(), Thread.currentThread().getName());
		return span;
	}
}


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/instrument/async/LCTRun.java:LCTRun.<init>
// Node: LCTRun


package org.myproject.ms.monitoring.instrument.async;

import java.lang.invoke.MethodHandles;
import java.util.concurrent.Executor;

import org.apache.commons.logging.Log;
import org.apache.commons.logging.LogFactory;
import org.springframework.beans.factory.BeanFactory;
import org.springframework.beans.factory.NoSuchBeanDefinitionException;
import org.myproject.ms.monitoring.DefaultItemNamer;
import org.myproject.ms.monitoring.ItemNamer;
import org.myproject.ms.monitoring.ChainKeys;
import org.myproject.ms.monitoring.Chainer;


public class LTExec implements Executor {

	private static final Log log = LogFactory.getLog(MethodHandles.lookup().lookupClass());

	private Chainer tracer;
	private final BeanFactory beanFactory;
	private final Executor delegate;
	private ChainKeys traceKeys;
	private ItemNamer spanNamer;

	public LTExec(BeanFactory beanFactory, Executor delegate) {
		this.beanFactory = beanFactory;
		this.delegate = delegate;
	}

	@Override
	public void execute(Runnable command) {
		if (this.tracer == null) {
			try {
				this.tracer = this.beanFactory.getBean(Chainer.class);
			}
			catch (NoSuchBeanDefinitionException e) {
				this.delegate.execute(command);
				return;
			}
		}
		this.delegate.execute(new SCTRun(this.tracer, traceKeys(), spanNamer(), command));
	}

	// due to some race conditions trace keys might not be ready yet
	private ChainKeys traceKeys() {
		if (this.traceKeys == null) {
			try {
				this.traceKeys = this.beanFactory.getBean(ChainKeys.class);
			}
			catch (NoSuchBeanDefinitionException e) {
				log.warn("TraceKeys bean not found - will provide a manually created instance");
				return new ChainKeys();
			}
		}
		return this.traceKeys;
	}

	// due to some race conditions trace keys might not be ready yet
	private ItemNamer spanNamer() {
		if (this.spanNamer == null) {
			try {
				this.spanNamer = this.beanFactory.getBean(ItemNamer.class);
			}
			catch (NoSuchBeanDefinitionException e) {
				log.warn("SpanNamer bean not found - will provide a manually created instance");
				return new DefaultItemNamer();
			}
		}
		return this.spanNamer;
	}

}


// Node: execute
// Node: traceKeys
// Node: spanNamer
// Node: DefaultItemNamer

package org.myproject.ms.monitoring.instrument.async;

import java.util.ArrayList;
import java.util.Collection;
import java.util.List;
import java.util.concurrent.Callable;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;

import org.springframework.beans.factory.BeanFactory;
import org.myproject.ms.monitoring.ItemNamer;
import org.myproject.ms.monitoring.ChainKeys;
import org.myproject.ms.monitoring.Chainer;


public class TEServ implements ExecutorService {
	ExecutorService delegate;
	Chainer tracer;
	private final String spanName;
	ChainKeys traceKeys;
	ItemNamer spanNamer;
	BeanFactory beanFactory;

	public TEServ(final ExecutorService delegate, final Chainer tracer,
			ChainKeys traceKeys, ItemNamer spanNamer) {
		this(delegate, tracer, traceKeys, spanNamer, null);
	}

	public TEServ(BeanFactory beanFactory, final ExecutorService delegate) {
		this.delegate = delegate;
		this.beanFactory = beanFactory;
		this.spanName = null;
	}

	public TEServ(final ExecutorService delegate, final Chainer tracer,
			ChainKeys traceKeys, ItemNamer spanNamer, String spanName) {
		this.delegate = delegate;
		this.tracer = tracer;
		this.spanName = spanName;
		this.traceKeys = traceKeys;
		this.spanNamer = spanNamer;
	}

	@Override
	public void execute(Runnable command) {
		final Runnable r = new LCTRun(tracer(), traceKeys(),
				spanNamer(), command, this.spanName);
		this.delegate.execute(r);
	}

	@Override
	public void shutdown() {
		this.delegate.shutdown();
	}

	@Override
	public List<Runnable> shutdownNow() {
		return this.delegate.shutdownNow();
	}

	@Override
	public boolean isShutdown() {
		return this.delegate.isShutdown();
	}

	@Override
	public boolean isTerminated() {
		return this.delegate.isTerminated();
	}

	@Override
	public boolean awaitTermination(long timeout, TimeUnit unit) throws InterruptedException {
		return this.delegate.awaitTermination(timeout, unit);
	}

	@Override
	public <T> Future<T> submit(Callable<T> task) {
		Callable<T> c = new SCTCall<>(tracer(), traceKeys(),
				spanNamer(), this.spanName, task);
		return this.delegate.submit(c);
	}

	@Override
	public <T> Future<T> submit(Runnable task, T result) {
		Runnable r = new SCTRun(tracer(), traceKeys(),
				spanNamer(), task, this.spanName);
		return this.delegate.submit(r, result);
	}

	@Override
	public Future<?> submit(Runnable task) {
		Runnable r = new LCTRun(tracer(), traceKeys(),
				spanNamer(), task, this.spanName);
		return this.delegate.submit(r);
	}

	@Override
	public <T> List<Future<T>> invokeAll(Collection<? extends Callable<T>> tasks) throws InterruptedException {
		return this.delegate.invokeAll(wrapCallableCollection(tasks));
	}

	@Override
	public <T> List<Future<T>> invokeAll(Collection<? extends Callable<T>> tasks, long timeout, TimeUnit unit)
			throws InterruptedException {
		return this.delegate.invokeAll(wrapCallableCollection(tasks), timeout, unit);
	}

	@Override
	public <T> T invokeAny(Collection<? extends Callable<T>> tasks) throws InterruptedException, ExecutionException {
		return this.delegate.invokeAny(wrapCallableCollection(tasks));
	}

	@Override
	public <T> T invokeAny(Collection<? extends Callable<T>> tasks, long timeout, TimeUnit unit)
			throws InterruptedException, ExecutionException, TimeoutException {
		return this.delegate.invokeAny(wrapCallableCollection(tasks), timeout, unit);
	}

	private <T> Collection<? extends Callable<T>> wrapCallableCollection(Collection<? extends Callable<T>> tasks) {
		List<Callable<T>> ts = new ArrayList<>();
		for (Callable<T> task : tasks) {
			if (!(task instanceof SCTCall)) {
				ts.add(new SCTCall<>(tracer(), traceKeys(),
						spanNamer(), this.spanName, task));
			}
		}
		return ts;
	}

	Chainer tracer() {
		if (this.tracer == null && this.beanFactory != null) {
			this.tracer = this.beanFactory.getBean(Chainer.class);
		}
		return this.tracer;
	}

	ChainKeys traceKeys() {
		if (this.traceKeys == null && this.beanFactory != null) {
			this.traceKeys = this.beanFactory.getBean(ChainKeys.class);
		}
		return this.traceKeys;
	}

	ItemNamer spanNamer() {
		if (this.spanNamer == null && this.beanFactory != null) {
			this.spanNamer = this.beanFactory.getBean(ItemNamer.class);
		}
		return this.spanNamer;
	}

}


// Node: invokeAll
// Node: wrapCallableCollection
// Node: invokeAny


package org.myproject.ms.monitoring.instrument.async;

import org.myproject.ms.monitoring.Item;
import org.myproject.ms.monitoring.ItemNamer;
import org.myproject.ms.monitoring.ChainKeys;
import org.myproject.ms.monitoring.ChainRunnable;
import org.myproject.ms.monitoring.Chainer;


public class SCTRun extends ChainRunnable {

	private final LCTRun traceRunnable;

	public SCTRun(Chainer tracer, ChainKeys traceKeys,
			ItemNamer spanNamer, Runnable delegate) {
		super(tracer, spanNamer, delegate);
		this.traceRunnable = new LCTRun(tracer, traceKeys, spanNamer, delegate);
	}

	public SCTRun(Chainer tracer, ChainKeys traceKeys,
			ItemNamer spanNamer, Runnable delegate, String name) {
		super(tracer, spanNamer, delegate, name);
		this.traceRunnable = new LCTRun(tracer, traceKeys, spanNamer, delegate, name);
	}

	@Override
	public void run() {
		Item span = startSpan();
		try {
			this.getDelegate().run();
		}
		finally {
			close(span);
		}
	}

	@Override
	protected Item startSpan() {
		Item span = this.getParent();
		if (span == null) {
			return this.traceRunnable.startSpan();
		}
		return continueSpan(span);
	}

	@Override protected void close(Item span) {
		if (this.getParent() == null) {
			super.close(span);
		} else {
			super.detachSpan(span);
		}
	}
}


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/instrument/async/SCTRun.java:SCTRun.<init>


package org.myproject.ms.monitoring.instrument.async;

import java.lang.invoke.MethodHandles;
import java.util.concurrent.Callable;
import java.util.concurrent.Future;
import java.util.concurrent.ThreadPoolExecutor;

import org.apache.commons.logging.Log;
import org.apache.commons.logging.LogFactory;
import org.springframework.beans.factory.BeanFactory;
import org.springframework.beans.factory.NoSuchBeanDefinitionException;
import org.myproject.ms.monitoring.DefaultItemNamer;
import org.myproject.ms.monitoring.ItemNamer;
import org.myproject.ms.monitoring.ChainKeys;
import org.myproject.ms.monitoring.Chainer;
import org.springframework.scheduling.concurrent.ThreadPoolTaskExecutor;
import org.springframework.util.concurrent.ListenableFuture;


@SuppressWarnings("serial")
public class LTTPTExec extends ThreadPoolTaskExecutor {

	private static final Log log = LogFactory.getLog(MethodHandles.lookup().lookupClass());

	private Chainer tracer;
	private final BeanFactory beanFactory;
	private final ThreadPoolTaskExecutor delegate;
	private ChainKeys traceKeys;
	private ItemNamer spanNamer;

	public LTTPTExec(BeanFactory beanFactory,
			ThreadPoolTaskExecutor delegate) {
		this.beanFactory = beanFactory;
		this.delegate = delegate;
	}

	@Override
	public void execute(Runnable task) {
		this.delegate.execute(new SCTRun(tracer(), traceKeys(), spanNamer(), task));
	}

	@Override
	public void execute(Runnable task, long startTimeout) {
		this.delegate.execute(new SCTRun(tracer(), traceKeys(), spanNamer(), task), startTimeout);
	}

	@Override
	public Future<?> submit(Runnable task) {
		return this.delegate.submit(new SCTRun(tracer(), traceKeys(), spanNamer(), task));
	}

	@Override
	public <T> Future<T> submit(Callable<T> task) {
		return this.delegate.submit(new SCTCall<>(tracer(), traceKeys(), spanNamer(), task));
	}

	@Override
	public ListenableFuture<?> submitListenable(Runnable task) {
		return this.delegate.submitListenable(new SCTRun(tracer(), traceKeys(), spanNamer(), task));
	}

	@Override
	public <T> ListenableFuture<T> submitListenable(Callable<T> task) {
		return this.delegate.submitListenable(new SCTCall<>(tracer(), traceKeys(), spanNamer(), task));
	}

	@Override
	public ThreadPoolExecutor getThreadPoolExecutor() throws IllegalStateException {
		return this.delegate.getThreadPoolExecutor();
	}

	public void destroy() {
		this.delegate.destroy();
		super.destroy();
	}

	@Override
	public void afterPropertiesSet() {
		this.delegate.afterPropertiesSet();
		super.afterPropertiesSet();
	}

	private Chainer tracer() {
		if (this.tracer == null) {
			this.tracer = this.beanFactory.getBean(Chainer.class);
		}
		return this.tracer;
	}

	private ChainKeys traceKeys() {
		if (this.traceKeys == null) {
			try {
				this.traceKeys = this.beanFactory.getBean(ChainKeys.class);
			}
			catch (NoSuchBeanDefinitionException e) {
				log.warn("TraceKeys bean not found - will provide a manually created instance");
				return new ChainKeys();
			}
		}
		return this.traceKeys;
	}

	private ItemNamer spanNamer() {
		if (this.spanNamer == null) {
			try {
				this.spanNamer = this.beanFactory.getBean(ItemNamer.class);
			}
			catch (NoSuchBeanDefinitionException e) {
				log.warn("SpanNamer bean not found - will provide a manually created instance");
				return new DefaultItemNamer();
			}
		}
		return this.spanNamer;
	}
}


// Node: submitListenable
// Node: getThreadPoolExecutor


package org.myproject.ms.monitoring.instrument.async;

import java.util.concurrent.Callable;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.ScheduledFuture;
import java.util.concurrent.TimeUnit;

import org.myproject.ms.monitoring.ItemNamer;
import org.myproject.ms.monitoring.Chainer;
import org.myproject.ms.monitoring.ChainKeys;


public class TSEServ extends TEServ implements ScheduledExecutorService {

	public TSEServ(ScheduledExecutorService delegate,
			Chainer tracer, ChainKeys traceKeys, ItemNamer spanNamer) {
		super(delegate, tracer, traceKeys, spanNamer);
	}

	private ScheduledExecutorService getScheduledExecutorService() {
		return (ScheduledExecutorService) this.delegate;
	}

	@Override
	public ScheduledFuture<?> schedule(Runnable command, long delay, TimeUnit unit) {
		Runnable r = new SCTRun(this.tracer, this.traceKeys, this.spanNamer, command);
		return getScheduledExecutorService().schedule(r, delay, unit);
	}

	@Override
	public <V> ScheduledFuture<V> schedule(Callable<V> callable, long delay, TimeUnit unit) {
		Callable<V> c = new SCTCall<>(this.tracer, this.traceKeys, this.spanNamer,  callable);
		return getScheduledExecutorService().schedule(c, delay, unit);
	}

	@Override
	public ScheduledFuture<?> scheduleAtFixedRate(Runnable command, long initialDelay, long period, TimeUnit unit) {
		Runnable r = new SCTRun(this.tracer, this.traceKeys, this.spanNamer,  command);
		return getScheduledExecutorService().scheduleAtFixedRate(r, initialDelay, period, unit);
	}

	@Override
	public ScheduledFuture<?> scheduleWithFixedDelay(Runnable command, long initialDelay, long delay, TimeUnit unit) {
		Runnable r = new SCTRun(this.tracer, this.traceKeys, this.spanNamer,  command);
		return getScheduledExecutorService().scheduleWithFixedDelay(r, initialDelay, delay, unit);
	}

}


// Node: getScheduledExecutorService
// Node: schedule
// Node: scheduleAtFixedRate
// Node: scheduleWithFixedDelay


package org.myproject.ms.monitoring.instrument.web;

import javax.servlet.http.HttpServletRequest;
import java.lang.invoke.MethodHandles;
import java.util.Collections;

import org.apache.commons.logging.Log;
import org.apache.commons.logging.LogFactory;
import org.springframework.beans.BeansException;
import org.springframework.beans.factory.BeanFactory;
import org.springframework.beans.factory.config.BeanPostProcessor;
import org.springframework.data.rest.webmvc.support.DelegatingHandlerMapping;
import org.springframework.web.servlet.HandlerExecutionChain;
import org.springframework.web.servlet.HandlerMapping;


class TSDBPProcess implements BeanPostProcessor {

	private static final Log log = LogFactory.getLog(MethodHandles.lookup().lookupClass());

	private final BeanFactory beanFactory;

	public TSDBPProcess(BeanFactory beanFactory) {
		this.beanFactory = beanFactory;
	}

	@Override
	public Object postProcessBeforeInitialization(Object bean, String beanName)
			throws BeansException {
		if (bean instanceof DelegatingHandlerMapping && !(bean instanceof TraceDelegatingHandlerMapping)) {
			if (log.isDebugEnabled()) {
				log.debug("Wrapping bean [" + beanName + "] of type [" + bean.getClass().getSimpleName() +
						"] in its trace representation");
			}
			return new TraceDelegatingHandlerMapping((DelegatingHandlerMapping) bean,
					this.beanFactory);
		}
		return bean;
	}

	@Override
	public Object postProcessAfterInitialization(Object bean, String beanName)
			throws BeansException {
		return bean;
	}

	private static class TraceDelegatingHandlerMapping extends DelegatingHandlerMapping {

		private final DelegatingHandlerMapping delegate;
		private final BeanFactory beanFactory;

		public TraceDelegatingHandlerMapping(DelegatingHandlerMapping delegate,
				BeanFactory beanFactory) {
			super(Collections.<HandlerMapping>emptyList());
			this.delegate = delegate;
			this.beanFactory = beanFactory;
		}

		@Override
		public int getOrder() {
			return this.delegate.getOrder();
		}

		@Override
		public HandlerExecutionChain getHandler(HttpServletRequest request)
				throws Exception {
			HandlerExecutionChain handlerExecutionChain = this.delegate.getHandler(request);
			if (handlerExecutionChain == null) {
				return null;
			}
			handlerExecutionChain.addInterceptor(new THInter(this.beanFactory));
			return handlerExecutionChain;
		}
	}
}


// Node: getOrder
// Node: getHandler
// Node: addInterceptor
// Node: THInter


package org.myproject.ms.monitoring.instrument.web;

import org.springframework.beans.factory.BeanFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.InterceptorRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurerAdapter;


@Configuration
class TWMConf extends WebMvcConfigurerAdapter {
	@Autowired BeanFactory beanFactory;

	@Bean
	public THInter traceHandlerInterceptor(BeanFactory beanFactory) {
		return new THInter(beanFactory);
	}

	@Override
	public void addInterceptors(InterceptorRegistry registry) {
		registry.addInterceptor(this.beanFactory.getBean(THInter.class));
	}
}


// Node: traceHandlerInterceptor
// Node: addInterceptors


package org.myproject.ms.monitoring.instrument.web;

import java.lang.invoke.MethodHandles;
import java.util.concurrent.atomic.AtomicReference;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import org.apache.commons.logging.Log;
import org.apache.commons.logging.LogFactory;
import org.springframework.beans.factory.BeanFactory;
import org.springframework.beans.factory.NoSuchBeanDefinitionException;
import org.springframework.boot.autoconfigure.web.ErrorController;
import org.myproject.ms.monitoring.Item;
import org.myproject.ms.monitoring.ChainKeys;
import org.myproject.ms.monitoring.Chainer;
import org.myproject.ms.monitoring.util.ExceptionUtils;
import org.myproject.ms.monitoring.util.ItemNameUtil;
import org.springframework.web.method.HandlerMethod;
import org.springframework.web.servlet.handler.HandlerInterceptorAdapter;


public class THInter extends HandlerInterceptorAdapter {

	private static final Log log = LogFactory.getLog(MethodHandles.lookup().lookupClass());

	private final BeanFactory beanFactory;

	private Chainer tracer;
	private ChainKeys traceKeys;
	private AtomicReference<ErrorController> errorController;

	public THInter(BeanFactory beanFactory) {
		this.beanFactory = beanFactory;
	}

	@Override
	public boolean preHandle(HttpServletRequest request, HttpServletResponse response,
			Object handler) throws Exception {
		String spanName = spanName(handler);
		boolean continueSpan = getRootSpanFromAttribute(request) != null;
		Item span = continueSpan ? getRootSpanFromAttribute(request) : getTracer().createSpan(spanName);
		if (log.isDebugEnabled()) {
			log.debug("Handling span " + span);
		}
		addClassMethodTag(handler, span);
		addClassNameTag(handler, span);
		setSpanInAttribute(request, span);
		if (!continueSpan) {
			setNewSpanCreatedAttribute(request, span);
		}
		return true;
	}

	private boolean isErrorControllerRelated(HttpServletRequest request) {
		return getErrorController() != null && getErrorController().getErrorPath()
				.equals(request.getRequestURI());
	}

	private void addClassMethodTag(Object handler, Item span) {
		if (handler instanceof HandlerMethod) {
			String methodName = ((HandlerMethod) handler).getMethod().getName();
			getTracer().addTag(getTraceKeys().getMvc().getControllerMethod(), methodName);
			if (log.isDebugEnabled()) {
				log.debug("Adding a method tag with value [" + methodName + "] to a span " + span);
			}
		}
	}

	private void addClassNameTag(Object handler, Item span) {
		String className;
		if (handler instanceof HandlerMethod) {
			className = ((HandlerMethod) handler).getBeanType().getSimpleName();
		} else {
			className = handler.getClass().getSimpleName();
		}
		if (log.isDebugEnabled()) {
			log.debug("Adding a class tag with value [" + className + "] to a span " + span);
		}
		getTracer().addTag(getTraceKeys().getMvc().getControllerClass(), className);
	}

	private String spanName(Object handler) {
		if (handler instanceof HandlerMethod) {
			return ItemNameUtil.toLowerHyphen(((HandlerMethod) handler).getMethod().getName());
		}
		return ItemNameUtil.toLowerHyphen(handler.getClass().getSimpleName());
	}

	@Override
	public void afterConcurrentHandlingStarted(HttpServletRequest request,
			HttpServletResponse response, Object handler) throws Exception {
		Item spanFromRequest = getNewSpanFromAttribute(request);
		Item rootSpanFromRequest = getRootSpanFromAttribute(request);
		if (log.isDebugEnabled()) {
			log.debug("Closing the span " + spanFromRequest + " and detaching its parent " + rootSpanFromRequest + " since the request is asynchronous");
		}
		getTracer().close(spanFromRequest);
		getTracer().detach(rootSpanFromRequest);
	}

	@Override
	public void afterCompletion(HttpServletRequest request, HttpServletResponse response,
			Object handler, Exception ex) throws Exception {
		if (isErrorControllerRelated(request)) {
			if (log.isDebugEnabled()) {
				log.debug("Skipping closing of a span for error controller processing");
			}
			return;
		}
		Item span = getRootSpanFromAttribute(request);
		if (ex != null) {
			String errorMsg = ExceptionUtils.getExceptionMessage(ex);
			if (log.isDebugEnabled()) {
				log.debug("Adding an error tag [" + errorMsg + "] to span " + span + "");
			}
			getTracer().addTag(Item.SPAN_ERROR_TAG_NAME, errorMsg);
		}
		if (getNewSpanFromAttribute(request) != null) {
			if (log.isDebugEnabled()) {
				log.debug("Closing span " + span);
			}
			Item newSpan = getNewSpanFromAttribute(request);
			getTracer().continueSpan(newSpan);
			getTracer().close(newSpan);
			clearNewSpanCreatedAttribute(request);
		}
	}

	private Item getNewSpanFromAttribute(HttpServletRequest request) {
		return (Item) request.getAttribute(TRAttr.NEW_SPAN_REQUEST_ATTR);
	}

	private Item getRootSpanFromAttribute(HttpServletRequest request) {
		return (Item) request.getAttribute(TFilter.TRACE_REQUEST_ATTR);
	}

	private void setSpanInAttribute(HttpServletRequest request, Item span) {
		request.setAttribute(TRAttr.HANDLED_SPAN_REQUEST_ATTR, span);
	}

	private void setNewSpanCreatedAttribute(HttpServletRequest request, Item span) {
		request.setAttribute(TRAttr.NEW_SPAN_REQUEST_ATTR, span);
	}

	private void clearNewSpanCreatedAttribute(HttpServletRequest request) {
		request.removeAttribute(TRAttr.NEW_SPAN_REQUEST_ATTR);
	}

	private Chainer getTracer() {
		if (this.tracer == null) {
			this.tracer = this.beanFactory.getBean(Chainer.class);
		}
		return this.tracer;
	}

	private ChainKeys getTraceKeys() {
		if (this.traceKeys == null) {
			this.traceKeys = this.beanFactory.getBean(ChainKeys.class);
		}
		return this.traceKeys;
	}

	ErrorController getErrorController() {
		if (this.errorController == null) {
			try {
				ErrorController errorController = this.beanFactory.getBean(ErrorController.class);
				this.errorController = new AtomicReference<>(errorController);
			} catch (NoSuchBeanDefinitionException e) {
				if (log.isTraceEnabled()) {
					log.trace("ErrorController bean not found");
				}
				this.errorController = new AtomicReference<>();
			}
		}
		return this.errorController.get();
	}

}




package org.myproject.ms.monitoring.instrument.web.client;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.autoconfigure.AutoConfigureAfter;
import org.springframework.boot.autoconfigure.condition.ConditionalOnBean;
import org.springframework.boot.autoconfigure.condition.ConditionalOnClass;
import org.springframework.boot.autoconfigure.condition.ConditionalOnMissingBean;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.myproject.ms.monitoring.instrument.web.HSInject;
import org.myproject.ms.monitoring.Chainer;
import org.myproject.ms.monitoring.instrument.web.HTKInject;
import org.myproject.ms.monitoring.instrument.web.TWAConf;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.task.AsyncListenableTaskExecutor;
import org.springframework.http.client.AsyncClientHttpRequestFactory;
import org.springframework.http.client.ClientHttpRequestFactory;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.scheduling.concurrent.ThreadPoolTaskScheduler;
import org.springframework.web.client.AsyncRestTemplate;


@Configuration
@SWCEnable
@ConditionalOnProperty(value = "spring.sleuth.web.async.client.enabled", matchIfMissing = true)
@ConditionalOnClass(AsyncRestTemplate.class)
@ConditionalOnBean(HTKInject.class)
@AutoConfigureAfter(TWAConf.class)
public class TWACAConf {

	@Autowired Chainer tracer;
	@Autowired private HTKInject httpTraceKeysInjector;
	@Autowired private HSInject spanInjector;
	@Autowired(required = false) private ClientHttpRequestFactory clientHttpRequestFactory;
	@Autowired(required = false) private AsyncClientHttpRequestFactory asyncClientHttpRequestFactory;

	private TACHRFW traceAsyncClientHttpRequestFactory() {
		ClientHttpRequestFactory clientFactory = this.clientHttpRequestFactory;
		AsyncClientHttpRequestFactory asyncClientFactory = this.asyncClientHttpRequestFactory;
		if (clientFactory == null) {
			clientFactory = defaultClientHttpRequestFactory(this.tracer);
		}
		if (asyncClientFactory == null) {
			asyncClientFactory = clientFactory instanceof AsyncClientHttpRequestFactory ?
					(AsyncClientHttpRequestFactory) clientFactory : defaultClientHttpRequestFactory(this.tracer);
		}
		return new TACHRFW(this.tracer, this.spanInjector,
				asyncClientFactory, clientFactory, this.httpTraceKeysInjector);
	}

	private SimpleClientHttpRequestFactory defaultClientHttpRequestFactory(Chainer tracer) {
		SimpleClientHttpRequestFactory simpleClientHttpRequestFactory = new SimpleClientHttpRequestFactory();
		simpleClientHttpRequestFactory.setTaskExecutor(asyncListenableTaskExecutor(tracer));
		return simpleClientHttpRequestFactory;
	}

	private AsyncListenableTaskExecutor asyncListenableTaskExecutor(Chainer tracer) {
		ThreadPoolTaskScheduler threadPoolTaskScheduler = new ThreadPoolTaskScheduler();
		threadPoolTaskScheduler.initialize();
		return new TALTExec(threadPoolTaskScheduler, tracer);
	}

	@Bean
	@ConditionalOnMissingBean
	@ConditionalOnProperty(value = "spring.sleuth.web.async.client.template.enabled", matchIfMissing = true)
	public AsyncRestTemplate traceAsyncRestTemplate() {
		return new TARTemp(traceAsyncClientHttpRequestFactory(), this.tracer);
	}

}


// Node: traceAsyncClientHttpRequestFactory
// Node: defaultClientHttpRequestFactory
// Node: TACHRFW
// Node: SimpleClientHttpRequestFactory
// Node: setTaskExecutor
// Node: asyncListenableTaskExecutor
// Node: ThreadPoolTaskScheduler
// Node: TALTExec
// Node: traceAsyncRestTemplate
// Node: TARTemp


package org.myproject.ms.monitoring.instrument.web.client;

import java.io.IOException;
import java.net.URI;

import org.myproject.ms.monitoring.instrument.web.HSInject;
import org.myproject.ms.monitoring.Chainer;
import org.myproject.ms.monitoring.instrument.web.HTKInject;
import org.springframework.core.task.AsyncListenableTaskExecutor;
import org.springframework.http.HttpMethod;
import org.springframework.http.client.AsyncClientHttpRequest;
import org.springframework.http.client.AsyncClientHttpRequestFactory;
import org.springframework.http.client.ClientHttpRequest;
import org.springframework.http.client.ClientHttpRequestFactory;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.scheduling.concurrent.ThreadPoolTaskScheduler;


public class TACHRFW extends ATHRInter
		implements ClientHttpRequestFactory, AsyncClientHttpRequestFactory {

	final AsyncClientHttpRequestFactory asyncDelegate;
	final ClientHttpRequestFactory syncDelegate;

	
	public TACHRFW(Chainer tracer,
			HSInject spanInjector,
			AsyncClientHttpRequestFactory asyncDelegate,
			HTKInject httpTraceKeysInjector) {
		super(tracer, spanInjector, httpTraceKeysInjector);
		this.asyncDelegate = asyncDelegate;
		this.syncDelegate = asyncDelegate instanceof ClientHttpRequestFactory ?
				(ClientHttpRequestFactory) asyncDelegate : defaultClientHttpRequestFactory();
	}

	
	public TACHRFW(Chainer tracer,
			HSInject spanInjector, HTKInject httpTraceKeysInjector) {
		super(tracer, spanInjector, httpTraceKeysInjector);
		SimpleClientHttpRequestFactory simpleClientHttpRequestFactory = defaultClientHttpRequestFactory();
		this.asyncDelegate = simpleClientHttpRequestFactory;
		this.syncDelegate = simpleClientHttpRequestFactory;
	}

	public TACHRFW(Chainer tracer,
			HSInject spanInjector,
			AsyncClientHttpRequestFactory asyncDelegate,
			ClientHttpRequestFactory syncDelegate,
			HTKInject httpTraceKeysInjector) {
		super(tracer, spanInjector, httpTraceKeysInjector);
		this.asyncDelegate = asyncDelegate;
		this.syncDelegate = syncDelegate;
	}

	private SimpleClientHttpRequestFactory defaultClientHttpRequestFactory() {
		SimpleClientHttpRequestFactory simpleClientHttpRequestFactory = new SimpleClientHttpRequestFactory();
		simpleClientHttpRequestFactory.setTaskExecutor(asyncListenableTaskExecutor(this.tracer));
		return simpleClientHttpRequestFactory;
	}

	private AsyncListenableTaskExecutor asyncListenableTaskExecutor(Chainer tracer) {
		ThreadPoolTaskScheduler threadPoolTaskScheduler = new ThreadPoolTaskScheduler();
		threadPoolTaskScheduler.initialize();
		return new TALTExec(threadPoolTaskScheduler, tracer);
	}

	@Override
	public AsyncClientHttpRequest createAsyncRequest(URI uri, HttpMethod httpMethod)
			throws IOException {
		AsyncClientHttpRequest request = this.asyncDelegate
				.createAsyncRequest(uri, httpMethod);
		addRequestTags(request);
		publishStartEvent(request);
		return request;
	}

	@Override
	public ClientHttpRequest createRequest(URI uri, HttpMethod httpMethod)
			throws IOException {
		ClientHttpRequest request = this.syncDelegate.createRequest(uri, httpMethod);
		addRequestTags(request);
		publishStartEvent(request);
		return request;
	}
}


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/instrument/web/client/TACHRFW.java:TACHRFW.<init>
// Node: createAsyncRequest
// Node: createRequest


package org.myproject.ms.monitoring.instrument.web.client;

import java.util.concurrent.Callable;
import java.util.concurrent.Future;

import org.myproject.ms.monitoring.Chainer;
import org.springframework.core.task.AsyncListenableTaskExecutor;
import org.springframework.util.concurrent.ListenableFuture;


public class TALTExec implements AsyncListenableTaskExecutor {

	private final AsyncListenableTaskExecutor delegate;
	private final Chainer tracer;

	TALTExec(AsyncListenableTaskExecutor delegate,
			Chainer tracer) {
		this.delegate = delegate;
		this.tracer = tracer;
	}

	@Override
	public ListenableFuture<?> submitListenable(Runnable task) {
		return this.delegate.submitListenable(this.tracer.wrap(task));
	}

	@Override
	public <T> ListenableFuture<T> submitListenable(Callable<T> task) {
		return this.delegate.submitListenable(this.tracer.wrap(task));
	}

	@Override
	public void execute(Runnable task, long startTimeout) {
		this.delegate.execute(this.tracer.wrap(task), startTimeout);
	}

	@Override
	public Future<?> submit(Runnable task) {
		return this.delegate.submit(this.tracer.wrap(task));
	}

	@Override
	public <T> Future<T> submit(Callable<T> task) {
		return this.delegate.submit(this.tracer.wrap(task));
	}

	@Override
	public void execute(Runnable task) {
		this.delegate.execute(this.tracer.wrap(task));
	}

}

// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/instrument/web/client/TALTExec.java:TALTExec.<init>
package org.myproject.ms.monitoring.instrument.web.client;

import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;

import java.lang.annotation.*;


@Retention(RetentionPolicy.RUNTIME)
@Target({ ElementType.TYPE, ElementType.METHOD})
@Documented
@ConditionalOnProperty(value = "spring.sleuth.web.client.enabled", matchIfMissing = true)
@interface SWCEnable {
}


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/instrument/web/client/SWCEnable.java:SWCEnable.<init>


package org.myproject.ms.monitoring.atcfg;

import java.util.Random;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.autoconfigure.condition.ConditionalOnMissingBean;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.myproject.ms.monitoring.DefaultItemNamer;
import org.myproject.ms.monitoring.NOItemAdjuster;
import org.myproject.ms.monitoring.NOItemReporter;
import org.myproject.ms.monitoring.Sampler;
import org.myproject.ms.monitoring.ItemAdjuster;
import org.myproject.ms.monitoring.ItemNamer;
import org.myproject.ms.monitoring.ItemReporter;
//import org.myproject.ms.monitoring.StateSpanAdjuster;
import org.myproject.ms.monitoring.ChainKeys;
import org.myproject.ms.monitoring.Chainer;
import org.myproject.ms.monitoring.lgger.ItemLogger;
import org.myproject.ms.monitoring.spl.NeverSampler;
import org.myproject.ms.monitoring.trace.DChainer;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;


@Configuration
@ConditionalOnProperty(value="spring.sleuth.enabled", matchIfMissing=true)
@EnableConfigurationProperties({ChainKeys.class, SleuthProperties.class})
public class TraceAutoConfiguration {
	@Autowired
	SleuthProperties properties;

	@Bean
	@ConditionalOnMissingBean
	public Random randomForSpanIds() {
		return new Random();
	}

	@Bean
	@ConditionalOnMissingBean
	public Sampler defaultTraceSampler() {
		return NeverSampler.INSTANCE;
	}

	@Bean
	@ConditionalOnMissingBean(Chainer.class)
	public DChainer sleuthTracer(Sampler sampler, Random random,
			ItemNamer spanNamer, ItemLogger spanLogger,
			ItemReporter spanReporter, ChainKeys traceKeys) {
		return new DChainer(sampler, random, spanNamer, spanLogger,
				spanReporter, this.properties.isTraceId128(), traceKeys);
	}

	@Bean
	@ConditionalOnMissingBean
	public ItemNamer spanNamer() {
		return new DefaultItemNamer();
	}

	@Bean
	@ConditionalOnMissingBean
	public ItemReporter defaultSpanReporter() {
		return new NOItemReporter();
	}

	@Bean
	@ConditionalOnMissingBean
	public ItemAdjuster defaultSpanAdjuster() {
		return new NOItemAdjuster();
//		return new StateSpanAdjuster();
	}

}


