// Cluster 27

package com.piggymetrics.notification.domain;

import java.util.stream.Stream;

public enum Frequency {

	WEEKLY(7), MONTHLY(30), QUARTERLY(90);

	private int days;

	Frequency(int days) {
		this.days = days;
	}

	public int getDays() {
		return days;
	}

	public static Frequency withDays(int days) {
		return Stream.of(Frequency.values())
				.filter(f -> f.getDays() == days)
				.findFirst()
				.orElseThrow(IllegalArgumentException::new);
	}
}


// Node: repos/cloned_ms_repos/piggymetrics/notification-service/src/main/java/com/piggymetrics/notification/domain/Frequency.java:Frequency.<init>
// Node: WEEKLY
// Node: MONTHLY
// Node: QUARTERLY
// Node: Frequency
