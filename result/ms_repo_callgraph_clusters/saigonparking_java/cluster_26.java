// Cluster 26

package com.bht.saigonparking.common.util;

import org.apache.logging.log4j.Level;

import lombok.extern.log4j.Log4j2;

/**
 *
 * @author bht
 */
@Log4j2
public final class LoggingUtil {

    private LoggingUtil() {
    }

    public static void log(Level logLevel, String key, String description, String value) {
        log.log(logLevel, format(key, description, value));
    }

    private static String format(String key, String description, String value) {
        return String.format("%-10s %-14s %s",
                "[" + key + "]",
                description + ":",
                value);
    }
}

// Node: repos/cloned_ms_repos/saigonparking/common/src/main/java/com/bht/saigonparking/common/util/LoggingUtil.java:LoggingUtil.<init>
// Node: LoggingUtil
package com.bht.saigonparking.emulator.util;

import org.apache.logging.log4j.Level;

import lombok.extern.log4j.Log4j2;

/**
 *
 * @author bht
 */
@Log4j2
public final class LoggingUtil {

    private LoggingUtil() {
    }

    public static void log(Level logLevel, String key, String description, String value) {
        log.log(logLevel, format(key, description, value));
    }

    private static String format(String key, String description, String value) {
        return String.format("%-10s %-14s %s",
                "[" + key + "]",
                description + ":",
                value);
    }
}

// Node: repos/cloned_ms_repos/saigonparking/emulator/src/main/java/com/bht/saigonparking/emulator/util/LoggingUtil.java:LoggingUtil.<init>
