// Cluster 113

package cancel.entity;

import edu.fudan.common.entity.Account;
import lombok.Data;
import edu.fudan.common.entity.Account;

/**
 * @author fdse
 */
@Data
public class GetAccountByIdResult {

    private boolean status;

    private String message;

    private Account account;

    public GetAccountByIdResult() {
        //Default Constructor
    }

}


// Node: repos/cloned_ms_repos/train-ticket/ts-cancel-service/src/main/java/cancel/entity/GetAccountByIdResult.java:GetAccountByIdResult.<init>
// Node: GetAccountByIdResult
