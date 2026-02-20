// Cluster 153



package org.myproject.ms.monitoring.spl;

import org.myproject.ms.monitoring.Sampler;
import org.myproject.ms.monitoring.Item;
import org.myproject.ms.monitoring.ItemAccessor;


public class IsChainingSampler implements Sampler {

	private ItemAccessor accessor;

	public IsChainingSampler(ItemAccessor accessor) {
		this.accessor = accessor;
	}

	@Override
	public boolean isSampled(Item span) {
		return this.accessor.isTracing();
	}
}


// Node: repos/cloned_ms_repos/train-ticket/old-docs/Lib/ms-monitoring-core/src/main/java/org/myproject/ms/monitoring/spl/IsChainingSampler.java:IsChainingSampler.<init>
// Node: IsChainingSampler
