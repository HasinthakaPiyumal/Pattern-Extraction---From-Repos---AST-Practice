// Cluster 22

package com.itachallenge.challenge.dto;

import lombok.Getter;
import lombok.Setter;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

@Component
@Getter @Setter
public class GenericResultDto<T> {

    private int offset;
    private int limit;
    private int count;
    private T[] results;

    @Autowired
    public GenericResultDto() {}

    public GenericResultDto(int offset, int limit, int count, T[] results) {
        this.offset = offset;
        this.limit = limit;
        this.count = count;
        this.results = results;
    }


    public void setInfo(int offset, int limit, int count, T[] results) {
        this.offset = offset;
        this.limit = limit;
        this.count = count;
        this.results = results;
    }

}

// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/main/java/com/itachallenge/challenge/dto/GenericResultDto.java:GenericResultDto.<init>
// Node: GenericResultDto
