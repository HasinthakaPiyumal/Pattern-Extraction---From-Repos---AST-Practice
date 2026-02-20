// Cluster 45

package com.itachallenge.submission.mapper;

import com.itachallenge.challenge.dto.submission.SubmissionDto;
import com.itachallenge.submission.document.SubmissionDocument;

import java.util.Objects;

public final class SubmissionMapper {

    private SubmissionMapper() {
    }

    public static SubmissionDto toDto(SubmissionDocument doc) {
        Objects.requireNonNull(doc, "SubmissionDocument cannot be null");

        return SubmissionDto.builder()
                .userId(doc.getUserId().toString())
                .challengeId(doc.getChallengeId().toString())
                .languageId(doc.getLanguageId().toString())
                .status(doc.getStatus().name())
                .submissionText(doc.getSubmissionText())
                .build();
    }
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/main/java/com/itachallenge/submission/mapper/SubmissionMapper.java:SubmissionMapper.<init>
// Node: SubmissionMapper
