// Cluster 29

package com.itachallenge.challenge.enums;

public enum Topic {
    ALL("All"),
    COMPONENTS("Components"),
    USE_STATE_USE_EFFECT("useState & useEffect"),
    EVENTS("Events"),
    CONDITIONAL_RENDERING("Conditional Rendering"),
    LISTS("Lists"),
    STYLES("Styles"),
    DEBUGGING("Debugging"),
    REACT_ROUTER("React Router"),
    DEFAULT_TOPIC("Default topic");

    private final String displayName;

    Topic(String displayName) {
        this.displayName = displayName;
    }

    public String getDisplayName() {
        return displayName;
    }

    public static Topic fromDisplayName(String displayName) {
        for (Topic topic : Topic.values()) {
            if (topic.getDisplayName().equalsIgnoreCase(displayName)) {
                return topic;
            }
        }
        throw new IllegalArgumentException("No enum constant with display name " + displayName);
    }


}



// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/main/java/com/itachallenge/challenge/enums/Topic.java:Topic.<init>
// Node: ALL
// Node: COMPONENTS
// Node: USE_STATE_USE_EFFECT
// Node: EVENTS
// Node: CONDITIONAL_RENDERING
// Node: LISTS
// Node: STYLES
// Node: DEBUGGING
// Node: REACT_ROUTER
// Node: DEFAULT_TOPIC
// Node: Topic
