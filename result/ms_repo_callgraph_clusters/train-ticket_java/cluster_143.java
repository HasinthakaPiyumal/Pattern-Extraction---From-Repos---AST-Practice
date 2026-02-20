// Cluster 143

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


// Node: setEnabled
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




package org.myproject.ms.monitoring.antn;

import org.springframework.boot.context.properties.ConfigurationProperties;


@ConfigurationProperties("spring.sleuth.annotation")
public class SleuthAnnotationProperties {

	private boolean enabled = true;

	public boolean isEnabled() {
		return this.enabled;
	}

	public void setEnabled(boolean enabled) {
		this.enabled = enabled;
	}
}


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


