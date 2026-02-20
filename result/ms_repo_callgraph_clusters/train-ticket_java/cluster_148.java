// Cluster 148

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

// Node: incrementAcceptedSpans
// Node: increment
// Node: incrementDroppedSpans
package org.myproject.ms.monitoring.mtc;


public class NOIMRep implements ItemMetricReporter {

	public void incrementAcceptedSpans(long quantity) {

	}

	public void incrementDroppedSpans(long quantity) {

	}
}

package org.myproject.ms.monitoring.mtc;


public interface ItemMetricReporter {

	
	void incrementAcceptedSpans(long quantity);

	
	void incrementDroppedSpans(long quantity);
}


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/mtc/ItemMetricReporter.java:ItemMetricReporter.<init>
