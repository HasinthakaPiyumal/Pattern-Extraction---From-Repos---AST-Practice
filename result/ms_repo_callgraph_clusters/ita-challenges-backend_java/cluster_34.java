// Cluster 34

package com.itachallenge.user.document.enums;

import lombok.Getter;

import java.util.Arrays;

@Getter
public enum ChallengeStatus {
    SUBMITTED_COMPLETE("SUBMITTED_COMPLETE"),
    IN_PROGRESS("IN_PROGRESS"),
    SUBMITTED_INCOMPLETE("SUBMITTED_INCOMPLETE");

    private final String value;

    ChallengeStatus(String value) {
        this.value = value;
    }

    public static ChallengeStatus challengeStatusFromString(String status) {
        ChallengeStatus output = null;
        if (status != null) {
            output = Arrays.stream(ChallengeStatus.values())
                    .filter(s -> status.equalsIgnoreCase(s.getValue()))
                    .findFirst()
                    .orElse(null);
        }
        return output;
    }

}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-user/src/main/java/com/itachallenge/user/document/enums/ChallengeStatus.java:ChallengeStatus.<init>
// Node: SUBMITTED_COMPLETE
// Node: IN_PROGRESS
// Node: SUBMITTED_INCOMPLETE
// Node: ChallengeStatus
package com.itachallenge.submission.enums;

import com.itachallenge.common.exception.BadRequestException;
import lombok.Getter;

import java.util.Arrays;

@Getter
public enum SubmissionStatus {
    SUBMITTED_COMPLETE("SUBMITTED_COMPLETE"),
    IN_PROGRESS("IN_PROGRESS"),
    SUBMITTED_INCOMPLETE("SUBMITTED_INCOMPLETE");

    private final String value;

    SubmissionStatus(String value) {
        this.value = value;
    }

    public static SubmissionStatus fromString(String status) {
        if (status == null || status.isBlank()) {
            throw new BadRequestException("status is required");
        }

        return Arrays.stream(SubmissionStatus.values())
                .filter(s -> status.equalsIgnoreCase(s.getValue()))
                .findFirst()
                .orElseThrow(() -> new BadRequestException("Invalid status: " + status));
    }
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/main/java/com/itachallenge/submission/enums/SubmissionStatus.java:SubmissionStatus.<init>
// Node: SubmissionStatus
