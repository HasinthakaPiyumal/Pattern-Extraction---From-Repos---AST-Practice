// Cluster 27

package edu.fudan.common.entity;

import java.io.Serializable;

/**
 * @author fdse
 */
public enum Type implements Serializable{
    /**
     * G
     */
    G("G", 1),
    /**
     * D
     */
    D("D", 2),
    /**
     * Z
     */
    Z("Z",3),
    /**
     * T
     */
    T("T", 4),
    /**
     * K
     */
    K("K", 5);

    private String name;
    private int index;

    Type(String name, int index) {
        this.name = name;
        this.index = index;
    }

    public static String getName(int index) {
        for (Type type : Type.values()) {
            if (type.getIndex() == index) {
                return type.name;
            }
        }
        return null;
    }

    public String getName() {
        return name;
    }

    void setName(String name) {
        this.name = name;
    }

    public int getIndex() {
        return index;
    }

    void setIndex(int index) {
        this.index = index;
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-common/src/main/java/edu/fudan/common/entity/Type.java:Type.<init>
// Node: G
// Node: D
// Node: Z
// Node: T
// Node: K
// Node: Type
package inside_payment.entity;

import java.io.Serializable;

/**
 * @author fdse
 */
public enum MoneyType implements Serializable {

    /**
     * add money
     */
    A("Add Money",1),
    /**
     * draw back money
     */
    D("Draw Back Money",2);

    private String name;
    private int index;

    MoneyType(String name, int index) {
        this.name = name;
        this.index = index;
    }

    public static String getName(int index) {
        for (MoneyType type : MoneyType.values()) {
            if (type.getIndex() == index) {
                return type.name;
            }
        }
        return null;
    }

    public String getName() {
        return name;
    }

    void setName(String name) {
        this.name = name;
    }

    public int getIndex() {
        return index;
    }

    void setIndex(int index) {
        this.index = index;
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-inside-payment-service/src/main/java/inside_payment/entity/MoneyType.java:MoneyType.<init>
// Node: A
// Node: MoneyType
package inside_payment.entity;

import java.io.Serializable;

/**
 * @author fdse
 */
public enum  PaymentType implements Serializable {

    /**
     * payment
     */
    P("Payment",1),
    /**
     * difference
     */
    D("Difference",2),
    /**
     * outside payment
     */
    O("Outside Payment",3),
    /**
     * difference and outside payment
     */
    E("Difference & Outside Payment",4);

    private String name;
    private int index;

    PaymentType(String name, int index) {
        this.name = name;
        this.index = index;
    }

    public static String getName(int index) {
        for (PaymentType type : PaymentType.values()) {
            if (type.getIndex() == index) {
                return type.name;
            }
        }
        return null;
    }

    public String getName() {
        return name;
    }

    void setName(String name) {
        this.name = name;
    }

    public int getIndex() {
        return index;
    }

    void setIndex(int index) {
        this.index = index;
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-inside-payment-service/src/main/java/inside_payment/entity/PaymentType.java:PaymentType.<init>
// Node: P
// Node: O
// Node: E
// Node: PaymentType
