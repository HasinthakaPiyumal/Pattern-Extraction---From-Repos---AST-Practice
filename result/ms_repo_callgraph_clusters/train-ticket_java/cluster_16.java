// Cluster 16

package waitorder.entity;

import edu.fudan.common.entity.OrderStatus;

public enum WaitListOrderStatus {
    /**
     * not paid
     */
    NOTPAID   (0,"Not Paid"),
    /**
     * paid and not collected
     */
    PAID      (1,"Paid & Not Collected"),
    /**
     * collected
     */
    COLLECTED (2,"Collected"),
    /**
     * cancel
     */
    CANCEL    (3,"Cancel"),
    /**
     * refunded
     */
    REFUNDS   (4,"Refunded"),
    /**
     * expired
     */
    EXPIRED   (5, "Expired");



    private int code;
    private String name;

    WaitListOrderStatus(int code, String name){
        this.code = code;
        this.name = name;
    }

    public int getCode(){
        return code;
    }

    public String getName() {
        return name;
    }

    public static String getNameByCode(int code){
        OrderStatus[] orderStatusSet = OrderStatus.values();
        for(OrderStatus orderStatus : orderStatusSet){
            if(orderStatus.getCode() == code){
                return orderStatus.getName();
            }
        }
        return orderStatusSet[0].getName();
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-wait-order-service/src/main/java/waitorder/entity/WaitListOrderStatus.java:WaitListOrderStatus.<init>
// Node: NOTPAID
// Node: PAID
// Node: COLLECTED
// Node: CANCEL
// Node: REFUNDS
// Node: EXPIRED
// Node: WaitListOrderStatus
package edu.fudan.common.entity;

/**
 * @author fdse
 */
public enum OrderStatus {

    /**
     * not paid
     */
    NOTPAID   (0,"Not Paid"),
    /**
     * paid and not collected
     */
    PAID      (1,"Paid & Not Collected"),
    /**
     * collected
     */
    COLLECTED (2,"Collected"),
    /**
     * cancel and rebook
     */
    CHANGE    (3,"Cancel & Rebook"),
    /**
     * cancel
     */
    CANCEL    (4,"Cancel"),
    /**
     * refunded
     */
    REFUNDS   (5,"Refunded"),
    /**
     * used
     */
    USED      (6,"Used");

    private int code;
    private String name;

    OrderStatus(int code, String name){
        this.code = code;
        this.name = name;
    }

    public int getCode(){
        return code;
    }

    public String getName() {
        return name;
    }

    public static String getNameByCode(int code){
        OrderStatus[] orderStatusSet = OrderStatus.values();
        for(OrderStatus orderStatus : orderStatusSet){
            if(orderStatus.getCode() == code){
                return orderStatus.getName();
            }
        }
        return orderStatusSet[0].getName();
    }

}


// Node: repos/cloned_ms_repos/train-ticket/ts-common/src/main/java/edu/fudan/common/entity/OrderStatus.java:OrderStatus.<init>
// Node: CHANGE
// Node: USED
// Node: OrderStatus
