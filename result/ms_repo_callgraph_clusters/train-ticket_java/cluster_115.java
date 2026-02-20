// Cluster 115

package price.service;

import edu.fudan.common.util.Response;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpHeaders;
import org.springframework.stereotype.Service;
import price.entity.PriceConfig;
import price.repository.PriceConfigRepository;

import java.util.*;


/**
 * @author fdse
 */
@Service
public class PriceServiceImpl implements PriceService {

    @Autowired(required=true)
    private PriceConfigRepository priceConfigRepository;

    private static final Logger LOGGER = LoggerFactory.getLogger(PriceServiceImpl.class);

    String noThatConfig = "No that config";

    @Override
    public Response createNewPriceConfig(PriceConfig createAndModifyPriceConfig, HttpHeaders headers) {
        PriceServiceImpl.LOGGER.info("[createNewPriceConfig]");
        PriceConfig priceConfig = null;
        // create
        if (createAndModifyPriceConfig.getId() == null || createAndModifyPriceConfig.getId().toString().length() < 10) {
            priceConfig = new PriceConfig();
            priceConfig.setId(UUID.randomUUID().toString());
            priceConfig.setBasicPriceRate(createAndModifyPriceConfig.getBasicPriceRate());
            priceConfig.setFirstClassPriceRate(createAndModifyPriceConfig.getFirstClassPriceRate());
            priceConfig.setRouteId(createAndModifyPriceConfig.getRouteId());
            priceConfig.setTrainType(createAndModifyPriceConfig.getTrainType());
            priceConfigRepository.save(priceConfig);
        } else {
            // modify
            Optional<PriceConfig> op = priceConfigRepository.findById(createAndModifyPriceConfig.getId());
            if (!op.isPresent()) {
                priceConfig = new PriceConfig();
                priceConfig.setId(createAndModifyPriceConfig.getId());
            }else{
                priceConfig = op.get();
            }
            priceConfig.setBasicPriceRate(createAndModifyPriceConfig.getBasicPriceRate());
            priceConfig.setFirstClassPriceRate(createAndModifyPriceConfig.getFirstClassPriceRate());
            priceConfig.setRouteId(createAndModifyPriceConfig.getRouteId());
            priceConfig.setTrainType(createAndModifyPriceConfig.getTrainType());
            priceConfigRepository.save(priceConfig);
        }
        return new Response<>(1, "Create success", priceConfig);
    }

    @Override
    public PriceConfig findById(String id, HttpHeaders headers) {
        PriceServiceImpl.LOGGER.info("[findById][ID: {}]", id);
        Optional<PriceConfig> op = priceConfigRepository.findById(UUID.fromString(id).toString());
        if(op.isPresent()){
            return op.get();
        }
        return null;
    }

    @Override
    public Response findByRouteIdAndTrainType(String routeId, String trainType, HttpHeaders headers) {
        PriceServiceImpl.LOGGER.info("[findByRouteIdAndTrainType][Route: {} , Train Type: {}]", routeId, trainType);
        PriceConfig priceConfig = priceConfigRepository.findByRouteIdAndTrainType(routeId, trainType);
        //PriceServiceImpl.LOGGER.info("[findByRouteIdAndTrainType]");

        if (priceConfig == null) {
            PriceServiceImpl.LOGGER.warn("[findByRouteIdAndTrainType][Find by route and train type warn][PricrConfig not found][RouteId: {}, TrainType: {}]",routeId,trainType);
            return new Response<>(0, noThatConfig, null);
        } else {
            return new Response<>(1, "Success", priceConfig);
        }
    }

    @Override
    public Response findByRouteIdsAndTrainTypes(List<String> ridsAndTts, HttpHeaders headers){
        List<String> routeIds = new ArrayList<>();
        List<String> trainTypes = new ArrayList<>();
        for(String rts: ridsAndTts){
            List<String> r_t  = Arrays.asList(rts.split(":"));
            routeIds.add(r_t.get(0));
            trainTypes.add(r_t.get(1));
        }
        List<PriceConfig> pcs = priceConfigRepository.findByRouteIdsAndTrainTypes(routeIds, trainTypes);
        Map<String, PriceConfig> pcMap = new HashMap<>();
        for(PriceConfig pc: pcs){
            String key = pc.getRouteId() + ":" + pc.getTrainType();
            if(ridsAndTts.contains(key)){
                pcMap.put(key, pc);
            }
        }
        if (pcMap == null) {
            PriceServiceImpl.LOGGER.warn("[findByRouteIdsAndTrainTypes][Find by routes and train types warn][PricrConfig not found][RouteIds: {}, TrainTypes: {}]",routeIds,trainTypes);
            return new Response<>(0, noThatConfig, null);
        } else {
            return new Response<>(1, "Success", pcMap);
        }
    }


    @Override
    public Response findAllPriceConfig(HttpHeaders headers) {
        List<PriceConfig> list = priceConfigRepository.findAll();
        if (list == null) {
            list = new ArrayList<>();
        }

        if (!list.isEmpty()) {
            PriceServiceImpl.LOGGER.warn("[findAllPriceConfig][Find all price config warn][{}]","No Content");
            return new Response<>(1, "Success", list);
        } else {
            return new Response<>(0, "No price config", null);
        }

    }

    @Override
    public Response deletePriceConfig(String pcId, HttpHeaders headers) {
        Optional<PriceConfig> op = priceConfigRepository.findById(pcId);
        if (!op.isPresent()) {
            PriceServiceImpl.LOGGER.error("[deletePriceConfig][Delete price config error][Price config not found][PriceConfigId: {}]",pcId);
            return new Response<>(0, noThatConfig, null);
        } else {
            PriceConfig pc = op.get();
            priceConfigRepository.delete(pc);
            return new Response<>(1, "Delete success", pc);
        }
    }

    @Override
    public Response updatePriceConfig(PriceConfig c, HttpHeaders headers) {
        Optional<PriceConfig> op = priceConfigRepository.findById(c.getId());
        if (!op.isPresent()) {
            PriceServiceImpl.LOGGER.error("[updatePriceConfig][Update price config error][Price config not found][PriceConfigId: {}]",c.getId());
            return new Response<>(0, noThatConfig, null);
        } else {
            PriceConfig priceConfig = op.get();
            priceConfig.setId(c.getId());
            priceConfig.setBasicPriceRate(c.getBasicPriceRate());
            priceConfig.setFirstClassPriceRate(c.getFirstClassPriceRate());
            priceConfig.setRouteId(c.getRouteId());
            priceConfig.setTrainType(c.getTrainType());
            priceConfigRepository.save(priceConfig);
            return new Response<>(1, "Update success", priceConfig);
        }
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-price-service/src/main/java/price/service/PriceServiceImpl.java:PriceServiceImpl.<init>
// Node: Autowired
// Node: DChainer


package org.myproject.ms.monitoring.lgger;

import org.slf4j.MDC;
import org.springframework.boot.autoconfigure.condition.ConditionalOnClass;
import org.springframework.boot.autoconfigure.condition.ConditionalOnMissingBean;
import org.springframework.boot.autoconfigure.condition.ConditionalOnMissingClass;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;


@Configuration
@ConditionalOnProperty(value="spring.sleuth.enabled", matchIfMissing=true)
public class LogAtcfg {

	@Configuration
	@ConditionalOnClass(MDC.class)
	@EnableConfigurationProperties(Slf4jProps.class)
	protected static class Slf4jConfiguration {

		@Bean
		@ConditionalOnProperty(value = "spring.sleuth.log.slf4j.enabled", matchIfMissing = true)
		@ConditionalOnMissingBean
		public ItemLogger slf4jSpanLogger(Slf4jProps sleuthSlf4jProperties) {
			// Sets up MDC entries X-B3-TraceId and X-B3-SpanId
			return new Slf4jItemLogger(sleuthSlf4jProperties.getNameSkipPattern());
		}

		@Bean
		@ConditionalOnProperty(value = "spring.sleuth.log.slf4j.enabled", havingValue = "false")
		@ConditionalOnMissingBean
		public ItemLogger noOpSlf4jSpanLogger() {
			return new NoItemLogger();
		}
	}

	@Bean
	@ConditionalOnMissingClass("org.slf4j.MDC")
	@ConditionalOnMissingBean
	public ItemLogger defaultLoggedSpansHandler() {
		return new NoItemLogger();
	}
}


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/lgger/LogAtcfg.java:LogAtcfg.<init>
// Node: ConditionalOnProperty
// Node: ConditionalOnClass
// Node: EnableConfigurationProperties
// Node: slf4jSpanLogger
// Node: Slf4jItemLogger
// Node: getNameSkipPattern
// Node: noOpSlf4jSpanLogger
// Node: NoItemLogger
// Node: ConditionalOnMissingClass
// Node: defaultLoggedSpansHandler


package org.myproject.ms.monitoring.lgger;

import java.util.regex.Pattern;

import org.slf4j.Logger;
import org.slf4j.MDC;
import org.myproject.ms.monitoring.Item;


public class Slf4jItemLogger implements ItemLogger {

	private final Logger log;
	private final Pattern nameSkipPattern;

	public Slf4jItemLogger(String nameSkipPattern) {
		this.nameSkipPattern = Pattern.compile(nameSkipPattern);
		this.log = org.slf4j.LoggerFactory.getLogger(Slf4jItemLogger.class);
	}

	Slf4jItemLogger(String nameSkipPattern, Logger log) {
		this.nameSkipPattern = Pattern.compile(nameSkipPattern);
		this.log = log;
	}

	@Override
	public void logStartedSpan(Item parent, Item span) {
		MDC.put(Item.SPAN_ID_NAME, Item.idToHex(span.getSpanId()));
		MDC.put(Item.SPAN_EXPORT_NAME, String.valueOf(span.isExportable()));
		MDC.put(Item.TRACE_ID_NAME, span.traceIdString());
		log("Starting span: {}", span);
		if (parent != null) {
			log("With parent: {}", parent);
			MDC.put(Item.PARENT_ID_NAME, Item.idToHex(parent.getSpanId()));
		}
	}

	@Override
	public void logContinuedSpan(Item span) {
		MDC.put(Item.SPAN_ID_NAME, Item.idToHex(span.getSpanId()));
		MDC.put(Item.TRACE_ID_NAME, span.traceIdString());
		MDC.put(Item.SPAN_EXPORT_NAME, String.valueOf(span.isExportable()));
		setParentIdIfPresent(span);
		log("Continued span: {}", span);
	}

	private void setParentIdIfPresent(Item span) {
		if (!span.getParents().isEmpty()) {
			MDC.put(Item.PARENT_ID_NAME, Item.idToHex(span.getParents().get(0)));
		}
	}

	@Override
	public void logStoppedSpan(Item parent, Item span) {
		if (span != null) {
			log("Stopped span: {}", span);
		}
		if (span != null && parent != null) {
			log("With parent: {}", parent);
			MDC.put(Item.SPAN_ID_NAME, Item.idToHex(parent.getSpanId()));
			MDC.put(Item.SPAN_EXPORT_NAME, String.valueOf(parent.isExportable()));
			setParentIdIfPresent(parent);
		}
		else {
			MDC.remove(Item.SPAN_ID_NAME);
			MDC.remove(Item.SPAN_EXPORT_NAME);
			MDC.remove(Item.TRACE_ID_NAME);
			MDC.remove(Item.PARENT_ID_NAME);
		}
	}

	private void log(String text, Item span) {
		if (span != null && this.nameSkipPattern.matcher(span.getName()).matches()) {
			return;
		}
		if (this.log.isTraceEnabled()) {
			this.log.trace(text, span);
		}
	}

}


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/lgger/Slf4jItemLogger.java:Slf4jItemLogger.<init>
package org.myproject.ms.monitoring.lgger;

import org.springframework.boot.context.properties.ConfigurationProperties;


@ConfigurationProperties("spring.sleuth.log.slf4j")
public class Slf4jProps {

	
	private boolean enabled = true;

	
	private String nameSkipPattern = "";

	public boolean isEnabled() {
		return this.enabled;
	}

	public void setEnabled(boolean enabled) {
		this.enabled = enabled;
	}

	public String getNameSkipPattern() {
		return this.nameSkipPattern;
	}

	public void setNameSkipPattern(String nameSkipPattern) {
		this.nameSkipPattern = nameSkipPattern;
	}
}


package org.myproject.ms.monitoring.mtc;

import org.springframework.boot.actuate.metrics.CounterService;


public class CSBSMRep implements ItemMetricReporter {
	private final String acceptedSpansMetricName;
	private final String droppedSpansMetricName;
	private final CounterService counterService;

	public CSBSMRep(String acceptedSpansMetricName,
			String droppedSpansMetricName, CounterService counterService) {
		this.acceptedSpansMetricName = acceptedSpansMetricName;
		this.droppedSpansMetricName = droppedSpansMetricName;
		this.counterService = counterService;
	}

	@Override
	public void incrementAcceptedSpans(long quantity) {
		for (int i = 0; i < quantity; i++) {
			this.counterService.increment(this.acceptedSpansMetricName);
		}
	}

	@Override
	public void incrementDroppedSpans(long quantity) {
		for (int i = 0; i < quantity; i++) {
			this.counterService.increment(this.droppedSpansMetricName);
		}
	}
}

// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/mtc/CSBSMRep.java:CSBSMRep.<init>
// Node: CSBSMRep
package org.myproject.ms.monitoring.mtc;

import org.springframework.boot.context.properties.ConfigurationProperties;


@ConfigurationProperties("spring.sleuth.metric")
public class SMProp {

	
	private boolean enabled = true;

	private Span span = new Span();

	public boolean isEnabled() {
		return this.enabled;
	}

	public void setEnabled(boolean enabled) {
		this.enabled = enabled;
	}

	public Span getSpan() {
		return this.span;
	}

	public void setSpan(Span span) {
		this.span = span;
	}

	public static class Span {

		private String acceptedName = "counter.span.accepted";

		private String droppedName = "counter.span.dropped";

		public String getAcceptedName() {
			return this.acceptedName;
		}

		public void setAcceptedName(String acceptedName) {
			this.acceptedName = acceptedName;
		}

		public String getDroppedName() {
			return this.droppedName;
		}

		public void setDroppedName(String droppedName) {
			this.droppedName = droppedName;
		}
	}
}


// Node: getSpan
// Node: getAcceptedName
// Node: getDroppedName


package org.myproject.ms.monitoring.mtc;

import java.lang.invoke.MethodHandles;

import org.apache.commons.logging.Log;
import org.apache.commons.logging.LogFactory;
import org.springframework.boot.actuate.metrics.CounterService;
import org.springframework.boot.autoconfigure.condition.ConditionOutcome;
import org.springframework.boot.autoconfigure.condition.ConditionalOnBean;
import org.springframework.boot.autoconfigure.condition.ConditionalOnClass;
import org.springframework.boot.autoconfigure.condition.ConditionalOnMissingBean;
import org.springframework.boot.autoconfigure.condition.ConditionalOnMissingClass;
import org.springframework.boot.autoconfigure.condition.SpringBootCondition;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.ConditionContext;
import org.springframework.context.annotation.Conditional;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.type.AnnotatedTypeMetadata;


@Configuration
@Conditional(ChainMetricsAtcfg.PickMetricIfMetricsIsMissing.class)
@EnableConfigurationProperties
public class ChainMetricsAtcfg {

	@Bean
	@ConditionalOnMissingBean
	public SMProp sleuthMetricProperties() {
		return new SMProp();
	}

	@Configuration
	@ConditionalOnClass(CounterService.class)
	@ConditionalOnMissingBean(ItemMetricReporter.class)
	protected static class CounterServiceSpanReporterConfig {
		@Bean
		@ConditionalOnBean(CounterService.class)
		public ItemMetricReporter spanReporterCounterService(CounterService counterService,
				SMProp sleuthMetricProperties) {
			return new CSBSMRep(sleuthMetricProperties.getSpan().getAcceptedName(),
					sleuthMetricProperties.getSpan().getDroppedName(), counterService);
		}

		@Bean
		@ConditionalOnMissingBean(CounterService.class)
		public ItemMetricReporter noOpSpanReporterCounterService() {
			return new NOIMRep();
		}
	}

	@Bean
	@ConditionalOnMissingClass("org.springframework.boot.actuate.metrics.CounterService")
	@ConditionalOnMissingBean(ItemMetricReporter.class)
	public ItemMetricReporter noOpSpanReporterCounterService() {
		return new NOIMRep();
	}

	static class PickMetricIfMetricsIsMissing extends SpringBootCondition {

		private static final Log log = LogFactory.getLog(MethodHandles.lookup().lookupClass());

		static final String DEPRECATED_SPRING_SLEUTH_METRICS_ENABLED = "spring.sleuth.metrics.enabled";
		static final String SPRING_SLEUTH_METRIC_ENABLED = "spring.sleuth.metric.enabled";

		@Override
		public ConditionOutcome getMatchOutcome(ConditionContext context, AnnotatedTypeMetadata metadata) {
			Boolean oldValue = context.getEnvironment().getProperty(DEPRECATED_SPRING_SLEUTH_METRICS_ENABLED, Boolean.class);
			Boolean newValue = context.getEnvironment().getProperty(SPRING_SLEUTH_METRIC_ENABLED, Boolean.class);
			if (oldValue != null) {
				log.warn("You're using an old version of the metrics property. Instead of using [" +
						DEPRECATED_SPRING_SLEUTH_METRICS_ENABLED + "] please use [" + SPRING_SLEUTH_METRIC_ENABLED + "]");
				return matchCondition(oldValue, DEPRECATED_SPRING_SLEUTH_METRICS_ENABLED);
			}
			if (newValue != null) {
				return matchCondition(newValue, SPRING_SLEUTH_METRIC_ENABLED);
			}
			return ConditionOutcome.match("No property was passed - assuming that metrics are enabled.");
		}

		private ConditionOutcome matchCondition(Boolean value, String property) {
			if (Boolean.TRUE.equals(value)) {
				return ConditionOutcome.match();
			}
			return ConditionOutcome.noMatch("Property [" + property + "] is set to false.");
		}
	}
}


// Node: sleuthMetricProperties
// Node: SMProp
// Node: ConditionalOnMissingBean
// Node: ConditionalOnBean
// Node: spanReporterCounterService

package org.myproject.ms.monitoring.antn;

import org.springframework.boot.autoconfigure.AutoConfigureAfter;
import org.springframework.boot.autoconfigure.condition.ConditionalOnBean;
import org.springframework.boot.autoconfigure.condition.ConditionalOnMissingBean;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.myproject.ms.monitoring.Chainer;
import org.myproject.ms.monitoring.atcfg.TraceAutoConfiguration;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;


@Configuration
@ConditionalOnBean(Chainer.class)
@ConditionalOnProperty(name = "spring.sleuth.annotation.enabled", matchIfMissing = true)
@AutoConfigureAfter(TraceAutoConfiguration.class)
@EnableConfigurationProperties(SleuthAnnotationProperties.class)
public class SleuthAnnotationAutoConfiguration {
	
	@Bean
	@ConditionalOnMissingBean
	SpanCreator spanCreator(Chainer tracer) {
		return new DefaultSpanCreator(tracer);
	}

	@Bean
	@ConditionalOnMissingBean
	TagValueExpressionResolver spelTagValueExpressionResolver() {
		return new SpelTagValueExpressionResolver();
	}

	@Bean
	@ConditionalOnMissingBean
	TagValueResolver noOpTagValueResolver() {
		return new NoOpTagValueResolver();
	}

	@Bean
	SleuthAdvisorConfig sleuthAdvisorConfig() {
		return new SleuthAdvisorConfig();
	}
	
}


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/antn/SleuthAnnotationAutoConfiguration.java:SleuthAnnotationAutoConfiguration.<init>
// Node: AutoConfigureAfter


package org.myproject.ms.monitoring.instrument.msg;

import org.myproject.ms.monitoring.ChainKeys;
import org.myproject.ms.monitoring.Chainer;
import org.springframework.integration.channel.ChannelInterceptorAware;
import org.springframework.integration.channel.interceptor.VetoCapableInterceptor;
import org.springframework.messaging.support.ChannelInterceptor;


class ITCInter extends TCInter implements VetoCapableInterceptor {


	public ITCInter(Chainer tracer, ChainKeys traceKeys,
			MSTMExtra spanExtractor,
			MSTMInject spanInjector) {
		super(tracer, traceKeys, spanExtractor, spanInjector);
	}

	@Override
	public boolean shouldIntercept(String beanName, ChannelInterceptorAware channel) {
		for (ChannelInterceptor interceptor : channel.getChannelInterceptors()) {
			if (interceptor instanceof ATCInter) {
				return false;
			}
		}
		return true;
	}

}


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/instrument/msg/ITCInter.java:ITCInter.<init>
// Node: ITCInter


package org.myproject.ms.monitoring.instrument.msg;

import org.springframework.boot.autoconfigure.condition.ConditionalOnBean;
import org.springframework.boot.autoconfigure.condition.ConditionalOnClass;
import org.springframework.boot.autoconfigure.condition.ConditionalOnMissingBean;
import org.myproject.ms.monitoring.ChainKeys;
import org.myproject.ms.monitoring.Chainer;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.messaging.Message;


@Configuration
@ConditionalOnClass(Message.class)
@ConditionalOnBean(Chainer.class)
public class TSMAConf {

	@Bean
	@ConditionalOnMissingBean
	public MSTMExtra messagingSpanExtractor() {
		return new HBMExtra();
	}

	@Bean
	@ConditionalOnMissingBean
	public MSTMInject messagingSpanInjector(ChainKeys traceKeys) {
		return new HBMInject(traceKeys);
	}
}


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/instrument/msg/TSMAConf.java:TSMAConf.<init>


package org.myproject.ms.monitoring.instrument.msg;

import java.util.Random;

import org.springframework.boot.autoconfigure.AutoConfigureAfter;
import org.springframework.boot.autoconfigure.condition.ConditionalOnBean;
import org.springframework.boot.autoconfigure.condition.ConditionalOnClass;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.myproject.ms.monitoring.ChainKeys;
import org.myproject.ms.monitoring.Chainer;
import org.myproject.ms.monitoring.atcfg.TraceAutoConfiguration;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.integration.config.GlobalChannelInterceptor;


@Configuration
@ConditionalOnClass(GlobalChannelInterceptor.class)
@ConditionalOnBean(Chainer.class)
@AutoConfigureAfter({ TraceAutoConfiguration.class,
		TSMAConf.class })
@ConditionalOnProperty(value = "spring.sleuth.integration.enabled", matchIfMissing = true)
@EnableConfigurationProperties(ChainKeys.class)
public class TSIAConf {

	@Bean
	@GlobalChannelInterceptor(patterns = "${spring.sleuth.integration.patterns:*}")
	public TCInter traceChannelInterceptor(Chainer tracer,
			ChainKeys traceKeys, Random random, MSTMExtra spanExtractor,
			MSTMInject spanInjector) {
		return new ITCInter(tracer, traceKeys, spanExtractor,
				spanInjector);
	}

}


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/instrument/msg/TSIAConf.java:TSIAConf.<init>
// Node: GlobalChannelInterceptor
// Node: traceChannelInterceptor
// Node: TSAspect


package org.myproject.ms.monitoring.instrument.schedl;

import org.springframework.boot.autoconfigure.AutoConfigureAfter;
import org.springframework.boot.autoconfigure.condition.ConditionalOnBean;
import org.springframework.boot.autoconfigure.condition.ConditionalOnClass;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.myproject.ms.monitoring.ChainKeys;
import org.myproject.ms.monitoring.Chainer;
import org.myproject.ms.monitoring.atcfg.TraceAutoConfiguration;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.EnableAspectJAutoProxy;

import java.util.regex.Pattern;


@Configuration
@EnableAspectJAutoProxy
@ConditionalOnProperty(value = "spring.sleuth.scheduled.enabled", matchIfMissing = true)
@ConditionalOnBean(Chainer.class)
@AutoConfigureAfter(TraceAutoConfiguration.class)
@EnableConfigurationProperties(SSProp.class)
public class TSAConf {

	@ConditionalOnClass(name = "org.aspectj.lang.ProceedingJoinPoint")
	@Bean
	public TSAspect traceSchedulingAspect(Chainer tracer, ChainKeys traceKeys,
			SSProp sleuthSchedulingProperties) {
		return new TSAspect(tracer, traceKeys, Pattern.compile(sleuthSchedulingProperties.getSkipPattern()));
	}
}


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/instrument/schedl/TSAConf.java:TSAConf.<init>
// Node: traceSchedulingAspect
// Node: getSkipPattern
package org.myproject.ms.monitoring.instrument.schedl;

import org.springframework.boot.context.properties.ConfigurationProperties;


@ConfigurationProperties("spring.sleuth.scheduled")
public class SSProp {

	
	private boolean enabled = true;

	
	private String skipPattern = "";

	public boolean isEnabled() {
		return this.enabled;
	}

	public void setEnabled(boolean enabled) {
		this.enabled = enabled;
	}

	public String getSkipPattern() {
		return this.skipPattern;
	}

	public void setSkipPattern(String skipPattern) {
		this.skipPattern = skipPattern;
	}
}


// Node: postProcessBeforeInitialization
// Node: postProcessAfterInitialization


package org.myproject.ms.monitoring.instrument.async;

import java.util.concurrent.Executor;

import org.springframework.beans.factory.BeanFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.autoconfigure.AutoConfigureAfter;
import org.springframework.boot.autoconfigure.condition.ConditionalOnBean;
import org.springframework.boot.autoconfigure.condition.ConditionalOnMissingBean;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.myproject.ms.monitoring.ChainKeys;
import org.myproject.ms.monitoring.Chainer;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.task.SimpleAsyncTaskExecutor;
import org.springframework.scheduling.annotation.AsyncConfigurer;
import org.springframework.scheduling.annotation.AsyncConfigurerSupport;
import org.springframework.scheduling.annotation.EnableAsync;


@EnableAsync
@Configuration
@ConditionalOnProperty(value = "spring.sleuth.async.enabled", matchIfMissing = true)
@ConditionalOnBean(Chainer.class)
@AutoConfigureAfter(ACAtcfg.class)
public class ADAtcfg {

	@Autowired private BeanFactory beanFactory;

	@Configuration
	@ConditionalOnMissingBean(AsyncConfigurer.class)
	@ConditionalOnProperty(value = "spring.sleuth.async.configurer.enabled", matchIfMissing = true)
	static class DefaultAsyncConfigurerSupport extends AsyncConfigurerSupport {

		@Autowired private BeanFactory beanFactory;

		@Override
		public Executor getAsyncExecutor() {
			return new LTExec(this.beanFactory, new SimpleAsyncTaskExecutor());
		}
	}

	@Bean
	public TAAsp traceAsyncAspect(Chainer tracer, ChainKeys traceKeys) {
		return new TAAsp(tracer, traceKeys, this.beanFactory);
	}

	@Bean
	public EBPProc executorBeanPostProcessor() {
		return new EBPProc(this.beanFactory);
	}

}

// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/instrument/async/ADAtcfg.java:ADAtcfg.<init>


package org.myproject.ms.monitoring.instrument.async;

import java.util.concurrent.Executor;

import org.springframework.aop.interceptor.AsyncUncaughtExceptionHandler;
import org.springframework.beans.factory.BeanFactory;
import org.springframework.scheduling.annotation.AsyncConfigurer;
import org.springframework.scheduling.annotation.AsyncConfigurerSupport;


public class LTACus extends AsyncConfigurerSupport {

	private final BeanFactory beanFactory;
	private final AsyncConfigurer delegate;

	public LTACus(BeanFactory beanFactory, AsyncConfigurer delegate) {
		this.beanFactory = beanFactory;
		this.delegate = delegate;
	}

	@Override
	public Executor getAsyncExecutor() {
		return new LTExec(this.beanFactory, this.delegate.getAsyncExecutor());
	}

	@Override
	public AsyncUncaughtExceptionHandler getAsyncUncaughtExceptionHandler() {
		return this.delegate.getAsyncUncaughtExceptionHandler();
	}

}


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/instrument/async/LTACus.java:LTACus.<init>
// Node: LTACus


package org.myproject.ms.monitoring.instrument.async;

import org.myproject.ms.monitoring.instrument.schedl.TSAConf;
import org.springframework.beans.BeansException;
import org.springframework.beans.factory.BeanFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.config.BeanPostProcessor;
import org.springframework.boot.autoconfigure.AutoConfigureAfter;
import org.springframework.boot.autoconfigure.AutoConfigureBefore;
import org.springframework.boot.autoconfigure.condition.ConditionalOnBean;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.context.annotation.Configuration;
import org.springframework.scheduling.annotation.AsyncConfigurer;


@Configuration
@ConditionalOnBean(AsyncConfigurer.class)
@AutoConfigureBefore(ADAtcfg.class)
@ConditionalOnProperty(value = "spring.sleuth.async.enabled", matchIfMissing = true)
@AutoConfigureAfter(TSAConf.class)
public class ACAtcfg implements BeanPostProcessor {

	@Autowired
	private BeanFactory beanFactory;

	@Override
	public Object postProcessBeforeInitialization(Object bean, String beanName)
			throws BeansException {
		return bean;
	}

	@Override
	public Object postProcessAfterInitialization(Object bean, String beanName)
			throws BeansException {
		if (bean instanceof AsyncConfigurer) {
			AsyncConfigurer configurer = (AsyncConfigurer) bean;
			return new LTACus(this.beanFactory, configurer);
		}
		return bean;
	}

}

// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/instrument/async/ACAtcfg.java:ACAtcfg.<init>
// Node: AutoConfigureBefore

package org.myproject.ms.monitoring.instrument.web;

import java.util.regex.Pattern;

import org.springframework.boot.autoconfigure.AutoConfigureAfter;
import org.springframework.boot.autoconfigure.condition.ConditionalOnBean;
import org.springframework.boot.autoconfigure.condition.ConditionalOnMissingBean;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.myproject.ms.monitoring.ChainKeys;
import org.myproject.ms.monitoring.Chainer;
import org.myproject.ms.monitoring.atcfg.TraceAutoConfiguration;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;


@Configuration
@ConditionalOnBean(Chainer.class)
@AutoConfigureAfter(TraceAutoConfiguration.class)
@EnableConfigurationProperties({ ChainKeys.class, SWProp.class })
public class THAConf {

	@Bean
	@ConditionalOnMissingBean
	public HTKInject httpTraceKeysInjector(Chainer tracer, ChainKeys traceKeys) {
		return new HTKInject(tracer, traceKeys);
	}

	@Bean
	@ConditionalOnMissingBean
	public HSExtra httpSpanExtractor(SWProp sleuthWebProperties) {
		return new ZHSExtra(Pattern.compile(sleuthWebProperties.getSkipPattern()));
	}

	@Bean
	@ConditionalOnMissingBean
	public HSInject httpSpanInjector() {
		return new ZHSInject();
	}
}


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/instrument/web/THAConf.java:THAConf.<init>
// Node: httpSpanExtractor
// Node: ZHSExtra
package org.myproject.ms.monitoring.instrument.web;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.boot.context.properties.NestedConfigurationProperty;


@ConfigurationProperties("spring.sleuth.web")
public class SWProp {

	public static final String DEFAULT_SKIP_PATTERN =
			"/api-docs.*|/autoconfig|/configprops|/dump|/health|/info|/metrics.*|/mappings|/trace|/swagger.*|.*\\.png|.*\\.css|.*\\.js|.*\\.html|/favicon.ico|/hystrix.stream";

	
	private boolean enabled = true;

	
	private String skipPattern = DEFAULT_SKIP_PATTERN;

	private Client client;

	public boolean isEnabled() {
		return this.enabled;
	}

	public void setEnabled(boolean enabled) {
		this.enabled = enabled;
	}

	public String getSkipPattern() {
		return this.skipPattern;
	}

	public void setSkipPattern(String skipPattern) {
		this.skipPattern = skipPattern;
	}

	public Client getClient() {
		return this.client;
	}

	public void setClient(Client client) {
		this.client = client;
	}

	public static class Client {

		
		private boolean enabled = true;

		public boolean isEnabled() {
			return this.enabled;
		}

		public void setEnabled(boolean enabled) {
			this.enabled = enabled;
		}
	}

	public static class Async {

		@NestedConfigurationProperty
		private AsyncClient client;

		public AsyncClient getClient() {
			return this.client;
		}

		public void setClient(AsyncClient client) {
			this.client = client;
		}
	}

	public static class AsyncClient {

		
		private boolean enabled;

		@NestedConfigurationProperty
		private Template template;

		public boolean isEnabled() {
			return this.enabled;
		}

		public void setEnabled(boolean enabled) {
			this.enabled = enabled;
		}

		public Template getTemplate() {
			return this.template;
		}

		public void setTemplate(Template template) {
			this.template = template;
		}
	}

	public static class Template {

		
		private boolean enabled;

		public boolean isEnabled() {
			return this.enabled;
		}

		public void setEnabled(boolean enabled) {
			this.enabled = enabled;
		}
	}
}


// Node: TFilter
// Node: TSDBPProcess

package org.myproject.ms.monitoring.instrument.web;

import java.util.regex.Pattern;

import org.springframework.beans.factory.BeanFactory;
import org.springframework.boot.actuate.autoconfigure.ManagementServerProperties;
import org.springframework.boot.autoconfigure.AutoConfigureAfter;
import org.springframework.boot.autoconfigure.condition.ConditionalOnBean;
import org.springframework.boot.autoconfigure.condition.ConditionalOnClass;
import org.springframework.boot.autoconfigure.condition.ConditionalOnMissingBean;
import org.springframework.boot.autoconfigure.condition.ConditionalOnMissingClass;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.boot.autoconfigure.condition.ConditionalOnWebApplication;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.boot.web.servlet.FilterRegistrationBean;
import org.myproject.ms.monitoring.ItemNamer;
import org.myproject.ms.monitoring.ItemReporter;
import org.myproject.ms.monitoring.ChainKeys;
import org.myproject.ms.monitoring.Chainer;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;
import org.springframework.util.StringUtils;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurerAdapter;

import static javax.servlet.DispatcherType.ASYNC;
import static javax.servlet.DispatcherType.ERROR;
import static javax.servlet.DispatcherType.FORWARD;
import static javax.servlet.DispatcherType.INCLUDE;
import static javax.servlet.DispatcherType.REQUEST;


@Configuration
@ConditionalOnProperty(value = "spring.sleuth.web.enabled", matchIfMissing = true)
@ConditionalOnWebApplication
@ConditionalOnBean(Chainer.class)
@AutoConfigureAfter(THAConf.class)
public class TWAConf {

	
	@Configuration
	@ConditionalOnClass(WebMvcConfigurerAdapter.class)
	@Import(TWMConf.class)
	protected static class TraceWebMvcAutoConfiguration {
	}

	@Bean
	public TWAsp traceWebAspect(Chainer tracer, ChainKeys traceKeys,
			ItemNamer spanNamer) {
		return new TWAsp(tracer, spanNamer, traceKeys);
	}

	@Bean
	@ConditionalOnClass(name = "org.springframework.data.rest.webmvc.support.DelegatingHandlerMapping")
	public TSDBPProcess traceSpringDataBeanPostProcessor(
			BeanFactory beanFactory) {
		return new TSDBPProcess(beanFactory);
	}

	@Bean
	public FilterRegistrationBean traceWebFilter(TFilter traceFilter) {
		FilterRegistrationBean filterRegistrationBean = new FilterRegistrationBean(
				traceFilter);
		filterRegistrationBean.setDispatcherTypes(ASYNC, ERROR, FORWARD, INCLUDE,
				REQUEST);
		filterRegistrationBean.setOrder(TFilter.ORDER);
		return filterRegistrationBean;
	}

	@Bean
	public TFilter traceFilter(Chainer tracer, ChainKeys traceKeys,
			SkipPatternProvider skipPatternProvider, ItemReporter spanReporter,
			HSExtra spanExtractor,
			HTKInject httpTraceKeysInjector) {
		return new TFilter(tracer, traceKeys, skipPatternProvider.skipPattern(),
				spanReporter, spanExtractor, httpTraceKeysInjector);
	}

	@Configuration
	@ConditionalOnClass(ManagementServerProperties.class)
	@ConditionalOnMissingBean(SkipPatternProvider.class)
	@EnableConfigurationProperties(SWProp.class)
	protected static class SkipPatternProviderConfig {

		@Bean
		@ConditionalOnBean(ManagementServerProperties.class)
		public SkipPatternProvider skipPatternForManagementServerProperties(
				final ManagementServerProperties managementServerProperties,
				final SWProp sleuthWebProperties) {
			return new SkipPatternProvider() {
				@Override
				public Pattern skipPattern() {
					return getPatternForManagementServerProperties(
							managementServerProperties,
							sleuthWebProperties);
				}
			};
		}

		
		static Pattern getPatternForManagementServerProperties(
				ManagementServerProperties managementServerProperties,
				SWProp sleuthWebProperties) {
			String skipPattern = sleuthWebProperties.getSkipPattern();
			if (StringUtils.hasText(skipPattern)
					&& StringUtils.hasText(managementServerProperties.getContextPath())) {
				return Pattern.compile(skipPattern + "|"
						+ managementServerProperties.getContextPath() + ".*");
			}
			else if (StringUtils.hasText(managementServerProperties.getContextPath())) {
				return Pattern
						.compile(managementServerProperties.getContextPath() + ".*");
			}
			return defaultSkipPattern(skipPattern);
		}

		@Bean
		@ConditionalOnMissingBean(ManagementServerProperties.class)
		public SkipPatternProvider defaultSkipPatternBeanIfManagementServerPropsArePresent(SWProp sleuthWebProperties) {
			return defaultSkipPatternProvider(sleuthWebProperties.getSkipPattern());
		}
	}

	@Bean
	@ConditionalOnMissingClass("org.springframework.boot.actuate.autoconfigure.ManagementServerProperties")
	@ConditionalOnMissingBean(SkipPatternProvider.class)
	public SkipPatternProvider defaultSkipPatternBean(SWProp sleuthWebProperties) {
		return defaultSkipPatternProvider(sleuthWebProperties.getSkipPattern());
	}

	private static SkipPatternProvider defaultSkipPatternProvider(
			final String skipPattern) {
		return new SkipPatternProvider() {
			@Override
			public Pattern skipPattern() {
				return defaultSkipPattern(skipPattern);
			}
		};
	}

	private static Pattern defaultSkipPattern(String skipPattern) {
		return StringUtils.hasText(skipPattern) ? Pattern.compile(skipPattern)
				: Pattern.compile(SWProp.DEFAULT_SKIP_PATTERN);
	}

	interface SkipPatternProvider {
		Pattern skipPattern();
	}
}


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/instrument/web/TWAConf.java:TWAConf.<init>
// Node: Import
// Node: traceWebAspect
// Node: traceSpringDataBeanPostProcessor
// Node: traceWebFilter
// Node: FilterRegistrationBean
// Node: setDispatcherTypes
// Node: setOrder
// Node: traceFilter
// Node: skipPatternForManagementServerProperties
// Node: defaultSkipPatternBeanIfManagementServerPropsArePresent
// Node: defaultSkipPatternProvider
// Node: defaultSkipPatternBean


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


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/instrument/web/client/TWACAConf.java:TWACAConf.<init>


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


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/instrument/web/client/TWCAConf.java:TWCAConf.<init>
// Node: traceRestTemplateInterceptor
// Node: TRTInter
package org.myproject.ms.monitoring.instrument.rest;

import org.springframework.boot.autoconfigure.AutoConfigureAfter;
import org.springframework.boot.autoconfigure.condition.ConditionalOnBean;
import org.springframework.boot.autoconfigure.condition.ConditionalOnClass;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.myproject.ms.monitoring.ChainKeys;
import org.myproject.ms.monitoring.Chainer;
import org.myproject.ms.monitoring.atcfg.TraceAutoConfiguration;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import com.netflix.hystrix.HystrixCommand;


@Configuration
@AutoConfigureAfter(TraceAutoConfiguration.class)
@ConditionalOnClass(HystrixCommand.class)
@ConditionalOnBean(Chainer.class)
@ConditionalOnProperty(value = "spring.sleuth.hystrix.strategy.enabled", matchIfMissing = true)
public class SHAConf {

	@Bean
	SHCStra sleuthHystrixConcurrencyStrategy(Chainer tracer, ChainKeys traceKeys) {
		return new SHCStra(tracer, traceKeys);
	}

}


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/instrument/rest/SHAConf.java:SHAConf.<init>
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

// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/instrument/messaging/websocket/TWSAConf.java:TWSAConf.<init>


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


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/atcfg/TraceAutoConfiguration.java:TraceAutoConfiguration.<init>
// Node: defaultTraceSampler
// Node: sleuthTracer
// Node: isTraceId128


package org.myproject.ms.monitoring.atcfg;

import org.springframework.boot.context.properties.ConfigurationProperties;


@ConfigurationProperties("spring.sleuth")
public class SleuthProperties {

	private boolean enabled = true;
	
	private boolean traceId128 = false;

	public boolean isEnabled() {
		return this.enabled;
	}

	public void setEnabled(boolean enabled) {
		this.enabled = enabled;
	}

	public boolean isTraceId128() {
		return this.traceId128;
	}

	public void setTraceId128(boolean traceId128) {
		this.traceId128 = traceId128;
	}
}


