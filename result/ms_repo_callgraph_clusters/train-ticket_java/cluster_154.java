// Cluster 154



package org.myproject.ms.monitoring.spl;

import org.myproject.ms.monitoring.Sampler;
import org.myproject.ms.monitoring.Item;


public class NeverSampler implements Sampler {

	public static final NeverSampler INSTANCE = new NeverSampler();

	@Override
	public boolean isSampled(Item span) {
		return false;
	}
}


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/spl/NeverSampler.java:NeverSampler.<init>
// Node: NeverSampler
