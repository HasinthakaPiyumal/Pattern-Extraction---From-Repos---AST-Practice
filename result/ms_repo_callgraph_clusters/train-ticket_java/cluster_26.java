// Cluster 26

package edu.fudan.common.entity;

/**
 * @author fdse
 */
public enum DocumentType {

    /**
     * null
     */
    NONE      (0,"Null"),
    /**
     * id card
     */
    ID_CARD   (1,"ID Card"),
    /**
     * passport
     */
    PASSPORT  (2,"Passport"),
    /**
     * other
     */
    OTHER     (3,"Other");

    private int code;
    private String name;

    DocumentType(int code, String name){
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
        DocumentType[] documentTypeSet = DocumentType.values();
        for(DocumentType documentType : documentTypeSet){
            if(documentType.getCode() == code){
                return documentType.getName();
            }
        }
        return documentTypeSet[0].getName();
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-common/src/main/java/edu/fudan/common/entity/DocumentType.java:DocumentType.<init>
// Node: NONE
// Node: ID_CARD
// Node: PASSPORT
// Node: OTHER
// Node: DocumentType
package edu.fudan.common.entity;

/**
 * @author fdse
 */
public enum Gender {

    /**
     * null
     */
    NONE   (0, "Null"),
    /**
     * male
     */
    MALE   (1, "Male"),
    /**
     * female
     */
    FEMALE (2, "Female"),
    /**
     * other
     */
    OTHER  (3, "Other");

    private int code;
    private String name;

    Gender(int code, String name){
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
        Gender[] genderSet = Gender.values();
        for(Gender gender : genderSet){
            if(gender.getCode() == code){
                return gender.getName();
            }
        }
        return genderSet[0].getName();
    }

}


// Node: repos/cloned_ms_repos/train-ticket/ts-common/src/main/java/edu/fudan/common/entity/Gender.java:Gender.<init>
// Node: MALE
// Node: FEMALE
// Node: Gender
package edu.fudan.common.entity;

/**
 * @author fdse
 */
public enum SeatClass {

    /**
     * no seat
     */
    NONE        (0,"NoSeat"),
    /**
     * green seat
     */
    BUSINESS    (1,"GreenSeat"),
    /**
     * first class seat
     */
    FIRSTCLASS  (2,"FirstClassSeat"),
    /**
     * second class seat
     */
    SECONDCLASS (3,"SecondClassSeat"),
    /**
     * hard seat
     */
    HARDSEAT    (4,"HardSeat"),
    /**
     * soft seat
     */
    SOFTSEAT    (5,"SoftSeat"),
    /**
     * hard bed
     */
    HARDBED     (6,"HardBed"),
    /**
     * soft bed
     */
    SOFTBED     (7,"SoftBed"),
    /**
     * high soft seat
     */
    HIGHSOFTBED (8,"HighSoftSeat");

    private int code;
    private String name;

    SeatClass(int code, String name){
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
        SeatClass[] seatClassSet = SeatClass.values();
        for(SeatClass seatClass : seatClassSet){
            if(seatClass.getCode() == code){
                return seatClass.getName();
            }
        }
        return seatClassSet[0].getName();
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-common/src/main/java/edu/fudan/common/entity/SeatClass.java:seat.<init>
// Node: BUSINESS
// Node: FIRSTCLASS
// Node: SECONDCLASS
// Node: HARDSEAT
// Node: SOFTSEAT
// Node: HARDBED
// Node: SOFTBED
// Node: HIGHSOFTBED
// Node: SeatClass
package user.dto;

/**
 * @author fdse
 */
public enum Gender {

    /**
     * null
     */
    NONE(0, "Null"),
    /**
     * male
     */
    MALE(1, "Male"),
    /**
     * female
     */
    FEMALE(2, "Female"),
    /**
     * other
     */
    OTHER(3, "Other");

    private int code;
    private String name;

    Gender(int code, String name) {
        this.code = code;
        this.name = name;
    }

    public int getCode() {
        return code;
    }

    public String getName() {
        return name;
    }

    public static String getNameByCode(int code) {
        Gender[] genderSet = Gender.values();
        for (Gender gender : genderSet) {
            if (gender.getCode() == code) {
                return gender.getName();
            }
        }
        return genderSet[0].getName();
    }

}


// Node: repos/cloned_ms_repos/train-ticket/ts-user-service/src/main/java/user/dto/Gender.java:Gender.<init>
package contacts.entity;

/**
 * @author fdse
 */
public enum DocumentType {

    /**
     * null
     */
    NONE      (0,"Null"),
    /**
     * id card
     */
    ID_CARD   (1,"ID Card"),
    /**
     * passport
     */
    PASSPORT  (2,"Passport"),
    /**
     * other
     */
    OTHER     (3,"Other");

    private int code;
    private String name;

    DocumentType(int code, String name){
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
        DocumentType[] documentTypeSet = DocumentType.values();
        for(DocumentType documentType : documentTypeSet){
            if(documentType.getCode() == code){
                return documentType.getName();
            }
        }
        return documentTypeSet[0].getName();
    }
}


// Node: repos/cloned_ms_repos/train-ticket/ts-contacts-service/src/main/java/contacts/entity/DocumentType.java:DocumentType.<init>
