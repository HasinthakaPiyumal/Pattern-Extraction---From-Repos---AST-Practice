// Cluster 37

package com.itachallenge.user.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.*;

@Getter
@Setter
public class AdminCreateUserRequestDto {

    @NotBlank(message = "Username must not be blank")
    private String username;

}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-user/src/main/java/com/itachallenge/user/dto/AdminCreateUserRequestDto.java:AdminCreateUserRequestDto.<init>
// Node: NotBlank
